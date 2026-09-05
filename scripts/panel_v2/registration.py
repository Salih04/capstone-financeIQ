"""Import-inert registration contract for the PIT panel v2 successor study.

This module is a governance artifact, not a collector, builder, evaluator, or
experiment runner. Importing it performs no file or network I/O, opens no
dataset, reads no target, and creates no output root. It contains only literals
and ``MappingProxyType`` declarations so the registration tests can inspect the
contract without making a scientific or data-acquisition side effect.

The existing v1 data and results remain immutable. This protocol registers a
new v2 construction; it does not retroactively certify the v1 cohort and does
not claim a predictive edge.
"""

from __future__ import annotations

from types import MappingProxyType


# --------------------------------------------------------------------------- #
# P1 — protocol and path contract
# --------------------------------------------------------------------------- #
VERSION_ID = "panel_v2_pit"
PROTOCOL_ID = "FI-PANEL-V2-PIT-v1"
REGISTRATION_DOC = "docs/PREREGISTERED_PANEL_V2_PIT.md"
APPLICABILITY_RULES_PATH = "docs/panel_v2/applicability_rules.csv"
PIT_CELL_EVIDENCE_SCHEMA_PATH = "docs/panel_v2/pit_cell_evidence.schema.json"
SOURCE_MANIFEST_SCHEMA_PATH = "docs/panel_v2/source_manifest.schema.json"
AUTHORITATIVE_BASE_COMMIT = "c418563f432f5b253fb3b0e69619c76608ea15ea"

RAW_ROOT = "data/trusted_raw_pit_v2/"
GENERATED_ROOT = "data/panel_v2_pit/"
CODE_PACKAGE = "scripts/panel_v2/"

REGISTRATION_ARTIFACTS = (
    REGISTRATION_DOC,
    PIT_CELL_EVIDENCE_SCHEMA_PATH,
    SOURCE_MANIFEST_SCHEMA_PATH,
    APPLICABILITY_RULES_PATH,
    "scripts/panel_v2/__init__.py",
    "scripts/panel_v2/registration.py",
    "tests/test_panel_v2_registration.py",
    "TASK_STATE.md",
)

REGISTRATION_ONLY = True
IMPORT_INERT = True
REGISTRATION_MODULE_PERFORMS_IO = False
RAW_ROOT_CREATED = False
GENERATED_ROOT_CREATED = False
COLLECTION_READY = False
IMPLEMENTATION_READY = False
OWNER_DECISIONS_REQUIRED = "NONE"

# The realized year range and row count are outputs of a later evidence-backed
# collection. They are not encoded in a core filename, version id, or import.
COVERAGE_MANIFEST_FILENAME = "manifest.json"
GENERATED_FILENAMES = MappingProxyType(
    {
        "panel": "panel.csv",
        "targets": "panel_targets.csv",
        "legacy_unverified": "legacy_unverified.csv",
        "cell_evidence": "pit_cell_evidence.csv",
        "row_eligibility": "row_eligibility.csv",
        "eligibility_report_json": "eligibility_report.json",
        "eligibility_report_md": "eligibility_report.md",
        "source_manifest": "source_manifest.json",
        "conflict_ledger": "conflict_ledger.csv",
        "feature_resolution": "feature_resolution.json",
        "benchmark_reconciliation": "benchmark_reconciliation.json",
        "target_overlap_reconciliation": "target_overlap_reconciliation.json",
        "coverage_manifest": COVERAGE_MANIFEST_FILENAME,
    }
)
RAW_FILENAMES = MappingProxyType(
    {
        "security_price_ledger": "prices/security_price_ledger.csv",
        "benchmark_ledger": "benchmark/benchmark_ledger.csv",
        "document_store": "documents/",
        "raw_source_manifest": "source_manifest.json",
    }
)

# --------------------------------------------------------------------------- #
# P2 — immutable historical boundary and Stage 3 isolation
# --------------------------------------------------------------------------- #
IMMUTABLE_WRITE_FORBIDDEN_PREFIXES = (
    "data/trusted/",
    "data/trusted_clean/",
    "data/trusted_raw/",
    "data/provenance/",
    "experiments/",
    "scripts/data_collection/",
    "docs/thesis/baseline/",
)
DIAGNOSTIC_READ_ALLOWED_PREFIXES = (
    "data/trusted_clean/",
    "data/trusted_raw/",
    "data/provenance/",
)
STAGE3_GUARD_SURFACES = (
    "experiments/run_experiments.py",
    "experiments/significance.py",
    "experiments/contamination_lab.py",
    "experiments/thesis/stage1b_registration.py",
    "experiments/thesis/stage2_registration.py",
    "experiments/thesis/provenance.py",
    "data/trusted_clean/modeling_dataset_training_2020_2025.csv",
    "data/trusted_clean/modeling_dataset_public_2020_2025.csv",
)
STAGE3_ISOLATION_PRESERVED = True
STAGE3_MUTATION_ALLOWED = False

# --------------------------------------------------------------------------- #
# P3 — source-class taxonomy (authoritative numbering)
# --------------------------------------------------------------------------- #
COMMON_SOURCE_METADATA = (
    "source_class",
    "source_id",
    "source_document_id",
    "source_ref",
    "first_publication_timestamp",
    "retrieval_timestamp",
    "document_sha256",
    "rights_status",
    "license_status",
    "reviewer",
    "review_date",
)

