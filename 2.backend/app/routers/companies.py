from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.analytics import MetricTransition, SectorNormalizedFeature
from app.models.company import Company
from app.models.financial import FinancialStatement, ComputedMetric
from app.models.user import User
from app.schemas.company import CompanyOut
from app.schemas.financial import (
    FinancialStatementOut,
    ComputedMetricOut,
    MetricTransitionOut,
    SectorNormalizedOut,
)
from app.services.kap_financials_service import get_kap_company_tickers


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def search_companies(
    q: str = Query(default="", description="Search by ticker or company name"),
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    kap_tickers = sorted(get_kap_company_tickers(db))

    db_rows = (
        db.query(Company)
        .filter(Company.ticker.in_(kap_tickers))
        .all()
    )

    row_by_ticker = {company.ticker: company for company in db_rows}

    q_lower = q.strip().lower()
    results = []

    for ticker in kap_tickers:
        company = row_by_ticker.get(ticker)

        company_name = company.company_name if company else ticker

        if q_lower:
            if (
                q_lower not in ticker.lower()
                and q_lower not in company_name.lower()
            ):
                continue

        if company:
            results.append(company)
        else:
            results.append(
                CompanyOut(
                    id=0,
                    ticker=ticker,
                    company_name=ticker,
                    sector=None,
                    sector_code=None,
                    description=None,
                    is_active=True,
                )
            )

    return results[:limit]


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")
    return company


@router.get("/{company_id}/financials", response_model=list[FinancialStatementOut])
def get_financials(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(FinancialStatement)
        .filter(FinancialStatement.company_id == company_id)
        .order_by(FinancialStatement.period.desc())
        .all()
    )


@router.get("/{company_id}/metrics", response_model=list[ComputedMetricOut])
def get_metrics(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return (
        db.query(ComputedMetric)
        .filter(ComputedMetric.company_id == company_id)
        .order_by(ComputedMetric.period.desc())
        .all()
    )


@router.get("/{company_id}/transitions", response_model=list[MetricTransitionOut])
def get_transitions(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    return (
        db.query(MetricTransition)
        .filter(MetricTransition.company_id == company_id)
        .order_by(MetricTransition.to_period.desc(), MetricTransition.metric_name)
        .all()
    )


@router.get("/{company_id}/sector-scores", response_model=list[SectorNormalizedOut])
def get_sector_scores(
    company_id: int,
    period: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    query = db.query(SectorNormalizedFeature).filter(
        SectorNormalizedFeature.company_id == company_id
    )

    if period:
        query = query.filter(SectorNormalizedFeature.period == period)

    return (
        query.order_by(
            SectorNormalizedFeature.period.desc(),
            SectorNormalizedFeature.feature_name,
        )
        .all()
    )