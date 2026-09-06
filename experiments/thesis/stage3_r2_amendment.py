"""Inert registration constants for the Stage 3 R2 amendment.

REGISTRATION ONLY. Importing this module performs no scientific draw, reads no
dataset, writes no result root, injects no defect, loads no adjudicator, and
has no execution entry point. R2 is a prospective accounting-only contract for
the already frozen Stage 3 attempt-1; it is not an adjudication result.
"""

from __future__ import annotations

from types import MappingProxyType


AMENDMENT_ID = "FINANCEIQ-THESIS-STAGE3-R2-INTEGRITY-ACCOUNTING"
AMENDMENT_DATE = "2026-09-06"
STATUS = "REGISTERED"
IMPLEMENTATION_STATUS = "NOT IMPLEMENTED"
ADJUDICATION_STATUS = "NOT ADJUDICATED"
REGISTRATION_ONLY = True
NO_SCIENTIFIC_RUN_PERFORMED = True
NO_R2_ADJUDICATION_PERFORMED = True

AUTHORITATIVE_BASE_COMMIT = "d4e7196fc43098f18b888ad602d1f1cd06101829"
EVIDENCE_COMMIT = "31643f19d58639b6aa4575625b4460dbdb4ab9b8"
POST_RUN_GOVERNANCE_COMMIT = "972f30adcf0f0419cec6fd71bfedb7967fad9ed2"
PR_A_MERGE = "d4e7196fc43098f18b888ad602d1f1cd06101829"
STAGE3_REGISTRATION_DOC = "docs/thesis/STAGE_3_REGISTRATION.md"
STAGE3_REGISTRATION_MODULE = "experiments/thesis/stage3_registration.py"
STAGE3_REGISTRATION_DOC_SHA256 = (
    "8153dfe0428faf902a01e83cd2d4c9b66a2c74da1a364dd76cea5f4682a2c621"
)
STAGE3_REGISTRATION_MODULE_SHA256 = (
    "839c6b8679b703508e0d50f36dde3a0de9861bf9706250138d75ab63f0549f1b"
)
STAGE3_REGISTERED_CONFIGURATION_SHA256 = (
    "4594521fde98c92a52400c9a02139c570b3d5241a2abfbd0d6006c213b51c677"
)


# --------------------------------------------------------------------------- #
# Frozen attempt-1 state and protected artifacts
# --------------------------------------------------------------------------- #
STAGE3_ATTEMPT_NUMBER = 1
STAGE3_ATTEMPT_TYPE = "initial"
STAGE3_ATTEMPT_STATUS = "complete"
STAGE3_PRIOR_INCOMPLETE_ATTEMPT = False
ORIGINAL_DECISION = "INCONCLUSIVE"
SOLE_FAILED_INTEGRITY_CONDITION = (
    "clean_comparator_byte_and_logical_identity"
)
SECOND_STAGE3_DRAW_AUTHORIZED = False
REPEAT_AFTER_CRASH_AUTHORIZED = False
STAGE3_FIRST_DRAW_IS_IMMUTABLE = True
ORIGINAL_ATTEMPT_ARTIFACTS_MUST_REMAIN_BYTE_IDENTICAL = True

DATASET_PATH = "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
DATASET_SHA256 = (
    "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
)
FROZEN_ATTEMPT1_ARTIFACT_HASHES = MappingProxyType(
    {
        "experiments/results_thesis/defect_injection/artifact_manifest.json": (
            "eeb25c9dd9cc0310679dc36470d3a7a913e8595de26649288e23d491db10ed4f"
        ),
        "experiments/results_thesis/defect_injection/attempts/attempt-1.json": (
            "657d1c777782ed41ec985073cfbf902b9398e56e63f1ae6b88b3fc8d8edb287e"
        ),
        "experiments/results_thesis/defect_injection/defect_injection_report.json": (
            "877f9367e768ce93c888bf0fec1dd5e7a9caa19369a9bfb5d47a818d2dd43a15"
        ),
        "experiments/results_thesis/defect_injection/defect_injection_report.md": (
            "d96be144a8ce7ccef37d2daee7a45179aa557002d4faa8262b947d0695109b7c"
        ),
        "experiments/results_thesis/defect_injection/defect_results.csv": (
            "bde017fa38af1f1446f1cada3c1d2973c5c5b797aa1bfefa2f6dc7dad113b852"
        ),
    }
)
FROZEN_ARTIFACT_HASHES = FROZEN_ATTEMPT1_ARTIFACT_HASHES
FROZEN_ATTEMPT1_ARTIFACT_COUNT = 5
HASH_MISMATCH_BEHAVIOR = "R2 REFUSES"

