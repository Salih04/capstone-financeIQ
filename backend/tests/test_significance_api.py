from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


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
