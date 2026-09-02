"""Machine-checkable guards for the Stage 2 prospective registration.

These tests validate the registration contract only. They do not implement or
run Stage 2, create its future result root, generate a repetition, or modify
historical Stage 1/Stage 1b artifacts.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pytest

from experiments import run_experiments as canonical
from experiments import significance as sig
from experiments.thesis import provenance as prov
from experiments.thesis import stage2_registration as reg


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_DOC = REPO_ROOT / reg.REGISTRATION_DOC
PROTOCOL_DOC = REPO_ROOT / reg.PROTOCOL_DOC
REGISTRATION_SOURCE = REPO_ROOT / "experiments/thesis/stage2_registration.py"
RESULT_ROOT = REPO_ROOT / reg.RESULT_ROOT.rstrip("/")
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
DATASET_PATH = REPO_ROOT / reg.DATASET_PATH
SIGNIFICANCE_PATH = REPO_ROOT / "experiments/significance.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_split(value: dict) -> tuple[str, tuple[int, ...], int]:
    return (
        value["name"],
        tuple(value["train_target_years"]),
        value["test_feature_year"],
    )


def binomial_upper_tail(n: int, p: float, lower: int) -> float:
    return sum(
        math.comb(n, successes)
        * p**successes
        * (1.0 - p) ** (n - successes)
        for successes in range(lower, n + 1)
    )


def compact(value: str) -> str:
    return " ".join(value.replace("**", "").split())


@pytest.fixture(scope="module")
def registration_doc() -> str:
    return REGISTRATION_DOC.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def protocol_doc() -> str:
    return PROTOCOL_DOC.read_text(encoding="utf-8")


def test_authoritative_hashes_are_exact_and_current():
    assert reg.SIGNIFICANCE_SHA256 == (
        "08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3"
    )
    assert reg.REPAIRED_SIGNIFICANCE_SHA256 == reg.SIGNIFICANCE_SHA256
    assert sha256(SIGNIFICANCE_PATH) == reg.SIGNIFICANCE_SHA256
    assert DATASET_PATH.is_file()
    assert sha256(DATASET_PATH) == (
        "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
    )
    assert reg.SOURCE_MODULE_HASHES == {
        "experiments/run_experiments.py": (
            "265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543"
        ),
        "experiments/significance.py": reg.SIGNIFICANCE_SHA256,
        "experiments/thesis/provenance.py": (
            "5a06c5c2e753cef0fe57e348250e7847b393c6173cd54c8be273f97976dc29f8"
        ),
    }
    for relative, expected in reg.SOURCE_MODULE_HASHES.items():
        assert sha256(REPO_ROOT / relative) == expected


def test_result_root_and_scientific_artifacts_are_absent():
    assert reg.RESULT_ROOT == "experiments/results_thesis/negative_control/"
    assert reg.RESULT_ROOT_EXISTS_AT_REGISTRATION is False
    assert reg.STAGE2_RESULT_EXISTS_AT_REGISTRATION is False
    assert reg.NO_STAGE2_SCIENTIFIC_DRAW_OR_OUTCOME is True
    assert not RESULT_ROOT.exists()
    assert not list(
        (REPO_ROOT / "experiments/results_thesis").glob("negative_control*")
    )


def test_current_registry_has_no_stage2_generated_output_contract():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert "experiments/results_thesis/negative_control" not in registry[
        "governed_roots"
    ]
    for section in ("entries", "prospective_entries"):
        assert not any(
            "experiments/results_thesis/negative_control"
            in entry["path_or_glob"]
            for entry in registry.get(section, [])
        )
    assert reg.PROSPECTIVE_ARTIFACT_CONTRACTS_REQUIRED_NOW is False
    assert reg.PROSPECTIVE_ARTIFACT_CONTRACT_STATUS == (
        "NOT_REQUIRED_AT_REGISTRATION"
    )


def test_canonical_models_and_splits_are_pinned_to_repository_source():
    assert reg.MODELS == (
        "linear_regression",
        "ridge",
        "lasso",
        "elasticnet",
        "random_forest",
        "gradient_boosting",
    )
    assert reg.MODELS == sig.ML_MODELS
    assert len(reg.MODELS) == 6
    assert reg.MODEL_FAMILY_DIVISOR == 6
    assert reg.MODEL_FAMILY_DIVISOR != len(canonical.MODELS)
    assert all(canonical.MODELS[name][0] == "ml" for name in reg.MODELS)
    assert not set(reg.MODELS) & {
        "baseline_equal_weight",
        "baseline_rank_score",
        "robust_rank_aggregation",
    }
    assert reg.MODEL_P_VALUE_SIDEDNESS == "two-sided"
    assert reg.MODEL_FAMILY_REJECTION_RULE == "min(1, 6 * min_raw_p) < 0.05"
    assert reg.HEADLINE_TIE_BREAK == "minimum raw p, then model name ascending"
    assert reg.CANONICAL_SPLIT_SOURCE == "experiments/run_experiments.py"
    assert reg.CANONICAL_SPLIT_SOURCE_SHA256 == reg.SOURCE_MODULE_HASHES[
        reg.CANONICAL_SPLIT_SOURCE
    ]

    expected_splits = tuple(
        source_split(split)
        for split in canonical.SPLITS
    )
    assert tuple(source_split(split) for split in reg.CANONICAL_SPLITS) == (
        expected_splits
    )
    assert reg.CANONICAL_SPLITS == reg.SPLITS == reg.SPLIT_DEFINITIONS


def test_canonical_model_specifications_are_frozen():
    for model in reg.MODELS:
        expected = canonical.MODEL_CONFIGS[model]
        actual = reg.MODEL_CONFIGS[model]
        assert actual["kind"] == expected["kind"] == "ml"
        assert actual["parameters"] == expected["parameters"]
        assert actual["seed"] == expected["seed"]
    assert reg.CANONICAL_FEATURE_COLUMN_COUNT == 40
    assert reg.CANONICAL_RANK_METHOD == "average"
    assert reg.CANONICAL_RANK_PERCENTILE is True
    assert reg.CANONICAL_IMPUTATION == "NaN -> 0.5"
    assert reg.CANONICAL_IMPUTATION_VALUE == 0.5
    assert reg.TARGET_COLUMN == "next_year_return_pct"
    assert reg.FEATURE_YEARS == (2020, 2021, 2022, 2023, 2024)
    assert reg.TARGET_YEARS == (2021, 2022, 2023, 2024, 2025)


def test_exact_control_names_roles_and_family_membership():
    assert reg.CONTROL_NAMES == (
        "NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN",
        "NC1_TARGET_PERMUTATION",
    )
    assert reg.CONFIRMATORY_CONTROLS == reg.CONTROL_NAMES
    assert reg.DIAGNOSTIC_NAMES == ("NC0_MASK_ALIGNED_DIAGNOSTIC",)
    assert reg.CONTROL_DECISION_FAMILY_SIZE == 2
    assert set(reg.CONTROL_ROLES) == set(reg.CONTROL_NAMES) | set(
        reg.DIAGNOSTIC_NAMES
    )
    assert all(
        reg.CONTROL_ROLES[name] == "CONFIRMATORY / GATING"
        for name in reg.CONTROL_NAMES
    )
    assert (
        reg.CONTROL_ROLES["NC0_MASK_ALIGNED_DIAGNOSTIC"]
        == "DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY"
    )


def test_nc1_definition_is_machine_checkable_and_forbids_test_only_permutation():
    assert reg.NC1_TEST_YEAR_ONLY_FORBIDDEN is True
    assert reg.NC1_FORBIDDEN_CONSTRUCTION == "test-year-only target permutation"
    for phrase in (
        "operate on the frozen canonical source/panel pipeline",
        "permute only OBSERVED next-year target values",
        "permute independently within every target year",
        "preserve target-null locations exactly",
        "include all years used by training and testing",
        "retrain all six models under the permuted target",
        "evaluate all registered splits normally",
    ):
        assert phrase.casefold() in {step.casefold() for step in reg.NC1_STEPS}
    assert reg.NC1_PRESERVES == (
        "target multiset within year",
        "target missingness/null locations",
        "feature matrix",
        "row universe",
        "train/test split definitions",
    )
    assert reg.NC1_DESTROYS == (
        "within-year feature/target association",
        "training signal from the real target mapping",
    )
    assert "does NOT establish absence of feature-side leakage" in (
        reg.NC1_SCOPE_LIMITATION
    )
    assert "circular" in reg.NC1_RATIONALE


def test_nc0_definition_preserves_joint_mask_structure_and_rejects_alternatives():
    assert reg.NC0_REAL_MASK_COLUMNS == 40
    assert reg.NC0_RAW_NOISE_DISTRIBUTION == "iid N(0,1)"
    assert reg.NC0_RANK_TRANSFORM == (
        "within-year average-rank percentile transform"
    )
    assert reg.NC0_MASK_PERMUTATION == (
        "one jointly applied row permutation per feature year across all 40 columns"
    )
    for phrase in (
        "generate fresh iid N(0,1) for every canonical row × feature cell",
        "canonical real 40-column missingness matrix",
        "jointly across ALL 40 feature columns",
        "same canonical within-year average-rank percentile transform",
        "keep the real target unchanged",
        "NaN -> 0.5",
        "retrain/evaluate the full six-model pipeline",
    ):
        assert any(phrase.casefold() in step.casefold() for step in reg.NC0_STEPS)
    assert reg.NC0_PRESERVES[:2] == (
        "each feature-year missingness rate",
        "row-wise co-missingness pattern multiset",
    )
    assert reg.NC0_DESTROYS == ("mask-to-target row alignment",)
    assert "does NOT establish absence of other feature-side leakage" in (
        reg.NC0_SCOPE_LIMITATION
    )
    assert set(reg.REJECTED_ALTERNATIVES) == {
        "LEGACY DENSE GAUSSIAN",
        "EXACT UNPERMUTED REAL MASK",
        "RAW N(0,1) + mask without rank transform",
    }
    assert "easier design matrix" in reg.REJECTED_ALTERNATIVES[
        "LEGACY DENSE GAUSSIAN"
    ]
    assert "target-associated" in reg.REJECTED_ALTERNATIVES[
        "EXACT UNPERMUTED REAL MASK"
    ]
    assert "off-centre" in reg.REJECTED_ALTERNATIVES[
        "RAW N(0,1) + mask without rank transform"
    ]


def test_nc0_diagnostic_is_frozen_outside_confirmatory_family():
    assert reg.NC0_DIAGNOSTIC_NAME == "NC0_MASK_ALIGNED_DIAGNOSTIC"
    assert reg.NC0_DIAGNOSTIC_ROLE == (
        "DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY"
    )
    assert reg.NC0_DIAGNOSTIC_IDS == tuple(range(3000, 4000))
    assert reg.R_DIAGNOSTIC == 1000
    assert reg.NC0_DIAGNOSTIC_SCOPE_LIMITATION == (
        "not an exact null-FPR test because the real mask is target-associated"
    )
    assert "mask-mediated target association" in " ".join(reg.NC0_DIAGNOSTIC_STEPS)
    assert set(reg.NC0_DIAGNOSTIC_IDS).isdisjoint(
        set(reg.NC0_IDS) | set(reg.NC1_IDS)
    )


def test_nc2_excluded_and_nc3_deferred():
    assert reg.NC2_STATUS == "EXCLUDED FROM STAGE 2 CONFIRMATORY FAMILY"
    assert reg.NC2_EXECUTION == "No NC2 execution in Stage 2."
    assert "not a clean null" in reg.NC2_REASON
    assert reg.NC3_STATUS == "DEFERRED DIAGNOSTIC"
    assert reg.NC3_EXECUTION == "No NC3 execution in Stage 2."
    assert "feature importance / ablation" in reg.NC3_REASON
    assert "separate diagnostic construction" in (
        reg.ALL_FEATURES_INDEPENDENT_PER_YEAR_STATUS
    )
    assert "not a third" in reg.ALL_FEATURES_INDEPENDENT_PER_YEAR_STATUS


def test_repetition_id_matrices_are_exact_and_gap_is_preserved():
    assert reg.BASE_SEED == 42
    assert prov.seed_for("negative_control") == reg.BASE_SEED
    assert reg.STAGE_1_IDS == tuple(range(0, 200))
    assert reg.STAGE_1B_IDS == tuple(range(200, 600))
    assert reg.RESERVED_IDS == tuple(range(600, 1000))
    assert reg.NC0_IDS == tuple(range(1000, 2000))
    assert reg.NC1_IDS == tuple(range(2000, 3000))
    assert reg.NC0_DIAGNOSTIC_IDS == tuple(range(3000, 4000))
    assert reg.R_PER_CONTROL == 1000
    assert reg.R_CONFIRMATORY_PER_CONTROL == 1000
    assert reg.R_DIAGNOSTIC == 1000
    assert reg.EXPECTED_REPETITION_ID_MATRICES == {
        reg.NC0_NAME: reg.NC0_IDS,
        reg.NC1_NAME: reg.NC1_IDS,
        reg.NC0_DIAGNOSTIC_NAME: reg.NC0_DIAGNOSTIC_IDS,
    }
    assert reg.ALL_STAGE2_IDS == (
        reg.NC0_IDS + reg.NC1_IDS + reg.NC0_DIAGNOSTIC_IDS
    )
    all_allocated = (
        reg.STAGE_1_IDS
        + reg.STAGE_1B_IDS
        + reg.RESERVED_IDS
        + reg.ALL_STAGE2_IDS
    )
    assert all_allocated == tuple(range(0, 4000))
    assert len(set(all_allocated)) == len(all_allocated)
    assert reg.NO_POOLING_WITH_STAGE_1_OR_STAGE_1B is True


def test_construction_streams_and_seed_functions_are_exact():
    assert reg.CONSTRUCTION_STREAMS == {
        "NC0_NOISE": 10,
        "NC0_MASK_ROW_PERMUTATION": 11,
        "NC1_TARGET_PERMUTATION": 20,
        "NC0_DIAGNOSTIC_NOISE": 30,
    }
    assert reg.STREAMS == reg.CONSTRUCTION_STREAMS
    assert reg.CONSTRUCTION_SEED_FORMULA == (
        "BASE_SEED * 1_000_003 + stream * 10_007 + repetition_id"
    )
    assert reg.SIGNIFICANCE_SEED_FORMULA == (
        "significance.DEFAULT_SEED + repetition_id = 42 + repetition_id"
    )
    for stream, repetition in (
        (10, 1000),
        (11, 1999),
        (20, 2000),
        (30, 3999),
    ):
        expected = 42 * 1_000_003 + stream * 10_007 + repetition
        assert reg.construction_seed(stream, repetition) == expected
    for repetition in (1000, 1999, 2000, 2999, 3999):
        assert reg.significance_seed(repetition) == 42 + repetition
    assert reg.SIGNIFICANCE_SEED_SHARED_ACROSS_MODELS is True


def test_stage2_seed_collisions_and_stage1_overlap_are_impossible():
    stream_ids = {
        "NC0_NOISE": reg.NC0_IDS,
        "NC0_MASK_ROW_PERMUTATION": reg.NC0_IDS,
        "NC1_TARGET_PERMUTATION": reg.NC1_IDS,
        "NC0_DIAGNOSTIC_NOISE": reg.NC0_DIAGNOSTIC_IDS,
    }
    construction_inputs = [
        (reg.CONSTRUCTION_STREAMS[stream], repetition)
        for stream, repetitions in stream_ids.items()
        for repetition in repetitions
    ]
    construction_seeds = {
        reg.construction_seed(stream, repetition)
        for stream, repetition in construction_inputs
    }
    assert len(construction_seeds) == len(construction_inputs)
    assert len(set(reg.CONSTRUCTION_STREAMS.values())) == len(
        reg.CONSTRUCTION_STREAMS
    )

    stage1_and_stage1b_construction = {
        base_seed * 1_000_003 + level * 10_007 + repetition
        for base_seed in (42, 43, 44)
        for level in range(6)
        for repetition in range(0, 600)
    }
    stage2_significance = {
        reg.significance_seed(repetition) for repetition in reg.ALL_STAGE2_IDS
    }
    historical_significance = {
        42 + repetition for repetition in range(0, 600)
    }
    assert construction_seeds.isdisjoint(stage1_and_stage1b_construction)
    assert construction_seeds.isdisjoint(stage2_significance)
    assert stage2_significance.isdisjoint(historical_significance)
    assert set(reg.RESERVED_IDS).isdisjoint(set(reg.ALL_STAGE2_IDS))


def test_model_family_and_control_gate_constants_are_separate():
    assert reg.MODEL_FAMILY_DIVISOR == 6
    assert reg.CONTROL_DECISION_FAMILY_SIZE == 2
    assert reg.MODEL_FAMILY_DIVISOR != reg.CONTROL_DECISION_FAMILY_SIZE
    assert reg.MODEL_ALPHA == 0.05
    assert reg.CONTROL_NULL_FPR == 0.05
    assert reg.CONTROL_ALPHA == 0.025
    assert reg.BONFERRONI_CONTROL_ALPHA == 0.025
    assert reg.FAMILY_FALSE_PROGRESSION_BLOCK_TARGET == 0.05
    assert reg.EXACT_K_CRIT_R1000 == 65
    assert reg.EXACT_BINOMIAL_CRITICAL_COUNT == 65
    assert reg.MIN_ANALYZABLE_DENOMINATOR == 1000
    assert reg.PERMUTATIONS == 10_000
    assert reg.BOOTSTRAPS == 10_000


def test_exact_binomial_critical_count_is_independently_recomputed():
    tail_at_65 = binomial_upper_tail(1000, 0.05, 65)
    tail_at_64 = binomial_upper_tail(1000, 0.05, 64)
    assert tail_at_65 == pytest.approx(0.02074989936553777, rel=1e-12)
    assert tail_at_64 == pytest.approx(0.028428397283993795, rel=1e-12)
    assert tail_at_65 <= 0.025
    assert tail_at_64 > 0.025
    assert 2.0 * tail_at_65 <= 0.05
    assert reg.EXACT_BINOMIAL_TAIL == "P[Binomial(1000, 0.05) >= 65]"
    assert reg.CONTROL_NULL_HYPOTHESIS == "H0: FPR_c <= 0.05"
    assert reg.CONTROL_ALTERNATIVE_HYPOTHESIS == "H1: FPR_c > 0.05"
    assert reg.CONTROL_FAILS_RULE == "X_c >= 65"
    assert reg.BONFERRONI_VALID_UNDER_ARBITRARY_DEPENDENCE is True
    assert reg.CONTROL_INDEPENDENCE_ASSUMED is False


def test_declared_power_values_match_exact_binomial_tails():
    for true_fpr, expected in reg.DECLARED_POWER_BY_TRUE_FPR.items():
        assert binomial_upper_tail(1000, true_fpr, 65) == pytest.approx(
            expected, abs=5e-11
        )
    assert reg.POWER_LIMITATION == (
        "Stage 2 has low power against mild inflation around 0.06."
    )
    assert reg.R_IS_NOT_A_RESOLUTION_THRESHOLD is True


def test_equivalence_is_descriptive_and_non_gating():
    assert reg.EQUIVALENCE_DELTA == 0.05
    assert reg.EQUIVALENCE_IS_GATING is False
    assert reg.EQUIVALENCE_STATUS == "descriptive / non-gating"
    assert reg.EQUIVALENCE_INTERVAL == "two-sided 90% CI against ±0.05"
    assert reg.EQUIVALENCE_RULE_WEAKENS_PREVIOUS_PASS_RULE is True
    assert reg.SESOI_STATUS == "UNRESOLVED"
    assert reg.DELTA_IS_FINANCEIQ_SESOI is False
    assert "not by itself Stage 2 scientific FAIL" in reg.EQUIVALENCE_VIOLATION
    assert reg.FPR_INTERVAL == "pointwise two-sided 95% Wilson interval"
    assert reg.WILSON_IS_GATING is False


def test_strict_completeness_and_degeneracy_contract_is_frozen():
    assert reg.STRICT_COMPLETE_DENOMINATOR is True
    assert reg.MIN_ANALYZABLE_DENOMINATOR == 1000
    assert len(reg.DEGENERACY_CHECKS) == 3
    assert "target" in reg.DEGENERACY_CHECKS[0]
    assert "prediction" in reg.DEGENERACY_CHECKS[1]
    assert "non-finite observed Spearman" in reg.DEGENERACY_CHECKS[2]
    assert reg.PARTIAL_MODEL_DEGENERACY_STATUS == (
        "INVALID / DEGENERATE_PARTIAL_MODEL"
    )
    assert reg.ALL_MODEL_DEGENERACY_STATUS == "INVALID / DEGENERATE_ALL_MODELS"
    assert reg.UNEXPECTED_EXCEPTION_STATUS == "INTEGRITY_FAILURE"
    assert len(reg.INVALID_REPETITION_RULES) == 5
    assert all("invalid repetition may not" in rule for rule in reg.INVALID_REPETITION_RULES)
    assert "INCONCLUSIVE" in reg.INCONCLUSIVE_RULE
    assert "cannot PASS or FAIL" in reg.INCONCLUSIVE_RULE


def test_closed_integrity_condition_identifiers_and_exclusions_are_explicit():
    assert len(reg.INTEGRITY_CONDITION_IDENTIFIERS) == 15
    assert reg.INTEGRITY_CONDITIONS == reg.INTEGRITY_CONDITION_IDENTIFIERS
    assert set(reg.INTEGRITY_CONDITION_DESCRIPTIONS) == set(
        reg.INTEGRITY_CONDITION_IDENTIFIERS
    )
    for identifier in reg.INTEGRITY_CONDITION_IDENTIFIERS:
        assert reg.INTEGRITY_CONDITION_DESCRIPTIONS[identifier].strip()
    assert reg.INTEGRITY_EXCLUSIONS == (
        "FPR",
        "rejection count",
        "IC",
        "p-value uniformity",
        "Wilson interval location",
        "gate result",
        "NC0/NC1 agreement",
        "equivalence result",
        "degeneracy magnitude beyond completeness classification itself",
    )
    assert reg.EXPLICIT_INTEGRITY_EXCLUSIONS == reg.INTEGRITY_EXCLUSIONS
    assert reg.INTEGRITY_EVALUATED_BEFORE_SCIENTIFIC_GATE is True
    assert reg.HIGH_FPR_IS_VALID_SCIENCE is True


def test_pre_run_disclosures_are_present_in_registration_and_amendment(
    registration_doc, protocol_doc
):
    for document in (registration_doc, protocol_doc):
        normalized = compact(document)
        for phrase in (
            "FAILED AS WRITTEN — INFORMATIVE",
            "complete Stage 1b calibration outcomes",
            "0/400 = 0.0000",
            "1/400 = 0.0025",
            "45/400 = 0.1125",
            "243/400 = 0.6075",
            "347/400 = 0.8675",
            "384/400 = 0.9600",
            "0.090305625773",
            "0.099628182092",
            "0.130441418767",
            "0.182221558521",
            "0.212800525022",
            "0.250279183231",
            "-0.0043485",
            "+0.0903056",
            "R=25",
            "0 family-wise rejections",
            "0 failed repetitions",
            "historical smoke test only, not Stage 2 calibration",
            "+0.225",
            "19 of 33",
            "non-finite observed statistic could produce",
            "forward-2026 hand-rolled permutation path",
            "analyze_model degeneracy behavior was unsafe / generic",
            "5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6",
            "08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3",
            "Historical Stage 1",
            "No Stage 2 scientific draw or outcome exists",
        ):
            assert phrase.casefold() in normalized.casefold(), phrase
    assert reg.STAGE_1_STATUS == "FAILED AS WRITTEN — INFORMATIVE"
    assert reg.STAGE_1B_OUTCOMES_ALREADY_INSPECTED is True
    assert reg.STAGE_1B_DETECTION_PROBABILITIES[0.35] == 0.8675
    assert reg.STAGE_1B_MEAN_FINAL_EVALUATED_IC[0.40] == 0.250279183231
    assert reg.LEGACY_DENSE_GAUSSIAN_PLACEBO["R"] == 25
    assert reg.PRE_STAGE2_MASK_DIAGNOSTICS["mask_columns_examined"] == 33
    assert reg.PRE_STAGE2_MASK_DIAGNOSTICS[
        "mask_columns_with_abs_pooled_ic_above_0_05"
    ] == 19
    assert reg.SIGNIFICANCE_DEFECTS_REPAIRED_BEFORE_REGISTRATION is True
    assert reg.HISTORICAL_ARTIFACTS_NOT_RERUN_OR_REWRITTEN is True


def test_protocol_amendment_is_dated_and_supersedes_old_design_prospectively(
    protocol_doc, registration_doc
):
    marker = "### 2026-09-02 — Stage 2 dated amendment and registration"
    assert marker in protocol_doc
    amendment = protocol_doc[protocol_doc.index(marker) :]
    old_design = "6 models × 2 null constructions = 12 tests, Bonferroni across 12"
    assert old_design in amendment
    for phrase in (
        "superseded prospectively before any Stage 2 outcome",
        "real evaluation's within-repetition operating family is six ML models",
        "model-family divisor is the frozen literal 6",
        "two confirmatory controls form a separate progression-decision family",
        "exact one-sided binomial tests with Bonferroni",
        "alpha=.025 per control",
        "Stage 1 divisor 5 is not used",
        "delta=.05 is retained as descriptive/non-gating",
        "weakening of the previously written Stage 2 pass rule",
        "No Stage 2 result exists at amendment time",
    ):
        assert phrase.casefold() in amendment.casefold(), phrase
    assert protocol_doc.index("## Stage 2 — Expanded negative control") < protocol_doc.index(
        marker
    )
    assert "The old block is not silently rewritten" in registration_doc
    assert "The old Stage 2 design" in registration_doc


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
        "run",
        "system",
        "exec",
        "eval",
    }
    assert not hasattr(reg, "main")
    assert reg.REGISTRATION_ONLY is True


def test_registration_import_is_filesystem_inert():
    tracked = (
        DATASET_PATH,
        SIGNIFICANCE_PATH,
        REGISTRATION_SOURCE,
        REPO_ROOT / "experiments/run_experiments.py",
        REPO_ROOT / "experiments/thesis/provenance.py",
    )
    before = {path: sha256(path) for path in tracked}
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import experiments.thesis.stage2_registration",
        ],
        cwd=REPO_ROOT,
        env=env,
        check=True,
    )
    after = {path: sha256(path) for path in tracked}
    assert after == before
    assert not RESULT_ROOT.exists()


def test_historical_stage1_and_stage1b_artifacts_are_unchanged_by_registration():
    historical = [
        REPO_ROOT / "experiments/thesis/positive_control.py",
        REPO_ROOT / "experiments/thesis/stage1b_registration.py",
        REPO_ROOT / "experiments/significance.py",
        REPO_ROOT / "experiments/results_thesis/positive_control",
        REPO_ROOT / "experiments/results_thesis/positive_control_calibration",
    ]

    def inventory(path: Path) -> dict[str, str]:
        if path.is_file():
            return {path.relative_to(REPO_ROOT).as_posix(): sha256(path)}
        return {
            item.relative_to(REPO_ROOT).as_posix(): sha256(item)
            for item in sorted(path.rglob("*"))
            if item.is_file()
        }

    before = {path: inventory(path) for path in historical}
    assert not RESULT_ROOT.exists()
    after = {path: inventory(path) for path in historical}
    assert after == before
