from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.research import regime


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "experiments" / "results_regime" / "regime_context_report.json"


def test_regime_context_endpoint_is_a_read_only_report_passthrough() -> None:
    regime.payload.cache_clear()
    source = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    response = TestClient(app).get("/research/regime-context")

    assert response.status_code == 200
    assert response.json() == source
    diagnostics = response.json()["conditional_diagnostics"]
    assert diagnostics["computed"] is False
    assert diagnostics["status"] == "not_computed_insufficient_regime_diversity"
    assert diagnostics["observed_distinct_regimes"] == 1


def test_regime_context_values_are_sourced_or_null_and_claim_safe() -> None:
    regime.payload.cache_clear()
    body = TestClient(app).get("/research/regime-context").json()

    for row in body["macro_context"]:
        for key in (
            "cpi_december_yoy_pct",
            "policy_rate_year_end_pct",
            "usdtry_year_end_try_per_usd",
            "bist100_return_pct",
        ):
            metric = row[key]
            if metric["value"] is None:
                assert metric["effective_date"] is None
                assert metric["source_id"] is None
                assert metric["source"] is None
            else:
                assert metric["effective_date"]
                assert metric["source_id"]
                assert metric["source"]

    serialized = json.dumps(body).casefold()
    assert '"recommendation"' not in serialized
    assert '"regime_specific_edge"' not in serialized
    assert '"observed_ic"' not in serialized
