# Paper 1: bounded documentation and source verification

Evidence check: **2026-10-27**, Europe/Zurich. Research support only;
not investment advice. Local documentation candidate; not a submitted paper.

## Authority and exact base

Freshly fetched and finally rechecked `origin/main`:
`efe3ed32ca958074c01ee9488f1f768a9d812c61` (PR #55 integration).
Isolated branch: `codex/fiq-16-13-14-evidence-20261027`.
The original checkout and frozen ledgers remain untouched.

Read current root/process AGENTS, paired process CLAUDE, PRD, REPO_MAP, TASK,
[governing Charter](../process/RESEARCH_CHARTER.md),
[FIQ-16/13/14 task cards](../process/TASKS_FINANCEIQ_2026-10-07.md), original
source list in gap-plan §13 and the [owner decision addendum](../research/OWNER_DECISION_ADDENDUM.md).
The project's supplied GLOBAL_AI_WORKFLOW (v2.1, 2026-10-14) and
FinanceIQ_AI_CHATGPT_CONTEXT (2026-10-14) are dated read-only references;
current repository decisions and the live task scope govern.
The 26 October addendum is on main but neither whole universe/protocol draft
is thereby adopted. No registration or protected-data access is inferred.

Supporting source: **FinanceIQ_Derin_Arastirma_TR.pdf**, dated 2026-10-27,
14 pages, 175,677 bytes, SHA-256
`b83eabe56392c0b248df26f1973ff6a256455bc855c0ce2049523713307d2d7a`.
Recovered from the referenced ChatGPT conversation attachment after its
reported `/mnt/data/` path was unavailable on this host; identical bytes also
exist in the owner's local Downloads copy. All 14 pages were read through
extracted text and rendered visual review. The PDF is supporting assertions,
not authority over repository rules, gates or status. No source mirror or
supplied PDF was edited or copied into this public repository candidate.

## Deliverables and status

| Card | Artifact | Status / limitation |
| --- | --- | --- |
| FIQ-16 | [Scientific disclosure and annual null table](survivorship_bound.md); [count/source identities](survivorship_count_evidence.json) | Scoped disclosure delivered. Structural survivor conditioning documented; extra return selection UNKNOWN; full annual table incomplete; no performance bound or FIQ-17 execution. |
| FIQ-13 | [Verification table and source limits](citation_verification.md); [proposed BibTeX](references.bib); [structured source identities](reference_evidence.json) | First twelve and core references checked; all 40 identities checked at declared bibliographic scope. PBO page range disputed/omitted; OpenAlex search assertions unverified. No 40-study replication claim. |
| FIQ-14 | [Dated official-source shortlist](journal_shortlist.md) | BIR/JAM full audit recommendation; length and fee facts distinguished from unknown fields and fit judgments. No acceptance prediction or submission. |
| Dependency | [Separate count-only request](kernel_request_fiq16.md) | For owner forwarding only; not sent. No other project's checkout, implementation, plans or outcomes accessed/transferred. |

The program-level clarification is in the root [README](../../README.md),
separate from the scientific paragraph. Charter §2-4 already establishes the
program boundary and was not rewritten. No Capstone company/sector/model cap
is imposed on independent U1/U2 research; unresolved U2 details stay unresolved.

## Verification actually performed

- `make docs-lint` — **PASS**, local links/cited paths/current baseline checks.
- `make claims-lint` — **PASS**, Model Confidence Contract v1.10.0.
- Additional scoped static verification — **PASS**: nested Markdown local links,
  40 unique bibliography keys and required identity fields, brace balance,
  36 retrieved DOI-response digests and DOI identity agreement, three existing
  configuration/projection input digests, bounded count identities and six
  all-null annual rows. Scratch checks and external metadata retrieval helpers
  were kept outside the repository; no acquisition code was added here.
- `git diff --check` and staged diff check — **PASS**; explicit task paths only.
- Fresh remote main recheck still matched the base SHA above.

These linters have limited coverage: docs-lint does not recursively cover all
new nested documents, so those local links were checked separately;
claims-lint covers configured product surfaces, not every research sentence.
No full BibTeX typesetting, remote-link availability guarantee, independent
scientific review, application suite, data/model pipeline or study run is claimed.

## Remaining queue and boundaries

Next FinanceIQ item is FIQ-15: draft only under its existing RESULTS/PIT-v2
source restriction, with unresolved selection measurement explicit. FIQ-09
phase 1 follows; neither a draft nor a third-party raw-file inventory was
created in this bounded FIQ-16/13/14 pass. Prior aggregate context was already
exposed; no clean/zero-prior-exposure claim is made.

No new returns, outcome calculation, holdout opening, model trial or membership
reconstruction occurred. Existing Capstone code/data/results were not changed.
One local documentation commit is intended; no push, PR, merge or OSF action
is authorized by this delivery. Local verification is not scientific validity
or owner acceptance of a paper.
