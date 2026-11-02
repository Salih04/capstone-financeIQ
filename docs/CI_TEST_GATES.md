# CI Test Gates

Dated 2026-10-29. Lane CI-SYNTHETIC-GATES, written for the A19 and A22 test-gating audit items as the owner relayed them. Those audit items are not recorded in this repository, so this record states what CI checks rather than claiming the audit is closed.

This document covers which tests GitHub Actions collects, runs, skips and deselects, and how every count is compared with an approved record. Counts for the root and backend suites live only in the dated [verification baseline](VERIFICATION_BASELINE.md). This document never copies those counts, and the gate never edits the baseline.

Passing CI shows that the software runs. It is not model validation and says nothing about predictive validity. Research support, not investment advice.

## What CI collected before this change

Evidence: GitHub Actions run `40335043386` on `main` at `efe3ed32` (2026-10-26).

| Surface | Observed before this change |
|---|---|
| Root suite (`tests/`) | Collect-only matched the baseline's collected count. Every id in `.github/ci-deselect.txt` resolved and was deselected. All remaining tests passed, with zero skips. |
| Backend suite (`backend/tests`) | Matched the baseline's collected and passed counts, with zero skips. |
| `experiments/pit/test_kernel_snapshot.py` | **Not collected.** The root gate collects only `tests/`. `jsonschema` is also missing from `requirements-root.txt`. |
| `experiments/research_core/tests/test_core.py` | **Not collected**, for the same reason. |
| Frontend (`frontend/`) | **No job.** No install, build or e2e step existed. |
| Missing vendor workbooks | `tests/test_corrected_yearly_ingestion.py` skips its whole module when the corrected-yearly XLSX files are absent. The files are tracked, so CI ran it and skipped nothing. Nothing checked the skip count, though, so if the workbooks went missing the module would skip silently and CI would still go green. Other modules skip the same way when a generated artifact is missing, for example `tests/test_excess_basis.py`. |

## Gates

The workflow is `.github/workflows/verify.yml`. The expected counts and the list of gates CI does not run are in `.github/ci-test-gates.json`. The checker is `.github/scripts/ci_test_gate.py`, which is standard library only, and its self-test is `.github/scripts/selftest_ci_test_gate.py`. The pytest gates also load `.github/scripts/ci_pytest_ledger.py`, a passive pytest plugin (`-p ci_pytest_ledger`, with `.github/scripts` on `PYTHONPATH`). It records every collected, deselected and reported node id and each test's outcome, including XFAIL and XPASS.

| Job | Gate | Expected collected count comes from |
|---|---|---|
| `verify` | Root portable suite, environment-qualified ids deselected | Baseline row `PYTHONPATH=. python -m pytest tests/` |
| `verify` | Backend suite | Baseline row `PYTHONPATH=backend python -m pytest backend/tests` |
| `synthetic-boundary` | PIT synthetic consumer (`experiments.pit.test_kernel_snapshot`) | Approved 16, from [the consumer status record](../experiments/pit/KERNEL_CONSUMER_STATUS.md) and PR #52 (`f7b1e4f9`) |
| `synthetic-boundary` | Research-core synthetic suite (`experiments/research_core/tests`) | Approved 21, from the PR #53 description (`4b029ef4`) |
| `frontend-build` | `npm ci` then `npm run build` from the committed lockfile | Build success, not a test count |
| `test-gate-summary` | Re-checks every counts file and the result of every job | — |

Each gate records collected, executed, passed, skipped and deselected counts in a JSON file. A pytest gate builds that file from the ledger and checks the ledger test by test against the JUnit report from the same run. JUnit alone is not enough: pytest writes a non-strict XPASS as a plain pass and records no deselection at all. A run checked only against JUnit could therefore collect 580 tests, deselect one outside the governed list, pass 579, and still match a 579-test baseline. Those files are kept as the `test-gate-counts-*` artifacts. The checker writes one table per job to the step summary.

### Comparison rules (fail closed)

A gate **fails** when any of these holds:

- a test fails or errors, or is an expected failure or unexpected success (XFAIL or XPASS, strict or not);
- any test is skipped, because a skip is not a pass;
- a pytest gate has no ledger, or its JUnit report or ledger is missing, unparseable, of the wrong schema, internally inconsistent, or disagrees with the other about which tests ran or passed;
- the counts file is unreadable, names another suite or runner, or holds a count that is not a non-negative integer;
- the set of deselected ids differs from `.github/ci-deselect.txt`, which is empty for every suite except the root portable suite. A deselection by `--deselect`, `-k`, `-m` or a conftest hook outside the list fails, even when the total count still matches. A listed id that is no longer deselected also fails;
- a collected test is removed from the run without a deselection record, or a selected test never reports an outcome;
- pytest exits non-zero or reports a collection error;
- for the root suite, the set of ids the run collected differs from the separate collect-only step;
- a collected test neither ran, nor skipped, nor was deselected;
- the collected count is below the approved count, which means tests were removed or silently reverted;
- the baseline row is missing, duplicated, or is not a full pass (collected equal to passed);
- a counts file is missing (the gate did not run), or a needed job did not succeed.

