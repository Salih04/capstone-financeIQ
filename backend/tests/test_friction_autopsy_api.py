from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services.research import significance


REPO_ROOT = Path(__file__).resolve().parents[2]
FRICTION_REPORT = REPO_ROOT / "experiments" / "results" / "friction_report.json"


def test_autopsy_payload_exposes_generated_friction_report_without_recalculation() -> None:
    source = json.loads(FRICTION_REPORT.read_text(encoding="utf-8"))
    payload = significance.autopsy_payload()

    assert payload["friction"] == source
    assert payload["friction"]["task"] == "R2-FRICTION-01"
    assert payload["friction"]["design"]["raw_prediction_magnitudes_emitted"] is False
    assert payload["friction"]["claim_safety"]["implementable_returns_established"] is False


def test_autopsy_endpoint_keeps_every_net_value_paired_with_gross_and_stamp() -> None:
    response = TestClient(app).get("/research/significance/autopsy")

    assert response.status_code == 200
    friction = response.json()["friction"]
    for row in friction["plot_rows"]:
        assert "gross_basket_mean_return_pct" in row
        assert "net_basket_mean_return_pct" in row
        assert row["chart_stamp"] == friction["chart_stamp"]
