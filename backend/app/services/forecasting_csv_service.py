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

DISCLAIMER = "Experimental ranking signal — research support only, NOT investment advice. Do not use for buy/sell/hold decisions."

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

# ---------------------------------------------------------------------------
# Target horizon: finalized annual (default) vs experimental partial 2025
# ---------------------------------------------------------------------------
# The finalized methodology is T financials -> T+1 FULL-YEAR realized return.
# 2020–2024 have finalized T+1 targets; 2025's T+1 target (full-year 2026) does
# not exist yet, so 2025 is inference-only by default.
#
# OPTIONAL experimental mode: include 2025 using a PARTIAL 2026 year-to-date
# return as a stand-in target. This is clearly labeled, never comparable to the
# finalized annual targets, and only available when real 2026 YTD data is present
# in the repo. No fabrication: if the source file is absent, partial mode reports
# unavailable and 2025 stays excluded.
FINALIZED_TRAIN_YEAR_TO = 2024
PARTIAL_YEAR = 2025
PARTIAL_TARGET_YEAR = 2026
TARGET_MODE_FINALIZED = "finalized_only"
TARGET_MODE_PARTIAL = "include_partial_2025"
VALID_TARGET_MODES = (TARGET_MODE_FINALIZED, TARGET_MODE_PARTIAL)
PARTIAL_TARGET_WARNING = (
    "2025 uses partial 2026 YTD return and is not directly comparable to "
    "finalized annual targets."
)
# Expected experimental source file (NOT committed; absent by default).
# Required columns: ticker, year(=2025), target_year(=2026),
# partial_ytd_return_pct, as_of_date, source.
PARTIAL_2026_YTD_CSV = (
    _REPO_ROOT / "data" / "trusted_clean" / "partial_2026_ytd_returns.csv"
)
_PARTIAL_REQUIRED_COLS = {"ticker", "partial_ytd_return_pct"}
PARTIAL_DATA_REQUIREMENT = (
    f"Expected file {PARTIAL_2026_YTD_CSV.name} in data/trusted_clean/ with columns "
    "[ticker, year=2025, target_year=2026, partial_ytd_return_pct, as_of_date, source]. "
    "partial_ytd_return_pct = (latest_2026_close / 2025_year_end_close - 1) * 100 from "
    "real Yahoo/official 2026 prices. Do not fabricate."
)


def normalize_target_mode(target_mode: str | None) -> str:
    tm = (target_mode or TARGET_MODE_FINALIZED).strip().lower()
    return tm if tm in VALID_TARGET_MODES else TARGET_MODE_FINALIZED


def partial_target_status() -> dict[str, Any]:
    """Report whether real 2025 -> 2026 YTD partial-target data is available.

    Never fabricates. Returns availability + reason and (when present) the
    as-of date / source / ticker count read from the experimental CSV.
    """
    p = PARTIAL_2026_YTD_CSV
    if not p.is_file():
        return {
            "available": False,
            "reason": "Partial 2026 YTD target data is not available in the repository.",
            "data_requirement": PARTIAL_DATA_REQUIREMENT,
            "source_file": str(p),
        }
    try:
        pt = pd.read_csv(p)
    except Exception as exc:  # unreadable file is treated as unavailable, not fatal
        return {
            "available": False,
            "reason": f"Partial 2026 YTD file could not be read ({type(exc).__name__}).",
            "data_requirement": PARTIAL_DATA_REQUIREMENT,
            "source_file": str(p),
        }
    missing = _PARTIAL_REQUIRED_COLS - set(pt.columns)
    valid = pt["partial_ytd_return_pct"].notna().sum() if "partial_ytd_return_pct" in pt.columns else 0
    if missing or valid == 0:
        return {
            "available": False,
            "reason": (
                f"Partial 2026 YTD file missing required columns {sorted(missing)}."
                if missing else "Partial 2026 YTD file has no usable return values."
            ),
            "data_requirement": PARTIAL_DATA_REQUIREMENT,
            "source_file": str(p),
        }
    as_of = str(pt["as_of_date"].dropna().max()) if "as_of_date" in pt.columns and pt["as_of_date"].notna().any() else None
    source = str(pt["source"].dropna().iloc[0]) if "source" in pt.columns and pt["source"].notna().any() else None
    return {
        "available": True,
        "reason": None,
        "as_of_date": as_of,
        "source": source,
        "ticker_count": int(valid),
        "source_file": str(p),
    }


