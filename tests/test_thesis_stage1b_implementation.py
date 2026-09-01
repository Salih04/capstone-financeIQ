"""Implementation-phase guards for the Stage 1b calibration runner.

These tests prove the governed Stage 1b apparatus is wired *before* it runs:
the runner exists and is inert on import, the registered scientific contract is
implemented literally, the governance wiring is complete, and the scientific
result root is still absent because no governed run has happened.

Nothing here executes the 6 x 400 experiment, inspects a Stage 1b outcome, or
creates ``experiments/results_thesis/positive_control_calibration/``. Where a
test needs records or a report, it fabricates obviously synthetic values: they
exercise schema and integrity machinery and are not measurements of anything.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import run_experiments as rx
from experiments import significance as sig
from experiments.placebo_lab import validate_claim_safety_text
from experiments.thesis import positive_control as stage1
from experiments.thesis import positive_control_calibration as pcc
from experiments.thesis import provenance as prov
from experiments.thesis import stage1b_registration as reg

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "experiments/thesis/positive_control_calibration.py"
STAGE_1B_OUTPUT_DIR = REPO_ROOT / reg.STAGE_1B_RESULT_ROOT.rstrip("/")
STAGE_1_OUTPUT_ROOT = REPO_ROOT / "experiments/results_thesis/positive_control"
STAGE_1_IMPLEMENTATION = REPO_ROOT / "experiments/thesis/positive_control.py"
MAKEFILE = REPO_ROOT / "Makefile"
REGISTRY = REPO_ROOT / "artifact_registry.json"


def stage1b_result_root_snapshot() -> dict:
    """A structural snapshot of the completed Stage 1b result root.

    POST-RUN, inertness of an import / no-op CLI / ``registered_plan()`` call is
    SNAPSHOT-UNCHANGED, not result-root absence. The snapshot binds the file
    inventory, every artifact hash, and the absence of ``.staging``. Empty inventory
    when the root does not exist.
    """
    root = STAGE_1B_OUTPUT_DIR
    files: dict[str, str] = {}
    dirs: list[str] = []
    if root.exists():
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root).as_posix()
            if path.is_file():
                files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
            elif path.is_dir():
                dirs.append(rel)
    return {
        "exists": root.exists(),
        "files": files,
        "dirs": dirs,
        "staging": (root / pcc.STAGING_DIRNAME).exists(),
    }


@pytest.fixture(scope="module")
def source() -> str:
    return RUNNER_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def makefile() -> str:
    return MAKEFILE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Synthetic fixtures. Every number below is invented by the test; none of it is
# a Stage 1b measurement, and none of it is ever written to the result root.
# --------------------------------------------------------------------------- #
def _all_keys(payload: object) -> set[str]:
    """Every mapping key anywhere in a nested structure."""
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.add(str(key))
            keys |= _all_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            keys |= _all_keys(item)
    return keys


def _fake_record(theta: float, repetition: int, *, p_raw: float = 0.5) -> dict:
    """One structurally valid record with obviously synthetic values."""
    checkpoints = {
        "ic_injected": theta,
        "ic_raw_carrier": 0.111111111111,
        "ic_panel_carrier": 0.111111111111,
        "ic_model_input_carrier": 0.111111111111,
        "ic_model_prediction": 0.222222222222,
        "ic_final_evaluation": 0.222222222222,
    }
    return {
        "carrier": pcc.CARRIER,
        "model": pcc.PRIMARY_MODEL,
        "ic_injected": pcc._rounded(theta),
        "level_index": pcc.level_index_for(theta),
        "repetition": repetition,
        "injection_seed": pcc.injection_seed_for(theta, repetition),
        "permutation_seed": pcc.permutation_seed_for(repetition),
        "injected_dataset_sha256": "0" * 64,
        "checkpoints": checkpoints,
        "checkpoint_n": {name: 240 for name, _ in stage1.CHECKPOINTS},
        "permutation_p_value_two_sided": pcc._rounded(p_raw),
        "stage1_operating_point_p_value": pcc._rounded(pcc.operating_point_p_value(p_raw)),
        "detected_stage1_rule": pcc.detected_by_stage1_rule(p_raw),
        "detected_raw_p05": pcc.detected_by_raw_p(p_raw),
        "bootstrap_ci_95": [-0.1, 0.3],
        "mechanism_invariants": {
            "carrier_observed_value_multiset_preserved_within_year": True,
            "carrier_missingness_mask_preserved": True,
            "targets_unchanged": True,
            "non_carrier_features_unchanged": True,
            "carrier_reaches_model_input": True,
            "identity_checkpoint_ics_agree": True,
            "ridge_prediction_ic_equals_final_evaluation_ic": True,
        },
    }


@pytest.fixture(scope="module")
def fake_records() -> list[dict]:
    return [
        _fake_record(theta, repetition)
        for theta in pcc.IC_GRID
        for repetition in pcc.REPETITION_IDS
    ]


@pytest.fixture(scope="module")
def fake_curve(fake_records: list[dict]) -> list[dict]:
    return pcc.calibration_curve(fake_records)


def _integrity_kwargs(records: list[dict], curve: list[dict], **overrides) -> dict:
    root = reg.STAGE_1B_RESULT_ROOT.rstrip("/")
    kwargs = {
        "records": records,
        "curve": curve,
        "levels": pcc.IC_GRID,
        "repetition_ids": pcc.REPETITION_IDS,
        "registered_source_sha": reg.DATASET_SHA256,
        "source_sha_before": reg.DATASET_SHA256,
        "source_sha_after": reg.DATASET_SHA256,
        "protected_digest_before": {"data/trusted_clean/x.csv": "a" * 64},
        "protected_digest_after": {"data/trusted_clean/x.csv": "a" * 64},
        "stage1_digest_before": {"experiments/results_thesis/positive_control/y.csv": "b" * 64},
        "stage1_digest_after": {"experiments/results_thesis/positive_control/y.csv": "b" * 64},
        "output_root": root,
        "output_paths": [f"{root}/{name}" for name in pcc.EMITTED_FILENAMES],
        "pipeline_source_restored": True,
        "replay_probe": {
            "ic_injected": 0.0,
            "repetition": 200,
            "identical": True,
            "digest": "c" * 64,
        },
    }
    kwargs.update(overrides)
    return kwargs


def _synthetic_raw(rows_per_year: int = 40, seed: int = 5) -> pd.DataFrame:
    """A tiny table shaped like the modeling CSV, with no real data in it."""
    rng = np.random.default_rng(seed)
    frames = []
    for year in (2022, 2023, 2024):
        values = rng.normal(size=rows_per_year)
        values[: rows_per_year // 10] = np.nan  # keep a missingness mask to preserve
        frames.append(
            pd.DataFrame(
                {
                    "ticker": [f"T{index:03d}" for index in range(rows_per_year)],
                    "year": year,
                    pcc.CARRIER: values,
                    "other": rng.normal(size=rows_per_year),
                    pcc.TARGET_COLUMN: rng.normal(size=rows_per_year),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


# --------------------------------------------------------------------------- #
# 1 / 24. Import is inert; nothing is created and nothing is mutated
# --------------------------------------------------------------------------- #
def test_importing_the_runner_creates_nothing_and_mutates_nothing():
    """Importing the runner and calling ``registered_plan()`` execute nothing.

    POST-RUN, inertness is SNAPSHOT-UNCHANGED: the modeling dataset, the completed
    Stage 1b artifact inventory and hashes, and the absence of ``.staging`` are all
    left exactly as found. ``registered_plan()['executed']`` is False because this
    process did not run Stage 1b — not because Stage 1b has never run.
    """
    dataset = REPO_ROOT / reg.DATASET_PATH
    before = hashlib.sha256(dataset.read_bytes()).hexdigest()
    assert before == reg.DATASET_SHA256
    snapshot_before = stage1b_result_root_snapshot()
    script = (
        "import hashlib, json, pathlib\n"
        f"dataset = pathlib.Path({str(dataset)!r})\n"
        f"root = pathlib.Path({str(STAGE_1B_OUTPUT_DIR)!r})\n"
        "def snap():\n"
        "    files, dirs = {}, []\n"
        "    if root.exists():\n"
        "        for p in sorted(root.rglob('*')):\n"
        "            rel = p.relative_to(root).as_posix()\n"
        "            if p.is_file():\n"
        "                files[rel] = hashlib.sha256(p.read_bytes()).hexdigest()\n"
        "            elif p.is_dir():\n"
        "                dirs.append(rel)\n"
        "    return {'exists': root.exists(), 'files': files, 'dirs': dirs,\n"
        "            'staging': (root / '.staging').exists()}\n"
        "before = hashlib.sha256(dataset.read_bytes()).hexdigest()\n"
        "snap_before = snap()\n"
        "import experiments.thesis.positive_control_calibration as pcc\n"
        "after = hashlib.sha256(dataset.read_bytes()).hexdigest()\n"
        "assert after == before, 'import mutated the modeling dataset'\n"
        "assert snap() == snap_before, 'import changed the Stage 1b result root'\n"
        "plan = pcc.registered_plan()\n"
        "assert plan['executed'] is False\n"
        "assert snap() == snap_before, 'registered_plan() changed the Stage 1b result root'\n"
        "assert not (root / '.staging').exists()\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    assert hashlib.sha256(dataset.read_bytes()).hexdigest() == before
    assert stage1b_result_root_snapshot() == snapshot_before
    assert not (STAGE_1B_OUTPUT_DIR / pcc.STAGING_DIRNAME).exists()


def test_cli_without_an_explicit_run_flag_executes_nothing():
    """Normal verification cannot trip the governed run: --run is mandatory.

    POST-RUN this is snapshot-unchanged inertness — the CLI without ``--run`` still
    returns ``executed=False`` and leaves the completed result root byte-for-byte
    as it found it.
    """
    snapshot_before = stage1b_result_root_snapshot()
    result = subprocess.run(
        [sys.executable, "-m", "experiments.thesis.positive_control_calibration"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": str(REPO_ROOT), "PATH": "/usr/bin:/bin"},
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["executed"] is False
    assert payload["experiment"] == reg.STAGE_1B_SLUG
    assert stage1b_result_root_snapshot() == snapshot_before
    assert not (STAGE_1B_OUTPUT_DIR / pcc.STAGING_DIRNAME).exists()


# --------------------------------------------------------------------------- #
# 2 / 6 / 23. Namespace: registered slug, distinct from Stage 1, now populated
# --------------------------------------------------------------------------- #
def test_runner_points_at_the_registered_slug_and_root():
    assert pcc.SLUG == reg.STAGE_1B_SLUG == "positive_control_calibration"
    assert pcc.RESULT_ROOT == STAGE_1B_OUTPUT_DIR
    assert pcc.RESULT_ROOT.relative_to(REPO_ROOT).as_posix() + "/" == reg.STAGE_1B_RESULT_ROOT
    assert prov.output_dir(pcc.SLUG, create=False) == pcc.RESULT_ROOT
    assert prov.seed_for(pcc.SLUG) == pcc.BASE_SEED == reg.BASE_SEED == 42
    # POST-RUN: the runner's registered root now holds the completed governed run.
    assert STAGE_1B_OUTPUT_DIR.is_dir()
    assert (STAGE_1B_OUTPUT_DIR / pcc.MANIFEST_FILENAME).is_file()


def test_stage1_root_stays_distinct_and_is_never_a_stage1b_target():
    assert pcc.STAGE_1_RESULT_ROOT != pcc.RESULT_ROOT
    assert pcc.STAGE_1_RESULT_ROOT == STAGE_1_OUTPUT_ROOT
    assert STAGE_1_OUTPUT_ROOT.is_dir()
    root = reg.STAGE_1B_RESULT_ROOT.rstrip("/")
    assert not root.startswith("experiments/results_thesis/positive_control/")
    assert root != "experiments/results_thesis/positive_control"


def test_result_root_is_complete_after_the_governed_run():
    """POST-RUN completion guard (replaces the pre-run absence guard).

    Lifecycle/completion state only: root existence, manifest existence, contract
    location, file inventory, ``.staging`` absence. No scientific quantity is
    inspected. ``RESULT_ROOT_EXISTS_AT_REGISTRATION`` stays False as a historical
    registration fact; the current filesystem carries the completed run.
    """
    assert reg.RESULT_ROOT_EXISTS_AT_REGISTRATION is False
    assert STAGE_1B_OUTPUT_DIR.is_dir()
    assert (STAGE_1B_OUTPUT_DIR / pcc.MANIFEST_FILENAME).is_file()
    assert not (STAGE_1B_OUTPUT_DIR / pcc.STAGING_DIRNAME).exists()

    # Exactly the expected persistent surface, recursively: five scientific
    # outputs (pcc.EMITTED_FILENAMES) plus the one operational attempt marker.
    # No unexpected persistent file, no unexpected directory.
    files = {
        path.relative_to(STAGE_1B_OUTPUT_DIR).as_posix()
        for path in STAGE_1B_OUTPUT_DIR.rglob("*")
        if path.is_file()
    }
    subdirs = [path for path in STAGE_1B_OUTPUT_DIR.rglob("*") if path.is_dir()]
    assert files == set(pcc.EMITTED_FILENAMES) | set(pcc.OPERATIONAL_FILENAMES)
    assert subdirs == []

    # The five scientific outputs remain exactly five; attempt_provenance.json is
    # operational, not a sixth scientific endpoint. artifact_manifest.json stays
    # the completion authority.
    assert len(pcc.EMITTED_FILENAMES) == 5
    assert pcc.OPERATIONAL_FILENAMES == ("attempt_provenance.json",)
    assert "attempt_provenance.json" not in pcc.EMITTED_FILENAMES
    assert pcc.MANIFEST_FILENAME in pcc.EMITTED_FILENAMES


# --------------------------------------------------------------------------- #
# Attempt lifecycle and transactional output safety
# --------------------------------------------------------------------------- #
def test_normal_run_refuses_any_existing_non_empty_root(tmp_path, monkeypatch):
    root = tmp_path / "positive_control_calibration"
    root.mkdir()
    (root / "partial.txt").write_text("incomplete", encoding="utf-8")
    monkeypatch.setattr(pcc, "RESULT_ROOT", root)

    with pytest.raises(pcc.Stage1bError, match="pre-existing non-empty"):
        pcc._prepare_attempt(repeat_after_crash=False)


def test_normal_run_refuses_an_incomplete_prior_attempt_and_requires_recovery_flag(
    tmp_path, monkeypatch
):
    root = tmp_path / "positive_control_calibration"
    monkeypatch.setattr(pcc, "RESULT_ROOT", root)
    _, marker, _, _ = pcc._prepare_attempt(repeat_after_crash=False)
    assert marker.is_file()

    with pytest.raises(pcc.Stage1bError, match="repeat-after-crash"):
        pcc._prepare_attempt(repeat_after_crash=False)


def test_crash_recovery_records_both_attempts_and_preserves_registered_identity(
    tmp_path, monkeypatch
):
    root = tmp_path / "positive_control_calibration"
    monkeypatch.setattr(pcc, "RESULT_ROOT", root)
    _, marker, first, first_number = pcc._prepare_attempt(repeat_after_crash=False)
    (root / pcc.STAGING_DIRNAME).mkdir()
    (root / pcc.STAGING_DIRNAME / "leftover.tmp").write_text("partial", encoding="utf-8")

    _, recovered_marker, second, second_number = pcc._prepare_attempt(
        repeat_after_crash=True
    )
    assert recovered_marker == marker
    assert first_number == 1 and second_number == 2
    assert [attempt["attempt_type"] for attempt in second["attempts"]] == [
        "initial",
        "crash_recovery",
    ]
    assert second["attempts"][0]["completion_status"] == "incomplete"
    assert second["attempts"][1]["prior_attempt_incomplete"] is True
    assert second["attempts"][1]["completion_status"] == "in_progress"
    assert second["registered_configuration_sha256"] == first[
        "registered_configuration_sha256"
    ] == pcc.registered_configuration_digest()
    assert second["registered_configuration"]["seed_schedule_sha256"] == first[
        "registered_configuration"
    ]["seed_schedule_sha256"]
    assert not (root / pcc.STAGING_DIRNAME).exists()


def test_crash_recovery_refuses_a_completed_run(tmp_path, monkeypatch):
    root = tmp_path / "positive_control_calibration"
    monkeypatch.setattr(pcc, "RESULT_ROOT", root)
    _, marker, payload, number = pcc._prepare_attempt(repeat_after_crash=False)
    payload = pcc._set_attempt_status(marker, payload, number, "complete")
    for name in pcc.EMITTED_FILENAMES:
        if name != pcc.MANIFEST_FILENAME:
            (root / name).write_text("fixture", encoding="utf-8")
    (root / pcc.MANIFEST_FILENAME).write_text(
        json.dumps(
            {
                "experiment": pcc.SLUG,
                "completion_status": "complete",
                "completion_authority": pcc.MANIFEST_FILENAME,
                "integrity_passed": True,
                "operational_attempt_provenance": {
                    "path": marker.resolve().as_posix(),
                    "sha256": prov.sha256_path(marker),
                },
            }
        ),
        encoding="utf-8",
    )
    assert pcc._is_complete_run(root)

    with pytest.raises(pcc.Stage1bError, match="complete"):
        pcc._prepare_attempt(repeat_after_crash=True)


def test_failure_during_scientific_write_cannot_create_completion_evidence(tmp_path, monkeypatch):
    staging = tmp_path / pcc.STAGING_DIRNAME / "attempt-1"
    report = {"experiment": pcc.SLUG}
    markdown = "Stage 1b apparatus characterization on synthetic input."
    original_write_text = Path.write_text

    def fail_on_markdown(self, data, *args, **kwargs):
        if self.name == pcc.OUTPUT_FILENAMES["report_md"]:
            raise OSError("simulated interrupted scientific write")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_on_markdown)
    with pytest.raises(OSError, match="interrupted"):
        pcc._write_scientific_artifacts(
            staging,
            report=report,
            markdown=markdown,
            records=[],
            curve=[],
        )
    assert not (tmp_path / pcc.MANIFEST_FILENAME).exists()
    assert not (staging / pcc.MANIFEST_FILENAME).exists()


def test_filesystem_backed_output_audit_requires_exact_recursive_surface(tmp_path):
    surface = tmp_path / "attempt-1"
    surface.mkdir()
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (surface / name).write_text("fixture", encoding="utf-8")
    clean = pcc._audit_output_surface(
        surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES
    )
    assert clean["passed"] is True
    assert set(clean["actual_scientific_files"]) == set(pcc.SCIENTIFIC_EMITTED_FILENAMES)

    nested = surface / "unexpected"
    nested.mkdir()
    (nested / "hidden.txt").write_text("unexpected", encoding="utf-8")
    contaminated = pcc._audit_output_surface(
        surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES
    )
    assert contaminated["passed"] is False
    assert "unexpected/hidden.txt" in contaminated["unexpected_files"]
    assert "unexpected" in contaminated["unexpected_directories"]


def test_output_confinement_integrity_uses_actual_audit_and_detects_extra_files(
    tmp_path, fake_records, fake_curve
):
    surface = tmp_path / "attempt-1"
    surface.mkdir()
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (surface / name).write_text("fixture", encoding="utf-8")
    audit = pcc._audit_output_surface(
        surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES
    )
    paths = [
        f"{reg.STAGE_1B_RESULT_ROOT.rstrip('/')}/.staging/attempt-1/{name}"
        for name in pcc.SCIENTIFIC_EMITTED_FILENAMES
    ]
    result = pcc.evaluate_integrity(
        **_integrity_kwargs(fake_records, fake_curve, output_paths=paths, output_audit=audit)
    )
    assert result["passed"] is True

    (surface / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    audit = pcc._audit_output_surface(
        surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES
    )
    result = pcc.evaluate_integrity(
        **_integrity_kwargs(fake_records, fake_curve, output_paths=paths, output_audit=audit)
    )
    assert "Stage 1b writes only to its isolated namespace" in result["failures"]

    result = pcc.evaluate_integrity(
        **_integrity_kwargs(
            fake_records,
            fake_curve,
            output_paths=paths,
            output_audit=pcc._audit_output_surface(
                surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES
            ),
            workspace_digest_before={"outside.txt": "a"},
            workspace_digest_after={"outside.txt": "b"},
        )
    )
    assert "Stage 1b writes only to its isolated namespace" in result["failures"]


def test_run_signature_has_only_operational_lifecycle_controls():
    assert set(inspect.signature(pcc.run).parameters) == {
        "progress",
        "repeat_after_crash",
    }
    assert inspect.signature(pcc.run_grid).parameters["levels"].default == pcc.IC_GRID
    assert inspect.signature(pcc.run_grid).parameters["repetition_ids"].default == pcc.REPETITION_IDS
    assert inspect.signature(pcc.run_grid).parameters["permutations"].default == pcc.PERMUTATIONS
    assert inspect.signature(pcc.run_grid).parameters["bootstraps"].default == pcc.BOOTSTRAPS
    assert inspect.signature(pcc._replay_probe).parameters["permutations"].default == pcc.PERMUTATIONS
    assert inspect.signature(pcc._replay_probe).parameters["bootstraps"].default == pcc.BOOTSTRAPS


def test_governed_run_pins_integrity_claim_safety_promotion_and_manifest_order(source):
    lines = source.splitlines()
    tree = ast.parse(source)
    run_node = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_run_attempt")
    run_source = "\n".join(lines[run_node.lineno - 1 : run_node.end_lineno])
    preflight = run_source.index("preflight_integrity = evaluate_integrity")
    first_stage_write = run_source.index("_write_scientific_artifacts(")
    actual_integrity = run_source.index("integrity = evaluate_integrity", first_stage_write)
    claim_safety = run_source.index("validate_claim_safety_text(markdown)", actual_integrity)
    promotion = run_source.index("_promote_scientific_artifacts")
    manifest = run_source.index("_write_final_manifest")
    assert preflight < first_stage_write < actual_integrity < claim_safety < promotion < manifest
    assert run_source.count("_write_final_manifest") == 1
    assert run_source.index("_set_attempt_status") < manifest
    assert run_source.rfind("write_text") < manifest

    # The governed orchestration invokes registered defaults and the full probe;
    # reduced settings are available only to explicit, non-governed helpers.
    run_grid_call = next(
        node
        for node in ast.walk(run_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_grid"
    )
    assert [keyword.arg for keyword in run_grid_call.keywords] == ["progress"]
    replay_call = next(
        node
        for node in ast.walk(run_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_replay_probe"
    )
    assert replay_call.keywords == []
    assert "break" not in run_source
    assert "adaptive" not in run_source.lower()


def test_stage1b_wrapper_discards_all_unregistered_stage1_fields():
    source = RUNNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "run_repetition"
    )
    allowed = {
        "injected_dataset_sha256",
        "checkpoints",
        "checkpoint_n",
        "permutation_p_value_two_sided",
        "bootstrap_ci_95",
    }
    accessed = set()
    for node in ast.walk(function):
        if not isinstance(node, ast.Subscript) or not isinstance(node.value, ast.Name):
            continue
        if node.value.id != "base":
            continue
        key = node.slice.value if isinstance(node.slice, ast.Constant) else None
        assert isinstance(key, str), "Stage 1 base access must name a safe field literally"
        accessed.add(key)
    assert accessed == allowed

    # No splat of ``base`` in any of the three Python forms may reach a Stage 1b
    # structure. ``ast.Starred`` alone misses ``{**base}`` and ``f(**base)``, so
    # dict-splat (ast.Dict key None) and keyword-splat (ast.keyword arg None) are
    # checked explicitly as well.
    for node in ast.walk(function):
        if isinstance(node, ast.Starred):
            assert not (
                isinstance(node.value, ast.Name) and node.value.id == "base"
            ), "base must never be iterable-splatted (*base) into Stage 1b output"
        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                assert not (
                    key is None
                    and isinstance(value, ast.Name)
                    and value.id == "base"
                ), "base must never be dict-splatted ({**base}) into Stage 1b output"
        if isinstance(node, ast.Call):
            for keyword in node.keywords:
                assert not (
                    keyword.arg is None
                    and isinstance(keyword.value, ast.Name)
                    and keyword.value.id == "base"
                ), "base must never be keyword-splatted (**base) into a Stage 1b call"
    literals = {
        node.value
        for node in ast.walk(function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    for forbidden in (
        "bonferroni_adjusted_p_value",
        "attenuation_ratio",
        "stagewise_ratio",
        "confirmatory_gate",
        "gate_informativeness",
    ):
        assert forbidden not in literals


# --------------------------------------------------------------------------- #
# C1 / H1 / M-b. Executed promotion, .staging teardown, and OS-metadata policy
# --------------------------------------------------------------------------- #
def test_executed_promotion_removes_attempt_and_staging_parent_then_passes_root_audit(
    tmp_path,
):
    """C1 regression: promotion must delete attempt-N *and* the empty ``.staging``
    parent, so the real post-promotion root audit sees no unexpected directory.

    Fails on the pre-fix implementation, which called ``staging.rmdir()`` only and
    left an empty ``.staging`` behind — enough for ``_audit_output_surface`` to
    report an unexpected directory and block the manifest forever.
    """
    root = tmp_path / "positive_control_calibration"
    root.mkdir()
    staging_parent = root / pcc.STAGING_DIRNAME
    staging = staging_parent / "attempt-1"
    staging.mkdir(parents=True)
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (staging / name).write_text("fabricated scientific fixture", encoding="utf-8")
    # An operational marker already sits in the real root, as it would at runtime.
    (root / pcc.ATTEMPT_MARKER_FILENAME).write_text("{}", encoding="utf-8")

    pcc._promote_scientific_artifacts(root, staging)

    assert not staging.exists()
    assert not staging_parent.exists()
    assert not any(child.is_dir() for child in root.rglob("*"))
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        assert (root / name).is_file()

    audit = pcc._audit_output_surface(
        root,
        expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES,
        operational_names=pcc.OPERATIONAL_FILENAMES,
    )
    assert audit["passed"] is True
    assert audit["unexpected_files"] == []
    assert audit["unexpected_directories"] == []
    assert set(audit["actual_scientific_files"]) == set(pcc.SCIENTIFIC_EMITTED_FILENAMES)


def test_promotion_fails_closed_on_unknown_staging_content(tmp_path):
    """A successful first-run completion never silently deletes unknown content."""
    root = tmp_path / "positive_control_calibration"
    root.mkdir()
    staging = root / pcc.STAGING_DIRNAME / "attempt-1"
    staging.mkdir(parents=True)
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (staging / name).write_text("fixture", encoding="utf-8")
    (staging / "surprise.txt").write_text("not a scientific output", encoding="utf-8")

    with pytest.raises(pcc.Stage1bIntegrityError, match="not empty after promotion"):
        pcc._promote_scientific_artifacts(root, staging)
    assert (staging / "surprise.txt").exists()


def test_ds_store_policy_is_exactly_one_immutable_filename():
    assert pcc.IGNORABLE_OS_METADATA == frozenset({".DS_Store"})
    assert isinstance(pcc.IGNORABLE_OS_METADATA, frozenset)


def test_purge_os_metadata_removes_only_ds_store_inside_the_surface(tmp_path):
    sibling = tmp_path / ".DS_Store"
    sibling.write_bytes(b"Bud1")
    surface = tmp_path / "positive_control_calibration"
    (surface / "sub").mkdir(parents=True)
    (surface / ".DS_Store").write_bytes(b"Bud1")
    (surface / "sub" / ".DS_Store").write_bytes(b"Bud1")
    (surface / "keep.txt").write_text("keep", encoding="utf-8")

    pcc._purge_os_metadata(surface)

    assert not (surface / ".DS_Store").exists()
    assert not (surface / "sub" / ".DS_Store").exists()
    assert (surface / "sub").is_dir()
    assert (surface / "keep.txt").is_file()
    assert sibling.exists(), "must never touch anything outside the surface"


def test_incomplete_root_cleanup_tolerates_a_ds_store(tmp_path, monkeypatch):
    """M-b/A: a Finder ``.DS_Store`` must not make --repeat-after-crash impossible."""
    root = tmp_path / "positive_control_calibration"
    monkeypatch.setattr(pcc, "RESULT_ROOT", root)
    _, marker, _, _ = pcc._prepare_attempt(repeat_after_crash=False)
    (root / ".DS_Store").write_bytes(b"Bud1")
    (root / pcc.OUTPUT_FILENAMES["repetitions"]).write_text("partial", encoding="utf-8")

    pcc._cleanup_incomplete_root(root)

    assert not (root / ".DS_Store").exists()
    assert not (root / pcc.OUTPUT_FILENAMES["repetitions"]).exists()
    assert (root / pcc.ATTEMPT_MARKER_FILENAME).is_file()


def test_incomplete_root_cleanup_still_fails_closed_on_other_junk(tmp_path, monkeypatch):
    for junk in (".junk", "unexpected.txt"):
        root = tmp_path / f"root-{junk}"
        monkeypatch.setattr(pcc, "RESULT_ROOT", root)
        pcc._prepare_attempt(repeat_after_crash=False)
        (root / junk).write_text("nope", encoding="utf-8")
        with pytest.raises(pcc.Stage1bError, match="unrecognized path"):
            pcc._cleanup_incomplete_root(root)


def test_output_audit_ignores_a_ds_store_but_still_flags_other_files(tmp_path):
    """M-b/B, C, D: only ``.DS_Store`` is tolerated; every other extra still fails."""
    surface = tmp_path / "attempt-1"
    surface.mkdir()
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (surface / name).write_text("fixture", encoding="utf-8")

    (surface / ".DS_Store").write_bytes(b"Bud1")
    clean = pcc._audit_output_surface(surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES)
    assert clean["passed"] is True
    assert ".DS_Store" not in clean["actual_files"]
    assert ".DS_Store" not in clean["actual_direct_files"]

    # C: an arbitrary unknown *hidden* file still fails confinement.
    (surface / ".junk").write_text("nope", encoding="utf-8")
    hidden = pcc._audit_output_surface(surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES)
    assert hidden["passed"] is False
    assert ".junk" in hidden["unexpected_files"]
    (surface / ".junk").unlink()

    # D: an arbitrary unexpected normal file still fails confinement.
    (surface / "unexpected.txt").write_text("nope", encoding="utf-8")
    normal = pcc._audit_output_surface(surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES)
    assert normal["passed"] is False
    assert "unexpected.txt" in normal["unexpected_files"]


def test_output_audit_detects_unexpected_nested_file_recursively(tmp_path):
    """Recursive confinement: nested content and its directory both fail closed,
    and a ``.DS_Store`` inside an unexpected directory does not rescue it."""
    surface = tmp_path / "attempt-1"
    surface.mkdir()
    for name in pcc.SCIENTIFIC_EMITTED_FILENAMES:
        (surface / name).write_text("fixture", encoding="utf-8")
    nested = surface / "unexpected_dir"
    nested.mkdir()
    (nested / "evil.txt").write_text("boom", encoding="utf-8")

    audit = pcc._audit_output_surface(surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES)
    assert audit["passed"] is False
    assert "unexpected_dir/evil.txt" in audit["unexpected_files"]
    assert "unexpected_dir" in audit["unexpected_directories"]

    (nested / ".DS_Store").write_bytes(b"Bud1")
    audit = pcc._audit_output_surface(surface, expected_names=pcc.SCIENTIFIC_EMITTED_FILENAMES)
    assert audit["passed"] is False
    assert "unexpected_dir" in audit["unexpected_directories"]


# --------------------------------------------------------------------------- #
# 3 / 4 / 5. Governance wiring
# --------------------------------------------------------------------------- #
def test_result_root_is_registered_in_governed_roots(registry):
    assert reg.STAGE_1B_RESULT_ROOT.rstrip("/") in registry["governed_roots"]
    assert "experiments/results_thesis/positive_control" in registry["governed_roots"]


def test_make_target_exists_and_requires_the_explicit_run_flag(makefile):
    assert "thesis-stage1b:" in makefile
    assert (
        "PYTHONPATH=. python experiments/thesis/positive_control_calibration.py --run"
        in makefile
    )
    assert "thesis-stage1b-replay:" in makefile
    assert (
        "PYTHONPATH=. python experiments/thesis/positive_control_calibration.py --replay-check"
        in makefile
    )
    phony = makefile.split("\n\n", 1)[0]
    assert "thesis-stage1b" in phony and "thesis-stage1b-replay" in phony


def test_artifact_contracts_cover_every_emitted_file(registry):
    """Scientific outputs and operational marker each have frozen contracts.

    POST-RUN: the six frozen ownership contracts now live in entries[] (entries[]
    requires a real file on disk) and none remains in prospective_entries[]. The
    contract dictionaries are still exactly the preregistered ones — the registry
    transition machinery (tests/test_artifact_registry.py) forbids any mutation on
    the move.
    """
    root = reg.STAGE_1B_RESULT_ROOT.rstrip("/")
    contracts = [
        entry
        for entry in registry["entries"]
        if entry["path_or_glob"].startswith(root + "/")
    ]
    assert not any(
        entry["path_or_glob"].startswith(root)
        for entry in registry.get("prospective_entries", [])
    )
    # No duplicate ownership within the Stage 1b root.
    patterns = [entry["path_or_glob"] for entry in contracts]
    assert len(patterns) == len(set(patterns))
    # No orphan governed output: every persistent file on disk is a contract.
    on_disk = {
        f"{root}/{path.relative_to(STAGE_1B_OUTPUT_DIR).as_posix()}"
        for path in STAGE_1B_OUTPUT_DIR.rglob("*")
        if path.is_file()
    }
    assert on_disk == set(patterns)
    scientific = [
        entry for entry in contracts if entry["path_or_glob"].rsplit("/", 1)[-1] in pcc.EMITTED_FILENAMES
    ]
    operational = [
        entry for entry in contracts if entry["path_or_glob"].rsplit("/", 1)[-1] in pcc.OPERATIONAL_FILENAMES
    ]
    assert {entry["path_or_glob"] for entry in scientific} == {
        f"{root}/{name}" for name in pcc.EMITTED_FILENAMES
    }
    assert {entry["path_or_glob"] for entry in operational} == {
        f"{root}/{name}" for name in pcc.OPERATIONAL_FILENAMES
    }
    assert len(contracts) == len(pcc.EMITTED_FILENAMES) + len(pcc.OPERATIONAL_FILENAMES)
    required_fields = {
        "path_or_glob",
        "artifact_class",
        "generator_command",
        "inputs",
        "hand_edit_forbidden",
        "notes",
    }
    for entry in contracts:
        assert set(entry) == required_fields, entry
        assert entry["artifact_class"] == "generated"
        assert entry["generator_command"] == "make thesis-stage1b"
        assert entry["hand_edit_forbidden"] is True
        if entry in scientific:
            assert entry["inputs"] == [reg.DATASET_PATH]
        else:
            assert entry["inputs"] == []
            assert "operational" in entry["notes"].lower()
        assert entry["notes"].strip()


def test_stage1b_outputs_are_owned_by_entries_after_the_run(registry):
    """Every emitted name is owned by entries[], and none stays prospective.

    entries[] requires a real file on disk. Pre-run the ownership lived in
    prospective_entries[]; the governed-run commit moved every Stage 1b contract
    across verbatim. The rule that governs that move is stated in the registry
    itself and its wording is unchanged.
    """
    root = reg.STAGE_1B_RESULT_ROOT.rstrip("/")
    owned = {
        entry["path_or_glob"]
        for entry in registry["entries"]
        if entry["path_or_glob"].startswith(root)
    }
    assert owned == {
        f"{root}/{name}"
        for name in set(pcc.EMITTED_FILENAMES) | set(pcc.OPERATIONAL_FILENAMES)
    }
    assert not any(
        entry["path_or_glob"].startswith(root)
        for entry in registry.get("prospective_entries", [])
    )
    assert "prospective_entry_rule" in registry
    rule = registry["prospective_entry_rule"]
    assert "verbatim into entries[]" in rule
    assert "coverage_rule" in rule
    assert "prospective_entries[]" in registry["artifact_class_definitions"]["proposed_future"]


def test_emitted_filenames_match_what_the_runner_actually_writes(source):
    """The frozen emitted set is the union of the writers, not a hand list."""
    assert set(pcc.EMITTED_FILENAMES) == set(pcc.OUTPUT_FILENAMES.values()) | {
        pcc.MANIFEST_FILENAME
    }
    assert pcc.EMITTED_FILENAMES == tuple(sorted(pcc.EMITTED_FILENAMES))
    for name in pcc.OUTPUT_FILENAMES.values():
        assert f'"{name}"' in source
    # provenance.write_manifest owns the manifest name.
    assert pcc.MANIFEST_FILENAME == "artifact_manifest.json"


# --------------------------------------------------------------------------- #
# 7 / 8 / 9 / 10 / 16. The registered scope, implemented literally
# --------------------------------------------------------------------------- #
def test_primary_arm_is_equity_only():
    assert pcc.CARRIER == reg.CARRIER == "equity"
    assert reg.STAGE_1B_CARRIERS == ("equity",)
    assert pcc.registered_plan()["carrier"] == "equity"


def test_exact_grid_and_report_order():
    assert pcc.IC_GRID == reg.IC_GRID == (0.00, 0.10, 0.20, 0.30, 0.35, 0.40)
    assert list(pcc.IC_GRID) == sorted(pcc.IC_GRID), "report order is numeric"
    assert len(pcc.IC_GRID) == 6


def test_exact_repetition_count_and_ids():
    assert pcc.REPETITIONS == reg.REPETITIONS == 400
    assert pcc.REPETITION_IDS == tuple(range(200, 600))
    assert pcc.REPETITION_IDS[0] == 200 and pcc.REPETITION_IDS[-1] == 599
    assert len(pcc.REPETITION_IDS) == pcc.REPETITIONS
    assert set(pcc.REPETITION_IDS).isdisjoint(reg.stage1_repetition_ids())


def test_ridge_is_the_only_model():
    assert pcc.PRIMARY_MODEL == reg.PRIMARY_MODEL == "ridge" == stage1.PRIMARY_MODEL
    assert pcc.PRIMARY_MODEL in rx.MODELS


def test_run_repetition_refuses_an_unregistered_cell():
    raw = _synthetic_raw()
    with pytest.raises(pcc.Stage1bError):
        pcc.run_repetition(raw, theta=0.90, repetition=200)
    with pytest.raises(pcc.Stage1bError):
        pcc.run_repetition(raw, theta=0.25, repetition=200)
    with pytest.raises(pcc.Stage1bError):
        pcc.run_repetition(raw, theta=0.30, repetition=0)
    with pytest.raises(pcc.Stage1bError):
        pcc.run_repetition(raw, theta=0.30, repetition=600)


# --------------------------------------------------------------------------- #
# 11 / 12 / 13 / 28. Seed identity
# --------------------------------------------------------------------------- #
def test_seed_level_indices_come_from_the_registered_map():
    assert pcc.level_index_for(0.40) == 4
    assert pcc.level_index_for(0.35) == 5
    assert tuple(pcc.level_index_for(theta) for theta in pcc.IC_GRID) == (0, 1, 2, 3, 5, 4)
    naive = {theta: index for index, theta in enumerate(sorted(pcc.IC_GRID))}
    assert naive[0.40] == 5 and naive[0.35] == 4
    assert pcc.level_index_for(0.40) != naive[0.40]
    assert pcc.level_index_for(0.35) != naive[0.35]


def test_runner_never_derives_a_level_index_by_enumeration(source):
    assert "enumerate(" not in source, "seed order must come from the frozen map"
    assert "level_index_for" in source
    assert "stage1.run_arm" not in source, "Stage 1's enumerate(levels) arm is the named drift site"
    assert pcc.level_index_for is not None
    assert pcc.level_index_for(0.35) == reg.level_index_for(0.35)


def test_declared_seed_formulas_reproduce_the_stage1_derivations():
    for theta in pcc.IC_GRID:
        for repetition in (200, 399, 599):
            expected = pcc.BASE_SEED * 1_000_003 + reg.level_index_for(theta) * 10_007 + repetition
            assert pcc.injection_seed_for(theta, repetition) == expected
            assert pcc.declared_injection_seed(theta, repetition) == expected
            assert pcc.injection_seed_for(theta, repetition) == stage1.derive_injection_seed(
                pcc.BASE_SEED, reg.level_index_for(theta), repetition
            )
            assert pcc.permutation_seed_for(repetition) == sig.DEFAULT_SEED + repetition
            assert pcc.declared_permutation_seed(repetition) == sig.DEFAULT_SEED + repetition
    # theta=0.40 keeps its legacy stream identity.
    assert pcc.injection_seed_for(0.40, 200) == 42_040_354


def test_no_seed_collision_and_no_stage1_stream_overlap():
    injection = {
        pcc.injection_seed_for(theta, repetition)
        for theta in pcc.IC_GRID
        for repetition in pcc.REPETITION_IDS
    }
    assert len(injection) == len(pcc.IC_GRID) * pcc.REPETITIONS == 2400
    permutation = {pcc.permutation_seed_for(r) for r in pcc.REPETITION_IDS}
    assert injection.isdisjoint(permutation)

    stage1_injection = {
        stage1.derive_injection_seed(stream, index, repetition)
        for stream in (pcc.BASE_SEED, pcc.BASE_SEED + 1, pcc.BASE_SEED + 2)
        for index in range(len(stage1.IC_GRID))
        for repetition in reg.stage1_repetition_ids()
    }
    stage1_permutation = {
        stage1.derive_permutation_seed(pcc.BASE_SEED, r) for r in reg.stage1_repetition_ids()
    }
    assert (injection | permutation).isdisjoint(stage1_injection | stage1_permutation)


# --------------------------------------------------------------------------- #
# 14 / 15 / 20. Detection semantics and the frozen operating divisor
# --------------------------------------------------------------------------- #
def test_operating_divisor_is_the_frozen_literal_five():
    assert pcc.STAGE1_OPERATIONAL_DIVISOR == reg.STAGE1_OPERATIONAL_DIVISOR == 5


def test_operating_divisor_is_not_a_stage1b_grid_length(source):
    """The divisor is bound to the frozen literal, never to any grid length.

    Checked on the parsed module rather than on raw text, so the registration
    wording quoted in the docstring and in the report's explanatory note cannot
    mask a real derivation.
    """
    assert pcc.STAGE1_OPERATIONAL_DIVISOR != len(pcc.IC_GRID)
    assert len(pcc.IC_GRID) == 6

    tree = ast.parse(source)
    divisor_assignments = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "STAGE1_OPERATIONAL_DIVISOR"
            for target in node.targets
        )
    ]
    assert len(divisor_assignments) == 1
    bound = divisor_assignments[0]
    assert isinstance(bound, ast.Attribute)
    assert bound.attr == "STAGE1_OPERATIONAL_DIVISOR"
    assert isinstance(bound.value, ast.Name) and bound.value.id == "reg"

    # Stage 1's confirmatory family size is not referenced anywhere in executable
    # code (the module docstring names it only to forbid it).
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            assert node.attr != "CONFIRMATORY_FAMILY_SIZE"
        if isinstance(node, ast.Name):
            assert node.id != "CONFIRMATORY_FAMILY_SIZE"

    # No grid length -- Stage 1b's or Stage 1's -- reaches the detection rules.
    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }
    for name in ("operating_point_p_value", "detected_by_stage1_rule", "detected_by_raw_p"):
        body = functions[name]
        referenced = {
            child.id for child in ast.walk(body) if isinstance(child, ast.Name)
        } | {child.attr for child in ast.walk(body) if isinstance(child, ast.Attribute)}
        assert "IC_GRID" not in referenced, name
        assert "len" not in referenced, name
        assert referenced <= {
            "STAGE1_OPERATIONAL_DIVISOR",
            "ALPHA",
            "operating_point_p_value",
            "p_raw",
            "min",
            "float",
            "bool",
        }, (name, referenced)


def test_detection_is_immune_to_the_stage1_family_size(monkeypatch):
    """Repointing Stage 1's family size must not move the Stage 1b operating point."""
    before = [pcc.detected_by_stage1_rule(p) for p in (0.0, 0.005, 0.0099, 0.01, 0.02, 0.05)]
    monkeypatch.setattr(stage1, "CONFIRMATORY_FAMILY_SIZE", 6, raising=True)
    monkeypatch.setattr(stage1, "IC_GRID", (0.0, 0.1, 0.2, 0.3, 0.35, 0.4), raising=True)
    after = [pcc.detected_by_stage1_rule(p) for p in (0.0, 0.005, 0.0099, 0.01, 0.02, 0.05)]
    assert before == after
    assert pcc.operating_point_p_value(0.01) == pytest.approx(0.05)


