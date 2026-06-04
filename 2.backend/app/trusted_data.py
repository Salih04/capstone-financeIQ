"""Trusted yearly dataset contract + conversion.

Single place that defines what the trusted 2020-2025 data IS. Both the
XLSX->CSV converter and the Postgres loader import from here so the schema
can never drift between them.

Trusted sources (and the ONLY accepted financial data):
    3.Datasets/2020stocks.xlsx ... 2025stocks.xlsx

Each file: one row per company, 54 columns, header on the SECOND row (the
first row is a title banner). `Company` holds the BIST ticker. Percentages are
stored as plain numbers (ROE 8.19 == 8.19%), monetary values as raw floats,
no thousands separators. Negatives are real. The year comes from the filename,
never from the data.
"""

from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd

# ---------------------------------------------------------------------------
# Column contract: original XLSX header -> normalized snake_case name.
# The year-specific annual-return column ("Return % (2020-01-02 - ...)") is
# matched separately by regex because its text changes every year.
# ---------------------------------------------------------------------------
COLUMN_MAP: dict[str, str] = {
    "Company": "ticker",
    "Indices": "indices",
    "Price": "price",
    "Daily % Change": "daily_change_pct",
    "Volume": "volume",
    "Return % (Last 1 Week)": "return_1w_pct",
    "Return % (Last 1 Month)": "return_1m_pct",
    "Return % (Last 3 Months)": "return_3m_pct",
    "Return % (Last 6 Months)": "return_6m_pct",
    "Return % (Year-to-Date / YTD)": "return_ytd_pct",
    "Return % (Last 1 Year)": "return_1y_pct",
    "Return % (Last 3 Years)": "return_3y_pct",
    "Return % (Last 5 Years)": "return_5y_pct",
    "Market Capitalization": "market_cap",
    "Enterprise Value (EV)": "enterprise_value",
    "P/E": "pe",
    "P/B": "pb",
    "EV/Sales": "ev_sales",
    "EV/EBITDA": "ev_ebitda",
    "PEG Ratio": "peg",
    "Gross Profit Margin": "gross_margin_pct",
    "EBITDA Margin": "ebitda_margin_pct",
    "Net Profit Margin": "net_margin_pct",
    "Return on Equity (ROE)": "roe_pct",
    "ROIC": "roic_pct",
    "Return on Assets (ROA)": "roa_pct",
    "Working Capital": "working_capital",
    "Net Debt": "net_debt",
    "Net Debt / EBITDA": "net_debt_ebitda",
    "Net Financial Expenses / EBITDA": "net_fin_exp_ebitda",
    "Current Ratio": "current_ratio",
    "Leverage Ratio": "leverage_ratio",
    "Financial Debt Ratio": "financial_debt_ratio",
    "Revenue Growth %": "revenue_growth_pct",
    "Gross Profit Growth %": "gross_profit_growth_pct",
    "EBITDA Growth %": "ebitda_growth_pct",
    "Operating Income Growth %": "operating_income_growth_pct",
    "Net Income Growth %": "net_income_growth_pct",
    "Total Assets": "total_assets",
    "Current Assets": "current_assets",
    "Non-Current Assets": "non_current_assets",
    "Short-Term Liabilities": "short_term_liabilities",
    "Long-Term Liabilities": "long_term_liabilities",
    "Equity": "equity",
    "Revenue": "revenue",
    "Gross Profit": "gross_profit",
    "Operating Income": "operating_income",
    "EBITDA": "ebitda",
    "Net Income": "net_income",
    "Free Cash Flow (FCF)": "free_cash_flow",
    "Cash Flow from Operating Activities": "ocf",
    "Cash Flow from Investing Activities": "icf",
    "Cash Flow from Financing Activities": "fcf_financing",
}

ANNUAL_RETURN_RE = re.compile(r"Return % \(\d{4}-\d{2}-\d{2} - \d{4}-\d{2}-\d{2}\)")
ANNUAL_RETURN_COL = "annual_return_pct"

# Cannot be null for a row to be valid.
REQUIRED_COLUMNS: tuple[str, ...] = ("ticker", "year")

# Columns that are percentages (stored as plain numbers, e.g. 8.19 == 8.19%).
PERCENT_COLUMNS: frozenset[str] = frozenset(
    {
        "daily_change_pct", "return_1w_pct", "return_1m_pct", "return_3m_pct",
        "return_6m_pct", "return_ytd_pct", "return_1y_pct", "return_3y_pct",
        "return_5y_pct", "annual_return_pct", "gross_margin_pct",
        "ebitda_margin_pct", "net_margin_pct", "roe_pct", "roic_pct",
        "roa_pct", "revenue_growth_pct", "gross_profit_growth_pct",
        "ebitda_growth_pct", "operating_income_growth_pct",
        "net_income_growth_pct",
    }
)

