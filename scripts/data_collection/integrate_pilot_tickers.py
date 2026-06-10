"""Integrate yfinance training-only tickers into the T->T+1 modeling dataset.

Appends rows for ALL tickers that are:
    - listed in data/config/universe_training_bist100.csv with is_training_universe=true
      AND is_public_universe=false
    - AND have valid rows in data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv

Why a separate script (not wired into build_all):
- pipeline.py::build_modeling_dataset() starts from stocks_2020_2025.csv (reference),
  which only covers the public_40.
- Training-only tickers have financial data from yfinance but are not in the reference file.
- This script bridges that gap: builds modeling rows using yfinance financials
  + Yahoo Chart year-end prices (for return targets), then appends them.
- Never overwrites existing public_40 rows or rows already in the base dataset.
- yfinance rows are always training-only (is_public_universe=false).

Prerequisites:
    1. data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv  (cleaned financials)
    2. data/config/universe_training_bist100.csv  (training-only tickers listed)
    3. data/trusted_clean/modeling_dataset_2020_2025.csv  (run: make data first)
    4. data/trusted_raw/prices/yahoo_year_end_prices.csv  (run: make fetch-training-prices first)

Run:
    PYTHONPATH=. python scripts/data_collection/integrate_pilot_tickers.py

Then:
    PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets

CAVEATS:
- yfinance is unofficial Yahoo Finance data. KAP cross-check recommended.
- FY2020 and FY2021 typically unavailable via yfinance for most BIST stocks.
- Cross-sectional ranks are computed within the yfinance cohort only (not vs public_40).
- 2025 rows are inference-only (no 2026 return target available yet).
- Tickers with no rows in the clean financials CSV are silently skipped.
- Do NOT claim full BIST100 expansion until training tickers > 40 with verified data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
RAW_DIR = REPO_ROOT / "data" / "trusted_raw"
CONFIG_DIR = REPO_ROOT / "data" / "config"

PILOT_FINANCIALS_CSV = RAW_DIR / "financials" / "bist100_yfinance_candidate_clean.csv"
PRICES_CSV = RAW_DIR / "prices" / "yahoo_year_end_prices.csv"
MODELING_CSV = CLEAN_DIR / "modeling_dataset_2020_2025.csv"
TRAINING_UNIVERSE_CSV = CONFIG_DIR / "universe_training_bist100.csv"
REPORT_OUT = CLEAN_DIR / "pilot_integration_report.json"

YFINANCE_SOURCE = "yfinance_unofficial"
DISCLAIMER = (
    "yfinance pilot expansion — NOT official KAP/IFRS data. "
    "KAP cross-check recommended. Training only. Not investment advice."
)

# Columns from yfinance clean that map directly to modeling dataset features
FINANCIAL_COLS = [
    "revenue", "gross_profit", "operating_income", "net_income", "ebitda",
    "total_assets", "current_assets", "non_current_assets",
    "short_term_liabilities", "long_term_liabilities", "equity",
    "working_capital", "net_debt",
    "roe", "roa", "gross_margin", "net_margin", "ebitda_margin",
]


def _load_training_only_tickers() -> set[str]:
    """Return tickers that are training-universe but NOT public-universe."""
    lines = [ln for ln in TRAINING_UNIVERSE_CSV.read_text().splitlines()
             if not ln.strip().startswith("#")]
    from io import StringIO
    df = pd.read_csv(StringIO("\n".join(lines)))
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    for col in ("is_public_universe", "is_training_universe"):
        df[col] = df[col].astype(str).str.lower().isin({"true", "1", "yes"})
    training_only = df[df["is_training_universe"] & ~df["is_public_universe"]]["ticker"]
    return set(training_only.tolist())


def _compute_returns_from_prices(prices: pd.DataFrame, tickers: set[str]) -> pd.DataFrame:
    """Derive same_year_return_pct from adj_close year-end prices.

    return(Y) = adjclose(Y) / adjclose(Y-1) - 1  (as percentage × 100)
    Requires adjclose for year Y-1 to compute return(Y).
    """
    p = prices[prices["ticker"].isin(tickers) & (prices["status"] == "success")].copy()
    p = p[["ticker", "year", "adjclose"]].dropna(subset=["adjclose"])
    p["adjclose"] = pd.to_numeric(p["adjclose"], errors="coerce")
    p = p.dropna(subset=["adjclose"])
    p = p.sort_values(["ticker", "year"])

    rows = []
    for ticker, grp in p.groupby("ticker"):
        grp = grp.set_index("year")["adjclose"].sort_index()
        years = sorted(grp.index)
        for year in years:
            prev_year = year - 1
            if prev_year in grp.index and grp[prev_year] != 0:
                ret_pct = (grp[year] / grp[prev_year] - 1) * 100
                rows.append({"ticker": ticker, "year": year, "same_year_return_pct": round(ret_pct, 4)})
            else:
                rows.append({"ticker": ticker, "year": year, "same_year_return_pct": np.nan})

    return pd.DataFrame(rows)


def _build_pilot_rows(
    financials: pd.DataFrame,
    returns: pd.DataFrame,
    existing_tickers: set[str],
) -> pd.DataFrame:
    """Build modeling dataset rows for pilot tickers.

    - Uses yfinance financial features
    - Uses Yahoo price-derived returns for targets
    - Never overwrites existing tickers
    """
    # Only build for truly new tickers
    fin = financials[~financials["ticker"].isin(existing_tickers)].copy()
    if fin.empty:
        print("[integrate] no new tickers to integrate — all pilot tickers already in modeling dataset")
        return pd.DataFrame()

    # Merge returns
    ret = returns[returns["ticker"].isin(fin["ticker"].unique())].copy()
    df = fin.merge(ret, on=["ticker", "year"], how="left")

    # Compute next_year_return_pct = this ticker's same_year_return in year+1
    nxt = ret.rename(columns={"year": "_yp", "same_year_return_pct": "next_year_return_pct"})
    nxt["year"] = nxt["_yp"] - 1
    df = df.merge(nxt[["ticker", "year", "next_year_return_pct"]], on=["ticker", "year"], how="left")

    df["target_year"] = df["year"] + 1

    # Cross-sectional ranks within pilot cohort (not mixed with public_40)
    grp = df.groupby("target_year")["next_year_return_pct"]
    v = df["next_year_return_pct"]
    df["next_year_rank_by_return"] = grp.rank(ascending=False, method="min")
    df["next_year_return_percentile"] = grp.rank(pct=True) * 100
    df["next_year_top_10pct_returner"] = (df["next_year_return_percentile"] >= 90).where(v.notna())
    df["next_year_top_20pct_returner"] = (df["next_year_return_percentile"] >= 80).where(v.notna())

    # Stub identity fields
    df["company_name"] = df["ticker"]
    df["sector"] = np.nan
    df["indices"] = np.nan
    df["is_bist100"] = False

    # Benchmark targets (not available for pilot — fill NaN)
    df["next_year_bist100_return_pct"] = np.nan
    df["next_year_excess_return_vs_bist100"] = np.nan
    df["next_year_outperform_bist100"] = np.nan

    # Meta
    df["has_target"] = df["next_year_return_pct"].notna()
    df["is_inference_row"] = ~df["has_target"]
    df["is_public_universe"] = False
    df["is_training_universe"] = True
    df["universe_source"] = "yfinance_pilot"

    return df


def main() -> int:
    # ── Preflight checks ──────────────────────────────────────────────────
    if not PILOT_FINANCIALS_CSV.is_file():
        print(
            f"[integrate] ERROR: {PILOT_FINANCIALS_CSV} not found.\n"
            "  Run: make collect-yfinance-bist100 && make clean-yfinance-bist100",
            file=sys.stderr,
        )
        return 1
    if not MODELING_CSV.is_file():
        print(f"[integrate] ERROR: {MODELING_CSV} not found. Run: make data", file=sys.stderr)
        return 1
    if not PRICES_CSV.is_file():
        print(
            f"[integrate] ERROR: {PRICES_CSV} not found.\n"
            "  Run: make fetch-training-prices",
            file=sys.stderr,
        )
        return 1

    training_only_tickers = _load_training_only_tickers()
    if not training_only_tickers:
        print("[integrate] No training-only tickers found in universe config. Nothing to integrate.")
        return 0
    print(f"[integrate] Training-only tickers from config: {sorted(training_only_tickers)}")

    # ── Load existing modeling dataset ────────────────────────────────────
    existing = pd.read_csv(MODELING_CSV)
    existing["ticker"] = existing["ticker"].astype(str).str.strip().str.upper()
    existing_tickers = set(existing["ticker"].unique())
    print(f"[integrate] Existing modeling dataset: {len(existing)} rows, {len(existing_tickers)} tickers")

    already_present = training_only_tickers & existing_tickers
    truly_new = training_only_tickers - existing_tickers
    if already_present:
        print(f"[integrate] Already present (skip): {sorted(already_present)}")
    if not truly_new:
        print("[integrate] All training-only tickers already in dataset. Nothing to append.")
        return 0
    print(f"[integrate] New tickers to integrate: {sorted(truly_new)}")

    # ── Load and filter financials ─────────────────────────────────────────
    financials = pd.read_csv(PILOT_FINANCIALS_CSV)
    financials["ticker"] = financials["ticker"].astype(str).str.strip().str.upper()
    available_in_clean = set(financials["ticker"].unique())
    no_financial_data = truly_new - available_in_clean
    if no_financial_data:
        print(
            f"[integrate] WARNING: {len(no_financial_data)} training-only ticker(s) have no rows in "
            f"clean financials CSV and will be skipped: {sorted(no_financial_data)}\n"
            "  Run: make collect-yfinance-bist100 && make clean-yfinance-bist100 to collect them."
        )

    financials = financials[financials["ticker"].isin(truly_new)].copy()
    if financials.empty:
        print("[integrate] ERROR: No financial data found for any new training-only ticker.", file=sys.stderr)
        return 1
    print(f"[integrate] yfinance financials rows: {len(financials)} for {sorted(financials['ticker'].unique())}")

    # ── Load prices and compute returns ───────────────────────────────────
    prices = pd.read_csv(PRICES_CSV)
    prices["ticker"] = prices["ticker"].astype(str).str.strip().str.upper()

    missing_price_tickers = truly_new - set(prices["ticker"].unique())
    if missing_price_tickers:
        print(f"[integrate] WARNING: No price data for: {sorted(missing_price_tickers)}")
        print("         Run fetch_yahoo_chart_prices.py with updated training universe CSV.")
        print("         These tickers will be integrated WITHOUT return targets (inference-only rows).")

    returns = _compute_returns_from_prices(prices, truly_new)
    if returns.empty:
        print("[integrate] No return targets computed from prices. All pilot rows will be inference-only.")
    else:
        cov = int(returns["same_year_return_pct"].notna().sum())
        print(f"[integrate] Returns computed: {cov} / {len(returns)} rows have same_year_return_pct")
        print(returns.groupby("ticker")["same_year_return_pct"].apply(
            lambda x: f"{x.notna().sum()}/{len(x)} years"
        ).to_dict())

    # ── Build pilot rows ──────────────────────────────────────────────────
    pilot_df = _build_pilot_rows(financials, returns, existing_tickers)
    if pilot_df.empty:
        return 0

    print(f"\n[integrate] Built {len(pilot_df)} pilot rows:")
    print(pilot_df.groupby("ticker")[["year", "has_target"]].apply(
        lambda g: f"years={sorted(g['year'].tolist())} targets={int(g['has_target'].sum())}/{len(g)}"
    ).to_dict())

    # ── Align columns with existing dataset ──────────────────────────────
    all_cols = list(existing.columns)

    # Add universe metadata cols if not present in existing
    for col in ("is_public_universe", "is_training_universe", "universe_source"):
        if col not in all_cols:
            all_cols.append(col)

    # Reindex pilot_df to match — missing columns become NaN
    pilot_aligned = pilot_df.reindex(columns=all_cols)

    # Also backfill existing dataset with universe columns if missing
    for col in ("is_public_universe", "is_training_universe", "universe_source"):
        if col not in existing.columns:
            if col == "is_public_universe":
                existing[col] = True
            elif col == "is_training_universe":
                existing[col] = True
            else:
                existing[col] = "public_40"

    # ── Append and save ───────────────────────────────────────────────────
    combined = pd.concat([existing, pilot_aligned], ignore_index=True)
    combined = combined.sort_values(["year", "ticker"]).reset_index(drop=True)

    # Sanity: never duplicate ticker-year
    dup = combined.duplicated(["ticker", "year"]).sum()
    if dup:
        print(f"[integrate] WARNING: {dup} duplicate ticker-year rows after merge — keeping last")
        combined = combined.drop_duplicates(["ticker", "year"], keep="last")

    combined.to_csv(MODELING_CSV, index=False)
    print(f"\n[integrate] Wrote {len(combined)} rows to {MODELING_CSV.name}")
    print(f"[integrate] Tickers: {combined['ticker'].nunique()} total "
          f"({existing_tickers.__len__()} existing + {len(truly_new)} pilot)")

    # ── Report ────────────────────────────────────────────────────────────
    pilot_rows_final = combined[combined["ticker"].isin(truly_new)]
    report = {
        "pilot_tickers_integrated": sorted(truly_new),
        "pilot_tickers_skipped_already_present": sorted(already_present),
        "pilot_rows_added": len(pilot_aligned.dropna(how="all")),
        "final_dataset_rows": len(combined),
        "final_dataset_tickers": combined["ticker"].nunique(),
        "existing_tickers": len(existing_tickers),
        "return_coverage": {
            t: int((pilot_rows_final[pilot_rows_final["ticker"] == t]["has_target"]).sum())
            for t in sorted(truly_new)
        },
        "years_per_ticker": {
            t: sorted(pilot_rows_final[pilot_rows_final["ticker"] == t]["year"].tolist())
            for t in sorted(truly_new)
        },
        "source": YFINANCE_SOURCE,
        "disclaimer": DISCLAIMER,
        "caveats": [
            "yfinance is unofficial. KAP cross-check recommended.",
            "FY2020 and FY2021 not available for pilot tickers.",
            "Pilot tickers are training-only (is_public_universe=false).",
            "Cross-sectional ranks for pilot tickers computed within pilot cohort only.",
            "Run split_universe_datasets to update training/public splits.",
        ],
    }
    REPORT_OUT.write_text(json.dumps(report, indent=2))
    print(f"[integrate] Report: {REPORT_OUT.name}")
    print(f"\n{DISCLAIMER}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
