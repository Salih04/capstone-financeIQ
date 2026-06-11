import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_supabase_token, decode_token, hash_password
from app.database import SessionLocal, get_db
from app.models.user import User

bearer_scheme = HTTPBearer()
# auto_error=False → missing/invalid Authorization header yields None instead of
# raising 403. Used by public demo endpoints that must work without a token.
optional_bearer_scheme = HTTPBearer(auto_error=False)


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


def _resolve_user_or_none(credentials: HTTPAuthorizationCredentials | None) -> User | None:
    """Verify a bearer token to a User, or return None. Never raises.

    DB-free when no token is supplied. A token is only accepted if its signature
    verifies (legacy SECRET_KEY JWT, or Supabase JWT when SUPABASE_JWT_SECRET is
    set) — unsigned/unchecked browser claims are never trusted.
    """
    if credentials is None:
        return None
    token = credentials.credentials
    db = None
    try:
        db = SessionLocal()
        try:
            return _legacy_user(token, db)
        except (JWTError, TypeError, ValueError, HTTPException):
            pass
        try:
            return _supabase_user(token, db)
        except (JWTError, TypeError, ValueError, HTTPException):
            return None
    except Exception:
        return None
    finally:
        if db is not None:
            db.close()


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> User | None:
    """Resolve the caller if a valid token is present; otherwise return None.
    Never raises 401/403 — used by endpoints that stay open regardless of mode.
    """
    return _resolve_user_or_none(credentials)


def require_access(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_bearer_scheme),
) -> User | None:
    """Access gate for research/forecasting data endpoints.

    - PUBLIC_DEMO_MODE=true  → behaves like ``optional_user`` (open read-only demo;
      returns the user if a valid token is present, else None — never blocks).
    - PUBLIC_DEMO_MODE=false → requires a verified authenticated user:
        * no/invalid token            → 401
        * REQUIRE_APPROVED_USER=true  → verified email must be in APPROVED_EMAILS;
          empty allowlist denies everyone (fail closed); unapproved → 403.

    Verification relies on token signatures only. In private mode the backend must
    be able to verify Supabase sessions, i.e. SUPABASE_JWT_SECRET must be set;
    without it every Supabase token fails to verify and access is denied (fail
    closed). Never leaks the allowlist or token claims in error responses.
    """
    if settings.PUBLIC_DEMO_MODE:
        return _resolve_user_or_none(credentials)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = _resolve_user_or_none(credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if settings.REQUIRE_APPROVED_USER:
        allowed = settings.approved_emails_set()
        email = (user.email or "").strip().lower()
        if not allowed or email not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is a private deployment. Your account is not approved for access.",
            )
    return user
