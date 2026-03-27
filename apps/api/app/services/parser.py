from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO

from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from pypdf import PdfReader


DATE_LINE_RE = re.compile(
    r"(?P<date>(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:\s*[-–]\s*\d{1,2})?(?:,\s*\d{4})?)",
    re.IGNORECASE,
)
SCHOOL_YEAR_RE = re.compile(r"(20\d{2}\s*[-/]\s*20\d{2})")


@dataclass
class ParsedEvent:
    raw_text: str
    raw_date_text: str | None
    start_date: date | None
    end_date: date | None
    label_raw: str | None
    notes: dict


@dataclass
class ParsedOutput:
    title: str | None
    school_year_text: str | None
    extracted_text: str
    extraction_confidence: float
    parse_method: str
    metadata: dict
    events: list[ParsedEvent]


def extract_events_from_text(text: str, default_year: int | None = None) -> list[ParsedEvent]:
    events: list[ParsedEvent] = []
    for raw_line in [line.strip() for line in text.splitlines() if line.strip()]:
        match = DATE_LINE_RE.search(raw_line)
        if not match:
            continue
        raw_date = match.group("date")
        start_date, end_date = parse_date_range(raw_date, default_year=default_year)
        label = raw_line.replace(raw_date, "").strip(" :-\u2013")
        events.append(
            ParsedEvent(
                raw_text=raw_line,
                raw_date_text=raw_date,
                start_date=start_date,
                end_date=end_date,
                label_raw=label or raw_line,
                notes={"extraction": "line_date_match"},
            )
        )
    return events


def parse_date_range(raw_date: str, default_year: int | None = None) -> tuple[date | None, date | None]:
    cleaned = raw_date.replace("\u2013", "-")
    base_default = datetime(default_year or date.today().year, 1, 1)
    if "-" not in cleaned:
        parsed = date_parser.parse(cleaned, fuzzy=True, default=base_default)
        return parsed.date(), parsed.date()
    month_part, day_part = cleaned.split(" ", 1)
    left, right = day_part.split("-", 1)
    left_day = re.sub(r"[^\d]", "", left)
    right_day_match = re.search(r"\d{1,2}", right)
    right_day = right_day_match.group(0) if right_day_match else re.sub(r"[^\d]", "", right)
    year_match = re.search(r"(\d{4})", cleaned)
    year = int(year_match.group(1)) if year_match else (default_year or date.today().year)
    start = date_parser.parse(f"{month_part} {left_day} {year}", fuzzy=True).date()
    end = date_parser.parse(f"{month_part} {right_day} {year}", fuzzy=True).date()
    return start, end


def parse_html_document(html: str) -> ParsedOutput:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    headings = [node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2", "h3"])]
    body_text = soup.get_text("\n", strip=True)
    school_year = SCHOOL_YEAR_RE.search(body_text)
    events = extract_events_from_text(body_text)
    return ParsedOutput(
        title=title,
        school_year_text=school_year.group(1) if school_year else None,
        extracted_text=body_text,
        extraction_confidence=0.8 if body_text else 0.2,
        parse_method="html_text",
        metadata={"headings": headings[:12]},
        events=events,
    )


def parse_pdf_document(content: bytes) -> ParsedOutput:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages)
    school_year = SCHOOL_YEAR_RE.search(text)
    events = extract_events_from_text(text)
    return ParsedOutput(
        title=None,
        school_year_text=school_year.group(1) if school_year else None,
        extracted_text=text,
        extraction_confidence=0.75 if text.strip() else 0.15,
        parse_method="pdf_text",
        metadata={"page_count": len(reader.pages)},
        events=events,
    )
