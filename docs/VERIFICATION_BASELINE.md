# Verification Baseline

Observed 2026-10-08 on the clean code snapshot at git `83a9d1084a203d33f89598ebbabbe8cbbfc0fb9e` for FIQ-04. The previous baseline was dated 2026-08-11 at `79fae27090ad327acf0a62dc25362d4edd7bff55`; 115 commits are in the history between that baseline and this verification target. The baseline records the clean source snapshot at the start of the refresh; the documentation update is committed separately.

| Check | Observed result |
|---|---|
| `PYTHONPATH=. python -m pytest tests/` | PASS — 1456 collected, 1456 passed |
| `PYTHONPATH=backend python -m pytest backend/tests` | PASS — 579 collected, 579 passed (27 deprecation warnings) |
| `make data-validate` | PASS — VALID; 403 modeling rows, 40 features, 321 target rows, 82 inference-only rows, benchmark available |
| `make claims-lint` | PASS — Model Confidence Contract v1.10.0 satisfied |
| `make docs-lint` | PASS — local links, cited paths, and active baseline assertions agree |

`cd backend && python -m pytest tests/` was run as well and reports the same 579 collected, 579 passed (27 warnings), so both documented backend invocations agree.

The first sandbox-restricted root attempt reported 1455 passed and one failure when `test_directory_fifo_and_socket_members_fail` could not bind its local Unix-domain socket (`PermissionError: [Errno 1] Operation not permitted`). With approval, the same canonical command ran with host permissions and passed all 1456 tests; that native result is recorded above.

## Count changes since the previous baseline

The root suite increased by 375 collected and passed tests (1081 to 1456). Comparing the test trees between `79fae27090ad327acf0a62dc25362d4edd7bff55` and `83a9d1084a203d33f89598ebbabbe8cbbfc0fb9e` shows additions and expansions in the excess/provenance tests (`tests/test_artifact_registry.py`, `tests/test_contamination_lab.py`, `tests/test_excess_basis.py`; commits `33376c59`, `bb17695f`, `a3bffc89`, `56e1fcf2`, `492ba5b9`, `f6649cf6`, `70ccf4d1`); thesis calibration and negative-control stages (`tests/test_thesis_positive_control.py`, `tests/test_thesis_stage1b_*.py`, `tests/test_thesis_stage2_*.py`, `tests/test_thesis_stage3*.py`; commits `08615166`, `bd63d972`, `1740222c`, `cb3cf211`, `3b4ac101`, `dad66720`, `2394944f`, `a1d1e0ff`, `67f29dc1`, `113c64c8`, `3a2cad0f`, `ca3ecd1e`, `5550dc06`, `972f30ad`, `7df5e703`, `60b659eb`); and point-in-time guard and price tests (`tests/test_pit_guard.py`, `tests/test_pit_prices.py`; commit `079bb832`). Existing registration and significance tests were also changed in this interval. These repository changes explain the net root increase; individual collected-test increments are not assigned to commits because collection was not rerun at every intermediate revision.

The backend suite increased by 27 collected and passed tests (552 to 579). Commit `547cffb5` added `backend/tests/test_evidence_status.py`; the new file contributes exactly 27 collected tests in both current backend invocations. This accounts for the full backend delta.

The root and backend counts are a dated observation, not a permanent constant. Re-run the commands after relevant changes and replace this baseline only in a task that owns verification truth.

Claims lint does not scan these operating Markdown files. Its green result confirms the registered Model Confidence Contract surfaces, not the accuracy of this documentation.

## Environment of record

The counts above were produced in this exact interpreter and package set:

| Item | Observed value |
|---|---|
| Interpreter | CPython 3.12.3, conda-forge build (`main`, Apr 15 2024), Clang 16.0.6 |
| Path | `/opt/anaconda3/bin/python` |
| Platform | macOS 27.0.1 (build 26A434), arm64 |
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

Three installed packages are **newer than the `backend/requirements.txt` pins** in this local environment: `pydantic` 2.9.0 (pinned 2.7.1), `pydantic-settings` 2.5.0 (pinned 2.2.1), and `bcrypt` 4.2.0 (pinned 4.0.1). The CI workflow installs the pinned `requirements-root.txt` environment; this refresh records the local version delta and did not independently recreate that pinned environment.

`requirements-root.txt` is the installable form of this environment for the root pipeline and its verification runs. It includes `backend/requirements.txt` (the root suite imports `app.services`) and adds exact pins for `numpy`, `scikit-learn`, `scipy`, and `pytest`. `yfinance` is deliberately absent: it is lazily imported by the manual collection scripts only and is never exercised by either suite.

### Historical clean-clone check (2026-08-11)

The backend suite, `make data-validate`, and `make claims-lint` were re-run in a fresh `git clone` of this repository (no `backend/.env`, no untracked files) and produced identical results — 552 passed, VALID, MCC v1.10.0 satisfied. At that date, this supported that the CI job needed no secrets, no `.env`, and no Postgres service.

## Continuous integration

`.github/workflows/verify.yml` runs the five checks in the table above on every push to `main`, every pull request, and on manual dispatch, using Python 3.12 and `requirements-root.txt`. It never regenerates data (`make data-validate` is validate-only) and never runs `make research`, so no CI run can overwrite a committed experiment artifact.

