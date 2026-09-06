"""Read-only Stage 3 R2 accounting-only adjudicator for frozen attempt-1.

INERT BY DEFAULT. Importing this module, or running it with no arguments,
performs no scientific computation, creates no result root, and writes no R2
artifact. Only the explicit ``--adjudicate`` path produces the two registered
R2 artifacts, and only after every frozen attempt-1 hash and the registered R2
contract verify.

R2 is retrospective and accounting-only. The explicit path reads the existing
frozen attempt-1 evidence, corrects exactly the one failed integrity-accounting
condition (``clean_comparator_byte_and_logical_identity``) using **DERIVED** --
never OBSERVED -- logical identity, carries the other sixteen frozen integrity
conditions unchanged, keeps every frozen per-defect status unchanged, and
reapplies the existing Stage 3 decision rule to the frozen statuses plus the R2
integrity result.

It never loads the dataset, reconstructs a DataFrame or ``_frame_fingerprint``,
reinjects a defect, re-evaluates a guard surface, fits a model, or recomputes an
IC. Expectation-match is excluded from the evidence chain. The design is frozen
in :mod:`stage3_r2_amendment` and ``docs/thesis/STAGE_3_R2_AMENDMENT.md``; this
module does not redesign it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from experiments.thesis import stage3_r2_amendment as amendment
from experiments.thesis import stage3_registration as reg

ROOT = Path(__file__).resolve().parents[2]

FROZEN_ATTEMPT1_ROOT = ROOT / amendment.STAGE3_RESULT_ROOT.rstrip("/")
R2_RESULT_ROOT = ROOT / amendment.R2_RESULT_ROOT.rstrip("/")
R2_ARTIFACT_FILENAMES = tuple(amendment.R2_RESULT_FILENAMES)
DATASET_PATH = ROOT / amendment.DATASET_PATH

REPORT_JSON_RELATIVE = "defect_injection_report.json"
ATTEMPT1_JSON_RELATIVE = "attempts/attempt-1.json"
MANIFEST_JSON_RELATIVE = "artifact_manifest.json"

DECISION_PASS = "PASS"
DECISION_FAIL = "FAIL"
DECISION_INCONCLUSIVE = reg.INCONCLUSIVE

A3_EVIDENCE_LABEL = amendment.A3_DERIVATION_LABEL  # "DERIVED"
CORRECTED_CONDITION = amendment.SOLE_FAILED_INTEGRITY_CONDITION
RETAINED_CONDITIONS = tuple(amendment.R2_RETAINED_FROZEN_INTEGRITY_CONDITIONS)  # 16
REGISTERED_DEFECT_IDS = tuple(amendment.R2_REGISTERED_DEFECT_IDS)
REGISTERED_DEFECT_COUNT = int(amendment.R2_REGISTERED_DEFECT_COUNT)


class R2AdjudicationError(RuntimeError):
    """Raised when a frozen pin or the registered R2 contract does not verify."""


# --------------------------------------------------------------------------- #
# Frozen-evidence readers (JSON only; never a dataset load)
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise R2AdjudicationError(f"frozen attempt-1 evidence missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise R2AdjudicationError(f"frozen attempt-1 evidence unreadable: {path}") from exc
    if not isinstance(payload, dict):
        raise R2AdjudicationError(f"frozen attempt-1 evidence is not an object: {path}")
    return payload


def load_frozen_evidence(source_root: Path | None = None) -> tuple[dict, dict, dict]:
    """Return (report, attempt-1 record, manifest). Read-only JSON access."""
    root = Path(source_root) if source_root is not None else FROZEN_ATTEMPT1_ROOT
    report = _read_json(root / REPORT_JSON_RELATIVE)
    attempt = _read_json(root / ATTEMPT1_JSON_RELATIVE)
    manifest = _read_json(root / MANIFEST_JSON_RELATIVE)
    return report, attempt, manifest


# --------------------------------------------------------------------------- #
# Hard verification of frozen pins and the registered R2 contract
# --------------------------------------------------------------------------- #
def verify_frozen_attempt1_hashes(hashes=None) -> dict[str, str]:
    """Hard-verify all five frozen attempt-1 SHA256 values; raise on any mismatch."""
    expected = amendment.FROZEN_ATTEMPT1_ARTIFACT_HASHES if hashes is None else hashes
    verified: dict[str, str] = {}
    for relative, want in expected.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise R2AdjudicationError(f"frozen attempt-1 artifact missing: {relative}")
        got = _sha256_file(path)
        if got != want:
            raise R2AdjudicationError(f"frozen attempt-1 artifact hash mismatch: {relative}")
        verified[relative] = got
    if len(verified) != int(amendment.FROZEN_ATTEMPT1_ARTIFACT_COUNT):
        raise R2AdjudicationError("frozen attempt-1 artifact count changed")
    return verified


def verify_registered_r2_contract(report: dict, attempt: dict, manifest: dict) -> dict[str, object]:
    """Hard-verify the registered R2 contract from frozen + registration evidence."""
    problems: list[str] = []

    module_path = ROOT / amendment.STAGE3_REGISTRATION_MODULE
    doc_path = ROOT / amendment.STAGE3_REGISTRATION_DOC
    if not module_path.is_file() or _sha256_file(module_path) != amendment.STAGE3_REGISTRATION_MODULE_SHA256:
        problems.append("stage3_registration.py hash mismatch")
    if not doc_path.is_file() or _sha256_file(doc_path) != amendment.STAGE3_REGISTRATION_DOC_SHA256:
        problems.append("STAGE_3_REGISTRATION.md hash mismatch")

    if not DATASET_PATH.is_file() or _sha256_file(DATASET_PATH) != amendment.DATASET_SHA256:
        problems.append("registered dataset SHA mismatch")

    for label, blob in (("report", report), ("attempt", attempt), ("manifest", manifest)):
        if blob.get("registered_configuration_sha256") != amendment.STAGE3_REGISTERED_CONFIGURATION_SHA256:
            problems.append(f"{label} registered_configuration_sha256 mismatch")

    if attempt.get("attempt_number") != amendment.STAGE3_ATTEMPT_NUMBER:
        problems.append("attempt_number changed")
    if attempt.get("attempt_type") != amendment.STAGE3_ATTEMPT_TYPE:
        problems.append("attempt_type changed")
    if attempt.get("status") != amendment.STAGE3_ATTEMPT_STATUS:
        problems.append("attempt status changed")
    if attempt.get("prior_incomplete_attempt") is not amendment.STAGE3_PRIOR_INCOMPLETE_ATTEMPT:
        problems.append("prior_incomplete_attempt changed")

    if manifest.get("completion_status") != "complete":
        problems.append("manifest completion_status is not complete")
    if manifest.get("completion_authority") != MANIFEST_JSON_RELATIVE:
        problems.append("manifest completion_authority changed")

    if report.get("decision") != amendment.ORIGINAL_DECISION:
        problems.append("frozen report decision is not INCONCLUSIVE")
    if manifest.get("decision") != amendment.ORIGINAL_DECISION:
        problems.append("frozen manifest decision is not INCONCLUSIVE")

    integrity = report.get("integrity")
    if not isinstance(integrity, dict):
        problems.append("frozen report has no integrity block")
        frozen_conditions: dict = {}
    else:
        frozen_conditions = integrity.get("conditions", {}) or {}
        if list(integrity.get("failures", [])) != [CORRECTED_CONDITION]:
            problems.append("frozen integrity failures are not exactly the known condition")
        if frozen_conditions.get(CORRECTED_CONDITION) is not False:
            problems.append("frozen known integrity condition is not False as recorded")
        if len(frozen_conditions) != len(reg.INTEGRITY_CONDITION_IDENTIFIERS):
            problems.append("frozen integrity condition count changed")

    if problems:
        raise R2AdjudicationError("; ".join(problems))
    return {
        "registration_module_sha256": amendment.STAGE3_REGISTRATION_MODULE_SHA256,
        "registration_doc_sha256": amendment.STAGE3_REGISTRATION_DOC_SHA256,
        "registered_configuration_sha256": amendment.STAGE3_REGISTERED_CONFIGURATION_SHA256,
        "dataset_path": amendment.DATASET_PATH,
        "dataset_sha256": amendment.DATASET_SHA256,
        "frozen_integrity_condition_count": len(frozen_conditions),
    }


# --------------------------------------------------------------------------- #
# R2 predicate A0-A3 (evaluated exactly as registered)
# --------------------------------------------------------------------------- #
def _defect_records(report: dict) -> list[dict]:
    records = report.get("defects", [])
    return [record for record in records if isinstance(record, dict)]


def evaluate_a0(defects: list[dict]) -> dict:
    ids = [record.get("defect_id") for record in defects]
    integral = [value for value in ids if isinstance(value, int)]
    passed = (
        len(defects) == REGISTERED_DEFECT_COUNT
        and len(integral) == REGISTERED_DEFECT_COUNT
        and len(set(integral)) == REGISTERED_DEFECT_COUNT
        and tuple(sorted(integral)) == tuple(sorted(REGISTERED_DEFECT_IDS))
    )
    return {"clause": "A0_CARDINALITY", "passed": bool(passed), "defect_ids": ids}


def evaluate_a1(report: dict, attempt: dict, manifest: dict) -> dict:
    defects = _defect_records(report)
    pin = amendment.DATASET_SHA256
    per_defect: list[dict] = []
    per_defect_ok = True
    for record in defects:
        before = record.get("source_sha256_before")
        after = record.get("source_sha256_after")
        matches = before == after == pin
        per_defect_ok = per_defect_ok and matches
        per_defect.append(
            {
                "defect_id": record.get("defect_id"),
                "source_sha256_before": before,
                "source_sha256_after": after,
                "matches_registered_pin": bool(matches),
            }
        )
    conditions = (report.get("integrity", {}) or {}).get("conditions", {}) or {}
    load_gates_ok = (
        manifest.get("completion_status") == "complete"
        and attempt.get("status") == "complete"
        and conditions.get("frozen_source_dataset_path_and_sha_match") is True
    )
    passed = per_defect_ok and load_gates_ok and len(defects) == REGISTERED_DEFECT_COUNT
    return {
        "clause": "A1_PINNED_CLEAN_SOURCE_RE_READ",
        "passed": bool(passed),
        "per_defect": per_defect,
        "load_time_source_integrity_gates_completed": bool(load_gates_ok),
    }


def evaluate_a2(defects: list[dict]) -> dict:
    per_defect: list[dict] = []
    all_empty = True
    for record in defects:
        signals = record.get("clean_comparator", {}).get("detection_signals")
        empty = signals == []
        all_empty = all_empty and empty
        per_defect.append(
            {
                "defect_id": record.get("defect_id"),
                "clean_detection_signals": signals,
                "is_empty_list": bool(empty),
            }
        )
    passed = all_empty and len(defects) == REGISTERED_DEFECT_COUNT
    return {"clause": "A2_ZERO_CLEAN_DETECTION_SIGNALS", "passed": bool(passed), "per_defect": per_defect}


def _a3_evidence(record: dict) -> dict:
    clean = record.get("clean_comparator", {}) if isinstance(record.get("clean_comparator"), dict) else {}
    mechanism = record.get("mechanism_invariants", {}) if isinstance(record.get("mechanism_invariants"), dict) else {}
    checks = mechanism.get("checks", {}) if isinstance(mechanism.get("checks"), dict) else {}
    return {
        "source_sha256_before": record.get("source_sha256_before"),
        "source_sha256_after": record.get("source_sha256_after"),
        "mechanism_invariants.passed": mechanism.get("passed"),
        "mechanism_invariants.checks.source_shape_clean": checks.get("source_shape_clean"),
        "clean_comparator.cleanup_proven": clean.get("cleanup_proven"),
        "clean_comparator.containment_passed": clean.get("containment_passed"),
        "clean_comparator.invocation_accounting_passed": clean.get("invocation_accounting_passed"),
    }


def evaluate_a3(defects: list[dict]) -> dict:
    pin = amendment.DATASET_SHA256
    per_defect: list[dict] = []
    all_derived = True
    for record in defects:
        evidence = _a3_evidence(record)
        derived = (
            evidence["source_sha256_before"] == pin
            and evidence["source_sha256_after"] == pin
            and evidence["mechanism_invariants.passed"] is True
            and evidence["mechanism_invariants.checks.source_shape_clean"] is True
            and evidence["clean_comparator.cleanup_proven"] is True
            and evidence["clean_comparator.containment_passed"] is True
            and evidence["clean_comparator.invocation_accounting_passed"] is True
        )
        all_derived = all_derived and derived
        per_defect.append(
            {
                "defect_id": record.get("defect_id"),
                "evidence": evidence,
                "derived_logical_identity": bool(derived),
            }
        )
    passed = all_derived and len(defects) == REGISTERED_DEFECT_COUNT
    return {
        "clause": "A3_DERIVED_CLEAN_LOGICAL_IDENTITY",
        "passed": bool(passed),
        "evidence_label": A3_EVIDENCE_LABEL,
        "is_derived_not_observed": True,
        "forbidden_observation_label": amendment.A3_FORBIDDEN_OBSERVATION_LABEL,
        "attempt1_fingerprint_values_persisted": bool(amendment.ATTEMPT1_FINGERPRINT_VALUES_PERSISTED),
        "per_defect": per_defect,
    }


def _readjudicated_decision(statuses: list[object], *, integrity_passed: bool) -> str:
    """Reapply the existing Stage 3 decision rule; never hardcode FAIL."""
    if not integrity_passed:
        return DECISION_INCONCLUSIVE
    if any(status == reg.INCONCLUSIVE for status in statuses):
        return DECISION_INCONCLUSIVE
    if len(statuses) != reg.DEFECT_FAMILY_SIZE:
        return DECISION_INCONCLUSIVE
    if all(status == reg.DETECTED for status in statuses):
        return DECISION_PASS
    return DECISION_FAIL


def evaluate_r2_predicate(report: dict, attempt: dict, manifest: dict) -> dict:
    """Evaluate A0-A3, carry the sixteen frozen conditions, and reapply the rule."""
    defects = _defect_records(report)
    a0 = evaluate_a0(defects)
    a1 = evaluate_a1(report, attempt, manifest)
    a2 = evaluate_a2(defects)
    a3 = evaluate_a3(defects)
    clauses = [a0, a1, a2, a3]
    predicate_passed = all(clause["passed"] for clause in clauses)

    frozen_conditions = (report.get("integrity", {}) or {}).get("conditions", {}) or {}
    carried: dict[str, object] = {}
    carried_ok = True
    for name in RETAINED_CONDITIONS:
        value = frozen_conditions.get(name)
        carried[name] = value
        carried_ok = carried_ok and value is True
    carried_count_ok = len(RETAINED_CONDITIONS) == int(
        amendment.R2_RETAINED_FROZEN_INTEGRITY_CONDITION_COUNT
    )

    corrected_value = bool(predicate_passed)
    r2_integrity_passed = bool(predicate_passed and carried_ok and carried_count_ok)

    statuses = [record.get("status") for record in defects]
    detected_by = {str(record.get("defect_id")): record.get("detected_by") for record in defects}
    readjudicated = _readjudicated_decision(statuses, integrity_passed=r2_integrity_passed)

    return {
        "predicate_clauses": clauses,
        "predicate_passed": bool(predicate_passed),
        "a3_evidence_label": A3_EVIDENCE_LABEL,
        "expectation_match_consumed": False,
        "expectation_match_excluded_from_evidence_chain": True,
        "carried_frozen_integrity_conditions": carried,
        "carried_frozen_integrity_conditions_all_true": bool(carried_ok),
        "carried_frozen_integrity_condition_count": len(RETAINED_CONDITIONS),
        "carried_frozen_integrity_conditions_recomputed": False,
        "corrected_condition": CORRECTED_CONDITION,
        "corrected_condition_value": corrected_value,
        "corrected_condition_evidence": A3_EVIDENCE_LABEL,
        "frozen_per_defect_statuses": {
            str(record.get("defect_id")): record.get("status") for record in defects
        },
        "frozen_per_defect_statuses_recomputed": False,
        "frozen_per_defect_detected_by": detected_by,
        "frozen_per_defect_detected_by_recomputed": False,
        "r2_integrity_passed": r2_integrity_passed,
        "readjudicated_decision": readjudicated,
        "readjudicated_decision_value_preregistered": False,
        "original_decision": amendment.ORIGINAL_DECISION,
        "original_decision_is_permanent": True,
    }


# --------------------------------------------------------------------------- #
# Prospective R2 record + human companion (written only on --adjudicate)
# --------------------------------------------------------------------------- #
def build_r2_record(*, frozen_hashes: dict, contract: dict, predicate: dict) -> dict:
    return {
        "schema_version": "1.0.0",
        "amendment_id": amendment.AMENDMENT_ID,
        "amendment_date": amendment.AMENDMENT_DATE,
        "stage": "Stage 3 R2 - accounting-only retrospective re-adjudication",
        "r2_option": amendment.R2_OPTION,
        "scope": amendment.R2_SCOPE,
        "generated_at_utc": _utc_now(),
        "source_root": amendment.STAGE3_RESULT_ROOT.rstrip("/"),
        "result_root": amendment.R2_RESULT_ROOT.rstrip("/"),
        "frozen_attempt1_artifact_sha256": dict(frozen_hashes),
        "registered_contract_verification": dict(contract),
        "original_decision": amendment.ORIGINAL_DECISION,
        "original_decision_is_permanent": True,
        "sole_failed_integrity_condition": CORRECTED_CONDITION,
        "r2_predicate": predicate,
        "a3_evidence_label": A3_EVIDENCE_LABEL,
        "a3_is_derived_not_observed": True,
        "expectation_match_consumed": False,
        "attempt1_fingerprint_values_persisted": bool(amendment.ATTEMPT1_FINGERPRINT_VALUES_PERSISTED),
        "readjudicated_decision": predicate["readjudicated_decision"],
        "readjudicated_decision_value_preregistered": False,
        "second_stage3_draw_authorized": False,
        "repeat_after_crash_authorized": False,
        "stage7_unlocked": False,
        "scientific_recomputation_performed": False,
        "claim_boundary": list(amendment.CLAIM_BOUNDARY),
    }


def render_r2_markdown(record: dict) -> str:
    predicate = record["r2_predicate"]
    lines = [
        "# Stage 3 R2 accounting-only adjudication",
        "",
        f"- Amendment: `{record['amendment_id']}`",
        f"- Original authoritative decision: **{record['original_decision']}** (permanent)",
        f"- Readjudicated decision: **{predicate['readjudicated_decision']}** "
        "(computed from the frozen per-defect statuses and the R2 integrity result; "
        "not preregistered)",
        f"- Corrected integrity condition: `{record['sole_failed_integrity_condition']}` "
        f"= {predicate['corrected_condition_value']} via **{record['a3_evidence_label']}** evidence",
        "- A3 clean logical identity is **DERIVED**, never "
        f"`{amendment.A3_FORBIDDEN_OBSERVATION_LABEL}`; attempt-1 did not persist "
        "fingerprint values.",
        "- Expectation-match is excluded from the evidence chain.",
        "- The other sixteen frozen integrity conditions are carried unchanged and are "
        "not recomputed. No per-defect status or `detected_by` value is recomputed.",
        "",
        "## R2 predicate",
        "",
        "| Clause | Passed |",
        "|---|---|",
    ]
    for clause in predicate["predicate_clauses"]:
        lines.append(f"| {clause['clause']} | {clause['passed']} |")
    lines.extend(
        [
            "",
            "## Frozen per-defect statuses (unchanged)",
            "",
            "| Defect | Status |",
            "|---:|---|",
        ]
    )
    for defect_id, status in predicate["frozen_per_defect_statuses"].items():
        lines.append(f"| {defect_id} | {status} |")
    lines.extend(
        [
            "",
            "## Scientific boundary",
            "",
            "No dataset load, defect injection, guard evaluation, model fit, IC "
            "computation, second governed Stage 3 draw, or `--repeat-after-crash` "
            "execution occurred. Stage 7 remains **BLOCKED**. Research support only; "
            "not investment advice.",
        ]
    )
    return "\n".join(lines) + "\n"


def _write_r2_artifacts(destination: Path, record: dict, markdown: str) -> list[Path]:
    destination = Path(destination)
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise R2AdjudicationError("R2 result root is not a safe directory")
    destination.mkdir(parents=True, exist_ok=True)
    json_path = destination / R2_ARTIFACT_FILENAMES[0]
    md_path = destination / R2_ARTIFACT_FILENAMES[1]
    json_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(markdown, encoding="utf-8")
    files = sorted(path.name for path in destination.iterdir() if path.is_file())
    subdirs = [path.name for path in destination.iterdir() if path.is_dir()]
    if files != sorted(R2_ARTIFACT_FILENAMES) or subdirs:
        raise R2AdjudicationError(
            "R2 result surface is not exactly the two registered files"
        )
    return [json_path, md_path]


# --------------------------------------------------------------------------- #
# Orchestration + inert entry point
# --------------------------------------------------------------------------- #
def adjudicate(*, destination: Path | None = None, write: bool = True) -> dict:
    """The explicit read-only R2 adjudication path. Never called on import/bare CLI."""
    frozen_hashes = verify_frozen_attempt1_hashes()
    report, attempt, manifest = load_frozen_evidence()
    contract = verify_registered_r2_contract(report, attempt, manifest)
    predicate = evaluate_r2_predicate(report, attempt, manifest)
    record = build_r2_record(frozen_hashes=frozen_hashes, contract=contract, predicate=predicate)
    markdown = render_r2_markdown(record)
    written: list[str] = []
    if write:
        target = Path(destination) if destination is not None else R2_RESULT_ROOT
        written = [
            str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
            for path in _write_r2_artifacts(target, record, markdown)
        ]
    return {"record": record, "markdown": markdown, "written": written}


def plan() -> dict:
    """Describe the inert state without verifying hashes or writing anything."""
    return {
        "executed": False,
        "amendment_id": amendment.AMENDMENT_ID,
        "adjudicated": False,
        "inert_by_default": True,
        "explicit_adjudication_flag": "--adjudicate",
        "result_root": amendment.R2_RESULT_ROOT.rstrip("/"),
        "result_root_exists": R2_RESULT_ROOT.exists(),
        "registered_artifacts": list(R2_ARTIFACT_FILENAMES),
        "original_decision": amendment.ORIGINAL_DECISION,
        "readjudicated_decision_produced": False,
        "second_stage3_draw_authorized": False,
        "repeat_after_crash_authorized": False,
        "stage7_unlocked": False,
        "scientific_computation_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 3 R2 accounting-only adjudicator (inert by default)."
    )
    parser.add_argument(
        "--adjudicate",
        action="store_true",
        help="run the explicit read-only R2 adjudication and write the two registered artifacts",
    )
    args = parser.parse_args(argv)
    if args.adjudicate:
        result = adjudicate()
        print(
            json.dumps(
                {
                    "written": result["written"],
                    "original_decision": result["record"]["original_decision"],
                    "readjudicated_decision": result["record"]["readjudicated_decision"],
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    print(json.dumps(plan(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
