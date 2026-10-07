"""Evidence status of API responses after the 2026-10-04 publication-lag audit.

The audit (``docs/audit/PUBLICATION_LAG_AUDIT.md``) withdrew the reading of the
original T->T+1 walk-forward: year-T features were annual statements used
before they were public. Endpoints that still serve scores, rankings, forecasts
or evaluations built on that design stay available as a historical record, and
their responses carry ``X-Evidence-Status: withdrawn_pre_pit``. No backend
service reads the corrected point-in-time result; it lives in ``RESULTS.md`` and
``experiments/results_pit_v2/``.

Endpoints that describe data (quality, lineage, frozen-column evidence) or
manage users and ingestion carry no status. ``backend/tests/test_evidence_status.py``
requires every registered route to be classified, so a new endpoint cannot
silently skip this decision.
"""

from __future__ import annotations

import re
from typing import Optional

EVIDENCE_STATUS_HEADER = "X-Evidence-Status"
EVIDENCE_NOTE_HEADER = "X-Evidence-Note"
WITHDRAWN_PRE_PIT = "withdrawn_pre_pit"
WITHDRAWN_PRE_PIT_NOTE = (
    "Pre-audit T->T+1 design (statements used before publication); "
    "superseded by the point-in-time evaluation in RESULTS.md"
)

_WITHDRAWN_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        # Forecasting router (declared without a prefix).
        r"^/(train-model|get-stocks|get-parameters|get-portfolio-analysis|get-stock-detail|get-explanation)$",
        r"^/parameters/catalog$",
        r"^/predict(/.*)?$",
        r"^/forecasting(/.*)?$",
        # Legacy scoring, its validation lab and exports.
        r"^/companies/[^/]+/(score|sector-scores|transitions)$",
        r"^/scoring(/.*)?$",
        r"^/score-runs/[^/]+$",
        r"^/users/me/score-runs$",
        r"^/reports/score-runs/.+$",
        r"^/validation(/.*)?$",
        # Research and research-agent routers (both mounted under /research).
        r"^/research/(scores|company|validation|dashboard|profit-consistency|benchmark/status"
        r"|significance|significance/autopsy|regime-context|return-basis|calibration|courtroom)$",
        r"^/research/(skeptic|memo)/[^/]+$",
        r"^/research/(summary|model-diagnostics|experiments|benchmark|companies|ask)$",
        r"^/research/company/[^/]+(/score)?$",
    )
)


def evidence_status_for(path: str) -> Optional[str]:
    """Return the evidence status for a request path, or None when none applies."""
    if any(pattern.match(path) for pattern in _WITHDRAWN_PATTERNS):
        return WITHDRAWN_PRE_PIT
    return None