# Final, deterministic column order for every emitted CSV.
OUTPUT_COLUMNS: tuple[str, ...] = (
    ("ticker", "year", "indices", "annual_return_pct")
    + tuple(v for v in COLUMN_MAP.values() if v not in ("ticker", "indices"))
)


def _norm_header(name: Any) -> str:
    return unicodedata.normalize("NFKC", str(name)).replace("﻿", "").strip()


def _year_from_filename(path: Path) -> int:
    m = re.match(r"(20\d{2})stocks", path.stem)
    if not m:
        raise ValueError(
            f"Cannot derive year from filename '{path.name}'. "
            "Trusted files must be named like '2024stocks.xlsx'."
        )
    return int(m.group(1))


def _to_number(v: Any) -> float | None:
    """Parse a cell into a float. Returns None for genuinely missing values.

    Never invents a value: blank/NaN/'-'/'N/A' -> None. A real 0 stays 0.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and math.isnan(v):
            return None
        return float(v)

    s = _norm_header(v)
    if s == "" or s.lower() in {"na", "n/a", "nan", "-", "—", "null", "none"}:
        return None

    s = s.replace("%", "").replace("₺", "").replace("TL", "").replace(" ", "")
    # Thousands/decimal separators: TR/EU "1.234.567,89" vs US "1,234,567.89".
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        # Lone comma: decimal if it looks like "12,5", thousands if "1,234".
        if re.fullmatch(r"-?\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")

    s = re.sub(r"[^0-9+\-.eE]", "", s)
    if s in {"", "-", "+", ".", "-.", "+."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def read_trusted_xlsx(path: Path) -> pd.DataFrame:
    """Read one trusted XLSX into a normalized, validated DataFrame.

    Raises ValueError on malformed structure. Does not modify the source file.
    """
    # The banner row is present in some files but not others, so the real
    # header is on row 0 or row 1. Detect by which one yields the 'Company'
    # column rather than assuming.
    raw = pd.read_excel(path, header=0)
    raw.columns = [_norm_header(c) for c in raw.columns]
    if "Company" not in raw.columns:
        raw = pd.read_excel(path, header=1)
        raw.columns = [_norm_header(c) for c in raw.columns]

    annual_col = next((c for c in raw.columns if ANNUAL_RETURN_RE.fullmatch(c)), None)

    rename: dict[str, str] = {}
    for src, dst in COLUMN_MAP.items():
        if src in raw.columns:
            rename[src] = dst
    if annual_col:
        rename[annual_col] = ANNUAL_RETURN_COL

    missing_src = [s for s in COLUMN_MAP if s not in raw.columns]
    if "Company" in missing_src:
        raise ValueError(f"{path.name}: missing required 'Company' column.")

    df = raw.rename(columns=rename)
    df["year"] = _year_from_filename(path)
    df["source_file"] = path.name

    # Drop fully-empty rows (no ticker).
    df["ticker"] = df["ticker"].map(lambda v: _norm_header(v).upper())
    df = df[df["ticker"].astype(bool) & (df["ticker"].str.lower() != "nan")].copy()

    # Coerce every numeric column safely; missing stays NaN (-> empty in CSV).
    for col in df.columns:
        if col in ("ticker", "indices", "source_file"):
            continue
        if col == "year":
            continue
        df[col] = df[col].map(_to_number)

    # Stable column order; only keep known columns + provenance.
    ordered = [c for c in OUTPUT_COLUMNS if c in df.columns] + ["source_file"]
    return df[ordered].reset_index(drop=True)


def validate_frame(df: pd.DataFrame, label: str) -> list[str]:
    """Return a list of validation errors (empty == valid)."""
    errors: list[str] = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"{label}: missing required column '{col}'")
    if errors:
        return errors

    if df["ticker"].isna().any() or (df["ticker"] == "").any():
        errors.append(f"{label}: rows with empty ticker present")

    dup = df.duplicated(subset=["ticker", "year"])
    if dup.any():
        dups = df.loc[dup, ["ticker", "year"]].to_dict("records")
        errors.append(f"{label}: duplicate ticker-year rows: {dups}")

    return errors


def summarize_frame(df: pd.DataFrame) -> dict[str, Any]:
    crit = ["revenue", "net_income", "total_assets", "equity"]
    return {
        "rows": int(len(df)),
        "years": sorted(int(y) for y in df["year"].dropna().unique()),
        "tickers": int(df["ticker"].nunique()),
        "columns": int(df.shape[1]),
        "missing_critical": {
            c: int(df[c].isna().sum()) for c in crit if c in df.columns
        },
    }
