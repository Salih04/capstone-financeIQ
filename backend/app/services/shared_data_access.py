"""Service boundary for replacing shared financial data, including rankings."""
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User


def require_shared_writer(db: Session, current_user: User | None) -> User:
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    # Do not flush caller state before checking the current stored authority.
    with db.no_autoflush:
        user = db.get(User, current_user.id, populate_existing=True)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active or user.role != "admin":
        raise HTTPException(status_code=403, detail="Shared data writes require an active admin.")
    return user
