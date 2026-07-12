from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "data" / "trusted_clean" / "feature_passports.json"


def test_feature_passports_endpoint_is_a_read_only_generated_artifact_passthrough():
    source = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    response = TestClient(app).get("/research/feature-passports")

    assert response.status_code == 200
    assert response.json() == source
    assert len(response.json()["passports"]) == 61

