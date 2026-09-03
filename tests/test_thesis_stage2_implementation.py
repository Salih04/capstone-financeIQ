"""Focused tests for the inert Stage 2 negative-control apparatus.

All construction/model fixtures in this module are invented test data.  The
tests never call the governed entry point, never use the frozen dataset for a
scientific run, and never write the registered Stage 2 result namespace.
"""

from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from experiments import run_experiments as canonical
from experiments import significance as sig
from experiments.thesis import negative_control as nc
from experiments.thesis import provenance as prov
from experiments.thesis import stage2_registration as reg


REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / reg.DATASET_PATH
SIGNIFICANCE_PATH = REPO_ROOT / "experiments/significance.py"
REGISTRY_PATH = REPO_ROOT / "artifact_registry.json"
RUNNER_PATH = REPO_ROOT / "experiments/thesis/negative_control.py"
STAGE2_ROOT = REPO_ROOT / reg.RESULT_ROOT.rstrip("/")
FEATURE_COLUMNS = tuple(f"feature_{index:02d}" for index in range(40))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@pytest.fixture(scope="module")
def synthetic_raw() -> pd.DataFrame:
    """Small source-shaped table with distinct, intentionally structured masks."""
    rng = np.random.default_rng(20260902)
    rows: list[dict[str, object]] = []
    missing_by_row = (
        (0, 1),
        (2, 3),
        (4,),
        (5,),
        (6,),
        (7,),
        (8,),
        (),
    )
    for year in reg.FEATURE_YEARS:
        for ticker_index in reversed(range(8)):
            values = rng.normal(size=len(FEATURE_COLUMNS))
            row: dict[str, object] = {
                "ticker": f"T{ticker_index:02d}",
                "year": year,
                reg.TARGET_COLUMN: (
                    np.nan
                    if ticker_index == 0
                    else float(year * 100 + ticker_index)
                ),
            }
            for index, column in enumerate(FEATURE_COLUMNS):
                row[column] = float(values[index])
            for index in missing_by_row[ticker_index]:
                row[FEATURE_COLUMNS[index]] = np.nan
            rows.append(row)
    # Reverse feature insertion order so the implementation must sort it.
    columns = ["ticker", "year", reg.TARGET_COLUMN, *reversed(FEATURE_COLUMNS)]
    return pd.DataFrame(rows)[columns]


def _gate_record(control: str, repetition_id: int, reject: bool) -> dict:
    return {
        "control": control,
        "repetition_id": repetition_id,
        "status": nc.ANALYZABLE_STATUS,
        "classification": nc.ANALYZABLE_STATUS,
        "analyzable": True,
        "family_reject": reject,
    }