SOURCE_CLASSES = MappingProxyType(
    {
        "SC-1": MappingProxyType(
            {
                "name": "PIT EFFECTIVE-DATED INDEX MEMBERSHIP",
                "description": (
                    "Effective-dated BIST 100 membership evidence. It establishes "
                    "membership state and never supplies a feature value."
                ),
                "may_originate_feature_value": False,
                "required_metadata": (
                    "index_id",
                    "membership_state",
                    "effective_from",
                    "effective_to",
                    "ticker_at_time",
                    "issuer_name_at_time",
                    "rulebook_version",
                ),
            }
        ),
        "SC-2": MappingProxyType(
            {
                "name": "SECURITY / ISSUER / LISTING IDENTITY AND SUCCESSION",
                "description": (
                    "Stable security, issuer, listing, rename, delisting, and "
                    "successor identity evidence. It is never inferred from a ticker."
                ),
                "may_originate_feature_value": False,
                "required_metadata": (
                    "security_id",
                    "issuer_id",
                    "ticker_at_time",
                    "listing_valid_from",
                    "listing_valid_to",
                    "succession_relation",
                    "successor_security_id",
                ),
            }
        ),
        "SC-3": MappingProxyType(
            {
                "name": "STATEMENT-FORMAT / ENTITY-CLASS CLASSIFICATION",
                "description": (
                    "Evidence for non-financial comparability or a financial or "
                    "other entity statement format. Unknown classification fails closed."
                ),
                "may_originate_feature_value": False,
                "required_metadata": (
                    "statement_format_class",
                    "entity_class",
                    "comparability_decision",
                    "classification_as_of_timestamp",
                ),
            }
        ),
        "SC-4": MappingProxyType(
            {
                "name": "PIT ANNUAL FINANCIAL STATEMENTS",
                "description": (
                    "The latest admissible annual filing selected under the feature-year "
                    "calendar cutoff, with its accounting and consolidation bases."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "fiscal_year_of_record",
                    "period_end_date",
                    "accounting_framework_id",
                    "measurement_basis",
                    "value_version",
                    "measuring_unit_date",
                    "currency_code",
                    "consolidation_basis",
                    "statement_cell_ref",
                ),
            }
        ),
        "SC-5": MappingProxyType(
            {
                "name": "EFFECTIVE-DATED SHARES OUTSTANDING",
                "description": (
                    "Shares-outstanding observations with effective dates and share "
                    "class identity. Missing shares remain missing."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "security_id",
                    "share_class_id",
                    "shares_outstanding",
                    "effective_from",
                    "effective_to",
                    "share_measurement_basis",
                ),
            }
        ),
        "SC-6": MappingProxyType(
            {
                "name": "SECURITY PRICES + CORPORATE-ACTION ADJUSTMENT EVIDENCE",
                "description": (
                    "Year-end security prices, trading status, and the evidence needed "
                    "to make the adjustment basis explicit and reproducible."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "security_id",
                    "price_date",
                    "price_field",
                    "adjustment_basis",
                    "corporate_action_evidence_ids",
                    "trading_status",
                    "currency_code",
                    "acquisition_status",
                ),
            }
        ),
        "SC-7": MappingProxyType(
            {
                "name": "XU100 BENCHMARK SERIES",
                "description": (
                    "A versioned XU100 BIST 100 benchmark series with explicit "
                    "instrument, provider, calendar, and annual formula identity."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "benchmark_version_id",
                    "instrument_id",
                    "index_variant",
                    "provider_id",
                    "endpoint",
                    "calendar_convention",
                    "annual_return_formula_id",
                ),
            }
        ),
        "SC-8": MappingProxyType(
            {
                "name": "REALIZED T+1 TARGET PRICE INPUTS",
                "description": (
                    "Separate target-side year-end price inputs for TC-A. This class "
                    "never enters the governed feature vector."
                ),
                "may_originate_feature_value": False,
                "required_metadata": (
                    "security_id",
                    "feature_year",
                    "target_year",
                    "price_date_t",
                    "price_date_t1",
                    "adjustment_basis",
                    "target_formula_id",
                ),
            }
        ),
        "SC-9": MappingProxyType(
            {
                "name": "GROWTH SOURCE / BASE-PERIOD EVIDENCE",
                "description": (
                    "Evidence that the current and comparative accounting cells form "
                    "an admissible same-basis growth pair."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "current_cell_ref",
                    "base_cell_ref",
                    "source_document_id",
                    "accounting_framework_id",
                    "measurement_basis",
                    "value_version",
                    "measuring_unit_date",
                    "currency_code",
                    "consolidation_basis",
                    "growth_formula_id",
                ),
            }
        ),
        "SC-10": MappingProxyType(
            {
                "name": "FINANCIAL_DEBT_RATIO DIRECT-DEFINITION EVIDENCE",
                "description": (
                    "A directly supplied financial_debt_ratio under one explicit "
                    "panel-wide definition. Repository derivation is forbidden."
                ),
                "may_originate_feature_value": True,
                "required_metadata": (
                    "definition_id",
                    "definition_text",
                    "numerator_definition",
                    "denominator_definition",
                    "definition_source_document_id",
                    "definition_publication_date",
                ),
            }
        ),
    }
)
SOURCE_CLASS_IDS = tuple(SOURCE_CLASSES)
SOURCE_CLASS_NAMES = tuple(spec["name"] for spec in SOURCE_CLASSES.values())
VALUE_ORIGINATING_SOURCE_CLASSES = tuple(
    key for key, spec in SOURCE_CLASSES.items() if spec["may_originate_feature_value"]
)
NON_VALUE_SOURCE_CLASSES = tuple(
    key for key, spec in SOURCE_CLASSES.items() if not spec["may_originate_feature_value"]
)

# This quarantine label is intentionally outside SC-1…SC-10. It may describe a
# separate legacy sidecar only; it can never be a governed v2 feature source.
LEGACY_SOURCE_LABEL = "LEGACY_VENDOR_SNAPSHOT"
LEGACY_SOURCE_LABEL_IS_REGISTERED_SOURCE_CLASS = False

# SC-1…SC-10 is the entire taxonomy. It is never extended, and no sentinel may be
# encoded as a source_class. Missing or not-applicable state is carried by
# ``is_null``, ``null_reason``, and the applicability rule instead. A cell may
# record ``source_class = null`` only when it is a null cell.
SOURCE_CLASS_TAXONOMY_IS_CLOSED = True
SOURCE_CLASS_SENTINELS_FORBIDDEN = (
    "MISSING",
    "NOT_APPLICABLE",
    "LEGACY",
    "LEGACY_VENDOR_SNAPSHOT",
    "UNKNOWN",
    "NONE",
    "UNVERIFIED",
)
SOURCE_CLASS_NULL_ALLOWED_ONLY_ON_NULL_CELL = True
SOURCE_CLASS_TAXONOMY_SURFACES = (
    REGISTRATION_DOC,
    PIT_CELL_EVIDENCE_SCHEMA_PATH,
    SOURCE_MANIFEST_SCHEMA_PATH,
    "scripts/panel_v2/registration.py",
    "tests/test_panel_v2_registration.py",
)

# --------------------------------------------------------------------------- #
# P4 / P5 — evidence and eligibility field contracts
# --------------------------------------------------------------------------- #
PIT_CELL_EVIDENCE_FIELDS = (
    "security_id",
    "ticker",
    "feature_year",
    "fiscal_year_of_record",
    "column",
    "value",
    "is_null",
    "null_reason",
    "applicability_rule_id",
    "source_class",
    "source_id",
    "source_document_id",
    "source_ref",
    "first_publication_timestamp",
    "as_of_timestamp",
    "knowledge_timestamp",
    "retrieval_timestamp",
    "document_sha256",
    "extraction_method",
    "transform_id",
    "transform_inputs",
    "pit_cutoff_timestamp",
    "pit_ok",
    "accounting_framework_id",
    "measurement_basis",
    "value_version",
    "measuring_unit_date",
    "currency_code",
    "consolidation_basis",
    "definition_id",
    "definition_text",
    "numerator_definition",
    "denominator_definition",
    "definition_source_document_id",
    "definition_publication_date",
    "frozen_screen_status",
    "conflict_group_id",
    "reviewer",
    "review_date",
)

ROW_ELIGIBILITY_FIELDS = (
    "security_id",
    "ticker",
    "feature_year",
    "identity_status",
    "membership_status",
    "statement_format_class",
    "accounting_framework_id",
    "measurement_basis",
    "value_version",
    "measuring_unit_date",
    "currency_code",
    "consolidation_basis",
    "fiscal_year_of_record",
    "fundamentals_source_document_id",
    "fundamentals_first_publication_timestamp",
    "pit_cutoff_timestamp",
    "row_pit_ok",
    "group_statuses",
    "not_applicable_cell_count",
    "not_applicable_cell_names",
    "confirmatory_eligible",
    "complete_case_zero_imputed",
    "ineligibility_reasons",
    "conflict_group_ids",
)

