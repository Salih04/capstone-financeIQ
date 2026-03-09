"""
comparison_service.py
─────────────────────
Run the same scoring model on multiple companies and return ranked results.
All companies are scored for the same period (or their individual latest period
if no explicit period is given) so the results are comparable.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial import ComputedMetric
from app.services.scoring_service import run_score

# Full 12-feature list mirroring scoring_service.py FEATURES
_METRIC_KEYS = [
    "roa", "roe", "operating_margin", "net_margin",
    "current_ratio", "quick_ratio", "cash_ratio",
    "debt_to_equity", "debt_to_assets",
    "ocf_to_debt", "ocf_to_assets", "cash_flow_margin",
]


def _metrics_to_dict(m: ComputedMetric) -> dict:
    return {k: getattr(m, k, None) for k in _METRIC_KEYS}


def compare_companies(
    db: Session,
    company_ids: list[int],
    period: str | None = None,
    mode: str = "rule_based",
    custom_weights: dict | None = None,
) -> list[dict]:
    """
    Score each company in *company_ids* and return a list of result dicts
    sorted by total_score descending.

    Each dict contains:
        company_id, ticker, company_name, period,
        total_score, success_probability, label_used, explanation_summary
    """
    results: list[dict] = []

    for cid in company_ids:
        company = db.get(Company, cid)
        if not company:
            continue

        # Fetch metrics ordered by period desc
        metrics_qs = (
            db.query(ComputedMetric)
            .filter(ComputedMetric.company_id == cid)
            .order_by(ComputedMetric.period.desc())
            .all()
        )
        if not metrics_qs:
            continue

        if period:
            current = next((m for m in metrics_qs if m.period == period), None)
            if not current:
                continue  # this company has no data for that period – skip silently
        else:
            current = metrics_qs[0]

        previous = metrics_qs[1] if len(metrics_qs) > 1 else None

        current_dict = _metrics_to_dict(current)
        previous_dict = _metrics_to_dict(previous) if previous else None

        score_result = run_score(
            current_dict,
            previous_dict,
            mode=mode,
            custom_weights=custom_weights,
            db=db,
        )

        results.append(
            {
                "company_id": cid,
                "ticker": company.ticker,
                "company_name": company.company_name,
                "period": current.period,
                "total_score": score_result.get("total_score"),
                "success_probability": score_result.get("success_probability"),
                "label_used": score_result.get("label_used"),
                "explanation_summary": score_result.get("explanation_summary"),
            }
        )

    # Sort best score first
    results.sort(key=lambda x: (x["total_score"] or 0), reverse=True)
    return results
