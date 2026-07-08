# TASK.md

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