def test_primary_and_secondary_detection_definitions_are_exact():
    for p_raw in (0.0, 0.0001, 0.0099, 0.00999, 0.01, 0.0101, 0.0499, 0.05, 0.5, 1.0):
        assert pcc.operating_point_p_value(p_raw) == min(1.0, 5 * p_raw)
        assert pcc.detected_by_stage1_rule(p_raw) == (min(1.0, 5 * p_raw) < 0.05)
        # The registered raw equivalent under the discrete p-value convention.
        assert pcc.detected_by_stage1_rule(p_raw) == (p_raw < 0.01)
        assert pcc.detected_by_raw_p(p_raw) == (p_raw < 0.05)
    assert reg.SECONDARY_IS_GATING is False


def test_secondary_diagnostic_is_labelled_non_gating(fake_curve):
    for summary in fake_curve:
        assert summary["secondary_detection"]["gating"] is False
        assert "non-gating" in summary["secondary_detection"]["name"]
        assert summary["primary_detection"]["name"] == reg.PRIMARY_DETECTION_NAME
        assert summary["primary_detection"]["rule"] == reg.PRIMARY_DETECTION_RULE


# --------------------------------------------------------------------------- #
# 17 / 18 / 19. Stage 1 performance machinery is not reused
# --------------------------------------------------------------------------- #
def test_stage1_performance_gates_are_absent(source):
    for name in (
        "confirmatory_gate",
        "gate_informativeness",
        "detection_threshold",
        "GATE_LEVELS",
        "MDE_BASE",
        "SANITY_IC",
        "CONFIRMATORY_REPETITION",
        "attenuation_ratios",
        "stagewise_ratios",
        "analytic_comparison",
    ):
        assert not hasattr(pcc, name), f"Stage 1b must not expose {name}"
        assert f"stage1.{name}" not in source, f"Stage 1b must not call stage1.{name}"
    assert reg.HAS_PERFORMANCE_GATE is False
    assert pcc.registered_plan()["has_performance_gate"] is False


