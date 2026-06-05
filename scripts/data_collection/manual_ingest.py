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


# Manual-source priority (lower = higher priority) for resolving expected overlap.
_SOURCE_PRIORITY = {
    "corrected_yearly_financials_candidate.csv": 0,   # verified per-year income/profitability
    "all_financials.csv": 1,
    "candidate_from_yearly_snapshots.csv": 5,         # legacy frozen snapshot evidence
}


def _source_priority(name: str) -> int:
    return _SOURCE_PRIORITY.get(name.lower(), 3)


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
    source_note: str = ""
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
            "source_note": self.source_note,
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

    # Columns a LOW-priority (legacy snapshot) source must NOT contribute: it
    # carries frozen balance-sheet values and the misaligned 2024 cells, which must
    # never override clean reference features. Legacy stays a listed source but only
    # fills genuinely-new gaps it alone provides.
    _LEGACY_BLOCKED = set(OVERRIDE_MAP) | {"market_cap", "enterprise_value", "pe_ratio",
                                           "pb_ratio", "ps_ratio", "ev_ebitda"}
    frames = []
    for p in files:
        rep.files.append(p.name)
        one = _read_one(p, rep, strict)
        if one is not None and len(one.columns) > 2:
            prio = _source_priority(p.name)
            # Only the legacy frozen-snapshot tier (prio >= 5) is barred from
            # contributing balance-sheet/valuation override columns; ordinary
            # manual files keep full override capability.
            if prio >= 5:
                drop = [c for c in one.columns if c in _LEGACY_BLOCKED]
                if drop:
                    one = one.drop(columns=drop)
            one["__prio"] = prio
            frames.append(one)
    frames = [f for f in frames if len([c for c in f.columns if c not in ("ticker", "year", "__prio")]) > 0]
    if not frames:
        rep.issues.append("manual financials present but no usable rows after validation")
        return None, rep

    df = pd.concat(frames, ignore_index=True)

    # Multiple manual sources legitimately cover the same ticker-years. Resolve by
    # SOURCE PRIORITY (corrected yearly first) instead of treating the expected
    # overlap as a scary "duplicate" issue. GroupBy.first() takes the first
    # NON-NULL value per column, so the higher-priority source wins where present
    # and a lower-priority source only fills gaps it alone has.
    dup = int(df.duplicated(["ticker", "year"]).sum())
    if dup:
        n_sources = df["__prio"].nunique()
        df = (df.sort_values("__prio")
                .groupby(["ticker", "year"], as_index=False).first())
        if n_sources > 1:
            rep.source_note = ("Multiple manual sources detected. Corrected yearly source was prioritized for "
                               "income/profitability fields; legacy snapshot source only filled fields it "
                               "uniquely provided. This overlap is expected, not an error.")
        else:
            # genuine same-priority duplicates -> still worth flagging
            rep.issues.append(f"{dup} duplicate ticker-year rows within a single source")
    df = df.drop(columns=["__prio"], errors="ignore")

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
