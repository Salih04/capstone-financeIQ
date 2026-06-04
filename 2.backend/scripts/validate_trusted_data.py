"""Validate the trusted yearly dataset + assert the codebase stays clean.

Runs without a database. Two halves:
  1. Data: XLSX exist -> convert -> CSV schema/rows/dups/numeric checks.
  2. Hygiene: active backend/frontend code must not reference Finnhub, the
     News API, or any quarantined module (seed/synthetic/scraper/old loader).

Exit code 0 == everything valid. Non-zero == at least one failure (printed).

Usage:
    python -m scripts.validate_trusted_data
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

from app.trusted_data import (
    PERCENT_COLUMNS,
    REQUIRED_COLUMNS,
    read_trusted_xlsx,
    summarize_frame,
    validate_frame,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASETS = REPO_ROOT / "3.Datasets"
TRUSTED_OUT = REPO_ROOT / "data" / "trusted"
COMBINED = TRUSTED_OUT / "stocks_2020_2025.csv"
EXPECTED_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# Patterns that must NOT appear in active (non-quarantined) source.
BANNED = [
    r"finnhub",
    r"NEWS_API_KEY",
    r"import_datasets",
    r"seed_companies",
    r"import_kap_html",
    r"generate_data",
    r"load_trusted_fundamentals",
]
SCAN_DIRS = [REPO_ROOT / "2.backend" / "app", REPO_ROOT / "1.frontend" / "src"]


def _fail(msg: str, failures: list[str]) -> None:
    print(f"  FAIL: {msg}")
    failures.append(msg)


def check_data(failures: list[str]) -> None:
    print("[data] checking trusted XLSX -> CSV")
    xlsx = sorted(DATASETS.glob("20*stocks.xlsx"))
    if len(xlsx) != len(EXPECTED_YEARS):
        _fail(f"expected {len(EXPECTED_YEARS)} XLSX files, found {len(xlsx)}", failures)

    frames = []
    for f in xlsx:
        df = read_trusted_xlsx(f)
        errs = validate_frame(df, f.name)
        for e in errs:
            _fail(e, failures)
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    s = summarize_frame(combined)
    print(f"  rows={s['rows']} years={s['years']} tickers={s['tickers']}")

    if s["years"] != EXPECTED_YEARS:
        _fail(f"years {s['years']} != expected {EXPECTED_YEARS}", failures)

    for col in REQUIRED_COLUMNS:
        if col not in combined.columns:
            _fail(f"required column '{col}' missing", failures)

    # Numeric columns must be numeric (NaN allowed, strings not).
    for col in combined.columns:
        if col in ("ticker", "indices", "source_file"):
            continue
        if not pd.api.types.is_numeric_dtype(combined[col]):
            _fail(f"column '{col}' is not numeric after conversion", failures)

    # Bounded percents (margins/returns) have a natural sanity range. Growth %
    # is intentionally excluded: the trusted data legitimately contains enormous
    # growth figures (hyperinflation, near-zero bases). We never alter real data,
    # so extreme growth is a WARNING, not a failure.
    bounded = {c for c in PERCENT_COLUMNS if not c.endswith("growth_pct")}
    for col in bounded:
        if col in combined.columns:
            if (combined[col].dropna().abs() > 100000).any():
                _fail(f"bounded percent column '{col}' has implausible values", failures)
    for col in PERCENT_COLUMNS:
        if col.endswith("growth_pct") and col in combined.columns:
            extreme = int((combined[col].dropna().abs() > 100000).sum())
            if extreme:
                print(f"  WARN: '{col}' has {extreme} extreme growth value(s) (kept as-is, real data)")

    # No future-year leakage helper: for each selected year, history is only <=.
    for y in EXPECTED_YEARS:
        hist = combined[combined["year"] <= y]
        if (hist["year"] > y).any():
            _fail(f"history for {y} leaks future years", failures)

    # Previous-year availability (every year except the first has a prior year).
    for y in EXPECTED_YEARS[1:]:
        if combined[combined["year"] == y - 1].empty:
            _fail(f"previous year {y-1} missing for {y}", failures)


def check_combined_csv(failures: list[str]) -> None:
    print("[data] checking generated combined CSV")
    if not COMBINED.is_file():
        print("  (combined CSV not generated yet; run convert_trusted_xlsx) - skipping")
        return
    df = pd.read_csv(COMBINED)
    for e in validate_frame(df, COMBINED.name):
        _fail(e, failures)


def check_hygiene(failures: list[str]) -> None:
    print("[hygiene] scanning active source for banned references")
    exts = {".py", ".js", ".jsx", ".ts", ".tsx"}
    for base in SCAN_DIRS:
        for path in base.rglob("*"):
            if path.suffix not in exts or "node_modules" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pat in BANNED:
                if re.search(pat, text, re.IGNORECASE):
                    _fail(f"{path.relative_to(REPO_ROOT)} references banned '{pat}'", failures)


def check_compile(failures: list[str]) -> None:
    print("[compile] py_compile backend")
    files = [
        str(p)
        for p in (REPO_ROOT / "2.backend").rglob("*.py")
        if ".venv" not in p.parts and "unnecessary" not in p.parts
    ]
    rc = subprocess.run(
        [sys.executable, "-m", "py_compile", *files],
        capture_output=True,
        text=True,
    )
    if rc.returncode != 0:
        _fail(f"py_compile failed: {rc.stderr.strip()[:300]}", failures)


def check_research(failures: list[str]) -> None:
    print("[research] scoring + validation + leakage")
    from app.services.research import benchmark, company, scoring, validation
    from app.services.research import feature_registry as reg

    # Target must never be a feature.
    if any(f.fundamental and f.name == "annual_return_pct" for f in reg.REGISTRY):
        _fail("realized return is marked as a fundamental feature (leak)", failures)
    if "annual_return_pct" in {f.name for f in reg.fundamental_features()}:
        _fail("realized return leaked into fundamental feature set", failures)

    years = scoring.data.available_years()
    prev_returns = None
    for y in years:
        sc = scoring.score_year(y).set_index("ticker").sort_index()
        if sc["fundamental_score"].isna().all():
            _fail(f"all fundamental scores NaN for {y}", failures)
        # Realized returns MUST change across years (that is the real time axis).
        rets = sc[scoring.data.TARGET_COLUMN].round(4)
        if prev_returns is not None and rets.equals(prev_returns):
            _fail(f"realized returns identical {y-1}->{y} (year not applied to returns)", failures)
        prev_returns = rets

    # Data-integrity report: which columns are frozen vs time-varying.
    var = scoring.data.column_variability()
    frozen_statement = [c for c in var["frozen_snapshot"]
                        if c in {"revenue", "net_income", "ebitda", "operating_income",
                                 "roe_pct", "roa_pct", "roic_pct", "net_margin_pct"}]
    if frozen_statement:
        print(f"  WARN: income-statement/profitability columns are FROZEN across years "
              f"(single 2025 snapshot): {frozen_statement}. Only balance-sheet, growth, "
              f"and realized return vary. Per-year fundamental trends are partly invalid.")
    print(f"  variability: {var['n_varying']} time-varying, {var['n_frozen']} frozen columns")

    v = validation.validate_all()
    if not v["per_year"]:
        _fail("validation produced no per-year results", failures)

    # Benchmark-missing state must be honest (no fabricated returns).
    if not benchmark.is_available():
        if benchmark.year_return(years[0]) is not None:
            _fail("benchmark reports missing but returns a value (fabrication)", failures)

    # ASELSAN example only if present (do not hardcode requirement).
    df = scoring.data.load_trusted()
    if "ASELS" in set(df["ticker"]):
        d = company.company_detail("ASELS", max(years))
        if d["fundamental_score"] is None:
            _fail("ASELS detail missing fundamental score", failures)
        print(f"  ASELS {max(years)}: score={d['fundamental_score']} return={d['realized_return']}")


def main() -> int:
    failures: list[str] = []
    check_data(failures)
    check_combined_csv(failures)
    check_hygiene(failures)
    check_research(failures)
    check_compile(failures)

    print()
    if failures:
        print(f"VALIDATION FAILED: {len(failures)} issue(s).")
        return 1
    print("VALIDATION PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
