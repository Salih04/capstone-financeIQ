"""Read-only passthrough for the committed R2-REGIME-01 context report."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
REPORT_PATH = REPO_ROOT / "experiments" / "results_regime" / "regime_context_report.json"


class RegimeContextReportMissing(RuntimeError):
    """Raised when the deterministic regime-context workflow has not run."""


@lru_cache(maxsize=1)
def payload() -> dict[str, Any]:
    """Return the committed report without recomputing macro or model statistics."""
    try:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RegimeContextReportMissing(
            "Regime context report unavailable. Run `make research-regime`."
        ) from exc
    if report.get("task") != "R2-REGIME-01":
        raise RegimeContextReportMissing("Regime context report has an unexpected task identifier.")
    return report
