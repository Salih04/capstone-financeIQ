from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.research import significance


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "experiments" / "results" / "significance_report.json"


def test_significance_endpoint_is_a_read_only_report_passthrough():
    source = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    response = TestClient(app).get("/research/significance")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == source["schema_version"]
    assert payload["headline"] == source["headline"]
    assert payload["power_analysis"] == source["power_analysis"]
    assert payload["limitations"] == source["limitations"]

    source_models = [model for model in source["models"] if model["kind"] == "ml"]
    assert payload["models"] == source_models
    assert len(payload["models"]) == 6
    for model in payload["models"]:
        pooled = model["pooled"]
        assert pooled["permutation_p_value_two_sided"] is not None
        assert pooled["bonferroni_adjusted_p_value"] is not None
        assert len(pooled["bootstrap_ci_95"]) == 2
        assert len(pooled["null_histogram"]["bin_edges"]) == len(pooled["null_histogram"]["counts"]) + 1


def test_autopsy_service_is_deterministic_and_source_labeled():
    first = significance.autopsy_payload()
    second = significance.autopsy_payload()

    assert first == second
    assert json.dumps(first, sort_keys=True, separators=(",", ":")) == json.dumps(
        second, sort_keys=True, separators=(",", ":")
    )
    assert set(first["evidence"]) == {
        "feature_stability_by_split",
        "feature_stability_summary",
        "coverage_impact",
        "leaderboard",
    }
    for exhibit in first["evidence"].values():
        assert (REPO_ROOT / exhibit["source_file"]).is_file()
        assert exhibit["rows"]

    stability = first["evidence"]["feature_stability_by_split"]["rows"]
    assert len(stability) == 120
    assert stability[0] == {
        "split": "test_2023",
        "feature": "benchmark_same_year_return_pct",
        "train_rows": 73,
        "abs_spearman_to_target": 0.7404,
        "spearman_to_target": -0.7404,
    }
    assert first["evidence"]["coverage_impact"]["rows"][0]["count"] == 33
    assert len(first["evidence"]["leaderboard"]["rows"]) == 27


def test_autopsy_endpoint_reuses_significance_and_pairs_claim_sensitive_values():
    response = TestClient(app).get("/research/significance/autopsy")

    assert response.status_code == 200
    body = response.json()
    assert body == significance.autopsy_payload()
    assert body["significance"] == significance.payload()
    assert body["significance"]["limitations"]

    for model in body["significance"]["models"]:
        pooled = model["pooled"]
        assert pooled["permutation_p_value_two_sided"] is not None
        assert pooled["bonferroni_adjusted_p_value"] is not None

    serialized = json.dumps(body).lower()
    for forbidden in (
        '"recommendation"',
        '"verdict"',
        '"expected_return"',
        'market-beating',
        'profitable trading',
    ):
        assert forbidden not in serialized
