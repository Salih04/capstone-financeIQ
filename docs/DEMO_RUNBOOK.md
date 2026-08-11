# FinanceIQ glass-box demo runbook

FinanceIQ is an academic decision-support research terminal. Its evidence shows
no reliable predictive edge. The demo succeeds by making the pipeline,
provenance, uncertainty, and limitations inspectable. It is research support
only, not investment advice.

Use the answers in the
[claims guide §5](../FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md#5-unsafe-demo-claims-to-avoid)
and [§14](../FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md#14-how-to-answer-is-this-investment-advice)
during questions. Do not improvise stronger wording.

## Before the audience arrives

Start the backend and frontend using the repository's normal local or Docker
instructions. The frontend routes in this runbook require an approved Supabase
session; the read-only API checks remain open only when `PUBLIC_DEMO_MODE=true`.
Do not describe a private, unavailable, or fallback surface as live.

Use the origin that matches the running frontend: `http://127.0.0.1:5173` for
Vite or `http://127.0.0.1:3000` for Docker. Route paths below are the stable part.

From the repository root, run:

```bash
make demo-check
curl -fsS http://127.0.0.1:8000/research/runtime-status | python -m json.tool
make claims-lint
```

Proceed with the live path only when the smoke check passes and runtime status
reports non-empty public/training CSV coverage with no required files missing.
Keep [the claims guide §5](../FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md#5-unsafe-demo-claims-to-avoid)
open in a separate tab.

## Scripted path — about 10 minutes

### 1. Runtime proof — 0:45

Show the `make demo-check` terminal first. It checks the real `/health`,
`/research/runtime-status`, and `/forecasting/options` targets. Then show the raw
runtime-status JSON and point to the repository-relative dataset paths, row and
ticker counts, missing-file list, configured AI provider, and deterministic
fallback availability.

Say only that the backend is reading the checked CSV artifacts. If any check is
red, take the matching fallback branch below.

### 2. Frozen-evidence specimen archive — 1:15

Open `/data-quality` on the running frontend. Select a specimen stamped `FROZEN`
and show its per-ticker evidence. Explain that rejected frozen columns remain
visible as audit evidence and are excluded from the modeling feature path;
missing values stay missing.

Evidence surfaces: `/research/data-quality`, `/research/summary`, and
`/research/frozen-evidence`, rendered by the real `/data-quality` route.

### 3. Seismograph and Instrumented Null — 2:00

Open `/experiments` on the running frontend. Hover a walk-forward fold in the
seismograph, compare it with the same-fold baseline, then scroll to the
Instrumented Null panel. Show the observed IC inside its within-year permutation
null, the raw and Bonferroni-adjusted p-values together, and the detectable-IC
thresholds labeled as design limits.

Do not turn a single fold, a raw p-value, or a power threshold into a positive
result. The page is backed by `/research/experiments`, `/research/significance`,
and the committed experiment artifacts named on the surface.

### 4. Negative Alpha Autopsy — 2:15

Open `/autopsy` on the running frontend and confirm the header says `LIVE ARTIFACT
MODE`. Walk through feature instability, small-sample overfit, sparse coverage,
multiplicity, design power, and the single-regime limitation. Finish on the
gross-versus-assumed-cost friction panel, keeping its in-drawing hypothetical
stamp and nominal-TRY universe label visible.

The page reads `/research/significance/autopsy`; it does not recompute evidence
or change any model or ranking.

### 5. Skeptic and Research Courtroom — 2:15

First expose the deterministic Skeptic payload:

```bash
curl -fsS http://127.0.0.1:8000/research/skeptic/ASELS | python -m json.tool
```

Then open `/courtroom` on the running frontend, enter `ASELS`, leave the optional
year blank, and open the evidence docket. Show the equal four-item budgets for
Bull, Bear, Skeptic, and Risk; open citation chips; and finish on Risk, which is
always last. Point out the terminal state: no adjudication slot.

Both modes are deterministic over named artifacts. They do not require an LLM,
and unavailable or malformed evidence produces an explicit error or structured
`insufficient_data` state.

### 6. Claim-tripwire finale — 1:30

Make a temporary visible edit in `frontend/src/pages/CourtroomPage.jsx` using the
first forbidden predictive verb in `model_confidence_contract.json`. Run:

```bash
make claims-lint
```

Show the `MCC-CLAIM-001` failure, then undo the temporary edit in the editor and
immediately run:

```bash
make claims-lint
git diff --exit-code -- frontend/src/pages/CourtroomPage.jsx
```

Do not finish until both commands exit zero. The temporary mutation is never a
demo artifact and must never be staged or committed.

Rehearsed on 2026-07-13 from a clean `frontend/src/pages/CourtroomPage.jsx`:

```text
$ make claims-lint
exit 2 — MCC-CLAIM-001 rejected one temporary line in CourtroomPage.jsx
$ make claims-lint
Claims lint PASSED: Model Confidence Contract v1.7.0 satisfied.
$ git diff --exit-code -- frontend/src/pages/CourtroomPage.jsx
exit 0
```

The same rehearsal's preflight transcript was:

```text
$ make demo-check
PASS /health: status=ok version=3.0.0
PASS /research/runtime-status: CSV-backed data (not fallback): public_rows=240 public_tickers=40
PASS /forecasting/options: CSV-backed data (not fallback): source=modeling_dataset_public_2020_2025.csv tickers=40 features=40
Demo smoke check passed: all endpoints report real CSV-backed runtime data.
```

## Fallback branches

### LLM unavailable

Show `/research/ai-status` or the `ai_provider` and
`llm_fallback_available` fields in `/research/runtime-status`; do not hide the
unavailable provider. Continue with Skeptic and Courtroom because their core
paths are deterministic. If demonstrating the research assistant, label its
validated deterministic fallback exactly as the returned response does.

### Backend unavailable

Do not present fallback values as live evidence. `/data-quality` and
`/experiments` visibly label their demo data when API requests fail. `/autopsy`
switches to `DEMO FALLBACK · NO VALUES`; use that state only to explain layout
and unavailable evidence. Courtroom displays the request failure and creates no
arguments. Skip live API assertions and show the failed smoke-check line as the
blocker.

### Authentication unavailable

Protected frontend routes redirect to `/login` without an approved Supabase
session. Keep the UI blocked and use the read-only API path only when the backend
is explicitly running in public demo mode. Never bypass or weaken authentication
for a presentation.

### Single-page version — about 3 minutes

With backend evidence and frontend authentication available, open `/autopsy`
only. Confirm `LIVE ARTIFACT MODE`, show the six limitation exhibits, pair raw
and corrected significance, state the detectable-IC values as design limits,
and finish with the stamped gross-versus-assumed-cost friction panel. If live
artifact mode is absent, use the backend-unavailable branch instead.

## Fresh-database bootstrap (scratch DB only)

To validate the bootstrap order on a clean database, use an isolated scratch
Postgres instance — never point this at an existing local or shared database.
Give the scratch stack its own Compose project name so it gets its own
volume and network, and drop the host port mapping if `5432` is already in
use locally:

```bash
printf 'services:\n  db:\n    ports: !reset []\n' | \
  docker compose -p financeiq-scratch -f docker-compose.yml -f - up -d db

docker compose -p financeiq-scratch build backend
```

Required bootstrap sequence, in order (see [`README.md`](../README.md) for
the standard non-scratch equivalents of these commands):

```bash
docker compose -p financeiq-scratch run --rm --no-deps backend \
  sh -lc 'alembic upgrade head && python -m scripts.load_trusted_yearly'

docker compose -p financeiq-scratch run --rm --no-deps backend \
  sh scripts/start_backend.sh
```

Confirm `alembic_version`, `yearly_stocks`, and `users` exist, and that
`/health` returns HTTP 200, using `docker compose exec` against the scratch
`db` service. Tear the scratch stack down afterward, including its volume:

```bash
docker compose -p financeiq-scratch down -v
```

This procedure is unverified until re-run against the current migration
head; see [`VERIFICATION_BASELINE.md`](VERIFICATION_BASELINE.md) for current
state and the [archived 2026-07-12 record](archive/verification/FRESH_DATABASE_BOOTSTRAP_VERIFICATION-2026-07-12.md)
for the last dated pass.

## Shutdown check

From the repository root:

```bash
make claims-lint
git diff --check
git status --short
```

The claim lint must be green, no temporary finale edit may remain, and the status
must contain only the intended documentation changes for the current work.
