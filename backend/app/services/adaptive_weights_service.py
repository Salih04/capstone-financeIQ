"""
Adaptive Weights Service
========================
Computes data-driven weight adjustments for the scoring model based on
historical return correlations.

Algorithm for a target period T:
1. Collect all historical periods H < T that have StockReturn data
2. For each (company, H): compute category strength scores (0-1 via percentile rank)
3. For each metric category: compute Pearson correlation with return_1y
4. Scale base_weights by (1 + LEARNING_RATE * correlation)
5. Normalize weights to preserve original total
6. Optional: apply within-sector adjustment for top performers

Correlation interpretation:
  - High positive corr → that category reliably predicted good returns → boost weight
  - Near-zero corr    → category was not predictive → keep weight
  - Negative corr     → category was inversely predictive → reduce weight
"""
from __future__ import annotations
import math
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

from app.models.financial import ComputedMetric, StockReturn
from app.models.company import Company

METRIC_CATEGORIES: dict[str, list[str]] = {
    "profitability": ["roa", "roe", "operating_margin", "net_margin"],
    "liquidity":     ["current_ratio", "quick_ratio", "cash_ratio"],
    "leverage":      ["debt_to_equity", "debt_to_assets"],
    "cash_flow":     ["ocf_to_debt", "ocf_to_assets", "cash_flow_margin"],
}

# For leverage, lower raw value = better financial health → invert percentile rank
LOWER_BETTER_CATEGORIES = {"leverage"}

# Learning rate: at corr=1.0, multiplier = 1 + LR = max boost
LEARNING_RATE = 0.35

# Need at least this many data points to trust the correlation
MIN_SAMPLES = 5

CATEGORY_LABELS = {
    "profitability": "Profitability",
    "liquidity":     "Liquidity",
    "leverage":      "Leverage",
    "cash_flow":     "Cash Flow",
}


# ── Math helpers ──────────────────────────────────────────────────────────────

def _pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return 0.0
    return max(-1.0, min(1.0, num / (dx * dy)))


def _percentile_rank(values: list[float], target: float) -> float:
    """0 = lowest, 1 = highest among values."""
    if len(values) <= 1:
        return 0.5
    below = sum(1 for v in values if v < target)
    return below / (len(values) - 1)


def _category_score(
    metrics: dict[str, float | None],
    category: str,
    period_dist: dict[str, list[float]],
) -> float | None:
    """Average percentile rank of available metrics in this category (higher = better)."""
    lower_better = category in LOWER_BETTER_CATEGORIES
    scores = []
    for metric in METRIC_CATEGORIES[category]:
        val = metrics.get(metric)
        if val is None:
            continue
        all_vals = period_dist.get(metric, [])
        if len(all_vals) < 2:
            continue
        rank = _percentile_rank(all_vals, val)
        if lower_better:
            rank = 1.0 - rank
        scores.append(rank)
    return sum(scores) / len(scores) if scores else None


# ── Main service ──────────────────────────────────────────────────────────────

def compute_adaptive_weights(
    target_period: str,
    base_weights: dict[str, float],
    db: Session,
    sector_code: Optional[str] = None,
) -> dict:
    """
    Returns dict with adjusted weights and full explanation.

    Shape:
    {
        "adjusted_weights": {metric: weight, ...},
        "category_adjustments": {category: {correlation, multiplier, samples, explanation}, ...},
        "periods_analyzed": [str, ...],
        "companies_analyzed": int,
        "sector_adjustment": dict | None,
        "sufficient_data": bool,
        "message": str | None,
    }
    """
    # ── 1. Find historical periods with return data ───────────────────────
    return_periods_q = (
        db.query(StockReturn.period)
        .filter(StockReturn.period < target_period)
        .distinct()
        .all()
    )
    historical_periods = sorted([r[0] for r in return_periods_q])

    if not historical_periods:
        return _no_data_result(base_weights, "No historical return data before this period.")

    # ── 2. Build per-period metric distributions ──────────────────────────
    all_cm = (
        db.query(ComputedMetric)
        .filter(ComputedMetric.period.in_(historical_periods))
        .all()
    )

    # period → metric → [values]
    period_dist: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    all_metric_keys = sum(METRIC_CATEGORIES.values(), [])
    for cm in all_cm:
        for metric in all_metric_keys:
            val = getattr(cm, metric, None)
            if val is not None:
                period_dist[cm.period][metric].append(val)

    # ── 3. Join metrics + returns ─────────────────────────────────────────
    returns_q = (
        db.query(StockReturn)
        .filter(
            StockReturn.period.in_(historical_periods),
            StockReturn.return_1y.isnot(None),
        )
        .all()
    )
    return_lookup: dict[tuple[int, str], float] = {
        (r.company_id, r.period): r.return_1y for r in returns_q
    }

    metrics_lookup: dict[tuple[int, str], dict] = {}
    for cm in all_cm:
        metrics_lookup[(cm.company_id, cm.period)] = {
            metric: getattr(cm, metric, None) for metric in all_metric_keys
        }

    rows: list[dict] = []
    for (company_id, period), return_1y in return_lookup.items():
        m = metrics_lookup.get((company_id, period))
        if m:
            rows.append({
                "company_id": company_id,
                "period": period,
                "metrics": m,
                "return_1y": return_1y,
            })

    if len(rows) < MIN_SAMPLES:
        return _no_data_result(
            base_weights,
            f"Insufficient data: {len(rows)} matching records (need {MIN_SAMPLES}).",
            historical_periods,
            len(rows),
        )

    # ── 4. Compute per-category correlation with returns ──────────────────
    category_details: dict[str, dict] = {}

    for category in METRIC_CATEGORIES:
        strengths, cat_returns = [], []

        for row in rows:
            dist = period_dist.get(row["period"], {})
            strength = _category_score(row["metrics"], category, dist)
            if strength is not None:
                strengths.append(strength)
                cat_returns.append(row["return_1y"])

        if len(strengths) < MIN_SAMPLES:
            category_details[category] = {
                "correlation": 0.0,
                "samples": len(strengths),
                "multiplier": 1.0,
                "explanation": f"{CATEGORY_LABELS[category]}: insufficient samples ({len(strengths)}), weight unchanged.",
            }
            continue

        corr = _pearson(strengths, cat_returns)
        multiplier = round(1.0 + LEARNING_RATE * corr, 4)

        category_details[category] = {
            "correlation": round(corr, 4),
            "samples": len(strengths),
            "multiplier": multiplier,
            "explanation": _build_explanation(category, corr, len(strengths), len(historical_periods)),
        }

    # ── 5. Apply multipliers + normalize ─────────────────────────────────
    original_total = sum(base_weights.values())
    new_weights: dict[str, float] = {}

    for category, metrics in METRIC_CATEGORIES.items():
        mult = category_details.get(category, {}).get("multiplier", 1.0)
        for metric in metrics:
            if metric in base_weights:
                new_weights[metric] = base_weights[metric] * mult

    adjusted_total = sum(new_weights.values())
    if adjusted_total > 0 and original_total > 0:
        scale = original_total / adjusted_total
        new_weights = {k: round(v * scale, 4) for k, v in new_weights.items()}

    # ── 6. Within-sector adjustment ───────────────────────────────────────
    sector_adj = None
    if sector_code:
        sector_adj = _sector_adjustment(rows, period_dist, sector_code, db)
        if sector_adj:
            for metric, mult in sector_adj.get("metric_multipliers", {}).items():
                if metric in new_weights:
                    new_weights[metric] = round(new_weights[metric] * mult, 4)
            # Re-normalize after sector adjustment
            total = sum(new_weights.values())
            if total > 0 and original_total > 0:
                scale = original_total / total
                new_weights = {k: round(v * scale, 4) for k, v in new_weights.items()}

    return {
        "adjusted_weights": new_weights,
        "category_adjustments": category_details,
        "periods_analyzed": historical_periods,
        "companies_analyzed": len(rows),
        "sector_adjustment": sector_adj,
        "sufficient_data": True,
        "message": None,
    }