A collected count **above** the approved count passes with a warning annotation. More tests do not weaken the gate. The dated baseline is not rewritten automatically: only a task that owns verification truth refreshes it.

### Synthetic-only boundary

The `synthetic-boundary` job uses a non-cone sparse checkout. Only the paths in `synthetic_workspace` in `.github/ci-test-gates.json` are materialized:

- the CI files
- the baseline document
- the two synthetic suites and their modules
- the copied Kernel fixtures
- the two requirements files

For sparse checkouts, `actions/checkout` fetches with a `blob:none` filter. This was checked in the action's source on 2026-10-29, not in a run log. So `data/`, experiment results and the vendor workbooks are not on the runner to be opened or recreated. A workspace check runs before and after the tests and fails on:

- any file outside that list;
- any directory outside it that is not an ancestor of an allowed path, even an empty one;
- every symlink anywhere, `.git` included, since the repository tracks none and a link inside an allowed directory could reach a forbidden path;
- anything that is not a regular file.

Symlinks are never followed, and an unreadable directory fails the check. The same check catches a test that writes into the workspace.

The environment is the pinned `requirements-root.txt` plus `experiments/pit/requirements-synthetic.txt` (`jsonschema`). The suites run through the same `unittest` loader as their documented commands. The `frontend-build` job checks out only `frontend/` and writes the bundle outside the workspace.

## Not run in CI, and never reported as passed

| Gate | Why not | Where it runs |
|---|---|---|
| Native full root suite, including every deselected id | Byte-identity and inode-recycling checks are tied to the machine of record ([baseline](VERIFICATION_BASELINE.md)) | Machine of record, before any baseline refresh |
| Frontend e2e (`npm run e2e`, Playwright) | Needs browser binaries, a backend and a Supabase session | Local runbook only |
| Experiment and outcome pipelines (`make research`, `make full-research`, studies) | They read or regenerate protected outcomes | Never in CI |

The summary job lists these under "Not run in CI — these are not passes."

## Changing an approved count

The approved synthetic counts change only together with the change to that suite, with its new count and source recorded in `.github/ci-test-gates.json`. Root and backend expectations change only through a dated baseline refresh. Adding a skip or a deselection to make a gate pass is a governance decision; the rules in `.github/ci-deselect.txt` apply.

## Local reproduction (synthetic only)

```bash
python -B .github/scripts/selftest_ci_test_gate.py -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python -B .github/scripts/ci_test_gate.py run-unittest --suite pit-synthetic --name experiments.pit.test_kernel_snapshot --out "$TMPDIR/test-gate/counts"
PYTHONDONTWRITEBYTECODE=1 python -B .github/scripts/ci_test_gate.py run-unittest --suite research-core-synthetic --discover experiments/research_core/tests --pattern 'test_*.py' --out "$TMPDIR/test-gate/counts"
python -B .github/scripts/ci_test_gate.py compare --suite pit-synthetic --suite research-core-synthetic --counts "$TMPDIR/test-gate/counts"
```

The self-test runs real pytest, through the ledger plugin, on invented suites in temporary directories. That covers non-strict and strict XPASS, XFAIL, 580 collected with one ungoverned deselection and 579 passed, `-k` and conftest deselection, silent drops and governed deselection. It also covers malformed reports and symlinked or special files in the workspace. It needs `pytest` installed and reads no repository data.

The PIT suite needs `jsonschema` and `pandas` installed.

## Limits

- GitHub-hosted runners keep network access. The boundary is enforced by what is checked out, not by network isolation.
- The hosted run of these new jobs has not been observed. This change was verified locally only: the self-test, both synthetic suites through the checker in a simulated sparse workspace, and the frontend build from a scratch copy of the committed tree.
- The ledger plugin and the stricter XPASS, deselection and symlink rules (2026-10-29, lane CI-ACCEPTANCE-BLOCKERS) were verified locally on synthetic suites only. The root and backend suites were not run under the plugin, and hosted CI is **NOT RUN** for this change.
- The root and backend gates still run on a full checkout that includes tracked raw data. This lane does not change that.
