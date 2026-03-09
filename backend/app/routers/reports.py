"""
routers/reports.py
───────────────────
Export score runs as CSV, JSON, or PDF.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.scoring import ScoreRun
from app.models.user import User
from app.services.report_service import generate_csv, generate_json, generate_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


def _get_run(db: Session, run_id: int, current_user: User) -> ScoreRun:
    run = db.get(ScoreRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Score run not found.")
    # Only the owner (or admin) may export
    if run.user_id != current_user.id and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Not authorised.")
    return run


@router.get("/score-runs/{run_id}/export.csv")
def export_csv(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_run(db, run_id, current_user)
    data = generate_csv(db, run_id)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="score_run_{run_id}.csv"'},
    )


@router.get("/score-runs/{run_id}/export.json")
def export_json(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_run(db, run_id, current_user)
    data = generate_json(db, run_id)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="score_run_{run_id}.json"'},
    )


@router.get("/score-runs/{run_id}/export.pdf")
def export_pdf(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_run(db, run_id, current_user)
    try:
        data = generate_pdf(db, run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="score_run_{run_id}.pdf"'},
    )