def target_metadata(target_mode: str, partial_available: bool) -> dict[str, Any]:
    """Explicit target-horizon metadata for the active mode."""
    if target_mode == TARGET_MODE_PARTIAL and partial_available:
        return {
            "mode": TARGET_MODE_PARTIAL,
            "finalized_annual_target": {
                "years": "2020-2024",
                "target_status": "finalized_annual",
                "comparable_to_full_year": True,
            },
            "partial_ytd_target": {
                "year": PARTIAL_YEAR,
                "target_year": PARTIAL_TARGET_YEAR,
                "target_status": "partial_ytd",
                "target_label": "2026 YTD partial return",
                "comparable_to_full_year": False,
                "warning": PARTIAL_TARGET_WARNING,
            },
        }
    return {
        "mode": TARGET_MODE_FINALIZED,
        "finalized_annual_target": {
            "years": "2020-2024",
            "target_status": "finalized_annual",
            "target_label": "T+1 finalized full-year realized return",
            "comparable_to_full_year": True,
        },
    }


def resolve_target_years(target_mode: str, finalized_trainable: list[int]) -> dict[str, Any]:
    """Decide training years + exclusions for the active target mode.

    Finalized years (2020–2024) are always the baseline. 2025 is added ONLY when
    partial mode is requested AND real partial data exists.
    """
    mode = normalize_target_mode(target_mode)
    finalized = [y for y in finalized_trainable if y <= FINALIZED_TRAIN_YEAR_TO]
    excluded: list[dict[str, Any]] = []
    includes_partial = False
    status = {"available": False, "reason": None}

    if mode == TARGET_MODE_PARTIAL:
        status = partial_target_status()
        if status["available"]:
            includes_partial = True
            training_years = sorted(set(finalized) | {PARTIAL_YEAR})
        else:
            training_years = finalized
            excluded.append({"year": PARTIAL_YEAR, "reason": status["reason"]})
    else:
        training_years = finalized
        # 2025 is intentionally inference-only under the finalized methodology.
        excluded.append({
            "year": PARTIAL_YEAR,
            "reason": "Inference-only under finalized methodology: full-year 2026 T+1 target not available.",
        })

    return {
        "target_mode": mode,
        "training_years": training_years,
        "includes_partial_targets": includes_partial,
        "partial_target_warning": PARTIAL_TARGET_WARNING if includes_partial else None,
        "excluded_years": excluded,
        "partial_status": status,
        "target_metadata": target_metadata(mode, includes_partial),
    }


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

