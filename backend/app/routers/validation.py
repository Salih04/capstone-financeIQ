"""
Validation Router – V3
POST /validation/run        → run time-split validation
GET  /validation/models/{id}/history → history of validation runs
GET  /validation/models/{id}/feature-importances
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.scoring_model import ScoringModel, ScoringModelMetric
from app.models.governance import ModelFeatureImportance
from app.schemas.v3 import ValidationRequest, ValidationRunOut, ModelFeatureImportanceOut
from app.services.validation_service import run_time_split_validation, get_validation_history
from app.services.audit_service import log_action

router = APIRouter(prefix="/validation", tags=["validation"])


def _require_admin_or_analyst(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("admin", "analyst"):
        raise HTTPException(status_code=403, detail="Admin or analyst role required.")
    return user


@router.post("/run")
def run_validation(
    body: ValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin_or_analyst),
):
    """Run time-split validation on a scoring model."""
    model = db.get(ScoringModel, body.scoring_model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")

    result = run_time_split_validation(
        db=db,
        scoring_model_id=body.scoring_model_id,
        train_ratio=body.train_ratio,
        label_def_id=body.label_def_id,
    )

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    log_action(
        db, "validation_run_created",
        actor_user_id=current_user.id,
        entity_type="scoring_model",
        entity_id=body.scoring_model_id,
        new_value={"f1": result.get("f1"), "roc_auc": result.get("roc_auc")},
    )
    db.commit()

    return result


@router.get("/models/{model_id}/history")
def get_model_validation_history(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    return get_validation_history(db, model_id)


@router.get("/models/{model_id}/feature-importances", response_model=list[ModelFeatureImportanceOut])
def get_feature_importances(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ModelFeatureImportance)
        .filter(ModelFeatureImportance.scoring_model_id == model_id)
        .order_by(ModelFeatureImportance.importance_rank.asc())
        .all()
    )
