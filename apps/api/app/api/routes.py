from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    AdminResultSummary,
    CheckRequest,
    CheckResponse,
    DiscoverRequest,
    DiscoverResponse,
    DistrictResponse,
    OverrideRequest,
    ReparseRequest,
    SourceSummary,
)
from app.services.checker import (
    create_manual_override,
    get_cached_or_fresh_result,
    get_district_or_404,
    list_admin_results,
    list_sources_for_district,
    reparse_sources,
    run_discovery,
)

router = APIRouter(prefix="/api")


@router.post("/check", response_model=CheckResponse)
def check_district(payload: CheckRequest, db: Session = Depends(get_db)) -> CheckResponse:
    return get_cached_or_fresh_result(db, payload)


@router.post("/districts/discover", response_model=DiscoverResponse)
def discover_district(payload: DiscoverRequest, db: Session = Depends(get_db)) -> DiscoverResponse:
    return run_discovery(db, payload.district_url)


@router.get("/districts/{district_id}", response_model=DistrictResponse)
def get_district(district_id: str, db: Session = Depends(get_db)) -> DistrictResponse:
    return get_district_or_404(db, district_id)


@router.get("/districts/{district_id}/sources", response_model=list[SourceSummary])
def get_sources(district_id: str, db: Session = Depends(get_db)) -> list[SourceSummary]:
    return list_sources_for_district(db, district_id)


@router.get("/districts/{district_id}/results", response_model=CheckResponse)
def get_result(district_id: str, date_value: date = Query(..., alias="date"), db: Session = Depends(get_db)) -> CheckResponse:
    district = get_district_or_404(db, district_id)
    return get_cached_or_fresh_result(db, CheckRequest(district_url=district.homepage_url, target_date=date_value))


@router.get("/admin/results", response_model=list[AdminResultSummary])
def admin_results(
    confidence_level: str | None = None,
    conflicts_only: bool = False,
    db: Session = Depends(get_db),
) -> list[AdminResultSummary]:
    return list_admin_results(db, confidence_level=confidence_level, conflicts_only=conflicts_only)


@router.post("/admin/overrides", response_model=CheckResponse)
def create_override(payload: OverrideRequest, db: Session = Depends(get_db)) -> CheckResponse:
    return create_manual_override(db, payload)


@router.post("/admin/reparse")
def reparse(payload: ReparseRequest, db: Session = Depends(get_db)) -> dict:
    if not payload.district_id and not payload.source_id:
        raise HTTPException(status_code=400, detail="district_id or source_id is required")
    return reparse_sources(db, payload)

