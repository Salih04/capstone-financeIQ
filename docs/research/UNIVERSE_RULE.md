# FIQ-06 — operational U1 rule

Owner decision: **2026-11-03 21:24:35 Europe/Zurich**. Queue 3 / Paper 2 G02.
Version **2.0.0 · OWNER-ADOPTED U1 RULE · NO EXECUTION AUTHORITY**.
Research support only; not investment advice.

## 1. Authority and adoption boundary

Read against live main `90d10f7c388c45bf41b7a9e5e5f5204a9de51b6d`:
[Charter §4–5](../process/RESEARCH_CHARTER.md),
[2026-10-26 scoped v1.0.0 adoption](OWNER_DECISION_ADDENDUM.md), and
[FIQ-06 card](../process/TASKS_FINANCEIQ_2026-10-07.md#fiq-06--u1u2-evren-kuralı-tasarımı).
The owner decision recorded 2026-11-03 21:24:35 Europe/Zurich adopts this exact
U1-only rule version 2.0.0 with the completeness and G03 amendments below. The
owner-fixed 3184 tier semantics and quarterly 30/20/50 validation are retained;
no new workbook inspection, BIST archive search or empirical count is claimed.

Historical R14 `8093ec0f54d80df31c50e3a806b06b0fb2f2a096` is evidence,
not adopted wholesale. Its source/admission machinery is not imported by
reference as an implicit executable dependency. This compact candidate defines
U1 only, preserving the adopted safeguards below. A major candidate version
distinguishes its material operational choices from the scoped v1.0.0 record.
No earlier rule, decision, formation or exposure record is rewritten.

The owner adopts this exact U1-only specification with the stated amendments,
while leaving U2, G03 mapping evidence and joint KAP/price feasibility as separate
gates. This rule adoption does not complete FIQ-06/U2, establish underlying data
adequacy, or authorize source access, formation, analysis or execution. The
append-only owner addendum records the actual Git adoption commit and exact rule
blob/content digests. Research use also requires lawful immutable inputs, a
reviewed consumer implementation, and study-specific registration/access gates.
Missing source evidence blocks a formation; it is not represented as an
unspecified algorithm or presumed complete source.

## 2. Formation, state and time

For each official BIST quarterly index period P, F is its evidenced effective
start, not the download date or the first convenient trading date. Store the
official effective date and its Europe/Istanbul formation instant separately
from the first trading session. Use historical timezone rules; an unsupported
time/ordering claim fails closed. No current constituent list or capstone list
is admissible as a substitute.

Bind each 3184 block to P using a readable in-document quarter/year label and
first-party effective-period evidence. Proposed OD-7(b)/16 resolution: printed
labels for both workbook blocks and announcement index tables; no filename,
sheet position or download metadata alone. An ordinal quarter label plus an
evidenced workbook year can bind only to the matching official quarter; a dated
label must agree with the evidenced period start. Missing year, conflicting or
duplicate labels, unexplained first-session/date mismatch or unknown layout
fail closed. No tolerance is silently introduced.

A later downloaded copy may establish an earlier state only through the adopted
B2 explained-revision rule and public-copy chronology, never by replacing the
formation state with the latest observed state. Earliest publicly evidenced,
content-compatible first-party copy establishes timing (adopted 22-B); preserve
every copy and its chronology. Incompatible content or unknown ordering fails.
The content-compatible public announcement's evidenced publication upper bound
must be strictly before F. A later 3184 retrieval may corroborate the historical
formation state but cannot retrospectively create a pre-F public announcement
or make a later membership decision eligible at F.

## 3. Narrowest-tier mapping — owner-fixed semantics

After deterministic lexical normalization (trim outer whitespace, preserve raw
cell text, canonical uppercase index code), retain one tier per source share row:

| Narrowest cell | In XU030 | In XU050 | In XU100 |
| --- | --- | --- | --- |
| XU030 | true | true | true |
| XU050 | false | true | true |
| XU100 | false | false | true |
| Other evidenced valid tier / evidenced empty non-member cell | false | false | false |
| Unreadable/missing parse or unknown vocabulary | null | null | null |

Thus `is_xu100 = cell in {XU030, XU050, XU100}` for an established cell.
Literal `cell == XU100` is **not** the BIST 100 universe. Null is an evidence
failure, never a false membership fact or a fill from another quarter.

Validate **each quarter independently**, at canonical security identity:
exactly 30 narrowest XU030 + 20 narrowest XU050 + 50 narrowest XU100 = 100.
Also validate nested set sizes 30/50/100 and subset relations. These are
validation requirements, not measured results. Wrong counts reject the entire
formation; never top up, truncate, sample or infer missing members. A passing
100 count cannot prove correct identities, quarter binding or timing.

Use adopted identity equivalence (21-A semantic / R14 alternative B), supported
by first-party-backed Kernel mappings valid at the operation's effective date.
Retain source codes and mapping IDs/hashes. Never guess from names or today's
tickers. Duplicate source rows, mapping collisions, contradictory tiers or
unresolved security/issuer/share-class identity fail the affected formation;
no silent deduplication to manufacture 100. Literal-code equality is a labelled
sensitivity only. Multiple officially distinct securities of an issuer remain
distinct; do not replace the index's security population with unique issuers.

## 4. Admission algorithm and adopted cross-checks

Evaluate all inventory period labels before propagating failures (adopted 23-B).
Known duplicate labels are global conflicts. Any deficient label can affect all
candidates under the adopted global policy; evaluate all labels and report
every cause, rather than stopping at the first unread one.

For a candidate (P,F), perform these ordered tests; retain all evaluated flags
and distinguish NOT EVALUATED from evaluated failures:

1. Scope source completeness to the two first-party channels used by U1:
   (a) record 3184 workbook completeness/retention evidence for the required
   quarter blocks, including the scope and limitations of the workbook channel;
   (b) record each BIST announcement-archive search date, exact query, result
   count, pagination/caps and found-copy reconciliation. Preserve source identity,
   period ranges, copy register and publication bounds. This is not universal
   proof that no other copy exists and must not be described as such. Do not infer
   absence from a zero-hit query or an unsearched/unretained channel. Unknown
   in-scope completeness fails closed. This U1-specific scope applies the adopted
   6(c)-A rule only to the two channels used; it does not establish that either
   channel was searched or complete.
2. Bind workbook/announcement labels and identities under §§2–3. Reject
   incompatible copy ranges/tables or unexplained revisions. Under B2, an
   admissible formation reading is static across copies or evolves only by
   a nondecreasing chronology of evidenced events. Apply those events to the
   same initial state and require every observed copy state to agree with its
   evidenced stage. Unknown publication stage or unexplained difference fails.
   Multiple distinct admissible formation states fail; no favorable-copy choice.
3. Construct S at F with §3's tier union, identity rules and all three count
   checks. Preserve workbook hash, sheet/row/column and raw tier for every member.
4. Identify BIST 100 periodic ADD/REMOVE sets and all evidenced same-day and
   own-period changes. Reserves are not members unless an evidenced event
   consumes them. Missing incoming identity or unresolved effective sequence
   fails any operation that needs that resulting state; never guess reserves.
5. Proposed OD-19 resolution: S is the effective start state including
   non-integrated events effective on F. Let IN0/OUT0 be those evidenced events
   not already incorporated in the periodic table. Require
   `(ADD ∪ IN0) − OUT0 ⊆ S` and `((REMOVE ∪ OUT0) − IN0) ∩ S = ∅` (M5).
   Integration status must be evidenced. For simultaneous events, use a
   first-party sequence or prove the resulting state and all applicability
   checks invariant under every possible ordering; otherwise fail closed.
6. From S apply own-period events strictly after F (M6): each outgoing member
   must be present and each named incoming member absent before its change.
   No outgoing-present/incoming-absent contradiction is allowed to pass as
   a start-of-period state. An unnamed final incoming state may support only
   the preceding applicability check, not subsequent state reconstruction.
7. M7: when a fully admitted predecessor is available and the complete ordered
   intervening events are evidenced, reconstruct F from that predecessor,
   periodic changes and non-integrated same-day events. Require identity-set
   equality with S; mismatch fails. Record NOT EVALUABLE and its exact reason
   otherwise. Adopted 20(a)1+(b)ii permits M5/M6 to suffice when M7 cannot be
   evaluated; an evaluable mismatch never becomes NOT EVALUABLE to escape it.
   No bulletin/M8 corroboration route or new bulletin-rights gate is introduced.

Failing any required test records an excluded formation and reason. For
diagnostic reproducibility, reason codes include `SOURCE_COMPLETENESS_UNKNOWN`,
`PERIOD_LABEL_CONFLICT`, `BLOCK_UNBOUND`, `COPY_REVISION_UNEXPLAINED`,
`CELL_UNKNOWN`, `TIER_COUNT_MISMATCH`, `IDENTITY_COLLISION`,
`ANNOUNCEMENT_DISAGREE`, `EVENT_ORDER_UNRESOLVED`, `STATE_TIMING_CONFLICT` and
`CHAIN_MISMATCH`; multiple causes are retained with the first failed step.
These codes do not establish source absence or economic nonexistence.

## 5. Following members and strata

Once admitted at F, preserve all formation rows through each study's declared
holding/event window, including exits, suspension, merger and delisting. Intra-
quarter entrants join at the next quarterly formation. Exit is not a drop rule.
An unknown terminal value is null with a reason, never zero or a fabricated
continuing price. Missing outcomes can make an analysis unavailable without
retroactively changing membership.

Keep non-financial primary and financial separate; holdings flagged. At G03,
derive the financial/non-financial stratum only from the KAP financial-statement
template evidenced through the KER-13b route: bank, insurance, or standard TFRS.
Determine holdings status through that same route; if it does not resolve the
status, preserve UNKNOWN/null. Do not infer strata or holdings from names, current
sector labels, the capstone cohort, or other proxy fields. KER-13b template
evidence has not been received here, so G03 and underlying stratum adequacy remain
blocked; this rule does not claim otherwise.

## 6. Output contract, window and adoption record

FinanceIQ's consumer output has one row per `(formation_effective_date,
entity_id, security_id)`: source tier/code, nested membership flags, inclusion
reason, nullable stratum/holding flag, membership/announcement document IDs,
effective range, source-publication bounds and precision, acquisition time,
raw content hashes, source locators, identity-map version/hash, snapshot contract
and hashes, rule version/content hash/Git blob, builder commit and timezone DB
version. Acquisition/publication/effective times are never conflated. The
private source-evidence record retains full chronology; public release requires
its own rights/output clearance, never raw redistribution by default.

Candidate study window is a precommitted list of quarterly periods, not the
earliest/latest dates chosen after looking at price coverage. Missing membership
evidence excludes/counts dates with reasons. Joint KAP/price coverage predicates
and threshold/window endpoint decisions (OD-4/14/15) remain **UNSET**, not waived
or declared established by this U1-only scope proposal. Protected metadata
counts require the exact adopted OD-1 boundary and separate access checks;
price coverage/lifecycle joins are not within the four permitted aggregates.
No feasibility counts, source observations or outcomes were read here.

The append-only [owner decision addendum](OWNER_DECISION_ADDENDUM.md) records the
owner decision timestamp and provenance separately from the actual Git adoption
timestamp, the accepted rule commit, blob SHA, SHA-256 digest of the exact rule
bytes, effective version, U1-only scope, amendments and remaining G03/U2/window
gates. Preserve adopted B2/6(c)/20/21/22/23 safeguards and prior evaluation/
exposure history, including UNKNOWN completeness; do not invent an empty history.

One review and at most one fix round for this rule; self-checks do not
replace independent scientific acceptance. Adoption and running a study are
distinct. This is a FinanceIQ rule/consumer contract only: no Kernel planning,
implementation, source acquisition, count result feedback or Kernel write is
authorized by this U1 rule.
