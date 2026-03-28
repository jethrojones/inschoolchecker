from datetime import date

from app.services.normalizer import normalize_event
from app.services.parser import ParsedEvent


def test_normalizer_maps_spring_break_to_out_of_school():
    event = ParsedEvent(
        raw_text="Spring Break March 27-28, 2026",
        raw_date_text="March 27-28, 2026",
        start_date=date(2026, 3, 27),
        end_date=date(2026, 3, 28),
        label_raw="Spring Break",
        notes={},
    )
    normalized = normalize_event(event)
    assert normalized.label_normalized == "spring_break"
    assert normalized.status_effect == "out_of_school"


def test_normalizer_rejects_bare_numeric_calendar_labels():
    event = ParsedEvent(
        raw_text="March 2026",
        raw_date_text="March 20, 2026",
        start_date=date(2026, 3, 20),
        end_date=date(2026, 3, 20),
        label_raw="26",
        notes={},
    )
    normalized = normalize_event(event)
    assert normalized.status_effect == "unknown"
