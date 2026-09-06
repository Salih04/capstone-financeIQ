"""Machine-checkable guards for the Stage 3 registration and post-run state.

These tests preserve the historical registration contract while checking the
completed attempt-1 result namespace. They do not implement Stage 3, inject any
defect, run any guard against an injected frame, or modify Stage 1 / Stage 1b /
Stage 2 artifacts.

Registration-test boundary — enforced here and by
``test_registration_tests_construct_no_injected_frame``:

* allowed — inspect repository source, read the frozen dataset read-only,
  verify frozen source facts, verify registration constants, prove source
  semantics structurally (AST / function contract), and prove that importing
  registration leaves the completed Stage 3 result root unchanged;
* forbidden — construct the 4000 transformation, the 4001 rotation, the 4002
  added leak column, the 4003 membership selection, or the 4004 duplication.

Every frozen injection count in the registration is a prospective expectation.
Verifying those counts behaviorally requires building an injected frame, so it
belongs to the Stage 3 *implementation* tests, not to these registration tests.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.thesis import provenance as prov
from experiments.thesis import stage3_registration as reg


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOC = REPO_ROOT / reg.REGISTRATION_DOC
PROTOCOL_DOC = REPO_ROOT / reg.PROTOCOL_DOC
REGISTRATION_SOURCE = REPO_ROOT / "experiments/thesis/stage3_registration.py"
RESULT_ROOT = REPO_ROOT / reg.RESULT_ROOT.rstrip("/")
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
DATASET_PATH = REPO_ROOT / reg.DATASET_PATH
MAKEFILE = REPO_ROOT / "Makefile"
THESIS_README = REPO_ROOT / "experiments/thesis/README.md"
TASK_STATE = REPO_ROOT / "TASK_STATE.md"
STAGE3_RESULT_FILENAMES = (
    "defect_injection_report.json",
    "defect_injection_report.md",
    "defect_results.csv",
    "artifact_manifest.json",
)
AUTHORITATIVE_BASE = "c418563f432f5b253fb3b0e69619c76608ea15ea"
AUTHORITATIVE_PROTOCOL_PREFIX_SHA256 = (
    "095ae8ddceebf186bcc9820036760a28b8dd21cb3ea81c0708bd151c118bbcbb"
)
CELL_PROVENANCE_REPOSITORY_AUTHORITY_SHA256 = (
    "4f61fe66c8328aa4d69eda3c27b9328058708d9733f18287db63bc9a1994c0c6"
)
HISTORICAL_UNCHANGED_HASHES = {
    "experiments/thesis/stage1b_registration.py": (
        "7a140f8caf4d2f58db6479a1124bf97241eb91dd6d207f12bc974f6110bf0caa"
    ),
    "experiments/thesis/positive_control.py": (
        "44c897568f17618b7db0a42103384f43d24da5fb296bf092b422ef51a495e27d"
    ),
    "experiments/thesis/positive_control_calibration.py": (
        "61a34acd577874ec269e4a654a686bdd1224c99016950aac01af694d10903020"
    ),
    "docs/thesis/STAGE_1B_REGISTRATION.md": (
        "d45b3e916f50ad54800d1a78c25ae06a303710c218264690063427f7b63e783e"
    ),
    "docs/thesis/STAGE_2_REGISTRATION.md": (
        "6744e67d2a3c58e5ba7ad5f7c7794aa5e5f8487b65e765789e6fc2041ec701cc"
    ),
}

REGISTERED_MUTATION_PATHS = (
    "TASK_STATE.md",
    "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md",
    "docs/thesis/STAGE_3_REGISTRATION.md",
    "experiments/thesis/README.md",
    "experiments/thesis/stage3_registration.py",
    "tests/test_thesis_stage3_registration.py",
)

STAGE3_AMENDMENT_MARKER = "### 2026-09-04 — Stage 3 dated amendment and registration"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compact(value: str) -> str:
    return " ".join(value.replace("**", "").replace("`", "").split())


def result_tree_hashes() -> dict[str, str]:
    return {
        item.relative_to(REPO_ROOT).as_posix(): sha256(item)
        for item in sorted(RESULT_ROOT.rglob("*"))
        if item.is_file()
    }


def _function_def(path: Path, name: str) -> ast.FunctionDef:
    """Return the top-level ``def name`` node of ``path``, parsed not executed."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is not a top-level function of {path}")


def _function_source(path: Path, name: str) -> str:
    return ast.unparse(_function_def(path, name))


@pytest.fixture(scope="module")
def registration_doc() -> str:
    return REGISTRATION_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def protocol_doc() -> str:
    return PROTOCOL_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def compact_registration_doc(registration_doc: str) -> str:
    return compact(registration_doc)


# --------------------------------------------------------------------------- #
# Source pin
# --------------------------------------------------------------------------- #
def test_authoritative_base_provenance_and_exact_registration_mutation_surface():
    assert reg.AUTHORITATIVE_BASE_COMMIT == AUTHORITATIVE_BASE
    # This commit is a frozen provenance identifier. Direct-parent and ancestry
    # verification was completed at review time and is intentionally not a CI
    # invariant: shallow checkouts need not contain the historical object.
    assert REGISTERED_MUTATION_PATHS == (
        "TASK_STATE.md",
        "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md",
        "docs/thesis/STAGE_3_REGISTRATION.md",
        "experiments/thesis/README.md",
        "experiments/thesis/stage3_registration.py",
        "tests/test_thesis_stage3_registration.py",
    )
    assert len(REGISTERED_MUTATION_PATHS) == 6
    assert len(set(REGISTERED_MUTATION_PATHS)) == 6
    for relative in REGISTERED_MUTATION_PATHS:
        assert (REPO_ROOT / relative).is_file(), relative
    assert reg.NO_STAGE3_INJECTION_DRAW_OR_OUTCOME is True
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME_IS_PROSPECTIVE is True
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME_IS_OBSERVED is False


def test_source_pin_path_and_hash_are_exact(compact_registration_doc):
    assert reg.DATASET_PATH == (
        "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
    )
    assert reg.DATASET_SHA256 == (
        "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
    )
    assert DATASET_PATH.is_file()
    assert sha256(DATASET_PATH) == reg.DATASET_SHA256
    assert reg.DATASET_SHA256 in compact_registration_doc
    assert reg.DATASET_PATH in compact_registration_doc
    assert reg.EXPANDED_DATASETS_ARE_NOT_STAGE3_INPUTS is True
    assert "FI-DATA-EXPAND outputs are not Stage 3 inputs" in compact_registration_doc


def test_registered_guard_surface_hashes_match_frozen_pins():
    assert set(reg.SOURCE_MODULE_HASHES) == {
        "scripts/data_collection/validate.py",
        "scripts/data_collection/pipeline.py",
        "scripts/data_collection/derive_alternative_targets.py",
        "scripts/data_collection/split_universe_datasets.py",
        "scripts/data_collection/validate_universe.py",
        "tests/test_pipeline_guards.py",
        "experiments/thesis/provenance.py",
        "experiments/run_experiments.py",
    }
    for relative, expected in reg.SOURCE_MODULE_HASHES.items():
        assert sha256(REPO_ROOT / relative) == expected, relative
    assert sha256(REPO_ROOT / reg.CELL_PROVENANCE_SOURCE) == reg.CELL_PROVENANCE_SHA256
    assert reg.AUTHORITATIVE_BASE_COMMIT == (
        "c418563f432f5b253fb3b0e69619c76608ea15ea"
    )


def test_declared_dataset_shape_facts_match_the_pinned_source():
    import pandas as pd

    frame = pd.read_csv(DATASET_PATH)
    assert len(frame) == reg.DATASET_ROW_COUNT == 403
    assert len(frame.columns) == reg.DATASET_COLUMN_COUNT == 61
    assert tuple(sorted(int(y) for y in frame["year"].unique())) == reg.DATASET_YEARS
    assert int(frame["year"].min()) == reg.DATASET_MIN_YEAR == 2020
    assert int((frame["year"] == reg.DATASET_MIN_YEAR).sum()) == (
        reg.DATASET_ROWS_AT_MIN_YEAR
    )
    assert int(frame[reg.TARGET_COLUMN].notna().sum()) == (
        reg.DATASET_OBSERVED_TARGET_ROWS
    )
    assert int(frame.duplicated(list(reg.KEY_COLUMNS)).sum()) == (
        reg.DATASET_DUPLICATE_KEYS
    )
    assert bool((frame[reg.ALIGNMENT_COLUMN] == frame["year"] + 1).all())


# --------------------------------------------------------------------------- #
# Closed defect family and IDs
# --------------------------------------------------------------------------- #
def test_defect_family_is_exactly_five_and_closed(compact_registration_doc):
    assert reg.DEFECT_FAMILY == (
        "FUTURE_YEAR_FEATURE_LEAKAGE",
        "T_TPLUS1_MISALIGNMENT",
        "TARGET_LEAKAGE_INTO_FEATURES",
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP",
        "DUPLICATE_ROW_INFLATION",
    )
    assert len(reg.DEFECT_FAMILY) == reg.DEFECT_FAMILY_SIZE == 5
    assert len(set(reg.DEFECT_FAMILY)) == 5
    assert reg.DEFECT_FAMILY_IS_CLOSED is True
    assert reg.NO_ADDITIONAL_DEFECT_CLASS_IN_FIRST_DRAW is True
    assert reg.INJECTIONS_PER_DEFECT_CLASS == 1
    assert reg.NO_SEVERITY_GRID is True
    assert reg.NO_REPEATED_PERFORMANCE_EXPERIMENT is True
    assert tuple(reg.GUARD_MAP) == reg.DEFECT_FAMILY
    assert tuple(reg.DEFECT_IDS) == reg.DEFECT_FAMILY
    assert tuple(reg.EXPECTED_DETECTION) == reg.DEFECT_FAMILY
    assert tuple(reg.RNG_USAGE) == reg.DEFECT_FAMILY
    for name in reg.DEFECT_FAMILY:
        assert name in compact_registration_doc


