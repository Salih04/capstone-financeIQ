"""Audit A01 + A08: verified-email allowlist, inactive accounts, stale roles.

Every token here is synthetic and signed with test-only secrets; no network.
"""
from __future__ import annotations

import os
import time
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["RESEARCH_LLM_PROVIDER"] = "none"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from jose import jwt  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402

_SUPABASE_SECRET = "audit-remediation-supabase-test-secret"
_PASSWORD = "Passw0rd!"
_SETTINGS = (
    "PUBLIC_DEMO_MODE", "REQUIRE_APPROVED_USER", "APPROVED_EMAILS",
    "SUPABASE_JWT_SECRET", "SUPABASE_URL", "SUPABASE_JWKS_URL",
    "SUPABASE_AUTO_CREATE_USERS", "SUPABASE_EMAIL_CONFIRMATION_ENFORCED",
)


@pytest.fixture(autouse=True)
def _isolated_settings():
    saved = {k: getattr(settings, k) for k in _SETTINGS}
    settings.SUPABASE_JWT_SECRET = _SUPABASE_SECRET
    settings.SUPABASE_URL = None
    settings.SUPABASE_JWKS_URL = None
    settings.SUPABASE_AUTO_CREATE_USERS = True
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = False
    yield
    for k, v in saved.items():
        setattr(settings, k, v)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def _email(tag: str) -> str:
    return f"{tag}-{uuid.uuid4().hex[:8]}@example.org"


def _make_user(email: str, *, role: str = "investor", active: bool = True) -> int:
    db = SessionLocal()
    try:
        user = User(email=email, password_hash=hash_password(_PASSWORD), role=role, is_active=active)
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()


def _update_user(user_id: int, **fields) -> None:
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        for k, v in fields.items():
            setattr(user, k, v)
        db.commit()
    finally:
        db.close()


def _stored_role(user_id: int) -> str:
    db = SessionLocal()
    try:
        return db.get(User, user_id).role
    finally:
        db.close()


def _legacy_token(user_id: int) -> str:
    return create_access_token({"sub": str(user_id)})


def _supabase_token(email: str, *, role: str | None = None, **extra) -> str:
    now = int(time.time())
    claims = {"sub": f"uid-{email}", "email": email, "aud": "authenticated",
              "iat": now, "exp": now + 3600, **extra}
    if role is not None:
        claims["app_metadata"] = {"provider": "email", "role": role}
    return jwt.encode(claims, _SUPABASE_SECRET, algorithm="HS256")


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _private_allowlist(*emails: str) -> None:
    settings.PUBLIC_DEMO_MODE = False
    settings.REQUIRE_APPROVED_USER = True
    settings.APPROVED_EMAILS = ",".join(emails)


# ── A01: unverified email ownership never satisfies the allowlist ────────────

def test_a01_self_registered_legacy_account_cannot_claim_allowlisted_email(client):
    victim = _email("a01-victim")
    _private_allowlist(victim)
    # Anyone can self-register any address; nothing proves inbox ownership.
    assert client.post("/auth/register", json={"email": victim, "password": "Attacker1!"}).status_code == 201
    login = client.post("/auth/login", json={"email": victim, "password": "Attacker1!"})
    assert login.status_code == 200
    r = client.get("/research/summary", headers=_bearer(login.json()["access_token"]))
    assert r.status_code == 403
    assert victim not in r.text


def test_a01_supabase_email_without_confirmation_attestation_is_denied(client):
    email = _email("a01-supa")
    _private_allowlist(email)
    r = client.get("/research/summary", headers=_bearer(_supabase_token(email)))
    assert r.status_code == 403


def test_a01_user_writable_email_verified_metadata_is_not_trusted(client):
    email = _email("a01-meta")
    _private_allowlist(email)
    token = _supabase_token(email, user_metadata={"email_verified": True})
    assert client.get("/research/summary", headers=_bearer(token)).status_code == 403


def test_a01_attested_supabase_email_on_allowlist_is_admitted(client):
    email = _email("a01-ok")
    _private_allowlist(email.upper())  # allowlist stays case-insensitive
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True
    assert client.get("/research/summary", headers=_bearer(_supabase_token(email))).status_code == 200


def test_a01_attested_but_unlisted_email_is_still_denied(client):
    _private_allowlist(_email("a01-other"))
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True
    r = client.get("/research/summary", headers=_bearer(_supabase_token(_email("a01-unlisted"))))
    assert r.status_code == 403


def test_a01_anonymous_supabase_session_never_verified(client):
    email = _email("a01-anon")
    _private_allowlist(email)
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True
    token = _supabase_token(email, is_anonymous=True)
    assert client.get("/research/summary", headers=_bearer(token)).status_code == 403