def test_report_carries_no_pass_fail_monotonicity_or_crossing(fake_records, fake_curve):
    report = _fake_report(fake_records, fake_curve)
    blob = json.dumps(report)
    assert "confirmatory" not in report
    assert "gate_informativeness" not in report
    assert "detection_threshold" not in report
    # No *computed* field may name a Stage 1 performance endpoint. The words
    # themselves appear in the registration's own prose (a non-monotone curve is
    # a valid result), so the check is on keys, not on free text.
    for key in _all_keys(report):
        assert not any(
            token in key.lower()
            for token in ("monoton", "gate_pass", "confirmatory", "threshold", "crossing")
        ), key
    for summary in report["calibration_curve"]:
        assert "passed" not in summary
        assert not any("monoton" in key.lower() for key in _all_keys(summary))
    assert report["design"]["has_performance_gate"] is False
    assert "80" not in json.dumps(report["calibration_curve"])
    assert blob


def test_excluded_stage1_arms_are_not_stage1b_arms(fake_records, fake_curve):
    assert 0.90 not in pcc.IC_GRID
    assert reg.EXCLUDED_STAGE_1_THETA_ARMS == (0.90,)
    report = _fake_report(fake_records, fake_curve)
    assert report["design"]["excluded_stage_1_theta_arms"] == [0.90]
    assert report["design"]["excluded_stage_1_carrier_arms"] == ["current_ratio missingness arm"]
    assert report["design"]["carriers"] == ["equity"]
    assert {summary["carrier"] for summary in report["calibration_curve"]} == {"equity"}
    assert {float(summary["ic_injected"]) for summary in report["calibration_curve"]} == set(
        pcc.IC_GRID
    )


