from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models.forecasting import QuarterlyFundamental


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "CLEANED_Financial"


COLUMN_ALIASES = {
    "ticker": "stock_code",
    "stock_code": "stock_code",
    "period": "period",
    "revenue": "revenue",
    "net_income": "net_income",
    "total_assets": "total_assets",
    "total_equity": "equity",
    "equity": "equity",
    "total_liabilities": "total_debt",
    "operating_cash_flow": "ocf",
    "ocf": "ocf",
    "operating_income": "ebit",
    "ebit": "ebit",
    "gross_profit": "gross_profit",
    "inventory": "inventory",
    "current_assets": "current_assets",
    "current_liabilities": "current_liabilities",
    "cash": "cash",
}


def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("ı", "i")
        for c in df.columns
    ]
    return df.rename(columns=COLUMN_ALIASES)


def parse_period(period: str):
    period = str(period).strip().upper()
    year = int(period[:4])
    quarter = int(period[-1])
    return year, quarter, period


def to_float(v):
    if pd.isna(v):
        return None
    try:
        return float(v)
    except Exception:
        return None


def main():
    db = SessionLocal()

    created = 0
    updated = 0
    skipped = 0

    files = sorted(DATA_DIR.glob("*.xlsx"))

    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {DATA_DIR}")

    for file in files:
        ticker = file.stem.upper()

        try:
            df = pd.read_excel(file)
            df = clean_columns(df)

            if "period" not in df.columns:
                print(f"SKIP {ticker}: missing period column")
                skipped += 1
                continue

            if "stock_code" not in df.columns:
                df["stock_code"] = ticker

            if "sector" not in df.columns:
                df["sector"] = "Industrial"

            for _, row in df.iterrows():
                try:
                    stock_code = str(row.get("stock_code", ticker)).strip().upper()
                    sector = str(row.get("sector", "Industrial")).strip()
                    year, quarter, period = parse_period(row["period"])

                    payload = {
                        "stock_code": stock_code,
                        "sector": sector,
                        "year": year,
                        "quarter": quarter,
                        "period": period,

                        "net_income": to_float(row.get("net_income")),
                        "equity": to_float(row.get("equity")),
                        "total_assets": to_float(row.get("total_assets")),
                        "revenue": to_float(row.get("revenue")),
                        "gross_profit": to_float(row.get("gross_profit")),

                        "ebitda": to_float(row.get("ebitda")),
                        "ocf": to_float(row.get("ocf")),
                        "capex": to_float(row.get("capex")),
                        "total_debt": to_float(row.get("total_debt")),
                        "cash": to_float(row.get("cash")),
                        "ebit": to_float(row.get("ebit")),
                        "interest_expense": to_float(row.get("interest_expense")),

                        "inventory": to_float(row.get("inventory")),
                        "receivables": to_float(row.get("receivables")),
                        "net_working_capital": to_float(row.get("net_working_capital")),

                        "market_cap": to_float(row.get("market_cap")),
                        "book_value": to_float(row.get("book_value")),
                        "enterprise_value": to_float(row.get("enterprise_value")),
                        "eps": to_float(row.get("eps")),
                        "growth_rate": to_float(row.get("growth_rate")),

                        "current_assets": to_float(row.get("current_assets")),
                        "current_liabilities": to_float(row.get("current_liabilities")),
                        "dividend_per_share": to_float(row.get("dividend_per_share")),
                        "price": to_float(row.get("price")),
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
                    db.rollback()
                    skipped += 1
                    print(f"SKIP row in {ticker}: {exc}")

            db.commit()
            print(f"Imported {ticker}")

        except Exception as exc:
            db.rollback()
            skipped += 1
            print(f"FAILED {ticker}: {exc}")

    db.close()

    print({
        "created": created,
        "updated": updated,
        "skipped": skipped,
    })


if __name__ == "__main__":
    main()