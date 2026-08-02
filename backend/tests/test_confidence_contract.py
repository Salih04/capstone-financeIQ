from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.services import forecasting_csv_service as svc


REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "model_confidence_contract.json"


def test_forecasting_service_satisfies_model_confidence_contract(monkeypatch):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    approved = contract["approved_wording"]
    inference_contract = contract["inference_contract"]

    assert contract["version"] == "1.10.0"
    assert contract["evidence_state"]["reliable_predictive_edge_observed"] is False
    assert svc.DISCLAIMER == approved["primary_disclaimer"]

    monkeypatch.setattr(
        svc,
        "_load_public_df",
        lambda: pd.DataFrame([{"ticker": "TEST", "year": 2025}]),
    )
    monkeypatch.setattr(
        svc,
        "train_parameters",
        lambda **_kwargs: {"top_parameters": [{"name": "feature_a", "weight": 1.0}]},
    )
    monkeypatch.setattr(
        svc,
        "run_forecast",
        lambda **_kwargs: {
            "items": [
                {
                    "rank": 1,
                    "ticker": "TEST",
                    "score": 0.5,
                    "confidence": 1.0,
                    "confidence_label": "high",
                    "top_parameters": [],
                    "is_inference_row": True,
                }
            ]
        },
    )

    response = svc.inference_forecast(input_year=2025)
    assert response[inference_contract["response_status_field"]] == inference_contract["required_status"]
    assert response["disclaimer"] == approved["primary_disclaimer"]
    assert response["rankings"]
    for row in response["rankings"]:
        for field, required_value in inference_contract["row_requirements"].items():
            assert row[field] is required_value
