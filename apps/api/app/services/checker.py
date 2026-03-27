from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import District, EventCandidate, InferenceResult, ManualOverride, ParsedDocument, Source
from app.schemas import (
    AdminResultSummary,
    CheckRequest,
    CheckResponse,
    DiscoverResponse,
    DistrictResponse,
    EvidenceItem,
    OverrideRequest,
    SourceSummary,
)
from app.services.discovery import discover_sources
from app.services.fetcher import fetch_url
from app.services.inference import cache_expiration_for, classify_evidence, infer_status
from app.services.normalizer import normalize_event
from app.services.parser import ParsedOutput, parse_html_document, parse_pdf_document
from app.services.url_safety import UnsafeURLError, canonical_domain, normalize_url


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def get_or_create_district(db: Session, district_url: str) -> District:
    normalized = normalize_url(district_url)
    domain = canonical_domain(normalized)
    district = db.scalar(select(District).where(District.canonical_domain == domain))
    if district:
        if district.homepage_url != normalized:
            district.homepage_url = normalized
            db.commit()
        return district
    district = District(name=domain, canonical_domain=domain, homepage_url=normalized)
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


def get_district_or_404(db: Session, district_id: str) -> DistrictResponse:
    district = db.get(District, district_id)
    if not district:
        raise LookupError("District not found")
    return DistrictResponse(
        id=district.id,
        name=district.name,
        canonical_domain=district.canonical_domain,
        homepage_url=district.homepage_url,
        cms_type_guess=district.cms_type_guess,
        timezone=district.timezone,
        status=district.status,
    )


