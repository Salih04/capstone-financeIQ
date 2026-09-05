"""Registration-only checks for the panel_v2_pit governance contract.

These tests may inspect registration sources, schemas, rules, and the frozen
repository evidence that those artifacts claim to restate. They must not fetch a
source, open a target file, build panel rows, inspect target overlap values, or
run a scientific experiment.

Two rules shape the file:

1. **Independent authority.** A registration cannot be validated against itself.
   Every material claim — the governed vector, the legacy quarantine set, the
   applicability semantics — is re-derived from an authority that predates and is
   independent of this candidate: Stage-A, ``experiments/run_experiments.py``,
   and the recorded v1 cell provenance. Comparing ``registration.py`` to a schema
   generated from ``registration.py`` proves nothing and is never done here.

2. **No conditional guarantees.** No test takes the shape "if the future module
   exists, inspect it; otherwise pass". That manufactures a structural guarantee
   out of an absent file. What exists now is proved now; what does not exist yet
   is asserted absent and recorded as deferred.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
from pathlib import Path

import scripts.panel_v2.registration as registration


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "scripts/panel_v2"
INIT_PATH = PACKAGE_DIR / "__init__.py"
REGISTRATION_PATH = PACKAGE_DIR / "registration.py"
TEST_PATH = Path(__file__).resolve()
DOC_PATH = ROOT / "docs/PREREGISTERED_PANEL_V2_PIT.md"
CELL_SCHEMA_PATH = ROOT / "docs/panel_v2/pit_cell_evidence.schema.json"
MANIFEST_SCHEMA_PATH = ROOT / "docs/panel_v2/source_manifest.schema.json"
RULES_PATH = ROOT / "docs/panel_v2/applicability_rules.csv"

# Authorities that are independent of this registration.
STAGE_A_PATH = ROOT / "docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md"
EXPERIMENTS_PATH = ROOT / "experiments/run_experiments.py"
MODELING_DATASET_PATH = ROOT / "data/trusted_clean/modeling_dataset_training_2020_2025.csv"
PROVENANCE_PATH = ROOT / "data/provenance/cell_provenance_public_2020_2025.csv"

EXPECTED_SOURCE_CLASSES = {
    "SC-1": "PIT EFFECTIVE-DATED INDEX MEMBERSHIP",
    "SC-2": "SECURITY / ISSUER / LISTING IDENTITY AND SUCCESSION",
    "SC-3": "STATEMENT-FORMAT / ENTITY-CLASS CLASSIFICATION",
    "SC-4": "PIT ANNUAL FINANCIAL STATEMENTS",
    "SC-5": "EFFECTIVE-DATED SHARES OUTSTANDING",
    "SC-6": "SECURITY PRICES + CORPORATE-ACTION ADJUSTMENT EVIDENCE",
    "SC-7": "XU100 BENCHMARK SERIES",
    "SC-8": "REALIZED T+1 TARGET PRICE INPUTS",
    "SC-9": "GROWTH SOURCE / BASE-PERIOD EVIDENCE",
    "SC-10": "FINANCIAL_DEBT_RATIO DIRECT-DEFINITION EVIDENCE",
}
FORBIDDEN_SOURCE_CLASS_SENTINELS = (
    "MISSING",
    "NOT_APPLICABLE",
    "LEGACY",
    "LEGACY_VENDOR_SNAPSHOT",
    "UNKNOWN",
    "NONE",
    "UNVERIFIED",
)
READER_CALL_NAMES = {
    "open",
    "read_csv",
    "read_json",
    "read_parquet",
    "read_excel",
    "read_text",
    "read_bytes",
    "load",
    "loads",
    "glob",
    "rglob",
    "iterdir",
    "urlopen",
    "get",
    "post",
    "request",
}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_rules() -> list[dict[str, str]]:
    with RULES_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _module_imports(source: str) -> set[str]:
    """Return every module name a source imports, at any nesting depth."""

    modules: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module or "")
    return modules


def _reader_calls(source: str) -> list[str]:
    """Return the source text of every I/O-capable call in a source file."""

    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node) in READER_CALL_NAMES:
            found.append(ast.get_source_segment(source, node) or _call_name(node))
    return found


def _normalize_condition(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "").replace("**", "")).strip().lower()


# --------------------------------------------------------------------------- #
# independent authorities
# --------------------------------------------------------------------------- #
def _stage_a_section(heading: str, next_heading: str) -> str:
    text = STAGE_A_PATH.read_text(encoding="utf-8")
    return text.split(heading)[1].split(next_heading)[0]


def _stage_a_feature_vector() -> tuple[tuple[str, ...], str, str]:
    """The governed vector and both hashes, read from Stage-A section 9."""

    section = _stage_a_section("## 9. Frozen feature authority", "## 10.")
    block = re.search(r"```\n(.*?)```", section, re.S).group(1)
    names = tuple(line.strip() for line in block.strip().splitlines() if line.strip())
    newline_sha, json_sha = re.findall(r"`([0-9a-f]{64})`", section)
    return names, newline_sha, json_sha


def _experiments_feature_vector() -> tuple[str, ...]:
    """The governed vector, re-derived the way Stage-A section 9 defines it.

    Stage-A declares the vector to be whatever ``_feature_cols`` returns for the
    modeling dataset in force. The exclusion set is lifted out of that function's
    own source by AST rather than retyped here, and only the dataset's HEADER row
    is read — no cell value, and no target value, is loaded.
    """

    tree = ast.parse(EXPERIMENTS_PATH.read_text(encoding="utf-8"))
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_feature_cols"
    )
    excluded = next(
        set(ast.literal_eval(node.value))
        for node in ast.walk(function)
        if isinstance(node, ast.Assign)
        and any(getattr(target, "id", None) == "non" for target in node.targets)
    )
    with MODELING_DATASET_PATH.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    return tuple(
        column
        for column in header
        if column not in excluded and not column.startswith("next_year_")
    )


def _provenance_legacy_features() -> tuple[str, ...]:
    """The legacy vendor-snapshot set, re-derived from recorded v1 cell provenance."""

    classes: dict[str, set[str]] = {}
    with PROVENANCE_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            classes.setdefault(row["column"], set()).add(row["source_class"])
    label = registration.LEGACY_SET_AUTHORITY_SOURCE_CLASS
    return tuple(sorted(column for column, seen in classes.items() if label in seen))


def _stage_a_groups() -> dict[str, tuple[str, ...]]:
    """Group membership, read from the Stage-A section 10.3 table."""

    groups: dict[str, tuple[str, ...]] = {}
    for line in _stage_a_section("### 10.3 ", "### 10.4 ").splitlines():
        match = re.match(r"^\|\s*(G[1-6])\s", line)
        if not match:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        groups[match.group(1)] = tuple(re.findall(r"`([a-z0-9_]+)`", cells[1]))
    return groups


def _stage_a_not_applicable_conditions() -> dict[str, str]:
    """The exhaustive Stage-A section 10.4 not-applicable conditions, per member.

    A member absent from the returned mapping is always applicable: section 10.4
    states that a member is not applicable *only* under the conditions it lists.
    """

    groups = _stage_a_groups()
    conditions: dict[str, str] = {}
    for line in _stage_a_section("### 10.4 ", "### 10.5 ").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in ("Member", "---"):
            continue
        members = list(re.findall(r"`([a-z0-9_]+)`", cells[0]))
        if not members and "five G4 growth members" in cells[0]:
            members = list(groups["G4"])
        if re.search(r"\*\*never\*\*", cells[1]):
            continue
        for member in members:
            conditions[member] = _normalize_condition(cells[1])
    return conditions


# --------------------------------------------------------------------------- #
# P1 — registration surface
# --------------------------------------------------------------------------- #
def test_registration_contract_paths_and_roots_are_frozen() -> None:
    assert registration.VERSION_ID == "panel_v2_pit"
    assert registration.PROTOCOL_ID == "FI-PANEL-V2-PIT-v1"
    assert registration.AUTHORITATIVE_BASE_COMMIT == "c418563f432f5b253fb3b0e69619c76608ea15ea"
    assert registration.REGISTRATION_ONLY is True
    assert registration.COLLECTION_READY is False
    assert registration.IMPLEMENTATION_READY is False
    assert registration.OWNER_DECISIONS_REQUIRED == "NONE"
    assert not (ROOT / registration.RAW_ROOT).exists()
    assert not (ROOT / registration.GENERATED_ROOT).exists()


def test_registration_artifact_tuple_is_the_complete_candidate_surface() -> None:
    """The tuple must name every changed path, including the package marker."""

    assert registration.REGISTRATION_ARTIFACTS == (
        "docs/PREREGISTERED_PANEL_V2_PIT.md",
        "docs/panel_v2/pit_cell_evidence.schema.json",
        "docs/panel_v2/source_manifest.schema.json",
        "docs/panel_v2/applicability_rules.csv",
        "scripts/panel_v2/__init__.py",
        "scripts/panel_v2/registration.py",
        "tests/test_panel_v2_registration.py",
        "TASK_STATE.md",
    )
    assert "scripts/panel_v2/__init__.py" in registration.REGISTRATION_ARTIFACTS
    for relative_path in registration.REGISTRATION_ARTIFACTS:
        assert (ROOT / relative_path).is_file(), relative_path

    # The package marker is exactly __init__.py. A stray init.py would make the
    # directory importable by accident under a different name, so it must not exist.
    assert INIT_PATH.is_file()
    assert not (PACKAGE_DIR / "init.py").exists()
    package_files = sorted(path.name for path in PACKAGE_DIR.glob("*.py"))
    assert package_files == ["__init__.py", "registration.py"]


def test_registration_import_is_inert_and_has_no_acquisition_imports() -> None:
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.extend(f"{node.module}:{alias.name}" for alias in node.names)
    assert imports == ["__future__:annotations", "types:MappingProxyType"]
    assert registration.IMPORT_INERT is True
    assert registration.REGISTRATION_MODULE_PERFORMS_IO is False
    assert _reader_calls(source) == []


# --------------------------------------------------------------------------- #
# H5 — source-class taxonomy
# --------------------------------------------------------------------------- #
def test_source_class_taxonomy_is_exactly_sc1_to_sc10_on_every_surface() -> None:
    assert {key: spec["name"] for key, spec in registration.SOURCE_CLASSES.items()} == (
        EXPECTED_SOURCE_CLASSES
    )
    assert registration.SOURCE_CLASS_IDS == tuple(EXPECTED_SOURCE_CLASSES)
    assert registration.SOURCE_CLASS_TAXONOMY_IS_CLOSED is True
    assert registration.SOURCE_CLASS_SENTINELS_FORBIDDEN == FORBIDDEN_SOURCE_CLASS_SENTINELS
    assert registration.LEGACY_SOURCE_LABEL_IS_REGISTERED_SOURCE_CLASS is False
    assert registration.LEGACY_SOURCE_LABEL not in registration.SOURCE_CLASS_IDS

    expected = list(EXPECTED_SOURCE_CLASSES)

    # The PIT cell schema admits the ten ids and null, and nothing else.
    cell = _load_json(CELL_SCHEMA_PATH)
    cell_enum = cell["$defs"]["source_class"]["enum"]
    assert cell_enum == [None, *expected]
    for sentinel in FORBIDDEN_SOURCE_CLASS_SENTINELS:
        assert sentinel not in cell_enum

    # The manifest schema admits the ten ids and nothing else — not even null.
    manifest = _load_json(MANIFEST_SCHEMA_PATH)
    manifest_enum = manifest["$defs"]["source_class"]["enum"]
    assert manifest_enum == expected
    for sentinel in FORBIDDEN_SOURCE_CLASS_SENTINELS:
        assert sentinel not in manifest_enum

    # The registration document tabulates the same ten ids in the same order.
    document = DOC_PATH.read_text(encoding="utf-8")
    documented = re.findall(r"^\| `(SC-\d+)` \| (.+?) \|$", document, re.M)
    assert [identifier for identifier, _ in documented] == expected
    assert [name.strip() for _, name in documented] == list(EXPECTED_SOURCE_CLASSES.values())

    # Only a null cell may omit a source class.
    assert registration.SOURCE_CLASS_NULL_ALLOWED_ONLY_ON_NULL_CELL is True
    branch = next(
        rule
        for rule in cell["allOf"]
        if rule["if"].get("properties", {}).get("source_class") == {"type": "null"}
    )
    assert branch["then"]["properties"]["is_null"] == {"const": True}


# --------------------------------------------------------------------------- #
# H3 — the governed feature vector, proved against independent authority
# --------------------------------------------------------------------------- #
def test_governed_vector_matches_stage_a_and_the_experiments_filter() -> None:
    stage_a_names, stage_a_newline_sha, stage_a_json_sha = _stage_a_feature_vector()
    derived_names = _experiments_feature_vector()

    # Two authorities that know nothing about this registration agree with each other.
    assert stage_a_names == derived_names
    assert len(stage_a_names) == 40

    # ...and the registration restates them exactly, in order.
    assert registration.GOVERNED_FEATURES_V2 == stage_a_names
    assert registration.GOVERNED_FEATURE_COUNT == 40
    assert len(registration.GOVERNED_FEATURES_V2) == 40
    assert len(set(registration.GOVERNED_FEATURES_V2)) == 40

    # ...and both registered serializations reproduce the Stage-A hashes.
    newline_sha = hashlib.sha256("\n".join(stage_a_names).encode("utf-8")).hexdigest()
    json_sha = hashlib.sha256(
        json.dumps(list(stage_a_names), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert newline_sha == stage_a_newline_sha == registration.GOVERNED_FEATURES_V2_NEWLINE_SHA256
    assert json_sha == stage_a_json_sha == registration.GOVERNED_FEATURES_V2_JSON_SHA256

    # The vector carries no target, PIT metadata, identity helper, eligibility, or
    # legacy-unverified name.
    governed = set(registration.GOVERNED_FEATURES_V2)
    assert governed.isdisjoint(registration.TARGET_FORBIDDEN_IN_PANEL_COLUMNS)
    assert governed.isdisjoint(registration.FEATURE_METADATA_FORBIDDEN_IN_VECTOR)
    assert governed.isdisjoint(registration.PANEL_IDENTITY_COLUMNS)
    assert governed.isdisjoint(registration.TARGET_IDENTITY_COLUMNS)
    assert governed.isdisjoint(registration.ROW_ELIGIBILITY_FIELDS)
    assert not any(
        name.endswith(registration.LEGACY_NAMESPACE_SUFFIX) for name in governed
    )
    assert registration.PANEL_CONTAINS_TARGET is False
    assert registration.TARGET_PHYSICALLY_SEPARATE is True


def test_manifest_schema_freezes_the_vector_identity_so_it_cannot_be_impersonated() -> None:
    stage_a_names, newline_sha, json_sha = _stage_a_feature_vector()
    resolution = _load_json(MANIFEST_SCHEMA_PATH)["properties"]["feature_resolution"]

    assert resolution["additionalProperties"] is False
    assert set(resolution["required"]) == {
        "resolved_features",
        "count",
        "newline_sha256",
        "json_sha256",
        "matches_registered_hash",
    }
    features = resolution["properties"]["resolved_features"]
    # prefixItems pins name AND position; items:false forbids a 41st entry.
    assert [item["const"] for item in features["prefixItems"]] == list(stage_a_names)
    assert features["minItems"] == features["maxItems"] == 40
    assert features["items"] is False
    assert features["uniqueItems"] is True
    # The hashes are consts, not free-form digests, so a manifest built over a
    # different vector fails validation instead of asserting its own correctness.
    assert resolution["properties"]["count"] == {"const": 40}
    assert resolution["properties"]["newline_sha256"] == {"const": newline_sha}
    assert resolution["properties"]["json_sha256"] == {"const": json_sha}
    assert resolution["properties"]["matches_registered_hash"] == {"const": True}


def test_concept_groups_match_stage_a_and_partition_the_forty_features() -> None:
    stage_a_groups = _stage_a_groups()
    registered = {
        group_id: tuple(group["members"])
        for group_id, group in registration.CONCEPT_GROUPS.items()
    }
    assert {key: set(value) for key, value in registered.items()} == {
        key: set(value) for key, value in stage_a_groups.items()
    }
    members = [member for group in registered.values() for member in group]
    assert len(members) == len(set(members)) == 40
    assert set(members) == set(registration.GOVERNED_FEATURES_V2)
    assert registration.VACUOUS_GROUP_SATISFACTION_ALLOWED is False
    assert registration.MISSINGNESS_GATE_RELAXATION_ALLOWED is False
    assert registration.SOURCE_CLASS_GAP_IS_NOT_APPLICABLE is False


# --------------------------------------------------------------------------- #
# H3 / D5 — legacy 17 quarantine, proved against recorded v1 provenance
# --------------------------------------------------------------------------- #
def test_legacy_seventeen_match_the_recorded_vendor_snapshot_provenance() -> None:
    assert registration.LEGACY_SET_AUTHORITY_PATH == "data/provenance/cell_provenance_public_2020_2025.csv"
    evidence = _provenance_legacy_features()

    assert len(evidence) == 17
    assert registration.LEGACY_VENDOR_SNAPSHOT_FEATURES == evidence
    assert registration.LEGACY_VENDOR_SNAPSHOT_FEATURE_COUNT == 17
    assert set(evidence) < set(registration.GOVERNED_FEATURES_V2)

    assert registration.LEGACY_NAMESPACE_SUFFIX == "_legacy_unverified"
    assert registration.LEGACY_DEFAULT_VALUE_IS_NULL is True
    assert registration.LEGACY_MAY_POPULATE_GOVERNED_FEATURE is False
    assert registration.LEGACY_GOVERNED_NAME_SUBSTITUTION_ALLOWED is False
    assert registration.LEGACY_DECLARABLE_AS_GOVERNED_VALUE_ORIGIN is False
    assert registration.LEGACY_RESOLVES_INTO_CONFIRMATORY_VECTOR is False

    quarantine = _load_json(MANIFEST_SCHEMA_PATH)["properties"]["legacy_quarantine"]
    assert [item["const"] for item in quarantine["properties"]["legacy_features"]["prefixItems"]] == (
        list(evidence)
    )
    assert quarantine["properties"]["count"] == {"const": 17}
    assert quarantine["properties"]["namespace_suffix"] == {"const": "_legacy_unverified"}
    assert quarantine["properties"]["legacy_is_registered_source_class"] == {"const": False}
    assert quarantine["properties"]["governed_name_substitution_allowed"] == {"const": False}
    assert quarantine["properties"]["accepted_value_origin_for_governed_features"] == {
        "const": False
    }
    assert "legacy_quarantine" in _load_json(MANIFEST_SCHEMA_PATH)["required"]

    # Enforcement at build time is a future gate and is not claimed as done.
    assert registration.LEGACY_QUARANTINE_BUILD_TIME_ENFORCEMENT == "DEFERRED_TO_IMPLEMENTATION"
    assert registration.LEGACY_QUARANTINE_CURRENTLY_ENFORCED_BY_A_BUILDER is False


# --------------------------------------------------------------------------- #
# C1 — evidence column domain and the fail-closed non-null contract
# --------------------------------------------------------------------------- #
def test_cell_schema_column_domain_is_exactly_the_governed_forty() -> None:
    stage_a_names, _, _ = _stage_a_feature_vector()
    schema = _load_json(CELL_SCHEMA_PATH)

    assert schema["$schema"].endswith("draft/2020-12/schema")
    assert schema["additionalProperties"] is False
    assert schema["properties"]["column"] == {"$ref": "#/$defs/governed_feature"}
    domain = schema["$defs"]["governed_feature"]
    assert domain["type"] == "string"
    assert domain["enum"] == list(stage_a_names)
    assert "minLength" not in schema["properties"]["column"]

    # Nothing outside the governed vector can be recorded as a feature cell.
    forbidden = {
        *registration.TARGET_FORBIDDEN_IN_PANEL_COLUMNS,
        *registration.FEATURE_METADATA_FORBIDDEN_IN_VECTOR,
        *registration.ROW_ELIGIBILITY_FIELDS,
        *(f"{name}{registration.LEGACY_NAMESPACE_SUFFIX}" for name in stage_a_names),
        "target_return_pct",
        "next_year_return_pct",
        "target_year",
        "anything_at_all",
    }
    assert set(domain["enum"]).isdisjoint(forbidden)
    assert registration.PIT_CELL_EVIDENCE_COLUMN_DOMAIN_IS_GOVERNED_40 is True
    assert registration.PIT_CELL_EVIDENCE_ARBITRARY_COLUMN_ALLOWED is False
    assert registration.LEGACY_CELLS_RECORDED_IN_PIT_CELL_EVIDENCE is False


def test_cell_schema_cannot_accept_a_non_null_cell_without_pit_evidence() -> None:
    schema = _load_json(CELL_SCHEMA_PATH)
    assert "is_null" in schema["required"]
    assert set(registration.REQUIRED_SEPARATE_PIT_FIELDS) <= set(schema["required"])
    assert set(registration.ACCOUNTING_COMPARISON_FIELDS) <= set(schema["required"])
    assert "publication_date" not in schema["properties"]

    branch = next(
        rule
        for rule in schema["allOf"]
        if rule["if"].get("properties", {}).get("is_null") == {"const": False}
    )
    assert branch["if"]["required"] == ["is_null"]
    then = branch["then"]

    # pit_ok=false is unrepresentable for a non-null cell.
    assert then["properties"]["pit_ok"] == {"const": True}
    # A non-null cell must originate from a value-originating class.
    assert then["properties"]["source_class"]["enum"] == list(
        registration.VALUE_ORIGINATING_SOURCE_CLASSES
    )
    # Temporal evidence must be present and non-nullable (the strict $def, which
    # unlike the nullable one does not admit null).
    strict = {"$ref": "#/$defs/timestamp"}
    for field in ("first_publication_timestamp", "knowledge_timestamp", "retrieval_timestamp"):
        assert then["properties"][field] == strict, field
        assert schema["$defs"]["timestamp"]["type"] == "string"
    assert then["properties"]["pit_cutoff_timestamp"]["type"] == "string"
    assert then["properties"]["document_sha256"] == {"$ref": "#/$defs/sha256"}
    assert schema["$defs"]["sha256"]["type"] == "string"
    assert then["properties"]["value"] == {"type": "number"}
    assert then["properties"]["null_reason"] == {"type": "null"}
    assert then["properties"]["frozen_screen_status"]["enum"] == list(
        registration.ADMISSIBLE_FROZEN_SCREEN_STATUSES
    )
    required = set(then["required"])
    assert {
        "pit_ok",
        "source_class",
        "source_id",
        "source_document_id",
        "source_ref",
        "document_sha256",
        "extraction_method",
        "first_publication_timestamp",
        "knowledge_timestamp",
        "retrieval_timestamp",
        "pit_cutoff_timestamp",
        "frozen_screen_status",
    } <= required

    # A null cell must carry a registered reason and no value.
    null_branch = next(
        rule
        for rule in schema["allOf"]
        if rule["if"].get("properties", {}).get("is_null") == {"const": True}
    )
    assert null_branch["then"]["properties"]["value"] == {"type": "null"}
    assert null_branch["then"]["properties"]["null_reason"]["type"] == "string"
    assert null_branch["then"]["properties"]["null_reason"]["enum"] == list(
        registration.NULL_REASONS
    )
    assert "null_reason" in null_branch["then"]["required"]


def test_pit_timestamp_ordering_is_registered_as_deferred_not_as_enforced() -> None:
    """Draft 2020-12 cannot compare two instance timestamps; say so, don't pretend."""

    assert registration.PIT_TIMESTAMP_ORDERING_ENFORCEMENT == "DEFERRED_TO_IMPLEMENTATION"
    assert registration.PIT_TIMESTAMP_ORDERING_CURRENTLY_ENFORCED is False
    assert registration.PIT_OK_IS_COMPUTED_NEVER_TRUSTED_FROM_INPUT is True
    assert registration.IMPLEMENTATION_VALIDATOR_EXISTS is False
    assert registration.PIT_COMPARISON == "first_publication_timestamp <= pit_cutoff_timestamp"
    assert registration.UNKNOWN_FIRST_PUBLICATION_DISPOSITION == "PIT_UNVERIFIABLE"

    contract = _load_json(CELL_SCHEMA_PATH)["x-implementation-validator-contract"]
    assert contract["status"] == "DEFERRED_TO_IMPLEMENTATION"
    assert contract["not_yet_executed"] is True
    assert contract["pit_ok_is_computed_never_trusted"] is True
    assert set(contract["must_fail_closed_when"]) >= set(
        registration.IMPLEMENTATION_VALIDATOR_FAIL_CLOSED_CONDITIONS[:2]
    )
    assert len(contract["must_fail_closed_when"]) == len(
        registration.IMPLEMENTATION_VALIDATOR_FAIL_CLOSED_CONDITIONS
    )


