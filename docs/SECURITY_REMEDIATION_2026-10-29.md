# Technical security remediation — 2026-10-29

**NO-GO for merge/deploy.** Local candidate for independent reconciliation, not
full security closure or scientific/rollout approval. Research support only;
not investment advice.

## Provenance and isolation

New branch `codex/fiq-security-remediation-20261029`, new worktree
`/Users/salihcamci/Documents/Codex/financeiq-security-remediation-20261029`,
starts exactly at `6f01f78433d4af2db8c137ccf765ad991bb85954`.
Fresh fetch: `origin/main=efe3ed32ca958074c01ee9488f1f768a9d812c61`.
Verified ancestry: main → `2abf4221` → `82398ab1` → `6f01f784`.
The previous remediation tree was clean initially and at final inspection,
still at that base. Independent-review files were not edited; its test module
was copied to task scratch, changing only the isolated PostgreSQL port.
No FIQ-09, paper, Kernel, frozen record or scientific result file was changed.

Read root/process AGENTS (paired process CLAUDE matches), current Charter,
adopted owner addendum, PRD/map/task navigation, security policy and prior
remediation/reconciliation. Charter/addendum match freshly fetched main;
the older context snapshot is not current adoption evidence. Required context
contains historical aggregates; no zero-prior-exposure claim is made.

Tests use a backend-only source archive plus copied candidate changes under
`/tmp/fiq-remediation-20261029`. An audit hook blocks data/result/private-vault
reads, old source/review checkouts and external sockets; only the task DB
socket at 127.0.0.1:56429 is allowed. The runner clears inherited settings,
disables provider calls and uses an empty research root. Synthetic settings
`.env` fixtures are allowed only under the task temporary directory.
PostgreSQL container `fiq-remediation-20261029-pg` is **16.14**, with existing
Alembic schema through `20260713_0007` applied only to this new disposable DB.
No new migration file or live migration. No existing app/review DB was used.
No raw vendor/protected-period/outcome artifact access, acquisition, estimator
fitting, experiment or analysis was performed.

## Fix–evidence matrix

Line numbers refer to candidate files.

| Finding | File:line and behavior | Synthetic evidence |
| --- | --- | --- |
| F4 HIGH: GET replaces shared rankings | `backend/app/services/forecasting_service.py:920`: parameter read returns existing/empty list. `:730`: forecast requires prior explicit admin training, otherwise 422; portfolio inherits this. | Empty/existing ranking snapshots; anonymous/investor/analyst/admin; alternate GET/POST/portfolio paths. |
| F4 alternate service writes | `backend/app/services/shared_data_access.py:8`: require caller and refresh current local active admin. Preset import `forecasting_service.py:186`, training `:641`, CV `:950` check before file/model/mutation work. `backend/app/routers/forecasting.py:146`: CV admin dependency; HTTP authorization errors preserved. | Direct absent/investor/analyst/inactive/revoked/deleted callers; real admin ranking replacement; synthetic admin CV; existing investor forecast/portfolio still persists its run without changing rankings. |
| F5: transition NaN/Infinity | `backend/app/services/transition_service.py:28`, `:55`: finite/null inputs, subtraction and percentage at persistence. | Two-period finite ±1e308 import and preexisting PostgreSQL NaN; SQL checks, not SQLite/JSON coercion. |
| F6: missing growth fill | `backend/app/services/forecasting_service.py:329`: finite numeric mask plus `pct_change(fill_method=None)` for both features. | `[10,null,20,40]` → first three growth values missing, then 1; unchanged source frame; all-null object columns. |
| F7: infinite denominator maps to zero | `backend/app/services/forecasting_service.py:305`: mask both ratio operands and nonfinite result. | ±Infinity/NaN/zero denominator, overflow, finite positive/zero controls; PostgreSQL infinite equity produces missing ROE. |
| Related derived persistence | `backend/app/services/sector_service.py:33`, `:67`, `:131`, `:139`: nonfinite inputs filtered; overflowed statistics/normalization null. `backend/app/services/ratio_service.py:46`: direct upsert finite/null. | Base `_stats([1e308,1e308])` returned infinite mean/std/median; `[-1e308,1e308]` raised OverflowError. New extreme and ordinary controls, SQL checks of computed metrics/transitions/benchmarks/normalized cells. |
| F8 | `frontend/package.json:27` and lock pin exactly **Vite 6.4.5**. | Current official advisory: affected 6.4.4, patched 6.4.5; npm audit/build/E2E. |
| F10 | `frontend/Dockerfile:1`: pinned Node 22/nginx digests; `:11`: lock then npm ci. `backend/Dockerfile:1`, `:5`: pinned Python 3.12 digest, complete runtime hash lock and binary-only install. Four open backend dependency ranges become tested exact pins. | Actual Linux arm64 image builds, pip check, six real HTTP smoke controls, nginx/API health, browser E2E against nginx image. |

