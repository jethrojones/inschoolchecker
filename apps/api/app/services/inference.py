from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from app.models import EventCandidate, ManualOverride, ParsedDocument, Source


STATUS_WEIGHT = {
    "same_day_closure_alert": 1.00,
    "same_day_delay_alert": 0.96,
    "calendar_exact_match": 0.90,
    "recent_announcement": 0.80,
    "weak_announcement": 0.50,
    "weekday_fallback": 0.30,
}


@dataclass
class InferenceEvidence:
    source: Source
    parsed_document: ParsedDocument
    event: EventCandidate
    evidence_type: str
    weight: float


@dataclass
class InferenceDecision:
    status: str
    confidence_score: float
    confidence_level: str
    explanation: str
    evidence: list[dict]
    conflicting_evidence: list[dict]
    rationale: list[dict]
    result_type: str = "inferred"


def confidence_level(score: float) -> str:
    if score >= 0.85:
        return "high"
    if score >= 0.60:
        return "medium"
    return "low"


def override_as_decision(override: ManualOverride) -> InferenceDecision:
    return InferenceDecision(
        status=override.status,
        confidence_score=1.0,
        confidence_level="high",
        explanation=override.explanation,
        evidence=[],
        conflicting_evidence=[],
        rationale=[{"type": "manual_override", "reason": override.reason, "created_by": override.created_by}],
        result_type="manual_override",
    )


def build_evidence_item(candidate: InferenceEvidence, matched: bool = True) -> dict:
    return {
        "type": candidate.evidence_type,
        "label": candidate.event.label_raw,
        "matched": matched,
        "source_id": candidate.source.id,
        "source_url": candidate.source.url,
        "source_title": candidate.source.title,
        "snippet": candidate.event.raw_text[:280],
        "start_date": candidate.event.start_date,
        "end_date": candidate.event.end_date,
        "parser_interpretation": candidate.event.status_effect,
        "freshness": candidate.source.last_fetched_at,
        "weight": candidate.weight,
    }


def infer_status(
    target_date: date,
    override: ManualOverride | None,
    evidence: list[InferenceEvidence],
) -> InferenceDecision:
    if override:
        return override_as_decision(override)

    ranked = sorted(evidence, key=lambda item: item.weight, reverse=True)
    same_day_closure = [item for item in ranked if item.evidence_type == "same_day_closure_alert"]
    if same_day_closure:
        best = same_day_closure[0]
        return InferenceDecision(
            status="out_of_school",
            confidence_score=best.weight,
            confidence_level=confidence_level(best.weight),
            explanation=f"{best.source.title or 'A district alert'} indicates students are out of school on {target_date.isoformat()}. Confidence is high because same-day alerts outrank static calendars.",
            evidence=[build_evidence_item(best)],
            conflicting_evidence=[],
            rationale=[{"rule": "same_day_alert_overrides_static_calendar"}],
        )

    same_day_delay = [item for item in ranked if item.evidence_type == "same_day_delay_alert"]
    if same_day_delay:
        best = same_day_delay[0]
        return InferenceDecision(
            status="delayed_or_modified",
            confidence_score=best.weight,
            confidence_level=confidence_level(best.weight),
            explanation=f"{best.source.title or 'A district alert'} indicates a delayed or modified schedule for {target_date.isoformat()}.",
            evidence=[build_evidence_item(best)],
            conflicting_evidence=[],
            rationale=[{"rule": "same_day_delay_alert"}],
        )

    exact_matches = [item for item in ranked if item.evidence_type == "calendar_exact_match"]
    if exact_matches:
        statuses = {item.event.status_effect for item in exact_matches}
        if len(statuses) > 1:
            top = exact_matches[:2]
            return InferenceDecision(
                status="unclear",
                confidence_score=0.4,
                confidence_level="low",
                explanation="The available calendar evidence conflicts for the target date, so the system is returning unclear rather than guessing.",
                evidence=[],
                conflicting_evidence=[build_evidence_item(item) for item in top],
                rationale=[{"rule": "conflicting_strong_sources"}],
            )
        best = exact_matches[0]
        mapped_status = "out_of_school" if best.event.status_effect == "out_of_school" else "delayed_or_modified"
        return InferenceDecision(
            status=mapped_status,
            confidence_score=best.weight,
            confidence_level=confidence_level(best.weight),
            explanation=f"{best.source.title or 'The district calendar'} shows '{best.event.label_raw}' on the target date.",
            evidence=[build_evidence_item(best)],
            conflicting_evidence=[],
            rationale=[{"rule": "official_calendar_exact_match"}],
        )

    recent_announcements = [item for item in ranked if item.evidence_type in {"recent_announcement", "weak_announcement"}]
    if recent_announcements:
        best = recent_announcements[0]
        status = "out_of_school" if best.event.status_effect == "out_of_school" else "delayed_or_modified"
        return InferenceDecision(
            status=status,
            confidence_score=best.weight,
            confidence_level=confidence_level(best.weight),
            explanation=f"{best.source.title or 'A district announcement'} suggests a schedule change for the target date, but it is weaker than a same-day alert or official calendar.",
            evidence=[build_evidence_item(best)],
            conflicting_evidence=[],
            rationale=[{"rule": "recent_announcement"}],
        )

    if target_date.weekday() < 5:
        score = STATUS_WEIGHT["weekday_fallback"]
        return InferenceDecision(
            status="unclear",
            confidence_score=score,
            confidence_level=confidence_level(score),
            explanation="No district-wide closure or schedule change was found. Because the evidence is only a weekday fallback, the result remains unclear.",
            evidence=[],
            conflicting_evidence=[],
            rationale=[{"rule": "weekday_fallback_insufficient"}],
        )

    return InferenceDecision(
        status="unclear",
        confidence_score=0.25,
        confidence_level="low",
        explanation="No reliable district-wide evidence was found for the target date.",
        evidence=[],
        conflicting_evidence=[],
        rationale=[{"rule": "insufficient_evidence"}],
    )


def classify_evidence(source: Source, parsed_document: ParsedDocument, event: EventCandidate, target_date: date) -> InferenceEvidence | None:
    if not event.start_date:
        return None
    if event.start_date <= target_date <= (event.end_date or event.start_date):
        if source.source_type == "alert_page" and event.status_effect == "out_of_school":
            evidence_type = "same_day_closure_alert"
        elif source.source_type == "alert_page" and event.status_effect == "delayed_or_modified":
            evidence_type = "same_day_delay_alert"
        elif source.source_type in {"pdf_calendar", "calendar_page"}:
            evidence_type = "calendar_exact_match"
        elif source.source_type == "news_post":
            evidence_type = "recent_announcement"
        else:
            evidence_type = "weak_announcement"
        return InferenceEvidence(
            source=source,
            parsed_document=parsed_document,
            event=event,
            evidence_type=evidence_type,
            weight=STATUS_WEIGHT[evidence_type],
        )
    return None


def cache_expiration_for(target_date: date) -> datetime:
    now = datetime.utcnow()
    if target_date == now.date():
        return now + timedelta(hours=1)
    return now + timedelta(hours=24)
