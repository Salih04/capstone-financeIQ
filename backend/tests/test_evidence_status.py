"""Responses built on the pre-audit T->T+1 design carry X-Evidence-Status."""

from __future__ import annotations

import re

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from app.core.evidence_status import (
    EVIDENCE_NOTE_HEADER,
    EVIDENCE_STATUS_HEADER,
    WITHDRAWN_PRE_PIT,
    evidence_status_for,
)
from app.main import app

# Reviewed routes that serve data, configuration, users or ingestion rather than
# results of the pre-audit design. Adding a route means classifying it here or
# in app/core/evidence_status.py.
NO_STATUS_ROUTES = {
    "/admin/audit-logs",
    "/admin/scoring-models",
    "/admin/scoring-models/{model_id}",
    "/admin/scoring-models/{model_id}/activate",
    "/admin/scoring-models/{model_id}/archive",
    "/admin/users",
    "/admin/users/{user_id}/role",
    "/analyst-verdicts",
    "/analyst-verdicts/aggregate",
    "/auth/login",
    "/auth/me",
    "/auth/register",
    "/companies",
    "/companies/{company_id}",
    "/companies/{company_id}/financials",
    "/companies/{company_id}/metrics",
    "/financials/import-csv",
    "/fundamentals/template",
    "/fundamentals/upload-csv",
    "/health",
    "/ingestion/dashboard",
    "/ingestion/import/csv",
    "/ingestion/issues",
    "/ingestion/jobs",
    "/ingestion/jobs/{job_id}",
    "/labeling/definitions",
    "/labeling/definitions/{label_id}",
    "/labeling/definitions/{label_id}/activate",
    "/labeling/definitions/{label_id}/preview",
    "/research/ai-status",
    "/research/data-quality",
    "/research/feature-passports",
    "/research/feature-registry",
    "/research/frozen-evidence",
    "/research/runtime-status",
    "/research/years",
    "/upload-data",
    "/users/me",
    "/users/me/profile",
}


def _concrete(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "x", path)


def test_every_route_is_classified():
    unclassified = sorted(
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
        and evidence_status_for(_concrete(route.path)) is None
        and route.path not in NO_STATUS_ROUTES
    )
    assert unclassified == []


def test_no_status_routes_are_not_marked_withdrawn():
    marked = sorted(p for p in NO_STATUS_ROUTES if evidence_status_for(_concrete(p)) is not None)
    assert marked == []


@pytest.mark.parametrize(
    "path",
    [
        "/predict",
        "/predict/heatmap",
        "/get-stocks",
        "/forecasting/run",
        "/forecasting/explain/AEFES",
        "/companies/7/score",
        "/scoring/compare",
        "/score-runs/12",
        "/reports/score-runs/12/export.pdf",
        "/validation/run",
        "/research/scores",
        "/research/significance/autopsy",
        "/research/skeptic/THYAO",
        "/research/company/THYAO/score",
        "/research/ask",
    ],
)
def test_pre_audit_paths_are_withdrawn(path):
    assert evidence_status_for(path) == WITHDRAWN_PRE_PIT


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/companies",
        "/companies/7/financials",
        "/research/data-quality",
        "/research/feature-passports",
        "/research/frozen-evidence",
        "/research/years",
        "/predictable",
        "/research/scores/extra",
    ],
)
def test_other_paths_carry_no_status(path):
    assert evidence_status_for(path) is None


def test_middleware_sets_headers_only_on_withdrawn_responses():
    client = TestClient(app)

    withdrawn = client.get("/forecasting/filters")
    assert withdrawn.headers.get(EVIDENCE_STATUS_HEADER) == WITHDRAWN_PRE_PIT
    assert "RESULTS.md" in withdrawn.headers.get(EVIDENCE_NOTE_HEADER, "")

    current = client.get("/health")
    assert current.status_code == 200
    assert EVIDENCE_STATUS_HEADER not in current.headers