New `backend/tests/test_security_remediation.py` covers 116 cases including
both DB engines. Existing preset missing-value test now supplies a synthetic
admin. No model-internal fitting/imputation was changed. Offline retrain/CV
scripts without an authenticated local admin now fail closed; no bypass was
added, and none were executed. CV's former missing-test-year training remains
in its explicit admin path. Its scientific validity is not assessed/approved.

`frontend/tests/e2e-forecasting.spec.js` replaces an obsolete signup/old-screen
flow with the current request/rendering contract. Courtroom layout checks use
synthetic responses. `frontend/tests/synthetic-session.js` aborts external
requests and fails unexpected API requests. Browser tests prove UI/contracts;
separate backend tests prove DB boundaries. No live Supabase/full-stack auth
acceptance is asserted.

## Executed checks and limitations

Logs/XML are under `/tmp/fiq-remediation-20261029/evidence/`, also copied with
the runner/source snapshot to the local artifact directory
`/Users/salihcamci/.codex/visualizations/2026/10/28/01a183fa-36da-7f60-9117-9fabd6bd7b07/financeiq-remediation-20261029/`. Counts overlap;
do not sum them into full-suite coverage.

| Log | Collected | Result | Deselected / skipped |
| --- | --- | --- | --- |
| `baseline.log`, unchanged base | 51 | 39 pass / 12 fail | 0 / 0 |
| `reconciliation-final.log`, same checks | 51 | 48 pass / 3 fail | 0 / 0 |
| `remediation-final.log`, new checks | 116 | 116 pass | 0 / 0 |
| `safe-regressions-final.log` | 204 | 192 pass | 12 / 0 |
| `pg-regressions.log` | 46 | 46 pass | 0 / 0 |
| `frontend-e2e.log`, local bundle | 3 | 3 pass | 0 / 0 |
| `docker-frontend-e2e.log`, nginx image | 3 | 3 pass | 0 / 0 |

The 192 selection is mixed: 39 security-parallel checks use disposable PG;
the other fixtures use isolated SQLite/config/unit checks. It is not a new
188-SQLite claim. Four added tests are the synthetic forecasting API contract.
The 12 deselections explicitly retain `not private and not a01`; these are not
skips. Full backend/root collection/execution was not run: some tests load
outcome/source artifacts even at collection. No 730→777 collection claim.

First new-test run: 103 pass / 3 fixture failures due to a reused globally
unique `(year,stock_code)` on PostgreSQL. Only synthetic ticker allocation was
corrected; rerun passed. Additional controls brought final coverage to 116.
Both logs remain. Deprecation/test-key warnings and existing large-bundle build
warning are visible; none were suppressed.

`npm ci --ignore-scripts`, `npm audit --json` (**0 known vulnerabilities**) and
`npm run build` pass. Docker uses full npm ci and pinned Node 22; local bundle
used Node 26.4.0. Both Docker builds and backend pip check pass. Runtime smoke:
health 200, investor parameter read 200, investor CV/train 403, admin empty-data
train 422, anonymous parameter read 401, ranking table unchanged.
Nginx `/api/health` also returns 200. Docker build context uses exact app code
and empty synthetic data/experiments/training placeholders: no data-bearing
production image/package/startup acceptance, amd64 test or bit-for-bit image
reproducibility claim. No Compose/data-loading startup script was run.

Full claims/docs lint was not executed: claims lint reads the outcome-bearing
confidence contract; docs lint traverses historical result-bearing documents.
Changed-file links, diff and scoped secret scanning are checked separately.
Hosted CI and independent review of the final SHA remain unrun. No live
account/session/configuration operation, push, PR, merge, deploy or data deletion.
Task containers are stopped without deleting synthetic databases or images.

### Exact safe commands