def _upsert_source(db: Session, district: District, candidate) -> Source:
    existing = db.scalar(select(Source).where(Source.district_id == district.id, Source.url == candidate.url))
    if existing:
        existing.rank_score = max(existing.rank_score, candidate.rank_score)
        existing.source_type = candidate.source_type
        existing.title = candidate.title or existing.title
        db.commit()
        return existing
    source = Source(
        district_id=district.id,
        url=candidate.url,
        source_type=candidate.source_type,
        title=candidate.title,
        file_type="application/pdf" if candidate.url.lower().endswith(".pdf") else "text/html",
        discovered_from_url=candidate.discovered_from_url,
        rank_score=candidate.rank_score,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _persist_parsed_output(db: Session, source: Source, parsed: ParsedOutput) -> ParsedDocument:
    document = ParsedDocument(
        source_id=source.id,
        parser_version="1",
        parse_method=parsed.parse_method,
        school_year_text=parsed.school_year_text,
        extracted_text=parsed.extracted_text,
        extraction_confidence=parsed.extraction_confidence,
        metadata_json=parsed.metadata,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    for parsed_event in parsed.events:
        normalized = normalize_event(parsed_event)
        db.add(
            EventCandidate(
                parsed_document_id=document.id,
                raw_text=parsed_event.raw_text,
                raw_date_text=parsed_event.raw_date_text,
                start_date=parsed_event.start_date,
                end_date=parsed_event.end_date,
                label_raw=parsed_event.label_raw,
                label_normalized=normalized.label_normalized,
                status_effect=normalized.status_effect,
                applies_to=normalized.applies_to,
                confidence=normalized.confidence,
                notes_json=normalized.notes | parsed_event.notes,
            )
        )
    db.commit()
    return document


def run_discovery(db: Session, district_url: str) -> DiscoverResponse:
    district = get_or_create_district(db, district_url)
    fetch = fetch_url(db, district.homepage_url)
    if not fetch.text:
        raise ValueError("Homepage did not return HTML content.")
    candidates, cms_type, title = discover_sources(district.homepage_url, fetch.text)
    district.cms_type_guess = cms_type or district.cms_type_guess
    district.name = title or district.name
    db.commit()
    sources = [_upsert_source(db, district, candidate) for candidate in candidates]
    return DiscoverResponse(
        district_id=district.id,
        district={"name": district.name, "canonical_domain": district.canonical_domain},
        cms_type_guess=district.cms_type_guess,
        sources=[_to_source_summary(source) for source in sources],
    )


def list_sources_for_district(db: Session, district_id: str) -> list[SourceSummary]:
    sources = db.scalars(select(Source).where(Source.district_id == district_id).order_by(Source.rank_score.desc())).all()
    return [_to_source_summary(source) for source in sources]


def _to_source_summary(source: Source) -> SourceSummary:
    return SourceSummary(
        id=source.id,
        title=source.title,
        url=source.url,
        source_type=source.source_type,
        freshness=_as_utc(source.last_fetched_at),
        rank_score=source.rank_score,
    )


def _find_active_override(db: Session, district_id: str, target_date: date) -> ManualOverride | None:
    now = datetime.now(timezone.utc)
    overrides = db.scalars(
        select(ManualOverride).where(
            ManualOverride.district_id == district_id,
            ManualOverride.target_date == target_date,
        )
    ).all()
    for override in overrides:
        expires_at = _as_utc(override.expires_at)
        if expires_at is None or expires_at >= now:
            return override
    return None


def _get_cached_result(db: Session, district_id: str, target_date: date) -> InferenceResult | None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return db.scalar(
        select(InferenceResult)
        .where(
            InferenceResult.district_id == district_id,
            InferenceResult.target_date == target_date,
            InferenceResult.cache_expires_at >= now,
        )
        .order_by(InferenceResult.generated_at.desc())
    )


def _result_to_response(db: Session, district: District, result: InferenceResult, result_type: str = "inferred") -> CheckResponse:
    sources = db.scalars(select(Source).where(Source.district_id == district.id).order_by(Source.rank_score.desc())).all()
    return CheckResponse(
        district={"name": district.name, "canonical_domain": district.canonical_domain},
        target_date=result.target_date,
        status=result.status,
        confidence_score=result.confidence_score,
        confidence_level=result.confidence_level,
        explanation=result.explanation,
        sources=[_to_source_summary(source) for source in sources[:6]],
        evidence=[EvidenceItem(**item) for item in result.evidence_json],
        result_type=result_type,
        last_checked=_as_utc(result.generated_at) or datetime.now(timezone.utc),
    )


def _parse_and_store_source(db: Session, source: Source) -> ParsedDocument | None:
    fetch = fetch_url(db, source.url, source=source)
    source.fetch_status = "fetched"
    source.last_fetched_at = fetch.fetched_at
    source.content_hash = fetch.content_hash
    source.snapshot_object_key = fetch.snapshot_path
    source.etag = fetch.headers.get("etag")
    source.last_modified_header = fetch.headers.get("last-modified")
    db.commit()
    parsed = parse_pdf_document(fetch.bytes_content) if source.url.lower().endswith(".pdf") else parse_html_document(fetch.text or "")
    return _persist_parsed_output(db, source, parsed)


def _build_fresh_result(db: Session, district: District, target_date: date) -> CheckResponse:
    override = _find_active_override(db, district.id, target_date)
    if override:
        decision = infer_status(target_date, override, [])
        result = InferenceResult(
            district_id=district.id,
            target_date=target_date,
            status=decision.status,
            confidence_score=decision.confidence_score,
            confidence_level=decision.confidence_level,
            explanation=decision.explanation,
            evidence_json=decision.evidence,
            conflicting_evidence_json=decision.conflicting_evidence,
            rationale_json=decision.rationale,
            generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            cache_expires_at=cache_expiration_for(target_date),
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return _result_to_response(db, district, result, result_type="manual_override")

    sources = db.scalars(select(Source).where(Source.district_id == district.id).order_by(Source.rank_score.desc())).all()
    parsed_documents_by_source: dict[str, ParsedDocument] = {}
    for source in sources[:4]:
        parsed_document = db.scalar(
            select(ParsedDocument).where(ParsedDocument.source_id == source.id).order_by(ParsedDocument.created_at.desc())
        )
        if not parsed_document:
            try:
                parsed_document = _parse_and_store_source(db, source)
            except Exception:
                continue
        if parsed_document:
            parsed_documents_by_source[source.id] = parsed_document

    evidence = []
    for source in sources:
        parsed_document = parsed_documents_by_source.get(source.id) or db.scalar(
            select(ParsedDocument).where(ParsedDocument.source_id == source.id).order_by(ParsedDocument.created_at.desc())
        )
        if not parsed_document:
            continue
        events = db.scalars(select(EventCandidate).where(EventCandidate.parsed_document_id == parsed_document.id)).all()
        for event in events:
            classified = classify_evidence(source, parsed_document, event, target_date)
            if classified:
                evidence.append(classified)

    calendar_sources = [source for source in sources if source.source_type in {"calendar_page", "pdf_calendar"}]
    decision = infer_status(
        target_date,
        None,
        evidence,
        has_calendar_coverage=bool(calendar_sources),
        calendar_sources=calendar_sources,
    )
    result = InferenceResult(
        district_id=district.id,
        target_date=target_date,
        status=decision.status,
        confidence_score=decision.confidence_score,
        confidence_level=decision.confidence_level,
        explanation=decision.explanation,
        evidence_json=decision.evidence,
        conflicting_evidence_json=decision.conflicting_evidence,
        rationale_json=decision.rationale,
        generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
        cache_expires_at=cache_expiration_for(target_date),
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return _result_to_response(db, district, result, decision.result_type)


def get_cached_or_fresh_result(db: Session, payload: CheckRequest) -> CheckResponse:
    target_date = payload.target_date or date.today()
    district = get_or_create_district(db, payload.district_url)
    override = _find_active_override(db, district.id, target_date)
    if override:
        decision = infer_status(target_date, override, [])
        result = InferenceResult(
            district_id=district.id,
            target_date=target_date,
            status=decision.status,
            confidence_score=decision.confidence_score,
            confidence_level=decision.confidence_level,
            explanation=decision.explanation,
            evidence_json=decision.evidence,
            conflicting_evidence_json=decision.conflicting_evidence,
            rationale_json=decision.rationale,
            generated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            cache_expires_at=cache_expiration_for(target_date),
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        return _result_to_response(db, district, result, "manual_override")
    if not payload.force_refresh:
        cached = _get_cached_result(db, district.id, target_date)
        if cached:
            return _result_to_response(db, district, cached, "inferred")
    sources = db.scalars(select(Source).where(Source.district_id == district.id)).all()
    if payload.force_refresh or not sources:
        try:
            run_discovery(db, district.homepage_url)
        except Exception:
            pass
    return _build_fresh_result(db, district, target_date)


def create_manual_override(db: Session, payload: OverrideRequest) -> CheckResponse:
    district = db.get(District, payload.district_id)
    if not district:
        raise LookupError("District not found")
    override = ManualOverride(
        district_id=payload.district_id,
        target_date=payload.target_date,
        status=payload.status,
        explanation=payload.explanation,
        created_by=payload.created_by,
        reason=payload.reason,
        expires_at=payload.expires_at,
    )
    db.add(override)
    db.commit()
    return get_cached_or_fresh_result(db, CheckRequest(district_url=district.homepage_url, target_date=payload.target_date))


def reparse_sources(db: Session, payload) -> dict:
    sources = []
    if payload.source_id:
        source = db.get(Source, payload.source_id)
        if source:
            sources.append(source)
    elif payload.district_id:
        sources.extend(db.scalars(select(Source).where(Source.district_id == payload.district_id)).all())
    reparsed = 0
    for source in sources:
        try:
            _parse_and_store_source(db, source)
            reparsed += 1
        except Exception:
            continue
    if payload.district_id:
        db.execute(delete(InferenceResult).where(InferenceResult.district_id == payload.district_id))
        db.commit()
    return {"reparsed_sources": reparsed}


def list_admin_results(db: Session, confidence_level: str | None = None, conflicts_only: bool = False) -> list[AdminResultSummary]:
    results = db.scalars(select(InferenceResult).order_by(InferenceResult.generated_at.desc())).all()
    summaries: list[AdminResultSummary] = []
    for result in results:
        if confidence_level and result.confidence_level != confidence_level:
            continue
        has_conflict = bool(result.conflicting_evidence_json)
        if conflicts_only and not has_conflict:
            continue
        district = db.get(District, result.district_id)
        if not district:
            continue
        summaries.append(
            AdminResultSummary(
                id=result.id,
                district_id=result.district_id,
                district_name=district.name,
                target_date=result.target_date,
                status=result.status,
                confidence_score=result.confidence_score,
                confidence_level=result.confidence_level,
                explanation=result.explanation,
                generated_at=result.generated_at,
                has_conflict=has_conflict,
            )
        )
    return summaries