# --------------------------------------------------------------------------- #
# C2 — financial_debt_ratio direct-definition gate
# --------------------------------------------------------------------------- #
def test_financial_debt_ratio_cannot_be_non_null_without_definition_evidence() -> None:
    schema = _load_json(CELL_SCHEMA_PATH)
    branch = next(
        rule
        for rule in schema["allOf"]
        if rule["if"].get("properties", {}).get("column") == {"const": "financial_debt_ratio"}
        and rule["if"]["properties"].get("is_null") == {"const": False}
    )
    assert sorted(branch["if"]["required"]) == ["column", "is_null"]
    then = branch["then"]

    assert then["properties"]["source_class"] == {"const": "SC-10"}
    for field in registration.FINANCIAL_DEBT_RATIO_REQUIRED_DEFINITION_METADATA:
        assert field in then["required"], field
        assert field in schema["properties"], field
    assert set(registration.FINANCIAL_DEBT_RATIO_REQUIRED_DEFINITION_METADATA) == {
        "definition_id",
        "definition_text",
        "numerator_definition",
        "denominator_definition",
        "definition_source_document_id",
        "definition_publication_date",
    }

    # definition_id may not be empty, null, or a sentinel.
    definition_id = then["properties"]["definition_id"]
    assert definition_id["type"] == "string"
    assert definition_id["minLength"] == 1
    assert set(definition_id["not"]["enum"]) == set(
        registration.FINANCIAL_DEBT_RATIO_FORBIDDEN_DEFINITION_ID_VALUES
    ) - {""}

    assert registration.FINANCIAL_DEBT_RATIO_REPOSITORY_DERIVATION_ALLOWED is False
    assert registration.FINANCIAL_DEBT_RATIO_REQUIRES_EXPLICIT_SOURCE_VALUE is True
    assert registration.FINANCIAL_DEBT_RATIO_FORMULA_INVENTED_HERE is False
    assert registration.FINANCIAL_DEBT_RATIO_FALLBACK == "NULL"
    assert registration.FINANCIAL_DEBT_RATIO_NULL_REASON == "DEFINITION_UNAVAILABLE"
    assert "DEFINITION_UNAVAILABLE" in registration.NULL_REASONS

    # G5 consequences stay exactly Stage-A: a null debt ratio fails the group.
    assert "financial_debt_ratio" in registration.CONCEPT_GROUPS["G5"]["members"]
    assert registration.FINANCIAL_DEBT_RATIO_G5_CONSEQUENCE_ACCEPTED is True
    assert registration.SECTION_10_3_RELAXATION_ALLOWED is False
    assert registration.MISSINGNESS_GATE_RELAXATION_ALLOWED is False

    # Panel-wide definition_id consistency is relational and cannot be a schema claim.
    assert registration.FINANCIAL_DEBT_RATIO_REQUIRES_PANEL_WIDE_DEFINITION_ID is True
    assert (
        registration.FINANCIAL_DEBT_RATIO_PANEL_WIDE_CONSISTENCY_ENFORCEMENT
        == "DEFERRED_TO_IMPLEMENTATION"
    )
    assert registration.FINANCIAL_DEBT_RATIO_PANEL_WIDE_CONSISTENCY_CURRENTLY_ENFORCED is False


