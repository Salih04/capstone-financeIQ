"""Stage 2 registered negative-control apparatus.

The module is deliberately inert until ``--run`` is supplied.  Importing it,
calling :func:`registered_plan`, and running the replay probe do not create the
Stage 2 result namespace or write scientific artifacts.

The registration in ``docs/thesis/STAGE_2_REGISTRATION.md`` is the authority.
This runner therefore keeps the construction layer, the canonical walk-forward
evaluation, the significance layer, and the governance layer separate.  In
particular, NC1 permutes the complete target panel before split construction,
and NC0 permutes one real missingness-mask row matrix jointly across all forty
feature columns before the canonical rank transform.
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
import subprocess
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import NormalDist
from typing import Any, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments import run_experiments as rx  # noqa: E402
from experiments import significance as sig  # noqa: E402
from experiments.placebo_lab import validate_claim_safety_text  # noqa: E402
from experiments.thesis import provenance as prov  # noqa: E402
from experiments.thesis import stage2_registration as reg  # noqa: E402

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor  # noqa: E402
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge  # noqa: E402


# --------------------------------------------------------------------------- #
# Registered identity and output namespace
# --------------------------------------------------------------------------- #
SLUG = reg.STAGE2_SLUG
RESULT_ROOT = prov.THESIS_RESULTS_ROOT / SLUG
STAGE_1_RESULT_ROOT = prov.THESIS_RESULTS_ROOT / "positive_control"
STAGE_1B_RESULT_ROOT = prov.THESIS_RESULTS_ROOT / "positive_control_calibration"

DATASET_PATH = ROOT / reg.DATASET_PATH
TARGET_COLUMN = reg.TARGET_COLUMN
TARGET_RETURN_COLUMN = "target_return"
FEATURE_YEAR_COLUMN = "feature_year"
TARGET_YEAR_COLUMN = "target_year"
MODEL_FAMILY = reg.MODELS
MODEL_FAMILY_DIVISOR = 6
PERMUTATIONS = reg.PERMUTATIONS
BOOTSTRAPS = reg.BOOTSTRAPS
BASE_SEED = reg.BASE_SEED
MODELS = MODEL_FAMILY
MODEL_CONFIGS = reg.MODEL_CONFIGS
CONTROL_NAMES = reg.CONTROL_NAMES
CONFIRMATORY_CONTROLS = reg.CONTROL_NAMES
DIAGNOSTIC_NAMES = reg.DIAGNOSTIC_NAMES
DIAGNOSTIC_CONTROLS = reg.DIAGNOSTIC_NAMES
REPETITION_ID_MATRICES = reg.EXPECTED_REPETITION_ID_MATRICES
NC0_IDS = reg.NC0_IDS
NC1_IDS = reg.NC1_IDS
NC0_DIAGNOSTIC_IDS = reg.NC0_DIAGNOSTIC_IDS
CONSTRUCTION_STREAMS = reg.CONSTRUCTION_STREAMS
PARTIAL_MODEL_DEGENERACY_STATUS = reg.PARTIAL_MODEL_DEGENERACY_STATUS
ALL_MODEL_DEGENERACY_STATUS = reg.ALL_MODEL_DEGENERACY_STATUS
INTEGRITY_FAILURE_STATUS = reg.UNEXPECTED_EXCEPTION_STATUS

OUTPUT_FILENAMES = {
    "report_json": "negative_control_report.json",
    "report_md": "negative_control_report.md",
    "repetitions": "repetitions.csv",
    "control_summary": "control_summary.csv",
    "diagnostic_repetitions": "diagnostic_repetitions.csv",
}
MANIFEST_FILENAME = "artifact_manifest.json"
ATTEMPT_MARKER_FILENAME = "attempt_provenance.json"
STAGING_DIRNAME = ".staging"
IGNORABLE_OS_METADATA: frozenset[str] = frozenset({".DS_Store"})
SCIENTIFIC_EMITTED_FILENAMES: tuple[str, ...] = tuple(
    sorted(OUTPUT_FILENAMES.values())
)
EMITTED_FILENAMES: tuple[str, ...] = tuple(
    sorted([*SCIENTIFIC_EMITTED_FILENAMES, MANIFEST_FILENAME])
)
OPERATIONAL_FILENAMES: tuple[str, ...] = (ATTEMPT_MARKER_FILENAME,)
ANALYZABLE_STATUS = "ANALYZABLE"

PROTECTED_DATA_ROOTS: tuple[str, ...] = (
    "data/trusted",
    "data/trusted_clean",
    "data/trusted_raw",
    "data/provenance",
)


class Stage2Error(RuntimeError):
    """Raised when a requested operation is outside the registered apparatus."""


class Stage2IntegrityError(Stage2Error):
    """Raised when the closed Stage 2 integrity contract fails."""


class Stage2ModelDegeneracy(Stage2Error):
    """Internal representation of a registered model-level degeneracy."""

    def __init__(self, model: str, reasons: list[dict[str, Any]]) -> None:
        self.model = model
        self.reasons = reasons
        super().__init__(f"model {model!r} is degenerate: {reasons}")


# --------------------------------------------------------------------------- #
# Small deterministic and filesystem helpers
# --------------------------------------------------------------------------- #
def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return prov.sha256_path(path)


def _canonical_json(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _rounded(value: float | int | None, digits: int = 12) -> float | None:
    if value is None:
        return None
    value = float(value)
    if not math.isfinite(value):
        return None
    return round(value, digits)


def _git_metadata() -> dict[str, Any]:
    def _git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    try:
        sha = _git("rev-parse", "HEAD")
        dirty = bool(_git("status", "--porcelain", "--untracked-files=normal"))
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "short_sha": "nogit", "dirty": None}
    return {"sha": sha, "short_sha": sha[:8], "dirty": dirty}


def implementation_hash() -> str:
    """Hash this runner for the future manifest; does not read the dataset."""
    return _sha256_path(Path(__file__).resolve())


def registration_hash() -> str:
    return _sha256_path(ROOT / "experiments/thesis/stage2_registration.py")


def tree_digest(root: Path) -> dict[str, str]:
    """Return a repo-relative digest of every file below ``root``."""
    if not root.is_dir() or root.is_symlink():
        return {}
    return {
        path.relative_to(ROOT).as_posix(): _sha256_path(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def protected_data_digest() -> dict[str, str]:
    digest: dict[str, str] = {}
    for relative in PROTECTED_DATA_ROOTS:
        digest.update(tree_digest(ROOT / relative))
    return digest


def workspace_digest_excluding_stage2() -> dict[str, str]:
    """Digest persistent files outside the Stage 2 result namespace."""
    stage_root = RESULT_ROOT.resolve()
    digest: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.is_symlink():
            continue
        try:
            path.resolve().relative_to(stage_root)
        except ValueError:
            digest[path.relative_to(ROOT).as_posix()] = _sha256_path(path)
    return digest


def _relative_to_repo(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


# --------------------------------------------------------------------------- #
# Registration identity and seed schedules
# --------------------------------------------------------------------------- #
def _seed_fields(control: str, repetition_id: int) -> dict[str, int]:
    if control == reg.NC0_NAME:
        return {
            "noise_seed": reg.construction_seed(
                reg.CONSTRUCTION_STREAMS["NC0_NOISE"], repetition_id
            ),
            "mask_permutation_seed": reg.construction_seed(
                reg.CONSTRUCTION_STREAMS["NC0_MASK_ROW_PERMUTATION"], repetition_id
            ),
        }
    if control == reg.NC1_NAME:
        return {
            "target_permutation_seed": reg.construction_seed(
                reg.CONSTRUCTION_STREAMS["NC1_TARGET_PERMUTATION"], repetition_id
            ),
        }
    if control == reg.NC0_DIAGNOSTIC_NAME:
        return {
            "diagnostic_noise_seed": reg.construction_seed(
                reg.CONSTRUCTION_STREAMS["NC0_DIAGNOSTIC_NOISE"], repetition_id
            ),
        }
    raise Stage2Error(f"unknown Stage 2 control {control!r}")


def _seed_schedule() -> list[dict[str, Any]]:
    schedule: list[dict[str, Any]] = []
    for control in (
        reg.NC0_NAME,
        reg.NC1_NAME,
        reg.NC0_DIAGNOSTIC_NAME,
    ):
        for repetition_id in reg.EXPECTED_REPETITION_ID_MATRICES[control]:
            schedule.append(
                {
                    "control": control,
                    "repetition_id": int(repetition_id),
                    "construction_seeds": _seed_fields(control, int(repetition_id)),
                    "significance_seed": reg.significance_seed(int(repetition_id)),
                }
            )
    return schedule


def registered_configuration() -> dict[str, Any]:
    """Return the complete non-tunable design identity for attempt provenance."""
    return {
        "experiment": SLUG,
        "result_root": reg.RESULT_ROOT,
        "dataset_path": reg.DATASET_PATH,
        "dataset_sha256": reg.DATASET_SHA256,
        "significance_sha256": reg.SIGNIFICANCE_SHA256,
        "source_module_hashes": dict(reg.SOURCE_MODULE_HASHES),
        "target_column": reg.TARGET_COLUMN,
        "feature_years": list(reg.FEATURE_YEARS),
        "target_years": list(reg.TARGET_YEARS),
        "feature_column_count": reg.CANONICAL_FEATURE_COLUMN_COUNT,
        "rank_method": reg.CANONICAL_RANK_METHOD,
        "rank_percentile": reg.CANONICAL_RANK_PERCENTILE,
        "imputation": reg.CANONICAL_IMPUTATION,
        "imputation_value": reg.CANONICAL_IMPUTATION_VALUE,
        "splits": [
            {
                "name": split["name"],
                "train_target_years": list(split["train_target_years"]),
                "test_feature_year": split["test_feature_year"],
            }
            for split in reg.CANONICAL_SPLITS
        ],
        "models": list(reg.MODELS),
        "model_configs": {
            name: {
                "kind": config["kind"],
                "parameters": dict(config["parameters"]),
                "seed": config["seed"],
            }
            for name, config in reg.MODEL_CONFIGS.items()
        },
        "model_family_divisor": 6,
        "alpha": reg.MODEL_ALPHA,
        "permutations": reg.PERMUTATIONS,
        "bootstraps": reg.BOOTSTRAPS,
        "construction_streams": dict(reg.CONSTRUCTION_STREAMS),
        "construction_seed_formula": reg.CONSTRUCTION_SEED_FORMULA,
        "significance_seed_formula": reg.SIGNIFICANCE_SEED_FORMULA,
        "repetition_id_matrices": {
            name: list(ids)
            for name, ids in reg.EXPECTED_REPETITION_ID_MATRICES.items()
        },
        "seed_schedule_sha256": _sha256_bytes(_canonical_json(_seed_schedule())),
        "strict_complete_denominator": reg.STRICT_COMPLETE_DENOMINATOR,
        "min_analyzable_denominator": reg.MIN_ANALYZABLE_DENOMINATOR,
        "control_family_size": reg.CONTROL_DECISION_FAMILY_SIZE,
        "exact_k_crit_r1000": reg.EXACT_K_CRIT_R1000,
        "equivalence_delta": reg.EQUIVALENCE_DELTA,
    }


def registered_configuration_digest() -> str:
    return _sha256_bytes(_canonical_json(registered_configuration()))


def _collision_report() -> dict[str, Any]:
    """Exhaustively check all registered construction and significance streams."""
    construction_inputs: list[tuple[str, int, int]] = []
    for stream_name, repetition_ids in (
        ("NC0_NOISE", reg.NC0_IDS),
        ("NC0_MASK_ROW_PERMUTATION", reg.NC0_IDS),
        ("NC1_TARGET_PERMUTATION", reg.NC1_IDS),
        ("NC0_DIAGNOSTIC_NOISE", reg.NC0_DIAGNOSTIC_IDS),
    ):
        stream = reg.CONSTRUCTION_STREAMS[stream_name]
        for repetition_id in repetition_ids:
            construction_inputs.append((stream_name, int(repetition_id), stream))

    construction_values: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for stream_name, repetition_id, stream in construction_inputs:
        construction_values[reg.construction_seed(stream, repetition_id)].append(
            (stream_name, repetition_id)
        )
    construction_collisions = {
        seed: labels for seed, labels in construction_values.items() if len(labels) > 1
    }

    construction_seeds = set(construction_values)
    stage2_significance = {
        reg.significance_seed(int(repetition_id)) for repetition_id in reg.ALL_STAGE2_IDS
    }
    historical_significance = {
        reg.SIGNIFICANCE_DEFAULT_SEED + repetition_id for repetition_id in range(0, 600)
    }
    historical_construction = {
        base_seed * 1_000_003 + level * 10_007 + repetition_id
        for base_seed in (42, 43, 44)
        for level in range(6)
        for repetition_id in range(0, 600)
    }
    return {
        "construction_count": len(construction_inputs),
        "construction_unique": len(construction_seeds) == len(construction_inputs),
        "construction_collisions": construction_collisions,
        "stream_ids_unique": len(set(reg.CONSTRUCTION_STREAMS.values()))
        == len(reg.CONSTRUCTION_STREAMS),
        "construction_significance_disjoint": construction_seeds.isdisjoint(
            stage2_significance
        ),
        "construction_historical_disjoint": construction_seeds.isdisjoint(
            historical_construction
        ),
        "construction_historical_significance_disjoint": construction_seeds.isdisjoint(
            historical_significance
        ),
        "stage2_significance_historical_disjoint": stage2_significance.isdisjoint(
            historical_significance
        ),
        "reserved_gap_disjoint": set(reg.RESERVED_IDS).isdisjoint(
            set(reg.ALL_STAGE2_IDS)
        ),
        "passed": (
            len(construction_seeds) == len(construction_inputs)
            and not construction_collisions
            and len(set(reg.CONSTRUCTION_STREAMS.values()))
            == len(reg.CONSTRUCTION_STREAMS)
            and construction_seeds.isdisjoint(stage2_significance)
            and construction_seeds.isdisjoint(historical_construction)
            and construction_seeds.isdisjoint(historical_significance)
            and stage2_significance.isdisjoint(historical_significance)
            and set(reg.RESERVED_IDS).isdisjoint(set(reg.ALL_STAGE2_IDS))
        ),
    }


def construction_seed(stream: int, repetition_id: int) -> int:
    """Public arithmetic-only alias for the registered construction formula."""
    return reg.construction_seed(stream, repetition_id)


def significance_seed(repetition_id: int) -> int:
    return reg.significance_seed(repetition_id)


# --------------------------------------------------------------------------- #
# Canonical panel and construction mechanisms
# --------------------------------------------------------------------------- #
def _feature_columns(raw: pd.DataFrame) -> list[str]:
    columns = sorted(rx._feature_cols(raw))
    if len(columns) != reg.CANONICAL_FEATURE_COLUMN_COUNT:
        raise Stage2IntegrityError(
            f"canonical source exposes {len(columns)} features, expected 40"
        )
    return columns


def _assert_canonical_source(raw: pd.DataFrame) -> list[str]:
    required = {"ticker", "year", TARGET_COLUMN}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise Stage2IntegrityError(f"canonical source is missing columns: {missing}")
    feature_columns = _feature_columns(raw)
    if raw.duplicated(["ticker", "year"]).any():
        raise Stage2IntegrityError("canonical source contains duplicate ticker/year keys")
    target_values = pd.to_numeric(raw[TARGET_COLUMN], errors="coerce")
    nonfinite_targets = target_values.notna() & ~np.isfinite(target_values)
    if bool(nonfinite_targets.any()):
        raise Stage2IntegrityError("canonical source contains non-finite observed targets")
    if tuple(feature_columns) != tuple(sorted(feature_columns)):
        raise Stage2IntegrityError("feature columns are not in fixed sorted order")
    return feature_columns


def _panel_skeleton(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    feature_columns = _assert_canonical_source(raw)
    source = raw.loc[raw["year"].isin(reg.FEATURE_YEARS)].copy(deep=True)
    source = source.sort_values(["year", "ticker"], kind="mergesort").reset_index(
        drop=True
    )
    source["year"] = pd.to_numeric(source["year"], errors="raise").astype(int)
    panel = source[["ticker", "year", *feature_columns, TARGET_COLUMN]].copy()
    panel = panel.rename(columns={"year": FEATURE_YEAR_COLUMN})
    panel[TARGET_YEAR_COLUMN] = panel[FEATURE_YEAR_COLUMN] + 1
    panel[TARGET_RETURN_COLUMN] = panel[TARGET_COLUMN].copy(deep=True)
    panel = panel[
        [
            "ticker",
            FEATURE_YEAR_COLUMN,
            TARGET_YEAR_COLUMN,
            *feature_columns,
            TARGET_COLUMN,
            TARGET_RETURN_COLUMN,
        ]
    ]
    return panel, feature_columns


def canonical_rank_percentile(
    panel: pd.DataFrame, feature_columns: Sequence[str]
) -> pd.DataFrame:
    """Apply the exact canonical average-rank percentile transform."""
    ranked = panel.copy(deep=True)
    for column in feature_columns:
        ranked[column] = ranked.groupby(FEATURE_YEAR_COLUMN, sort=True)[column].rank(
            method="average", pct=True
        )
    return ranked


def build_real_panel(raw: pd.DataFrame) -> pd.DataFrame:
    panel, feature_columns = _panel_skeleton(raw)
    return canonical_rank_percentile(panel, feature_columns)


def generate_iid_noise(rows: int, columns: int, seed: int) -> np.ndarray:
    if rows < 0 or columns < 0:
        raise ValueError("noise shape must be non-negative")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=(rows, columns))


def jointly_permute_mask(
    mask: np.ndarray | pd.DataFrame,
    feature_years: Sequence[int] | pd.Series,
    seed: int,
    *,
    return_permutations: bool = False,
) -> np.ndarray | tuple[np.ndarray, dict[int, list[int]]]:
    """Permute mask rows jointly across all columns, once per feature year."""
    source = mask.to_numpy(dtype=bool, copy=True) if isinstance(mask, pd.DataFrame) else np.asarray(mask, dtype=bool)
    if source.ndim != 2:
        raise ValueError("missingness mask must be a two-dimensional matrix")
    years = np.asarray(feature_years)
    if len(years) != len(source):
        raise ValueError("feature-year vector and mask row count differ")
    result = source.copy()
    rng = np.random.default_rng(seed)
    permutations: dict[int, list[int]] = {}
    for year in sorted({int(value) for value in years.tolist()}):
        positions = np.flatnonzero(years == year)
        order = rng.permutation(len(positions))
        result[positions, :] = source[positions[order], :]
        permutations[year] = [int(value) for value in order.tolist()]
    if return_permutations:
        return result, permutations
    return result


permute_mask_jointly = jointly_permute_mask


def _array_digest(values: np.ndarray) -> str:
    return _sha256_bytes(np.ascontiguousarray(values).tobytes())


def _masked_noise_panel(
    raw: pd.DataFrame,
    *,
    noise_seed: int,
    mask_seed: int | None,
    permute_rows: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    skeleton, feature_columns = _panel_skeleton(raw)
    real_mask = skeleton[feature_columns].isna().to_numpy(dtype=bool)
    noise = generate_iid_noise(len(skeleton), len(feature_columns), noise_seed)
    if permute_rows:
        permuted_mask, permutations = jointly_permute_mask(
            real_mask,
            skeleton[FEATURE_YEAR_COLUMN],
            int(mask_seed),
            return_permutations=True,
        )
    else:
        permuted_mask = real_mask.copy()
        permutations = {
            int(year): list(range(int(np.sum(skeleton[FEATURE_YEAR_COLUMN] == year))))
            for year in reg.FEATURE_YEARS
            if bool(np.any(skeleton[FEATURE_YEAR_COLUMN] == year))
        }
    masked_noise = np.where(permuted_mask, np.nan, noise)
    constructed = skeleton.copy(deep=True)
    constructed[feature_columns] = masked_noise
    ranked = canonical_rank_percentile(constructed, feature_columns)
    metadata = {
        "feature_columns": list(feature_columns),
        "real_mask": real_mask,
        "permuted_mask": permuted_mask,
        "noise": noise,
        "masked_noise": masked_noise,
        "noise_seed": int(noise_seed),
        "mask_seed": None if mask_seed is None else int(mask_seed),
        "mask_row_permuted": bool(permute_rows),
        "joint_mask_permutation": bool(permute_rows),
        "permutations": permutations,
        "mask_row_alignment_changed": bool(
            permute_rows
            and any(
                order != list(range(len(order)))
                for order in permutations.values()
            )
        ),
        "noise_sha256": _array_digest(noise),
        "masked_noise_sha256": _array_digest(np.nan_to_num(masked_noise, nan=0.0)),
    }
    return ranked, metadata


def _validate_repetition_id(control: str, repetition_id: int) -> None:
    expected = reg.EXPECTED_REPETITION_ID_MATRICES.get(control)
    if expected is None or int(repetition_id) not in expected:
        raise Stage2Error(
            f"repetition {repetition_id!r} is outside the registered {control} matrix"
        )


def _build_nc0_panel_with_metadata(
    raw: pd.DataFrame, repetition_id: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    _validate_repetition_id(reg.NC0_NAME, repetition_id)
    noise_seed = reg.construction_seed(
        reg.CONSTRUCTION_STREAMS["NC0_NOISE"], int(repetition_id)
    )
    mask_seed = reg.construction_seed(
        reg.CONSTRUCTION_STREAMS["NC0_MASK_ROW_PERMUTATION"], int(repetition_id)
    )
    panel, metadata = _masked_noise_panel(
        raw,
        noise_seed=noise_seed,
        mask_seed=mask_seed,
        permute_rows=True,
    )
    metadata.update(
        {
            "nc0_noise_seed": noise_seed,
            "mask_row_permutation_seed": mask_seed,
        }
    )
    return panel, metadata


def build_nc0_panel(
    raw: pd.DataFrame, repetition_id: int, *, return_metadata: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    panel, metadata = _build_nc0_panel_with_metadata(raw, repetition_id)
    return (panel, metadata) if return_metadata else panel


def _build_diagnostic_panel_with_metadata(
    raw: pd.DataFrame, repetition_id: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    _validate_repetition_id(reg.NC0_DIAGNOSTIC_NAME, repetition_id)
    noise_seed = reg.construction_seed(
        reg.CONSTRUCTION_STREAMS["NC0_DIAGNOSTIC_NOISE"], int(repetition_id)
    )
    panel, metadata = _masked_noise_panel(
        raw,
        noise_seed=noise_seed,
        mask_seed=None,
        permute_rows=False,
    )
    metadata["diagnostic_noise_seed"] = noise_seed
    return panel, metadata


def build_nc0_diagnostic_panel(
    raw: pd.DataFrame, repetition_id: int, *, return_metadata: bool = False
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    panel, metadata = _build_diagnostic_panel_with_metadata(raw, repetition_id)
    return (panel, metadata) if return_metadata else panel


def _permute_targets_within_year(
    panel: pd.DataFrame, *, seed: int
) -> tuple[pd.DataFrame, dict[int, list[int]]]:
    """Permute all observed targets in the complete target panel."""
    result = panel.copy(deep=True)
    values = result[TARGET_COLUMN].copy(deep=True)
    rng = np.random.default_rng(seed)
    permutations: dict[int, list[int]] = {}
    for target_year in sorted(reg.TARGET_YEARS):
        positions = np.flatnonzero(
            result[TARGET_YEAR_COLUMN].to_numpy(dtype=int) == target_year
        )
        observed_positions = positions[
            ~pd.isna(values.iloc[positions]).to_numpy(dtype=bool)
        ]
        order = rng.permutation(len(observed_positions))
        source_values = values.iloc[observed_positions].to_numpy(copy=True)
        permuted_values = source_values[order]
        result.iloc[observed_positions, result.columns.get_loc(TARGET_COLUMN)] = (
            permuted_values
        )
        result.iloc[
            observed_positions, result.columns.get_loc(TARGET_RETURN_COLUMN)
        ] = permuted_values
        permutations[target_year] = [int(value) for value in order.tolist()]
    return result, permutations


def build_nc1_panel(
    raw: pd.DataFrame,
    repetition_id: int,
    *,
    return_metadata: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, dict[str, Any]]:
    _validate_repetition_id(reg.NC1_NAME, repetition_id)
    panel = build_real_panel(raw)
    permuted, permutations = _permute_targets_within_year(
        panel,
        seed=reg.construction_seed(
            reg.CONSTRUCTION_STREAMS["NC1_TARGET_PERMUTATION"], int(repetition_id)
        ),
    )
    metadata = {
        "feature_columns": list(
            _feature_columns(raw)
        ),
        "target_permutation_seed": reg.construction_seed(
            reg.CONSTRUCTION_STREAMS["NC1_TARGET_PERMUTATION"], int(repetition_id)
        ),
        "target_permutations": permutations,
        "target_years_processed": list(reg.TARGET_YEARS),
        "complete_panel_before_splits": True,
        "test_year_only_construction": False,
    }
    return (permuted, metadata) if return_metadata else permuted


permute_targets_within_year = _permute_targets_within_year


# --------------------------------------------------------------------------- #
# Mechanism invariants
# --------------------------------------------------------------------------- #
def _series_equal(left: pd.Series, right: pd.Series) -> bool:
    return bool(left.equals(right))


def _series_byte_identical(left: pd.Series, right: pd.Series) -> bool:
    if left.dtype != right.dtype or len(left) != len(right):
        return False
    left_values = np.ascontiguousarray(left.to_numpy(copy=False))
    right_values = np.ascontiguousarray(right.to_numpy(copy=False))
    return left_values.tobytes() == right_values.tobytes()


def _row_keys(panel: pd.DataFrame) -> list[tuple[str, int]]:
    return [
        (str(ticker), int(year))
        for ticker, year in zip(
            panel["ticker"].tolist(), panel[FEATURE_YEAR_COLUMN].tolist()
        )
    ]


def _year_multiset(panel: pd.DataFrame, column: str) -> dict[int, np.ndarray]:
    values = pd.to_numeric(panel[column], errors="coerce")
    result: dict[int, np.ndarray] = {}
    for year in sorted(panel[TARGET_YEAR_COLUMN].unique()):
        observed = values[panel[TARGET_YEAR_COLUMN] == year].to_numpy(dtype=float)
        result[int(year)] = np.sort(observed[np.isfinite(observed)])
    return result


def _mask_pattern_multiset(mask: np.ndarray, years: Sequence[int]) -> dict[int, list[tuple[bool, ...]]]:
    years_array = np.asarray(years)
    result: dict[int, list[tuple[bool, ...]]] = {}
    for year in sorted({int(value) for value in years_array.tolist()}):
        positions = np.flatnonzero(years_array == year)
        result[year] = sorted(tuple(bool(value) for value in row) for row in mask[positions])
    return result


def _split_identity_matches() -> bool:
    actual = tuple(
        (
            split["name"],
            tuple(int(value) for value in split["train_target_years"]),
            int(split["test_feature_year"]),
        )
        for split in rx.SPLITS
    )
    expected = tuple(
        (
            split["name"],
            tuple(int(value) for value in split["train_target_years"]),
            int(split["test_feature_year"]),
        )
        for split in reg.CANONICAL_SPLITS
    )
    return actual == expected


def _check_mechanism_invariants(
    raw: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    control: str,
    metadata: dict[str, Any],
) -> dict[str, bool]:
    real_panel = build_real_panel(raw)
    feature_columns = list(metadata["feature_columns"])
    feature_matrix_unchanged = all(
        _series_equal(real_panel[column], panel[column]) for column in feature_columns
    )
    rows_unchanged = _row_keys(real_panel) == _row_keys(panel)
    null_mask_unchanged = _series_equal(
        real_panel[TARGET_COLUMN].isna(), panel[TARGET_COLUMN].isna()
    )
    target_multiset_unchanged = all(
        np.array_equal(left, right, equal_nan=True)
        for year, left in _year_multiset(real_panel, TARGET_COLUMN).items()
        for right in [_year_multiset(panel, TARGET_COLUMN).get(year, np.array([]))]
    )

    invariants: dict[str, bool] = {
        "row_universe_unchanged": bool(rows_unchanged),
        "target_null_locations_preserved": bool(null_mask_unchanged),
        "target_multiset_by_year_preserved": bool(target_multiset_unchanged),
        "canonical_splits_unchanged": _split_identity_matches(),
    }

    if control == reg.NC1_NAME:
        invariants["feature_matrix_unchanged"] = bool(feature_matrix_unchanged)
        target_changed = {
            int(year): not np.array_equal(
                real_panel.loc[
                    real_panel[TARGET_YEAR_COLUMN].eq(year), TARGET_COLUMN
                ].to_numpy(),
                panel.loc[panel[TARGET_YEAR_COLUMN].eq(year), TARGET_COLUMN].to_numpy(),
                equal_nan=True,
            )
            for year in reg.TARGET_YEARS
        }
        invariants.update(
            {
                "all_target_years_processed": metadata["target_years_processed"]
                == list(reg.TARGET_YEARS),
                "train_and_test_targets_use_permuted_panel": bool(
                    metadata["complete_panel_before_splits"]
                ),
                "no_test_only_construction": not bool(
                    metadata["test_year_only_construction"]
                ),
                "target_permutation_stream_used": metadata.get(
                    "target_permutation_seed"
                )
                is not None,
                # A finite random permutation may be the identity in a small
                # fixture.  Record that observation, but do not turn it into
                # an integrity or scientific gate.
                "target_changed_by_year": all(target_changed.values())
                if target_changed
                else False,
            }
        )
        return invariants

    real_mask = metadata["real_mask"]
    permuted_mask = metadata["permuted_mask"]
    if control == reg.NC0_NAME:
        expected_mask = jointly_permute_mask(
            real_mask,
            real_panel[FEATURE_YEAR_COLUMN],
            int(metadata["mask_seed"]),
        )
    else:
        expected_mask = real_mask.copy()
    counts_preserved = all(
        np.array_equal(
            real_mask[np.asarray(real_panel[FEATURE_YEAR_COLUMN]) == year].sum(axis=0),
            permuted_mask[np.asarray(real_panel[FEATURE_YEAR_COLUMN]) == year].sum(axis=0),
        )
        for year in reg.FEATURE_YEARS
    )
    co_missingness_preserved = (
        _mask_pattern_multiset(real_mask, real_panel[FEATURE_YEAR_COLUMN])
        == _mask_pattern_multiset(permuted_mask, real_panel[FEATURE_YEAR_COLUMN])
    )
    rank_exact = True
    for index in range(len(feature_columns)):
        column = feature_columns[index]
        expected_ranked = real_panel.copy(deep=True)
        expected_ranked[column] = metadata["masked_noise"][:, index]
        expected_ranked = canonical_rank_percentile(expected_ranked, [column])
        rank_exact = rank_exact and _series_equal(panel[column], expected_ranked[column])
    invariants.update(
        {
            "target_byte_identical": _series_byte_identical(
                real_panel[TARGET_COLUMN], panel[TARGET_COLUMN]
            ),
            "target_return_byte_identical": _series_byte_identical(
                real_panel[TARGET_RETURN_COLUMN], panel[TARGET_RETURN_COLUMN]
            ),
            "fresh_iid_noise_construction": bool(
                metadata["noise"].shape == (len(real_panel), len(feature_columns))
                and np.isfinite(metadata["noise"]).all()
            ),
            "joint_mask_permutation_matches_registered_seed": bool(
                (metadata["joint_mask_permutation"] if control == reg.NC0_NAME else not metadata["joint_mask_permutation"])
                and np.array_equal(permuted_mask, expected_mask)
            ),
            "per_feature_year_missingness_counts_preserved": bool(counts_preserved),
            "rowwise_co_missingness_multiset_preserved": bool(co_missingness_preserved),
            "feature_matrix_replaced_from_real": bool(not feature_matrix_unchanged),
            "rank_transform_after_masking_exact": bool(rank_exact),
            "six_models_and_splits_unchanged": _split_identity_matches()
            and tuple(reg.MODELS) == tuple(MODEL_FAMILY),
        }
    )
    if control == reg.NC0_NAME:
        invariants["mask_row_alignment_changed"] = bool(
            metadata.get("mask_row_alignment_changed")
        )
    if control == reg.NC0_DIAGNOSTIC_NAME:
        invariants.update(
            {
                "diagnostic_isolated": True,
                "confirmatory_gate_excluded": True,
                "real_mask_alignment_retained": bool(
                    not metadata["mask_row_permuted"]
                ),
            }
        )
    return invariants


def mechanism_invariants(
    raw: pd.DataFrame, panel: pd.DataFrame, *, control: str, metadata: dict[str, Any]
) -> dict[str, bool]:
    """Public pure invariant checker used by focused fixture tests."""
    return _check_mechanism_invariants(
        raw, panel, control=control, metadata=metadata
    )


# --------------------------------------------------------------------------- #
# Registered six-model evaluation and strict degeneracy handling
# --------------------------------------------------------------------------- #
def _assert_registered_runtime_contract() -> None:
    ml_models = tuple(
        name for name, (kind, _function) in rx.MODELS.items() if kind == "ml"
    )
    if ml_models != tuple(reg.MODELS):
        raise Stage2IntegrityError(
            f"canonical ML family drifted: {ml_models!r} != {tuple(reg.MODELS)!r}"
        )
    if any(
        reg.MODEL_CONFIGS[name] != rx.MODEL_CONFIGS[name] for name in reg.MODELS
    ):
        raise Stage2IntegrityError("registered model configuration differs from canonical source")
    if not _split_identity_matches():
        raise Stage2IntegrityError("canonical split definitions differ from registration")
    if reg.MODEL_FAMILY_DIVISOR != 6:
        raise Stage2IntegrityError("registered model-family divisor is not literal 6")


def _make_model(name: str):
    if name == "linear_regression":
        return LinearRegression()
    if name == "ridge":
        return Ridge(alpha=1.0)
    if name == "lasso":
        return Lasso(alpha=0.1, max_iter=5000)
    if name == "elasticnet":
        return ElasticNet(alpha=0.1, max_iter=5000)
    if name == "random_forest":
        return RandomForestRegressor(n_estimators=200, max_depth=4, random_state=42)
    if name == "gradient_boosting":
        return GradientBoostingRegressor(
            random_state=42, max_depth=2, n_estimators=120
        )
    raise Stage2IntegrityError(f"unregistered model requested: {name!r}")


def _fit_registered_model(
    name: str, x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray
) -> np.ndarray:
    model = _make_model(name)
    x_train_imputed = np.nan_to_num(x_train, nan=0.5)
    x_test_imputed = np.nan_to_num(x_test, nan=0.5)
    model.fit(x_train_imputed, y_train)
    return np.asarray(model.predict(x_test_imputed), dtype=float)


def _prediction_frame(panel: pd.DataFrame, feature_columns: Sequence[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for split in reg.CANONICAL_SPLITS:
        train = panel[
            (panel[FEATURE_YEAR_COLUMN] + 1).isin(split["train_target_years"])
        ]
        test = panel[panel[FEATURE_YEAR_COLUMN] == split["test_feature_year"]]
        x_train = train[list(feature_columns)].to_numpy(dtype=float)
        y_train = pd.to_numeric(train[TARGET_RETURN_COLUMN], errors="coerce").to_numpy(
            dtype=float
        )
        x_test = test[list(feature_columns)].to_numpy(dtype=float)
        y_test = pd.to_numeric(test[TARGET_RETURN_COLUMN], errors="coerce").to_numpy(
            dtype=float
        )
        train_observed = ~np.isnan(y_train)
        x_train = x_train[train_observed]
        y_train = y_train[train_observed]
        for model_name in reg.MODELS:
            predictions = _fit_registered_model(model_name, x_train, y_train, x_test)
            for ticker, actual, prediction in zip(
                test["ticker"].tolist(), y_test, predictions
            ):
                rows.append(
                    {
                        "ticker": str(ticker),
                        "year": int(split["test_feature_year"] + 1),
                        "model": model_name,
                        "y_true": float(actual) if np.isfinite(actual) else np.nan,
                        "y_pred": float(prediction)
                        if np.isfinite(prediction)
                        else float(prediction),
                        "split": str(split["name"]),
                    }
                )
    return pd.DataFrame(
        rows,
        columns=["ticker", "year", "model", "y_true", "y_pred", "split"],
    )


def _model_degeneracy(predictions: pd.DataFrame, model: str) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []
    model_frame = predictions[predictions["model"] == model]
    for split in sorted(model_frame["split"].dropna().unique().tolist()):
        group = model_frame[model_frame["split"] == split]
        y_true = pd.to_numeric(group["y_true"], errors="coerce").to_numpy(dtype=float)
        y_pred = pd.to_numeric(group["y_pred"], errors="coerce").to_numpy(dtype=float)
        finite = np.isfinite(y_true) & np.isfinite(y_pred)
        finite_true = y_true[finite]
        finite_pred = y_pred[finite]
        if np.any(np.isfinite(y_true) & ~np.isfinite(y_pred)):
            reasons.append(
                {"split": str(split), "reason": "prediction contains non-finite values"}
            )
        if np.any(~np.isfinite(y_true) & ~np.isnan(y_true)):
            reasons.append(
                {"split": str(split), "reason": "target contains non-finite values"}
            )
        if np.unique(finite_true).size < 2:
            reasons.append(
                {"split": str(split), "reason": "target <2 distinct finite values"}
            )
        if np.unique(finite_pred).size < 2:
            reasons.append(
                {"split": str(split), "reason": "prediction <2 distinct finite values"}
            )
        if finite_true.size == 0:
            reasons.append(
                {"split": str(split), "reason": "no finite paired observations"}
            )
            continue
        observed = sig.spearman_ic(finite_true, finite_pred)
        if not np.isfinite(observed):
            reasons.append(
                {"split": str(split), "reason": "non-finite observed Spearman"}
            )
    expected_splits = {split["name"] for split in reg.CANONICAL_SPLITS}
    absent_splits = sorted(expected_splits - set(model_frame["split"].dropna()))
    reasons.extend(
        {"split": str(split), "reason": "no evaluated split"} for split in absent_splits
    )
    return reasons


def _finite_analysis(result: dict[str, Any]) -> bool:
    pooled = result.get("pooled", {})
    values: list[float] = []
    for key in ("observed_ic", "permutation_p_value_two_sided"):
        try:
            value = float(pooled[key])
        except (KeyError, TypeError, ValueError):
            return False
        if not math.isfinite(value):
            return False
        values.append(value)
    ci = pooled.get("bootstrap_ci_95")
    if not isinstance(ci, list) or len(ci) != 2:
        return False
    return all(isinstance(value, (int, float)) and math.isfinite(float(value)) for value in ci)


def _family_result(model_results: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [result for result in model_results if result["status"] == ANALYZABLE_STATUS]
    if tuple(result["model"] for result in valid) != tuple(reg.MODELS):
        raise Stage2IntegrityError("family calculation did not receive exactly six model results")
    headline = min(
        valid,
        key=lambda result: (
            float(result["analysis"]["pooled"]["permutation_p_value_two_sided"]),
            result["model"],
        ),
    )
    min_raw_p = min(
        float(result["analysis"]["pooled"]["permutation_p_value_two_sided"])
        for result in valid
    )
    adjusted = min(1.0, 6 * min_raw_p)
    return {
        "min_raw_p": min_raw_p,
        "model_family_divisor": 6,
        "bonferroni_adjusted_p_value": adjusted,
        "family_reject": bool(adjusted < 0.05),
        "headline_model": headline["model"],
        "headline_tie_break": reg.HEADLINE_TIE_BREAK,
    }


def _construction_panel(
    raw: pd.DataFrame, control: str, repetition_id: int
) -> tuple[pd.DataFrame, dict[str, Any]]:
    if control == reg.NC0_NAME:
        return _build_nc0_panel_with_metadata(raw, repetition_id)
    if control == reg.NC1_NAME:
        return build_nc1_panel(raw, repetition_id, return_metadata=True)
    if control == reg.NC0_DIAGNOSTIC_NAME:
        return _build_diagnostic_panel_with_metadata(raw, repetition_id)
    raise Stage2Error(f"unknown Stage 2 control {control!r}")


def run_repetition(
    raw: pd.DataFrame,
    *,
    control: str,
    repetition_id: int,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
) -> dict[str, Any]:
    """Construct and evaluate one registered repetition without writing files."""
    _assert_registered_runtime_contract()
    _validate_repetition_id(control, repetition_id)
    if permutations != PERMUTATIONS or bootstraps != BOOTSTRAPS:
        raise Stage2IntegrityError(
            "registered Stage 2 repetitions require exactly 10,000 permutations "
            "and 10,000 bootstraps"
        )
    try:
        panel, metadata = _construction_panel(raw, control, int(repetition_id))
        metadata["repetition_id"] = int(repetition_id)
        feature_columns = list(metadata["feature_columns"])
        predictions = _prediction_frame(panel, feature_columns)
        degeneracy_by_model = {
            model: _model_degeneracy(predictions, model) for model in reg.MODELS
        }
    except Stage2Error:
        raise
    except Exception as exc:
        raise Stage2IntegrityError(
            f"INTEGRITY_FAILURE: unexpected construction or prediction exception "
            f"in control={control}, repetition={repetition_id}"
        ) from exc
    significance = reg.significance_seed(int(repetition_id))

    degenerate_models = {
        model: reasons for model, reasons in degeneracy_by_model.items() if reasons
    }
    model_results: list[dict[str, Any]] = []
    if degenerate_models:
        all_degenerate = len(degenerate_models) == 6
        classification = (
            reg.ALL_MODEL_DEGENERACY_STATUS
            if all_degenerate
            else reg.PARTIAL_MODEL_DEGENERACY_STATUS
        )
        for model in reg.MODELS:
            if model in degenerate_models:
                model_results.append(
                    {
                        "model": model,
                        "status": "DEGENERATE_MODEL",
                        "degeneracy": degenerate_models[model],
                        "significance_seed": significance,
                    }
                )
            else:
                model_results.append(
                    {
                        "model": model,
                        "status": "NOT_ANALYZED_DUE_TO_REPETITION_DEGENERACY",
                        "significance_seed": significance,
                    }
                )
        record: dict[str, Any] = {
            "control": control,
            "role": reg.CONTROL_ROLES[control],
            "repetition_id": int(repetition_id),
            "status": classification,
            "classification": classification,
            "analyzable": False,
            "significance_seed": significance,
            "permutations": PERMUTATIONS,
            "bootstraps": BOOTSTRAPS,
            "construction_seeds": _seed_fields(control, int(repetition_id)),
            "model_results": model_results,
            "degenerate_models": degenerate_models,
            "mechanism_invariants": _check_mechanism_invariants(
                raw, panel, control=control, metadata=metadata
            ),
            "prediction_rows": int(len(predictions)),
        }
        return record

    for model in reg.MODELS:
        model_predictions = predictions[predictions["model"] == model].copy()
        try:
            analysis = sig.analyze_model(
                model_predictions,
                permutations=permutations,
                bootstraps=bootstraps,
                seed=significance,
            )
        except sig.DegenerateStatisticError as exc:
            raise Stage2IntegrityError(
                f"pre-analysis degeneracy guard disagreed with significance.py for {model}: {exc}"
            ) from exc
        except Exception as exc:
            raise Stage2IntegrityError(
                f"unexpected exception in model={model}, repetition={repetition_id}"
            ) from exc
        if not _finite_analysis(analysis):
            raise Stage2IntegrityError(
                f"non-finite significance output in model={model}, repetition={repetition_id}"
            )
        model_results.append(
            {
                "model": model,
                "status": ANALYZABLE_STATUS,
                "significance_seed": significance,
                "analysis": analysis,
            }
        )

    family = _family_result(model_results)
    invariants = _check_mechanism_invariants(
        raw, panel, control=control, metadata=metadata
    )
    if control == reg.NC0_DIAGNOSTIC_NAME:
        invariants.update(
            {
                "diagnostic_isolated": True,
                "confirmatory_gate_excluded": True,
                "real_mask_alignment_retained": not metadata["mask_row_permuted"],
            }
        )
    return {
        "control": control,
        "role": reg.CONTROL_ROLES[control],
        "repetition_id": int(repetition_id),
        "status": ANALYZABLE_STATUS,
        "classification": ANALYZABLE_STATUS,
        "analyzable": True,
        "significance_seed": significance,
        "permutations": PERMUTATIONS,
        "bootstraps": BOOTSTRAPS,
        "construction_seeds": _seed_fields(control, int(repetition_id)),
        "model_results": model_results,
        "family": family,
        "family_reject": family["family_reject"],
        "mechanism_invariants": invariants,
        "prediction_rows": int(len(predictions)),
    }


def run_control(
    raw: pd.DataFrame,
    control: str,
    *,
    repetition_ids: Sequence[int] | None = None,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    progress: bool = False,
) -> list[dict[str, Any]]:
    ids = tuple(
        int(value)
        for value in (
            reg.EXPECTED_REPETITION_ID_MATRICES[control]
            if repetition_ids is None
            else repetition_ids
        )
    )
    if len(set(ids)) != len(ids):
        raise Stage2IntegrityError(f"duplicate repetition ids requested for {control}")
    for repetition_id in ids:
        _validate_repetition_id(control, repetition_id)
    records: list[dict[str, Any]] = []
    for repetition_id in ids:
        records.append(
            run_repetition(
                raw,
                control=control,
                repetition_id=repetition_id,
                permutations=permutations,
                bootstraps=bootstraps,
            )
        )
        if progress:
            print(f"[stage2] {control} repetition={repetition_id} done", flush=True)
    return records


def run_all(
    raw: pd.DataFrame,
    *,
    repetition_ids: Mapping[str, Sequence[int]] | None = None,
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
    progress: bool = False,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for control in (reg.NC0_NAME, reg.NC1_NAME, reg.NC0_DIAGNOSTIC_NAME):
        ids = None if repetition_ids is None else repetition_ids.get(control)
        records.extend(
            run_control(
                raw,
                control,
                repetition_ids=ids,
                permutations=permutations,
                bootstraps=bootstraps,
                progress=progress,
            )
        )
    return records


# --------------------------------------------------------------------------- #
# Gate and descriptive summaries
# --------------------------------------------------------------------------- #
def wilson_interval(successes: int, trials: int, *, confidence: float = 0.95) -> list[float]:
    if trials < 1 or successes < 0 or successes > trials:
        raise ValueError("Wilson interval requires 0 <= successes <= trials and trials > 0")
    z = NormalDist().inv_cdf(0.5 + confidence / 2.0)
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (proportion + z * z / (2.0 * trials)) / denominator
    radius = z * math.sqrt(
        proportion * (1.0 - proportion) / trials + z * z / (4.0 * trials * trials)
    ) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def binomial_upper_tail(n: int, p: float, lower: int) -> float:
    if lower <= 0:
        return 1.0
    if lower > n:
        return 0.0
    return float(
        sum(
            math.comb(n, successes)
            * p**successes
            * (1.0 - p) ** (n - successes)
            for successes in range(lower, n + 1)
        )
    )


def _records_by_control(
    records: Sequence[dict[str, Any]] | Mapping[str, Sequence[dict[str, Any]]],
    diagnostic_records: Sequence[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if isinstance(records, Mapping):
        for control, values in records.items():
            for record in values:
                copy = dict(record)
                copy.setdefault("control", control)
                grouped[copy["control"]].append(copy)
    else:
        for record in records:
            if "control" in record:
                grouped[str(record["control"])].append(dict(record))
    if diagnostic_records is not None:
        for record in diagnostic_records:
            copy = dict(record)
            copy.setdefault("control", reg.NC0_DIAGNOSTIC_NAME)
            grouped[copy["control"]].append(copy)
    return dict(grouped)


def _equivalence_summary(
    records: Sequence[dict[str, Any]], model: str
) -> dict[str, Any]:
    values = [
        float(model_result["analysis"]["pooled"]["observed_ic"])
        for record in records
        if record.get("analyzable")
        for model_result in record.get("model_results", [])
        if model_result.get("model") == model
        and model_result.get("status") == ANALYZABLE_STATUS
    ]
    if not values:
        return {
            "model": model,
            "n": 0,
            "mean_pooled_ic": None,
            "ci_90": None,
            "delta": reg.EQUIVALENCE_DELTA,
            "equivalent_to_zero": None,
            "violation": None,
            "gating": False,
        }
    array = np.asarray(values, dtype=float)
    mean = float(np.mean(array))
    standard_error = (
        float(np.std(array, ddof=1) / math.sqrt(len(array))) if len(array) > 1 else 0.0
    )
    margin = NormalDist().inv_cdf(0.95) * standard_error
    low, high = mean - margin, mean + margin
    equivalent = bool(low >= -reg.EQUIVALENCE_DELTA and high <= reg.EQUIVALENCE_DELTA)
    return {
        "model": model,
        "n": len(values),
        "mean_pooled_ic": mean,
        "ci_90": [low, high],
        "delta": reg.EQUIVALENCE_DELTA,
        "equivalent_to_zero": equivalent,
        "violation": not equivalent,
        "gating": False,
        "interval_method": "normal approximation to the repetition-level pooled IC mean",
    }


def summarize_control(records: Sequence[dict[str, Any]], control: str) -> dict[str, Any]:
    if control not in reg.CONTROL_NAMES:
        raise Stage2Error("only confirmatory controls have a scientific gate summary")
    analyzable = [record for record in records if record.get("analyzable") is True]
    rejection_count = sum(bool(record.get("family_reject")) for record in analyzable)
    model_summaries = [_equivalence_summary(analyzable, model) for model in reg.MODELS]
    return {
        "control": control,
        "role": reg.CONTROL_ROLES[control],
        "registered_denominator": 1000,
        "analyzable_repetitions": len(analyzable),
        "invalid_repetitions": len(records) - len(analyzable),
        "rejection_count": int(rejection_count),
        "fpr_estimate": float(rejection_count / 1000),
        "wilson_95_pointwise": wilson_interval(rejection_count, 1000),
        "complete": len(records) == 1000 and len(analyzable) == 1000,
        "fails_if_complete": bool(
            len(records) == 1000 and len(analyzable) == 1000 and rejection_count >= 65
        ),
        "exact_upper_tail_at_boundary": binomial_upper_tail(
            1000, reg.CONTROL_NULL_FPR, rejection_count
        ),
        "equivalence": model_summaries,
        "equivalence_is_gating": False,
    }


def summarize_diagnostic(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "control": reg.NC0_DIAGNOSTIC_NAME,
        "role": reg.NC0_DIAGNOSTIC_ROLE,
        "registered_denominator": reg.R_DIAGNOSTIC,
        "analyzable_repetitions": sum(
            record.get("analyzable") is True for record in records
        ),
        "invalid_repetitions": sum(
            record.get("analyzable") is not True for record in records
        ),
        "model_family": list(reg.MODELS),
        "gate_member": False,
        "affects_stage2_gate": False,
        "scope_limitation": reg.NC0_DIAGNOSTIC_SCOPE_LIMITATION,
    }


def evaluate_gate(
    records: Sequence[dict[str, Any]] | Mapping[str, Sequence[dict[str, Any]]],
    *,
    integrity_passed: bool | Mapping[str, Any] = True,
) -> dict[str, Any]:
    """Evaluate only the registered two-control gate."""
    if isinstance(integrity_passed, Mapping):
        integrity_ok = bool(integrity_passed.get("passed"))
    else:
        integrity_ok = bool(integrity_passed)
    grouped = _records_by_control(records)
    summaries = {
        control: summarize_control(grouped.get(control, []), control)
        for control in reg.CONTROL_NAMES
    }
    if not integrity_ok:
        decision = "INTEGRITY_FAILURE"
        evaluated = False
    elif any(
        not summaries[control]["complete"]
        for control in reg.CONTROL_NAMES
    ):
        decision = "INCONCLUSIVE"
        evaluated = False
    else:
        failed_controls = [
            control
            for control in reg.CONTROL_NAMES
            if summaries[control]["rejection_count"] >= 65
        ]
        decision = "FAIL" if failed_controls else "PASS"
        evaluated = True
    return {
        "decision": decision,
        "status": decision,
        "integrity_passed": integrity_ok,
        "scientific_gate_evaluated": evaluated,
        "confirmatory_controls": summaries,
        "diagnostic_excluded": reg.NC0_DIAGNOSTIC_NAME,
        "diagnostic_affects_gate": False,
        "critical_count": 65,
        "registered_denominator": 1000,
        "control_family_size": 2,
    }


evaluate_stage2_gate = evaluate_gate


# --------------------------------------------------------------------------- #
# Closed integrity contract
# --------------------------------------------------------------------------- #
def _check(passed: bool, detail: str) -> dict[str, Any]:
    return {"passed": bool(passed), "detail": detail}


def _normalise_repo_path(value: str | Path) -> str:
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            return path.resolve().as_posix()
    return path.as_posix().removeprefix("./")


def _root_matches_registered(value: str | Path | None) -> bool:
    if value is None:
        return False
    normalised = _normalise_repo_path(value).rstrip("/")
    return normalised == reg.RESULT_ROOT.rstrip("/")


def _record_model_results(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    values = record.get("model_results", [])
    if isinstance(values, Mapping):
        return [dict({"model": model}, **dict(result)) for model, result in values.items()]
    return [dict(value) for value in values if isinstance(value, Mapping)]


def _finite_or_registered_degeneracy(records: Sequence[dict[str, Any]]) -> tuple[bool, str]:
    failures: list[str] = []
    required_invariants = {
        reg.NC0_NAME: (
            "target_byte_identical",
            "target_return_byte_identical",
            "fresh_iid_noise_construction",
            "joint_mask_permutation_matches_registered_seed",
            "per_feature_year_missingness_counts_preserved",
            "rowwise_co_missingness_multiset_preserved",
            "feature_matrix_replaced_from_real",
            "mask_row_alignment_changed",
            "rank_transform_after_masking_exact",
            "six_models_and_splits_unchanged",
        ),
        reg.NC1_NAME: (
            "feature_matrix_unchanged",
            "row_universe_unchanged",
            "target_null_locations_preserved",
            "target_multiset_by_year_preserved",
            "canonical_splits_unchanged",
            "all_target_years_processed",
            "train_and_test_targets_use_permuted_panel",
            "no_test_only_construction",
            "target_permutation_stream_used",
        ),
        reg.NC0_DIAGNOSTIC_NAME: (
            "target_byte_identical",
            "target_return_byte_identical",
            "fresh_iid_noise_construction",
            "joint_mask_permutation_matches_registered_seed",
            "per_feature_year_missingness_counts_preserved",
            "rowwise_co_missingness_multiset_preserved",
            "feature_matrix_replaced_from_real",
            "rank_transform_after_masking_exact",
            "six_models_and_splits_unchanged",
            "diagnostic_isolated",
            "confirmatory_gate_excluded",
            "real_mask_alignment_retained",
        ),
    }
    for record in records:
        control = record.get("control")
        model_results = _record_model_results(record)
        model_names = [result.get("model") for result in model_results]
        if model_names != list(reg.MODELS):
            failures.append(
                f"rep={record.get('repetition_id')}: model cells are not the exact six-model family"
            )
        if record.get("permutations") != PERMUTATIONS:
            failures.append(
                f"rep={record.get('repetition_id')}: permutations are not exactly {PERMUTATIONS}"
            )
        if record.get("bootstraps") != BOOTSTRAPS:
            failures.append(
                f"rep={record.get('repetition_id')}: bootstraps are not exactly {BOOTSTRAPS}"
            )
        status = record.get("status")
        if status == ANALYZABLE_STATUS:
            if record.get("analyzable") is not True:
                failures.append(f"rep={record.get('repetition_id')}: analyzable flag is false")
            if record.get("classification") != ANALYZABLE_STATUS:
                failures.append(f"rep={record.get('repetition_id')}: invalid analyzable classification")
            for model_result in model_results:
                if model_result.get("status") != ANALYZABLE_STATUS:
                    failures.append(
                        f"rep={record.get('repetition_id')}: non-analyzable model in analyzable repetition"
                    )
                elif not _finite_analysis(dict(model_result.get("analysis", {}))):
                    failures.append(
                        f"rep={record.get('repetition_id')}: non-finite model analysis"
                    )
            family = record.get("family")
            if not isinstance(family, Mapping) or family.get("model_family_divisor") != 6:
                failures.append(f"rep={record.get('repetition_id')}: family divisor is not literal 6")
            if not isinstance(record.get("family_reject"), bool):
                failures.append(f"rep={record.get('repetition_id')}: family rejection is not classified")
            invariants = record.get("mechanism_invariants", {})
            for key in required_invariants.get(control, ()):
                if invariants.get(key) is not True:
                    failures.append(
                        f"rep={record.get('repetition_id')}: mechanism invariant {key} failed"
                    )
        elif status in {
            reg.PARTIAL_MODEL_DEGENERACY_STATUS,
            reg.ALL_MODEL_DEGENERACY_STATUS,
        }:
            if record.get("analyzable") is not False:
                failures.append(f"rep={record.get('repetition_id')}: invalid repetition marked analyzable")
            if record.get("classification") != status:
                failures.append(f"rep={record.get('repetition_id')}: missing degeneracy classification")
            degenerate_models = record.get("degenerate_models")
            if not isinstance(degenerate_models, Mapping) or not degenerate_models:
                failures.append(f"rep={record.get('repetition_id')}: missing degenerate model map")
            else:
                degenerate_names = set(degenerate_models)
                if not degenerate_names <= set(reg.MODELS):
                    failures.append(
                        f"rep={record.get('repetition_id')}: unknown degenerate model"
                    )
                if "family" in record:
                    failures.append(
                        f"rep={record.get('repetition_id')}: invalid repetition carries family output"
                    )
                expected_all = status == reg.ALL_MODEL_DEGENERACY_STATUS
                if (len(degenerate_names) == 6) != expected_all:
                    failures.append(
                        f"rep={record.get('repetition_id')}: degeneracy class does not match model count"
                    )
                if not expected_all and len(degenerate_names) >= 6:
                    failures.append(
                        f"rep={record.get('repetition_id')}: partial degeneracy has all models"
                    )
                for model_result in model_results:
                    model = model_result.get("model")
                    expected_status = (
                        "DEGENERATE_MODEL"
                        if model in degenerate_names
                        else "NOT_ANALYZED_DUE_TO_REPETITION_DEGENERACY"
                    )
                    if model_result.get("status") != expected_status:
                        failures.append(
                            f"rep={record.get('repetition_id')}: invalid model result classification"
                        )
                    if "analysis" in model_result:
                        failures.append(
                            f"rep={record.get('repetition_id')}: invalid repetition carries significance output"
                        )
            invariants = record.get("mechanism_invariants", {})
            for key in required_invariants.get(control, ()):
                if invariants.get(key) is not True:
                    failures.append(
                        f"rep={record.get('repetition_id')}: mechanism invariant {key} failed"
                    )
        else:
            failures.append(f"rep={record.get('repetition_id')}: unexpected status {status!r}")
    return not failures, "; ".join(failures[:5])


def evaluate_integrity(
    *,
    records: Sequence[dict[str, Any]] | Mapping[str, Sequence[dict[str, Any]]],
    registered_source_path: str = reg.DATASET_PATH,
    source_path: str | Path | None = None,
    registered_source_sha: str = reg.DATASET_SHA256,
    source_sha_before: str | None = None,
    source_sha_after: str | None = None,
    significance_sha: str | None = None,
    source_module_hashes: Mapping[str, str] | None = None,
    protected_digest_before: Mapping[str, str] | None = None,
    protected_digest_after: Mapping[str, str] | None = None,
    stage1_digest_before: Mapping[str, str] | None = None,
    stage1_digest_after: Mapping[str, str] | None = None,
    stage1b_digest_before: Mapping[str, str] | None = None,
    stage1b_digest_after: Mapping[str, str] | None = None,
    workspace_digest_before: Mapping[str, str] | None = None,
    workspace_digest_after: Mapping[str, str] | None = None,
    output_root: str | Path | None = None,
    output_paths: Sequence[str | Path] | None = None,
    output_audit: Mapping[str, Any] | None = None,
    source_override_restored: bool | None = None,
    pipeline_source_restored: bool | None = None,
    replay_probe: Mapping[str, Any] | None = None,
    diagnostic_records: Sequence[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate exactly the closed 15-condition registration list.

    This function is pure: callers provide all filesystem observations.  It
    intentionally does not inspect FPR, rejection thresholds, IC magnitude,
    p-value uniformity, Wilson location, or any other registered exclusion.
    """
    grouped = _records_by_control(records, diagnostic_records)
    all_records = [
        record
        for control in (
            reg.NC0_NAME,
            reg.NC1_NAME,
            reg.NC0_DIAGNOSTIC_NAME,
        )
        for record in grouped.get(control, [])
    ]

    expected_matrices = {
        control: tuple(int(value) for value in ids)
        for control, ids in reg.EXPECTED_REPETITION_ID_MATRICES.items()
    }
    actual_matrices = {
        control: tuple(
            sorted(int(record.get("repetition_id")) for record in values)
        )
        for control, values in grouped.items()
        if control in expected_matrices
    }
    unknown_controls = sorted(set(grouped) - set(expected_matrices))
    complete_matrices = actual_matrices == expected_matrices and not unknown_controls

    repetition_cells = [
        (str(record.get("control")), int(record.get("repetition_id")))
        for record in all_records
        if record.get("repetition_id") is not None
    ]
    repetition_counts = Counter(repetition_cells)
    duplicate_repetitions = sorted(
        cell for cell, count in repetition_counts.items() if count > 1
    )
    model_cells: list[tuple[str, int, str]] = []
    for record in all_records:
        control = str(record.get("control"))
        repetition_id = record.get("repetition_id")
        if repetition_id is None:
            continue
        for model_result in _record_model_results(record):
            model = model_result.get("model")
            if model is not None:
                model_cells.append((control, int(repetition_id), str(model)))
    model_counts = Counter(model_cells)
    duplicate_model_cells = sorted(
        cell for cell, count in model_counts.items() if count > 1
    )

    seed_mismatches: list[str] = []
    expected_model_cells_ok = True
    finite_ok, finite_detail = _finite_or_registered_degeneracy(all_records)
    for record in all_records:
        control = str(record.get("control"))
        repetition_id = record.get("repetition_id")
        if repetition_id is None or control not in expected_matrices:
            seed_mismatches.append(f"unknown control/id: {control}/{repetition_id}")
            continue
        expected_fields = _seed_fields(control, int(repetition_id))
        recorded_fields = record.get("construction_seeds", {})
        if not isinstance(recorded_fields, Mapping):
            recorded_fields = {}
        for field, expected in expected_fields.items():
            actual = record.get(field, recorded_fields.get(field))
            if actual != expected:
                seed_mismatches.append(
                    f"{control} repetition={repetition_id} {field}: {actual!r} != {expected!r}"
                )
        if record.get("significance_seed") != reg.significance_seed(int(repetition_id)):
            seed_mismatches.append(f"{control} repetition={repetition_id} significance seed")

        result_models = [result.get("model") for result in _record_model_results(record)]
        if result_models != list(reg.MODELS):
            expected_model_cells_ok = False

    paths = [_normalise_repo_path(path) for path in (output_paths or [])]
    output_root_identity = _normalise_repo_path(output_root) if output_root is not None else ""
    root_prefix = output_root_identity.rstrip("/") + "/" if output_root_identity else ""
    escaping = sorted(
        path for path in paths if not root_prefix or not path.startswith(root_prefix)
    )
    protected_hits = sorted(
        path
        for path in paths
        for protected in (*prov.PROTECTED_RESULTS_ROOTS, *PROTECTED_DATA_ROOTS)
        if path == protected or path.startswith(protected.rstrip("/") + "/")
    )
    audit_ok = True
    audit_detail = "actual output audit not supplied in pure fixture mode"
    if output_audit is not None:
        audit_ok = bool(output_audit.get("passed")) and set(
            output_audit.get("actual_scientific_files", [])
        ) == set(SCIENTIFIC_EMITTED_FILENAMES) and not any(
            output_audit.get(key)
            for key in ("unexpected_files", "unexpected_directories", "symlink_escapes", "missing_scientific_files")
        )
        audit_detail = json.dumps(dict(output_audit), sort_keys=True)
    outside_namespace_ok = (
        workspace_digest_before is not None
        and workspace_digest_after is not None
        and dict(workspace_digest_before) == dict(workspace_digest_after)
    )
    historical_stage1_ok = (
        stage1_digest_before is not None
        and stage1_digest_after is not None
        and dict(stage1_digest_before) == dict(stage1_digest_after)
    )
    historical_stage1b_ok = (
        stage1b_digest_before is not None
        and stage1b_digest_after is not None
        and dict(stage1b_digest_before) == dict(stage1b_digest_after)
    )
    protected_data_ok = (
        protected_digest_before is not None
        and protected_digest_after is not None
        and dict(protected_digest_before) == dict(protected_digest_after)
    )
    source_restored = (
        source_override_restored
        if source_override_restored is not None
        else pipeline_source_restored
    )
    collision = _collision_report()
    replay_ok = bool(
        replay_probe
        and replay_probe.get("identical") is True
        and replay_probe.get("control") == reg.NC0_NAME
        and replay_probe.get("repetition_id") == reg.NC0_IDS[0]
        and replay_probe.get("permutations") == PERMUTATIONS
        and replay_probe.get("bootstraps") == BOOTSTRAPS
        and isinstance(replay_probe.get("digest"), str)
        and len(replay_probe["digest"]) == 64
    )

    conditions = {
        "frozen_source_dataset_path_and_sha_match": _check(
            _normalise_repo_path(registered_source_path) == reg.DATASET_PATH
            and source_path is not None
            and _normalise_repo_path(source_path) == reg.DATASET_PATH
            and source_sha_before == source_sha_after == registered_source_sha == reg.DATASET_SHA256,
            f"source_path={source_path!s}; source_sha_before={source_sha_before!s}; source_sha_after={source_sha_after!s}",
        ),
        "repaired_significance_sha_matches": _check(
            significance_sha == reg.SIGNIFICANCE_SHA256,
            f"significance_sha={significance_sha!s}",
        ),
        "registered_stage2_source_module_hashes_match": _check(
            source_module_hashes is not None
            and dict(source_module_hashes) == dict(reg.SOURCE_MODULE_HASHES),
            f"required_source_hashes={dict(source_module_hashes or {})}",
        ),
        "complete_expected_repetition_id_matrices": _check(
            complete_matrices,
            f"expected={expected_matrices}; actual={actual_matrices}; unknown_controls={unknown_controls}",
        ),
        "no_duplicate_repetition_ids_or_model_cells": _check(
            not duplicate_repetitions and not duplicate_model_cells,
            f"duplicate_repetitions={duplicate_repetitions[:5]}; duplicate_model_cells={duplicate_model_cells[:5]}",
        ),
        "exact_seed_formulas_reproduce": _check(
            not seed_mismatches,
            f"mismatches={seed_mismatches[:5]}",
        ),
        "no_seed_collisions_or_forbidden_overlap": _check(
            bool(collision["passed"]),
            json.dumps(collision, sort_keys=True),
        ),
        "writes_confined_to_stage2_result_namespace": _check(
            _root_matches_registered(output_root)
            and not escaping
            and not protected_hits
            and audit_ok,
            f"output_root={output_root!s}; escaping={escaping}; protected_hits={protected_hits}; audit={audit_detail}",
        ),
        "stage1_and_stage1b_result_roots_untouched": _check(
            historical_stage1_ok and historical_stage1b_ok,
            f"stage1_unchanged={historical_stage1_ok}; stage1b_unchanged={historical_stage1b_ok}",
        ),
        "no_trusted_data_or_provenance_mutation": _check(
            protected_data_ok,
            f"protected_data_unchanged={protected_data_ok}",
        ),
        "protected_digest_outside_stage2_root_unchanged": _check(
            outside_namespace_ok,
            f"outside_namespace_unchanged={outside_namespace_ok}",
        ),
        "runtime_source_override_restored_on_all_exit_paths": _check(
            bool(source_restored), f"source_override_restored={source_restored}",
        ),
        "deterministic_replay_contract": _check(
            replay_ok,
            f"replay_probe={dict(replay_probe or {})}",
        ),
        "finite_valid_statistics_or_registered_degeneracy": _check(
            finite_ok,
            finite_detail,
        ),
        "all_expected_model_cells_present_for_analyzable_repetitions": _check(
            expected_model_cells_ok
            and not duplicate_model_cells
            and all(
                len(_record_model_results(record)) == 6
                for record in all_records
                if record.get("analyzable") is True
            ),
            "every analyzable repetition carries the six registered model cells",
        ),
    }
    if tuple(conditions) != tuple(reg.INTEGRITY_CONDITION_IDENTIFIERS):
        raise Stage2IntegrityError("implementation integrity list drifted from registration")
    failures = [name for name, result in conditions.items() if not result["passed"]]
    return {
        "contract": "closed deterministic list — docs/thesis/STAGE_2_REGISTRATION.md",
        "conditions": conditions,
        "checks": conditions,
        "failures": failures,
        "passed": not failures,
        "excluded_from_every_check": list(reg.INTEGRITY_EXCLUSIONS),
        "evaluated_before_scientific_gate": True,
        "high_fpr_is_valid_science": True,
    }


