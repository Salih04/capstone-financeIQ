from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.core.dependencies import get_current_user
from app.core.security import hash_password
from app.database import SessionLocal
from app.main import app
from app.models.analyst_verdict import AnalystVerdict
from app.models.audit import AuditLog
from app.models.user import User
from app.services.analyst_verdict_service import LEDGER_BOUNDARY
from app.services.scoring_service import run_score


CLIENT = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_verdict_rows():
    original_overrides = dict(app.dependency_overrides)
    original_demo_mode = settings.PUBLIC_DEMO_MODE
    settings.PUBLIC_DEMO_MODE = True
    with SessionLocal() as db:
        db.query(AnalystVerdict).delete()
        db.commit()
    yield
    app.dependency_overrides = original_overrides
    settings.PUBLIC_DEMO_MODE = original_demo_mode


def _authenticated_user(email: str = "loop-analyst@example.com") -> int:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password("test-only-password"),
                role="analyst",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        user_id = user.id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)
    return user_id


def _payload(**overrides) -> dict:
    payload = {
        "ticker": "ASELS",
        "year": 2025,
        "verdict": "disagree",
        "reason_type": "model_instability",
        "note": "The persisted model ranks disagree materially.",
    }
    payload.update(overrides)
    return payload


def test_authenticated_write_appends_and_aggregate_is_deterministic():
    user_id = _authenticated_user()
    payloads = [
        _payload(ticker="ASTOR", year=2024, reason_type="data_gap"),
        _payload(ticker="ASELS", verdict="agree", reason_type="evidence_quality"),
        _payload(ticker="ASELS", note=None),
    ]

    responses = [CLIENT.post("/analyst-verdicts", json=payload) for payload in payloads]
    assert [response.status_code for response in responses] == [201, 201, 201]
    assert responses[0].json()["user_id"] == user_id
    assert responses[0].json()["ticker"] == "ASTOR"
    with SessionLocal() as db:
        audit_rows = (
            db.query(AuditLog)
            .filter(AuditLog.action_type == "analyst_verdict_recorded")
            .all()
        )
        assert len(audit_rows) >= 3
        assert all(row.actor_user_id == user_id for row in audit_rows[-3:])

    first = CLIENT.get("/analyst-verdicts/aggregate")
    second = CLIENT.get("/analyst-verdicts/aggregate")
    assert first.status_code == second.status_code == 200
    assert first.content == second.content

    body = first.json()
    assert body["purpose"] == LEDGER_BOUNDARY
    assert "crowd signal" in body["interpretation"]
    assert [row["ticker"] for row in body["rows"]] == ["ASELS", "ASTOR"]
    asels = body["rows"][0]
    assert asels["verdict_counts"] == {
        "agree": 1,
        "disagree": 1,
        "abstain": 0,
        "total": 2,
    }
    assert set(asels) == {"ticker", "year", "verdict_counts", "reason_counts"}
    assert asels["reason_counts"]["evidence_quality"] == 1
    assert asels["reason_counts"]["model_instability"] == 1


def test_public_demo_mode_never_opens_verdict_writes():
    response = CLIENT.post("/analyst-verdicts", json=_payload())

    assert response.status_code in {401, 403}
    with SessionLocal() as db:
        assert db.query(AnalystVerdict).count() == 0


def test_invalid_enum_ticker_and_note_are_rejected():
    _authenticated_user("loop-negative@example.com")

    responses = [
        CLIENT.post("/analyst-verdicts", json=_payload(verdict="strong_agree")),
        CLIENT.post("/analyst-verdicts", json=_payload(reason_type="crowd_signal")),
        CLIENT.post("/analyst-verdicts", json=_payload(ticker="BAD TICKER")),
        CLIENT.post("/analyst-verdicts", json=_payload(note="x" * 2001)),
    ]

    assert [response.status_code for response in responses] == [422, 422, 422, 422]
    with SessionLocal() as db:
        assert db.query(AnalystVerdict).count() == 0


def test_verdict_rows_never_change_scoring_service_output():
    user_id = _authenticated_user("loop-pin@example.com")
    current = {
        "roa": 0.10,
        "roe": 0.16,
        "operating_margin": 0.20,
        "net_margin": 0.12,
        "current_ratio": 2.0,
        "quick_ratio": 1.2,
        "cash_ratio": 0.4,
        "debt_to_equity": 0.5,
        "debt_to_assets": 0.3,
        "ocf_to_debt": 0.25,
        "ocf_to_assets": 0.15,
        "cash_flow_margin": 0.18,
    }

    with SessionLocal() as db:
        before = run_score(
            current,
            mode="rule_based",
            db=db,
            company_id=999_999,
            period="2025",
        )
        db.add(
            AnalystVerdict(
                ticker="ASELS",
                year=2025,
                verdict="disagree",
                reason_type="methodology",
                note="Pin-test row.",
                user_id=user_id,
            )
        )
        db.flush()
        after = run_score(
            current,
            mode="rule_based",
            db=db,
            company_id=999_999,
            period="2025",
        )

    assert before == after


def test_verdict_api_is_append_only_and_aggregate_exposes_no_notes_or_users():
    paths = CLIENT.get("/openapi.json").json()["paths"]
    verdict_paths = {path: methods for path, methods in paths.items() if path.startswith("/analyst-verdicts")}

    assert set(verdict_paths["/analyst-verdicts"]) == {"post"}
    assert set(verdict_paths["/analyst-verdicts/aggregate"]) == {"get"}