NULL_REASONS = (
    "NOT_APPLICABLE",
    "MISSING_SOURCE_CLASS_GAP",
    "MISSING_NOT_EVIDENCED",
    "PIT_INADMISSIBLE",
    "PIT_UNVERIFIABLE",
    "FROZEN_SCREEN_REJECTED",
    "CONFLICT_UNADJUDICATED",
    "BASIS_MISMATCH",
    "BASIS_UNKNOWN",
    "DEFINITION_UNAVAILABLE",
    "LEGACY_SOURCE_FORBIDDEN",
    "IDENTITY_UNRESOLVED",
    "STATEMENT_FORMAT_NON_COMPARABLE",
    "WINDOW_INCOMPLETE",
    "BENCHMARK_VARIANT_MISMATCH",
)
FROZEN_SCREEN_STATUSES = (
    "PASSED",
    "FROZEN_REPEATED",
    "INSUFFICIENT_PERIODS",
    "NOT_APPLICABLE",
    "NOT_SCREENED",
)
ADMISSIBLE_FROZEN_SCREEN_STATUSES = ("PASSED", "NOT_APPLICABLE")

# --------------------------------------------------------------------------- #
# P6 — D1 PIT cutoff and annual-filing selection
# --------------------------------------------------------------------------- #
PIT_CUTOFF_RULE = "end_of_calendar_year_T_in_Europe_Istanbul"
PIT_CUTOFF_DATE_TEMPLATE = "{feature_year}-12-31"
PIT_CUTOFF_TIMESTAMP_TEMPLATE = "{feature_year}-12-31T23:59:59.999999+03:00"
PIT_CUTOFF_TIMEZONE = "Europe/Istanbul"
PIT_CUTOFF_INCLUSIVE = True
PIT_COMPARISON = "first_publication_timestamp <= pit_cutoff_timestamp"
KNOWLEDGE_TIMESTAMP_RULE = (
    "maximum first_publication_timestamp of the source document and every input "
    "document consumed by its transform"
)
RETRIEVAL_TIMESTAMP_IS_NOT_FIRST_PUBLICATION_TIMESTAMP = True
FISCAL_YEAR_T_FILING_ADMISSIBLE_FOR_FEATURE_YEAR_T = False
FUNDAMENTALS_SELECTION_RULE = (
    "select the latest admissible annual filing by fiscal_year_of_record whose "
    "first_publication_timestamp is at or before the feature-year cutoff"
)
FEATURE_YEAR_EQUALS_FISCAL_YEAR = False
POST_CUTOFF_RESTATEMENT_DISPOSITION = "record_in_conflict_ledger_never_apply"
UNKNOWN_FIRST_PUBLICATION_DISPOSITION = "PIT_UNVERIFIABLE"
REQUIRED_SEPARATE_PIT_FIELDS = (
    "feature_year",
    "fiscal_year_of_record",
    "source_document_id",
    "first_publication_timestamp",
    "pit_cutoff_timestamp",
)

# --------------------------------------------------------------------------- #
# C1 — governed evidence column domain and the fail-closed non-null contract
# --------------------------------------------------------------------------- #
# pit_cell_evidence records FEATURE-CELL evidence. Its ``column`` domain is the
# exact registered governed vector and nothing else: no target column, no PIT
# metadata name, no eligibility field, no identity helper, and no legacy
# ``_legacy_unverified`` name may be admitted as a governed feature cell.
PIT_CELL_EVIDENCE_COLUMN_DOMAIN_IS_GOVERNED_40 = True
PIT_CELL_EVIDENCE_ARBITRARY_COLUMN_ALLOWED = False
PIT_CELL_EVIDENCE_ADDITIONAL_PROPERTIES_ALLOWED = False
LEGACY_CELLS_RECORDED_IN_PIT_CELL_EVIDENCE = False

# Schema layer — what Draft 2020-12 does prove for a non-null governed cell.
NON_NULL_CELL_SCHEMA_REQUIREMENTS = (
    "is_null is false",
    "value is a number",
    "null_reason is null",
    "pit_ok is true",
    "source_class is one of the value-originating SC-1…SC-10 members",
    "source_id, source_document_id, source_ref, and extraction_method are non-empty",
    "document_sha256 is a 64-character lowercase hex digest",
    "first_publication_timestamp, knowledge_timestamp, and retrieval_timestamp are "
    "present, non-null, and carry an explicit timezone offset",
    "pit_cutoff_timestamp is present and matches the D1 calendar-year-end template",
    "frozen_screen_status is PASSED or NOT_APPLICABLE",
)
NULL_CELL_SCHEMA_REQUIREMENTS = (
    "value is null",
    "null_reason is a registered NULL_REASONS member and is not null",
)

# Implementation layer — what the schema cannot prove and must not claim.
PIT_OK_IS_COMPUTED_NEVER_TRUSTED_FROM_INPUT = True
PIT_OK_PREDICATE = (
    "knowledge_timestamp <= pit_cutoff_timestamp, both normalized to Europe/Istanbul"
)
PIT_TIMESTAMP_ORDERING_ENFORCEMENT = "DEFERRED_TO_IMPLEMENTATION"
PIT_TIMESTAMP_ORDERING_CURRENTLY_ENFORCED = False
PIT_TIMESTAMP_ORDERING_DEFERRAL_REASON = (
    "JSON Schema Draft 2020-12 has no relational comparison between two instance "
    "values, so it cannot prove that one timestamp precedes another. The schema "
    "freezes presence, type, vocabulary, and pit_ok=true; the ordering predicate "
    "itself is deferred to an implementation validator that does not exist yet."
)
IMPLEMENTATION_VALIDATOR_FAIL_CLOSED_CONDITIONS = (
    "the first-public or knowledge timestamp is absent",
    "the pit_cutoff timestamp is absent",
    "the knowledge or first-public timestamp is after the pit_cutoff timestamp",
    "a timestamp timezone cannot be normalized",
    "the evidence chronology is internally inconsistent",
)
IMPLEMENTATION_VALIDATOR_EXISTS = False

