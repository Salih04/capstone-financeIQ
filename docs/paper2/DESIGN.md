# Paper 2 — KAP disclosure event study

**FIQ-19 · preparation v0.4 · 2026-11-03 · OWNER DECISIONS RECONCILED; NOT REGISTERED**

Research support only; not investment advice. No study is registered or run by
this document. The owner decisions recorded 2026-11-03 approve the Queue 2 design
recommendations with the G12 and G14/G09 amendments, plus CDS-only Batch B.
Earlier D3/D5/D9 and narrow D2/D4/D8 approvals remain in force. These design
decisions authorize documentation synchronization and outcome-free eligibility
counts only; they do not authorize outcome access, study execution or registration.
All unresolved choices and evidence gates remain explicit below.
The [OSF draft](OSF_PREREGISTRATION_DRAFT.md) supplies the study-record fields.
v0.3 (2026-10-29) only reconciles this text with the already adopted
[owner decision addendum](../research/OWNER_DECISION_ADDENDUM.md) (PR #55,
`efe3ed32`, committed after v0.2); it makes no new scientific choice. Gate
matrix, stale-text findings and unmade decisions:
[REGISTRATION_READINESS_AUDIT.md](REGISTRATION_READINESS_AUDIT.md).

## 1. Authority, scope and questions