# ── Sector adjustment helper ──────────────────────────────────────────────────

def _sector_adjustment(
    rows: list[dict],
    period_dist: dict,
    sector_code: str,
    db: Session,
) -> dict | None:
    """
    Find top quartile performers within the sector.
    Identify which metric category they excel in.
    Apply a +10% multiplier to that category's metrics.
    """
    sector_ids = {
        c.id for c in
        db.query(Company)
        .filter(Company.sector_code == sector_code, Company.is_active == True)
        .all()
    }
    if not sector_ids:
        return None

    sector_rows = [r for r in rows if r["company_id"] in sector_ids]
    if len(sector_rows) < 3:
        return None

    # Top quartile by return_1y
    sorted_rows = sorted(sector_rows, key=lambda r: r["return_1y"], reverse=True)
    top_n = max(1, len(sorted_rows) // 4)
    top_performers = sorted_rows[:top_n]

    # Average category strength for top performers
    cat_strength_sums: dict[str, list[float]] = defaultdict(list)
    for row in top_performers:
        dist = period_dist.get(row["period"], {})
        for category in METRIC_CATEGORIES:
            s = _category_score(row["metrics"], category, dist)
            if s is not None:
                cat_strength_sums[category].append(s)

    cat_avg = {
        cat: round(sum(vals) / len(vals), 3)
        for cat, vals in cat_strength_sums.items()
        if vals
    }
    if not cat_avg:
        return None

    dominant = max(cat_avg, key=lambda c: cat_avg[c])
    metric_multipliers = {m: 1.10 for m in METRIC_CATEGORIES[dominant]}

    return {
        "sector_code": sector_code,
        "top_performers_analyzed": top_n,
        "dominant_category": dominant,
        "category_strengths": cat_avg,
        "metric_multipliers": metric_multipliers,
        "explanation": (
            f"Top {top_n} {sector_code} sector performers excel in "
            f"{CATEGORY_LABELS[dominant]} (avg strength: {cat_avg[dominant]:.2f}). "
            f"Weights for {CATEGORY_LABELS[dominant]} metrics boosted +10%."
        ),
    }


# ── Result builders ───────────────────────────────────────────────────────────

def _no_data_result(
    base_weights: dict,
    message: str,
    periods: list | None = None,
    n_companies: int = 0,
) -> dict:
    return {
        "adjusted_weights": base_weights,
        "category_adjustments": {},
        "periods_analyzed": periods or [],
        "companies_analyzed": n_companies,
        "sector_adjustment": None,
        "sufficient_data": False,
        "message": message,
    }


def _build_explanation(category: str, corr: float, n: int, n_periods: int) -> str:
    label = CATEGORY_LABELS[category]
    strength = "strong" if abs(corr) > 0.5 else "moderate" if abs(corr) > 0.25 else "weak"
    direction = "positive" if corr >= 0 else "negative"
    action = "increased" if corr > 0.05 else ("decreased" if corr < -0.05 else "unchanged")
    return (
        f"{label} showed {strength} {direction} correlation ({corr:+.2f}) with "
        f"1-year stock returns across {n_periods} historical period(s) ({n} data points). "
        f"Weight {action}."
    )
