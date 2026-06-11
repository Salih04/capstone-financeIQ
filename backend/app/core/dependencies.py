import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_supabase_token, decode_token, hash_password
from app.database import get_db
from app.models.user import User

bearer_scheme = HTTPBearer()


def _role_from_supabase(payload: dict) -> str:
    app_metadata = payload.get("app_metadata") or {}
    role = app_metadata.get("role") or "investor"
    return role if role in {"admin", "analyst", "investor"} else "investor"


def _legacy_user(token: str, db: Session) -> User:
    payload = decode_token(token)
    user_id: int = int(payload.get("sub"))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _supabase_user(token: str, db: Session) -> User:
    payload = decode_supabase_token(token)
    email = payload.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase token missing email")

    user = db.query(User).filter(User.email == email).first()
    role = _role_from_supabase(payload)
    if not user:
        if not settings.SUPABASE_AUTO_CREATE_USERS:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Supabase user is not provisioned")
        user = User(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(32)),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    if user.role != role:
        user.role = role
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        return _legacy_user(token, db)
    except (JWTError, TypeError, ValueError, HTTPException):
        pass

    try:
        return _supabase_user(token, db)
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