Authority: adopted [Research Charter](../process/RESEARCH_CHARTER.md), including
FO-0, and the exact FIQ-19 card in
[TASKS_FINANCEIQ_2026-10-07.md](../process/TASKS_FINANCEIQ_2026-10-07.md).
Document source: exact local commit `a66ee4f4562877a0367514b62ecdd904b50b6573`
(v0.2 preparation, following v0.1 `7e07044e`). Only these two Paper 2 files
were imported, without source-branch ancestry, onto verified current origin/main
`f7b1e4f9fa43e47b6cb638521f966981abd6695c` (PR #52), fetched 2026-10-26.
Authority for this amendment: explicit owner task “FIQ-19 v0.2 — Apply explicit
owner decisions and commit”, dated 2026-10-26; no approval is backdated.
This task merges or adopts no separate governance or implementation lane.
PR #52 is already on the verified base; its synthetic consumer does not establish
research-data readiness or scientific adoption.
v0.2 landed on main as `b2b31536` (PR #54), whose parent is `4b029ef4` (PR #53),
not the preparation base named above. v0.3 is edited on main `efe3ed32` (PR #55).

FIQ-06 R14 (`8093ec0f54d80df31c50e3a806b06b0fb2f2a096`) and FIQ-11 R7
(`1463425ae1c4ea592a9e6efc3a1a26ca6810137b`) remain **unadopted as whole drafts**.
The 2026-10-26 addendum adopted only the scoped FIQ-06 v1.0.0 rules B2,
6(c)-A, 20(a)1 + (b)ii, 21-A, 22-B and 23-B, approved as rules but operationally
blocked where definitions or evidence are missing; it also adopted FIQ-11
dispositions OD-1 = B, OD-2 = B, OD-3 = B, OD-4 = A, OD-5 = B, OD-6 (a)(b)(c),
OD-7 = B, OD-8 = A and itemised I-1..I-16 states. On 2026-11-03, the owner
prospectively adopted the U1-only rule v2.0.0 with the stated completeness and G03
amendments. Its exact file is pinned by rule commit
`45c75ac7f0a7715dfd84b210b3a42830318311a0` and SHA-256
`3e3307ad95e2d1d9af5724ce2f3a7737ff8cf809a0b6985220fc4d8a4822b42f`; publication
to main remains subject to the separate review and hosted CI. This version records
the rule decision only: archive evidence, G03 mapping, source adequacy and the
feasible window remain open, and FIQ-06 is not complete. FIQ-11 remains governed
by its 2026-10-26 dispositions. Their binding effect on this study is in the OSF
draft's boundaries section. UNIVERSE_RULE 22-B governs membership-announcement
copies; it is not transferred to D2 event timing.

Target population: quarterly U1 formation samples under Charter §4; primary
stratum non-financial firms, holdings flagged, and financial firms descriptive
only. Retain index leavers, suspensions, mergers and delistings through the event
window; do not use the capstone cohort or a survivor filter. The owner approved
one historical, explicitly semi-clean associational opening: candidate event
publication dates 2023-01-01 through 2025-12-31, with every outcome dependency
ending by 2025-12-31; candidate development dates 2017-01-01 through 2022-12-31
only if an adopted U1 feasible window supports them. No later forward look is
granted. Owner-adopted U1 rule v2.0.0 and its exact file digest are pinned above;
publication to main is pending its separate review and hosted CI. This rule
adoption does not establish source adequacy: G02's scoped workbook/archive evidence,
G03's template-based strata mapping (U OD-8(a) with evidence EV-3), and the feasible
window (U OD-4/14/15) remain OPEN/BLOCKED. Strata are UNKNOWN and the primary
sample cannot yet be populated.

| Question | Proposed estimand, one row per issuer/report event |
|---|---|
| RQ1: Does surprise relate to disclosure reaction? | Equal-event OLS slope beta of signed surprise S_q on two-session cumulative abnormal return CAR[0,+1], in return units per S_q unit, within the eligible U1 non-financial sample |
| RQ2: What explains the move? | Equal-event mean signed contribution of each fixed factor, intercept and residual to that same cumulative excess return; descriptive dispersion of those components, without a causal interpretation |
| RQ3: Does the IAS 29 relation differ? | Difference delta in the S_q slope between verified IAS-29 and non-IAS-29 reporting bases, from the interaction S_q × basis; a regime association, not an identified IAS-29 treatment effect |

Fit RQ1 as CAR = intercept + beta S_q + error. For RQ3 fit CAR = intercept +
beta S_q + gamma IAS + delta(S_q × IAS) + error. Basis, macro conditions and sample composition can change together.
Residuals do not isolate earnings news.

## 2. Publication time and prospective surprise

**D2 — OWNER-APPROVED 2026-11-03.** CAR[0,+1] is primary; CAR[-1,+1] is the wider-window sensitivity. The first historical price-setting close strictly after evidenced KAP publication defines session 0. Use a versioned BIST calendar including half-days, auctions, closures and historical Europe/Istanbul offsets. Unknown time precision, original offset or close ties are unalignable. Operational timestamp/calendar evidence remains gated. Event origin is the first public KAP financial-statement release
for that issuer/reporting period, including the attached statements. Preserve
publication, ingestion and any correction times separately. Use the timestamp's
verified original offset and historical `Europe/Istanbul` conversion, plus a
versioned exchange calendar with holidays, half-days, closures and auctions.
Session 0 is the first session whose price-setting closing auction occurs
strictly after publication. Before-open and intraday releases map to that day's
session; releases at/after the closing price determination or on non-trading days
map to the next session. Do not equate the end of continuous trading or later
trades at an already fixed price with the price-setting close. Unknown precision,
offset or tie ordering means unalignable, not an inferred timestamp.

CAR[0,+1] uses close-to-close total returns from close[-1] to close[+1]. It captures
part of the pre-announcement day for intraday events; daily data cannot identify
an instantaneous response. The owner-approved 2026-10-26 terminology is CAR[-1,+1] **wider-window sensitivity**;
it adds pre-event exposure and does not remove confounding. Freeze historical calendar rules before
matching; today's timetable is not evidence of past hours.

**D3 — OWNER-APPROVED 2026-10-26; operations approved 2026-11-03.** The single primary surprise is

```text
S_q = (E_q - expected_E_q) / MV_q
expected_E_q = E_(q-4) * CPI(q_end_month) / CPI((q-4)_end_month)
MV_q = close_on_fiscal_quarter_last_trading_session * shares_known_at_that_time
```

E_q is consolidated discrete-quarter profit attributable to owners of the parent,
with fixed currency and scope, from the first event release. E_(q-4) is the
eligible PIT prior-year quarter earnings available strictly before that release;
a comparative newly published in the event cannot rewrite the expectation.
MV_q uses the fiscal quarter's last trading session, not the last close before
KAP publication. Retain the actual historical share count known at that session,
matching price adjustments, share classes, capital actions, currency and earnings
ownership scope; never substitute today's shares or a later capitalization.
Missing, nonpositive or unverified denominators make the observation unavailable;
no fill, interpolation or inferred denominator is allowed. Stale/nontrading-price
verification conventions remain to be frozen before registration.

Both CPI observations must have been published strictly before the KAP event.
Freeze exact series, reference-month mapping, release/vintage policy and measuring
units before registration; unavailable publication/vintage evidence means the
observation is unavailable. Use no unreleased index or later revision as if it
were known at the event. Require compatible accounting bases, currency, scope
and measurement units for the seasonal comparison and its market-value scale.
Check the unit date already embedded in each earnings observation: apply the
specified CPI ratio once to the eligible prior-quarter earnings, and never apply
it again to an already converted comparative. If the exact approved formula and
compatible units cannot both be established without double inflation conversion,
the event is unavailable; do not silently replace the formula. CPI conversion
changes purchasing-power units within compatible bases; it cannot bridge
historical cost and TMS29/IAS29 accounts.

YTD subtraction requires compatible bases and common measuring units for both
operands; do not splice nominal and restated cumulative amounts. Preserve original
PIT earnings, share counts, original and adjusted prices, adjustment lineage,
CPI values, vintage identifiers and publication timestamps alongside all derived
parents and transformation hashes. These are prospective FinanceIQ derivative
rules, not a claim that Kernel v4 already exports them.

**Diagnostic sensitivity candidates only:** drifted seasonal random walk
Ehat_q = E_(q-4) + c_i, with c_i fitted only on declared development/pre-event
training history; and eight-difference SUE with d_k = E_k - E_(k-4),
SUE_q = (E_q - E_(q-4)) / sample_SD(d_(q-8), …, d_(q-1)). Both require
comparable PIT history and declared units. SUE requires twelve historical quarter
positions E_(q-12)..E_(q-1), plus E_q, all eight eligible pre-event differences
and finite positive SD. Drift requires a frozen training length, minimum history,
basis-break policy and refit schedule. Neither is a primary alternative or a
post-outcome replacement. No tuning against CAR or CPI/drift search is authorized.
The simple drift rule is not claimed as an exact Foster (1977) replication.
Livnat–Mendenhall's price-scaled EPS change is related literature; the approved
total-earnings/CPI/quarter-end-market-value formula is a study adaptation.

The card's earnings-announcement-return alternative cannot independently explain
the same CAR (circularity). Proposed sensitivity: session-0 abnormal return as an explicitly return-based signal for
CAR[+2,+5] only, labelled a separate delayed-response diagnostic, logged and disclosed under D9, never a surprise substitute.

## 3. Expected returns, attribution and IAS 29

**D4 — OWNER-APPROVED DESIGN 2026-11-03; source and access evidence remain gated.** Fit each security's daily excess-return model on sessions
[-250,-31], requiring at least 160 complete observations, an identified design
matrix and positive residual variance; no parameter selection using event returns.
Use OLS with intercept and four fixed factors: broad BIST total-return market
excess return; change in the TRY two-year sovereign yield; log USD/TRY change;
and a public non-resident net equity-flow release signal. Fix the risk-free
conversion, source series identifiers, units and yield tenor before registration.
All coefficient estimation and scaling use only pre-event available inputs.

For flows, use the newly published weekly net equity-flow amount divided by
the SD of the preceding eight published amounts, assigned to the first daily
close strictly after its release. A verified non-release day has signal zero
(no news arrival, not imputed zero flow); an unknown release calendar/value is
missing. This measures response to public flow information, not contemporaneous
daily investor flows. No weekly-to-daily interpolation or backdating to the
reference week. Unknown flow release times remain missing. Owner-approved 2026-10-26 rate fallback priority, fixed
for the whole study **before registration and before any outcomes**:
(1) verified TRY two-year sovereign yield change; (2) verified EVDS benchmark
sovereign-yield change with evidenced tenor/roll convention; (3) verified one-week
repo policy-rate change assigned at public announcement, with announcement and
effective dates separate. Candidate (3) measures policy news, not two-year market
yield changes; an EVDS benchmark may differ in tenor, liquidity and roll exposure
from the two-year series. Disclose these different economic interpretations and
label the selected attribution estimand explicitly. Do not switch
series event by event or select by fit/significance. Select the highest-ranked
feasible candidate only after outcome-free rights, source-ID, units, coverage,
release-time and revision evidence is established with authorization. Exact IDs
and historical PIT support are **UNSET/UNVERIFIED**; current EVDS access is not a
historical vintage archive. Freeze the selected ID, transformation and failure
rule in both documents. Risk-free conversion is a separate source choice. No
approved/evidenced rate candidate, flow signal or other required factor means
stop the four-factor specification; report RQ2 unavailable rather than silently
reducing it. The G07 owner decision approves the model and rate hierarchy; source IDs, rights,
quote conversions, PIT timing and access evidence remain gated. No data retrieval
is authorized.

**Optional RQ2 extension — OWNER-APPROVED ON, CDS ONLY (2026-11-03).** Preserve
the four-factor descriptive primary and add the daily change in the Turkey five-year
sovereign CDS quote; reuse the existing USD/TRY FX column once. The optional
policy-rate surprise is EXCLUDED because the minimum 20 evidenced decisions in
`[-250,-31]` is infeasible and no immutable pre-meeting expectation archive exists.
Do not replace it with actual rate changes or another expectations source. This
exclusion does not change the approved D4 risk-free-rate hierarchy. LSEG CDS
availability and rights must be established before registration. If LSEG CDS is
unavailable before registration, the extension is UNAVAILABLE, with no fallback or
post-hoc substitution. Contract, quote side, currency, restructuring clause,
timestamps, units, frequency alignment, missing rules and PIT lineage remain
evidence gates. No outcome access, data acquisition or execution is authorized.

For each event, sum excess returns = 2 × fitted intercept + sum of each
fitted-loading × factor realization + CAR residual over sessions 0 and +1.
Report signed components and their reconciliation, without percentage shares. Contemporaneous
market/rate/FX realizations become known during the outcome window: they are
ex-post attribution controls, not pre-announcement predictors. Freeze their
publication/vintage policy too. Sensitivity: market-only benchmark, to diagnose
factor conditioning; it cannot replace the four-factor primary after results.

**D5 — OWNER-APPROVED 2026-10-26; conditional feasibility only.** Mark actual basis from each
filing's metadata, never infer it from calendar year alone. Exclude incompatible
historical-cost/TMS29 transition quarters from surprise-based analyses and count
them in attrition. Require within-basis histories and
common measuring units; record transition exclusions separately and retain
otherwise eligible RQ2 descriptions. A price-index rescaling alone does not
reconstruct full IAS29 accounts. No later comparative backfill into an earlier
information set. The following inherited chronology is conditional source evidence,
not an eligibility count or a new verification in this amendment:

| Period / claim | Evidence status and implication |
|---|---|
| FY2023 | VERIFIED general rule: KGK's 23 November 2023 announcement requires inflation adjustment for annual periods ending on/after 31 December 2023; sector regulators can set different transition dates. SPK 81/1820 is corroborated by official bulletin 2024/6, p.16. This is not issuer-specific basis evidence. |
| 2023Q4 = FY2023 − M9 2023 | INFERRED incompatibility for a reporter whose FY is IAS29 and whose M9 is historical cost. Do not subtract those amounts. Issuer-specific operands, prior restatements and their publication times are UNVERIFIED. |
| 2024 interims | Official SPK bulletin confirms extra time for the first two following interim reports. 2024Q1 as the first scheduled calendar-year IAS29 interim is an inference; actual first publication, fiscal calendars and exemptions are UNVERIFIED. |
| Approved primary: earliest potential TMS29 comparison | The general annual rule continues to periods ending after FY2023. If 2024Q1 first supplied eligible IAS29 quarterly earnings, 2025Q1 is a candidate first seasonal comparison to already-public 2024Q1. This is conditional feasibility, not proof that any 2025Q1 event qualifies. Measuring units, CPI availability, shares and prior comparatives must pass. |
| Eight-difference SUE diagnostic through locked 2023–2025 | If compatible history starts in 2024Q1 with no earlier PIT-eligible IAS29 quarter history, q−12 ≥ 2024Q1 implies earliest q = 2027Q1. Under those assumptions the SUE diagnostic has no IAS29 events in the locked holdout: its basis-interaction diagnostic is NOT ESTIMABLE and its surprise-slope diagnostic loses IAS29-era observations. This does not establish eligibility of the approved primary. Exact publication dates, eligible-event counts and cluster-threshold passage/failure are UNVERIFIED; these are not empirical findings. Earlier comparatives publicly available before an event could change the start, subject to the frozen lineage rule. |

The thirteen-quarter dependency concerns the diagnostic SUE only; it does not
replace the approved primary. 2025Q1 is the earliest potential TMS29 comparable
event under the stated history assumption, never guaranteed eligibility. Actual
basis, units, CPI releases, quarter-end shares/prices and immutable PIT lineage
must pass for every event. No cohort, protected coverage count or outcome was
inspected in this amendment. A same-basis asset-scaled sensitivity remains
PROPOSED / UNRESOLVED; ratios are not automatically basis-invariant.

**RQ3 eligibility — OWNER-AUTHORIZED OUTCOME-FREE COUNTS (2026-11-03).** Before
registration, obtain only these three aggregates for candidate IAS 29-basis events
in the owner-approved candidate event interval: (1) eligible event count, (2)
distinct issuer count, and (3) distinct event-session count. Use only publication
dates, filing-basis metadata and issuer/session identity facts. The authorization
excludes event rows or identifiers in the response, returns, prices, CARs and all
other outcomes. The scoped [KERNEL REQUEST #24](https://github.com/Salih04/financeiq-pit-kernel/issues/24)
asks for these aggregates from existing rights-cleared evidence; no new acquisition
or Kernel planning/edits are authorized. The request is open and no response/count
has been received. Until evidence is returned, counts and
RQ3 eligibility are **UNAVAILABLE**, not zero, and no cluster-threshold passage
can be inferred.

D6's approved floor is at least 30 issuer clusters and at least 30 session
clusters for RQ1 and RQ3 inference. Both reporting bases and an identified
interaction are required. Count authorization does not establish that source facts
exist or that the threshold is met. **RQ3 is not dropped by default.** If an
outcome-free source fact is unavailable or the floor is not met, preserve RQ3 as
UNAVAILABLE / NOT ESTIMABLE under the registered rule; do not silently remove it,
claim an interaction, or manufacture a p-value. Resolve the exact pre-registration
treatment of an unavailable family member before freezing D9. Any later forward
RQ3 confirmation requires its own authorized registration and access conditions.
No returns or outcomes have been inspected, and no count has yet been computed.

## 4. Dependence, exclusions and falsification

**D6 — OWNER-APPROVED 2026-11-03; calibration NOT RUN.** Use issuer × event-session
two-way clustered slope inference with two-sided 95% intervals. The minimum is 30
clusters in each dimension for RQ1 and RQ3; below the floor, report estimates only
and make no confirmatory significance claim. Use the Kolari–Pynnönen test only for
mean CAR and only with valid pre-event correlation estimates. Report the equal-weight
calendar-time HAC(5) diagnostic. Before FIQ-21, freeze 2,000 development-only
null repetitions with seed 20261102 and a complete outcome-free null-scenario
generator. Calibration passes only if, for every predeclared null scenario, the
upper two-sided 95% binomial interval for the nominal 5% null-rejection rate is at
most 7.5%. The scenario generator is still an evidence/technical gate; no
simulation or true-date outcome access has occurred. These safeguards apply to RQ1
and RQ3; unavailable tests remain UNAVAILABLE.

**D7 — OWNER-APPROVED 2026-11-03.** Treat simultaneous first filings for the same
issuer/period as one event and retain all lineage. If two distinct issuer events'
[0,+1] windows overlap, exclude both from the isolated-event primary sample and
describe bundled events separately. Mechanically classify co-announcements from
evidenced KAP disclosure-type codes using the frozen categories: dividends or
distributions; share or rights actions; mergers or acquisitions; and trading-status
changes. Only residual “other” items are coded by the owner while blind to returns;
record disagreements, and exclude unresolved items with a reason. No LLM coding.
Retain the full eligible-event sample as a labelled diagnostic. No exclusion based
on return magnitude, surprise sign or significance; no winsorisation. KAP code
mapping and classification evidence remain gates and must be frozen before outcome
access.

Missing stays null. Exclude only from the analysis requiring the missing item:
surprise absence does not imply removal from factor attribution. Reject ambiguous
identity, unestablished membership, unverifiable timestamp, incompatible earnings,
invalid estimation model, or missing event returns with explicit reason codes.
Use source-evidenced corporate actions and terminal proceeds; never convert a
suspension or absent delisting price into zero return. Count these failures and
state the resulting attrition risk; do not claim survivor-inclusive returns when
terminal outcomes are unavailable. No stored-data imputation.

**D8 — OWNER-APPROVED 2026-11-03.** Use seed 20261102 and pin the runtime and
sampling algorithm before registration. Draw 100 distinct integer session offsets
without replacement from [-120,-21] ∪ [21,120]. In repetition r, apply **one
common offset s_r to every issuer's complete event calendar** in the permitted
development block; never draw independent issuer shifts. Preserve inter-issuer
date clustering among retained events. Apply boundary, own-issuer real-disclosure/
co-announcement-window and overlapping-placebo exclusions **event by event**, using
D7 rules. Drop each conflicting placebo event (both members of a conflicting
same-issuer pair), not the whole common shift because one issuer collides. Count
each event once in attrition; retain all reason flags. Report per-shift retained
events, exclusion counts/reasons, issuer/date clusters, clustering effects and
unusable shifts. Do not resample offsets, redraw until valid or search for benign
p-values; zero retained events means that repetition is unavailable. Missingness/
eligibility rules remain fixed. Later FIQ-21 work is separately gated and has not
run.
Negative control: surprise versus CAR[-20,-11], same eligibility and clustering.
This diagnoses anticipation/confounding; passing does not establish identification.
Placebos, controls, mean-CAR and sensitivities are diagnostic under D9, with all
results/attempts disclosed; none rescues a failed confirmatory test. No true-date
abnormal returns, placebo calculation or simulation is authorized by this draft.

## 5. Owner decisions and source check

The owner decisions recorded 2026-11-03 21:24:35 Europe/Zurich amend the
2026-10-26 approvals as shown below. They do not adopt the whole study, close
source/evidence gates or authorize registration or execution.

| ID | Status and remaining disposition before freeze |
|---|---|
| D1 | OWNER-APPROVED 2026-11-03: one historical, explicitly semi-clean associational opening; candidate event dates 2023-01-01..2025-12-31, outcomes end by 2025-12-31; candidate development 2017-01-01..2022-12-31 conditional on U1 feasibility; non-financial U1 primary, holdings flagged, financials descriptive; no forward look. Operational U1, stratum mapping and feasibility remain gates |
| D2 | OWNER-APPROVED 2026-11-03: CAR[0,+1] primary; CAR[-1,+1] wider-window sensitivity; first price-setting close strictly after evidenced KAP publication; versioned BIST calendar and timestamp treatment as §2. Timestamp/calendar source evidence remains gated |
| D3 | OWNER-APPROVED 2026-10-26; operations approved 2026-11-03: CPI seasonal expectation, quarter-end MV and exact price/share rules as §2; source IDs, units and PIT evidence remain gated |
| D4 | OWNER-APPROVED 2026-11-03: four-factor OLS design and D4 hierarchy/rules as §3; optional RQ2 extension ON for CDS daily change with existing FX once; policy-rate surprise excluded. Source IDs and rights remain gated |
| D5 | OWNER-APPROVED: filing-metadata basis, transition exclusions with attrition, no CPI bridge, conditional earliest 2025Q1. G09 count scope amended 2026-11-03 as §3; source facts and counts remain unavailable pending evidence |
| D6 | OWNER-APPROVED 2026-11-03: two-way clustering, 30-cluster floor in both dimensions, KP mean-CAR test, calendar-time HAC(5), and 2,000-repetition calibration rule; scenario generator and FIQ-21 results remain NOT RUN |
| D7 | OWNER-APPROVED 2026-11-03: mechanical KAP disclosure-code classification; owner codes residual “other” blind to returns; no LLM; remaining classification evidence must be frozen |
| D8 | OWNER-APPROVED 2026-11-03: seed 20261102, 100 offsets, common session shift, event-level collision handling, negative control and reporting as §4; no simulation/placebo run |
| D9 | OWNER-APPROVED 2026-11-03: alpha 0.05, two-sided Holm, one terminal analysis through 2025-12-31, no equivalence test or sequential/size stopping. RQ3 remains planned, not dropped by default; exact treatment of an unavailable family member must be frozen before registration |
| D10 | PROPOSED / UNRESOLVED: immutable source manifest, rights/vintages, exposure assessment and exact execution gates; no access authorized here. Adopted OD-2 = B adds binding to an immutable study identity and a cross-study exposure ledger, whose location and schema are UNSET |

**D9 — OWNER-APPROVED 2026-11-03.** Use alpha 0.05 and two-sided Holm for the
planned RQ1 beta and eligible RQ3 delta; RQ3 is not dropped by default. No
equivalence margin/test. Use one fixed terminal analysis after all gates, with
observation end 2025-12-31; no sequential testing, significance stopping or sample-
size stopping. Freeze the exact treatment of an unavailable family member before
registration. An unavailable test is **UNAVAILABLE**, without an artificial
p-value or post-outcome family change. D6 safeguards apply to both slopes.
Placebo, lead-window negative control, mean-CAR and sensitivities are diagnostic;
report all attempts without confirmatory claims or significance rescue. RQ2 is
descriptive. Historical trials/exposure remain separate and append-only; reconcile
prior evaluated configurations under Charter §5.6. Unknown prior trial count is
UNSET, never zero. Selection corrections, exposure assessment and all governing
Charter conditions remain gates; no silent family change is allowed.

**2026 unregistered quarantine interval.** Records originally published from
2026-01-01 until the actual OSF registration timestamp belong to this explicitly
identified unregistered quarantine interval, not development, locked holdout or
forward confirmation. Later retrieval or correction does not reclassify original
publication time. No registration timestamp is set and this task grants no access
to or evaluation of the interval. Forward eligibility still requires separate
exposure and access assessment; no window-end-based reclassification is allowed.

Inherited methodological-source checks reported on 2026-10-25 by the source
commit (publisher/author/standard-setter pages or original papers; no empirical
FinanceIQ material). These checks were not rerun in this amendment:

- [Kolari & Pynnönen (2010), RFS 23:3996–4025](https://doi.org/10.1093/rfs/hhq072): verified publisher abstract on cross-sectional dependence and standardized mean-event tests; not a justification for a SUE regression test.
- [Cameron, Gelbach & Miller (2006), NBER t0327](https://www.nber.org/papers/t0327): verified multiway covariance proposal; cluster floor here is a design proposal, not a theorem from that paper.
- [Brown & Warner (1985), JFE 14:3–31](https://doi.org/10.1016/0304-405X(85)90042-X): verified publisher abstract; supports considering daily-return variance/autocorrelation, not study-specific power claims.
- [Holm (1979), SJS 6:65–70](https://www.jstor.org/stable/4615733): bibliography confirmed in the indexed [original-paper copy](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf). Full-text retrieval failed; methodological verification remains **UNVERIFIED** before registration. The approved family still requires governing trial/exposure reconciliation.
- [IFRS IAS 29](https://www.ifrs.org/issued-standards/list-of-standards/ias-29-financial-reporting-in-hyperinflationary-economies/): verified current-unit and comparative-restatement requirements. Turkish issuer-specific application and historical basis metadata remain unverified.
- [Borsa İstanbul market functioning](https://www.borsaistanbul.com/en/markets/equity-market/market-functioning): verified distinction between closing-price determination and subsequent fixed-price trades. Historical calendars and KAP timestamp semantics remain unverified; operational alignment is gated.

Owner approval is a scientific design disposition, not source validation.
Thresholds and remaining choices keep their status in the decision table.

### Inherited v0.2 source register — checks reported by source commit on 2026-10-26

The following source-check statuses are inherited from `a66ee4f4`, not independently
rechecked in this owner-decision amendment. No study data was acquired.

- **VERIFIED regulation:** [KGK original announcement, points 1–2](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/Diger/Enf_%20Muh_%20Duyuru_ESEB.pdf), dated/corroborated by [KGK 2024-32, 25 April 2024](https://www.kgk.gov.tr/ContentAssignmentDetail/4997/Finansal-Tablo-O%CC%88rnekleri-ve-Kullan%C4%B1m-Rehberine-I%CC%87lis%CC%A7kin-Deg%CC%86is%CC%A7iklikler-Resmi-Gazetede-Yay%C4%B1mlanm%C4%B1s%CC%A7t%C4%B1r-). It establishes a general annual transition with regulator exceptions, not uniform issuer histories.
- **VERIFIED SPK corroboration:** [official 2024/6 bulletin, p.16, item 2](https://spk.gov.tr/data/65b2beba8f95db1f44c2b15a/2024-6.pdf) explicitly identifies 28 December 2023 decision 81/1820, annual FY2023 start and added annual/interim reporting time. No actual KAP filing or deadline-based publication timestamp was inferred.
- **VERIFIED IAS29 measurement rule:** [IFRS standard-setter summary](https://www.ifrs.org/issued-standards/list-of-standards/ias-29-financial-reporting-in-hyperinflationary-economies/) requires current purchasing-power units, including comparatives, using a general price index. It does not validate this study's CPI forecast or issuer comparability.
- **VERIFIED bibliography/abstract; exact drift attribution UNVERIFIED:** Foster (1977), *The Accounting Review* 52(1), 1–21, [original paper, university-hosted copy](https://faculty.utrgv.edu/diego.escobari/teaching/Econ8375/Papers/2018-Auto2-Norman.pdf), stable identifier JSTOR 246028. Abstract supports seasonal and adjacent-quarter components; later full-text access timed out. The simple drift candidate and its training rule remain a study proposal, not a claimed exact Foster replication.
- **VERIFIED bibliography and related formula:** Livnat & Mendenhall (2006), *JAR* 44(1), 177–205, [publisher](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1475-679X.2006.00196.x). The [author's 9 April 2004 working draft, §3.2, Eq.(1), p.16](https://pages.stern.nyu.edu/~jlivnat/jar%20resubmit.pdf) uses seasonal EPS change / quarter-end share price, with split adjustments. It is not the final published text and does not validate total earnings / fiscal-quarter-end capitalization, IAS29 conversions or a 2025Q1 start.
- **VERIFIED platform only:** [CBRT 26 January 2026 EVDS announcement](https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB%2BEN/Main%2BMenu/Announcements/Press%2BReleases/2026/ANO2026-03) describes metadata and release-calendar features. No series values queried. Two-year yield access, indicative-series identity, historical policy/CPI vintages and PIT completeness are **UNVERIFIED**; do not treat the platform announcement as evidence of a historical series.

**v0.3 source recheck, 2026-10-29 (text extracted from the official PDFs; no
study data):** [SPK bulletin 2024/6, dated 25/01/2024, p.16 item 2](https://spk.gov.tr/data/65b2beba8f95db1f44c2b15a/2024-6.pdf)
VERIFIED: decision 81/1820 of 28.12.2023 applies TMS 29 from annual reports for
periods ending 31.12.2023 and grants 10 extra weeks for annual and 6 for the first
two interim reports. [KGK announcement](https://www.kgk.gov.tr/Portalv2Uploads/files/Duyurular/v2/Diger/Enf_%20Muh_%20Duyuru_ESEB.pdf)
points 1–2 VERIFIED as summarized above; the PDF body prints no date, so
23 November 2023 rests on file metadata plus the REPORTED KGK 2024-32 corroboration.

Only the owner decisions itemized above are approved. Remaining D decisions,
remaining FIQ-06 evidence gates (source adequacy, window, strata) and the
unresolved FIQ-11 I-items, per-target `D_i` content under OD-6,
rights/PIT lineage, FIQ-07/08/12, KER-07/09 and relevant return/calendar transport,
then separately authorized FIQ-20/21 and FO-7 registration remain dependencies.
