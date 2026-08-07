from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["RESEARCH_LLM_PROVIDER"] = "none"

from app.main import app  # noqa: E402
from app.services import citations, skeptic_service  # noqa: E402
from app.services.research import calibration, significance  # noqa: E402


CLIENT = TestClient(app)
REPO = Path(__file__).resolve().parents[2]
SIGNIFICANCE_SOURCE = "experiments/results/significance_report.json"
CALIBRATION_SOURCE = "experiments/results/calibration_report.json"
FRICTION_SOURCE = "experiments/results/friction_report.json"
FRICTION_MARKDOWN_SOURCE = "experiments/results/friction_report.md"
SKEPTIC_SOURCE = "backend/app/services/skeptic_service.py"
CITATION_KEYS = {
    "citation_id",
    "citation_kind",
    "evidence_family",
    "source_artifact",
    "sha256",
    "scope",
    "field_path",
    "value",
    "derivation",
    "locator",
    "quoted_text",
    "label",
}


def _sha(relative: str) -> str:
    return hashlib.sha256((REPO / relative).read_bytes()).hexdigest()


def _assert_citations(
    response: dict, expected_family: str, expected_source: str | tuple[str, ...]
) -> None:
    expected_sources = {expected_source} if isinstance(expected_source, str) else set(expected_source)
    citations_body = response["citations"]
    assert citations_body
    assert [item["citation_id"] for item in citations_body] == [
        f"C{index:03d}" for index in range(1, len(citations_body) + 1)
    ]
    for item in citations_body:
        assert set(item) == CITATION_KEYS
        assert item["evidence_family"] == expected_family
        assert item["source_artifact"] in expected_sources
        assert item["sha256"] == _sha(item["source_artifact"])
        if item["citation_kind"] == "json_field":
            assert item["field_path"]
            assert item["locator"] is None
            citations.verify_json_field(
                item["source_artifact"], item["field_path"], item["value"]
            )
        elif item["citation_kind"] == "text_span":
            assert item["field_path"] is None
            citations.verify_text_span(
                item["source_artifact"], item["locator"], item["quoted_text"]
            )
        else:
            assert item["citation_kind"] == "service_evidence"
            assert item["field_path"]


def test_significance_headline_is_six_model_and_source_bound() -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": "raw and adjusted p-value significance"}
    )
    assert response.status_code == 200
    body = response.json()
    evidence = body["grounded_evidence"]
    expected = significance.significance_headline_payload()
    assert body["intent"] == "significance_headline"
    assert body["answer"] == expected["answer"] == body["grounded_answer"]
    assert evidence["analysis"]["multiplicity"]["family_size"] == 6
    assert evidence["analysis"]["multiplicity"]["method"] == "Bonferroni"
    assert str(evidence["headline"]["permutation_p_value_two_sided"]) in body["answer"]
    assert str(evidence["headline"]["bonferroni_adjusted_p_value"]) in body["answer"]
    assert body["llm_used"] is False
    assert body["llm_result"] is None
    _assert_citations(body, "significance", SIGNIFICANCE_SOURCE)


def test_significance_serving_query_is_not_the_six_model_branch() -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": "serving significance headline"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "general"
    assert body.get("grounded_evidence") is None
    assert body.get("citations", []) == []


def test_skeptic_report_reuses_exact_service_shape_and_order() -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": "skeptic report for THYAO"}
    )
    assert response.status_code == 200
    body = response.json()
    evidence = body["grounded_evidence"]
    assert body["intent"] == "skeptic_report"
    assert set(evidence) == {"ticker", "checks", "footer"}
    assert evidence["ticker"] == "THYAO"
    assert [check["check_id"] for check in evidence["checks"]] == [
        "staleness_frozen_probe",
        "missingness_attack",
        "instability_probe",
        "cohort_integrity_challenge",
        "universe_scale_reminder",
        "backtest_reminder",
    ]
    assert body["answer"] == body["grounded_answer"]
    assert body["llm_used"] is False
    _assert_citations(body, "skeptic", SKEPTIC_SOURCE)
    for item in body["citations"]:
        assert citations.resolve_field(
            evidence, item["field_path"], source=SKEPTIC_SOURCE
        ) == item["value"]


def test_skeptic_body_ticker_normalizes_and_invalid_or_ambiguous_input_falls_back() -> None:
    normalized = CLIENT.post(
        "/research/ask", json={"question": "skeptic report", "ticker": "thyao"}
    ).json()
    assert normalized["intent"] == "skeptic_report"
    assert normalized["grounded_evidence"]["ticker"] == "THYAO"

    invalid = CLIENT.post(
        "/research/ask", json={"question": "skeptic report", "ticker": "bad!"}
    ).json()
    assert invalid["intent"] != "skeptic_report"
    assert invalid.get("grounded_evidence") is None
    assert invalid.get("citations", []) == []

    ambiguous = CLIENT.post(
        "/research/ask", json={"question": "skeptic report for THYAO and ASELS"}
    ).json()
    assert ambiguous["intent"] != "skeptic_report"
    assert ambiguous.get("grounded_evidence") is None
    assert ambiguous.get("citations", []) == []