def get_options(target_mode: str = TARGET_MODE_FINALIZED) -> dict[str, Any]:
    """Return available years and feature columns from the CSV pipeline.

    ``trainable_years`` always reflects the FINALIZED methodology (2020–2024) so
    2025 never renders as a normal finalized training year. ``training_years`` is
    mode-aware and only includes 2025 when partial mode is on AND real partial
    2026 YTD data exists.
    """
    mode = normalize_target_mode(target_mode)
    df = _load_df()
    feat_cols = _feature_cols(df)

    finalized_trainable = sorted(
        int(y) for y in df[df["has_target"].astype(str).str.lower().isin({"true", "1"})]["year"].unique()
    )
    all_years = sorted(int(y) for y in df["year"].unique())
    tickers = sorted(df["ticker"].unique().tolist())

    resolved = resolve_target_years(mode, finalized_trainable)

    return {
        "available": True,
        # Finalized-only trainable years — unchanged contract, never includes 2025.
        "trainable_years": [y for y in finalized_trainable if y <= FINALIZED_TRAIN_YEAR_TO],
        "all_years": all_years,
        "inference_years": [y for y in all_years if y > FINALIZED_TRAIN_YEAR_TO],
        "default_prediction_year": PARTIAL_YEAR,
        "default_target_year": PARTIAL_TARGET_YEAR,
        "inference_explanation": (
            f"{PARTIAL_YEAR} is excluded from finalized training because its "
            f"{PARTIAL_TARGET_YEAR} realized return is unavailable, but it is used as "
            f"inference input for the {PARTIAL_TARGET_YEAR} forecast."
        ),
        "feature_columns": feat_cols,
        "ticker_count": len(tickers),
        "tickers": tickers,
        "data_source": "modeling_dataset_public_2020_2025.csv",
        "training_data_source": "modeling_dataset_training_2020_2025.csv",
        "note": "CSV-backed pipeline. Public options show 40 companies; training uses the expanded internal universe.",
        # ── target-horizon block ──
        "target_mode": resolved["target_mode"],
        "training_years": resolved["training_years"],
        "includes_partial_targets": resolved["includes_partial_targets"],
        "partial_target_warning": resolved["partial_target_warning"],
        "available_years": all_years,
        "excluded_years": resolved["excluded_years"],
        "partial_target_status": resolved["partial_status"],
        "target_metadata": resolved["target_metadata"],
        "partial_mode_supported": True,
    }


def _merge_partial_2025_target(df: pd.DataFrame) -> pd.DataFrame:
    """Inject REAL partial 2026 YTD return into 2025 rows' target column.

    Reads ``PARTIAL_2026_YTD_CSV`` (only called when it exists and is usable) and
    sets ``next_year_return_pct``/``has_target`` for matching 2025 tickers from
    actual data. Never fabricates: rows without a real partial value stay NaN.
    """
    pt = pd.read_csv(PARTIAL_2026_YTD_CSV)
    pt["ticker"] = pt["ticker"].astype(str).str.strip().str.upper()
    mapping = dict(zip(pt["ticker"], pd.to_numeric(pt["partial_ytd_return_pct"], errors="coerce")))
    out = df.copy()
    mask_2025 = out["year"] == PARTIAL_YEAR
    out.loc[mask_2025, "next_year_return_pct"] = out.loc[mask_2025, "ticker"].map(mapping)
    out.loc[mask_2025, "has_target"] = out.loc[mask_2025, "next_year_return_pct"].notna()
    return out


