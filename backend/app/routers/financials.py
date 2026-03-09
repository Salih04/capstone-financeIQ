import io
from typing import Any
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.company import Company
from app.models.financial import FinancialStatement, ComputedMetric
from app.models.user import User
from app.schemas.financial import FinancialStatementCreate, FinancialStatementOut
from app.services.ratio_service import compute_ratios, upsert_computed_metrics

router = APIRouter(prefix="/financials", tags=["financials"])

FLOAT_COLUMNS = [
    "revenue", "net_income", "total_assets", "total_equity", "total_liabilities",
    "current_assets", "current_liabilities", "cash", "operating_cash_flow",
]


@router.post("/import-csv", response_model=dict)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    CSV format expected columns:
    ticker, period, revenue, net_income, total_assets, total_equity,
    total_liabilities, current_assets, current_liabilities, cash, operating_cash_flow
    """
    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    required = {"ticker", "period"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {missing}")

    created = 0
    updated = 0
    errors = []

    for _, row in df.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        period = str(row["period"]).strip()

        company = db.query(Company).filter(Company.ticker == ticker).first()
        if not company:
            errors.append(f"Ticker '{ticker}' not found – skipped.")
            continue

        existing = (
            db.query(FinancialStatement)
            .filter(
                FinancialStatement.company_id == company.id,
                FinancialStatement.period == period,
            )
            .first()
        )

        data: dict[str, Any] = {}
        for col in FLOAT_COLUMNS:
            val = row.get(col)
            data[col] = float(val) if pd.notna(val) else None

        if existing:
            for k, v in data.items():
                setattr(existing, k, v)
            db.commit()
            db.refresh(existing)
            stmt = existing
            updated += 1
        else:
            stmt = FinancialStatement(company_id=company.id, period=period, **data)
            db.add(stmt)
            db.commit()
            db.refresh(stmt)
            created += 1

        # Recalculate and save computed metrics
        ratios = compute_ratios(stmt)
        upsert_computed_metrics(db, company.id, period, ratios)

    return {"created": created, "updated": updated, "errors": errors}
