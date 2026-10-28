import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWTError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_supabase_token, decode_token, hash_password
from app.database import SessionLocal, get_db
from app.models.user import User

bearer_scheme = HTTPBearer()
# auto_error=False → missing/invalid Authorization header yields None instead of
# raising 403. Used by public demo endpoints that must work without a token.
optional_bearer_scheme = HTTPBearer(auto_error=False)


# Privilege order used to stop a token claim from raising a stored role.
_ROLE_RANK = {"investor": 0, "analyst": 1, "admin": 2}


def _role_from_supabase(payload: dict) -> str:
    app_metadata = payload.get("app_metadata") or {}
    role = app_metadata.get("role") or "investor"
    return role if role in _ROLE_RANK else "investor"


def _supabase_email_verified(payload: dict) -> bool:
    """Whether the token's email may be treated as proven inbox ownership.

    Supabase access tokens carry no admin-controlled confirmation claim, and
    ``user_metadata.email_verified`` is writable by the user, so it is ignored.
    Ownership is trusted only when the deployment attests that the project
    issues sessions solely for confirmed emails; anonymous sessions never count.
    """
    if payload.get("is_anonymous") is True:
        return False
    return bool(settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED)


def _legacy_user(token: str, db: Session) -> User:
    payload = decode_token(token)
    user_id: int = int(payload.get("sub"))
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def _supabase_user(token: str, db: Session) -> tuple[User, bool]:
    """Return the user for a verified Supabase token and whether its email is proven."""
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
        return user, _supabase_email_verified(payload)

    # The stored role is authoritative for an existing user. A token claim may
    # only lower it, so a stale or out-of-sync token never restores or grants
    # a privilege that FinanceIQ has revoked.
    if _ROLE_RANK[role] < _ROLE_RANK.get(user.role, _ROLE_RANK["investor"]):
        user.role = role
        db.add(user)
        db.commit()
        db.refresh(user)
    return user, _supabase_email_verified(payload)


def _authenticate(token: str, db: Session) -> tuple[User, bool]:
    """Resolve a signature-verified token to (user, email ownership proven).

    Legacy accounts are self-registered without any email check, so their
    email is never treated as proven.
    """
    try:
        return _legacy_user(token, db), False
    except (PyJWTError, TypeError, ValueError, HTTPException):
        pass
    return _supabase_user(token, db)


def _ensure_active(user: User) -> User:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled.")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        user, _ = _authenticate(credentials.credentials, db)
    except (PyJWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return _ensure_active(user)


def require_roles(*roles: str):
    """Dependency factory: an active caller whose stored role is in ``roles``."""
    allowed = frozenset(roles)

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your role is not permitted to perform this operation.",
            )
        return current_user

    return _dependency


# Shared financial records (statements, ratios, quarterly fundamentals, cohort
# presets, sector rankings) are read by every user. Only admins may replace
# them until the owner names another writer role (fail closed).
require_shared_data_writer = require_roles("admin")


def _resolve_identity_or_none(
    credentials: HTTPAuthorizationCredentials | None,
) -> tuple[User, bool] | None:
    """Verify a bearer token to an active (user, email proven), or None. Never raises.

    DB-free when no token is supplied. A token is only accepted if its signature
    verifies (legacy SECRET_KEY JWT, or Supabase JWT when SUPABASE_JWT_SECRET is
    set) — unsigned/unchecked browser claims are never trusted. Disabled
    accounts resolve to None.
    """
    if credentials is None:
        return None
    token = credentials.credentials
    db = None
    try:
        db = SessionLocal()
        try:
            user, email_verified = _authenticate(token, db)
        except (PyJWTError, TypeError, ValueError, HTTPException):
            return None
        if not user.is_active:
            return None
        return user, email_verified
    except Exception:
        return None
    finally:
        if db is not None:
            db.close()


def _resolve_user_or_none(credentials: HTTPAuthorizationCredentials | None) -> User | None:
    identity = _resolve_identity_or_none(credentials)
    return identity[0] if identity else None


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
        * no/invalid token or disabled account → 401
        * REQUIRE_APPROVED_USER=true  → the email must be proven (see
          ``_supabase_email_verified``; legacy self-registered emails never are)
          and in APPROVED_EMAILS; empty allowlist denies everyone (fail closed);
          unproven or unapproved → 403.

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
    identity = _resolve_identity_or_none(credentials)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user, email_verified = identity

    if settings.REQUIRE_APPROVED_USER:
        allowed = settings.approved_emails_set()
        email = (user.email or "").strip().lower()
        if not email_verified or not allowed or email not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This is a private deployment. Your account is not approved for access.",
            )
    return user
