# TASK.md

## Status (2026-07-08)

**This validation objective is COMPLETE** (commit `47e1510a`, re-verified 2026-07-08 — see `OPERATING_LAYER_VALIDATION.md` for the full re-check, including test runs). Do not re-execute it. Current work for agents is sequenced in `FINANCEIQ_AGENT_TASK_QUEUE.md`; small/cheap models must also follow `FINANCEIQ_SMALL_MODEL_RULES.md`. Note: the "no documentation files beyond these four" restriction below applied to the original validation task only; the strategy-pass documents (`OPERATING_LAYER_VALIDATION.md`, `FINANCEIQ_*.md`, `.agent/memory/`) were explicitly authorized afterward.

**Update 2026-07-12:** a candidate forward roadmap now exists — `FINANCEIQ_MOONSHOT_ROADMAP.md` (assessment, twelve evidence-grounded roadmap ideas, Stage 0–4 prioritization, do-not-claim register, interviewer narrative). Its execution tasks are appended to `FINANCEIQ_AGENT_TASK_QUEUE.md` as **Phase 2** (R2-* tasks). Nothing in the roadmap is committed work, and none of it may weaken the IC ≈ 0 honesty boundary.

**Update 2026-07-13: Phase 1 AND Phase 2 are COMPLETE and committed** (HEAD `fbab761f`; suites re-verified this date — root 168/168, backend 85/85). Do not start OPS-01 or any R2-* task; they are done. **Next agent: start with R3-GOV-01** in `FINANCEIQ_AGENT_TASK_QUEUE.md` § "Phase 3 — Execution truth & frontier queue" and follow the Phase-3 order there. Planning provenance (candidate register, adversarial review, dependency graph, waves, verification matrix, model allocation): `FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md`. Strategic frame: `FINANCEIQ_MOONSHOT_ROADMAP.md` §9.

## Objective

Validate the four-file operating layer for this repository. Confirm that `CLAUDE.md`, `PRD.md`, and `REPO_MAP.md` accurately describe the current repo. Fix only incorrect paths, wrong commands, misleading architecture descriptions, false product claims, or unclear task instructions. Do not implement product features.

## Context Files

1. `CLAUDE.md`
2. `PRD.md`
3. `REPO_MAP.md`
4. Spot-check against: root directory listing, `Makefile`, `README.md`, `backend/app/routers/`, `frontend/src/pages/`, `frontend/package.json`, `backend/requirements.txt`, `docker-compose.yml`.

## Allowed Changes

- Corrections to paths, commands, counts, and architecture descriptions in `CLAUDE.md`, `PRD.md`, `REPO_MAP.md`, `TASK.md`.
- Resolving items marked "Needs verification" (confirm or correct them).
- Removing claims not supported by repo evidence.

## Forbidden Changes

- Any source-code, pipeline, data, config, or dependency change.
- Implementing features, fixing bugs, refactoring, or renaming files/folders.
- Creating documentation files beyond these four.
- Editing generated outputs under `data/trusted/` or `data/trusted_clean/`.

## Acceptance Criteria

1. Every path named in the three docs exists in the repo (or is explicitly marked "needs verification").
2. Every command in `CLAUDE.md` matches a real Makefile target, script, or package.json script.
3. `PRD.md` claims match `README.md`/`TASK_STATE.md` evidence; no invented features or users.
4. `REPO_MAP.md` sections point at real, high-leverage paths.
5. No product code was changed.

## Verification

```bash
# Existence spot-checks (no code execution required)
ls backend/app/routers backend/app/services frontend/src/pages scripts/data_collection data/trusted_clean
grep -n "full-research\|data-validate\|research-agent-check" Makefile

# Optional, if environment allows:
PYTHONPATH=. python -m pytest tests/          # root suite -> 95 pass, 2 fail (stale call_local_llm)

# Backend suite. Do NOT run as `cd backend && pytest tests/` if an untracked
# backend/.env holds OPENROUTER_* keys: Settings forbids extra inputs and
# collection aborts. Run from the repo root instead -> 51/51 pass.
PYTHONPATH=backend python -m pytest backend/tests
```

Both suites were run on 2026-07-08; results above are observed, not assumed.

## Final Response Format

1. **Verdict** — accurate / corrected, per file.
2. **Corrections made** — file + line-level description of each fix (or "none needed").
3. **Remaining uncertainties** — anything still marked "needs verification" and why.
