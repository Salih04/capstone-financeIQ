from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.research import calibration


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "experiments" / "results" / "calibration_report.json"


def _load() -> dict:
    return json.loads(REPORT_PATH.read_text(encoding="utf-8"))


def _clear_cache() -> None:
    # No-op once a test has monkeypatched the loader with a plain function.
    clear = getattr(calibration._load_cached, "cache_clear", None)
    if clear is not None:
        clear()


def _body() -> dict:
    _clear_cache()
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 200
    return response.json()


def _route_status(monkeypatch, doctored: Any) -> int:
    """GET the public route while the committed artifact reads as ``doctored``."""
    _clear_cache()
    monkeypatch.setattr(calibration, "_load_cached", lambda *_args: doctored)
    return TestClient(app).get("/research/calibration").status_code


# ---------------------------------------------------------------------------
# Happy path: the committed artifact still produces the same served response.
# ---------------------------------------------------------------------------


def test_endpoint_success_and_schema() -> None:
    body = _body()
    assert body["task"] == "R3-UI-03"
    assert body["schema_version"] == 1
    assert body["source_task"] == "R2-CAL-01"
    assert body["source_artifact"] == "experiments/results/calibration_report.json"
    assert (REPO_ROOT / body["source_artifact"]).is_file()
    for block in ("calibration", "confidence_quantity", "claim_safety", "sample", "replay_provenance"):
        assert isinstance(body[block], dict)
    assert isinstance(body["limitations"], list) and body["limitations"]


def test_values_are_exact_passthrough_of_the_committed_report() -> None:
    body = _body()
    report = _load()

    assert body["report_schema_version"] == report["schema_version"]
    assert body["claim_safety"] == report["claim_safety"]
    assert body["sample"] == report["sample"]
    assert body["limitations"] == report["limitations"]

    calib = report["calibration"]
    served = body["calibration"]
    assert served["status"] == calib["status"] == "not_estimable"
    assert served["verdict"] == calib["verdict"]
    assert served["confidence_values"] == calib["confidence_values"] == [0.25]
    assert served["confidence_unique_values"] == calib["confidence_unique_values"] == 1
    assert served["informative_about_rank_error"] == calib["informative_about_rank_error"] is False
    assert served["requested_bins"] == calib["requested_bins"]
    assert served["realized_bins"] == calib["realized_bins"]

    monotonicity = calib["monotonicity"]
    served_mono = body["calibration"]["monotonicity"]
    assert served_mono["status"] == monotonicity["status"] == "not_estimable"
    assert served_mono["reason"] == monotonicity["reason"]
    assert served_mono["higher_confidence_lower_error_spearman"] is None
    assert served_mono["bootstrap_95pct"] is None
    assert served_mono["bootstrap_samples_requested"] == monotonicity["bootstrap_samples_requested"]
    assert served_mono["bootstrap_samples_usable"] == monotonicity["bootstrap_samples_usable"] == 0
    assert served_mono["seed"] == monotonicity["seed"]

    quantity = report["confidence_quantity"]
    served_quantity = body["confidence_quantity"]
    assert served_quantity["confidence_score"] == quantity["confidence_score"] == 0.25
    assert served_quantity["quantity"] == quantity["quantity"]
    assert served_quantity["scope"] == quantity["scope"]
    assert served_quantity["hybrid_weight"] == quantity["hybrid_weight"]
    assert served_quantity["confidence_reasons"] == quantity["confidence_reasons"]
    assert served_quantity["confidence_level"] == quantity["confidence_level"]
    assert served_quantity["service_function"] == quantity["service_function"]
    assert served_quantity["consumer_function"] == quantity["consumer_function"]


def test_replay_provenance_matches_the_copy_and_the_artifact() -> None:
    body = _body()
    provenance = _load()["replay_provenance"]
    assert body["replay_provenance"]["git_sha"] == provenance["git_sha"]
    assert body["replay_provenance"]["git_sha"].startswith("a95e1e1c")
    assert body["replay_provenance"]["replay_date"] == provenance["replay_date"]
    assert body["replay_provenance"]["random_seed"] == provenance["random_seed"]
    assert body["replay_provenance"]["code_version"] == provenance["code_version"]
    assert body["sample"]["independent_ticker_year_outcomes"] == 240


