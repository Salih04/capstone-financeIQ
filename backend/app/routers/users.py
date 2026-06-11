from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserOut, UserProfileSetup


router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/profile", response_model=UserOut)
def update_profile(
    body: UserProfileSetup,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    current_user.user_type = body.user_type
    current_user.risk_level = body.risk_level
    current_user.investment_scope = body.investment_scope
    current_user.sector_focus = body.sector_focus
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
