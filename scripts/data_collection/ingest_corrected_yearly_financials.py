"""Ingest the CORRECTED yearly financial XLSX files as verified manual history.

Source: data/trusted_raw/financials_corrected_yearly/{2020..2025}stocks.xlsx,
sheet `clean_data`, 40 tickers/year.

Unlike the old frozen exports, the income-statement / profitability fields in
these files genuinely VARY per year and are accepted as real per-year history.
Valuation fields (pe, pb, ev_ebitda, market_capitalization, enterprise_value)
remain a frozen snapshot and are rejected. Leakage fields (price, returns,
volume) are never exported. The 2024 file has a known column-misalignment in the
balance-sheet / ratio / growth block; affected cells are detected and rejected
(never poured into the candidate) rather than poisoning the dataset.

Honesty rules: no fabrication, no imputation. A cell that fails validation
becomes NaN (and is counted), never a guessed value.

Writes:
  data/trusted_raw/financials/corrected_yearly_financials_candidate.csv
  data/trusted_clean/corrected_yearly_ingestion_report.json
  data/trusted_clean/corrected_yearly_ingestion_report.md

Run: PYTHONPATH=. python -m scripts.data_collection.ingest_corrected_yearly_financials
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = REPO_ROOT / "data" / "trusted_raw" / "financials_corrected_yearly"
OUT_CSV = REPO_ROOT / "data" / "trusted_raw" / "financials" / "corrected_yearly_financials_candidate.csv"
REPORT_JSON = REPO_ROOT / "data" / "trusted_clean" / "corrected_yearly_ingestion_report.json"
REPORT_MD = REPO_ROOT / "data" / "trusted_clean" / "corrected_yearly_ingestion_report.md"

SHEET = "clean_data"
YEARS = list(range(2020, 2026))
EXPECTED_TICKERS = 40

# Source column -> canonical alias recognised by manual_ingest._CANON.
# Only income-statement + profitability/margin fields are CANDIDATES for acceptance.
INCOME_FIELDS = {
    "revenue": "revenue",
    "gross_profit": "gross_profit",
    "operating_income": "operating_income",
    "ebitda": "ebitda",
    "net_income": "net_income",
}
MARGIN_FIELDS = {
    "gross_profit_margin": "gross_profit_margin",
    "ebitda_margin": "ebitda_margin",
    "net_profit_margin": "net_profit_margin",
    "roe": "roe",
    "roa": "roa",
}
# Valuation: theoretically valuable but frozen here -> rejected, reported.
VALUATION_FIELDS = ("pe", "pb", "ev_ebitda", "ev_sales", "peg_ratio",
                    "market_capitalization", "enterprise_value")
# Leakage: never exported.
LEAKAGE_FIELDS = ("price", "period_return", "day_return", "volume", "return_1w",
                  "return_1m", "return_3m", "return_6m", "return_ytd",
                  "return_1y", "return_3y", "return_5y")
# Balance-sheet / ratio / growth block that the 2024 file misaligns.
ALIGN_CHECK_FIELDS = ("total_assets", "current_assets", "non_current_assets",
                      "short_term_liabilities", "long_term_liabilities", "equity",
                      "working_capital", "net_debt", "current_ratio", "leverage_ratio",
                      "financial_debt_ratio", "revenue_growth", "gross_profit_growth",
                      "ebitda_growth", "operating_income_growth", "net_income_growth")

FROZEN_FRAC_REJECT = 0.5    # reject a candidate column if >=50% of tickers never vary
MARGIN_ABS_LIMIT = 300.0    # |margin/roe/roa| beyond this looks like a magnitude, not a ratio
MISALIGN_MIN_RATIO = 0.05   # money cell < 5% of a ticker's median money scale => suspected ratio leak
REQUIRED_SOURCE_COLUMNS = {"stock_code", *INCOME_FIELDS, *MARGIN_FIELDS}


def _validate_source_frame(df: pd.DataFrame, filename: str) -> pd.DataFrame:
    """Reject malformed manual workbooks before any values enter the candidate."""
    normalized = [str(c).strip().lower() for c in df.columns]
    duplicate_headers = sorted({c for c in normalized if normalized.count(c) > 1})
    if duplicate_headers:
        raise ValueError(
            f"{filename}: malformed header; duplicate column name(s): {duplicate_headers}"
        )
    df = df.copy()
    df.columns = normalized

    missing = sorted(REQUIRED_SOURCE_COLUMNS - set(df.columns))
    if missing:
        raise ValueError(
            f"{filename}: malformed header; missing required column(s): {missing}. "
            "Expected stock_code plus the corrected income/profitability fields."
        )

    raw_tickers = df["stock_code"]
    blank = raw_tickers.isna() | raw_tickers.astype(str).str.strip().eq("")
    tickers = raw_tickers.astype(str).str.upper().str.strip()
    duplicate_count = int(tickers[~blank].duplicated().sum())
    unique_count = int(tickers[~blank].nunique())
    if len(df) != EXPECTED_TICKERS or unique_count != EXPECTED_TICKERS or blank.any() or duplicate_count:
        raise ValueError(
            f"{filename}: malformed shape; expected exactly {EXPECTED_TICKERS} rows with "
            f"{EXPECTED_TICKERS} unique non-empty stock_code values, found {len(df)} rows, "
            f"{unique_count} unique tickers, {int(blank.sum())} blank ticker(s), and "
            f"{duplicate_count} duplicate ticker row(s)."
        )
    return df


def _load_all() -> tuple[pd.DataFrame, dict]:
    frames, coverage, issues = [], {}, []
    for y in YEARS:
        f = SRC_DIR / f"{y}stocks.xlsx"
        if not f.is_file():
            issues.append(f"missing source file: {f.name}")
            continue
        df = pd.read_excel(f, sheet_name=SHEET)
        df = _validate_source_frame(df, f.name)
        df["ticker"] = df["stock_code"].astype(str).str.upper().str.strip()
        df["year"] = y
        df["__source_file"] = f.name
        n = df["ticker"].nunique()
        coverage[y] = int(n)
        frames.append(df)
    if not frames:
        raise SystemExit("no corrected yearly files found")
    return pd.concat(frames, ignore_index=True), {"coverage": coverage, "issues": issues}


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace("%", "", regex=False)
                         .str.replace(",", "", regex=False).str.strip(), errors="coerce")


def _frozen_ticker_count(df: pd.DataFrame, col: str) -> int:
    g = df.groupby("ticker")[col]
    return int((g.nunique(dropna=True) <= 1).sum())


def _detect_2024_misalignment(df: pd.DataFrame) -> dict:
    """Flag cells in the 2024 balance-sheet/ratio/growth block whose scale is wrong.

    A money/magnitude field carrying a tiny ratio-like value, or a ratio field
    carrying a balance-sheet-magnitude value, is evidence of the documented
    right-shift in the 2024 export.
    """
    evidence = {}
    for col in ALIGN_CHECK_FIELDS:
        if col not in df.columns:
            continue
        vals = _num(df[col])
        per_ticker_med = df.assign(_v=vals).groupby("ticker")["_v"].transform(
            lambda s: s[df.loc[s.index, "year"] != 2024].abs().median())
        is2024 = df["year"] == 2024
        v2024 = vals[is2024]
        med = per_ticker_med[is2024]
        # money-magnitude columns: a 2024 cell that collapses to <5% of the ticker's
        # own non-2024 magnitude (e.g. a ratio sitting where assets belong)
        ratio_like = (med > 1e6) & (v2024.abs() < MISALIGN_MIN_RATIO * med)
        # ratio columns: a 2024 cell that explodes to a balance-sheet magnitude
        magnitude_like = (med.abs() < 1e3) & (v2024.abs() > 1e6)
        bad = int((ratio_like | magnitude_like).sum())
        if bad:
            evidence[col] = bad
    return evidence


def ingest() -> dict:
    df, meta = _load_all()
    issues = list(meta["issues"])
    misalign = _detect_2024_misalignment(df)

    accepted: dict[str, dict] = {}
    rejected: dict[str, dict] = {}
    frozen_valuation: dict[str, dict] = {}

    def col_meta(col, status, reason=""):
        return {"source_file": "corrected_yearly/*.xlsx",
                "status": status, "rejection_reason": reason,
                "years_covered": YEARS,
                "frozen_ticker_count": _frozen_ticker_count(df, col) if col in df.columns else None}

    # 1) leakage fields: never exported
    for col in LEAKAGE_FIELDS:
        if col in df.columns:
            rejected[col] = col_meta(col, "rejected", "leakage_field")

    # 2) valuation fields: frozen snapshot -> rejected, reported separately
    for col in VALUATION_FIELDS:
        if col not in df.columns:
            continue
        fc = _frozen_ticker_count(df, col)
        if fc >= FROZEN_FRAC_REJECT * EXPECTED_TICKERS:
            frozen_valuation[col] = col_meta(col, "rejected", "frozen_snapshot")
        else:
            rejected[col] = col_meta(col, "rejected", "valuation_excluded")

    out = pd.DataFrame({"ticker": df["ticker"], "year": df["year"]})

    # 3) income (money) fields
    for col, canon in INCOME_FIELDS.items():
        if col not in df.columns:
            rejected[canon] = col_meta(col, "rejected", "absent"); continue
        vals = _num(df[col]).copy()
        m = col_meta(col, "", "")
        if vals.isna().all():
            rejected[canon] = {**m, "status": "rejected", "rejection_reason": "all_null"}; continue
        # null 2024 cells that look misaligned (ratio sitting in a money field)
        per_med = df.assign(_v=vals).groupby("ticker")["_v"].transform(
            lambda s: s[df.loc[s.index, "year"] != 2024].abs().median())
        bad24 = (df["year"] == 2024) & (per_med > 1e6) & (vals.abs() < MISALIGN_MIN_RATIO * per_med)
        nbad = int(bad24.sum())
        if nbad:
            vals = vals.mask(bad24)
        fc = _frozen_ticker_count(df, col)
        if fc >= FROZEN_FRAC_REJECT * EXPECTED_TICKERS:
            rejected[canon] = {**m, "status": "rejected", "rejection_reason": "frozen_snapshot",
                               "frozen_ticker_count": fc}; continue
        out[canon] = vals
        accepted[canon] = {**m, "status": "accepted", "rejection_reason": "",
                           "frozen_ticker_count": fc, "misaligned_cells": nbad, "kind": "money"}

    # 4) margin / profitability fields
    for col, canon in MARGIN_FIELDS.items():
        if col not in df.columns:
            rejected[canon] = col_meta(col, "rejected", "absent"); continue
        vals = _num(df[col]).copy()
        if vals.isna().all():
            rejected[canon] = col_meta(col, "rejected", "all_null"); continue
        # reject cells that look like balance-sheet magnitudes (misalignment), not ratios
        bad = vals.abs() > MARGIN_ABS_LIMIT
        nbad = int(bad.sum())
        vals = vals.mask(bad)
        valid_frac = float(vals.notna().mean())
        fc = _frozen_ticker_count(df, col)
        if valid_frac < 0.5:
            rejected[canon] = {**col_meta(col, "rejected", "magnitude_like_not_ratio"),
                               "misaligned_cells": nbad}; continue
        if fc >= FROZEN_FRAC_REJECT * EXPECTED_TICKERS:
            rejected[canon] = col_meta(col, "rejected", "frozen_snapshot"); continue
        out[canon] = vals
        accepted[canon] = {**col_meta(col, "accepted"), "misaligned_cells": nbad, "kind": "ratio"}

    # keep only ticker-years with at least one accepted value
    feat_cols = [c for c in out.columns if c not in ("ticker", "year")]
    out = out.dropna(subset=feat_cols, how="all")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    report = {
        "source_dir": str(SRC_DIR.relative_to(REPO_ROOT)),
        "sheet": SHEET,
        "rows_read": int(len(df)),
        "rows_written": int(len(out)),
        "coverage_by_year": meta["coverage"],
        "expected_tickers_per_year": EXPECTED_TICKERS,
        "accepted_columns": accepted,
        "rejected_columns": rejected,
        "frozen_valuation_columns": frozen_valuation,
        "misalignment_2024_evidence": misalign,
        "candidate_csv": str(OUT_CSV.relative_to(REPO_ROOT)),
        "issues": issues,
        "note": ("Income/profitability fields vary per year and are accepted; valuation fields are a "
                 "frozen snapshot and rejected; 2024 misaligned cells rejected, not imputed."),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2, default=str))
    _write_md(report)
    return report


def _write_md(r: dict) -> None:
    acc = ", ".join(sorted(r["accepted_columns"])) or "none"
    rej = ", ".join(sorted(r["rejected_columns"])) or "none"
    froz = ", ".join(sorted(r["frozen_valuation_columns"])) or "none"
    lines = [
        "# Corrected yearly financial ingestion report", "",
        "Verified per-year income/profitability history from corrected XLSX exports. "
        "Research/educational only — NOT investment advice.", "",
        f"- Source: `{r['source_dir']}` (sheet `{r['sheet']}`)",
        f"- Rows read: **{r['rows_read']}**  |  candidate rows written: **{r['rows_written']}**",
        f"- Coverage by year: {r['coverage_by_year']}", "",
        "## Accepted columns (genuinely year-varying)", "", acc, "",
        "## Rejected columns", "", rej, "",
        "## Frozen valuation columns (still rejected)", "", froz, "",
        "## 2024 misalignment evidence (cells rejected, not imputed)", "",
        (", ".join(f"{k}: {v} cells" for k, v in r["misalignment_2024_evidence"].items()) or "none detected"), "",
        "## Per-column detail", "", "| column | status | reason | frozen_tickers | misaligned_cells |",
        "|---|---|---|---|---|",
    ]
    for col, m in {**r["accepted_columns"], **r["rejected_columns"], **r["frozen_valuation_columns"]}.items():
        lines.append(f"| `{col}` | {m.get('status')} | {m.get('rejection_reason') or '-'} | "
                     f"{m.get('frozen_ticker_count', '-')} | {m.get('misaligned_cells', '-')} |")
    if r["issues"]:
        lines += ["", "## Issues", ""] + [f"- {i}" for i in r["issues"]]
    REPORT_MD.write_text("\n".join(lines))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default=None, help="override source dir")
    a = ap.parse_args(argv)
    if a.src:
        global SRC_DIR
        SRC_DIR = Path(a.src)
    rep = ingest()
    print(f"[corrected] rows_read={rep['rows_read']} written={rep['rows_written']}")
    print(f"[corrected] accepted={sorted(rep['accepted_columns'])}")
    print(f"[corrected] frozen_valuation={sorted(rep['frozen_valuation_columns'])}")
    print(f"[corrected] 2024_misalignment={rep['misalignment_2024_evidence']}")
    print(f"[corrected] wrote {OUT_CSV.name}, {REPORT_JSON.name}, {REPORT_MD.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
