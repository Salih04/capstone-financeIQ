# Paper 2 — outcome-blind owner decision batch

2026-11-02, Europe/Zurich · Queue 2 · **PROPOSED / ALL NEW CHOICES UNSET**.
Research support only; not investment advice. A single sitting can approve the
recommendations, except where a row explicitly retains an evidence dependency.
Approval of a recommendation is not evidence closure, registration or execution.

Authority: latest owner Work Mode instruction; live main
`a8f190491ad466c2f92a21b9c3f938f7a5f89be3`, [Charter](../process/RESEARCH_CHARTER.md),
[adopted addendum](../research/OWNER_DECISION_ADDENDUM.md),
[DESIGN v0.3](DESIGN.md), [OSF draft](OSF_PREREGISTRATION_DRAFT.md), and
[25-row readiness matrix](REGISTRATION_READINESS_AUDIT.md#5-registration-gate-and-decision-matrix).
The PR #61 status document was read at `c85ed06e`; its 20-gate summary is dated
evidence, not a replacement for that matrix. This document changes neither
DESIGN nor OSF fields. On adoption they must be synchronized in one exact
freeze commit; the adopted D3/D5/D9 and narrow D2/D4/D8 approvals remain intact.

## Batch A — ten recommendations

| Gate | Recommended default for owner approval | Why / consequence | Decision |
| --- | --- | --- | --- |
| G01 / D1 | One historical, explicitly semi-clean associational opening. Candidate event-publication interval 2023-01-01 through 2025-12-31; every outcome dependency must end by 2025-12-31. Candidate development interval 2017-01-01 through 2022-12-31, conditional on an adopted U1 feasible window; no presumed coverage. Primary non-financial U1, holdings flagged, financials descriptive only. | Uses existing FO-0 boundaries without moving them. Band/straddle exclusions still apply. No later forward look is granted to this study; forward confirmation needs a distinct authorized registration and exposure assessment. Operational U1 hash, strata mapping and actual feasibility remain UNSET. | UNSET |
| G04 / D2 | CAR[0,+1] primary, [-1,+1] wider-window diagnostic. Session 0 is the first historical price-setting close strictly after the evidenced KAP publication time. Use versioned BIST calendars including half-days, auctions, closures and historical Europe/Istanbul offsets. Date-only, unknown offset/precision or unresolved close ties are unalignable. | Preserves the proposed estimand and approved sensitivity. Intraday events include pre-announcement movement; no instantaneous-response interpretation. Calendar/export ID and timestamp semantics remain UNSET until G05 evidence. | UNSET |
| G06 / D3 operations | Official headline all-items monthly CPI, non-seasonally adjusted, with its exact series/base/units frozen after metadata verification; reference months are each fiscal quarter's end month, as approved D3. Use the version actually public strictly before the event, not today's revised history. Shares must be security-class- and date-valid, known at quarter end; require an actual trade on that quarter's last scheduled session, with evidenced price/action/share basis. No carry-forward price or current-share substitution. | Keeps the approved CPI seasonal formula exactly. Unknown or incompatible vintage/basis makes the observation unavailable. Exact CPI/export/share IDs are UNSET and are evidence gates, not numbers to invent. This recommendation alone cannot close G06. | UNSET |
| G07 / D4 | Retain the approved whole-study rate priority: two-year TRY yield, then evidenced EVDS benchmark, then policy-rate change, chosen only by separately authorized outcome-free feasibility. Freeze daily OLS/intercept on [-250,-31], minimum 160 complete rows, full-rank matrix and positive residual variance. Market factor: broad BIST total return less risk-free; FX: daily log USD/TRY change; flows: the published weekly signal and eight-prior-release scaling exactly as DESIGN, never backdated/interpolated. Risk-free: evidenced TRY one-session holding return, in simple daily units; an annual quote is unusable until its day-count/compounding conversion is frozen. | Maintains one economic specification for all events; no fit-driven fallback or silent factor deletion. LSEG primary, DataStore cross-check, Yahoo dev-only is settled. Exact series IDs, rate quote conversion, vintage/release support and usable factor transport remain UNSET. If any required factor is unavailable, RQ2 is unavailable. | UNSET |
| G10 / D6 | Issuer × session two-way clustered slope inference, two-sided 95% intervals, minimum 30 clusters in each dimension for both RQ1 and RQ3. Below the floor: estimates only, no confirmatory significance claim. KP test only for mean CAR with valid pre-event correlation estimates; equal-weight calendar-time HAC(5) diagnostic. Before FIQ-21: freeze 2,000 null repetitions, seed 20261102, development-only synthetic/pseudo-event calibration; proposed acceptance: upper two-sided 95% binomial interval for null rejection rate ≤7.5% at nominal 5%, for every predeclared null scenario. | The floor and 7.5% tolerance are proposed design judgments, not theorems or measured calibration. Define the complete null-scenario generator before authorizing simulation; do not select scenarios after seeing size. Failures block asymptotic confirmatory inference; no retuning floor or replacing tests on true event outcomes. G11 remains NOT RUN. | UNSET |
| G12 / D7 | One issuer/period first filing; simultaneous duplicates collapse with all lineage retained. Same-issuer overlapping primary windows: exclude both from isolated-event primary. Co-announcement taxonomy: dividends/distributions; share/rights actions; mergers/acquisitions; trading-status changes. Blind human coding of timestamped metadata before returns, with an adjudicator recording disagreement; unresolved coding excluded with reason. No LLM coding in the default. Full eligible-event sample is diagnostic; no winsorization or return-driven exclusion. | Keeps mechanical exclusion independent of signs and significance. Missingness affects only the analysis needing the field; formation members survive exits/delistings. Taxonomy version and exact coding record must be frozen. Any later LLM choice reopens OD-5 non-leakage requirements prospectively. | UNSET |
| G13 / D8 | Seed 20261102; pin runtime and sampling algorithm. Draw 100 distinct integer session offsets without replacement from [-120,-21] ∪ [21,120]. In each repetition use one common shift across issuers' development calendars. Apply fixed boundary/own-issuer collision rules event by event, dropping both conflicting pair members. No reroll/replacement for empty or unusable repetitions. Negative control CAR[-20,-11]. | Preserves the approved common-shift and collision amendments. Boundary attrition and resulting cluster changes are reported for all attempts. These are diagnostics; no placebo, negative-control or simulation is run by this document. | UNSET |
| G14 / D9 | Alpha 0.05, two-sided Holm on RQ1 beta and eligible RQ3 delta, or RQ1 alone if RQ3 excluded prospectively. No equivalence margin/test. One fixed terminal analysis after all gates, on the frozen 2025-12-31 observation end; no sequential testing, sample-size stopping or optional extension. | D9's family is already approved, not newly enlarged. Default for G09: if separately authorized eligibility evidence is unavailable, exclude RQ3 before registration, record NOT ESTIMABLE / forward-study candidate. Owner must explicitly adopt that disposition; missing counts never imply threshold passage. Unavailable tests remain UNAVAILABLE. | UNSET |
| G16 / OD-6 | Separate full immutable lineage from target dependency D_i. For each CAR target include all price endpoints, action/dividend/terminal-proceeds facts used in its return construction and all in-window factor/risk-free realizations used to define abnormal return. Start with the earliest such dependency; complete at the latest first-publication/availability bound. Pre-outcome benchmark estimation data remain outside D_i under adopted OD-6(c). Recommend also keeping genuinely pre-outcome surprise inputs and the fixed pre-event flow-scaling history in predictor lineage rather than D_i; late/revised input that enters an outcome computation must be included. | The last recommendation is a NEW owner choice, not implied by OD-6(c). All predictor/estimation reads retain PIT and protected-access checks even when outside D_i. No source can be hidden from access/exposure logs by this classification. Freeze D_i separately for primary, wider and lead windows; exclude band observations per adopted OD-6(a)/(b). | UNSET |
| G17 / straddles | Exclude locked-period observations whose D_i includes any first-publication dependency on/after 2026-01-01. Do not move them into development or forward confirmation. Freeze original public versions; a later correction cannot retroactively make an event eligible or clean. If a required correction moves b* across a boundary, append the revision and exclude/fail closed; do not rerun or silently overwrite. Registration-day timestamps require a separate G22 disposition. | No band sensitivity or quarantine access. Count only through a separately authorized exact aggregation route; otherwise counts remain UNSET/NOT EVALUATED. The four OD-1 aggregates are not blanket authorization for these counts. | UNSET |

## Batch B — optional RQ2 macro extension (separate choice)

**Recommended default: OFF; owner choice UNSET.** Preserve the original
four-factor RQ2 as the descriptive primary. Do not add factors because they
explain observed events better.

If ON, register ONE labelled descriptive extension before any outcome access:
policy-rate **surprise**, Turkey five-year sovereign CDS change and the existing
USD/TRY change. Reuse the existing FX column once; never duplicate it. Retain
the original yield factor and disclose the different economic roles of a yield
change, an expectation innovation, CDS and FX. Full-rank failure makes the
extension unavailable; do not delete a collinear column after seeing fit.

- Policy surprise = announced policy decision minus the expectation recorded
  publicly and immutably before the announcement. Candidate default: archived
  pre-meeting survey median for the same instrument, measured in percentage
  points. Exact instrument, source ID, cutoff and revision rules are UNSET.
  An actual policy-rate change is not automatically a surprise. If no valid
  expectation exists, omit the entire optional extension, not substitute zero.
- CDS: fixed five-year Turkey sovereign contract, quote side, currency and
  restructuring clause; first difference in basis points at evidenced daily
  quote timestamps. LSEG is the intended primary transport, not proof of rights
  or quote availability. No splicing conventions are inferred.
- Map surprises only after public announcement; on an evidenced scheduled day
  without a meeting set policy-news impulse to zero (a structural event rule,
  not imputation). Unknown meeting coverage is null. The coefficient is
  estimable only with a predeclared minimum of 20 evidenced decisions in the
  pre-event estimation window; otherwise extension unavailable. This proposed
  minimum is a design choice and may make the daily extension infeasible.
  No interpolation, backward assignment, or later-vintage innovation fitting.
- Freeze factor normalization on pre-event training data only, source hashes,
  calendars, frequency alignment, missing rules and D_i under G16. Report all
  contributions and failures; no causal decomposition, added confirmatory
  hypothesis or rescue of RQ1/RQ3 by significance. If inferential testing is
  later requested, prospectively amend multiplicity before viewing outcomes.

## Batch C — record and residual gates

Owner may record `A: approve defaults / exceptions: ...; B: OFF or ON; C:
authorize synchronization only`, with actual timestamp and signature. All
three fields currently **UNSET**. No silence or elapsed time is approval.

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