OBSERVED_DEFECT_MATRIX = MappingProxyType(
    {
        4000: "NOT_DETECTED",
        4001: "NOT_DETECTED",
        4002: "DETECTED",
        4003: "NOT_DETECTED",
        4004: "DETECTED",
    }
)
OBSERVED_MATRIX_IS_NOT_ADJUDICATION_EVIDENCE = True
EXPECTATION_MATCH_IS_EXCLUDED_FROM_EVIDENCE = True


# --------------------------------------------------------------------------- #
# R2 namespace and output lifecycle
# --------------------------------------------------------------------------- #
STAGE3_RESULT_ROOT = "experiments/results_thesis/defect_injection/"
R2_RESULT_ROOT = (
    "experiments/results_thesis/defect_injection_r2_adjudication/"
)
RESULT_ROOT = R2_RESULT_ROOT
R2_RESULT_ROOT_EXISTS_AT_REGISTRATION = False
R2_RESULT_FILENAMES = (
    "stage3_r2_adjudication.json",
    "stage3_r2_adjudication.md",
)
R2_PROSPECTIVE_ARTIFACT_PATHS = tuple(
    f"{R2_RESULT_ROOT}{filename}" for filename in R2_RESULT_FILENAMES
)
R2_PROSPECTIVE_ARTIFACT_COUNT = 2
R2_HAS_NO_ATTEMPTS_DIRECTORY = True
R2_HAS_NO_SCIENTIFIC_RUN_MANIFEST = True
R2_JSON_IS_AUTHORITATIVE_FUTURE_ADJUDICATION_RECORD = True
R2_ARTIFACTS_ARE_PROSPECTIVE_ONLY = True


# --------------------------------------------------------------------------- #
# Locked Option A semantics
# --------------------------------------------------------------------------- #
R2_OPTION = "A"
R2_SCOPE = "accounting-only retrospective re-adjudication"
R2_READS_EXISTING_FROZEN_ATTEMPT1_EVIDENCE_ONLY = True
R2_CORRECTS_ONLY = SOLE_FAILED_INTEGRITY_CONDITION
R2_RECOMPUTES_NO_SCIENTIFIC_QUANTITY = True
R2_DOES_NOT_REWRITE_ORIGINAL_ARTIFACTS = True
R2_RETAINED_FROZEN_INTEGRITY_CONDITIONS = (
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
    "expected_guard_mapping_evaluated_exactly_once",
    "no_defect_silently_omitted",
    "secondary_ic_only_on_undetected_defects",
    "no_invalid_evaluation_converted_to_non_detection",
    "deterministic_replay_contract",
)
R2_RETAINED_FROZEN_INTEGRITY_CONDITION_COUNT = 16
R2_RETAINED_INTEGRITY_CONDITIONS_MUST_REMAIN_TRUE = True
R2_RETAINED_INTEGRITY_CONDITIONS_MUST_NOT_BE_RECOMPUTED = True

