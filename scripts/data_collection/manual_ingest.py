"""Manual real financial-history ingestion (T -> T+1 pipeline).

Reads per-ticker files (data/trusted_raw/financials/<TICKER>.csv) and/or a
combined data/trusted_raw/financials/all_financials.csv, validates them
strictly, and returns a canonical one-row-per-ticker-year frame to merge into
the modeling dataset.

Honesty rules:
  * No fabrication, no imputation. Missing manual values stay NaN.
  * Non-numeric financial cells are a hard validation error (likely a misaligned
    file), never silently coerced to NaN/0.
  * Frozen snapshot values are NEVER used to fill years the user did not supply;
    a manually-supplied column is real where present and NaN elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# Canonical manual columns (alias -> canonical). Aliases are matched
# case-insensitively after stripping spaces and non-alphanumerics to "_".
_CANON: dict[str, list[str]] = {
    # income statement
    "revenue": ["revenue", "sales", "net_sales"],
    "gross_profit": ["gross_profit"],
    "operating_income": ["operating_income", "operating_profit", "ebit"],
    "ebitda": ["ebitda"],
    "net_income": ["net_income", "net_profit"],
    # margins / profitability
    "gross_margin": ["gross_margin", "gross_profit_margin"],
    "operating_margin": ["operating_margin"],
    "ebitda_margin": ["ebitda_margin"],
    "net_margin": ["net_margin", "net_profit_margin"],
    "roe": ["roe", "return_on_equity"],
    "roa": ["roa", "return_on_assets"],
    # balance sheet
    "total_assets": ["total_assets"],
    "current_assets": ["current_assets"],
    "non_current_assets": ["non_current_assets"],
    "total_liabilities": ["total_liabilities"],
    "short_term_liabilities": ["short_term_liabilities", "current_liabilities"],
    "long_term_liabilities": ["long_term_liabilities", "non_current_liabilities"],
    "total_equity": ["total_equity", "equity", "shareholders_equity"],
    "working_capital": ["working_capital"],
    "net_debt": ["net_debt"],
    # valuation
    "market_cap": ["market_cap", "market_capitalization"],
    "enterprise_value": ["enterprise_value", "ev"],
    "pe_ratio": ["pe_ratio", "pe", "p_e"],
    "pb_ratio": ["pb_ratio", "pb", "p_b"],
    "ps_ratio": ["ps_ratio", "ps", "p_s", "ev_sales"],
    "ev_ebitda": ["ev_ebitda"],
    # momentum / trading
    "return_3m_pct": ["return_3m_pct", "return_3m"],
    "return_6m_pct": ["return_6m_pct", "return_6m"],
    "return_12m_pct": ["return_12m_pct", "return_12m", "return_1y_pct"],
    "avg_volume": ["avg_volume", "average_volume"],
    "turnover_ratio": ["turnover_ratio"],
}
# Manual columns that, when present, override an existing base column.
OVERRIDE_MAP = {
    "total_equity": "equity",
    "total_assets": "total_assets",
    "current_assets": "current_assets",
    "non_current_assets": "non_current_assets",
    "short_term_liabilities": "short_term_liabilities",
    "long_term_liabilities": "long_term_liabilities",
    "working_capital": "working_capital",
    "net_debt": "net_debt",
}
MANUAL_NUMERIC = set(_CANON.keys())
_ALIAS_TO_CANON = {a: c for c, al in _CANON.items() for a in al}


def _norm(name: str) -> str:
    s = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(name).strip())
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


@dataclass
class ManualReport:
    files: list[str] = field(default_factory=list)
    rows_ingested: int = 0
    coverage: dict = field(default_factory=dict)        # year -> ticker count
    columns_ingested: list[str] = field(default_factory=list)
    unknown_columns: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    misaligned_columns: list[str] = field(default_factory=list)
    all_null_columns: list[str] = field(default_factory=list)
    present: bool = False

    def as_dict(self) -> dict:
        return {
            "files": self.files,
            "rows_ingested": self.rows_ingested,
            "coverage_by_year": self.coverage,
            "columns_ingested": self.columns_ingested,
            "unknown_columns_ignored": self.unknown_columns,
            "misaligned_columns_rejected": self.misaligned_columns,
            "all_null_columns_rejected": self.all_null_columns,
            "issues": self.issues,
            "present": self.present,
        }


def _coerce_numeric(series: pd.Series) -> tuple[pd.Series, float]:
    """Return (numeric series, fraction of non-null cells that failed to parse)."""
    raw = series.copy()
    num = pd.to_numeric(
        raw.astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )
    nonnull = raw.notna() & (raw.astype(str).str.strip() != "")
    failed = int((nonnull & num.isna()).sum())
    denom = int(nonnull.sum()) or 1
    return num, failed / denom


def _read_one(path: Path, rep: ManualReport, strict: bool) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(path, comment="#")
    except Exception as exc:
        rep.issues.append(f"{path.name}: malformed CSV ({exc})")
        return None
    if df.empty:
        rep.issues.append(f"{path.name}: empty file")
        return None

    df.columns = [_norm(c) for c in df.columns]
    is_combined = path.name.lower() == "all_financials.csv"

    # ticker
    if "ticker" not in df.columns:
        if is_combined:
            rep.issues.append("all_financials.csv: missing required 'ticker' column")
            return None
        df["ticker"] = path.stem.upper()  # infer from filename
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    # year
    if "year" not in df.columns:
        rep.issues.append(f"{path.name}: missing required 'year' column")
        return None
    yr = pd.to_numeric(df["year"], errors="coerce")
    if yr.isna().any() or not yr.dropna().between(1990, 2100).all():
        rep.issues.append(f"{path.name}: invalid/non-numeric year values (possible column misalignment)")
        if strict:
            return None
    df["year"] = yr.astype("Int64")
    df = df.dropna(subset=["year"]).copy()
    df["year"] = df["year"].astype(int)

    # map known columns, collect unknowns
    out = pd.DataFrame({"ticker": df["ticker"], "year": df["year"]})
    for col in df.columns:
        if col in ("ticker", "year"):
            continue
        canon = _ALIAS_TO_CANON.get(col)
        if not canon:
            if col not in rep.unknown_columns:
                rep.unknown_columns.append(col)
            continue
        num, fail_frac = _coerce_numeric(df[col])
        if fail_frac > 0.5:
            # most cells non-numeric -> suspected misalignment, reject column
            if canon not in rep.misaligned_columns:
                rep.misaligned_columns.append(canon)
            msg = f"{path.name}: column '{col}'->'{canon}' {fail_frac:.0%} non-numeric (misalignment?)"
            rep.issues.append(msg)
            if strict:
                continue
            continue
        out[canon] = num

    # duplicate ticker-year within file
    dup = out.duplicated(["ticker", "year"]).sum()
    if dup:
        rep.issues.append(f"{path.name}: {dup} duplicate ticker-year rows")
        out = out.drop_duplicates(["ticker", "year"], keep="last")
    return out


def load_manual(
    financials_dir: Path,
    known_tickers: set[str] | None = None,
    strict: bool = False,
    allow_partial: bool = True,
) -> tuple[pd.DataFrame | None, ManualReport]:
    rep = ManualReport()
    if not financials_dir.is_dir():
        return None, rep
    files = sorted(p for p in financials_dir.glob("*.csv") if "template" not in p.parts[-1].lower())
    files = [p for p in files if p.parent.name == "financials"]
    if not files:
        return None, rep

    frames = []
    for p in files:
        rep.files.append(p.name)
        one = _read_one(p, rep, strict)
        if one is not None and len(one.columns) > 2:
            frames.append(one)
    if not frames:
        rep.issues.append("manual financials present but no usable rows after validation")
        return None, rep

    df = pd.concat(frames, ignore_index=True)

    # duplicate ticker-year across files
    dup = df.duplicated(["ticker", "year"]).sum()
    if dup:
        rep.issues.append(f"{dup} duplicate ticker-year rows across manual files")
        df = df.drop_duplicates(["ticker", "year"], keep="last")

    # unknown tickers
    if known_tickers:
        unknown = sorted(set(df["ticker"]) - known_tickers)
        if unknown:
            rep.issues.append(f"unknown tickers not in universe: {unknown}")

    # drop all-null manual columns
    manual_cols = [c for c in df.columns if c not in ("ticker", "year")]
    for c in manual_cols:
        if df[c].isna().all():
            rep.all_null_columns.append(c)
    df = df.drop(columns=rep.all_null_columns, errors="ignore")

    rep.present = True
    rep.rows_ingested = int(len(df))
    rep.columns_ingested = [c for c in df.columns if c not in ("ticker", "year")]
    rep.coverage = df.groupby("year")["ticker"].nunique().to_dict()
    return df, rep
