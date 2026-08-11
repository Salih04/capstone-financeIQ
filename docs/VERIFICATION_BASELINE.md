# Verification Baseline

Observed 2026-08-11 at git `79fae27090ad327acf0a62dc25362d4edd7bff55` for the CI-bootstrap truth refresh. The tracked tree was clean except for the changes this refresh introduces (`requirements-root.txt`, `.github/workflows/verify.yml`, one `scripts/lint_doc_links.py` exclusion). The previous baseline was dated 2026-07-18 at `18514ac5`; 51 commits landed between it and this observation, which is why the backend count below moved.

| Check | Observed result |
|---|---|
| `PYTHONPATH=. python -m pytest tests/` | PASS — 1081 collected, 1081 passed |
| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 552 collected, 552 passed (27 deprecation warnings) |
| `make data-validate` | PASS — VALID; 403 modeling rows, 40 features, 321 target rows, 82 inference-only rows, benchmark available |
| `make claims-lint` | PASS — Model Confidence Contract v1.10.0 satisfied |
| `make docs-lint` | PASS — local links, cited paths, and active baseline assertions agree |

`cd backend && python -m pytest tests/` was run as well and reports the same 552 passed, so both documented backend invocations agree.

The root and backend counts are a dated observation, not a permanent constant. Re-run the commands after relevant changes and replace this baseline only in a task that owns verification truth.

Claims lint does not scan these operating Markdown files. Its green result confirms the registered Model Confidence Contract surfaces, not the accuracy of this documentation.

## Environment of record

The counts above were produced in this exact interpreter and package set:

| Item | Observed value |
|---|---|
| Interpreter | CPython 3.12.3, conda-forge build (`main`, Apr 15 2024), Clang 16.0.6 |
| Path | `/opt/anaconda3/bin/python` |
| Platform | macOS 26.6, arm64 |
| `numpy` | 1.26.4 |
| `pandas` | 2.2.2 |
| `scipy` | 1.13.1 |
| `scikit-learn` | 1.5.1 |
| `pytest` | 8.3.3 |
| `fastapi` | 0.111.0 |
| `sqlalchemy` | 2.0.30 |
| `httpx` | 0.27.0 |
| `shap` | 0.51.0 |
| `reportlab` | 4.4.4 |

Three installed packages are **newer than the `backend/requirements.txt` pins** in this local environment: `pydantic` 2.9.0 (pinned 2.7.1), `pydantic-settings` 2.5.0 (pinned 2.2.1), and `bcrypt` 4.2.0 (pinned 4.0.1). The suites pass on both this environment and on the pinned set that CI installs; the delta is recorded rather than hidden, and any future failure that reproduces only in CI should be checked against it first.

`requirements-root.txt` is the installable form of this environment for the root pipeline and its verification runs. It includes `backend/requirements.txt` (the root suite imports `app.services`) and adds exact pins for `numpy`, `scikit-learn`, `scipy`, and `pytest`. `yfinance` is deliberately absent: it is lazily imported by the manual collection scripts only and is never exercised by either suite.

### Clean-clone check

The backend suite, `make data-validate`, and `make claims-lint` were re-run in a fresh `git clone` of this repository (no `backend/.env`, no untracked files) and produced identical results — 552 passed, VALID, MCC v1.10.0 satisfied. This is the evidence that the CI job needs no secrets, no `.env`, and no Postgres service.

## Continuous integration

`.github/workflows/verify.yml` runs the five checks in the table above on every push to `main`, every pull request, and on manual dispatch, using Python 3.12 and `requirements-root.txt`. It never regenerates data (`make data-validate` is validate-only) and never runs `make research`, so no CI run can overwrite a committed experiment artifact.

First green run: GitHub Actions `31534431511` (ubuntu-latest, PR #10, 2026-08-11) — root 1066 passed / 15 deselected in 5:17, backend 552 passed, data `VALID`, claims lint v1.10.0, docs lint and its self-test passed. Run `31514453938` on the same branch is the failing first attempt kept for provenance; the 15 tests it surfaced are the deselect list below.

CI runs the **environment-portable** part of the root suite: 1066 of 1081 tests. The 15 exceptions are listed with their reasons in `.github/ci-deselect.txt` and fall into two classes — byte-identity and 1e-12 statistic-parity checks over experiment artifacts generated on macOS arm64 (Linux x86_64 agrees to about eleven significant digits, which is exactly the environment-qualification the repository already documents), and output-authority fixtures that assert on inode recycling, where APFS and ext4 disagree. Those tests are deselected in CI only; they are not skipped, weakened, or removed, they must still pass on the machine of record, and a workflow step fails the build if any listed id stops resolving. The counts in the table above are the full-suite numbers from that machine.

Coverage is measured but not enforced: both pytest steps add `pytest-cov` reporting flags, the two XML reports are archived as a build artifact, and the Codecov upload step is present but commented out until a `CODECOV_TOKEN` secret exists. No coverage threshold gates a run, and coverage output is gitignored — `tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact` reads `git status`, so any generated file left untracked in the working tree fails that guard. The same guard fails locally whenever verification work is left uncommitted; that is the guard behaving as designed, not a broken test.

The `make docs-lint` row was previously red at `18514ac5`: `docs/R3_SERV_01_FABLE5_REVIEW_HANDOFF.md:121` cited the then-current root count 356/356 inside a dated review-closure paragraph. That file is now in the lint's `TRUTH_DRIFT_EXCLUSIONS` as dated review evidence, matching how every other dated verification record in the repository is treated — the historical count is preserved, not rewritten.

## Frontend route inventory

The R3-GOV-01 spot-check found 23 `frontend/src/pages/*Page.jsx` files. `frontend/src/App.jsx` contains 27 `<Route>` declarations: 22 render page components and 5 redirect via `<Navigate>` (`/`, `/search`, `/ai-search`, `/reports`, and `*`). Re-counted 2026-08-11 and unchanged.
