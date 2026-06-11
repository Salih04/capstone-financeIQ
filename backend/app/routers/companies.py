from fastapi import APIRouter, Depends, HTTPException, Query
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
from app.services.dataset_service import get_dataset_tickers


router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
def search_companies(
    q: str = Query(default="", description="Search by ticker, company name, or sector"),
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    dataset_tickers = set(get_dataset_tickers())

    query = db.query(Company).filter(Company.is_active == True)

    if dataset_tickers:
        query = query.filter(Company.ticker.in_(dataset_tickers))

    q_lower = q.strip().lower()

    if q_lower:
        like = f"%{q_lower}%"
        query = query.filter(
            (Company.ticker.ilike(like))
            | (Company.company_name.ilike(like))
            | (Company.sector.ilike(like))
            | (Company.sector_code.ilike(like))
        )

    return (
        query
        .order_by(Company.ticker.asc())
        .limit(limit)
        .all()
    )


@router.get("/{company_id}", response_model=CompanyOut)
def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .filter(Company.is_active == True)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    return company


@router.get("/{company_id}/financials", response_model=list[FinancialStatementOut])
def get_financials(
    company_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .filter(Company.is_active == True)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

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
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .filter(Company.is_active == True)
        .first()
    )

    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

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
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .filter(Company.is_active == True)
        .first()
    )

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
    company = (
        db.query(Company)
        .filter(Company.id == company_id)
        .filter(Company.is_active == True)
        .first()
    )

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
