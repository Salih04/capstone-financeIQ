"""Company detail + research dashboard aggregation (PHASE 7 / 8)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.research import benchmark, data, scoring, validation

TARGET = data.TARGET_COLUMN

# Key raw metrics surfaced on the detail panel.
_KEY_METRICS = (
    "price", "market_cap", "pe", "pb", "roe_pct", "roa_pct", "roic_pct",
    "net_margin_pct", "ebitda_margin_pct", "revenue_growth_pct",
    "net_income_growth_pct", "current_ratio", "leverage_ratio",
    "net_income", "operating_income", "ebitda", "free_cash_flow", "revenue",
)


def _f(v):
    return None if v is None or pd.isna(v) else float(v)


def year_overview(year: int) -> dict:
    """All companies for a year: scores + realized return (scatter + table)."""
    scored = scoring.score_year(year)
    rows = []
    for _, r in scored.iterrows():
        rows.append({
            "ticker": r["ticker"],
            "fundamental_score": _f(r["fundamental_score"]),
            "market_score": _f(r["market_score"]),
            "realized_return": _f(r[TARGET]),
            "score_rank": None if pd.isna(r["score_rank"]) else int(r["score_rank"]),
            "return_rank": None if pd.isna(r["return_rank"]) else int(r["return_rank"]),
            "missingness": _f(r["fundamental_missingness"]),
        })
    return {
        "year": year,
        "count": len(rows),
        "benchmark_available": benchmark.is_available(),
        "bist100_return": benchmark.year_return(year),
        "companies": rows,
    }


def company_detail(ticker: str, year: int) -> dict:
    ticker = ticker.strip().upper()
    raw = data.year_frame(year)
    if ticker not in set(raw["ticker"]):
        raise ValueError(f"{ticker} not in trusted data for {year}.")

    scored = scoring.score_year(year).set_index("ticker")
    row = scored.loc[ticker]
    raw_row = raw.set_index("ticker").loc[ticker]

    ret = _f(row[TARGET])
    bist = benchmark.year_return(year)
    excess = None if (bist is None or ret is None) else round(ret - bist, 2)

    best_ticker = scored[TARGET].idxmax()
    best_ret = _f(scored[TARGET].max())
    gap_to_best = None if (ret is None or best_ret is None) else round(best_ret - ret, 2)

    return {
        "ticker": ticker,
        "year": year,
        "fundamental_score": _f(row["fundamental_score"]),
        "market_score": _f(row["market_score"]),
        "missingness": _f(row["fundamental_missingness"]),
        "realized_return": ret,
        "bist100_return": bist,
        "excess_vs_bist100": excess,
        "outperformed_bist100": None if excess is None else excess > 0,
        "return_rank": None if pd.isna(row["return_rank"]) else int(row["return_rank"]),
        "score_rank": None if pd.isna(row["score_rank"]) else int(row["score_rank"]),
        "total_companies": int(len(scored)),
        "best_performer": {"ticker": best_ticker, "return": best_ret},
        "gap_to_best": gap_to_best,
        "profit_status": {
            "net_income_positive": None if pd.isna(raw_row.get("net_income")) else bool(raw_row["net_income"] > 0),
            "operating_income_positive": None if pd.isna(raw_row.get("operating_income")) else bool(raw_row["operating_income"] > 0),
            "ebitda_positive": None if pd.isna(raw_row.get("ebitda")) else bool(raw_row["ebitda"] > 0),
            "fcf_positive": None if pd.isna(raw_row.get("free_cash_flow")) else bool(raw_row["free_cash_flow"] > 0),
        },
        "key_metrics": {m: _f(raw_row.get(m)) for m in _KEY_METRICS if m in raw.columns},
        "score_breakdown": scoring.explain(ticker, year)["categories"],
    }


def dashboard() -> dict:
    """Model-quality summary across all years (PHASE 8)."""
    v = validation.validate_all()
    variability = data.column_variability()
    # Mismatch cases for the most recent year: high score / low return etc.
    latest = max(data.available_years())
    scored = scoring.score_year(latest).dropna(subset=["fundamental_score", TARGET])
    scored = scored.sort_values("fundamental_score", ascending=False)
    top_score = scored.head(5)[["ticker", "fundamental_score", TARGET, "return_rank"]]
    top_return = scored.sort_values(TARGET, ascending=False).head(5)[
        ["ticker", "fundamental_score", TARGET, "score_rank"]
    ]
    return {
        "validation": v,
        "benchmark": benchmark.status(),
        "latest_year": latest,
        "top_score_stocks": top_score.round(2).to_dict("records"),
        "top_return_stocks": top_return.round(2).to_dict("records"),
        "column_variability": variability,
        "data_note": (
            "DATA INTEGRITY: this dataset is inconsistent. Income-statement, "
            "valuation and momentum fields (revenue, net income, margins, ROE/ROA, "
            "P/E, price, market cap, returns) are a FROZEN 2025 snapshot repeated "
            "in every yearly file, while balance-sheet, leverage, growth %, and the "
            "realized annual return genuinely vary by year. The Fundamental Score "
            "therefore only partly varies across years. Treat per-year fundamental "
            "trends with caution."
        ),
        "disclaimer": (
            "Same-year correlation is EXPLANATORY, not predictive. Not financial advice."
        ),
    }
