# Process documentation

FinanceIQ was built with AI coding agents under a spec → review → CI-gate
workflow. I own the research design, the engineering decisions, the
acceptance criteria and the validation; agents wrote much of the code against
written specifications.

This directory keeps the material that workflow produced — the rules agents
work under, product scope, the repository map, completed task packets and
dated plans — for provenance. It is not the description of the research.

| If you want… | Read |
| --- | --- |
| The question, method, result and limitations | [`../../README.md`](../../README.md), [`../../RESULTS.md`](../../RESULTS.md) |
| The full methodology | [`../../METHODOLOGY.md`](../../METHODOLOGY.md) |
| Audits of the data and of the published result | [`../audit/`](../audit/PUBLICATION_LAG_AUDIT.md) |
| The rules a coding agent follows | [`AGENTS.md`](AGENTS.md) (byte-identical to [`CLAUDE.md`](CLAUDE.md)) |

## Old → new paths (moved 2026-10, branch `phase2/public-credibility`)

| Old path | New path |
| --- | --- |
| `AGENTS.md`, `CLAUDE.md` | `docs/process/` (short pointers remain at the root because tools load them from there) |
| `PRD.md`, `REPO_MAP.md`, `TASK.md`, `PROJECT_CONTEXT.md` | `docs/process/` |
| `FINANCEIQ_SMALL_MODEL_RULES.md`, `FINANCEIQ_MOONSHOT_ROADMAP.md`, `FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md`, `OPERATING_LAYER_VALIDATION.md` | `docs/process/` |
| `DATA_01_DATA_DICTIONARY_AUDIT.md` | `docs/audit/` |
| Application/deployment sections of `README.md` | `docs/OPERATIONS.md` |

Contents are unchanged. Two process files stay at the root because code
reads them by path: `TASK_STATE.md` (Stage 3 registration test) and
`FINANCEIQ_AGENT_TASK_QUEUE.md` (memo citation service). Dated documents that
link to the old paths, including pre-registrations, were not edited.
