"""
routers/admin.py – V3
======================
Admin-only endpoints:
  - Model Registry CRUD with V3 fields (status, feature_set_version, etc.)
  - Audit log access
  - User management
"""
from __future__ import annotations
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.scoring_model import ScoringModel, ScoringModelMetric
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.scoring import ScoringModelOut
from app.schemas.v3 import ModelRegistryCreate, ModelRegistryOut, ModelRegistryUpdate, AuditLogOut
from app.schemas.user import UserOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if getattr(current_user, "role", "investor") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required.")
    return current_user


# ── Model Registry ────────────────────────────────────────────────────────────

@router.get("/scoring-models", response_model=list[ModelRegistryOut])
def list_scoring_models(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    return db.query(ScoringModel).order_by(ScoringModel.created_at.desc()).all()


@router.post("/scoring-models", response_model=ModelRegistryOut, status_code=status.HTTP_201_CREATED)
def create_scoring_model(
    body: ModelRegistryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    model = ScoringModel(
        model_name=body.model_name,
        model_type=body.model_type,
        version=body.version,
        description=body.description,
        feature_set_version=body.feature_set_version,
        label_strategy=body.label_strategy,
        evaluation_horizon=body.evaluation_horizon,
        status="draft",
        is_active=False,
        created_by=current_user.id,
    )
    db.add(model)
    db.flush()

    for m in body.metrics:
        db.add(ScoringModelMetric(
            scoring_model_id=model.id,
            feature_name=m.get("feature_name", ""),
            weight=m.get("weight", 1.0),
            threshold_min=m.get("threshold_min"),
            threshold_max=m.get("threshold_max"),
            direction=m.get("direction", "higher"),
        ))

    log_action(db, "model_created", actor_user_id=current_user.id,
               entity_type="scoring_model", entity_id=model.id,
               new_value={"model_name": body.model_name, "model_type": body.model_type})
    db.commit()
    db.refresh(model)
    return model


@router.get("/scoring-models/{model_id}", response_model=ModelRegistryOut)
def get_scoring_model(
    model_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    return model


@router.patch("/scoring-models/{model_id}", response_model=ModelRegistryOut)
def update_scoring_model(
    model_id: int,
    body: ModelRegistryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    if model.status == "archived":
        raise HTTPException(status_code=400, detail="Archived models cannot be edited.")

    old_vals = {"model_name": model.model_name, "status": model.status}
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(model, field, value)

    log_action(db, "model_updated", actor_user_id=current_user.id,
               entity_type="scoring_model", entity_id=model_id,
               old_value=old_vals, new_value=body.model_dump(exclude_none=True))
    db.commit()
    db.refresh(model)
    return model


@router.post("/scoring-models/{model_id}/activate", response_model=ModelRegistryOut)
def activate_scoring_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    """Set a model to 'active'. Deactivates/archives same-type models that were active."""
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    if model.status == "archived":
        raise HTTPException(status_code=400, detail="Cannot activate an archived model.")

    # Deactivate other active models of same type
    siblings = db.query(ScoringModel).filter(
        ScoringModel.model_type == model.model_type,
        ScoringModel.id != model_id,
        ScoringModel.status == "active",
    ).all()
    for s in siblings:
        s.status = "archived"
        s.is_active = False

    model.status = "active"
    model.is_active = True
    model.activated_at = datetime.now(timezone.utc)

    log_action(db, "model_activated", actor_user_id=current_user.id,
               entity_type="scoring_model", entity_id=model_id,
               description=f"Model '{model.model_name}' v{model.version} activated.")
    db.commit()
    db.refresh(model)
    return model


@router.post("/scoring-models/{model_id}/archive", response_model=ModelRegistryOut)
def archive_scoring_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    model.status = "archived"
    model.is_active = False
    log_action(db, "model_archived", actor_user_id=current_user.id,
               entity_type="scoring_model", entity_id=model_id)
    db.commit()
    db.refresh(model)
    return model


@router.delete("/scoring-models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scoring_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    model = db.get(ScoringModel, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Scoring model not found.")
    if model.status == "active":
        raise HTTPException(status_code=400, detail="Cannot delete the active model. Archive it first.")
    log_action(db, "model_deleted", actor_user_id=current_user.id,
               entity_type="scoring_model", entity_id=model_id,
               description=f"Deleted model '{model.model_name}' v{model.version}")
    db.delete(model)
    db.commit()


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    return db.query(User).order_by(User.created_at.desc()).all()


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    """Change a user's role. Valid values: investor | admin | analyst."""
    valid_roles = {"investor", "admin", "analyst"}
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role must be one of {valid_roles}.")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    old_role = user.role
    user.role = role
    log_action(db, "user_role_changed", actor_user_id=current_user.id,
               entity_type="user", entity_id=user_id,
               old_value={"role": old_role}, new_value={"role": role})
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role}


# ── Audit Logs ────────────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=list[AuditLogOut])
def get_audit_logs(
    action_type: str | None = None,
    entity_type: str | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(_require_admin),
):
    q = db.query(AuditLog)
    if action_type:
        q = q.filter(AuditLog.action_type == action_type)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.created_at.desc()).limit(limit).all()