# --------------------------------------------------------------------------- #
# P18 — governed 40-feature vector and metadata separation
# --------------------------------------------------------------------------- #
GOVERNED_FEATURES_V2 = (
    "benchmark_same_year_return_pct",
    "current_assets",
    "current_ratio",
    "ebitda",
    "ebitda_growth_pct",
    "ebitda_margin",
    "enterprise_value",
    "equity",
    "ev_ebitda",
    "financial_debt_ratio",
    "gross_margin",
    "gross_profit",
    "gross_profit_growth_pct",
    "leverage_ratio",
    "long_term_liabilities",
    "market_cap",
    "net_debt",
    "net_debt_to_ebitda",
    "net_income",
    "net_income_growth_pct",
    "net_margin",
    "non_current_assets",
    "operating_income",
    "operating_income_growth_pct",
    "pb_ratio",
    "pe_ratio",
    "price_adjclose_t",
    "price_data_available",
    "price_drawdown_from_3y_high_pct",
    "price_history_years_available",
    "price_momentum_1y_pct",
    "price_momentum_2y_pct",
    "price_vs_bist100_1y_pct",
    "revenue",
    "revenue_growth_pct",
    "roa",
    "roe",
    "short_term_liabilities",
    "total_assets",
    "working_capital",
)
GOVERNED_FEATURE_COUNT = 40
# The vector is not defined by this module. Its authority is Stage-A §9, which
# resolves it from experiments/run_experiments.py::_feature_cols over the
# modeling dataset in force. Both are independent of this registration and both
# are checked by the registration tests.
GOVERNED_FEATURES_AUTHORITY_DOC = "docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md"
GOVERNED_FEATURES_AUTHORITY_SECTION = "9. Frozen feature authority"
GOVERNED_FEATURES_AUTHORITY_MODULE = "experiments/run_experiments.py"
GOVERNED_FEATURES_AUTHORITY_FILTER = "_feature_cols"
GOVERNED_FEATURES_AUTHORITY_DATASET = (
    "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
)
GOVERNED_FEATURES_V2_NEWLINE_SHA256 = (
    "041566fc685b043c8618af859c268aa736fa5ae87b0d2679a2b35df779659575"
)
GOVERNED_FEATURES_V2_JSON_SHA256 = (
    "f8064f43ca5a446e21b2357fdafa4a9f6a1b7dfcbe7e79b8bc0835125c452543"
)
PANEL_IDENTITY_COLUMNS = ("security_id", "ticker", "feature_year")
TARGET_IDENTITY_COLUMNS = ("security_id", "ticker", "feature_year", "target_year")
FEATURE_METADATA_FORBIDDEN_IN_VECTOR = (
    "security_id",
    "ticker",
    "feature_year",
    "fiscal_year_of_record",
    "source_class",
    "source_id",
    "source_document_id",
    "source_ref",
    "first_publication_timestamp",
    "as_of_timestamp",
    "knowledge_timestamp",
    "retrieval_timestamp",
    "document_sha256",
    "extraction_method",
    "transform_id",
    "transform_inputs",
    "pit_cutoff_timestamp",
    "pit_ok",
    "applicability_rule_id",
    "null_reason",
    "frozen_screen_status",
    "conflict_group_id",
    "reviewer",
    "review_date",
    "accounting_framework_id",
    "measurement_basis",
    "value_version",
    "measuring_unit_date",
    "currency_code",
    "consolidation_basis",
    "definition_id",
    "confirmatory_eligible",
)
PIT_METADATA_FORBIDDEN_IN_PANEL = FEATURE_METADATA_FORBIDDEN_IN_VECTOR
PANEL_CONTAINS_TARGET = False
TARGET_PHYSICALLY_SEPARATE = True
TARGET_FORBIDDEN_IN_PANEL_COLUMNS = (
    "target_return_pct",
    "next_year_return_pct",
    "next_year_nominal_try_return_pct",
    "next_year_excess_return_vs_bist100",
    "next_year_real_return_pct",
    "next_year_usd_return_pct",
    "next_year_rank_by_return",
    "next_year_return_percentile",
    "target_year",
)

# --------------------------------------------------------------------------- #
# P8 / P9 — concept-group eligibility and fail-closed missingness
# --------------------------------------------------------------------------- #
CONCEPT_GROUPS = MappingProxyType(
    {
        "G1": MappingProxyType(
            {
                "name": "SIZE_SCALE",
                "members": (
                    "revenue",
                    "total_assets",
                    "equity",
                    "current_assets",
                    "non_current_assets",
                    "market_cap",
                    "enterprise_value",
                ),
            }
        ),
        "G2": MappingProxyType(
            {
                "name": "PROFITABILITY",
                "members": (
                    "gross_profit",
                    "operating_income",
                    "ebitda",
                    "net_income",
                    "gross_margin",
                    "ebitda_margin",
                    "net_margin",
                    "roa",
                    "roe",
                ),
            }
        ),
        "G3": MappingProxyType(
            {
                "name": "VALUATION",
                "members": ("pe_ratio", "pb_ratio", "ev_ebitda"),
            }
        ),
        "G4": MappingProxyType(
            {
                "name": "GROWTH",
                "members": (
                    "revenue_growth_pct",
                    "gross_profit_growth_pct",
                    "ebitda_growth_pct",
                    "operating_income_growth_pct",
                    "net_income_growth_pct",
                ),
            }
        ),
        "G5": MappingProxyType(
            {
                "name": "LEVERAGE_LIQUIDITY",
                "members": (
                    "short_term_liabilities",
                    "long_term_liabilities",
                    "net_debt",
                    "net_debt_to_ebitda",
                    "leverage_ratio",
                    "financial_debt_ratio",
                    "current_ratio",
                    "working_capital",
                ),
            }
        ),
        "G6": MappingProxyType(
            {
                "name": "PRICE_MOMENTUM",
                "members": (
                    "price_adjclose_t",
                    "price_data_available",
                    "price_history_years_available",
                    "price_momentum_1y_pct",
                    "price_momentum_2y_pct",
                    "price_drawdown_from_3y_high_pct",
                    "price_vs_bist100_1y_pct",
                    "benchmark_same_year_return_pct",
                ),
            }
        ),
    }
)
GROUP_IDS = tuple(CONCEPT_GROUPS)
GROUP_SATISFIED_RULE = "applicable_count > 0 AND null_count_among_applicable == 0"
VACUOUS_GROUP_SATISFACTION_ALLOWED = False
CONFIRMATORY_ELIGIBLE_RULE = (
    "resolved identity AND PIT member AND comparable statement format AND row PIT "
    "valid AND no unadjudicated conflict AND every G1..G6 is satisfied"
)
MISSINGNESS_GATE_RELAXATION_ALLOWED = False
SOURCE_CLASS_GAP_DISPOSITION = "MISSING_SOURCE_CLASS_GAP"
SOURCE_CLASS_GAP_IS_NOT_APPLICABLE = False
APPLICABILITY_RULES_COVER_GOVERNED_FEATURES = True