def test_defect_ids_are_4000_to_4004_without_duplicates_or_collisions():
    assert reg.ALL_STAGE3_IDS == (4000, 4001, 4002, 4003, 4004)
    assert tuple(reg.DEFECT_IDS.values()) == reg.ALL_STAGE3_IDS
    assert len(set(reg.ALL_STAGE3_IDS)) == 5
    assert reg.STAGE3_ID_RANGE == (4000, 4004)
    for name, defect_id in reg.DEFECT_IDS.items():
        assert reg.GUARD_MAP[name]["DEFECT_ID"] == defect_id
        assert reg.GUARD_MAP[name]["DEFECT_NAME"] == name

    forbidden = set(reg.STAGE_1_IDS) | set(reg.STAGE_1B_IDS)
    forbidden |= set(reg.RESERVED_IDS) | set(reg.STAGE_2_IDS)
    assert forbidden == set(range(0, 4000))
    assert not forbidden & set(reg.ALL_STAGE3_IDS)
    for label, (low, high) in reg.FORBIDDEN_ID_RANGES.items():
        assert all(not (low <= i <= high) for i in reg.ALL_STAGE3_IDS), label


def test_seed_schedule_is_literal_deterministic_and_reproduces():
    assert reg.BASE_SEED == 42
    assert prov.SEEDS["defect_injection"] == reg.BASE_SEED
    assert prov.seed_for("defect_injection") == reg.BASE_SEED
    assert reg.PROVENANCE_SEED_SOURCE == 'provenance.SEEDS["defect_injection"]'
    assert reg.STAGE3_SEED_FORMULA == "BASE_SEED * 1_000_003 + defect_id"
    assert dict(reg.STAGE3_SEED_VALUES) == {
        4000: 42004126,
        4001: 42004127,
        4002: 42004128,
        4003: 42004129,
        4004: 42004130,
    }
    for defect_id, expected in reg.STAGE3_SEED_VALUES.items():
        assert reg.injection_seed(defect_id) == expected
        assert reg.injection_seed(defect_id) == 42 * 1_000_003 + defect_id
    assert len(set(reg.STAGE3_SEED_VALUES.values())) == 5


def test_every_defect_is_registered_no_rng():
    assert reg.NO_RNG == "NO_RNG"
    assert set(reg.RNG_USAGE.values()) == {"NO_RNG"}
    assert reg.ALL_INJECTIONS_ARE_DETERMINISTIC is True
    assert reg.RNG_CONSUMPTION_IN_FIRST_DRAW_IS_INTEGRITY_FAILURE is True


# --------------------------------------------------------------------------- #
# Guard map: no fabrication, NONE_EXISTING preserved
# --------------------------------------------------------------------------- #
def test_guard_map_records_are_complete_for_every_defect():
    required = {
        "DEFECT_ID",
        "DEFECT_NAME",
        "CLEAN_BASELINE_CONDITION",
        "EXACT_INJECTION_MECHANISM",
        "CONTAINMENT_BOUNDARY",
        "EXPECTED_GUARD",
        "EXACT_DETECTION_SIGNAL",
        "EXPECTED_RESULT",
        "SECONDARY_IC_APPLICABLE",
        "INTEGRITY_INVARIANTS",
        "EVALUATED_SURFACES",
        "ROW_UNIVERSE",
    }
    for name, record in reg.GUARD_MAP.items():
        assert required <= set(record), name
        assert record["EXPECTED_RESULT"] in (reg.DETECTED, reg.NOT_DETECTED)
        assert isinstance(record["SECONDARY_IC_APPLICABLE"], bool)
        assert record["EVALUATED_SURFACES"], name
        assert record["INTEGRITY_INVARIANTS"], name
        assert str(record["CLEAN_BASELINE_CONDITION"]).strip()
        assert str(record["EXACT_INJECTION_MECHANISM"]).strip()
        for surface in record["EVALUATED_SURFACES"]:
            assert surface in reg.GUARD_SURFACES, (name, surface)


def test_no_guard_is_fabricated_and_none_existing_is_preserved():
    for name, record in reg.GUARD_MAP.items():
        expected = record["EXPECTED_GUARD"]
        if expected == reg.NONE_EXISTING:
            assert record["EXACT_DETECTION_SIGNAL"] == reg.NO_DETECTION_SIGNAL, name
            assert record["EXPECTED_RESULT"] == reg.NOT_DETECTED, name
            assert str(record["GUARD_GAP_REASON"]).strip(), name
        else:
            assert expected in reg.GUARD_SURFACES, name
            assert expected in record["EVALUATED_SURFACES"], name
            assert record["EXACT_DETECTION_SIGNAL"] != reg.NO_DETECTION_SIGNAL
            assert record["EXPECTED_RESULT"] == reg.DETECTED, name
            assert reg.GUARD_SURFACES[expected]["reachability"] == (
                "REACHABLE_CONTAINED"
            ), name

    # Every catalogued surface points at a real repository location.
    for key, surface in reg.GUARD_SURFACES.items():
        assert surface["kind"] in reg.GUARD_OBJECT_KINDS, key
        assert surface["reachability"] in reg.REACHABILITY_STATES, key
        relative = surface["location"].split("::")[0]
        assert (REPO_ROOT / relative).is_file(), key
        assert str(surface["signal"]).strip(), key


def test_expected_guard_gaps_are_registered_prospectively(compact_registration_doc):
    assert reg.EXPECTED_GUARD_GAPS == (
        "FUTURE_YEAR_FEATURE_LEAKAGE",
        "T_TPLUS1_MISALIGNMENT",
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP",
    )
    assert "TARGET_LEAKAGE_INTO_FEATURES" not in reg.EXPECTED_GUARD_GAPS
    gaps = tuple(
        name
        for name, record in reg.GUARD_MAP.items()
        if record["EXPECTED_GUARD"] == reg.NONE_EXISTING
    )
    assert gaps == reg.EXPECTED_GUARD_GAPS
    assert dict(reg.EXPECTED_DETECTION) == {
        "FUTURE_YEAR_FEATURE_LEAKAGE": reg.NOT_DETECTED,
        "T_TPLUS1_MISALIGNMENT": reg.NOT_DETECTED,
        "TARGET_LEAKAGE_INTO_FEATURES": reg.DETECTED,
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP": reg.NOT_DETECTED,
        "DUPLICATE_ROW_INFLATION": reg.DETECTED,
    }
    for name, record in reg.GUARD_MAP.items():
        assert record["EXPECTED_RESULT"] == reg.EXPECTED_DETECTION[name]
    assert reg.EXPECTED_FIRST_DRAW_DECISION == "FAIL"
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME == "FAIL — INFORMATIVE"
    assert reg.EXPECTED_FAIL_IS_INFORMATIVE is True
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME_IS_PROSPECTIVE is True
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME_IS_OBSERVED is False
    assert reg.EXPECTATION_DOES_NOT_CHANGE_THE_PASS_RULE is True
    assert reg.DETECTION_IS_DECIDED_BY_EMITTED_SIGNAL_NOT_BY_EXPECTATION is True
    assert "Expected first-draw outcome: FAIL — INFORMATIVE" in (
        compact_registration_doc
    )
    assert "not an observed scientific result" in compact_registration_doc


def test_no_guard_repair_or_new_guard_before_the_first_draw():
    assert reg.NO_NEW_GUARD_BEFORE_FIRST_DRAW is True
    assert reg.NO_GUARD_REPAIR_BEFORE_FIRST_DRAW is True
    assert reg.GUARD_REPAIR_BELONGS_TO_SEPARATE_REMEDIATION_STAGE is True
    assert reg.FIRST_DRAW_ARTIFACTS_ARE_IMMUTABLE is True
    assert reg.INPUT_BLIND_SILENCE_IS_NOT_EVALUATION is True
    assert reg.INPUT_BLIND_SILENCE_IS_NOT_NON_DETECTION is True


# --------------------------------------------------------------------------- #
# Reachability claims proved against the live repository source
# --------------------------------------------------------------------------- #
def test_named_target_leakage_condition_is_structurally_unreachable():
    """Proved from the exclusion sets themselves, without building any frame."""
    from scripts.data_collection import pipeline as pipeline_module

    surface = reg.GUARD_SURFACES["GS_TARGET_LEAK_VALIDATE_ISSUE"]
    assert surface["reachability"] == "STRUCTURALLY_UNREACHABLE"

    # feature_columns is a pure name filter over a fixed exclusion set. The
    # exact literals the two validator conditions test are members of it, so
    # both conditions are unsatisfiable for every DataFrame.
    excluded = (
        set(pipeline_module.IDENTITY_COLS)
        | set(pipeline_module.TARGET_COLS)
        | set(pipeline_module.META_COLS)
        | {"indices", "target_year"}
    )
    assert "next_year_return_pct" in pipeline_module.TARGET_COLS
    assert "same_year_return_pct" in pipeline_module.META_COLS
    assert "next_year_return_pct" in excluded
    assert "same_year_return_pct" in excluded

    filter_source = _function_source(
        REPO_ROOT / "scripts/data_collection/pipeline.py", "feature_columns"
    )
    tree = ast.parse(filter_source)
    comprehensions = [
        node for node in ast.walk(tree) if isinstance(node, ast.ListComp)
    ]
    assert len(comprehensions) == 1
    # The only condition is membership in the exclusion set: no prefix rule and
    # no value inspection, so nothing but the exact name can be removed.
    (condition,) = comprehensions[0].generators[0].ifs
    assert isinstance(condition, ast.Compare)
    assert isinstance(condition.ops[0], ast.NotIn)
    assert isinstance(condition.comparators[0], ast.Name)
    assert condition.comparators[0].id == "excl"

    # The registered injected column name is outside that exclusion set, so the
    # repository's own feature rule admits it. This is a name-level fact; no
    # frame is constructed.
    leaked = reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"]["COLUMNS_ADDED"][0]
    assert leaked == "leaked_next_year_return_pct"
    assert leaked not in excluded
    assert not leaked.startswith("next_year_")

    validate_source = (
        REPO_ROOT / "scripts/data_collection/validate.py"
    ).read_text(encoding="utf-8")
    assert 'issues.append("LEAKAGE: next_year_return_pct present in feature set")' in (
        validate_source
    )
    assert reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"][
        "NAMED_SURFACE_FOR_THIS_CLASS"
    ] == "GS_TARGET_LEAK_VALIDATE_ISSUE"
    assert "STRUCTURALLY" in reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"][
        "NAMED_SURFACE_REMAINS_STRUCTURALLY_UNREACHABLE"
    ]