def test_runner_never_selects_a_secondary_carrier(source):
    assert '["secondary"]' not in source
    assert "current_ratio" not in source.split('"""', 2)[2], "no current_ratio outside the docstring"


# --------------------------------------------------------------------------- #
# 21 / 22. Output schema
# --------------------------------------------------------------------------- #
def _fake_report(records: list[dict], curve: list[dict]) -> dict:
    integrity = pcc.evaluate_integrity(**_integrity_kwargs(records, curve))
    return pcc.build_report(
        records=records,
        curve=curve,
        integrity=integrity,
        replay_probe={"ic_injected": 0.0, "repetition": 200, "identical": True, "digest": "c" * 64},
        raw_path=rx.TRAINING_MODELING,
        base_seed=pcc.BASE_SEED,
        started_at="2026-01-01T00:00:00Z",
        duration_seconds=1.0,
        test_split_sizes=[80, 80, 80],
        split_count=3,
    )


def test_output_schema_carries_every_registered_summary(fake_curve):
    assert len(fake_curve) == len(pcc.IC_GRID)
    for summary in fake_curve:
        for block in ("realized_raw_carrier_ic", "final_evaluated_ic"):
            assert set(summary[block]) == {"n", "mean", "sd", "median", "p05", "p95"}
        assert summary["repetitions"] == pcc.REPETITIONS
        assert summary["repetition_id_range"] == [200, 599]
        assert summary["level_index"] == reg.level_index_for(float(summary["ic_injected"]))
        for block in ("primary_detection", "secondary_detection"):
            assert {"name", "rule", "detections", "rate", "wilson_95_pointwise"} <= set(
                summary[block]
            )
        assert set(summary["checkpoint_summary"]) == {name for name, _ in stage1.CHECKPOINTS}
    # The registered summaries are the checkpoint chain's two named endpoints.
    for summary in fake_curve:
        assert summary["realized_raw_carrier_ic"] == summary["checkpoint_summary"]["ic_raw_carrier"]
        assert summary["final_evaluated_ic"] == summary["checkpoint_summary"]["ic_final_evaluation"]


