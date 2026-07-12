"""Read-only access to generated per-column lineage passports."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.paths import resolve_repo_root


REPORT_PATH = resolve_repo_root() / "data" / "trusted_clean" / "feature_passports.json"
REQUIRED_FIELDS = {
    "name",
    "registry_role",
    "source_class",
    "transform_chain",
    "leakage_risk",
    "acceptance_status",
    "caveats",
    "evidence_files",
}


class FeaturePassportsMissing(RuntimeError):
    """Raised when generated lineage evidence is missing or malformed."""


@lru_cache(maxsize=2)
def _load_cached(path: str, mtime: float) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def payload() -> dict:
    """Return the generated artifact without recalculating or enriching it."""
    if not REPORT_PATH.is_file():
        raise FeaturePassportsMissing(
            f"Feature passports not found at {REPORT_PATH}. Run `make data-validate`."
        )
    artifact = _load_cached(str(REPORT_PATH), REPORT_PATH.stat().st_mtime)
    passports = artifact.get("passports")
    if not isinstance(passports, list) or not passports:
        raise FeaturePassportsMissing("Feature passports have an unsupported schema.")
    if any(set(passport) != REQUIRED_FIELDS for passport in passports):
        raise FeaturePassportsMissing("Feature passports contain a malformed record.")
    return artifact