def test_cell_provenance_is_reachable_through_a_caller_supplied_private_root():
    """The provenance module is NOT input-blind: its root is a parameter."""
    from scripts.data_collection import build_cell_provenance as bcp

    source = REPO_ROOT / reg.CELL_PROVENANCE_SOURCE
    assert reg.CELL_PROVENANCE_CALLABLE == (
        "scripts.data_collection.build_cell_provenance.generate"
    )

    # Exact callable + exact private-root semantics, proved structurally.
    for name in ("generate", "resolve_input", "open_checked_file", "prepare_output_dir"):
        node = _function_def(source, name)
        arguments = [argument.arg for argument in node.args.args]
        assert reg.CELL_PROVENANCE_ROOT_PARAMETER in arguments, name
    generate = _function_def(source, "generate")
    assert [argument.arg for argument in generate.args.args] == ["root"]
    assert len(generate.args.defaults) == 1
    assert isinstance(generate.args.defaults[0], ast.Name)
    assert generate.args.defaults[0].id == "REPO_ROOT"
    assert reg.CELL_PROVENANCE_ROOT_DEFAULT == "build_cell_provenance.REPO_ROOT"

    # Exact required relative dataset path, and the closed declared-input set.
    assert reg.CELL_PROVENANCE_REQUIRED_DATASET_REL == bcp.DATASET_REL
    assert bcp.DATASET_REL in bcp.ALLOWED_INPUT_RELS
    assert len(bcp.ALLOWED_INPUT_RELS) == reg.CELL_PROVENANCE_REQUIRED_INPUT_COUNT
    assert set(bcp.ALLOWED_INPUT_RELS) == set(bcp.SOURCE_ARTIFACT_RELS)

    # The private-root pattern is a frozen current-source contract. Its
    # review-time authority is represented by a literal hash, not a Git object.
    authority = reg.CELL_PROVENANCE_REPOSITORY_AUTHORITY.split("::")
    authority_path = REPO_ROOT / authority[0]
    assert authority_path.is_file()
    assert sha256(authority_path) == CELL_PROVENANCE_REPOSITORY_AUTHORITY_SHA256
    authority_node = _function_def(authority_path, authority[1])
    authority_calls = [
        node for node in ast.walk(authority_node) if isinstance(node, ast.Call)
    ]
    assert any(
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "mktemp"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "provenance_repo"
        for node in authority_calls
    )
    assert any(
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "generate"
        and node.args
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "sandbox"
        for node in authority_calls
    )

    # Therefore the surfaces are reachable, not input-blind.
    assert reg.PROVENANCE_SURFACE_WAS_MISCLASSIFIED_AT_FIRST_REGISTRATION_DRAFT is True
    for key in reg.CELL_PROVENANCE_SURFACES:
        surface = reg.GUARD_SURFACES[key]
        assert surface["kind"] == "PROVENANCE_INTEGRITY", key
        assert surface["reachability"] == "REACHABLE_CONTAINED", key
        assert surface["containment_requirement"] == "PRIVATE_PROVENANCE_ROOT", key
        assert "input_blindness_proof" not in surface, key
    assert "PRIVATE_PROVENANCE_ROOT" in reg.CONTAINMENT_MODES
    assert reg.PRIVATE_PROVENANCE_ROOT_REQUIREMENT == (
        reg.CELL_PROVENANCE_PRIVATE_ROOT_SEMANTICS
    )
    assert reg.CELL_PROVENANCE_CANONICAL_DATA_UNTOUCHED is True


def test_cell_provenance_failure_literals_exist_verbatim_in_repository_source():
    """Every registered provenance signal is a string the module really raises."""
    source = (REPO_ROOT / reg.CELL_PROVENANCE_SOURCE).read_text(encoding="utf-8")
    for literal in (
        'raise ProvenanceError("passports v1 does not cover exactly the dataset columns")',
        'raise ProvenanceError(f"columns absent from the frozen resolution table: {missing_specs}")',
        'raise ProvenanceError(f"duplicate dataset key: {(ticker, year)}")',
        'raise ProvenanceError(f"upstream cell not present in the artifact: {parent}")',
    ):
        assert literal in source, literal

    # generate evaluates the passports-coverage condition before it calls
    # build_records, so an undeclared column raises that error first.
    generate = ast.unparse(_function_def(REPO_ROOT / reg.CELL_PROVENANCE_SOURCE, "generate"))
    passports_at = generate.index("passports v1 does not cover exactly the dataset columns")
    build_records_at = generate.index("build_records(")
    assert passports_at < build_records_at
    coverage = reg.GUARD_SURFACES["GS_CELL_PROVENANCE_COLUMN_COVERAGE"]
    assert "before it calls build_records" in coverage["signal_precedence"]
    assert "passports-coverage error first" in coverage["signal_precedence"]

    # build_records decides the frozen-resolution-table condition and the
    # duplicate-key condition before any cell is resolved.
    build_records = ast.unparse(
        _function_def(REPO_ROOT / reg.CELL_PROVENANCE_SOURCE, "build_records")
    )
    assert build_records.index("columns absent from the frozen resolution table") < (
        build_records.index("resolve_cell(")
    )
    assert build_records.index("duplicate dataset key") < build_records.index(
        "resolve_cell("
    )


def test_provenance_lineage_closure_is_a_baseline_state_not_a_detection_signal():
    """The pinned training source is not the complete grid the closure assumes."""
    import pandas as pd

    surface = reg.GUARD_SURFACES["GS_CELL_PROVENANCE_LINEAGE_CLOSURE"]
    assert surface["registered_as_detection_signal"] is False
    assert surface["fires_on_clean_comparator_for_the_pinned_source"] is True
    assert reg.PROVENANCE_LINEAGE_CLOSURE_IS_NOT_A_DETECTION_SIGNAL is True

    # upstream_cells_for gates a hop on the dataset-wide present_years set, not
    # on the per-ticker year set.
    upstream = ast.unparse(
        _function_def(REPO_ROOT / reg.CELL_PROVENANCE_SOURCE, "upstream_cells_for")
    )
    assert "target not in present_years" in upstream
    assert "ticker" not in upstream.split("def price(")[1].split("return")[0]

    # The pinned Stage 3 source is an incomplete (ticker, year) grid, so the
    # closure cannot hold on it — clean or injected, identically.
    frame = pd.read_csv(DATASET_PATH)
    years_per_ticker = frame.groupby("ticker")["year"].nunique()
    assert int(years_per_ticker.min()) < len(reg.DATASET_YEARS)
    assert not bool((years_per_ticker == len(reg.DATASET_YEARS)).all())

    # It is registered neither as a signal nor as a containment failure.
    for record in reg.GUARD_MAP.values():
        assert "GS_CELL_PROVENANCE_LINEAGE_CLOSURE" not in record["EVALUATED_SURFACES"]
    checkpoint = reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"]["EVALUATION_CHECKPOINT"]
    assert "not a signal and not a containment failure" in checkpoint


def test_4002_is_detected_by_the_reachable_existing_provenance_schema_guard():
    from scripts.data_collection import build_cell_provenance as bcp

    record = reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"]
    assert record["EXPECTED_GUARD"] == "GS_CELL_PROVENANCE_COLUMN_COVERAGE"
    assert record["EXPECTED_GUARD"] != reg.NONE_EXISTING
    assert record["EXPECTED_RESULT"] == reg.DETECTED
    assert record["SECONDARY_IC_APPLICABLE"] is False
    assert record["EXACT_DETECTION_SIGNAL"] != reg.NO_DETECTION_SIGNAL
    assert len(record["EXACT_DETECTION_SIGNAL"]) == 2

    leaked = record["COLUMNS_ADDED"][0]
    # The injected column is undeclared in BOTH frozen column-set declarations.
    assert leaked not in bcp.COLUMN_SPECS
    passports = json.loads(
        (REPO_ROOT / bcp.PASSPORTS_V1_REL).read_text(encoding="utf-8")
    )
    passport_names = {entry["name"] for entry in passports["passports"]}
    assert passports["schema_version"] == "1.0.0"
    assert leaked not in passport_names

    # The clean pinned source trips neither declaration: same 61 column names.
    import pandas as pd

    columns = list(pd.read_csv(DATASET_PATH, nrows=0).columns)
    assert len(columns) == reg.DATASET_COLUMN_COUNT
    assert set(columns) == set(bcp.COLUMN_SPECS) == passport_names
    assert "column-identical" in reg.CELL_PROVENANCE_SCHEMA_IS_COLUMN_IDENTICAL_ACROSS_DATASETS or (
        "same 61 column names"
        in reg.CELL_PROVENANCE_SCHEMA_IS_COLUMN_IDENTICAL_ACROSS_DATASETS
    )

    # The named validator surface for this class stays structurally unreachable
    # and is NOT repaired: detection comes from a different existing surface.
    assert reg.GUARD_SURFACES["GS_TARGET_LEAK_VALIDATE_ISSUE"]["reachability"] == (
        "STRUCTURALLY_UNREACHABLE"
    )
    assert reg.NO_GUARD_REPAIR_BEFORE_FIRST_DRAW is True
    assert reg.NO_NEW_GUARD_BEFORE_FIRST_DRAW is True
    assert "no guard was added or repaired" in record["DETECTING_SURFACE_RATIONALE"]


