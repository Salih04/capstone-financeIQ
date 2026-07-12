from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services import skeptic_service as skeptic


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT = json.loads((REPO_ROOT / "model_confidence_contract.json").read_text(encoding="utf-8"))


def _prediction_fixture(second_model_reverses: bool) -> pd.DataFrame:
    rows = []
    tickers = ["TEST", "B", "C", "D"]
    first = [4.0, 3.0, 2.0, 1.0]
    second = [1.0, 2.0, 3.0, 4.0] if second_model_reverses else first
    for model, values in (("baseline_equal_weight", first), ("ridge", second)):
        rows.extend(
            {
                "ticker": ticker,
                "year": 2025,
                "model": model,
                "y_pred": value,
            }
            for ticker, value in zip(tickers, values, strict=True)
        )
    return pd.DataFrame(rows)


def test_staleness_probe_fails_on_an_accepted_frozen_input():
    result = skeptic.staleness_frozen_probe(
        {"ticker": "TEST", "year": 2025, "feature_a": 1.0},
        {
            "feature_columns": ["feature_a"],
            "frozen_feature_columns_remaining": ["feature_a"],
        },
        {"columns": {"feature_a": {}}},
        {
            "passports": [
                {"name": "feature_a", "source_class": "vendor_xlsx"},
            ]
        },
    )

    assert result["verdict"] == "fail"
    assert result["severity"] == "high"


def test_staleness_probe_warns_for_a_lineage_gap_without_calling_it_frozen():
    result = skeptic.staleness_frozen_probe(
        {"ticker": "TEST", "year": 2025, "feature_a": 1.0},
        {"feature_columns": ["feature_a"], "frozen_feature_columns_remaining": []},
        {"columns": {"feature_a": {}}},
        {"passports": [{"name": "feature_a", "source_class": "unknown"}]},
    )

    assert result["verdict"] == "warn"
    assert "source_class=unknown" in result["evidence"][-1]["fact"]


def test_missingness_attack_uses_report_coverage_and_warns_for_sparse_row():
    result = skeptic.missingness_attack(
        {"ticker": "TEST", "year": 2025, "a": 1.0, "b": None},
        {
            "feature_columns": ["a", "b"],
            "missingness": {"a": 0.25, "b": 0.25},
        },
    )

    assert result["verdict"] == "warn"
    assert "0.7500" in result["evidence"][1]["fact"]
    assert "not an uncited heuristic" in result["evidence"][1]["fact"]


def test_instability_probe_warns_only_beyond_half_the_field():
    kinds = {"baseline_equal_weight": "baseline", "ridge": "ml"}
    unstable = skeptic.instability_probe("TEST", _prediction_fixture(True), kinds)
    stable = skeptic.instability_probe("TEST", _prediction_fixture(False), kinds)

    assert unstable["verdict"] == "warn"
    assert unstable["severity"] == "high"
    assert "3.0/4" in unstable["evidence"][0]["fact"]
    assert "baseline" in unstable["evidence"][-1]["fact"]
    assert "ml" in unstable["evidence"][-1]["fact"]
    assert stable["verdict"] == "pass"


def test_cohort_challenge_parses_gap_ticker_and_preserves_unknown_reason():
    audit = """
The results describe a retrospectively fixed repository cohort with unresolved survivorship.
It does not prove why an observation is missing.
| Public ticker | Missing years |
|---|---|
| ASTOR | 2020, 2021, 2022 |
"""
    gap = skeptic.cohort_integrity_challenge("ASTOR", audit)
    complete = skeptic.cohort_integrity_challenge("ASELS", audit)

    assert gap["verdict"] == "warn"
    assert gap["severity"] == "high"
    assert "2020, 2021, 2022" in gap["evidence"][1]["fact"]
    assert "does not establish why" in gap["evidence"][1]["fact"]
    assert complete["severity"] == "moderate"


def test_missing_artifacts_return_structured_insufficient_data():
    checks = [
        skeptic.staleness_frozen_probe(None, None, None, None),
        skeptic.missingness_attack(None, None),
        skeptic.instability_probe("TEST", None),
        skeptic.cohort_integrity_challenge("TEST", None),
        skeptic.universe_scale_reminder(None, None, None),
        skeptic.backtest_reminder(None),
    ]

    assert [item["check_id"] for item in checks] == list(skeptic._CHECK_IDS)
    assert all(item["verdict"] == "insufficient_data" for item in checks)
    assert all(set(item) == {"check_id", "verdict", "evidence", "severity"} for item in checks)


def test_real_reports_are_deterministic_ordered_and_fully_cited():
    skeptic._prediction_ranks_cached.cache_clear()
    first = skeptic.skeptic_report("ASELS")
    second = skeptic.skeptic_report("asels")

    assert first == second
    assert skeptic._prediction_ranks_cached.cache_info().misses == 1
    assert skeptic._prediction_ranks_cached.cache_info().hits >= 1
    assert set(first) == {"ticker", "checks", "footer"}
    assert first["ticker"] == "ASELS"
    assert [item["check_id"] for item in first["checks"]] == list(skeptic._CHECK_IDS)
    assert first["checks"][-1]["check_id"] == "backtest_reminder"
    assert first["footer"] == skeptic.FOOTER
    for check in first["checks"]:
        assert set(check) == {"check_id", "verdict", "evidence", "severity"}
        assert check["verdict"] in {"pass", "warn", "fail", "insufficient_data"}
        for evidence in check["evidence"]:
            assert set(evidence) == {"fact", "source_file"}
            assert (REPO_ROOT / evidence["source_file"]).is_file()


def test_real_coverage_gap_ticker_has_audit_warning():
    report = skeptic.skeptic_report("ASTOR")
    cohort = next(
        item for item in report["checks"] if item["check_id"] == "cohort_integrity_challenge"
    )

    assert cohort["verdict"] == "warn"
    assert cohort["severity"] == "high"
    assert any("2020, 2021, 2022" in item["fact"] for item in cohort["evidence"])


def test_response_copy_is_negative_claim_safe_and_has_no_serving_fields():
    report = skeptic.skeptic_report("ASELS")
    response_text = json.dumps(report, ensure_ascii=False)

    for rule in CONTRACT["rules"]:
        for pattern in rule["patterns"]:
            assert re.search(pattern, response_text, re.IGNORECASE) is None
    assert not ({"score", "rank", "forecast", "recommendation", "signal"} & set(report))
    assert CONTRACT["evidence_state"]["reliable_predictive_edge_observed"] is False


def test_skeptic_endpoint_shape_and_invalid_ticker():
    client = TestClient(app)
    response = client.get("/research/skeptic/ASELS")
    invalid = client.get("/research/skeptic/BAD-TICKER")

    assert response.status_code == 200
    assert set(response.json()) == {"ticker", "checks", "footer"}
    assert len(response.json()["checks"]) == 6
    assert invalid.status_code == 422