def test_wilson_intervals_are_pointwise_and_bracket_the_estimate(fake_curve):
    assert reg.DETECTION_INTERVAL == "pointwise 95% Wilson"
    for summary in fake_curve:
        for block in ("primary_detection", "secondary_detection"):
            low, high = summary[block]["wilson_95_pointwise"]
            rate = summary[block]["rate"]
            assert 0.0 <= low <= rate <= high <= 1.0
            assert summary[block]["wilson_95_pointwise"] == stage1._wilson_interval(
                summary[block]["detections"], summary["repetitions"]
            )
        assert "simultaneous" not in json.dumps(summary)


def test_report_states_the_pointwise_interval_boundary(fake_records, fake_curve):
    report = _fake_report(fake_records, fake_curve)
    limitations = " ".join(report["limitations"]).lower()
    assert "pointwise per theta" in limitations
    assert "not simultaneous or between-level" in limitations
    assert "no between-theta inference" in limitations
    assert report["design"]["detection_interval"] == "pointwise 95% Wilson"


def test_rendered_markdown_passes_the_shared_claim_safety_validator(fake_records, fake_curve):
    markdown = pcc.render_markdown(_fake_report(fake_records, fake_curve))
    validate_claim_safety_text(markdown)
    assert "Stage 1b" in markdown
    assert "no scientific performance gate" in markdown.lower()
    assert "pointwise" in markdown


