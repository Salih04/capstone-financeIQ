"""
comparison_service.py
─────────────────────
Run five model families on multiple companies and return:
- per-model rankings
- final weighted ensemble ranking
"""
from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.company import Company
from app.models.financial import ComputedMetric
from app.services.scoring_service import (
    ENSEMBLE_WEIGHTS_V1,
    MULTI_MODEL_IDS,
    ModelScoringUnavailable,
    run_score,
)

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
) -> dict:
    results: list[dict] = []
    warnings: list[str] = []
    model_outputs: dict[str, list[dict]] = {m: [] for m in MULTI_MODEL_IDS}

    # Fetch all requested companies in ONE query to avoid N+1
    company_map: dict[int, Company] = {
        c.id: c
        for c in db.query(Company).filter(Company.id.in_(company_ids)).all()
    }

    mean_query = db.query(*[func.avg(getattr(ComputedMetric, k)).label(k) for k in _METRIC_KEYS])
    if period:
        mean_query = mean_query.filter(ComputedMetric.period == period)
    mean_row = mean_query.first()
    mean_map = {k: (float(getattr(mean_row, k)) if mean_row and getattr(mean_row, k) is not None else None) for k in _METRIC_KEYS}

    for cid in company_ids:
        company = company_map.get(cid)
        if not company:
            warnings.append(f"Company ID {cid} not found and was excluded.")
            continue

        # Fetch metrics ordered by period desc
        metrics_qs = (
            db.query(ComputedMetric)
            .filter(ComputedMetric.company_id == cid)
            .order_by(ComputedMetric.period.desc())
            .all()
        )
        if not metrics_qs:
            warnings.append(
                f"{company.ticker} has no computed metrics and was excluded."
            )
            continue

        if period:
            current = next((m for m in metrics_qs if m.period == period), None)
            if not current:
                warnings.append(
                    f"{company.ticker} has no data for {period} and was excluded."
                )
                continue
        else:
            current = metrics_qs[0]

        previous = metrics_qs[1] if len(metrics_qs) > 1 else None

        current_dict = _metrics_to_dict(current)
        previous_dict = _metrics_to_dict(previous) if previous else None
        if mean_map:
            current_dict = {k: (mean_map.get(k) if current_dict.get(k) is None else current_dict.get(k)) for k in _METRIC_KEYS}
            if previous_dict:
                previous_dict = {k: (mean_map.get(k) if previous_dict.get(k) is None else previous_dict.get(k)) for k in _METRIC_KEYS}
        per_model_scores: dict[str, float] = {}
        per_model_probs: dict[str, float] = {}
        model_warnings: list[str] = []

        for model_id in MULTI_MODEL_IDS:
            try:
                score_result = run_score(
                    current_dict,
                    previous_dict,
                    mode=model_id,
                    custom_weights=custom_weights,
                    db=db,
                    company_id=company.id,
                    period=current.period,
                )
                per_model_scores[model_id] = float(score_result.get("total_score") or 0.0)
                per_model_probs[model_id] = float(score_result.get("success_probability") or 0.0)
                model_outputs[model_id].append(
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
            except ModelScoringUnavailable as exc:
                model_warnings.append(f"{model_id}: {exc}")

        if not per_model_scores:
            warnings.append(
                f"{company.ticker} had no available model outputs and was excluded. "
                + " | ".join(model_warnings)
            )
            continue

        available_weights = {
            model_id: ENSEMBLE_WEIGHTS_V1[model_id]
            for model_id in per_model_scores
            if model_id in ENSEMBLE_WEIGHTS_V1
        }
        weight_sum = sum(available_weights.values())
        if weight_sum <= 0:
            warnings.append(f"{company.ticker} had invalid ensemble weights and was excluded.")
            continue
        ensemble_prob = sum(
            per_model_probs[m] * (w / weight_sum) for m, w in available_weights.items()
        )
        ensemble_score = round(ensemble_prob * 100, 2)
        explanation = (
            f"Ensemble_v1 over: {', '.join(sorted(per_model_scores.keys()))}."
            + (f" Warnings: {' | '.join(model_warnings)}" if model_warnings else "")
        )

        results.append(
            {
                "company_id": cid,
                "ticker": company.ticker,
                "company_name": company.company_name,
                "period": current.period,
                "total_score": ensemble_score,
                "success_probability": round(ensemble_prob, 4),
                "label_used": "ensemble_v1",
                "explanation_summary": explanation,
                "per_model_scores": per_model_scores,
            }
        )
        for w in model_warnings:
            warnings.append(f"{company.ticker}: {w}")

    results.sort(key=lambda x: (x["total_score"] or 0), reverse=True)
    for model_id, rows in model_outputs.items():
        rows.sort(key=lambda x: (x["total_score"] or 0), reverse=True)
    return {
        "items": results,
        "warnings": warnings,
        "model_outputs": model_outputs,
        "ensemble_weights": ENSEMBLE_WEIGHTS_V1,
    }
