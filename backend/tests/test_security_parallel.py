"""Synthetic HTTP/service regressions; no research files, provider or live DB.

Run against the unchanged candidate first to reproduce the negative controls.
The small app mounts the real routers and uses the real authentication boundary.
"""
import os
import time
import uuid

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.core import dependencies as deps
from app.core.security import create_access_token, hash_password
from app.database import Base, get_db
from app.models.company import Company
from app.models.scoring import ScoreDetail, ScoreRun
from app.models.user import User
from app.routers import admin, auth, reports, scoring
from app.services import report_service

ISSUER_URL = "https://synthetic-security.supabase.co"
ISSUER = ISSUER_URL + "/auth/v1"
SECRET = "synthetic-parallel-security-test-secret"


@pytest.fixture
def env(monkeypatch):
    pg_url = os.environ.get("FIQ_TEST_POSTGRES_URL")
    if pg_url:
        engine = create_engine(pg_url)
        assert engine.url.get_backend_name() == "postgresql"
    else:
        engine = create_engine("sqlite://", poolclass=StaticPool,
                               connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    factory = sessionmaker(bind=connection, expire_on_commit=False,
                           join_transaction_mode="create_savepoint")
    monkeypatch.setattr(deps, "SessionLocal", factory)
    for name, value in dict(PUBLIC_DEMO_MODE=True, REQUIRE_APPROVED_USER=False,
                            APPROVED_EMAILS="", SUPABASE_URL=ISSUER_URL,
                            SUPABASE_JWT_SECRET=SECRET, SUPABASE_AUTO_CREATE_USERS=True,
                            SUPABASE_EMAIL_CONFIRMATION_ENFORCED=False).items():
        monkeypatch.setattr(settings, name, value)
    # Before remediation this setting does not exist: exercise the original
    # email fallback unchanged to record its failure, rather than mocking it.
    if hasattr(settings, "SUPABASE_IDENTITY_BINDINGS"):
        monkeypatch.setattr(settings, "SUPABASE_IDENTITY_BINDINGS", {})

    def session():
        with factory() as db:
            yield db

    app = FastAPI()
    for router in (auth.router, admin.router, scoring.router, reports.router):
        app.include_router(router)
    app.dependency_overrides[get_db] = session

    @app.get("/gate")
    def gate(user=Depends(deps.require_access)):
        return {"id": user.id if user else None}

    with factory() as db:
        users = [User(email=f"{role}-{uuid.uuid4().hex}@example.org",
                      password_hash=hash_password("Synthetic1!"), role=role, is_active=True)
                 for role in ("investor", "analyst", "admin")]
        db.add_all(users)
        company = Company(ticker="SYNTH", company_name="Synthetic only")
        db.add(company)
        db.flush()
        run = ScoreRun(user_id=users[0].id, company_id=company.id, period="synthetic",
                       model_name="synthetic", total_score=None, success_probability=None,
                       rich_explanation_json='{"private":"synthetic-owner-note"}')
        db.add(run)
        db.flush()
        db.add(ScoreDetail(score_run_id=run.id, metric_name="synthetic-private-detail",
                           metric_value=None, weight=None, contribution=None))
        db.commit()
        run_id = run.id
    yield TestClient(app), factory, users, run_id
    transaction.rollback()
    connection.close()
    engine.dispose()


def legacy(user):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user.id)})}


def supa(user, *, sub="synthetic-subject", **claims):
    now = int(time.time())
    payload = dict(sub=sub, iss=ISSUER, aud="authenticated", iat=now, exp=now + 600,
                   email=user.email, app_metadata={"role": user.role})
    payload.update(claims)
    return {"Authorization": "Bearer " + jwt.encode(payload, SECRET, algorithm="HS256")}


def bind(user, sub="synthetic-subject"):
    if hasattr(settings, "SUPABASE_IDENTITY_BINDINGS"):
        settings.SUPABASE_IDENTITY_BINDINGS = {sub: user.id}


@pytest.mark.parametrize("demo", [True, False])
def test_guessed_score_id_does_not_expose_another_users_run(env, demo):
    client, _, users, run_id = env
    settings.PUBLIC_DEMO_MODE = demo
    response = client.get(f"/score-runs/{run_id}", headers=legacy(users[1]))
    assert response.status_code == 403
    assert "synthetic-owner-note" not in response.text
    assert "synthetic-private-detail" not in response.text