def test_fixed_panel_copy_is_verbatim() -> None:
    body = _body()
    assert body["panel_copy"] == (
        "Confidence audited (R2-CAL-01, replay of git `a95e1e1c`): the hybrid "
        "confidence component was constant at 0.25 across all 240 audited "
        "ticker-year outcomes, so calibration against rank error is not estimable "
        "at this scale. Confidence is not a probability of return or recommendation "
        "strength."
    )
    assert body["panel_copy"] == calibration.PANEL_COPY


def test_response_is_claim_safe() -> None:
    body = _body()
    serialized = json.dumps(body).lower()
    for forbidden in ("unreliable", "predicts", "recommendation strength is", "market-beating"):
        assert forbidden not in serialized
    assert body["claim_safety"]["confidence_is_probability_of_return_profit_or_success"] is False
    assert body["claim_safety"]["confidence_is_recommendation_strength"] is False
    assert body["claim_safety"]["validated_predictive_reliability_established"] is False


# ---------------------------------------------------------------------------
# Route-level fail-closed behaviour: missing / unreadable / malformed artifact.
# ---------------------------------------------------------------------------


def test_missing_source_file_raises_explicitly(monkeypatch, tmp_path) -> None:
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    with pytest.raises(calibration.CalibrationReportMissing):
        calibration.payload()


def test_missing_source_file_returns_503_from_route(monkeypatch, tmp_path) -> None:
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 503


