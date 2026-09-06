"""Behavioral tests for the completed Stage 3 apparatus.

These tests exercise private/in-memory constructions and private temporary
guard inputs.  They deliberately do not call ``run()``, ``replay_check()``, a
Stage 3 Makefile target, or any governed result writer.  The completed
attempt-1 result namespace is treated as immutable post-run evidence.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from experiments.thesis import defect_injection as stage3
from experiments.thesis import stage3_registration as reg

canonical = stage3.canonical
STAGE3_RESULT_FILENAMES = (*stage3.SCIENTIFIC_EMITTED_FILENAMES, stage3.MANIFEST_FILENAME)


def _assert_completed_result_namespace() -> None:
    result_root = stage3.RESULT_ROOT
    assert result_root.is_dir()
    assert {
        path.name for path in result_root.iterdir() if path.is_file()
    } == set(STAGE3_RESULT_FILENAMES)
    attempts = result_root / stage3.ATTEMPTS_DIRNAME
    assert attempts.is_dir()
    assert sorted(path.name for path in attempts.glob("attempt-*.json")) == [
        "attempt-1.json"
    ]
    assert not (result_root / stage3.STAGING_DIRNAME).exists()

    manifest = json.loads(
        (result_root / stage3.MANIFEST_FILENAME).read_text(encoding="utf-8")
    )
    assert manifest["completion_status"] == "complete"
    assert manifest["completion_authority"] == stage3.MANIFEST_FILENAME
    assert manifest["decision"] == reg.INCONCLUSIVE
    assert manifest["integrity_passed"] is False

    attempt = json.loads(
        (attempts / "attempt-1.json").read_text(encoding="utf-8")
    )
    assert attempt["attempt_number"] == 1
    assert attempt["attempt_type"] == "initial"
    assert attempt["status"] == "complete"
    assert attempt["prior_incomplete_attempt"] is False


@pytest.fixture(scope="module")
def clean_frame() -> pd.DataFrame:
    return stage3.load_clean_frame()


def test_registered_configuration_and_plan_are_exact_and_inert():
    configuration = stage3.registered_configuration()
    assert configuration["defect_family"] == list(reg.DEFECT_FAMILY)
    assert configuration["defect_ids"] == dict(reg.DEFECT_IDS)
    assert configuration["registered_guard_contract"]
    assert configuration["secondary_metric"]["model"] == "ridge"
    assert configuration["secondary_metric"]["parameters"] == {"alpha": 1.0}
    plan = stage3.registered_plan()
    assert plan["executed"] is False
    assert plan["scientific_draw_performed"] is False
    assert plan["result_root_created"] is True
    _assert_completed_result_namespace()


@pytest.mark.parametrize("defect_name", reg.DEFECT_FAMILY)
def test_each_injection_has_the_frozen_behavioral_invariants(clean_frame, defect_name):
    injected = stage3.inject_defect(clean_frame, defect_name)
    repeated = stage3.inject_defect(clean_frame, defect_name)
    invariant_result = stage3.assert_mechanism_invariants(
        defect_name, clean_frame, injected
    )

    assert invariant_result["passed"] is True
    assert stage3._frame_equal(injected, repeated)
    assert stage3._frame_equal(clean_frame, stage3.load_clean_frame())


def test_injection_counts_and_4001_stale_collateral_are_exact(clean_frame):
    future = stage3.inject_defect(clean_frame, "FUTURE_YEAR_FEATURE_LEAKAGE")
    future_checks = stage3.mechanism_invariants(
        "FUTURE_YEAR_FEATURE_LEAKAGE", clean_frame, future
    )["checks"]
    assert future_checks["rows_receiving_future_value"] is True
    assert future_checks["rows_changed"] is True

    misaligned = stage3.inject_defect(clean_frame, "T_TPLUS1_MISALIGNMENT")
    assert stage3._changed_count(
        clean_frame[reg.PRIMARY_TARGET_COLUMN], misaligned[reg.PRIMARY_TARGET_COLUMN]
    ) == 320
    assert stage3._series_values_equal(
        clean_frame[reg.PRIMARY_TARGET_COLUMN].isna(),
        misaligned[reg.PRIMARY_TARGET_COLUMN].isna(),
    )
    for column in reg.STALE_DERIVED_TARGET_COLUMNS:
        assert stage3._series_values_equal(clean_frame[column], misaligned[column])


def test_4002_and_4003_and_4004_constructions_are_exact(clean_frame):
    leaked = stage3.inject_defect(clean_frame, "TARGET_LEAKAGE_INTO_FEATURES")
    assert list(leaked.columns) == [*clean_frame.columns, "leaked_next_year_return_pct"]
    assert stage3._series_values_equal(
        leaked["leaked_next_year_return_pct"], leaked[reg.PRIMARY_TARGET_COLUMN]
    )
    assert stage3.mechanism_invariants(
        "TARGET_LEAKAGE_INTO_FEATURES", clean_frame, leaked
    )["passed"] is True

    lookahead = stage3.inject_defect(clean_frame, "LOOKAHEAD_UNIVERSE_MEMBERSHIP")
    assert len(lookahead) == 243
    assert len(clean_frame) - len(lookahead) == 160
    assert set(lookahead["universe_source"]) == {"lookahead_survivor"}
    assert stage3.mechanism_invariants(
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP", clean_frame, lookahead
    )["passed"] is True

    duplicated = stage3.inject_defect(clean_frame, "DUPLICATE_ROW_INFLATION")
    assert duplicated.shape == (443, 61)
    assert int(duplicated.duplicated(list(reg.KEY_COLUMNS)).sum()) == 40
    assert stage3.mechanism_invariants(
        "DUPLICATE_ROW_INFLATION", clean_frame, duplicated
    )["passed"] is True


@pytest.mark.parametrize("defect_name", reg.DEFECT_FAMILY)
def test_clean_comparator_has_no_signal_and_private_cleanup_is_proven(
    clean_frame, defect_name
):
    evaluation = stage3.evaluate_guard_surfaces(
        clean_frame, defect_name, comparator="clean"
    )
    assert evaluation["detection_signals"] == []
    assert evaluation["containment_failures"] == []
    assert evaluation["containment_passed"] is True
    assert evaluation["cleanup_proven"] is True
    assert evaluation["invocation_accounting_passed"] is True


def test_4002_reaches_private_provenance_column_coverage(clean_frame):
    injected = stage3.inject_defect(clean_frame, "TARGET_LEAKAGE_INTO_FEATURES")
    evaluation = stage3.evaluate_guard_surfaces(injected, "TARGET_LEAKAGE_INTO_FEATURES")
    detected = {signal["surface"] for signal in evaluation["detection_signals"]}
    assert detected == {"GS_CELL_PROVENANCE_COLUMN_COVERAGE"}
    assert evaluation["containment_passed"] is True
    assert evaluation["cleanup_proven"] is True
    assert evaluation["invocation_accounting_passed"] is True
    coverage = next(
        result
        for result in evaluation["surface_results"]
        if result["surface"] == "GS_CELL_PROVENANCE_COLUMN_COVERAGE"
    )
    assert "passports v1 does not cover exactly the dataset columns" in coverage["signal"]
    assert "columns absent from the frozen resolution table" in coverage["signal"]
    duplicate = next(
        result
        for result in evaluation["surface_results"]
        if result["surface"] == "GS_CELL_PROVENANCE_DUP_KEY"
    )
    assert duplicate["status"] == "NO_SIGNAL"
    assert duplicate["invocation_count"] == 1


def test_4004_keeps_existing_duplicate_guards_and_fail_fast_boundary(clean_frame):
    injected = stage3.inject_defect(clean_frame, "DUPLICATE_ROW_INFLATION")
    evaluation = stage3.evaluate_guard_surfaces(injected, "DUPLICATE_ROW_INFLATION")
    detected = {signal["surface"] for signal in evaluation["detection_signals"]}
    assert detected == {
        "GS_DUP_ALT_TARGETS",
        "GS_DUP_VALIDATE_ISSUE",
        "GS_CELL_PROVENANCE_DUP_KEY",
    }
    assert "GS_ALIGNMENT_ALT_TARGETS" not in evaluation["evaluated_surfaces"]
    assert evaluation["containment_passed"] is True
    assert evaluation["cleanup_proven"] is True
    assert evaluation["invocation_accounting_passed"] is True


def test_private_evaluation_does_not_mutate_canonical_data_or_redirected_attributes(
    clean_frame,
):
    before = stage3.protected_workspace_digest()
    source_before = stage3._sha256_path(stage3.DATASET_PATH)
    module_attributes = (
        stage3.pipeline.QUALITY_JSON,
        stage3.pipeline.QUALITY_MD,
        stage3.validator.FEATURE_JSON,
        stage3.validator.FEATURE_MD,
    )
    for defect_name in reg.DEFECT_FAMILY:
        stage3.evaluate_guard_surfaces(
            stage3.inject_defect(clean_frame, defect_name), defect_name
        )
    assert stage3.protected_workspace_digest() == before
    assert stage3._sha256_path(stage3.DATASET_PATH) == source_before == reg.DATASET_SHA256
    assert module_attributes == (
        stage3.pipeline.QUALITY_JSON,
        stage3.pipeline.QUALITY_MD,
        stage3.validator.FEATURE_JSON,
        stage3.validator.FEATURE_MD,
    )
    _assert_completed_result_namespace()


def test_containment_failure_is_inconclusive_and_restores_validator_state(
    clean_frame, monkeypatch
):
    original_attributes = (
        stage3.pipeline.QUALITY_JSON,
        stage3.pipeline.QUALITY_MD,
        stage3.validator.FEATURE_JSON,
        stage3.validator.FEATURE_MD,
    )

    def fail_validation(*args, **kwargs):
        raise RuntimeError("synthetic private validator failure")

    monkeypatch.setattr(stage3.validator, "validate", fail_validation)
    injected = stage3.inject_defect(clean_frame, "FUTURE_YEAR_FEATURE_LEAKAGE")
    result = stage3.evaluate_defect(
        "FUTURE_YEAR_FEATURE_LEAKAGE", clean_frame, injected
    )
    assert result["status"] == reg.INCONCLUSIVE
    assert result["containment_passed"] is False
    assert result["secondary_ic"] is None
    assert original_attributes == (
        stage3.pipeline.QUALITY_JSON,
        stage3.pipeline.QUALITY_MD,
        stage3.validator.FEATURE_JSON,
        stage3.validator.FEATURE_MD,
    )


def test_4001_secondary_metric_isolated_from_stale_targets_and_exactly_canonical(
    clean_frame,
):
    injected = stage3.inject_defect(clean_frame, "T_TPLUS1_MISALIGNMENT")
    original_training_path = canonical.TRAINING_MODELING
    secondary = stage3.compute_secondary_ic(clean_frame, injected)

    assert secondary["model"] == "ridge"
    assert secondary["alpha"] == 1.0
    assert secondary["target"] == reg.SECONDARY_METRIC_TARGET
    assert secondary["rank_method"] == "average"
    assert secondary["rank_percentile"] is True
    assert secondary["imputation"] == "NaN -> 0.5"
    assert secondary["pooled"] is False
    assert secondary["threshold"] is None
    assert secondary["significance_test"] is False
    assert secondary["gating"] is False
    assert [row["name"] for row in secondary["splits"]] == [
        split["name"] for split in reg.SECONDARY_METRIC_SPLITS
    ]
    assert len(secondary["splits"]) == 3
    assert secondary["stale_derived_target_columns_consumed"] == []
    assert all(
        not column.startswith("next_year_")
        for column in secondary["feature_columns"]
    )
    for row in secondary["splits"]:
        assert row["delta_ic"] == pytest.approx(
            row["injected_ic"] - row["clean_ic"]
        )
    assert canonical.TRAINING_MODELING == original_training_path


def test_4001_stale_derived_target_consumer_violation_is_inconclusive(
    clean_frame, monkeypatch
):
    original_selector = canonical._feature_cols

    def stale_selector(frame):
        return [*original_selector(frame), reg.STALE_DERIVED_TARGET_COLUMNS[0]]

    monkeypatch.setattr(canonical, "_feature_cols", stale_selector)
    injected = stage3.inject_defect(clean_frame, "T_TPLUS1_MISALIGNMENT")
    with pytest.raises(stage3.Stage3ConsumerBoundaryError):
        stage3.compute_secondary_ic(clean_frame, injected)


@pytest.mark.parametrize(
    ("statuses", "integrity_passed", "expected"),
    [
        ([reg.DETECTED] * 5, True, stage3.PASS),
        ([reg.DETECTED, reg.DETECTED, reg.NOT_DETECTED, reg.DETECTED, reg.DETECTED], True, stage3.FAIL),
        ([reg.DETECTED, reg.INCONCLUSIVE, reg.DETECTED, reg.DETECTED, reg.DETECTED], True, reg.INCONCLUSIVE),
        ([reg.DETECTED] * 5, False, reg.INCONCLUSIVE),
        ([reg.DETECTED] * 4, True, reg.INCONCLUSIVE),
    ],
)
def test_pass_fail_inconclusive_precedence(statuses, integrity_passed, expected):
    results = [{"status": status} for status in statuses]
    assert stage3.decide(results, integrity_passed=integrity_passed) == expected


@pytest.mark.parametrize(
    "defect_name",
    ("TARGET_LEAKAGE_INTO_FEATURES", "DUPLICATE_ROW_INFLATION"),
)
def test_secondary_metric_is_not_run_for_detected_defects(
    clean_frame, defect_name, monkeypatch
):
    def should_not_run(*args, **kwargs):
        raise AssertionError("secondary IC must not run for a detected defect")

    monkeypatch.setattr(stage3, "compute_secondary_ic", should_not_run)
    result = stage3.evaluate_defect(
        defect_name, clean_frame, stage3.inject_defect(clean_frame, defect_name)
    )
    assert result["status"] == reg.DETECTED
    assert result["secondary_ic"] is None
    assert result["secondary_ic_computed"] is False


def test_output_schema_is_explicit_without_writing_to_governed_result(tmp_path):
    matrix = {
        "defects": [],
        "decision": reg.INCONCLUSIVE,
        "integrity": {"passed": False, "conditions": {}, "failures": ["test"]},
    }
    report = stage3.build_report(matrix)
    assert {
        "schema_version",
        "experiment",
        "stage",
        "registration",
        "result_root",
        "source_artifacts",
        "registered_configuration",
        "registered_configuration_sha256",
        "expected_first_draw_outcome",
        "expected_first_draw_outcome_is_prospective",
        "defects",
        "decision",
        "integrity",
        "claim_boundary",
        "git",
        "python",
        "governed_scientific_draw_performed",
        "guard_repaired",
    } <= set(report)
    assert report["expected_first_draw_outcome_is_prospective"] is True
    assert report["governed_scientific_draw_performed"] is True
    markdown = stage3.render_markdown(report)
    assert "not investment advice" in markdown.lower()

    csv_path = tmp_path / stage3.RESULTS_CSV_FILENAME
    fake_result = {
        "defect_id": 4002,
        "defect_name": "TARGET_LEAKAGE_INTO_FEATURES",
        "status": reg.DETECTED,
        "expected_result": reg.DETECTED,
        "expected_guard": "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
        "detected_by": ["GS_CELL_PROVENANCE_COLUMN_COVERAGE"],
        "secondary_ic_computed": False,
        "containment_passed": True,
        "mechanism_invariants": {"passed": True},
    }
    stage3._write_defect_results_csv(csv_path, [fake_result])
    assert set(pd.read_csv(csv_path).columns) == {
        "defect_id",
        "defect_name",
        "status",
        "expected_result",
        "expected_guard",
        "detected_by",
        "secondary_ic_applicable",
        "secondary_ic_computed",
        "containment_passed",
        "mechanism_invariants_passed",
    }
    _assert_completed_result_namespace()


def test_crash_recovery_only_cleans_known_private_namespace(tmp_path, monkeypatch):
    result_root = tmp_path / "defect_injection"
    monkeypatch.setattr(stage3, "RESULT_ROOT", result_root)
    root, marker, record, number = stage3._prepare_attempt(repeat_after_crash=False)
    assert root == result_root
    assert number == 1
    assert marker == result_root / "attempts" / "attempt-1.json"
    assert record["status"] == "in_progress"

    staging = result_root / stage3.STAGING_DIRNAME / "attempt-1"
    staging.mkdir(parents=True)
    (staging / "partial.json").write_text("partial\n", encoding="utf-8")
    (result_root / stage3.REPORT_JSON_FILENAME).write_text("{}\n", encoding="utf-8")
    stage3._set_attempt_status(marker, record, "incomplete")

    recovered_root, recovered_marker, recovered, recovered_number = (
        stage3._prepare_attempt(repeat_after_crash=True)
    )
    assert recovered_root == result_root
    assert recovered_number == 2
    assert recovered_marker == result_root / "attempts" / "attempt-2.json"
    assert recovered["attempt_type"] == "crash_recovery"
    assert recovered["prior_incomplete_attempt"] is True
    assert not staging.exists()
    assert not (result_root / stage3.REPORT_JSON_FILENAME).exists()
    assert (result_root / "attempts" / "attempt-1.json").is_file()
    assert (result_root / "attempts" / "attempt-2.json").is_file()


def test_completed_result_root_remains_unchanged_after_ordinary_implementation_tests():
    _assert_completed_result_namespace()


# --------------------------------------------------------------------------- #
# Recovery repair: completion/durability is separate from the integrity verdict
# --------------------------------------------------------------------------- #
def _hash_tree(root: Path) -> dict[str, str]:
    digests: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            digests[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return digests


@pytest.fixture
def complete_but_inconclusive_root(tmp_path, monkeypatch) -> Path:
    """A byte-for-byte copy of the frozen complete-but-INCONCLUSIVE attempt-1."""
    destination = tmp_path / "defect_injection"
    shutil.copytree(stage3.REGISTERED_RESULT_ROOT, destination)
    manifest = json.loads((destination / stage3.MANIFEST_FILENAME).read_text("utf-8"))
    assert manifest["completion_status"] == "complete"
    assert manifest["integrity_passed"] is False
    assert manifest["decision"] == reg.INCONCLUSIVE
    monkeypatch.setattr(stage3, "RESULT_ROOT", destination)
    return destination


def test_complete_but_inconclusive_run_is_classified_complete(complete_but_inconclusive_root):
    root = complete_but_inconclusive_root
    assert stage3._is_complete_run(root) is True
    assert stage3._durably_complete_attempt_exists(root) is True


def test_repeat_after_crash_refuses_a_complete_but_inconclusive_run_byte_for_byte(
    complete_but_inconclusive_root,
):
    root = complete_but_inconclusive_root
    before = _hash_tree(root)
    with pytest.raises(stage3.Stage3Error):
        stage3._prepare_attempt(repeat_after_crash=True)
    assert _hash_tree(root) == before
    for name in stage3.SCIENTIFIC_EMITTED_FILENAMES:
        assert (root / name).is_file()


def test_cleanup_primitive_refuses_when_a_complete_attempt_exists(
    complete_but_inconclusive_root,
):
    root = complete_but_inconclusive_root
    before = _hash_tree(root)
    with pytest.raises(stage3.Stage3Error, match="complete attempt record"):
        stage3._cleanup_incomplete_root(root)
    assert _hash_tree(root) == before


def test_normal_run_against_a_complete_root_does_not_steer_to_repeat_after_crash(
    complete_but_inconclusive_root,
):
    with pytest.raises(stage3.Stage3Error) as excinfo:
        stage3._prepare_attempt(repeat_after_crash=False)
    message = str(excinfo.value)
    assert "complete Stage 3 run already exists" in message
    assert "overwrite is refused" in message
    assert "repeat-after-crash" not in message


def test_incomplete_root_recovery_still_works_and_survives_the_repair(tmp_path, monkeypatch):
    root = tmp_path / "defect_injection"
    monkeypatch.setattr(stage3, "RESULT_ROOT", root)
    stage3._prepare_attempt(repeat_after_crash=False)
    marker = root / stage3.ATTEMPTS_DIRNAME / "attempt-1.json"
    record = json.loads(marker.read_text("utf-8"))
    (root / stage3.REPORT_JSON_FILENAME).write_text("{}\n", encoding="utf-8")
    stage3._set_attempt_status(marker, record, "incomplete")

    recovered_root, _, recovered, number = stage3._prepare_attempt(repeat_after_crash=True)
    assert recovered_root == root
    assert number == 2
    assert recovered["attempt_type"] == "crash_recovery"
    assert not (root / stage3.REPORT_JSON_FILENAME).exists()


# --------------------------------------------------------------------------- #
# Forward clean-fingerprint predicate + per-defect fingerprint persistence
# --------------------------------------------------------------------------- #
def _integrity_conditions_for(fingerprints, *, clean_signals=None):
    clean_signals = clean_signals or [[] for _ in reg.DEFECT_FAMILY]
    results = [
        {
            "defect_id": 4000 + index,
            "defect_name": name,
            "status": reg.NOT_DETECTED,
            "secondary_ic": None,
            "failure_reasons": [],
            "containment_passed": True,
            "clean_comparator": {
                "detection_signals": clean_signals[index],
                "cleanup_proven": True,
                "invocation_accounting_passed": True,
            },
            "injected_guard_evaluation": {
                "cleanup_proven": True,
                "invocation_accounting_passed": True,
            },
        }
        for index, name in enumerate(reg.DEFECT_FAMILY)
    ]
    return stage3._integrity_result(
        before_protected={},
        after_protected={},
        before_modules={},
        after_modules={},
        results=results,
        source_hashes=[reg.DATASET_SHA256],
        clean_fingerprints=fingerprints,
    )


def test_forward_fingerprint_predicate_can_pass_for_five_identical_fingerprints():
    result = _integrity_conditions_for(["fp"] * reg.DEFECT_FAMILY_SIZE)
    assert result["conditions"]["clean_comparator_byte_and_logical_identity"] is True
    assert result["clean_fingerprints"] == ["fp"] * reg.DEFECT_FAMILY_SIZE


def test_forward_fingerprint_predicate_fails_for_differing_fingerprints():
    differing = ["fp", "fp", "other", "fp", "fp"]
    result = _integrity_conditions_for(differing)
    assert result["conditions"]["clean_comparator_byte_and_logical_identity"] is False


def test_forward_fingerprint_predicate_fails_on_wrong_cardinality_or_clean_signal():
    assert (
        _integrity_conditions_for(["fp"])["conditions"][
            "clean_comparator_byte_and_logical_identity"
        ]
        is False
    )
    signals = [[], [], [{"surface": "GS_X"}], [], []]
    assert (
        _integrity_conditions_for(["fp"] * 5, clean_signals=signals)["conditions"][
            "clean_comparator_byte_and_logical_identity"
        ]
        is False
    )


def test_per_defect_clean_fingerprint_is_persisted_in_matrix_accounting(clean_frame, monkeypatch):
    """execute_registered_matrix attaches each per-defect clean fingerprint.

    Guard evaluation is stubbed so this stays a private in-memory accounting
    check and never touches a governed result root.
    """
    monkeypatch.setattr(
        stage3,
        "evaluate_defect",
        lambda name, clean, injected: {
            "defect_id": int(reg.DEFECT_IDS[name]),
            "defect_name": name,
            "status": reg.NOT_DETECTED,
            "detected_by": [],
            "clean_comparator": {
                "detection_signals": [],
                "cleanup_proven": True,
                "containment_passed": True,
                "invocation_accounting_passed": True,
            },
            "injected_guard_evaluation": {
                "detection_signals": [],
                "cleanup_proven": True,
                "containment_passed": True,
                "invocation_accounting_passed": True,
            },
            "mechanism_invariants": {"passed": True, "checks": {"source_shape_clean": True}},
            "secondary_ic": None,
            "secondary_ic_computed": False,
            "containment_passed": True,
            "failure_reasons": [],
        },
    )
    matrix = stage3.execute_registered_matrix(progress=False)
    fingerprints = [record["clean_fingerprint"] for record in matrix["defects"]]
    assert len(fingerprints) == reg.DEFECT_FAMILY_SIZE
    assert len(set(fingerprints)) == 1
    assert matrix["integrity"]["clean_fingerprints"] == fingerprints
    assert not stage3.RESULT_ROOT.exists() or stage3.RESULT_ROOT.is_dir()
    _assert_completed_result_namespace()
