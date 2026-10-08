# FinanceIQ repository hygiene closure report

Read-only inventory snapshot: **2026-10-08 10:41:10 CEST (+0200)**.

## Scope and closure sequence

The FIQ-02 card specified report-first ordering: inventory and report, then owner approval, then any cleanup. Owner-directed cleanup overtook that sequence. This is the **post-cleanup closure record**, not a record of an agent-run cleanup or a request to remove anything. The current inventory below was refreshed after that owner cleanup.

The current local `main` ref is `7b62c1b29cf319a073887eaa79a3a0fa262e4261`. Requested base: `7b62c1b29cf319a073887eaa79a3a0fa262e4261`. Match: **yes**. The dedicated report checkout is on `codex/fiq-02-hygiene-closure-20261008` at `7b62c1b29cf319a073887eaa79a3a0fa262e4261` before this report commit.

Owner-reported cleanup history (these are separate observations and are not reconstructed as one simultaneous snapshot):

- Stale worktree metadata was pruned conservatively.
- The FO-3 merged worktree was removed only after its process holders were cleared.
- An earlier batch removed 15 clean, merged, non-SC5 worktrees.
- A later batch archived 24 additional non-SC5 worktrees with local state before removing them. Recovery location: `/Users/salihcamci/FinanceIQ_WORKTREE_SALVAGE/non-sc5-before-remove-20261007-195019`.
- The owner observed `SALVAGE_ARCHIVE_VERIFY: PASS`. This is owner-reported; this task did not access or independently verify the recovery archive.
- Local branches were intentionally preserved. The active mobile-responsive worktree was intentionally preserved. SC5 worktrees and archive state were intentionally preserved.
- The owner observed 36 registered worktrees immediately after cleanup, then a later snapshot observed 37 while subsequent task activity was occurring. This fresh snapshot observes a different later state with the count shown below; these counts are not simultaneous.

No worktree or branch was changed. SC5 repository contents, evidence, acquisition state, archive contents, and salvage contents were not opened; this census read only the worktree and branch-ref metadata needed to verify protected HEADs and reachability. No research result files were opened and no outcome was computed. Historical removed worktrees do not appear in the current registration census.

## Snapshot summary

- Current registered worktrees: **44**.
- SC5-preserved: **30** with SC5 in path or branch; plus **1** SC5-related run10 evidence worktree.
- External worktrees: **2**.
- Active cwd holders observed: **9 worktrees**.
- Dirty worktrees: **7**.
- Detached worktrees: **3**.
- Local branches merged into current main: **293**; not merged: **10**.

Definitions: registered paths come from `git worktree list --porcelain`. Clean/dirty is based on `git -C <path> status --porcelain=v1 --untracked-files=all`. A live cwd holder was observed with `lsof -nP -d cwd`; a holder counts when its cwd equals the worktree path or is beneath it. HEAD ref containment uses `git branch -a --contains <HEAD>` (local and remote-tracking branches; tags excluded). “Merged into main” means HEAD is an ancestor of the local `refs/heads/main` observed above. Last commit date is the committer date (`%cs`). Process and Git observations are point-in-time; task activity may register new worktrees later.

Actions are proposals only. `KEEP` protects dirty or active work, SC5/run10, and the live primary/task checkout. `REVIEW` means path ownership, detached state, branch reachability, or current task purpose needs owner review. `EVENTUAL_REMOVE` identifies a clean, inactive, merged, internal, non-SC5 candidate for a future owner-directed cleanup only; no such action is authorized or performed by this report.

## Current registered worktrees

