"""Shared authorization boundary for persisted user-owned score reads."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.scoring import ScoreRun
from app.models.user import User


def get_owned_score_run(db: Session, run_id: int, *, current_user: User | None) -> ScoreRun:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    current_user = db.get(User, current_user.id, populate_existing=True)
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")
    # Also guard direct service callers; demo mode never makes owned runs public.
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")
    run = db.get(ScoreRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Score run not found.")
    if run.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorised.")
    return run