@pytest.mark.parametrize("ticker", ["ZZZZ", "A1B2", "XYZ.DE"])
def test_skeptic_query_accepts_unknown_digit_and_dot_tickers(ticker: str) -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": f"skeptic report for {ticker}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "skeptic_report"
    assert body["grounded_evidence"]["ticker"] == ticker


def test_skeptic_query_body_agreement_and_disagreement_are_deterministic() -> None:
    agreed = CLIENT.post(
        "/research/ask",
        json={"question": "skeptic report for ZZZZ", "ticker": "zzzz"},
    ).json()
    assert agreed["intent"] == "skeptic_report"
    assert agreed["grounded_evidence"]["ticker"] == "ZZZZ"

    disagreed = CLIENT.post(
        "/research/ask",
        json={"question": "skeptic report for ZZZZ", "ticker": "THYAO"},
    ).json()
    assert disagreed["intent"] != "skeptic_report"
    assert disagreed.get("grounded_evidence") is None
    assert disagreed.get("citations", []) == []


def test_calibration_finding_preserves_producer_owned_boundary() -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": "calibration finding"}
    )
    assert response.status_code == 200
    body = response.json()
    evidence = body["grounded_evidence"]
    expected = calibration.payload()
    assert body["intent"] == "calibration_finding"
    assert body["answer"] == body["grounded_answer"]
    assert body["answer"].startswith(expected["panel_copy"])
    assert evidence["confidence_quantity"]["confidence_score"] == 0.25
    assert evidence["sample"]["independent_ticker_year_outcomes"] == 240
    assert evidence["calibration"]["status"] == "not_estimable"
    assert evidence["claim_safety"]["confidence_is_probability_of_return_profit_or_success"] is False
    assert evidence["claim_safety"]["confidence_is_recommendation_strength"] is False
    _assert_citations(body, "calibration", CALIBRATION_SOURCE)


def test_friction_stamp_is_exact_and_bounded() -> None:
    response = CLIENT.post(
        "/research/ask", json={"question": "friction sensitivity stamp"}
    )
    assert response.status_code == 200
    body = response.json()
    evidence = body["grounded_evidence"]
    expected = significance.friction_stamp_payload()
    assert body["intent"] == "friction_stamp"
    assert body["answer"] == expected["answer"] == body["grounded_answer"]
    assert set(evidence) == {"answer", "task", "chart_stamp", "limitations", "claim_safety"}
    assert "plot_rows" not in evidence
    assert "wealth_path" not in evidence
    assert "horizon" not in evidence
    assert "recommendation" not in evidence
    assert evidence["claim_safety"]["implementable_returns_established"] is False
    assert evidence["claim_safety"]["investment_value_established"] is False
    _assert_citations(
        body, "friction", (FRICTION_SOURCE, FRICTION_MARKDOWN_SOURCE)
    )
    markdown_citations = [
        item for item in body["citations"] if item["citation_kind"] == "text_span"
    ]
    assert len(markdown_citations) == 1
    assert markdown_citations[0]["source_artifact"] == FRICTION_MARKDOWN_SOURCE
    assert markdown_citations[0]["quoted_text"] == evidence["chart_stamp"]


def test_new_grounded_responses_are_deterministic() -> None:
    first = CLIENT.post(
        "/research/ask", json={"question": "friction sensitivity stamp"}
    ).json()
    second = CLIENT.post(
        "/research/ask", json={"question": "friction sensitivity stamp"}
    ).json()
    assert first == second


@pytest.mark.parametrize(
    ("question", "service", "expected_intent"),
    [
        ("significance headline", significance, "significance_headline"),
        ("calibration finding", calibration, "calibration_finding"),
    ],
)
def test_grounded_source_failure_returns_normal_fallback(
    monkeypatch: pytest.MonkeyPatch, question: str, service, expected_intent: str
) -> None:
    def fail(*_args, **_kwargs):
        raise RuntimeError("source unavailable")

    monkeypatch.setattr(
        service,
        "_strict_json_source" if expected_intent == "significance_headline" else "payload",
        fail,
    )
    body = CLIENT.post("/research/ask", json={"question": question}).json()
    assert body["intent"] == expected_intent
    assert body["fallback_used"] is True
    assert body["llm_used"] is False
    assert body.get("grounded_evidence") is None
    assert body.get("citations", []) == []


def test_calibration_and_friction_collision_keeps_existing_fallback() -> None:
    body = CLIENT.post(
        "/research/ask", json={"question": "calibration finding and friction stamp"}
    ).json()
    assert body["intent"] == "general"
    assert body.get("grounded_evidence") is None
    assert body.get("citations", []) == []


def test_direct_skeptic_service_contract_remains_the_source() -> None:
    report = skeptic_service.skeptic_report("THYAO")
    assert report["ticker"] == "THYAO"
    assert report["footer"] == skeptic_service.FOOTER
