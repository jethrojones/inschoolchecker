from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


SchoolStatus = Literal["in_school", "out_of_school", "delayed_or_modified", "unclear"]
ConfidenceLevel = Literal["high", "medium", "low"]


class CheckRequest(BaseModel):
    district_url: str = Field(..., examples=["https://www.examplek12.org"])
    target_date: date | None = None


class DistrictSummary(BaseModel):
    name: str
    canonical_domain: str


class SourceSummary(BaseModel):
    id: str
    title: str | None = None
    url: HttpUrl | str
    source_type: str
    freshness: datetime | None = None
    rank_score: float | None = None


class EvidenceItem(BaseModel):
    type: str
    label: str | None = None
    matched: bool = True
    source_id: str | None = None
    source_url: str | None = None
    source_title: str | None = None
    snippet: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    parser_interpretation: str | None = None
    freshness: datetime | None = None
    weight: float | None = None


class CheckResponse(BaseModel):
    district: DistrictSummary
    target_date: date
    status: SchoolStatus
    confidence_score: float
    confidence_level: ConfidenceLevel
    explanation: str
    sources: list[SourceSummary]
    evidence: list[EvidenceItem]
    result_type: Literal["inferred", "manual_override"]
    last_checked: datetime


class DiscoverRequest(BaseModel):
    district_url: str


class DiscoverResponse(BaseModel):
    district_id: str
    district: DistrictSummary
    cms_type_guess: str | None = None
    sources: list[SourceSummary]


class DistrictResponse(BaseModel):
    id: str
    name: str
    canonical_domain: str
    homepage_url: str
    cms_type_guess: str | None = None
    timezone: str | None = None
    status: str


class OverrideRequest(BaseModel):
    district_id: str
    target_date: date
    status: SchoolStatus
    explanation: str
    created_by: str
    reason: str
    expires_at: datetime | None = None


class ReparseRequest(BaseModel):
    district_id: str | None = None
    source_id: str | None = None


class AdminResultSummary(BaseModel):
    id: str
    district_id: str
    district_name: str
    target_date: date
    status: SchoolStatus
    confidence_score: float
    confidence_level: ConfidenceLevel
    explanation: str
    generated_at: datetime
    has_conflict: bool

