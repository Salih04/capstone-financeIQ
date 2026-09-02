"""Stage 2 prospective registration constants.

REGISTRATION ONLY. Importing this module performs no scientific draw, reads no
dataset, writes no result root, fits no model, and has no execution entry
point. It contains the owner-locked Stage 2 design from
docs/thesis/STAGE_2_REGISTRATION.md so registration tests can prove the
machine-readable contract before a future runner exists.

The registration is prospective but not blind. Stage 1, the complete Stage 1b
calibration outcome, the legacy dense-Gaussian placebo, pre-run mask diagnostics,
and the repaired significance implementation were already known when this
registration was written. No Stage 2 draw or outcome exists.
"""

from __future__ import annotations

from types import MappingProxyType


# --------------------------------------------------------------------------- #
# Namespace and authoritative source pins
# --------------------------------------------------------------------------- #
STAGE2_SLUG = "negative_control"
RESULT_ROOT = "experiments/results_thesis/negative_control/"
REGISTRATION_DOC = "docs/thesis/STAGE_2_REGISTRATION.md"
PROTOCOL_DOC = "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md"

# This is a historical registration-phase fact. The module must not create it.
RESULT_ROOT_EXISTS_AT_REGISTRATION = False
STAGE2_RESULT_EXISTS_AT_REGISTRATION = False
REGISTRATION_ONLY = True

DATASET_PATH = "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
DATASET_SHA256 = (
    "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
)
SIGNIFICANCE_SHA256 = (
    "08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3"
)
REPAIRED_SIGNIFICANCE_SHA256 = SIGNIFICANCE_SHA256
OLD_SIGNIFICANCE_SHA256 = (
    "5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6"
)

# These are source pins for the future runner's canonical panel, significance,
# and thesis-provenance dependencies. The registration module itself is not
# self-hashed: a source cannot contain a stable literal hash of its own bytes.
SOURCE_MODULE_HASHES = MappingProxyType(
    {
        "experiments/run_experiments.py": (
            "265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543"
        ),
        "experiments/significance.py": SIGNIFICANCE_SHA256,
        "experiments/thesis/provenance.py": (
            "5a06c5c2e753cef0fe57e348250e7847b393c6173cd54c8be273f97976dc29f8"
        ),
    }
)
CANONICAL_SOURCE_HASHES = SOURCE_MODULE_HASHES
CANONICAL_SPLIT_SOURCE = "experiments/run_experiments.py"
CANONICAL_SPLIT_SOURCE_SHA256 = SOURCE_MODULE_HASHES[CANONICAL_SPLIT_SOURCE]


# --------------------------------------------------------------------------- #
# Canonical panel, model family, and splits
# --------------------------------------------------------------------------- #
TARGET_COLUMN = "next_year_return_pct"
KEY_COLUMNS = ("ticker", "year")
FEATURE_YEARS = (2020, 2021, 2022, 2023, 2024)
TARGET_YEARS = (2021, 2022, 2023, 2024, 2025)
CANONICAL_FEATURE_COLUMN_COUNT = 40
CANONICAL_RANK_METHOD = "average"
CANONICAL_RANK_PERCENTILE = True
CANONICAL_IMPUTATION = "NaN -> 0.5"
CANONICAL_IMPUTATION_VALUE = 0.5

# Exact source definitions from experiments/run_experiments.py. The future
# runner must reconstruct the source list/dicts without changing their values.
CANONICAL_SPLITS = (
    MappingProxyType(
        {
            "name": "test_2023",
            "train_target_years": (2021, 2022),
            "test_feature_year": 2022,
        }
    ),
    MappingProxyType(
        {
            "name": "test_2024",
            "train_target_years": (2021, 2022, 2023),
            "test_feature_year": 2023,
        }
    ),
    MappingProxyType(
        {
            "name": "test_2025",
            "train_target_years": (2021, 2022, 2023, 2024),
            "test_feature_year": 2024,
        }
    ),
)
SPLITS = CANONICAL_SPLITS
SPLIT_DEFINITIONS = CANONICAL_SPLITS

MODELS = (
    "linear_regression",
    "ridge",
    "lasso",
    "elasticnet",
    "random_forest",
    "gradient_boosting",
)
MODEL_FAMILY = MODELS
MODEL_FAMILY_DIVISOR = 6
MODEL_ALPHA = 0.05
MODEL_P_VALUE_SIDEDNESS = "two-sided"
MODEL_FAMILY_REJECTION_RULE = "min(1, 6 * min_raw_p) < 0.05"
HEADLINE_TIE_BREAK = "minimum raw p, then model name ascending"
PERMUTATIONS = 10_000
BOOTSTRAPS = 10_000