def test_input_blind_universe_surfaces_have_no_point_in_time_membership_record():
    for key in (
        "GS_UNIVERSE_SPLIT_TEST",
        "GS_UNIVERSE_VALIDATE_SCRIPT",
        "GS_UNIVERSE_SPLIT_LEAK",
        "GS_LEAKAGE_PIPELINE_TEST",
    ):
        assert reg.GUARD_SURFACES[key]["reachability"] == "INPUT_BLIND"
        assert str(reg.GUARD_SURFACES[key]["input_blindness_proof"]).strip()

    import pandas as pd

    public = pd.read_csv(REPO_ROOT / "data/config/universe_public_40.csv", comment="#")
    training = pd.read_csv(
        REPO_ROOT / "data/config/universe_training_bist100.csv", comment="#"
    )
    # No year dimension anywhere: no point-in-time membership record exists.
    assert "year" not in public.columns
    assert "year" not in training.columns

    record = reg.GUARD_MAP["LOOKAHEAD_UNIVERSE_MEMBERSHIP"]
    assert record["EXPECTED_GUARD"] == reg.NONE_EXISTING
    assert record["INPUT_BLIND_SURFACES_NOT_EVALUATED"] == (
        "GS_UNIVERSE_SPLIT_TEST",
        "GS_UNIVERSE_VALIDATE_SCRIPT",
        "GS_UNIVERSE_SPLIT_LEAK",
    )
    # The reachable provenance surfaces are evaluated for 4003, not excused as
    # input-blind.
    assert "GS_CELL_PROVENANCE_DUP_KEY" in record["EVALUATED_SURFACES"]
    assert "GS_CELL_PROVENANCE_COLUMN_COVERAGE" in record["EVALUATED_SURFACES"]
    assert record["NO_CANONICAL_DATASET_CHANGE"] is True


def test_duplicate_guard_signals_exist_verbatim_in_repository_source():
    record = reg.GUARD_MAP["DUPLICATE_ROW_INFLATION"]
    assert record["EXPECTED_GUARD"] == "GS_DUP_ALT_TARGETS"
    assert record["CONFIRMING_GUARD"] == "GS_DUP_VALIDATE_ISSUE"
    assert record["EXPECTED_RESULT"] == reg.DETECTED
    assert record["SECONDARY_IC_APPLICABLE"] is False

    alt_targets = (
        REPO_ROOT / "scripts/data_collection/derive_alternative_targets.py"
    ).read_text(encoding="utf-8")
    assert 'contains duplicate ticker/year keys' in alt_targets
    assert 'raise ValueError("modeling target_year must align exactly to year + 1")' in (
        alt_targets
    )

    validate_source = (
        REPO_ROOT / "scripts/data_collection/validate.py"
    ).read_text(encoding="utf-8")
    assert 'issues.append(f"{dup} duplicate ticker-year rows")' in validate_source
    assert 'df.duplicated(["ticker", "year"]).sum()' in validate_source

    # The registered fail-fast ordering is a structural fact of _load_modeling:
    # required columns, then duplicate keys, then target_year alignment.
    loader = ast.unparse(
        _function_def(
            REPO_ROOT / "scripts/data_collection/derive_alternative_targets.py",
            "_load_modeling",
        )
    )
    required_at = loader.index("is missing required columns")
    duplicate_at = loader.index("contains duplicate ticker/year keys")
    alignment_at = loader.index("modeling target_year must align exactly to year + 1")
    assert required_at < duplicate_at < alignment_at
    assert record["FAIL_FAST_SURFACE_NOT_EVALUATED"] == "GS_ALIGNMENT_ALT_TARGETS"


def test_alignment_surface_is_label_scoped_only():
    surface = reg.GUARD_SURFACES["GS_ALIGNMENT_ALT_TARGETS"]
    assert surface["condition"] == "not target_years.eq(years + 1).all()"
    assert "label arithmetic only" in surface["scope_limitation"]
    record = reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]
    assert "GS_ALIGNMENT_ALT_TARGETS" in record["EVALUATED_SURFACES"]
    assert record["EXPECTED_GUARD"] == reg.NONE_EXISTING
    assert record["COLUMNS_MODIFIED"] == ("next_year_return_pct",)
    assert reg.ALIGNMENT_COLUMN not in record["COLUMNS_MODIFIED"]


# --------------------------------------------------------------------------- #
# Injection mechanisms are exact and mutually distinct
# --------------------------------------------------------------------------- #
def test_registered_injection_mechanisms_are_frozen_without_being_executed():
    """Registration freezes each mechanism as text plus counts; it builds none.

    Constructing any of the five frames here would be executing a registered
    Stage 3 defect. The counts below are asserted to be well-formed prospective
    expectations, consistent with read-only facts of the frozen source; they are
    verified behaviorally by the Stage 3 implementation tests.
    """
    assert reg.REGISTRATION_TESTS_CONSTRUCT_INJECTED_FRAMES is False
    assert reg.FROZEN_INJECTION_COUNTS_ARE_PROSPECTIVE is True
    assert reg.BEHAVIORAL_INJECTION_TESTS_BELONG_TO_IMPLEMENTATION is True
    for phrase in (
        "construct the 4000 transformation",
        "construct the 4001 rotation",
        "construct the 4002 added leak column",
        "construct the 4003 membership selection",
        "construct the 4004 duplication",
        "execute any registered Stage 3 defect construction",
    ):
        assert phrase in reg.REGISTRATION_TESTS_MAY_NOT, phrase

    future_year = reg.GUARD_MAP["FUTURE_YEAR_FEATURE_LEAKAGE"]
    misalignment = reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]
    leakage = reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"]
    universe = reg.GUARD_MAP["LOOKAHEAD_UNIVERSE_MEMBERSHIP"]
    duplicates = reg.GUARD_MAP["DUPLICATE_ROW_INFLATION"]

    # 4000 — a row can only receive a future value if a T+1 partner exists, and
    # only a subset of those can actually change value.
    assert 0 < future_year["EXPECTED_ROWS_CHANGING_VALUE"] <= (
        future_year["EXPECTED_ROWS_RECEIVING_A_FUTURE_VALUE"]
    )
    assert future_year["EXPECTED_ROWS_RECEIVING_A_FUTURE_VALUE"] < (
        reg.DATASET_ROW_COUNT
    )
    assert future_year["COLUMNS_MODIFIED"] == ("total_assets",)

    # 4001 — a within-ticker rotation can change at most the observed rows.
    assert 0 < misalignment["EXPECTED_ROWS_CHANGING_VALUE"] <= (
        reg.DATASET_OBSERVED_TARGET_ROWS
    )
    assert misalignment["COLUMNS_MODIFIED"] == (reg.TARGET_COLUMN,)

    # 4002 — one added column, nothing modified.
    assert leakage["COLUMNS_MODIFIED"] == ()
    assert leakage["COLUMNS_ADDED"] == ("leaked_next_year_return_pct",)

    # 4003 — the membership partition is exhaustive over the frozen row count.
    assert universe["EXPECTED_MEMBER_ROWS"] + universe["EXPECTED_DROPPED_ROWS"] == (
        reg.DATASET_ROW_COUNT
    )
    assert universe["EXPECTED_MEMBER_ROWS"] > 0
    assert universe["EXPECTED_DROPPED_ROWS"] > 0
    assert universe["TIE_RULE"] == "median comparison is >= (ties are retained as members)"

    # 4004 — the duplicated block is exactly the minimum feature year.
    assert duplicates["COLUMNS_MODIFIED"] == ()
    assert f"{reg.DATASET_ROW_COUNT} clean rows plus {reg.DATASET_ROWS_AT_MIN_YEAR} " in (
        duplicates["ROW_UNIVERSE"]
    )
    assert "443 rows" in duplicates["ROW_UNIVERSE"]
    assert reg.DATASET_ROW_COUNT + reg.DATASET_ROWS_AT_MIN_YEAR == 443


def test_injection_classes_are_mutually_distinct():
    future_year = reg.GUARD_MAP["FUTURE_YEAR_FEATURE_LEAKAGE"]
    target_leak = reg.GUARD_MAP["TARGET_LEAKAGE_INTO_FEATURES"]
    misalignment = reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]
    duplicates = reg.GUARD_MAP["DUPLICATE_ROW_INFLATION"]

    # Future-year leakage is not target-column leakage.
    assert future_year["COLUMNS_MODIFIED"] == ("total_assets",)
    assert reg.TARGET_COLUMN not in future_year["COLUMNS_MODIFIED"]
    assert "DISTINCTNESS_FROM_TARGET_LEAKAGE" in future_year
    assert target_leak["COLUMNS_ADDED"] == ("leaked_next_year_return_pct",)
    assert future_year["EXACT_INJECTION_MECHANISM"] != (
        target_leak["EXACT_INJECTION_MECHANISM"]
    )

    # Misalignment is neither target leakage nor duplicate inflation.
    assert "not target leakage" in misalignment["DISTINCTNESS"]
    assert "not duplicate-row inflation" in misalignment["DISTINCTNESS"].lower()
    assert misalignment["COLUMNS_MODIFIED"] == (reg.TARGET_COLUMN,)
    assert duplicates["COLUMNS_MODIFIED"] == ()

    # Every mechanism string is unique.
    mechanisms = [
        record["EXACT_INJECTION_MECHANISM"] for record in reg.GUARD_MAP.values()
    ]
    assert len(set(mechanisms)) == 5


