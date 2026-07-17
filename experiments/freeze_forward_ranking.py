"""Freeze the 2026 forward ranking for pre-registered evaluation (R3-PREREG-01).

This script does NOT reimplement the forward-ranking heuristic.  It loads the
unchanged backend service (``forecasting_csv_service``) through the documented
``RESEARCH_REPO_ROOT`` seam and invokes the exact production forward-inference
function that ``GET /forecasting/inference?year=2025`` serves:
``inference_forecast(input_year=2025, top_n=12)`` (which internally calls the
service's own ``train_parameters`` and ``run_forecast``).  Its output is frozen
verbatim, stamped with the git SHA, the service source checksum, and the input
dataset checksums, so a later evaluation can be run against outcomes that do not
exist yet.

Pre-registration boundary: freezing the ranking is a discipline, not a
prediction.  The frozen ranking is an ``unevaluated_forward_forecast``; it is not
a recommendation, an expected-return claim, or evidence of a reliable predictive
edge.  See ``docs/PREREGISTERED_2026_EVALUATION.md``.

Determinism: running ``make freeze-forward-2026`` twice at the same repository
state produces byte-identical ``forward_ranking_2026.csv`` and
``freeze_manifest.json``.  No wall-clock timestamp is written; the deterministic
freeze identifier is derived from the protocol identifier and the git SHA.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "experiments" / "results_forward_2026"
FROZEN_RANKING_PATH = RESULTS_DIR / "forward_ranking_2026.csv"
FREEZE_MANIFEST_PATH = RESULTS_DIR / "freeze_manifest.json"

SERVICE_FILE = ROOT / "backend" / "app" / "services" / "forecasting_csv_service.py"
PUBLIC_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_public_2020_2025.csv"
TRAINING_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_training_2020_2025.csv"
BASE_DATASET = ROOT / "data" / "trusted_clean" / "modeling_dataset_2020_2025.csv"

PROTOCOL_DOCUMENT = "docs/PREREGISTERED_2026_EVALUATION.md"
PROTOCOL_IDENTIFIER = "PREREG-2026-FORWARD-v1"

TASK_ID = "R3-PREREG-01"
FEATURE_YEAR = 2025
TARGET_YEAR = 2026
TOP_N = 12
REGENERATION_COMMAND = "make freeze-forward-2026"

# Independent canonical anchors. The ranking checksum is also pinned in the
# evaluator and protocol. The manifest anchor prevents a hand-edited canonical
# provenance record from being silently replaced by a later regeneration.
PINNED_FROZEN_RANKING_SHA256 = (
    "a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f"
)
PINNED_FREEZE_MANIFEST_SHA256 = (
    "6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea"
)

# The production forward-inference entry point plus the service functions it
# depends on.  All three must resolve to SERVICE_FILE (no reimplementation).
SERVICE_FUNCTIONS = (
    "backend/app/services/forecasting_csv_service.py::inference_forecast",
    "backend/app/services/forecasting_csv_service.py::train_parameters",
    "backend/app/services/forecasting_csv_service.py::run_forecast",
)

# Fixed, ordered frozen-ranking schema.  Ranking fields first, then constant
# provenance columns so the frozen artifact is fully self-describing.
FROZEN_COLUMNS = [
    "ticker",
    "feature_year",
    "target_year",
    "frozen_rank",
    "frozen_score",
    "confidence",
    "confidence_label",
    "signal_label",
    "eligibility_status",
    "is_inference",
    "realized_return_available",
    "protocol_identifier",
    "freeze_git_sha",
    "freeze_identifier",
    "service_source_sha256",
    "public_dataset_sha256",
    "training_dataset_sha256",
    "base_dataset_sha256",
]

ELIGIBILITY_STATUS = "eligible_for_ranking"
SEMANTIC_RANKING_COLUMNS = FROZEN_COLUMNS[:11]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_sha() -> str:
    """Repo HEAD at freeze time.  Deterministic for a given commit."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def load_service_module(repo_root: Path = ROOT) -> ModuleType:
    """Import the real backend service after applying its documented root override.

    Loads ``forecasting_csv_service`` directly from ``SERVICE_FILE`` and asserts
    that the forward-inference entry point and the two functions it depends on
    all originate in that file.  This guarantees the freeze invokes the shipped
    service, never a reimplementation.
    """
    import os

    backend = str(ROOT / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    previous = os.environ.get("RESEARCH_REPO_ROOT")
    os.environ["RESEARCH_REPO_ROOT"] = str(repo_root)
    try:
        module_name = (
            f"_financeiq_prereg_freeze_{hashlib.sha256(str(repo_root).encode()).hexdigest()[:12]}"
        )
        spec = importlib.util.spec_from_file_location(module_name, SERVICE_FILE)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load real service module from {SERVICE_FILE}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            os.environ.pop("RESEARCH_REPO_ROOT", None)
        else:
            os.environ["RESEARCH_REPO_ROOT"] = previous

    for function_name in ("inference_forecast", "train_parameters", "run_forecast"):
        function = getattr(module, function_name, None)
        source = Path(inspect.getsourcefile(function) or "").resolve() if function else None
        if function is None or source != SERVICE_FILE.resolve():
            raise RuntimeError(
                f"{TASK_ID} must invoke {SERVICE_FILE}::{function_name}; got {source}"
            )
    return module


def invoke_production_inference(service: ModuleType) -> dict[str, Any]:
    """Call the exact production forward-inference path; contains no scoring logic."""
    result = service.inference_forecast(input_year=FEATURE_YEAR, top_n=TOP_N)
    if not isinstance(result, dict):
        raise TypeError("inference_forecast must return a dict")
    if not result.get("available"):
        raise RuntimeError(
            f"Production inference for feature year {FEATURE_YEAR} is unavailable: "
            f"{result.get('reason')}"
        )
    if int(result.get("input_year", -1)) != FEATURE_YEAR:
        raise ValueError("Service input_year does not match the frozen feature year")
    if int(result.get("target_year", -1)) != TARGET_YEAR:
        raise ValueError("Service target_year does not match the frozen target year")
    if result.get("prediction_status") != "unevaluated_forward_forecast":
        raise ValueError(
            "Service prediction_status is not 'unevaluated_forward_forecast'; refusing to "
            "freeze anything that could read as an evaluated result"
        )
    return result


def build_frozen_frame(
    inference_result: dict[str, Any],
    *,
    provenance: dict[str, str],
) -> pd.DataFrame:
    """Serialize the production rankings verbatim, in production rank order.

    Ranks and order are taken exactly as the service assigned them (stable sort
    on score descending with ordinal ranks); nothing is re-sorted or re-scored.
    """
    rankings = inference_result.get("rankings")
    if not isinstance(rankings, list) or not rankings:
        raise ValueError("Production inference returned no rankings to freeze")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in rankings:
        ticker = str(item["ticker"]).strip().upper()
        if ticker in seen:
            raise ValueError(f"Production inference returned duplicate ticker {ticker!r}")
        seen.add(ticker)
        if int(item["input_year"]) != FEATURE_YEAR or int(item["target_year"]) != TARGET_YEAR:
            raise ValueError(f"Ranking row for {ticker!r} has an unexpected feature/target year")
        if bool(item["realized_return_available"]):
            raise ValueError(
                f"Ranking row for {ticker!r} claims a realized {TARGET_YEAR} outcome; the "
                "forward year must be unevaluated at freeze time"
            )
        rows.append(
            {
                "ticker": ticker,
                "feature_year": FEATURE_YEAR,
                "target_year": TARGET_YEAR,
                "frozen_rank": int(item["rank"]),
                "frozen_score": float(item["score"]),
                "confidence": float(item["confidence"]),
                "confidence_label": str(item["confidence_label"]),
                "signal_label": str(item["signal_label"]),
                "eligibility_status": ELIGIBILITY_STATUS,
                "is_inference": bool(item.get("is_inference", True)),
                "realized_return_available": bool(item["realized_return_available"]),
                "protocol_identifier": PROTOCOL_IDENTIFIER,
                "freeze_git_sha": provenance["freeze_git_sha"],
                "freeze_identifier": provenance["freeze_identifier"],
                "service_source_sha256": provenance["service_source_sha256"],
                "public_dataset_sha256": provenance["public_dataset_sha256"],
                "training_dataset_sha256": provenance["training_dataset_sha256"],
                "base_dataset_sha256": provenance["base_dataset_sha256"],
            }
        )

    frame = pd.DataFrame(rows, columns=FROZEN_COLUMNS)
    expected_ranks = list(range(1, len(frame) + 1))
    if frame["frozen_rank"].tolist() != expected_ranks:
        raise ValueError("Frozen ranks are not the contiguous 1..N production ordering")
    return frame


def _provenance() -> dict[str, str]:
    git_sha = _git_sha()
    return {
        "freeze_git_sha": git_sha,
        "freeze_identifier": f"{PROTOCOL_IDENTIFIER}:{git_sha[:12]}",
        "service_source_sha256": _sha256(SERVICE_FILE),
        "public_dataset_sha256": _sha256(PUBLIC_DATASET),
        "training_dataset_sha256": _sha256(TRAINING_DATASET),
        "base_dataset_sha256": _sha256(BASE_DATASET),
    }


def _recorded_path(path: Path) -> str:
    """Return a stable output path without embedding a machine-specific root."""
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def build_manifest(
    frame: pd.DataFrame,
    provenance: dict[str, str],
    frozen_path: Path,
    *,
    recorded_output_path: Path | None = None,
) -> dict[str, Any]:
    """Build provenance for the concrete CSV produced for this freeze request.

    ``frozen_path`` is always the file whose bytes are hashed. During an
    existing-freeze comparison it may be an isolated candidate; in that case
    ``recorded_output_path`` identifies the canonical destination without ever
    opening that destination for writing.
    """
    frozen_sha = _sha256(frozen_path)
    output_path = recorded_output_path or frozen_path
    recorded_frozen_path = _recorded_path(output_path)
    source_artifacts = [
        {
            "path": recorded_frozen_path,
            "sha256": frozen_sha,
            "role": "immutable frozen forward ranking",
        },
        {
            "path": _recorded_path(SERVICE_FILE),
            "sha256": provenance["service_source_sha256"],
            "role": "production forward-inference service invoked read-only",
        },
        {
            "path": _recorded_path(PUBLIC_DATASET),
            "sha256": provenance["public_dataset_sha256"],
            "role": "public-universe scoring input",
        },
        {
            "path": _recorded_path(TRAINING_DATASET),
            "sha256": provenance["training_dataset_sha256"],
            "role": "training-universe fitting input",
        },
        {
            "path": _recorded_path(BASE_DATASET),
            "sha256": provenance["base_dataset_sha256"],
            "role": "base modeling fallback input",
        },
    ]
    return {
        "schema_version": "1.0.0",
        "task": TASK_ID,
        "artifact_type": "pre_registration_freeze_manifest",
        "protocol_identifier": PROTOCOL_IDENTIFIER,
        "protocol_document": PROTOCOL_DOCUMENT,
        "feature_year": FEATURE_YEAR,
        "target_year": TARGET_YEAR,
        "freeze_git_sha": provenance["freeze_git_sha"],
        "freeze_identifier": provenance["freeze_identifier"],
        "reimplementation_used": False,
        "service_functions_invoked": list(SERVICE_FUNCTIONS),
        "cohort": {
            "description": (
                "Public 40-company universe rows for feature year 2025 scored by the "
                "production forward-inference path."
            ),
            "feature_year": FEATURE_YEAR,
            "target_year": TARGET_YEAR,
            "row_count": int(len(frame)),
            "eligibility_rule": (
                "Every public-universe row the production inference path scores for feature "
                "year 2025 is frozen; ranking eligibility does not depend on any future outcome."
            ),
        },
        "frozen_ranking": {
            "path": recorded_frozen_path,
            "sha256": frozen_sha,
            "row_count": int(len(frame)),
        },
        "regeneration": {
            "owner_command": REGENERATION_COMMAND,
            "hand_edit_forbidden": True,
            "immutable_after_outcome_data": True,
            "note": (
                "Regenerating this frozen ranking after any 2026 outcome data exists "
                "invalidates the pre-registration and is forbidden without an owner decision "
                "recorded as a dated amendment in docs/PREREGISTERED_2026_EVALUATION.md."
            ),
        },
        "source_artifacts": source_artifacts,
        "claim_boundary": (
            "This frozen ranking is an unevaluated forward forecast. Freezing it establishes "
            "pre-registration discipline only; it is not a prediction of returns, a "
            "recommendation, or evidence of a reliable predictive edge. The pre-registered "
            "2026 evaluation is nearly powerless by design."
        ),
        "independent_review": {
            "status": "PENDING",
            "required_reviewer": "Fable 5 in a separate context/model family from the implementer",
            "merge_ready": False,
        },
    }


def _write_frozen_csv(frame: pd.DataFrame, path: Path) -> None:
    if list(frame.columns) != FROZEN_COLUMNS:
        raise ValueError(f"frozen columns must be exactly {FROZEN_COLUMNS}")
    path.write_text(frame.to_csv(index=False, lineterminator="\n"), encoding="utf-8")


def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return (
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _refusal(reason_code: str, reason: str, **details: Any) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "freeze_refused",
        "reason_code": reason_code,
        "reason": reason,
        "artifacts_unchanged": True,
        **details,
    }


def _validate_existing_freeze(
    ranking_path: Path,
    manifest_path: Path,
    *,
    canonical: bool,
) -> dict[str, Any]:
    """Validate existing bytes and embedded provenance without mutating them."""
    ranking_sha = _sha256(ranking_path)
    manifest_sha = _sha256(manifest_path)
    if canonical and ranking_sha != PINNED_FROZEN_RANKING_SHA256:
        return _refusal(
            "pinned_frozen_ranking_checksum_mismatch",
            "Canonical frozen ranking no longer matches its independently pinned checksum.",
            expected_sha256=PINNED_FROZEN_RANKING_SHA256,
            actual_sha256=ranking_sha,
        )
    if canonical and manifest_sha != PINNED_FREEZE_MANIFEST_SHA256:
        return _refusal(
            "pinned_freeze_manifest_checksum_mismatch",
            "Canonical freeze manifest no longer matches its independently pinned checksum.",
            expected_sha256=PINNED_FREEZE_MANIFEST_SHA256,
            actual_sha256=manifest_sha,
        )
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _refusal("freeze_manifest_malformed", f"Freeze manifest is not valid JSON: {exc}")

    if manifest.get("protocol_identifier") != PROTOCOL_IDENTIFIER:
        return _refusal(
            "protocol_identifier_mismatch",
            "Existing freeze manifest carries a different protocol identifier.",
        )
    frozen_record = manifest.get("frozen_ranking")
    if not isinstance(frozen_record, dict) or frozen_record.get("sha256") != ranking_sha:
        return _refusal(
            "freeze_manifest_ranking_checksum_mismatch",
            "Existing manifest does not match the existing frozen ranking bytes.",
        )
    try:
        frame = pd.read_csv(ranking_path)
    except Exception as exc:
        return _refusal("frozen_ranking_malformed", f"Frozen ranking is not readable: {exc}")
    if list(frame.columns) != FROZEN_COLUMNS:
        return _refusal(
            "frozen_ranking_schema_mismatch",
            "Existing frozen ranking schema differs from the pre-registered schema.",
        )
    if int(frozen_record.get("row_count", -1)) != len(frame):
        return _refusal(
            "freeze_manifest_row_count_mismatch",
            "Existing manifest row count differs from the frozen ranking.",
        )
    if set(frame["protocol_identifier"].astype(str)) != {PROTOCOL_IDENTIFIER}:
        return _refusal(
            "frozen_ranking_protocol_mismatch",
            "Frozen ranking rows carry an unexpected protocol identifier.",
        )
    if set(frame["freeze_git_sha"].astype(str)) != {str(manifest.get("freeze_git_sha"))}:
        return _refusal(
            "freeze_git_sha_internal_mismatch",
            "Frozen ranking and manifest disagree about the original freeze Git SHA.",
        )

    for item in manifest.get("source_artifacts", []):
        if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
            return _refusal(
                "freeze_manifest_source_provenance_malformed",
                "Freeze manifest contains a malformed source-artifact record.",
            )
        source_path = ranking_path if item.get("role") == "immutable frozen forward ranking" else ROOT / item["path"]
        if not source_path.is_file():
            return _refusal(
                "source_artifact_missing",
                f"Recorded source artifact is missing: {item['path']}",
            )
        actual = _sha256(source_path)
        if actual != item["sha256"]:
            if source_path.resolve() == SERVICE_FILE.resolve():
                code = "service_checksum_drift"
            elif source_path.resolve() in {
                PUBLIC_DATASET.resolve(), TRAINING_DATASET.resolve(), BASE_DATASET.resolve()
            }:
                code = "source_data_checksum_drift"
            else:
                code = "source_artifact_checksum_drift"
            return _refusal(
                code,
                f"Recorded source checksum no longer matches {item['path']}.",
                expected_sha256=item["sha256"],
                actual_sha256=actual,
            )
    return {
        "ok": True,
        "manifest": manifest,
        "frame": frame,
        "ranking_sha256": ranking_sha,
        "manifest_sha256": manifest_sha,
    }


def _candidate_drift_reason(
    existing: dict[str, Any],
    candidate_frame: pd.DataFrame,
    candidate_manifest: dict[str, Any],
    candidate_csv_bytes: bytes,
    candidate_manifest_bytes: bytes,
    ranking_path: Path,
    manifest_path: Path,
) -> tuple[str, str] | None:
    recorded = existing["manifest"]
    if not existing["frame"][SEMANTIC_RANKING_COLUMNS].equals(
        candidate_frame[SEMANTIC_RANKING_COLUMNS]
    ):
        return "semantic_ranking_drift", "Candidate production ranking differs semantically."
    if recorded.get("freeze_git_sha") != candidate_manifest.get("freeze_git_sha"):
        return (
            "freeze_git_sha_drift",
            "Repository HEAD differs from the original freeze state; the recorded freeze_git_sha "
            "must remain the parent/pre-freeze repository state.",
        )
    if (
        existing["frame"]["service_source_sha256"].astype(str).iloc[0]
        != candidate_frame["service_source_sha256"].astype(str).iloc[0]
    ):
        return "service_checksum_drift", "Production service checksum differs from the freeze."
    for column in (
        "public_dataset_sha256",
        "training_dataset_sha256",
        "base_dataset_sha256",
    ):
        if existing["frame"][column].astype(str).iloc[0] != candidate_frame[column].astype(str).iloc[0]:
            return "source_data_checksum_drift", f"Candidate provenance differs in {column}."
    if ranking_path.read_bytes() != candidate_csv_bytes:
        return "candidate_csv_bytes_differ", "Candidate frozen-ranking bytes differ."
    if manifest_path.read_bytes() != candidate_manifest_bytes:
        return "candidate_manifest_bytes_differ", "Candidate freeze-manifest bytes differ."
    return None


def freeze(results_dir: Path = RESULTS_DIR) -> dict[str, Any]:
    ranking_path = results_dir / FROZEN_RANKING_PATH.name
    manifest_path = results_dir / FREEZE_MANIFEST_PATH.name
    ranking_exists = ranking_path.exists()
    manifest_exists = manifest_path.exists()
    if ranking_exists != manifest_exists:
        return _refusal(
            "partial_frozen_artifacts",
            "Exactly one frozen artifact exists; refusing to create or replace either file.",
        )

    existing: dict[str, Any] | None = None
    if ranking_exists and manifest_exists:
        existing = _validate_existing_freeze(
            ranking_path,
            manifest_path,
            canonical=results_dir.resolve() == RESULTS_DIR.resolve(),
        )
        if not existing["ok"]:
            return existing

    provenance = _provenance()
    service = load_service_module(ROOT)
    inference_result = invoke_production_inference(service)
    frame = build_frozen_frame(inference_result, provenance=provenance)

    if existing is not None:
        with tempfile.TemporaryDirectory(prefix="financeiq-prereg-candidate-") as temp_dir:
            candidate_path = Path(temp_dir) / FROZEN_RANKING_PATH.name
            _write_frozen_csv(frame, candidate_path)
            manifest = build_manifest(
                frame,
                provenance,
                candidate_path,
                recorded_output_path=ranking_path,
            )
            candidate_csv_bytes = candidate_path.read_bytes()
            candidate_manifest_bytes = _manifest_bytes(manifest)
        drift = _candidate_drift_reason(
            existing,
            frame,
            manifest,
            candidate_csv_bytes,
            candidate_manifest_bytes,
            ranking_path,
            manifest_path,
        )
        if drift is not None:
            return _refusal(drift[0], drift[1])
        return {
            "ok": True,
            "status": "already_frozen_identical",
            "artifacts_unchanged": True,
            "manifest": existing["manifest"],
        }

    results_dir.mkdir(parents=True, exist_ok=True)
    _write_frozen_csv(frame, ranking_path)
    manifest = build_manifest(frame, provenance, ranking_path)
    manifest_path.write_bytes(_manifest_bytes(manifest))
    return {
        "ok": True,
        "status": "frozen_created",
        "artifacts_unchanged": False,
        "manifest": manifest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()
    result = freeze(results_dir=args.results_dir)
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
