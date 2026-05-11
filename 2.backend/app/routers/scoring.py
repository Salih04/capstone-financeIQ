from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.analytics import SectorNormalizedFeature
from app.models.company import Company
from app.models.financial import ComputedMetric
from app.models.scoring import ScoreRun, ScoreDetail
from app.models.scoring_model import ScoringModel
from app.models.user import User
from app.schemas.scoring import (
    ScoreRunOut, ScoreRunSummary, ScoreRequest,
    CompareRequest, CompareResult,
    CommonPeriodsRequest, CommonPeriodsResult,
)
from app.services.comparison_service import compare_companies
from app.services.scoring_service import ModelScoringUnavailable, run_multi_model_score, run_score
from app.services.explanation_service import build_rich_explanations
from app.services.adaptive_weights_service import compute_adaptive_weights

router = APIRouter(tags=["scoring"])

# Full 12-metric key list (must match scoring_service.py FEATURES)
_METRIC_KEYS = [
    "roa", "roe", "operating_margin", "net_margin",
    "current_ratio", "quick_ratio", "cash_ratio",
    "debt_to_equity", "debt_to_assets",
    "ocf_to_debt", "ocf_to_assets", "cash_flow_margin",
]


def _to_dict(m: ComputedMetric) -> dict:
    return {k: getattr(m, k, None) for k in _METRIC_KEYS}


def _get_sector_z_scores(db: Session, company_id: int, period: str) -> dict[str, float | None]:
    rows = (
        db.query(SectorNormalizedFeature)
        .filter(
            SectorNormalizedFeature.company_id == company_id,
            SectorNormalizedFeature.period == period,
        )
        .all()
    )
    return {r.feature_name: r.z_score for r in rows}