def test_derived_target_columns_are_frozen_as_not_recomputed():
    record = reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]
    assert record["DERIVED_TARGET_COLUMNS_NOT_RECOMPUTED"] == (
        "next_year_rank_by_return",
        "next_year_return_percentile",
        "next_year_top_10pct_returner",
        "next_year_top_20pct_returner",
        "next_year_excess_return_vs_bist100",
        "next_year_outperform_bist100",
    )
    assert "NOT" in record["DERIVED_COLUMN_RULE"]
    assert "No implementation may recompute them" in record["DERIVED_COLUMN_RULE"]


# --------------------------------------------------------------------------- #
# Containment
# --------------------------------------------------------------------------- #
def test_containment_boundary_forbids_canonical_mutation():
    assert reg.CONTAINMENT_MODES == (
        "IN_MEMORY_FRAME",
        "PRIVATE_TEMP_CSV",
        "VALIDATE_OUTPUT_REDIRECTION",
        "PRIVATE_PROVENANCE_ROOT",
    )
    for name, record in reg.GUARD_MAP.items():
        assert record["CONTAINMENT_BOUNDARY"], name
        for mode in record["CONTAINMENT_BOUNDARY"]:
            assert mode in reg.CONTAINMENT_MODES, name
        for surface_key in record["EVALUATED_SURFACES"]:
            requirement = reg.GUARD_SURFACES[surface_key].get(
                "containment_requirement"
            )
            if requirement is not None:
                assert requirement in record["CONTAINMENT_BOUNDARY"], (
                    name,
                    surface_key,
                    requirement,
                )
    for forbidden in (
        "data/trusted",
        "data/trusted_clean",
        "data/config",
        "experiments/results_thesis/positive_control",
        "experiments/results_thesis/positive_control_calibration",
        "experiments/results_thesis/negative_control",
    ):
        assert forbidden in reg.FORBIDDEN_MUTATION_TARGETS
    assert reg.CLEAN_COMPARATOR_FIRES_ANY_SIGNAL == "INCONCLUSIVE"
    assert isinstance(reg.RESTORATION_POLICY, str) and reg.RESTORATION_POLICY
    assert isinstance(reg.FAILURE_BEHAVIOR, str) and reg.FAILURE_BEHAVIOR


def test_duplicate_fail_fast_surface_accounting_is_reachable_and_complete():
    record = reg.GUARD_MAP["DUPLICATE_ROW_INFLATION"]
    assert record["EVALUATED_SURFACES"] == (
        "GS_REQUIRED_COLUMNS_ALT_TARGETS",
        "GS_DUP_ALT_TARGETS",
        "GS_DUP_VALIDATE_ISSUE",
        "GS_TARGET_LEAK_VALIDATE_ISSUE",
        "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
        "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
        "GS_CELL_PROVENANCE_DUP_KEY",
    )
    assert record["FAIL_FAST_SURFACE_NOT_EVALUATED"] == (
        "GS_ALIGNMENT_ALT_TARGETS"
    )
    assert "raises" in record["FAIL_FAST_REASON"]
    assert "before" in record["FAIL_FAST_REASON"]
    # The reachable provenance duplicate-key guard is a third confirming signal;
    # 4004's expected result is unchanged by the corrected classification.
    assert record["CONFIRMING_PROVENANCE_GUARD"] == "GS_CELL_PROVENANCE_DUP_KEY"
    assert len(record["EXACT_DETECTION_SIGNAL"]) == 3
    assert record["EXPECTED_RESULT"] == reg.DETECTED


def test_validate_output_redirection_is_registered_because_validate_writes():
    validate_source = (
        REPO_ROOT / "scripts/data_collection/validate.py"
    ).read_text(encoding="utf-8")
    # The redirection requirement exists because validate() really does write
    # into data/trusted_clean.
    assert "P.QUALITY_JSON.write_text(" in validate_source
    assert "P.QUALITY_MD.write_text(" in validate_source
    assert "FEATURE_JSON.write_text(" in validate_source
    assert "FEATURE_MD.write_text(" in validate_source
    assert reg.VALIDATE_REDIRECTED_ATTRIBUTES == (
        "scripts.data_collection.pipeline.QUALITY_JSON",
        "scripts.data_collection.pipeline.QUALITY_MD",
        "scripts.data_collection.validate.FEATURE_JSON",
        "scripts.data_collection.validate.FEATURE_MD",
    )
    assert reg.VALIDATE_READS_REFERENCE_CSV == "data/trusted/stocks_2020_2025.csv"
    assert reg.VALIDATE_REFERENCE_READ_IS_READ_ONLY is True
    for path in reg.CANONICAL_DIGESTS_REVERIFIED_AFTER_EACH_DEFECT:
        assert (REPO_ROOT / path).is_file(), path
    for surface_key in (
        "GS_DUP_VALIDATE_ISSUE",
        "GS_TARGET_LEAK_VALIDATE_ISSUE",
        "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
    ):
        assert reg.GUARD_SURFACES[surface_key]["containment_requirement"] == (
            "VALIDATE_OUTPUT_REDIRECTION"
        )


# --------------------------------------------------------------------------- #
# Decision rule, secondary metric, integrity contract, claim boundary
# --------------------------------------------------------------------------- #
def test_pass_fail_inconclusive_rules_are_literal(compact_registration_doc):
    assert reg.PASS_RULE == (
        "all five completed registered defects are detected by their "
        "preregistered existing guards"
    )
    assert reg.FAIL_RULE == (
        "at least one completed registered defect is not detected"
    )
    assert "integrity, containment, execution, or completeness" in reg.INCONCLUSIVE_RULE
    assert reg.INTEGRITY_PRECEDES_SCIENTIFIC_DECISION is True
    assert reg.INCONCLUSIVE_TAKES_PRECEDENCE_OVER_PASS_FAIL is True
    assert reg.DETECTION_MUST_PRECEDE_MODEL_EVALUATION is True
    assert reg.PRIMARY_GATE_INDEPENDENT_OF == (
        "model performance",
        "IC threshold",
        "p-values",
        "permutation significance",
        "multiplicity",
    )
    for phrase in (
        "PASS — all five completed registered defects are detected",
        "FAIL — at least one completed registered defect is not detected",
        "INCONCLUSIVE — at least one registered defect cannot be evaluated",
        "Integrity and INCONCLUSIVE take precedence",
    ):
        assert phrase in compact_registration_doc, phrase


def test_secondary_ic_is_descriptive_non_gating_and_scope_limited(
    compact_registration_doc,
):
    assert reg.SECONDARY_METRIC_APPLIES_ONLY_TO_UNDETECTED_DEFECTS is True
    assert reg.SECONDARY_METRIC_IS_GATING is False
    assert reg.SECONDARY_METRIC_STATUS == "NON-GATING / DESCRIPTIVE ONLY"
    assert reg.SECONDARY_METRIC_MODEL == "ridge"
    assert dict(reg.SECONDARY_METRIC_MODEL_PARAMETERS) == {"alpha": 1.0}
    assert reg.SECONDARY_METRIC_TARGET == reg.TARGET_COLUMN
    assert reg.SECONDARY_METRIC_IMPUTATION == "NaN -> 0.5"
    assert reg.SECONDARY_METRIC_RANK_METHOD == "average"
    assert reg.SECONDARY_METRIC_SPLIT_SOURCE == "experiments/run_experiments.py"
    assert reg.SECONDARY_METRIC_FORBIDDEN == (
        "p-value",
        "significance test",
        "multiplicity correction",
        "predictive-edge inference",
    )
    assert reg.SECONDARY_METRIC_CORRELATION == (
        "Spearman(prediction, observed target)"
    )
    assert reg.SECONDARY_METRIC_DISTORTION_FORMULA == (
        "delta_ic(split) = injected_ic(split) - clean_ic(split)"
    )
    assert reg.SECONDARY_METRIC_IS_PER_SPLIT is True
    assert reg.SECONDARY_METRIC_HAS_CROSS_SPLIT_AGGREGATE is False
    assert "no pooling across splits or defects" in (
        reg.SECONDARY_METRIC_REPORTING_SCOPE
    )
    names = tuple(split["name"] for split in reg.SECONDARY_METRIC_SPLITS)
    assert names == ("test_2023", "test_2024", "test_2025")

    # The registered splits EQUAL the repository's canonical walk-forward
    # splits exactly: same names, same order, same fields. Not a subset.
    from experiments import run_experiments as canonical

    def normalize(split: dict) -> tuple:
        assert set(split) == set(reg.SECONDARY_METRIC_SPLIT_FIELDS), split
        return (
            split["name"],
            tuple(split["train_target_years"]),
            split["test_feature_year"],
        )

    source_splits = [normalize(split) for split in canonical.SPLITS]
    registered = [normalize(dict(split)) for split in reg.SECONDARY_METRIC_SPLITS]
    assert registered == source_splits
    assert len(registered) == reg.SECONDARY_METRIC_SPLIT_COUNT == 3
    assert len(source_splits) == len(set(source_splits))
    assert reg.SECONDARY_METRIC_SPLITS_EQUAL_CANONICAL_SPLITS_EXACTLY is True
    assert reg.SECONDARY_METRIC_SPLIT_SYMBOL == "experiments.run_experiments.SPLITS"

    # Applicability follows detection expectation exactly.
    for name, record in reg.GUARD_MAP.items():
        expected_applicable = record["EXPECTED_RESULT"] == reg.NOT_DETECTED
        assert record["SECONDARY_IC_APPLICABLE"] is expected_applicable, name
    assert "NON-GATING and DESCRIPTIVE ONLY" in compact_registration_doc
    assert reg.SECONDARY_METRIC_DISTORTION_FORMULA in compact_registration_doc
    assert "no pooling across splits or defects" in compact_registration_doc


