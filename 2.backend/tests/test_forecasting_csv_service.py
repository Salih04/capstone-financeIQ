from __future__ import annotations

from app.services import forecasting_csv_service as svc


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
