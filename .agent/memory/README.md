# .agent/memory — repo-local agent lessons

## Purpose

Durable, repo-specific lessons for coding agents working on FinanceIQ, so mistakes and discoveries survive across sessions and across different agents/models. This directory stores *earned* knowledge only — things confirmed by actually running commands or reading code in this repo.

## Format rules

1. **One lesson per file**, named `NN-short-kebab-slug.md` (e.g. `01-backend-pytest-env-trap.md`).
2. **First line of every lesson is a one-line summary** (a single bold sentence). Details, evidence, and the command/output that confirmed it follow below.
3. **Only confirmed, repo-specific lessons.** A lesson must cite the file, command, or output that proves it. No hunches, no general programming advice.
4. **What belongs here:** command discoveries (flags, env vars, working directories that matter), recurring traps (things that failed the same way twice), confirmed implementation patterns (e.g. "contract tests pin API shapes — extend them, don't bypass"), and mistakes an agent actually made here with how to avoid them.
5. **What does not belong here:** anything already in `CLAUDE.md`, `PRD.md`, `REPO_MAP.md`, or `TASK.md` — those are the operating layer; do not duplicate them. If a lesson deserves promotion into `CLAUDE.md`, propose that in your final report instead of copying it both places.
6. **Update, don't duplicate.** Before writing, scan existing filenames; if a lesson exists on the topic, edit it.
7. **Delete lessons that prove wrong.** A stale lesson is worse than none. If repo changes invalidate a note, remove it (or correct it) in the same task that made the change.
8. **No vague preferences or speculation.** "Prefer smaller diffs" is not a lesson; "`make research` rewrites committed files under `experiments/` — never run it for verification-only purposes" is.

## Current state

Empty by design (created 2026-07-08 during the strategy/validation pass). Known traps are currently documented in `CLAUDE.md` ("Known test-suite state") and `FINANCEIQ_SMALL_MODEL_RULES.md` §7 — per rule 5, they are not duplicated here. Task DOC-01 in `FINANCEIQ_AGENT_TASK_QUEUE.md` seeds the first lessons once new ones are earned.