@router.post("/companies/{company_id}/score", response_model=ScoreRunOut)
def score_company(
    company_id: int,
    body: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company = db.get(Company, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found.")

    all_metrics = (
        db.query(ComputedMetric)
        .filter(ComputedMetric.company_id == company_id)
        .order_by(ComputedMetric.period.desc())
        .all()
    )
    if not all_metrics:
        raise HTTPException(
            status_code=422,
            detail="No computed metrics found. Please import financial data first.",
        )

    if body.period:
        current_metric = next((m for m in all_metrics if m.period == body.period), None)
        if not current_metric:
            raise HTTPException(status_code=404, detail=f"No metrics for period '{body.period}'.")
    else:
        current_metric = all_metrics[0]

    previous_metric = all_metrics[1] if len(all_metrics) > 1 else None

    current_dict = _to_dict(current_metric)
    previous_dict = _to_dict(previous_metric) if previous_metric else None

    # Optional: load custom weights from a stored ScoringModel
    custom_weights: dict | None = None
    scoring_model: ScoringModel | None = None
    if body.scoring_model_id:
        scoring_model = db.get(ScoringModel, body.scoring_model_id)
        if scoring_model:
            custom_weights = {
                m.feature_name: m.weight for m in (scoring_model.metrics or [])
            }
    # Direct custom_weights from request body take priority
    if body.custom_weights:
        custom_weights = body.custom_weights

    # Adaptive weights: compute data-driven adjustments from historical returns
    adaptive_weights_info: dict | None = None
    if body.use_adaptive_weights:
        from app.services.scoring_service import _RULE_WEIGHTS
        base_w = custom_weights or _RULE_WEIGHTS.copy()
        sector_code = company.sector_code if hasattr(company, "sector_code") else None
        adaptive_weights_info = compute_adaptive_weights(
            target_period=current_metric.period,
            base_weights=base_w,
            db=db,
            sector_code=sector_code,
        )
        if adaptive_weights_info.get("sufficient_data"):
            custom_weights = adaptive_weights_info["adjusted_weights"]

    try:
        if body.ensemble or body.selected_models:
            result = run_multi_model_score(
                current_dict,
                previous_dict,
                db=db,
                company_id=company_id,
                period=current_metric.period,
                selected_models=body.selected_models,
            )
        else:
            result = run_score(
                current_dict,
                previous_dict,
                mode=body.mode,
                custom_weights=custom_weights,
                db=db,
                company_id=company_id,
                period=current_metric.period,
            )
    except ModelScoringUnavailable as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # ── V3: Enrich with 3-level explanations + sector z-scores ──
    sector_z = _get_sector_z_scores(db, company_id, current_metric.period)
    v3_result = build_rich_explanations(result, current_dict, previous_dict, sector_z)

    model_name = (
        (scoring_model.model_name if scoring_model else None)
        or ("ensemble_v1_v3" if (body.ensemble or body.selected_models) else f"{body.mode}_v3")
    )

    rich = v3_result.get("rich_explanation", {})
    if adaptive_weights_info:
        rich["adaptive_weights"] = adaptive_weights_info
    confidence_flag = (
        "high" if rich.get("data_completeness", 0) >= 0.9
        else "medium" if rich.get("data_completeness", 0) >= 0.6
        else "low"
    )

    score_run = ScoreRun(
        user_id=current_user.id,
        company_id=company_id,
        period=current_metric.period,
        model_name=model_name,
        scoring_model_id=body.scoring_model_id,
        total_score=v3_result["total_score"],
        success_probability=v3_result["success_probability"],
        label_used=v3_result.get("label_used"),
        explanation_summary=v3_result.get("explanation_summary"),
        data_completeness=rich.get("data_completeness"),
        confidence_flag=confidence_flag,
        rich_explanation_json=json.dumps(rich),
    )
    db.add(score_run)
    db.flush()

    for d in v3_result["details"]:
        db.add(
            ScoreDetail(
                score_run_id=score_run.id,
                metric_name=d["metric_name"],
                metric_value=d["metric_value"],
                normalized_value=d.get("normalized_value"),
                weight=d["weight"],
                contribution=d["contribution"],
                comment=d.get("comment"),
                transition_value=d.get("transition_value"),
                sector_z_score=d.get("sector_z_score"),
                l2_explanation=d.get("l2_explanation"),
                l3_counterfactual=d.get("l3_counterfactual"),
            )
        )

    db.commit()
    db.refresh(score_run)
    return score_run

@router.post("/scoring/common-periods", response_model=CommonPeriodsResult)
def common_periods(
    body: CommonPeriodsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Returns the intersection of available periods for the given company IDs.
    Use this to populate the period dropdown before running a compare.
    """
    if not body.company_ids:
        raise HTTPException(status_code=422, detail="Provide at least one company_id.")

    period_sets: list[set[str]] = []
    excluded: list[str] = []

    companies = (
        db.query(Company)
        .filter(Company.id.in_(body.company_ids))
        .all()
    )
    company_map = {c.id: c for c in companies}

    for cid in body.company_ids:
        company = company_map.get(cid)
        if not company:
            excluded.append(f"ID {cid}")
            continue
        periods = {
            r[0]
            for r in db.query(ComputedMetric.period)
            .filter(ComputedMetric.company_id == cid)
            .all()
        }
        if not periods:
            excluded.append(company.ticker)
            continue
        period_sets.append(periods)

    if not period_sets:
        return CommonPeriodsResult(
            common_periods=[],
            total_companies=len(body.company_ids),
            excluded_companies=excluded,
        )

    common = sorted(period_sets[0].intersection(*period_sets[1:]), reverse=True)
    return CommonPeriodsResult(
        common_periods=common,
        total_companies=len(body.company_ids),
        excluded_companies=excluded,
    )


@router.post("/scoring/compare", response_model=CompareResult)
def compare_stocks(
    body: CompareRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Run five model families, then return per-model + ensemble ranked results."""
    if not body.company_ids:
        raise HTTPException(status_code=422, detail="Provide at least one company_id.")
    try:
        comparison = compare_companies(
            db=db,
            company_ids=body.company_ids,
            period=body.period,
            mode=body.mode,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {exc}")

    return CompareResult(
        items=comparison.get("items", []),
        warnings=comparison.get("warnings", []),
        model_outputs=comparison.get("model_outputs", {}),
        ensemble_weights=comparison.get("ensemble_weights", {}),
    )


@router.get("/scoring/adaptive-weights")
def preview_adaptive_weights(
    period: str,
    sector_code: str | None = None,
    scoring_model_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Preview the weight adjustments that adaptive scoring would apply for a given period.
    Returns the adjusted weights + per-category correlation analysis.
    """
    from app.services.scoring_service import _RULE_WEIGHTS
    base_weights: dict
    if scoring_model_id:
        model = db.get(ScoringModel, scoring_model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Scoring model not found.")
        base_weights = {m.feature_name: m.weight for m in (model.metrics or [])}
    else:
        base_weights = _RULE_WEIGHTS.copy()

    result = compute_adaptive_weights(
        target_period=period,
        base_weights=base_weights,
        db=db,
        sector_code=sector_code,
    )
    return result


@router.get("/score-runs/{run_id}", response_model=ScoreRunOut)
def get_score_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    run = db.get(ScoreRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Score run not found.")
    return run


@router.get("/users/me/score-runs")
def my_score_runs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    runs = (
        db.query(ScoreRun)
        .filter(ScoreRun.user_id == current_user.id)
        .order_by(ScoreRun.created_at.desc())
        .limit(50)
        .all()
    )
    result = []
    for run in runs:
        company = db.get(Company, run.company_id)
        result.append({
            "id": run.id,
            "company_id": run.company_id,
            "ticker": company.ticker if company else None,
            "company_name": company.company_name if company else None,
            "period": run.period,
            "model_name": run.model_name,
            "total_score": run.total_score,
            "success_probability": run.success_probability,
            "label_used": run.label_used,
            "confidence_flag": run.confidence_flag,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        })
    return result