def test_invalid_json_returns_503_from_route(monkeypatch, tmp_path) -> None:
    _clear_cache()
    target = tmp_path / "experiments" / "results"
    target.mkdir(parents=True)
    (target / "calibration_report.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 503


def test_json_that_is_not_an_object_returns_503_from_route(monkeypatch, tmp_path) -> None:
    _clear_cache()
    target = tmp_path / "experiments" / "results"
    target.mkdir(parents=True)
    (target / "calibration_report.json").write_text("[1, 2, 3]", encoding="utf-8")
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 503


def test_non_utf8_artifact_returns_503_from_route(monkeypatch, tmp_path) -> None:
    """A corrupt (non-UTF-8) artifact is a malformed artifact, not a 500."""
    _clear_cache()
    target = tmp_path / "experiments" / "results"
    target.mkdir(parents=True)
    (target / "calibration_report.json").write_bytes(b'{"task": "\xff\xfeR2-CAL-01"}')
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 503


def test_unreadable_artifact_returns_503_from_route(monkeypatch) -> None:
    """An artifact present but unreadable fails closed rather than as a 500."""

    def deny(*_args):
        raise PermissionError(13, "Permission denied")

    _clear_cache()
    monkeypatch.setattr(calibration, "_load_cached", deny)
    assert TestClient(app).get("/research/calibration").status_code == 503


# ---------------------------------------------------------------------------
# Route-level fail-closed behaviour: doctored artifacts.
#
# Every case below must reach the public route as 503, never 200 (silently
# serving copy the artifact no longer supports) and never 500 (an unhandled
# structural error escaping the service).
# ---------------------------------------------------------------------------


def _drop(*path: str) -> Callable[[dict], None]:
    def mutate(report: dict) -> None:
        node = report
        for key in path[:-1]:
            node = node[key]
        node.pop(path[-1])

    return mutate


def _set(value: Any, *path: str) -> Callable[[dict], None]:
    def mutate(report: dict) -> None:
        node = report
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value

    return mutate


CONTRADICTORY_OR_MALFORMED_CASES: list[tuple[str, Callable[[dict], None]]] = [
    # --- scientifically contradictory: calibration became estimable ---------
    ("calibration_status_estimable", _set("estimable", "calibration", "status")),
    (
        "informative_about_rank_error_true",
        _set(True, "calibration", "informative_about_rank_error"),
    ),
    ("confidence_unique_values_two", _set(2, "calibration", "confidence_unique_values")),
    ("confidence_values_two_values", _set([0.25, 0.5], "calibration", "confidence_values")),
    ("confidence_values_single_other", _set([0.5], "calibration", "confidence_values")),
    ("confidence_values_empty", _set([], "calibration", "confidence_values")),
    ("confidence_score_not_025", _set(0.5, "confidence_quantity", "confidence_score")),
    ("audited_quantity_changed", _set("something_else", "confidence_quantity", "quantity")),
    # --- scientifically contradictory: monotonicity ------------------------
    ("monotonicity_status_estimable", _set("estimable", "calibration", "monotonicity", "status")),
    (
        "monotonicity_coefficient_present",
        _set(-0.31, "calibration", "monotonicity", "higher_confidence_lower_error_spearman"),
    ),
    (
        "monotonicity_bootstrap_present",
        _set([-0.5, 0.1], "calibration", "monotonicity", "bootstrap_95pct"),
    ),
    (
        "monotonicity_usable_samples_present",
        _set(2000, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    # --- scientifically contradictory: sample / provenance ------------------
    ("sample_outcomes_239", _set(239, "sample", "independent_ticker_year_outcomes")),
    ("sample_outcomes_241", _set(241, "sample", "independent_ticker_year_outcomes")),
    ("replay_sha_mismatch", _set("deadbeef" * 5, "replay_provenance", "git_sha")),
    ("replay_sha_not_a_string", _set(12345, "replay_provenance", "git_sha")),
    # --- wrong task ---------------------------------------------------------
    ("wrong_task", _set("R2-SIG-01", "task")),
    ("task_missing", _drop("task")),
    ("task_not_a_string", _set(["R2-CAL-01"], "task")),
    # --- claim-safety flags the closing sentence depends on -----------------
    ("claim_safety_probability_true", _set(True, "claim_safety", "confidence_is_probability_of_return_profit_or_success")),
    ("claim_safety_recommendation_true", _set(True, "claim_safety", "confidence_is_recommendation_strength")),
    ("claim_safety_reliability_true", _set(True, "claim_safety", "validated_predictive_reliability_established")),
    ("claim_safety_flag_missing", _drop("claim_safety", "confidence_is_recommendation_strength")),
    # --- wrong top-level container types ------------------------------------
    ("calibration_is_a_list", _set([{"status": "not_estimable"}], "calibration")),
    ("calibration_is_a_string", _set("not_estimable", "calibration")),
    ("calibration_is_null", _set(None, "calibration")),
    ("sample_is_a_list", _set([240], "sample")),
    ("claim_safety_is_a_list", _set([], "claim_safety")),
    ("confidence_quantity_is_a_list", _set([], "confidence_quantity")),
    ("replay_provenance_is_a_list", _set([], "replay_provenance")),
    ("limitations_is_an_object", _set({"a": 1}, "limitations")),
    ("limitations_is_empty", _set([], "limitations")),
    # --- malformed nested objects ------------------------------------------
    ("monotonicity_is_a_list", _set([], "calibration", "monotonicity")),
    ("monotonicity_is_a_string", _set("not_estimable", "calibration", "monotonicity")),
    ("monotonicity_is_null", _set(None, "calibration", "monotonicity")),
    ("code_version_is_a_list", _set([], "replay_provenance", "code_version")),
    ("confidence_values_is_a_string", _set("0.25", "calibration", "confidence_values")),
    ("confidence_reasons_is_a_string", _set("small_sample", "confidence_quantity", "confidence_reasons")),
    # --- missing required top-level blocks ----------------------------------
    ("missing_calibration", _drop("calibration")),
    ("missing_claim_safety", _drop("claim_safety")),
    ("missing_confidence_quantity", _drop("confidence_quantity")),
    ("missing_replay_provenance", _drop("replay_provenance")),
    ("missing_sample", _drop("sample")),
    ("missing_limitations", _drop("limitations")),
    ("missing_schema_version", _drop("schema_version")),
    # --- missing required nested fields --------------------------------------
    ("missing_calibration_status", _drop("calibration", "status")),
    ("missing_calibration_verdict", _drop("calibration", "verdict")),
    ("missing_informative_flag", _drop("calibration", "informative_about_rank_error")),
    ("missing_confidence_unique_values", _drop("calibration", "confidence_unique_values")),
    ("missing_confidence_values", _drop("calibration", "confidence_values")),
    ("missing_requested_bins", _drop("calibration", "requested_bins")),
    ("missing_realized_bins", _drop("calibration", "realized_bins")),
    ("missing_monotonicity", _drop("calibration", "monotonicity")),
    ("missing_monotonicity_status", _drop("calibration", "monotonicity", "status")),
    ("missing_monotonicity_reason", _drop("calibration", "monotonicity", "reason")),
    ("missing_monotonicity_spearman", _drop("calibration", "monotonicity", "higher_confidence_lower_error_spearman")),
    ("missing_monotonicity_bootstrap", _drop("calibration", "monotonicity", "bootstrap_95pct")),
    ("missing_monotonicity_seed", _drop("calibration", "monotonicity", "seed")),
    ("missing_sample_outcomes", _drop("sample", "independent_ticker_year_outcomes")),
    ("missing_git_sha", _drop("replay_provenance", "git_sha")),
    ("missing_replay_date", _drop("replay_provenance", "replay_date")),
    ("missing_random_seed", _drop("replay_provenance", "random_seed")),
    ("missing_code_version", _drop("replay_provenance", "code_version")),
    ("missing_confidence_score", _drop("confidence_quantity", "confidence_score")),
    ("missing_confidence_quantity_name", _drop("confidence_quantity", "quantity")),
    ("missing_hybrid_weight", _drop("confidence_quantity", "hybrid_weight")),
    ("missing_service_function", _drop("confidence_quantity", "service_function")),
    # --- wrong scalar types --------------------------------------------------
    ("unique_values_is_a_string", _set("1", "calibration", "confidence_unique_values")),
    ("outcomes_is_a_string", _set("240", "sample", "independent_ticker_year_outcomes")),
    ("informative_flag_is_a_string", _set("false", "calibration", "informative_about_rank_error")),
    ("status_is_a_number", _set(0, "calibration", "status")),
    ("schema_version_is_a_number", _set(1, "schema_version")),
    ("random_seed_is_a_string", _set("42", "replay_provenance", "random_seed")),
    # --- limitations: non-string elements ------------------------------------
    ("limitations_item_is_a_number", _set([1, "text"], "limitations")),
    ("limitations_item_is_a_boolean", _set([True], "limitations")),
    ("limitations_item_is_null", _set([None], "limitations")),
    ("limitations_item_is_a_list", _set([["nested"]], "limitations")),
    ("limitations_item_is_an_object", _set([{"a": 1}], "limitations")),
    # --- confidence_reasons: non-string elements ------------------------------
    ("confidence_reasons_item_is_a_number", _set([1], "confidence_quantity", "confidence_reasons")),
    ("confidence_reasons_item_is_a_boolean", _set([True], "confidence_quantity", "confidence_reasons")),
    ("confidence_reasons_item_is_null", _set([None], "confidence_quantity", "confidence_reasons")),
    ("confidence_reasons_item_is_a_list", _set([[]], "confidence_quantity", "confidence_reasons")),
    ("confidence_reasons_item_is_an_object", _set([{}], "confidence_quantity", "confidence_reasons")),
    # --- sample.target_years: malformed elements and containers --------------
    ("target_years_item_is_a_string", _set(["2023", 2024, 2025], "sample", "target_years")),
    ("target_years_item_is_a_float", _set([2023.5, 2024, 2025], "sample", "target_years")),
    ("target_years_item_is_a_boolean", _set([True, 2024, 2025], "sample", "target_years")),
    ("target_years_item_is_null", _set([None, 2024, 2025], "sample", "target_years")),
    ("target_years_mixed_types", _set([2023, "2024", True], "sample", "target_years")),
    ("target_years_is_empty", _set([], "sample", "target_years")),
    ("target_years_has_duplicates", _set([2023, 2023, 2024], "sample", "target_years")),
    ("target_years_out_of_order", _set([2024, 2023, 2025], "sample", "target_years")),
    ("target_years_invalid_year_too_low", _set([1899, 2024, 2025], "sample", "target_years")),
    ("target_years_invalid_year_too_high", _set([2023, 2024, 2101], "sample", "target_years")),
    ("target_years_invalid_year_negative", _set([-1, 2024, 2025], "sample", "target_years")),
    ("target_years_is_a_string", _set("2023,2024,2025", "sample", "target_years")),
    ("target_years_missing", _drop("sample", "target_years")),
    # --- sample: other nested passthrough fields ------------------------------
    ("sample_models_is_zero", _set(0, "sample", "models")),
    ("sample_models_is_negative", _set(-1, "sample", "models")),
    ("sample_models_is_a_boolean", _set(True, "sample", "models")),
    ("sample_models_is_a_string", _set("9", "sample", "models")),
    ("sample_prediction_model_rows_is_zero", _set(0, "sample", "prediction_model_rows")),
    ("sample_prediction_model_rows_is_a_boolean", _set(True, "sample", "prediction_model_rows")),
    ("sample_rows_per_model_year_is_empty", _set([], "sample", "rows_per_model_year")),
    ("sample_rows_per_model_year_item_negative", _set([-1], "sample", "rows_per_model_year")),
    ("sample_rows_per_model_year_item_zero", _set([0], "sample", "rows_per_model_year")),
    ("sample_rows_per_model_year_item_boolean", _set([True], "sample", "rows_per_model_year")),
    ("sample_rows_per_model_year_item_string", _set(["80"], "sample", "rows_per_model_year")),
    ("sample_universe_is_empty", _set("", "sample", "universe")),
    ("sample_universe_is_a_number", _set(81, "sample", "universe")),
    ("sample_universe_is_null", _set(None, "sample", "universe")),
    # --- replay_provenance.code_version: malformed containers/scalars ---------
    (
        "code_version_value_is_a_number",
        _set({"backend/app/services/research_agent.py": 12345}, "replay_provenance", "code_version"),
    ),
    (
        "code_version_value_is_a_boolean",
        _set({"backend/app/services/research_agent.py": True}, "replay_provenance", "code_version"),
    ),
    (
        "code_version_value_is_null",
        _set({"backend/app/services/research_agent.py": None}, "replay_provenance", "code_version"),
    ),
    (
        "code_version_value_is_empty_string",
        _set({"backend/app/services/research_agent.py": ""}, "replay_provenance", "code_version"),
    ),
    ("code_version_is_empty_object", _set({}, "replay_provenance", "code_version")),
    # --- random_seed: bool-as-int and invalid value ---------------------------
    ("random_seed_is_a_boolean", _set(True, "replay_provenance", "random_seed")),
    ("random_seed_is_negative", _set(-1, "replay_provenance", "random_seed")),
    ("monotonicity_seed_is_a_boolean", _set(True, "calibration", "monotonicity", "seed")),
    ("monotonicity_seed_is_negative", _set(-1, "calibration", "monotonicity", "seed")),
    # --- verdict / reason: altered or unsupported values ----------------------
    ("verdict_is_altered", _set("A different, unsupported verdict.", "calibration", "verdict")),
    ("verdict_is_a_number", _set(0, "calibration", "verdict")),
    ("monotonicity_reason_is_altered", _set("A different, unsupported reason.", "calibration", "monotonicity", "reason")),
    ("monotonicity_reason_is_a_number", _set(0, "calibration", "monotonicity", "reason")),
    # --- bin counts: invalid and internally inconsistent -----------------------
    ("requested_bins_is_negative", _set(-1, "calibration", "requested_bins")),
    ("requested_bins_is_zero", _set(0, "calibration", "requested_bins")),
    ("requested_bins_is_a_float", _set(10.5, "calibration", "requested_bins")),
    ("requested_bins_is_a_boolean", _set(True, "calibration", "requested_bins")),
    ("requested_bins_is_a_string", _set("10", "calibration", "requested_bins")),
    ("requested_bins_is_null", _set(None, "calibration", "requested_bins")),
    ("realized_bins_is_negative", _set(-1, "calibration", "realized_bins")),
    ("realized_bins_is_zero", _set(0, "calibration", "realized_bins")),
    ("realized_bins_is_a_float", _set(1.5, "calibration", "realized_bins")),
    ("realized_bins_is_a_boolean", _set(True, "calibration", "realized_bins")),
    ("realized_bins_is_a_string", _set("1", "calibration", "realized_bins")),
    ("realized_bins_is_null", _set(None, "calibration", "realized_bins")),
    ("realized_bins_exceeds_requested_bins", _set(11, "calibration", "realized_bins")),
    # --- claim_safety: other nested passthrough fields --------------------------
    ("claim_safety_conclusion_altered", _set("a reliable predictive edge", "claim_safety", "contract_conclusion")),
    ("claim_safety_conclusion_is_a_number", _set(0, "claim_safety", "contract_conclusion")),
    ("claim_safety_version_is_empty", _set("", "claim_safety", "contract_version")),
    ("claim_safety_version_is_a_number", _set(130, "claim_safety", "contract_version")),
    ("claim_safety_statement_altered", _set("confidence is recommendation strength", "claim_safety", "statement")),
    ("claim_safety_statement_is_a_number", _set(0, "claim_safety", "statement")),
    (
        "claim_safety_core_ranking_changed_true",
        _set(True, "claim_safety", "core_ranking_or_model_computation_changed"),
    ),
    (
        "claim_safety_core_ranking_changed_is_a_string",
        _set("false", "claim_safety", "core_ranking_or_model_computation_changed"),
    ),
    # --- BLOCKER A: whole-block passthrough / injected keys -------------------
    (
        "claim_safety_confidence_establishes_predictive_skill_true",
        _set(True, "claim_safety", "confidence_establishes_predictive_skill"),
    ),
    (
        "claim_safety_note_injected",
        _set("Confidence is a probability of return.", "claim_safety", "note"),
    ),
    ("claim_safety_unknown_scalar_key", _set("x", "claim_safety", "extra_scalar")),
    ("claim_safety_unknown_list_key", _set([1, 2, 3], "claim_safety", "extra_list")),
    ("claim_safety_unknown_nested_object_key", _set({"a": 1}, "claim_safety", "extra_object")),
    ("sample_unknown_scalar_key", _set("x", "sample", "extra_scalar")),
    ("sample_unknown_list_key", _set([1, 2], "sample", "extra_list")),
    ("sample_unknown_nested_object_key", _set({"a": 1}, "sample", "extra_object")),
    ("calibration_unknown_key", _set("x", "calibration", "extra_field")),
    ("monotonicity_unknown_key", _set("x", "calibration", "monotonicity", "extra_field")),
    ("confidence_quantity_unknown_key", _set("x", "confidence_quantity", "extra_field")),
    ("replay_provenance_unknown_key", _set("x", "replay_provenance", "extra_field")),
    (
        "code_version_unknown_key",
        _set("deadbeef", "replay_provenance", "code_version", "unexpected/file.py"),
    ),
    # --- BLOCKER B: non-finite numbers -----------------------------------------
    ("hybrid_weight_is_nan", _set(float("nan"), "confidence_quantity", "hybrid_weight")),
    (
        "hybrid_weight_is_positive_infinity",
        _set(float("inf"), "confidence_quantity", "hybrid_weight"),
    ),
    (
        "hybrid_weight_is_negative_infinity",
        _set(float("-inf"), "confidence_quantity", "hybrid_weight"),
    ),
    ("hybrid_weight_exceeds_valid_range", _set(1.5, "confidence_quantity", "hybrid_weight")),
    ("hybrid_weight_is_negative", _set(-0.1, "confidence_quantity", "hybrid_weight")),
    ("confidence_score_is_nan", _set(float("nan"), "confidence_quantity", "confidence_score")),
    (
        "confidence_score_is_positive_infinity",
        _set(float("inf"), "confidence_quantity", "confidence_score"),
    ),
    # --- BLOCKER C: bootstrap request/usable count -----------------------------
    (
        "bootstrap_samples_requested_is_zero",
        _set(0, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_negative",
        _set(-100, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_a_boolean",
        _set(True, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_a_float",
        _set(2000.5, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_a_string",
        _set("2000", "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_null",
        _set(None, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_a_list",
        _set([2000], "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_requested_is_an_object",
        _set({}, "calibration", "monotonicity", "bootstrap_samples_requested"),
    ),
    (
        "bootstrap_samples_usable_is_negative",
        _set(-1, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    (
        "bootstrap_samples_usable_is_a_boolean",
        _set(True, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    (
        "bootstrap_samples_usable_is_a_string",
        _set("0", "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    (
        "bootstrap_samples_usable_is_a_float",
        _set(0.5, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    (
        "bootstrap_samples_usable_is_null",
        _set(None, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    (
        "bootstrap_samples_usable_exceeds_requested",
        _set(2001, "calibration", "monotonicity", "bootstrap_samples_usable"),
    ),
    # --- additional hardening: duplicates and empty mandatory strings ---------
    ("limitations_has_duplicates", _set(["Same text.", "Same text."], "limitations")),
    (
        "confidence_reasons_has_duplicates",
        _set(["small_sample (-0.25)", "small_sample (-0.25)"], "confidence_quantity", "confidence_reasons"),
    ),
    ("confidence_quantity_scope_is_empty", _set("", "confidence_quantity", "scope")),
    ("confidence_quantity_level_is_empty", _set("", "confidence_quantity", "confidence_level")),
    (
        "confidence_quantity_service_function_is_empty",
        _set("", "confidence_quantity", "service_function"),
    ),
    (
        "confidence_quantity_consumer_function_is_empty",
        _set("", "confidence_quantity", "consumer_function"),
    ),
    ("replay_provenance_replay_date_is_empty", _set("", "replay_provenance", "replay_date")),
    ("report_schema_version_is_empty", _set("", "schema_version")),
]


@pytest.mark.parametrize(
    "case,mutate",
    CONTRADICTORY_OR_MALFORMED_CASES,
    ids=[case for case, _ in CONTRADICTORY_OR_MALFORMED_CASES],
)
def test_contradictory_or_malformed_artifact_returns_503_from_route(
    monkeypatch, case: str, mutate: Callable[[dict], None]
) -> None:
    doctored = copy.deepcopy(_load())
    mutate(doctored)
    assert _route_status(monkeypatch, doctored) == 503, case


@pytest.mark.parametrize(
    "case,mutate",
    CONTRADICTORY_OR_MALFORMED_CASES,
    ids=[case for case, _ in CONTRADICTORY_OR_MALFORMED_CASES],
)
def test_contradictory_or_malformed_artifact_raises_the_report_exception(
    monkeypatch, case: str, mutate: Callable[[dict], None]
) -> None:
    doctored = copy.deepcopy(_load())
    mutate(doctored)
    _clear_cache()
    monkeypatch.setattr(calibration, "_load_cached", lambda *_args: doctored)
    with pytest.raises(calibration.CalibrationReportMissing):
        calibration.payload()


def test_top_level_non_object_artifacts_return_503_from_route(monkeypatch) -> None:
    for doctored in ([], "R2-CAL-01", 42, None):
        assert _route_status(monkeypatch, doctored) == 503, repr(doctored)


def test_unrelated_programming_errors_are_not_disguised_as_a_missing_report(monkeypatch) -> None:
    """No indiscriminate broad catch: only artifact faults become 503."""

    def explode(*_args):
        raise ZeroDivisionError("unrelated application bug")

    _clear_cache()
    monkeypatch.setattr(calibration, "_load_cached", explode)
    with pytest.raises(ZeroDivisionError):
        calibration.payload()


def test_unmutated_deep_copy_still_serves_200_through_the_route(monkeypatch) -> None:
    """Control: the adversarial harness itself does not cause the 503s above."""
    assert _route_status(monkeypatch, copy.deepcopy(_load())) == 200


# ---------------------------------------------------------------------------
# BLOCKER A: the valid response must contain exactly the intended filtered
# key sets -- reconstruction must neither drop a required key nor leak one.
# ---------------------------------------------------------------------------


def test_valid_response_key_sets_are_exactly_the_intended_filtered_sets() -> None:
    body = _body()
    assert set(body) == {
        "task",
        "schema_version",
        "source_task",
        "report_schema_version",
        "panel_copy",
        "calibration",
        "confidence_quantity",
        "claim_safety",
        "sample",
        "replay_provenance",
        "limitations",
        "source_artifact",
    }
    assert set(body["calibration"]) == {
        "status",
        "verdict",
        "informative_about_rank_error",
        "confidence_unique_values",
        "confidence_values",
        "requested_bins",
        "realized_bins",
        "monotonicity",
    }
    assert set(body["calibration"]["monotonicity"]) == {
        "status",
        "reason",
        "higher_confidence_lower_error_spearman",
        "bootstrap_95pct",
        "bootstrap_samples_requested",
        "bootstrap_samples_usable",
        "seed",
    }
    assert set(body["confidence_quantity"]) == {
        "quantity",
        "scope",
        "confidence_level",
        "confidence_reasons",
        "confidence_score",
        "hybrid_weight",
        "service_function",
        "consumer_function",
    }
    assert set(body["claim_safety"]) == {
        "confidence_is_probability_of_return_profit_or_success",
        "confidence_is_recommendation_strength",
        "contract_conclusion",
        "contract_version",
        "core_ranking_or_model_computation_changed",
        "statement",
        "validated_predictive_reliability_established",
    }
    assert set(body["sample"]) == {
        "independent_ticker_year_outcomes",
        "models",
        "prediction_model_rows",
        "rows_per_model_year",
        "target_years",
        "universe",
    }
    assert set(body["replay_provenance"]) == {
        "git_sha",
        "git_worktree_dirty",
        "replay_date",
        "random_seed",
        "code_version",
    }
    assert set(body["replay_provenance"]["code_version"]) == {
        "backend/app/services/forecasting_csv_service.py",
        "backend/app/services/research_agent.py",
    }


def test_returned_lists_are_not_live_references_into_the_cached_artifact() -> None:
    """Two calls sharing the same `lru_cache`d parse must not share mutable state,
    and mutating one served payload must never corrupt a later one."""
    _clear_cache()
    first = calibration.payload()
    second = calibration.payload()
    assert first["limitations"] is not second["limitations"]
    assert first["sample"]["target_years"] is not second["sample"]["target_years"]
    assert (
        first["confidence_quantity"]["confidence_reasons"]
        is not second["confidence_quantity"]["confidence_reasons"]
    )

    first["limitations"].append("mutated")
    first["sample"]["target_years"].append(9999)
    first["confidence_quantity"]["confidence_reasons"].append("mutated")

    third = calibration.payload()
    assert "mutated" not in third["limitations"]
    assert 9999 not in third["sample"]["target_years"]
    assert "mutated" not in third["confidence_quantity"]["confidence_reasons"]


# ---------------------------------------------------------------------------
# BLOCKER B: real on-disk NaN / Infinity / -Infinity artifacts.
#
# `json.dumps` (unlike the JSON spec) serializes `float("nan")`/`float("inf")`/
# `float("-inf")` as the bare tokens `NaN`/`Infinity`/`-Infinity` by default, so
# this reproduces exactly what a corrupted or hand-edited on-disk artifact
# would contain -- not just a mutated in-memory dict.
# ---------------------------------------------------------------------------


def _write_report(tmp_path: Path, report: dict) -> None:
    target = tmp_path / "experiments" / "results"
    target.mkdir(parents=True, exist_ok=True)
    (target / "calibration_report.json").write_text(json.dumps(report), encoding="utf-8")


@pytest.mark.parametrize(
    "case,value",
    [
        ("hybrid_weight_nan", float("nan")),
        ("hybrid_weight_infinity", float("inf")),
        ("hybrid_weight_negative_infinity", float("-inf")),
    ],
    ids=["hybrid_weight_nan", "hybrid_weight_infinity", "hybrid_weight_negative_infinity"],
)
def test_on_disk_non_finite_hybrid_weight_returns_503(
    monkeypatch, tmp_path, case: str, value: float
) -> None:
    doctored = copy.deepcopy(_load())
    doctored["confidence_quantity"]["hybrid_weight"] = value
    _write_report(tmp_path, doctored)
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    assert TestClient(app).get("/research/calibration").status_code == 503, case


@pytest.mark.parametrize(
    "case,value",
    [
        ("confidence_score_nan", float("nan")),
        ("confidence_score_infinity", float("inf")),
        ("confidence_score_negative_infinity", float("-inf")),
    ],
    ids=["confidence_score_nan", "confidence_score_infinity", "confidence_score_negative_infinity"],
)
def test_on_disk_non_finite_additional_numeric_field_returns_503(
    monkeypatch, tmp_path, case: str, value: float
) -> None:
    """A second returned numeric field (`confidence_score`), not just `hybrid_weight`."""
    doctored = copy.deepcopy(_load())
    doctored["confidence_quantity"]["confidence_score"] = value
    _write_report(tmp_path, doctored)
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    assert TestClient(app).get("/research/calibration").status_code == 503, case


def test_on_disk_valid_finite_artifact_still_returns_200(monkeypatch, tmp_path) -> None:
    """Control: writing the unmodified committed artifact to disk still serves 200."""
    _write_report(tmp_path, _load())
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    response = TestClient(app).get("/research/calibration")
    assert response.status_code == 200
    assert response.json()["confidence_quantity"]["hybrid_weight"] == 0.2


def test_on_disk_bare_nan_token_in_json_text_returns_503(monkeypatch, tmp_path) -> None:
    """A hand-corrupted artifact spelling a bare `NaN` token, not produced via `json.dumps`."""
    doctored = copy.deepcopy(_load())
    text = json.dumps(doctored).replace('"hybrid_weight": 0.2', '"hybrid_weight": NaN')
    target = tmp_path / "experiments" / "results"
    target.mkdir(parents=True)
    (target / "calibration_report.json").write_text(text, encoding="utf-8")
    _clear_cache()
    monkeypatch.setattr(calibration, "resolve_repo_root", lambda: tmp_path)
    assert TestClient(app).get("/research/calibration").status_code == 503