def _prediction_fixture(*, constant_models: set[str] | None = None) -> pd.DataFrame:
    constant_models = constant_models or set()
    rows: list[dict[str, object]] = []
    for split_index, split in enumerate(reg.CANONICAL_SPLITS):
        year = split["test_feature_year"] + 1
        for row_index in range(5):
            for model in reg.MODELS:
                rows.append(
                    {
                        "ticker": f"T{row_index:02d}",
                        "year": year,
                        "model": model,
                        "split": split["name"],
                        "y_true": float(split_index * 10 + row_index),
                        "y_pred": (
                            1.0
                            if model in constant_models
                            else float(row_index + split_index / 10)
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _valid_mechanism_invariants(control: str) -> dict[str, bool]:
    if control == reg.NC1_NAME:
        return {
            "feature_matrix_unchanged": True,
            "row_universe_unchanged": True,
            "target_null_locations_preserved": True,
            "target_multiset_by_year_preserved": True,
            "canonical_splits_unchanged": True,
            "all_target_years_processed": True,
            "train_and_test_targets_use_permuted_panel": True,
            "no_test_only_construction": True,
            "target_permutation_stream_used": True,
        }
    values = {
        "target_byte_identical": True,
        "target_return_byte_identical": True,
        "fresh_iid_noise_construction": True,
        "joint_mask_permutation_matches_registered_seed": True,
        "per_feature_year_missingness_counts_preserved": True,
        "rowwise_co_missingness_multiset_preserved": True,
        "feature_matrix_replaced_from_real": True,
        "rank_transform_after_masking_exact": True,
        "six_models_and_splits_unchanged": True,
    }
    if control == reg.NC0_NAME:
        values["mask_row_alignment_changed"] = True
    else:
        values.update(
            {
                "diagnostic_isolated": True,
                "confirmatory_gate_excluded": True,
                "real_mask_alignment_retained": True,
            }
        )
    return values


def _valid_record(
    control: str,
    repetition_id: int,
    *,
    family_reject: bool = False,
    raw_p: float = 0.5,
    observed_ic: float = 0.0,
) -> dict:
    analysis = {
        "pooled": {
            "observed_ic": observed_ic,
            "permutation_p_value_two_sided": raw_p,
            "bootstrap_ci_95": [-0.1, 0.1],
        }
    }
    model_results = [
        {
            "model": model,
            "status": nc.ANALYZABLE_STATUS,
            "significance_seed": reg.significance_seed(repetition_id),
            "analysis": copy.deepcopy(analysis),
        }
        for model in reg.MODELS
    ]
    return {
        "control": control,
        "role": reg.CONTROL_ROLES[control],
        "repetition_id": repetition_id,
        "status": nc.ANALYZABLE_STATUS,
        "classification": nc.ANALYZABLE_STATUS,
        "analyzable": True,
        "significance_seed": reg.significance_seed(repetition_id),
        "permutations": reg.PERMUTATIONS,
        "bootstraps": reg.BOOTSTRAPS,
        "construction_seeds": {
            field: value
            for field, value in (
                nc._seed_fields(control, repetition_id).items()
            )
        },
        "model_results": model_results,
        "family": {
            "min_raw_p": raw_p,
            "model_family_divisor": 6,
            "bonferroni_adjusted_p_value": min(1.0, 6 * raw_p),
            "family_reject": family_reject,
            "headline_model": reg.MODELS[0],
        },
        "family_reject": family_reject,
        "mechanism_invariants": _valid_mechanism_invariants(control),
    }


@pytest.fixture(scope="module")
def valid_integrity_records() -> list[dict]:
    records: list[dict] = []
    for control in (
        reg.NC0_NAME,
        reg.NC1_NAME,
        reg.NC0_DIAGNOSTIC_NAME,
    ):
        for repetition_id in reg.EXPECTED_REPETITION_ID_MATRICES[control]:
            records.append(_valid_record(control, repetition_id))
    return records


def _integrity_kwargs(records: list[dict], **overrides) -> dict:
    output_root = reg.RESULT_ROOT.rstrip("/")
    kwargs = {
        "records": records,
        "source_path": DATASET_PATH,
        "registered_source_sha": reg.DATASET_SHA256,
        "source_sha_before": reg.DATASET_SHA256,
        "source_sha_after": reg.DATASET_SHA256,
        "significance_sha": reg.SIGNIFICANCE_SHA256,
        "source_module_hashes": dict(reg.SOURCE_MODULE_HASHES),
        "protected_digest_before": {"data/trusted_clean/x.csv": "a" * 64},
        "protected_digest_after": {"data/trusted_clean/x.csv": "a" * 64},
        "stage1_digest_before": {
            "experiments/results_thesis/positive_control/x": "b" * 64
        },
        "stage1_digest_after": {
            "experiments/results_thesis/positive_control/x": "b" * 64
        },
        "stage1b_digest_before": {
            "experiments/results_thesis/positive_control_calibration/x": "c" * 64
        },
        "stage1b_digest_after": {
            "experiments/results_thesis/positive_control_calibration/x": "c" * 64
        },
        "workspace_digest_before": {"outside.txt": "d" * 64},
        "workspace_digest_after": {"outside.txt": "d" * 64},
        "output_root": output_root,
        "output_paths": [
            f"{output_root}/{name}" for name in nc.SCIENTIFIC_EMITTED_FILENAMES
        ],
        "output_audit": {
            "passed": True,
            "actual_scientific_files": list(nc.SCIENTIFIC_EMITTED_FILENAMES),
            "unexpected_files": [],
            "unexpected_directories": [],
            "symlink_escapes": [],
            "missing_scientific_files": [],
        },
        "source_override_restored": True,
        "replay_probe": {
            "control": reg.NC0_NAME,
            "repetition_id": reg.NC0_IDS[0],
            "identical": True,
            "digest": "e" * 64,
            "permutations": reg.PERMUTATIONS,
            "bootstraps": reg.BOOTSTRAPS,
        },
    }
    kwargs.update(overrides)
    return kwargs


def test_import_and_default_plan_do_not_create_stage2_root():
    assert not STAGE2_ROOT.exists()
    plan = nc.registered_plan()
    assert plan["executed"] is False
    assert plan["result_root_created"] is False
    assert plan["scientific_draw_performed"] is False
    assert not STAGE2_ROOT.exists()


def test_subprocess_import_is_filesystem_inert():
    tracked = [DATASET_PATH, SIGNIFICANCE_PATH, RUNNER_PATH]
    before = {path: _sha256(path) for path in tracked}
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(
        [sys.executable, "-c", "import experiments.thesis.negative_control"],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
    )
    assert {path: _sha256(path) for path in tracked} == before
    assert not STAGE2_ROOT.exists()


def test_registered_result_namespace_and_prospective_contracts_are_exact():
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    root = reg.RESULT_ROOT.rstrip("/")
    assert root in registry["governed_roots"]
    assert not any(
        entry["path_or_glob"].startswith(root + "/")
        for entry in registry["entries"]
    )
    expected_names = set(nc.EMITTED_FILENAMES) | set(nc.OPERATIONAL_FILENAMES)
    prospective = [
        entry
        for entry in registry["prospective_entries"]
        if entry["path_or_glob"].startswith(root + "/")
    ]
    assert {entry["path_or_glob"].rsplit("/", 1)[-1] for entry in prospective} == expected_names
    assert len(prospective) == len(expected_names)
    for entry in prospective:
        assert set(entry) == {
            "path_or_glob",
            "artifact_class",
            "generator_command",
            "inputs",
            "hand_edit_forbidden",
            "notes",
        }
        assert entry["artifact_class"] == "generated"
        assert entry["generator_command"] == "make thesis-stage2"
        assert entry["hand_edit_forbidden"] is True
        if entry["path_or_glob"].endswith(nc.ATTEMPT_MARKER_FILENAME):
            assert entry["inputs"] == []
        else:
            assert entry["inputs"] == [reg.DATASET_PATH]
        assert entry["notes"].strip()


def test_make_target_and_runner_require_explicit_governed_flag():
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "thesis-stage2:" in makefile
    assert "thesis-stage2-replay:" in makefile
    assert "negative_control.py --run" in makefile
    assert "negative_control.py --replay-check" in makefile
    source = RUNNER_PATH.read_text(encoding="utf-8")
    assert "if __name__ == \"__main__\":" in source
    assert "enumerate(" not in source


def test_nc0_uses_one_joint_mask_permutation_and_rank_after_masking(synthetic_raw):
    real = nc.build_real_panel(synthetic_raw)
    panel, metadata = nc.build_nc0_panel(
        synthetic_raw, reg.NC0_IDS[0], return_metadata=True
    )
    skeleton, feature_columns = nc._panel_skeleton(synthetic_raw)
    expected_noise = nc.generate_iid_noise(
        len(skeleton), len(feature_columns), metadata["noise_seed"]
    )
    expected_mask = nc.jointly_permute_mask(
        metadata["real_mask"],
        skeleton[nc.FEATURE_YEAR_COLUMN],
        metadata["mask_seed"],
    )
    expected_masked = np.where(expected_mask, np.nan, expected_noise)
    expected_skeleton = skeleton.copy()
    expected_skeleton[feature_columns] = expected_masked
    expected_ranked = nc.canonical_rank_percentile(expected_skeleton, feature_columns)

    assert feature_columns == list(FEATURE_COLUMNS)
    assert list(panel.columns) == [
        "ticker",
        nc.FEATURE_YEAR_COLUMN,
        nc.TARGET_YEAR_COLUMN,
        *FEATURE_COLUMNS,
        reg.TARGET_COLUMN,
        nc.TARGET_RETURN_COLUMN,
    ]
    assert np.array_equal(metadata["noise"], expected_noise)
    assert np.array_equal(metadata["permuted_mask"], expected_mask)
    for column in feature_columns:
        assert panel[column].equals(expected_ranked[column])
    assert real[reg.TARGET_COLUMN].equals(panel[reg.TARGET_COLUMN])
    assert real[nc.TARGET_RETURN_COLUMN].equals(panel[nc.TARGET_RETURN_COLUMN])
    for year in reg.FEATURE_YEARS:
        real_rows = metadata["real_mask"][skeleton[nc.FEATURE_YEAR_COLUMN] == year]
        permuted_rows = metadata["permuted_mask"][skeleton[nc.FEATURE_YEAR_COLUMN] == year]
        assert np.array_equal(real_rows.sum(axis=0), permuted_rows.sum(axis=0))
        assert sorted(map(tuple, real_rows)) == sorted(map(tuple, permuted_rows))
    invariants = nc.mechanism_invariants(
        synthetic_raw,
        panel,
        control=reg.NC0_NAME,
        metadata=metadata,
    )
    assert all(invariants.values()), invariants
    assert invariants["mask_row_alignment_changed"] is True


def test_joint_mask_permutation_cannot_be_independent_by_column(synthetic_raw):
    _, metadata = nc.build_nc0_panel(
        synthetic_raw, reg.NC0_IDS[0], return_metadata=True
    )
    mask = metadata["real_mask"]
    years = nc._panel_skeleton(synthetic_raw)[0][nc.FEATURE_YEAR_COLUMN]
    joint, permutations = nc.jointly_permute_mask(
        mask, years, metadata["mask_seed"], return_permutations=True
    )
    for year in reg.FEATURE_YEARS:
        positions = np.flatnonzero(years.to_numpy() == year)
        order = np.asarray(permutations[year], dtype=int)
        assert np.array_equal(joint[positions], mask[positions[order]])
        assert all(
            np.array_equal(joint[position], mask[positions[order_index]])
            for position, order_index in zip(positions, order)
        )


def test_nc1_permutation_covers_all_target_years_and_preserves_nulls(synthetic_raw):
    real = nc.build_real_panel(synthetic_raw)
    panel, metadata = nc.build_nc1_panel(
        synthetic_raw, reg.NC1_IDS[0], return_metadata=True
    )
    assert metadata["target_years_processed"] == list(reg.TARGET_YEARS)
    assert metadata["complete_panel_before_splits"] is True
    assert metadata["test_year_only_construction"] is False
    assert real["ticker"].tolist() == panel["ticker"].tolist()
    assert real[nc.FEATURE_YEAR_COLUMN].tolist() == panel[nc.FEATURE_YEAR_COLUMN].tolist()
    assert real[list(FEATURE_COLUMNS)].equals(panel[list(FEATURE_COLUMNS)])
    assert real[reg.TARGET_COLUMN].isna().equals(panel[reg.TARGET_COLUMN].isna())
    assert real[nc.TARGET_RETURN_COLUMN].isna().equals(panel[nc.TARGET_RETURN_COLUMN].isna())
    for target_year in reg.TARGET_YEARS:
        real_values = real.loc[real[nc.TARGET_YEAR_COLUMN] == target_year, reg.TARGET_COLUMN]
        permuted_values = panel.loc[panel[nc.TARGET_YEAR_COLUMN] == target_year, reg.TARGET_COLUMN]
        assert np.array_equal(
            np.sort(real_values.dropna().to_numpy()),
            np.sort(permuted_values.dropna().to_numpy()),
        )
    assert panel[reg.TARGET_COLUMN].equals(panel[nc.TARGET_RETURN_COLUMN])
    invariants = nc.mechanism_invariants(
        synthetic_raw,
        panel,
        control=reg.NC1_NAME,
        metadata=metadata,
    )
    assert all(invariants.values()), invariants


def test_diagnostic_retains_real_mask_and_isolated_non_gating(synthetic_raw):
    real = nc.build_real_panel(synthetic_raw)
    panel, metadata = nc.build_nc0_diagnostic_panel(
        synthetic_raw, reg.NC0_DIAGNOSTIC_IDS[0], return_metadata=True
    )
    skeleton, _ = nc._panel_skeleton(synthetic_raw)
    assert metadata["diagnostic_noise_seed"] == reg.construction_seed(30, 3000)
    assert np.array_equal(
        metadata["permuted_mask"], metadata["real_mask"]
    )
    assert np.array_equal(
        metadata["permuted_mask"],
        skeleton[list(FEATURE_COLUMNS)].isna().to_numpy(dtype=bool),
    )
    assert real[reg.TARGET_COLUMN].equals(panel[reg.TARGET_COLUMN])
    invariants = nc.mechanism_invariants(
        synthetic_raw,
        panel,
        control=reg.NC0_DIAGNOSTIC_NAME,
        metadata=metadata,
    )
    assert all(invariants.values()), invariants
    assert invariants["real_mask_alignment_retained"] is True


def test_seed_formulas_and_exhaustive_collision_report_are_exact():
    for stream in reg.CONSTRUCTION_STREAMS.values():
        for repetition_id in (1000, 1999, 2000, 2999, 3000, 3999):
            expected = 42 * 1_000_003 + stream * 10_007 + repetition_id
            assert nc.construction_seed(stream, repetition_id) == expected
    for repetition_id in (1000, 1999, 2000, 2999, 3000, 3999):
        assert nc.significance_seed(repetition_id) == 42 + repetition_id
    report = nc._collision_report()
    assert report["construction_count"] == 4_000
    assert report["construction_unique"] is True
    assert report["passed"] is True


def test_exact_six_model_family_and_registered_significance_settings():
    assert nc.MODEL_FAMILY == reg.MODELS == sig.ML_MODELS
    assert len(nc.MODEL_FAMILY) == 6
    assert nc.MODEL_FAMILY_DIVISOR == 6
    assert inspect.signature(nc.run_repetition).parameters["permutations"].default == 10_000
    assert inspect.signature(nc.run_repetition).parameters["bootstraps"].default == 10_000
    assert inspect.signature(nc._replay_probe).parameters["permutations"].default == 10_000
    assert inspect.signature(nc._replay_probe).parameters["bootstraps"].default == 10_000
    p_values = [0.2, 0.1, 0.009, 0.3, 0.4, 0.5]
    model_results = [
        {
            "model": model,
            "status": nc.ANALYZABLE_STATUS,
            "analysis": {
                "pooled": {
                    "permutation_p_value_two_sided": p_value,
                    "observed_ic": 0.0,
                    "bootstrap_ci_95": [-0.1, 0.1],
                }
            },
        }
        for model, p_value in zip(reg.MODELS, p_values)
    ]
    family = nc._family_result(model_results)
    assert family["model_family_divisor"] == 6
    assert family["min_raw_p"] == 0.009
    assert family["bonferroni_adjusted_p_value"] == pytest.approx(0.054)
    assert family["family_reject"] is False
    p_values[0] = 0.008
    model_results[0]["analysis"]["pooled"]["permutation_p_value_two_sided"] = 0.008
    assert nc._family_result(model_results)["family_reject"] is True


def test_model_constructors_match_canonical_effective_parameters():
    expected_effective_defaults = {
        "linear_regression": {"fit_intercept": True},
        "ridge": {},
        "lasso": {},
        "elasticnet": {"l1_ratio": 0.5},
        "random_forest": {"n_jobs": None},
        "gradient_boosting": {},
    }
    for name in reg.MODELS:
        estimator = nc._make_model(name)
        effective = estimator.get_params(deep=False)
        registered = canonical.MODEL_CONFIGS[name]

        assert registered == reg.MODEL_CONFIGS[name]
        for parameter, expected in registered["parameters"].items():
            assert effective[parameter] == expected, (name, parameter)
        if registered["seed"] is not None:
            assert effective["random_state"] == registered["seed"]
        for parameter, expected in expected_effective_defaults[name].items():
            assert effective[parameter] == expected, (name, parameter)

    assert canonical.MODEL_CONFIGS["random_forest"]["parameters"].get("n_jobs") is None
    assert canonical.MODEL_CONFIGS["random_forest"]["seed"] == 42
    assert canonical.MODEL_CONFIGS["gradient_boosting"]["seed"] == 42


def test_registered_runner_rejects_non_registered_resampling_counts(synthetic_raw):
    with pytest.raises(nc.Stage2IntegrityError, match="exactly 10,000"):
        nc.run_repetition(
            synthetic_raw,
            control=reg.NC0_NAME,
            repetition_id=reg.NC0_IDS[0],
            permutations=1_000,
        )


def test_degeneracy_classification_is_partial_or_all_without_p_values(
    synthetic_raw, monkeypatch
):
    panel, metadata = nc.build_nc0_panel(
        synthetic_raw, reg.NC0_IDS[0], return_metadata=True
    )
    monkeypatch.setattr(
        nc,
        "_construction_panel",
        lambda raw, control, repetition_id: (panel, dict(metadata)),
    )
    monkeypatch.setattr(
        nc,
        "_prediction_frame",
        lambda panel, feature_columns: _prediction_fixture(
            constant_models={reg.MODELS[0]}
        ),
    )
    partial = nc.run_repetition(
        synthetic_raw, control=reg.NC0_NAME, repetition_id=reg.NC0_IDS[0]
    )
    assert partial["status"] == reg.PARTIAL_MODEL_DEGENERACY_STATUS
    assert partial["analyzable"] is False
    assert set(partial["degenerate_models"]) == {reg.MODELS[0]}
    assert len(partial["model_results"]) == 6
    assert all("analysis" not in result for result in partial["model_results"])

    monkeypatch.setattr(
        nc,
        "_prediction_frame",
        lambda panel, feature_columns: _prediction_fixture(
            constant_models=set(reg.MODELS)
        ),
    )
    all_degenerate = nc.run_repetition(
        synthetic_raw, control=reg.NC0_NAME, repetition_id=reg.NC0_IDS[0]
    )
    assert all_degenerate["status"] == reg.ALL_MODEL_DEGENERACY_STATUS
    assert set(all_degenerate["degenerate_models"]) == set(reg.MODELS)
    assert len(all_degenerate["model_results"]) == 6


def test_unexpected_model_or_construction_exception_is_integrity_failure(
    synthetic_raw, monkeypatch
):
    monkeypatch.setattr(
        nc,
        "_prediction_frame",
        lambda panel, feature_columns: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    with pytest.raises(nc.Stage2IntegrityError, match="INTEGRITY_FAILURE"):
        nc.run_repetition(
            synthetic_raw, control=reg.NC0_NAME, repetition_id=reg.NC0_IDS[0]
        )


def test_gate_has_exact_64_pass_65_fail_and_incomplete_inconclusive():
    nc0_64 = [_gate_record(reg.NC0_NAME, 1000 + i, i < 64) for i in range(1000)]
    nc1_64 = [_gate_record(reg.NC1_NAME, 2000 + i, i < 64) for i in range(1000)]
    assert nc.evaluate_gate({reg.NC0_NAME: nc0_64, reg.NC1_NAME: nc1_64})["decision"] == "PASS"

    nc0_65 = [_gate_record(reg.NC0_NAME, 1000 + i, i < 65) for i in range(1000)]
    assert nc.evaluate_gate({reg.NC0_NAME: nc0_65, reg.NC1_NAME: nc1_64})["decision"] == "FAIL"

    nc0_incomplete = nc0_64[:-1]
    assert nc.evaluate_gate(
        {reg.NC0_NAME: nc0_incomplete, reg.NC1_NAME: nc1_64}
    )["decision"] == "INCONCLUSIVE"


def test_gate_fails_when_nc1_reaches_the_registered_critical_count():
    nc0_64 = [_gate_record(reg.NC0_NAME, 1000 + i, i < 64) for i in range(1000)]
    nc1_65 = [_gate_record(reg.NC1_NAME, 2000 + i, i < 65) for i in range(1000)]
    result = nc.evaluate_gate(
        {reg.NC0_NAME: nc0_64, reg.NC1_NAME: nc1_65}, integrity_passed=True
    )
    assert result["decision"] == "FAIL"
    assert result["status"] == "FAIL"


def test_integrity_failure_precedes_gate_for_complete_controls():
    nc0_64 = [_gate_record(reg.NC0_NAME, 1000 + i, i < 64) for i in range(1000)]
    nc1_64 = [_gate_record(reg.NC1_NAME, 2000 + i, i < 64) for i in range(1000)]
    result = nc.evaluate_gate(
        {reg.NC0_NAME: nc0_64, reg.NC1_NAME: nc1_64}, integrity_passed=False
    )
    assert result["decision"] == reg.UNEXPECTED_EXCEPTION_STATUS
    assert result["status"] == reg.UNEXPECTED_EXCEPTION_STATUS
    assert result["scientific_gate_evaluated"] is False


def test_diagnostic_rejections_cannot_change_confirmatory_gate():
    confirmatory = {
        reg.NC0_NAME: [_gate_record(reg.NC0_NAME, 1000 + i, i < 64) for i in range(1000)],
        reg.NC1_NAME: [_gate_record(reg.NC1_NAME, 2000 + i, i < 64) for i in range(1000)],
    }
    with_diagnostic = {
        **confirmatory,
        reg.NC0_DIAGNOSTIC_NAME: [
            _gate_record(reg.NC0_DIAGNOSTIC_NAME, 3000 + i, True)
            for i in range(1000)
        ],
    }
    assert nc.evaluate_gate(confirmatory)["decision"] == "PASS"
    result = nc.evaluate_gate(with_diagnostic)
    assert result["decision"] == "PASS"
    assert result["diagnostic_affects_gate"] is False
    assert result["diagnostic_excluded"] == reg.NC0_DIAGNOSTIC_NAME


def test_extra_invalid_repetition_cannot_be_ignored_by_gate():
    nc0 = [_gate_record(reg.NC0_NAME, 1000 + i, i < 64) for i in range(1000)]
    nc0.append(
        {
            "control": reg.NC0_NAME,
            "repetition_id": 9999,
            "status": reg.PARTIAL_MODEL_DEGENERACY_STATUS,
            "analyzable": False,
            "family_reject": False,
        }
    )
    nc1 = [_gate_record(reg.NC1_NAME, 2000 + i, i < 64) for i in range(1000)]
    assert nc.evaluate_gate({reg.NC0_NAME: nc0, reg.NC1_NAME: nc1})["decision"] == "INCONCLUSIVE"


def test_closed_integrity_contract_is_exact_and_excludes_scientific_quantities(
    valid_integrity_records,
):
    result = nc.evaluate_integrity(**_integrity_kwargs(valid_integrity_records))
    assert tuple(result["conditions"]) == reg.INTEGRITY_CONDITION_IDENTIFIERS
    assert result["failures"] == []
    assert result["passed"] is True
    assert result["excluded_from_every_check"] == list(reg.INTEGRITY_EXCLUSIONS)
    assert result["high_fpr_is_valid_science"] is True
    assert result["evaluated_before_scientific_gate"] is True

    high_fpr = [
        {
            **record,
            "family_reject": True,
            "family": {
                **record["family"],
                "family_reject": True,
                "min_raw_p": 0.001,
            },
        }
        for record in valid_integrity_records
    ]
    high_fpr_result = nc.evaluate_integrity(**_integrity_kwargs(high_fpr))
    assert high_fpr_result["passed"] is True


def test_integrity_detects_source_seed_output_and_model_cell_tampering(
    valid_integrity_records,
):
    source_failure = nc.evaluate_integrity(
        **_integrity_kwargs(
            valid_integrity_records,
            source_sha_after="f" * 64,
        )
    )
    assert "frozen_source_dataset_path_and_sha_match" in source_failure["failures"]

    seed_failure_records = copy.deepcopy(valid_integrity_records)
    seed_failure_records[0]["construction_seeds"]["noise_seed"] += 1
    seed_failure = nc.evaluate_integrity(
        **_integrity_kwargs(seed_failure_records)
    )
    assert "exact_seed_formulas_reproduce" in seed_failure["failures"]

    output_failure = nc.evaluate_integrity(
        **_integrity_kwargs(
            valid_integrity_records,
            output_paths=["experiments/results/escaped.csv"],
        )
    )
    assert "writes_confined_to_stage2_result_namespace" in output_failure["failures"]

    duplicate_failure_records = copy.deepcopy(valid_integrity_records)
    duplicate_failure_records[0]["model_results"].append(
        copy.deepcopy(duplicate_failure_records[0]["model_results"][0])
    )
    duplicate_failure = nc.evaluate_integrity(
        **_integrity_kwargs(duplicate_failure_records)
    )
    assert "no_duplicate_repetition_ids_or_model_cells" in duplicate_failure["failures"]
    assert "all_expected_model_cells_present_for_analyzable_repetitions" in duplicate_failure["failures"]


def test_integrity_accepts_explicit_registered_degeneracy_without_p_value_substitution():
    record = _valid_record(reg.NC0_NAME, reg.NC0_IDS[0])
    record["status"] = reg.PARTIAL_MODEL_DEGENERACY_STATUS
    record["classification"] = reg.PARTIAL_MODEL_DEGENERACY_STATUS
    record["analyzable"] = False
    record.pop("family")
    record["degenerate_models"] = {reg.MODELS[0]: [{"reason": "prediction <2 distinct finite values"}]}
    for model_result in record["model_results"]:
        if model_result["model"] == reg.MODELS[0]:
            model_result["status"] = "DEGENERATE_MODEL"
            model_result.pop("analysis")
        else:
            model_result["status"] = "NOT_ANALYZED_DUE_TO_REPETITION_DEGENERACY"
            model_result.pop("analysis")
    ok, detail = nc._finite_or_registered_degeneracy([record])
    assert ok, detail
    record["model_results"][1]["analysis"] = {
        "pooled": {
            "observed_ic": 0.0,
            "permutation_p_value_two_sided": 1.0,
            "bootstrap_ci_95": [-0.1, 0.1],
        }
    }
    ok, _ = nc._finite_or_registered_degeneracy([record])
    assert ok is False


def test_lifecycle_refuses_nonempty_root_and_requires_crash_recovery(tmp_path, monkeypatch):
    root = tmp_path / "negative_control"
    monkeypatch.setattr(nc, "RESULT_ROOT", root)
    prepared, marker, payload, attempt = nc._prepare_attempt(repeat_after_crash=False)
    assert prepared == root
    assert attempt == 1
    assert marker.name == nc.ATTEMPT_MARKER_FILENAME
    assert marker.is_file()
    assert not (root / nc.STAGING_DIRNAME).exists()
    with pytest.raises(nc.Stage2Error, match="repeat-after-crash"):
        nc._prepare_attempt(repeat_after_crash=False)

    (root / nc.STAGING_DIRNAME).mkdir()
    (root / nc.STAGING_DIRNAME / "partial.tmp").write_text("partial", encoding="utf-8")
    _, recovered_marker, recovered, recovered_number = nc._prepare_attempt(
        repeat_after_crash=True
    )
    assert recovered_marker == marker
    assert recovered_number == 2
    assert recovered["attempts"][0]["completion_status"] == "incomplete"
    assert recovered["attempts"][1]["completion_status"] == "in_progress"
    assert not (root / nc.STAGING_DIRNAME).exists()
    assert payload["registered_configuration_sha256"] == recovered[
        "registered_configuration_sha256"
    ]


def test_run_cannot_be_redirected_outside_registered_namespace(tmp_path, monkeypatch):
    redirected = tmp_path / "redirected"
    monkeypatch.setattr(nc, "RESULT_ROOT", redirected)
    with pytest.raises(nc.Stage2IntegrityError, match="registered result namespace"):
        nc.run(progress=False)
    assert not redirected.exists()


def test_output_audit_rejects_nested_or_unexpected_files(tmp_path):
    surface = tmp_path / "attempt-1"
    surface.mkdir()
    for name in nc.SCIENTIFIC_EMITTED_FILENAMES:
        (surface / name).write_text("fixture", encoding="utf-8")
    assert nc._audit_output_surface(
        surface, expected_names=nc.SCIENTIFIC_EMITTED_FILENAMES
    )["passed"] is True
    nested = surface / "unexpected"
    nested.mkdir()
    (nested / "extra.txt").write_text("extra", encoding="utf-8")
    audit = nc._audit_output_surface(
        surface, expected_names=nc.SCIENTIFIC_EMITTED_FILENAMES
    )
    assert audit["passed"] is False
    assert "unexpected/extra.txt" in audit["unexpected_files"]
    assert "unexpected" in audit["unexpected_directories"]


def test_significance_source_sha_and_historical_roots_are_unchanged():
    assert _sha256(SIGNIFICANCE_PATH) == reg.SIGNIFICANCE_SHA256
    assert _sha256(DATASET_PATH) == reg.DATASET_SHA256
    assert not STAGE2_ROOT.exists()
    for path in (
        REPO_ROOT / "experiments/results_thesis/positive_control",
        REPO_ROOT / "experiments/results_thesis/positive_control_calibration",
    ):
        assert path.is_dir()
