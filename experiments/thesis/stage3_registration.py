"""Stage 3 prospective registration constants.

REGISTRATION ONLY. Importing this module performs no scientific draw, reads no
dataset, writes no result root, injects no defect, fits no model, and has no
execution entry point. It contains the owner-locked Stage 3 design from
docs/thesis/STAGE_3_REGISTRATION.md so registration tests can prove the
machine-readable contract independently of the separate implementation runner.

The registration is prospective but not blind. Stage 1, Stage 1b, the completed
Stage 2 governed run, and the current contents of the repository's protection
surfaces were all known when this registration was written. No Stage 3
injection, draw, or outcome exists.

Three of the five registered defects are preregistered as NOT_DETECTED because
the authoritative base carries no reachable guard for them. That expectation is
recorded prospectively, before the first draw, and is not repaired here.

The registration records prospective expectations only. Registration tests may
inspect source, read the frozen dataset read-only, and prove structural facts;
they never construct an injected Stage 3 frame. Every frozen injection count in
this module is a prospective expectation to be verified by Stage 3
implementation tests, not by registration tests.
"""

from __future__ import annotations

from types import MappingProxyType


# --------------------------------------------------------------------------- #
# Namespace and authoritative pins
# --------------------------------------------------------------------------- #
STAGE3_SLUG = "defect_injection"
RESULT_ROOT = "experiments/results_thesis/defect_injection/"
REGISTRATION_DOC = "docs/thesis/STAGE_3_REGISTRATION.md"
PROTOCOL_DOC = "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md"
AUTHORITATIVE_BASE_COMMIT = "c418563f432f5b253fb3b0e69619c76608ea15ea"

# Historical registration-phase facts. The module must not create any of this.
REGISTRATION_ONLY = True
RESULT_ROOT_EXISTS_AT_REGISTRATION = False
STAGE3_RESULT_EXISTS_AT_REGISTRATION = False
NO_STAGE3_INJECTION_DRAW_OR_OUTCOME = True
NO_MAKEFILE_RUN_TARGET_AT_REGISTRATION = True
NO_GOVERNED_ROOT_OR_PROSPECTIVE_ENTRY_AT_REGISTRATION = True

# D4 — source pin. FI-DATA-EXPAND outputs are NOT Stage 3 inputs.
DATASET_PATH = "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
DATASET_SHA256 = (
    "3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78"
)
EXPANDED_DATASETS_ARE_NOT_STAGE3_INPUTS = True
EXPANDED_DATASET_RULE = (
    "Expanded or PIT-corrected datasets must use a separate versioned path and "
    "a separate prospective registration; they are not Stage 3 inputs."
)

# Frozen shape facts of the pinned source, used as containment invariants. The
# module states them; it does not read the file to obtain them.
DATASET_ROW_COUNT = 403
DATASET_COLUMN_COUNT = 61
DATASET_YEARS = (2020, 2021, 2022, 2023, 2024, 2025)
DATASET_MIN_YEAR = 2020
DATASET_ROWS_AT_MIN_YEAR = 40
DATASET_OBSERVED_TARGET_ROWS = 321
DATASET_DUPLICATE_KEYS = 0

TARGET_COLUMN = "next_year_return_pct"
KEY_COLUMNS = ("ticker", "year")
ALIGNMENT_COLUMN = "target_year"

# Source pins for the guard implementations Stage 3 evaluates. The registration
# module is not self-hashed: a source cannot contain a stable literal hash of
# its own bytes.
SOURCE_MODULE_HASHES = MappingProxyType(
    {
        "scripts/data_collection/validate.py": (
            "9c63b199adda5655fd9b53c1c66fff0b0e602af9de827553c6a74ada9cbc77ab"
        ),
        "scripts/data_collection/pipeline.py": (
            "2c75228837df46d440a323b1428d8a1a896b0db22e64708cce6d7c17a459a386"
        ),
        "scripts/data_collection/derive_alternative_targets.py": (
            "4c297bd38aa837468b95f74ab9e5893e8ad2cd1c0d589b6eeb2789b93bbc3002"
        ),
        "scripts/data_collection/split_universe_datasets.py": (
            "294d177540fe4efbfd9d231c36248c9cb5a8af4c3afe77e97efeb2cdbb37dccd"
        ),
        "scripts/data_collection/validate_universe.py": (
            "1d2b71fa143982720a0f7123bccc01c4f9032aab56179bac72390e9b8ea1fb66"
        ),
        "tests/test_pipeline_guards.py": (
            "5607c049ef69ff7c0afe073d7ebe7520b821beb4f726e60f85d71204413d098f"
        ),
        "experiments/thesis/provenance.py": (
            "5a06c5c2e753cef0fe57e348250e7847b393c6173cd54c8be273f97976dc29f8"
        ),
        "experiments/run_experiments.py": (
            "265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543"
        ),
    }
)
CELL_PROVENANCE_SOURCE = "scripts/data_collection/build_cell_provenance.py"
CELL_PROVENANCE_SHA256 = (
    "51053f267f0c9a1e5b1186f8f6ad73e72bab5c6ef59a1230bd12ee06a118b5f7"
)

# The secondary metric consumes the canonical walk-forward source. It is pinned
# by full literal SHA256 — never an abbreviation — and it is unchanged from the
# authoritative base.
RUN_EXPERIMENTS_SOURCE = "experiments/run_experiments.py"
RUN_EXPERIMENTS_SHA256 = (
    "265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543"
)
RUN_EXPERIMENTS_UNCHANGED_FROM_AUTHORITATIVE_BASE = True
RUN_EXPERIMENTS_IS_SECONDARY_CONSUMER_AUTHORITY = True