| Classification | Path | HEAD | Branch or detached | Clean/dirty | Active cwd holder | HEAD in local/remote ref | Merged into main | Last commit date | Proposed action |
|---|---|---|---|---|---|---|---|---|---|
| primary checkout, active-session, dirty | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ` | `7243c5efa7d00ff45200cfa7589cebd2f3ba0017` | `codex/fiq-01-study-record-template-20261007` | dirty | yes | yes | yes | 2026-10-07 | **KEEP** |
| external | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/.phase2-worktrees/financeiq` | `8b6a9a29afff3892cfb61bc4c87dc11cb0c1ff73` | `phase2/public-credibility` | clean | no | yes | yes | 2026-10-04 | **REVIEW** |
| registered worktree | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/cap-exhaustion-guard-a958c9` | `9681646e5199896c11b48c3bb6cd0319deba0c09` | `local/cap-exhaustion-guard-a958c9` | clean | no | yes | yes | 2026-09-01 | **EVENTUAL_REMOVE** |
| active-session | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/capstone-v1-record-09259b` | `457d8bf903535cb8c03eb1bf9056f9d3dfbdaa8e` | `local/capstone-v1-record-09259b` | clean | yes | yes | no | 2026-10-08 | **KEEP** |
| active-session, dirty | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-mobile-responsive-f48d61` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/financeiq-mobile-responsive-f48d61` | dirty | yes | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved, active-session, dirty | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-amendment-03-92b432` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/financeiq-sc5-amendment-03-92b432` | dirty | yes | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-amendment-03-gate1-9ec0ee` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/financeiq-sc5-amendment-03-gate1-9ec0ee` | clean | no | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-amendment-03-i2-1ba6d5` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/financeiq-sc5-amendment-03-i2-1ba6d5` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-gate1-amendment-74ba98` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/financeiq-sc5-gate1-amendment-74ba98` | clean | no | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-gate1-r2-a76070` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/financeiq-sc5-gate1-r2-a76070` | clean | no | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-stage2-degeneracy-review-a28a32` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-reconciliation-6130ab` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-stage3-r2-integrity-2f26c4` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-run10-live-execution-62077c` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| active-session, dirty, HEAD equals main | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-02-hygiene-closure-20261008` | `7b62c1b29cf319a073887eaa79a3a0fa262e4261` | `codex/fiq-02-hygiene-closure-20261008` | dirty | yes | yes | yes | 2026-10-08 | **KEEP** |
| HEAD equals main | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-03-panel-v2-status-20261008` | `7b62c1b29cf319a073887eaa79a3a0fa262e4261` | `claude/fiq-03-panel-v2-status-20261008` | clean | no | yes | yes | 2026-10-08 | **REVIEW** |
| active-session | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-20261007` | `43dcd2aade75593764c75e2686bfaacf02508863` | `codex/fiq-05-capstone-v1-record-20261007` | clean | yes | yes | no | 2026-10-08 | **KEEP** |
| dirty, HEAD equals main | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-20261008` | `7b62c1b29cf319a073887eaa79a3a0fa262e4261` | `claude/fiq-05-capstone-v1-record-20261008` | dirty | no | yes | yes | 2026-10-08 | **KEEP** |
| active-session | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-63f5da` | `7dccc12c8ea939b364cffa9dffd3d32c63d3a04f` | `local/fiq-05-capstone-v1-record-63f5da` | clean | yes | yes | yes | 2026-10-07 | **KEEP** |
| active-session, dirty | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-tag-governance-694f8e` | `43dcd2aade75593764c75e2686bfaacf02508863` | `local/fiq-05-tag-governance-694f8e` | dirty | yes | yes | no | 2026-10-08 | **KEEP** |
| active-session | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/panel-v2-preregistration-closure-7547e0` | `41a63dae190e4736f229450ac7975050a3d998b3` | `local/panel-v2-preregistration-closure-7547e0` | clean | yes | yes | no | 2026-10-08 | **KEEP** |
| SC5-related run10 evidence | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/run10-evidence-closeout-16691a` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/run10-evidence-closeout-16691a` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-acquisition-readiness-3bde3e` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-run10-closeout-review-2e0e88` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-amendment-03-guard-audit-7ec5c7` | `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6` | `local/sc5-amendment-03-guard-audit-7ec5c7` | clean | no | yes | yes | 2026-10-04 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-amendment-03-i2-derivation-b98cd0` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-amendment-03-i2-derivation-b98cd0` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-amendment-03-i2-validation-3002a1` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-amendment-03-i2-validation-3002a1` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-amendment-03-i2-validation-a5920c` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-amendment-03-i2-validation-a5920c` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-amendment-03-spec-447e53` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-amendment-03-spec-447e53` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-amendment-03-08d263` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-amendment-03-08d263` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-amendment-03-9e5dad` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-amendment-03-9e5dad` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-amendment-03-bfafdd` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-amendment-03-bfafdd` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-amendment-03-review-263b11` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-amendment-03-review-263b11` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-amendment-03-review-c72068` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-amendment-03-review-c72068` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved, detached | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-exhaustion-guard-20260930` | `2a0318967b8689116bb2c7e96dd0d761aa2b9a8b` | `detached` | clean | no | yes | no | 2026-10-03 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-exhaustion-review-34223a` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-cap-exhaustion-review-34223a` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-extension-261330` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-cap-extension-261330` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-extension-e9b0d2` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-cap-extension-e9b0d2` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-extension-impact-3204c8` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-cap-extension-impact-3204c8` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved, detached | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-transport-observability-362318` | `b04d8b8f41b729157980edd4010b164f8cb21b85` | `detached` | clean | no | yes | no | 2026-09-28 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-transport-observability-d02be1` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-batch1-run09-closeout-651a14` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-cap-exhaustion-guard-8f99f0` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-cap-exhaustion-guard-8f99f0` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-cap-exhaustion-guard-review-5b3677` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-cap-exhaustion-guard-review-5b3677` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-cap-exhaustion-guard-tests-3d3211` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-cap-exhaustion-guard-tests-3d3211` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-cap-exhaustion-validation-c7c84f` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-cap-exhaustion-validation-c7c84f` | clean | no | yes | yes | 2026-09-07 | **KEEP** |
| SC5-preserved, dirty | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-replacement-runner-1144e037` | `1144e0370bad62557d67725f4a4cac732f26664e` | `local/sc5-replacement-runner-1144e037` | dirty | no | yes | yes | 2026-09-07 | **KEEP** |
| external, detached | `/Users/salihcamci/Documents/Codex/2026-10-04/referenced-chatgpt-conversation-this-is-an/work/financeiq-baseline` | `1144e0370bad62557d67725f4a4cac732f26664e` | `detached` | clean | no | yes | yes | 2026-09-07 | **REVIEW** |

### Main and external worktrees

- The primary checkout path is `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ`. It is checked out on `codex/fiq-01-study-record-template-20261007`, not on `main`.
- No registered worktree is attached to the local `main` branch.
- External registered worktrees are `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/.phase2-worktrees/financeiq` and `/Users/salihcamci/Documents/Codex/2026-10-04/referenced-chatgpt-conversation-this-is-an/work/financeiq-baseline`; both are marked REVIEW in the table.

### Active-session worktrees

- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/capstone-v1-record-09259b`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-mobile-responsive-f48d61`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-amendment-03-92b432`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-02-hygiene-closure-20261008`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-20261007`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-63f5da`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-tag-governance-694f8e`
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/panel-v2-preregistration-closure-7547e0`

### Dirty and detached worktrees

**Dirty:**
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ` — `codex/fiq-01-study-record-template-20261007` at `7243c5efa7d00ff45200cfa7589cebd2f3ba0017`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-mobile-responsive-f48d61` — `local/financeiq-mobile-responsive-f48d61` at `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-sc5-amendment-03-92b432` — `local/financeiq-sc5-amendment-03-92b432` at `cfa52b2af9528cb45484d26439f6f64aa4e2c4b6`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-02-hygiene-closure-20261008` — `codex/fiq-02-hygiene-closure-20261008` at `7b62c1b29cf319a073887eaa79a3a0fa262e4261`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-capstone-v1-record-20261008` — `claude/fiq-05-capstone-v1-record-20261008` at `7b62c1b29cf319a073887eaa79a3a0fa262e4261`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/fiq-05-tag-governance-694f8e` — `local/fiq-05-tag-governance-694f8e` at `43dcd2aade75593764c75e2686bfaacf02508863`.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-replacement-runner-1144e037` — `local/sc5-replacement-runner-1144e037` at `1144e0370bad62557d67725f4a4cac732f26664e`.

**Detached:**
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-exhaustion-guard-20260930` — HEAD `2a0318967b8689116bb2c7e96dd0d761aa2b9a8b`; local or remote branch ref contains HEAD: **yes**; merged into main: **no**.
- `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-transport-observability-362318` — HEAD `b04d8b8f41b729157980edd4010b164f8cb21b85`; local or remote branch ref contains HEAD: **yes**; merged into main: **no**.
- `/Users/salihcamci/Documents/Codex/2026-10-04/referenced-chatgpt-conversation-this-is-an/work/financeiq-baseline` — HEAD `1144e0370bad62557d67725f4a4cac732f26664e`; local or remote branch ref contains HEAD: **yes**; merged into main: **yes**.

