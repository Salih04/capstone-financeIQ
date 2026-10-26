# OSF preregistration draft — Paper 2

**FIQ-19 · preparation v0.2 · 2026-10-26 · LIMITED OWNER DECISIONS APPLIED; NOT REGISTERED**

Research support only; not investment advice. **NOT SUBMITTED.** Registration
identifier, URL, DOI and effective timestamp: **UNSET**. Incomplete
BEFORE record following [STUDY_RECORD_TEMPLATE.md](../process/STUDY_RECORD_TEMPLATE.md),
not permission to collect data, inspect protected availability or execute analyses.
Only the explicit owner-approved 2026-10-26 D3/D5/D9 decisions and narrow
D2/D4/D8 amendments are approved, as itemized in DESIGN §5. All remaining D
choices are **PROPOSED / UNRESOLVED**. These dispositions do not authorize access
or execution. Preparation uses only the two documents from source commit
`a66ee4f4562877a0367514b62ecdd904b50b6573`, imported without branch ancestry onto
verified main `f7b1e4f9fa43e47b6cb638521f966981abd6695c` (PR #52), fetched
2026-10-26. Authority is the owner task “FIQ-19 v0.2 — Apply explicit owner
decisions and commit”, dated 2026-10-26; no approval is backdated.
[DESIGN.md](DESIGN.md) is the shared specification; freeze both files together.

## BEFORE — proposed registration fields

**Study identity and question.** Proposed ID `paper2-kap-events`, v0.2. Study date
is a drafting date only. RQ1: relation of prospective seasonal earnings surprise
to CAR[0,+1]. RQ2: statistical decomposition into market, rates, FX, public-flow
information, intercept and residual. RQ3: difference in the surprise slope by
verified IAS 29 basis. Population, estimands, formulas, estimators, windows,
exclusions and sensitivities are exactly DESIGN §§1–4, with their stated decision
status. **Owner-approved D3 primary:**

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
assumption, not guaranteed eligibility. Before registration, use dates and
metadata only to count eligible IAS29 events, distinct event-session clusters
and relevant issuer clusters, under separately authorized outcome-free protected-
coverage rules. Apply the predeclared D6 threshold, including the issuer-cluster
requirement (currently proposed: at least 30 in each dimension), both bases and
an identified interaction. D6 remains PROPOSED / UNRESOLVED and must be disposed
of before freezing its threshold. No returns or outcomes may be inspected; this
task authorizes no counts. If counts themselves are not authorized, fail closed,
record eligibility UNVERIFIED and do not infer passage. If the threshold fails,
remove RQ3 from the registered confirmatory family before registration and label
it **NOT ESTIMABLE / forward-holdout-only candidate**. Any future forward-holdout
RQ3 confirmation needs its own authorized registration and access conditions.
No invented coverage, cluster counts, power or publication dates are supplied.
No additional model family or search is registered here.

**Universe and snapshots.** Charter U1 is adopted; operational rule version,
effective date and immutable snapshot IDs/hashes are **UNSET**. Availability, sample size, power, effect size and source access are unverified.
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
estimand. Remaining D4 choices are PROPOSED / UNRESOLVED. No event-wise substitution,
current-series backfill or permission to query protected values. D2's CAR[-1,+1]
is a wider-window sensitivity that does not remove timing confounding; D8 uses a common issuer-wide session shift per
repetition with event-level collision exclusions, discarded-event counts and
clustering-effect disclosure, no outcome-driven shift selection and no redraws.
Only the D2/D4/D8 amendments identified in DESIGN §5 are approved; their other
choices remain PROPOSED / UNRESOLVED.

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

FIQ-11 R7 is unadopted. D1/D10 must explicitly resolve its OD-1 (protected coverage
checks), OD-2 (project/study opening scope), OD-3 (forward-only claim authority),
OD-6 (boundary bands, including estimation-window information), and OD-8 (scope
of protection), plus relevant I-4/I-5 and I-10–I-16 (classification, replacements,
amendments, exposure, cutoff provenance, boundary trigger, snapshots and looks).
OD-4/OD-5 require disposition if refitting on locked data or LLM features is later
proposed; neither is in this design. OD-7 concerns FIQ-17, not Paper 2 registration
authority. These are dependency questions, not adopted policies or permissions.

Proposed conservative primary: keep estimation-window information in event
lineage; exclude boundary-band events from development and confirmation pending
OD-6. Sensitivity only if expressly approved: classify using the event outcome
interval while treating the pre-event estimation window separately, because
benchmark fitting may differ from exposure to the event outcome. Neither policy
is approved. The quarantine interval above is explicit; remaining
forward eligibility, outcome completion, pre-registration dependency information
and amendment effects require an explicit owner disposition; no event becomes
forward merely because its return window ends after registration. No exception
for coverage checks, availability counts, new snapshots or another study is granted.

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

Before registration reconcile all prior relevant evaluated configurations and
source/exposure records, including failures, abandoned attempts, pilots,
calibrations, related studies and post-hoc variants. N is **UNSET**, never assumed
zero because this drafting task ran no trials. Record occurrence, access,
computation, emission/display evidence, timing, materiality and uncertainty;
unknown exposure or missing trial accounting blocks confirmatory claims. No
private incident record was accessed or amended.

**Multiplicity (D9) — OWNER-APPROVED 2026-10-26, limited scope.** The
confirmatory family is RQ1 beta plus eligible RQ3 delta, with two-sided Holm.
When RQ3 is excluded by the eligibility rule before registration, the registered
family contains RQ1 alone. Freeze the eligible family before registration;
never change it after seeing outcomes. Report unavailable tests as **UNAVAILABLE**,
without artificial p-values or invented hypotheses. RQ1 must also satisfy D6
feasibility, identification and inference safeguards; excluding RQ3 is no waiver.

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
governance compatibility blocks registration/claims. No silent inflation of the
registered family or invented placeholders substitutes for this reconciliation.
A new primary/answering configuration requires prospective governance and
registration treatment. D9 alpha, exact stopping details and governing prior-
trial/exposure reconciliation remain PROPOSED / UNRESOLVED; proposed familywise
alpha is 0.05, not separately approved by this amendment.

**Stopping and nulls (D9) — PROPOSED / UNRESOLVED details.** One fixed terminal analysis, no interim outcome looks,
no significance stopping, no sample extension after seeing estimates. Owner must
set exact event-publication start/end, latest outcome-completion date, fixed
forward accrual end and administrative data-lock date before submission; all are
**UNSET**. The available study span cannot be selected from favourable outcomes.
Stop without inferential claims if rights, lineage, comparability, trial accounting
or approved inference gates fail; report the failure. Failed runs/replacements
need an approved rule before access; this draft grants no reset or second opening.

Statistical null: beta=0 / delta=0. Report estimates, ordinary 95% intervals and
multiplicity-adjusted p-values together. Failure to reject is inconclusive about
absence, not equivalence. No practical-equivalence margin is invented; owner must
specify and justify one before registration if practical-null claims are desired.
All null, adverse and unavailable results are reportable. No power or detectable-effect estimate is claimed. Evidence that changes the conclusion:
adequately calibrated, authorized held-out estimates inconsistent with zero after
family correction strengthen an association claim; opposite-sign replication,
lead-window effects, sensitivity instability or source/basis failures weaken it.
None establishes causation or predictive ability outside Charter claim gates.

## Required downstream gates — no execution authorized here

1. Preserve the 2026-10-26 D3/D5/D9 approvals and narrow D2/D4/D8 amendments;
   owner disposes of all remaining DESIGN D choices and relevant FIQ-06/FIQ-11
   adoption/evidence dependencies, final classification,
   exposure assessment and claim limits. Neither R14 nor R7 is merged by this task.
2. Establish adopted operational U1 and authorized PIT/source-rights lineage.
   FIQ-20 and FIQ-21 each require FIQ-19, FIQ-07, KER-07, KER-13a and KER-13c per
   their cards. FIQ-20 is only a separately authorized timestamp/calendar/price-
   existence pilot; FIQ-21 is separately authorized placebo power/calibration
   work, recorded in the trial ledger. No protected-window exemption is implied.
3. Establish separately authorized outcome-free RQ3 eligibility counts and
   D6 safeguards for both RQ1/RQ3; fail closed without count authorization.
   Reconcile pilot/calibration findings without true-date outcome inspection;
   independent review before paper analyses; complete all UNSET fields and freeze
   the two-document specification, snapshot policy, exact hypotheses, sources,
   exclusions, seed, dates, ledger cutoff/count and one-look execution manifest.
   PR #52 on the verified base supplies an approved synthetic consumer, not
   research-data readiness. FIQ-12 candidates do not establish adopted access
   controls; establish verified consumer/ledger/access gates before execution.
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