def test_run_experiments_is_pinned_by_full_sha256(compact_registration_doc):
    """The secondary IC depends on this source, so it is pinned exactly."""
    relative = reg.RUN_EXPERIMENTS_SOURCE
    assert relative == "experiments/run_experiments.py"
    path = REPO_ROOT / relative
    assert path.is_file()

    # Full literal, never abbreviated.
    assert len(reg.RUN_EXPERIMENTS_SHA256) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", reg.RUN_EXPERIMENTS_SHA256)
    assert sha256(path) == reg.RUN_EXPERIMENTS_SHA256
    assert reg.RUN_EXPERIMENTS_UNCHANGED_FROM_AUTHORITATIVE_BASE is True
    assert reg.RUN_EXPERIMENTS_IS_SECONDARY_CONSUMER_AUTHORITY is True

    # The same pin backs the split source and is written out in full in the doc.
    assert reg.SECONDARY_METRIC_SPLIT_SOURCE == relative
    assert reg.SECONDARY_METRIC_SPLIT_SOURCE_SHA256 == reg.RUN_EXPERIMENTS_SHA256
    assert reg.SOURCE_MODULE_HASHES[relative] == reg.RUN_EXPERIMENTS_SHA256
    assert reg.RUN_EXPERIMENTS_SHA256 in compact_registration_doc


def test_4001_consumer_boundary_holds_against_repository_authority():
    """Stale derived targets cannot reach the estimand — proved from source."""
    from experiments import run_experiments as canonical

    boundary = reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]["CONSUMER_BOUNDARY"]
    assert boundary is reg.CONSUMER_BOUNDARY_4001
    assert reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"][
        "STALE_COLLATERAL_IS_FORBIDDEN_FROM_THE_ESTIMAND"
    ] is True

    # The registered injection is unchanged: rotate the primary target only.
    assert reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"]["COLUMNS_MODIFIED"] == (
        reg.PRIMARY_TARGET_COLUMN,
    )
    assert reg.GUARD_MAP["T_TPLUS1_MISALIGNMENT"][
        "DERIVED_TARGET_COLUMNS_NOT_RECOMPUTED"
    ] == reg.STALE_DERIVED_TARGET_COLUMNS
    assert reg.STALE_COLLATERAL_FORBIDDEN_ROLES == (
        "predictor",
        "alternate target",
        "alignment authority",
        "detection signal",
        "secondary IC input",
    )
    assert boundary["VIOLATION_RESULT"] == reg.INCONCLUSIVE == "INCONCLUSIVE"

    # (a) Canonical predictor selection excludes every next_year_* column. The
    # filter is a pure name rule; proved by AST, not by a source substring.
    feature_cols = _function_def(REPO_ROOT / reg.RUN_EXPERIMENTS_SOURCE, "_feature_cols")
    comprehensions = [
        node for node in ast.walk(feature_cols) if isinstance(node, ast.ListComp)
    ]
    assert len(comprehensions) == 1
    (condition,) = comprehensions[0].generators[0].ifs
    assert isinstance(condition, ast.BoolOp) and isinstance(condition.op, ast.And)
    assert len(condition.values) == 2
    membership, prefix = condition.values
    assert isinstance(membership, ast.Compare)
    assert isinstance(membership.ops[0], ast.NotIn)
    assert isinstance(prefix, ast.UnaryOp) and isinstance(prefix.op, ast.Not)
    assert isinstance(prefix.operand, ast.Call)
    assert prefix.operand.func.attr == "startswith"
    assert prefix.operand.args[0].value == "next_year_"

    # (b) Every registered next_year_* column is therefore excluded by name,
    # including the primary target and all six stale derived targets.
    from scripts.data_collection import pipeline as pipeline_module

    next_year_columns = [
        column
        for column in pipeline_module.TARGET_COLS
        if column.startswith("next_year_")
    ]
    assert set(reg.STALE_DERIVED_TARGET_COLUMNS) < set(next_year_columns)
    assert reg.PRIMARY_TARGET_COLUMN in next_year_columns
    for column in next_year_columns:
        assert column.startswith("next_year_")
    assert reg.NO_NEXT_YEAR_COLUMN_MAY_BE_A_PREDICTOR is True

    # (c) The secondary target is exactly next_year_return_pct and the
    # registered secondary path selects no alternate target.
    assert reg.SECONDARY_METRIC_TARGET == reg.PRIMARY_TARGET_COLUMN
    assert reg.TARGET_COLUMN == reg.PRIMARY_TARGET_COLUMN
    assert reg.SECONDARY_METRIC_TARGET_SELECTOR == (
        "experiments.run_experiments.build_panel_for_target("
        "target_col='next_year_return_pct', target_path=None)"
    )
    assert reg.SECONDARY_METRIC_FORBIDDEN_TARGETS == reg.STALE_DERIVED_TARGET_COLUMNS
    for forbidden in reg.SECONDARY_METRIC_FORBIDDEN_TARGETS:
        assert forbidden != reg.SECONDARY_METRIC_TARGET
        assert forbidden in canonical.TARGETS or forbidden.startswith("next_year_")
    assert reg.SECONDARY_METRIC_ALTERNATIVE_TARGET_TABLE_FORBIDDEN is True

    # (d) The canonical target-parameterized entry point exists, takes the
    # target as an explicit argument, and defaults its alternative-target table
    # to None — so pinning the argument fully determines the target. The
    # multi-target TARGETS iteration lives in _eval_target, which the registered
    # secondary path does not use.
    panel_builder = _function_def(
        REPO_ROOT / reg.RUN_EXPERIMENTS_SOURCE, "build_panel_for_target"
    )
    assert [argument.arg for argument in panel_builder.args.args] == [
        "target_col",
        "target_path",
    ]
    assert len(panel_builder.args.defaults) == 1
    assert panel_builder.args.defaults[0].value is None
    body = ast.unparse(panel_builder)
    assert "TARGETS" not in body
    for forbidden in reg.STALE_DERIVED_TARGET_COLUMNS:
        assert forbidden not in body
    eval_target = ast.unparse(
        _function_def(REPO_ROOT / reg.RUN_EXPERIMENTS_SOURCE, "_eval_target")
    )
    assert "build_panel_for_target(target_col)" in eval_target

    # (e) Derived target columns are not feature inputs anywhere in the
    # registered secondary path: the only feature selector is _feature_cols.
    assert reg.SECONDARY_METRIC_FEATURE_SELECTOR == (
        "experiments.run_experiments._feature_cols"
    )
    assert "_feature_cols(m)" in body


def test_closed_integrity_contract_and_exclusions(compact_registration_doc):
    assert len(reg.INTEGRITY_CONDITION_IDENTIFIERS) == 17
    assert len(set(reg.INTEGRITY_CONDITION_IDENTIFIERS)) == 17
    assert set(reg.INTEGRITY_CONDITION_DESCRIPTIONS) == set(
        reg.INTEGRITY_CONDITION_IDENTIFIERS
    )
    for required in (
        "frozen_source_dataset_path_and_sha_match",
        "registered_stage3_module_hashes_match",
        "exactly_five_registered_defect_ids",
        "no_duplicate_defect_ids_or_defect_names",
        "correct_seed_schedule",
        "no_forbidden_id_overlap",
        "writes_confined_to_stage3_result_namespace",
        "stage1_stage1b_stage2_result_roots_untouched",
        "no_trusted_data_or_config_mutation",
        "no_source_module_mutation",
        "injection_containment_restored_after_each_defect",
        "clean_comparator_byte_and_logical_identity",
        "expected_guard_mapping_evaluated_exactly_once",
        "no_defect_silently_omitted",
        "secondary_ic_only_on_undetected_defects",
        "no_invalid_evaluation_converted_to_non_detection",
        "deterministic_replay_contract",
    ):
        assert required in reg.INTEGRITY_CONDITION_IDENTIFIERS
        assert required in compact_registration_doc
    assert reg.INTEGRITY_EVALUATED_BEFORE_SCIENTIFIC_GATE is True
    assert reg.GUARD_GAP_IS_VALID_SCIENCE is True
    assert reg.GOVERNED_RUN_IMPLEMENTATION_NOT_INVENTED_AT_REGISTRATION is True
    assert reg.REPLAY_IMPLEMENTATION_NOT_REGISTERED is True
    for exclusion in reg.INTEGRITY_EXCLUSIONS:
        assert exclusion in compact_registration_doc


def test_claim_boundary_is_explicit(compact_registration_doc):
    assert reg.CLAIM_BOUNDARY[0].startswith(
        "Stage 3 may establish only whether the preregistered existing guard map"
    )
    for phrase in (
        "absence of all leakage",
        "universal pipeline safety",
        "predictive edge",
        "alpha",
        "investment value",
        "production readiness",
        "correctness of expanded datasets",
        "correctness of future unknown defect classes",
    ):
        assert any(phrase in claim for claim in reg.CLAIM_BOUNDARY), phrase
        assert phrase in compact_registration_doc, phrase
    assert (
        "A FAIL is informative and expected if existing guard gaps are real."
        in reg.CLAIM_BOUNDARY
    )
    assert "Research support only; not investment advice." in reg.CLAIM_BOUNDARY
    assert "not investment advice" in compact_registration_doc


# --------------------------------------------------------------------------- #
# Stage 7 gate
# --------------------------------------------------------------------------- #
def test_stage7_remains_blocked_under_existing_wording(protocol_doc):
    assert reg.STAGE_1_STATUS == "FAILED AS WRITTEN — INFORMATIVE"
    assert reg.STAGE_7_REMAINS_BLOCKED is True
    assert reg.STAGE_3_DOES_NOT_UNLOCK_STAGE_7 is True
    assert reg.STAGE_7_REINTERPRETATION_REQUIRES_SEPARATE_PROSPECTIVE_GOVERNANCE is True
    assert reg.STAGE_7_EXISTING_WORDING == "Only after stages 1–3 pass"

    # The original Stage 7 wording is still present and was not amended.
    stage7_index = protocol_doc.index("## Stage 7 — BIST signal search (gated)")
    body = protocol_doc[stage7_index : protocol_doc.index("## Amendments")]
    assert "Only after stages 1–3 pass" in body
    amendment = protocol_doc[protocol_doc.index(STAGE3_AMENDMENT_MARKER) :]
    assert "Stage 3 does not silently unlock Stage 7" in amendment
    assert "remains authoritative and is not amended" in compact(amendment)
    assert "FAILED AS WRITTEN — INFORMATIVE" in amendment


