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
)
from app.services.comparison_service import compare_companies
from app.services.scoring_service import run_score
from app.services.explanation_service import build_rich_explanations

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

    result = run_score(
        current_dict,
        previous_dict,
        mode=body.mode,
        custom_weights=custom_weights,
        db=db,
        company_id=company_id,
        period=current_metric.period,
    )

    # ── V3: Enrich with 3-level explanations + sector z-scores ──
    sector_z = _get_sector_z_scores(db, company_id, current_metric.period)
    v3_result = build_rich_explanations(result, current_dict, previous_dict, sector_z)

    model_name = (
        (scoring_model.model_name if scoring_model else None)
        or f"{body.mode}_v3"
    )

    rich = v3_result.get("rich_explanation", {})
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

@router.post("/scoring/compare", response_model=CompareResult)
def compare_stocks(
    body: CompareRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Score multiple companies with the same model and return ranked results."""
    if not body.company_ids:
        raise HTTPException(status_code=422, detail="Provide at least one company_id.")
    results = compare_companies(
        db=db,
        company_ids=body.company_ids,
        period=body.period,
        mode=body.mode,
    )
    return CompareResult(items=results)


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


