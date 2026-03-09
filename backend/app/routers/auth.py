from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserRegister, UserLogin, UserOut, Token

router = APIRouter(prefix="/auth", tags=["auth"])

MAX_FAILED = 5
LOCK_MINUTES = 15


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(email=body.email, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    # Check lockout
    locked_until = getattr(user, "locked_until", None)
    if locked_until and datetime.utcnow() < locked_until:
        remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        raise HTTPException(
            status_code=403,
            detail=f"Account locked. Try again in {remaining} minute(s).",
        )

    if not verify_password(body.password, user.password_hash):
        # Increment failure counter
        if hasattr(user, "failed_login_count"):
            user.failed_login_count = (user.failed_login_count or 0) + 1
            if user.failed_login_count >= MAX_FAILED:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCK_MINUTES)
                db.commit()
                raise HTTPException(
                    status_code=403,
                    detail=f"Too many failed attempts. Account locked for {LOCK_MINUTES} minutes.",
                )
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    # Success — reset counters
    if hasattr(user, "failed_login_count"):
        user.failed_login_count = 0
    if hasattr(user, "locked_until"):
        user.locked_until = None
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
