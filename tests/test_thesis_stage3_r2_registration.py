"""Machine-checkable guards for the inert Stage 3 R2 registration."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

from experiments.thesis import stage3_r2_amendment as reg


REPO_ROOT = Path(__file__).resolve().parents[1]
R2_ROOT = REPO_ROOT / reg.R2_RESULT_ROOT.rstrip("/")
R2_SOURCE = REPO_ROOT / "experiments/thesis/stage3_r2_amendment.py"
R2_DOC = REPO_ROOT / "docs/thesis/STAGE_3_R2_AMENDMENT.md"
PROTOCOL = REPO_ROOT / "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md"
REGISTRY = REPO_ROOT / "artifact_registry.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_registration_lifecycle_and_authority_are_exact():
    assert reg.AMENDMENT_ID == "FINANCEIQ-THESIS-STAGE3-R2-INTEGRITY-ACCOUNTING"
    assert reg.AMENDMENT_DATE == "2026-09-06"
    assert reg.STATUS == "REGISTERED"
    assert reg.IMPLEMENTATION_STATUS == "NOT IMPLEMENTED"
    assert reg.ADJUDICATION_STATUS == "NOT ADJUDICATED"
    assert reg.REGISTRATION_ONLY is True
    assert reg.NO_SCIENTIFIC_RUN_PERFORMED is True
    assert reg.NO_R2_ADJUDICATION_PERFORMED is True
    assert reg.AUTHORITATIVE_BASE_COMMIT == (
        "d4e7196fc43098f18b888ad602d1f1cd06101829"
    )
    assert reg.EVIDENCE_COMMIT == "31643f19d58639b6aa4575625b4460dbdb4ab9b8"
    assert reg.POST_RUN_GOVERNANCE_COMMIT == (
        "972f30adcf0f0419cec6fd71bfedb7967fad9ed2"
    )


def test_frozen_attempt1_hashes_and_original_decision_are_preserved():
    assert reg.ORIGINAL_DECISION == "INCONCLUSIVE"
    assert reg.STAGE3_ATTEMPT_NUMBER == 1
    assert reg.STAGE3_ATTEMPT_TYPE == "initial"
    assert reg.STAGE3_ATTEMPT_STATUS == "complete"
    assert reg.STAGE3_PRIOR_INCOMPLETE_ATTEMPT is False
    assert reg.SOLE_FAILED_INTEGRITY_CONDITION == (
        "clean_comparator_byte_and_logical_identity"
    )
    assert len(reg.FROZEN_ATTEMPT1_ARTIFACT_HASHES) == 5
    for relative, expected in reg.FROZEN_ATTEMPT1_ARTIFACT_HASHES.items():
        path = REPO_ROOT / relative
        assert path.is_file(), relative
        assert sha256(path) == expected, relative
    assert reg.DATASET_SHA256 == (
        "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
    )
    assert sha256(REPO_ROOT / reg.DATASET_PATH) == reg.DATASET_SHA256
    assert reg.STAGE3_REGISTERED_CONFIGURATION_SHA256 == (
        "4594521fde98c92a52400c9a02139c570b3d5241a2abfbd0d6006c213b51c677"
    )
    assert sha256(REPO_ROOT / reg.STAGE3_REGISTRATION_DOC) == (
        reg.STAGE3_REGISTRATION_DOC_SHA256
    )
    assert sha256(REPO_ROOT / reg.STAGE3_REGISTRATION_MODULE) == (
        reg.STAGE3_REGISTRATION_MODULE_SHA256
    )
    assert reg.ATTEMPT1_FINGERPRINT_VALUES_PERSISTED is False
    assert reg.ORIGINAL_ATTEMPT_ARTIFACTS_MUST_REMAIN_BYTE_IDENTICAL is True


def test_r2_root_is_absent_and_registry_has_exactly_two_prospective_contracts():
    assert reg.R2_RESULT_ROOT_EXISTS_AT_REGISTRATION is False
    assert not R2_ROOT.exists()
    assert reg.R2_RESULT_FILENAMES == (
        "stage3_r2_adjudication.json",
        "stage3_r2_adjudication.md",
    )
    assert reg.R2_PROSPECTIVE_ARTIFACT_COUNT == 2
    assert reg.R2_HAS_NO_ATTEMPTS_DIRECTORY is True
    assert reg.R2_HAS_NO_SCIENTIFIC_RUN_MANIFEST is True

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    root = reg.R2_RESULT_ROOT.rstrip("/")
    assert root in registry["governed_roots"]
    prospective = [
        entry
        for entry in registry["prospective_entries"]
        if entry["path_or_glob"].startswith(root + "/")
    ]
    assert tuple(entry["path_or_glob"] for entry in prospective) == tuple(
        f"{root}/{name}" for name in reg.R2_RESULT_FILENAMES
    )
    assert len(prospective) == 2
    assert all(entry["artifact_class"] == "generated" for entry in prospective)
    assert all(entry["hand_edit_forbidden"] is True for entry in prospective)
    assert all(
        entry["generator_command"] == "make thesis-stage3-r2-adjudication"
        for entry in prospective
    )
    assert all(entry["notes"].strip() for entry in prospective)
    assert not any(
        entry["path_or_glob"].startswith(root + "/")
        for entry in registry["entries"]
    )


def test_a0_to_a3_and_derived_not_observed_contract_is_registered():
    assert reg.R2_OPTION == "A"
    assert reg.R2_REGISTERED_DEFECT_IDS == (4000, 4001, 4002, 4003, 4004)
    assert reg.R2_REGISTERED_DEFECT_COUNT == 5
    assert len(reg.R2_PREDICATE_CLAUSES) == 4
    assert set(reg.R2_PREDICATE_CLAUSES) == {
        "A0_CARDINALITY",
        "A1_PINNED_CLEAN_SOURCE_RE_READ",
        "A2_ZERO_CLEAN_DETECTION_SIGNALS",
        "A3_DERIVED_CLEAN_LOGICAL_IDENTITY",
    }
    assert reg.R2_A1_REQUIRED_COMPARISON == (
        "source_sha256_before == source_sha256_after == registered DATASET_SHA256",
        "completed load-time source-integrity gates without raising",
    )
    assert reg.R2_A2_REQUIRED_FIELD == "clean_comparator.detection_signals == []"
    assert reg.A3_REQUIRED_DERIVED_EVIDENCE_FIELDS == (
        "source_sha256_before",
        "source_sha256_after",
        "mechanism_invariants.passed",
        "mechanism_invariants.checks.source_shape_clean",
        "clean_comparator.cleanup_proven",
        "clean_comparator.containment_passed",
        "clean_comparator.invocation_accounting_passed",
    )
    assert reg.A3_DERIVATION_LABEL == "DERIVED"
    assert reg.A3_FORBIDDEN_OBSERVATION_LABEL == "OBSERVED_FINGERPRINT_EQUALITY"
    assert reg.A3_IS_DERIVED_NOT_OBSERVED is True
    assert reg.R2_MUST_FAIL_CLOSED_ON_MISSING_OR_MISMATCHED_FROZEN_INPUT is True
    assert reg.R2_RETAINED_FROZEN_INTEGRITY_CONDITION_COUNT == 16
    assert len(reg.R2_RETAINED_FROZEN_INTEGRITY_CONDITIONS) == 16


def test_r2_does_not_preregister_a_readjudicated_value_or_authorize_a_draw():
    assert reg.READJUDICATED_DECISION_FIELD == "readjudicated_decision"
    assert reg.READJUDICATED_DECISION_VALUE_PREREGISTERED is False
    assert reg.READJUDICATED_DECISION_COMPUTED_ONLY_BY_FUTURE_ADJUDICATOR is True
    assert reg.R2_DECISION_FUNCTION_DOES_NOT_HARDCODE_FAIL is True
    assert reg.R2_ORIGINAL_DECISION_REMAINS_PERMANENTLY == "INCONCLUSIVE"
    assert reg.SECOND_STAGE3_DRAW_AUTHORIZED is False
    assert reg.REPEAT_AFTER_CRASH_AUTHORIZED is False
    assert reg.NO_SECOND_STAGE3_DRAW is True
    assert reg.FORWARD_PREDICATE_REGISTERED is True
    assert reg.FORWARD_PREDICATE_EXERCISED_BY_R2 is False
    assert (
        reg.FUTURE_EXECUTION_MUST_PERSIST_EACH_PER_DEFECT_CLEAN_FINGERPRINT
        is True
    )


def test_recovery_repair_is_registered_but_not_implemented():
    assert "integrity_passed == true" in reg.RECOVERY_DEFECT
    assert len(reg.RECOVERY_REPAIR_REQUIREMENTS) == 4
    assert reg.RECOVERY_REPAIR_REGISTERED is True
    assert reg.RECOVERY_REPAIR_IMPLEMENTED is False
    assert any(
        "status == complete" in item for item in reg.RECOVERY_REPAIR_REQUIREMENTS
    )
    assert any(
        "cleanup primitive" in item for item in reg.RECOVERY_REPAIR_REQUIREMENTS
    )


def test_documents_mirror_the_registration_and_protocol_amendment():
    amendment = R2_DOC.read_text(encoding="utf-8")
    protocol = PROTOCOL.read_text(encoding="utf-8")
    for phrase in (
        "2026-09-06",
        "REGISTERED / NOT IMPLEMENTED / NOT ADJUDICATED",
        "R2 Option A",
        "A0 — cardinality",
        "A1 — pinned clean source re-read contract",
        "A2 — zero clean detection signals",
        "A3 — derived clean logical identity",
        "DERIVED",
        "OBSERVED_FINGERPRINT_EQUALITY",
        "attempt-1 did **not** persist",
        "readjudicated_decision",
        "R2 REFUSES",
        "No second Stage 3 draw",
        "repeat-after-crash",
        "Stage 7 remains **BLOCKED**",
    ):
        assert phrase in amendment, phrase
    marker = "### 2026-09-06 — Stage 3 R2 integrity-accounting amendment"
    assert protocol.count(marker) == 1
    suffix = protocol[protocol.index(marker) :]
    for phrase in (
        "What changed.",
        "Why.",
        "What had already been observed.",
        "accounting-only",
        "DERIVED",
        "No scientific parameter",
        "multiplicity",
        "readjudicated_decision",
    ):
        assert phrase in suffix, phrase


def test_registration_module_is_ast_inert_and_has_no_execution_entry_point():
    tree = ast.parse(
        R2_SOURCE.read_text(encoding="utf-8"), filename=str(R2_SOURCE)
    )
    assert not any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for node in ast.walk(tree)
    )
    assert not any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
    forbidden_calls = {
        "read_csv",
        "read_json",
        "DataFrame",
        "open",
        "write_text",
        "mkdir",
        "unlink",
        "rmtree",
        "fit",
    }
    calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert calls.isdisjoint(forbidden_calls)
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"exec", "eval", "compile"}
        for node in ast.walk(tree)
    )


def test_stage7_remains_blocked_and_residual_disclosures_are_explicit():
    assert reg.STAGE_7_UNLOCKED is False
    assert reg.STAGE_7_REMAINS_BLOCKED is True
    assert len(reg.STAGE_7_BLOCKED_REASONS) == 3
    assert reg.GOVERNED_DRAW_STARTED_CLEAN is True
    assert reg.DIRTY_AT_START_MUST_NOT_BE_CLAIMED is True
    assert len(reg.RESIDUAL_DISCLOSURES) == 3
    assert any(
        "fingerprint values were not persisted" in item
        for item in reg.RESIDUAL_DISCLOSURES
    )
    assert len(reg.R2_FALSIFIERS) == 11
