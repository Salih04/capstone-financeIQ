# OWNER DECISION ADDENDUM

**Owner: Salih | Decision and evidence-check date: 2026-10-26.** Explicit owner
instruction in this implementation session, continuing FINANCEIQ-2
(`6acad10e-7ca4-83eb-a5da-0e717846e484`), is the authority. Decisions take effect
in this local commit, never retroactively; publication/integration is pending.
Research support only; not investment advice.

**Exact evidence.** Fresh fetch and remote-ref check: main
`b2b3153651b19aa5c21ffc2a36a40f4bf1efc32f`; GitHub confirms [PR #54](https://github.com/Salih04/capstone-financeIQ/pull/54)
squash-merged there. At that base: [Charter](../process/RESEARCH_CHARTER.md),
[task cards](../process/TASKS_FINANCEIQ_2026-10-07.md) FIQ-06/07/11/12/17/19-25,
and [Paper 2 design](../paper2/DESIGN.md). Local, clean, byte-verified candidates:
U (absent from main) = `docs/research/UNIVERSE_RULE.md` at
`8093ec0f54d80df31c50e3a806b06b0fb2f2a096`, branch
`codex/fiq-06-remediation-r14-20261024`;
P (absent from main) = `docs/research/PROTOCOL.md` at
`1463425ae1c4ea592a9e6efc3a1a26ca6810137b`, branch
`codex/fiq-11-remediation-r7-20261022`.
Neither candidate file is on this main; local evidence is not remote publication.
Relevant clauses: U §3.4, §9.4-9.10; P §0.5, §1.1-1.4, §4.3-5.3, §7.2, §10.1-10.2.

## FIQ-06: v1.0.0 - PARTIAL/SCOPED ADOPTION

Only the following **APPROVED rules** are adopted as the scoped v1.0.0 subset.
This explicit owner scope amendment replaces U §9.5's whole-draft adoption
sequence only for this subset: R14 as a whole is **NOT APPROVED**, FIQ-06 is
**NOT COMPLETED**, and no R15 or additional approval round is required here.

| U decision | Adopted rule |
|---|---|
| B2 | Formation-based documented explained-revision candidate, U §3.4 steps 5-7: for each formation date, one consistent static or nondecreasing running reading across later copies, using evidenced event chronology; never replace the formation state with a later state. Unknown chronology, incompatible or unexplained differences fail closed. |
| 6(c)-A | Require scoped first-party completeness/retention evidence **and an auditable negative search**, covering required channels, intervals/classes, found-copy reconciliation, pagination/caps, parsing and stopping/completeness limits. Establish both empty-channel absence and absence of further copies on positive channels. Search alone, incomplete/contradictory evidence or missing retention proof cannot establish absence. |
| 20(a)1 + (b)ii | M5/M6 suffice if M7 is not evaluable; when evaluable, M7 mismatch still fails. M7's predecessor anchor must have been admitted. M8 bulletin route/OD-18 and its conditional EV-4 requirement are moot under this choice; no bulletin evidence is asserted. |
| 21 | Owner's **21-A semantic choice**: primary equality uses evidenced identity equivalence; literal text equality is sensitivity. U §9.6 calls equivalence **B**, not A: the explicit semantic choice here controls. Require first-party-backed, effective-date-valid Kernel mappings, unambiguous equivalence and collision handling; never infer aliases. Missing mapping/collision definitions block the affected operation. |
| 22-B | Earliest publicly evidenced, content-compatible first-party copy establishes timing; preserve all copies, chronology, range/table agreement, completeness and downstream predecessor effects. Unknown publication order or incompatible content never silently passes. |
| 23-B | Evaluate **all labels** before propagating deficient-label effects; no premature inventory-wide block from the first unread label. After evaluation, deficient labels affect all candidates, with known duplicates global and unresolved labels fail-closed. If completeness or propagation semantics remain undefined, affected M0.6/adjacency operations stay blocked. |

**OPEN/BLOCKED:** OD-7(b)/16/17/19; OD-1/2/3/9/10/13 and §7.4 (U2);
OD-4/14/15 (feasible window); OD-8(a)/EV-3 classification vocabulary/mapping.
Other unapproved choices remain unresolved and fail closed. No exact-100 rule
is inferred from the Charter; no EV-3 mapping, source evidence, feasible window
or research-ready universe is created. The full card's acceptance criteria
remain outstanding. Approved rules whose required definitions/evidence are
missing remain **approved as rules, operationally blocked**.

## FIQ-11: approved dispositions only

P R7 is **NOT adopted as a whole**. The decisions below supersede only their
named draft alternatives; they neither register a study nor unlock data.

| P decision | Approved disposition |
|---|---|
| OD-1 = B | Only aggregate metadata counts in protected periods: U1 member count per formation date; identity coverage; eligible KAP filing-event count; distinct event-date count per quarter. Use only authorized membership/identity/filing metadata with access checks and immutable lineage. No exposed individual rows, joins or indirect leakage; no price presence/coverage, suspension/delisting details, prices, returns or outcomes. Undefined eligibility, coverage denominator, output or safe aggregation means fail closed. This is no unlocked protected-data read. FIQ-20 price pilot is development-only. |
| OD-2 = B | One confirmatory opening per study, bound to immutable study identity and a cross-study exposure ledger; amendment/re-registration cannot reset it. No authorization of multiple window openings or interim looks. |
| OD-3 = B | A properly preregistered **clean forward holdout**, with explicit exposure/claim status, can sustain predictive claims despite contaminated or blocked historical locked holdout; Charter §5 rule 4 receives one clarifying sentence. Forward dates alone never prove cleanliness. Paper 2 concerns association; this claim option chiefly affects Study 3. |
| OD-4 = A | Locked-outcome refitting remains disallowed; reconsider at FIQ-24, with no permission granted now. |
| OD-5 = B | Bind a demonstrated non-leakage argument to the LLM version, target and use, or label exploratory; UNKNOWN cutoff never auto-passes. |
| OD-6 | (a) Exclude boundary-band observations (`e_i <= 2022-12-31 < b*_min,i <= 2025-12-31`); (b) no secondary confirmatory use; (c) benchmark/expected-return estimation-window data ending **before** the outcome interval do **not** enter event outcome dependency `D_i`. Retain PIT/as-of, prediction-time, training-only fitting, purge/embargo and other leakage checks; no automatic event eligibility. |
| OD-7 = B | FIQ-17 protected 2023-2025 U1 outcome calculations only **after BOTH Paper 2 AND Study 3 confirmatory openings**, and only with FIQ-17's own applicable OSF record, committed spec, ledger and access gates. Development work is otherwise permitted under its prerequisites; this task authorizes no execution. |
| OD-8 = A | No narrowing of project-wide protected classes. |

**I-item dispositions (P §10.2).** L = **LEFT UNRESOLVED**, no wholesale
confirmation; fail closed where needed. R = **REPLACED only in the named scope**,
with all remaining content LEFT UNRESOLVED.

| Item | Disposition | Item | Disposition |
|---|---|---|---|
| I-1 | L | I-9 | L: historical selection correction remains gated |
| I-2 | L | I-10 | L |
| I-3 | L | I-11 | L |
| I-4 | R: OD-6 only | I-12 | L: no clean-status algorithm adopted |
| I-5 | R: OD-1/8 only | I-13 | L |
| I-6 | L | I-14 | R: FO-0 freeze below only |
| I-7 | L | I-15 | L |
| I-8 | L | I-16 | L: no extra opening/look granted |

**Freeze/history.** FO-0 boundaries froze **2026-10-09**, verified local commit
`292674c55275a7c8b1430b3de6468e58a903a479`; no separate first-evaluation freeze
is invented. Preserve every prior U1 evaluation, including unauthorized,
failed/abandoned trials and exposures, in append-only trial/exposure records,
with occurrence versus discovery/recording dates; never backdate authorization
or assume an empty inventory. Inventory completeness is **UNVERIFIED**.

**Preserved limits.** Frozen Capstone v1; accepted U1/survivor inclusion; FO-0
development through 2022-12-31, locked 2023-2025 and post-registration forward;
Paper 2's 2026-to-actual-OSF quarantine and approved D3/D5/D9 remain unchanged.
D6/30-cluster threshold remains unapproved; OD-1 does not authorize every RQ3
feasibility output (including issuer/session-cluster outputs). D9 does not erase
historical trials or silently enlarge its approved family. Missing stays null.
FIQ-12's merged inert core is not an operational access grant. This documentation
performs no counts, protected reads, outcome work, model/simulation, OSF action
or Kernel change/transfer. Required context contained legacy aggregate summaries;
no zero-prior-exposure claim is made.