Run backend commands from `/tmp/fiq-remediation-20261029` with its task PG
running. The runner supplies clean env/PYTHONPATH, `-p fiq_guard`, `--confcutdir`,
no pytest cache, and per-run XML/log files. Never substitute a live database.
The runner/interpreter/evidence are temporary local files, not durable storage.

```bash
P=/tmp/fiq-security-env-20261028/bin/python
$P run_checks.py remediation-final backend/tests/test_security_remediation.py
$P run_checks.py reconciliation-final test_reconciliation.py -s
$P run_checks.py pg-regressions \
  backend/tests/test_security_parallel.py backend/tests/test_postgres_integrity.py
$P run_checks.py safe-regressions-final \
  backend/tests/test_security_parallel.py backend/tests/test_auth_hardening.py \
  backend/tests/test_supabase_jwks.py backend/tests/test_shared_record_authz.py \
  backend/tests/test_missing_value_semantics.py backend/tests/test_config.py \
  backend/tests/test_forecasting_api_contract.py -k 'not private and not a01'

# New worktree's frontend/; synthetic build only:
npm ci --ignore-scripts
npm audit --json
VITE_API_URL=/api VITE_SUPABASE_URL=http://127.0.0.1:56329 \
  VITE_SUPABASE_ANON_KEY=synthetic-test-public-key npm run build
E2E_BASE_URL=http://127.0.0.1:53029 npm run e2e -- --reporter=line --workers=1

# Worktree root; review any lock refresh diff:
uv pip compile backend/requirements.txt --python-version 3.12 \
  --python-platform linux --generate-hashes --only-binary :all: \
  --no-annotate -o backend/requirements.lock
```

E2E requires the synthetic-built bundle above, not production env settings.
Exact Docker commands/smoke scripts, source hashes, image ids and runtime freeze
are retained in the external evidence bundle.

## Independent mismatches and owner decisions

Nine technical failures from the 51-check baseline now pass. Three unchanged
failures remain for other-user `/get-stock-detail`, `/get-explanation` and
`/predict/history` reads. These remain red under an owner/admin safe-default
expectation. This is the remediation author's replay of unchanged independent
test logic, not a fresh independent-review verdict.

| Owner choice | Options | Safe interim / next action |
| --- | --- | --- |
| Forecast sharing | Owner+active-admin only; explicit run sharing with audience/consent; or globally shared forecasts with a defined user-context/history visibility rule. | Recommend owner+admin; do not implement before adoption. No new rollout exposing records. Current sharing remains unchanged and blocks privacy acceptance if private runs are intended. Decide existing/null-owner run handling. |
| Global private-mode DB reads | Global sensitive-read allowlist or documented per-route matrix. | Existing research/CSV gate does not prove global protection; `/companies` remains an observed scope mismatch. No silent policy change. |
| Real identity mapping / first admin | Proven issuer/subject bridge or separately reviewed durable registry/offline recovery. | Empty bindings fail closed. Prior runbook's proof, lifecycle and recovery decisions remain open; no live inventory/mapping/promotion/migration. |
| Session revocation | Bounded JWT exposure, local version/denylist or provider-session checks on selected actions; specify reset/re-enable/regrant semantics. | No global revocation claim. Owner chooses latency/recovery; no live session changes. |

Existing nonfinite rows were not scanned/backfilled/deleted. Service fixes do
not make arbitrary ORM/raw SQL reject NaN; PostgreSQL still accepts it, as the
negative control shows. Further schema constraints/cleanup need separate scope.
Software verification does not establish scientific validity or investment edge.
**NO-GO for merge/deploy** pending fresh independent reconciliation of the
immutable candidate SHA and unresolved owner/rollout decisions.

## Official sources checked 2026-10-29

- [Vite maintainer GHSA-8g5g-mxqh-grgj](https://github.com/vitejs/vite/security/advisories/GHSA-8g5g-mxqh-grgj): affected 6.4.4, patched 6.4.5; exposure requires a network-exposed dev server plus an otherwise denied sensitive file inside allowed directories. Static production exposure was not demonstrated.
- [Supabase sessions](https://supabase.com/docs/guides/auth/sessions): JWT expiry and session existence differ; no live session check was added.
- [Supabase changelog](https://supabase.com/changelog.md): inspected for relevant breaking changes; no provider feature or live configuration implemented.
