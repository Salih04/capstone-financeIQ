"""Research API — yearly trusted-data scoring + validation (PHASE 2/7/8/10).

All endpoints read the trusted yearly CSV via the research services. No legacy
quarterly/winner tables, no external APIs. Selected period is always a YEAR.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import require_access
from app.models.user import User
from app.services import skeptic_service
from app.services.research import (
    benchmark,
    company,
    data,
    feature_passports,
    feature_registry,
    profit,
    scoring,
    significance,
    validation,
)

router = APIRouter(prefix="/research", tags=["research"])


def _guard_year(year: int) -> None:
    years = data.available_years()
    if year not in years:
        raise HTTPException(422, f"Year {year} not in trusted data. Available: {years}")


@router.get("/years")
def years(_: User | None = Depends(require_access)):
    return {"years": data.available_years(), "supported": list(data.SUPPORTED_YEARS)}


@router.get("/scores")
def scores(year: int = Query(...), _: User | None = Depends(require_access)):
    _guard_year(year)
    return company.year_overview(year)


@router.get("/company")
def company_detail(
    ticker: str = Query(...),
    year: int = Query(...),
    _: User | None = Depends(require_access),
):
    _guard_year(year)
    try:
        return company.company_detail(ticker, year)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.get("/validation")
def validation_all(_: User | None = Depends(require_access)):
    return validation.validate_all()


@router.get("/dashboard")
def dashboard(_: User | None = Depends(require_access)):
    return company.dashboard()


@router.get("/profit-consistency")
def profit_consistency(year: int = Query(...), _: User | None = Depends(require_access)):
    _guard_year(year)
    return profit.profit_consistency(year)


@router.get("/benchmark/status")
def benchmark_status(_: User | None = Depends(require_access)):
    return benchmark.status()


@router.get("/feature-registry")
def registry(_: User | None = Depends(require_access)):
    return {"features": feature_registry.registry_as_dicts()}


@router.get("/feature-passports")
def passports(_: User | None = Depends(require_access)):
    """Serve generated lineage records; never infer missing provenance at request time."""
    try:
        return feature_passports.payload()
    except feature_passports.FeaturePassportsMissing as exc:
        raise HTTPException(503, str(exc))


@router.get("/significance")
def significance_report(_: User | None = Depends(require_access)):
    """Serve committed significance/power evidence; never recompute it at request time."""
    try:
        return significance.payload()
    except significance.SignificanceReportMissing as exc:
        raise HTTPException(503, str(exc))


@router.get("/significance/autopsy")
def autopsy_report(_: User | None = Depends(require_access)):
    """Extend significance evidence with parsed, committed autopsy CSVs."""
    try:
        return significance.autopsy_payload()
    except significance.SignificanceReportMissing as exc:
        raise HTTPException(503, str(exc))


@router.get("/skeptic/{ticker}")
def skeptic_report(ticker: str, _: User | None = Depends(require_access)):
    """Challenge a ticker with cached, committed evidence; never alter its score."""
    try:
        return skeptic_service.skeptic_report(ticker)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
