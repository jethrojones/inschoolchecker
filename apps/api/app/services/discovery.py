from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

DISCOVERY_KEYWORDS = {
    "calendar": 4.0,
    "school year": 3.0,
    "academic calendar": 4.0,
    "district calendar": 4.0,
    "no school": 4.5,
    "closure": 5.0,
    "closed": 5.0,
    "delay": 4.0,
    "delayed start": 5.0,
    "inclement weather": 5.0,
    "emergency": 4.5,
    "alert": 4.0,
    "news": 2.0,
}


@dataclass
class CandidateSource:
    url: str
    title: str | None
    source_type: str
    rank_score: float
    discovered_from_url: str


def fingerprint_cms(html: str) -> str | None:
    lowered = html.lower()
    if "apptegy_cms" in lowered or "thrillshare" in lowered:
        return "apptegy"
    if "finalsite" in lowered:
        return "finalsite"
    if "schoolwires" in lowered or "blackboard" in lowered:
        return "blackboard"
    if "wp-content" in lowered:
        return "wordpress"
    if "googlesite" in lowered or "sites.google.com" in lowered:
        return "google_sites"
    return None


def guess_source_type(text: str, href: str) -> str:
    lowered = f"{text} {href}".lower()
    if href.lower().endswith(".pdf"):
        return "pdf_calendar" if "calendar" in lowered else "pdf_document"
    if any(term in lowered for term in ("alert", "closure", "delay", "emergency", "weather")):
        return "alert_page"
    if "news" in lowered or "announcement" in lowered:
        return "news_post"
    if "calendar" in lowered:
        return "calendar_page"
    return "homepage_link"


def rank_candidate(text: str, href: str, position: int) -> float:
    lowered = f"{text} {href}".lower()
    score = 0.0
    for keyword, weight in DISCOVERY_KEYWORDS.items():
        if keyword in lowered:
            score += weight
    if href.lower().endswith(".pdf"):
        score += 3.0
    if "calendar" in lowered and href.lower().endswith(".pdf"):
        score += 0.5
    if position < 10:
        score += 1.0
    if any(token in href.lower() for token in ("/calendar", "/alerts", "/news", "/weather")):
        score += 1.5
    return score


def discover_sources(homepage_url: str, html: str, max_candidates: int = 12) -> tuple[list[CandidateSource], str | None, str | None]:
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else None
    candidates: list[CandidateSource] = []
    for index, anchor in enumerate(soup.find_all("a", href=True)):
        text = anchor.get_text(" ", strip=True)
        href = urljoin(homepage_url, anchor["href"])
        if urlparse(href).scheme not in {"http", "https"}:
            continue
        score = rank_candidate(text, href, index)
        if score <= 0:
            continue
        candidates.append(
            CandidateSource(
                url=href,
                title=text or None,
                source_type=guess_source_type(text, href),
                rank_score=score,
                discovered_from_url=homepage_url,
            )
        )
    deduped: dict[str, CandidateSource] = {}
    for candidate in sorted(candidates, key=lambda item: item.rank_score, reverse=True):
        deduped.setdefault(candidate.url, candidate)
    return list(deduped.values())[:max_candidates], fingerprint_cms(html), title
