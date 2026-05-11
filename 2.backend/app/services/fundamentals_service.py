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


COLUMN_ALIASES = {
    "ticker": "stock_code",
    "total_equity": "equity",
    "total_liabilities": "total_debt",
    "operating_cash_flow": "ocf",
    "operating_income": "ebit",
}


REQUIRED_COLUMNS = {
    "ticker",
    "period",
    "revenue",
    "net_income",
    "total_assets",
    "total_equity",
    "total_liabilities",
    "current_assets",
    "current_liabilities",
    "cash",
    "operating_cash_flow",
    "operating_income",
    "gross_profit",
    "inventory",
}


def _parse_period(period: str) -> tuple[int, int]:
    m = re.fullmatch(r"(202[0-5])Q([1-4])", str(period).strip().upper())
    if not m:
        raise ValueError("period must be in 2020/12..2025/12 format")
    return int(m.group(1)), int(m.group(2))


def upload_quarterly_fundamentals_csv(db: Session, content: bytes) -> dict[str, Any]:
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    df.columns = [c.strip() for c in df.columns]

    cols = set(df.columns)
    missing = REQUIRED_COLUMNS - cols
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.rename(columns=COLUMN_ALIASES)

    created, updated, skipped = 0, 0, 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            stock_code = str(row["stock_code"]).strip().upper()
            sector = str(row.get("sector", "Industrial")).strip()
            period = str(row["period"]).strip().upper()
            year, quarter = _parse_period(period)

            if not stock_code or stock_code.lower() == "nan":
                raise ValueError("stock_code is empty")

            payload = {
                "stock_code": stock_code,
                "sector": sector,
                "year": year,
                "quarter": quarter,
                "period": period,
                "net_income": _to_float(row.get("net_income")),
                "equity": _to_float(row.get("equity")),
                "total_assets": _to_float(row.get("total_assets")),
                "revenue": _to_float(row.get("revenue")),
                "gross_profit": _to_float(row.get("gross_profit")),
                "ebitda": None,
                "ocf": _to_float(row.get("ocf")),
                "capex": None,
                "total_debt": _to_float(row.get("total_debt")),
                "cash": _to_float(row.get("cash")),
                "ebit": _to_float(row.get("ebit")),
                "interest_expense": None,
                "inventory": _to_float(row.get("inventory")),
                "receivables": None,
                "net_working_capital": None,
                "market_cap": None,
                "book_value": None,
                "enterprise_value": None,
                "eps": None,
                "growth_rate": None,
                "current_assets": _to_float(row.get("current_assets")),
                "current_liabilities": _to_float(row.get("current_liabilities")),
                "dividend_per_share": None,
                "price": None,
            }

            existing = (
                db.query(QuarterlyFundamental)
                .filter(
                    QuarterlyFundamental.stock_code == stock_code,
                    QuarterlyFundamental.period == period,
                )
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

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }
