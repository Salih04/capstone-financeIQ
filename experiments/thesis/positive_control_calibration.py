"""Stage 1b — prospective calibration / diagnostic runner for the positive control.

Registered in ``docs/thesis/STAGE_1B_REGISTRATION.md`` and in the 2026-08-29
Stage 1b amendment of ``docs/thesis/PRE_EXPERIMENT_PROTOCOL.md``. Every scientific
constant below is read from ``experiments/thesis/stage1b_registration.py``; none
is defined here and none may be tuned after looking at a result.

What this is
------------
Stage 1 (``positive_control.py``) is historical and frozen: it asked a
pass/fail question and answered **FAILED AS WRITTEN — INFORMATIVE**. Stage 1b
asks a *descriptive* question with the same apparatus, on the same fixed
realized ``equity`` panel: for each nominal ``theta`` on the registered grid,
what does the chain

    nominal theta
      -> realized raw equity carrier IC
      -> ridge prediction IC and final evaluation IC
      -> Stage-1-operational-rule detection probability

actually look like? The primary result is vector-valued and descriptive. Stage 1b
has **no scientific performance PASS/FAIL gate**: a flat, non-monotone, weak,
surprising, or high-background curve is a scientific result, not an integrity
failure. Only the closed, deterministic integrity contract in the registration
can invalidate the run.

What is deliberately NOT computed here
--------------------------------------
Stage 1's ``confirmatory_gate``, ``gate_informativeness``, strict-monotonicity
pass/fail, the ``GATE_LEVELS`` rejection criterion, an 80%-detection gate, and
any interpolated threshold crossing. Those are historical Stage 1 quantities.
The ``current_ratio`` missingness arm and the theta=0.90 sanity arm are Stage 1
diagnostics and are not Stage 1b arms.

The frozen operating divisor
----------------------------
The primary detection rule is the unchanged historical Stage 1 operating point
``min(1, 5 * p_raw) < 0.05``. The literal ``5`` comes from
``stage1b_registration.STAGE1_OPERATIONAL_DIVISOR`` and is **never** derived from
``len(IC_GRID)``, from ``positive_control.CONFIRMATORY_FAMILY_SIZE``, or from the
number of Stage 1b levels. Stage 1b's six levels are not a hypothesis family and
no family-wise-error-control claim is made across them.

Seed identity
-------------
Seed level indices come from ``stage1b_registration.level_index_for`` — the
frozen theta-to-index map — never from ``enumerate`` over the grid. Report order
stays numeric (0.00 … 0.40); seed identity keeps ``0.40 -> 4`` and ``0.35 -> 5``
so no legacy Stage 1 stream is renumbered.

Run:
    make thesis-stage1b            # the one governed prospective run
    make thesis-stage1b-replay     # determinism probe; writes nothing
Outputs: experiments/results_thesis/positive_control_calibration/

Importing this module runs nothing, reads no dataset, writes no file, and does
not create the result root.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import platform
import shutil
import sys
import tempfile
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import run_experiments as rx  # noqa: E402
from experiments import significance as sig  # noqa: E402
from experiments.placebo_lab import validate_claim_safety_text  # noqa: E402
from experiments.thesis import positive_control as stage1  # noqa: E402
from experiments.thesis import provenance as prov  # noqa: E402
from experiments.thesis import stage1b_registration as reg  # noqa: E402

# --------------------------------------------------------------------------- #
# Registered constants. Every one of these is re-exported from
# experiments/thesis/stage1b_registration.py, which is itself machine-checked
# against docs/thesis/STAGE_1B_REGISTRATION.md. Nothing scientific is defined
# in this module.
# --------------------------------------------------------------------------- #
SLUG = reg.STAGE_1B_SLUG
STAGE_1_SLUG = reg.STAGE_1_SLUG

#: Declared result root. Held as a plain Path: constructing it creates nothing.
RESULT_ROOT = prov.THESIS_RESULTS_ROOT / SLUG
STAGE_1_RESULT_ROOT = prov.THESIS_RESULTS_ROOT / STAGE_1_SLUG

IC_GRID: tuple[float, ...] = reg.IC_GRID
CARRIER = reg.CARRIER
PRIMARY_MODEL = reg.PRIMARY_MODEL
REPETITIONS = reg.REPETITIONS
REPETITION_IDS: tuple[int, ...] = reg.stage1b_repetition_ids()
BASE_SEED = reg.BASE_SEED
PERMUTATIONS = reg.PERMUTATIONS
BOOTSTRAPS = reg.BOOTSTRAPS
ALPHA = reg.ALPHA

#: FROZEN historical Stage 1 operating divisor, taken as a literal from the
#: registration. Never recomputed from any Stage 1b grid length or family size.
STAGE1_OPERATIONAL_DIVISOR = reg.STAGE1_OPERATIONAL_DIVISOR

#: "The already governed Stage 1 numerical tolerance": Stage 1 emits every IC
#: rounded to ``positive_control.ROUND_DIGITS`` decimal places, and the governed
#: Stage 1 report's identity checkpoints agree exactly at that granularity. The
#: tolerance is therefore that same emission granularity, derived rather than
#: chosen here.
ROUND_DIGITS = stage1.ROUND_DIGITS
IDENTITY_TOLERANCE = 10.0 ** -ROUND_DIGITS

#: Checkpoints Stage 1 itself declares to be identity/invariant. Reused from the
#: Stage 1 role table so Stage 1b invents no new checkpoint semantics.
IDENTITY_CHECKPOINTS: tuple[str, ...] = tuple(
    name for name, role in stage1.CHECKPOINT_ROLES.items() if role == "identity_invariant"
)

#: data/trusted*, data/trusted_clean*, data/provenance* — the registration's
#: protected data trees. None of them may change across the run.
PROTECTED_DATA_ROOTS: tuple[str, ...] = (
    "data/trusted",
    "data/trusted_clean",
    "data/trusted_raw",
    "data/provenance",
)

OUTPUT_FILENAMES = {
    "report_json": "positive_control_calibration_report.json",
    "report_md": "positive_control_calibration_report.md",
    "repetitions": "repetitions.csv",
    "calibration_curve": "calibration_curve.csv",
}
MANIFEST_FILENAME = "artifact_manifest.json"
ATTEMPT_MARKER_FILENAME = "attempt_provenance.json"
STAGING_DIRNAME = ".staging"

#: The only operating-system metadata filename Stage 1b will tolerate or delete
#: inside its own isolated result namespace. Deliberately a one-element frozen
#: set: ``.DS_Store`` is not a scientific output, not operational provenance,
#: needs no registry contract, and this must never be broadened into a general
#: hidden-file or platform-junk allowlist. Any other unexpected file — hidden or
#: not — and any unexpected directory still fail confinement closed.
IGNORABLE_OS_METADATA: frozenset[str] = frozenset({".DS_Store"})

#: Scientific files are staged and promoted together. The manifest is governance
#: completion evidence, not a scientific measurement; the attempt marker is
#: operational governance/provenance and is deliberately outside this set.
SCIENTIFIC_EMITTED_FILENAMES: tuple[str, ...] = tuple(sorted(OUTPUT_FILENAMES.values()))
#: The complete, frozen set of governed scientific/evidence files emitted by the
#: one registered run. artifact_registry.json carries one prospective ownership
#: entry per name, plus a separate operational marker contract.
EMITTED_FILENAMES: tuple[str, ...] = tuple(
    sorted([*SCIENTIFIC_EMITTED_FILENAMES, MANIFEST_FILENAME])
)
OPERATIONAL_FILENAMES: tuple[str, ...] = (ATTEMPT_MARKER_FILENAME,)

#: The one already-registered cell re-executed inside the run as a deterministic
#: replay probe. It is a duplicate of a cell the run already contains, so it
#: introduces no new setting, no new seed, and no new scientific quantity.
REPLAY_PROBE_THETA = IC_GRID[0]
REPLAY_PROBE_REPETITION = REPETITION_IDS[0]

PANEL_ID_COLUMNS = stage1.PANEL_ID_COLUMNS
TARGET_COLUMN = stage1.TARGET_COLUMN
YEAR_COLUMN = stage1.YEAR_COLUMN

CLAIM_SAFETY_SENTENCE = (
    "Stage 1b characterizes how the frozen measurement pipeline responds to a synthetic "
    "relationship of known nominal strength injected into one raw column. It is apparatus "
    "characterization on manufactured input, not evidence about BIST equities: a recovered "
    "quantity here measures the instrument, and the repository's committed walk-forward null "
    "is untouched by anything reported here."
)


class Stage1bError(RuntimeError):
    """Raised when the stage would violate its own prospective registration."""


class Stage1bIntegrityError(Stage1bError):
    """Raised when a condition on the registration's closed integrity list fails."""


# These fail-closed checks protect execution/provenance and output integrity;
# they are implementation invariants, not additional scientific gates.
EXECUTION_PRECONDITIONS: tuple[str, ...] = (
    "registered carrier assertion",
    "registered seed/provenance equality",
    "malformed or empty level result rejection",
    "injected-table hash internal consistency",
    "filesystem-backed staged-output confinement",
    "outside-namespace workspace write confinement",
)


# --------------------------------------------------------------------------- #
# Small helpers — all delegate to the Stage 1 primitives where one exists
# --------------------------------------------------------------------------- #
def _rounded(value: float | None, digits: int = ROUND_DIGITS) -> float | None:
    return stage1._rounded(value, digits)


def _sha256_path(path: Path) -> str:
    return prov.sha256_path(path)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def implementation_hash() -> str:
    """SHA256 of this runner's own source, recorded with the result."""
    return _sha256_path(Path(__file__).resolve())


def registration_hash() -> str:
    """SHA256 of the registered constants module the run was governed by."""
    return _sha256_path(ROOT / "experiments" / "thesis" / "stage1b_registration.py")


def _git_metadata() -> dict:
    return stage1._git_metadata()


def _summarize(values: Sequence[float | None]) -> dict[str, float | None]:
    """Registered descriptive summary: mean, SD, median, p05, p95.

    Numerics come from the Stage 1 summarizer unchanged; only the median key is
    renamed from Stage 1's ``p50`` to the name the registration uses.
    """
    base = stage1._summarize(list(values))
    return {
        "n": base["n"],
        "mean": base["mean"],
        "sd": base["sd"],
        "median": base["p50"],
        "p05": base["p05"],
        "p95": base["p95"],
    }


def tree_digest(root: Path) -> dict[str, str]:
    """``{repo-relative path: sha256}`` for every file under ``root``.

    A missing root yields an empty map, so "absent before and after" compares
    equal without special-casing.
    """
    if not root.is_dir():
        return {}
    return {
        path.relative_to(ROOT).as_posix(): _sha256_path(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def workspace_digest_excluding_stage1b() -> dict[str, str]:
    """Digest persistent repository files outside the isolated Stage 1b root."""
    stage_root = _result_root().resolve()
    digest: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            path.resolve().relative_to(stage_root)
        except ValueError:
            digest[path.relative_to(ROOT).as_posix()] = _sha256_path(path)
    return digest


def protected_data_digest() -> dict[str, str]:
    """Digest of every protected data tree named by the registration."""
    digest: dict[str, str] = {}
    for relative in PROTECTED_DATA_ROOTS:
        digest.update(tree_digest(ROOT / relative))
    return digest


# --------------------------------------------------------------------------- #
# Attempt lifecycle and filesystem transaction helpers
# --------------------------------------------------------------------------- #
def _result_root() -> Path:
    """Return the declared Stage 1b root without creating it."""
    return RESULT_ROOT


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _seed_schedule() -> list[dict[str, int | float]]:
    """The exact registered seed schedule, independent of report order."""
    return [
        {
            "theta": _rounded(theta),
            "repetition": int(repetition),
            "injection_seed": int(injection_seed_for(theta, repetition)),
            "permutation_seed": int(permutation_seed_for(repetition)),
        }
        for theta in IC_GRID
        for repetition in REPETITION_IDS
    ]


def registered_configuration() -> dict:
    """Return the complete non-tunable Stage 1b configuration identity."""
    schedule = _seed_schedule()
    return {
        "carrier": CARRIER,
        "model": PRIMARY_MODEL,
        "ic_grid": [_rounded(theta) for theta in IC_GRID],
        "level_index_map": {str(theta): int(index) for theta, index in reg.LEVEL_INDEX.items()},
        "repetition_ids": [int(repetition) for repetition in REPETITION_IDS],
        "repetitions_per_level": REPETITIONS,
        "base_seed": BASE_SEED,
        "injection_seed_formula": reg.INJECTION_SEED_FORMULA,
        "permutation_seed_formula": reg.PERMUTATION_SEED_FORMULA,
        "seed_schedule_sha256": _sha256_bytes(_canonical_json(schedule)),
        "alpha": ALPHA,
        "permutations": PERMUTATIONS,
        "bootstraps": BOOTSTRAPS,
        "stage1_operational_divisor": STAGE1_OPERATIONAL_DIVISOR,
        "primary_detection_rule": reg.PRIMARY_DETECTION_RULE,
        "secondary_detection_rule": reg.SECONDARY_DIAGNOSTIC_RULE,
    }


def registered_configuration_digest() -> str:
    return _sha256_bytes(_canonical_json(registered_configuration()))


def _marker_path(root: Path) -> Path:
    return root / ATTEMPT_MARKER_FILENAME


def _atomic_json_write(path: Path, payload: dict) -> None:
    """Atomically persist governance metadata, leaving no partial marker."""
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def _new_attempt_marker(attempt_number: int, attempt_type: str, prior_incomplete: bool) -> dict:
    configuration = registered_configuration()
    digest = registered_configuration_digest()
    return {
        "schema_version": 1,
        "governance_class": "operational_attempt_provenance",
        "experiment": SLUG,
        "completion_authority": MANIFEST_FILENAME,
        "registered_configuration_sha256": digest,
        "registered_configuration": configuration,
        "attempts": [
            {
                "attempt_number": attempt_number,
                "attempt_type": attempt_type,
                "registered_configuration_sha256": digest,
                "seed_schedule_sha256": configuration["seed_schedule_sha256"],
                "prior_attempt_incomplete": prior_incomplete,
                "completion_status": "in_progress",
                "started_at_utc": _utc_now(),
            }
        ],
    }


def _load_attempt_marker(root: Path) -> dict:
    marker = _marker_path(root)
    if not marker.is_file() or marker.is_symlink():
        raise Stage1bError(
            "an incomplete Stage 1b root has no durable attempt marker; refusing to "
            "guess its provenance"
        )
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage1bError("the Stage 1b attempt marker is unreadable; refusing recovery") from exc
    expected = registered_configuration()
    if payload.get("governance_class") != "operational_attempt_provenance":
        raise Stage1bError("the Stage 1b marker is not classified as operational provenance")
    if payload.get("experiment") != SLUG:
        raise Stage1bError("the Stage 1b marker belongs to a different experiment")
    if payload.get("registered_configuration") != expected or payload.get(
        "registered_configuration_sha256"
    ) != registered_configuration_digest():
        raise Stage1bError(
            "registered Stage 1b configuration or seed schedule changed; crash recovery is refused"
        )
    attempts = payload.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise Stage1bError("the Stage 1b marker contains no attempt records")
    numbers = [attempt.get("attempt_number") for attempt in attempts if isinstance(attempt, dict)]
    if len(numbers) != len(attempts) or len(set(numbers)) != len(numbers):
        raise Stage1bError("the Stage 1b marker has invalid attempt numbering")
    if any(attempt.get("attempt_type") not in {"initial", "crash_recovery"} for attempt in attempts):
        raise Stage1bError("the Stage 1b marker has an invalid attempt type")
    return payload


def _purge_os_metadata(surface: Path) -> None:
    """Delete only ``.DS_Store`` files anywhere under one Stage 1b directory.

    macOS Finder drops ``.DS_Store`` into any directory it displays, including
    the isolated Stage 1b namespace during a run. It carries no science and no
    provenance, so a stray one must not permanently block ``--repeat-after-crash``
    or the final output-surface audit. This helper is deliberately narrow: it
    never touches anything outside ``surface``, never removes a directory, and
    never removes any name outside ``IGNORABLE_OS_METADATA``.
    """
    if not surface.is_dir() or surface.is_symlink():
        return
    for path in sorted(surface.rglob("*")):
        if (
            path.name in IGNORABLE_OS_METADATA
            and path.is_file()
            and not path.is_symlink()
        ):
            path.unlink()


def _audit_output_surface(
    surface: Path,
    *,
    expected_names: tuple[str, ...],
    operational_names: tuple[str, ...] = (),
) -> dict:
    """Inspect actual files recursively on a staging or final output surface.

    This is an implementation invariant: only direct, expected files are valid;
    nested files/directories and symlink escapes are reported as unexpected.
    """
    expected = set(expected_names)
    operational = set(operational_names)
    if not surface.is_dir() or surface.is_symlink():
        return {
            "surface": str(surface),
            "actual_files": [],
            "actual_direct_files": [],
            "actual_scientific_files": [],
            "unexpected_files": ["<surface is not a directory>"],
            "unexpected_directories": [],
            "missing_scientific_files": sorted(expected),
            "symlink_escapes": [],
            "passed": False,
        }

    actual_files: list[str] = []
    unexpected_files: list[str] = []
    symlink_escapes: list[str] = []
    for path in sorted(surface.rglob("*")):
        if not path.is_file():
            continue
        if path.name in IGNORABLE_OS_METADATA and not path.is_symlink():
            continue
        relative = path.relative_to(surface).as_posix()
        actual_files.append(relative)
        try:
            path.resolve().relative_to(surface.resolve())
        except ValueError:
            symlink_escapes.append(relative)
        if path.parent != surface or path.name not in expected | operational:
            unexpected_files.append(relative)

    unexpected_directories = [
        path.relative_to(surface).as_posix()
        for path in sorted(surface.rglob("*"))
        if path.is_dir()
    ]
    direct_names = {
        path.name
        for path in surface.iterdir()
        if path.is_file() and not (path.name in IGNORABLE_OS_METADATA and not path.is_symlink())
    }
    actual_scientific = sorted(direct_names & expected)
    missing = sorted(expected - set(actual_scientific))
    return {
        "surface": str(surface),
        "actual_files": actual_files,
        "actual_direct_files": sorted(direct_names),
        "actual_scientific_files": actual_scientific,
        "unexpected_files": sorted(unexpected_files),
        "unexpected_directories": unexpected_directories,
        "missing_scientific_files": missing,
        "symlink_escapes": sorted(symlink_escapes),
        "passed": not unexpected_files and not unexpected_directories and not symlink_escapes and not missing,
    }


def _relative_to_repo(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def _is_complete_run(root: Path) -> bool:
    """Completion is final-manifest evidence plus an exact final filesystem."""
    manifest = root / MANIFEST_FILENAME
    marker = _marker_path(root)
    if not manifest.is_file() or marker.is_symlink() or not marker.is_file():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    evidence = payload.get("operational_attempt_provenance", {})
    if not isinstance(evidence, dict):
        return False
    attempts = marker_payload.get("attempts")
    if not isinstance(attempts, list) or not attempts or not isinstance(attempts[-1], dict):
        return False
    marker_relative = (
        _relative_to_repo(marker)
        if marker.is_absolute() and marker.is_relative_to(ROOT)
        else marker.resolve().as_posix()
    )
    audit = _audit_output_surface(
        root,
        expected_names=EMITTED_FILENAMES,
        operational_names=OPERATIONAL_FILENAMES,
    )
    return bool(
        payload.get("experiment") == SLUG
        and payload.get("completion_status") == "complete"
        and payload.get("completion_authority") == MANIFEST_FILENAME
        and payload.get("integrity_passed") is True
        and evidence.get("path") == marker_relative
        and evidence.get("sha256") == _sha256_path(marker)
        and attempts[-1].get("completion_status") == "complete"
        and audit["passed"]
        and set(audit["actual_direct_files"]) == set(EMITTED_FILENAMES) | set(OPERATIONAL_FILENAMES)
    )


def _cleanup_incomplete_root(root: Path) -> None:
    """Remove only known Stage 1b files from an incomplete attempt."""
    allowed_files = set(SCIENTIFIC_EMITTED_FILENAMES) | {MANIFEST_FILENAME}
    marker_temp = f".{ATTEMPT_MARKER_FILENAME}.tmp"
    _purge_os_metadata(root)
    for child in sorted(root.iterdir()):
        if child.name == ATTEMPT_MARKER_FILENAME:
            continue
        if child.name in IGNORABLE_OS_METADATA and child.is_file() and not child.is_symlink():
            child.unlink()
            continue
        if child.name == marker_temp:
            if child.is_file() and not child.is_symlink():
                child.unlink()
            else:
                raise Stage1bError("refusing to remove an unexpected Stage 1b marker temporary")
            continue
        if child.name == STAGING_DIRNAME:
            if child.is_symlink() or not child.is_dir():
                raise Stage1bError("refusing to remove an unsafe Stage 1b staging path")
            shutil.rmtree(child)
            continue
        if child.name in allowed_files:
            if child.is_symlink() or not child.is_file():
                raise Stage1bError(f"refusing to remove an unsafe Stage 1b file: {child.name}")
            child.unlink()
            continue
        raise Stage1bError(
            f"incomplete Stage 1b root contains an unrecognized path {child.name!r}; refusing cleanup"
        )


def _prepare_attempt(*, repeat_after_crash: bool) -> tuple[Path, Path, dict, int]:
    """Create/recover the isolated marker before reading or running science."""
    root = _result_root()
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise Stage1bError("Stage 1b result root is not a safe directory")

    if not repeat_after_crash:
        if root.exists() and any(root.iterdir()):
            if _is_complete_run(root):
                raise Stage1bError(
                    "a complete Stage 1b run already exists; --run refuses overwrite"
                )
            raise Stage1bError(
                "a pre-existing non-empty Stage 1b result root exists; use "
                "--repeat-after-crash only for an incomplete attempt"
            )
        root.mkdir(parents=True, exist_ok=True)
        marker_payload = _new_attempt_marker(1, "initial", False)
        _atomic_json_write(_marker_path(root), marker_payload)
        return root, _marker_path(root), marker_payload, 1

    if not root.is_dir() or not any(root.iterdir()):
        raise Stage1bError(
            "--repeat-after-crash requires an existing non-empty incomplete Stage 1b attempt"
        )
    if _is_complete_run(root):
        raise Stage1bError("--repeat-after-crash refuses a complete Stage 1b run")
    marker_payload = _load_attempt_marker(root)
    _cleanup_incomplete_root(root)
    prior_attempts = marker_payload["attempts"]
    for attempt in prior_attempts:
        attempt["completion_status"] = "incomplete"
    attempt_number = max(int(attempt["attempt_number"]) for attempt in prior_attempts) + 1
    configuration = registered_configuration()
    marker_payload["attempts"].append(
        {
            "attempt_number": attempt_number,
            "attempt_type": "crash_recovery",
            "registered_configuration_sha256": registered_configuration_digest(),
            "seed_schedule_sha256": configuration["seed_schedule_sha256"],
            "prior_attempt_incomplete": True,
            "completion_status": "in_progress",
            "started_at_utc": _utc_now(),
        }
    )
    _atomic_json_write(_marker_path(root), marker_payload)
    return root, _marker_path(root), marker_payload, attempt_number


def _set_attempt_status(marker_path: Path, marker_payload: dict, attempt_number: int, status: str) -> dict:
    updated = json.loads(json.dumps(marker_payload))
    for attempt in updated["attempts"]:
        if int(attempt["attempt_number"]) == attempt_number:
            attempt["completion_status"] = status
            break
    else:
        raise Stage1bError(f"attempt {attempt_number} is absent from the Stage 1b marker")
    _atomic_json_write(marker_path, updated)
    return updated


def _write_scientific_artifacts(
    staging: Path,
    *,
    report: dict,
    markdown: str,
    records: list[dict],
    curve: list[dict],
) -> None:
    """Write only scientific files into a private staging directory."""
    staging.mkdir(parents=True, exist_ok=False)
    (staging / OUTPUT_FILENAMES["report_json"]).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (staging / OUTPUT_FILENAMES["report_md"]).write_text(markdown, encoding="utf-8")
    pd.DataFrame([_flatten_record(record) for record in records]).to_csv(
        staging / OUTPUT_FILENAMES["repetitions"], index=False, float_format="%.17g"
    )
    pd.DataFrame(
        [
            {
                "ic_injected": summary["ic_injected"],
                "level_index": summary["level_index"],
                "carrier": summary["carrier"],
                "model": summary["model"],
                "repetitions": summary["repetitions"],
                "repetition_id_first": summary["repetition_id_range"][0],
                "repetition_id_last": summary["repetition_id_range"][1],
                "mean_realized_raw_carrier_ic": summary["realized_raw_carrier_ic"]["mean"],
                "sd_realized_raw_carrier_ic": summary["realized_raw_carrier_ic"]["sd"],
                "median_realized_raw_carrier_ic": summary["realized_raw_carrier_ic"]["median"],
                "p05_realized_raw_carrier_ic": summary["realized_raw_carrier_ic"]["p05"],
                "p95_realized_raw_carrier_ic": summary["realized_raw_carrier_ic"]["p95"],
                "mean_final_evaluated_ic": summary["final_evaluated_ic"]["mean"],
                "sd_final_evaluated_ic": summary["final_evaluated_ic"]["sd"],
                "median_final_evaluated_ic": summary["final_evaluated_ic"]["median"],
                "p05_final_evaluated_ic": summary["final_evaluated_ic"]["p05"],
                "p95_final_evaluated_ic": summary["final_evaluated_ic"]["p95"],
                "primary_detections": summary["primary_detection"]["detections"],
                "primary_detection_rate": summary["primary_detection"]["rate"],
                "primary_wilson_95_pointwise_low": summary["primary_detection"][
                    "wilson_95_pointwise"
                ][0],
                "primary_wilson_95_pointwise_high": summary["primary_detection"][
                    "wilson_95_pointwise"
                ][1],
                "secondary_detections": summary["secondary_detection"]["detections"],
                "secondary_detection_rate": summary["secondary_detection"]["rate"],
                "secondary_wilson_95_pointwise_low": summary["secondary_detection"][
                    "wilson_95_pointwise"
                ][0],
                "secondary_wilson_95_pointwise_high": summary["secondary_detection"][
                    "wilson_95_pointwise"
                ][1],
                "secondary_is_gating": summary["secondary_detection"]["gating"],
            }
            for summary in curve
        ]
    ).to_csv(staging / OUTPUT_FILENAMES["calibration_curve"], index=False, float_format="%.17g")


def _promote_scientific_artifacts(root: Path, staging: Path) -> None:
    """Promote known staged files one by one, then remove the now-empty staging tree.

    ``staging`` is ``<root>/.staging/attempt-N``. Once every scientific file has
    been moved out, both the attempt directory and its ``.staging`` parent must be
    empty. Each is removed with ``rmdir`` so a non-empty directory fails closed
    instead of being force-deleted — a successful first-run completion never
    silently discards unknown staging content, and ``shutil.rmtree`` is never used
    on the result root. The final root audit must then see no ``.staging`` at all.
    Recovery handles an interrupted promotion.
    """
    for name in SCIENTIFIC_EMITTED_FILENAMES:
        os.replace(staging / name, root / name)

    staging_parent = staging.parent
    if staging_parent.name != STAGING_DIRNAME or staging_parent.parent != root:
        raise Stage1bIntegrityError(
            "the Stage 1b staging directory is not the expected <root>/.staging/attempt-N path"
        )

    _purge_os_metadata(staging)
    try:
        staging.rmdir()
    except OSError as exc:
        raise Stage1bIntegrityError(
            "the Stage 1b attempt staging directory is not empty after promotion "
            f"({sorted(child.name for child in staging.iterdir())}); refusing to force-delete it"
        ) from exc

    _purge_os_metadata(staging_parent)
    try:
        staging_parent.rmdir()
    except OSError as exc:
        raise Stage1bIntegrityError(
            f"the Stage 1b {STAGING_DIRNAME!r} parent is not empty after promotion "
            f"({sorted(child.name for child in staging_parent.iterdir())}); refusing to "
            "force-delete it"
        ) from exc


def _write_final_manifest(*, slug: str, artifacts: list[Path], source_artifacts: list[tuple[Path, str]], extra: dict) -> Path:
    """Write completion evidence and never write recovery state afterward."""
    try:
        return prov.write_manifest(
            slug,
            artifacts=artifacts,
            source_artifacts=source_artifacts,
            extra=extra,
        )
    except Exception as exc:
        setattr(exc, "_stage1b_manifest_write_started", True)
        raise


# --------------------------------------------------------------------------- #
# Seeds — level index comes from the frozen map, never from enumeration
# --------------------------------------------------------------------------- #
def level_index_for(theta: float) -> int:
    """The registered seed level index. 0.40 stays 4; 0.35 is the new index 5."""
    return reg.level_index_for(theta)


def injection_seed_for(theta: float, repetition: int) -> int:
    """``base_seed*1_000_003 + level_index*10_007 + repetition``, via Stage 1."""
    return stage1.derive_injection_seed(BASE_SEED, level_index_for(theta), repetition)


def permutation_seed_for(repetition: int) -> int:
    """``significance.DEFAULT_SEED + repetition``, via Stage 1. No theta term."""
    return stage1.derive_permutation_seed(BASE_SEED, repetition)


def declared_injection_seed(theta: float, repetition: int) -> int:
    """The declared formula written out literally, for the reproduction check.

    Deliberately independent of ``positive_control.derive_injection_seed`` so the
    integrity check compares two independent expressions of the same registered
    formula rather than a function against itself.
    """
    return int(BASE_SEED * 1_000_003 + level_index_for(theta) * 10_007 + repetition)


def declared_permutation_seed(repetition: int) -> int:
    """The declared permutation formula written out literally."""
    return int(sig.DEFAULT_SEED + repetition)


# --------------------------------------------------------------------------- #
# Detection — primary operating point and secondary non-gating diagnostic
# --------------------------------------------------------------------------- #
def operating_point_p_value(p_raw: float) -> float:
    """``min(1, 5 * p_raw)`` using the FROZEN historical divisor literal."""
    return min(1.0, STAGE1_OPERATIONAL_DIVISOR * float(p_raw))


def detected_by_stage1_rule(p_raw: float) -> bool:
    """PRIMARY: ``min(1, 5 * p_raw) < 0.05`` — the Stage 1 operating point."""
    return bool(operating_point_p_value(p_raw) < ALPHA)


def detected_by_raw_p(p_raw: float) -> bool:
    """SECONDARY, NON-GATING diagnostic: ``raw p < 0.05``.

    Reported alongside the primary rule and never used to gate, invalidate, or
    reinterpret the run.
    """
    return bool(float(p_raw) < ALPHA)


# --------------------------------------------------------------------------- #
# Mechanism invariants (registration section B)
# --------------------------------------------------------------------------- #
def _carrier_year_multisets(frame: pd.DataFrame, carrier: str) -> dict[int, np.ndarray]:
    values = pd.to_numeric(frame[carrier], errors="coerce")
    result: dict[int, np.ndarray] = {}
    for year in sorted(frame[YEAR_COLUMN].unique()):
        mask = (frame[YEAR_COLUMN] == year).to_numpy()
        observed = values.to_numpy(dtype=float)[mask]
        result[int(year)] = np.sort(observed[np.isfinite(observed)])
    return result


def check_mechanism_invariants(
    raw: pd.DataFrame, injected: pd.DataFrame, *, carrier: str = CARRIER
) -> dict[str, bool]:
    """Verify the registered mechanism invariants on one injected table.

    Outcome-blind by construction: every check compares structure between the
    source table and the injected table. None of them looks at an IC, a p-value,
    a detection flag, or any performance statistic.
    """
    before = _carrier_year_multisets(raw, carrier)
    after = _carrier_year_multisets(injected, carrier)
    multiset_preserved = set(before) == set(after) and all(
        before[year].shape == after[year].shape and np.array_equal(before[year], after[year])
        for year in before
    )
    missingness_preserved = bool(
        raw[carrier].isna().to_numpy().tolist() == injected[carrier].isna().to_numpy().tolist()
    )
    targets_unchanged = bool(raw[TARGET_COLUMN].equals(injected[TARGET_COLUMN]))
    other_columns = [column for column in raw.columns if column != carrier]
    non_carrier_unchanged = bool(
        list(raw.columns) == list(injected.columns)
        and all(raw[column].equals(injected[column]) for column in other_columns)
    )
    return {
        "carrier_observed_value_multiset_preserved_within_year": bool(multiset_preserved),
        "carrier_missingness_mask_preserved": missingness_preserved,
        "targets_unchanged": targets_unchanged,
        "non_carrier_features_unchanged": non_carrier_unchanged,
    }


def check_checkpoint_identities(
    checkpoints: dict[str, float | None], *, tolerance: float = IDENTITY_TOLERANCE
) -> dict[str, bool]:
    """Registered checks 19 and 20 — identity agreement, not performance.

    These compare checkpoints of the *same* quantity measured at successive
    points of the pipeline. They never threshold the magnitude of any IC.
    """
    identity_values = [checkpoints.get(name) for name in IDENTITY_CHECKPOINTS]
    identity_agree = all(value is not None for value in identity_values) and all(
        abs(float(value) - float(identity_values[0])) <= tolerance for value in identity_values
    )
    prediction = checkpoints.get("ic_model_prediction")
    evaluation = checkpoints.get("ic_final_evaluation")
    prediction_agrees = (
        prediction is not None
        and evaluation is not None
        and abs(float(prediction) - float(evaluation)) <= tolerance
    )
    return {
        "identity_checkpoint_ics_agree": bool(identity_agree),
        "ridge_prediction_ic_equals_final_evaluation_ic": bool(prediction_agrees),
    }


# --------------------------------------------------------------------------- #
# Pipeline-source guard
# --------------------------------------------------------------------------- #
@contextlib.contextmanager
def _restored_pipeline_source() -> Iterator[Path]:
    """Runner-level guard: ``TRAINING_MODELING`` is restored on every exit path.

    Stage 1's per-repetition ``_pipeline_reads`` already restores the override;
    this wraps the whole grid so an exception anywhere in the run still leaves
    the production pipeline pointing at the real dataset.
    """
    original = rx.TRAINING_MODELING
    try:
        yield original
    finally:
        rx.TRAINING_MODELING = original


def _injected_csv_sha256(injected: pd.DataFrame) -> str:
    """SHA256 of the injected table serialized exactly as Stage 1 serializes it."""
    with tempfile.TemporaryDirectory(prefix="financeiq-stage1b-verify-") as scratch:
        path = Path(scratch) / "modeling_dataset_training_injected.csv"
        injected.to_csv(path, index=False)
        return _sha256_path(path)


# --------------------------------------------------------------------------- #
# One repetition
# --------------------------------------------------------------------------- #
def run_repetition(
    raw: pd.DataFrame,
    *,
    theta: float,
    repetition: int,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
) -> dict:
    """One registered Stage 1b cell: inject, run the real pipeline, describe it.

    The numerical work is Stage 1's, unchanged. What Stage 1b adds is the
    registered seed lookup, the mechanism-invariant verification of the exact
    table the pipeline consumed, and its own detection semantics — computed from
    the frozen operating divisor, never from Stage 1's confirmatory family size.
    """
    if theta not in reg.LEVEL_INDEX:
        raise Stage1bError(f"theta {theta!r} is not on the registered Stage 1b grid")
    if repetition not in set(REPETITION_IDS):
        raise Stage1bError(
            f"repetition {repetition!r} is outside the registered Stage 1b id range "
            f"{REPETITION_IDS[0]}..{REPETITION_IDS[-1]}"
        )

    index = level_index_for(theta)
    injection_seed = injection_seed_for(theta, repetition)
    permutation_seed = permutation_seed_for(repetition)

    injected = stage1.inject_carrier(raw, CARRIER, theta, seed=injection_seed)
    invariants = check_mechanism_invariants(raw, injected)
    verified_sha = _injected_csv_sha256(injected)

    base = stage1.run_repetition(
        raw,
        CARRIER,
        theta,
        injection_seed=injection_seed,
        permutation_seed=permutation_seed,
        permutations=permutations,
        bootstraps=bootstraps,
    )
    if base["injected_dataset_sha256"] != verified_sha:
        raise Stage1bIntegrityError(
            "the table verified for mechanism invariants is not the table the pipeline "
            "consumed; injection is not reproducible for a fixed seed"
        )

    checkpoints = base["checkpoints"]
    counts = base["checkpoint_n"]
    invariants["carrier_reaches_model_input"] = bool(
        counts.get("ic_model_input_carrier") not in (None, 0)
    )
    invariants.update(check_checkpoint_identities(checkpoints))

    p_raw = float(base["permutation_p_value_two_sided"])
    return {
        "carrier": CARRIER,
        "model": PRIMARY_MODEL,
        "ic_injected": _rounded(theta),
        "level_index": index,
        "repetition": repetition,
        "injection_seed": int(injection_seed),
        "permutation_seed": int(permutation_seed),
        "injected_dataset_sha256": verified_sha,
        "checkpoints": checkpoints,
        "checkpoint_n": counts,
        "permutation_p_value_two_sided": _rounded(p_raw),
        "stage1_operating_point_p_value": _rounded(operating_point_p_value(p_raw)),
        "detected_stage1_rule": detected_by_stage1_rule(p_raw),
        "detected_raw_p05": detected_by_raw_p(p_raw),
        "bootstrap_ci_95": base["bootstrap_ci_95"],
        "mechanism_invariants": invariants,
    }


def run_grid(
    raw: pd.DataFrame,
    *,
    levels: tuple[float, ...] = IC_GRID,
    repetition_ids: tuple[int, ...] = REPETITION_IDS,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    progress: bool = False,
) -> list[dict]:
    """Every registered (theta, repetition) cell, in numeric report order.

    Report order is numeric; seed identity is the frozen map. The loop never
    enumerates the grid, so a reordering of ``IC_GRID`` cannot renumber a stream.
    """
    records: list[dict] = []
    for theta in levels:
        for repetition in repetition_ids:
            records.append(
                run_repetition(
                    raw,
                    theta=theta,
                    repetition=repetition,
                    permutations=permutations,
                    bootstraps=bootstraps,
                )
            )
        if progress:
            print(
                f"[stage1b] carrier={CARRIER} theta={theta:.2f} "
                f"level_index={level_index_for(theta)} reps={len(repetition_ids)} done",
                flush=True,
            )
    return records


def records_digest(records: list[dict]) -> str:
    """Deterministic content digest of an ordered record set (replay evidence)."""
    return _sha256_bytes(json.dumps(records, sort_keys=True).encode("utf-8"))


# --------------------------------------------------------------------------- #
# Aggregation — registered descriptive summaries only
# --------------------------------------------------------------------------- #
def summarize_level(records: list[dict]) -> dict:
    """Collapse one theta into its registered descriptive summary.

    No pass/fail, no monotonicity, no threshold crossing, no attenuation
    coefficient: the registration fixes this list and Stage 1b adds nothing to it.
    """
    if not records:
        raise Stage1bError("cannot summarize an empty level")
    thetas = {record["ic_injected"] for record in records}
    if len(thetas) != 1:
        raise Stage1bError(f"level records disagree on ic_injected: {sorted(thetas)}")
    theta = float(next(iter(thetas)))
    indices = {record["level_index"] for record in records}
    if len(indices) != 1:
        raise Stage1bError(f"level records disagree on level_index: {sorted(indices)}")

    trials = len(records)
    repetitions = sorted(int(record["repetition"]) for record in records)
    primary_hits = sum(1 for record in records if record["detected_stage1_rule"])
    secondary_hits = sum(1 for record in records if record["detected_raw_p05"])

    checkpoint_summary = {
        name: _summarize([record["checkpoints"][name] for record in records])
        for name, _ in stage1.CHECKPOINTS
    }
    return {
        "ic_injected": _rounded(theta),
        "level_index": int(next(iter(indices))),
        "carrier": CARRIER,
        "model": PRIMARY_MODEL,
        "repetitions": trials,
        "repetition_id_range": [repetitions[0], repetitions[-1]],
        # Registered summary A: realized raw equity carrier IC.
        "realized_raw_carrier_ic": checkpoint_summary["ic_raw_carrier"],
        # Registered summary B: final ridge / evaluated IC.
        "final_evaluated_ic": checkpoint_summary["ic_final_evaluation"],
        "checkpoint_summary": checkpoint_summary,
        "primary_detection": {
            "name": reg.PRIMARY_DETECTION_NAME,
            "rule": reg.PRIMARY_DETECTION_RULE,
            "raw_equivalent": reg.PRIMARY_DETECTION_RAW_EQUIVALENT,
            "detections": primary_hits,
            "rate": _rounded(primary_hits / trials),
            "wilson_95_pointwise": stage1._wilson_interval(primary_hits, trials),
        },
        "secondary_detection": {
            "name": reg.SECONDARY_DETECTION_NAME,
            "rule": reg.SECONDARY_DIAGNOSTIC_RULE,
            "gating": reg.SECONDARY_IS_GATING,
            "detections": secondary_hits,
            "rate": _rounded(secondary_hits / trials),
            "wilson_95_pointwise": stage1._wilson_interval(secondary_hits, trials),
        },
        "permutation_p_summary": _summarize(
            [record["permutation_p_value_two_sided"] for record in records]
        ),
    }


def calibration_curve(records: list[dict], *, levels: tuple[float, ...] = IC_GRID) -> list[dict]:
    """One summary per registered theta, in numeric report order."""
    summaries = []
    for theta in levels:
        rounded = _rounded(theta)
        summaries.append(summarize_level([r for r in records if r["ic_injected"] == rounded]))
    return summaries


def required_output_values(curve: list[dict]) -> list[tuple[str, float | None]]:
    """The outputs the registration requires to be finite, named for diagnostics."""
    values: list[tuple[str, float | None]] = []
    for summary in curve:
        label = f"theta={summary['ic_injected']}"
        for block in ("primary_detection", "secondary_detection"):
            values.append((f"{label}.{block}.rate", summary[block]["rate"]))
            low, high = summary[block]["wilson_95_pointwise"]
            values.append((f"{label}.{block}.wilson_low", low))
            values.append((f"{label}.{block}.wilson_high", high))
        for block in ("realized_raw_carrier_ic", "final_evaluated_ic"):
            for statistic in ("mean", "sd", "median", "p05", "p95"):
                values.append((f"{label}.{block}.{statistic}", summary[block][statistic]))
    return values


# --------------------------------------------------------------------------- #
# Closed integrity contract — pure evaluator
# --------------------------------------------------------------------------- #
def _check(passed: bool, detail: str) -> dict:
    return {"passed": bool(passed), "detail": detail}


def evaluate_integrity(
    *,
    records: list[dict],
    curve: list[dict],
    levels: tuple[float, ...],
    repetition_ids: tuple[int, ...],
    registered_source_sha: str,
    source_sha_before: str,
    source_sha_after: str,
    protected_digest_before: dict[str, str],
    protected_digest_after: dict[str, str],
    stage1_digest_before: dict[str, str],
    stage1_digest_after: dict[str, str],
    output_root: str,
    output_paths: list[str],
    pipeline_source_restored: bool,
    replay_probe: dict,
    output_audit: dict | None = None,
    workspace_digest_before: dict[str, str] | None = None,
    workspace_digest_after: dict[str, str] | None = None,
) -> dict:
    """Evaluate the registration's CLOSED integrity list. Pure: no I/O.

    Keys are the registered condition strings themselves, so a test can prove
    the report covers the closed list exactly. Every check is deterministic and
    outcome-blind: none inspects IC magnitude, detection rate, monotonicity,
    Wilson interval position, the theta=0 diagnostic, a crossing location, or
    any other performance statistic.
    """
    expected_cells = {(_rounded(theta), repetition) for theta in levels for repetition in repetition_ids}
    seen_cells = [(record["ic_injected"], int(record["repetition"])) for record in records]
    seen_counts = Counter(seen_cells)
    duplicates = sorted(cell for cell, count in seen_counts.items() if count > 1)
    missing = sorted(expected_cells - set(seen_counts))

    seed_formula_mismatches = [
        f"theta={record['ic_injected']} rep={record['repetition']}"
        for record in records
        if record["injection_seed"]
        != declared_injection_seed(float(record["ic_injected"]), int(record["repetition"]))
        or record["permutation_seed"] != declared_permutation_seed(int(record["repetition"]))
    ]

    injection_seeds = [record["injection_seed"] for record in records]
    permutation_seeds = {record["permutation_seed"] for record in records}
    injection_unique = len(set(injection_seeds)) == len(injection_seeds)
    streams_disjoint = set(injection_seeds).isdisjoint(permutation_seeds)

    stage1_injection = {
        stage1.derive_injection_seed(stream_seed, index, repetition)
        for stream_seed in (BASE_SEED, BASE_SEED + 1, BASE_SEED + 2)
        for index in range(len(stage1.IC_GRID))
        for repetition in reg.stage1_repetition_ids()
    }
    stage1_permutation = {
        stage1.derive_permutation_seed(BASE_SEED, repetition)
        for repetition in reg.stage1_repetition_ids()
    }
    stage1_overlap = (set(injection_seeds) | permutation_seeds) & (
        stage1_injection | stage1_permutation
    )

    root_prefix = output_root.rstrip("/") + "/"
    escaping = sorted(path for path in output_paths if not path.startswith(root_prefix))
    protected_root_hits = sorted(
        path
        for path in output_paths
        for protected in (*prov.PROTECTED_RESULTS_ROOTS, *PROTECTED_DATA_ROOTS)
        if path == protected or path.startswith(protected.rstrip("/") + "/")
    )
    filesystem_output_ok = True
    filesystem_output_detail = "actual output audit not supplied in pure fixture mode"
    if output_audit is not None:
        filesystem_output_ok = bool(output_audit.get("passed")) and set(
            output_audit.get("actual_scientific_files", [])
        ) == set(SCIENTIFIC_EMITTED_FILENAMES)
        filesystem_output_detail = (
            f"actual_files={output_audit.get('actual_files', [])}; "
            f"unexpected_files={output_audit.get('unexpected_files', [])}; "
            f"unexpected_directories={output_audit.get('unexpected_directories', [])}; "
            f"missing={output_audit.get('missing_scientific_files', [])}"
        )
    if workspace_digest_before is not None or workspace_digest_after is not None:
        workspace_write_ok = workspace_digest_before == workspace_digest_after
        filesystem_output_ok = filesystem_output_ok and workspace_write_ok
        filesystem_output_detail += (
            f"; outside_namespace_unchanged={workspace_write_ok}"
        )

    non_finite = [
        name
        for name, value in required_output_values(curve)
        if value is None or not math.isfinite(float(value))
    ]

    mechanical = {
        "registered source dataset hash matches": _check(
            source_sha_before == registered_source_sha,
            f"pre-run source sha256 {source_sha_before[:12]}… vs registered "
            f"{registered_source_sha[:12]}…",
        ),
        "source remains unchanged": _check(
            source_sha_before == source_sha_after,
            f"post-run source sha256 {source_sha_after[:12]}…",
        ),
        "complete 6 × 400 matrix": _check(
            len(records) == len(levels) * len(repetition_ids)
            and set(seen_cells) == expected_cells,
            f"{len(records)} cells over {len(levels)} levels × {len(repetition_ids)} repetitions",
        ),
        "no missing/duplicate repetition cells": _check(
            not missing and not duplicates,
            f"missing={missing[:5]} duplicates={duplicates[:5]}",
        ),
        "declared seed formulas reproduced": _check(
            not seed_formula_mismatches,
            f"{len(seed_formula_mismatches)} cells disagreed with the declared formulas",
        ),
        "no seed collision": _check(
            injection_unique and streams_disjoint,
            f"{len(set(injection_seeds))} distinct injection seeds; "
            f"injection/permutation streams disjoint={streams_disjoint}",
        ),
        "no Stage 1 repetition/seed overlap": _check(
            not stage1_overlap,
            f"{len(stage1_overlap)} seeds shared with Stage 1 streams",
        ),
        "Stage 1b writes only to its isolated namespace": _check(
            not escaping and not protected_root_hits and filesystem_output_ok,
            f"root={output_root}; escaping={escaping}; protected_hits={protected_root_hits}; "
            f"{filesystem_output_detail}",
        ),
        "Stage 1 historical namespace is not overwritten": _check(
            stage1_digest_before == stage1_digest_after,
            f"{len(stage1_digest_before)} Stage 1 files hashed before and after",
        ),
        "no data/trusted*, data/trusted_clean*, or data/provenance* mutation": _check(
            protected_digest_before == protected_digest_after,
            f"{len(protected_digest_before)} protected data files hashed before and after",
        ),
        "required outputs finite": _check(
            not non_finite, f"{len(non_finite)} non-finite required outputs: {non_finite[:5]}"
        ),
        "replay deterministic": _check(
            bool(replay_probe.get("identical")),
            f"replay probe theta={replay_probe.get('ic_injected')} "
            f"repetition={replay_probe.get('repetition')} identical="
            f"{replay_probe.get('identical')}",
        ),
        "runtime override restored on every exit path": _check(
            pipeline_source_restored,
            "run_experiments.TRAINING_MODELING matched its pre-run value after the grid",
        ),
    }

    def _all(flag: str) -> bool:
        return all(bool(record["mechanism_invariants"].get(flag)) for record in records)

    mechanism = {
        "carrier observed-value multiset preserved within year": _check(
            _all("carrier_observed_value_multiset_preserved_within_year"),
            "per-year sorted observed carrier values identical to the source table",
        ),
        "carrier missingness mask preserved": _check(
            _all("carrier_missingness_mask_preserved"), "null stays null, cell for cell"
        ),
        "targets unchanged": _check(
            _all("targets_unchanged"), f"{TARGET_COLUMN} identical to the source table"
        ),
        "non-carrier features unchanged": _check(
            _all("non_carrier_features_unchanged"), "every non-carrier column identical"
        ),
        "equity reaches the modeled feature path": _check(
            _all("carrier_reaches_model_input"),
            f"{CARRIER} measured at the model-input checkpoint in every cell",
        ),
        "identity/invariant checkpoint ICs agree within the already governed Stage 1 "
        "numerical tolerance": _check(
            _all("identity_checkpoint_ics_agree"),
            f"identity checkpoints {list(IDENTITY_CHECKPOINTS)} agree within "
            f"{IDENTITY_TOLERANCE:g}",
        ),
        "ridge prediction IC and final evaluation IC agree within the already governed "
        "Stage 1 numerical tolerance": _check(
            _all("ridge_prediction_ic_equals_final_evaluation_ic"),
            f"ic_model_prediction equals ic_final_evaluation within {IDENTITY_TOLERANCE:g}",
        ),
    }

    failures = sorted(
        name for block in (mechanical, mechanism) for name, result in block.items() if not result["passed"]
    )
    return {
        "contract": "closed deterministic list — docs/thesis/STAGE_1B_REGISTRATION.md",
        "has_performance_gate": reg.HAS_PERFORMANCE_GATE,
        "excluded_from_every_check": list(reg.INTEGRITY_CHECK_EXCLUSIONS),
        "mechanical": mechanical,
        "mechanism": mechanism,
        "failures": failures,
        "passed": not failures,
    }


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _flatten_record(record: dict) -> dict:
    flat = {
        "carrier": record["carrier"],
        "model": record["model"],
        "ic_injected": record["ic_injected"],
        "level_index": record["level_index"],
        "repetition": record["repetition"],
        "injection_seed": record["injection_seed"],
        "permutation_seed": record["permutation_seed"],
        "injected_dataset_sha256": record["injected_dataset_sha256"],
        "permutation_p_value_two_sided": record["permutation_p_value_two_sided"],
        "stage1_operating_point_p_value": record["stage1_operating_point_p_value"],
        "detected_stage1_rule": record["detected_stage1_rule"],
        "detected_raw_p05": record["detected_raw_p05"],
    }
    for name, _ in stage1.CHECKPOINTS:
        flat[name] = record["checkpoints"][name]
        flat[f"n_{name}"] = record["checkpoint_n"][name]
    for name, value in sorted(record["mechanism_invariants"].items()):
        flat[f"invariant_{name}"] = value
    return flat


LIMITATIONS: tuple[str, ...] = (
    "Stage 1b is apparatus characterization on synthetic input. It establishes no predictive "
    "edge, no alpha, no investment value, and no production readiness, and the repository's "
    "committed walk-forward finding is unchanged by it.",
    "The primary result is descriptive. Stage 1b has no scientific performance PASS/FAIL gate: "
    "a flat, non-monotone, weak, surprising, or high-background curve is a scientific result, "
    "not an integrity failure.",
    "The realized equity panel is fixed across repetitions. The synthetic injection draw changes "
    "and the permutation-test RNG changes, so the reported variation carries injection-draw "
    "randomness plus permutation Monte-Carlo randomness conditional on this one realized panel. "
    "It excludes uncertainty from drawing another equity universe, market panel, time period, "
    "PIT universe, or monthly sample.",
    "Wilson intervals are pointwise per theta. The permutation seed does not depend on theta or "
    "level index, so the permutation RNG stream is shared across theta levels for the same "
    "repetition id; the intervals are marginal and are not simultaneous or between-level "
    "comparison intervals. No between-theta inference is drawn from them.",
    "For R=400 the approximate worst-case pointwise Wilson half-width is about 4.9 percentage "
    "points near p=0.50 and about 3.9 percentage points near p=0.80. R=400 improves grid-point "
    "precision but does not identify an exact between-grid crossing, and no interpolation is "
    "confirmatory.",
    "The divisor 5 in the primary rule is the frozen historical Stage 1 operating divisor, "
    "retained as one fixed operating point for comparability. Stage 1b's six theta levels are "
    "not a hypothesis family and no family-wise-error-control claim is made across them.",
    "theta=0 is not a zero-signal market world: the real non-carrier features remain in the "
    "pipeline, so the theta=0 rung describes that background rather than zero.",
    "theta is a synthetic copula design constant. It is not a realistic BIST IC, not a universal "
    "IC benchmark, and not a smallest effect size of interest; SESOI remains UNRESOLVED.",
    "The injection permutes the carrier's own observed values within each year, which destroys "
    "that column's joint structure with the other features. Every rung including theta=0 carries "
    "the same damage, so the curve is internally consistent, but the absolute recovered IC is "
    "not the IC an equally strong naturally-occurring feature would give.",
    "The temporary run_experiments.TRAINING_MODELING override is process-global and this stage "
    "is single-threaded; concurrent execution is outside its scope.",
)


def build_report(
    *,
    records: list[dict],
    curve: list[dict],
    integrity: dict,
    replay_probe: dict,
    raw_path: Path,
    base_seed: int,
    started_at: str,
    duration_seconds: float,
    test_split_sizes: list[int],
    split_count: int,
) -> dict:
    return {
        "schema_version": 1,
        "experiment": SLUG,
        "stage": "Stage 1b — prospective calibration / diagnostic re-scope of the Stage 1 positive control",
        "registration": reg.REGISTRATION_DOC,
        "protocol": reg.PROTOCOL_DOC,
        "claim_safety": {
            "descriptive_research_evidence_only": True,
            "reliable_predictive_edge_established": False,
            "investment_value_established": False,
            "apparatus_characterization_only": True,
            "statement": CLAIM_SAFETY_SENTENCE,
        },
        "provenance": {
            "git": _git_metadata(),
            "seed": base_seed,
            "implementation_sha256": implementation_hash(),
            "registration_module_sha256": registration_hash(),
            "stage1_implementation_sha256": stage1.implementation_hash(),
            "significance_module_sha256": _sha256_path(ROOT / "experiments" / "significance.py"),
            "pipeline_module_sha256": _sha256_path(ROOT / "experiments" / "run_experiments.py"),
            "source_dataset": {
                "path": raw_path.relative_to(ROOT).as_posix(),
                "sha256": _sha256_path(raw_path),
                "registered_sha256": reg.DATASET_SHA256,
                "size_bytes": raw_path.stat().st_size,
            },
            "python": platform.python_version(),
            "platform": platform.platform(),
            "started_at_utc": started_at,
            "duration_seconds": _rounded(duration_seconds, 3),
        },
        "design": {
            "prospective_not_blind": reg.PROSPECTIVE_NOT_BLIND,
            "carrier": CARRIER,
            "carriers": list(reg.STAGE_1B_CARRIERS),
            "model": PRIMARY_MODEL,
            "injection_mechanism": reg.INJECTION_MECHANISM,
            "ic_grid": list(IC_GRID),
            "new_rung": reg.NEW_RUNG,
            "level_index_map": {str(theta): index for theta, index in reg.LEVEL_INDEX.items()},
            "report_order": "numeric; seed identity is the frozen level-index map",
            "repetitions_per_level": REPETITIONS,
            "repetition_ids": [REPETITION_IDS[0], REPETITION_IDS[-1]],
            "permutations": PERMUTATIONS,
            "bootstraps": BOOTSTRAPS,
            "alpha": ALPHA,
            "stage1_operational_divisor": STAGE1_OPERATIONAL_DIVISOR,
            "stage1_operational_divisor_note": (
                "Frozen historical Stage 1 operating divisor, retained as one fixed operating "
                "point only. Not derived from len(IC_GRID), not a Stage 1b hypothesis-family "
                "size, and not a six-level family-wise-error-control claim."
            ),
            "primary_detection": {
                "name": reg.PRIMARY_DETECTION_NAME,
                "rule": reg.PRIMARY_DETECTION_RULE,
                "raw_equivalent": reg.PRIMARY_DETECTION_RAW_EQUIVALENT,
            },
            "secondary_detection": {
                "name": reg.SECONDARY_DETECTION_NAME,
                "rule": reg.SECONDARY_DIAGNOSTIC_RULE,
                "gating": reg.SECONDARY_IS_GATING,
            },
            "has_performance_gate": reg.HAS_PERFORMANCE_GATE,
            "detection_interval": reg.DETECTION_INTERVAL,
            "excluded_stage_1_carrier_arms": list(reg.EXCLUDED_STAGE_1_CARRIER_ARMS),
            "excluded_stage_1_theta_arms": list(reg.EXCLUDED_STAGE_1_THETA_ARMS),
            "not_computed": [
                "Stage 1 confirmatory_gate",
                "Stage 1 gate_informativeness",
                "strict-monotonicity pass/fail",
                "GATE_LEVELS rejection criterion",
                "80%-detection gate or interpolated threshold crossing",
            ],
            "seed_formulas": {
                "injection": reg.INJECTION_SEED_FORMULA,
                "permutation": reg.PERMUTATION_SEED_FORMULA,
            },
            "test_split_sizes": test_split_sizes,
            "split_count": split_count,
            "sesoi_status": reg.SESOI_STATUS,
            "stage_1_status": reg.STAGE_1_STATUS,
            "stage_2_status": reg.STAGE_2_STATUS,
        },
        "checkpoint_definitions": {name: description for name, description in stage1.CHECKPOINTS},
        "checkpoint_roles": stage1.CHECKPOINT_ROLES,
        "calibration_curve": curve,
        "execution_preconditions": {
            "classification": "execution preconditions / implementation invariants",
            "checks": list(EXECUTION_PRECONDITIONS),
            "note": (
                "These checks protect the registered execution and provenance boundary; "
                "they are not additional scientific integrity or performance gates."
            ),
        },
        "integrity": integrity,
        "replay": {
            "probe": replay_probe,
            "records_digest": records_digest(records),
            "rule": (
                "One governed prospective run with the frozen seed schedule. A deterministic "
                "replay with identical settings is verification, not a new scientific run."
            ),
        },
        "limitations": list(LIMITATIONS),
    }


def render_markdown(report: dict) -> str:
    design = report["design"]
    lines: list[str] = [
        "# Stage 1b — positive-control calibration / diagnostic",
        "",
        report["claim_safety"]["statement"],
        "",
        f"Registration: `{report['registration']}` · protocol: `{report['protocol']}` · "
        f"git `{report['provenance']['git']['short_sha']}` · seed {report['provenance']['seed']} · "
        f"implementation `{report['provenance']['implementation_sha256'][:12]}`",
        "",
        "## Design",
        "",
        f"- Carrier: `{design['carrier']}` only · model `{design['model']}`",
        f"- Grid (report order): {design['ic_grid']} · new rung {design['new_rung']}",
        f"- Seed level-index map: {design['level_index_map']} "
        "(frozen; report order is numeric, seed identity is the map)",
        f"- Repetitions: {design['repetitions_per_level']} per level, global ids "
        f"{design['repetition_ids'][0]}–{design['repetition_ids'][1]}",
        f"- Permutations {design['permutations']} · bootstraps {design['bootstraps']} · "
        f"alpha {design['alpha']}",
        f"- Primary: {design['primary_detection']['name']} — `{design['primary_detection']['rule']}`",
        f"- Secondary: {design['secondary_detection']['name']} — "
        f"`{design['secondary_detection']['rule']}` (gating: {design['secondary_detection']['gating']})",
        f"- Scientific performance gate: **{design['has_performance_gate']}**",
        f"- Not computed: {', '.join(design['not_computed'])}",
        f"- Excluded historical Stage 1 arms: "
        f"{', '.join(design['excluded_stage_1_carrier_arms'])}; theta="
        f"{', '.join(str(v) for v in design['excluded_stage_1_theta_arms'])}",
        "",
        "The divisor 5 is the frozen historical Stage 1 operating divisor, kept as one fixed "
        "operating point so this descriptive curve stays comparable to Stage 1. The six theta "
        "levels are not a hypothesis family and no family-wise-error-control claim is made "
        "across them.",
        "",
        "## Calibration and detection by theta",
        "",
        "| theta | mean realized raw carrier IC | mean final evaluated IC | "
        "primary detections / reps | primary rate | pointwise 95% Wilson | secondary rate |",
        "|---|---|---|---|---|---|---|",
    ]
    for summary in report["calibration_curve"]:
        raw_mean = summary["realized_raw_carrier_ic"]["mean"]
        final_mean = summary["final_evaluated_ic"]["mean"]
        primary = summary["primary_detection"]
        secondary = summary["secondary_detection"]
        low, high = primary["wilson_95_pointwise"]
        lines.append(
            f"| {float(summary['ic_injected']):.2f} | {raw_mean} | {final_mean} | "
            f"{primary['detections']}/{summary['repetitions']} | {primary['rate']} | "
            f"[{low}, {high}] | {secondary['rate']} |"
        )

    lines += [
        "",
        "Wilson intervals are pointwise per theta. They are marginal intervals, not simultaneous "
        "or between-level comparison intervals, and no between-theta inference is drawn from them.",
        "",
        "## Registered descriptive summaries",
        "",
        "| theta | quantity | mean | SD | median | p05 | p95 |",
        "|---|---|---|---|---|---|---|",
    ]
    for summary in report["calibration_curve"]:
        for label, key in (
            ("realized raw carrier IC", "realized_raw_carrier_ic"),
            ("final evaluated IC", "final_evaluated_ic"),
        ):
            stats = summary[key]
            lines.append(
                f"| {float(summary['ic_injected']):.2f} | {label} | {stats['mean']} | "
                f"{stats['sd']} | {stats['median']} | {stats['p05']} | {stats['p95']} |"
            )

    integrity = report["integrity"]
    lines += [
        "",
        "## Closed integrity contract",
        "",
        f"All deterministic conditions passed: **{integrity['passed']}** "
        f"(failures: {integrity['failures'] or 'none'}).",
        "",
        "No integrity check inspects or thresholds "
        f"{', '.join(integrity['excluded_from_every_check'])}. Run validity is governed by this "
        "closed deterministic list only; there is no scientific performance gate.",
        "",
        "| check | passed |",
        "|---|---|",
    ]
    for block in ("mechanical", "mechanism"):
        for name, result in integrity[block].items():
            lines.append(f"| {name} | {result['passed']} |")

    lines += [
        "",
        "## Replay",
        "",
        f"Replay probe on the registered cell theta={report['replay']['probe'].get('ic_injected')}, "
        f"repetition {report['replay']['probe'].get('repetition')}: identical = "
        f"{report['replay']['probe'].get('identical')}. Ordered-record digest "
        f"`{report['replay']['records_digest'][:16]}`.",
        "",
        report["replay"]["rule"],
        "",
        "## Limitations",
        "",
    ]
    lines += [f"- {item}" for item in report["limitations"]]
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #
def registered_plan() -> dict:
    """What the one governed run would do. Reads nothing and writes nothing."""
    return {
        "experiment": SLUG,
        "registration": reg.REGISTRATION_DOC,
        "carrier": CARRIER,
        "model": PRIMARY_MODEL,
        "ic_grid": list(IC_GRID),
        "level_index_map": {str(theta): index for theta, index in reg.LEVEL_INDEX.items()},
        "repetitions_per_level": REPETITIONS,
        "repetition_ids": [REPETITION_IDS[0], REPETITION_IDS[-1]],
        "permutations": PERMUTATIONS,
        "bootstraps": BOOTSTRAPS,
        "alpha": ALPHA,
        "stage1_operational_divisor": STAGE1_OPERATIONAL_DIVISOR,
        "primary_detection": reg.PRIMARY_DETECTION_RULE,
        "secondary_detection": reg.SECONDARY_DIAGNOSTIC_RULE,
        "has_performance_gate": reg.HAS_PERFORMANCE_GATE,
        "result_root": reg.STAGE_1B_RESULT_ROOT,
        "emitted_files": list(EMITTED_FILENAMES),
        "operational_files": list(OPERATIONAL_FILENAMES),
        "cells": len(IC_GRID) * REPETITIONS,
        "executed": False,
        "note": (
            "Nothing was run. The one governed Stage 1b run requires an explicit --run "
            "(make thesis-stage1b)."
        ),
    }


def _assert_registered_carrier(raw: pd.DataFrame) -> None:
    """The Stage 1 coverage rule must still select the registered carrier."""
    selected = stage1.select_carriers(raw)["primary"]
    if selected != CARRIER:
        raise Stage1bError(
            f"the Stage 1 primary carrier rule now selects {selected!r}, not the registered "
            f"Stage 1b carrier {CARRIER!r}; this requires a dated amendment, not a code change"
        )


def _replay_probe(
    raw: pd.DataFrame,
    records: list[dict],
    *,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
) -> dict:
    """Re-execute one already-registered cell and compare it byte for byte.

    The probe cell is part of the run itself, executed with identical registered
    settings, so this adds no setting, no seed, and no scientific quantity — it
    is the deterministic-replay evidence the closed contract requires.
    """
    theta, repetition = REPLAY_PROBE_THETA, REPLAY_PROBE_REPETITION
    original = [
        record
        for record in records
        if record["ic_injected"] == _rounded(theta) and int(record["repetition"]) == repetition
    ]
    if len(original) != 1:
        raise Stage1bIntegrityError("the replay probe cell is not present exactly once in the run")
    replayed = run_repetition(
        raw, theta=theta, repetition=repetition, permutations=permutations, bootstraps=bootstraps
    )
    first = json.dumps(original[0], sort_keys=True)
    second = json.dumps(replayed, sort_keys=True)
    return {
        "ic_injected": _rounded(theta),
        "repetition": repetition,
        "identical": first == second,
        "digest": _sha256_bytes(first.encode("utf-8")),
    }


def run(*, progress: bool = True, repeat_after_crash: bool = False) -> Path:
    """Execute the governed run or its explicitly authorized crash recovery.

    ``repeat_after_crash`` is operational lifecycle state, not a scientific
    setting. The grid, R, seeds, permutations, bootstraps, alpha, carrier, model,
    and detection rules remain frozen in the registration in both modes.
    """
    root, marker_path, marker_payload, attempt_number = _prepare_attempt(
        repeat_after_crash=repeat_after_crash
    )
    try:
        return _run_attempt(
            root,
            marker_path=marker_path,
            marker_payload=marker_payload,
            attempt_number=attempt_number,
            progress=progress,
        )
    except Exception as exc:
        if not getattr(exc, "_stage1b_manifest_write_started", False):
            with contextlib.suppress(Exception):
                _set_attempt_status(marker_path, marker_payload, attempt_number, "incomplete")
        raise


def _run_attempt(
    root: Path,
    *,
    marker_path: Path,
    marker_payload: dict,
    attempt_number: int,
    progress: bool,
) -> Path:
    """Run one attempt after the durable lifecycle marker has been written."""
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    workspace_before = workspace_digest_excluding_stage1b()

    base_seed = prov.seed_for(SLUG)
    if base_seed != BASE_SEED:
        raise Stage1bError(
            f"declared seed for {SLUG!r} is {base_seed}, registration says {BASE_SEED}"
        )

    raw_path = rx.TRAINING_MODELING
    if not raw_path.is_file():
        raise Stage1bError(f"modeling dataset not found: {raw_path}")
    source_sha_before = _sha256_path(raw_path)
    if source_sha_before != reg.DATASET_SHA256:
        raise Stage1bIntegrityError(
            f"source dataset sha256 {source_sha_before} does not match the registered "
            f"{reg.DATASET_SHA256}; the registration governs a specific dataset"
        )
    protected_before = protected_data_digest()
    stage1_before = tree_digest(STAGE_1_RESULT_ROOT)

    raw = pd.read_csv(raw_path)
    _assert_registered_carrier(raw)

    reference_panel = rx.build_panel()
    test_years = sorted(split["test_feature_year"] for split in rx.SPLITS)
    test_split_sizes = sorted(
        int(count)
        for count in reference_panel[reference_panel["feature_year"].isin(test_years)]
        .groupby("feature_year")
        .size()
        .to_list()
    )

    with _restored_pipeline_source() as original_source:
        records = run_grid(raw, progress=progress)
        replay_probe = _replay_probe(raw, records)
    pipeline_source_restored = rx.TRAINING_MODELING == original_source

    source_sha_after = _sha256_path(raw_path)
    protected_after = protected_data_digest()
    stage1_after = tree_digest(STAGE_1_RESULT_ROOT)
    workspace_after = workspace_digest_excluding_stage1b()

    curve = calibration_curve(records)
    output_root = reg.STAGE_1B_RESULT_ROOT.rstrip("/")
    planned_output_paths = [
        f"{output_root}/{name}" for name in SCIENTIFIC_EMITTED_FILENAMES
    ]

    preflight_integrity = evaluate_integrity(
        records=records,
        curve=curve,
        levels=IC_GRID,
        repetition_ids=REPETITION_IDS,
        registered_source_sha=reg.DATASET_SHA256,
        source_sha_before=source_sha_before,
        source_sha_after=source_sha_after,
        protected_digest_before=protected_before,
        protected_digest_after=protected_after,
        stage1_digest_before=stage1_before,
        stage1_digest_after=stage1_after,
        output_root=output_root,
        output_paths=planned_output_paths,
        pipeline_source_restored=pipeline_source_restored,
        replay_probe=replay_probe,
        workspace_digest_before=workspace_before,
        workspace_digest_after=workspace_after,
    )
    if not preflight_integrity["passed"]:
        raise Stage1bIntegrityError(
            "closed integrity contract failed before staging. Failing conditions: "
            + "; ".join(preflight_integrity["failures"])
        )

    report = build_report(
        records=records,
        curve=curve,
        integrity=preflight_integrity,
        replay_probe=replay_probe,
        raw_path=raw_path,
        base_seed=base_seed,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_seconds=time.perf_counter() - clock,
        test_split_sizes=test_split_sizes,
        split_count=len(rx.SPLITS),
    )
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)

    staging_parent = root / STAGING_DIRNAME
    staging_parent.mkdir(parents=True, exist_ok=True)
    staging = staging_parent / f"attempt-{attempt_number}"
    _write_scientific_artifacts(
        staging,
        report=report,
        markdown=markdown,
        records=records,
        curve=curve,
    )
    stage_audit = _audit_output_surface(
        staging,
        expected_names=SCIENTIFIC_EMITTED_FILENAMES,
    )
    if not stage_audit["passed"]:
        raise Stage1bIntegrityError(
            "staged output confinement failed; completion evidence will not be written: "
            + json.dumps(stage_audit, sort_keys=True)
        )

    actual_staged_paths = [
        _relative_to_repo(path)
        for path in sorted(staging.rglob("*"))
        if path.is_file()
    ]
    integrity = evaluate_integrity(
        records=records,
        curve=curve,
        levels=IC_GRID,
        repetition_ids=REPETITION_IDS,
        registered_source_sha=reg.DATASET_SHA256,
        source_sha_before=source_sha_before,
        source_sha_after=source_sha_after,
        protected_digest_before=protected_before,
        protected_digest_after=protected_after,
        stage1_digest_before=stage1_before,
        stage1_digest_after=stage1_after,
        output_root=output_root,
        output_paths=actual_staged_paths,
        pipeline_source_restored=pipeline_source_restored,
        replay_probe=replay_probe,
        output_audit=stage_audit,
        workspace_digest_before=workspace_before,
        workspace_digest_after=workspace_after,
    )
    if not integrity["passed"]:
        raise Stage1bIntegrityError(
            "closed integrity contract failed before promotion. Failing conditions: "
            + "; ".join(integrity["failures"])
        )

    # Rewrite the staged report with the final actual-filesystem integrity result.
    report = build_report(
        records=records,
        curve=curve,
        integrity=integrity,
        replay_probe=replay_probe,
        raw_path=raw_path,
        base_seed=base_seed,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_seconds=time.perf_counter() - clock,
        test_split_sizes=test_split_sizes,
        split_count=len(rx.SPLITS),
    )
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)
    (staging / OUTPUT_FILENAMES["report_json"]).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (staging / OUTPUT_FILENAMES["report_md"]).write_text(markdown, encoding="utf-8")

    _promote_scientific_artifacts(root, staging)
    output = prov.output_dir(SLUG, create=False)
    _purge_os_metadata(output)
    final_pre_manifest_audit = _audit_output_surface(
        output,
        expected_names=SCIENTIFIC_EMITTED_FILENAMES,
        operational_names=OPERATIONAL_FILENAMES,
    )
    if not final_pre_manifest_audit["passed"]:
        raise Stage1bIntegrityError(
            "promoted output confinement failed; completion evidence will not be written: "
            + json.dumps(final_pre_manifest_audit, sort_keys=True)
        )

    marker_payload = _set_attempt_status(
        marker_path, marker_payload, attempt_number, "complete"
    )
    marker_relative = _relative_to_repo(marker_path)
    report_json = output / OUTPUT_FILENAMES["report_json"]
    report_md = output / OUTPUT_FILENAMES["report_md"]
    repetitions_csv = output / OUTPUT_FILENAMES["repetitions"]
    curve_csv = output / OUTPUT_FILENAMES["calibration_curve"]

    if progress:
        print(f"[stage1b] finalizing {report_json.relative_to(ROOT)}")

    # This is the final write. The manifest is the completion authority and is
    # emitted only after integrity, claim-safety, staging, and promotion checks.
    _write_final_manifest(
        slug=SLUG,
        artifacts=[report_json, report_md, repetitions_csv, curve_csv],
        source_artifacts=[(raw_path, "modeling dataset (read-only; never modified)")],
        extra={
            "stage": "Stage 1b — prospective calibration / diagnostic",
            "registration": reg.REGISTRATION_DOC,
            "git": _git_metadata(),
            "implementation_sha256": implementation_hash(),
            "registration_module_sha256": registration_hash(),
            "ic_grid": list(IC_GRID),
            "repetitions_per_level": REPETITIONS,
            "repetition_ids": [REPETITION_IDS[0], REPETITION_IDS[-1]],
            "permutations": PERMUTATIONS,
            "stage1_operational_divisor": STAGE1_OPERATIONAL_DIVISOR,
            "has_performance_gate": reg.HAS_PERFORMANCE_GATE,
            "integrity_passed": integrity["passed"],
            "records_digest": records_digest(records),
            "completion_status": "complete",
            "completion_authority": MANIFEST_FILENAME,
            "scientific_emitted_files": list(SCIENTIFIC_EMITTED_FILENAMES),
            "operational_attempt_provenance": {
                "path": marker_relative,
                "sha256": _sha256_path(marker_path),
                "classification": "governance/provenance metadata; not a scientific emitted artifact",
            },
            "attempt_provenance": marker_payload,
        },
    )

    return report_json


def replay_check(*, permutations: int = 2_000) -> dict:
    """Determinism probe: run one repetition id across the grid twice and compare.

    Writes nothing, creates no result root, and reports no scientific value — only
    whether the two passes are identical, plus a digest. Verification machinery,
    not a scientific run.
    """
    raw = pd.read_csv(rx.TRAINING_MODELING)
    _assert_registered_carrier(raw)
    with _restored_pipeline_source():
        passes = [
            run_grid(
                raw,
                repetition_ids=(REPETITION_IDS[0],),
                permutations=permutations,
                bootstraps=permutations,
                progress=False,
            )
            for _ in range(2)
        ]
    first = json.dumps(passes[0], sort_keys=True)
    second = json.dumps(passes[1], sort_keys=True)
    return {
        "identical": first == second,
        "digest": _sha256_bytes(first.encode("utf-8")),
        "cells": len(passes[0]),
        "permutations": permutations,
        "note": "reduced-permutation determinism probe; not the governed run",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 1b calibration runner. Without --run it only prints the plan."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--run",
        action="store_true",
        help="execute the one governed prospective Stage 1b run (make thesis-stage1b)",
    )
    mode.add_argument(
        "--replay-check",
        action="store_true",
        help="determinism probe over one repetition id; writes nothing",
    )
    mode.add_argument(
        "--repeat-after-crash",
        action="store_true",
        help="recover only an incomplete prior Stage 1b attempt using its registered settings",
    )
    args = parser.parse_args()

    if args.replay_check:
        result = replay_check()
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["identical"] else 1)
    if args.run:
        run()
        return
    if args.repeat_after_crash:
        run(repeat_after_crash=True)
        return
    print(json.dumps(registered_plan(), indent=2))


if __name__ == "__main__":
    main()