# The applicability contract is frozen by Stage-A §10.3 (group membership) and
# §10.4 (the exhaustive not-applicable conditions). This registration restates it;
# it may not extend, relax, or reinterpret it, and the registration tests check the
# CSV against the Stage-A document rather than against these constants.
APPLICABILITY_AUTHORITY_DOC = "docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md"
APPLICABILITY_AUTHORITY_SECTIONS = (
    "10.3 Concept groups, exact members, exact minima",
    "10.4 Structurally-not-applicable concepts (exact conditions)",
    "10.5 Source-class structural missingness",
)
APPLICABILITY_RULE_COLUMNS = (
    "rule_id",
    "rule_kind",
    "feature",
    "concept_group",
    "applicability",
    "not_applicable_when",
    "condition_evidence_required",
    "when_condition_unevidenced",
    "null_reason_when_not_applicable",
    "null_reason_when_applicable_but_absent",
    "required_source_classes",
    "basis",
)
APPLICABILITY_RULE_COUNT = 48
APPLICABILITY_RULE_KINDS = ("APPLICABILITY", "ADMISSIBILITY")
# ALWAYS_APPLICABLE and CONDITIONAL restate a Stage-A §10.4 verdict for the
# feature the rule scopes. PER_FEATURE_APPLICABILITY is the only admissible value
# for a panel-wide admissibility gate: such a gate constrains whether an already
# applicable cell may carry a value, and it must not assert one applicability
# verdict over features whose Stage-A verdicts differ.
APPLICABILITY_VALUES = ("ALWAYS_APPLICABLE", "CONDITIONAL", "PER_FEATURE_APPLICABILITY")
APPLICABILITY_SCOPE_TOKENS = ("(all governed features)", "(five growth features)")
UNEVIDENCED_CONDITION_DISPOSITION = "APPLICABLE_AND_FAIL_CLOSED"
APPLICABILITY_STAGE_A_EXTENSION_ALLOWED = False

# --------------------------------------------------------------------------- #
# P10 / D5 — legacy 17 quarantine
# --------------------------------------------------------------------------- #
LEGACY_NAMESPACE_SUFFIX = "_legacy_unverified"
LEGACY_DEFAULT_VALUE_IS_NULL = True
LEGACY_MAY_POPULATE_GOVERNED_FEATURE = False
LEGACY_RESOLVES_INTO_CONFIRMATORY_VECTOR = False
LEGACY_PHYSICAL_FILE = GENERATED_FILENAMES["legacy_unverified"]
LEGACY_VENDOR_SNAPSHOT_FEATURES = (
    "current_assets",
    "current_ratio",
    "ebitda_growth_pct",
    "equity",
    "financial_debt_ratio",
    "gross_profit_growth_pct",
    "leverage_ratio",
    "long_term_liabilities",
    "net_debt",
    "net_debt_to_ebitda",
    "net_income_growth_pct",
    "non_current_assets",
    "operating_income_growth_pct",
    "revenue_growth_pct",
    "short_term_liabilities",
    "total_assets",
    "working_capital",
)
LEGACY_VENDOR_SNAPSHOT_FEATURE_COUNT = 17
LEGACY_SET_DERIVATION = (
    "the distinct governed columns whose recorded v1 cell provenance carries "
    "source_class 'vendor_xlsx'; registration states the set, and the registration "
    "tests re-derive it from the repository provenance evidence"
)
LEGACY_SET_AUTHORITY_PATH = "data/provenance/cell_provenance_public_2020_2025.csv"
LEGACY_SET_AUTHORITY_SOURCE_CLASS = "vendor_xlsx"
LEGACY_GOVERNED_NAME_SUBSTITUTION_ALLOWED = False
LEGACY_DECLARABLE_AS_GOVERNED_VALUE_ORIGIN = False
# The manifest schema refuses a legacy source class outright. Preventing a future
# builder from writing a legacy value under a governed name is a runtime gate that
# no artifact in this registration implements.
LEGACY_QUARANTINE_BUILD_TIME_ENFORCEMENT = "DEFERRED_TO_IMPLEMENTATION"
LEGACY_QUARANTINE_CURRENTLY_ENFORCED_BY_A_BUILDER = False

# --------------------------------------------------------------------------- #
# P11 / D4 — accounting bases and TMS 29 / TAS 29 verification
# --------------------------------------------------------------------------- #
ACCOUNTING_FRAMEWORK_IDS = (
    "TFRS_NOMINAL_HISTORICAL_COST",
    "TFRS_TMS29_RESTATED",
    "IFRS_IASB_NOMINAL_HISTORICAL_COST",
    "IFRS_IASB_IAS29_RESTATED",
    "BOBI_FRS_NOMINAL",
    "BOBI_FRS_S25_RESTATED",
    "BDDK_SUPERVISORY_FORMAT_NOMINAL",
    "UNKNOWN",
)
MEASUREMENT_BASIS_VALUES = ("NOMINAL", "INFLATION_RESTATED", "UNKNOWN")
VALUE_VERSION_VALUES = ("ORIGINAL", "RESTATED", "UNKNOWN")
ACCOUNTING_COMPARISON_FIELDS = (
    "accounting_framework_id",
    "measurement_basis",
    "value_version",
    "measuring_unit_date",
    "currency_code",
    "consolidation_basis",
)
TAS29_VERIFICATION_STATUS = "VERIFIED"
TAS29_VERIFICATION_SOURCE = "authoritative prior TAS 29 / TMS 29 verification"
TAS29_POLICY = (
    "Original/restated value version and nominal/inflation-restated measurement "
    "basis are separate fields. A TMS 29-restated T current figure may be compared "
    "with the T-1 RESTATED COMPARATIVE presented in the same first-public filing, "
    "subject to the feature-year PIT cutoff."
)
TMS29_RESTATED_CURRENT_WITH_SAME_FILING_COMPARATIVE_ALLOWED = True
TMS29_RESTATED_CURRENT_WITH_OLD_NOMINAL_FILING_ALLOWED = False
GROWTH_REQUIRED_MATCHES = ACCOUNTING_COMPARISON_FIELDS
GROWTH_SAME_FILING_REQUIRED = True
GROWTH_SAME_FILING_RULE = (
    "current and T-1 comparative cells share source_document_id and all six "
    "ACCOUNTING_COMPARISON_FIELDS"
)
GROWTH_UNKNOWN_OR_MISMATCH_DISPOSITION = "NULL"
GROWTH_CROSS_FILING_COMPOSITION_ALLOWED = False
GROWTH_REBASING_BY_PIPELINE_ALLOWED = False
GROWTH_FEATURES = CONCEPT_GROUPS["G4"]["members"]

# --------------------------------------------------------------------------- #
# P12 / D3 — financial_debt_ratio direct-definition gate
# --------------------------------------------------------------------------- #
FINANCIAL_DEBT_RATIO_REPOSITORY_DERIVATION_ALLOWED = False
FINANCIAL_DEBT_RATIO_REQUIRES_EXPLICIT_SOURCE_VALUE = True
FINANCIAL_DEBT_RATIO_REQUIRES_PANEL_WIDE_DEFINITION_ID = True
FINANCIAL_DEBT_RATIO_REQUIRED_DEFINITION_METADATA = (
    "definition_id",
    "definition_text",
    "numerator_definition",
    "denominator_definition",
    "definition_source_document_id",
    "definition_publication_date",
)
FINANCIAL_DEBT_RATIO_FALLBACK = "NULL"
FINANCIAL_DEBT_RATIO_NULL_REASON = "DEFINITION_UNAVAILABLE"
FINANCIAL_DEBT_RATIO_G5_CONSEQUENCE_ACCEPTED = True
SECTION_10_3_RELAXATION_ALLOWED = False
# A non-null financial_debt_ratio cell is inadmissible without every registered
# definition field and an SC-10 origin. The schema proves that per cell. Whether
# one definition_id holds across the whole panel is a relational property no
# JSON Schema can express, so it is registered here and deferred.
FINANCIAL_DEBT_RATIO_FORBIDDEN_DEFINITION_ID_VALUES = (
    "",
    "UNKNOWN",
    "NONE",
    "NULL",
    "N/A",
    "NA",
    "TBD",
    "DEFAULT",
)
FINANCIAL_DEBT_RATIO_DEFINITION_ENFORCED_PER_CELL_BY_SCHEMA = True
FINANCIAL_DEBT_RATIO_PANEL_WIDE_CONSISTENCY_ENFORCEMENT = "DEFERRED_TO_IMPLEMENTATION"
FINANCIAL_DEBT_RATIO_PANEL_WIDE_CONSISTENCY_CURRENTLY_ENFORCED = False
FINANCIAL_DEBT_RATIO_FORMULA_INVENTED_HERE = False

