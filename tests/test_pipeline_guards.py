from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "trusted_clean"
CONFIG = ROOT / "data" / "config"


def _csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, comment="#")


def test_public_40_vs_expanded_training_universe_split():
    public_uni = _csv(CONFIG / "universe_public_40.csv")
    training_uni = _csv(CONFIG / "universe_training_bist100.csv")
    public = _csv(CLEAN / "modeling_dataset_public_2020_2025.csv")
    training = _csv(CLEAN / "modeling_dataset_training_2020_2025.csv")

    public_tickers = set(public_uni["ticker"].astype(str).str.upper())
    training_tickers = set(training_uni["ticker"].astype(str).str.upper())

    assert len(public_tickers) == 40
    assert public_tickers.issubset(training_tickers)
    assert set(public["ticker"].astype(str).str.upper()) == public_tickers
    assert set(training["ticker"].astype(str).str.upper()).issubset(training_tickers)
    assert training["ticker"].nunique() >= public["ticker"].nunique()


def test_leakage_guards_exclude_targets_and_same_year_return_from_features():
    quality = json.loads((CLEAN / "data_quality_report.json").read_text())
    features = set(quality["feature_columns"])

    assert "same_year_return_pct" not in features
    assert "next_year_return_pct" not in features
    assert not any(c.startswith("next_year_") for c in features)
    assert quality["valid_for_T_to_T1_modeling"] is True
    assert quality["issues"] == []


def test_2025_is_inference_only_without_t_plus_1_target():
    public = _csv(CLEAN / "modeling_dataset_public_2020_2025.csv")
    y2025 = public[public["year"] == 2025]

    assert len(y2025) == 40
    assert y2025["has_target"].astype(str).str.lower().isin({"false", "0"}).all()
    assert y2025["is_inference_row"].astype(str).str.lower().isin({"true", "1"}).all()
    assert y2025["next_year_return_pct"].isna().all()


def test_modeling_schema_has_leakage_safe_market_features():
    public = _csv(CLEAN / "modeling_dataset_public_2020_2025.csv")
    expected = {
        "price_adjclose_t",
        "price_data_available",
        "price_history_years_available",
        "price_momentum_1y_pct",
        "price_momentum_2y_pct",
        "price_drawdown_from_3y_high_pct",
        "benchmark_same_year_return_pct",
        "price_vs_bist100_1y_pct",
    }
    assert expected.issubset(public.columns)
    assert public["price_momentum_1y_pct"].notna().sum() > 0