# --------------------------------------------------------------------------- #
# H2 — applicability rules, checked against Stage-A rather than against themselves
# --------------------------------------------------------------------------- #
def test_applicability_rules_have_the_registered_shape() -> None:
    with RULES_PATH.open(newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    assert tuple(header) == registration.APPLICABILITY_RULE_COLUMNS
    assert len(header) == 12

    rows = _read_rules()
    assert len(rows) == registration.APPLICABILITY_RULE_COUNT == 48
    identifiers = [row["rule_id"] for row in rows]
    assert identifiers == [f"AR-{index:03d}" for index in range(1, 49)]
    assert len(set(identifiers)) == 48

    for row in rows:
        assert row["rule_kind"] in registration.APPLICABILITY_RULE_KINDS
        assert row["applicability"] in registration.APPLICABILITY_VALUES
        classes = set(row["required_source_classes"].split(";"))
        assert classes <= set(registration.SOURCE_CLASS_IDS)
        # SC-8 is target-side and never gates a governed feature cell.
        assert "SC-8" not in classes
        for token in filter(None, row["null_reason_when_applicable_but_absent"].split(";")):
            assert token in registration.NULL_REASONS, token
        for token in filter(None, row["null_reason_when_not_applicable"].split(";")):
            assert token in registration.NULL_REASONS, token
        assert row["basis"].strip()


def test_every_applicability_rule_matches_stage_a_semantics() -> None:
    """All 48 rows are audited against Stage-A 10.3/10.4, not just AR-042 and AR-044."""

    groups = _stage_a_groups()
    group_of = {member: group for group, members in groups.items() for member in members}
    conditions = _stage_a_not_applicable_conditions()
    rows = _read_rules()

    def scope(feature_cell: str) -> tuple[str, ...]:
        if feature_cell == "(all governed features)":
            return tuple(sorted(group_of))
        if feature_cell == "(five growth features)":
            return groups["G4"]
        return (feature_cell,)

    # The 40 per-feature rules cover the governed vector once each, in order.
    feature_rows = [row for row in rows if row["rule_kind"] == "APPLICABILITY"]
    assert len(feature_rows) == 40
    assert [row["feature"] for row in feature_rows] == sorted(group_of)
    assert {row["feature"]: row["concept_group"] for row in feature_rows} == group_of

    for row in rows:
        members = scope(row["feature"])
        assert members, row["rule_id"]
        assert set(members) <= set(group_of), row["rule_id"]
        verdicts = {conditions.get(member) for member in members}

        if len(verdicts) > 1:
            # A gate spanning features whose Stage-A verdicts differ may not assert
            # any single applicability verdict of its own.
            assert row["applicability"] == "PER_FEATURE_APPLICABILITY", row["rule_id"]
            assert row["feature"] in registration.APPLICABILITY_SCOPE_TOKENS
            assert row["not_applicable_when"] == "", row["rule_id"]
            continue

        condition = verdicts.pop()
        if condition is None:
            assert row["applicability"] == "ALWAYS_APPLICABLE", row["rule_id"]
            assert row["not_applicable_when"] == "", row["rule_id"]
            assert row["null_reason_when_not_applicable"] == "", row["rule_id"]
            assert row["when_condition_unevidenced"] == "N/A", row["rule_id"]
        else:
            assert row["applicability"] == "CONDITIONAL", row["rule_id"]
            assert _normalize_condition(row["not_applicable_when"]) == condition, row["rule_id"]
            assert row["condition_evidence_required"].strip(), row["rule_id"]
            assert row["when_condition_unevidenced"] == (
                registration.UNEVIDENCED_CONDITION_DISPOSITION
            ), row["rule_id"]
            assert row["null_reason_when_not_applicable"] == "NOT_APPLICABLE", row["rule_id"]

    # Stage-A 10.4 declares exactly thirteen conditional members; no more, no fewer.
    assert len(conditions) == 13
    assert sum(1 for row in feature_rows if row["applicability"] == "CONDITIONAL") == 13


def test_ar_042_and_ar_044_are_corrected_to_the_stage_a_contract() -> None:
    conditions = _stage_a_not_applicable_conditions()
    rows = {row["rule_id"]: row for row in _read_rules()}

    growth = rows["AR-042"]
    assert growth["rule_kind"] == "ADMISSIBILITY"
    assert growth["feature"] == "(five growth features)"
    assert growth["concept_group"] == "G4"
    assert growth["applicability"] == "CONDITIONAL"
    assert _normalize_condition(growth["not_applicable_when"]) == (
        conditions["revenue_growth_pct"]
    )
    assert growth["when_condition_unevidenced"] == "APPLICABLE_AND_FAIL_CLOSED"
    assert growth["null_reason_when_not_applicable"] == "NOT_APPLICABLE"
    # The invalid composite token is gone; both registered reasons are named.
    assert growth["null_reason_when_applicable_but_absent"] == "BASIS_MISMATCH;BASIS_UNKNOWN"
    assert "BASIS_MISMATCH_OR_BASIS_UNKNOWN" not in RULES_PATH.read_text(encoding="utf-8")
    assert growth["required_source_classes"] == "SC-4;SC-9"

    drawdown = rows["AR-044"]
    assert drawdown["rule_kind"] == "ADMISSIBILITY"
    assert drawdown["feature"] == "price_drawdown_from_3y_high_pct"
    assert drawdown["applicability"] == "CONDITIONAL"
    assert _normalize_condition(drawdown["not_applicable_when"]) == (
        conditions["price_drawdown_from_3y_high_pct"]
    )
    assert drawdown["when_condition_unevidenced"] == "APPLICABLE_AND_FAIL_CLOSED"
    assert drawdown["null_reason_when_not_applicable"] == "NOT_APPLICABLE"
    assert drawdown["null_reason_when_applicable_but_absent"] == "WINDOW_INCOMPLETE"
    # Its admissibility verdict must agree with the AR-029 applicability rule.
    assert _normalize_condition(rows["AR-029"]["not_applicable_when"]) == (
        _normalize_condition(drawdown["not_applicable_when"])
    )

    # Stage-A 10.5: a source-class gap for a defined concept is missingness.
    assert rows["AR-010"]["feature"] == "financial_debt_ratio"
    assert rows["AR-010"]["null_reason_when_applicable_but_absent"] == "MISSING_SOURCE_CLASS_GAP"
    assert rows["AR-043"]["null_reason_when_applicable_but_absent"] == "DEFINITION_UNAVAILABLE"
    assert registration.SOURCE_CLASS_GAP_DISPOSITION == "MISSING_SOURCE_CLASS_GAP"
    assert registration.APPLICABILITY_STAGE_A_EXTENSION_ALLOWED is False


# --------------------------------------------------------------------------- #
# H1 — no-peek: prove what exists, defer what does not
# --------------------------------------------------------------------------- #
def test_registration_package_has_no_target_reading_path_at_all() -> None:
    package_sources = sorted(PACKAGE_DIR.glob("*.py"))
    assert [path.name for path in package_sources] == ["__init__.py", "registration.py"]

    imported: set[str] = set()
    for path in package_sources:
        source = path.read_text(encoding="utf-8")
        # No I/O-capable call anywhere in the package.
        assert _reader_calls(source) == [], path.name
        imported |= _module_imports(source)

    # Import closure: the package reaches nothing that could open a file. Because
    # the closure is empty of readers at depth one, there is no transitive path.
    assert imported <= {"__future__", "types"}, imported
    assert registration.NO_PEEK_REGISTRATION_GUARD is True
    assert registration.NO_PEEK_TARGET_READ_ALLOWED is False
    assert registration.NO_PEEK_TARGET_FILENAME == "panel_targets.csv"
    assert registration.NO_PEEK_TARGET_COLUMN_NAMES == (
        registration.TARGET_FORBIDDEN_IN_PANEL_COLUMNS
    )


def test_no_registration_artifact_opens_the_target_artifact() -> None:
    target_terms = {
        registration.NO_PEEK_TARGET_FILENAME,
        registration.GENERATED_FILENAMES["targets"],
        *registration.NO_PEEK_TARGET_COLUMN_NAMES,
    }
    for path in (INIT_PATH, REGISTRATION_PATH, TEST_PATH):
        source = path.read_text(encoding="utf-8")
        for call_source in _reader_calls(source):
            assert not any(term in call_source for term in target_terms), (
                f"{path.name}: {call_source}"
            )
    # The target artifact is not present, and nothing here created it.
    assert not (ROOT / registration.GENERATED_ROOT).exists()


def test_future_transitive_no_peek_is_deferred_not_silently_satisfied() -> None:
    """A test that inspects a future reader 'if it exists' proves nothing.

    So the future readers are asserted ABSENT, and the obligation to audit their
    transitive import and read closure is recorded as an implementation gate.
    """

    for relative_path in registration.NO_PEEK_FUTURE_IMPLEMENTATION_READERS:
        assert not (ROOT / relative_path).exists(), relative_path
    assert registration.FUTURE_NO_PEEK_ENFORCEMENT == "DEFERRED_TO_IMPLEMENTATION"
    assert registration.FUTURE_TRANSITIVE_NO_PEEK_PROVEN is False
    assert "transitive import and read" in registration.FUTURE_NO_PEEK_IMPLEMENTATION_GATE
    assert registration.NO_PEEK_REGISTRATION_SURFACE == (
        "scripts/panel_v2/__init__.py",
        "scripts/panel_v2/registration.py",
        "tests/test_panel_v2_registration.py",
    )


# --------------------------------------------------------------------------- #
# H4 / M3 — nothing is closed, and nothing is claimed to run
# --------------------------------------------------------------------------- #
def test_b1_to_b8_are_registered_contracts_and_not_closed_by_design() -> None:
    assert set(registration.INPUT_DEFECT_STATUS) == {f"B{index}" for index in range(1, 9)}
    for defect, (registered, enforcement) in registration.INPUT_DEFECT_STATUS.items():
        assert registered in registration.DEFECT_REGISTRATION_STATUSES, defect
        assert enforcement in registration.DEFECT_ENFORCEMENT_STATUSES, defect
        # Registration freezes intent; it does not implement it.
        assert enforcement == "DEFERRED_TO_IMPLEMENTATION", defect
    assert registration.B1_B8_RUNTIME_ENFORCED is False
    assert registration.B1_B8_IMPLEMENTATION_TESTS_EXIST is False
    assert not hasattr(registration, "B1_B8_CLOSED_BY_DESIGN")
    assert not hasattr(registration, "INPUT_DEFECT_DISPOSITIONS")

    # The claim must be absent from every registration surface, not just renamed.
    for path in (REGISTRATION_PATH, DOC_PATH, INIT_PATH, RULES_PATH):
        text = path.read_text(encoding="utf-8")
        assert "CLOSED_BY_DESIGN" not in text, path.name
        assert "closed by design" not in text.lower(), path.name


def test_implementation_only_controls_are_not_reported_as_enforced() -> None:
    expected = {
        "source_rounding_reconciliation",
        "append_only_acquisition_writer",
        "no_overwrite_behaviour",
        "explicit_acquisition_status",
        "corporate_action_adjustment_validation",
        "full_pit_timestamp_ordering",
        "panel_wide_financial_debt_ratio_definition_consistency",
        "future_transitive_no_peek",
        "b1_b8_runtime_fixes",
    }
    assert set(registration.IMPLEMENTATION_ONLY_CONTROLS) == expected
    for control, states in registration.IMPLEMENTATION_ONLY_CONTROLS.items():
        assert states == ("REGISTERED", "IMPLEMENTATION_REQUIRED", "NOT_YET_EXECUTED"), control
    assert registration.IMPLEMENTATION_ONLY_CONTROLS_CURRENTLY_EXECUTED is False
    assert registration.ACQUISITION_IMPLEMENTED is False
    assert registration.BUILDER_IMPLEMENTED is False
    assert registration.DRY_RUN_IMPLEMENTED_AT_REGISTRATION is False
    assert registration.ARTIFACT_REGISTRY_EDITED_AT_REGISTRATION is False

    contract = _load_json(MANIFEST_SCHEMA_PATH)["x-implementation-validator-contract"]
    assert contract["status"] == "DEFERRED_TO_IMPLEMENTATION"
    assert contract["not_yet_executed"] is True
    assert len(contract["controls"]) == len(expected)


# --------------------------------------------------------------------------- #
# owner locks D1–D7
# --------------------------------------------------------------------------- #
def test_d1_preserves_calendar_cutoff_and_separates_fiscal_year() -> None:
    assert registration.PIT_CUTOFF_TIMEZONE == "Europe/Istanbul"
    assert registration.PIT_CUTOFF_INCLUSIVE is True
    assert registration.PIT_CUTOFF_DATE_TEMPLATE == "{feature_year}-12-31"
    assert registration.PIT_CUTOFF_TIMESTAMP_TEMPLATE.endswith("23:59:59.999999+03:00")
    assert registration.FISCAL_YEAR_T_FILING_ADMISSIBLE_FOR_FEATURE_YEAR_T is False
    assert registration.FEATURE_YEAR_EQUALS_FISCAL_YEAR is False
    assert registration.RETRIEVAL_TIMESTAMP_IS_NOT_FIRST_PUBLICATION_TIMESTAMP is True
    assert registration.REQUIRED_SEPARATE_PIT_FIELDS == (
        "feature_year",
        "fiscal_year_of_record",
        "source_document_id",
        "first_publication_timestamp",
        "pit_cutoff_timestamp",
    )
    cutoff = _load_json(CELL_SCHEMA_PATH)["properties"]["pit_cutoff_timestamp"]
    assert cutoff["pattern"] == r"^[0-9]{4}-12-31T23:59:59\.999999\+03:00$"


def test_d2_target_and_overlap_policy_have_no_arbitrary_numeric_bound() -> None:
    assert registration.TARGET_ID == "TC-A"
    assert registration.TARGET_FORMULA_ID == "TC-A_YEAR_END_ADJUSTED_RETURN"
    assert registration.TARGET_FORMULA == "100 * (P_adj(T+1) / P_adj(T) - 1)"
    assert registration.TARGET_WINDOW == "feature_year T year-end to target_year T+1 year-end"
    assert registration.TARGET_PHYSICALLY_SEPARATE is True
    assert registration.PANEL_CONTAINS_TARGET is False
    assert registration.TARGET_REVISES_FROZEN_V1 is False
    assert registration.FROZEN_TARGETS_EVER_REWRITTEN is False
    assert registration.TARGET_OVERLAP_ARITHMETIC == "decimal"
    assert registration.TARGET_OVERLAP_REQUIRES_EXACT_STABLE_SECURITY_IDENTITY is True
    assert registration.TARGET_OVERLAP_REQUIRES_EXACT_TARGET_WINDOW is True
    assert registration.TARGET_OVERLAP_ARBITRARY_NUMERIC_BOUND is None
    assert registration.TARGET_OVERLAP_UNKNOWN_ROUNDING_RULE == "no_representation_bound"
    assert registration.TARGET_OVERLAP_TUNING_AFTER_INSPECTION_ALLOWED is False
    assert registration.TARGET_OVERLAP_AVERAGING_ALLOWED is False
    assert registration.TARGET_OVERLAP_SELECTION_ROLE == (
        "DIAGNOSTIC_ONLY_NOT_PREDICTIVE_OUTCOME_SELECTION"
    )
    source = REGISTRATION_PATH.read_text(encoding="utf-8")
    document = DOC_PATH.read_text(encoding="utf-8")
    forbidden_bound_name = "TARGET_OVERLAP_" + "TOL"
    forbidden_decimal = "0." + "01"
    assert forbidden_bound_name not in source
    assert forbidden_decimal not in source
    assert forbidden_decimal not in document


def test_d4_tms29_and_growth_bases_are_separate_and_fail_closed() -> None:
    expected = (
        "accounting_framework_id",
        "measurement_basis",
        "value_version",
        "measuring_unit_date",
        "currency_code",
        "consolidation_basis",
    )
    assert registration.ACCOUNTING_COMPARISON_FIELDS == expected
    assert registration.GROWTH_REQUIRED_MATCHES == expected
    assert registration.TMS29_RESTATED_CURRENT_WITH_SAME_FILING_COMPARATIVE_ALLOWED is True
    assert registration.TMS29_RESTATED_CURRENT_WITH_OLD_NOMINAL_FILING_ALLOWED is False
    assert registration.GROWTH_SAME_FILING_REQUIRED is True
    assert registration.GROWTH_UNKNOWN_OR_MISMATCH_DISPOSITION == "NULL"
    assert registration.GROWTH_CROSS_FILING_COMPOSITION_ALLOWED is False
    assert registration.GROWTH_REBASING_BY_PIPELINE_ALLOWED is False
    assert "separate fields" in registration.TAS29_POLICY
    assert "same first-public filing" in registration.TAS29_POLICY
    assert set(registration.GROWTH_FEATURES) == set(_stage_a_groups()["G4"])


def test_d6_benchmark_and_d7_rederivation_locks_hold() -> None:
    assert registration.BENCHMARK_INSTRUMENT_ID == "XU100.IS"
    assert registration.BENCHMARK_INSTRUMENT_CONCEPT == "BIST 100 PRICE INDEX"
    assert registration.BENCHMARK_INDEX_VARIANT == "PRICE_INDEX"
    assert registration.BENCHMARK_VARIANTS_INTERCHANGEABLE is False
    assert registration.BENCHMARK_CONTINUOUS_SERIES_ACROSS_VARIANTS_ALLOWED is False
    assert registration.BENCHMARK_TOTAL_RETURN_VERSION_ID != registration.BENCHMARK_VERSION_ID
    assert registration.BENCHMARK_FROZEN_V1_REWRITE_ALLOWED is False
    assert registration.BENCHMARK_OLD_COLLECTOR_ALLOWED is False
    assert registration.PRICE_LEDGER_APPEND_ONLY is True
    assert registration.PRICE_LEDGER_OVERWRITE_ALLOWED is False
    assert registration.PRICE_STATUS_DEFAULTING_ALLOWED is False
    assert registration.V1_CELLS_COPIED_INTO_V2 is False
    assert registration.V2_REDERIVES_2020_2025_ROWS is True


# --------------------------------------------------------------------------- #
# feasibility, P-index, and scope negations
# --------------------------------------------------------------------------- #
def test_feasibility_is_conditional_and_collection_stays_held() -> None:
    assert registration.FULL_PANEL_FEASIBLE == "CONDITIONAL"
    assert registration.FULL_PANEL_FEASIBLE_CONFIRMED is False
    assert registration.SOURCE_FEASIBILITY_STATUS == "CONDITIONAL_NOT_CONFIRMED"
    assert registration.COLLECTION_BLOCKING_SOURCE_CLASSES == ("SC-1", "SC-2", "SC-5", "SC-6", "SC-8")
    assert registration.SOURCE_ACCESS_DEPTH_GATES == ("SC-4", "SC-7")
    assert registration.SOURCE_NORMALIZATION_DEFINITION_GATES == ("SC-3", "SC-9", "SC-10")
    assert registration.SOURCE_FEASIBILITY_ACCESS_LICENSE_PREREQUISITE is True
    assert registration.EXTERNAL_RIGHTS_AGREEMENTS_REQUIRED is True
    assert "owner authorization alone" in registration.RESTRICTED_SOURCE_POLICY
    assert set(registration.SOURCE_FEASIBILITY_DISPOSITIONS) == set(registration.SOURCE_CLASS_IDS)
    manifest = _load_json(MANIFEST_SCHEMA_PATH)["properties"]["source_feasibility"]
    assert manifest["properties"]["collection_ready"] == {"const": False}
    assert manifest["properties"]["access_license_checks_required"] == {"const": True}


def test_p1_to_p23_are_all_resolved_in_registration() -> None:
    assert set(registration.P1_P23_DISPOSITIONS) == {f"P{index}" for index in range(1, 24)}
    assert registration.P1_P23_COUNT == 23
    assert all(value.startswith("RESOLVED:") for value in registration.P1_P23_DISPOSITIONS.values())
    # The two items the review flagged must name their deferral, not imply enforcement.
    assert "deferred to implementation" in registration.P1_P23_DISPOSITIONS["P17"]
    assert "deferred to implementation" in registration.P1_P23_DISPOSITIONS["P12"]


def test_immutable_and_scientific_scope_negations_are_frozen() -> None:
    assert registration.NEW_DATA_COLLECTED is False
    assert registration.OLD_DATA_CHANGED is False
    assert registration.SCIENTIFIC_RUN_PERFORMED is False
    assert registration.PREDICTIVE_EDGE_ESTABLISHED is False
    assert registration.STAGE3_ISOLATION_PRESERVED is True
    assert registration.STAGE3_MUTATION_ALLOWED is False
    for prefix in (
        "data/trusted/",
        "data/trusted_clean/",
        "data/trusted_raw/",
        "data/provenance/",
        "experiments/",
        "scripts/data_collection/",
    ):
        assert prefix in registration.IMMUTABLE_WRITE_FORBIDDEN_PREFIXES
    assert registration.DRY_RUN_REQUIRED_BEFORE_ACQUISITION is True
    assert registration.DRY_RUN_EXPECTED_CONFIRMATORY_ROWS == 0
    assert registration.REGISTRATION_MAY_NOT_ACQUIRE is True
