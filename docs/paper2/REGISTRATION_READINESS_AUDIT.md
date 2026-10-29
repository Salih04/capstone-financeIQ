# Paper 2 — registration-readiness audit

**Lane PAPER2-REGISTRATION-READINESS (owner audit items A14/A18) · 2026-10-29 · NOT REGISTERED · NOT REGISTRATION-READY**

Research support only; not investment advice. This audit reconciles the Paper 2
design ([DESIGN.md](DESIGN.md)) and OSF draft ([OSF_PREREGISTRATION_DRAFT.md](OSF_PREREGISTRATION_DRAFT.md))
with owner decisions **already adopted** on main. It makes no scientific choice,
sets no hypothesis, sample count, threshold, cluster rule, power or result,
submits nothing to OSF, opens no holdout, runs no code that computes outcomes and
inspects no real dataset, PIT Kernel snapshot or contract. Every decision not
adopted is listed as **UNSET / NEEDS-DECISION** (§8), not resolved.

Labels follow the global workflow: VERIFIED (direct evidence, cited), REPORTED
(inherited, not rerun), INFERRED (stated assumption or mechanical consequence),
UNVERIFIED, BLOCKED, NEEDS-DECISION.

## 0. Evidence base

| Item | Exact reference | Status |
|---|---|---|
| Main at audit start | `efe3ed32ca958074c01ee9488f1f768a9d812c61` (PR #55), fetched 2026-10-29; worktree branch `local/paper2-registration-audit-c66bbe` was at the same commit | VERIFIED |
| Paper 2 v0.2 as landed | `b2b3153651b19aa5c21ffc2a36a40f4bf1efc32f` (PR #54), committed 2026-10-26 13:59:41 +0100, parent `4b029ef4` (PR #53) | VERIFIED |
| Owner decision addendum | [OWNER_DECISION_ADDENDUM.md](../research/OWNER_DECISION_ADDENDUM.md), landed in `efe3ed32`, committed 2026-10-26 14:56:27 +0100; its evidence base was `b2b31536`, so it postdates and cites Paper 2 v0.2 | VERIFIED |
| Charter | [RESEARCH_CHARTER.md](../process/RESEARCH_CHARTER.md): adopted 2026-10-07; FO-0 2026-10-09 (`292674c5`); §5 rule 4 owner clarification 2026-10-26 | VERIFIED |
| Task cards | [TASKS_FINANCEIQ_2026-10-07.md](../process/TASKS_FINANCEIQ_2026-10-07.md) §4 FO-7, §5.6 FIQ-19/20/21/22; FIQ-06/FIQ-11 notes added in `efe3ed32` | VERIFIED |
| FIQ-06 candidate U | `docs/research/UNIVERSE_RULE.md` at `8093ec0f` (R14) — local commit, **absent from main** | VERIFIED (local object) |
| FIQ-11 candidate P | `docs/research/PROTOCOL.md` at `1463425a` (R7) — local commit, **absent from main** | VERIFIED (local object) |
| FIQ-12 inert core | [experiments/research_core/README.md](../../experiments/research_core/README.md) (PR #53): `require_protected_access` always denies; no policy, schema or unlock | VERIFIED |
| Study template | [STUDY_RECORD_TEMPLATE.md](../process/STUDY_RECORD_TEMPLATE.md) | VERIFIED |
| Owner context files | `AI_PROJECT_CONTEXTS/GLOBAL_AI_WORKFLOW.md` (v2.1, 2026-10-14) and `FinanceIQ_AI_CHATGPT_CONTEXT.md` (snapshot 2026-10-14, main `47f06a28`) — outside this repository and **stale** relative to `efe3ed32` (§3, F-12) | VERIFIED (read) |

Candidate files U and P were read only for the sections the addendum names and
for their definitions of `D_i`, `e_i`, `b*_min,i`, the window classes and the
I-items. Their text is **not adopted**; only the addendum's dispositions are.

## 1. Adopted owner decision → Paper 2 reconciliation

"v0.2" = text at `b2b31536`; "v0.3" = this lane's edits. DESIGN/OSF line numbers
refer to v0.2 at `b2b31536`; addendum lines to `efe3ed32`.

### 1.1 Charter and FO-0

| Adopted decision (source) | Paper 2 v0.2 | v0.3 action | Residual status |
|---|---|---|---|
| FO-0 boundaries: development ≤ 2022-12-31; locked 2023-01-01..2025-12-31; forward = published after OSF registration (Charter preamble, §5 rule 7) | OSF L111-113 preserves verbatim | Unchanged | VERIFIED consistent |
| FO-0 freeze date 2026-10-09, `292674c5`; no separate first-evaluation freeze (addendum L78-84) | Not stated | Recorded in OSF boundaries | VERIFIED |
| U1 rule, survivor inclusion, fail closed (Charter §4) | DESIGN L33-37 | Unchanged; operational version still UNSET (§1.3) | Consistent |
| Locked holdout semi-clean (Charter §5 rule 7) | OSF L119-120 | Unchanged | Consistent |
| §5 rule 4 clarification: pre-registered clean forward result may support a predictive claim (addendum OD-3 = B) | Not reflected | OSF: noted; Paper 2 claims are associational, so the clarification does not widen Paper 2 claims | Consistent |
| IAS 29 must be addressed by the protocol (Charter §5 rule 7) | DESIGN D5 (owner-approved) | Unchanged | Operational evidence UNVERIFIED (G08) |
| Every trial counts (Charter §5 rule 6) | OSF L162-168, L183-196 | Unchanged; I-9 status added | N UNSET (G15) |
| Independent review for analyses that enter a paper (Charter §5 rule 9) | OSF gate 3, 5 | Unchanged | Not done (G21) |

### 1.2 FIQ-11 protocol dispositions (addendum L50-61, L63-76)

| Decision | Adopted disposition (summary) | Paper 2 v0.2 | v0.3 action | Residual |
|---|---|---|---|---|
| OD-1 = B | Only four aggregate metadata counts in protected periods; no price presence/coverage, rows, joins, prices, returns; undefined eligibility fails closed; FIQ-20 price pilot development-only | OSF L122-125 lists OD-1 as unresolved; DESIGN L198-207 / OSF L62-69 require "separately authorized" RQ3 counts | OSF/DESIGN state OD-1 = B; RQ3 issuer/session-cluster and basis-label counts are **not** among the four permitted aggregates (addendum L88-89); FIQ-20 development-only | RQ3 eligibility UNVERIFIED; owner gate G09 |
| OD-2 = B | One confirmatory opening per study, bound to immutable study identity and cross-study exposure ledger; no reset by amendment; no extra openings or interim looks | OSF L122-126 unresolved; D9 stopping already "one fixed terminal analysis" | Stated in OSF boundaries and stopping | Which window that single opening uses is D1, UNSET (G01); ledger location UNSET (G18) |
| OD-3 = B | Clean pre-registered forward holdout can sustain predictive claims; dates alone never prove cleanliness | OSF L126 unresolved | Stated; association claims only | No clean-status algorithm (I-12 L) |
| OD-4 = A | No refitting on locked outcomes | OSF L127-128 "require disposition if proposed" | Stated as disposed; Paper 2 proposes no refit | Interpretation note G25 |
| OD-5 = B | LLM use needs a bound non-leakage argument or is exploratory; UNKNOWN cutoff never passes | OSF L127-128 | Stated; binds D7 coding if an LLM is ever used | No LLM use registered |
| OD-6 (a)(b)(c) | (a) exclude band `e_i <= 2022-12-31 < b*_min,i <= 2025-12-31`; (b) no secondary confirmatory use; (c) estimation-window data ending before the outcome interval are not in `D_i`; all other leakage checks retained | OSF L131-140 "conservative primary: keep estimation-window information in event lineage … pending OD-6 … Neither policy is approved" | **Stale text replaced** by the adopted disposition; v0.2 conservative primary marked superseded; no band sensitivity re-introduced | Per-target `D_i` definitions UNSET (G16); straddle/correction rules (G17) |
| OD-7 = B | FIQ-17 protected outcomes only after both Paper 2 **and** Study 3 confirmatory openings | OSF L128-129 "OD-7 concerns FIQ-17" | Stated as downstream dependency on Paper 2's opening | Informational (G24) |
| OD-8 = A | No narrowing of project-wide protected classes | OSF L125 unresolved | Stated | Consistent |
| I-1, I-2, I-3, I-6, I-7, I-8, I-10, I-11, I-13, I-15 = L | Left unresolved; fail closed where needed | Not itemised | Listed in OSF; each relevant one mapped to a gate | G17, G19, G22, G23 |
| I-4 = R (OD-6 only) | Band rule replaced only as OD-6 | — | As OD-6 | — |
| I-5 = R (OD-1/8 only) | Exemption content only as OD-1/OD-8 | — | As OD-1/OD-8 | Other exemption rows unresolved |
| I-9 = L | Historical selection correction remains gated | D9 "reconcile prior configurations" | Stated: reconciliation cannot close while I-9 is unresolved | Blocks claims (G15) |
| I-12 = L | No clean-status algorithm adopted | OSF L119-120 semi-clean | Stated | G23 |
| I-14 = R | FO-0 freeze 2026-10-09 only | — | Recorded | — |
| I-16 = L | No extra opening or look | Consistent with D9 | Stated | — |

### 1.3 FIQ-06 scoped v1.0.0 (addendum L19-46)

| Item | Adopted / open | Paper 2 relevance | v0.3 action |
|---|---|---|---|
| B2, 6(c)-A, 20(a)1 + (b)ii, 21-A semantic, 22-B, 23-B | Adopted as rules; "approved as rules, operationally blocked" where definitions/evidence are missing | U1 membership admission only. 22-B (earliest content-compatible copy) concerns membership announcements and is **not** transferred to KAP financial-statement event timing (D2) | Universe field cites "scoped v1.0.0 subset, operationally blocked" |
| R14 as a whole, FIQ-06 completion | NOT APPROVED / NOT COMPLETED | No operational U1 version exists | Universe version stays UNSET |
| OD-4/14/15 (feasible window) | OPEN/BLOCKED | Paper 2 study period cannot be fixed from U1 feasibility | G01/G02 |
| OD-8(a) + EV-3 (strata mapping) | OPEN/BLOCKED; strata stay UNKNOWN | Paper 2's primary non-financial stratum cannot be populated | G03 |
| OD-7(b)/16/17/19 | OPEN/BLOCKED | Formation-date admission | G02 |
| U2 decisions | OPEN/BLOCKED | Paper 2 does not use U2 | None |

### 1.4 Paper 2's own decisions (DESIGN §5, owner 2026-10-26)

Unchanged by this audit. Addendum L85-89 confirms "approved D3/D5/D9 remain
unchanged" and "D6/30-cluster threshold remains unapproved".

| ID | Adopted part | Still UNSET |
|---|---|---|
| D1 | Quarantine 2026-01-01 → actual OSF registration (DESIGN L303-309); FIQ-11 dispositions now bind (§1.2) | Scope, operational U1 version, strata, which protected window the single opening uses, event-publication start/end, observation end |
| D2 | CAR[-1,+1] is a wider-window sensitivity | Primary window, session-0 rule, calendar source, timestamp precision |
| D3 | CPI seasonal expectation, quarter-end MV primary; drift/SUE diagnostics only | CPI series ID, reference-month mapping, vintage policy, share source, stale-price rule |
| D4 | Rate fallback priority 2y yield → EVDS benchmark → policy rate; outcome-blind selection | All source IDs, risk-free conversion, estimation window/minimum (proposed), flow scaling |
| D5 | Filing-metadata basis, transition exclusions, no CPI bridge, conditional 2025Q1, RQ3 eligibility rule | Basis-metadata availability, same-basis asset-scaled sensitivity |
| D6 | — | Whole decision (two-way clustering, 30-cluster floor, KP test, calendar-time, calibration criteria) |
| D7 | — | Whole decision |
| D8 | Common shift per repetition, event-level collisions, no outcome-driven shift selection | Seed, number of offsets (proposed 100), negative-control window |
| D9 | RQ1 beta + eligible RQ3 delta, two-sided Holm; RQ1 alone if RQ3 excluded before registration | Alpha (proposed 0.05), stopping dates, prior-trial reconciliation |
| D10 | OD-2 ledger binding now adopted | Source manifest, rights/vintages, exposure assessment, execution gates |

## 2. Mechanical consequences of adopted text (INFERRED, no counts)

These follow from adopted rules applied to the design's proposed windows. They are
rule consequences, not empirical findings; no event, date or count was inspected.

1. **OD-6(a) is per target.** `D_i` differs by window. For CAR[0,+1], `D_i` starts
   at close[-1]; an event whose close[-1] falls on or before 2022-12-31 and whose
   window completes in 2023 is band and excluded. For CAR[-1,+1] (close[-2]) and the
   negative control CAR[-20,-11] (close[-21]) the band reaches further into 2023, so
   diagnostic samples can differ from the primary sample near the boundary.
2. **OD-6(c) removes the estimation window [-250,-31] from `D_i`.** v0.2's warning
   (and candidate P §1.3's "known impact while OD-6 is open") that most 2023 events
   fall in the band no longer applies to the expected-return estimation window.
   Access to estimation-window returns dated in a protected window remains a
   protected-window touch; OD-6(c) changes classification only.
3. **Undecided `D_i` membership.** Whether in-window factor realizations, the
   eight-release flow-scaling history and the surprise inputs (E_q, E_(q-4), MV_q,
   CPI) belong to `D_i` is not settled by adopted text. Narrow and wide readings
   change which early-2023 events are band. This is NEEDS-DECISION (G16), and the
   choice must be outcome-blind and registered.
4. **Quarantine edge.** An observation whose `D_i` contains any record originally
   published on or after 2026-01-01 (for example a late-December 2025 event whose
   close[+1] is in January 2026, or a 2026 correction) depends on quarantine data.
   Paper 2's approved quarantine grants no access, so such an observation cannot be
   evaluated as locked holdout; candidate P's observation-level table (I-1/I-3)
   is unadopted. Fail closed and count from dates only once counting is authorized
   (G17).
5. **2025 annual and Q4 releases.** A fiscal-2025 event first published on or
   after 2026-01-01 is in the quarantine interval by its publication time, whatever
   its fiscal period. Combined with D5's conditional 2025Q1 start and the 2024
   transition exclusions, the IAS 29 side of RQ3 inside the locked holdout is at most
   the 2025 interim events published in 2025 (INFERRED, conditional on D5's stated
   history assumption; no eligibility is asserted).
6. **One opening.** OD-2 = B and I-16 = L give Paper 2 one confirmatory opening.
   A later forward confirmation of RQ3 (DESIGN L208-212) therefore requires its own
   registered study identity, as v0.2 already says.

## 3. Stale or conflicting text findings

| ID | Location (v0.2 @ `b2b31536` unless stated) | Finding | Resolution |
|---|---|---|---|
| F-1 | OSF L122-129 | Lists FIQ-11 OD-1/2/3/6/8 and OD-4/5 as unresolved dependencies; superseded by addendum L54-61 | Replaced in v0.3; history note keeps v0.2 pointer |
| F-2 | OSF L131-140 | "Proposed conservative primary" keeps estimation-window data in lineage and offers an unapproved sensitivity; conflicts with adopted OD-6(b)/(c) | Replaced; no band sensitivity |
| F-3 | DESIGN L26-31; OSF L122 | R14/R7 described only as "unadopted draft dependencies"; addendum adopts scoped subsets | Rewritten: whole drafts unadopted, named dispositions adopted |
| F-4 | DESIGN L17-20; OSF L12-15 | States base `f7b1e4f9` (PR #52); PR #54 actually landed on `4b029ef4` (PR #53) | v0.3 records the landed parent; v0.2 statement kept as preparation history |
| F-5 | OSF L234-236 | "FIQ-12 candidates do not establish adopted access controls" — FIQ-12 inert core is merged (PR #53) and denies all protected access | Reworded |
| F-6 | DESIGN L198-207; OSF L62-69 | RQ3 counts "under separately authorized outcome-free protected-coverage rules" — OD-1 = B now fixes the permitted aggregates and excludes cluster outputs | Reworded; gate G09 |
| F-7 | OSF L224-227 | FIQ-20 "separately authorized … price-existence pilot" — OD-1 = B makes it development-only | Reworded |
| F-8 | DESIGN L278 (D1 row) | "FIQ-11 boundary/exposure authority" unresolved — now partly resolved | Reworded |
| F-9 | DESIGN L337-340 | "FIQ-06 R14/FIQ-11 R7 disposition" as one dependency | Reworded to remaining open items |
| F-10 | DESIGN L184 | "KGK's 23 November 2023 announcement" — the PDF body carries no date; 23 November 2023 is its file metadata, and the date's corroboration by KGK 2024-32 is REPORTED, not rechecked | Source note added in v0.3 |
| F-11 | TASKS FIQ-19 card | Cites `docs/research/UNIVERSE_RULE.md` and `docs/research/PROTOCOL.md`, absent from main (also P §10.3 G-7) | Not edited (outside lane); reported |
| F-12 | `FinanceIQ_AI_CHATGPT_CONTEXT.md` (2026-10-14) | Shows OD-1..OD-8 open with interim states and FIQ-06 R3 / FIQ-11 R2 SHAs; superseded by addendum and R14/R7 | Not edited (outside repository and lane); owner should refresh |
| F-13 | TASKS §2 wave table vs FIQ-21 card | Wave 5 lists KER-13a for FIQ-20/21; the FIQ-21 card omits it. v0.2 followed the table | Stricter list kept and the discrepancy noted in OSF gate 2; card not edited |
| F-14 | Candidate P `1463425a` §1.1, §1.3, §10.1 | "While OD-6 is open, estimation-window data are part of `D_i`" and the open-state OD-6 table | Candidate text, not on main; addendum controls for its named scope; not edited |

No v0.2 text that the owner approved (D3/D5/D9 and the D2/D4/D8 amendments) was
altered.

## 4. Gap audit by area

| Area | Gap | Status |
|---|---|---|
| Source IDs | KAP filing row type and Kernel export; exchange calendar; prices, total returns, corporate actions, terminal proceeds; historical share counts; BIST total-return market index; TRY 2-year yield, EVDS benchmark, policy rate; USD/TRY; non-resident equity-flow series and release calendar; CPI series and vintages; risk-free series | All UNSET; rights per source UNSET (Kernel-owned); no data retrieved |
| Time rules | KAP timestamp precision/offset semantics; historical closing-auction and half-day calendars; CPI and flow release times; correction handling; registration-day rule (I-1 L); straddle and correction-driven `b*` (G17) | UNVERIFIED / UNSET |
| IAS 29 basis | Filing-metadata basis labels in Kernel exports; protected-window basis labels are not among OD-1's permitted aggregates; same-basis asset-scaled sensitivity | UNVERIFIED / UNSET; general regulatory timing VERIFIED (§6) |
| Calibration | FIQ-21 not run; acceptance criteria for test size not set; D6 floor unapproved; D8 seed and offsets unset | UNSET; no power or detectable-effect claim |
| Multiplicity | Alpha proposed, not approved; N UNSET; I-9 gated; FIQ-12 has no trial schema | UNSET / BLOCKED |
| Availability | No counts of events, clusters, coverage or band events; RQ3 eligibility UNVERIFIED; 2025Q1 start conditional; delisting/terminal proceeds unverified | UNVERIFIED |

## 5. Registration gate and decision matrix

Type: **O** owner scientific decision · **E** evidence · **A** separate access or
execution authorization · **G** governance/registration · **T** technical build.
"Blocks" = blocks OSF registration (R), confirmatory execution (X) or claims (C).

| Gate | Type | Requirement | Current state | Blocks | Acceptance criterion |
|---|---|---|---|---|---|
| G01 | O | D1: Paper 2 scope; which protected window the single opening uses; event-publication start/end; observation end | UNSET | R | Dated owner decision recorded in DESIGN §5 and OSF fields |
| G02 | O/E | Operational U1 version: FIQ-06 OD-7(b)/16/17/19 and OD-4/14/15 disposed; rule text on main | BLOCKED | R, X | Adopted U1 version with effective date and hash cited in OSF |
| G03 | O/E | Strata mapping UNIVERSE_RULE OD-8(a) + EV-3 | BLOCKED (strata UNKNOWN) | R, X | Versioned mapping table adopted; non-financial stratum assignable |
| G04 | O | D2 remainder: primary window, session-0 rule, calendar source, timestamp precision | UNSET | R | Owner disposition; both documents identical |
| G05 | E/A | KAP timestamp semantics and historical calendar; FIQ-20 development-only pilot (OD-1 = B) | NOT RUN | R | FIQ-20 report on development data only, with mismatch causes |
| G06 | E | D3 operational: CPI series/vintage, reference-month mapping, share source, stale-price rule | UNSET | R | Frozen IDs and rules; outcome-free evidence of PIT availability |
| G07 | O/E/A | D4 remainder and rate-candidate selection by authorized outcome-blind feasibility | UNSET | R | Selected candidate, IDs, units and failure rule frozen in both documents |
| G08 | E/O | D5 basis-metadata availability; same-basis sensitivity decision | UNVERIFIED / UNSET | R | Kernel export evidence for basis labels; owner disposition of sensitivity |
| G09 | A/O | RQ3 eligibility counts (IAS 29 events, session and issuer clusters) — not authorized by OD-1 = B | UNVERIFIED | R (family freeze) | Either an owner-approved exact count authorization with defined outputs, or an owner decision on the treatment of UNVERIFIED eligibility, recorded before freezing the D9 family |
| G10 | O | D6 whole decision, including calibration acceptance criteria | UNAPPROVED | R | Owner disposition; criteria fixed before FIQ-21 results are read |
| G11 | A/T | FIQ-21 power/calibration (prerequisites FIQ-19, FIQ-07, KER-07, KER-13c); no adopted text authorizes protected-window inputs, so development data only | NOT RUN | R | Seeded, ledger-logged report; no true-date abnormal returns |
| G12 | O | D7 bundling, co-announcement taxonomy, blind coding (OD-5 = B if an LLM codes) | UNSET | R | Owner disposition and frozen taxonomy |
| G13 | O | D8 seed, number of offsets, negative-control window | UNSET | R | Values frozen at registration |
| G14 | O | D9 alpha, stopping details, dates; optional equivalence margin | UNSET | R | Owner disposition |
| G15 | G | Prior-trial and exposure reconciliation; N; I-9 = L | BLOCKED | R, C | Itemised append-only inventory with N and cutoff; owner acceptance of the selection treatment |
| G16 | O/G | Per-target `D_i` definitions under OD-6 (factor realizations, flow-scaling history, surprise inputs) | UNSET | R | Registered `D_i` per target, chosen without outcomes |
| G17 | O/G | Observations straddling 2025-12-31/2026-01-01 and correction-driven `b*`; band and straddle counting route | Fail closed | R | Owner-confirmed exclusion and counting text |
| G18 | G/T | OD-2 immutable study identity and cross-study exposure ledger; recording location (candidate P G-2) | UNSET; FIQ-12 inert | X | Adopted ledger location and schema; opening bound to study ID |
| G19 | T/E | Snapshot binding (I-15 L); FIQ-07/08; KER-07, KER-13a, KER-13c; reviewed Kernel export row types | BLOCKED | R, X | Immutable snapshot IDs and hashes cited per source |
| G20 | O/E | Per-source rights decisions (Kernel), DataStore manual download only | UNSET | R, X | Approved rights record per source |
| G21 | G | Independent review of DESIGN/OSF v0.3 and later freeze | NOT DONE | R, C | Review record APPROVED on the exact frozen commit |
| G22 | G/O | FO-7 OSF submission by owner; registration-day rule (I-1 L) | NOT DONE | X | Real OSF URL, timestamp and git binding recorded |
| G23 | G | Exposure assessment (I-7, I-12 = L): semi-clean status, assistant-design inventory | OPEN | C | Owner-accepted exposure statement; no clean claim from dates |
| G24 | — | OD-7 = B: FIQ-17 waits for Paper 2 and Study 3 openings | Informational | — | Paper 2 opening recorded in the cross-study ledger |
| G25 | O | OD-4 = A covers refits; per-event benchmark estimation inside the single opening is not addressed by adopted text | INTERPRETATION | R | Owner or independent reviewer confirms in-opening estimation is part of the registered analysis |

**Readiness verdict:** NOT REGISTRATION-READY. All 24 non-informational gates
are open; G24 is informational. Pre-registration is not complete.

## 6. Evidence citation map

| Claim in DESIGN/OSF | Source | Status |
|---|---|---|
| FO-0 boundaries and freeze | Charter preamble, §5 rule 7; addendum L78-84; commit `292674c5` dated 2026-10-09 | VERIFIED |
| FIQ-11 OD-1..OD-8 dispositions | Addendum L50-61 | VERIFIED |
| I-item dispositions | Addendum L63-76 | VERIFIED |
| FIQ-06 scoped rules and open items | Addendum L19-46 | VERIFIED |
| D3/D5/D9 unchanged; D6 unapproved; OD-1 does not cover all RQ3 outputs | Addendum L85-89 | VERIFIED |
| Definitions of `D_i`, `e_i`, `b*_min,i`, window classes | Candidate P `1463425a` §1.1, §1.3 | Candidate text; used only to read adopted formulas |
| Inert FIQ-12 guard | `experiments/research_core/guard.py`, README | VERIFIED |
| SPK decision 81/1820 of 28.12.2023: TMS 29 from annual reports for periods ending 31.12.2023; 10 extra weeks for annual and 6 extra weeks for the first two interim reports | [SPK Bulletin 2024/6, 25/01/2024, p.16 item 2](https://spk.gov.tr/data/65b2beba8f95db1f44c2b15a/2024-6.pdf) | VERIFIED 2026-10-29 (text extracted) |
| KGK roadmap points 1-2: TMS 29 for annual periods ending on/after 31 December 2023; sector regulators may set different transition dates | [KGK announcement PDF](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/Diger/Enf_%20Muh_%20Duyuru_ESEB.pdf) | Text VERIFIED 2026-10-29; date from file metadata only |
| Kolari–Pynnönen, Cameron–Gelbach–Miller, Brown–Warner, Holm, IAS 29, Borsa İstanbul market functioning, Foster, Livnat–Mendenhall, CBRT EVDS | DESIGN §5 source registers | REPORTED (2026-10-25/26), not rerun; Holm full text UNVERIFIED |

No citation was used to support a FinanceIQ empirical claim.

## 7. Publication- and exposure-date checks

| Check | Result |
|---|---|
| Paper 2 v0.2 vs addendum order | v0.2 committed 13:59:41, addendum 14:56:27 (+0100, 2026-10-26): v0.2 could not reflect OD dispositions (VERIFIED) |
| Addendum effect | "Take effect in this local commit, never retroactively" (addendum L5): v0.2 text was correct when written; v0.3 applies the addendum prospectively from 2026-10-29 |
| No backdating | v0.3 dates its own reconciliation 2026-10-29; owner approvals keep their 2026-10-26 date |
| Quarantine interval | Started 2026-01-01; no OSF registration exists on 2026-10-29, so the interval is open and growing; forward holdout has not started (VERIFIED absence of a registration record in repository; OSF itself not queried) |
| Source dates vs boundaries | SPK bulletin 25/01/2024 and KGK 2023 file sit in the locked-holdout calendar span but are regulation, not study data; CBRT EVDS announcement (26 January 2026) is in the quarantine span and is a platform note, not series values |
| Context staleness | Owner context snapshot 2026-10-14 predates PRs #52-55 |

## 8. Unmade owner decisions (explicitly UNSET)

1. D1: Paper 2 scope, protected window of the single opening, event-publication
   start/end, observation end (G01).
2. Remaining FIQ-06 decisions for an operational U1 version and strata mapping (G02, G03).
3. D2 remainder (G04); D3 operational conventions (G06); D4 remainder (G07).
4. D5 same-basis asset-scaled sensitivity (G08).
5. RQ3 eligibility route: exact count authorization or treatment of UNVERIFIED (G09).
6. D6 entirely, including calibration acceptance criteria (G10).
7. D7 entirely (G12); D8 seed and number of offsets (G13).
8. D9 alpha, stopping details and dates; any practical-equivalence margin (G14).
9. Per-target `D_i` content under OD-6 (G16) and straddle/correction handling (G17).
10. Prior-trial/exposure acceptance and selection treatment (G15, G23).
11. Interpretation of OD-4 for in-opening benchmark estimation (G25).
12. FO-7 timing and submission (G22).

None is answered here. No hypothesis, sample count, threshold, cluster rule,
power or result is set.

## 9. Acceptance criteria

**Registration-ready** only when: every gate in §5 except G24 is closed with a
cited, dated record; DESIGN and OSF draft are identical in every shared field and
frozen at one commit; all UNSET fields are filled by dated owner decisions; the
exposure ledger shows no Paper 2 outcome inspection; independent review approves
that exact commit; the owner then performs FO-7.

**This audit** is acceptable when: (1) every adopted disposition in the addendum
appears in §1 with a v0.3 action; (2) DESIGN/OSF v0.3 contain no text treating
FIQ-11 OD-1..OD-8 as open or proposing the superseded OD-6 policy; (3) owner-
approved D3/D5/D9 and D2/D4/D8 text is unchanged; (4) local links resolve; (5) the
diff touches only `docs/paper2/`.

## 10. Exposure record for this preparation (append-only)

Read: the two owner context files (the FinanceIQ file contains legacy aggregate
capstone outcome summaries of the withdrawn annual study), the Charter, task cards,
addendum, study template, FIQ-12 README and guard, the two Paper 2 files, the
named sections of candidates U and P (U's grep output included membership-evidence
metadata such as period dates and node identifiers), and two regulator PDFs (the
SPK page also showed issuer names in a corporate-governance list). Not opened:
`PRD.md`, `RESULTS.md`, experiment results, data files, Kernel snapshots, SC5
caches or issuer filings. No Paper 2 outcome, event date, count or return was seen
or computed. This is a disclosure, not a zero-exposure claim.
