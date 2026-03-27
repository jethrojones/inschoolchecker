from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


class District(Base):
    __tablename__ = "districts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    canonical_domain: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    homepage_url: Mapped[str] = mapped_column(Text)
    cms_type_guess: Mapped[str | None] = mapped_column(String(64), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sources: Mapped[list["Source"]] = relationship(back_populates="district", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    district_id: Mapped[str] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    discovered_from_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    rank_score: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    fetch_status: Mapped[str] = mapped_column(String(32), default="pending")
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_modified_header: Mapped[str | None] = mapped_column(String(255), nullable=True)
    etag: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    snapshot_object_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    district: Mapped["District"] = relationship(back_populates="sources")
    parsed_documents: Mapped[list["ParsedDocument"]] = relationship(back_populates="source", cascade="all, delete-orphan")


class ParsedDocument(Base):
    __tablename__ = "parsed_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    parser_version: Mapped[str] = mapped_column(String(32))
    parse_method: Mapped[str] = mapped_column(String(64))
    school_year_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    extraction_confidence: Mapped[float] = mapped_column(Float)
    metadata_json: Mapped[dict] = mapped_column(json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    source: Mapped["Source"] = relationship(back_populates="parsed_documents")
    event_candidates: Mapped[list["EventCandidate"]] = relationship(back_populates="parsed_document", cascade="all, delete-orphan")


class EventCandidate(Base):
    __tablename__ = "event_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parsed_document_id: Mapped[str] = mapped_column(ForeignKey("parsed_documents.id", ondelete="CASCADE"), index=True)
    raw_text: Mapped[str] = mapped_column(Text)
    raw_date_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    label_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    label_normalized: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status_effect: Mapped[str] = mapped_column(String(64))
    applies_to: Mapped[str] = mapped_column(String(64), default="district_wide")
    confidence: Mapped[float] = mapped_column(Float)
    notes_json: Mapped[dict] = mapped_column(json_type(), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    parsed_document: Mapped["ParsedDocument"] = relationship(back_populates="event_candidates")


class InferenceResult(Base):
    __tablename__ = "inference_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    district_id: Mapped[str] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), index=True)
    target_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(64))
    confidence_score: Mapped[float] = mapped_column(Float)
    confidence_level: Mapped[str] = mapped_column(String(16))
    explanation: Mapped[str] = mapped_column(Text)
    evidence_json: Mapped[list] = mapped_column(json_type(), default=list)
    conflicting_evidence_json: Mapped[list] = mapped_column(json_type(), default=list)
    rationale_json: Mapped[list] = mapped_column(json_type(), default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cache_expires_at: Mapped[datetime] = mapped_column(DateTime)


class ManualOverride(Base):
    __tablename__ = "manual_overrides"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    district_id: Mapped[str] = mapped_column(ForeignKey("districts.id", ondelete="CASCADE"), index=True)
    target_date: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(64))
    explanation: Mapped[str] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(String(255))
    reason: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FetchLog(Base):
    __tablename__ = "fetch_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id: Mapped[str | None] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    request_url: Mapped[str] = mapped_column(Text)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    robots_checked: Mapped[bool] = mapped_column(Boolean, default=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

