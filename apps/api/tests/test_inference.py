from datetime import date, datetime

from app.models import EventCandidate, ParsedDocument, Source
from app.services.inference import classify_evidence, infer_status


def make_source(source_type: str) -> Source:
    return Source(
        id="src-1",
        district_id="district-1",
        url="https://district.example/source",
        source_type=source_type,
        title="District Source",
        rank_score=9,
        last_fetched_at=datetime.utcnow(),
    )


def make_document() -> ParsedDocument:
    return ParsedDocument(
        id="doc-1",
        source_id="src-1",
        parser_version="1",
        parse_method="html_text",
        school_year_text="2025-2026",
        extracted_text="Closed March 27, 2026",
        extraction_confidence=0.8,
        metadata_json={},
    )


def make_event(status_effect: str) -> EventCandidate:
    return EventCandidate(
        id="event-1",
        parsed_document_id="doc-1",
        raw_text="Closed March 27, 2026",
        raw_date_text="March 27, 2026",
        start_date=date(2026, 3, 27),
        end_date=date(2026, 3, 27),
        label_raw="Closed",
        label_normalized="closure",
        status_effect=status_effect,
        applies_to="district_wide",
        confidence=0.98,
        notes_json={},
    )


def test_same_day_alert_outranks_other_evidence():
    evidence = [
        classify_evidence(make_source("alert_page"), make_document(), make_event("out_of_school"), date(2026, 3, 27))
    ]
    decision = infer_status(date(2026, 3, 27), None, [item for item in evidence if item])
    assert decision.status == "out_of_school"
    assert decision.confidence_level == "high"


def test_conflicting_calendar_evidence_returns_unclear():
    source = make_source("pdf_calendar")
    document = make_document()
    first = classify_evidence(source, document, make_event("out_of_school"), date(2026, 3, 27))
    second_event = make_event("delayed_or_modified")
    second_event.id = "event-2"
    second = classify_evidence(source, document, second_event, date(2026, 3, 27))
    decision = infer_status(date(2026, 3, 27), None, [item for item in [first, second] if item])
    assert decision.status == "unclear"

