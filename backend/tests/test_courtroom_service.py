from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import courtroom_service as courtroom
from app.services import skeptic_service


REPO_ROOT = Path(__file__).resolve().parents[2]


def _all_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from _all_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _all_keys(child)


def _resolve(root, dotted_field: str):
    value = root
    for part in dotted_field.split("."):
        value = value[part]
    return value


def test_real_report_is_deterministic_equal_budgeted_cited_and_risk_last(monkeypatch):
    monkeypatch.setenv("RESEARCH_LLM_PROVIDER", "none")
    first = courtroom.courtroom_report("ASELS")
    second = courtroom.courtroom_report("asels")

    assert first == second
    assert first["status"] == "complete"
    assert first["mode"] == "deterministic"
    assert first["ticker"] == "ASELS"
    assert first["year"] == 2025
    assert first["evidence_budget_per_persona"] == courtroom.EVIDENCE_BUDGET
    assert [persona["persona_id"] for persona in first["personas"]] == list(
        courtroom.PERSONA_ORDER
    )
    assert first["personas"][-1]["persona_id"] == "risk"
    assert all(
        len(persona["items"]) == courtroom.EVIDENCE_BUDGET
        for persona in first["personas"]
    )
    assert first["closing"] == courtroom.CLOSING

    for persona in first["personas"]:
        for item in persona["items"]:
            assert set(item) == {"statement", "citation", "limitation"}
            assert set(item["citation"]) == {"field", "value", "source_file"}
            assert item["statement"]
            assert item["limitation"]
            assert (REPO_ROOT / item["citation"]["source_file"]).is_file()


def test_bull_and_bear_percentiles_resolve_to_context_and_accepted_passports():
    report = courtroom.courtroom_report("ASELS", 2024)
    context_path = REPO_ROOT / "data/trusted_clean/company_contexts/ASELS_2024.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    passports = json.loads(
        (REPO_ROOT / "data/trusted_clean/feature_passports.json").read_text(encoding="utf-8")
    )
    accepted = {
        item["name"]
        for item in passports["passports"]
        if item["acceptance_status"] == "accepted_feature"
    }
    bull, bear = report["personas"][:2]
    bull_values = [item["citation"]["value"] for item in bull["items"]]
    bear_values = [item["citation"]["value"] for item in bear["items"]]

    assert bull_values == sorted(bull_values, reverse=True)
    assert bear_values == sorted(bear_values)
    for persona in (bull, bear):
        for item in persona["items"]:
            field = item["citation"]["field"]
            metric = field.rsplit(".", 1)[-1]
            assert metric in accepted
            assert _resolve(context, field) == item["citation"]["value"]
            assert item["citation"]["source_file"] == context_path.relative_to(REPO_ROOT).as_posix()


def test_skeptic_items_are_fixed_verbatim_facts_from_the_challenge_report():
    source = skeptic_service.skeptic_report("ASELS")
    source_checks = {item["check_id"]: item for item in source["checks"]}
    report = courtroom.courtroom_report("ASELS")
    skeptic = report["personas"][2]

    for check_id, item in zip(courtroom._SKEPTIC_CHECK_IDS, skeptic["items"], strict=True):
        evidence = source_checks[check_id]["evidence"][0]
        assert item["statement"] == evidence["fact"]
        assert item["citation"]["value"] == evidence["fact"]
        assert item["citation"]["source_file"] == evidence["source_file"]


def test_response_has_no_adjudication_recommendation_consensus_or_return_projection_surface():
    report = courtroom.courtroom_report("ASELS")
    forbidden_keys = {
        "verdict",
        "recommendation",
        "winner",
        "consensus",
        "consensus_score",
        "expected_return",
        "expected_returns",
        "buy",
        "sell",
        "hold",
    }
    assert forbidden_keys.isdisjoint(set(_all_keys(report)))

    serialized = json.dumps(report, ensure_ascii=False).casefold()
    assert serialized.count("verdict") == 1
    assert courtroom.CLOSING.casefold() in serialized
    remaining = serialized.replace(courtroom.CLOSING.casefold(), "")
    for pattern in (
        r"\b(?:buy|sell|hold)\b",
        r"\bwinner\b",
        r"\bconsensus(?: score)?\b",
        r"\bexpected[-_ ]returns?\b",
        r"\bmarket[-\s]beating\b",
        r"\bprofitable\s+trad(?:e|es|ing)\b",
        r"\b(?:issues?|renders?|reaches?)\s+(?:a\s+)?verdict\b",
    ):
        assert re.search(pattern, remaining, flags=re.IGNORECASE) is None


def test_missing_context_returns_insufficient_data_without_persona_arguments(monkeypatch, tmp_path):
    monkeypatch.setattr(courtroom, "COMPANY_CONTEXTS_DIR", tmp_path / "missing")
    report = courtroom.courtroom_report("ASELS")

    assert report["status"] == "insufficient_data"
    assert report["personas"] == []
    assert report["missing_evidence"] == [
        {
            "source_file": "data/trusted_clean/company_contexts/ASELS_<latest>.json",
            "reason": "company context is missing",
        }
    ]


def test_malformed_context_and_artifacts_return_insufficient_data(monkeypatch, tmp_path):
    contexts = tmp_path / "contexts"
    contexts.mkdir()
    malformed_context = contexts / "ASELS_2025.json"
    malformed_context.write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(courtroom, "COMPANY_CONTEXTS_DIR", contexts)

    context_report = courtroom.courtroom_report("ASELS")
    assert context_report["status"] == "insufficient_data"
    assert context_report["personas"] == []
    assert "malformed" in context_report["missing_evidence"][0]["reason"]

    valid_context = REPO_ROOT / "data/trusted_clean/company_contexts/ASELS_2025.json"
    malformed_context.write_text(valid_context.read_text(encoding="utf-8"), encoding="utf-8")
    malformed_passports = tmp_path / "feature_passports.json"
    malformed_passports.write_text('{"passports": "wrong-shape"}', encoding="utf-8")
    monkeypatch.setattr(courtroom, "FEATURE_PASSPORTS", malformed_passports)

    passport_report = courtroom.courtroom_report("ASELS")
    assert passport_report["status"] == "insufficient_data"
    assert passport_report["personas"] == []
    assert "feature passports are malformed" in passport_report["missing_evidence"][0]["reason"]


def test_api_shape_invalid_ticker_and_missing_year_context():
    client = TestClient(app)
    response = client.post("/research/courtroom", json={"ticker": "ASELS", "year": 2024})
    invalid = client.post("/research/courtroom", json={"ticker": "BAD-TICKER"})
    missing = client.post("/research/courtroom", json={"ticker": "ASELS", "year": 1999})

    assert response.status_code == 200
    assert response.json() == courtroom.courtroom_report("ASELS", 2024)
    assert invalid.status_code == 422
    assert missing.status_code == 200
    assert missing.json()["status"] == "insufficient_data"