# --------------------------------------------------------------------------- #
# Report and output lifecycle
# --------------------------------------------------------------------------- #
def records_digest(records: Sequence[dict[str, Any]]) -> str:
    return _sha256_bytes(json.dumps(list(records), sort_keys=True).encode("utf-8"))


def _flatten_record(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for model_result in _record_model_results(record):
        pooled = model_result.get("analysis", {}).get("pooled", {})
        rows.append(
            {
                "control": record.get("control"),
                "role": record.get("role"),
                "repetition_id": record.get("repetition_id"),
                "status": record.get("status"),
                "analyzable": record.get("analyzable"),
                "classification": record.get("classification"),
                "model": model_result.get("model"),
                "model_status": model_result.get("status"),
                "permutations": record.get("permutations"),
                "bootstraps": record.get("bootstraps"),
                "significance_seed": model_result.get(
                    "significance_seed", record.get("significance_seed")
                ),
                "family_reject": record.get("family_reject"),
                "observed_ic": pooled.get("observed_ic"),
                "permutation_p_value_two_sided": pooled.get(
                    "permutation_p_value_two_sided"
                ),
                "bootstrap_ci_95": json.dumps(pooled.get("bootstrap_ci_95")),
                "degeneracy": json.dumps(model_result.get("degeneracy", []), sort_keys=True),
                "mechanism_invariants": json.dumps(
                    record.get("mechanism_invariants", {}), sort_keys=True
                ),
            }
        )
    return rows


def build_report(
    records: Sequence[dict[str, Any]],
    integrity: Mapping[str, Any],
    *,
    replay_probe: Mapping[str, Any],
    source_path: Path,
    base_seed: int,
    started_at: str,
    duration_seconds: float,
) -> dict[str, Any]:
    grouped = _records_by_control(records)
    controls = {
        control: summarize_control(grouped.get(control, []), control)
        for control in reg.CONTROL_NAMES
    }
    diagnostic = summarize_diagnostic(grouped.get(reg.NC0_DIAGNOSTIC_NAME, []))
    gate = evaluate_gate(grouped, integrity_passed=integrity)
    return {
        "schema_version": 1,
        "stage": "Stage 2 — expanded negative controls",
        "experiment": SLUG,
        "registration": reg.REGISTRATION_DOC,
        "claim_boundary": list(reg.CLAIM_BOUNDARY),
        "design": {
            "controls": list(reg.CONTROL_NAMES),
            "diagnostics": list(reg.DIAGNOSTIC_NAMES),
            "roles": dict(reg.CONTROL_ROLES),
            "models": list(reg.MODELS),
            "model_family_divisor": 6,
            "permutations": reg.PERMUTATIONS,
            "bootstraps": reg.BOOTSTRAPS,
            "alpha": reg.MODEL_ALPHA,
            "p_value_sidedness": reg.MODEL_P_VALUE_SIDEDNESS,
            "splits": registered_configuration()["splits"],
            "construction_seed_formula": reg.CONSTRUCTION_SEED_FORMULA,
            "significance_seed_formula": reg.SIGNIFICANCE_SEED_FORMULA,
            "repetition_id_matrices": registered_configuration()[
                "repetition_id_matrices"
            ],
            "strict_complete_denominator": True,
            "min_analyzable_denominator": 1000,
            "equivalence_delta": reg.EQUIVALENCE_DELTA,
            "equivalence_is_gating": False,
        },
        "source": {
            "path": reg.DATASET_PATH,
            "sha256": reg.DATASET_SHA256,
            "actual_path": _relative_to_repo(source_path),
        },
        "replay": dict(replay_probe),
        "integrity": dict(integrity),
        "gate": gate,
        "controls": controls,
        "diagnostic": diagnostic,
        "records_digest": records_digest(records),
        "records": list(records),
        "run": {
            "base_seed": base_seed,
            "started_at_utc": started_at,
            "duration_seconds": round(duration_seconds, 6),
            "git": _git_metadata(),
        },
        "limitations": [
            "These controls characterize apparatus behavior under the registered constructions only.",
            "The diagnostic uses a target-associated real mask and is not an exact null-FPR test.",
            "Passing this stage would not establish absence of feature-side PIT or alignment leakage.",
            "Research support only; not investment advice.",
        ],
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    gate = report["gate"]
    lines = [
        "# Stage 2 expanded negative-control report",
        "",
        "This report characterizes the registered apparatus constructions. It is research support only, not investment advice.",
        "",
        f"**Stage 2 gate status:** {gate['decision']}",
        "",
        "## Confirmatory controls",
        "",
        "| Control | Analyzable / registered | Rejections X | FPR X / 1000 | Wilson 95% | Complete |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for control in reg.CONTROL_NAMES:
        summary = report["controls"][control]
        low, high = summary["wilson_95_pointwise"]
        lines.append(
            f"| {control} | {summary['analyzable_repetitions']} / {summary['registered_denominator']} | "
            f"{summary['rejection_count']} | {summary['fpr_estimate']:.6f} | "
            f"[{low:.6f}, {high:.6f}] | {'yes' if summary['complete'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "The confirmatory rule is family rejection when min(1, 6 × minimum raw two-sided p) < 0.05. A complete control fails at X ≥ 65; incomplete denominators are inconclusive.",
            "The Wilson intervals and the equivalence delta are descriptive and non-gating.",
            "",
            "## Diagnostic arm",
            "",
            f"{reg.NC0_DIAGNOSTIC_NAME} is {reg.NC0_DIAGNOSTIC_ROLE}. Its output is isolated from the confirmatory gate.",
            "",
            "## Integrity",
            "",
            f"Closed integrity contract passed: **{report['integrity']['passed']}**.",
            "",
            "## Limitations",
            "",
            *[f"- {limitation}" for limitation in report["limitations"]],
            "",
        ]
    )
    validate_claim_safety_text("\n".join(lines))
    return "\n".join(lines)


def _control_summary_rows(
    report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for control in reg.CONTROL_NAMES:
        summary = report["controls"][control]
        rows.append(
            {
                "control": control,
                "role": summary["role"],
                "registered_denominator": summary["registered_denominator"],
                "analyzable_repetitions": summary["analyzable_repetitions"],
                "invalid_repetitions": summary["invalid_repetitions"],
                "rejection_count": summary["rejection_count"],
                "fpr_estimate": summary["fpr_estimate"],
                "wilson_95_pointwise_low": summary["wilson_95_pointwise"][0],
                "wilson_95_pointwise_high": summary["wilson_95_pointwise"][1],
                "complete": summary["complete"],
                "fails_if_complete": summary["fails_if_complete"],
                "gate_decision": report["gate"]["decision"],
                "equivalence_is_gating": False,
            }
        )
    return rows


def _write_scientific_artifacts(
    staging: Path,
    *,
    report: Mapping[str, Any],
    records: Sequence[dict[str, Any]],
) -> None:
    staging.mkdir(parents=True, exist_ok=False)
    (staging / OUTPUT_FILENAMES["report_json"]).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (staging / OUTPUT_FILENAMES["report_md"]).write_text(
        render_markdown(report), encoding="utf-8"
    )
    grouped = _records_by_control(records)
    confirmatory_rows = [
        row
        for control in reg.CONTROL_NAMES
        for record in grouped.get(control, [])
        for row in _flatten_record(record)
    ]
    diagnostic_rows = [
        row
        for record in grouped.get(reg.NC0_DIAGNOSTIC_NAME, [])
        for row in _flatten_record(record)
    ]
    pd.DataFrame(confirmatory_rows).to_csv(
        staging / OUTPUT_FILENAMES["repetitions"], index=False, float_format="%.17g"
    )
    pd.DataFrame(_control_summary_rows(report)).to_csv(
        staging / OUTPUT_FILENAMES["control_summary"],
        index=False,
        float_format="%.17g",
    )
    pd.DataFrame(diagnostic_rows).to_csv(
        staging / OUTPUT_FILENAMES["diagnostic_repetitions"],
        index=False,
        float_format="%.17g",
    )


def _audit_output_surface(
    surface: Path,
    *,
    expected_names: Sequence[str],
    operational_names: Sequence[str] = (),
) -> dict[str, Any]:
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
        if path.is_file()
        and not (path.name in IGNORABLE_OS_METADATA and not path.is_symlink())
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
        "passed": not unexpected_files
        and not unexpected_directories
        and not symlink_escapes
        and not missing,
    }


def _purge_os_metadata(surface: Path) -> None:
    if not surface.is_dir() or surface.is_symlink():
        return
    for path in sorted(surface.rglob("*")):
        if path.name in IGNORABLE_OS_METADATA and path.is_file() and not path.is_symlink():
            path.unlink()


def _marker_path(root: Path) -> Path:
    return root / ATTEMPT_MARKER_FILENAME


def _new_attempt_marker(attempt_number: int, attempt_type: str, prior_incomplete: bool) -> dict[str, Any]:
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


def _load_attempt_marker(root: Path) -> dict[str, Any]:
    marker = _marker_path(root)
    if not marker.is_file() or marker.is_symlink():
        raise Stage2Error("incomplete Stage 2 root has no durable attempt marker")
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Stage2Error("Stage 2 attempt marker is unreadable") from exc
    if payload.get("governance_class") != "operational_attempt_provenance":
        raise Stage2Error("Stage 2 marker is not operational provenance")
    if payload.get("experiment") != SLUG:
        raise Stage2Error("Stage 2 marker belongs to another experiment")
    if payload.get("registered_configuration") != registered_configuration() or payload.get(
        "registered_configuration_sha256"
    ) != registered_configuration_digest():
        raise Stage2Error("registered Stage 2 configuration changed; recovery refused")
    attempts = payload.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        raise Stage2Error("Stage 2 marker has no attempts")
    numbers = [attempt.get("attempt_number") for attempt in attempts]
    if any(not isinstance(number, int) for number in numbers) or len(set(numbers)) != len(numbers):
        raise Stage2Error("Stage 2 marker has invalid attempt numbering")
    if any(
        attempt.get("attempt_type") not in {"initial", "crash_recovery"}
        for attempt in attempts
        if isinstance(attempt, dict)
    ):
        raise Stage2Error("Stage 2 marker has invalid attempt type")
    return payload


def _is_complete_run(root: Path) -> bool:
    manifest = root / MANIFEST_FILENAME
    marker = _marker_path(root)
    if not manifest.is_file() or not marker.is_file() or marker.is_symlink():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    attempts = marker_payload.get("attempts")
    evidence = payload.get("operational_attempt_provenance", {})
    if not isinstance(attempts, list) or not attempts or not isinstance(evidence, dict):
        return False
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
        and evidence.get("path") == _relative_to_repo(marker)
        and evidence.get("sha256") == _sha256_path(marker)
        and attempts[-1].get("completion_status") == "complete"
        and audit["passed"]
        and set(audit["actual_direct_files"])
        == set(EMITTED_FILENAMES) | set(OPERATIONAL_FILENAMES)
    )


def _cleanup_incomplete_root(root: Path) -> None:
    allowed_files = set(SCIENTIFIC_EMITTED_FILENAMES) | {MANIFEST_FILENAME}
    _purge_os_metadata(root)
    for child in sorted(root.iterdir()):
        if child.name == ATTEMPT_MARKER_FILENAME:
            continue
        if child.name in IGNORABLE_OS_METADATA and child.is_file() and not child.is_symlink():
            child.unlink()
            continue
        if child.name == STAGING_DIRNAME:
            if child.is_symlink() or not child.is_dir():
                raise Stage2Error("unsafe Stage 2 staging path")
            shutil.rmtree(child)
            continue
        if child.name in allowed_files:
            if child.is_symlink() or not child.is_file():
                raise Stage2Error(f"unsafe Stage 2 file: {child.name}")
            child.unlink()
            continue
        raise Stage2Error(f"incomplete Stage 2 root contains unrecognized path {child.name!r}")


def _prepare_attempt(*, repeat_after_crash: bool) -> tuple[Path, Path, dict[str, Any], int]:
    root = RESULT_ROOT
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise Stage2Error("Stage 2 result root is not a safe directory")
    if not repeat_after_crash:
        if root.exists() and any(root.iterdir()):
            if _is_complete_run(root):
                raise Stage2Error("a complete Stage 2 run already exists; --run refuses overwrite")
            raise Stage2Error(
                "a pre-existing non-empty Stage 2 result root exists; use --repeat-after-crash"
            )
        root.mkdir(parents=True, exist_ok=True)
        marker_payload = _new_attempt_marker(1, "initial", False)
        marker = _marker_path(root)
        _atomic_json_write(marker, marker_payload)
        return root, marker, marker_payload, 1
    if not root.is_dir() or not any(root.iterdir()):
        raise Stage2Error("--repeat-after-crash requires a non-empty incomplete Stage 2 root")
    if _is_complete_run(root):
        raise Stage2Error("--repeat-after-crash refuses a complete Stage 2 run")
    marker_payload = _load_attempt_marker(root)
    _cleanup_incomplete_root(root)
    for attempt in marker_payload["attempts"]:
        attempt["completion_status"] = "incomplete"
    number = max(attempt["attempt_number"] for attempt in marker_payload["attempts"]) + 1
    configuration = registered_configuration()
    marker_payload["attempts"].append(
        {
            "attempt_number": number,
            "attempt_type": "crash_recovery",
            "registered_configuration_sha256": registered_configuration_digest(),
            "seed_schedule_sha256": configuration["seed_schedule_sha256"],
            "prior_attempt_incomplete": True,
            "completion_status": "in_progress",
            "started_at_utc": _utc_now(),
        }
    )
    marker = _marker_path(root)
    _atomic_json_write(marker, marker_payload)
    return root, marker, marker_payload, number


def _set_attempt_status(
    marker_path: Path, marker_payload: dict[str, Any], attempt_number: int, status: str
) -> dict[str, Any]:
    updated = json.loads(json.dumps(marker_payload))
    for attempt in updated["attempts"]:
        if attempt["attempt_number"] == attempt_number:
            attempt["completion_status"] = status
            break
    else:
        raise Stage2Error(f"attempt {attempt_number} is absent from marker")
    _atomic_json_write(marker_path, updated)
    return updated


def _promote_scientific_artifacts(root: Path, staging: Path) -> None:
    for name in SCIENTIFIC_EMITTED_FILENAMES:
        os.replace(staging / name, root / name)
    staging_parent = staging.parent
    if staging_parent.name != STAGING_DIRNAME or staging_parent.parent != root:
        raise Stage2IntegrityError("unsafe Stage 2 staging path")
    _purge_os_metadata(staging)
    try:
        staging.rmdir()
    except OSError as exc:
        raise Stage2IntegrityError("Stage 2 attempt staging directory is not empty") from exc
    _purge_os_metadata(staging_parent)
    try:
        staging_parent.rmdir()
    except OSError as exc:
        raise Stage2IntegrityError("Stage 2 staging parent is not empty") from exc


def _write_final_manifest(
    *, artifacts: Sequence[Path], source_artifacts: Sequence[tuple[Path, str]], extra: dict[str, Any]
) -> Path:
    try:
        return prov.write_manifest(
            SLUG,
            artifacts=artifacts,
            source_artifacts=source_artifacts,
            extra=extra,
        )
    except Exception as exc:
        setattr(exc, "_stage2_manifest_write_started", True)
        raise


@contextlib.contextmanager
def _restored_pipeline_source() -> Iterator[Path]:
    """Restore the canonical source override even if a future hook fails."""
    original = rx.TRAINING_MODELING
    try:
        yield original
    finally:
        rx.TRAINING_MODELING = original


def _replay_probe(
    raw: pd.DataFrame,
    *,
    control: str = reg.NC0_NAME,
    repetition_id: int = reg.NC0_IDS[0],
    permutations: int = PERMUTATIONS,
    bootstraps: int = BOOTSTRAPS,
) -> dict[str, Any]:
    """Replay one registered cell twice; writes no result and claims no outcome."""
    first = run_repetition(
        raw,
        control=control,
        repetition_id=repetition_id,
        permutations=permutations,
        bootstraps=bootstraps,
    )
    second = run_repetition(
        raw,
        control=control,
        repetition_id=repetition_id,
        permutations=permutations,
        bootstraps=bootstraps,
    )
    first_json = json.dumps(first, sort_keys=True)
    second_json = json.dumps(second, sort_keys=True)
    return {
        "control": control,
        "repetition_id": repetition_id,
        "identical": first_json == second_json,
        "digest": _sha256_bytes(first_json.encode("utf-8")),
        "permutations": permutations,
        "bootstraps": bootstraps,
        "note": "deterministic replay verification; not a fresh governed repetition",
    }


def replay_check(
    *, permutations: int = PERMUTATIONS, bootstraps: int = BOOTSTRAPS
) -> dict[str, Any]:
    """Read the frozen source and replay one cell without creating the result root."""
    raw = pd.read_csv(DATASET_PATH)
    _assert_canonical_source(raw)
    with _restored_pipeline_source():
        return _replay_probe(
            raw,
            permutations=permutations,
            bootstraps=bootstraps,
        )


def registered_plan() -> dict[str, Any]:
    """Describe the registered run without reading data or creating a path."""
    return {
        "executed": False,
        "experiment": SLUG,
        "result_root": reg.RESULT_ROOT,
        "controls": list(reg.CONTROL_NAMES),
        "diagnostics": list(reg.DIAGNOSTIC_NAMES),
        "models": list(reg.MODELS),
        "repetitions": {
            name: len(ids)
            for name, ids in reg.EXPECTED_REPETITION_ID_MATRICES.items()
        },
        "explicit_run_flag": "--run",
        "replay_flag": "--replay-check",
        "repeat_after_crash_flag": "--repeat-after-crash",
        "scientific_draw_performed": False,
        "result_root_created": False,
    }


def _run_attempt(
    root: Path,
    *,
    marker_path: Path,
    marker_payload: dict[str, Any],
    attempt_number: int,
    progress: bool,
) -> Path:
    started = datetime.now(timezone.utc)
    clock = time.perf_counter()
    workspace_before = workspace_digest_excluding_stage2()

    base_seed = prov.seed_for(SLUG)
    if base_seed != BASE_SEED:
        raise Stage2IntegrityError("declared negative-control seed differs from registration")
    _assert_registered_runtime_contract()
    if not DATASET_PATH.is_file():
        raise Stage2IntegrityError(f"registered dataset not found: {DATASET_PATH}")
    source_sha_before = _sha256_path(DATASET_PATH)
    if source_sha_before != reg.DATASET_SHA256:
        raise Stage2IntegrityError("registered dataset SHA does not match")
    protected_before = protected_data_digest()
    stage1_before = tree_digest(STAGE_1_RESULT_ROOT)
    stage1b_before = tree_digest(STAGE_1B_RESULT_ROOT)
    raw = pd.read_csv(DATASET_PATH)
    _assert_canonical_source(raw)

    with _restored_pipeline_source() as original_source:
        records = run_all(raw, progress=progress)
        replay_probe = _replay_probe(raw)
    source_override_restored = rx.TRAINING_MODELING == original_source
    source_sha_after = _sha256_path(DATASET_PATH)
    protected_after = protected_data_digest()
    stage1_after = tree_digest(STAGE_1_RESULT_ROOT)
    stage1b_after = tree_digest(STAGE_1B_RESULT_ROOT)
    workspace_after = workspace_digest_excluding_stage2()
    output_root = reg.RESULT_ROOT.rstrip("/")
    staging = root / STAGING_DIRNAME / f"attempt-{attempt_number}"
    planned_paths = [
        _relative_to_repo(staging / name) for name in SCIENTIFIC_EMITTED_FILENAMES
    ]

    preflight_integrity = evaluate_integrity(
        records=records,
        source_path=DATASET_PATH,
        registered_source_sha=reg.DATASET_SHA256,
        source_sha_before=source_sha_before,
        source_sha_after=source_sha_after,
        significance_sha=_sha256_path(ROOT / "experiments/significance.py"),
        source_module_hashes={
            path: _sha256_path(ROOT / path) for path in reg.SOURCE_MODULE_HASHES
        },
        protected_digest_before=protected_before,
        protected_digest_after=protected_after,
        stage1_digest_before=stage1_before,
        stage1_digest_after=stage1_after,
        stage1b_digest_before=stage1b_before,
        stage1b_digest_after=stage1b_after,
        workspace_digest_before=workspace_before,
        workspace_digest_after=workspace_after,
        output_root=output_root,
        output_paths=planned_paths,
        source_override_restored=source_override_restored,
        replay_probe=replay_probe,
    )
    if not preflight_integrity["passed"]:
        raise Stage2IntegrityError(
            "closed integrity contract failed before staging: "
            + "; ".join(preflight_integrity["failures"])
        )

    report = build_report(
        records,
        preflight_integrity,
        replay_probe=replay_probe,
        source_path=DATASET_PATH,
        base_seed=base_seed,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_seconds=time.perf_counter() - clock,
    )
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)
    staging.parent.mkdir(parents=True, exist_ok=True)
    _write_scientific_artifacts(staging, report=report, records=records)
    stage_audit = _audit_output_surface(
        staging, expected_names=SCIENTIFIC_EMITTED_FILENAMES
    )
    if not stage_audit["passed"]:
        raise Stage2IntegrityError("staged output confinement failed")

    actual_paths = [
        _relative_to_repo(path)
        for path in sorted(staging.rglob("*"))
        if path.is_file()
    ]
    integrity = evaluate_integrity(
        records=records,
        source_path=DATASET_PATH,
        registered_source_sha=reg.DATASET_SHA256,
        source_sha_before=source_sha_before,
        source_sha_after=source_sha_after,
        significance_sha=_sha256_path(ROOT / "experiments/significance.py"),
        source_module_hashes={
            path: _sha256_path(ROOT / path) for path in reg.SOURCE_MODULE_HASHES
        },
        protected_digest_before=protected_before,
        protected_digest_after=protected_after,
        stage1_digest_before=stage1_before,
        stage1_digest_after=stage1_after,
        stage1b_digest_before=stage1b_before,
        stage1b_digest_after=stage1b_after,
        workspace_digest_before=workspace_before,
        workspace_digest_after=workspace_after,
        output_root=output_root,
        output_paths=actual_paths,
        output_audit=stage_audit,
        source_override_restored=source_override_restored,
        replay_probe=replay_probe,
    )
    if not integrity["passed"]:
        raise Stage2IntegrityError(
            "closed integrity contract failed before promotion: "
            + "; ".join(integrity["failures"])
        )

    report = build_report(
        records,
        integrity,
        replay_probe=replay_probe,
        source_path=DATASET_PATH,
        base_seed=base_seed,
        started_at=started.isoformat().replace("+00:00", "Z"),
        duration_seconds=time.perf_counter() - clock,
    )
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)
    (staging / OUTPUT_FILENAMES["report_json"]).write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (staging / OUTPUT_FILENAMES["report_md"]).write_text(markdown, encoding="utf-8")

    _promote_scientific_artifacts(root, staging)
    _purge_os_metadata(root)
    final_audit = _audit_output_surface(
        root,
        expected_names=SCIENTIFIC_EMITTED_FILENAMES,
        operational_names=OPERATIONAL_FILENAMES,
    )
    if not final_audit["passed"]:
        raise Stage2IntegrityError("promoted output confinement failed")
    marker_payload = _set_attempt_status(
        marker_path, marker_payload, attempt_number, "complete"
    )
    output = prov.output_dir(SLUG, create=False)
    report_json = output / OUTPUT_FILENAMES["report_json"]
    report_md = output / OUTPUT_FILENAMES["report_md"]
    repetitions = output / OUTPUT_FILENAMES["repetitions"]
    control_summary = output / OUTPUT_FILENAMES["control_summary"]
    diagnostic_repetitions = output / OUTPUT_FILENAMES["diagnostic_repetitions"]
    _write_final_manifest(
        artifacts=[
            report_json,
            report_md,
            repetitions,
            control_summary,
            diagnostic_repetitions,
        ],
        source_artifacts=[(DATASET_PATH, "registered modeling dataset; read-only")],
        extra={
            "stage": "Stage 2 — expanded negative controls",
            "registration": reg.REGISTRATION_DOC,
            "implementation_sha256": implementation_hash(),
            "registration_module_sha256": registration_hash(),
            "source_module_hashes": {
                path: _sha256_path(ROOT / path) for path in reg.SOURCE_MODULE_HASHES
            },
            "registered_configuration": registered_configuration(),
            "registered_configuration_sha256": registered_configuration_digest(),
            "integrity_passed": integrity["passed"],
            "gate_decision": report["gate"]["decision"],
            "records_digest": records_digest(records),
            "completion_status": "complete",
            "completion_authority": MANIFEST_FILENAME,
            "scientific_emitted_files": list(SCIENTIFIC_EMITTED_FILENAMES),
            "operational_attempt_provenance": {
                "path": _relative_to_repo(marker_path),
                "sha256": _sha256_path(marker_path),
                "classification": "governance/provenance metadata; not a scientific emitted artifact",
            },
            "attempt_provenance": marker_payload,
        },
    )
    return report_json


def run(*, progress: bool = True, repeat_after_crash: bool = False) -> Path:
    """Execute the one explicit governed Stage 2 run."""
    registered_root = (ROOT / reg.RESULT_ROOT.rstrip("/")).resolve()
    if RESULT_ROOT.resolve() != registered_root:
        raise Stage2IntegrityError(
            "governed Stage 2 execution cannot be redirected away from the registered result namespace"
        )
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
        if not getattr(exc, "_stage2_manifest_write_started", False):
            with contextlib.suppress(Exception):
                _set_attempt_status(marker_path, marker_payload, attempt_number, "incomplete")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="execute the governed Stage 2 run")
    mode.add_argument(
        "--replay-check",
        action="store_true",
        help="replay one registered cell twice without writing output",
    )
    mode.add_argument(
        "--repeat-after-crash",
        action="store_true",
        help="recover one incomplete Stage 2 attempt with identical settings",
    )
    args = parser.parse_args()
    if args.replay_check:
        result = replay_check()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["identical"] else 1
    if args.run:
        run()
        return 0
    if args.repeat_after_crash:
        run(repeat_after_crash=True)
        return 0
    print(json.dumps(registered_plan(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
