"""Score vs realized-return validation (PHASE 4).

Honestly measures whether the Fundamental Score relates to the realized yearly
return. Per year: Pearson + Spearman correlation, top-k hit rate, and
quintile spread. Nothing here is tuned to flatter the score.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.services.research import data, scoring

TARGET = data.TARGET_COLUMN


def _top_k_hit_rate(scored: pd.DataFrame, k: int) -> float | None:
    n = len(scored)
    if n < k:
        return None
    top_score = set(scored.nlargest(k, "fundamental_score")["ticker"])
    top_ret = set(scored.nlargest(k, TARGET)["ticker"])
    return round(len(top_score & top_ret) / k, 3)


def _quintile_spread(scored: pd.DataFrame) -> dict:
    s = scored.dropna(subset=["fundamental_score", TARGET])
    if len(s) < 10:
        return {"high_mean": None, "low_mean": None, "spread": None}
    s = s.sort_values("fundamental_score")
    q = max(1, len(s) // 5)
    low_mean = s.head(q)[TARGET].mean()    # lowest-score quintile
    high_mean = s.tail(q)[TARGET].mean()   # highest-score quintile
    return {
        "high_mean": round(float(high_mean), 2),
        "low_mean": round(float(low_mean), 2),
        "spread": round(float(high_mean - low_mean), 2),
    }


def validate_year(year: int) -> dict:
    scored = scoring.score_year(year)
    s = scored.dropna(subset=["fundamental_score", TARGET])
    pearson = s["fundamental_score"].corr(s[TARGET], method="pearson") if len(s) > 2 else np.nan
    spearman = s["fundamental_score"].corr(s[TARGET], method="spearman") if len(s) > 2 else np.nan

    return {
        "year": year,
        "n": int(len(s)),
        "pearson": None if pd.isna(pearson) else round(float(pearson), 3),
        "spearman": None if pd.isna(spearman) else round(float(spearman), 3),
        "hit_at_5": _top_k_hit_rate(scored, 5),
        "hit_at_10": _top_k_hit_rate(scored, 10),
        "hit_at_20": _top_k_hit_rate(scored, 20),
        "quintile": _quintile_spread(scored),
    }


def validate_all() -> dict:
    years = data.available_years()
    per_year = [validate_year(y) for y in years]
    spearmans = [p["spearman"] for p in per_year if p["spearman"] is not None]
    worked = [p["year"] for p in per_year if (p["spearman"] or 0) > 0.1]
    failed = [p["year"] for p in per_year if (p["spearman"] or 0) < -0.1]
    return {
        "per_year": per_year,
        "mean_spearman": round(float(np.mean(spearmans)), 3) if spearmans else None,
        "years_score_worked": worked,
        "years_score_failed": failed,
        "note": (
            "Positive correlation => higher Fundamental Score associated with "
            "higher realized return that year (explanatory, not predictive)."
        ),
    }