@pytest.mark.parametrize("actor", [0, 2])
@pytest.mark.parametrize("suffix", ["", "/export.csv", "/export.json", "/export.pdf"])
def test_owner_and_admin_keep_score_read_and_exports(env, actor, suffix):
    client, _, users, run_id = env
    prefix = "/reports" if suffix else ""
    response = client.get(f"{prefix}/score-runs/{run_id}{suffix}", headers=legacy(users[actor]))
    assert response.status_code == 200


@pytest.mark.parametrize("suffix", ["/export.csv", "/export.json", "/export.pdf"])
def test_report_router_denies_cross_user_reads(env, suffix):
    client, _, users, run_id = env
    assert client.get(f"/reports/score-runs/{run_id}{suffix}", headers=legacy(users[1])).status_code == 403


@pytest.mark.parametrize("generator", ["generate_csv", "generate_json", "generate_pdf"])
def test_direct_report_service_requires_a_caller(env, generator):
    _, factory, _, run_id = env
    with factory() as db, pytest.raises(HTTPException) as exc:
        getattr(report_service, generator)(db, run_id)
    assert exc.value.status_code == 401


@pytest.mark.parametrize("generator", ["generate_csv", "generate_json", "generate_pdf"])
def test_direct_report_service_checks_owner_and_current_role(env, generator):
    _, factory, users, run_id = env
    generate = getattr(report_service, generator)
    with factory() as db:
        assert generate(db, run_id, current_user=users[0])
        assert generate(db, run_id, current_user=users[2])
        with pytest.raises(HTTPException) as exc:
            generate(db, run_id, current_user=users[1])
        assert exc.value.status_code == 403
    # Deliberately retain the detached, stale admin object across revocation.
    with factory() as db:
        db.get(User, users[2].id).role = "investor"
        db.commit()
    with factory() as db, pytest.raises(HTTPException) as exc:
        generate(db, run_id, current_user=users[2])
    assert exc.value.status_code == 403


def test_my_score_runs_remains_owner_scoped(env):
    client, _, users, run_id = env
    assert [row["id"] for row in client.get("/users/me/score-runs", headers=legacy(users[0])).json()] == [run_id]
    assert client.get("/users/me/score-runs", headers=legacy(users[1])).json() == []


def test_missing_score_and_anonymous_remain_denied(env):
    client, _, users, _ = env
    assert client.get("/score-runs/999999", headers=legacy(users[0])).status_code == 404
    assert client.get("/score-runs/1").status_code in (401, 403)


@pytest.mark.parametrize("attested", [False, True])
def test_same_email_different_subject_cannot_take_over_legacy_admin(env, attested):
    client, factory, users, _ = env
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = attested
    bind(users[2], "right-subject")
    token = supa(users[2], sub="attacker-subject")
    assert client.get("/auth/me", headers=token).status_code == 401
    assert client.get("/admin/users", headers=token).status_code == 401
    with factory() as db:
        assert db.get(User, users[2].id).role == "admin"


def test_unbound_subject_never_bootstraps_an_admin(env):
    client, factory, users, _ = env
    users[2].email = "new-admin@example.org"
    assert client.get("/admin/users", headers=supa(users[2])).status_code == 401
    with factory() as db:
        assert db.query(User).filter(User.email == "new-admin@example.org").count() == 0


def test_bound_subject_survives_email_change_without_relinking(env):
    client, factory, users, _ = env
    bind(users[0])
    with factory() as db:
        count_before = db.query(User).count()
    response = client.get("/auth/me", headers=supa(users[0], email=users[2].email))
    assert response.status_code == 200
    assert response.json()["id"] == users[0].id
    with factory() as db:
        assert db.query(User).count() == count_before


def test_bound_subject_does_not_need_email_as_identity(env):
    client, _, users, _ = env
    bind(users[0])
    response = client.get("/auth/me", headers=supa(users[0], email=None))
    assert response.status_code == 200
    assert response.json()["id"] == users[0].id