R2_PREDICATE_CLAUSES = MappingProxyType(
    {
        "A0_CARDINALITY": (
            "Exactly five frozen defect records exist, covering registered IDs "
            "4000, 4001, 4002, 4003, and 4004 exactly once."
        ),
        "A1_PINNED_CLEAN_SOURCE_RE_READ": (
            "For every frozen defect record, source_sha256_before == "
            "source_sha256_after == registered DATASET_SHA256, and the "
            "completed run proves the load-time source-integrity gates completed "
            "without raising."
        ),
        "A2_ZERO_CLEAN_DETECTION_SIGNALS": (
            "For every frozen defect record, "
            "clean_comparator.detection_signals == []."
        ),
        "A3_DERIVED_CLEAN_LOGICAL_IDENTITY": (
            "For all five frozen defect records, derive logical identity only "
            "from the pinned source SHA before/after, mechanism_invariants.passed, "
            "mechanism_invariants.checks.source_shape_clean, "
            "clean_comparator.cleanup_proven, "
            "clean_comparator.containment_passed, and "
            "clean_comparator.invocation_accounting_passed."
        ),
    }
)
A0_CARDINALITY = R2_PREDICATE_CLAUSES["A0_CARDINALITY"]
A1_PINNED_CLEAN_SOURCE_RE_READ = R2_PREDICATE_CLAUSES[
    "A1_PINNED_CLEAN_SOURCE_RE_READ"
]
A2_ZERO_CLEAN_DETECTION_SIGNALS = R2_PREDICATE_CLAUSES[
    "A2_ZERO_CLEAN_DETECTION_SIGNALS"
]
A3_DERIVED_CLEAN_LOGICAL_IDENTITY = R2_PREDICATE_CLAUSES[
    "A3_DERIVED_CLEAN_LOGICAL_IDENTITY"
]
R2_REGISTERED_DEFECT_IDS = (4000, 4001, 4002, 4003, 4004)
R2_REGISTERED_DEFECT_COUNT = 5
R2_A0_ALLOWED_EVIDENCE = (
    "frozen report defect records",
    "frozen integrity conditions for exact family and completeness",
)
R2_A1_REQUIRED_COMPARISON = (
    "source_sha256_before == source_sha256_after == registered DATASET_SHA256",
    "completed load-time source-integrity gates without raising",
)
R2_A2_REQUIRED_FIELD = "clean_comparator.detection_signals == []"
A3_REQUIRED_DERIVED_EVIDENCE_FIELDS = (
    "source_sha256_before",
    "source_sha256_after",
    "mechanism_invariants.passed",
    "mechanism_invariants.checks.source_shape_clean",
    "clean_comparator.cleanup_proven",
    "clean_comparator.containment_passed",
    "clean_comparator.invocation_accounting_passed",
)
A3_DERIVATION_LABEL = "DERIVED"
A3_FORBIDDEN_OBSERVATION_LABEL = "OBSERVED_FINGERPRINT_EQUALITY"
A3_IS_DERIVED_NOT_OBSERVED = True
ATTEMPT1_FINGERPRINT_VALUES_PERSISTED = False
R2_MUST_NOT_CLAIM_FINGERPRINT_VALUES_WERE_PERSISTED = True
R2_MUST_FAIL_CLOSED_ON_MISSING_OR_MISMATCHED_FROZEN_INPUT = True

R2_ALLOWED_EVIDENCE = (
    "existing frozen attempt-1 report and attempt record",
    "existing frozen attempt-1 artifact manifest",
    "registered R2 predicate A0 through A3",
)
R2_FORBIDDEN_OPERATIONS = (
    "reinject any defect",
    "reevaluate guard surfaces",
    "load the source dataset to reconstruct fingerprints",
    "recompute _frame_fingerprint",
    "refit Ridge",
    "recompute secondary IC",
    "change any per-defect status",
    "change any detected_by value",
    "change mechanism invariants",
    "change containment results",
    "recompute the other sixteen integrity conditions",
    "use expectation-match as evidence",
    "perform a second scientific draw",
)
R2_DATASET_LOADING_FORBIDDEN = True
R2_FINGERPRINT_RECONSTRUCTION_FORBIDDEN = True
R2_MODEL_RECOMPUTATION_FORBIDDEN = True
R2_IC_RECOMPUTATION_FORBIDDEN = True

READJUDICATED_DECISION_FIELD = "readjudicated_decision"
READJUDICATED_DECISION_VALUE_PREREGISTERED = False
READJUDICATED_DECISION_COMPUTED_ONLY_BY_FUTURE_ADJUDICATOR = True
R2_DECISION_FUNCTION = (
    "If all retained frozen integrity conditions remain true and A0 through A3 "
    "pass, the future adjudicator computes readjudicated_decision from the "
    "frozen per-defect statuses using the registered Stage 3 decision rule; "
    "otherwise it records INCONCLUSIVE."
)
R2_DECISION_FUNCTION_DOES_NOT_HARDCODE_FAIL = True
R2_ORIGINAL_DECISION_REMAINS_PERMANENTLY = ORIGINAL_DECISION
FROZEN_PER_DEFECT_STATUSES_AND_DETECTED_BY_ARE_UNCHANGED = True


