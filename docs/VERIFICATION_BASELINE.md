# Verification Baseline

Observed 2026-07-18 at git `18514ac51f7e7912caf5a04b3b6526e77ce53f98` for the GOV-02 documentation-only governance truth-sync. The working tree was clean when the checks began.

| Check | Observed result |
|---|---|
| `PYTHONPATH=. python -m pytest tests/` | PASS — 356 collected, 356 passed |
| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 99 collected, 99 passed (27 deprecation warnings) |
| `make data-validate` | PASS — VALID; 403 modeling rows, 40 features, 321 target rows, 82 inference-only rows, benchmark available |
| `make claims-lint` | PASS — Model Confidence Contract v1.8.0 satisfied |

The root and backend counts are a dated observation, not a permanent constant. Re-run the commands after relevant changes and replace this baseline only in a task that owns verification truth.

Claims lint does not scan these operating Markdown files. Its green result confirms the registered Model Confidence Contract surfaces, not the accuracy of this documentation.

## Frontend route inventory

The R3-GOV-01 spot-check found 23 `frontend/src/pages/*Page.jsx` files. `frontend/src/App.jsx` contains 27 `<Route>` declarations: 22 render page components and 5 redirect via `<Navigate>` (`/`, `/search`, `/ai-search`, `/reports`, and `*`).
