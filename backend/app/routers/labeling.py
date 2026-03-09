"""
Labeling Lab Router – V3
GET    /labeling/definitions           → list all label definitions
POST   /labeling/definitions           → create a label definition
POST   /labeling/definitions/{id}/preview -> preview label distribution
POST   /labeling/definitions/{id}/activate
DELETE /labeling/definitions/{id}
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.governance import LabelDefinition
from app.schemas.v3 import LabelDefinitionCreate, LabelDefinitionOut, LabelPreviewOut
from app.services.labeling_service import (
    get_label_definitions, activate_label_definition, preview_label_distribution
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/labeling", tags=["labeling"])


def _require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return user


@router.get("/definitions", response_model=list[LabelDefinitionOut])
def list_definitions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_label_definitions(db)


@router.post("/definitions", response_model=LabelDefinitionOut)
def create_definition(
    body: LabelDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    ld = LabelDefinition(**body.model_dump(), created_by=current_user.id)
    db.add(ld)
    db.flush()
    log_action(
        db, "label_created",
        actor_user_id=current_user.id,
        entity_type="label_definition",
        entity_id=ld.id,
        new_value=body.model_dump(),
    )
    db.commit()
    db.refresh(ld)
    return ld


@router.post("/definitions/{label_id}/preview", response_model=LabelPreviewOut)
def preview_definition(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ld = db.get(LabelDefinition, label_id)
    if not ld:
        raise HTTPException(status_code=404, detail="Label definition not found.")
    result = preview_label_distribution(db, ld)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/definitions/{label_id}/activate", response_model=LabelDefinitionOut)
def activate_definition(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    ld = db.get(LabelDefinition, label_id)
    if not ld:
        raise HTTPException(status_code=404, detail="Label definition not found.")
    result = activate_label_definition(db, label_id, current_user.id)
    log_action(
        db, "label_activated",
        actor_user_id=current_user.id,
        entity_type="label_definition",
        entity_id=label_id,
    )
    db.commit()
    return result


@router.delete("/definitions/{label_id}", status_code=204)
def delete_definition(
    label_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_admin),
):
    ld = db.get(LabelDefinition, label_id)
    if not ld:
        raise HTTPException(status_code=404, detail="Label definition not found.")
    if ld.is_active:
        raise HTTPException(status_code=400, detail="Cannot delete the active label definition.")
    db.delete(ld)
    log_action(db, "label_deleted", actor_user_id=current_user.id, entity_id=label_id)
    db.commit()
