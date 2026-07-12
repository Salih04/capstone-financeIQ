"""Authenticated append-only writes and read-only analyst dissent aggregates."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_access
from app.database import get_db
from app.models.user import User
from app.schemas.analyst_verdict import (
    AnalystVerdictAggregateOut,
    AnalystVerdictCreate,
    AnalystVerdictOut,
)
from app.services.analyst_verdict_service import aggregate_verdicts, create_verdict
from app.services.audit_service import log_action


router = APIRouter(prefix="/analyst-verdicts", tags=["analyst-verdicts"])


@router.post("", response_model=AnalystVerdictOut, status_code=status.HTTP_201_CREATED)
def append_analyst_verdict(
    body: AnalystVerdictCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Append a verdict. Public demo mode never relaxes this write gate."""
    verdict = create_verdict(db, body, current_user.id)
    log_action(
        db,
        "analyst_verdict_recorded",
        actor_user_id=current_user.id,
        entity_type="analyst_verdict",
        entity_id=verdict.id,
        new_value={
            "ticker": verdict.ticker,
            "year": verdict.year,
            "verdict": verdict.verdict,
            "reason_type": verdict.reason_type,
        },
    )
    db.commit()
    db.refresh(verdict)
    return verdict


@router.get("/aggregate", response_model=AnalystVerdictAggregateOut)
def analyst_verdict_aggregate(
    ticker: str | None = Query(default=None, min_length=1, max_length=20),
    year: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    _: User | None = Depends(require_access),
):
    """Expose descriptive counts only; no note, user, score, or rank fields."""
    return aggregate_verdicts(db, ticker=ticker, year=year)
