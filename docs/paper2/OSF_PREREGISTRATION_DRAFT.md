# OSF preregistration draft — Paper 2

**FIQ-19 · preparation v0.4 · 2026-11-03 · OWNER DECISIONS RECONCILED; NOT REGISTERED**

Research support only; not investment advice. **NOT SUBMITTED.** Registration
identifier, URL, DOI and effective timestamp: **UNSET**. Incomplete
BEFORE record following [STUDY_RECORD_TEMPLATE.md](../process/STUDY_RECORD_TEMPLATE.md),
not permission to collect data, inspect protected availability or execute analyses.
Owner decisions recorded 2026-11-03 21:24:35 Europe/Zurich approve the Queue 2
recommendations with the G12 and G14/G09 amendments and authorize the CDS-only
RQ2 extension. Earlier 2026-10-26 D3/D5/D9 and narrow D2/D4/D8 decisions remain
in force, with the changes itemized in DESIGN §5 and the owner decision batch.
Only outcome-free RQ3 eligibility counts are authorized beyond documentation
synchronization. No outcome access, acquisition, analysis, simulation, OSF
submission or registration is authorized. All remaining choices and evidence
requirements stay explicit. Historical v0.2/v0.3 provenance remains in Git; this
v0.4 amendment is synchronized with [DESIGN.md](DESIGN.md) in one freeze commit.
Gates and unmade decisions: [REGISTRATION_READINESS_AUDIT.md](REGISTRATION_READINESS_AUDIT.md).

## BEFORE — proposed registration fields

**Study identity and question.** Proposed ID `paper2-kap-events`; document v0.4 is a drafting version, not a registration. RQ1: relation of prospective seasonal earnings surprise to CAR[0,+1]. RQ2: statistical decomposition into market, rates, FX and public-flow information, intercept and residual; the optional descriptive extension adds CDS as specified below. RQ3: difference in the surprise slope by verified IAS 29 basis. Population, estimands, formulas, estimators, windows, exclusions and sensitivities are exactly DESIGN §§1–4, with the owner-approved status recorded there. D1 is one historical, explicitly semi-clean associational opening: candidate event publication dates 2023-01-01 through 2025-12-31 with every outcome dependency ending by 2025-12-31; candidate development dates 2017-01-01 through 2022-12-31 only if the adopted U1 feasible window supports them. Non-financial U1 is primary, holdings are flagged, financial firms are descriptive only, and no later forward look is granted. Operational U1 version, stratum mapping and feasibility remain gates. **Owner-approved D3 primary:**

```text
S_q = (E_q - expected_E_q) / MV_q
expected_E_q = E_(q-4) * CPI(q_end_month) / CPI((q-4)_end_month)
MV_q = close_on_fiscal_quarter_last_trading_session * shares_known_at_that_time
```

E_q is first-event consolidated discrete-quarter profit attributable to owners
of the parent; E_(q-4) is eligible PIT prior-year earnings public strictly before
the event. A comparative newly published at that event cannot replace the frozen
expectation. Both CPI observations must have been published before the KAP event.
Require compatible accounting bases, scope, currency and measurement units,
including the earnings/market-value scale. Preserve original PIT earnings, share
counts, original/adjusted prices, adjustments, vintage IDs, publication timestamps
and transformation lineage. MV_q uses the quarter's last trading session and the
share count known then, never the last close before publication or today's shares.
Missing, nonpositive or unverified denominators produce unavailable observations,
never filled values. Freeze CPI series/vintage rules and price/share verification
before registration. Apply the specified CPI ratio once; do not reconvert an
already converted comparative. If the approved formula and unit compatibility
cannot both be verified without double inflation conversion, mark unavailable.
CPI conversion cannot bridge historical cost and TMS29/IAS29 bases; YTD
subtraction also requires compatible operands, as DESIGN §2 specifies.

Drifted seasonal random walk and eight-difference SUE are diagnostic sensitivity
candidates only, conditional on comparable PIT history and predeclared training/
unit rules. They cannot replace the primary after outcomes. SUE's twelve-quarter
historical dependency is not a primary eligibility requirement.

