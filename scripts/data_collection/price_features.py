"""Leakage-safe year-T price features from cached Yahoo year-end prices."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
PRICES_CSV = REPO_ROOT / "data" / "trusted_raw" / "prices" / "yahoo_year_end_prices.csv"

PRICE_FEATURE_COLUMNS = [
    "price_adjclose_t",
    "price_data_available",
    "price_history_years_available",
    "price_momentum_1y_pct",
    "price_momentum_2y_pct",
    "price_drawdown_from_3y_high_pct",
    "benchmark_same_year_return_pct",
    "price_vs_bist100_1y_pct",
]


def build_price_features(
    prices_csv: Path = PRICES_CSV,
    benchmark: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return one row per ticker-year with features known by end of year T.

    Required input is cached Yahoo year-end adjusted close. Returns are computed
    from year-end prices at or before T, so no T+1 target data enters features.
    """
    if not prices_csv.is_file():
        return pd.DataFrame(columns=["ticker", "year", *PRICE_FEATURE_COLUMNS])

    p = pd.read_csv(prices_csv)
    if "adjclose" not in p.columns and "year_end_close" in p.columns:
        p["adjclose"] = p["year_end_close"]
    if "status" not in p.columns:
        p["status"] = "success"
    if not {"ticker", "year", "adjclose", "status"}.issubset(p.columns):
        return pd.DataFrame(columns=["ticker", "year", *PRICE_FEATURE_COLUMNS])
    p = p[p["status"].astype(str).str.lower().eq("success")].copy()
    p["ticker"] = p["ticker"].astype(str).str.strip().str.upper()
    p["year"] = pd.to_numeric(p["year"], errors="coerce")
    p["adjclose"] = pd.to_numeric(p["adjclose"], errors="coerce")
    p = p.dropna(subset=["ticker", "year", "adjclose"])
    p["year"] = p["year"].astype(int)
    p = p.sort_values(["ticker", "year"]).drop_duplicates(["ticker", "year"], keep="last")

    rows: list[dict] = []
    for ticker, grp in p.groupby("ticker"):
        s = grp.set_index("year")["adjclose"].sort_index()
        seen = 0
        for year, price in s.items():
            seen += 1
            prev1 = s.get(year - 1, np.nan)
            prev2 = s.get(year - 2, np.nan)
            last3 = s.loc[(s.index <= year) & (s.index >= year - 2)]
            high3 = float(last3.max()) if len(last3) else np.nan
            mom1 = (price / prev1 - 1) * 100 if pd.notna(prev1) and prev1 else np.nan
            mom2 = (price / prev2 - 1) * 100 if pd.notna(prev2) and prev2 else np.nan
            dd3 = (price / high3 - 1) * 100 if pd.notna(high3) and high3 else np.nan
            rows.append({
                "ticker": ticker,
                "year": int(year),
                "price_adjclose_t": round(float(price), 6),
                "price_data_available": 1.0,
                "price_history_years_available": float(seen),
                "price_momentum_1y_pct": round(float(mom1), 6) if pd.notna(mom1) else np.nan,
                "price_momentum_2y_pct": round(float(mom2), 6) if pd.notna(mom2) else np.nan,
                "price_drawdown_from_3y_high_pct": round(float(dd3), 6) if pd.notna(dd3) else np.nan,
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame(columns=["ticker", "year", *PRICE_FEATURE_COLUMNS])

    out["benchmark_same_year_return_pct"] = np.nan
    out["price_vs_bist100_1y_pct"] = np.nan
    if benchmark is not None and not benchmark.empty:
        b = benchmark[["year", "bist100_return_pct"]].copy()
        b["year"] = pd.to_numeric(b["year"], errors="coerce")
        b["bist100_return_pct"] = pd.to_numeric(b["bist100_return_pct"], errors="coerce")
        b = b.dropna(subset=["year", "bist100_return_pct"])
        b["year"] = b["year"].astype(int)
        out = out.merge(
            b.rename(columns={"bist100_return_pct": "benchmark_same_year_return_pct"}),
            on="year",
            how="left",
            suffixes=("", "_bench"),
        )
        if "benchmark_same_year_return_pct_bench" in out.columns:
            out["benchmark_same_year_return_pct"] = out.pop("benchmark_same_year_return_pct_bench")
        out["price_vs_bist100_1y_pct"] = (
            out["price_momentum_1y_pct"] - out["benchmark_same_year_return_pct"]
        )

    return out[["ticker", "year", *PRICE_FEATURE_COLUMNS]]