# Literal historical pins supplied by repository authority for files that this
# registration must not change. Tests compare both the working bytes and the
# authoritative-base blobs to these values; they never hash a file and compare
# that value to a second hash of the same working file.
HISTORICAL_PROTECTED_HASHES = MappingProxyType(
    {
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
)


# --------------------------------------------------------------------------- #
# D1 — closed catalogue of EXISTING protection surfaces on the authoritative
# base. No surface here was created for Stage 3. No new guard may be added
# before the first governed Stage 3 draw.
# --------------------------------------------------------------------------- #
GUARD_OBJECT_KINDS = (
    "VALIDATOR_ISSUE",
    "COMMAND_FAILURE",
    "EXISTING_TEST",
    "PROVENANCE_INTEGRITY",
)

#: Sentinel recorded when the authoritative base carries no applicable guard.
NONE_EXISTING = "NONE_EXISTING"

#: Reachability vocabulary for an existing surface, evaluated against a
#: contained (private, in-memory / private-temp-file) construction.
REACHABILITY_STATES = (
    # the surface can be executed against the contained construction and its
    # condition is satisfiable
    "REACHABLE_CONTAINED",
    # the surface executes, but its condition cannot be satisfied by any input
    "STRUCTURALLY_UNREACHABLE",
    # the surface only ever reads canonical committed paths, so a contained
    # construction cannot reach it; its silence is neither evaluation nor
    # non-detection
    "INPUT_BLIND",
)

# --------------------------------------------------------------------------- #
# Cell-provenance reachability, read from the source rather than assumed.
#
# build_cell_provenance is NOT input-blind. Its path integrity is parameterized
# on a caller-supplied root: generate(root=REPO_ROOT) and
# resolve_input(rel, root=REPO_ROOT) both accept a root, and every containment
# assertion (assert_within_repo, assert_no_symlink_ancestors, prepare_output_dir)
# is evaluated against that caller-supplied root. What is frozen is the RELATIVE
# path, not the absolute one: resolve_input admits exactly the ten members of
# ALLOWED_INPUT_RELS. A contained construction therefore reaches the module by
# materializing the declared relative inputs under a private temporary root.
# Repository authority for this pattern already exists on the authoritative
# base: tests/test_cell_provenance.py's `regenerated` fixture copies
# SOURCE_ARTIFACT_RELS into tmp_path_factory.mktemp("provenance_repo") and calls
# bcp.generate(sandbox).
# --------------------------------------------------------------------------- #
CELL_PROVENANCE_CALLABLE = "scripts.data_collection.build_cell_provenance.generate"
CELL_PROVENANCE_ROOT_PARAMETER = "root"
CELL_PROVENANCE_ROOT_DEFAULT = "build_cell_provenance.REPO_ROOT"
CELL_PROVENANCE_REQUIRED_DATASET_REL = (
    "data/trusted_clean/modeling_dataset_public_2020_2025.csv"
)
CELL_PROVENANCE_REQUIRED_INPUT_COUNT = 10
CELL_PROVENANCE_PRIVATE_ROOT_SEMANTICS = (
    "the injected frame is written to <private_root>/"
    "data/trusted_clean/modeling_dataset_public_2020_2025.csv and the other "
    "nine declared inputs of ALLOWED_INPUT_RELS are copied unmodified beneath "
    "the same private root; generate(root=<private_root>) then reads and writes "
    "only inside that root, so no canonical path is read for mutation and "
    "data/provenance is never touched"
)
CELL_PROVENANCE_PRIVATE_ROOT_PROOF = (
    "generate and resolve_input both take a caller-supplied root parameter and "
    "every path assertion is evaluated against it; only the relative path is "
    "frozen, so materializing the declared relative inputs under a private "
    "temporary root reaches the module. tests/test_cell_provenance.py's "
    "`regenerated` fixture already exercises exactly this on the authoritative "
    "base via bcp.generate(sandbox)."
)
CELL_PROVENANCE_REPOSITORY_AUTHORITY = (
    "tests/test_cell_provenance.py::regenerated"
)
CELL_PROVENANCE_CANONICAL_DATA_UNTOUCHED = True
CELL_PROVENANCE_SCHEMA_IS_COLUMN_IDENTICAL_ACROSS_DATASETS = (
    "the public and training modeling datasets carry the same 61 column names "
    "in the same order, and that set equals both COLUMN_SPECS and the "
    "feature_passports.json passport names, so the clean pinned source does not "
    "trip either frozen column-set declaration"
)

GUARD_SURFACES = MappingProxyType(
    {
        "GS_DUP_VALIDATE_ISSUE": MappingProxyType(
            {
                "kind": "VALIDATOR_ISSUE",
                "location": "scripts/data_collection/validate.py::validate",
                "condition": 'dup = df.duplicated(["ticker", "year"]).sum(); if dup',
                "signal": 'issues[] member "<n> duplicate ticker-year rows"',
                "secondary_signal": 'report["valid_for_T_to_T1_modeling"] is False',
                "reachability": "REACHABLE_CONTAINED",
                "containment_requirement": "VALIDATE_OUTPUT_REDIRECTION",
            }
        ),
        "GS_TARGET_LEAK_VALIDATE_ISSUE": MappingProxyType(
            {
                "kind": "VALIDATOR_ISSUE",
                "location": "scripts/data_collection/validate.py::validate",
                "condition": '"next_year_return_pct" in P.feature_columns(df)',
                "signal": (
                    'issues[] member "LEAKAGE: next_year_return_pct present in '
                    'feature set"'
                ),
                "reachability": "STRUCTURALLY_UNREACHABLE",
                "unreachability_proof": (
                    "pipeline.feature_columns excludes set(TARGET_COLS) by exact "
                    "name and next_year_return_pct is a member of TARGET_COLS, so "
                    "the condition is unsatisfiable for every DataFrame"
                ),
                "containment_requirement": "VALIDATE_OUTPUT_REDIRECTION",
            }
        ),
        "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE": MappingProxyType(
            {
                "kind": "VALIDATOR_ISSUE",
                "location": "scripts/data_collection/validate.py::validate",
                "condition": '"same_year_return_pct" in P.feature_columns(df)',
                "signal": (
                    'issues[] member "LEAKAGE: same_year_return_pct present in '
                    'feature set"'
                ),
                "reachability": "STRUCTURALLY_UNREACHABLE",
                "unreachability_proof": (
                    "pipeline.feature_columns excludes set(META_COLS) by exact "
                    "name and same_year_return_pct is a member of META_COLS"
                ),
                "containment_requirement": "VALIDATE_OUTPUT_REDIRECTION",
            }
        ),
        "GS_DUP_ALT_TARGETS": MappingProxyType(
            {
                "kind": "COMMAND_FAILURE",
                "location": (
                    "scripts/data_collection/derive_alternative_targets.py::"
                    "_load_modeling"
                ),
                "condition": 'frame.duplicated(["ticker", "year"]).any()',
                "signal": (
                    'ValueError("<path> contains duplicate ticker/year keys")'
                ),
                "reachability": "REACHABLE_CONTAINED",
                "containment_requirement": "PRIVATE_TEMP_CSV",
            }
        ),
        "GS_ALIGNMENT_ALT_TARGETS": MappingProxyType(
            {
                "kind": "COMMAND_FAILURE",
                "location": (
                    "scripts/data_collection/derive_alternative_targets.py::"
                    "_load_modeling"
                ),
                "condition": "not target_years.eq(years + 1).all()",
                "signal": (
                    'ValueError("modeling target_year must align exactly to '
                    'year + 1")'
                ),
                "reachability": "REACHABLE_CONTAINED",
                "scope_limitation": (
                    "label arithmetic only; it compares the target_year column "
                    "against year + 1 and never checks which year a target VALUE "
                    "was actually realized in"
                ),
                "containment_requirement": "PRIVATE_TEMP_CSV",
            }
        ),
        "GS_REQUIRED_COLUMNS_ALT_TARGETS": MappingProxyType(
            {
                "kind": "COMMAND_FAILURE",
                "location": (
                    "scripts/data_collection/derive_alternative_targets.py::"
                    "_load_modeling"
                ),
                "condition": (
                    'sorted({"ticker", "year", "target_year", '
                    '"next_year_return_pct"} - set(frame.columns))'
                ),
                "signal": 'ValueError("<path> is missing required columns: [...]")',
                "reachability": "REACHABLE_CONTAINED",
                "containment_requirement": "PRIVATE_TEMP_CSV",
            }
        ),
        "GS_LEAKAGE_PIPELINE_TEST": MappingProxyType(
            {
                "kind": "EXISTING_TEST",
                "location": (
                    "tests/test_pipeline_guards.py::"
                    "test_leakage_guards_exclude_targets_and_same_year_return_from_features"
                ),
                "condition": (
                    'not any(c.startswith("next_year_") for c in features); '
                    'quality["issues"] == []'
                ),
                "signal": "AssertionError from the named test",
                "reachability": "INPUT_BLIND",
                "input_blindness_proof": (
                    "the test reads the committed "
                    "data/trusted_clean/data_quality_report.json and never "
                    "accepts an injected frame; reaching it would require "
                    "writing into data/trusted_clean, which the containment "
                    "boundary forbids"
                ),
            }
        ),
        "GS_UNIVERSE_SPLIT_TEST": MappingProxyType(
            {
                "kind": "EXISTING_TEST",
                "location": (
                    "tests/test_pipeline_guards.py::"
                    "test_public_40_vs_expanded_training_universe_split"
                ),
                "condition": (
                    "time-invariant ticker set containment against "
                    "data/config/universe_public_40.csv and "
                    "data/config/universe_training_bist100.csv"
                ),
                "signal": "AssertionError from the named test",
                "reachability": "INPUT_BLIND",
                "input_blindness_proof": (
                    "the universe configs are ticker-keyed with no year column, "
                    "so no point-in-time membership record exists to compare "
                    "against; the test also reads canonical committed paths only"
                ),
            }
        ),
        "GS_UNIVERSE_VALIDATE_SCRIPT": MappingProxyType(
            {
                "kind": "COMMAND_FAILURE",
                "location": "scripts/data_collection/validate_universe.py",
                "condition": (
                    "assert public==40 tickers; train>=49; public subset of "
                    "train; training_only>=9"
                ),
                "signal": "AssertionError / non-zero exit",
                "reachability": "INPUT_BLIND",
                "input_blindness_proof": (
                    "the script reads three hardcoded data/trusted_clean paths "
                    "and accepts no input path; every assertion is a "
                    "time-invariant ticker-set check"
                ),
            }
        ),
        "GS_UNIVERSE_SPLIT_LEAK": MappingProxyType(
            {
                "kind": "COMMAND_FAILURE",
                "location": "scripts/data_collection/split_universe_datasets.py::main",
                "condition": (
                    "non_public_in_public = set(df_public['ticker']) - "
                    "public_tickers"
                ),
                "signal": '"[split] FATAL: non-public tickers leaked into public dataset"',
                "reachability": "INPUT_BLIND",
                "input_blindness_proof": (
                    "MODELING_CSV is a hardcoded canonical path and main() writes "
                    "into data/trusted_clean; it cannot be pointed at a contained "
                    "construction without violating the containment boundary"
                ),
            }
        ),
        "GS_CELL_PROVENANCE_DUP_KEY": MappingProxyType(
            {
                "kind": "PROVENANCE_INTEGRITY",
                "location": (
                    "scripts/data_collection/build_cell_provenance.py::build_records"
                ),
                "condition": (
                    "(ticker, year) already in seen_keys while keying dataset rows"
                ),
                "signal": 'ProvenanceError("duplicate dataset key: (...)")',
                "reachability": "REACHABLE_CONTAINED",
                "reachability_proof": CELL_PROVENANCE_PRIVATE_ROOT_PROOF,
                "containment_requirement": "PRIVATE_PROVENANCE_ROOT",
                "corrected_classification": (
                    "previously registered as INPUT_BLIND on the incorrect premise "
                    "that resolve_input admits no caller-supplied root; the module "
                    "takes root as a parameter, so the surface is reachable inside "
                    "a private provenance root and its silence would be a real "
                    "non-detection rather than a non-evaluation"
                ),
            }
        ),
        "GS_CELL_PROVENANCE_COLUMN_COVERAGE": MappingProxyType(
            {
                "kind": "PROVENANCE_INTEGRITY",
                "location": (
                    "scripts/data_collection/build_cell_provenance.py::generate"
                ),
                "condition": (
                    "set(v1_classes) != set(dataset_columns) in generate; and "
                    "sorted(c for c in dataset_columns if c not in COLUMN_SPECS) "
                    "in build_records"
                ),
                "signal": (
                    'ProvenanceError("passports v1 does not cover exactly the '
                    'dataset columns")'
                ),
                "secondary_signal": (
                    'ProvenanceError("columns absent from the frozen resolution '
                    "table: ['leaked_next_year_return_pct']\")"
                ),
                "signal_precedence": (
                    "generate evaluates the passports-coverage condition before it "
                    "calls build_records, so an undeclared column raises the "
                    "passports-coverage error first; the frozen-resolution-table "
                    "error is the same fact restated at the build_records entry "
                    "checks and is raised when build_records is reached or invoked "
                    "directly"
                ),
                "reachability": "REACHABLE_CONTAINED",
                "reachability_proof": CELL_PROVENANCE_PRIVATE_ROOT_PROOF,
                "evaluation_checkpoint": (
                    "the two frozen column-set declarations, both of which are "
                    "evaluated before any cell is resolved and before any lineage "
                    "validation"
                ),
                "containment_requirement": "PRIVATE_PROVENANCE_ROOT",
            }
        ),
        "GS_CELL_PROVENANCE_LINEAGE_CLOSURE": MappingProxyType(
            {
                "kind": "PROVENANCE_INTEGRITY",
                "location": (
                    "scripts/data_collection/build_cell_provenance.py::"
                    "validate_records"
                ),
                "condition": "parent not in graph for a named upstream cell",
                "signal": (
                    'ProvenanceError("upstream cell not present in the artifact: '
                    '<cell_id>")'
                ),
                "reachability": "REACHABLE_CONTAINED",
                "reachability_proof": CELL_PROVENANCE_PRIVATE_ROOT_PROOF,
                "containment_requirement": "PRIVATE_PROVENANCE_ROOT",
                "registered_as_detection_signal": False,
                "fires_on_clean_comparator_for_the_pinned_source": True,
                "not_a_detection_signal_proof": (
                    "upstream_cells_for gates a lineage hop on the dataset-wide "
                    "present_years set rather than on the per-ticker year set, so "
                    "it names a price_adjclose_t / benchmark cell for a "
                    "(ticker, year) pair that need not exist. The public dataset "
                    "the tool declares is a complete 40-ticker x 6-year grid, so "
                    "the closure holds there. The pinned Stage 3 source is the "
                    "training dataset: 81 tickers, 403 rows, minimum 3 years per "
                    "ticker, an incomplete grid. This condition therefore fires "
                    "identically on the clean comparator and on every injected "
                    "frame, carries no information about any injection, and is "
                    "registered as a known baseline terminal state — never as a "
                    "detection signal and never as a containment failure"
                ),
            }
        ),
    }
)

#: Fixed set of the provenance surfaces reached through a private provenance
#: root. Registered so no implementation may quietly widen or narrow them.
CELL_PROVENANCE_SURFACES = (
    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
    "GS_CELL_PROVENANCE_DUP_KEY",
    "GS_CELL_PROVENANCE_LINEAGE_CLOSURE",
)
PROVENANCE_LINEAGE_CLOSURE_IS_NOT_A_DETECTION_SIGNAL = True
PROVENANCE_SURFACE_WAS_MISCLASSIFIED_AT_FIRST_REGISTRATION_DRAFT = True

#: An INPUT_BLIND surface staying silent is neither an evaluation nor a
#: non-detection. Recording one as "did not fire" would convert an invalid
#: evaluation into evidence of guard adequacy.
INPUT_BLIND_SILENCE_IS_NOT_EVALUATION = True
INPUT_BLIND_SILENCE_IS_NOT_NON_DETECTION = True
NO_NEW_GUARD_BEFORE_FIRST_DRAW = True
NO_GUARD_REPAIR_BEFORE_FIRST_DRAW = True
GUARD_REPAIR_BELONGS_TO_SEPARATE_REMEDIATION_STAGE = True
FIRST_DRAW_ARTIFACTS_ARE_IMMUTABLE = True


# --------------------------------------------------------------------------- #
# D3 / D5 — closed first-draw defect family and registered IDs
# --------------------------------------------------------------------------- #
DEFECT_FAMILY = (
    "FUTURE_YEAR_FEATURE_LEAKAGE",
    "T_TPLUS1_MISALIGNMENT",
    "TARGET_LEAKAGE_INTO_FEATURES",
    "LOOKAHEAD_UNIVERSE_MEMBERSHIP",
    "DUPLICATE_ROW_INFLATION",
)
DEFECT_FAMILY_SIZE = 5
DEFECT_FAMILY_IS_CLOSED = True
NO_ADDITIONAL_DEFECT_CLASS_IN_FIRST_DRAW = True
INJECTIONS_PER_DEFECT_CLASS = 1
NO_SEVERITY_GRID = True
NO_REPEATED_PERFORMANCE_EXPERIMENT = True

DEFECT_IDS = MappingProxyType(
    {
        "FUTURE_YEAR_FEATURE_LEAKAGE": 4000,
        "T_TPLUS1_MISALIGNMENT": 4001,
        "TARGET_LEAKAGE_INTO_FEATURES": 4002,
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP": 4003,
        "DUPLICATE_ROW_INFLATION": 4004,
    }
)
ALL_STAGE3_IDS = (4000, 4001, 4002, 4003, 4004)
STAGE3_ID_RANGE = (4000, 4004)


# --------------------------------------------------------------------------- #
# D5 / 9 — seed schedule. No ID may collide with an earlier stage's IDs.
# --------------------------------------------------------------------------- #
BASE_SEED = 42
PROVENANCE_SEED_SOURCE = 'provenance.SEEDS["defect_injection"]'
STAGE_1_IDS = tuple(range(0, 200))
STAGE_1B_IDS = tuple(range(200, 600))
RESERVED_IDS = tuple(range(600, 1000))
STAGE_2_IDS = tuple(range(1000, 4000))
FORBIDDEN_ID_RANGES = MappingProxyType(
    {
        "STAGE_1": (0, 199),
        "STAGE_1B": (200, 599),
        "RESERVED": (600, 999),
        "STAGE_2": (1000, 3999),
    }
)
STAGE3_SEED_FORMULA = "BASE_SEED * 1_000_003 + defect_id"
STAGE3_SEED_VALUES = MappingProxyType(
    {
        4000: 42004126,
        4001: 42004127,
        4002: 42004128,
        4003: 42004129,
        4004: 42004130,
    }
)


def injection_seed(defect_id: int) -> int:
    """Return the frozen injection seed without drawing any random value."""
    return BASE_SEED * 1_000_003 + defect_id


#: Every first-draw injection is fully deterministic. The formula above is
#: frozen so that no implementation may invent one later, but it is unused in
#: the first governed draw. An implementation that consumes an RNG for any of
#: the five registered defects is an integrity failure, not a design choice.
NO_RNG = "NO_RNG"
RNG_USAGE = MappingProxyType(
    {
        "FUTURE_YEAR_FEATURE_LEAKAGE": NO_RNG,
        "T_TPLUS1_MISALIGNMENT": NO_RNG,
        "TARGET_LEAKAGE_INTO_FEATURES": NO_RNG,
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP": NO_RNG,
        "DUPLICATE_ROW_INFLATION": NO_RNG,
    }
)
ALL_INJECTIONS_ARE_DETERMINISTIC = True
RNG_CONSUMPTION_IN_FIRST_DRAW_IS_INTEGRITY_FAILURE = True


# --------------------------------------------------------------------------- #
# 3 — injection safety and containment
# --------------------------------------------------------------------------- #
CONTAINMENT_MODES = (
    "IN_MEMORY_FRAME",
    "PRIVATE_TEMP_CSV",
    "VALIDATE_OUTPUT_REDIRECTION",
    "PRIVATE_PROVENANCE_ROOT",
)
CLEAN_COMPARATOR = (
    "a fresh pandas.read_csv of the pinned source, whose SHA256 is verified "
    "immediately before and after every defect, evaluated through the same "
    "registered surfaces and required to emit zero registered detection signals"
)
CLEAN_COMPARATOR_FIRES_ANY_SIGNAL = "INCONCLUSIVE"
RESTORATION_POLICY = (
    "every mutation is confined to a private in-memory copy and, where a "
    "registered surface requires a file, to a private temporary directory "
    "created outside data/ and outside experiments/results_thesis/; the "
    "directory is removed and every redirected module attribute is restored on "
    "ALL exit paths, including exception paths"
)
FAILURE_BEHAVIOR = (
    "a defect whose containment cannot be established, whose restoration fails, "
    "or whose registered surfaces cannot all be executed exactly as registered "
    "is INCONCLUSIVE; it is never recorded as NOT_DETECTED and never recorded "
    "as DETECTED"
)
#: PRIVATE_PROVENANCE_ROOT is the containment mode for the cell-provenance
#: surfaces: the ten declared relative inputs are materialized under a private
#: temporary root, the injected frame taking the declared dataset relative path,
#: and generate(root=<private root>) reads and writes only inside that root.
PRIVATE_PROVENANCE_ROOT_REQUIREMENT = CELL_PROVENANCE_PRIVATE_ROOT_SEMANTICS
FORBIDDEN_MUTATION_TARGETS = (
    "data/trusted",
    "data/trusted_raw",
    "data/trusted_clean",
    "data/config",
    "data/provenance",
    "experiments/results_thesis/positive_control",
    "experiments/results_thesis/positive_control_calibration",
    "experiments/results_thesis/negative_control",
    "scripts/",
    "experiments/ except experiments/results_thesis/defect_injection/",
    "tests/",
)

#: validate() writes four report files into data/trusted_clean. Any evaluation
#: of a validator-issue surface MUST redirect all four to the private temporary
#: directory first and restore them afterwards; evaluating it by writing into
#: data/trusted_clean is forbidden and makes the defect INCONCLUSIVE instead.
VALIDATE_REDIRECTED_ATTRIBUTES = (
    "scripts.data_collection.pipeline.QUALITY_JSON",
    "scripts.data_collection.pipeline.QUALITY_MD",
    "scripts.data_collection.validate.FEATURE_JSON",
    "scripts.data_collection.validate.FEATURE_MD",
)
VALIDATE_READS_REFERENCE_CSV = "data/trusted/stocks_2020_2025.csv"
VALIDATE_REFERENCE_READ_IS_READ_ONLY = True
CANONICAL_DIGESTS_REVERIFIED_AFTER_EACH_DEFECT = (
    "data/trusted_clean/modeling_dataset_training_2020_2025.csv",
    "data/trusted_clean/data_quality_report.json",
    "data/trusted_clean/data_quality_report.md",
    "data/trusted_clean/feature_engineering_report.json",
    "data/trusted_clean/feature_engineering_report.md",
)


# --------------------------------------------------------------------------- #
# D1 / 2 / 4-8 — the frozen guard map. One closed record per defect class.
#
# EXPECTED_GUARD is either a GUARD_SURFACES key or the NONE_EXISTING sentinel.
# EVALUATED_SURFACES are the existing surfaces that MUST be executed for the
# defect so the draw is not vacuous. DETECTION is decided by whether any
# preregistered EXACT_DETECTION_SIGNAL is actually emitted before any model or
# significance evaluation, not by whether the expectation was met.
# --------------------------------------------------------------------------- #
DETECTED = "DETECTED"
NOT_DETECTED = "NOT_DETECTED"
NO_DETECTION_SIGNAL = "NONE"
INCONCLUSIVE = "INCONCLUSIVE"


# --------------------------------------------------------------------------- #
# D8 — 4001 primary-target consumer boundary.
#
# The 4001 injection rotates observed next_year_return_pct within ticker and
# recomputes nothing. The six other derived next_year_* target columns are
# therefore STALE COLLATERAL. They are disclosed here and fenced out of the
# Stage 3 estimand by an executable boundary, not by convention.
# --------------------------------------------------------------------------- #
PRIMARY_TARGET_COLUMN = "next_year_return_pct"
STALE_DERIVED_TARGET_COLUMNS = (
    "next_year_rank_by_return",
    "next_year_return_percentile",
    "next_year_top_10pct_returner",
    "next_year_top_20pct_returner",
    "next_year_excess_return_vs_bist100",
    "next_year_outperform_bist100",
)
STALE_COLLATERAL_FORBIDDEN_ROLES = (
    "predictor",
    "alternate target",
    "alignment authority",
    "detection signal",
    "secondary IC input",
)
STALE_COLLATERAL_CONSUMPTION_RESULT = INCONCLUSIVE
CONSUMER_BOUNDARY_4001 = MappingProxyType(
    {
        "PRIMARY_DETECTION_INPUTS": (
            "only the registered guard surfaces named in EVALUATED_SURFACES"
        ),
        "SECONDARY_IC_INPUTS": (
            "only the canonical predictor features selected by "
            "experiments.run_experiments._feature_cols, plus "
            "next_year_return_pct as the single target"
        ),
        "FORBIDDEN_COLUMNS": STALE_DERIVED_TARGET_COLUMNS,
        "FORBIDDEN_ROLES": STALE_COLLATERAL_FORBIDDEN_ROLES,
        "VIOLATION_RESULT": INCONCLUSIVE,
        "VIOLATION_RULE": (
            "if any implementation path consumes a stale derived next_year_* "
            "target column as predictor, alternate target, alignment authority, "
            "detection signal, or secondary IC input, defect 4001 is classified "
            "INCONCLUSIVE — never DETECTED and never NOT_DETECTED"
        ),
        "REPOSITORY_AUTHORITY": (
            "experiments.run_experiments._feature_cols excludes every column "
            "whose name starts with next_year_, so no next_year_* column — "
            "primary or stale derived — can enter the canonical model input; the "
            "registered secondary target is pinned to the single literal "
            "next_year_return_pct"
        ),
    }
)

GUARD_MAP = MappingProxyType(
    {
        "FUTURE_YEAR_FEATURE_LEAKAGE": MappingProxyType(
            {
                "DEFECT_ID": 4000,
                "DEFECT_NAME": "FUTURE_YEAR_FEATURE_LEAKAGE",
                "CLEAN_BASELINE_CONDITION": (
                    "every total_assets cell at (ticker, T) holds the year-T "
                    "reported value of the pinned source; no registered surface "
                    "emits a signal on the clean comparator"
                ),
                "EXACT_INJECTION_MECHANISM": (
                    "in a private in-memory copy, for every row (ticker, T) that "
                    "has a partner row (ticker, T+1) inside the frame, overwrite "
                    "total_assets with the frame's total_assets value at "
                    "(ticker, T+1); rows without a T+1 partner keep the clean "
                    "value"
                ),
                "ROW_UNIVERSE": "all 403 rows; none added, none removed",
                "COLUMNS_MODIFIED": ("total_assets",),
                "RELATIONSHIP_MODIFIED": (
                    "the year-of-record of a feature value: a year-T feature cell "
                    "carries a year-T+1 observation of the same feature"
                ),
                "DISTINCTNESS_FROM_TARGET_LEAKAGE": (
                    "the leaked variable is a feature column, sourced from the "
                    "same feature one year ahead; the target column is not "
                    "copied, not read, and not a function of the injected value"
                ),
                "EXPECTED_ROWS_RECEIVING_A_FUTURE_VALUE": 322,
                "EXPECTED_ROWS_CHANGING_VALUE": 202,
                "CONTAINMENT_BOUNDARY": (
                    "IN_MEMORY_FRAME",
                    "PRIVATE_TEMP_CSV",
                    "VALIDATE_OUTPUT_REDIRECTION",
                    "PRIVATE_PROVENANCE_ROOT",
                ),
                "EXPECTED_GUARD": NONE_EXISTING,
                "EVALUATED_SURFACES": (
                    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
                    "GS_DUP_ALT_TARGETS",
                    "GS_ALIGNMENT_ALT_TARGETS",
                    "GS_DUP_VALIDATE_ISSUE",
                    "GS_TARGET_LEAK_VALIDATE_ISSUE",
                    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
                    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                    "GS_CELL_PROVENANCE_DUP_KEY",
                ),
                "GUARD_GAP_REASON": (
                    "no surface on the authoritative base compares a feature cell "
                    "against its upstream year-of-record; the alignment guard "
                    "checks only the target_year column arithmetic, and cell "
                    "provenance is reachable through a private provenance root "
                    "but only declares column coverage, key uniqueness and "
                    "lineage closure — never the year-of-record of a value — so "
                    "a value-for-value overwrite passes both of its reachable "
                    "conditions unchanged"
                ),
                "EXACT_DETECTION_SIGNAL": NO_DETECTION_SIGNAL,
                "EXPECTED_RESULT": NOT_DETECTED,
                "SECONDARY_IC_APPLICABLE": True,
                "INTEGRITY_INVARIANTS": (
                    "pinned source SHA256 unchanged before and after",
                    "row count 403 and column count 61 unchanged",
                    "no duplicate (ticker, year) key created",
                    "target_year == year + 1 on every row",
                    "next_year_return_pct byte-identical to the clean comparator",
                    "exactly one column differs from the clean comparator",
                    "exactly 202 rows' total_assets differ from the clean value",
                    "no null introduced or removed in total_assets",
                ),
            }
        ),
        "T_TPLUS1_MISALIGNMENT": MappingProxyType(
            {
                "DEFECT_ID": 4001,
                "DEFECT_NAME": "T_TPLUS1_MISALIGNMENT",
                "CLEAN_BASELINE_CONDITION": (
                    "the next_year_return_pct on row (ticker, T) is that ticker's "
                    "realized return in T+1, and target_year == year + 1 on every "
                    "row; no registered surface emits a signal on the clean "
                    "comparator"
                ),
                "EXACT_INJECTION_MECHANISM": (
                    "in a private in-memory copy, for each ticker take the "
                    "ascending-year ordered subsequence of rows whose "
                    "next_year_return_pct is observed (non-null), of length k, and "
                    "cyclically rotate those observed values forward by exactly "
                    "one position: v_new[i] = v_old[(i - 1) mod k]; no other "
                    "column is touched"
                ),
                "ROW_UNIVERSE": "all 403 rows; none added, none removed",
                "COLUMNS_MODIFIED": ("next_year_return_pct",),
                "RELATIONSHIP_MODIFIED": (
                    "the temporal association between the feature row (ticker, T) "
                    "and the year in which its attached outcome was realized"
                ),
                "DERIVED_TARGET_COLUMNS_NOT_RECOMPUTED": (
                    "next_year_rank_by_return",
                    "next_year_return_percentile",
                    "next_year_top_10pct_returner",
                    "next_year_top_20pct_returner",
                    "next_year_excess_return_vs_bist100",
                    "next_year_outperform_bist100",
                ),
                "EXPECTED_ROWS_CHANGING_VALUE": 320,
                "DERIVED_COLUMN_RULE": (
                    "the derived target columns are deliberately NOT recomputed; "
                    "recomputation would be a second, unregistered modification. "
                    "No implementation may recompute them."
                ),
                "DERIVED_COLUMN_DISCLOSURE": (
                    "leaving them un-recomputed makes them STALE COLLATERAL: they "
                    "still carry values consistent with the clean target and "
                    "inconsistent with the rotated one. This is disclosed, not "
                    "repaired, and stale collateral is forbidden from influencing "
                    "the Stage 3 estimand."
                ),
                "STALE_COLLATERAL_IS_FORBIDDEN_FROM_THE_ESTIMAND": True,
                "CONSUMER_BOUNDARY": CONSUMER_BOUNDARY_4001,
                "DISTINCTNESS": (
                    "not target leakage: the target is not copied into any "
                    "feature. Not duplicate-row inflation: the row universe, the "
                    "key columns, target_year, has_target, is_inference_row, the "
                    "null locations, and the per-ticker target multiset are all "
                    "preserved exactly."
                ),
                "CONTAINMENT_BOUNDARY": (
                    "IN_MEMORY_FRAME",
                    "PRIVATE_TEMP_CSV",
                    "VALIDATE_OUTPUT_REDIRECTION",
                    "PRIVATE_PROVENANCE_ROOT",
                ),
                "EXPECTED_GUARD": NONE_EXISTING,
                "EVALUATED_SURFACES": (
                    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
                    "GS_DUP_ALT_TARGETS",
                    "GS_ALIGNMENT_ALT_TARGETS",
                    "GS_DUP_VALIDATE_ISSUE",
                    "GS_TARGET_LEAK_VALIDATE_ISSUE",
                    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
                    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                    "GS_CELL_PROVENANCE_DUP_KEY",
                ),
                "GUARD_GAP_REASON": (
                    "GS_ALIGNMENT_ALT_TARGETS is the only alignment surface on the "
                    "authoritative base and it compares the target_year column "
                    "against year + 1. This injection leaves target_year exactly "
                    "as it was, so the label arithmetic still holds while the "
                    "value provenance is wrong. No surface verifies which year a "
                    "target value was realized in. The reachable cell-provenance "
                    "surfaces do not close the gap either: the column set, the "
                    "(ticker, year) key set and the lineage graph are all "
                    "unchanged by a within-ticker rotation of observed values."
                ),
                "EXACT_DETECTION_SIGNAL": NO_DETECTION_SIGNAL,
                "EXPECTED_RESULT": NOT_DETECTED,
                "SECONDARY_IC_APPLICABLE": True,
                "INTEGRITY_INVARIANTS": (
                    "pinned source SHA256 unchanged before and after",
                    "row count 403 and column count 61 unchanged",
                    "no duplicate (ticker, year) key created",
                    "target_year == year + 1 on every row",
                    "null locations of next_year_return_pct byte-identical to clean",
                    "has_target and is_inference_row identical to clean",
                    "per-ticker multiset of observed target values identical to clean",
                    "observed-target row count still 321",
                    "exactly 320 rows' next_year_return_pct differ from clean",
                    "every feature column identical to clean",
                ),
            }
        ),
        "TARGET_LEAKAGE_INTO_FEATURES": MappingProxyType(
            {
                "DEFECT_ID": 4002,
                "DEFECT_NAME": "TARGET_LEAKAGE_INTO_FEATURES",
                "CLEAN_BASELINE_CONDITION": (
                    "no column outside TARGET_COLS carries the target value, and "
                    "pipeline.feature_columns of the clean frame contains no "
                    "copy of next_year_return_pct; no registered surface emits a "
                    "signal on the clean comparator"
                ),
                "EXACT_INJECTION_MECHANISM": (
                    "in a private in-memory copy, add exactly one new column "
                    "named leaked_next_year_return_pct whose value on every row "
                    "equals that row's next_year_return_pct, nulls preserved "
                    "exactly; no existing column is modified and no row is added"
                ),
                "ROW_UNIVERSE": "all 403 rows; none added, none removed",
                "COLUMNS_MODIFIED": (),
                "COLUMNS_ADDED": ("leaked_next_year_return_pct",),
                "RELATIONSHIP_MODIFIED": (
                    "the target value becomes available inside the feature set"
                ),
                "COLUMN_NAME_RATIONALE": (
                    "the name is not in IDENTITY_COLS, TARGET_COLS or META_COLS "
                    "and does not start with next_year_, so it enters "
                    "pipeline.feature_columns under the repository's own feature "
                    "rule and experiments.run_experiments._feature_cols under the "
                    "secondary metric's canonical model-input rule, without "
                    "relying on any name-prefix accident. This is the smallest "
                    "canonical target-to-feature perturbation; it does not broaden "
                    "into arbitrary future variables."
                ),
                "CONTAINMENT_BOUNDARY": (
                    "IN_MEMORY_FRAME",
                    "PRIVATE_TEMP_CSV",
                    "VALIDATE_OUTPUT_REDIRECTION",
                    "PRIVATE_PROVENANCE_ROOT",
                ),
                "EXPECTED_GUARD": "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                "EVALUATED_SURFACES": (
                    "GS_TARGET_LEAK_VALIDATE_ISSUE",
                    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
                    "GS_DUP_VALIDATE_ISSUE",
                    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
                    "GS_DUP_ALT_TARGETS",
                    "GS_ALIGNMENT_ALT_TARGETS",
                    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                    "GS_CELL_PROVENANCE_DUP_KEY",
                ),
                "NAMED_SURFACE_FOR_THIS_CLASS": "GS_TARGET_LEAK_VALIDATE_ISSUE",
                "NAMED_SURFACE_REMAINS_STRUCTURALLY_UNREACHABLE": (
                    "GS_TARGET_LEAK_VALIDATE_ISSUE is the surface the repository "
                    "names for this defect class and it stays STRUCTURALLY "
                    "UNREACHABLE: its condition tests the exact literal name "
                    "next_year_return_pct against pipeline.feature_columns, which "
                    "removes that exact name unconditionally. The condition is "
                    "unsatisfiable for every DataFrame, so no value-carrying copy "
                    "under any other name can trigger it. The prefix-based check "
                    "in GS_LEAKAGE_PIPELINE_TEST is INPUT_BLIND: it reads the "
                    "committed quality report, not an injected frame. This is a "
                    "separate guard-surface fact and it is not repaired here; "
                    "detection for this defect comes from a different existing "
                    "surface."
                ),
                "DETECTING_SURFACE_RATIONALE": (
                    "the injected column is an undeclared column. "
                    "build_cell_provenance freezes the dataset's column set twice "
                    "— once as the feature_passports.json passport names in "
                    "generate, once as COLUMN_SPECS in build_records — and "
                    "leaked_next_year_return_pct is absent from both. Reached "
                    "through a private provenance root, the module fails closed "
                    "on the added column before it resolves a single cell. This "
                    "is an existing provenance/schema guard, registered as found; "
                    "no guard was added or repaired."
                ),
                "EXACT_DETECTION_SIGNAL": (
                    'ProvenanceError raised by build_cell_provenance.generate '
                    'whose message is exactly "passports v1 does not cover '
                    'exactly the dataset columns"',
                    "ProvenanceError raised by "
                    "build_cell_provenance.build_records whose message is exactly "
                    "\"columns absent from the frozen resolution table: "
                    "['leaked_next_year_return_pct']\"",
                ),
                "DETECTION_RULE": (
                    "detection counts if at least one of the two registered "
                    "signals is emitted before any model or significance "
                    "evaluation; generate reaches the passports-coverage "
                    "condition first, so that signal is the expected one and the "
                    "frozen-resolution-table signal is recorded when reached"
                ),
                "EVALUATION_CHECKPOINT": (
                    "both registered signals are decided at the frozen column-set "
                    "declarations, which generate evaluates before any cell is "
                    "resolved and before validate_records runs. The later "
                    "GS_CELL_PROVENANCE_LINEAGE_CLOSURE condition fires on the "
                    "clean comparator for the pinned training source and is "
                    "registered as a baseline terminal state, not a signal and "
                    "not a containment failure."
                ),
                "EXPECTED_RESULT": DETECTED,
                "SECONDARY_IC_APPLICABLE": False,
                "INTEGRITY_INVARIANTS": (
                    "pinned source SHA256 unchanged before and after",
                    "row count 403 unchanged; column count 62 in the injected frame",
                    "no duplicate (ticker, year) key created",
                    "target_year == year + 1 on every row",
                    "every pre-existing column byte-identical to the clean comparator",
                    "leaked_next_year_return_pct equals next_year_return_pct on "
                    "every row including null positions",
                    "leaked_next_year_return_pct is a member of "
                    "pipeline.feature_columns of the injected frame",
                    "leaked_next_year_return_pct is a member of "
                    "experiments.run_experiments._feature_cols of the injected frame",
                ),
            }
        ),
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP": MappingProxyType(
            {
                "DEFECT_ID": 4003,
                "DEFECT_NAME": "LOOKAHEAD_UNIVERSE_MEMBERSHIP",
                "CLEAN_BASELINE_CONDITION": (
                    "universe membership is the ticker-level, time-invariant "
                    "assignment produced by split_universe_datasets from "
                    "data/config/universe_*.csv, and no row's membership depends "
                    "on any outcome realized after year T; no registered surface "
                    "emits a signal on the clean comparator"
                ),
                "EXACT_INJECTION_MECHANISM": (
                    "in a private in-memory copy, for each target_year compute the "
                    "median of the observed next_year_return_pct values in that "
                    "target_year using pandas.Series.median(); mark a row a member "
                    "iff its next_year_return_pct is null OR its "
                    "next_year_return_pct >= that target_year median; set "
                    "is_training_universe and is_public_universe to the membership "
                    "flag; set universe_source to lookahead_survivor for members "
                    "and lookahead_dropped for non-members; then restrict the "
                    "frame to member rows, exactly as split_universe_datasets "
                    "derives a universe dataset from a membership flag"
                ),
                "ROW_UNIVERSE": (
                    "restricted to look-ahead members; rows are only removed, "
                    "never added and never duplicated"
                ),
                "COLUMNS_MODIFIED": (
                    "is_training_universe",
                    "is_public_universe",
                    "universe_source",
                ),
                "RELATIONSHIP_MODIFIED": (
                    "universe membership at year T is decided using the realized "
                    "T+1 outcome, which is not knowable at T"
                ),
                "NULL_TARGET_ROW_RULE": (
                    "rows whose target is unobserved are retained, because an "
                    "unobservable outcome cannot be selected on; the look-ahead "
                    "selection applies only to rows with an observed target"
                ),
                "TIE_RULE": "median comparison is >= (ties are retained as members)",
                "EXPECTED_MEMBER_ROWS": 243,
                "EXPECTED_DROPPED_ROWS": 160,
                "NO_CANONICAL_DATASET_CHANGE": True,
                "CONTAINMENT_BOUNDARY": (
                    "IN_MEMORY_FRAME",
                    "PRIVATE_TEMP_CSV",
                    "VALIDATE_OUTPUT_REDIRECTION",
                    "PRIVATE_PROVENANCE_ROOT",
                ),
                "EXPECTED_GUARD": NONE_EXISTING,
                "EVALUATED_SURFACES": (
                    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
                    "GS_DUP_ALT_TARGETS",
                    "GS_ALIGNMENT_ALT_TARGETS",
                    "GS_DUP_VALIDATE_ISSUE",
                    "GS_TARGET_LEAK_VALIDATE_ISSUE",
                    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
                    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                    "GS_CELL_PROVENANCE_DUP_KEY",
                ),
                "INPUT_BLIND_SURFACES_NOT_EVALUATED": (
                    "GS_UNIVERSE_SPLIT_TEST",
                    "GS_UNIVERSE_VALIDATE_SCRIPT",
                    "GS_UNIVERSE_SPLIT_LEAK",
                ),
                "GUARD_GAP_REASON": (
                    "the repository holds no point-in-time universe-membership "
                    "record: data/config/universe_public_40.csv and "
                    "data/config/universe_training_bist100.csv are ticker-keyed "
                    "with no year column, so no surface can distinguish membership "
                    "known at T from membership decided with T+1 information. "
                    "Every existing universe surface is additionally INPUT_BLIND: "
                    "each reads hardcoded canonical paths and none accepts an "
                    "injected frame. Their silence is recorded as NOT EVALUATED, "
                    "never as non-detection. The reachable cell-provenance "
                    "surfaces are evaluated and are silent by construction: "
                    "dropping rows changes neither the column set nor the "
                    "uniqueness of the (ticker, year) key, and provenance records "
                    "no membership semantics at all."
                ),
                "EXACT_DETECTION_SIGNAL": NO_DETECTION_SIGNAL,
                "EXPECTED_RESULT": NOT_DETECTED,
                "SECONDARY_IC_APPLICABLE": True,
                "INTEGRITY_INVARIANTS": (
                    "pinned source SHA256 unchanged before and after",
                    "data/config/universe_public_40.csv unchanged",
                    "data/config/universe_training_bist100.csv unchanged",
                    "no row added and no duplicate (ticker, year) key created",
                    "target_year == year + 1 on every retained row",
                    "every feature and target VALUE on a retained row identical to "
                    "the clean comparator",
                    "only the three membership columns differ in value",
                    "exactly 243 rows retained and 160 rows removed",
                ),
            }
        ),
        "DUPLICATE_ROW_INFLATION": MappingProxyType(
            {
                "DEFECT_ID": 4004,
                "DEFECT_NAME": "DUPLICATE_ROW_INFLATION",
                "CLEAN_BASELINE_CONDITION": (
                    "the pinned source has zero duplicated (ticker, year) keys and "
                    "no registered surface emits a signal on the clean comparator"
                ),
                "EXACT_INJECTION_MECHANISM": (
                    "in a private in-memory copy, append an exact copy of every "
                    "row whose year equals the minimum year present in the pinned "
                    "source (2020), preserving every column value including the "
                    "key columns; the duplicates are appended after the original "
                    "rows and no value is altered"
                ),
                "ROW_UNIVERSE": (
                    "403 clean rows plus 40 appended duplicates = 443 rows; the "
                    "duplicated block is fully determined by year == 2020, so "
                    "there is no sampling and no ambiguity"
                ),
                "COLUMNS_MODIFIED": (),
                "RELATIONSHIP_MODIFIED": (
                    "the (ticker, year) key stops being unique and the 2020 "
                    "feature year is double-weighted"
                ),
                "CONTAINMENT_BOUNDARY": (
                    "IN_MEMORY_FRAME",
                    "PRIVATE_TEMP_CSV",
                    "VALIDATE_OUTPUT_REDIRECTION",
                    "PRIVATE_PROVENANCE_ROOT",
                ),
                "EXPECTED_GUARD": "GS_DUP_ALT_TARGETS",
                "CONFIRMING_GUARD": "GS_DUP_VALIDATE_ISSUE",
                "CONFIRMING_PROVENANCE_GUARD": "GS_CELL_PROVENANCE_DUP_KEY",
                "EVALUATED_SURFACES": (
                    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
                    "GS_DUP_ALT_TARGETS",
                    "GS_DUP_VALIDATE_ISSUE",
                    "GS_TARGET_LEAK_VALIDATE_ISSUE",
                    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
                    "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                    "GS_CELL_PROVENANCE_DUP_KEY",
                ),
                "FAIL_FAST_SURFACE_NOT_EVALUATED": "GS_ALIGNMENT_ALT_TARGETS",
                "FAIL_FAST_REASON": (
                    "derive_alternative_targets._load_modeling raises at the "
                    "registered duplicate-key check before control can reach its "
                    "later target_year alignment condition; that later condition "
                    "is therefore not part of this defect's EVALUATED_SURFACES"
                ),
                "EXACT_DETECTION_SIGNAL": (
                    "ValueError raised by "
                    "derive_alternative_targets._load_modeling whose message ends "
                    'with " contains duplicate ticker/year keys"',
                    'validate() issues[] containing the exact string "40 duplicate '
                    'ticker-year rows" with '
                    'report["valid_for_T_to_T1_modeling"] is False',
                    "ProvenanceError raised by "
                    "build_cell_provenance.build_records whose message starts "
                    'with "duplicate dataset key: "',
                ),
                "DETECTION_RULE": (
                    "detection counts if at least one of the three registered "
                    "signals is emitted before any model or significance "
                    "evaluation; all three are recorded"
                ),
                "EXPECTED_RESULT": DETECTED,
                "SECONDARY_IC_APPLICABLE": False,
                "INTEGRITY_INVARIANTS": (
                    "pinned source SHA256 unchanged before and after",
                    "injected frame has 443 rows and 61 columns",
                    "exactly 40 duplicated (ticker, year) keys",
                    "every duplicated row is value-identical to its original",
                    "target_year == year + 1 on every row",
                    "the first 403 rows are byte-identical to the clean comparator",
                ),
            }
        ),
    }
)