# The six model specifications are copied from the canonical source. Baselines
# are deliberately absent from this Stage 2 confirmatory family.
MODEL_CONFIGS = MappingProxyType(
    {
        "linear_regression": MappingProxyType(
            {"kind": "ml", "parameters": MappingProxyType({}), "seed": None}
        ),
        "ridge": MappingProxyType(
            {
                "kind": "ml",
                "parameters": MappingProxyType({"alpha": 1.0}),
                "seed": None,
            }
        ),
        "lasso": MappingProxyType(
            {
                "kind": "ml",
                "parameters": MappingProxyType({"alpha": 0.1, "max_iter": 5000}),
                "seed": None,
            }
        ),
        "elasticnet": MappingProxyType(
            {
                "kind": "ml",
                "parameters": MappingProxyType({"alpha": 0.1, "max_iter": 5000}),
                "seed": None,
            }
        ),
        "random_forest": MappingProxyType(
            {
                "kind": "ml",
                "parameters": MappingProxyType(
                    {"n_estimators": 200, "max_depth": 4}
                ),
                "seed": 42,
            }
        ),
        "gradient_boosting": MappingProxyType(
            {
                "kind": "ml",
                "parameters": MappingProxyType(
                    {"max_depth": 2, "n_estimators": 120}
                ),
                "seed": 42,
            }
        ),
    }
)


# --------------------------------------------------------------------------- #
# Confirmatory controls and diagnostic arms
# --------------------------------------------------------------------------- #
NC0_NAME = "NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN"
NC1_NAME = "NC1_TARGET_PERMUTATION"
NC0_DIAGNOSTIC_NAME = "NC0_MASK_ALIGNED_DIAGNOSTIC"
CONTROL_NAMES = (NC0_NAME, NC1_NAME)
CONFIRMATORY_CONTROLS = CONTROL_NAMES
DIAGNOSTIC_NAMES = (NC0_DIAGNOSTIC_NAME,)
CONTROL_DECISION_FAMILY_SIZE = 2
CONTROL_ROLES = MappingProxyType(
    {
        NC0_NAME: "CONFIRMATORY / GATING",
        NC1_NAME: "CONFIRMATORY / GATING",
        NC0_DIAGNOSTIC_NAME: "DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY",
    }
)

NC1_STEPS = (
    "operate on the frozen canonical source/panel pipeline",
    "permute only OBSERVED next-year target values",
    "permute independently within every target year",
    "preserve target-null locations exactly",
    "include all years used by training and testing",
    "retrain all six models under the permuted target",
    "evaluate all registered splits normally",
)
NC1_PRESERVES = (
    "target multiset within year",
    "target missingness/null locations",
    "feature matrix",
    "row universe",
    "train/test split definitions",
)
NC1_DESTROYS = (
    "within-year feature/target association",
    "training signal from the real target mapping",
)
NC1_SCOPE_LIMITATION = (
    "null for within-year rank association; does NOT establish absence of "
    "feature-side leakage"
)
NC1_TEST_YEAR_ONLY_FORBIDDEN = True
NC1_FORBIDDEN_CONSTRUCTION = (
    "test-year-only target permutation"
)
NC1_RATIONALE = (
    "Holding y_pred fixed and permuting only a test year's y_true is one draw "
    "from the same within-year reference distribution already used by "
    "significance.py; it is circular and does not test retraining/apparatus "
    "behavior."
)

NC0_STEPS = (
    "generate fresh iid N(0,1) for every canonical row × feature cell",
    "for each feature year separately, take the canonical real 40-column missingness matrix",
    "apply ONE independently seeded row permutation within that year jointly across ALL 40 feature columns",
    "apply the permuted mask to the fresh noise",
    "apply the SAME canonical within-year average-rank percentile transform used by the panel pipeline",
    "keep the real target unchanged",
    "keep canonical imputation unchanged: NaN -> 0.5",
    "retrain/evaluate the full six-model pipeline",
)
NC0_PRESERVES = (
    "each feature-year missingness rate",
    "row-wise co-missingness pattern multiset",
    "target",
    "feature-year row universe",
    "canonical splits",
    "six registered models",
)
NC0_DESTROYS = ("mask-to-target row alignment",)
NC0_SCOPE_LIMITATION = (
    "a target-alignment/missingness-channel null; it does NOT establish "
    "absence of other feature-side leakage"
)
NC0_REAL_MASK_COLUMNS = 40
NC0_RANK_TRANSFORM = "within-year average-rank percentile transform"
NC0_RAW_NOISE_DISTRIBUTION = "iid N(0,1)"
NC0_MASK_PERMUTATION = (
    "one jointly applied row permutation per feature year across all 40 columns"
)