First green run: GitHub Actions `31534431511` (ubuntu-latest, PR #10, 2026-08-11) — root 1066 passed / 15 deselected in 5:17, backend 552 passed, data `VALID`, claims lint v1.10.0, docs lint and its self-test passed. Run `31514453938` on the same branch is the failing first attempt kept for provenance; the 15 tests it surfaced are the deselect list below.

The workflow's **environment-portable** root gate now selects 1441 of the 1456 collected tests and deselects the 15 exact ids in `.github/ci-deselect.txt`. The workflow first checks that every listed id still resolves; the same collect-only check during this refresh found 1456 root tests and all 15 ids present. The 15 exceptions fall into two documented classes — byte-identity and 1e-12 statistic-parity checks over experiment artifacts generated on macOS arm64, and output-authority fixtures that assert on inode recycling, where APFS and ext4 differ. The cross-platform failure observations remain dated evidence from 2026-08-11; this refresh did not run the suite on Ubuntu. All 15 ids were included in the full native run, and the complete 1456-test suite passed on the machine of record. The workflow deselects these ids only; they are not skipped or removed.

Coverage is measured and reported but never enforced: both pytest steps add `pytest-cov` reporting flags, the two XML reports are archived as a build artifact, and both are now uploaded to Codecov as two separate reports — root coverage under flag `root`, backend coverage under flag `backend`. Each upload is a distinct `codecov/codecov-action@v5` step with `disable_search: true` and `fail_ci_if_error: false`, so a Codecov outage can never turn a genuinely green verification red. Codecov statuses are configured `informational: true` in the root `codecov.yml`, the Codecov PR comment is disabled, and Codecov is not a required status check.

The two flags measure different things and must not be read as one aggregate coverage number. Root Linux coverage reflects the 1441-test environment-portable gate described above, not the full suite; the full 1456 remains the native machine-of-record reproducibility gate. The 15 environment-qualified tests stay intact — they are deselected in CI only, pass in the native run, and must never be weakened, skipped, or rewritten in order to raise a coverage number. No test may be modified for coverage reasons. One consequence of the split is worth stating plainly: the root suite does execute some `backend/app/services` code (it imports `app.services`), but that execution is not represented in the backend report, because the root report measures only `scripts`, `experiments`, and `research_agent_training`. Neither flag is therefore a complete picture of how much of that package is exercised.

Coverage is software-execution evidence only. It is not model validation, and it carries no implication about predictive validity, alpha, profitability, causal validity, feature selection, or deployment readiness. The scientific conclusion is unchanged: no reliable predictive edge has been established.

No coverage threshold gates a run, and coverage output is gitignored — `tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact` reads `git status`, so any generated file left untracked in the working tree fails that guard. The same guard fails locally whenever verification work is left uncommitted; that is the guard behaving as designed, not a broken test.

The `make docs-lint` row was previously red at `18514ac5`: `docs/R3_SERV_01_FABLE5_REVIEW_HANDOFF.md:121` cited the then-current root count 356/356 inside a dated review-closure paragraph, and `docs/R3_UI_02_FABLE5_REVIEW_HANDOFF.md:104` likewise carried the stale backend count. Four exact-path entries were added to the lint's `TRUTH_DRIFT_EXCLUSIONS` as one frozen historical evidence class: those two files plus `docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md` and `docs/R3_PREREG_01_FABLE5_REVIEW_HANDOFF.md`, neither of which currently emits a truth-drift diagnostic — they are members of the same dated R3 review-evidence class, excluded for consistency rather than to silence a present failure. So only two of the four are currently load-bearing. The exclusions are exact paths, not a pattern: they suppress truth-drift checking for those four dated records only, every current-authority document remains fully linted, and the historical counts are preserved rather than rewritten — matching how every other dated verification record in the repository is treated.

## Frontend route inventory

The R3-GOV-01 spot-check found 23 `frontend/src/pages/*Page.jsx` files. `frontend/src/App.jsx` contains 27 `<Route>` declarations: 22 render page components and 5 redirect via `<Navigate>` (`/`, `/search`, `/ai-search`, `/reports`, and `*`). Re-counted 2026-08-11 and unchanged.

## R4-ROBUST-01 packet reproducibility note

The R4-ROBUST-01 implementation was introduced in commit `bbdd7eeeadf2583661bf39d0175f215564cfa4fe`
(`feat: add R4 robustness diagnostics`).

The implementation and generated contamination artifacts are present in repository history. The implementation contains a frozen approval gate referencing:

- `/tmp/r4-robust-01-canonical-implementation-packet-v3.md`
- `/tmp/r4-robust-01-discovery-report.md`
- `/tmp/r4-robust-01-final-prepacket-evidence.md`

Those external pre-packet evidence files are not present in the current machine filesystem and were not recoverable from repository history. Therefore `make research-contamination` cannot currently reproduce the R4 generation path because the implementation intentionally fails closed when approval packet hashes cannot be verified.

No implementation files, experiment artifacts, registry entries, or claim boundaries were modified during this investigation.

Status: historical artifact verified; fresh regeneration blocked by missing external approval evidence.