@pytest.mark.parametrize("claim", [{"sub": ""}, {"iss": "https://wrong.invalid/auth/v1"},
                                   {"is_anonymous": True}, {"exp": None}])
def test_invalid_bound_identity_fails_closed(env, claim):
    client, _, users, _ = env
    bind(users[0])
    assert client.get("/auth/me", headers=supa(users[0], **claim)).status_code == 401


def test_no_configured_issuer_cannot_resolve_binding(env):
    client, _, users, _ = env
    bind(users[0])
    settings.SUPABASE_URL = None
    assert client.get("/auth/me", headers=supa(users[0])).status_code == 401


def test_missing_expiration_is_rejected_even_for_bound_subject(env):
    client, _, users, _ = env
    bind(users[0])
    claims = dict(sub="synthetic-subject", iss=ISSUER, aud="authenticated", email=users[0].email)
    headers = {"Authorization": "Bearer " + jwt.encode(claims, SECRET, algorithm="HS256")}
    assert client.get("/auth/me", headers=headers).status_code == 401


def test_jwks_verified_bound_subject_resolves_without_email_lookup(env, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from jwt.algorithms import RSAAlgorithm
    from app.core import security
    import json

    client, _, users, _ = env
    bind(users[0])
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update(kid="synthetic-bound-key", alg="RS256", use="sig")
    monkeypatch.setattr(security, "_get_jwks", lambda *args, **kwargs: {"keys": [jwk]})
    token = jwt.encode(dict(sub="synthetic-subject", iss=ISSUER, aud="authenticated",
                            exp=int(time.time()) + 600, email=users[2].email),
                       key, algorithm="RS256", headers={"kid": "synthetic-bound-key"})
    response = client.get("/auth/me", headers={"Authorization": "Bearer " + token})
    assert response.status_code == 200
    assert response.json()["id"] == users[0].id


def test_changed_email_does_not_inherit_old_allowlist_approval(env):
    client, _, users, _ = env
    bind(users[0])
    settings.PUBLIC_DEMO_MODE = False
    settings.REQUIRE_APPROVED_USER = True
    settings.APPROVED_EMAILS = users[0].email
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True
    assert client.get("/gate", headers=supa(users[0], email="changed@example.org")).status_code == 403


def test_bound_confirmed_allowlist_and_public_demo_still_work(env):
    client, _, users, _ = env
    assert client.get("/gate").status_code == 200
    bind(users[0])
    settings.PUBLIC_DEMO_MODE = False
    settings.REQUIRE_APPROVED_USER = True
    settings.APPROVED_EMAILS = users[0].email.upper()
    settings.SUPABASE_EMAIL_CONFIRMATION_ENFORCED = True
    assert client.get("/gate", headers=supa(users[0])).status_code == 200


@pytest.mark.parametrize("provider", ["legacy", "supabase"])
def test_stale_token_cannot_restore_role_or_disabled_access(env, provider):
    client, factory, users, _ = env
    bind(users[2])
    token = legacy(users[2]) if provider == "legacy" else supa(users[2])
    assert client.get("/admin/users", headers=token).status_code == 200
    with factory() as db:
        db.get(User, users[2].id).role = "investor"
        db.commit()
    assert client.get("/admin/users", headers=token).status_code == 403
    with factory() as db:
        assert db.get(User, users[2].id).role == "investor"
        db.get(User, users[2].id).is_active = False
        db.commit()
    assert client.get("/auth/me", headers=token).status_code == 403


def test_deleted_bound_user_is_never_recreated_by_old_token(env):
    client, factory, users, _ = env
    bind(users[2])
    token = supa(users[2])
    with factory() as db:
        count_before = db.query(User).count()
        db.delete(db.get(User, users[2].id))
        db.commit()
    assert client.get("/auth/me", headers=token).status_code == 401
    with factory() as db:
        assert db.query(User).count() == count_before - 1
        assert db.query(User).filter(User.email == users[2].email).count() == 0


def test_registration_ignores_requested_admin_role(env):
    client, _, _, _ = env
    response = client.post("/auth/register", json={"email": "registrant@example.org",
                                                  "password": "Synthetic1!", "role": "admin"})
    assert response.status_code == 201
    assert response.json()["role"] == "investor"
