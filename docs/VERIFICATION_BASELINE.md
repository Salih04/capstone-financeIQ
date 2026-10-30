# Verification Baseline

Current CI count authority — updated 2026-10-30 on the verified merged `main` commit `84f6242431e87d7031f85e0aae2f5726a972cafc` (PR #58). The 2026-10-08 machine-of-record baseline is preserved **byte-for-byte** at [its dated archive](archive/verification/VERIFICATION_BASELINE_2026-10-08.md); this refresh does not rewrite that historical observation.

This table supplies the single approved collected-count row for each root/backend command in `.github/scripts/ci_test_gate.py`. **Rows have different evidence contexts:** root's complete 1456-pass evidence is the historical 2026-10-08 native macOS run (not repeated on the merged commit); backend's 916-pass evidence is the 2026-10-30 GitHub-hosted Linux run with `FIQ_TEST_POSTGRES_URL` pointing at disposable PostgreSQL. Do not misrepresent the root's 15 environment-qualified Linux deselections as passes.

| Check | Observed result |
|---|---|
| `PYTHONPATH=. python -m pytest tests/` | PASS — 1456 collected, 1456 passed (2026-10-08 native macOS evidence; historical, not a 2026-10-30 full-root execution) |
| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 916 collected, 916 passed (2026-10-30 hosted Linux with disposable PostgreSQL; 346 warnings) |
| `make data-validate` | PASS — VALID; 403 modeling rows, 40 features, 321 target rows, 82 inference-only rows, benchmark available (403/82 are carried from the 2026-10-08 record; 2026-10-30 validate-only run confirmed VALID, features=40, target_rows=321, benchmark=yes; tracked data files unchanged) |
| `make claims-lint` | PASS — Model Confidence Contract v1.10.0 satisfied (2026-10-30 hosted) |
| `make docs-lint` | PASS — links, cited paths, and active baseline assertions (2026-10-30 hosted) |

## Verified 2026-10-30 hosted results

Source: [GitHub Actions main push run 41049675638](https://github.com/Salih04/capstone-financeIQ/actions/runs/41049675638) at `84f62424`, successful on 2026-10-30 11:51:55 UTC. The same merge's [secret-scan run 41049675634](https://github.com/Salih04/capstone-financeIQ/actions/runs/41049675634) succeeded.

| Surface | Collected | Executed | Passed | Skipped | Deselected | Gate |
|---|---:|---:|---:|---:|---:|---|
| Root portable Linux | 1456 | 1441 | 1441 | 0 | 15 governed IDs | PASS |
| Backend (SQLite + disposable PostgreSQL) | 916 | 916 | 916 | 0 | 0 | PASS |
| PIT synthetic consumer | 16 | 16 | 16 | 0 | 0 | PASS |
| Research-core synthetic | 21 | 21 | 21 | 0 | 0 | PASS |

Frontend production build, data validation, claims lint, docs lint, docs-lint self-test, test-gate summary and secret scan also passed. No independent full native root re-run or production deployment was performed. The root portable 15 deselections remain governed by `.github/ci-deselect.txt`, and are **not** silent skips or waived work. CI rejects skips, XFAIL, XPASS, unknown deselections, missing ledgers and missing reports. A successful test run verifies software execution only, not scientific validity.

## Why backend collection increased: 579 to 916 (+337)

The 579-pass number belongs to the 2026-10-08 clean macOS snapshot `83a9d1084a203d33f89598ebbabbe8cbbfc0fb9e`. The 916-pass number is the 2026-10-30 merged Linux CI snapshot `84f6242431e87d7031f85e0aae2f5726a972cafc`. Comparing those commits shows **seven added backend test modules**:

- `backend/tests/test_auth_hardening.py`
- `backend/tests/test_heatmap_missingness.py`
- `backend/tests/test_missing_value_semantics.py`
- `backend/tests/test_postgres_integrity.py`
- `backend/tests/test_security_parallel.py`
- `backend/tests/test_security_remediation.py`
- `backend/tests/test_shared_record_authz.py`

Five existing test modules changed: `test_config.py`, `test_forecasting_api_contract.py`, `test_forecasting_partial_target.py`, `test_private_mode.py`, and `test_supabase_jwks.py`. `backend/tests/conftest.py` also changed to a disposable `TemporaryDirectory` SQLite fixture. The 2026-10-30 workflow enables `FIQ_TEST_POSTGRES_URL` for PostgreSQL-specific synthetic tests, and some new tests are parametrized.

**Attribution boundary:** +337 is the observed *net collected-count difference between two dated environments and revisions*, not a measured sum of test contributions from individual files or commits. Per-file pytest collection was not captured for both revisions under identical conditions; do not infer per-file increments from source line or function counts. The 2026-10-30 count is approved for the **hosted backend gate in its declared environment**, not asserted as a 916-test native/macOS baseline.

Between those SHAs, the comparison shows no modifications under `data/` or `experiments/results/`. This verification-truth update changes no source data, research results, tests, test exclusions, thresholds or workflow execution policy.

## Carried historical machine-of-record scope

The R3-GOV-01 spot-check found 23 `frontend/src/pages/*Page.jsx` files. `frontend/src/App.jsx` contains 27 `<Route>` declarations: 22 render page components and 5 redirect. This is a dated historical inventory, not a new browser or route acceptance test.

The historical archive preserves the previous package versions, native suite run details, data-quality counts, 15 Linux exception rationale, coverage limitations, frozen-artifact reproducibility restrictions and old snapshot provenance. Those dated observations must not be silently substituted for new measurements. When a fresh full-root native gate or another counted suite is run, record its exact command, environment and commit separately.

Research support only; not investment advice. No investment edge or scientific confirmation is established by these checks.
