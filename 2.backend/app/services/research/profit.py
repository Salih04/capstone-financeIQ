"""Profit-consistency check (PHASE 5).

Joins, for each company-year: profitability flags from the financial
statements, the Fundamental Score, the realized return and its rank, and (if a
benchmark is configured) BIST100-relative performance.

Answers directly: "statements show profit and our score says strong -- did the
stock actually perform?"
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.research import benchmark, data, scoring

TARGET = data.TARGET_COLUMN


def _flag(v) -> bool | None:
    return None if pd.isna(v) else bool(v > 0)


def profit_table(year: int) -> pd.DataFrame:
    raw = data.year_frame(year)
    scored = scoring.score_year(year).set_index("ticker")
    bench = benchmark.year_return(year)  # None if missing

    rows = []
    for _, r in raw.iterrows():
        t = r["ticker"]
        ret = pd.to_numeric(pd.Series([r[TARGET]]), errors="coerce").iloc[0]
        s = scored.loc[t] if t in scored.index else None
        excess = None if (bench is None or pd.isna(ret)) else round(float(ret - bench), 2)
        rows.append({
            "ticker": t,
            "year": year,
            "net_income_positive": _flag(r.get("net_income")),
            "operating_income_positive": _flag(r.get("operating_income")),
            "ebitda_positive": _flag(r.get("ebitda")),
            "fcf_positive": _flag(r.get("free_cash_flow")),
            "fundamental_score": None if s is None or pd.isna(s["fundamental_score"]) else float(s["fundamental_score"]),
            "realized_return": None if pd.isna(ret) else round(float(ret), 2),
            "return_rank": None if s is None or pd.isna(s["return_rank"]) else int(s["return_rank"]),
            "excess_vs_bist100": excess,
        })
    return pd.DataFrame(rows)


def _bucket(row, score_median, ret_median) -> str:
    hs = row["fundamental_score"] is not None and row["fundamental_score"] >= score_median
    hr = row["realized_return"] is not None and row["realized_return"] >= ret_median
    profit = bool(row["net_income_positive"])
    if hs and hr and profit:
        return "high_score_profit_strong_return"
    if hs and profit and not hr:
        return "high_score_profit_weak_return"
    if not hs and not hr:
        return "low_score_weak_return"
    if not hs and hr:
        return "low_score_strong_return"
    if profit and not hr:
        return "profitable_but_underperformed"
    if not profit and hr:
        return "unprofitable_but_outperformed"
    return "other"


def profit_consistency(year: int) -> dict:
    df = profit_table(year)
    score_median = df["fundamental_score"].median(skipna=True)
    ret_median = df["realized_return"].median(skipna=True)
    df["bucket"] = df.apply(lambda r: _bucket(r, score_median, ret_median), axis=1)
    counts = df["bucket"].value_counts().to_dict()
    return {
        "year": year,
        "benchmark_available": benchmark.year_return(year) is not None,
        "buckets": counts,
        "rows": df.to_dict("records"),
    }
