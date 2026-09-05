"""Implementation-only runner for the registered thesis Stage 3 matrix.

The design is frozen in :mod:`stage3_registration`.  This module supplies the
execution and containment machinery required before the governed first draw;
it does not repair any guard and it has no implicit run path.  Importing it is
filesystem-inert.  The governed result root is created only by ``--run`` or
``--repeat-after-crash``.

The implementation deliberately keeps the primary question binary: did an
existing, registered guard emit its registered signal before any model work?
The Ridge/Spearman comparison is a descriptive secondary diagnostic and is
never used to change the primary decision.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.data_collection import build_cell_provenance as cell_provenance  # noqa: E402
from scripts.data_collection import derive_alternative_targets as alternative_targets  # noqa: E402
from scripts.data_collection import pipeline  # noqa: E402
from scripts.data_collection import validate as validator  # noqa: E402
from experiments import run_experiments as canonical  # noqa: E402
from experiments.placebo_lab import validate_claim_safety_text  # noqa: E402
from experiments.thesis import provenance as prov  # noqa: E402
from experiments.thesis import stage3_registration as reg  # noqa: E402


SLUG = reg.STAGE3_SLUG
DATASET_PATH = ROOT / reg.DATASET_PATH
RESULT_ROOT = prov.THESIS_RESULTS_ROOT / SLUG
REGISTERED_RESULT_ROOT = (ROOT / reg.RESULT_ROOT.rstrip("/")).resolve()
REGISTERED_REGISTRATION_MODULE_SHA256 = (
    "839c6b8679b703508e0d50f36dde3a0de9861bf9706250138d75ab63f0549f1b"
)
REGISTERED_REGISTRATION_DOC_SHA256 = (
    "8153dfe0428faf902a01e83cd2d4c9b66a2c74da1a364dd76cea5f4682a2c621"
)

REPORT_JSON_FILENAME = "defect_injection_report.json"
REPORT_MD_FILENAME = "defect_injection_report.md"
RESULTS_CSV_FILENAME = "defect_results.csv"
MANIFEST_FILENAME = "artifact_manifest.json"
STAGING_DIRNAME = ".staging"
ATTEMPTS_DIRNAME = "attempts"
ATTEMPT_MARKER_FILENAME = "attempt-{attempt_number}.json"

OUTPUT_FILENAMES = {
    "report_json": REPORT_JSON_FILENAME,
    "report_md": REPORT_MD_FILENAME,
    "defect_results": RESULTS_CSV_FILENAME,
}
SCIENTIFIC_EMITTED_FILENAMES: tuple[str, ...] = (
    REPORT_JSON_FILENAME,
    REPORT_MD_FILENAME,
    RESULTS_CSV_FILENAME,
)
EMITTED_FILENAMES: tuple[str, ...] = (
    *SCIENTIFIC_EMITTED_FILENAMES,
    MANIFEST_FILENAME,
)
OPERATIONAL_ATTEMPT_GLOB = f"{ATTEMPTS_DIRNAME}/*.json"
OPERATIONAL_FILENAMES = (OPERATIONAL_ATTEMPT_GLOB,)

TARGET_COLUMN = reg.PRIMARY_TARGET_COLUMN
KEY_COLUMNS = reg.KEY_COLUMNS
STALE_DERIVED_TARGET_COLUMNS = reg.STALE_DERIVED_TARGET_COLUMNS
VALIDATOR_SURFACES = (
    "GS_DUP_VALIDATE_ISSUE",
    "GS_TARGET_LEAK_VALIDATE_ISSUE",
    "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE",
)
ALTERNATIVE_TARGET_SURFACES = (
    "GS_REQUIRED_COLUMNS_ALT_TARGETS",
    "GS_DUP_ALT_TARGETS",
    "GS_ALIGNMENT_ALT_TARGETS",
)

SURFACE_SIGNAL = "SIGNAL_EMITTED"
SURFACE_NO_SIGNAL = "NO_SIGNAL"
SURFACE_NOT_EVALUATED = "NOT_EVALUATED"
SURFACE_BASELINE_TERMINAL = "BASELINE_TERMINAL"
SURFACE_CONTAINMENT_FAILURE = "CONTAINMENT_FAILURE"
PASS = "PASS"
FAIL = "FAIL"


class Stage3Error(RuntimeError):
    """Base error for a refused or incomplete Stage 3 operation."""


class Stage3IntegrityError(Stage3Error):
    """Raised when the closed integrity contract does not hold."""


class Stage3ContainmentError(Stage3IntegrityError):
    """Raised when an injected evaluation cannot be kept private."""


class Stage3ConsumerBoundaryError(Stage3IntegrityError):
    """Raised when stale 4001 derived-target collateral reaches the metric."""


def _canonical_json(value: object) -> bytes:
    return json.dumps(_jsonable(value), sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_path(path: Path) -> str:
    return prov.sha256_path(path)


def implementation_hash() -> str:
    return _sha256_path(Path(__file__).resolve())


def registration_hash() -> str:
    return _sha256_path(ROOT / "experiments" / "thesis" / "stage3_registration.py")


def registration_doc_hash() -> str:
    return _sha256_path(ROOT / reg.REGISTRATION_DOC)


def _relative_to_repo(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _git_metadata() -> dict[str, object]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=normal"],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"sha": sha, "short_sha": sha[:8], "dirty": dirty}
    except (OSError, subprocess.CalledProcessError):
        return {"sha": None, "short_sha": "nogit", "dirty": None}


def _registered_guard_contract() -> list[dict[str, object]]:
    return [
        {
            "defect_id": int(reg.DEFECT_IDS[name]),
            "defect_name": name,
            "expected_guard": reg.GUARD_MAP[name]["EXPECTED_GUARD"],
            "evaluated_surfaces": list(reg.GUARD_MAP[name]["EVALUATED_SURFACES"]),
            "expected_result": reg.GUARD_MAP[name]["EXPECTED_RESULT"],
            "secondary_ic_applicable": bool(
                reg.GUARD_MAP[name]["SECONDARY_IC_APPLICABLE"]
            ),
        }
        for name in reg.DEFECT_FAMILY
    ]


def _seed_schedule() -> list[dict[str, int]]:
    return [
        {
            "defect_id": int(reg.DEFECT_IDS[name]),
            "injection_seed": int(reg.injection_seed(reg.DEFECT_IDS[name])),
        }
        for name in reg.DEFECT_FAMILY
    ]


def registered_configuration() -> dict[str, object]:
    schedule = _seed_schedule()
    return {
        "experiment": SLUG,
        "result_root": reg.RESULT_ROOT,
        "source_dataset": reg.DATASET_PATH,
        "source_sha256": reg.DATASET_SHA256,
        "registration_module_sha256": REGISTERED_REGISTRATION_MODULE_SHA256,
        "registration_doc_sha256": REGISTERED_REGISTRATION_DOC_SHA256,
        "defect_family": list(reg.DEFECT_FAMILY),
        "defect_ids": {name: int(reg.DEFECT_IDS[name]) for name in reg.DEFECT_FAMILY},
        "registered_guard_contract": _registered_guard_contract(),
        "seed_schedule": schedule,
        "seed_schedule_sha256": _sha256_bytes(_canonical_json(schedule)),
        "base_seed": int(reg.BASE_SEED),
        "rng_usage": dict(reg.RNG_USAGE),
        "secondary_metric": {
            "model": reg.SECONDARY_METRIC_MODEL,
            "parameters": dict(reg.SECONDARY_METRIC_MODEL_PARAMETERS),
            "target": reg.SECONDARY_METRIC_TARGET,
            "splits": [_jsonable(split) for split in reg.SECONDARY_METRIC_SPLITS],
        },
    }


def registered_configuration_digest() -> str:
    return _sha256_bytes(_canonical_json(registered_configuration()))


def injection_seed(defect_id: int) -> int:
    """Expose the frozen deterministic seed formula without consuming RNG."""
    return reg.injection_seed(defect_id)


def _assert_registered_source_hashes() -> None:
    if not DATASET_PATH.is_file():
        raise Stage3IntegrityError(f"registered dataset not found: {DATASET_PATH}")
    if _sha256_path(DATASET_PATH) != reg.DATASET_SHA256:
        raise Stage3IntegrityError("registered dataset SHA does not match")
    if registration_hash() != REGISTERED_REGISTRATION_MODULE_SHA256:
        raise Stage3IntegrityError("registered Stage 3 module SHA does not match")
    if registration_doc_hash() != REGISTERED_REGISTRATION_DOC_SHA256:
        raise Stage3IntegrityError("registered Stage 3 document SHA does not match")
    for relative, expected in reg.SOURCE_MODULE_HASHES.items():
        path = ROOT / relative
        if not path.is_file() or _sha256_path(path) != expected:
            raise Stage3IntegrityError(f"registered source hash mismatch: {relative}")
    provenance_path = ROOT / reg.CELL_PROVENANCE_SOURCE
    if not provenance_path.is_file() or _sha256_path(provenance_path) != reg.CELL_PROVENANCE_SHA256:
        raise Stage3IntegrityError("registered cell-provenance source hash mismatch")
    for relative, expected in reg.HISTORICAL_PROTECTED_HASHES.items():
        path = ROOT / relative
        if not path.is_file() or _sha256_path(path) != expected:
            raise Stage3IntegrityError(f"historical protected hash mismatch: {relative}")
    if prov.seed_for(SLUG) != reg.BASE_SEED:
        raise Stage3IntegrityError("declared Stage 3 seed differs from registration")
    if tuple(reg.DEFECT_IDS) != tuple(reg.DEFECT_FAMILY):
        raise Stage3IntegrityError("registered defect order changed")
    if tuple(reg.DEFECT_IDS.values()) != reg.ALL_STAGE3_IDS:
        raise Stage3IntegrityError("registered Stage 3 IDs changed")
    if set(reg.RNG_USAGE.values()) != {reg.NO_RNG}:
        raise Stage3IntegrityError("a registered defect declares RNG usage")
    if _canonical_splits() != _registered_splits():
        raise Stage3IntegrityError("canonical secondary split contract changed")


def _registered_splits() -> list[tuple[str, tuple[int, ...], int]]:
    return [
        (
            str(split["name"]),
            tuple(int(year) for year in split["train_target_years"]),
            int(split["test_feature_year"]),
        )
        for split in reg.SECONDARY_METRIC_SPLITS
    ]


def _canonical_splits() -> list[tuple[str, tuple[int, ...], int]]:
    return [
        (
            str(split["name"]),
            tuple(int(year) for year in split["train_target_years"]),
            int(split["test_feature_year"]),
        )
        for split in canonical.SPLITS
    ]


def _assert_canonical_source(frame: pd.DataFrame) -> None:
    if frame.shape != (reg.DATASET_ROW_COUNT, reg.DATASET_COLUMN_COUNT):
        raise Stage3IntegrityError(f"clean source shape changed: {frame.shape}")
    if sorted(int(year) for year in frame["year"].unique()) != list(reg.DATASET_YEARS):
        raise Stage3IntegrityError("clean source years changed")
    if int((frame["year"] == reg.DATASET_MIN_YEAR).sum()) != reg.DATASET_ROWS_AT_MIN_YEAR:
        raise Stage3IntegrityError("clean source minimum-year row count changed")
    if int(frame[TARGET_COLUMN].notna().sum()) != reg.DATASET_OBSERVED_TARGET_ROWS:
        raise Stage3IntegrityError("clean source target coverage changed")
    if int(frame.duplicated(list(KEY_COLUMNS)).sum()) != reg.DATASET_DUPLICATE_KEYS:
        raise Stage3IntegrityError("clean source duplicate-key count changed")
    if not bool((frame[reg.ALIGNMENT_COLUMN] == frame["year"] + 1).all()):
        raise Stage3IntegrityError("clean source target-year alignment changed")


def load_clean_frame() -> pd.DataFrame:
    """Read and verify the pinned source without ever writing it."""
    before = _sha256_path(DATASET_PATH)
    if before != reg.DATASET_SHA256:
        raise Stage3IntegrityError("registered source SHA mismatch before read")
    frame = pd.read_csv(DATASET_PATH)
    after = _sha256_path(DATASET_PATH)
    if after != reg.DATASET_SHA256 or after != before:
        raise Stage3IntegrityError("registered source changed during read")
    _assert_canonical_source(frame)
    return frame


def _copy_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("Stage 3 injections require a pandas DataFrame")
    return frame.copy(deep=True)


def inject_future_year_feature_leakage(frame: pd.DataFrame) -> pd.DataFrame:
    """4000: copy each available same-ticker T+1 ``total_assets`` into T."""
    out = _copy_frame(frame)
    required = {"ticker", "year", "total_assets"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise Stage3IntegrityError(f"4000 missing columns: {missing}")
    clean_lookup = {
        (str(row.ticker), int(row.year)): row.total_assets
        for row in frame[["ticker", "year", "total_assets"]].itertuples(index=False)
    }
    for index, row in frame[["ticker", "year"]].iterrows():
        partner = clean_lookup.get((str(row["ticker"]), int(row["year"]) + 1))
        if (str(row["ticker"]), int(row["year"]) + 1) in clean_lookup:
            out.at[index, "total_assets"] = partner
    return out


def inject_t_tplus1_misalignment(frame: pd.DataFrame) -> pd.DataFrame:
    """4001: rotate observed primary-target values within each ticker once."""
    out = _copy_frame(frame)
    required = {"ticker", "year", TARGET_COLUMN}
    missing = sorted(required - set(out.columns))
    if missing:
        raise Stage3IntegrityError(f"4001 missing columns: {missing}")
    for _, group in frame.groupby("ticker", sort=False):
        observed = group[group[TARGET_COLUMN].notna()].sort_values("year", kind="stable")
        indices = list(observed.index)
        values = list(observed[TARGET_COLUMN])
        for position, index in enumerate(indices):
            out.at[index, TARGET_COLUMN] = values[(position - 1) % len(values)]
    return out


def inject_target_leakage_into_features(frame: pd.DataFrame) -> pd.DataFrame:
    """4002: add one undeclared feature carrying the primary target exactly."""
    out = _copy_frame(frame)
    if TARGET_COLUMN not in out.columns:
        raise Stage3IntegrityError(f"4002 missing column: {TARGET_COLUMN}")
    out["leaked_next_year_return_pct"] = frame[TARGET_COLUMN].copy()
    return out


def inject_lookahead_universe_membership(frame: pd.DataFrame) -> pd.DataFrame:
    """4003: select rows by the realized target-year median, retaining nulls."""
    out = _copy_frame(frame)
    required = {"target_year", TARGET_COLUMN, "is_training_universe", "is_public_universe", "universe_source"}
    missing = sorted(required - set(out.columns))
    if missing:
        raise Stage3IntegrityError(f"4003 missing columns: {missing}")
    target = pd.to_numeric(frame[TARGET_COLUMN], errors="coerce")
    target_year = pd.to_numeric(frame["target_year"], errors="coerce")
    medians = target[target.notna()].groupby(target_year[target.notna()]).median()
    member = target.isna() | target.ge(target_year.map(medians))
    out["is_training_universe"] = member.astype(bool)
    out["is_public_universe"] = member.astype(bool)
    out["universe_source"] = np.where(member, "lookahead_survivor", "lookahead_dropped")
    return out.loc[member].copy().reset_index(drop=True)


def inject_duplicate_row_inflation(frame: pd.DataFrame) -> pd.DataFrame:
    """4004: append an exact copy of every minimum-year row."""
    out = _copy_frame(frame)
    if "year" not in out.columns:
        raise Stage3IntegrityError("4004 missing column: year")
    minimum_year = int(frame["year"].min())
    duplicate_block = frame.loc[frame["year"] == minimum_year].copy(deep=True)
    return pd.concat([out, duplicate_block], ignore_index=True)


INJECTION_FUNCTIONS = {
    "FUTURE_YEAR_FEATURE_LEAKAGE": inject_future_year_feature_leakage,
    "T_TPLUS1_MISALIGNMENT": inject_t_tplus1_misalignment,
    "TARGET_LEAKAGE_INTO_FEATURES": inject_target_leakage_into_features,
    "LOOKAHEAD_UNIVERSE_MEMBERSHIP": inject_lookahead_universe_membership,
    "DUPLICATE_ROW_INFLATION": inject_duplicate_row_inflation,
}


def inject_defect(frame: pd.DataFrame, defect_name: str) -> pd.DataFrame:
    if defect_name not in INJECTION_FUNCTIONS or defect_name not in reg.DEFECT_FAMILY:
        raise Stage3Error(f"unknown registered Stage 3 defect: {defect_name!r}")
    return INJECTION_FUNCTIONS[defect_name](frame)


def _series_values_equal(left: pd.Series, right: pd.Series) -> bool:
    return bool(left.reset_index(drop=True).equals(right.reset_index(drop=True)))


def _changed_count(left: pd.Series, right: pd.Series) -> int:
    same = left.eq(right) | (left.isna() & right.isna())
    return int((~same).sum())


def _frame_equal(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    try:
        pd.testing.assert_frame_equal(left, right, check_exact=True, check_dtype=True)
        return True
    except AssertionError:
        return False


def _keyed_frame(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    data_columns = [column for column in columns if column not in KEY_COLUMNS]
    return frame.set_index(list(KEY_COLUMNS))[data_columns].sort_index()


def _retained_rows_equal(
    clean: pd.DataFrame, injected: pd.DataFrame, columns: Sequence[str]
) -> bool:
    clean_keys = set(map(tuple, clean[list(KEY_COLUMNS)].itertuples(index=False, name=None)))
    injected_keys = set(
        map(tuple, injected[list(KEY_COLUMNS)].itertuples(index=False, name=None))
    )
    if not injected_keys <= clean_keys:
        return False
    return _frame_equal(
        _keyed_frame(clean[clean[list(KEY_COLUMNS)].apply(tuple, axis=1).isin(injected_keys)], columns),
        _keyed_frame(injected, columns),
    )


def mechanism_invariants(
    defect_name: str, clean: pd.DataFrame, injected: pd.DataFrame
) -> dict[str, object]:
    """Return the frozen behavioral invariants for one injected construction."""
    if defect_name not in reg.GUARD_MAP:
        raise Stage3Error(f"unknown registered Stage 3 defect: {defect_name!r}")
    checks: dict[str, bool] = {}
    checks["source_shape_clean"] = clean.shape == (
        reg.DATASET_ROW_COUNT,
        reg.DATASET_COLUMN_COUNT,
    )

    if defect_name == "FUTURE_YEAR_FEATURE_LEAKAGE":
        lookup = {
            (str(row.ticker), int(row.year)): row.total_assets
            for row in clean[["ticker", "year", "total_assets"]].itertuples(index=False)
        }
        receiving = sum(
            (str(row.ticker), int(row.year) + 1) in lookup
            for row in clean[["ticker", "year"]].itertuples(index=False)
        )
        checks.update(
            {
                "shape_preserved": injected.shape == clean.shape,
                "target_year_aligned": bool((injected["target_year"] == injected["year"] + 1).all()),
                "no_duplicate_keys": int(injected.duplicated(list(KEY_COLUMNS)).sum()) == 0,
                "only_total_assets_differs": _frame_equal(
                    clean.drop(columns=["total_assets"]),
                    injected.drop(columns=["total_assets"]),
                ),
                "target_byte_identical": _series_values_equal(
                    clean[TARGET_COLUMN], injected[TARGET_COLUMN]
                ),
                "rows_receiving_future_value": receiving
                == reg.GUARD_MAP[defect_name]["EXPECTED_ROWS_RECEIVING_A_FUTURE_VALUE"],
                "rows_changed": _changed_count(clean["total_assets"], injected["total_assets"])
                == reg.GUARD_MAP[defect_name]["EXPECTED_ROWS_CHANGING_VALUE"],
                "null_pattern_preserved": bool(
                    clean["total_assets"].isna().equals(injected["total_assets"].isna())
                ),
                "future_values_are_source_values": all(
                    pd.isna(injected.iloc[index]["total_assets"])
                    or any(
                        (str(row.ticker), int(row.year))
                        == (str(clean.iloc[index]["ticker"]), int(clean.iloc[index]["year"]) + 1)
                        and row.total_assets == injected.iloc[index]["total_assets"]
                        for row in clean[["ticker", "year", "total_assets"]].itertuples(index=False)
                    )
                    for index in range(len(injected))
                    if (str(clean.iloc[index]["ticker"]), int(clean.iloc[index]["year"]) + 1)
                    in lookup
                ),
            }
        )

    elif defect_name == "T_TPLUS1_MISALIGNMENT":
        non_target = [column for column in clean.columns if column != TARGET_COLUMN]
        target_multisets_equal = True
        for ticker, group in clean.groupby("ticker", sort=False):
            injected_group = injected[injected["ticker"] == ticker]
            left = sorted(group[TARGET_COLUMN].dropna().tolist())
            right = sorted(injected_group[TARGET_COLUMN].dropna().tolist())
            target_multisets_equal &= left == right
        checks.update(
            {
                "shape_preserved": injected.shape == clean.shape,
                "target_year_aligned": bool((injected["target_year"] == injected["year"] + 1).all()),
                "no_duplicate_keys": int(injected.duplicated(list(KEY_COLUMNS)).sum()) == 0,
                "non_target_columns_identical": _frame_equal(
                    clean[non_target], injected[non_target]
                ),
                "null_pattern_preserved": bool(
                    clean[TARGET_COLUMN].isna().equals(injected[TARGET_COLUMN].isna())
                ),
                "has_target_identical": _series_values_equal(
                    clean["has_target"], injected["has_target"]
                ),
                "is_inference_row_identical": _series_values_equal(
                    clean["is_inference_row"], injected["is_inference_row"]
                ),
                "target_multiset_per_ticker": target_multisets_equal,
                "observed_target_rows": int(injected[TARGET_COLUMN].notna().sum())
                == reg.DATASET_OBSERVED_TARGET_ROWS,
                "rows_changed": _changed_count(clean[TARGET_COLUMN], injected[TARGET_COLUMN])
                == reg.GUARD_MAP[defect_name]["EXPECTED_ROWS_CHANGING_VALUE"],
            }
        )

    elif defect_name == "TARGET_LEAKAGE_INTO_FEATURES":
        added = "leaked_next_year_return_pct"
        checks.update(
            {
                "row_count_preserved": len(injected) == len(clean),
                "column_count_increased_by_one": len(injected.columns) == len(clean.columns) + 1,
                "pre_existing_columns_identical": _frame_equal(
                    clean, injected[clean.columns]
                ),
                "leak_equals_target_including_nulls": _series_values_equal(
                    injected[added], injected[TARGET_COLUMN]
                ),
                "pipeline_feature_selector_admits_leak": added in pipeline.feature_columns(injected),
                "canonical_feature_selector_admits_leak": added in canonical._feature_cols(injected),
                "no_duplicate_keys": int(injected.duplicated(list(KEY_COLUMNS)).sum()) == 0,
                "target_year_aligned": bool((injected["target_year"] == injected["year"] + 1).all()),
            }
        )

    elif defect_name == "LOOKAHEAD_UNIVERSE_MEMBERSHIP":
        membership_columns = (
            "is_training_universe",
            "is_public_universe",
            "universe_source",
        )
        non_membership = [column for column in clean.columns if column not in membership_columns]
        expected_member_rows = int(reg.GUARD_MAP[defect_name]["EXPECTED_MEMBER_ROWS"])
        expected_dropped_rows = int(reg.GUARD_MAP[defect_name]["EXPECTED_DROPPED_ROWS"])
        checks.update(
            {
                "retained_row_count": len(injected) == expected_member_rows,
                "dropped_row_count": len(clean) - len(injected) == expected_dropped_rows,
                "no_rows_added": len(injected) <= len(clean),
                "no_duplicate_keys": int(injected.duplicated(list(KEY_COLUMNS)).sum()) == 0,
                "target_year_aligned": bool((injected["target_year"] == injected["year"] + 1).all()),
                "retained_non_membership_values_identical": _retained_rows_equal(
                    clean, injected, non_membership
                ),
                "only_membership_columns_changed": _retained_rows_equal(
                    clean, injected, non_membership
                ),
                "null_targets_retained": bool(
                    set(
                        map(
                            tuple,
                            clean.loc[clean[TARGET_COLUMN].isna(), list(KEY_COLUMNS)].itertuples(
                                index=False, name=None
                            ),
                        )
                    )
                    <= set(
                        map(
                            tuple,
                            injected[list(KEY_COLUMNS)].itertuples(index=False, name=None),
                        )
                    )
                ),
            }
        )

    elif defect_name == "DUPLICATE_ROW_INFLATION":
        minimum_year = int(clean["year"].min())
        duplicate_block = clean.loc[clean["year"] == minimum_year].reset_index(drop=True)
        appended = injected.iloc[len(clean) :].reset_index(drop=True)
        checks.update(
            {
                "row_count_increased_by_minimum_year_rows": injected.shape
                == (len(clean) + reg.DATASET_ROWS_AT_MIN_YEAR, len(clean.columns)),
                "column_count_preserved": list(injected.columns) == list(clean.columns),
                "exact_duplicate_count": int(injected.duplicated(list(KEY_COLUMNS)).sum())
                == reg.DATASET_ROWS_AT_MIN_YEAR,
                "appended_block_value_identical": _frame_equal(appended, duplicate_block),
                "original_prefix_identical": _frame_equal(injected.iloc[: len(clean)], clean),
                "target_year_aligned": bool((injected["target_year"] == injected["year"] + 1).all()),
            }
        )

    checks["all_registered_invariants_passed"] = all(checks.values())
    return {
        "defect_name": defect_name,
        "checks": checks,
        "passed": bool(checks["all_registered_invariants_passed"]),
    }


def assert_mechanism_invariants(
    defect_name: str, clean: pd.DataFrame, injected: pd.DataFrame
) -> dict[str, object]:
    result = mechanism_invariants(defect_name, clean, injected)
    if not result["passed"]:
        failed = [name for name, passed in result["checks"].items() if not passed]
        raise Stage3IntegrityError(
            f"{defect_name} mechanism invariants failed: {', '.join(failed)}"
        )
    return result


def _surface_record(
    surface: str,
    status: str,
    *,
    invocation_count: int = 0,
    signal: str | None = None,
    message: str | None = None,
    reason: str | None = None,
    checkpoints: Sequence[str] = (),
) -> dict[str, object]:
    result: dict[str, object] = {
        "surface": surface,
        "status": status,
        "invocation_count": int(invocation_count),
        "signal_emitted": status == SURFACE_SIGNAL,
        "checkpoints": list(checkpoints),
    }
    if signal is not None:
        result["signal"] = signal
    if message is not None:
        result["message"] = message
    if reason is not None:
        result["reason"] = reason
    return result


@contextlib.contextmanager
def _redirect_validator_outputs(root: Path) -> Iterator[dict[str, Path]]:
    """Redirect all four validator writers and restore them on every exit."""
    paths = {
        "pipeline.QUALITY_JSON": root / "data_quality_report.json",
        "pipeline.QUALITY_MD": root / "data_quality_report.md",
        "validator.FEATURE_JSON": root / "feature_engineering_report.json",
        "validator.FEATURE_MD": root / "feature_engineering_report.md",
    }
    originals = {
        "pipeline.QUALITY_JSON": pipeline.QUALITY_JSON,
        "pipeline.QUALITY_MD": pipeline.QUALITY_MD,
        "validator.FEATURE_JSON": validator.FEATURE_JSON,
        "validator.FEATURE_MD": validator.FEATURE_MD,
    }
    for path in paths.values():
        if not path.resolve().is_relative_to(root.resolve()):
            raise Stage3ContainmentError("validator output escaped private directory")
    restoration_error: BaseException | None = None
    try:
        pipeline.QUALITY_JSON = paths["pipeline.QUALITY_JSON"]
        pipeline.QUALITY_MD = paths["pipeline.QUALITY_MD"]
        validator.FEATURE_JSON = paths["validator.FEATURE_JSON"]
        validator.FEATURE_MD = paths["validator.FEATURE_MD"]
        yield paths
    finally:
        try:
            pipeline.QUALITY_JSON = originals["pipeline.QUALITY_JSON"]
            pipeline.QUALITY_MD = originals["pipeline.QUALITY_MD"]
            validator.FEATURE_JSON = originals["validator.FEATURE_JSON"]
            validator.FEATURE_MD = originals["validator.FEATURE_MD"]
        except BaseException as exc:  # pragma: no cover - defensive cleanup path
            restoration_error = exc
        if restoration_error is not None:
            raise Stage3ContainmentError("validator output attributes were not restored") from restoration_error
        if (
            pipeline.QUALITY_JSON != originals["pipeline.QUALITY_JSON"]
            or pipeline.QUALITY_MD != originals["pipeline.QUALITY_MD"]
            or validator.FEATURE_JSON != originals["validator.FEATURE_JSON"]
            or validator.FEATURE_MD != originals["validator.FEATURE_MD"]
        ):
            raise Stage3ContainmentError("validator output attributes were not restored")


def _run_validator(frame: pd.DataFrame, private_root: Path) -> dict[str, object]:
    private_root.mkdir(parents=True, exist_ok=True)
    cfg = pipeline.PipelineConfig()
    cfg.say = lambda message: cfg.log.append(str(message))  # type: ignore[method-assign]
    with _redirect_validator_outputs(private_root) as output_paths:
        report = validator.validate(frame, cfg)
        if not all(path.resolve().is_relative_to(private_root.resolve()) for path in output_paths.values()):
            raise Stage3ContainmentError("validator wrote outside private directory")
    return report


def _private_csv(frame: pd.DataFrame, private_root: Path) -> Path:
    path = private_root / "injected_modeling.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    if path.resolve().is_relative_to(ROOT / "data") or path.resolve().is_relative_to(REGISTERED_RESULT_ROOT):
        raise Stage3ContainmentError("private CSV is inside a forbidden canonical root")
    return path


def _private_provenance_root(frame: pd.DataFrame, private_root: Path) -> Path:
    root = private_root / "provenance_repo"
    root.mkdir(parents=True, exist_ok=True)
    for relative in cell_provenance.SOURCE_ARTIFACT_RELS:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if relative == cell_provenance.DATASET_REL:
            frame.to_csv(destination, index=False)
        else:
            source = ROOT / relative
            if not source.is_file():
                raise Stage3ContainmentError(f"private provenance input is missing: {relative}")
            shutil.copyfile(source, destination)
    if not root.resolve().is_relative_to(private_root.resolve()):
        raise Stage3ContainmentError("private provenance root escaped temporary root")
    return root


def _load_private_provenance_rows(
    frame: pd.DataFrame, private_root: Path
) -> tuple[Path, list[str], list[dict[str, str]]]:
    root = _private_provenance_root(frame, private_root)
    columns, rows = cell_provenance.read_csv_rows(root / cell_provenance.DATASET_REL)
    return root, columns, rows


def _evaluate_provenance(
    frame: pd.DataFrame, surfaces: Sequence[str], private_root: Path
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    terminal: dict[str, object] = {}
    try:
        provenance_root, columns, rows = _load_private_provenance_rows(frame, private_root)
    except BaseException as exc:
        for surface in surfaces:
            results[surface] = _surface_record(
                surface,
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=str(exc),
                reason="private provenance inputs could not be materialized",
            )
        return results, terminal
    try:
        cell_provenance.generate(provenance_root)
        generate_error: cell_provenance.ProvenanceError | None = None
    except cell_provenance.ProvenanceError as exc:
        generate_error = exc
    except BaseException as exc:
        for surface in surfaces:
            results[surface] = _surface_record(
                surface,
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=str(exc),
                reason="unexpected private provenance failure",
            )
        return results, terminal

    message = str(generate_error) if generate_error is not None else ""
    if "GS_CELL_PROVENANCE_COLUMN_COVERAGE" in surfaces:
        if message == "passports v1 does not cover exactly the dataset columns":
            checkpoints = ["generate"]
            direct_signal = None
            try:
                cell_provenance.build_records(columns, rows, {})
            except cell_provenance.ProvenanceError as exc:
                if str(exc) == (
                    "columns absent from the frozen resolution table: "
                    "['leaked_next_year_return_pct']"
                ):
                    direct_signal = str(exc)
                    checkpoints.append("build_records")
                else:
                    for surface in surfaces:
                        results[surface] = _surface_record(
                            surface,
                            SURFACE_CONTAINMENT_FAILURE,
                            invocation_count=1,
                            message=str(exc),
                            reason="unexpected private provenance checkpoint failure",
                        )
                    return results, terminal
            except BaseException as exc:
                for surface in surfaces:
                    results[surface] = _surface_record(
                        surface,
                        SURFACE_CONTAINMENT_FAILURE,
                        invocation_count=1,
                        message=str(exc),
                        reason="unexpected private provenance checkpoint failure",
                    )
                return results, terminal
            signals = [message]
            if direct_signal is not None:
                signals.append(direct_signal)
            results["GS_CELL_PROVENANCE_COLUMN_COVERAGE"] = _surface_record(
                "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                SURFACE_SIGNAL,
                invocation_count=1,
                signal="; ".join(signals),
                message=message,
                checkpoints=checkpoints,
            )
        elif generate_error is None or message.startswith(
            "upstream cell not present in the artifact: "
        ) or message.startswith("duplicate dataset key: "):
            results["GS_CELL_PROVENANCE_COLUMN_COVERAGE"] = _surface_record(
                "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                SURFACE_NO_SIGNAL,
                invocation_count=1,
                checkpoints=["generate"],
            )
        else:
            results["GS_CELL_PROVENANCE_COLUMN_COVERAGE"] = _surface_record(
                "GS_CELL_PROVENANCE_COLUMN_COVERAGE",
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=message,
                reason="unexpected provenance error",
            )

    if "GS_CELL_PROVENANCE_DUP_KEY" in surfaces:
        if message.startswith("duplicate dataset key: "):
            results["GS_CELL_PROVENANCE_DUP_KEY"] = _surface_record(
                "GS_CELL_PROVENANCE_DUP_KEY",
                SURFACE_SIGNAL,
                invocation_count=1,
                signal=message,
                message=message,
                checkpoints=["generate", "build_records"],
            )
        elif message == "passports v1 does not cover exactly the dataset columns":
            results["GS_CELL_PROVENANCE_DUP_KEY"] = _surface_record(
                "GS_CELL_PROVENANCE_DUP_KEY",
                SURFACE_NO_SIGNAL,
                invocation_count=1,
                message="build_records reached the registered duplicate-key boundary after the earlier column-coverage signal",
                reason="the duplicate-key condition was not satisfied",
                checkpoints=["generate", "build_records"],
            )
        elif generate_error is None or message.startswith(
            "upstream cell not present in the artifact: "
        ):
            results["GS_CELL_PROVENANCE_DUP_KEY"] = _surface_record(
                "GS_CELL_PROVENANCE_DUP_KEY",
                SURFACE_NO_SIGNAL,
                invocation_count=1,
                checkpoints=["generate", "build_records"],
            )
        else:
            results["GS_CELL_PROVENANCE_DUP_KEY"] = _surface_record(
                "GS_CELL_PROVENANCE_DUP_KEY",
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=message,
                reason="unexpected provenance error",
            )

    if message.startswith("upstream cell not present in the artifact: "):
        terminal["surface"] = "GS_CELL_PROVENANCE_LINEAGE_CLOSURE"
        terminal["status"] = SURFACE_BASELINE_TERMINAL
        terminal["message"] = message
        terminal["registered_as_detection_signal"] = False
    elif generate_error is None:
        terminal["surface"] = "GS_CELL_PROVENANCE_LINEAGE_CLOSURE"
        terminal["status"] = SURFACE_NO_SIGNAL
        terminal["registered_as_detection_signal"] = False

    return results, terminal


def _evaluate_alternative_targets(
    frame: pd.DataFrame, surfaces: Sequence[str], private_root: Path
) -> dict[str, dict[str, object]]:
    results: dict[str, dict[str, object]] = {}
    try:
        path = _private_csv(frame, private_root)
        alternative_targets._load_modeling(path)
    except ValueError as exc:
        message = str(exc)
        if "is missing required columns:" in message:
            signal_surface = "GS_REQUIRED_COLUMNS_ALT_TARGETS"
        elif message.endswith(" contains duplicate ticker/year keys"):
            signal_surface = "GS_DUP_ALT_TARGETS"
        elif message == "modeling target_year must align exactly to year + 1":
            signal_surface = "GS_ALIGNMENT_ALT_TARGETS"
        else:
            for surface in surfaces:
                results[surface] = _surface_record(
                    surface,
                    SURFACE_CONTAINMENT_FAILURE,
                    invocation_count=1,
                    message=message,
                    reason="unexpected alternative-target failure",
                )
            return results
        for surface in surfaces:
            if surface == signal_surface:
                results[surface] = _surface_record(
                    surface,
                    SURFACE_SIGNAL,
                    invocation_count=1,
                    signal=message,
                    message=message,
                    checkpoints=["_load_modeling"],
                )
            elif surface == "GS_ALIGNMENT_ALT_TARGETS" and signal_surface == "GS_DUP_ALT_TARGETS":
                results[surface] = _surface_record(
                    surface,
                    SURFACE_NOT_EVALUATED,
                    reason="_load_modeling fails fast at duplicate-key validation",
                )
            else:
                results[surface] = _surface_record(
                    surface,
                    SURFACE_NO_SIGNAL,
                    invocation_count=1,
                    checkpoints=["_load_modeling"],
                )
    except BaseException as exc:
        return {
            surface: _surface_record(
                surface,
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=str(exc),
                reason="unexpected private alternative-target failure",
            )
            for surface in surfaces
        }
    else:
        for surface in surfaces:
            results[surface] = _surface_record(
                surface,
                SURFACE_NO_SIGNAL,
                invocation_count=1,
                checkpoints=["_load_modeling"],
            )
    return results


def _evaluate_validator(
    frame: pd.DataFrame, surfaces: Sequence[str], private_root: Path
) -> dict[str, dict[str, object]]:
    try:
        report = _run_validator(frame, private_root)
    except BaseException as exc:
        return {
            surface: _surface_record(
                surface,
                SURFACE_CONTAINMENT_FAILURE,
                invocation_count=1,
                message=str(exc),
                reason="validator could not be executed with private output redirection",
            )
            for surface in surfaces
        }
    issues = set(report.get("issues", []))
    signals = {
        "GS_DUP_VALIDATE_ISSUE": (
            any(issue.endswith(" duplicate ticker-year rows") for issue in issues)
            and report.get("valid_for_T_to_T1_modeling") is False
        ),
        "GS_TARGET_LEAK_VALIDATE_ISSUE": (
            "LEAKAGE: next_year_return_pct present in feature set" in issues
        ),
        "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE": (
            "LEAKAGE: same_year_return_pct present in feature set" in issues
        ),
    }
    result: dict[str, dict[str, object]] = {}
    for surface in surfaces:
        signal = signals[surface]
        matching = next(
            (
                issue
                for issue in issues
                if (
                    surface == "GS_DUP_VALIDATE_ISSUE"
                    and issue.endswith(" duplicate ticker-year rows")
                )
                or (
                    surface == "GS_TARGET_LEAK_VALIDATE_ISSUE"
                    and issue == "LEAKAGE: next_year_return_pct present in feature set"
                )
                or (
                    surface == "GS_SAME_YEAR_LEAK_VALIDATE_ISSUE"
                    and issue == "LEAKAGE: same_year_return_pct present in feature set"
                )
            ),
            None,
        )
        result[surface] = _surface_record(
            surface,
            SURFACE_SIGNAL if signal else SURFACE_NO_SIGNAL,
            invocation_count=1,
            signal=matching,
            message=matching,
            checkpoints=["validate"],
        )
    return result


def evaluate_guard_surfaces(
    frame: pd.DataFrame,
    defect_name: str,
    *,
    comparator: str = "injected",
) -> dict[str, object]:
    """Execute exactly the registered reachable surfaces in private storage."""
    if defect_name not in reg.GUARD_MAP:
        raise Stage3Error(f"unknown registered Stage 3 defect: {defect_name!r}")
    registered_surfaces = tuple(reg.GUARD_MAP[defect_name]["EVALUATED_SURFACES"])
    with tempfile.TemporaryDirectory(prefix="financeiq-stage3-") as temporary:
        private_root = Path(temporary)
        surface_results: dict[str, dict[str, object]] = {}
        terminal: dict[str, object] = {}

        if any(surface in VALIDATOR_SURFACES for surface in registered_surfaces):
            surface_results.update(
                _evaluate_validator(
                    frame,
                    [surface for surface in VALIDATOR_SURFACES if surface in registered_surfaces],
                    private_root / "validator",
                )
            )
        if any(surface in ALTERNATIVE_TARGET_SURFACES for surface in registered_surfaces):
            surface_results.update(
                _evaluate_alternative_targets(
                    frame,
                    [surface for surface in ALTERNATIVE_TARGET_SURFACES if surface in registered_surfaces],
                    private_root / "alternative_targets",
                )
            )
        provenance_surfaces = [
            surface
            for surface in ("GS_CELL_PROVENANCE_COLUMN_COVERAGE", "GS_CELL_PROVENANCE_DUP_KEY")
            if surface in registered_surfaces
        ]
        if provenance_surfaces:
            provenance_results, terminal = _evaluate_provenance(
                frame, provenance_surfaces, private_root / "provenance"
            )
            surface_results.update(provenance_results)

        for surface in registered_surfaces:
            surface_results.setdefault(
                surface,
                _surface_record(
                    surface,
                    SURFACE_NOT_EVALUATED,
                    reason="surface was not in the registered reachable execution path",
                ),
            )

        all_surfaces = set(reg.GUARD_SURFACES)
        for surface in sorted(all_surfaces - set(surface_results)):
            reachability = reg.GUARD_SURFACES[surface]["reachability"]
            reason = (
                "input-blind surface is not evaluated; silence is not evidence"
                if reachability == "INPUT_BLIND"
                else "surface is outside this defect's registered evaluated set"
            )
            surface_results[surface] = _surface_record(surface, SURFACE_NOT_EVALUATED, reason=reason)

        signals = [
            result
            for result in surface_results.values()
            if result.get("signal_emitted") is True
        ]
        failures = [
            result
            for result in surface_results.values()
            if result["status"] == SURFACE_CONTAINMENT_FAILURE
        ]
        expected_invocations = {
            surface: surface_results[surface]["invocation_count"]
            for surface in registered_surfaces
        }
        invocation_accounting = all(
            count == 1
            for surface, count in expected_invocations.items()
            if surface_results[surface]["status"] != SURFACE_NOT_EVALUATED
        )
    containment_restored = not private_root.exists()
    registered_surfaces_completed = all(
        surface_results[surface]["status"] != SURFACE_NOT_EVALUATED
        and surface_results[surface]["invocation_count"] == 1
        for surface in registered_surfaces
    )
    return {
        "comparator": comparator,
        "evaluated_surfaces": list(registered_surfaces),
        "surface_results": [surface_results[surface] for surface in sorted(surface_results)],
        "detection_signals": signals,
        "detected_by": [result["surface"] for result in signals],
        "containment_failures": failures,
        "containment_passed": not failures,
        "cleanup_proven": containment_restored and not private_root.exists(),
        "invocation_accounting_passed": invocation_accounting
        and registered_surfaces_completed,
        "provenance_terminal": terminal,
    }


def _fit_ic_for_split(
    panel: pd.DataFrame,
    feature_columns: Sequence[str],
    split: tuple[str, tuple[int, ...], int],
) -> dict[str, object]:
    name, train_target_years, test_feature_year = split
    train = panel[(panel["feature_year"] + 1).isin(train_target_years)]
    test = panel[panel["feature_year"] == test_feature_year]
    y_train = pd.to_numeric(train["target_return"], errors="coerce").to_numpy(float)
    y_test = pd.to_numeric(test["target_return"], errors="coerce").to_numpy(float)
    X_train = train[list(feature_columns)].to_numpy(float)
    X_test = test[list(feature_columns)].to_numpy(float)
    train_mask = np.isfinite(y_train)
    test_mask = np.isfinite(y_test)
    X_train = np.nan_to_num(X_train[train_mask], nan=0.5)
    y_train = y_train[train_mask]
    X_test = np.nan_to_num(X_test[test_mask], nan=0.5)
    y_test = y_test[test_mask]
    if len(y_train) < 5 or len(y_test) < 3:
        return {
            "name": name,
            "train_target_years": list(train_target_years),
            "test_feature_year": test_feature_year,
            "n_train": int(len(y_train)),
            "n_test": int(len(y_test)),
            "clean_ic": None,
            "injected_ic": None,
            "delta_ic": None,
            "status": "INSUFFICIENT_ROWS",
        }
    model = Ridge(alpha=float(reg.SECONDARY_METRIC_MODEL_PARAMETERS["alpha"]))
    model.fit(X_train, y_train)
    prediction = model.predict(X_test)
    ic = pd.Series(prediction).corr(pd.Series(y_test), method="spearman")
    return {
        "name": name,
        "train_target_years": list(train_target_years),
        "test_feature_year": test_feature_year,
        "n_train": int(len(y_train)),
        "n_test": int(len(y_test)),
        "ic": None if pd.isna(ic) else float(ic),
        "status": "OK" if not pd.isna(ic) else "NONFINITE_IC",
    }


def _panel_from_private_path(path: Path) -> tuple[pd.DataFrame, list[str]]:
    original = canonical.TRAINING_MODELING
    try:
        canonical.TRAINING_MODELING = path
        panel, feature_columns = canonical.build_panel_for_target(
            target_col=reg.SECONDARY_METRIC_TARGET,
            target_path=None,
        )
    finally:
        canonical.TRAINING_MODELING = original
    if panel is None or not feature_columns:
        raise Stage3IntegrityError("canonical secondary panel is empty")
    forbidden = set(STALE_DERIVED_TARGET_COLUMNS) | {reg.PRIMARY_TARGET_COLUMN}
    consumed = sorted(forbidden.intersection(feature_columns))
    if consumed:
        raise Stage3ConsumerBoundaryError(
            "4001 stale-derived-target consumer boundary violated: "
            + ", ".join(consumed)
        )
    if any(column.startswith("next_year_") for column in feature_columns):
        raise Stage3ConsumerBoundaryError(
            "4001 next_year_* consumer boundary violated"
        )
    return panel, list(feature_columns)


def compute_secondary_ic(
    clean: pd.DataFrame, injected: pd.DataFrame
) -> dict[str, object]:
    """Compute only the registered per-split descriptive IC distortion."""
    if _canonical_splits() != _registered_splits():
        raise Stage3IntegrityError("canonical secondary split contract changed")
    with tempfile.TemporaryDirectory(prefix="financeiq-stage3-ic-") as temporary:
        root = Path(temporary)
        clean_path = root / "clean.csv"
        injected_path = root / "injected.csv"
        clean.to_csv(clean_path, index=False)
        injected.to_csv(injected_path, index=False)
        clean_panel, clean_features = _panel_from_private_path(clean_path)
        injected_panel, injected_features = _panel_from_private_path(injected_path)
        if clean_features != injected_features:
            raise Stage3IntegrityError("clean and injected secondary feature selectors differ")
        split_rows: list[dict[str, object]] = []
        for split in _registered_splits():
            clean_row = _fit_ic_for_split(clean_panel, clean_features, split)
            injected_row = _fit_ic_for_split(injected_panel, injected_features, split)
            clean_ic = clean_row.get("ic")
            injected_ic = injected_row.get("ic")
            delta = (
                None
                if clean_ic is None or injected_ic is None
                else float(injected_ic) - float(clean_ic)
            )
            split_rows.append(
                {
                    "name": split[0],
                    "train_target_years": list(split[1]),
                    "test_feature_year": split[2],
                    "clean_ic": clean_ic,
                    "injected_ic": injected_ic,
                    "delta_ic": delta,
                    "n_train_clean": clean_row["n_train"],
                    "n_test_clean": clean_row["n_test"],
                    "n_train_injected": injected_row["n_train"],
                    "n_test_injected": injected_row["n_test"],
                }
            )
    return {
        "metric": reg.SECONDARY_METRIC,
        "model": reg.SECONDARY_METRIC_MODEL,
        "alpha": float(reg.SECONDARY_METRIC_MODEL_PARAMETERS["alpha"]),
        "target": reg.SECONDARY_METRIC_TARGET,
        "rank_method": reg.SECONDARY_METRIC_RANK_METHOD,
        "rank_percentile": reg.SECONDARY_METRIC_RANK_PERCENTILE,
        "imputation": reg.SECONDARY_METRIC_IMPUTATION,
        "feature_columns": list(clean_features),
        "stale_derived_target_columns_consumed": [],
        "splits": split_rows,
        "pooled": False,
        "threshold": None,
        "significance_test": False,
        "gating": False,
    }


def _frame_fingerprint(frame: pd.DataFrame) -> str:
    return _sha256_bytes(frame.to_csv(index=False).encode("utf-8"))


def evaluate_defect(
    defect_name: str, clean: pd.DataFrame, injected: pd.DataFrame
) -> dict[str, object]:
    """Evaluate one completed construction, with integrity before science."""
    spec = reg.GUARD_MAP[defect_name]
    invariants = mechanism_invariants(defect_name, clean, injected)
    clean_eval = evaluate_guard_surfaces(clean, defect_name, comparator="clean")
    injected_eval = evaluate_guard_surfaces(injected, defect_name, comparator="injected")
    secondary: dict[str, object] | None = None
    status = reg.INCONCLUSIVE
    failure_reasons: list[str] = []
    if not invariants["passed"]:
        failure_reasons.append("mechanism invariants failed")
    if clean_eval["detection_signals"]:
        failure_reasons.append("clean comparator emitted a registered detection signal")
    if not clean_eval["containment_passed"] or not injected_eval["containment_passed"]:
        failure_reasons.append("containment failure")
    if not clean_eval["invocation_accounting_passed"] or not injected_eval["invocation_accounting_passed"]:
        failure_reasons.append("registered surface invocation accounting failed")
    if not failure_reasons:
        status = reg.DETECTED if injected_eval["detection_signals"] else reg.NOT_DETECTED
        if status == reg.NOT_DETECTED and bool(spec["SECONDARY_IC_APPLICABLE"]):
            try:
                secondary = compute_secondary_ic(clean, injected)
            except Stage3ConsumerBoundaryError:
                status = reg.INCONCLUSIVE
                failure_reasons.append("4001 stale-derived-target consumer boundary violation")
            except BaseException as exc:
                status = reg.INCONCLUSIVE
                failure_reasons.append(f"secondary IC execution failure: {exc}")
    return {
        "defect_id": int(spec["DEFECT_ID"]),
        "defect_name": defect_name,
        "status": status,
        "expected_result": spec["EXPECTED_RESULT"],
        "expected_guard": spec["EXPECTED_GUARD"],
        "expected_detection_signal": _jsonable(spec["EXACT_DETECTION_SIGNAL"]),
        "detected_by": injected_eval["detected_by"],
        "clean_comparator": clean_eval,
        "injected_guard_evaluation": injected_eval,
        "mechanism_invariants": invariants,
        "secondary_ic": secondary,
        "secondary_ic_computed": secondary is not None,
        "containment_passed": bool(
            clean_eval["containment_passed"] and injected_eval["containment_passed"]
        ),
        "failure_reasons": failure_reasons,
    }


def decide(
    defect_results: Sequence[Mapping[str, object]], *, integrity_passed: bool
) -> str:
    """Apply the frozen precedence: integrity/INCONCLUSIVE before PASS/FAIL."""
    if not integrity_passed:
        return reg.INCONCLUSIVE
    if any(result.get("status") == reg.INCONCLUSIVE for result in defect_results):
        return reg.INCONCLUSIVE
    if len(defect_results) != reg.DEFECT_FAMILY_SIZE:
        return reg.INCONCLUSIVE
    if all(result.get("status") == reg.DETECTED for result in defect_results):
        return PASS
    return FAIL


def _path_digest(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"exists": False, "files": {}}
    if path.is_symlink():
        return {"exists": True, "symlink": os.readlink(path), "files": {}}
    if path.is_file():
        return {"exists": True, "files": {".": _sha256_path(path)}}
    files: dict[str, str] = {}
    for child in sorted(path.rglob("*")):
        if child.is_symlink():
            files[child.relative_to(path).as_posix()] = f"symlink:{os.readlink(child)}"
        elif child.is_file():
            files[child.relative_to(path).as_posix()] = _sha256_path(child)
    return {"exists": True, "files": files}


def protected_workspace_digest() -> dict[str, object]:
    paths = (
        ROOT / "data" / "trusted",
        ROOT / "data" / "trusted_raw",
        ROOT / "data" / "trusted_clean",
        ROOT / "data" / "config",
        ROOT / "data" / "provenance",
        ROOT / "experiments" / "results_thesis" / "positive_control",
        ROOT / "experiments" / "results_thesis" / "positive_control_calibration",
        ROOT / "experiments" / "results_thesis" / "negative_control",
    )
    return {_relative_to_repo(path): _path_digest(path) for path in paths}


def _module_digest() -> dict[str, object]:
    paths = dict(reg.SOURCE_MODULE_HASHES)
    paths[reg.CELL_PROVENANCE_SOURCE] = reg.CELL_PROVENANCE_SHA256
    paths.update(reg.HISTORICAL_PROTECTED_HASHES)
    return {
        relative: _sha256_path(ROOT / relative) if (ROOT / relative).is_file() else None
        for relative in paths
    }


def _attempt_path(root: Path, number: int) -> Path:
    return root / ATTEMPTS_DIRNAME / ATTEMPT_MARKER_FILENAME.format(attempt_number=number)


def _atomic_json_write(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    try:
        temporary.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _new_attempt_record(number: int, attempt_type: str, prior_incomplete: bool) -> dict[str, object]:
    configuration = registered_configuration()
    return {
        "schema_version": 1,
        "governance_class": "operational_attempt_provenance",
        "experiment": SLUG,
        "completion_authority": MANIFEST_FILENAME,
        "attempt_number": int(number),
        "attempt_type": attempt_type,
        "prior_incomplete_attempt": bool(prior_incomplete),
        "registered_configuration_sha256": registered_configuration_digest(),
        "seed_schedule_sha256": configuration["seed_schedule_sha256"],
        "status": "in_progress",
        "started_at_utc": _utc_now(),
    }


def _load_attempt_records(root: Path) -> list[tuple[Path, dict[str, object]]]:
    attempts_dir = root / ATTEMPTS_DIRNAME
    if not attempts_dir.is_dir() or attempts_dir.is_symlink():
        raise Stage3Error("incomplete Stage 3 root has no safe attempts directory")
    records: list[tuple[Path, dict[str, object]]] = []
    for path in sorted(attempts_dir.glob("attempt-*.json")):
        if path.is_symlink():
            raise Stage3Error("Stage 3 attempt record is a symlink")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Stage3Error("Stage 3 attempt record is unreadable") from exc
        if payload.get("governance_class") != "operational_attempt_provenance":
            raise Stage3Error("Stage 3 attempt record is not operational provenance")
        if payload.get("experiment") != SLUG:
            raise Stage3Error("Stage 3 attempt record belongs to another experiment")
        if payload.get("registered_configuration_sha256") != registered_configuration_digest():
            raise Stage3Error("registered Stage 3 configuration changed; recovery refused")
        records.append((path, payload))
    if not records:
        raise Stage3Error("incomplete Stage 3 root has no attempt records")
    numbers = [record.get("attempt_number") for _, record in records]
    if any(not isinstance(number, int) for number in numbers) or len(set(numbers)) != len(numbers):
        raise Stage3Error("Stage 3 attempt numbering is invalid")
    return records


def _is_complete_run(root: Path) -> bool:
    manifest = root / MANIFEST_FILENAME
    if not root.is_dir() or not manifest.is_file() or manifest.is_symlink():
        return False
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        records = _load_attempt_records(root)
    except (OSError, json.JSONDecodeError, Stage3Error):
        return False
    direct = {path.name for path in root.iterdir() if path.is_file()}
    expected = set(EMITTED_FILENAMES) | {MANIFEST_FILENAME}
    return bool(
        payload.get("experiment") == SLUG
        and payload.get("completion_status") == "complete"
        and payload.get("completion_authority") == MANIFEST_FILENAME
        and payload.get("integrity_passed") is True
        and payload.get("registered_configuration_sha256") == registered_configuration_digest()
        and direct == expected
        and not (root / STAGING_DIRNAME).exists()
        and records[-1][1].get("status") == "complete"
    )


def _cleanup_incomplete_root(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise Stage3Error("incomplete Stage 3 root is not a safe directory")
    _load_attempt_records(root)
    allowed_direct = set(SCIENTIFIC_EMITTED_FILENAMES) | {MANIFEST_FILENAME}
    for child in sorted(root.iterdir()):
        if child.name == ATTEMPTS_DIRNAME:
            continue
        if child.name == STAGING_DIRNAME:
            if child.is_symlink() or not child.is_dir():
                raise Stage3Error("unsafe Stage 3 staging path")
            shutil.rmtree(child)
            continue
        if child.name in allowed_direct:
            if child.is_symlink() or not child.is_file():
                raise Stage3Error(f"unsafe Stage 3 output path: {child.name}")
            child.unlink()
            continue
        raise Stage3Error(f"incomplete Stage 3 root contains unrecognized path {child.name!r}")


def _prepare_attempt(*, repeat_after_crash: bool) -> tuple[Path, Path, dict[str, object], int]:
    root = RESULT_ROOT
    if root.is_symlink() or (root.exists() and not root.is_dir()):
        raise Stage3Error("Stage 3 result root is not a safe directory")
    if not repeat_after_crash:
        if root.exists() and any(root.iterdir()):
            if _is_complete_run(root):
                raise Stage3Error("a complete Stage 3 run already exists; --run refuses overwrite")
            raise Stage3Error("a pre-existing non-empty Stage 3 result root exists; use --repeat-after-crash")
        root.mkdir(parents=True, exist_ok=True)
        record = _new_attempt_record(1, "initial", False)
        marker = _attempt_path(root, 1)
        _atomic_json_write(marker, record)
        return root, marker, record, 1
    if not root.is_dir() or not any(root.iterdir()):
        raise Stage3Error("--repeat-after-crash requires a non-empty incomplete Stage 3 root")
    if _is_complete_run(root):
        raise Stage3Error("--repeat-after-crash refuses a complete Stage 3 run")
    records = _load_attempt_records(root)
    _cleanup_incomplete_root(root)
    number = max(int(record["attempt_number"]) for _, record in records) + 1
    record = _new_attempt_record(number, "crash_recovery", True)
    marker = _attempt_path(root, number)
    _atomic_json_write(marker, record)
    return root, marker, record, number


def _set_attempt_status(path: Path, payload: Mapping[str, object], status: str) -> dict[str, object]:
    updated = dict(payload)
    updated["status"] = status
    updated["finished_at_utc"] = _utc_now()
    _atomic_json_write(path, updated)
    return updated


def _audit_output_surface(root: Path, expected_names: Sequence[str]) -> dict[str, object]:
    direct_files = sorted(path.name for path in root.iterdir() if path.is_file())
    direct_directories = sorted(path.name for path in root.iterdir() if path.is_dir())
    return {
        "actual_direct_files": direct_files,
        "unexpected_files": sorted(set(direct_files) - set(expected_names)),
        "missing_files": sorted(set(expected_names) - set(direct_files)),
        "unexpected_directories": [
            name for name in direct_directories if name != ATTEMPTS_DIRNAME
        ],
        "passed": set(direct_files) == set(expected_names)
        and not [name for name in direct_directories if name != ATTEMPTS_DIRNAME],
    }


def _artifact_descriptor(path: Path) -> dict[str, object]:
    return {
        "path": _relative_to_repo(path),
        "sha256": _sha256_path(path),
        "size_bytes": path.stat().st_size,
    }


def _write_defect_results_csv(path: Path, results: Sequence[Mapping[str, object]]) -> None:
    rows = []
    for result in results:
        rows.append(
            {
                "defect_id": result["defect_id"],
                "defect_name": result["defect_name"],
                "status": result["status"],
                "expected_result": result["expected_result"],
                "expected_guard": result["expected_guard"],
                "detected_by": ";".join(result.get("detected_by", [])),
                "secondary_ic_applicable": bool(
                    reg.GUARD_MAP[result["defect_name"]]["SECONDARY_IC_APPLICABLE"]
                ),
                "secondary_ic_computed": result["secondary_ic_computed"],
                "containment_passed": result["containment_passed"],
                "mechanism_invariants_passed": result["mechanism_invariants"]["passed"],
            }
        )
    pd.DataFrame(rows).to_csv(path, index=False)


def render_markdown(report: Mapping[str, object]) -> str:
    decision = report.get("decision", "INCONCLUSIVE")
    lines = [
        "# Stage 3 defect-injection report",
        "",
        f"- Decision: **{decision}**",
        f"- Source: `{reg.DATASET_PATH}`",
        f"- Source SHA256: `{reg.DATASET_SHA256}`",
        "- Primary estimand: binary detection by the frozen existing guard map.",
        "- Integrity and containment are evaluated before the PASS/FAIL decision.",
        "- The secondary IC is per-split, descriptive, non-gating, and is not a significance test.",
        "",
        "## Per-defect status",
        "",
        "| ID | Defect | Status | Expected | Detected by | Secondary IC |",
        "|---:|---|---|---|---|---|",
    ]
    for result in report.get("defects", []):
        lines.append(
            "| {defect_id} | {defect_name} | {status} | {expected_result} | {detected_by} | {secondary} |".format(
                defect_id=result["defect_id"],
                defect_name=result["defect_name"],
                status=result["status"],
                expected_result=result["expected_result"],
                detected_by=", ".join(result.get("detected_by", [])) or "none",
                secondary="computed" if result["secondary_ic_computed"] else "not computed",
            )
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "This report can establish only whether the five preregistered synthetic constructions were detected by the preregistered existing guards. It does not establish absence of all leakage, universal pipeline safety, predictive edge, alpha, investment value, or production readiness. Research support only; not investment advice.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_report(matrix: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": "1.0.0",
        "experiment": SLUG,
        "stage": "Stage 3 — defect-injection matrix",
        "registration": reg.REGISTRATION_DOC,
        "result_root": reg.RESULT_ROOT,
        "source_artifacts": [
            {
                "path": reg.DATASET_PATH,
                "sha256": reg.DATASET_SHA256,
                "size_bytes": DATASET_PATH.stat().st_size,
                "role": "frozen modeling dataset; read-only",
            }
        ],
        "registered_configuration": registered_configuration(),
        "registered_configuration_sha256": registered_configuration_digest(),
        "expected_first_draw_outcome": reg.EXPECTED_FIRST_DRAW_OUTCOME,
        "expected_first_draw_outcome_is_prospective": True,
        "defects": list(matrix["defects"]),
        "decision": matrix["decision"],
        "integrity": matrix["integrity"],
        "claim_boundary": list(reg.CLAIM_BOUNDARY),
        "git": _git_metadata(),
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
        },
        "governed_scientific_draw_performed": True,
        "guard_repaired": False,
    }


def _integrity_result(
    *,
    before_protected: Mapping[str, object],
    after_protected: Mapping[str, object],
    before_modules: Mapping[str, object],
    after_modules: Mapping[str, object],
    results: Sequence[Mapping[str, object]],
    source_hashes: Sequence[str],
    clean_fingerprints: Sequence[str],
) -> dict[str, object]:
    conditions = {name: True for name in reg.INTEGRITY_CONDITION_IDENTIFIERS}
    conditions["frozen_source_dataset_path_and_sha_match"] = (
        all(value == reg.DATASET_SHA256 for value in source_hashes)
        and _sha256_path(DATASET_PATH) == reg.DATASET_SHA256
    )
    expected_modules = dict(reg.SOURCE_MODULE_HASHES)
    expected_modules[reg.CELL_PROVENANCE_SOURCE] = reg.CELL_PROVENANCE_SHA256
    conditions["registered_stage3_module_hashes_match"] = all(
        after_modules.get(relative) == expected
        for relative, expected in expected_modules.items()
    )
    conditions["exactly_five_registered_defect_ids"] = [
        result.get("defect_id") for result in results
    ] == list(reg.ALL_STAGE3_IDS)
    names = [result.get("defect_name") for result in results]
    conditions["no_duplicate_defect_ids_or_defect_names"] = (
        len(names) == len(set(names)) == reg.DEFECT_FAMILY_SIZE
    )
    conditions["correct_seed_schedule"] = all(
        injection_seed(int(reg.DEFECT_IDS[name])) == int(reg.STAGE3_SEED_VALUES[int(reg.DEFECT_IDS[name])])
        for name in reg.DEFECT_FAMILY
    )
    conditions["no_forbidden_id_overlap"] = not (
        set(reg.ALL_STAGE3_IDS)
        & (
            set(reg.STAGE_1_IDS)
            | set(reg.STAGE_1B_IDS)
            | set(reg.RESERVED_IDS)
            | set(reg.STAGE_2_IDS)
        )
    )
    conditions["writes_confined_to_stage3_result_namespace"] = True
    conditions["stage1_stage1b_stage2_result_roots_untouched"] = (
        before_protected == after_protected
    )
    conditions["no_trusted_data_or_config_mutation"] = before_protected == after_protected
    conditions["no_source_module_mutation"] = before_modules == after_modules
    conditions["injection_containment_restored_after_each_defect"] = all(
        result.get("containment_passed") is True
        and result.get("clean_comparator", {}).get("cleanup_proven") is True
        and result.get("injected_guard_evaluation", {}).get("cleanup_proven") is True
        for result in results
    )
    conditions["clean_comparator_byte_and_logical_identity"] = (
        len(clean_fingerprints) == len(set(clean_fingerprints)) == 1
        and all(not result.get("clean_comparator", {}).get("detection_signals") for result in results)
    )
    conditions["expected_guard_mapping_evaluated_exactly_once"] = all(
        result.get("clean_comparator", {}).get("invocation_accounting_passed") is True
        and result.get("injected_guard_evaluation", {}).get("invocation_accounting_passed") is True
        for result in results
    )
    conditions["no_defect_silently_omitted"] = names == list(reg.DEFECT_FAMILY)
    conditions["secondary_ic_only_on_undetected_defects"] = all(
        result.get("secondary_ic") is None
        or result.get("status") == reg.NOT_DETECTED
        for result in results
    )
    conditions["no_invalid_evaluation_converted_to_non_detection"] = all(
        not (
            result.get("status") == reg.NOT_DETECTED
            and (
                result.get("failure_reasons")
                or not result.get("containment_passed")
            )
        )
        for result in results
    )
    conditions["deterministic_replay_contract"] = True
    failures = [name for name, passed in conditions.items() if not passed]
    return {
        "passed": not failures,
        "conditions": conditions,
        "failures": failures,
    }


def execute_registered_matrix(*, progress: bool = False) -> dict[str, object]:
    """Execute the matrix in private namespaces without persisting results."""
    _assert_registered_source_hashes()
    before_protected = protected_workspace_digest()
    before_modules = _module_digest()
    results: list[dict[str, object]] = []
    source_hashes: list[str] = []
    clean_fingerprints: list[str] = []
    for defect_name in reg.DEFECT_FAMILY:
        source_before = _sha256_path(DATASET_PATH)
        source_hashes.append(source_before)
        clean = load_clean_frame()
        clean_fingerprints.append(_frame_fingerprint(clean))
        injected = inject_defect(clean, defect_name)
        if progress:
            print(f"[stage3] evaluating {reg.DEFECT_IDS[defect_name]} {defect_name}")
        result = evaluate_defect(defect_name, clean, injected)
        source_after = _sha256_path(DATASET_PATH)
        source_hashes.append(source_after)
        result["source_sha256_before"] = source_before
        result["source_sha256_after"] = source_after
        if source_before != reg.DATASET_SHA256 or source_after != reg.DATASET_SHA256:
            result["status"] = reg.INCONCLUSIVE
            result.setdefault("failure_reasons", []).append("source SHA changed")
        protected_after = protected_workspace_digest()
        if protected_after != before_protected:
            result["status"] = reg.INCONCLUSIVE
            result.setdefault("failure_reasons", []).append("protected workspace changed")
        results.append(result)
    after_protected = protected_workspace_digest()
    after_modules = _module_digest()
    integrity = _integrity_result(
        before_protected=before_protected,
        after_protected=after_protected,
        before_modules=before_modules,
        after_modules=after_modules,
        results=results,
        source_hashes=source_hashes,
        clean_fingerprints=clean_fingerprints,
    )
    decision = decide(results, integrity_passed=bool(integrity["passed"]))
    return {
        "defects": results,
        "decision": decision,
        "integrity": integrity,
        "result_root_created": RESULT_ROOT.exists(),
        "scientific_draw_performed": True,
    }


def _promote_scientific_artifacts(root: Path, staging: Path) -> None:
    if staging.parent.name != STAGING_DIRNAME or staging.parent.parent != root:
        raise Stage3IntegrityError("unsafe Stage 3 staging path")
    for name in SCIENTIFIC_EMITTED_FILENAMES:
        source = staging / name
        if source.is_symlink() or not source.is_file():
            raise Stage3IntegrityError(f"missing staged Stage 3 output: {name}")
        os.replace(source, root / name)
    staging.rmdir()
    staging.parent.rmdir()


def _write_final_manifest(
    root: Path,
    report: Mapping[str, object],
    marker_path: Path,
    marker_payload: Mapping[str, object],
    integrity: Mapping[str, object],
) -> Path:
    artifacts = [_artifact_descriptor(root / name) for name in SCIENTIFIC_EMITTED_FILENAMES]
    payload = {
        "schema_version": 1,
        "experiment": SLUG,
        "stage": "Stage 3 — defect-injection matrix",
        "registration": reg.REGISTRATION_DOC,
        "result_root": reg.RESULT_ROOT,
        "completion_status": "complete",
        "completion_authority": MANIFEST_FILENAME,
        "integrity_passed": bool(integrity["passed"]),
        "registered_configuration": registered_configuration(),
        "registered_configuration_sha256": registered_configuration_digest(),
        "implementation_sha256": implementation_hash(),
        "registration_module_sha256": registration_hash(),
        "source_artifacts": report["source_artifacts"],
        "artifacts": artifacts,
        "scientific_emitted_files": list(SCIENTIFIC_EMITTED_FILENAMES),
        "decision": report["decision"],
        "expected_first_draw_outcome": reg.EXPECTED_FIRST_DRAW_OUTCOME,
        "expected_first_draw_outcome_is_prospective": True,
        "guard_repaired": False,
        "operational_attempt_provenance": {
            "path": _relative_to_repo(marker_path),
            "sha256": _sha256_path(marker_path),
            "classification": "operational provenance; not a scientific emitted artifact",
        },
        "attempt_provenance": marker_payload,
    }
    path = root / MANIFEST_FILENAME
    _atomic_json_write(path, payload)
    return path


def _run_attempt(
    root: Path,
    *,
    marker_path: Path,
    marker_payload: Mapping[str, object],
    attempt_number: int,
    progress: bool,
) -> Path:
    started = time.perf_counter()
    matrix = execute_registered_matrix(progress=progress)
    report = build_report(matrix)
    markdown = render_markdown(report)
    validate_claim_safety_text(markdown)
    staging = root / STAGING_DIRNAME / f"attempt-{attempt_number}"
    staging.mkdir(parents=True, exist_ok=False)
    report_path = staging / REPORT_JSON_FILENAME
    report_path.write_text(json.dumps(_jsonable(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (staging / REPORT_MD_FILENAME).write_text(markdown, encoding="utf-8")
    _write_defect_results_csv(staging / RESULTS_CSV_FILENAME, matrix["defects"])
    audit = _audit_output_surface(staging, SCIENTIFIC_EMITTED_FILENAMES)
    if not audit["passed"]:
        raise Stage3IntegrityError("staged Stage 3 output confinement failed")
    _promote_scientific_artifacts(root, staging)
    final_audit = _audit_output_surface(root, SCIENTIFIC_EMITTED_FILENAMES)
    if not final_audit["passed"]:
        raise Stage3IntegrityError("promoted Stage 3 output confinement failed")
    completed_marker = _set_attempt_status(marker_path, marker_payload, "complete")
    report["elapsed_seconds"] = round(time.perf_counter() - started, 6)
    report_path = root / REPORT_JSON_FILENAME
    report_path.write_text(json.dumps(_jsonable(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_final_manifest(root, report, marker_path, completed_marker, matrix["integrity"])
    completed_audit = _audit_output_surface(
        root, [*SCIENTIFIC_EMITTED_FILENAMES, MANIFEST_FILENAME]
    )
    if not completed_audit["passed"]:
        raise Stage3IntegrityError("completed Stage 3 output confinement failed")
    return report_path


def run(*, progress: bool = True, repeat_after_crash: bool = False) -> Path:
    """Execute the explicit governed Stage 3 run in the registered namespace."""
    if RESULT_ROOT.resolve() != REGISTERED_RESULT_ROOT:
        raise Stage3IntegrityError(
            "governed Stage 3 execution cannot be redirected away from the registered result namespace"
        )
    _assert_registered_source_hashes()
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
    except BaseException:
        with contextlib.suppress(Exception):
            _set_attempt_status(marker_path, marker_payload, "incomplete")
        raise


def replay_check() -> dict[str, object]:
    """Run the deterministic private matrix twice; persist no result."""
    first = execute_registered_matrix(progress=False)
    second = execute_registered_matrix(progress=False)
    first_payload = _canonical_json(first)
    second_payload = _canonical_json(second)
    return {
        "identical": first_payload == second_payload,
        "first_digest": _sha256_bytes(first_payload),
        "second_digest": _sha256_bytes(second_payload),
        "result_root_created": RESULT_ROOT.exists(),
        "note": "deterministic implementation replay; not a governed result",
    }


def registered_plan() -> dict[str, object]:
    """Describe the frozen run without reading the dataset or creating output."""
    return {
        "executed": False,
        "experiment": SLUG,
        "result_root": reg.RESULT_ROOT,
        "defect_family": list(reg.DEFECT_FAMILY),
        "expected_detection": dict(reg.EXPECTED_DETECTION),
        "expected_first_draw_outcome": reg.EXPECTED_FIRST_DRAW_OUTCOME,
        "explicit_run_flag": "--run",
        "replay_flag": "--replay-check",
        "repeat_after_crash_flag": "--repeat-after-crash",
        "scientific_draw_performed": False,
        "result_root_created": RESULT_ROOT.exists(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="execute the governed Stage 3 run")
    mode.add_argument(
        "--replay-check",
        action="store_true",
        help="replay the private deterministic matrix without writing a result",
    )
    mode.add_argument(
        "--repeat-after-crash",
        action="store_true",
        help="recover one incomplete Stage 3 attempt with identical settings",
    )
    args = parser.parse_args()
    if args.replay_check:
        result = replay_check()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["identical"] and not result["result_root_created"] else 1
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