def test_required_outputs_are_enumerated_for_the_finiteness_check(fake_curve):
    values = pcc.required_output_values(fake_curve)
    names = {name for name, _ in values}
    assert len(values) == len(pcc.IC_GRID) * (2 * 3 + 2 * 5)
    assert all(value is None or math.isfinite(float(value)) for _, value in values)
    assert any("primary_detection.rate" in name for name in names)
    assert any("final_evaluated_ic.median" in name for name in names)


# --------------------------------------------------------------------------- #
# 25 / 26. Source hash and output confinement
# --------------------------------------------------------------------------- #
def test_source_sha_contract_matches_the_registered_dataset():
    dataset = REPO_ROOT / reg.DATASET_PATH
    assert dataset.is_file()
    assert prov.sha256_path(dataset) == reg.DATASET_SHA256
    assert rx.TRAINING_MODELING.resolve() == dataset.resolve()


def test_source_hash_mismatch_fails_the_integrity_contract(fake_records, fake_curve):
    result = pcc.evaluate_integrity(
        **_integrity_kwargs(fake_records, fake_curve, source_sha_before="f" * 64)
    )
    assert result["passed"] is False
    assert "registered source dataset hash matches" in result["failures"]


def test_protected_paths_cannot_be_stage1b_output_targets(fake_records, fake_curve):
    for target in (
        "data/trusted_clean/modeling_dataset_training_2020_2025.csv",
        "data/provenance/x.json",
        "experiments/results/predictions_split_a.csv",
        "experiments/results_thesis/positive_control/repetitions.csv",
    ):
        result = pcc.evaluate_integrity(
            **_integrity_kwargs(fake_records, fake_curve, output_paths=[target])
        )
        assert result["passed"] is False
        assert "Stage 1b writes only to its isolated namespace" in result["failures"]
    # provenance refuses to hand the slug a protected directory at all.
    for protected in prov.PROTECTED_RESULTS_ROOTS:
        assert not reg.STAGE_1B_RESULT_ROOT.startswith(protected + "/")
        assert reg.STAGE_1B_RESULT_ROOT.rstrip("/") != protected


