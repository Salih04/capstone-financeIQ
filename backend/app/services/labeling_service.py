"""
Labeling Service – V3
======================
Generate success labels based on a LabelDefinition configuration.
Supports multiple benchmark strategies:
  - sector_median  : success if rule-based score >= sector median + threshold
  - upper_quartile : success if score >= p75 of sector
  - absolute       : success if score >= fixed threshold * 100
  - risk_adjusted  : success if score >= threshold * 100 AND debt_to_assets <= 0.7

Also provides label distribution preview for the admin labeling lab.
"""
from __future__ import annotations
from typing import Any

from sqlalchemy.orm import Session

from app.models.financial import ComputedMetric
from app.models.governance import LabelDefinition
from app.services.scoring_service import run_score, _RULE_WEIGHTS

_FEATURES = list(_RULE_WEIGHTS.keys())


def _compute_all_scores(db: Session) -> list[dict]:
    """Score all ComputedMetric rows using rule-based mode."""
    rows = db.query(ComputedMetric).order_by(ComputedMetric.period.asc()).all()
    results = []
    for row in rows:
        feat = {f: getattr(row, f, None) for f in _FEATURES}
        if any(v is None for v in feat.values()):
            continue
        rb = run_score(feat)
        results.append({
            "company_id": row.company_id,
            "period": row.period,
            "score": rb["total_score"],
            "feat": feat,
        })
    return results


def preview_label_distribution(
    db: Session,
    label_def: LabelDefinition,
) -> dict[str, Any]:
    """
    Preview how many rows would be labeled positive/negative with the given
    LabelDefinition settings.  Does NOT persist anything.
    """
    scored = _compute_all_scores(db)
    if not scored:
        return {"error": "No complete metric rows found."}

    threshold_score = label_def.success_threshold * 100
    bench_type = label_def.sector_benchmark_type
    scores = [r["score"] for r in scored]

    import statistics
    median_score = statistics.median(scores)
    p75_score = sorted(scores)[int(len(scores) * 0.75)]

    labels = []
    for r in scored:
        s = r["score"]
        feat = r["feat"]
        if bench_type == "sector_median":
            label = 1 if s >= median_score else 0
        elif bench_type == "upper_quartile":
            label = 1 if s >= p75_score else 0
        elif bench_type == "risk_adjusted":
            debt_ok = feat.get("debt_to_assets", 1.0) <= 0.7
            label = 1 if (s >= threshold_score and debt_ok) else 0
        else:  # absolute
            label = 1 if s >= threshold_score else 0
        labels.append(label)

    n_pos = sum(labels)
    n_total = len(labels)
    imbalance = abs((n_pos / n_total) - 0.5) if n_total > 0 else 0

    return {
        "total_rows": n_total,
        "positive_count": n_pos,
        "negative_count": n_total - n_pos,
        "positive_rate": round(n_pos / n_total, 4) if n_total > 0 else 0,
        "imbalance_ratio": round(imbalance, 4),
        "imbalance_warning": imbalance > 0.35,
        "median_score_used": round(median_score, 2),
        "p75_score_used": round(p75_score, 2),
        "benchmark_type": bench_type,
        "threshold": label_def.success_threshold,
    }


def get_label_definitions(db: Session) -> list[LabelDefinition]:
    return db.query(LabelDefinition).order_by(LabelDefinition.created_at.desc()).all()


def activate_label_definition(db: Session, label_id: int, actor_user_id: int) -> LabelDefinition:
    """Set one label definition as active, deactivate all others."""
    all_defs = db.query(LabelDefinition).all()
    for ld in all_defs:
        ld.is_active = (ld.id == label_id)
    db.commit()
    return db.get(LabelDefinition, label_id)