EXPECTED_DETECTION = MappingProxyType(
    {
        "FUTURE_YEAR_FEATURE_LEAKAGE": NOT_DETECTED,
        "T_TPLUS1_MISALIGNMENT": NOT_DETECTED,
        "TARGET_LEAKAGE_INTO_FEATURES": DETECTED,
        "LOOKAHEAD_UNIVERSE_MEMBERSHIP": NOT_DETECTED,
        "DUPLICATE_ROW_INFLATION": DETECTED,
    }
)
EXPECTED_GUARD_GAPS = (
    "FUTURE_YEAR_FEATURE_LEAKAGE",
    "T_TPLUS1_MISALIGNMENT",
    "LOOKAHEAD_UNIVERSE_MEMBERSHIP",
)
EXPECTED_FIRST_DRAW_DECISION = "FAIL"
EXPECTED_FIRST_DRAW_OUTCOME = "FAIL — INFORMATIVE"
EXPECTED_FAIL_IS_INFORMATIVE = True
EXPECTED_FIRST_DRAW_OUTCOME_IS_PROSPECTIVE = True
EXPECTED_FIRST_DRAW_OUTCOME_IS_OBSERVED = False
EXPECTATION_DOES_NOT_CHANGE_THE_PASS_RULE = True
DETECTION_IS_DECIDED_BY_EMITTED_SIGNAL_NOT_BY_EXPECTATION = True