def test_protocol_amendment_is_dated_and_appended_after_the_stage3_body(protocol_doc):
    marker_bytes = STAGE3_AMENDMENT_MARKER.encode("utf-8")
    protocol_bytes = protocol_doc.encode("utf-8")
    boundary_marker = b"\n\n" + marker_bytes + b"\n"
    assert protocol_bytes.count(boundary_marker) == 1
    boundary = protocol_bytes.index(boundary_marker)
    authoritative_prefix = protocol_bytes[: boundary + 1]
    assert hashlib.sha256(authoritative_prefix).hexdigest() == (
        AUTHORITATIVE_PROTOCOL_PREFIX_SHA256
    )
    appended_suffix = protocol_bytes[boundary + 1 :]
    assert appended_suffix.startswith(b"\n" + marker_bytes + b"\n")

    assert STAGE3_AMENDMENT_MARKER in protocol_doc
    assert protocol_doc.index("## Stage 3 — Defect-injection matrix") < (
        protocol_doc.index(STAGE3_AMENDMENT_MARKER)
    )
    assert protocol_doc.index("## Amendments") < protocol_doc.index(
        STAGE3_AMENDMENT_MARKER
    )
    # The Stage 2 amendment stays above the Stage 3 amendment; nothing is rewritten.
    assert protocol_doc.index(
        "### 2026-09-02 — Stage 2 dated amendment and registration"
    ) < protocol_doc.index(STAGE3_AMENDMENT_MARKER)
    # The original Stage 3 stage entry is intact.
    stage3_body = protocol_doc[
        protocol_doc.index("## Stage 3 — Defect-injection matrix") : protocol_doc.index(
            "## Stage 4 — External known-signal calibration"
        )
    ]
    assert "Pass requires **100% detection**" in stage3_body
    assert "Stop and repair the guard." in stage3_body

    amendment = protocol_doc[protocol_doc.index(STAGE3_AMENDMENT_MARKER) :]
    for phrase in (
        "The old block is not silently rewritten",
        "No Stage 3 injection has been constructed",
        "c418563f432f5b253fb3b0e69619c76608ea15ea",
        "NONE_EXISTING",
        "NO_RNG",
        "NON-GATING and DESCRIPTIVE ONLY",
        "not investment advice",
    ):
        assert phrase in amendment, phrase

    # The corrected registration is reflected in the amendment itself, not in a
    # fabricated post-registration history: the amendment predates any draw.
    compact_amendment = compact(amendment)
    for phrase in (
        "Three of the five defects are preregistered as NOT_DETECTED",
        "expected first-draw guard gaps are therefore exactly 4000, 4001, and 4003",
        "4000 NOT_DETECTED, 4001 NOT_DETECTED, 4002 DETECTED, 4003 NOT_DETECTED, "
        "4004 DETECTED",
        "is a reachable provenance/integrity guard, not an input-blind one",
        "PRIVATE_PROVENANCE_ROOT",
        "remains STRUCTURALLY_UNREACHABLE and is recorded as a separate, "
        "existing-but-useless guard-surface fact",
        "They construct no injected frame",
        reg.RUN_EXPERIMENTS_SHA256,
        "must equal experiments.run_experiments.SPLITS exactly",
        "remain stale collateral",
        "classifies 4001 INCONCLUSIVE",
    ):
        assert phrase in compact_amendment, phrase
    assert "Four of the five defects are preregistered" not in compact_amendment
    assert reg.EXPECTED_FIRST_DRAW_OUTCOME in amendment


# --------------------------------------------------------------------------- #
# Registration/implementation boundary
# --------------------------------------------------------------------------- #
def test_completed_result_root_and_historical_registration_absence_are_preserved(
    registration_doc,
):
    assert reg.RESULT_ROOT == "experiments/results_thesis/defect_injection/"
    assert reg.RESULT_ROOT_EXISTS_AT_REGISTRATION is False
    assert reg.STAGE3_RESULT_EXISTS_AT_REGISTRATION is False
    assert reg.NO_STAGE3_INJECTION_DRAW_OR_OUTCOME is True
    assert RESULT_ROOT.is_dir()
    assert {path.name for path in RESULT_ROOT.iterdir()} == {
        *STAGE3_RESULT_FILENAMES,
        "attempts",
    }
    assert (RESULT_ROOT / "attempts" / "attempt-1.json").is_file()
    assert not (RESULT_ROOT / ".staging").exists()
    assert (
        "experiments/results_thesis/defect_injection/ does not exist at registration time"
        in compact(registration_doc)
    )
    assert sorted(REPO_ROOT.glob("experiments/thesis/stage3_*.py")) == [REGISTRATION_SOURCE]
    implementation_source = REPO_ROOT / "experiments/thesis/defect_injection.py"
    assert implementation_source.is_file()
    assert REGISTRATION_SOURCE.is_file()

    makefile = MAKEFILE.read_text(encoding="utf-8")
    for target in (
        "thesis-stage3:",
        "thesis-stage3-replay:",
        "thesis-stage3-repeat-after-crash:",
    ):
        assert target in makefile
    assert "defect_injection.py --run" in makefile
    assert "defect_injection.py --replay-check" in makefile
    assert "defect_injection.py --repeat-after-crash" in makefile
    assert reg.NO_MAKEFILE_RUN_TARGET_AT_REGISTRATION is True

    assert reg.STAGE3_SLUG in prov.EXPERIMENT_SLUGS
    assert (prov.THESIS_RESULTS_ROOT / reg.STAGE3_SLUG).is_dir()


def test_registry_has_stage3_completed_output_contracts_and_no_prospective_outputs():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    root = reg.RESULT_ROOT.rstrip("/")
    assert root in registry["governed_roots"]
    expected_paths = (
        f"{root}/defect_injection_report.json",
        f"{root}/defect_injection_report.md",
        f"{root}/defect_results.csv",
        f"{root}/artifact_manifest.json",
        f"{root}/attempts/*.json",
    )
    completed = [
        entry
        for entry in registry["entries"]
        if entry["path_or_glob"].startswith(root + "/")
    ]
    assert tuple(entry["path_or_glob"] for entry in completed) == expected_paths
    assert registry["prospective_entries"] == []
    assert len(completed) == len(expected_paths)
    for entry in completed:
        assert set(entry) == {
            "path_or_glob",
            "artifact_class",
            "generator_command",
            "inputs",
            "hand_edit_forbidden",
            "notes",
        }
        if entry["path_or_glob"].endswith("attempts/*.json"):
            assert entry["artifact_class"] == "run_manifest"
        else:
            assert entry["artifact_class"] == "generated"
        assert entry["generator_command"] == "make thesis-stage3"
        assert entry["hand_edit_forbidden"] is True
        assert entry["notes"].strip()
        if entry["path_or_glob"].endswith("attempts/*.json"):
            assert entry["inputs"] == []
        else:
            assert entry["inputs"] == [reg.DATASET_PATH]
    assert RESULT_ROOT.is_dir()
    assert {
        path.name for path in RESULT_ROOT.iterdir() if path.is_file()
    } == set(STAGE3_RESULT_FILENAMES)
    assert (RESULT_ROOT / "attempts" / "attempt-1.json").is_file()
    assert not (RESULT_ROOT / ".staging").exists()
    assert reg.NO_GOVERNED_ROOT_OR_PROSPECTIVE_ENTRY_AT_REGISTRATION is True
    assert reg.PROSPECTIVE_ARTIFACT_CONTRACTS_REQUIRED_AT_REGISTRATION is False
    assert reg.PROSPECTIVE_ARTIFACT_CONTRACT_STATUS_AT_REGISTRATION == (
        "NOT_REQUIRED_AT_REGISTRATION"
    )
    assert reg.IMPLEMENTATION_MUST_ADD_RUNNER_TARGET_AND_OWNERSHIP_BEFORE_RUN is True


def test_readme_and_task_ledger_record_post_run_state():
    readme = compact(THESIS_README.read_text(encoding="utf-8"))
    for phrase in (
        "Stage 3 (defect_injection) is registered, implemented, and has completed exactly one governed first draw",
        "Stage 3 — first governed draw complete; integrity INCONCLUSIVE",
        "five-class family remains frozen",
        "first governed draw occurred exactly once",
        "attempt-1 is complete",
        "original authoritative decision is INCONCLUSIVE",
        "clean_comparator_byte_and_logical_identity",
        "fingerprint/accounting chained-comparison defect",
        "31643f19d58639b6aa4575625b4460dbdb4ab9b8",
        "FAIL — INFORMATIVE",
        reg.DATASET_PATH,
        reg.DATASET_SHA256,
        "completed result namespace",
        "defect_injection.py",
        "make thesis-stage3",
        "prospective_entries[]",
        "private provenance root",
        "4001",
        "Stage 7 remains blocked",
        "not investment advice",
        "second governed draw is forbidden",
        "R2 accounting-only remediation is planned but NOT YET REGISTERED",
        "The registration tests construct no injected frame",
    ):
        assert phrase in readme, phrase
    # 4002 is no longer described as an expected guard gap anywhere.
    assert "4000–4003 (NOT_DETECTED)" not in readme
    assert "guard gaps for 4000–4003" not in readme

    ledger = compact(TASK_STATE.read_text(encoding="utf-8"))
    registration_marker = "FINANCEIQ-THESIS-STAGE3-REGISTRATION-CLOSEOUT"
    implementation_marker = "FINANCEIQ-THESIS-STAGE3-IMPLEMENTATION-ONLY"
    post_run_marker = "FINANCEIQ-THESIS-STAGE3-POST-RUN-GOVERNANCE-TRANSITION"
    assert registration_marker in ledger
    assert implementation_marker in ledger
    assert post_run_marker in ledger
    entry = ledger[ledger.rindex(post_run_marker) :]
    for phrase in (
        "first governed Stage 3 draw occurred exactly once",
        "attempt_number=1",
        "attempt_type=initial",
        "status=complete",
        "prior_incomplete_attempt=false",
        "original authoritative decision is INCONCLUSIVE",
        "clean_comparator_byte_and_logical_identity",
        "4000 FUTURE_YEAR_FEATURE_LEAKAGE",
        "4001 T_TPLUS1_MISALIGNMENT",
        "4002 TARGET_LEAKAGE_INTO_FEATURES",
        "4003 LOOKAHEAD_UNIVERSE_MEMBERSHIP",
        "4004 DUPLICATE_ROW_INFLATION",
        reg.DATASET_SHA256,
        "observed matrix matches the prospective expectation map",
        "does not override the failed integrity condition",
        "fingerprint/accounting chained-comparison defect",
        "31643f19d58639b6aa4575625b4460dbdb4ab9b8",
        "No second governed draw is authorized",
        "--repeat-after-crash remains forbidden",
        "R2 accounting-only remediation is planned but NOT YET REGISTERED",
        "Stage 7 remains BLOCKED",
    ):
        assert phrase in entry, phrase
    assert "4000–4003 NOT_DETECTED" not in entry
    assert "(4000–4003 NOT_DETECTED)" not in entry


