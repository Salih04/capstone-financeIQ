"""Filesystem path helpers for local runs and Docker.

Backend code lives under ``backend/app`` locally, but under ``/app/app`` in the
container. Resolve the project data root by looking for ``data/`` instead of
assuming a fixed parent depth.
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