REJECTED_ALTERNATIVES = MappingProxyType(
    {
        "LEGACY DENSE GAUSSIAN": (
            "valid mathematical null but removes the real missingness/imputation "
            "path and therefore runs an easier design matrix than the real apparatus"
        ),
        "EXACT UNPERMUTED REAL MASK": (
            "NOT a confirmatory null because pre-run diagnostics showed the mask "
            "itself is target-associated"
        ),
        "RAW N(0,1) + mask without rank transform": (
            "forbidden because imputation value 0.5 becomes an artificial "
            "off-centre feature cluster not present in the canonical "
            "rank-percentile panel"
        ),
    }
)

NC0_DIAGNOSTIC_STEPS = (
    "fresh rank-Gaussian noise",
    "the EXACT REAL per-cell missingness mask retained in its real row alignment",
    "target unchanged",
    "measure mask-mediated target association / imputation-channel behavior",
)
NC0_DIAGNOSTIC_ROLE = "DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY"
NC0_DIAGNOSTIC_SCOPE_LIMITATION = (
    "not an exact null-FPR test because the real mask is target-associated"
)

CONTROL_DEFINITIONS = MappingProxyType(
    {
        NC1_NAME: MappingProxyType(
            {
                "role": CONTROL_ROLES[NC1_NAME],
                "steps": NC1_STEPS,
                "preserves": NC1_PRESERVES,
                "destroys": NC1_DESTROYS,
                "scope_limitation": NC1_SCOPE_LIMITATION,
                "test_year_only_forbidden": NC1_TEST_YEAR_ONLY_FORBIDDEN,
            }
        ),
        NC0_NAME: MappingProxyType(
            {
                "role": CONTROL_ROLES[NC0_NAME],
                "steps": NC0_STEPS,
                "preserves": NC0_PRESERVES,
                "destroys": NC0_DESTROYS,
                "scope_limitation": NC0_SCOPE_LIMITATION,
                "rejected_alternatives": REJECTED_ALTERNATIVES,
            }
        ),
    }
)


# --------------------------------------------------------------------------- #
# Repetition IDs and RNG contract
# --------------------------------------------------------------------------- #
BASE_SEED = 42
PROVENANCE_SEED_SOURCE = 'provenance.SEEDS["negative_control"]'

STAGE_1_IDS = tuple(range(0, 200))
STAGE_1B_IDS = tuple(range(200, 600))
RESERVED_IDS = tuple(range(600, 1000))
NC0_IDS = tuple(range(1000, 2000))
NC1_IDS = tuple(range(2000, 3000))
NC0_DIAGNOSTIC_IDS = tuple(range(3000, 4000))

R_PER_CONTROL = 1000
R_CONFIRMATORY_PER_CONTROL = R_PER_CONTROL
R_DIAGNOSTIC = 1000
EXPECTED_REPETITION_ID_MATRICES = MappingProxyType(
    {
        NC0_NAME: NC0_IDS,
        NC1_NAME: NC1_IDS,
        NC0_DIAGNOSTIC_NAME: NC0_DIAGNOSTIC_IDS,
    }
)
ALL_STAGE2_IDS = NC0_IDS + NC1_IDS + NC0_DIAGNOSTIC_IDS
NO_POOLING_WITH_STAGE_1_OR_STAGE_1B = True

CONSTRUCTION_STREAMS = MappingProxyType(
    {
        "NC0_NOISE": 10,
        "NC0_MASK_ROW_PERMUTATION": 11,
        "NC1_TARGET_PERMUTATION": 20,
        "NC0_DIAGNOSTIC_NOISE": 30,
    }
)
STREAMS = CONSTRUCTION_STREAMS
CONSTRUCTION_SEED_FORMULA = (
    "BASE_SEED * 1_000_003 + stream * 10_007 + repetition_id"
)
SIGNIFICANCE_SEED_FORMULA = (
    "significance.DEFAULT_SEED + repetition_id = 42 + repetition_id"
)
SIGNIFICANCE_DEFAULT_SEED = 42
SIGNIFICANCE_SEED_SHARED_ACROSS_MODELS = True