# --------------------------------------------------------------------------- #
# P13 — security price and adjustment policy
# --------------------------------------------------------------------------- #
PRICE_LEDGER_APPEND_ONLY = True
PRICE_LEDGER_OVERWRITE_ALLOWED = False
PRICE_ACQUISITION_STATUSES = ("SUCCESS", "NO_DATA", "NOT_TRADING", "ERROR")
PRICE_STATUS_DEFAULTING_ALLOWED = False
PRICE_ADMISSIBLE_STATUS = "SUCCESS"
PRICE_LEDGER_KEY = ("security_id", "price_date", "adjustment_basis")
PRICE_ANNUAL_OBSERVATION_RULE = (
    "last evidenced trading-day adjusted price on or before the calendar-year end"
)
PRICE_FEATURE_ADJUSTMENT_BASIS_REQUIRED = True
PRICE_MISSINGNESS_DISPOSITION = "NULL_NEVER_ZERO_OR_FORWARD_FILLED"
G6_WINDOW_START_OFFSET = -2
G6_WINDOW_END_OFFSET = 0
G6_DEEPEST_LOOKBACK = "T-2"
PRICE_HISTORY_YEARS_AVAILABLE_SCOPE = "declared_T_minus_2_to_T_window_only"
PRICE_HISTORY_YEARS_AVAILABLE_RANGE = (0, 3)
DRAWDOWN_REQUIRES_COMPLETE_EVIDENCED_WINDOW = True
DRAWDOWN_ON_TRUNCATED_WINDOW = "NULL"
DRAWDOWN_ZERO_ON_TRUNCATED_WINDOW_ALLOWED = False

# --------------------------------------------------------------------------- #
# P14 / D6 — benchmark version and continuity policy
# --------------------------------------------------------------------------- #
BENCHMARK_INDEX_VARIANTS = ("PRICE_INDEX", "TOTAL_RETURN_INDEX")
BENCHMARK_INDEX_VARIANT = "PRICE_INDEX"
BENCHMARK_INSTRUMENT_ID = "XU100.IS"
BENCHMARK_INSTRUMENT_CONCEPT = "BIST 100 PRICE INDEX"
BENCHMARK_VERSION_ID = "XU100_PRICE_INDEX_V1"
BENCHMARK_TOTAL_RETURN_VERSION_ID = "XU100_TOTAL_RETURN_INDEX_SEPARATE_VERSION"
BENCHMARK_PROVIDER_ID = "YAHOO_FINANCE"
BENCHMARK_SOURCE_ID = "frozen_v1_xu100_price_series_source"
BENCHMARK_ENDPOINT = "Yahoo Finance chart endpoint"
BENCHMARK_CALENDAR_CONVENTION = "source trading observations within calendar year"
BENCHMARK_ANNUAL_RETURN_FORMULA_ID = "first_to_last_close_return_pct"
BENCHMARK_ANNUAL_RETURN_FORMULA = "100 * (last_close_in_year / first_close_in_year - 1)"
BENCHMARK_VERSION_PINS = (
    "benchmark_version_id",
    "source_class",
    "source_id",
    "provider_id",
    "instrument_id",
    "index_variant",
    "endpoint",
    "calendar_convention",
    "annual_return_formula_id",
    "declared_acquisition_window",
)
BENCHMARK_VARIANTS_INTERCHANGEABLE = False
BENCHMARK_CONTINUOUS_SERIES_ACROSS_VARIANTS_ALLOWED = False
BENCHMARK_WINDOW_DECLARED_BEFORE_ACQUISITION = True
BENCHMARK_OLD_COLLECTOR_ALLOWED = False
BENCHMARK_FROZEN_V1_PATH = "data/trusted_raw/bist100_benchmark_returns.csv"
BENCHMARK_FROZEN_V1_REWRITE_ALLOWED = False
BENCHMARK_OVERLAP_POLICY = (
    "record exact overlap diagnostics against frozen v1 without absorbing revisions "
    "or rewriting frozen v1"
)

# --------------------------------------------------------------------------- #
# P15 / D2 — TC-A target and exact overlap reconciliation
# --------------------------------------------------------------------------- #
TARGET_ID = "TC-A"
TARGET_COLUMN = "target_return_pct"
TARGET_FORMULA_ID = "TC-A_YEAR_END_ADJUSTED_RETURN"
TARGET_FORMULA = "100 * (P_adj(T+1) / P_adj(T) - 1)"
TARGET_PRICE_SOURCE = "SC-8 evidenced year-end security price inputs"
TARGET_IS_NEW_CONSTRUCTION = True
TARGET_REVISES_FROZEN_V1 = False
TARGET_WINDOW = "feature_year T year-end to target_year T+1 year-end"
FROZEN_TARGETS_EVER_REWRITTEN = False

TARGET_OVERLAP_REQUIRES_EXACT_STABLE_SECURITY_IDENTITY = True
TARGET_OVERLAP_REQUIRES_EXACT_TARGET_WINDOW = True
TARGET_OVERLAP_ARITHMETIC = "decimal"
TARGET_OVERLAP_SERIALIZATION = "canonical_decimal_serialization"
TARGET_OVERLAP_EXACT_SERIES_RULE = (
    "when both source series are exact under their source definitions, canonical "
    "decimal serializations must be equal"
)
TARGET_OVERLAP_SOURCE_ROUNDING_RULE = (
    "when a source declares rounding precision, derive only the representation "
    "interval mathematically implied by that precision"
)
TARGET_OVERLAP_UNKNOWN_ROUNDING_RULE = "no_representation_bound"
TARGET_OVERLAP_ARBITRARY_NUMERIC_BOUND = None
TARGET_OVERLAP_DISCREPANCY_DISPOSITION = "DEFINITION_OR_SOURCE_SERIES_BREAK"
TARGET_OVERLAP_TUNING_AFTER_INSPECTION_ALLOWED = False
TARGET_OVERLAP_AVERAGING_ALLOWED = False
TARGET_OVERLAP_SELECTION_ROLE = "DIAGNOSTIC_ONLY_NOT_PREDICTIVE_OUTCOME_SELECTION"
TARGET_OVERLAP_COMPARE_KEYS = (
    "security_id",
    "feature_year",
    "target_year",
    "target_start_price_date",
    "target_end_price_date",
)

