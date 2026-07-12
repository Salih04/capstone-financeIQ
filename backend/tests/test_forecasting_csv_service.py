from __future__ import annotations

import pandas as pd
import pytest

from app.services import forecasting_csv_service as svc


@pytest.fixture
def forecast_rows_with_missing_feature() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "ticker": "FULL",
                "year": 2024,
                "feature_a": 10.0,
                "feature_b": 20.0,
                "is_inference_row": False,
            },
            {
                "ticker": "MISS",
                "year": 2024,
                "feature_a": 5.0,
                "feature_b": None,
                "is_inference_row": False,
            },
            {
                "ticker": "PEER",
                "year": 2024,
                "feature_a": 1.0,
                "feature_b": 10.0,
                "is_inference_row": False,
            },
        ]
    )


def test_csv_options_public_universe_only():
    opts = svc.get_options()

    assert opts["available"] is True
    assert opts["ticker_count"] == 40
    assert opts["data_source"] == "modeling_dataset_public_2020_2025.csv"
    assert opts["training_data_source"] == "modeling_dataset_training_2020_2025.csv"


def test_training_uses_internal_expanded_dataset_and_run_outputs_public_40():
    trained = svc.train_parameters(train_year_from=2020, train_year_to=2024, top_n=8)

    assert trained["total_training_rows"] >= 200
    assert trained["winner_rows"] > 0
    assert len(trained["top_parameters"]) <= 8

    weights = {p["name"]: p["weight"] for p in trained["top_parameters"]}
    result = svc.run_forecast(year=2025, trained_weights=weights)

    assert result["stock_count"] == 40
    assert len(result["items"]) == 40
    assert all(item["is_inference_row"] for item in result["items"])


def test_missing_feature_reduces_confidence_and_is_not_imputed(
    monkeypatch, forecast_rows_with_missing_feature
):
    monkeypatch.setattr(svc, "_load_df", lambda: forecast_rows_with_missing_feature)

    result = svc.run_forecast(
        year=2024,
        trained_weights={"feature_a": 1.0, "feature_b": 1.0},
    )
    items = {item["ticker"]: item for item in result["items"]}

    assert items["FULL"]["confidence"] == 1.0
    assert items["MISS"]["confidence"] == 0.5
    assert items["MISS"]["confidence"] < items["FULL"]["confidence"]
    assert items["MISS"]["missing_parameters"] == ["feature_b"]
    assert {p["name"] for p in items["MISS"]["top_parameters"]} == {"feature_a"}


def test_missing_feature_explanation_calls_out_reduced_confidence(
    monkeypatch, forecast_rows_with_missing_feature
):
    monkeypatch.setattr(svc, "_load_df", lambda: forecast_rows_with_missing_feature)

    result = svc.run_forecast(
        year=2024,
        trained_weights={"feature_a": 1.0, "feature_b": 1.0},
    )
    items = {item["ticker"]: item for item in result["items"]}

    assert "Some features missing — confidence reduced." in items["MISS"]["warnings"]
    assert "Some features missing — confidence reduced." not in items["FULL"]["warnings"]
