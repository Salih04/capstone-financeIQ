from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models.forecasting import QuarterlyFundamental


def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace("%", "").replace(" ", "")
    if not s:
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    s = re.sub(r"[^0-9+\-.eE]", "", s)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


REQUIRED_COLUMNS = {
    "stock_code",
    "sector",
    "period",
    "net_income",
    "equity",
    "total_assets",
    "revenue",
    "gross_profit",
    "ebitda",
    "ocf",
    "capex",
    "total_debt",
    "cash",
    "ebit",
    "interest_expense",
    "inventory",
    "receivables",
    "net_working_capital",
    "market_cap",
    "book_value",
    "enterprise_value",
    "eps",
    "growth_rate",
    "current_assets",
    "current_liabilities",
    "dividend_per_share",
    "price",
}


def _parse_period(period: str) -> tuple[int, int]:
    m = re.fullmatch(r"(202[3-5])Q([1-4])", str(period).strip().upper())
    if not m:
        raise ValueError("period must be in 2023Q1..2025Q4 format")
    return int(m.group(1)), int(m.group(2))


def upload_quarterly_fundamentals_csv(db: Session, content: bytes) -> dict[str, Any]:
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    cols = {c.strip() for c in df.columns}
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    created, updated, skipped = 0, 0, 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            stock_code = str(row["stock_code"]).strip().upper()
            sector = str(row["sector"]).strip()
            period = str(row["period"]).strip().upper()
            year, quarter = _parse_period(period)
            payload = {
                "stock_code": stock_code,
                "sector": sector,
                "year": year,
                "quarter": quarter,
                "period": period,
                "net_income": _to_float(row["net_income"]),
                "equity": _to_float(row["equity"]),
                "total_assets": _to_float(row["total_assets"]),
                "revenue": _to_float(row["revenue"]),
                "gross_profit": _to_float(row["gross_profit"]),
                "ebitda": _to_float(row["ebitda"]),
                "ocf": _to_float(row["ocf"]),
                "capex": _to_float(row["capex"]),
                "total_debt": _to_float(row["total_debt"]),
                "cash": _to_float(row["cash"]),
                "ebit": _to_float(row["ebit"]),
                "interest_expense": _to_float(row["interest_expense"]),
                "inventory": _to_float(row["inventory"]),
                "receivables": _to_float(row["receivables"]),
                "net_working_capital": _to_float(row["net_working_capital"]),
                "market_cap": _to_float(row["market_cap"]),
                "book_value": _to_float(row["book_value"]),
                "enterprise_value": _to_float(row["enterprise_value"]),
                "eps": _to_float(row["eps"]),
                "growth_rate": _to_float(row["growth_rate"]),
                "current_assets": _to_float(row["current_assets"]),
                "current_liabilities": _to_float(row["current_liabilities"]),
                "dividend_per_share": _to_float(row["dividend_per_share"]),
                "price": _to_float(row["price"]),
            }
            existing = (
                db.query(QuarterlyFundamental)
                .filter(QuarterlyFundamental.stock_code == stock_code, QuarterlyFundamental.period == period)
                .first()
            )
            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(QuarterlyFundamental(**payload))
                created += 1
        except Exception as exc:
            skipped += 1
            errors.append(f"row {idx + 1}: {exc}")

    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "errors": errors}