# --------------------------------------------------------------------------- #
# P16 / P17 — physical target separation and executable no-peek contract
# --------------------------------------------------------------------------- #
NO_PEEK_TARGET_FILENAME = "panel_targets.csv"
NO_PEEK_TARGET_COLUMN_NAMES = TARGET_FORBIDDEN_IN_PANEL_COLUMNS
# What exists now, and is therefore actually provable now. Every module in the
# panel_v2 package at this commit is audited: none opens a file, and none imports
# anything that could.
NO_PEEK_REGISTRATION_SURFACE = (
    "scripts/panel_v2/__init__.py",
    "scripts/panel_v2/registration.py",
    "tests/test_panel_v2_registration.py",
)
NO_PEEK_REGISTRATION_STRUCTURAL_PROOF = (
    "the registration artifacts perform no I/O, contain no target-file open or read "
    "call, and their import closure inside scripts/panel_v2 reaches no module that "
    "can open the target artifact"
)
NO_PEEK_REGISTRATION_GUARD = True
NO_PEEK_TARGET_READ_ALLOWED = False

# What does not exist yet, and therefore cannot be proven now. These names are
# reserved so a future module cannot claim the guard was already satisfied. A
# registration test that inspected a path "if it exists" would manufacture a
# structural guarantee out of an absent file, so the test asserts their ABSENCE
# and this deferral instead.
NO_PEEK_FUTURE_IMPLEMENTATION_READERS = (
    "scripts/panel_v2/feasibility.py",
    "scripts/panel_v2/eligibility.py",
    "scripts/panel_v2/builder.py",
    "scripts/panel_v2/splits.py",
)
FUTURE_NO_PEEK_ENFORCEMENT = "DEFERRED_TO_IMPLEMENTATION"
FUTURE_TRANSITIVE_NO_PEEK_PROVEN = False
FUTURE_NO_PEEK_IMPLEMENTATION_GATE = (
    "when feasibility.py, eligibility.py, a builder module, or any other reader is "
    "introduced, implementation tests must examine its transitive import and read "
    "closure and prove it cannot access panel_targets.csv before the target stage"
)

# --------------------------------------------------------------------------- #
# P19 — conflict and source precedence policy
# --------------------------------------------------------------------------- #
LAST_WRITE_WINS_ALLOWED = False
CONFLICT_RESOLUTION = "preserve_all_candidates_and_fail_closed_pending_adjudication"
CONFLICT_UNADJUDICATED_CELL_DISPOSITION = "NULL"
CONFLICT_ADJUDICATION_STATUSES = ("UNADJUDICATED", "RESOLVED", "IRRECONCILABLE")
CONFLICT_LEDGER_FIELDS = (
    "conflict_group_id",
    "security_id",
    "ticker",
    "feature_year",
    "column",
    "candidate_index",
    "candidate_value",
    "source_class",
    "source_document_id",
    "first_publication_timestamp",
    "knowledge_timestamp",
    "adjudication_status",
    "adjudication_rationale",
    "adjudicated_by",
    "adjudication_date",
)

# --------------------------------------------------------------------------- #
# P20 / P21 / P22 — acquisition, dry-run, and artifact gates
# --------------------------------------------------------------------------- #
FORBIDDEN_ACQUISITION_WRITERS = (
    "scripts/fetch_yahoo_chart_prices.py",
    "scripts/data_collection/collect_bist100_benchmark.py",
)
REGISTRATION_MAY_NOT_ACQUIRE = True
EXTERNAL_RIGHTS_AGREEMENTS_REQUIRED = True
RESTRICTED_SOURCE_POLICY = (
    "No commercial or restricted source may be used without the applicable external "
    "rights or agreement; internal owner authorization alone is insufficient."
)
SOURCE_FEASIBILITY_ACCESS_LICENSE_PREREQUISITE = True
DRY_RUN_REQUIRED_BEFORE_ACQUISITION = True
DRY_RUN_CONTRACT = (
    "before acquisition, a future implementation must prove a schema-valid zero-row "
    "panel, separate target file, and zero confirmatory rows on empty governed inputs"
)
DRY_RUN_EXPECTED_CONFIRMATORY_ROWS = 0
DRY_RUN_IMPLEMENTED_AT_REGISTRATION = False
ARTIFACT_OWNERSHIP_REQUIRED_BEFORE_FIRST_RUN = True
ARTIFACT_REGISTRY_PATH = "artifact_registry.json"
ARTIFACT_REGISTRY_EDITED_AT_REGISTRATION = False
ARTIFACT_GOVERNANCE_PREREQUISITES = (
    "add data/panel_v2_pit to artifact_registry.json governed_roots",
    "declare every generated output as a prospective artifact entry with a generator",
    "add panel_v2_pit Makefile targets",
    "record the commands in docs/VERIFICATION_BASELINE.md",
)

# --------------------------------------------------------------------------- #
# Source-feasibility result and collection hold
# --------------------------------------------------------------------------- #
FULL_PANEL_FEASIBLE = "CONDITIONAL"
FULL_PANEL_FEASIBLE_CONFIRMED = False
SOURCE_FEASIBILITY_STATUS = "CONDITIONAL_NOT_CONFIRMED"
COLLECTION_BLOCKING_SOURCE_CLASSES = ("SC-1", "SC-2", "SC-5", "SC-6", "SC-8")
SOURCE_ACCESS_DEPTH_GATES = ("SC-4", "SC-7")
SOURCE_NORMALIZATION_DEFINITION_GATES = ("SC-3", "SC-9", "SC-10")
SOURCE_FEASIBILITY_DISPOSITIONS = MappingProxyType(
    {
        "SC-1": "HARD_COLLECTION_BLOCKER",
        "SC-2": "HARD_COLLECTION_BLOCKER",
        "SC-3": "NORMALIZATION_DEFINITION_GATE",
        "SC-4": "ACCESS_DEPTH_GATE",
        "SC-5": "HARD_COLLECTION_BLOCKER",
        "SC-6": "HARD_COLLECTION_BLOCKER",
        "SC-7": "ACCESS_DEPTH_GATE",
        "SC-8": "HARD_COLLECTION_BLOCKER",
        "SC-9": "NORMALIZATION_DEFINITION_GATE",
        "SC-10": "NORMALIZATION_DEFINITION_GATE",
    }
)
COLLECTION_PREREQUISITES = (
    "source feasibility is confirmed for every required class",
    "access and licensing rights are evidenced for every retained source",
    "stable identity and effective dates are complete or fail closed",
    "artifact ownership and implementation gates are wired before first run",
)