def train_parameters(
    train_year_from: int = 2020,
    train_year_to: int = 2024,
    top_n: int = 12,
    target_mode: str = TARGET_MODE_FINALIZED,
) -> dict[str, Any]:
    """Compute feature weights from historical top-quartile returners.

    For each feature, compute the normalised discrimination power between
    winners (top-25% returners) and the rest, pooled across the training years.

    Default ``finalized_only`` uses 2020–2024 finalized T+1 targets and never
    includes 2025. ``include_partial_2025`` adds 2025 using REAL partial 2026 YTD
    data when present; if absent, 2025 is excluded with a clear reason (no fake
    target is ever invented).

    Returns ranked list of features with weights in [0, 1].
    """
    mode = normalize_target_mode(target_mode)
    df = _load_training_df()
    feat_cols = _feature_cols(df)

    finalized_trainable = sorted(
        int(y) for y in df[df["has_target"].astype(str).str.lower().isin({"true", "1"})]["year"].unique()
    )
    resolved = resolve_target_years(mode, finalized_trainable)
    includes_partial = resolved["includes_partial_targets"]

    if includes_partial:
        df = _merge_partial_2025_target(df)

    # Finalized-only caps the training window at 2024 regardless of request.
    effective_to = train_year_to if includes_partial else min(train_year_to, FINALIZED_TRAIN_YEAR_TO)

    train_mask = (
        df["year"].between(train_year_from, effective_to)
        & df["has_target"].astype(str).str.lower().isin({"true", "1"})
    )
    tdf = df[train_mask].copy()

    if tdf.empty:
        raise ValueError(
            f"No training data for {train_year_from}–{effective_to}. "
            "Use years 2020–2024 for training (2025 has no finalized next-year target)."
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
        "train_year_to": effective_to,
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
        # ── target-horizon block ──
        "target_mode": resolved["target_mode"],
        "training_years": resolved["training_years"],
        "includes_partial_targets": includes_partial,
        "partial_target_warning": resolved["partial_target_warning"],
        "excluded_years": resolved["excluded_years"],
        "partial_target_status": resolved["partial_status"],
        "target_metadata": resolved["target_metadata"],
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


def _signal_label(score: float) -> str:
    if score >= 0.66:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    return "LOW"


def inference_forecast(input_year: int = PARTIAL_YEAR, top_n: int = 12) -> dict[str, Any]:
    """Forward-looking ranking: train on finalized T+1 targets (2020–2024), then
    apply the learned signal to ``input_year`` financial rows to rank the next year.

    This is the MAIN forward forecast (e.g. 2025 rows → 2026 ranking). It is NOT a
    backtest: ``input_year``'s realized next-year return does not exist yet, so
    nothing here is evaluated. Always uses finalized_only training — never the
    experimental partial-2025 target mode.
    """
    target_year = input_year + 1
    df = _load_public_df()
    year_df = df[df["year"] == input_year]
    if year_df.empty:
        return {
            "input_year": input_year,
            "target_year": target_year,
            "mode": "inference",
            "available": False,
            "reason": (
                f"{input_year} inference rows are not available in the public modeling dataset."
            ),
            "training_window": {"start_year": 2020, "end_year": FINALIZED_TRAIN_YEAR_TO,
                                "target_status": "finalized_annual"},
            "prediction_status": "unavailable",
            "count": 0,
            "rankings": [],
            "disclaimer": DISCLAIMER,
        }

    # Train on finalized targets only, then rank the inference year.
    trained = train_parameters(
        train_year_from=2020, train_year_to=FINALIZED_TRAIN_YEAR_TO,
        top_n=top_n, target_mode=TARGET_MODE_FINALIZED,
    )
    weights = {p["name"]: p["weight"] for p in trained["top_parameters"]}
    run = run_forecast(year=input_year, trained_weights=weights)

    # Realized next-year return exists only for finalized years (≤2024).
    realized = input_year <= FINALIZED_TRAIN_YEAR_TO
    rankings = []
    for it in run["items"]:
        rankings.append({
            "rank": it["rank"],
            "ticker": it["ticker"],
            "score": it["score"],
            "confidence": it["confidence"],
            "confidence_label": it["confidence_label"],
            "signal_label": _signal_label(it["score"]),
            "top_parameters": it.get("top_parameters", [])[:3],
            "input_year": input_year,
            "target_year": target_year,
            "is_inference": bool(it.get("is_inference_row", True)),
            "realized_return_available": realized,
        })

    return {
        "input_year": input_year,
        "target_year": target_year,
        "mode": "inference",
        "available": True,
        "training_window": {"start_year": 2020, "end_year": FINALIZED_TRAIN_YEAR_TO,
                            "target_status": "finalized_annual"},
        "prediction_status": "unevaluated_forward_forecast",
        "methodology_note": (
            f"{input_year} financial rows are used as inference inputs to generate a "
            f"{target_year} forward-looking ranking. {target_year} realized returns are "
            "not available, so this is not a backtest result."
        ),
        "top_features_used": trained["top_parameters"],
        "count": len(rankings),
        "rankings": rankings,
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
