"""
TransitionService – computes inter-period changes for all computed metrics.

For each pair of consecutive periods (t-1 → t) it produces:
  abs_change  = new_value - old_value
  pct_change  = abs_change / |old_value|   (None if old_value == 0 or sign is negative-base)

Edge cases handled:
  - Missing period  → skipped (insufficient history)
  - old_value == 0  → pct_change = None
  - Either value is None → abs_change = None, pct_change = None
"""

from sqlalchemy.orm import Session

from app.models.analytics import MetricTransition
from app.models.financial import ComputedMetric

ALL_METRICS = [
    "roa", "roe", "operating_margin", "net_margin",
    "current_ratio", "quick_ratio", "cash_ratio",
    "debt_to_equity", "debt_to_assets",
    "ocf_to_debt", "ocf_to_assets", "cash_flow_margin",
]


def _safe_pct(new_val, old_val):
    if new_val is None or old_val is None or old_val == 0:
        return None
    return (new_val - old_val) / abs(old_val)


def compute_transitions_for_company(db: Session, company_id: int) -> int:
    """
    Fetch all ComputedMetric rows for a company, sort by period,
    then compute transitions for each consecutive pair.
    Returns the number of transition rows upserted.
    """
    rows = (
        db.query(ComputedMetric)
        .filter(ComputedMetric.company_id == company_id)
        .order_by(ComputedMetric.period.asc())
        .all()
    )

    if len(rows) < 2:
        return 0

    count = 0
    for i in range(1, len(rows)):
        prev = rows[i - 1]
        curr = rows[i]

        for metric in ALL_METRICS:
            old_val = getattr(prev, metric, None)
            new_val = getattr(curr, metric, None)

            abs_change = (
                (new_val - old_val)
                if (new_val is not None and old_val is not None)
                else None
            )
            pct_change = _safe_pct(new_val, old_val)

            # Upsert
            existing = (
                db.query(MetricTransition)
                .filter(
                    MetricTransition.company_id == company_id,
                    MetricTransition.from_period == prev.period,
                    MetricTransition.to_period == curr.period,
                    MetricTransition.metric_name == metric,
                )
                .first()
            )

            if existing:
                existing.old_value = old_val
                existing.new_value = new_val
                existing.abs_change = abs_change
                existing.pct_change = pct_change
            else:
                db.add(
                    MetricTransition(
                        company_id=company_id,
                        from_period=prev.period,
                        to_period=curr.period,
                        metric_name=metric,
                        old_value=old_val,
                        new_value=new_val,
                        abs_change=abs_change,
                        pct_change=pct_change,
                    )
                )
                count += 1

    db.commit()
    return count


def get_latest_transitions(db: Session, company_id: int) -> list[MetricTransition]:
    """Return transitions for the most recent period pair."""
    periods = (
        db.query(MetricTransition.to_period)
        .filter(MetricTransition.company_id == company_id)
        .distinct()
        .order_by(MetricTransition.to_period.desc())
        .first()
    )
    if not periods:
        return []
    latest = periods[0]
    return (
        db.query(MetricTransition)
        .filter(
            MetricTransition.company_id == company_id,
            MetricTransition.to_period == latest,
        )
        .all()
    )
