"""Focused contract tests for R3-SERV-01 serving-path evaluation."""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import serving_eval as se


def _fixture_modeling(*, missing_test_outcome: bool = False) -> pd.DataFrame:
    rows = []
    tickers = [f"T{i:02d}" for i in range(1, 9)]
    for year in (2020, 2021, 2022):
        for index, ticker in enumerate(tickers, start=1):
            target = float(((index * 7 + year) % 13) - 6)
            if missing_test_outcome and year == 2022 and ticker == "T08":
                target = np.nan
            rows.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "has_target": bool(pd.notna(target)),
                    "next_year_return_pct": target,
                    "feature_a": float(index + (year - 2020) * 0.5),
                    "feature_b": float((9 - index) * (year - 2019)),
                    "feature_sparse": np.nan if ticker == "T03" else float(index % 3),
                }
            )
    return pd.DataFrame(rows)


def _fixture_spec() -> se.SplitSpec:
    return se.SplitSpec(
        name="test_2023",
        train_target_years=(2021, 2022),
        train_feature_years=(2020, 2021),
        test_feature_year=2022,
        test_target_year=2023,
    )


def _fixture_reference(modeling: pd.DataFrame) -> pd.DataFrame:
    rows = modeling[
        (modeling["year"] == 2022) & modeling["next_year_return_pct"].notna()
    ][["ticker", "next_year_return_pct"]].copy()
    rows.insert(1, "year", 2023)
    return rows.rename(columns={"next_year_return_pct": "y_true"}).reset_index(drop=True)


def _write_service_root(root: Path, prepared: se.PreparedSplit) -> None:
    clean = root / "data" / "trusted_clean"
    clean.mkdir(parents=True)
    prepared.training_rows.to_csv(
        clean / "modeling_dataset_training_2020_2025.csv", index=False
    )
    prepared.service_scoring_rows.to_csv(
        clean / "modeling_dataset_public_2020_2025.csv", index=False
    )
    prepared.service_scoring_rows.to_csv(
        clean / "modeling_dataset_2020_2025.csv", index=False
    )