def construction_seed(stream: int, repetition_id: int) -> int:
    """Return the frozen construction seed without drawing random values."""
    return BASE_SEED * 1_000_003 + stream * 10_007 + repetition_id


def significance_seed(repetition_id: int) -> int:
    """Return the registered significance seed without drawing random values."""
    return SIGNIFICANCE_DEFAULT_SEED + repetition_id


# --------------------------------------------------------------------------- #
# Completeness and degeneracy contract
# --------------------------------------------------------------------------- #
STRICT_COMPLETE_DENOMINATOR = True
MIN_ANALYZABLE_DENOMINATOR = 1000
DEGENERACY_CHECKS = (
    "target having <2 distinct finite values per model and evaluated split",
    "prediction having <2 distinct finite values per model and evaluated split",
    "non-finite observed Spearman statistic per model and evaluated split",
)
DEGENERACY_CLASSIFICATIONS = MappingProxyType(
    {
        "DEGENERATE_PARTIAL_MODEL": "INVALID / DEGENERATE_PARTIAL_MODEL",
        "DEGENERATE_ALL_MODELS": "INVALID / DEGENERATE_ALL_MODELS",
        "UNEXPECTED_EXCEPTION": "INTEGRITY_FAILURE",
    }
)
PARTIAL_MODEL_DEGENERACY_STATUS = DEGENERACY_CLASSIFICATIONS[
    "DEGENERATE_PARTIAL_MODEL"
]
ALL_MODEL_DEGENERACY_STATUS = DEGENERACY_CLASSIFICATIONS["DEGENERATE_ALL_MODELS"]
UNEXPECTED_EXCEPTION_STATUS = DEGENERACY_CLASSIFICATIONS["UNEXPECTED_EXCEPTION"]
INVALID_REPETITION_RULES = (
    "invalid repetition may not disappear",
    "invalid repetition may not be converted to p=1",
    "invalid repetition may not be counted as a non-rejection",
    "invalid repetition may not reduce divisor 6",
    "invalid repetition may not reduce the denominator and still allow PASS",
)
INCONCLUSIVE_RULE = (
    "if either confirmatory analyzable denominator is below 1000, Stage 2 is "
    "INCONCLUSIVE and cannot PASS or FAIL through the scientific FPR gate"
)


# --------------------------------------------------------------------------- #
# Estimand, exact gate, and descriptive uncertainty
# --------------------------------------------------------------------------- #
PRIMARY_ESTIMAND = (
    "For each confirmatory control c, X_c is the number of the 1000 complete "
    "repetitions in which the six-model family rule rejects."
)
FPR_ESTIMATE = "X_c / 1000"
FPR_INTERVAL = "pointwise two-sided 95% Wilson interval"
WILSON_IS_GATING = False

CONTROL_NULL_FPR = 0.05
CONTROL_ALPHA = 0.025
BONFERRONI_CONTROL_ALPHA = CONTROL_ALPHA
FAMILY_FALSE_PROGRESSION_BLOCK_TARGET = 0.05
EXACT_K_CRIT_R1000 = 65
EXACT_BINOMIAL_CRITICAL_COUNT = EXACT_K_CRIT_R1000
EXACT_BINOMIAL_TAIL = "P[Binomial(1000, 0.05) >= 65]"
CONTROL_NULL_HYPOTHESIS = "H0: FPR_c <= 0.05"
CONTROL_ALTERNATIVE_HYPOTHESIS = "H1: FPR_c > 0.05"
CONTROL_FAILS_RULE = "X_c >= 65"
STAGE2_FAILS_RULE = "NC0 fails OR NC1 fails"
STAGE2_PASSES_RULE = (
    "both controls have exactly 1000 analyzable repetitions; NC0 X <= 64; "
    "NC1 X <= 64; integrity contract passed"
)
STAGE2_INCONCLUSIVE_RULE = (
    "either confirmatory analyzable denominator < 1000"
)
BONFERRONI_VALID_UNDER_ARBITRARY_DEPENDENCE = True
CONTROL_INDEPENDENCE_ASSUMED = False
CONTROL_DEPENDENCE_STATEMENT = (
    "Bonferroni control is valid under arbitrary dependence between NC0 and NC1; "
    "the controls are not assumed independent"
)