# --------------------------------------------------------------------------- #
# Forward-only runner correction, separate from R2 attempt-1
# --------------------------------------------------------------------------- #
FORWARD_RUNNER_PREDICATE = (
    "len(clean_fingerprints) == DEFECT_FAMILY_SIZE",
    "len(set(clean_fingerprints)) == 1",
    "all(clean comparator detection_signals are empty)",
)
FORWARD_PREDICATE_REGISTERED = True
FORWARD_PREDICATE_EXERCISED_BY_R2 = False
FUTURE_EXECUTION_MUST_PERSIST_EACH_PER_DEFECT_CLEAN_FINGERPRINT = True
FORWARD_CORRECTION_IS_NOT_AN_R2_REPLAY = True
NO_SECOND_STAGE3_DRAW = True


# --------------------------------------------------------------------------- #
# Recovery defect and later repair contract
# --------------------------------------------------------------------------- #
RECOVERY_DEFECT = (
    "completion logic incorrectly requires integrity_passed == true, which can "
    "classify a complete-but-INCONCLUSIVE attempt as incomplete"
)
RECOVERY_DELETION_RISK = (
    "repeat-after-crash can delete defect_injection_report.json, "
    "defect_injection_report.md, defect_results.csv, and artifact_manifest.json"
)
RECOVERY_REPAIR_REQUIREMENTS = (
    "separate completion/durability from integrity verdict",
    "refuse repeat-after-crash if ANY attempt record has status == complete",
    "make the cleanup primitive refuse deletion if a complete attempt exists",
    "remove any operator message that directs a complete run toward repeat-after-crash",
)
RECOVERY_REPAIR_REGISTERED = True
RECOVERY_REPAIR_IMPLEMENTED = False


# --------------------------------------------------------------------------- #
# Residual issues, falsifiers, and downstream gate
# --------------------------------------------------------------------------- #
RESIDUAL_DISCLOSURES = (
    "attempt-1 fingerprint values were not persisted",
    "some integrity conditions are implementation accounting assertions rather "
    "than independently persisted measurements",
    "the Stage 3 report does not populate the limitations register like some "
    "earlier thesis reports",
)
GOVERNED_DRAW_STARTED_CLEAN = True
LATER_GIT_DIRTY_TRUE_IS_NOT_DIRTY_AT_START_EVIDENCE = True
DIRTY_AT_START_MUST_NOT_BE_CLAIMED = True

R2_FALSIFIERS = (
    "any frozen attempt-1 artifact SHA mismatch",
    "registered configuration mismatch",
    "Stage 3 registration module or document hash mismatch",
    "any frozen integrity condition besides the known condition is false",
    "any clean detection signal is non-empty",
    "any source_sha256 before or after differs from the pin",
    "required A3 derived-evidence fields are missing or false",
    "frozen per-defect statuses are shown to depend on the accounting bug",
    "adjudication requires dataset loading, injection, guard reevaluation, model recomputation, or IC recomputation",
    "a second governed Stage 3 draw occurs",
    "repeat-after-crash is executed against attempt-1",
)

STAGE_1_STATUS = "FAILED AS WRITTEN — INFORMATIVE"
STAGE_3_STATUS = "NOT PASSED; original decision INCONCLUSIVE"
STAGE_7_UNLOCKED = False
STAGE_7_REMAINS_BLOCKED = True
STAGE_7_BLOCKED_REASONS = (
    "Stage 1 remains FAILED AS WRITTEN — INFORMATIVE",
    "Stage 3 has not passed",
    "R2 registration cannot unlock any downstream stage",
)

CLAIM_BOUNDARY = (
    "R2 is accounting-only and retrospective over existing frozen attempt-1 evidence.",
    "R2 establishes no new scientific observation.",
    "R2 establishes no predictive edge, alpha, investment value, or production readiness.",
    "Research support only; not investment advice.",
)
