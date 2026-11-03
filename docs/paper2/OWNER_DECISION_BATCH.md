# Paper 2 — outcome-blind owner decision batch

Originating recommendations: 2026-11-02 · Queue 2 · **OWNER DECISIONS RECORDED 2026-11-03**.
Research support only; not investment advice. A single sitting can approve the
recommendations, except where a row explicitly retains an evidence dependency.
Approval of a recommendation is not evidence closure, registration or execution.

Authority: explicit owner message recorded 2026-11-03 21:24:35 Europe/Zurich; live main
`90d10f7c388c45bf41b7a9e5e5f5204a9de51b6d`, [Charter](../process/RESEARCH_CHARTER.md),
[adopted addendum](../research/OWNER_DECISION_ADDENDUM.md),
[DESIGN v0.4](DESIGN.md), [OSF draft v0.4](OSF_PREREGISTRATION_DRAFT.md), and
[25-row readiness matrix](REGISTRATION_READINESS_AUDIT.md#5-registration-gate-and-decision-matrix).
The PR #61 status document was read at `c85ed06e`; its 20-gate summary is dated
evidence, not a replacement for that matrix. The owner approved Batch A’s ten
recommendations with the G12 and G14/G09 amendments below, selected Batch B ON
for CDS only, and authorized Batch C to synchronize DESIGN and OSF in one freeze
commit. These approvals are design decisions only; no outcomes, analysis,
simulation, registration or OSF submission are authorized.

## Batch A — ten recommendations

| Gate | Owner-approved disposition | Why / consequence | Decision |
| --- | --- | --- | --- |
| G01 / D1 | One historical, explicitly semi-clean associational opening. Candidate event-publication interval 2023-01-01 through 2025-12-31; every outcome dependency must end by 2025-12-31. Candidate development interval 2017-01-01 through 2022-12-31, conditional on an adopted U1 feasible window; no presumed coverage. Primary non-financial U1, holdings flagged, financials descriptive only. | Uses existing FO-0 boundaries without moving them. Band/straddle exclusions still apply. No later forward look is granted to this study; forward confirmation needs a distinct authorized registration and exposure assessment. Operational U1 hash, strata mapping and actual feasibility remain UNSET. | APPROVED — 2026-11-03 |
| G04 / D2 | CAR[0,+1] primary, [-1,+1] wider-window diagnostic. Session 0 is the first historical price-setting close strictly after the evidenced KAP publication time. Use versioned BIST calendars including half-days, auctions, closures and historical Europe/Istanbul offsets. Date-only, unknown offset/precision or unresolved close ties are unalignable. | Preserves the proposed estimand and approved sensitivity. Intraday events include pre-announcement movement; no instantaneous-response interpretation. Calendar/export ID and timestamp semantics remain UNSET until G05 evidence. | APPROVED — 2026-11-03 |
| G06 / D3 operations | Official headline all-items monthly CPI, non-seasonally adjusted, with its exact series/base/units frozen after metadata verification; reference months are each fiscal quarter's end month, as approved D3. Use the version actually public strictly before the event, not today's revised history. Shares must be security-class- and date-valid, known at quarter end; require an actual trade on that quarter's last scheduled session, with evidenced price/action/share basis. No carry-forward price or current-share substitution. | Keeps the approved CPI seasonal formula exactly. Unknown or incompatible vintage/basis makes the observation unavailable. Exact CPI/export/share IDs are UNSET and are evidence gates, not numbers to invent. This recommendation alone cannot close G06. | APPROVED — 2026-11-03 |
| G07 / D4 | Retain the approved whole-study rate priority: two-year TRY yield, then evidenced EVDS benchmark, then policy-rate change, chosen only by separately authorized outcome-free feasibility. Freeze daily OLS/intercept on [-250,-31], minimum 160 complete rows, full-rank matrix and positive residual variance. Market factor: broad BIST total return less risk-free; FX: daily log USD/TRY change; flows: the published weekly signal and eight-prior-release scaling exactly as DESIGN, never backdated/interpolated. Risk-free: evidenced TRY one-session holding return, in simple daily units; an annual quote is unusable until its day-count/compounding conversion is frozen. | Maintains one economic specification for all events; no fit-driven fallback or silent factor deletion. LSEG primary, DataStore cross-check, Yahoo dev-only is settled. Exact series IDs, rate quote conversion, vintage/release support and usable factor transport remain UNSET. If any required factor is unavailable, RQ2 is unavailable. | APPROVED — 2026-11-03 |
| G10 / D6 | Issuer × session two-way clustered slope inference, two-sided 95% intervals, minimum 30 clusters in each dimension for both RQ1 and RQ3. Below the floor: estimates only, no confirmatory significance claim. KP test only for mean CAR with valid pre-event correlation estimates; equal-weight calendar-time HAC(5) diagnostic. Before FIQ-21: freeze 2,000 null repetitions, seed 20261102, development-only synthetic/pseudo-event calibration; acceptance: upper two-sided 95% binomial interval for null rejection rate ≤7.5% at nominal 5%, for every predeclared null scenario. | The floor and 7.5% tolerance are approved design judgments, not theorems or measured calibration. Define the complete null-scenario generator before any simulation; do not select scenarios after seeing size. Failures block asymptotic confirmatory inference; no retuning floor or replacing tests on true event outcomes. G11 remains NOT RUN. | APPROVED — 2026-11-03 |
| G12 / D7 | One issuer/period first filing; simultaneous duplicates collapse with all lineage retained. Same-issuer overlapping primary windows: exclude both from isolated-event primary. Mechanically classify co-announcements from evidenced KAP disclosure-type codes using the frozen taxonomy. Only residual “other” items are coded by the owner blind to returns; record disagreements and unresolved items, and exclude unresolved coding by reason. No LLM coding. Full eligible-event sample is diagnostic; no winsorization or return-driven exclusion. | Classification remains outcome-blind. Missingness affects only the analysis needing the field; formation members survive exits/delistings. Taxonomy version, code mapping and exact coding record remain evidence gates. | APPROVED WITH AMENDMENT — 2026-11-03 |
| G13 / D8 | Seed 20261102; pin runtime and sampling algorithm. Draw 100 distinct integer session offsets without replacement from [-120,-21] ∪ [21,120]. In each repetition use one common shift across issuers' development calendars. Apply fixed boundary/own-issuer collision rules event by event, dropping both conflicting pair members. No reroll/replacement for empty or unusable repetitions. Negative control CAR[-20,-11]. | Preserves the approved common-shift and collision amendments. Boundary attrition and resulting cluster changes are reported for all attempts. These are diagnostics; no placebo, negative-control or simulation is run by this document. | APPROVED — 2026-11-03 |
| G14 / D9 and G09 | Alpha 0.05; two-sided Holm for RQ1 beta and eligible RQ3 delta. RQ3 is not dropped by default. No equivalence margin/test. One fixed terminal analysis after all gates, with observation end 2025-12-31; no sequential testing, sample-size stopping or optional extension. Outcome-free RQ3 eligibility counts are authorized now: IAS 29-basis event count, distinct issuers, and distinct event sessions only. | Authorization does not establish source facts or threshold passage. Kernel request #24 is open. If facts are unavailable, mark counts and affected eligibility UNAVAILABLE; do not inspect returns, prices or CARs or automatically drop RQ3. Unavailable tests receive no artificial p-value; freeze family handling before registration without post-outcome changes. | APPROVED WITH AMENDMENT — 2026-11-03 |
| G16 / OD-6 | Separate full immutable lineage from target dependency D_i. For each CAR target include all price endpoints, action/dividend/terminal-proceeds facts used in its return construction and all in-window factor/risk-free realizations used to define abnormal return. Start with the earliest such dependency; complete at the latest first-publication/availability bound. Pre-outcome benchmark estimation data remain outside D_i under adopted OD-6(c). Keep genuinely pre-outcome surprise inputs and fixed pre-event flow-scaling history in predictor lineage rather than D_i; late/revised input that enters an outcome computation must be included. | The owner approved this lineage rule on 2026-11-03; it is not implied by OD-6(c). All predictor/estimation reads retain PIT and protected-access checks even when outside D_i. No source can be hidden from access/exposure logs by this classification. Freeze D_i separately for primary, wider and lead windows; exclude band observations per adopted OD-6(a)/(b). | APPROVED — 2026-11-03 |
| G17 / straddles | Exclude locked-period observations whose D_i includes any first-publication dependency on/after 2026-01-01. Do not move them into development or forward confirmation. Freeze original public versions; a later correction cannot retroactively make an event eligible or clean. If a required correction moves b* across a boundary, append the revision and exclude/fail closed; do not rerun or silently overwrite. Registration-day timestamps require a separate G22 disposition. | No band sensitivity or quarantine access. G17 band/straddle counts remain UNSET/NOT EVALUATED without separate authorization. The owner separately authorized only the exact G09 eligibility aggregates; no G17 straddle/quarantine count is authorized. | APPROVED — 2026-11-03 |

## Batch B — optional RQ2 macro extension

**OWNER-APPROVED ON — CDS ONLY (2026-11-03).** Preserve the original
four-factor RQ2 as the descriptive primary. The labelled descriptive extension
adds the daily change in Turkey five-year sovereign CDS and reuses the existing
USD/TRY FX column exactly once. Do not add factors based on observed event
outcomes. The policy-rate surprise is **EXCLUDED**: the minimum 20 evidenced
decisions in `[-250,-31]` is infeasible and no immutable pre-meeting expectation
archive exists. Do not substitute actual rate changes, another expectation
source, or another CDS source. This exclusion applies to the optional surprise
extension; the separately approved D4 risk-free-rate hierarchy is unchanged.

LSEG CDS availability and rights must be established before registration. If the
LSEG CDS series is unavailable before registration, mark the extension
**UNAVAILABLE**; no post-hoc fallback or substitution is permitted. Exact
contract, quote side, currency, restructuring clause, daily timestamps, units,
calendar/frequency alignment, missing rules, PIT lineage and rights remain
evidence gates. Full-rank failure also makes the extension unavailable; do not
delete a collinear column after seeing fit. No outcome access, acquisition,
normalization fit or execution is authorized by this decision.

## Batch C — record and residual gates

Owner decision recorded 2026-11-03 21:24:35 Europe/Zurich:
`A: approved, with G12 and G14/G09 amendments; B: ON, CDS only; C: synchronize
DESIGN and OSF in one freeze commit.` This authorization covers documentation
synchronization only. Separately, G14/G09 authorizes only the three
outcome-free eligibility aggregates specified above; [Kernel request #24](https://github.com/Salih04/financeiq-pit-kernel/issues/24)
is open with no response or counts. No additional Kernel planning/edits, data
acquisition, outcome access, study execution or OSF submission is authorized.

Even full batch approval does not close G02/03/05/08/09/11/15/18/19/20/21/22/23/25.
G20 must reference the already CLOSED KAP/BIST-announcement/3184 rights decisions
without reopening them; remaining price/macro product uses require applicable
evidence. G25 in-opening benchmark estimation is still an explicit confirmation
gate. Exact metadata/series IDs, classification evidence, trial/exposure inventory,
operational access controls, independent review and owner FO-7 remain required.
No fabricated counts, measurements, data acquisition, Kernel planning/edits,
protected reads, outcomes, OSF action or experiments occurred here.

Exposure: existing capstone aggregates in required context and historical Paper 1
text were already seen; no zero-prior-exposure claim. This batch used only
method/governance documents for Paper 2, not its empirical inputs or outcomes.