def _load_service_directly(root: Path, monkeypatch: pytest.MonkeyPatch):
    """Independent test-side import of the production file, not experiment code."""
    backend = str(se.ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    monkeypatch.setenv("RESEARCH_REPO_ROOT", str(root))
    module_name = f"_direct_serving_fixture_{root.name}"
    spec = importlib.util.spec_from_file_location(module_name, se.SERVICE_FILE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_analysis(*, ic: float, lower: float, upper: float, p_value: float) -> dict:
    return {
        "status": "estimated",
        "pooled": {
            "observed_ic": ic,
            "bootstrap_ci_95": [lower, upper],
            "permutation_p_value_two_sided": p_value,
        },
        "exploratory_by_split": [
            {
                "split": "test_2023",
                "year": 2023,
                "n": 8,
                "observed_ic": ic,
                "bootstrap_ci_95": [lower, upper],
                "permutation_p_value_two_sided": p_value,
            }
        ],
    }


def _fake_split_record() -> dict:
    return {
        "name": "test_2023",
        "train_feature_years": [2020, 2021],
        "train_target_years": [2021, 2022],
        "test_feature_year": 2022,
        "test_target_year": 2023,
        "training_rows": 16,
        "service_training_window": [2020, 2021],
        "panel_rows": 8,
        "eligible_rows": 8,
        "excluded_missing_outcome": [],
        "selected_parameters": [{"name": "feature_a", "weight": 1.0, "rank": 1}],
        "prediction_artifact": "experiments/results_serving_eval/predictions_serving_2023.csv",
    }


def test_exact_walk_forward_year_boundaries_match_canonical_harness():
    assert [
        (
            spec.name,
            spec.train_feature_years,
            spec.train_target_years,
            spec.test_feature_year,
            spec.test_target_year,
        )
        for spec in se.split_specs()
    ] == [
        ("test_2023", (2020, 2021), (2021, 2022), 2022, 2023),
        ("test_2024", (2020, 2021, 2022), (2021, 2022, 2023), 2023, 2024),
        ("test_2025", (2020, 2021, 2022, 2023), (2021, 2022, 2023, 2024), 2024, 2025),
    ]


def test_training_restriction_and_test_outcome_non_visibility():
    modeling = _fixture_modeling()
    prepared = se.prepare_split(modeling, _fixture_reference(modeling), _fixture_spec())
    assert tuple(sorted(prepared.training_rows["year"].unique())) == (2020, 2021)
    assert prepared.training_rows["year"].max() < prepared.spec.test_feature_year
    assert prepared.service_scoring_rows["next_year_return_pct"].isna().all()
    assert prepared.service_scoring_rows["has_target"].eq(False).all()
    assert prepared.realized_outcomes["y_true"].notna().all()


def test_same_eligible_cohort_and_missing_outcome_handling_are_explicit():
    modeling = _fixture_modeling(missing_test_outcome=True)
    reference = _fixture_reference(modeling)
    prepared = se.prepare_split(modeling, reference, _fixture_spec())
    assert prepared.panel_rows == 8
    assert len(prepared.service_scoring_rows) == 7
    assert set(prepared.service_scoring_rows["ticker"]) == set(reference["ticker"])
    assert prepared.excluded_missing_outcome == ("T08",)


def test_present_outcome_omitted_from_reference_is_rejected():
    modeling = _fixture_modeling()
    reference = _fixture_reference(modeling).query("ticker != 'T08'")
    with pytest.raises(ValueError, match="omits rows with present outcomes"):
        se.prepare_split(modeling, reference, _fixture_spec())


def test_duplicate_ticker_year_is_rejected(tmp_path: Path):
    modeling = _fixture_modeling()
    duplicate = pd.concat([modeling, modeling.iloc[[0]]], ignore_index=True)
    path = tmp_path / "duplicate.csv"
    duplicate.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate ticker/year"):
        se.load_modeling_dataset(path)


def test_harness_invokes_real_service_and_matches_direct_output_row_for_row(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    modeling = _fixture_modeling()
    prepared = se.prepare_split(modeling, _fixture_reference(modeling), _fixture_spec())
    _write_service_root(tmp_path, prepared)
    service = _load_service_directly(tmp_path, monkeypatch)
    assert Path(inspect.getsourcefile(service.train_parameters)).resolve() == se.SERVICE_FILE.resolve()
    assert Path(inspect.getsourcefile(service.run_forecast)).resolve() == se.SERVICE_FILE.resolve()

    direct_trained = service.train_parameters(
        train_year_from=2020,
        train_year_to=2021,
        top_n=se.TOP_N,
        target_mode=service.TARGET_MODE_FINALIZED,
    )
    direct_weights = {
        row["name"]: row["weight"] for row in direct_trained["top_parameters"]
    }
    direct = service.run_forecast(
        year=2022,
        trained_weights=direct_weights,
        risk_level="medium",
        user_type="individual",
    )

    calls = {"train_parameters": 0, "run_forecast": 0}
    original_train = service.train_parameters
    original_run = service.run_forecast

    def train_wrapper(*args, **kwargs):
        calls["train_parameters"] += 1
        return original_train(*args, **kwargs)

    def run_wrapper(*args, **kwargs):
        calls["run_forecast"] += 1
        return original_run(*args, **kwargs)

    monkeypatch.setattr(service, "train_parameters", train_wrapper)
    monkeypatch.setattr(service, "run_forecast", run_wrapper)
    harness_trained, harness = se.invoke_loaded_service(service, _fixture_spec())

    assert calls == {"train_parameters": 1, "run_forecast": 1}
    assert harness_trained["top_parameters"] == direct_trained["top_parameters"]
    assert json.dumps(harness["items"], sort_keys=True) == json.dumps(
        direct["items"], sort_keys=True
    )

    predictions = se.predictions_from_service(prepared, harness)
    direct_scores = {row["ticker"]: row["score"] for row in direct["items"]}
    assert predictions["y_pred"].tolist() == [
        direct_scores[ticker] for ticker in predictions["ticker"]
    ]


def test_service_missing_features_and_deterministic_ties_are_preserved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    modeling = _fixture_modeling()
    prepared = se.prepare_split(modeling, _fixture_reference(modeling), _fixture_spec())
    scoring = prepared.service_scoring_rows.head(3).copy()
    scoring["feature_a"] = [1.0, 1.0, np.nan]
    prepared.service_scoring_rows = scoring
    prepared.realized_outcomes = prepared.realized_outcomes[
        prepared.realized_outcomes["ticker"].isin(scoring["ticker"])
    ].copy()
    _write_service_root(tmp_path, prepared)
    service = _load_service_directly(tmp_path, monkeypatch)

    first = service.run_forecast(year=2022, trained_weights={"feature_a": 1.0})
    second = service.run_forecast(year=2022, trained_weights={"feature_a": 1.0})
    assert first["items"] == second["items"]
    assert [row["ticker"] for row in first["items"][:2]] == ["T01", "T02"]
    missing = next(row for row in first["items"] if row["ticker"] == "T03")
    assert missing["missing_parameters"] == ["feature_a"]
    assert missing["confidence"] == 0.0


def test_constant_output_has_explicit_insufficient_data_state():
    rows = pd.DataFrame(
        {
            "ticker": ["A", "B", "C"],
            "year": [2023, 2023, 2023],
            "model": [se.MODEL_NAME] * 3,
            "y_true": [1.0, 2.0, 3.0],
            "y_pred": [0.5, 0.5, 0.5],
            "split": ["test_2023"] * 3,
        }
    )
    result = se.analyze_serving_predictions(rows, permutations=1_000, bootstraps=10)
    assert result["status"] == "insufficient_data"
    assert "Spearman IC is undefined" in result["reason"]


def test_too_few_rows_has_explicit_insufficient_data_state():
    rows = pd.DataFrame(
        {
            "ticker": ["A", "B"],
            "year": [2023, 2023],
            "model": [se.MODEL_NAME] * 2,
            "y_true": [1.0, 2.0],
            "y_pred": [0.2, 0.8],
            "split": ["test_2023"] * 2,
        }
    )
    result = se.analyze_serving_predictions(rows, permutations=1_000, bootstraps=10)
    assert result == {
        "status": "insufficient_data",
        "reason": "test_2023 has fewer than three eligible rows",
    }


def test_raw_p_value_is_outside_family_and_no_serving_adjusted_field():
    report = se.build_report(
        _fake_analysis(ic=-0.123, lower=-0.300, upper=0.050, p_value=0.2345),
        [_fake_split_record()],
    )
    serving = report["serving_result"]
    assert serving["test_label"] == se.SINGLE_TEST_LABEL
    assert serving["raw_permutation_p_value_two_sided"] == 0.2345
    assert not any("bonferroni" in key.lower() for key in serving)
    assert report["six_model_family_context"]["family_size"] == 6
    assert len(report["six_model_family_context"]["models"]) == 6
    assert se.MODEL_NAME not in report["six_model_family_context"]["family"]


def test_precommitted_negative_wording_is_not_contrarian():
    sentence = se.format_conclusion(
        _fake_analysis(ic=-0.123, lower=-0.300, upper=0.050, p_value=0.2345)
    )
    assert sentence == (
        "The user-facing serving heuristic's walk-forward IC is -0.123 (95% CI "
        "[-0.300,0.050], permutation p=0.2345); this is not distinguishable from "
        "the within-year null, and in either case does not establish investment value, "
        "implementability, or a reliable predictive edge."
    )
    assert "contrarian" not in sentence.lower()


def test_distinguishable_fixture_still_does_not_claim_predictive_edge():
    sentence = se.format_conclusion(
        _fake_analysis(ic=0.350, lower=0.100, upper=0.500, p_value=0.0100)
    )
    assert "this is distinguishable from the within-year null" in sentence
    assert sentence.endswith(
        "does not establish investment value, implementability, or a reliable predictive edge."
    )


def test_report_provenance_checksums_owner_and_pending_review_are_pinned():
    report = se.build_report(
        _fake_analysis(ic=0.100, lower=-0.100, upper=0.300, p_value=0.5000),
        [_fake_split_record()],
    )
    assert report["task"] == se.TASK_ID
    assert report["service_path_parity"]["functions_invoked"] == list(se.SERVICE_FUNCTIONS)
    assert report["artifact_ownership"]["owner"] == se.REGENERATION_COMMAND
    assert report["artifact_ownership"]["hand_edit_forbidden"] is True
    assert report["independent_review"]["status"] == "PENDING"
    assert report["independent_review"]["merge_ready"] is False
    for source in report["source_artifacts"]:
        path = se.ROOT / source["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == source["sha256"]


def test_json_and_markdown_rendering_are_byte_deterministic():
    analysis = _fake_analysis(ic=0.100, lower=-0.100, upper=0.300, p_value=0.5000)
    report_one = se.build_report(analysis, [_fake_split_record()])
    report_two = se.build_report(analysis, [_fake_split_record()])
    json_one = json.dumps(report_one, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    json_two = json.dumps(report_two, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    assert json_one.encode() == json_two.encode()
    assert se.render_markdown(report_one).encode() == se.render_markdown(report_two).encode()


def test_prediction_serialization_preserves_service_precision(tmp_path: Path):
    frame = pd.DataFrame(
        [
            {
                "ticker": "AAA",
                "year": 2023,
                "model": se.MODEL_NAME,
                "y_true": 12.3456789012345,
                "y_pred": 0.1234,
            }
        ]
    )
    path = tmp_path / "predictions.csv"
    se._write_prediction_dump(frame, path)
    loaded = pd.read_csv(path)
    assert loaded.loc[0, "y_pred"] == 0.1234
    assert loaded.loc[0, "y_true"] == pytest.approx(frame.loc[0, "y_true"], rel=0, abs=1e-15)


def test_environment_override_is_restored_after_service_import(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    modeling = _fixture_modeling()
    prepared = se.prepare_split(modeling, _fixture_reference(modeling), _fixture_spec())
    _write_service_root(tmp_path, prepared)
    monkeypatch.setenv("RESEARCH_REPO_ROOT", "/sentinel")
    service = se._load_service_module(tmp_path)
    assert os.environ["RESEARCH_REPO_ROOT"] == "/sentinel"
    assert service._REPO_ROOT == tmp_path