**Owner-approved D5 and RQ3 eligibility:** establish actual accounting basis from
filing metadata, never calendar year alone; exclude incompatible historical-cost/
TMS29 transition quarters from surprise-based analyses and count attrition.
2025Q1 is an earliest potential comparable TMS29 event under the stated history
assumption, not guaranteed eligibility. The owner authorized only these outcome-
free eligibility aggregates before registration: IAS 29-basis event count,
distinct issuer count and distinct event-session count. Use publication dates,
filing-basis metadata and issuer/session identity only. The scoped
[KERNEL REQUEST #24](https://github.com/Salih04/financeiq-pit-kernel/issues/24) asks for them from
existing rights-cleared evidence; no new acquisition or Kernel planning/edits are
authorized. The request is open and no response/count has been received. No rows,
identifiers, returns, prices, CARs or other outcomes are
requested. Until source evidence is returned, counts and RQ3 eligibility are
**UNAVAILABLE**, not zero; no threshold passage is inferred. D6's owner-approved
floor is at least 30 issuer clusters and at least 30 session clusters for RQ1 and
RQ3. Both reporting bases and an identified interaction remain required. **RQ3 is
not dropped by default.** If source facts are unavailable or the floor is not met,
keep it UNAVAILABLE / NOT ESTIMABLE under the registered rule; do not silently
remove it or manufacture a p-value. Freeze the exact treatment of an unavailable
family member before registration. Any future forward-holdout RQ3 confirmation
needs its own authorized registration and access conditions. No counts have yet
been received or computed; no outcome has been inspected.

**Universe and snapshots.** Charter U1 and the 2026-10-26 scoped FIQ-06 v1.0.0
rules remain adopted. On 2026-11-03 the owner prospectively adopted the U1-only
rule v2.0.0 with the stated completeness and G03 amendments; its exact file is
pinned by rule commit `45c75ac7f0a7715dfd84b210b3a42830318311a0` and SHA-256
`3e3307ad95e2d1d9af5724ce2f3a7737ff8cf809a0b6985220fc4d8a4822b42f`. Publication
to main remains subject to separate review and hosted CI. R14 is not approved as
a whole and FIQ-06 is not completed. The rule adoption does not establish source
adequacy: G02 workbook/archive evidence, G03 template-based strata mapping, the
feasible window, effective formation dates and immutable snapshot IDs/hashes
remain **UNSET**. Availability, sample size, power, effect size and source access
are unverified.
Before registration, bind source rights decisions and immutable lineage for:
membership evidence and cross-checks; effective issuer/security identities;
original and amended KAP filings and accounting units; exchange calendar;
prices/corporate actions/terminal proceeds; benchmark, yield, risk-free, FX,
flow and price-index series with actual release calendars and vintages.

For each source retain source identifier/locator, raw content hash, immutable
snapshot ID, retrieval and ingestion times, public-availability evidence,
reference period, revisions, transformation/code hash and derived-row parent
hashes. Keep `public_at` distinct from trusted persisted `system_as_of` and
transaction-commit visibility. Late imports do not prove historical usability. D4's owner-approved fallback priority is verified TRY two-year sovereign yield
→ verified EVDS benchmark sovereign yield → verified policy-rate changes
(announced one-week repo changes).
Select the highest-ranked PIT-feasible candidate by authorized outcome-blind
feasibility before registration, consistently across observations; freeze it for
the entire study. Never replace it using fit, significance or performance;
IDs, units, historical release/vintage proof and fallback feasibility are UNSET.
Two-year market yield, EVDS benchmark (with potentially different tenor/roll)
and policy news have different economic interpretations; disclose the selected
estimand. The D4 design choices are approved; source IDs, rights, quote conversions, PIT
timing and access evidence remain gated. No event-wise substitution, current-series
backfill or permission to query protected values. D2's CAR[-1,+1]
is a wider-window sensitivity that does not remove timing confounding; D8 uses a common issuer-wide session shift per
repetition with event-level collision exclusions, discarded-event counts and
clustering-effect disclosure, no outcome-driven shift selection and no redraws.
The 2026-11-03 owner decision keeps the D4 risk-free hierarchy unchanged and
adds an optional RQ2 extension ON for CDS only: add the daily change in the Turkey
five-year sovereign CDS quote and reuse the existing USD/TRY FX column once. The
policy-rate surprise is EXCLUDED because the minimum 20 evidenced decisions in
`[-250,-31]` is infeasible and no immutable pre-meeting expectation archive exists.
If LSEG CDS is unavailable before registration, the extension is UNAVAILABLE with
no fallback or post-hoc substitution. Contract, quote side, currency, restructuring
clause, timestamps, units, alignment, missing rules, rights and PIT lineage remain
evidence gates. This does not authorize data retrieval or outcome access.

Each event must bind the pre-release information set,
forecast/scale parents, calendar mapping and estimation sample. Post-registration
forward snapshots need a frozen binding policy with append-only hashes; later
corrections never overwrite the registered vintage. These requirements do not establish current FIQ-08/Kernel capability. Kernel →
FinanceIQ only; outcomes, residuals and selections never flow back to Kernel.

**Boundaries and exposure.** Preserve FO-0 verbatim: development through
2022-12-31; locked holdout 2023-01-01 through 2025-12-31; forward holdout consists
of data published after actual OSF registration. No boundary change is proposed.
Records originally published from **2026-01-01 until the actual OSF registration
timestamp** form an explicitly identified **unregistered quarantine interval**,
not development, locked holdout or forward confirmation. Subsequent retrieval or
correction does not reclassify original publication time. This task grants no
access to or evaluation of that interval. No actual registration time or forward
start is invented. The Charter labels the
historical holdout semi-clean; no pristine historical confirmation claim follows.

FO-0 boundaries froze on 2026-10-09 (commit `292674c5`); no separate
first-evaluation freeze exists. FIQ-11 R7 is not adopted as a whole. The owner's
2026-10-26 addendum adopts these dispositions, which bind this study:

- **OD-1 = B.** In protected periods only four aggregate metadata counts are
  generally permitted (U1 member count per formation date; identity coverage;
  eligible KAP filing-event count; distinct event-date count per quarter), from
  authorized metadata with access checks and immutable lineage. No individual
  rows, joins, price presence/coverage, suspension/delisting details, prices,
  returns or outcomes. Undefined eligibility, denominator, output or aggregation
  fails closed. FIQ-20 is development-only. A separate owner decision dated
  2026-11-03 authorizes only the three outcome-free RQ3 eligibility aggregates
  specified in DESIGN §3; it does not widen OD-1 for any other use.
- **OD-2 = B.** One confirmatory opening for this study, bound to its immutable
  study identity and a cross-study exposure ledger; amendment or re-registration
  cannot reset it; no further openings or interim looks.
- **OD-3 = B.** Charter §5 rule 4 is clarified for forward predictive claims;
  Paper 2 makes associational claims only, so its claim scope is unchanged.
- **OD-4 = A.** No refitting on locked-holdout outcomes. **OD-5 = B.** Any LLM
  use (none is registered here; D7 uses no LLM coding) needs a non-leakage
  argument bound to version, target and use, or is exploratory.
- **OD-6.** (a) Observations with `e_i <= 2022-12-31 < b*_min,i <= 2025-12-31`
  are excluded from development and confirmatory samples; (b) they have no
  secondary confirmatory use; (c) benchmark/expected-return estimation-window data
  ending before the outcome interval (here sessions [-250,-31]) do not enter
  `D_i`. PIT/as-of, training-only fitting, purge/embargo and other leakage checks
  remain; no event becomes eligible automatically. Classification is per target,
  so primary, wider-window and lead-window samples can differ near the boundary.
  Access to estimation-window data dated in a protected window remains a touch.
  Which other data enter each target's `D_i` (in-window factor realizations, the
  flow-scaling history, surprise inputs) is **UNSET** and must be registered
  without outcomes.
