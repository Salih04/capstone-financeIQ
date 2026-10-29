# Paper 1 scientific-readiness audit

Lane **PAPER1-SCIENTIFIC-READINESS**, checked **2026-10-29**, Europe/Zurich.
Research support only; not investment advice. Agent-prepared documentation
audit: **not independent scientific review, not approval, not a submission.**

## Exact base

| Item | SHA / state |
| --- | --- |
| Fresh `origin/main` (fetched 2026-10-29) | `efe3ed32ca958074c01ee9488f1f768a9d812c61` |
| FIQ-15 candidate reviewed | `4b6c88237e38bc240b864b04548eef67bdec5549`, branch `codex/fiq-15-manuscript-20261027`; **not merged** (not an ancestor of main) |
| Its prerequisite | `7b444a35298f7b04012d818ff70fcbc57b85d6b3` (FIQ-16/13/14), not merged |
| This branch | `local/paper1-readiness-audit-ebc214`, fast-forwarded from main to the candidate as an explicit local prerequisite, the same pattern FIQ-15 used for `7b444a35` |

If FIQ-15 is amended or rejected, this audit refers to the bytes at
`4b6c8823` and must be rechecked.

## Authority and scope

Live owner instruction of 2026-10-29 (continuing FINANCEIQ). Read: global
workflow v2.1 and FinanceIQ context (both dated 2026-10-14, read-only),
root/process AGENTS, Research Charter (adopted, FO-0 approved), owner decision
addendum of 2026-10-26, task cards FIQ-13 to FIQ-17.

Owned paths: `docs/paper1/readiness/**` only. The FIQ-15 draft, PDF,
crosswalk, bibliography and FIQ-16 files are unchanged. No PIT code, U1,
research core, Paper 2, CI or security file is touched.

Outcome numbers were checked only against `RESULTS.md` and the exact
`experiments/results_pit_v2/REPORT.md`. Details and the full read list are in
[claim_audit.md](claim_audit.md).

## Deliverables

| File | Content |
| --- | --- |
| [claim_audit.md](claim_audit.md) | Claim-by-claim verification, crosswalk re-check (38 records, 62/62 excerpts), gap register G-1 to G-9 |
| [reviewer_objection_matrix.md](reviewer_objection_matrix.md) | 20 anticipated objections with severity, existing answer, residual gap |
| [editorial_corrections.md](editorial_corrections.md) | Eleven bounded, source-backed edits E1-E11 and items deliberately not changed |
| [draft_corrections.patch](draft_corrections.patch) | The edits as a unified diff against the candidate draft; **not applied** |
| [scope_proposal.md](scope_proposal.md) | Options A (existing-evidence bounded audit), B (wait for FIQ-17), C (both); owner choice UNSET |
| [submission_readiness.md](submission_readiness.md) | BIR/JAM requirements as verifiable on 2026-10-29, declarations, references, rights |

## Main findings

1. Every number in the draft matches its authorized source; the 38-note
   crosswalk is intact and pinned.
2. Disclosure gaps, all fixable by wording from existing sources: the
   feature-set change (40 → 38) is missing from the "bundled correction" list;
   pre-registration knowledge (+0.005, +0.193, price inspection, near-zero
   PIT-safe reruns) is understated; the ±25 % jump rule was set after price
   inspection; the corrected FY2024 window overlaps the 2026 forward window;
   the analytic MDE (0.185) and harness detection (17 % at IC 0.2) are not
   reconciled; IAS 29 basis change from FY2023 is not discussed.
3. Gaps existing sources cannot close: market-value categories sum to 319 of
   323; MDE α/sidedness; timing of exploratory reruns; complete trial count;
   vendor identity and rights; FO-1 provenance.
4. Not submission-ready for any venue: no AI declaration, data statement,
   anonymization or venue reference style; BIR's guide could not be read.
5. Selection effect remains NOT RUN and UNKNOWN; nothing here estimates it.

## Owner decisions (none taken here)

| Decision | Options |
| --- | --- |
| Publication scope | A / B / C in [scope_proposal.md](scope_proposal.md) — UNSET |
| Apply E1-E11 | All, some, none; then regenerate or withdraw `draft.pdf` |
| Venue | BIR, JAM or other (FIQ-14) — UNSET |
| FO-1, FO-4 | Selection statement; rights review before a data statement |
| G-1, G-4, G-6 | Statements from the registered run record, if the owner chooses to close them |
| Independent review | Who reviews (charter §5 rule 9) |

## Verification actually performed

All on 2026-10-29 at this branch before commit:

- Crosswalk re-check (scratch script, not committed): 38/38 records,
  62/62 pinned excerpts and file digests match — PASS.
- `git apply --check docs/paper1/readiness/draft_corrections.patch` against
  the candidate draft — PASS. Patched scratch copy: 38 notes still cited, no
  anchor missing, NOT RUN/UNKNOWN/placeholder/registration-SHA counts
  unchanged, reference list byte-identical, every heading and table row kept —
  PASS. Every added number/date/phrase found in its cited note excerpt — PASS.
- Local-link check of `docs/paper1/readiness/*.md` — PASS (0 broken).
- `make docs-lint` — PASS. `make claims-lint` — PASS (Model Confidence
  Contract v1.10.0). Neither linter scans this nested folder's prose.
- `git diff --cached --check` — PASS after scoping `*.patch -whitespace`
  in this folder's `.gitattributes` (diff format, not prose whitespace).
- Root suite after the commit: reported in the lane's final report, not here.

Static checks only. They show transcription and consistency, not scientific
validity. No application, data or model pipeline was run.
