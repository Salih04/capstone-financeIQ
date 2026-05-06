
from pathlib import Path
import pandas as pd

from app.database import SessionLocal
from app.models.financial import ComputedMetric, FinancialStatement
from app.models.company import Company

DATA_DIR = Path("/app/3.Datasets")


def to_float(v):
    if pd.isna(v):
        return None
    try:
        return float(v)
    except Exception:
        return None

def pct(v):
    value = to_float(v)
    if value is None:
        return None
    return value / 100

def read_dataset(file: Path) -> pd.DataFrame:
    df = pd.read_excel(file)

    if "Company" not in df.columns:
        df = pd.read_excel(file, header=1)

    df.columns = [str(c).strip() for c in df.columns]
    return df


def safe_payload(payload: dict) -> dict:
    return {
        k: v for k, v in payload.items()
        if hasattr(ComputedMetric, k)
    }


def main():
    db = SessionLocal()

    files = sorted(DATA_DIR.glob("*stocks.xlsx"))
    if not files:
        raise RuntimeError(f"No dataset files found in {DATA_DIR}")

    created = 0
    updated = 0
    skipped = 0

    for file in files:
        year = int(file.stem[:4])
        period = f"{year}Q4"

        df = read_dataset(file)

        for _, row in df.iterrows():
            ticker = str(row.get("Company", "")).strip().upper()

            if not ticker or ticker == "COMPANY" or ticker == "NAN":
                skipped += 1
                continue

            company = db.query(Company).filter(
                Company.ticker == ticker,
                Company.is_active == True,
            ).first()

            if not company:
                skipped += 1
                continue            
            revenue = to_float(row.get("Revenue"))
            gross_profit = to_float(row.get("Gross Profit"))
            op_income = to_float(row.get("Operating Income"))
            net_income = to_float(row.get("Net Income"))
            total_assets = to_float(row.get("Total Assets"))
            equity = to_float(row.get("Equity"))
            current_assets = to_float(row.get("Current Assets"))
            current_liabilities = to_float(row.get("Short-Term Liabilities"))
            total_liabilities = None
            long_term_liabilities = to_float(row.get("Long-Term Liabilities"))
            if current_liabilities is not None and long_term_liabilities is not None:
                total_liabilities = current_liabilities + long_term_liabilities

            ocf = to_float(row.get("Cash Flow from Operating Activities"))
            net_debt = to_float(row.get("Net Debt"))
            inventory = to_float(row.get("Inventory"))

            payload = {
                "company_id": company.id,
                "period": period,

                "roe": pct(row.get("Return on Equity (ROE)")),
                "roa": pct(row.get("Return on Assets (ROA)")),
                "net_margin": pct(row.get("Net Profit Margin")),

                "current_ratio": to_float(row.get("Current Ratio")),
                "debt_to_equity": pct(row.get("Leverage Ratio")),
                "debt_to_assets": pct(row.get("Financial Debt Ratio")),
                "ocf_to_debt": to_float(row.get("Net Debt / EBITDA")),
                "operating_margin": (op_income / revenue) if revenue and op_income is not None else None,
                "cash_flow_margin": (ocf / revenue) if revenue and ocf is not None else None,
                "ocf_to_assets": (ocf / total_assets) if total_assets and ocf is not None else None,
                "quick_ratio": ((current_assets - inventory) / current_liabilities) if current_assets is not None and inventory is not None and current_liabilities else None,

            }

            payload = safe_payload(payload)

            existing = db.query(ComputedMetric).filter(
                ComputedMetric.company_id == company.id,
                ComputedMetric.period == period,
            ).first()

            if existing:
                for k, v in payload.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(ComputedMetric(**payload))
                created += 1

            fs_payload = {
                "company_id": company.id,
                "period": period,
                "revenue": revenue,
                "gross_profit": gross_profit,
                "operating_income": op_income,
                "net_income": net_income,
                "total_assets": total_assets,
                "total_equity": equity,
                "current_assets": current_assets,
                "current_liabilities": current_liabilities,
                "total_liabilities": total_liabilities,
                "operating_cash_flow": ocf,
            }

            fs_payload = {
                k: v for k, v in fs_payload.items()
                if hasattr(FinancialStatement, k)
            }

            existing_fs = db.query(FinancialStatement).filter(
                FinancialStatement.company_id == company.id,
                FinancialStatement.period == period,
            ).first()

            if existing_fs:
                for k, v in fs_payload.items():
                    setattr(existing_fs, k, v)
            else:
                db.add(FinancialStatement(**fs_payload))
                
                
            

    db.commit()
    db.close()

    print("Created:", created)
    print("Updated:", updated)
    print("Skipped:", skipped)


if __name__ == "__main__":
    main()