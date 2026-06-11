"""Forecasting service backed by the validated CSV pipeline.

Uses the validated CSV pipeline:
  - training/model fitting: data/trusted_clean/modeling_dataset_training_2020_2025.csv
  - public options/ranking/explanations: data/trusted_clean/modeling_dataset_public_2020_2025.csv

This keeps the expanded yfinance training universe internal while exposing only
the validated public 40-company universe in the UI. This is a deterministic,
honest baseline:

  1. Training: identify top-quartile returners (historical winners) per year,
     measure per-feature discrimination power → normalised weights.
  2. Run: rank public-universe stocks for a given year using those weights and
     percentile-normalised feature values.

Guardrails:
  - Output is EXPERIMENTAL research support, NOT investment advice.
  - Missing values reduce confidence; they are never fabricated.
  - No buy/sell/hold signals or price targets.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from app.core.paths import resolve_repo_root

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_REPO_ROOT = resolve_repo_root()
_TRAINING_CSV = _REPO_ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
_PUBLIC_CSV = _REPO_ROOT / "data" / "trusted_clean" / "modeling_dataset_public_2020_2025.csv"
_BASE_CSV = _REPO_ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"

DISCLAIMER = "Experimental ranking signal — NOT investment advice. Do not use for buy/sell/hold decisions."

# Columns that are NOT predictive features
_NON_FEATURES = {
    "ticker", "company_name", "year", "sector", "indices", "is_bist100",
    "same_year_return_pct", "target_year", "has_target", "is_inference_row",
    "is_public_universe", "is_training_universe", "universe_source",
    "next_year_return_pct", "next_year_rank_by_return", "next_year_return_percentile",
    "next_year_top_10pct_returner", "next_year_top_20pct_returner",
    "next_year_bist100_return_pct", "next_year_excess_return_vs_bist100",
    "next_year_outperform_bist100",
}

_WINNER_PERCENTILE = 0.75   # top 25% by next-year return = winner


def _read_modeling_csv(path: Path, label: str) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(
            f"{label} dataset not found at {path}. Run `make full-research-agent`."
        )
    df = pd.read_csv(path)
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    return df


def _load_public_df() -> pd.DataFrame:
    """Public-facing 40-company universe for dropdowns, rankings, and explain."""
    p = _PUBLIC_CSV if _PUBLIC_CSV.is_file() else _BASE_CSV
    return _read_modeling_csv(p, "public modeling")


def _load_training_df() -> pd.DataFrame:
    """Internal training universe, expanded with yfinance training-only rows."""
    p = _TRAINING_CSV if _TRAINING_CSV.is_file() else _BASE_CSV
    return _read_modeling_csv(p, "training modeling")


def _load_df() -> pd.DataFrame:
    """Backward-compatible alias: public-facing data by default."""
    return _load_public_df()


def _feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in _NON_FEATURES and df[c].dtype in (float, int, "float64", "int64")]


def _num(v: Any) -> float | None:
    try:
        fv = float(v)
        return None if math.isnan(fv) or math.isinf(fv) else round(fv, 6)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_options() -> dict[str, Any]:
    """Return available years and feature columns from the CSV pipeline."""
    df = _load_df()
    feat_cols = _feature_cols(df)

    trainable = sorted(
        int(y) for y in df[df["has_target"].astype(str).str.lower().isin({"true", "1"})]["year"].unique()
    )
    all_years = sorted(int(y) for y in df["year"].unique())
    tickers = sorted(df["ticker"].unique().tolist())

    return {
        "available": True,
        "trainable_years": trainable,
        "all_years": all_years,
        "inference_years": [y for y in all_years if y not in trainable],
        "feature_columns": feat_cols,
        "ticker_count": len(tickers),
        "tickers": tickers,
        "data_source": "modeling_dataset_public_2020_2025.csv",
        "training_data_source": "modeling_dataset_training_2020_2025.csv",
        "note": "CSV-backed pipeline. Public options show 40 companies; training uses the expanded internal universe.",
    }


def train_parameters(
    train_year_from: int = 2020,
    train_year_to: int = 2024,
    top_n: int = 12,
) -> dict[str, Any]:
    """Compute feature weights from historical top-quartile returners.

    For each feature, compute the normalised discrimination power between
    winners (top-25% returners) and the rest, pooled across the training years.

    Returns ranked list of features with weights in [0, 1].
    """
    df = _load_training_df()
    feat_cols = _feature_cols(df)

    train_mask = (
        df["year"].between(train_year_from, train_year_to)
        & df["has_target"].astype(str).str.lower().isin({"true", "1"})
    )
    tdf = df[train_mask].copy()

    if tdf.empty:
        raise ValueError(
            f"No training data for {train_year_from}–{train_year_to}. "
            "Use years 2020–2024 for training (2025 has no next-year target)."
        )

    # Mark winners per year (top WINNER_PERCENTILE by next_year_return_pct)
    tdf["_winner"] = False
    for yr, grp in tdf.groupby("year"):
        threshold = grp["next_year_return_pct"].quantile(_WINNER_PERCENTILE)
        tdf.loc[grp.index, "_winner"] = grp["next_year_return_pct"] >= threshold

    winners = tdf[tdf["_winner"]]
    losers = tdf[~tdf["_winner"]]

    scores: dict[str, float] = {}
    feature_stats: list[dict] = []

    for col in feat_cols:
        w_vals = pd.to_numeric(winners[col], errors="coerce").dropna()
        l_vals = pd.to_numeric(losers[col], errors="coerce").dropna()
        all_vals = pd.to_numeric(tdf[col], errors="coerce").dropna()

        if len(w_vals) < 3 or len(all_vals) < 5:
            scores[col] = 0.0
            continue

        # Standardised mean difference (effect size)
        std = float(all_vals.std()) or 1.0
        effect = float(w_vals.mean() - all_vals.mean()) / std

        # Coverage among winners (fraction of winners with non-null value)
        coverage = len(w_vals) / max(1, len(winners))

        # Point-biserial-like correlation proxy
        mu_w = float(w_vals.mean())
        mu_l = float(l_vals.mean()) if len(l_vals) else mu_w
        mu_a = float(all_vals.mean())
        sd_a = std

        raw_score = max(0.0, abs(effect)) * coverage
        scores[col] = raw_score

        feature_stats.append({
            "name": col,
            "raw_score": round(raw_score, 4),
            "winner_mean": round(mu_w, 4),
            "non_winner_mean": round(mu_l, 4),
            "overall_mean": round(mu_a, 4),
            "effect_size": round(effect, 4),
            "coverage": round(coverage, 4),
        })

    if not scores or max(scores.values()) == 0:
        raise ValueError("No discriminating features found. Check training data coverage.")

    max_score = max(scores.values())
    normalised = {col: round(v / max_score, 4) for col, v in scores.items()}

    ranked = sorted(normalised.items(), key=lambda x: x[1], reverse=True)
    top = ranked[:top_n]

    return {
        "train_year_from": train_year_from,
        "train_year_to": train_year_to,
        "top_n_requested": top_n,
        "winner_percentile": _WINNER_PERCENTILE,
        "winner_rows": int(len(winners)),
        "total_training_rows": int(len(tdf)),
        "top_parameters": [
            {"name": col, "weight": w, "rank": i + 1}
            for i, (col, w) in enumerate(top)
        ],
        "all_feature_stats": {
            s["name"]: {k: v for k, v in s.items() if k != "name"}
            for s in feature_stats
        },
        "disclaimer": DISCLAIMER,
    }


def run_forecast(
    year: int,
    trained_weights: dict[str, float],
    risk_level: str = "medium",
    user_type: str = "individual",
) -> dict[str, Any]:
    """Rank public-universe stocks for the given year using trained weights.

    Scoring:
      for each feature f:
        rank_pct(stock, f, year) = percentile of the stock's value among all
                                   stocks in that year (0=worst, 1=best)
        contribution(f) = weight(f) * rank_pct
      score = sum(contributions) / sum(weights used)
    Confidence = fraction of top-weighted features with non-null value.
    """
    df = _load_df()
    year_df = df[df["year"] == year].copy()

    if year_df.empty:
        raise ValueError(f"No data for year {year}. Available years: {sorted(df['year'].unique().tolist())}")

    if not trained_weights:
        raise ValueError("trained_weights is empty. Run /forecasting/train first.")

    used_cols = sorted(trained_weights.keys())
    weight_sum = sum(trained_weights[c] for c in used_cols) or 1.0

    risk_factor = {"low": 0.90, "medium": 1.0, "high": 1.10}.get(risk_level.lower(), 1.0)

    # Precompute within-year percentiles for each feature
    pct_maps: dict[str, dict[str, float]] = {}
    for col in used_cols:
        if col not in year_df.columns:
            pct_maps[col] = {}
            continue
        numeric = pd.to_numeric(year_df[col], errors="coerce")
        total_non_null = numeric.notna().sum()
        if total_non_null < 2:
            pct_maps[col] = {}
            continue
        ranked = numeric.rank(pct=True, na_option="keep")
        pct_maps[col] = {
            str(row["ticker"]).upper(): float(ranked.loc[idx])
            for idx, row in year_df.iterrows()
            if pd.notna(ranked.loc[idx])
        }

    scored: list[dict[str, Any]] = []
    for _, row in year_df.iterrows():
        ticker = str(row["ticker"]).upper()
        contribs: list[dict] = []
        total = 0.0
        valid_count = 0

        for col in used_cols:
            w = trained_weights[col]
            pct = pct_maps.get(col, {}).get(ticker)
            if pct is None:
                continue
            c = w * pct
            contribs.append({
                "name": col,
                "weight": round(w, 4),
                "value": _num(row.get(col)),
                "percentile_in_year": round(pct * 100, 1),
                "contribution": round(c, 4),
            })
            total += c
            valid_count += 1

        score = (total / weight_sum) * risk_factor
        score = max(0.0, min(1.0, score))
        confidence = valid_count / max(1, len(used_cols))
        conf_label = "high" if confidence >= 0.80 else "medium" if confidence >= 0.50 else "low"
        contribs.sort(key=lambda x: x["contribution"], reverse=True)

        missing = [c for c in used_cols if c not in (ct["name"] for ct in contribs)]

        scored.append({
            "ticker": ticker,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "confidence_label": conf_label,
            "top_parameters": contribs[:5],
            "missing_parameters": missing,
            "is_inference_row": bool(row.get("is_inference_row", False)),
            "warnings": [
                DISCLAIMER,
                *(["Some features missing — confidence reduced."] if missing else []),
                *(["2025 is inference-only: no next-year return target exists."] if int(row["year"]) == 2025 else []),
            ],
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(scored, start=1):
        item["rank"] = i

    return {
        "year": year,
        "user_type": user_type,
        "risk_level": risk_level,
        "stock_count": len(scored),
        "items": scored,
        "disclaimer": DISCLAIMER,
    }


def explain_ticker(ticker: str, year: int | None = None) -> dict[str, Any]:
    """Return per-stock structured explanation for the latest (or given) year."""
    df = _load_df()
    t = ticker.upper()
    sub = df[df["ticker"] == t]
    if sub.empty:
        raise KeyError(f"Ticker {t!r} not in public universe.")

    if year is None:
        year = int(sub["year"].max())

    row_df = sub[sub["year"] == year]
    if row_df.empty:
        raise KeyError(f"No data for {t} year {year}.")

    row = row_df.iloc[0]
    feat_cols = _feature_cols(df)
    year_df = df[df["year"] == year]

    features: list[dict] = []
    missing: list[str] = []

    for col in feat_cols:
        v = _num(row.get(col))
        if v is None:
            missing.append(col)
            continue
        series = pd.to_numeric(year_df[col], errors="coerce").dropna()
        if len(series) < 2:
            continue
        pct = round(float((series < v).mean() * 100), 1)
        features.append({
            "name": col,
            "value": v,
            "percentile_in_year": pct,
            "signal": "above_median" if pct >= 50 else "below_median",
        })

    features.sort(key=lambda x: x["percentile_in_year"], reverse=True)

    return {
        "ticker": t,
        "year": year,
        "is_inference_row": bool(row.get("is_inference_row", False)),
        "top_features": features[:8],
        "bottom_features": features[-4:] if len(features) > 4 else [],
        "missing_features": missing,
        "feature_count": len(features),
        "missing_count": len(missing),
        "data_quality": {
            "coverage": round(len(features) / max(1, len(feat_cols)), 3),
            "missing_fields": missing,
        },
        "guardrails": {
            "not_investment_advice": True,
            "no_buy_sell_recommendation": True,
            "research_support_only": True,
        },
        "disclaimer": DISCLAIMER,
    }