DECLARED_POWER_BY_TRUE_FPR = MappingProxyType(
    {
        0.06: 0.2703680264,
        0.075: 0.8982904410,
        0.10: 0.9999627573,
    }
)
CONTROL_POWER_BY_TRUE_FPR = DECLARED_POWER_BY_TRUE_FPR
POWER_LIMITATION = "Stage 2 has low power against mild inflation around 0.06."
R_IS_NOT_A_RESOLUTION_THRESHOLD = True


# --------------------------------------------------------------------------- #
# Equivalence limb and SESOI boundary
# --------------------------------------------------------------------------- #
EQUIVALENCE_DELTA = 0.05
EQUIVALENCE_IS_GATING = False
EQUIVALENCE_STATUS = "descriptive / non-gating"
EQUIVALENCE_INTERVAL = "two-sided 90% CI against ±0.05"
EQUIVALENCE_VIOLATION = (
    "reportable finding requiring investigation before Stage 3 progression, "
    "but not by itself Stage 2 scientific FAIL"
)
EQUIVALENCE_RULE_WEAKENS_PREVIOUS_PASS_RULE = True
SESOI_STATUS = "UNRESOLVED"
DELTA_IS_FINANCEIQ_SESOI = False


# --------------------------------------------------------------------------- #
# NC2 / NC3 status and integrity contract
# --------------------------------------------------------------------------- #
NC2_DEFINITION = (
    "cross-year/cohort target derangement that moves target values across years "
    "while preserving a ticker/cohort relation"
)
NC2_STATUS = "EXCLUDED FROM STAGE 2 CONFIRMATORY FAMILY"
NC2_EXECUTION = "No NC2 execution in Stage 2."
NC2_REASON = (
    "not a clean null for the within-year Spearman estimand; can preserve "
    "persistent ticker return structure or alter year distributions, and has low "
    "marginal value versus NC1 / later alignment-defect testing"
)

NC3_DEFINITION = (
    "single-feature-at-a-time within-year permutation while other features remain aligned"
)
NC3_STATUS = "DEFERRED DIAGNOSTIC"
NC3_EXECUTION = "No NC3 execution in Stage 2."
NC3_REASON = (
    "not a negative-control null; it is feature importance / ablation because "
    "the remaining real features retain real target association"
)
ALL_FEATURES_INDEPENDENT_PER_YEAR_STATUS = (
    "separate diagnostic construction, not NC3 confirmatory and not a third "
    "confirmatory family member"
)