- **OD-7 = B.** FIQ-17's protected 2023–2025 outcome work waits until both this
  study's and Study 3's confirmatory openings exist; this is a downstream effect,
  not a Paper 2 permission.
- **OD-8 = A.** Project-wide protected classes are not narrowed for this study.
- **I-items.** I-4 and I-5 are replaced only as OD-6 and OD-1/OD-8; I-14 only as
  the FO-0 freeze. I-1 (registration-day rule), I-2, I-3 (lineage-aware
  classification), I-6, I-7 (assistant inventory), I-8, I-9 (historical selection
  correction), I-10 (reruns), I-11 (amendment timing), I-12 (no clean-status
  algorithm), I-13, I-15 (snapshot contract) and I-16 (no extra opening or look)
  are LEFT UNRESOLVED and fail closed where needed.

*Superseded v0.2 text (at `b2b31536`, before PR #55):* v0.2 listed these OD items
as unresolved and proposed a "conservative primary" keeping estimation-window
information in event lineage, with an unapproved sensitivity. Adopted OD-6(b)/(c)
supersede both; no band sensitivity is retained.

Observations whose `D_i` contains any record originally published on or after
2026-01-01 (for example a window ending in January 2026, or a later correction)
depend on the quarantine interval and are not evaluated as locked holdout; their
counting route and labelling are **UNSET** and fail closed. Remaining forward
eligibility, outcome completion and amendment effects still require explicit owner
disposition; no event becomes forward merely because its return window ends after
registration. No exception for coverage checks, availability counts, new snapshots
or another study is granted beyond OD-1 = B, except the exact outcome-free RQ3
eligibility aggregates authorized in DESIGN §3.

**Prior trials and exposure disclosure (append-only).** The source commit's
v0.1/v0.2 disclosures remain in git history and are retained here as historical
reports: earlier context/operating/Charter/PRD guidance included aggregate legacy
outcomes; a referenced chat supplied task/method proposals; public-source searches
incidentally surfaced issuer accounting-note snippets, without opening those
reports or testing feasibility. The source reported no local empirical exports,
protected windows, SC5/performance-file inspection, study outcomes, simulations
or feasibility counts. These inherited reports are not reverified by this task
and never establish zero prior exposure or clean confirmation.

For this owner-decision amendment, the required project context and current
Charter/agent guidance were read; they contain historical aggregate capstone
summaries. No legacy results/performance file, protected dataset, experiment
result, unrelated task queue or issuer filing was opened. Only Git metadata,
the two design documents, governing instructions and the relevant repository map
were inspected. No study trial, coverage count, simulation or analysis was run.
Record this context exposure in the later owner assessment; do not erase prior
history or call this an exposure-free preparation. No private incident record
was accessed or amended.

For the v0.3 reconciliation (2026-10-29): the owner's global workflow and
FinanceIQ context files (the latter containing legacy aggregate capstone outcome
summaries), the Charter, task cards, addendum, study template, FIQ-12 core
README/guard, named sections of the R14/R7 candidates (membership-evidence
metadata visible in search output) and two regulator PDFs (one page also listing
issuer names) were read. `PRD.md`, `RESULTS.md`, experiment results, data files,
Kernel snapshots, SC5 caches and issuer filings were not opened. No Paper 2
outcome, event date, count or return was seen or computed. Not a zero-exposure claim.

Before registration reconcile all prior relevant evaluated configurations and
source/exposure records, including failures, abandoned attempts, pilots,
calibrations, related studies and post-hoc variants. N is **UNSET**, never assumed
zero because this drafting task ran no trials. Record occurrence, access,
computation, emission/display evidence, timing, materiality and uncertainty;
unknown exposure or missing trial accounting blocks confirmatory claims. No
private incident record was accessed or amended.

**Multiplicity (D9) — OWNER-APPROVED 2026-11-03.** Use alpha 0.05 and two-sided
Holm for the planned RQ1 beta and eligible RQ3 delta. RQ3 is not dropped by default.
No equivalence margin or test. Use one fixed terminal analysis after all gates,
with outcome-dependency end 2025-12-31; no sequential testing, significance stopping
or sample-size stopping. Freeze the exact treatment of any unavailable family
member before registration. Report unavailable tests as **UNAVAILABLE**, without
artificial p-values or post-outcome family changes. D6 safeguards apply to both
slopes. RQ2 is descriptive. Keep prior trials and exposure separate and append-only;
reconcile relevant prior configurations under Charter §5.6. Unknown trial count N
remains UNSET, never zero. The approved family does not waive selection corrections,
exposure assessment, or governing Charter conditions.

RQ2 is descriptive. Mean-CAR, placebo, lead-window negative control, benchmark,
window, surprise and all other sensitivity results are diagnostics, transparently
reported without confirmatory claims or rescue of a failed test. Report complete
attempt inventories, estimates, intervals and available diagnostic p-values.

Keep all historical trials/exposure disclosures separately and append-only.
Unknown trial count N remains UNSET, never zero. Every trial, including failed
and abandoned configurations, remains logged under Charter §5.6. The approved
beta/eligible-delta family does not adopt FIQ-11 R7 or waive governing trial/
exposure reconciliation, selection corrections or claim limits. Before
registration reconcile relevant prior answering configurations and specify any
required additional selection correction or authorized fresh confirmation design.
Two-sided Holm cannot cleanse adaptive selection or holdout exposure; unresolved
governance compatibility blocks registration/claims. FIQ-11 I-9 is LEFT
UNRESOLVED (historical selection correction remains gated), so this
reconciliation cannot yet be closed. No silent inflation of the
registered family or invented placeholders substitutes for this reconciliation.
A new primary/answering configuration requires prospective governance and
registration treatment. Alpha 0.05 and one fixed terminal analysis are approved;
prior-trial/exposure reconciliation, exact unavailable-family handling and all
other governance gates remain open.

**Stopping and nulls (D9) — OWNER-APPROVED 2026-11-03; residual registration details remain gated.**
OD-2 = B permits one confirmatory opening. D1 fixes a historical, explicitly
semi-clean associational study: candidate event-publication interval
2023-01-01..2025-12-31, all outcome dependencies ending by 2025-12-31, candidate
development interval 2017-01-01..2022-12-31 conditional on U1 feasibility, and no
later forward look. Use one fixed terminal analysis; no interim looks, significance
stopping, sample-size stopping or extension after estimates. Administrative data-lock
and registration-day timestamp mechanics remain to be frozen. The available study
span cannot be selected from favorable outcomes. Stop without inferential claims if
rights, lineage, comparability, trial accounting or approved inference gates fail;
report the failure. This draft grants no reset or second opening.

Statistical null: beta=0 / delta=0. Report estimates, ordinary 95% intervals and
multiplicity-adjusted p-values together. Failure to reject is inconclusive about
absence, not equivalence. No practical-equivalence margin or test is approved; no practical-null claim is
registered.
All null, adverse and unavailable results are reportable. No power or detectable-effect estimate is claimed. Evidence that changes the conclusion:
adequately calibrated, authorized held-out estimates inconsistent with zero after
family correction strengthen an association claim; opposite-sign replication,
lead-window effects, sensitivity instability or source/basis failures weaken it.
None establishes causation or predictive ability outside Charter claim gates.

## Required downstream gates — no execution authorized here

1. Preserve the 2026-10-26 D3/D5/D9 approvals, narrow D2/D4/D8 amendments and
   2026-11-03 decisions in DESIGN §5; owner resolves remaining DESIGN D choices
   and relevant FIQ-06 source-evidence dependencies, FIQ-11 residual items, final classification,
   exposure assessment and claim limits. Neither R14 nor R7 is merged by this task;
   only the addendum's scoped FIQ-06 rules and FIQ-11 dispositions are adopted.
2. Publish the owner-adopted U1 rule v2.0.0 through its separate review and
   hosted CI, then establish source adequacy, the feasible window and authorized
   PIT/source-rights lineage.
   FIQ-20 and FIQ-21 each require FIQ-19, FIQ-07, KER-07, KER-13a and KER-13c per
   the task-file wave table (FIQ-21's own card omits KER-13a; the stricter list is
   kept). FIQ-20 is only a separately
   authorized timestamp/calendar/price-existence pilot and, under OD-1 = B,
   development-only; FIQ-21 is separately authorized placebo power/calibration
   work, recorded in the trial ledger, and no adopted text authorizes it to use
   protected-window inputs. No protected-window exemption is implied.
3. Obtain the outcome-free RQ3 eligibility aggregates authorized in DESIGN §3
   from existing rights-cleared evidence; if source facts are unavailable, keep
   counts UNAVAILABLE. Do not access outcomes. Complete the D6 calibration gate for
   both RQ1/RQ3 and freeze unavailable-family handling before registration.
   Reconcile pilot/calibration findings without true-date outcome inspection;
   independent review before paper analyses; complete all UNSET fields and freeze
   the two-document specification, snapshot policy, exact hypotheses, sources,
   exclusions, seed, dates, ledger cutoff/count and one-look execution manifest.
   PR #52 on the verified base supplies an approved synthetic consumer, not
   research-data readiness. The merged FIQ-12 inert core (PR #53) always denies
   protected access and has no trial schema, policy or unlock; it is not an
   operational access grant. Establish verified consumer/ledger/access gates and
   the OD-2 cross-study exposure ledger before execution.
4. FO-7: owner submits the finalized preregistration to OSF and records its real
   URL/timestamp and exact git binding. This draft is not an OSF submission.
5. FIQ-22: separately authorize main analysis only after registration and the
   prerequisite/adoption/exposure/access gates pass; execute through the approved
   ledger exactly as registered. Independent review and Charter claim gates remain
   necessary for paper inclusion. No Kernel changes or reverse information flow.

## AFTER — deliberately unfilled

No registered analysis, post-hoc analysis, estimate, deviation assessment or trial
count is supplied. After authorized execution record registered versus post-hoc
analyses, estimates/uncertainty, all exclusions and nulls, deviations with timing
and exposure, limitations and reconciled N using the study-record template.