Each detached HEAD is contained in a local/remote branch ref. The detached-only reachable-commit check (`git rev-list <HEAD> --not --all`) found **no commits unique to any detached HEAD**.

### SC5 preservation

- Required archive branch `archive/sc5-kap-batch1-2026-10-03` exists at `2a0318967b8689116bb2c7e96dd0d761aa2b9a8b` in the local ref inventory.
- Critical preserved HEAD `2a0318967b8689116bb2c7e96dd0d761aa2b9a8b` is registered at `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/sc5-batch1-cap-exhaustion-guard-20260930`. It is detached, ref-contained, and remains **KEEP** despite not being merged into main.
- All current SC5 worktrees and the SC5-related run10 evidence worktree are proposed KEEP regardless of merge status. This report does not inspect SC5 contents, files, evidence, acquisition state, or archive contents.

### Local branch reachability

Local branches merged into `main` (**293**):

```text
chore/refresh-pipeline-audit-snapshot
ci/actions-node24-maintenance
claude/elastic-neumann-d498cc
claude/fiq-03-panel-v2-status-20261008
claude/fiq-05-capstone-v1-record-20261008
claude/gallant-cartwright-ee6e85
codex/fiq-01-study-record-template-20261007
codex/fiq-02-hygiene-closure-20261008
codex/fiq-05-capstone-v1-record
codex/fiq-05-capstone-v1-record-from-main
data-expand/kap-trigger-audit
data-expand/membership-collision-2020
data-expand/membership-event-audit
data-expand/membership-sourcing-04b
data-expand/p3184-2020-reconciliation
dev/codespaces-wave1
docs/preregister-data-expansion-stage-a
docs/source-use-owner-amendment
fix/bist100-benchmark-output-path-forward
fix/data-relative-universe-split-paths
fix/quarterly-snapshot-relative-path
fix/yearly-snapshot-relative-paths
local/affectionate-keller-63400c
local/affectionate-ptolemy-130c13
local/ai-assistant-trust-replay-23227e
local/ai-research-assistant-trust-96fa78
local/autopsy-page-trust-audit-46196a
local/benchmark-page-trust-audit-ff1670
local/bist-100-membership-provenance-14e54f
local/branch-location-check-f2f53f
local/cap-exhaustion-guard-a958c9
local/capstone-strategy-readiness-ab0527
local/cell-provenance-lineage-contract-a69fe8
local/company-compare-responsive-replay-ec4535
local/company-detail-unification-df79cd
local/data-quality-page-trust-b448f5
local/data-quality-trust-replay-a13a70
local/eager-brattain-e94e74
local/eager-taussig-b00ce0
local/elated-cohen-dabd9f
local/exciting-jepsen-eb5559
local/exciting-kapitsa-2c277e
local/experiments-page-trust-9f2351
local/experiments-trust-replay-53cab0
local/fable5-harvest
local/fable5-roadmap-audit-obs3-8df9c8
local/fi-data-expand-02-preregistration-826551
local/fi-data-path-02c-audit-adjudication-08c74f
local/fi-data-path-02c-refresh-c2f8c1
local/fi-tool-02-merge-verify-96452e
local/financeiq-api-evaluation-ab74e1
local/financeiq-architecture-audit-e3690b
local/financeiq-audit-reconciliation-34a36c
local/financeiq-audit-reconciliation-953af2
local/financeiq-audit-reconciliation-ce2f51
local/financeiq-benchmark-provenance-f8cf2e
local/financeiq-bist-audit-c62f61
local/financeiq-calibration-design-31144b
local/financeiq-codespaces-readiness-39bb61
local/financeiq-codespaces-wave1-96a674
local/financeiq-data-audit-b97914
local/financeiq-data-correlation-3c159d
local/financeiq-data-provenance-audit-fb73c6
local/financeiq-data-repair-design-88dfb9
local/financeiq-data-sufficiency-audit-79b774
local/financeiq-defect-injection-b208df
local/financeiq-dependency-adjudication-398f5b
local/financeiq-directory-audit-f16c61
local/financeiq-engineering-audit-a41604
local/financeiq-evidence-corrections-6e1f4a
local/financeiq-evidence-service-review-5b3c76
local/financeiq-fintables-audit-0fb778
local/financeiq-harness-cleanup-1fe3b7
local/financeiq-harness-reconciliation-32dbda
local/financeiq-ic-zero-audit-670b04
local/financeiq-inference-year-fix-1d1d7a
local/financeiq-mobile-responsive-f48d61
local/financeiq-mock-remediation-972d51
local/financeiq-orphan-cleanup-1ea94c
local/financeiq-orphan-worktree-audit-fbe999
local/financeiq-p0-trust-review-3f8e25
local/financeiq-panel-v2-pit-microfix-858adb
local/financeiq-panel-v2-pit-preregistration-1642d6
local/financeiq-panel-v2-pit-review-7bac89
local/financeiq-panel-v2-transplant-f14525
local/financeiq-phase2-planning-b9d477
local/financeiq-positive-control-review-0d1653
local/financeiq-positive-control-review-1d2b40
local/financeiq-positive-control-stage1-96f1fe
local/financeiq-power-audit-cb7a4f
local/financeiq-power-frontier-design-746d63
local/financeiq-pr22-ci-repair-0ac666
local/financeiq-pr22-ci-repair-c092d6
local/financeiq-preregistration-design-952b2d
local/financeiq-prior-shutdown-b75bb6
local/financeiq-r3-memo-01-review-d1f50c
local/financeiq-r3-miss-01-review-cda3e7
local/financeiq-r3-null-01-review-d39800
local/financeiq-r3-null-01-verify-04acfc
local/financeiq-r3-prereg-01-b851f4
local/financeiq-r3-prereg-01-review-32593a
local/financeiq-r3-serv-01-review-1125b1
local/financeiq-r3-tgt-01-corrections-df646b
local/financeiq-r3-tgt-01-review-9540df
local/financeiq-raw-layer-control-1dc18f
local/financeiq-recent-additions-268e40
local/financeiq-release-audit-315570
local/financeiq-research-review-c26885
local/financeiq-rev-01-governance-166cb8
local/financeiq-sc5-amendment-03-92b432
local/financeiq-sc5-amendment-03-gate1-9ec0ee
local/financeiq-sc5-amendment-03-i2-1ba6d5
local/financeiq-sc5-batch1-gate-a2182b
local/financeiq-sc5-diagnostic-02-7e5ed6
local/financeiq-sc5-gate1-amendment-74ba98
local/financeiq-sc5-gate1-r2-a76070
local/financeiq-score-explorer-integrity-bd9f77
local/financeiq-significance-failclosed-8d31c4
local/financeiq-small-model-os-corrections-d5c0f2
local/financeiq-source-use-amendment-ca2d07
local/financeiq-stage-a-preregistration-197b17
local/financeiq-stage1-microfix-review-7df9e4
local/financeiq-stage1b-audit-464803
local/financeiq-stage1b-audit-5944e0
local/financeiq-stage1b-bookkeeping-92c4e1
local/financeiq-stage1b-governed-run-7e4c21
local/financeiq-stage1b-impl-b85ce9
local/financeiq-stage1b-implementation-4c7e91
local/financeiq-stage1b-limitations-register-3f1c00
local/financeiq-stage1b-post-run-guard-a7f9fd
local/financeiq-stage1b-registration-6f2d91
local/financeiq-stage1b-registration-f981b4
local/financeiq-stage1b-registration-fix-44ab03
local/financeiq-stage1b-review-60d1b0
local/financeiq-stage1b-review-a4a8b9
local/financeiq-stage1b-review-b40990
local/financeiq-stage1b-safety-review-917867
local/financeiq-stage1b-staging-cleanup-80fa8d
local/financeiq-stage2-audit-a4971f
local/financeiq-stage2-degeneracy-review-a28a32
local/financeiq-stage2-governance-657af0
local/financeiq-stage2-governed-run-2d83a7
local/financeiq-stage2-implementation-6c91e4
local/financeiq-stage2-ledger-close-c9934218
local/financeiq-stage2-nc-validity-8f8ba1
local/financeiq-stage2-negative-controls-8bd24f
local/financeiq-stage2-registration-4f7c2a
local/financeiq-stage2-review-d8ff6d
local/financeiq-stage3-defect-registration-ecbe8f
local/financeiq-stage3-r2-audit-acf905
local/financeiq-stage3-r2-integrity-2f26c4
local/financeiq-stage3-readiness-01f850
local/financeiq-stage3-readiness-646cbc
local/financeiq-stage3-review-c4ad1a
local/financeiq-stale-path-audit-272444
local/financeiq-stale-paths-repair-dda527
local/financeiq-stash-cleanup-aa5441
local/financeiq-stash-forensics-671e36
local/financeiq-thesis-analysis-1e78af
local/financeiq-thesis-pivot-plan-f53b23
local/financeiq-thesis-week0-baseline-b85db0
local/financeiq-tmp-stub-prune-3eaf58
local/financeiq-trust-remediation-1de73c
local/financeiq-worktree-audit-d9733f
local/financeiq-worktree-cleanup-p1-99fa66
local/financeiq-worktree-forensics-3fbe71
local/financeiq-worktree-preservation-5b8d3f
local/financeiq-worktree-repair-809a5e
local/financeiq-worktree-shutdown-1124c8
local/fintables-governance-audit-e6c6fa
local/fiq-05-capstone-v1-record-63f5da
local/focused-carson-ecd845
local/forecasting-page-trust-63e1d4
local/forecasting-trust-replay-062206
local/git-status-report-531bde
local/github-actions-node-runtime-b1a1e6
local/governance-ai-agent-rules-5b584f
local/hardcore-mahavira-527829
local/honest-demo-data-notes
local/hungry-poitras-b33668
local/inspect-2020-05-22-catalogue-19374e
local/inspiring-morse-02b421
local/kap-trigger-reserve-audit-84bd7d
local/nervous-cori-ec7912
local/nice-chatelet-dce077
local/nice-meninsky-27a079
local/org-scoped-agent-activity-review-dc254f
local/p0-trust-remediation-review-e707bd
local/p3184-2020-evidence-fixes-6848bf
local/p3184-2020-provenance-correction-875e58
local/portfolio-docs-validation-040181
local/prof-jonathan-review-persona-646092
local/proofspace-frontend-review-31d5b5
local/public-apis-ecosystem-eval-18b40f
local/quarterly-snapshot-path-fix-c4ff50
local/r3-memo-01-packet-freeze
local/r3-miss-01-amendment-fbc80d
local/r3-miss-01-compatibility-repair-8427d7
local/r3-miss-01-five-blocker-0386b4
local/r3-miss-01-mandatory-repair-641348
local/r3-miss-01-missingness-sensitivity
local/r3-miss-01-missingness-sensitivity-323279
local/r3-miss-01-missingness-sensitivity-ad3e40
local/r3-miss-01-repair-completion-0043a6
local/r3-null-01-placebo
local/r3-null-01-placebo-34c76e
local/r3-prereg-01-review-approval-f491c5
local/r3-stat-01-review-81e762
local/r3-tgt-01-audit-record-fa4fdb
local/r3-tgt-01-excess-basis-2e6992
local/r3-tgt-01-excess-implementation
local/r3-tgt-01-excess-return
local/r3-tgt-01-excess-return-487593
local/r3-tgt-01-excess-target-fitting-6156c4
local/r3-tgt-01-governance-amendment-437b14
local/r3-tgt-01-independent-review
local/r3-tgt-01-merge-closure-381108
local/r3-tgt-01-owner-amendment-e9b534
local/r3-tgt-01-post-commit-record-1cba84
local/r3-tgt-01-rereview-approval-bde212
local/r3-tgt-01-review-defects-08d3d5
local/r3-tgt-01-review-record-38f5be
local/r3-tgt-01-tech-review-b2728e
local/r3-ui-02-return-basis
local/repo-operating-layer-5cafc6
local/reverent-hugle-3bb540
local/route-1-model-routing-config-a00c42
local/run10-evidence-closeout-16691a
local/sams-security-boundary-verify-b38476
local/sc5-acquisition-readiness-3bde3e
local/sc5-aksen-diagnostic-review-13dc7a
local/sc5-aksen-empty-day-review-f1feec
local/sc5-amendment-03-guard-audit-7ec5c7
local/sc5-amendment-03-i2-derivation-b98cd0
local/sc5-amendment-03-i2-validation-3002a1
local/sc5-amendment-03-i2-validation-a5920c
local/sc5-amendment-03-spec-447e53
local/sc5-authority-escape-hatches-ad1470
local/sc5-batch1-amendment-03-08d263
local/sc5-batch1-amendment-03-9e5dad
local/sc5-batch1-amendment-03-bfafdd
local/sc5-batch1-amendment-03-review-263b11
local/sc5-batch1-amendment-03-review-c72068
local/sc5-batch1-cap-exhaustion-review-34223a
local/sc5-batch1-cap-extension-261330
local/sc5-batch1-cap-extension-e9b0d2
local/sc5-batch1-cap-extension-impact-3204c8
local/sc5-batch1-freeze-review-25549b
local/sc5-batch1-preflight-354c09
local/sc5-batch1-reconciliation-6130ab
local/sc5-batch1-run09-closeout-651a14
local/sc5-batch1-run09-live-7a8e92
local/sc5-batch1-transport-observability-362318
local/sc5-batch1-transport-observability-d02be1
local/sc5-batch1-ua-i0-i1-transition-f61db1
local/sc5-batch1-ua-integrity-review-e86e91
local/sc5-batch1-ua-preflight-43f39b
local/sc5-cap-exhaustion-guard-8f99f0
local/sc5-cap-exhaustion-guard-review-5b3677
local/sc5-cap-exhaustion-guard-tests-3d3211
local/sc5-cap-exhaustion-validation-c7c84f
local/sc5-file-bound-orchestration-d179aa
local/sc5-replacement-runner-1144e037
local/sc5-run10-closeout-review-2e0e88
local/sc5-run10-live-execution-62077c
local/screener-v1-contract-bb653c
local/serene-darwin-2665a2
local/session-05eb52
local/session-06d07f
local/session-46aea9
local/session-65144d
local/session-a85f6e
local/session-ea661e
local/small-model-operating-system
local/small-model-operating-system-b6b071
local/stage-1b-calibration-design-ba0546
local/stage2-gate-multiplicity-review-c51cb1
local/stage2-negative-controls-design-cf8f8d
local/stage2-registration-review-6c7058
local/stage3-attempt1-evidence-freeze-6084b45f
local/stage3-implementation-5550dc06
local/stage3-integrity-adjudication-5d17f2
local/stage3-r2-integrity-governance-e733c4
local/stage3-r2-registration-7df5e703
local/stage3-registration-microfix-efce12
local/strange-proskuriakova-3f03c1
local/velora-strategic-continuation-de5f26
local/wonderful-mclaren-39effe
local/xenodochial-heyrovsky-3e2bd6
local/yearly-snapshot-relocatability-44a590
local/zealous-swirles-55d07e
main
phase2/public-credibility
```

Local branches not merged into `main` (**10**):

```text
archive/sc5-kap-batch1-2026-10-03
claude/modest-franklin-37915b
claude/pensive-faraday-3b49b6
codex/fiq-05-capstone-v1-record-20261007
local/capstone-v1-record-09259b
local/fiq-05-tag-governance-694f8e
local/panel-v2-pit-prereg-6084b45f
local/panel-v2-preregistration-closure-7547e0
local/r4-robust-01-contamination-stress
local/stage3-r2-adjudication-evidence-1144e037
```

The archive branch is deliberately retained even though its reachability is summarized above. Branch listing is read-only; no branch was deleted.
