"""Research API — yearly trusted-data scoring + validation (PHASE 2/7/8/10).

All endpoints read the trusted yearly CSV via the research services. No legacy
quarterly/winner tables, no external APIs. Selected period is always a YEAR.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.research import (
    benchmark,
    company,
    data,
    feature_registry,
    profit,
    scoring,
    validation,
)

router = APIRouter(prefix="/research", tags=["research"])


def _guard_year(year: int) -> None:
    years = data.available_years()
    if year not in years:
        raise HTTPException(422, f"Year {year} not in trusted data. Available: {years}")


@router.get("/years")
def years(_: User = Depends(get_current_user)):
    return {"years": data.available_years(), "supported": list(data.SUPPORTED_YEARS)}


@router.get("/scores")
def scores(year: int = Query(...), _: User = Depends(get_current_user)):
    _guard_year(year)
    return company.year_overview(year)


@router.get("/company")
def company_detail(
    ticker: str = Query(...),
    year: int = Query(...),
    _: User = Depends(get_current_user),
):
    _guard_year(year)
    try:
        return company.company_detail(ticker, year)
    except ValueError as exc:
        raise HTTPException(404, str(exc))


@router.get("/validation")
def validation_all(_: User = Depends(get_current_user)):
    return validation.validate_all()


@router.get("/dashboard")
def dashboard(_: User = Depends(get_current_user)):
    return company.dashboard()


@router.get("/profit-consistency")
def profit_consistency(year: int = Query(...), _: User = Depends(get_current_user)):
    _guard_year(year)
    return profit.profit_consistency(year)


@router.get("/benchmark/status")
def benchmark_status(_: User = Depends(get_current_user)):
    return benchmark.status()


@router.get("/feature-registry")
def registry(_: User = Depends(get_current_user)):
    return {"features": feature_registry.registry_as_dicts()}
