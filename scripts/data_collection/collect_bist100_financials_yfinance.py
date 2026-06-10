"""Collect BIST100 financial statement data via yfinance (unofficial Yahoo Finance API).

SOURCE ATTRIBUTION
------------------
Data comes from Yahoo Finance via the unofficial `yfinance` library.
Yahoo Finance sources fundamentals from company filings and may differ from
the official KAP/IFRS filings in edge cases. Always cross-check critical values
against the official KAP public disclosure platform (kap.borsaistanbul.com).

LICENSE / TERMS
---------------
Yahoo Finance data is free for personal, educational, research use.
Bulk automated downloading may violate Yahoo's Terms of Service.
This script fetches one ticker at a time with configurable delays.
Do not run against hundreds of tickers in a tight loop.

COVERAGE LIMITATIONS
---------------------
- yfinance for BIST stocks typically only goes back to FY2022 (sometimes FY2021).
  FY2020 and FY2021 data is frequently absent or NaN for Turkish listings.
- Banks (GARAN, AKBNK, ISCTR, VAKBN, YKBNK) have non-standard IS structure:
  "revenue" = net interest income, EBITDA is undefined. These are flagged.
- Holdings (KCHOL, SAHOL, DOHOL) consolidate many sectors; financial ratios
  are not directly comparable with pure-play companies.
- EBITDA is NOT available in yfinance income statement; it is approximated as
  EBIT + Depreciation&Amortization where both are present, else left null.

OUTPUT
------
Writes: data/trusted_raw/financials/bist100_yfinance_candidate.csv

Feed this into the pipeline:
    PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets
    PYTHONPATH=. python -m scripts.data_collection.build_all

EXPANSION IS INCOMPLETE UNTIL
------------------------------
1. Return targets for new tickers exist in the legacy reference CSV.
   (data/trusted/stocks_2020_2025.csv or via compute_bist100_returns_from_prices.py)
2. New tickers are added to data/config/universe_training_bist100.csv.
3. `make data && make split-datasets` is re-run.
4. Training tickers > 40.

Run:
    pip install yfinance  # not in requirements.txt; optional research dep
    PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py
    PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py \\
        --tickers GARAN VESTL AKBNK
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import time
from io import StringIO
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("bist100_yf")

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_CSV = REPO_ROOT / "data" / "trusted_raw" / "financials" / "bist100_yfinance_candidate.csv"
CANDIDATES_CSV = REPO_ROOT / "data" / "config" / "bist100_candidates.csv"
REPORT_JSON = REPO_ROOT / "data" / "trusted_clean" / "bist100_yfinance_report.json"

# Current public_40 — never re-fetch these; they already have corrected financials.
PUBLIC_40 = {
    "AEFES", "ARCLK", "ASELS", "ASTOR", "BIMAS", "BRSAN", "BTCIM", "CANTE",
    "CCOLA", "CIMSA", "DOAS", "DSTKF", "ENKAI", "EREGL", "FROTO", "GUBRF",
    "HEKTS", "KONTR", "KRDMD", "KUYAS", "MAVI", "MGROS", "MIATK", "OYAKC",
    "PASEU", "PETKM", "PGSUS", "SASA", "SISE", "TAVHL", "TCELL", "THYAO",
    "TOASO", "TRALT", "TRMET", "TSKB", "TTKOM", "TUPRS", "TURSG", "ULKER",
}

# Fallback candidate list used when --candidates-csv is not provided and no CSV exists.
# Banks flagged separately — they need special handling (no gross_profit/EBITDA).
DEFAULT_CANDIDATES = [
    "VESTL", "KCHOL", "SAHOL", "AKSA", "DOHOL", "KOZAL",
    "EKGYO", "ODAS", "SMRTG", "AKSEN",
]

BANK_TICKERS = {
    "GARAN", "AKBNK", "ISCTR", "VAKBN", "YKBNK", "HALKB", "TSKB",
    "QNBFB", "ALBRK", "SKBNK", "DENIZ",
}

# Required fields for a row to be considered "valid" (for --missing-only logic).
_VALID_REQUIRED = ["revenue", "net_income", "total_assets", "equity"]


def _load_candidates_csv(path: Path) -> list[str]:
    """Load ticker list from bist100_candidates.csv, skipping comment lines."""
    lines = [ln for ln in path.read_text().splitlines() if not ln.strip().startswith("#") and ln.strip()]
    df = pd.read_csv(StringIO("\n".join(lines)))
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    return df["ticker"].tolist()


def _tickers_with_valid_data(raw_csv: Path) -> set[str]:
    """Return tickers that already have ≥1 row with non-null core fields in the raw CSV."""
    if not raw_csv.is_file():
        return set()
    df = pd.read_csv(raw_csv)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    for col in _VALID_REQUIRED:
        if col not in df.columns:
            df[col] = float("nan")
    valid = df[df[_VALID_REQUIRED].notna().all(axis=1)]
    return set(valid["ticker"].unique())

# yfinance row → canonical pipeline column
IS_FIELD_MAP = {
    "Total Revenue": "revenue",
    "Operating Revenue": "revenue",       # fallback
    "Gross Profit": "gross_profit",
    "Operating Income": "operating_income",
    "EBIT": "operating_income",           # fallback
    "Net Income": "net_income",
    "Net Income Common Stockholders": "net_income",   # fallback
    "Reconciled Depreciation": "_depreciation",
    "Depreciation And Amortization In Income Statement": "_depreciation",
}

BS_FIELD_MAP = {
    "Total Assets": "total_assets",
    "Current Assets": "current_assets",
    "Total Non Current Assets": "non_current_assets",
    "Current Liabilities": "short_term_liabilities",
    "Total Non Current Liabilities Net Minority Interest": "long_term_liabilities",
    "Common Stock Equity": "equity",
    "Stockholders Equity": "equity",
    "Total Equity Gross Minority Interest": "equity",
    "Working Capital": "working_capital",
    "Net Debt": "net_debt",
}

YEARS = list(range(2020, 2026))


def _try_import_yfinance():
    try:
        import yfinance as yf
        return yf
    except ImportError:
        raise SystemExit(
            "yfinance not installed. Run: pip install yfinance\n"
            "This is an optional research dependency not included in requirements.txt."
        )


def _extract_row(df, candidates: list[str]):
    """Return first matching row from a pandas DataFrame index, or None."""
    for c in candidates:
        if c in df.index:
            return df.loc[c]
    return None


def _safe_float(v) -> float | None:
    try:
        f = float(v)
        import math
        return None if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return None


def fetch_ticker_financials(yf, ticker: str, delay_s: float = 2.0) -> list[dict]:
    """Fetch annual IS + BS for one ticker. Returns list of dicts (one per year)."""
    symbol = f"{ticker}.IS"
    is_bank = ticker in BANK_TICKERS
    rows = []

    try:
        t = yf.Ticker(symbol)
        fin = t.financials     # income statement, columns = year-end timestamps
        bs = t.balance_sheet
    except Exception as exc:
        log.warning(f"{ticker}: yfinance fetch failed — {exc}")
        return []
    finally:
        time.sleep(delay_s)

    if fin is None or fin.empty:
        log.warning(f"{ticker}: income statement empty or unavailable")
        return []

    retrieved_at = datetime.date.today().isoformat()

    for col in fin.columns:
        year = col.year if hasattr(col, "year") else None
        if year not in YEARS:
            continue

        row: dict = {
            "ticker": ticker,
            "year": year,
            "source": "yfinance_unofficial",
            "retrieved_at": retrieved_at,
        }

        # Income statement fields
        for yf_row, canon in IS_FIELD_MAP.items():
            if yf_row in fin.index:
                v = _safe_float(fin.loc[yf_row, col])
                if v is not None:
                    if canon == "_depreciation":
                        row["_depreciation"] = v
                    elif canon not in row:
                        row[canon] = v

        # Approximate EBITDA = operating_income + depreciation (if both present)
        if "operating_income" in row and "_depreciation" in row:
            row["ebitda"] = row["operating_income"] + row["_depreciation"]

        # Balance sheet
        if bs is not None and not bs.empty and col in bs.columns:
            for yf_row, canon in BS_FIELD_MAP.items():
                if yf_row in bs.index and canon not in row:
                    v = _safe_float(bs.loc[yf_row, col])
                    if v is not None:
                        row[canon] = v

        # Derived ratios (only if base values present)
        ni = row.get("net_income")
        eq = row.get("equity")
        ta = row.get("total_assets")
        rev = row.get("revenue")
        gp = row.get("gross_profit")
        ebitda = row.get("ebitda")

        if ni is not None and eq is not None and eq != 0:
            row["roe"] = round(ni / eq * 100, 4)
        if ni is not None and ta is not None and ta != 0:
            row["roa"] = round(ni / ta * 100, 4)
        if rev is not None and rev != 0:
            if gp is not None:
                row["gross_margin"] = round(gp / rev * 100, 4)
            if ni is not None:
                row["net_margin"] = round(ni / rev * 100, 4)
            if ebitda is not None:
                row["ebitda_margin"] = round(ebitda / rev * 100, 4)

        if is_bank:
            row["_bank_warning"] = (
                "Bank ticker: 'revenue' is net interest income; EBITDA undefined; "
                "gross_profit unavailable. Ratios not comparable with non-bank companies."
            )

        row.pop("_depreciation", None)
        rows.append(row)

    log.info(f"{ticker}: fetched {len(rows)} year rows ({[r['year'] for r in rows]})")
    return rows


def collect(tickers: list[str], delay_s: float = 2.0) -> pd.DataFrame:
    yf = _try_import_yfinance()
    import warnings
    warnings.filterwarnings("ignore")

    skip = [t for t in tickers if t in PUBLIC_40]
    fetch = [t for t in tickers if t not in PUBLIC_40]

    if skip:
        log.warning(f"Skipping {skip} — already in public_40 with corrected financials.")

    all_rows = []
    for ticker in fetch:
        log.info(f"Fetching {ticker}.IS ...")
        rows = fetch_ticker_financials(yf, ticker, delay_s=delay_s)
        all_rows.extend(rows)

    if not all_rows:
        log.warning("No data collected.")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["ticker", "year"])
    df = df.sort_values(["ticker", "year"])
    return df


def write_output(df: pd.DataFrame) -> None:
    if df.empty:
        log.warning("Nothing to write.")
        return

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Merge with existing candidate if present (add new ticker-years, don't overwrite)
    if OUT_CSV.is_file():
        existing = pd.read_csv(OUT_CSV)
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["ticker", "year"], keep="last")
        combined = combined.sort_values(["ticker", "year"])
        combined.to_csv(OUT_CSV, index=False)
        log.info(f"Merged with existing. Total rows: {len(combined)}")
    else:
        df.to_csv(OUT_CSV, index=False)
        log.info(f"Wrote {len(df)} rows to {OUT_CSV.name}")

    # Report
    tickers_collected = sorted(df["ticker"].unique().tolist())
    years_by_ticker = {
        t: sorted(df[df["ticker"] == t]["year"].tolist())
        for t in tickers_collected
    }
    field_coverage = {
        col: int(df[col].notna().sum())
        for col in df.columns
        if col not in ("ticker", "year", "source", "retrieved_at", "_bank_warning")
    }
    bank_tickers_collected = [t for t in tickers_collected if t in BANK_TICKERS]

    report = {
        "collected_tickers": tickers_collected,
        "ticker_count": len(tickers_collected),
        "rows_written": len(df),
        "years_by_ticker": years_by_ticker,
        "field_coverage_nonnull_rows": field_coverage,
        "bank_tickers_flagged": bank_tickers_collected,
        "output_csv": str(OUT_CSV.relative_to(REPO_ROOT)),
        "data_source": "yfinance_unofficial (Yahoo Finance fundamentals database)",
        "data_source_url": "https://finance.yahoo.com",
        "terms_note": (
            "Yahoo Finance data is free for personal/educational use. "
            "Cross-check critical values against KAP (kap.borsaistanbul.com)."
        ),
        "coverage_warning": (
            "yfinance typically only provides FY2022+ for most BIST stocks. "
            "FY2020 and FY2021 rows will be NaN for many tickers."
        ),
        "next_steps": [
            "1. Review bist100_yfinance_candidate.csv for data quality.",
            "2. Add verified tickers to data/config/universe_training_bist100.csv "
               "(set is_training_universe=true).",
            "3. Ensure those tickers also have annual return targets in "
               "data/trusted/stocks_2020_2025.csv (or run compute_bist100_returns).",
            "4. Run: PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets",
            "5. Run: PYTHONPATH=. python -m scripts.data_collection.build_all",
            "6. Training tickers > 40 confirms expansion succeeded.",
        ],
        "expansion_not_complete": (
            "Training universe expansion is NOT complete until new tickers have both "
            "(a) financial features AND (b) next-year return targets. "
            "Do not claim expanded training until tickers > 40 in the modeling dataset."
        ),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2))
    log.info(f"Report: {REPORT_JSON.name}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--tickers", nargs="+", default=None,
        help="Explicit BIST tickers to collect (without .IS suffix). "
             "Overrides --candidates-csv and the default list.",
    )
    ap.add_argument(
        "--candidates-csv", type=Path, default=None,
        help=f"CSV of candidates to collect (default: {CANDIDATES_CSV.relative_to(REPO_ROOT)} if it exists).",
    )
    ap.add_argument(
        "--missing-only", action="store_true",
        help="Skip tickers that already have ≥1 valid row in the raw output CSV.",
    )
    ap.add_argument(
        "--force-refresh", action="store_true",
        help="Re-fetch even tickers already present in the raw CSV (overrides --missing-only).",
    )
    ap.add_argument(
        "--delay", type=float, default=2.0,
        help="Seconds to sleep between tickers (default 2.0 — respect rate limits).",
    )
    ap.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be fetched without writing output.",
    )
    args = ap.parse_args(argv)

    # Resolve ticker list
    if args.tickers:
        tickers = [t.upper().strip() for t in args.tickers]
    elif args.candidates_csv or CANDIDATES_CSV.is_file():
        csv_path = Path(args.candidates_csv) if args.candidates_csv else CANDIDATES_CSV
        tickers = _load_candidates_csv(csv_path)
        log.info(f"Loaded {len(tickers)} candidates from {csv_path.name}")
    else:
        tickers = [t.upper().strip() for t in DEFAULT_CANDIDATES]
        log.info(f"Using built-in default candidates ({len(tickers)} tickers). "
                 f"Create {CANDIDATES_CSV.relative_to(REPO_ROOT)} for the full list.")

    # Apply --missing-only (skip tickers that already have valid data)
    if args.missing_only and not args.force_refresh:
        already_have = _tickers_with_valid_data(OUT_CSV)
        before = len(tickers)
        tickers = [t for t in tickers if t not in already_have]
        skipped = before - len(tickers)
        if skipped:
            log.info(f"--missing-only: skipping {skipped} tickers with existing valid data.")
        if not tickers:
            log.info("All candidate tickers already have valid data. Nothing to fetch.")
            return

    log.info(f"Targets: {tickers}")
    log.info(
        "DATA SOURCE: yfinance (unofficial Yahoo Finance). "
        "Cross-check with KAP (kap.borsaistanbul.com) for official filings."
    )
    log.info(
        "IMPORTANT: This does NOT complete BIST100 training expansion. "
        "Return targets for new tickers still required."
    )

    if args.dry_run:
        skip = [t for t in tickers if t in PUBLIC_40]
        fetch = [t for t in tickers if t not in PUBLIC_40]
        print(f"Would fetch: {fetch}")
        print(f"Would skip (already in public_40): {skip}")
        return

    df = collect(tickers, delay_s=args.delay)
    write_output(df)

    if not df.empty:
        print("\n── COLLECTION SUMMARY ──────────────────────────────────")
        print(f"Tickers collected : {sorted(df['ticker'].unique().tolist())}")
        print(f"Total rows        : {len(df)}")
        years_by_t = df.groupby("ticker")["year"].apply(list).to_dict()
        for t, yrs in sorted(years_by_t.items()):
            print(f"  {t:8s}: {sorted(yrs)}")
        print(f"\nOutput: {OUT_CSV}")
        print(f"Report: {REPORT_JSON}")
        print(
            "\n⚠  EXPANSION NOT COMPLETE. Still needed:"
            "\n   1. Verify data quality against KAP filings."
            "\n   2. Add tickers + return targets to pipeline reference data."
            "\n   3. Update universe_training_bist100.csv."
            "\n   4. Re-run make data && make split-datasets."
            "\n   5. Confirm training tickers > 40."
        )


if __name__ == "__main__":
    main()