# --------------------------------------------------------------------------- #
# D5 — primary estimand, gate, and secondary metric
# --------------------------------------------------------------------------- #
PRIMARY_ESTIMAND = (
    "binary guard detection per defect class: whether a preregistered existing "
    "guard emits its exact registered detection signal for the completed "
    "registered injection, before any model or significance evaluation"
)
DETECTION_MUST_PRECEDE_MODEL_EVALUATION = True
PASS_RULE = (
    "all five completed registered defects are detected by their preregistered "
    "existing guards"
)
FAIL_RULE = "at least one completed registered defect is not detected"
INCONCLUSIVE_RULE = (
    "at least one registered defect cannot be evaluated exactly as "
    "preregistered due to integrity, containment, execution, or completeness "
    "failure"
)
INTEGRITY_PRECEDES_SCIENTIFIC_DECISION = True
INCONCLUSIVE_TAKES_PRECEDENCE_OVER_PASS_FAIL = True

PRIMARY_GATE_INDEPENDENT_OF = (
    "model performance",
    "IC threshold",
    "p-values",
    "permutation significance",
    "multiplicity",
)

SECONDARY_METRIC = "apparent IC distortion"
SECONDARY_METRIC_APPLIES_ONLY_TO_UNDETECTED_DEFECTS = True
SECONDARY_METRIC_MODEL = "ridge"
SECONDARY_METRIC_MODEL_PARAMETERS = MappingProxyType({"alpha": 1.0})
SECONDARY_METRIC_TARGET = "next_year_return_pct"
SECONDARY_METRIC_RANK_METHOD = "average"
SECONDARY_METRIC_RANK_PERCENTILE = True
SECONDARY_METRIC_IMPUTATION = "NaN -> 0.5"
SECONDARY_METRIC_SPLIT_SOURCE = "experiments/run_experiments.py"
SECONDARY_METRIC_SPLIT_SOURCE_SHA256 = RUN_EXPERIMENTS_SHA256
SECONDARY_METRIC_SPLIT_SYMBOL = "experiments.run_experiments.SPLITS"
SECONDARY_METRIC_SPLIT_FIELDS = (
    "name",
    "train_target_years",
    "test_feature_year",
)
#: The registered split tuple must equal the canonical SPLITS surface exactly —
#: same names, same order, same train_target_years, same test_feature_year. No
#: additional and no omitted split is allowed; a subset is not sufficient.
SECONDARY_METRIC_SPLITS_EQUAL_CANONICAL_SPLITS_EXACTLY = True
SECONDARY_METRIC_SPLIT_COUNT = 3
SECONDARY_METRIC_FEATURE_SELECTOR = "experiments.run_experiments._feature_cols"
SECONDARY_METRIC_TARGET_SELECTOR = (
    "experiments.run_experiments.build_panel_for_target("
    "target_col='next_year_return_pct', target_path=None)"
)
SECONDARY_METRIC_ALTERNATIVE_TARGET_TABLE_FORBIDDEN = True
SECONDARY_METRIC_TARGET_ITERATION_FORBIDDEN = (
    "the registered secondary path never iterates experiments.run_experiments."
    "TARGETS and never selects an alternate target; it pins the single literal "
    "next_year_return_pct"
)
SECONDARY_METRIC_FORBIDDEN_TARGETS = STALE_DERIVED_TARGET_COLUMNS
NO_NEXT_YEAR_COLUMN_MAY_BE_A_PREDICTOR = True
SECONDARY_METRIC_SPLITS = (
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
SECONDARY_METRIC_IS_GATING = False
SECONDARY_METRIC_STATUS = "NON-GATING / DESCRIPTIVE ONLY"
SECONDARY_METRIC_FORBIDDEN = (
    "p-value",
    "significance test",
    "multiplicity correction",
    "predictive-edge inference",
)
SECONDARY_METRIC_COMPARATOR = (
    "the same Ridge / split / target construction evaluated on the clean "
    "comparator frame, reported as a descriptive difference"
)
SECONDARY_METRIC_CORRELATION = "Spearman(prediction, observed target)"
SECONDARY_METRIC_DISTORTION_FORMULA = (
    "delta_ic(split) = injected_ic(split) - clean_ic(split)"
)
SECONDARY_METRIC_REPORTING_SCOPE = (
    "one signed delta_ic per canonical split; negative, zero, and positive "
    "values are retained; no pooling across splits or defects and no aggregate "
    "threshold"
)
SECONDARY_METRIC_IS_PER_SPLIT = True
SECONDARY_METRIC_HAS_CROSS_SPLIT_AGGREGATE = False


# --------------------------------------------------------------------------- #
# 10 — closed minimum integrity contract. Registration defines the required
# semantics only; no governed-run or recovery implementation is invented here.
# --------------------------------------------------------------------------- #
INTEGRITY_CONDITION_IDENTIFIERS = (
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
)
INTEGRITY_CONDITION_DESCRIPTIONS = MappingProxyType(
    {
        "frozen_source_dataset_path_and_sha_match": (
            "data/trusted_clean/modeling_dataset_training_2020_2025.csv with "
            "SHA256 3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78, "
            "verified before and after every defect"
        ),
        "registered_stage3_module_hashes_match": (
            "the Stage 3 registration doc, registration module, and every "
            "registered guard-surface source hash match their pinned values at "
            "run time"
        ),
        "exactly_five_registered_defect_ids": (
            "exactly the five IDs 4000, 4001, 4002, 4003, 4004 are executed"
        ),
        "no_duplicate_defect_ids_or_defect_names": "no duplicates in either key space",
        "correct_seed_schedule": (
            "injection_seed(defect_id) reproduces the frozen values; any RNG "
            "consumption in the first draw is an integrity failure"
        ),
        "no_forbidden_id_overlap": (
            "no Stage 3 ID falls in 0-199, 200-599, 600-999, or 1000-3999"
        ),
        "writes_confined_to_stage3_result_namespace": (
            "every persisted output lands under "
            "experiments/results_thesis/defect_injection/ and nowhere else; "
            "working files live in a private temporary directory that is removed"
        ),
        "stage1_stage1b_stage2_result_roots_untouched": (
            "positive_control, positive_control_calibration and negative_control "
            "result roots are byte-identical before and after"
        ),
        "no_trusted_data_or_config_mutation": (
            "data/trusted*, data/trusted_clean*, data/config* and data/provenance "
            "are byte-identical before and after"
        ),
        "no_source_module_mutation": (
            "every registered guard-surface source module is byte-identical "
            "before and after; runtime attribute redirection is restored on all "
            "exit paths"
        ),
        "injection_containment_restored_after_each_defect": (
            "the private temporary directory is removed and every redirected "
            "module attribute restored after each defect, including on exception "
            "paths"
        ),
        "clean_comparator_byte_and_logical_identity": (
            "the clean comparator is re-read from the pinned source for every "
            "defect, emits zero registered detection signals, and is logically "
            "identical across defects"
        ),
        "expected_guard_mapping_evaluated_exactly_once": (
            "each defect's EVALUATED_SURFACES set is executed exactly once; no "
            "surface is retried after seeing its outcome"
        ),
        "no_defect_silently_omitted": (
            "all five registered defects appear in the result record with an "
            "explicit DETECTED / NOT_DETECTED / INCONCLUSIVE status"
        ),
        "secondary_ic_only_on_undetected_defects": (
            "the descriptive IC comparison is computed only where the defect "
            "status is NOT_DETECTED, and never for a DETECTED or INCONCLUSIVE "
            "defect"
        ),
        "no_invalid_evaluation_converted_to_non_detection": (
            "a containment failure, an unexecuted surface, or the silence of an "
            "INPUT_BLIND surface is recorded as INCONCLUSIVE or NOT EVALUATED, "
            "never as NOT_DETECTED and never as DETECTED"
        ),
        "deterministic_replay_contract": (
            "if a replay is performed it must reproduce every per-defect status "
            "and every registered invariant exactly; the contract is defined here "
            "prospectively and no replay implementation is registered yet"
        ),
    }
)
INTEGRITY_CONDITIONS = INTEGRITY_CONDITION_IDENTIFIERS
INTEGRITY_EXCLUSIONS = (
    "apparent IC magnitude",
    "IC distortion size",
    "model performance",
    "how many defects were detected",
    "whether the first draw PASSes or FAILs",
)
INTEGRITY_EVALUATED_BEFORE_SCIENTIFIC_GATE = True
GUARD_GAP_IS_VALID_SCIENCE = True
GOVERNED_RUN_IMPLEMENTATION_NOT_INVENTED_AT_REGISTRATION = True
REPLAY_IMPLEMENTATION_NOT_REGISTERED = True


# --------------------------------------------------------------------------- #
# D6 — Stage 7 gate. Stage 3 does not silently unlock Stage 7.
# --------------------------------------------------------------------------- #
STAGE_1_STATUS = "FAILED AS WRITTEN — INFORMATIVE"
STAGE_1B_STATUS = "DIAGNOSTIC / CALIBRATION ONLY"
STAGE_2_STATUS = "COMPLETED — SCIENTIFIC DECISION PASS"
STAGE_7_EXISTING_WORDING = "Only after stages 1–3 pass"
STAGE_7_REMAINS_BLOCKED = True
STAGE_7_BLOCKED_REASON = (
    "Stage 1 remains FAILED AS WRITTEN — INFORMATIVE, so the existing Stage 7 "
    "wording is not satisfied even if Stage 3 passes"
)
STAGE_3_DOES_NOT_UNLOCK_STAGE_7 = True
STAGE_7_REINTERPRETATION_REQUIRES_SEPARATE_PROSPECTIVE_GOVERNANCE = True


# --------------------------------------------------------------------------- #
# 11 — claim boundary
# --------------------------------------------------------------------------- #
CLAIM_BOUNDARY = (
    "Stage 3 may establish only whether the preregistered existing guard map "
    "detects the five preregistered synthetic defects under the frozen "
    "construction.",
    "It does NOT establish absence of all leakage.",
    "It does NOT establish universal pipeline safety.",
    "It does NOT establish predictive edge.",
    "It does NOT establish alpha.",
    "It does NOT establish investment value.",
    "It does NOT establish production readiness.",
    "It does NOT establish correctness of expanded datasets.",
    "It does NOT establish correctness of future unknown defect classes.",
    "A FAIL is informative and expected if existing guard gaps are real.",
    "Research support only; not investment advice.",
)


# --------------------------------------------------------------------------- #
# Registration-test boundary. Registration proves the contract; it never
# performs the science.
# --------------------------------------------------------------------------- #
REGISTRATION_TESTS_MAY = (
    "inspect repository source",
    "read the frozen dataset read-only",
    "verify frozen source facts",
    "verify registration constants",
    "prove source semantics structurally, including by AST",
    "prove that no Stage 3 result root exists",
)
REGISTRATION_TESTS_MAY_NOT = (
    "construct the 4000 transformation",
    "construct the 4001 rotation",
    "construct the 4002 added leak column",
    "construct the 4003 membership selection",
    "construct the 4004 duplication",
    "execute any registered Stage 3 defect construction",
)
REGISTRATION_TESTS_CONSTRUCT_INJECTED_FRAMES = False
BEHAVIORAL_INJECTION_TESTS_BELONG_TO_IMPLEMENTATION = True
FROZEN_INJECTION_COUNTS_ARE_PROSPECTIVE = True
FROZEN_INJECTION_COUNTS_VERIFIED_AT = (
    "Stage 3 implementation tests, in the separate implementation task"
)
FUTURE_IMPLEMENTATION_MUST_REMAIN_REGISTRATION_SEPARATE = True
IMPLEMENTATION_MUST_ADD_RUNNER_TARGET_AND_OWNERSHIP_BEFORE_RUN = True
PROSPECTIVE_ARTIFACT_CONTRACTS_REQUIRED_AT_REGISTRATION = False
PROSPECTIVE_ARTIFACT_CONTRACT_STATUS_AT_REGISTRATION = (
    "NOT_REQUIRED_AT_REGISTRATION"
)