INTEGRITY_CONDITION_IDENTIFIERS = (
    "frozen_source_dataset_path_and_sha_match",
    "repaired_significance_sha_matches",
    "registered_stage2_source_module_hashes_match",
    "complete_expected_repetition_id_matrices",
    "no_duplicate_repetition_ids_or_model_cells",
    "exact_seed_formulas_reproduce",
    "no_seed_collisions_or_forbidden_overlap",
    "writes_confined_to_stage2_result_namespace",
    "stage1_and_stage1b_result_roots_untouched",
    "no_trusted_data_or_provenance_mutation",
    "protected_digest_outside_stage2_root_unchanged",
    "runtime_source_override_restored_on_all_exit_paths",
    "deterministic_replay_contract",
    "finite_valid_statistics_or_registered_degeneracy",
    "all_expected_model_cells_present_for_analyzable_repetitions",
)
INTEGRITY_CONDITION_DESCRIPTIONS = MappingProxyType(
    {
        "frozen_source_dataset_path_and_sha_match": (
            "frozen source dataset path and SHA match"
        ),
        "repaired_significance_sha_matches": (
            "repaired significance.py SHA matches 08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3"
        ),
        "registered_stage2_source_module_hashes_match": (
            "registered Stage 2 source/module hashes match"
        ),
        "complete_expected_repetition_id_matrices": (
            "complete expected repetition-ID matrices"
        ),
        "no_duplicate_repetition_ids_or_model_cells": "no duplicates",
        "exact_seed_formulas_reproduce": "exact seed formulas reproduce",
        "no_seed_collisions_or_forbidden_overlap": (
            "no collisions / forbidden overlap"
        ),
        "writes_confined_to_stage2_result_namespace": (
            "writes confined to the Stage 2 result namespace"
        ),
        "stage1_and_stage1b_result_roots_untouched": (
            "Stage 1 and Stage 1b result roots untouched"
        ),
        "no_trusted_data_or_provenance_mutation": (
            "no data/trusted*, data/trusted_clean*, or provenance mutation"
        ),
        "protected_digest_outside_stage2_root_unchanged": (
            "whole-repo protected digest outside the Stage 2 result root unchanged "
            "where current infrastructure supports it"
        ),
        "runtime_source_override_restored_on_all_exit_paths": (
            "runtime source override restored on all exit paths"
        ),
        "deterministic_replay_contract": "deterministic replay contract",
        "finite_valid_statistics_or_registered_degeneracy": (
            "finite valid statistics OR explicit registered degeneracy classification"
        ),
        "all_expected_model_cells_present_for_analyzable_repetitions": (
            "all expected model cells present for analyzable repetitions"
        ),
    }
)
INTEGRITY_CONDITIONS = INTEGRITY_CONDITION_IDENTIFIERS
INTEGRITY_EXCLUSIONS = (
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
EXPLICIT_INTEGRITY_EXCLUSIONS = INTEGRITY_EXCLUSIONS
INTEGRITY_EVALUATED_BEFORE_SCIENTIFIC_GATE = True
HIGH_FPR_IS_VALID_SCIENCE = True


# --------------------------------------------------------------------------- #
# Pre-run disclosure record
# --------------------------------------------------------------------------- #
STAGE_1_STATUS = "FAILED AS WRITTEN — INFORMATIVE"
STAGE_1B_OUTCOMES_ALREADY_INSPECTED = True
STAGE_1B_DETECTION_PROBABILITIES = MappingProxyType(
    {
        0.00: 0.0000,
        0.10: 0.0025,
        0.20: 0.1125,
        0.30: 0.6075,
        0.35: 0.8675,
        0.40: 0.9600,
    }
)
STAGE_1B_MEAN_FINAL_EVALUATED_IC = MappingProxyType(
    {
        0.00: 0.090305625773,
        0.10: 0.099628182092,
        0.20: 0.130441418767,
        0.30: 0.182221558521,
        0.35: 0.212800525022,
        0.40: 0.250279183231,
    }
)
STAGE_1B_THETA_ZERO_MEAN_RAW_CARRIER_IC = -0.0043485
STAGE_1B_THETA_ZERO_MEAN_FINAL_IC = 0.0903056

LEGACY_DENSE_GAUSSIAN_PLACEBO = MappingProxyType(
    {
        "R": 25,
        "family_wise_rejections": 0,
        "failed_repetitions": 0,
        "status": "historical smoke test only, not Stage 2 calibration",
    }
)
PRE_STAGE2_MASK_DIAGNOSTICS = MappingProxyType(
    {
        "one_missingness_indicator_pooled_ic": 0.225,
        "mask_columns_with_abs_pooled_ic_above_0_05": 19,
        "mask_columns_examined": 33,
        "motivation": "These observations motivated the NC0 design.",
    }
)
KNOWN_SIGNIFICANCE_DEFECTS = (
    "non-finite observed statistic could produce minimum p-value in a helper",
    "forward-2026 hand-rolled permutation path had the same failure mode",
    "analyze_model degeneracy behavior was unsafe / generic",
)
SIGNIFICANCE_DEFECTS_REPAIRED_BEFORE_REGISTRATION = True
HISTORICAL_ARTIFACTS_NOT_RERUN_OR_REWRITTEN = True
NO_STAGE2_SCIENTIFIC_DRAW_OR_OUTCOME = True


# --------------------------------------------------------------------------- #
# Claim boundary and future governance boundary
# --------------------------------------------------------------------------- #
CLAIM_BOUNDARY = (
    "Stage 2 may establish only apparatus behavior under the registered null constructions.",
    "It does NOT establish predictive edge, alpha, investment value, production readiness, absence of leakage, absence of predictability, universal FPR calibration, or naturally occurring IC calibration.",
    "Passing Stage 2 does NOT prove absence of feature-side PIT/alignment leakage; that belongs to later defect-injection stages.",
    "Research support only; not investment advice.",
)
FUTURE_IMPLEMENTATION_MUST_REMAIN_REGISTRATION_SEPARATE = True
FUTURE_RESULT_OWNERSHIP_WIRING_REQUIRED_BEFORE_RUN = True
PROSPECTIVE_ARTIFACT_CONTRACTS_REQUIRED_NOW = False
PROSPECTIVE_ARTIFACT_CONTRACT_STATUS = "NOT_REQUIRED_AT_REGISTRATION"
