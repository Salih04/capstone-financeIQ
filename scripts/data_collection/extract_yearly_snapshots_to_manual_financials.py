"""Extract candidate financial features from yearly stock Excel files.

Reads 20YYstocks.xlsx (and (1) duplicates / .csv) snapshots, normalizes headers,
maps recognized columns to the manual financial-history schema, and writes:

    data/trusted_raw/financials/candidate_from_yearly_snapshots.csv

This is CANDIDATE data, not trusted. It flows through the same manual-ingestion
validator (`make data`); columns only become features if they genuinely vary
across years, are non-leaky, non-frozen, and not misaligned. Nothing here is
fabricated or imputed — nulls stay null.

Conservative by design:
  * Realized-return / momentum columns are NEVER emitted as candidate features
    (they are target/leakage sources).
  * Columns failing misalignment heuristics are dropped with a reason.

CLI:
    python -m scripts.data_collection.extract_yearly_snapshots_to_manual_financials \
        [--input-dir DIR] [--output-file FILE] [--validate] [--strict] [--dry-run]
        [--force] [--selected-tickers A,B] [--start-year Y] [--end-year Y]
        [--prefer-largest-file] [--prefer-most-columns]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEARCH_DIRS = [
    REPO_ROOT / "data",
    REPO_ROOT / "data" / "raw",
    REPO_ROOT / "data" / "trusted_raw",
    REPO_ROOT / "data" / "trusted_raw" / "yearly_snapshots",
    REPO_ROOT / "data/raw/yearly_xlsx",
]
OUTPUT_FILE = REPO_ROOT / "data" / "trusted_raw" / "financials" / "candidate_from_yearly_snapshots.csv"
MIGRATION_JSON = REPO_ROOT / "data" / "trusted_clean" / "yearly_snapshot_migration_report.json"
MIGRATION_MD = REPO_ROOT / "data" / "trusted_clean" / "yearly_snapshot_migration_report.md"

YEAR_FILE_RE = re.compile(r"(20\d{2})stocks(\(\d+\))?\.(xlsx|csv)$", re.IGNORECASE)
ANNUAL_RETURN_RE = re.compile(r"return\s*%?\s*\(?20\d{2}")  # year-window return col

# Normalized raw XLSX header -> manual canonical name. Conservative: only
# genuine financial-statement / valuation columns. Returns/momentum excluded.
RAW_TO_CANON = {
    "revenue": "revenue",
    "gross_profit": "gross_profit",
    "operating_income": "operating_income",
    "ebitda": "ebitda",
    "net_income": "net_income",
    "gross_profit_margin": "gross_margin",
    "ebitda_margin": "ebitda_margin",
    "net_profit_margin": "net_margin",
    "return_on_equity_roe": "roe",
    "roe": "roe",
    "return_on_assets_roa": "roa",
    "roa": "roa",
    "roic": "roic",
    "total_assets": "total_assets",
    "current_assets": "current_assets",
    "non_current_assets": "non_current_assets",
    "short_term_liabilities": "short_term_liabilities",
    "long_term_liabilities": "long_term_liabilities",
    "equity": "total_equity",
    "working_capital": "working_capital",
    "net_debt": "net_debt",
    "current_ratio": "current_ratio",
    "leverage_ratio": "leverage_ratio",
    "financial_debt_ratio": "financial_debt_ratio",
    "net_debt_ebitda": "net_debt_to_ebitda",
    "market_capitalization": "market_cap",
    "enterprise_value_ev": "enterprise_value",
    "p_e": "pe_ratio",
    "p_b": "pb_ratio",
    "ev_sales": "ps_ratio",
    "ev_ebitda": "ev_ebitda",
}
# Canonical groups for misalignment sanity ranges.
RATIO_LIKE = {"current_ratio", "leverage_ratio", "financial_debt_ratio",
              "net_debt_to_ebitda", "pe_ratio", "pb_ratio", "ps_ratio", "ev_ebitda"}
PCT_LIKE = {"gross_margin", "ebitda_margin", "net_margin", "roe", "roa", "roic"}
BIG_MONEY = {"revenue", "gross_profit", "operating_income", "ebitda", "net_income",
             "total_assets", "current_assets", "non_current_assets",
             "short_term_liabilities", "long_term_liabilities", "total_equity",
             "working_capital", "net_debt", "market_cap", "enterprise_value"}


def _norm(name) -> str:
    s = unicodedata.normalize("NFKC", str(name)).strip().lower()
    s = s.replace("ı", "i").replace("ş", "s").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ç", "c")
    s = "".join(ch if ch.isalnum() else "_" for ch in s)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def _read_table(path: Path) -> pd.DataFrame | None:
    try:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path, header=0)
            if not any(_norm(c) in ("company", "ticker") for c in df.columns):
                df = pd.read_excel(path, header=1)
    except Exception:
        return None
    if df is None or df.empty:
        return None
    return df


def _discover(search_dirs, rep) -> dict[int, list[Path]]:
    by_year: dict[int, list[Path]] = {}
    seen = set()
    for d in search_dirs:
        if not d.is_dir():
            continue
        rep["input_folders_searched"].append(str(d))
        for p in sorted(d.glob("*")):
            if not p.is_file() or p in seen:
                continue
            m = YEAR_FILE_RE.search(p.name)
            if not m:
                if p.suffix.lower() in (".xlsx", ".csv"):
                    rep["files_skipped"].append({"file": str(p), "reason": "name does not match 20YYstocks"})
                continue
            seen.add(p)
            by_year.setdefault(int(m.group(1)), []).append(p)
    return by_year


def _score_file(path: Path) -> tuple[int, int]:
    df = _read_table(path)
    if df is None:
        return (0, 0)
    recognized = sum(1 for c in df.columns if _norm(c) in RAW_TO_CANON or _norm(c) in ("company", "ticker"))
    return (len(df), recognized)


def _detect_misalignment(canon: str, s: pd.Series) -> str | None:
    v = pd.to_numeric(s, errors="coerce").dropna()
    if v.empty:
        return None
    med = float(v.abs().median())
    if canon in PCT_LIKE and med > 1e4:
        return "pct_column_has_currency_like_magnitudes"
    if canon in RATIO_LIKE and med > 1e5:
        return "ratio_column_has_balance_sheet_like_magnitudes"
    if canon in BIG_MONEY and 0 < med < 1.0:
        return "money_column_has_tiny_decimal_values"
    return None


def extract(cfg) -> dict:
    rep = {
        "input_folders_searched": [], "files_discovered": [], "files_skipped": [],
        "year_files": {}, "selected_file_per_year": {}, "duplicate_years": {},
        "rows_per_file": {}, "ticker_coverage_per_year": {}, "columns_discovered": {},
        "columns_mapped": {}, "columns_skipped": {}, "annual_return_col_per_year": {},
        "candidate_columns_written": [], "columns_rejected_misaligned": [],
        "ambiguous_columns": [], "output_file": str(cfg.output_file),
        "output_rows": 0, "ticker_year_coverage": {}, "issues": [],
    }
    by_year = _discover(cfg.search_dirs, rep)
    if not by_year:
        rep["issues"].append("no yearly stock files found in any search dir")
        return rep

    frames = []
    for year in sorted(by_year):
        if cfg.start_year and year < cfg.start_year:
            continue
        if cfg.end_year and year > cfg.end_year:
            continue
        files = by_year[year]
        rep["year_files"][year] = [str(p) for p in files]
        for p in files:
            rep["files_discovered"].append(str(p))
        if len(files) > 1:
            rep["duplicate_years"][year] = [str(p) for p in files]
        # choose best by (rows, recognized cols)
        scored = sorted(files, key=lambda p: _score_file(p), reverse=True)
        chosen = scored[0]
        rep["selected_file_per_year"][year] = str(chosen)

        df = _read_table(chosen)
        if df is None:
            rep["files_skipped"].append({"file": str(chosen), "reason": "unreadable/empty"})
            continue
        rep["rows_per_file"][str(chosen)] = int(len(df))

        norm_cols = {c: _norm(c) for c in df.columns}
        rep["columns_discovered"][year] = sorted(set(norm_cols.values()))

        # ticker
        tcol = next((c for c, n in norm_cols.items() if n in ("company", "ticker")), None)
        if tcol is None:
            rep["files_skipped"].append({"file": str(chosen), "reason": "no ticker/company column"})
            continue
        out = pd.DataFrame()
        out["ticker"] = df[tcol].astype(str).str.strip().str.upper()
        out["year"] = year

        # annual return column (target source only — never a feature)
        ann = next((c for c, n in norm_cols.items() if ANNUAL_RETURN_RE.search(n)), None)
        rep["annual_return_col_per_year"][year] = (ann or None)

        mapped, skipped = {}, {}
        seen_canon: dict[str, str] = {}
        for c, n in norm_cols.items():
            if c == tcol:
                continue
            if n == "indices":
                out["indices"] = df[c]
                continue
            canon = RAW_TO_CANON.get(n)
            if not canon:
                # explicitly note leaky/return columns we deliberately skip
                if "return" in n or n in ("price", "daily_change", "volume"):
                    skipped[n] = "leaky_or_snapshot_return/price/volume (target/momentum)"
                else:
                    skipped[n] = "unrecognized"
                continue
            if canon in seen_canon:
                rep["ambiguous_columns"].append({"year": year, "canonical": canon,
                                                  "sources": [seen_canon[canon], n]})
                skipped[n] = f"ambiguous_duplicate_of_{seen_canon[canon]}"
                continue
            num = pd.to_numeric(
                df[c].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip(),
                errors="coerce",
            )
            mis = _detect_misalignment(canon, num)
            if mis:
                rep["columns_rejected_misaligned"].append({"year": year, "column": canon, "reason": mis})
                skipped[n] = f"misaligned:{mis}"
                continue
            out[canon] = num
            mapped[n] = canon
            seen_canon[canon] = n

        rep["columns_mapped"][year] = mapped
        rep["columns_skipped"][year] = skipped
        rep["ticker_coverage_per_year"][year] = int(out["ticker"].nunique())
        frames.append(out)

    if not frames:
        rep["issues"].append("no usable yearly frames after extraction")
        return rep

    cand = pd.concat(frames, ignore_index=True)
    if cfg.selected_tickers:
        cand = cand[cand["ticker"].isin({t.upper() for t in cfg.selected_tickers})]
    # drop indices from candidate features (metadata only, pipeline derives is_bist100)
    cand = cand.drop(columns=["indices"], errors="ignore")
    # one row per ticker-year
    dup = cand.duplicated(["ticker", "year"]).sum()
    if dup:
        rep["issues"].append(f"{dup} duplicate ticker-year rows collapsed (kept last)")
        cand = cand.drop_duplicates(["ticker", "year"], keep="last")

    feat_cols = [c for c in cand.columns if c not in ("ticker", "year")]
    rep["candidate_columns_written"] = sorted(feat_cols)
    rep["output_rows"] = int(len(cand))
    rep["ticker_year_coverage"] = cand.groupby("year")["ticker"].nunique().to_dict()
    rep["next_command"] = "make data   # ingest + validate the candidate file"

    if not cfg.dry_run:
        cfg.output_file.parent.mkdir(parents=True, exist_ok=True)
        cand.to_csv(cfg.output_file, index=False)
    return rep


def _write_reports(rep: dict) -> None:
    MIGRATION_JSON.parent.mkdir(parents=True, exist_ok=True)
    MIGRATION_JSON.write_text(json.dumps(rep, indent=2, default=str))
    lines = ["# Yearly-snapshot migration report\n",
             f"- Output: `{rep['output_file']}`  | rows: **{rep['output_rows']}**",
             f"- Candidate columns written: {rep['candidate_columns_written']}",
             f"- Ticker-year coverage: {rep['ticker_year_coverage']}",
             f"- Duplicate-year files: {rep['duplicate_years'] or 'none'}",
             f"- Misaligned columns rejected: {rep['columns_rejected_misaligned'] or 'none'}",
             f"- Ambiguous columns: {rep['ambiguous_columns'] or 'none'}",
             f"- Issues: {rep['issues'] or 'none'}", "",
             "## Selected file per year", ""]
    for y, f in rep["selected_file_per_year"].items():
        lines.append(f"- {y}: `{f}` (rows {rep['rows_per_file'].get(f, '?')}, "
                     f"annual-return col: {rep['annual_return_col_per_year'].get(y)})")
    lines += ["", "## Columns skipped (per year, with reason)", ""]
    for y, sk in rep.get("columns_skipped", {}).items():
        lines.append(f"### {y}")
        for col, reason in sk.items():
            lines.append(f"- `{col}`: {reason}")
    lines += ["", f"Next: `{rep.get('next_command', 'make data')}`"]
    MIGRATION_MD.write_text("\n".join(lines))


class _Cfg:
    def __init__(self, a):
        self.search_dirs = [Path(a.input_dir)] if a.input_dir else DEFAULT_SEARCH_DIRS
        self.output_file = Path(a.output_file) if a.output_file else OUTPUT_FILE
        self.validate = a.validate
        self.strict = a.strict
        self.dry_run = a.dry_run
        self.force = a.force
        self.selected_tickers = [t.strip() for t in a.selected_tickers.split(",")] if a.selected_tickers else None
        self.start_year = a.start_year
        self.end_year = a.end_year


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input-dir", default=None)
    ap.add_argument("--output-file", default=None)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--selected-tickers", default=None)
    ap.add_argument("--start-year", type=int, default=None)
    ap.add_argument("--end-year", type=int, default=None)
    ap.add_argument("--prefer-largest-file", action="store_true")
    ap.add_argument("--prefer-most-columns", action="store_true")
    a = ap.parse_args(argv)
    cfg = _Cfg(a)

    rep = extract(cfg)
    _write_reports(rep)

    print(f"[extract] searched {len(rep['input_folders_searched'])} dirs; "
          f"files: {len(rep['files_discovered'])}; selected years: {list(rep['selected_file_per_year'])}")
    print(f"[extract] candidate columns: {rep['candidate_columns_written']}")
    print(f"[extract] rows written: {rep['output_rows']} -> {rep['output_file']}"
          f"{' (dry-run, not written)' if cfg.dry_run else ''}")
    if rep["columns_rejected_misaligned"]:
        print(f"[extract] misaligned rejected: {rep['columns_rejected_misaligned']}")
    if rep["issues"]:
        for i in rep["issues"]:
            print(f"[extract] issue: {i}")
    if cfg.strict and rep["issues"]:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