def test_registration_tests_construct_no_injected_frame():
    """This module may read the frozen dataset; it may never mutate a frame.

    Proved structurally against this file's own AST: nothing read from a CSV is
    ever written to, and none of the frame-construction APIs the five
    registered injections require is called anywhere in the module.
    """
    own_path = Path(__file__).resolve()
    tree = ast.parse(own_path.read_text(encoding="utf-8"), filename=str(own_path))

    frame_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr in {"read_csv", "read_json", "DataFrame"}
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    frame_names.add(target.id)
    # Read-only frozen-source reads are allowed and really do occur here.
    assert frame_names

    # No value read from a dataset is ever assigned into or mutated.
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Subscript) and isinstance(
                    target.value, ast.Name
                ):
                    assert target.value.id not in frame_names, ast.dump(target)
                if isinstance(target, ast.Attribute) and isinstance(
                    target.value, ast.Name
                ):
                    assert target.value.id not in frame_names, ast.dump(target)

    # None of the five registered constructions can be expressed without one of
    # these APIs on a frame or on the dataframe libraries themselves; none of
    # them is called here.
    forbidden_calls = {
        "roll",
        "concat",
        "copy",
        "assign",
        "where",
        "merge",
        "transform",
        "rename",
        "to_csv",
        "drop",
        "append",
        "reindex",
        "sort_values",
        "loc",
        "iloc",
    }
    frame_like = frame_names | {"pd", "pandas", "np", "numpy"}
    violations = set()
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
            continue
        receiver = node.func.value
        if isinstance(receiver, ast.Name) and receiver.id in frame_like:
            if node.func.attr in forbidden_calls:
                violations.add(f"{receiver.id}.{node.func.attr}")
    assert not violations, sorted(violations)

    # Nothing in this module names the pandas/numpy frame constructors either,
    # so no injected frame can be assembled from literals.
    constructors = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            receiver = node.func.value
            if isinstance(receiver, ast.Name) and receiver.id in {
                "pd",
                "pandas",
                "np",
                "numpy",
            }:
                constructors.add(f"{receiver.id}.{node.func.attr}")
    assert constructors <= {"pd.read_csv"}, sorted(constructors)
    assert reg.REGISTRATION_TESTS_CONSTRUCT_INJECTED_FRAMES is False


def test_registration_source_has_no_scientific_execution_path():
    source = REGISTRATION_SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(REGISTRATION_SOURCE))
    imported_modules = []
    calls = []
    has_main_guard = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Compare)
                and isinstance(node.test.left, ast.Name)
                and node.test.left.id == "__name__"
            ):
                has_main_guard = True

    assert imported_modules == ["__future__", "types"]
    assert not has_main_guard
    assert not set(imported_modules) & {
        "numpy",
        "pandas",
        "scipy",
        "sklearn",
        "subprocess",
        "random",
        "pathlib",
        "os",
    }
    assert not set(calls) & {
        "open",
        "read_text",
        "read_bytes",
        "write_text",
        "write_bytes",
        "mkdir",
        "unlink",
        "rmdir",
        "rmtree",
        "run",
        "system",
        "exec",
        "eval",
        "output_dir",
        "read_csv",
        "to_csv",
    }
    assert not hasattr(reg, "main")
    assert reg.REGISTRATION_ONLY is True
    # The only callables are the pure seed helper and the frozen-mapping wrapper.
    assert set(calls) <= {"MappingProxyType", "tuple", "range"}


def test_registration_import_is_filesystem_inert():
    tracked = [
        DATASET_PATH,
        REGISTRATION_SOURCE,
        REGISTRATION_DOC,
        PROTOCOL_DOC,
        REGISTRY_PATH,
        MAKEFILE,
    ]
    tracked.extend(REPO_ROOT / relative for relative in reg.SOURCE_MODULE_HASHES)
    tracked.extend(
        REPO_ROOT / relative
        for relative in reg.CANONICAL_DIGESTS_REVERIFIED_AFTER_EACH_DEFECT
    )
    before = {path: sha256(path) for path in tracked}

    historical_roots = (
        REPO_ROOT / "experiments/results_thesis/positive_control",
        REPO_ROOT / "experiments/results_thesis/positive_control_calibration",
        REPO_ROOT / "experiments/results_thesis/negative_control",
    )

    def inventory() -> dict[str, str]:
        return {
            item.relative_to(REPO_ROOT).as_posix(): sha256(item)
            for root in historical_roots
            for item in sorted(root.rglob("*"))
            if item.is_file()
        }

    historical_before = inventory()
    assert historical_before
    completed_before = result_tree_hashes()

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [sys.executable, "-c", "import experiments.thesis.stage3_registration"],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )

    assert {path: sha256(path) for path in tracked} == before
    assert inventory() == historical_before
    assert result_tree_hashes() == completed_before
    assert RESULT_ROOT.is_dir()


def test_stage1_stage1b_stage2_registrations_and_provenance_are_unchanged():
    assert dict(reg.HISTORICAL_PROTECTED_HASHES) == {
        "experiments/significance.py": (
            "08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3"
        ),
        "experiments/thesis/negative_control.py": (
            "39a396630c6a753fb645d4315b274eaac8e928d3cbc500d059e0fd8d32224833"
        ),
        "experiments/thesis/stage2_registration.py": (
            "295e69ee09c2d7f6900efbbd79ee2c224e05830ace3abf98170b3c5bea33faef"
        ),
    }
    for relative, expected in reg.HISTORICAL_PROTECTED_HASHES.items():
        assert sha256(REPO_ROOT / relative) == expected, relative

    # Stage 3 registration adds a slug-free contract: provenance already
    # declared the slug and seed in the frozen source pins.
    assert sha256(REPO_ROOT / "experiments/thesis/provenance.py") == (
        reg.SOURCE_MODULE_HASHES["experiments/thesis/provenance.py"]
    )
    assert prov.SEEDS["defect_injection"] == 42
    assert "defect_injection" in prov.EXPERIMENT_SLUGS

    # These historical registration and artifact files are also protected by
    # literal hashes; no historical Git object is needed to enforce them.
    for relative, expected in HISTORICAL_UNCHANGED_HASHES.items():
        path = REPO_ROOT / relative
        assert path.is_file(), relative
        assert sha256(path) == expected, relative

# --------------------------------------------------------------------------- #
# Code / document coherence
# --------------------------------------------------------------------------- #
def test_registration_doc_matches_the_registration_module(compact_registration_doc):
    for name, record in reg.GUARD_MAP.items():
        assert f"{record['DEFECT_ID']} — {name}" in compact_registration_doc

    for surface_key in reg.GUARD_SURFACES:
        assert surface_key in compact_registration_doc, surface_key

    for defect_id, seed in reg.STAGE3_SEED_VALUES.items():
        assert str(seed) in compact_registration_doc, seed
        assert str(defect_id) in compact_registration_doc

    for literal in (
        reg.STAGE3_SEED_FORMULA,
        reg.RESULT_ROOT,
        reg.STAGE3_SLUG,
        reg.NONE_EXISTING,
        reg.NO_RNG,
        reg.EXPECTED_FIRST_DRAW_OUTCOME,
        reg.AUTHORITATIVE_BASE_COMMIT,
    ):
        assert literal in compact_registration_doc, literal

    for state in reg.REACHABILITY_STATES:
        assert state in compact_registration_doc, state

    assert compact("**Status: REGISTRATION ONLY.**") in compact_registration_doc
    assert (
        "experiments/results_thesis/defect_injection/ does not exist at "
        "registration time" in compact_registration_doc
    )


def test_owner_locks_are_reflected_literally(compact_registration_doc):
    for lock in ("D1 —", "D2 —", "D3 —", "D4 —", "D5 —", "D6 —"):
        assert lock in compact_registration_doc, lock
    for phrase in (
        "No new guard may be added before the first governed Stage 3 draw",
        "no guard gap is repaired before the first draw",
        "Any later repair belongs to a separate remediation stage",
        "historical first-draw artifacts remain immutable",
        "exactly one injection per class",
        "no severity grid",
        "no repeated performance experiment",
        "Detection counts only if a preregistered existing guard fires",
        "Only after stages 1–3 pass",
    ):
        assert phrase in compact_registration_doc, phrase


def test_registration_doc_has_no_unresolved_placeholder():
    text = REGISTRATION_DOC.read_text(encoding="utf-8")
    assert not re.search(r"\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b", text)
    assert not re.search(r"\bTODO\b|\bTBD\b|\bFIXME\b", REGISTRATION_SOURCE.read_text(
        encoding="utf-8"
    ))