def test_a01_private_mode_without_allowlist_keeps_legacy_access(client):
    """Allowlist-free private mode needs no email proof; legacy tokens keep working."""
    user_id = _make_user(_email("a01-noallow"))
    settings.PUBLIC_DEMO_MODE = False
    settings.REQUIRE_APPROVED_USER = False
    assert client.get("/research/summary", headers=_bearer(_legacy_token(user_id))).status_code == 200


# ── A08: inactive accounts are rejected everywhere ──────────────────────────

def test_a08_inactive_legacy_token_rejected_by_protected_endpoint(client):
    user_id = _make_user(_email("a08-legacy"))
    token = _legacy_token(user_id)
    assert client.get("/auth/me", headers=_bearer(token)).status_code == 200
    _update_user(user_id, is_active=False)
    r = client.get("/auth/me", headers=_bearer(token))
    assert r.status_code == 403
    assert r.json()["detail"] == "Account is disabled."


def test_a08_inactive_account_cannot_log_in(client):
    email = _email("a08-login")
    _make_user(email, active=False)
    r = client.post("/auth/login", json={"email": email, "password": _PASSWORD})
    assert r.status_code == 403
    assert "access_token" not in r.text


def test_a08_inactive_account_login_with_wrong_password_stays_generic(client):
    email = _email("a08-enum")
    _make_user(email, active=False)
    r = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert r.status_code == 401
    assert "disabled" not in r.text.lower()


def test_a08_inactive_user_denied_private_research_access(client):
    user_id = _make_user(_email("a08-private"), active=False)
    settings.PUBLIC_DEMO_MODE = False
    settings.REQUIRE_APPROVED_USER = False
    assert client.get("/research/summary", headers=_bearer(_legacy_token(user_id))).status_code == 401


def test_a08_inactive_supabase_user_rejected(client):
    email = _email("a08-supa")
    _make_user(email, active=False)
    assert client.get("/auth/me", headers=_bearer(_supabase_token(email))).status_code == 403


def test_a08_inactive_admin_cannot_use_admin_endpoints(client):
    user_id = _make_user(_email("a08-admin"), role="admin", active=False)
    assert client.get("/admin/users", headers=_bearer(_legacy_token(user_id))).status_code == 403


# ── A08: stale tokens never restore a revoked role ──────────────────────────

def test_a08_stale_supabase_admin_claim_cannot_restore_revoked_admin(client):
    email = _email("a08-stale")
    user_id = _make_user(email, role="admin")
    stale = _supabase_token(email, role="admin")  # issued while still admin
    assert client.get("/admin/users", headers=_bearer(stale)).status_code == 200
    _update_user(user_id, role="investor")  # admin revoked in FinanceIQ
    assert client.get("/admin/users", headers=_bearer(stale)).status_code == 403
    assert _stored_role(user_id) == "investor"


def test_a08_supabase_claim_cannot_escalate_existing_user(client):
    email = _email("a08-escalate")
    user_id = _make_user(email, role="analyst")
    assert client.get("/admin/users", headers=_bearer(_supabase_token(email, role="admin"))).status_code == 403
    assert _stored_role(user_id) == "analyst"


def test_a08_supabase_downgrade_is_applied(client):
    email = _email("a08-down")
    user_id = _make_user(email, role="admin")
    assert client.get("/admin/users", headers=_bearer(_supabase_token(email, role="investor"))).status_code == 403
    assert _stored_role(user_id) == "investor"
    # A later token still carrying admin cannot climb back up.
    assert client.get("/admin/users", headers=_bearer(_supabase_token(email, role="admin"))).status_code == 403
    assert _stored_role(user_id) == "investor"


def test_a08_matching_supabase_admin_keeps_access(client):
    email = _email("a08-keep")
    _make_user(email, role="admin")
    assert client.get("/admin/users", headers=_bearer(_supabase_token(email, role="admin"))).status_code == 200


def test_a08_new_supabase_user_is_provisioned_from_signed_claim(client):
    email = _email("a08-new")
    r = client.get("/auth/me", headers=_bearer(_supabase_token(email, role="analyst")))
    assert r.status_code == 200
    assert r.json()["role"] == "analyst"


def test_a08_legacy_role_revocation_applies_to_existing_token(client):
    user_id = _make_user(_email("a08-legacy-role"), role="admin")
    token = _legacy_token(user_id)
    assert client.get("/admin/users", headers=_bearer(token)).status_code == 200
    _update_user(user_id, role="investor")
    assert client.get("/admin/users", headers=_bearer(token)).status_code == 403
