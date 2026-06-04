
import re
from pathlib import Path
import pandas as pd

from app.database import SessionLocal
from app.models.financial import ComputedMetric, FinancialStatement, StockReturn
from app.models.company import Company
from app.models.forecasting import QuarterlyFundamental, WinnerCohortRow

DATA_DIR = Path("/app/3.Datasets")

# Column name that varies by year, e.g. "Return % (2025-01-02 - 2025-12-31)"
_ANNUAL_RETURN_PATTERN = re.compile(r"Return % \(\d{4}-\d{2}-\d{2} - \d{4}-\d{2}-\d{2}\)")


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


def safe_payload(payload: dict, model_class) -> dict:
    return {
        k: v for k, v in payload.items()
        if hasattr(model_class, k)
    }


def _find_annual_return_col(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if _ANNUAL_RETURN_PATTERN.match(col):
            return col
    return None


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
        period = f"{year}/12"

        df = read_dataset(file)
        annual_return_col = _find_annual_return_col(df)

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

            # ── Core financial statement fields ────────────────────────────
            revenue = to_float(row.get("Revenue"))
            gross_profit = to_float(row.get("Gross Profit"))
            op_income = to_float(row.get("Operating Income"))
            net_income = to_float(row.get("Net Income"))
            total_assets = to_float(row.get("Total Assets"))
            equity = to_float(row.get("Equity"))
            current_assets = to_float(row.get("Current Assets"))
            current_liabilities = to_float(row.get("Short-Term Liabilities"))
            long_term_liabilities = to_float(row.get("Long-Term Liabilities"))
            total_liabilities = None
            if current_liabilities is not None and long_term_liabilities is not None:
                total_liabilities = current_liabilities + long_term_liabilities

            ocf = to_float(row.get("Cash Flow from Operating Activities"))
            net_debt = to_float(row.get("Net Debt"))
            inventory = to_float(row.get("Inventory"))

            # ── Core computed metrics (scoring uses these 12) ──────────────
            metric_payload = {
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
                "quick_ratio": (
                    (current_assets - inventory) / current_liabilities
                    if current_assets is not None and inventory is not None and current_liabilities
                    else None
                ),

                # ── Extended metrics (analytics/display, not used in scoring weights) ──
                "gross_profit_margin": pct(row.get("Gross Profit Margin")),
                "ebitda_margin": pct(row.get("EBITDA Margin")),
                "roic": pct(row.get("ROIC")),
                "revenue_growth": pct(row.get("Revenue Growth %")),
                "ebitda_growth": pct(row.get("EBITDA Growth %")),
                "net_income_growth": pct(row.get("Net Income Growth %")),
                "pe_ratio": to_float(row.get("P/E")),
                "pb_ratio": to_float(row.get("P/B")),
                "ev_ebitda": to_float(row.get("EV/EBITDA")),
                "ev_sales": to_float(row.get("EV/Sales")),
                "peg_ratio": to_float(row.get("PEG Ratio")),
                "working_capital": to_float(row.get("Working Capital")),
            }

            metric_payload = safe_payload(metric_payload, ComputedMetric)

            existing = db.query(ComputedMetric).filter(
                ComputedMetric.company_id == company.id,
                ComputedMetric.period == period,
            ).first()

            if existing:
                for k, v in metric_payload.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(ComputedMetric(**metric_payload))
                created += 1

            # ── Financial statement ────────────────────────────────────────
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
            fs_payload = safe_payload(fs_payload, FinancialStatement)

            existing_fs = db.query(FinancialStatement).filter(
                FinancialStatement.company_id == company.id,
                FinancialStatement.period == period,
            ).first()

            if existing_fs:
                for k, v in fs_payload.items():
                    setattr(existing_fs, k, v)
            else:
                db.add(FinancialStatement(**fs_payload))

            # ── Stock return & market data ─────────────────────────────────
            ret_payload = {
                "company_id": company.id,
                "period": period,
                "annual_return": to_float(row.get(annual_return_col)) if annual_return_col else None,
                "return_1w": to_float(row.get("Return % (Last 1 Week)")),
                "return_1m": to_float(row.get("Return % (Last 1 Month)")),
                "return_3m": to_float(row.get("Return % (Last 3 Months)")),
                "return_6m": to_float(row.get("Return % (Last 6 Months)")),
                "return_ytd": to_float(row.get("Return % (Year-to-Date / YTD)")),
                "return_1y": to_float(row.get("Return % (Last 1 Year)")),
                "return_3y": to_float(row.get("Return % (Last 3 Years)")),
                "return_5y": to_float(row.get("Return % (Last 5 Years)")),
                "price": to_float(row.get("Price")),
                "market_cap": to_float(row.get("Market Capitalization")),
                "enterprise_value": to_float(row.get("Enterprise Value (EV)")),
            }
            ret_payload = safe_payload(ret_payload, StockReturn)

            existing_ret = db.query(StockReturn).filter(
                StockReturn.company_id == company.id,
                StockReturn.period == period,
            ).first()

            if existing_ret:
                for k, v in ret_payload.items():
                    setattr(existing_ret, k, v)
            else:
                db.add(StockReturn(**ret_payload))

            # ── QuarterlyFundamental (required by multi-model training) ────
            ebitda = to_float(row.get("EBITDA"))
            qf_payload = {
                "stock_code": company.ticker,
                "sector": company.sector or "",
                "year": year,
                "quarter": 4,
                "period": period,
                "net_income": net_income,
                "equity": equity,
                "total_assets": total_assets,
                "revenue": revenue,
                "gross_profit": gross_profit,
                "ebitda": ebitda,
                "ocf": ocf,
                "market_cap": to_float(row.get("Market Capitalization")),
                "enterprise_value": to_float(row.get("Enterprise Value (EV)")),
                "price": to_float(row.get("Price")),
                "current_assets": current_assets,
                "current_liabilities": current_liabilities,
            }
            qf_payload = {k: v for k, v in qf_payload.items() if hasattr(QuarterlyFundamental, k)}

            existing_qf = db.query(QuarterlyFundamental).filter(
                QuarterlyFundamental.stock_code == company.ticker,
                QuarterlyFundamental.period == period,
            ).first()

            if existing_qf:
                for k, v in qf_payload.items():
                    setattr(existing_qf, k, v)
            else:
                db.add(QuarterlyFundamental(**qf_payload))

            # ── WinnerCohortRow (return labels for multi-model training) ───
            return_1y_val = to_float(row.get("Return % (Last 1 Year)"))
            wr_payload = {
                "source_file": file.name,
                "year": year,
                "sector": company.sector or "",
                "stock_code": company.ticker,
                "period_return": return_1y_val,
                "price": to_float(row.get("Price")),
                "return_1w": to_float(row.get("Return % (Last 1 Week)")),
                "return_1m": to_float(row.get("Return % (Last 1 Month)")),
                "return_3m": to_float(row.get("Return % (Last 3 Months)")),
                "return_6m": to_float(row.get("Return % (Last 6 Months)")),
                "return_ytd": to_float(row.get("Return % (Year-to-Date / YTD)")),
                "return_1y": return_1y_val,
                "return_3y": to_float(row.get("Return % (Last 3 Years)")),
                "return_5y": to_float(row.get("Return % (Last 5 Years)")),
            }
            wr_payload = {k: v for k, v in wr_payload.items() if hasattr(WinnerCohortRow, k)}

            existing_wr = db.query(WinnerCohortRow).filter(
                WinnerCohortRow.year == year,
                WinnerCohortRow.stock_code == company.ticker,
            ).first()

            if existing_wr:
                for k, v in wr_payload.items():
                    setattr(existing_wr, k, v)
            else:
                db.add(WinnerCohortRow(**wr_payload))

    db.commit()
    db.close()

    print("Metrics created:", created)
    print("Metrics updated:", updated)
    print("Skipped:", skipped)


if __name__ == "__main__":
    main()