def test_protected_data_and_stage1_mutation_fail_the_contract(fake_records, fake_curve):
    mutated = pcc.evaluate_integrity(
        **_integrity_kwargs(
            fake_records, fake_curve, protected_digest_after={"data/trusted_clean/x.csv": "z" * 64}
        )
    )
    assert "no data/trusted*, data/trusted_clean*, or data/provenance* mutation" in mutated["failures"]
    overwritten = pcc.evaluate_integrity(
        **_integrity_kwargs(fake_records, fake_curve, stage1_digest_after={})
    )
    assert "Stage 1 historical namespace is not overwritten" in overwritten["failures"]


def test_protected_data_roots_cover_the_registered_trees():
    assert pcc.PROTECTED_DATA_ROOTS == (
        "data/trusted",
        "data/trusted_clean",
        "data/trusted_raw",
        "data/provenance",
    )
    digest = pcc.protected_data_digest()
    assert digest, "protected data trees must be hashable before and after the run"
    assert all(path.startswith("data/") for path in digest)


# --------------------------------------------------------------------------- #
# 27. Runtime override restoration
# --------------------------------------------------------------------------- #
def test_pipeline_source_override_is_restored_after_the_block():
    original = rx.TRAINING_MODELING
    with pcc._restored_pipeline_source() as reported:
        assert reported == original
        rx.TRAINING_MODELING = Path("/nonexistent/injected.csv")
    assert rx.TRAINING_MODELING == original


def test_pipeline_source_override_is_restored_after_an_exception():
    original = rx.TRAINING_MODELING
    with pytest.raises(RuntimeError):
        with pcc._restored_pipeline_source():
            rx.TRAINING_MODELING = Path("/nonexistent/injected.csv")
            raise RuntimeError("boom")
    assert rx.TRAINING_MODELING == original
    assert rx._modeling_csv() == original


def test_unrestored_override_fails_the_integrity_contract(fake_records, fake_curve):
    result = pcc.evaluate_integrity(
        **_integrity_kwargs(fake_records, fake_curve, pipeline_source_restored=False)
    )
    assert "runtime override restored on every exit path" in result["failures"]


# --------------------------------------------------------------------------- #
# Closed integrity contract coverage
# --------------------------------------------------------------------------- #
def test_integrity_report_covers_the_closed_registered_list(fake_records, fake_curve):
    result = pcc.evaluate_integrity(**_integrity_kwargs(fake_records, fake_curve))
    assert tuple(result["mechanical"]) == reg.MECHANICAL_PROVENANCE_CHECKS
    assert tuple(result["mechanism"]) == reg.MECHANISM_INVARIANT_CHECKS
    assert result["failures"] == []
    assert result["passed"] is True
    assert result["has_performance_gate"] is False
    assert result["excluded_from_every_check"] == list(reg.INTEGRITY_CHECK_EXCLUSIONS)


