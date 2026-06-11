"""Fundamental + Market-Aware scoring (PHASE 3).

Cross-sectional rank normalization within each year:
  * For every feature, rank companies into a percentile [0, 1].
  * LOWER_BETTER features are inverted so 1.0 is always "best".
  * Value multiples are ranked only over positive values (negative P/E etc.
    are treated as missing, not "cheap").
  * Missing values are excluded from the rank and tracked as missingness;
    they are never filled with fake zeros.
  * A category score is the mean of its available feature percentiles.
  * The Fundamental Score is the mean of category scores, scaled to 0..100.

Rank normalization is robust to the dataset's extreme outliers (e.g. growth %
in the trillions) without discarding real data.

The Fundamental Score never uses any realized-return column. The Market-Aware
Score uses only momentum windows and is reported separately.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.research import data, feature_registry as reg


def compute_derived(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ("revenue", "free_cash_flow", "net_income", "ocf", "market_cap"):
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # FCF margin: only where revenue is positive (else undefined, not 0).
    df["fcf_margin_pct"] = (df["free_cash_flow"] / df["revenue"] * 100.0).where(df["revenue"] > 0)
    # Cash-flow earnings quality: OCF / Net Income, only where NI != 0.
    df["cfo_to_net_income"] = (df["ocf"] / df["net_income"]).where(df["net_income"] != 0)
    # Size: log market cap, only where positive.
    df["log_market_cap"] = np.log(df["market_cap"].where(df["market_cap"] > 0))
    return df


def _percentile(series: pd.Series, feat: reg.Feature) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if feat.positive_only:
        s = s.where(s > 0)
    # average rank percentile in [0,1]; NaN stays NaN (tracked as missing)
    pct = s.rank(method="average", pct=True)
    if feat.direction == reg.LOWER_BETTER:
        pct = 1.0 - pct
    return pct


def _category_scores(df: pd.DataFrame, feats: list[reg.Feature]) -> tuple[pd.DataFrame, dict]:
    """Return per-feature percentile frame + category->feature-name map."""
    cats: dict[str, list[str]] = {}
    pct_cols = {}
    for f in feats:
        if f.name not in df.columns:
            continue
        pct_cols[f.name] = _percentile(df[f.name], f)
        cats.setdefault(f.category, []).append(f.name)
    pct_df = pd.DataFrame(pct_cols, index=df.index)
    return pct_df, cats


def score_year(year: int) -> pd.DataFrame:
    """Score every company in a year. Returns one row per ticker."""
    raw = data.year_frame(year)
    df = compute_derived(raw)

    f_feats = reg.fundamental_features()
    m_feats = reg.market_features()

    f_pct, f_cats = _category_scores(df, f_feats)
    m_pct, m_cats = _category_scores(df, m_feats)

    out = pd.DataFrame({"ticker": df["ticker"], "year": year})

    # Category means (skip missing), then overall mean of categories.
    f_cat_scores = {}
    for cat, names in f_cats.items():
        f_cat_scores[cat] = f_pct[names].mean(axis=1, skipna=True)
        out[f"cat_{cat}"] = (f_cat_scores[cat] * 100).round(2)
    fundamental = pd.concat(f_cat_scores.values(), axis=1).mean(axis=1, skipna=True)
    out["fundamental_score"] = (fundamental * 100).round(2)

    if m_cats:
        market = m_pct.mean(axis=1, skipna=True)
        out["market_score"] = (market * 100).round(2)
    else:
        out["market_score"] = np.nan

    # Missingness: fraction of fundamental features unavailable per company.
    avail = f_pct.notna().sum(axis=1)
    total = max(len(f_pct.columns), 1)
    out["fundamental_missingness"] = (1 - avail / total).round(3)

    # Realized ground truth carried through (NOT used in scoring).
    out[data.TARGET_COLUMN] = pd.to_numeric(df[data.TARGET_COLUMN], errors="coerce")

    # Ranks (1 = best). Score rank desc, return rank desc.
    out["score_rank"] = out["fundamental_score"].rank(ascending=False, method="min")
    out["return_rank"] = out[data.TARGET_COLUMN].rank(ascending=False, method="min")
    out["score_rank"] = out["score_rank"].astype("Int64")
    out["return_rank"] = out["return_rank"].astype("Int64")
    return out


def explain(ticker: str, year: int) -> dict:
    """Per-category contributions + per-feature percentile for one company."""
    raw = data.year_frame(year)
    df = compute_derived(raw)
    ticker = ticker.strip().upper()
    if ticker not in set(df["ticker"]):
        raise ValueError(f"{ticker} not in trusted data for {year}.")

    f_pct, f_cats = _category_scores(df, reg.fundamental_features())
    idx = df.index[df["ticker"] == ticker][0]

    categories = []
    for cat, names in f_cats.items():
        feats = []
        for n in names:
            v = f_pct.at[idx, n]
            feats.append({
                "feature": n,
                "percentile": None if pd.isna(v) else round(float(v) * 100, 1),
                "raw": None if pd.isna(df.at[idx, n]) else float(df.at[idx, n]),
            })
        cat_pct = f_pct.loc[idx, names].mean(skipna=True)
        categories.append({
            "category": cat,
            "category_score": None if pd.isna(cat_pct) else round(float(cat_pct) * 100, 1),
            "features": feats,
        })
    return {"ticker": ticker, "year": year, "categories": categories}
