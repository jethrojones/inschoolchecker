from datetime import date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import District, EventCandidate, InferenceResult, ParsedDocument, Source


@pytest.fixture
def db_session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_district(db_session: Session) -> District:
    district = District(
        name="Example Public Schools",
        canonical_domain="examplek12.org",
        homepage_url="https://www.examplek12.org/",
        cms_type_guess="wordpress",
    )
    db_session.add(district)
    db_session.commit()
    db_session.refresh(district)

    source = Source(
        district_id=district.id,
        url="https://www.examplek12.org/calendar.pdf",
        source_type="pdf_calendar",
        title="2025-2026 District Calendar",
        file_type="application/pdf",
        rank_score=9.5,
        last_fetched_at=datetime.utcnow(),
    )
    db_session.add(source)
    db_session.commit()
    db_session.refresh(source)

    parsed = ParsedDocument(
        source_id=source.id,
        parser_version="1",
        parse_method="pdf_text",
        school_year_text="2025-2026",
        extracted_text="Spring Break March 27-28, 2026",
        extraction_confidence=0.8,
        metadata_json={},
    )
    db_session.add(parsed)
    db_session.commit()
    db_session.refresh(parsed)

    event = EventCandidate(
        parsed_document_id=parsed.id,
        raw_text="Spring Break March 27-28, 2026",
        raw_date_text="March 27-28, 2026",
        start_date=date(2026, 3, 27),
        end_date=date(2026, 3, 28),
        label_raw="Spring Break",
        label_normalized="spring_break",
        status_effect="out_of_school",
        applies_to="district_wide",
        confidence=0.95,
        notes_json={},
    )
    db_session.add(event)
    db_session.commit()

    result = InferenceResult(
        district_id=district.id,
        target_date=date(2026, 3, 27),
        status="out_of_school",
        confidence_score=0.9,
        confidence_level="high",
        explanation="The district calendar shows Spring Break on the target date.",
        evidence_json=[],
        conflicting_evidence_json=[],
        rationale_json=[],
        generated_at=datetime.utcnow(),
        cache_expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db_session.add(result)
    db_session.commit()

    return district
