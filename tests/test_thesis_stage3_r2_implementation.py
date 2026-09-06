"""Behavioral guards for the read-only Stage 3 R2 accounting-only adjudicator.

These tests never invoke the governed R2 result root. They exercise the inert
default path, structural boundaries, fail-closed predicate behavior, and an
isolated temp-destination writer. The frozen attempt-1 result namespace is
treated as immutable evidence and is only ever read.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.thesis import stage3_r2_adjudication as adj
from experiments.thesis import stage3_r2_amendment as amendment
from experiments.thesis import stage3_registration as reg

REPO_ROOT = Path(__file__).resolve().parents[1]
R2_SOURCE = REPO_ROOT / "experiments/thesis/stage3_r2_adjudication.py"
R2_RESULT_ROOT = REPO_ROOT / amendment.R2_RESULT_ROOT.rstrip("/")

FORBIDDEN_SCIENTIFIC_NAMES = {
    "read_csv",
    "read_parquet",
    "DataFrame",
    "_frame_fingerprint",
    "load_clean_frame",
    "inject_defect",
    "evaluate_guard_surfaces",
    "evaluate_defect",
    "mechanism_invariants",
    "assert_mechanism_invariants",
    "compute_secondary_ic",
    "execute_registered_matrix",
    "build_panel_for_target",
    "Ridge",
    "fit",
}
FORBIDDEN_IMPORT_ROOTS = {"pandas", "numpy", "sklearn", "scipy"}
EXPECTATION_MATCH_TOKENS = (
    "expected_result",
    "expected_detection_signal",
    "expected_guard",
    "EXPECTED_DETECTION",
    "OBSERVED_DEFECT_MATRIX",
    "expectation_map",
)


@pytest.fixture(scope="module")
def frozen_evidence():
    return adj.load_frozen_evidence()


def _module_tree() -> ast.AST:
    return ast.parse(R2_SOURCE.read_text(encoding="utf-8"), filename=str(R2_SOURCE))


# --------------------------------------------------------------------------- #
# Inertness and namespace absence
# --------------------------------------------------------------------------- #
def test_import_is_inert_and_creates_no_result_root():
    assert not R2_RESULT_ROOT.exists()
    assert adj.plan()["adjudicated"] is False
    assert adj.plan()["scientific_computation_performed"] is False
    assert not R2_RESULT_ROOT.exists()


def test_bare_cli_is_inert_and_writes_nothing(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(R2_SOURCE)],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["adjudicated"] is False
    assert payload["result_root_exists"] is False
    assert not R2_RESULT_ROOT.exists()


def test_r2_result_root_is_absent_before_any_execution():
    assert not R2_RESULT_ROOT.exists()
    assert amendment.R2_RESULT_ROOT_EXISTS_AT_REGISTRATION is False


# --------------------------------------------------------------------------- #
# Structural boundaries: no scientific recomputation path
# --------------------------------------------------------------------------- #
def test_adjudicator_imports_no_scientific_stack():
    tree = _module_tree()
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert imported.isdisjoint(FORBIDDEN_IMPORT_ROOTS)
    # It must not import the Stage 3 scientific runner at all.
    assert "defect_injection" not in {
        (node.module or "").split(".")[-1]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }


def test_adjudicator_calls_no_forbidden_scientific_function():
    tree = _module_tree()
    called: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                called.add(func.attr)
            elif isinstance(func, ast.Name):
                called.add(func.id)
    assert called.isdisjoint(FORBIDDEN_SCIENTIFIC_NAMES)


def test_adjudicator_never_consumes_expectation_match():
    source = R2_SOURCE.read_text(encoding="utf-8")
    for token in EXPECTATION_MATCH_TOKENS:
        assert token not in source, token


# --------------------------------------------------------------------------- #
# Frozen-pin verification is fail-closed
# --------------------------------------------------------------------------- #
def test_all_five_frozen_attempt1_hashes_are_hard_verified(frozen_evidence):
    verified = adj.verify_frozen_attempt1_hashes()
    assert set(verified) == set(amendment.FROZEN_ATTEMPT1_ARTIFACT_HASHES)
    assert len(verified) == amendment.FROZEN_ATTEMPT1_ARTIFACT_COUNT


@pytest.mark.parametrize("target", sorted(amendment.FROZEN_ATTEMPT1_ARTIFACT_HASHES))
def test_frozen_hash_mismatch_refuses(target):
    tampered = dict(amendment.FROZEN_ATTEMPT1_ARTIFACT_HASHES)
    tampered[target] = "0" * 64
    with pytest.raises(adj.R2AdjudicationError):
        adj.verify_frozen_attempt1_hashes(hashes=tampered)


def test_registered_contract_verifies_against_live_frozen_evidence(frozen_evidence):
    report, attempt, manifest = frozen_evidence
    contract = adj.verify_registered_r2_contract(report, attempt, manifest)
    assert contract["registered_configuration_sha256"] == (
        amendment.STAGE3_REGISTERED_CONFIGURATION_SHA256
    )
    assert contract["frozen_integrity_condition_count"] == len(
        reg.INTEGRITY_CONDITION_IDENTIFIERS
    )


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda r, a, m: r.__setitem__("decision", "PASS"), id="report_decision"),
        pytest.param(lambda r, a, m: a.__setitem__("status", "incomplete"), id="attempt_status"),
        pytest.param(
            lambda r, a, m: a.__setitem__("registered_configuration_sha256", "x" * 64),
            id="config_sha",
        ),
        pytest.param(
            lambda r, a, m: m.__setitem__("completion_status", "in_progress"),
            id="manifest_incomplete",
        ),
        pytest.param(
            lambda r, a, m: r["integrity"].__setitem__("failures", []),
            id="integrity_failures_cleared",
        ),
    ],
)
def test_registered_contract_is_fail_closed(frozen_evidence, mutate):
    report, attempt, manifest = (json.loads(json.dumps(blob)) for blob in frozen_evidence)
    mutate(report, attempt, manifest)
    with pytest.raises(adj.R2AdjudicationError):
        adj.verify_registered_r2_contract(report, attempt, manifest)


# --------------------------------------------------------------------------- #
# A0-A3 evaluated exactly as registered, and fail-closed
# --------------------------------------------------------------------------- #
def test_predicate_passes_on_frozen_evidence_and_preserves_statuses(frozen_evidence):
    report, attempt, manifest = frozen_evidence
    predicate = adj.evaluate_r2_predicate(report, attempt, manifest)
    assert predicate["predicate_passed"] is True
    assert [clause["passed"] for clause in predicate["predicate_clauses"]] == [True] * 4
    assert predicate["a3_evidence_label"] == "DERIVED"
    assert predicate["expectation_match_consumed"] is False
    assert predicate["carried_frozen_integrity_conditions_recomputed"] is False
    assert predicate["frozen_per_defect_statuses_recomputed"] is False
    assert predicate["frozen_per_defect_detected_by_recomputed"] is False
    frozen = {
        str(record["defect_id"]): record["status"] for record in report["defects"]
    }
    assert predicate["frozen_per_defect_statuses"] == frozen
    carried = predicate["carried_frozen_integrity_conditions"]
    assert set(carried) == set(amendment.R2_RETAINED_FROZEN_INTEGRITY_CONDITIONS)
    assert len(carried) == 16
    assert all(value is True for value in carried.values())
    # readjudicated_decision is the mechanical output of the frozen statuses, not
    # a preregistered value: two of five frozen rows are NOT_DETECTED.
    assert predicate["readjudicated_decision"] == "FAIL"
    assert predicate["readjudicated_decision_value_preregistered"] is False
    assert predicate["original_decision"] == "INCONCLUSIVE"


def test_a0_is_fail_closed():
    assert adj.evaluate_a0([{"defect_id": i} for i in (4000, 4001, 4002, 4003)])["passed"] is False
    assert adj.evaluate_a0([{"defect_id": i} for i in (4000, 4001, 4002, 4003, 9999)])["passed"] is False
    assert adj.evaluate_a0([{"defect_id": i} for i in (4000, 4000, 4002, 4003, 4004)])["passed"] is False
    assert adj.evaluate_a0([{"defect_id": i} for i in (4000, 4001, 4002, 4003, 4004)])["passed"] is True


def test_a1_is_fail_closed(frozen_evidence):
    report, attempt, manifest = (json.loads(json.dumps(blob)) for blob in frozen_evidence)
    assert adj.evaluate_a1(report, attempt, manifest)["passed"] is True
    bad_source = json.loads(json.dumps(report))
    bad_source["defects"][0]["source_sha256_after"] = "f" * 64
    assert adj.evaluate_a1(bad_source, attempt, manifest)["passed"] is False
    no_gate = json.loads(json.dumps(report))
    no_gate["integrity"]["conditions"]["frozen_source_dataset_path_and_sha_match"] = False
    result = adj.evaluate_a1(no_gate, attempt, manifest)
    assert result["passed"] is False
    assert result["load_time_source_integrity_gates_completed"] is False


def test_a2_is_fail_closed(frozen_evidence):
    report, _, _ = frozen_evidence
    defects = json.loads(json.dumps(report["defects"]))
    assert adj.evaluate_a2(defects)["passed"] is True
    defects[2]["clean_comparator"]["detection_signals"] = [{"surface": "GS_X"}]
    assert adj.evaluate_a2(defects)["passed"] is False
    missing = json.loads(json.dumps(report["defects"]))
    missing[1]["clean_comparator"].pop("detection_signals")
    assert adj.evaluate_a2(missing)["passed"] is False


def test_a3_derived_evidence_is_fail_closed_and_labelled_derived(frozen_evidence):
    report, _, _ = frozen_evidence
    defects = json.loads(json.dumps(report["defects"]))
    ok = adj.evaluate_a3(defects)
    assert ok["passed"] is True
    assert ok["evidence_label"] == "DERIVED"
    assert ok["is_derived_not_observed"] is True
    assert ok["forbidden_observation_label"] == "OBSERVED_FINGERPRINT_EQUALITY"
    assert ok["attempt1_fingerprint_values_persisted"] is False

    for field_mutation in (
        lambda d: d[0]["mechanism_invariants"].__setitem__("passed", False),
        lambda d: d[0]["mechanism_invariants"]["checks"].__setitem__("source_shape_clean", False),
        lambda d: d[0]["clean_comparator"].__setitem__("cleanup_proven", False),
        lambda d: d[0]["clean_comparator"].__setitem__("containment_passed", False),
        lambda d: d[0]["clean_comparator"].__setitem__("invocation_accounting_passed", False),
        lambda d: d[0].__setitem__("source_sha256_before", "a" * 64),
        lambda d: d[0]["mechanism_invariants"].pop("passed"),
    ):
        mutated = json.loads(json.dumps(report["defects"]))
        field_mutation(mutated)
        assert adj.evaluate_a3(mutated)["passed"] is False


def test_predicate_ignores_expectation_match(frozen_evidence):
    report, attempt, manifest = (json.loads(json.dumps(blob)) for blob in frozen_evidence)
    for record in report["defects"]:
        record["expected_result"] = "DETECTED"
        record["expected_detection_signal"] = "anything"
        record["expected_guard"] = "GS_FAKE"
    predicate = adj.evaluate_r2_predicate(report, attempt, manifest)
    assert predicate["predicate_passed"] is True
    assert predicate["readjudicated_decision"] == "FAIL"


@pytest.mark.parametrize(
    ("statuses", "integrity_passed", "expected"),
    [
        ([reg.DETECTED] * 5, True, "PASS"),
        ([reg.DETECTED, reg.NOT_DETECTED, reg.DETECTED, reg.DETECTED, reg.DETECTED], True, "FAIL"),
        ([reg.DETECTED, reg.INCONCLUSIVE, reg.DETECTED, reg.DETECTED, reg.DETECTED], True, "INCONCLUSIVE"),
        ([reg.DETECTED] * 5, False, "INCONCLUSIVE"),
        ([reg.DETECTED] * 4, True, "INCONCLUSIVE"),
    ],
)
def test_readjudicated_decision_reapplies_the_stage3_rule(statuses, integrity_passed, expected):
    assert adj._readjudicated_decision(statuses, integrity_passed=integrity_passed) == expected


# --------------------------------------------------------------------------- #
# Isolated-destination writer: exactly two registered files, no attempts dir
# --------------------------------------------------------------------------- #
def test_writer_emits_exactly_two_registered_files(tmp_path, frozen_evidence):
    report, attempt, manifest = frozen_evidence
    frozen_hashes = adj.verify_frozen_attempt1_hashes()
    contract = adj.verify_registered_r2_contract(report, attempt, manifest)
    predicate = adj.evaluate_r2_predicate(report, attempt, manifest)
    record = adj.build_r2_record(
        frozen_hashes=frozen_hashes, contract=contract, predicate=predicate
    )
    markdown = adj.render_r2_markdown(record)

    destination = tmp_path / "defect_injection_r2_adjudication"
    written = adj._write_r2_artifacts(destination, record, markdown)

    assert sorted(path.name for path in written) == [
        "stage3_r2_adjudication.json",
        "stage3_r2_adjudication.md",
    ]
    assert sorted(p.name for p in destination.iterdir()) == [
        "stage3_r2_adjudication.json",
        "stage3_r2_adjudication.md",
    ]
    assert not any(p.is_dir() for p in destination.iterdir())
    assert not (destination / "attempts").exists()

    payload = json.loads((destination / "stage3_r2_adjudication.json").read_text())
    assert payload["original_decision"] == "INCONCLUSIVE"
    assert payload["readjudicated_decision_value_preregistered"] is False
    assert payload["stage7_unlocked"] is False
    assert payload["scientific_recomputation_performed"] is False
    assert "not investment advice" in (
        destination / "stage3_r2_adjudication.md"
    ).read_text().lower()

    assert not R2_RESULT_ROOT.exists()


def test_writer_refuses_a_third_file(tmp_path):
    destination = tmp_path / "r2"
    destination.mkdir()
    (destination / "attempts").mkdir()
    with pytest.raises(adj.R2AdjudicationError):
        adj._write_r2_artifacts(destination, {"k": "v"}, "# x\n")
