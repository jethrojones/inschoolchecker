from __future__ import annotations

from dataclasses import dataclass

from app.services.parser import ParsedEvent


NORMALIZATION_RULES: list[tuple[tuple[str, ...], tuple[str, str, float]]] = [
    (("holiday",), ("holiday", "out_of_school", 0.9)),
    (("no school",), ("no_school", "out_of_school", 0.98)),
    (("spring break",), ("spring_break", "out_of_school", 0.95)),
    (("winter break",), ("winter_break", "out_of_school", 0.95)),
    (("thanksgiving break",), ("thanksgiving_break", "out_of_school", 0.95)),
    (("non student",), ("non_student_day", "out_of_school", 0.92)),
    (("teacher workday", "teacher work day", "staff development"), ("teacher_workday", "out_of_school", 0.88)),
    (("semester break",), ("semester_break", "out_of_school", 0.92)),
    (("delayed start", "late start", "2-hour delay", "two-hour delay"), ("delayed_start", "delayed_or_modified", 0.97)),
    (("remote learning",), ("remote_learning", "delayed_or_modified", 0.9)),
    (("conference",), ("conference", "conditional", 0.55)),
    (("weather make up", "weather makeup"), ("weather_makeup", "conditional", 0.5)),
    (("closed", "closure"), ("closure", "out_of_school", 0.98)),
]


@dataclass
class NormalizedEvent:
    label_normalized: str
    status_effect: str
    confidence: float
    applies_to: str
    notes: dict


def normalize_event(event: ParsedEvent) -> NormalizedEvent:
    label = (event.label_raw or event.raw_text).lower()
    notes = {"raw_label": event.label_raw, "raw_text": event.raw_text}
    for keywords, outcome in NORMALIZATION_RULES:
        if any(keyword in label for keyword in keywords):
            normalized_label, effect, confidence = outcome
            applies_to = "district_wide" if effect != "informational_only" else "unknown"
            return NormalizedEvent(normalized_label, effect, confidence, applies_to, notes)
    return NormalizedEvent("unknown", "unknown", 0.35, "unknown", notes)

