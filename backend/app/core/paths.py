"""Filesystem path helpers for local runs and Docker.

Backend code lives under ``backend/app`` locally, but under ``/app/app`` in the
container. This module is the single repo-root resolution strategy for the whole
backend: every research/forecasting service resolves data paths through here so
local dev and Docker/Render behave identically.

Resolution order (first hit wins):
  1. ``RESEARCH_REPO_ROOT`` env var (explicit override — set to /app in Docker)
  2. parent dirs of this file that actually contain a ``data/`` directory
  3. ``/app`` (container default)
  4. current working directory

A directory only qualifies if it contains ``data/`` so we never resolve to a
parent that lacks the canonical dataset tree.
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_repo_root() -> Path:
    env_root = os.environ.get("RESEARCH_REPO_ROOT")
    here = Path(__file__).resolve()
    candidates = [
        Path(env_root) if env_root else None,
        here.parents[3] if len(here.parents) > 3 else None,
        here.parents[2] if len(here.parents) > 2 else None,
        Path("/app"),
        Path.cwd(),
    ]
    for candidate in candidates:
        if candidate and (candidate / "data").is_dir():
            return candidate
    return here.parents[3]


# Backwards/ergonomic alias used by services.
def get_repo_root() -> Path:
    return resolve_repo_root()


def get_trusted_clean_dir() -> Path:
    return resolve_repo_root() / "data" / "trusted_clean"


def get_public_modeling_dataset_path() -> Path:
    return get_trusted_clean_dir() / "modeling_dataset_public_2020_2025.csv"


def get_training_modeling_dataset_path() -> Path:
    return get_trusted_clean_dir() / "modeling_dataset_training_2020_2025.csv"


def get_base_modeling_dataset_path() -> Path:
    return get_trusted_clean_dir() / "modeling_dataset_2020_2025.csv"


def get_company_contexts_dir() -> Path:
    return get_trusted_clean_dir() / "company_contexts"


def required_runtime_files() -> dict[str, Path]:
    """Canonical files/dirs the research layer needs at runtime."""
    clean = get_trusted_clean_dir()
    return {
        "trusted_clean_dir": clean,
        "public_dataset": get_public_modeling_dataset_path(),
        "training_dataset": get_training_modeling_dataset_path(),
        "company_contexts_dir": get_company_contexts_dir(),
    }


def missing_required_runtime_files() -> list[str]:
    """Return names of required files/dirs that are absent. Empty list = healthy."""
    missing: list[str] = []
    for name, path in required_runtime_files().items():
        ok = path.is_dir() if name.endswith("_dir") else path.is_file()
        if not ok:
            missing.append(name)
    return missing


def assert_required_runtime_files() -> None:
    """Raise a clear error if canonical data is missing — never fail silently.

    Docker/Render misconfiguration (wrong build context, missing COPY data/)
    surfaces here as an explicit message instead of empty API responses.
    """
    missing = missing_required_runtime_files()
    if missing:
        root = resolve_repo_root()
        detail = ", ".join(
            f"{name}={path}" for name, path in required_runtime_files().items()
            if name in missing
        )
        raise FileNotFoundError(
            f"Required FinanceIQ runtime data missing (repo_root={root}): {detail}. "
            "Check the Docker build context copies data/ and that RESEARCH_REPO_ROOT "
            "points at the repo root."
        )
