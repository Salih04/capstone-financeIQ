"""Build per-company structured context JSON files for the RAG layer.

Reads from validated pipeline outputs (public universe only). Output is used
by the research agent's LLM layer as structured context — never investment advice.

Outputs: data/trusted_clean/company_contexts/{TICKER}_{YEAR}.json

Run:
    PYTHONPATH=. python scripts/build_company_contexts.py [--year 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from io import StringIO
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
CLEAN_DIR = REPO_ROOT / "data" / "trusted_clean"
CONFIG_DIR = REPO_ROOT / "data" / "config"
CONTEXTS_DIR = CLEAN_DIR / "company_contexts"

PUBLIC_UNIVERSE_CSV = CONFIG_DIR / "universe_public_40.csv"
PUBLIC_MODELING = CLEAN_DIR / "modeling_dataset_public_2020_2025.csv"
FALLBACK_MODELING = CLEAN_DIR / "modeling_dataset_2020_2025.csv"
MODEL_OUTPUTS = REPO_ROOT / "experiments" / "results" / "research_agent_model_outputs.csv"
QUALITY_JSON = CLEAN_DIR / "data_quality_report.json"
FREE_VALUATION_REPORT = CLEAN_DIR / "free_valuation_history_report.json"

FINANCIAL_COLS = ["revenue", "net_income", "equity", "ebitda", "roe", "roa",
                  "gross_profit", "operating_income", "net_margin", "gross_margin",
                  "ebitda_margin"]
VALUATION_COLS = ["market_cap", "enterprise_value", "pe_ratio", "pb_ratio", "ev_ebitda"]

MODEL_LIMITATIONS = [
    "small_sample (~40 stocks/year)",
    "walk-forward Spearman near zero (no reliable predictive edge)",
    "valuation features may be from frozen snapshot for some years",
    "no guaranteed future return prediction",
]


def _load_universe(csv_path: Path) -> set[str]:
    if not csv_path.is_file():
        return set()
    lines = [ln for ln in csv_path.read_text().splitlines() if not ln.strip().startswith("#")]
    df = pd.read_csv(StringIO("\n".join(lines)))
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    if "is_public_universe" in df.columns:
        df["is_public_universe"] = df["is_public_universe"].astype(str).str.lower().isin({"true", "1", "yes"})
        return set(df[df["is_public_universe"]]["ticker"])
    return set(df["ticker"])


def _num(v) -> float | None:
    try:
        fv = float(v)
        import math
        return None if math.isnan(fv) else round(fv, 4)
    except (TypeError, ValueError):
        return None


def _load_model_outputs() -> dict[str, dict]:
    """Returns {ticker: {ml_score, ml_rank, year}} for latest year per ticker."""
    if not MODEL_OUTPUTS.is_file():
        return {}
    try:
        mo = pd.read_csv(MODEL_OUTPUTS)
        mo["ticker"] = mo["ticker"].astype(str).str.upper()
        out = {}
        for t, grp in mo.groupby("ticker"):
            row = grp.sort_values("year").iloc[-1]
            out[t] = {
                "ml_score": _num(row.get("ml_score")),
                "ml_rank": int(row["ml_rank"]) if pd.notna(row.get("ml_rank")) else None,
            }
        return out
    except Exception:
        return {}


def _year_medians(df: pd.DataFrame, year: int, cols: list[str]) -> dict:
    sub = df[df["year"] == year]
    out = {}
    for c in cols:
        if c in sub.columns:
            v = _num(sub[c].median())
            if v is not None:
                out[c] = v
    return out


def _percentile_in_year(df: pd.DataFrame, year: int, ticker: str, cols: list[str]) -> dict:
    sub = df[df["year"] == year]
    row = sub[sub["ticker"] == ticker]
    if row.empty:
        return {}
    out = {}
    for c in cols:
        if c not in sub.columns:
            continue
        v = _num(row.iloc[0].get(c))
        if v is None:
            continue
        series = pd.to_numeric(sub[c], errors="coerce").dropna()
        if len(series) < 2:
            continue
        pct = round(float((series < v).mean() * 100), 1)
        out[c] = pct
    return out


def build_context(ticker: str, year: int, df: pd.DataFrame,
                  model_outputs: dict, public_tickers: set) -> dict:
    t = ticker.upper()
    sub = df[(df["ticker"] == t) & (df["year"] == year)]

    is_public = t in public_tickers

    if sub.empty:
        row_data: dict = {}
    else:
        row_data = sub.iloc[0].to_dict()

    def _get(col):
        return _num(row_data.get(col))

    ml_info = model_outputs.get(t, {})

    # Financials
    financials = {c: _get(c) for c in FINANCIAL_COLS}

    # Valuation — map pipeline column names to context names
    col_map = {"pe_ratio": "pe_ratio", "pb_ratio": "pb_ratio", "ev_ebitda": "ev_ebitda",
               "market_cap": "market_cap", "enterprise_value": "enterprise_value"}
    valuation_vals = {name: _get(col) for name, col in col_map.items()}

    # Data quality
    missing_fields = [c for c, v in {**financials, **valuation_vals}.items() if v is None]
    warnings = []
    if sub.empty:
        warnings.append(f"no data row for {t} year {year}")
    if row_data.get("is_inference_row"):
        warnings.append("inference_row: no T+1 target available (2025 is latest year)")

    # Benchmark percentiles for public companies
    feature_cols = FINANCIAL_COLS + list(col_map.values())
    percentiles = _percentile_in_year(df, year, t, feature_cols)
    medians = _year_medians(df, year, feature_cols)

    return {
        "ticker": t,
        "year": year,
        "universe": {
            "is_public_universe": is_public,
            "is_training_universe": bool(row_data.get("is_training_universe", is_public)),
        },
        "model": {
            "ml_score": ml_info.get("ml_score"),
            "ml_rank": ml_info.get("ml_rank"),
            "target_definition": "year-T features -> year-(T+1) realized return",
            "model_limitations": MODEL_LIMITATIONS,
        },
        "financials": financials,
        "valuation": {
            **valuation_vals,
            "price_source": "yahoo_chart_api",
            "price_date": f"{year}-12-31 (approximate year-end)",
        },
        "benchmarks": {
            "training_universe_percentiles": percentiles,
            "year_medians": medians,
        },
        "data_quality": {
            "missing_fields": missing_fields,
            "warnings": warnings,
            "has_data_row": not sub.empty,
        },
        "guardrails": {
            "not_investment_advice": True,
            "no_buy_sell_recommendation": True,
            "research_support_only": True,
        },
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=None,
                    help="Build contexts for this year only (default: all years in dataset)")
    ap.add_argument("--ticker", type=str, default=None,
                    help="Build context for this ticker only")
    args = ap.parse_args(argv)

    modeling_path = PUBLIC_MODELING if PUBLIC_MODELING.is_file() else FALLBACK_MODELING
    if not modeling_path.is_file():
        print(f"[contexts] ERROR: no modeling dataset found. Run `make data && make split-datasets` first.",
              file=sys.stderr)
        return 1

    public_tickers = _load_universe(PUBLIC_UNIVERSE_CSV)
    df = pd.read_csv(modeling_path)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()

    # Only public tickers in context output
    if public_tickers:
        df = df[df["ticker"].isin(public_tickers)]

    model_outputs = _load_model_outputs()
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)

    years = [args.year] if args.year else sorted(df["year"].unique().tolist())
    tickers = [args.ticker.upper()] if args.ticker else sorted(df["ticker"].unique().tolist())

    count = 0
    for year in years:
        for ticker in tickers:
            ctx = build_context(ticker, int(year), df, model_outputs, public_tickers)
            out_path = CONTEXTS_DIR / f"{ticker}_{year}.json"
            out_path.write_text(json.dumps(ctx, indent=2))
            count += 1

    print(f"[contexts] wrote {count} context files to {CONTEXTS_DIR}")
    print(f"[contexts] public universe: {len(public_tickers)} tickers, years: {years}")
    if model_outputs:
        ml_present = sum(1 for v in model_outputs.values() if v.get("ml_score") is not None)
        print(f"[contexts] ml_score available: {ml_present}/{len(model_outputs)} tickers")
    else:
        print("[contexts] ml_score: not available (run experiments first)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