def test_integrity_detects_missing_and_duplicate_cells(fake_records, fake_curve):
    short = fake_records[:-1]
    result = pcc.evaluate_integrity(**_integrity_kwargs(short, fake_curve))
    assert "complete 6 × 400 matrix" in result["failures"]
    assert "no missing/duplicate repetition cells" in result["failures"]

    duplicated = fake_records[:-1] + [fake_records[0]]
    result = pcc.evaluate_integrity(**_integrity_kwargs(duplicated, fake_curve))
    assert "no missing/duplicate repetition cells" in result["failures"]


def test_integrity_detects_a_seed_formula_violation(fake_records, fake_curve):
    tampered = [dict(record) for record in fake_records]
    tampered[7]["injection_seed"] = tampered[7]["injection_seed"] + 1
    result = pcc.evaluate_integrity(**_integrity_kwargs(tampered, fake_curve))
    assert "declared seed formulas reproduced" in result["failures"]


def test_integrity_detects_a_broken_mechanism_invariant(fake_records, fake_curve):
    tampered = [dict(record) for record in fake_records]
    broken = dict(tampered[3]["mechanism_invariants"])
    broken["carrier_missingness_mask_preserved"] = False
    tampered[3] = {**tampered[3], "mechanism_invariants": broken}
    result = pcc.evaluate_integrity(**_integrity_kwargs(tampered, fake_curve))
    assert "carrier missingness mask preserved" in result["failures"]


def test_integrity_detects_a_failed_replay_probe(fake_records, fake_curve):
    result = pcc.evaluate_integrity(
        **_integrity_kwargs(
            fake_records,
            fake_curve,
            replay_probe={"ic_injected": 0.0, "repetition": 200, "identical": False},
        )
    )
    assert "replay deterministic" in result["failures"]


def test_no_integrity_check_inspects_a_performance_statistic(fake_records, fake_curve):
    """A weak, flat, or high-background curve must not fail the contract.

    Two record sets differing only in their p-values -- one detecting nowhere,
    one detecting everywhere -- must produce the same integrity verdict.
    """
    def _records(p_raw: float) -> list[dict]:
        return [
            _fake_record(theta, repetition, p_raw=p_raw)
            for theta in pcc.IC_GRID
            for repetition in pcc.REPETITION_IDS
        ]

    never, always = _records(0.9), _records(0.0)
    never_curve, always_curve = pcc.calibration_curve(never), pcc.calibration_curve(always)
    assert never_curve[0]["primary_detection"]["rate"] == 0.0
    assert always_curve[0]["primary_detection"]["rate"] == 1.0
    verdicts = [
        pcc.evaluate_integrity(**_integrity_kwargs(records, curve))["passed"]
        for records, curve in ((never, never_curve), (always, always_curve))
    ]
    assert verdicts == [True, True]


# --------------------------------------------------------------------------- #
# 29. Replay / determinism machinery on a tiny non-scientific fixture
# --------------------------------------------------------------------------- #
def test_records_digest_is_deterministic_and_order_sensitive(fake_records):
    sample = fake_records[:5]
    assert pcc.records_digest(sample) == pcc.records_digest(list(sample))
    assert pcc.records_digest(sample) != pcc.records_digest(list(reversed(sample)))
    assert len(pcc.records_digest(sample)) == 64


def test_injection_replays_identically_on_a_synthetic_fixture():
    """Same seed, same bytes — the property the replay probe relies on."""
    raw = _synthetic_raw()
    seed = pcc.injection_seed_for(0.30, 200)
    first = stage1.inject_carrier(raw, pcc.CARRIER, 0.30, seed=seed)
    second = stage1.inject_carrier(raw, pcc.CARRIER, 0.30, seed=seed)
    assert pcc._injected_csv_sha256(first) == pcc._injected_csv_sha256(second)
    other = stage1.inject_carrier(raw, pcc.CARRIER, 0.30, seed=seed + 1)
    assert pcc._injected_csv_sha256(other) != pcc._injected_csv_sha256(first)


def test_mechanism_invariants_hold_on_a_synthetic_injection():
    raw = _synthetic_raw()
    injected = stage1.inject_carrier(
        raw, pcc.CARRIER, 0.30, seed=pcc.injection_seed_for(0.30, 200)
    )
    invariants = pcc.check_mechanism_invariants(raw, injected)
    assert all(invariants.values()), invariants


def test_mechanism_invariants_catch_a_tampered_table():
    raw = _synthetic_raw()
    injected = stage1.inject_carrier(
        raw, pcc.CARRIER, 0.30, seed=pcc.injection_seed_for(0.30, 200)
    )
    fabricated = injected.copy(deep=True)
    fabricated.loc[fabricated.index[0], pcc.CARRIER] = 999.0
    assert not pcc.check_mechanism_invariants(raw, fabricated)[
        "carrier_observed_value_multiset_preserved_within_year"
    ]

    filled = injected.copy(deep=True)
    null_rows = filled.index[filled[pcc.CARRIER].isna()]
    filled.loc[null_rows[0], pcc.CARRIER] = 0.0
    assert not pcc.check_mechanism_invariants(raw, filled)["carrier_missingness_mask_preserved"]

    retargeted = injected.copy(deep=True)
    retargeted.loc[retargeted.index[0], pcc.TARGET_COLUMN] = 42.0
    assert not pcc.check_mechanism_invariants(raw, retargeted)["targets_unchanged"]

    other = injected.copy(deep=True)
    other.loc[other.index[0], "other"] = 42.0
    assert not pcc.check_mechanism_invariants(raw, other)["non_carrier_features_unchanged"]


def test_identity_checkpoint_tolerance_is_the_governed_stage1_granularity():
    assert pcc.ROUND_DIGITS == stage1.ROUND_DIGITS == 12
    assert pcc.IDENTITY_TOLERANCE == 10.0 ** -12
    assert pcc.IDENTITY_CHECKPOINTS == (
        "ic_raw_carrier",
        "ic_panel_carrier",
        "ic_model_input_carrier",
    )
    agreeing = {
        "ic_raw_carrier": 0.25,
        "ic_panel_carrier": 0.25,
        "ic_model_input_carrier": 0.25,
        "ic_model_prediction": 0.19,
        "ic_final_evaluation": 0.19,
    }
    assert all(pcc.check_checkpoint_identities(agreeing).values())
    drifted = {**agreeing, "ic_panel_carrier": 0.25 + 1e-9}
    assert not pcc.check_checkpoint_identities(drifted)["identity_checkpoint_ics_agree"]
    mismatched = {**agreeing, "ic_final_evaluation": 0.20}
    assert not pcc.check_checkpoint_identities(mismatched)[
        "ridge_prediction_ic_equals_final_evaluation_ic"
    ]


# --------------------------------------------------------------------------- #
# 30. Stage 1's historical surface is untouched
# --------------------------------------------------------------------------- #
def test_stage1_implementation_and_artifacts_are_not_modified():
    tracked = [
        STAGE_1_IMPLEMENTATION,
        REPO_ROOT / "experiments/significance.py",
        REPO_ROOT / "experiments/run_experiments.py",
        REPO_ROOT / "docs/thesis/STAGE_1B_REGISTRATION.md",
        REPO_ROOT / "docs/thesis/PRE_EXPERIMENT_PROTOCOL.md",
        STAGE_1_OUTPUT_ROOT / "positive_control_report.json",
        STAGE_1_OUTPUT_ROOT / "positive_control_report.md",
        STAGE_1_OUTPUT_ROOT / "repetitions.csv",
        STAGE_1_OUTPUT_ROOT / "detection_curve.csv",
        STAGE_1_OUTPUT_ROOT / "attenuation_by_stage.csv",
        STAGE_1_OUTPUT_ROOT / "artifact_manifest.json",
    ]
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    changed = {line[3:] for line in status if len(line) >= 4}
    for path in tracked:
        assert path.exists(), path
        assert path.relative_to(REPO_ROOT).as_posix() not in changed


def test_stage1b_reuses_stage1_helpers_without_redefining_them(source):
    """Reuse, not a fork: the numerics come from the Stage 1 primitives."""
    for helper in (
        "stage1.inject_carrier",
        "stage1.run_repetition",
        "stage1.derive_injection_seed",
        "stage1.derive_permutation_seed",
        "stage1._wilson_interval",
        "stage1.CHECKPOINTS",
    ):
        assert helper in source
    assert "def inject_carrier" not in source
    assert "def derive_injection_seed" not in source