# --------------------------------------------------------------------------- #
# B1…B8 — prospective defect dispositions
# --------------------------------------------------------------------------- #
# Registration freezes prospective repair contracts. It does not implement them,
# and it does not close them. Each defect therefore carries two independent
# statuses: what this registration has frozen, and whether code enforces it. No
# defect below is closed, and none may be reported as design-closed.
DEFECT_REGISTRATION_STATUSES = ("REGISTERED_DESIGN_CONTRACT", "NOT_ADDRESSED")
DEFECT_ENFORCEMENT_STATUSES = ("DEFERRED_TO_IMPLEMENTATION", "ENFORCED_BY_TESTED_CODE")
INPUT_DEFECT_STATUS = MappingProxyType(
    {
        "B1": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B2": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B3": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B4": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B5": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B6": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B7": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
        "B8": ("REGISTERED_DESIGN_CONTRACT", "DEFERRED_TO_IMPLEMENTATION"),
    }
)
INPUT_DEFECT_REGISTERED_INTENT = MappingProxyType(
    {
        "B1": "price_history_years_available is scoped to the declared T-2..T window",
        "B2": "an incomplete drawdown window yields NULL, never zero",
        "B3": "the legacy 17 stay null and quarantined and never populate a governed name",
        "B4": "TC-A is a separately identified literal annual target",
        "B5": "the security price ledger is append-only and never overwritten",
        "B6": "NO_DATA, NOT_TRADING, and ERROR never default to a value",
        "B7": "one future split declaration home is required before any run",
        "B8": "realized coverage is carried by manifest.json, not by file or version names",
    }
)
INPUT_DEFECT_REGISTERED_CONTROLS = MappingProxyType(
    {
        "B1": "PRICE_HISTORY_YEARS_AVAILABLE_SCOPE",
        "B2": "DRAWDOWN_REQUIRES_COMPLETE_EVIDENCED_WINDOW",
        "B3": "LEGACY_DEFAULT_VALUE_IS_NULL",
        "B4": "TARGET_ID",
        "B5": "PRICE_LEDGER_APPEND_ONLY",
        "B6": "PRICE_STATUS_DEFAULTING_ALLOWED",
        "B7": "SPLIT_SINGLE_DECLARATION_HOME",
        "B8": "COVERAGE_MANIFEST_FILENAME",
    }
)
# Explicitly NOT claimed. Registration has frozen intended behaviour; no code
# now enforces that behaviour, because no builder, writer, or validator exists.
B1_B8_RUNTIME_ENFORCED = False
B1_B8_IMPLEMENTATION_TESTS_EXIST = False

SPLIT_SINGLE_DECLARATION_HOME = "scripts/panel_v2/splits.py"
SPLIT_LITERAL_DUPLICATION_ALLOWED = False
SPLIT_SCHEDULE_DECLARED_AT_REGISTRATION = False
SPLIT_SCHEDULE_SHAPE = "expanding_window_walk_forward_one_test_feature_year_per_fold"
PANEL_IDENTITY_CARRIES_YEAR_RANGE = False

# --------------------------------------------------------------------------- #
# M3 — controls that are registered but not executed anywhere at this commit
# --------------------------------------------------------------------------- #
# Each entry is (registration state, implementation state, execution state). The
# third element is the honest one: nothing in this registration runs. A frozen
# contract is not an enforced control, and this table exists so no later summary
# can quietly upgrade one into the other.
IMPLEMENTATION_ONLY_CONTROL_STATES = ("REGISTERED", "IMPLEMENTATION_REQUIRED", "NOT_YET_EXECUTED")
IMPLEMENTATION_ONLY_CONTROLS = MappingProxyType(
    {
        "source_rounding_reconciliation": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "append_only_acquisition_writer": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "no_overwrite_behaviour": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "explicit_acquisition_status": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "corporate_action_adjustment_validation": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "full_pit_timestamp_ordering": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "panel_wide_financial_debt_ratio_definition_consistency": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "future_transitive_no_peek": IMPLEMENTATION_ONLY_CONTROL_STATES,
        "b1_b8_runtime_fixes": IMPLEMENTATION_ONLY_CONTROL_STATES,
    }
)
IMPLEMENTATION_ONLY_CONTROLS_CURRENTLY_EXECUTED = False
ACQUISITION_IMPLEMENTED = False
BUILDER_IMPLEMENTED = False

# --------------------------------------------------------------------------- #
# P1…P23 — resolved disposition index
# --------------------------------------------------------------------------- #
P1_P23_DISPOSITIONS = MappingProxyType(
    {
        "P1": "RESOLVED: protocol, base, roots, and year-neutral output names are frozen",
        "P2": "RESOLVED: historical data, provenance, and experiment writes are forbidden",
        "P3": "RESOLVED: SC-1…SC-10 taxonomy is frozen with no later renumbering",
        "P4": "RESOLVED: cell evidence carries PIT, accounting, provenance, and null state",
        "P5": "RESOLVED: row eligibility uses explicit identity, membership, format, and group gates",
        "P6": "RESOLVED: D1 uses the inclusive calendar-year-end Europe/Istanbul cutoff",
        "P7": "RESOLVED: source manifest must pin source identity, rights, version, and coverage",
        "P8": "RESOLVED: G1…G6 require every applicable member and reject empty groups",
        "P9": "RESOLVED: source-class gaps are missingness, never structural non-applicability",
        "P10": (
            "RESOLVED: the legacy 17 are derived from repository provenance evidence and "
            "quarantined; build-time enforcement is deferred to implementation"
        ),
        "P11": "RESOLVED: growth requires same-filing, same-basis, comparable accounting cells",
        "P12": (
            "RESOLVED: financial_debt_ratio requires the registered definition evidence per "
            "cell or NULL; panel-wide definition_id consistency is deferred to implementation"
        ),
        "P13": (
            "RESOLVED: the price contract is append-only, adjusted-basis explicit, and "
            "missing-safe; no writer implements it yet"
        ),
        "P14": "RESOLVED: XU100 continuity is the BIST 100 PRICE_INDEX version only",
        "P15": "RESOLVED: TC-A and exact/representation-only overlap diagnostics are frozen",
        "P16": "RESOLVED: target data is physically separate from the feature panel",
        "P17": (
            "RESOLVED: the registration artifacts are structurally no-peek and no-I/O; "
            "transitive no-peek for readers that do not exist yet is deferred to implementation"
        ),
        "P18": "RESOLVED: the governed 40-feature order and both hashes are frozen",
        "P19": "RESOLVED: conflicting candidates are preserved and fail closed",
        "P20": "RESOLVED: legacy year-end writers cannot create the v2 panel",
        "P21": "RESOLVED: zero-row dry-run is a prerequisite, not implemented here",
        "P22": "RESOLVED: registry/Makefile/baseline ownership is required before first run",
        "P23": "RESOLVED: Stage 3 implementation and historical artifacts remain isolated",
    }
)
P1_P23_COUNT = 23

# --------------------------------------------------------------------------- #
# Scope negations — registration is complete; collection is deliberately held
# --------------------------------------------------------------------------- #
NEW_DATA_COLLECTED = False
OLD_DATA_CHANGED = False
SCIENTIFIC_RUN_PERFORMED = False
PREDICTIVE_EDGE_ESTABLISHED = False
V2_REDERIVES_2020_2025_ROWS = True
V1_CELLS_COPIED_INTO_V2 = False
