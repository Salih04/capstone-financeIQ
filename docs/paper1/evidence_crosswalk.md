# Paper 1 evidence and citation crosswalk

## Version and access boundary

Fresh main base: `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
Verified local prerequisite: `7b444a35298f7b04012d818ff70fcbc57b85d6b3`,
which has main as its immediate parent and is not assumed merged. The FIQ-15
branch starts from this preparation commit, preserving its source artifacts.
`RESULTS.md` and `experiments/results_pit_v2/REPORT.md` are byte-identical to
main. Both last changed at `ae97a9ffa38e607a26846dfd732057ab72c56be2`.
The report identifies the run commit as
`079bb832b8f9466ab70ae6ef4d60c02cd3080875`; that is distinct from the source
snapshot, manuscript commit, and any future integration SHA.

Only those two frozen documents supply empirical outcome numbers. The live
owner explicitly also authorizes cohort/selection disclosure and the existing
single-date FIQ-16 overlap; these non-outcome quantities are sourced separately
below. Governance dates come from the adopted Charter/addendum; literature years
and the accounting-lag convention come from verified bibliography/primary text.
Identifiers (PIT-v2, U1, FIQ-17), citation-note labels, and commit strings are not
estimated quantities. No outcome values are sourced from an old chat, context
summary, report.json, another report, protected data, or Kernel internals.

Each manuscript evidence note resolves to an entry below. The companion
[evidence_crosswalk.json](evidence_crosswalk.json) stores exact source excerpts,
full commits, line ranges and SHA-256 identities. Published main sources use
commit permalinks; unpushed preparation sources use local relative links with
explicit Git object identities. Their GitHub availability is not claimed.
Reopen those exact versions with `git show COMMIT:PATH`. Source locations are at their
pinned commits, not mutable working-tree line numbers. Every numerical table
cell, repeated abstract/body statistic, sample count, calendar date, numeric
threshold and control rate was checked against its entry. Written-out counts
(e.g. three, six, five) were reviewed semantically as well. This is transcription
verification, not statistical validation or independent review.

## Numeric evidence and bounded factual claims

### N01

**Claim:** 81 firms; 40 reported; selected in 2026 from then-current listings.

**Limit:** 40 reported is an explicitly authorized FIQ-16/Charter scope fact, not a newly read outcome. Selection mechanism beyond the frame remains undocumented.

- [`RESULTS.md`, lines 123-131](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L123-L131); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/paper1/survivorship_bound.md`, lines 11-30](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### N02

**Claim:** Original +0.150, p 0.017; corrected +0.031, p 0.63, 95 % CI −0.100 … +0.162.

**Limit:** Separate historical and corrected estimates; no subtraction or isolated causal attribution.

- [`RESULTS.md`, lines 39-51](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L39-L51); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`experiments/results_pit_v2/REPORT.md`, lines 13-24](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L13-L24); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N03

**Claim:** No secondary ML result distinguishable after its reported family adjustment.

**Limit:** Post-hoc within-year-null comparison, not proof of no predictability.

- [`experiments/results_pit_v2/REPORT.md`, lines 26-35](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L26-L35); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N04

**Claim:** Minimum detectable |IC| 0.185 at 80 % power.

**Limit:** Analytic design sensitivity, not a confidence bound.

- [`RESULTS.md`, lines 108-119](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L108-L119); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`experiments/results_pit_v2/REPORT.md`, lines 21-24](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L21-L24); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N05

**Claim:** Historical audit found timing, adjustment-basis and pre-listing defects; old interpretation withdrawn.

**Limit:** Qualitative synthesis of the authorized results summary.

- [`RESULTS.md`, lines 50-86](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L50-L86); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N06

**Claim:** 81 firms; 2020–2025; 40 reported; 40 original features; nominal-TRY calendar-year target.

**Limit:** Panel scope is not historical index eligibility. Reported-cohort fact is authorized FIQ-16 evidence.

- [`RESULTS.md`, lines 20-33](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L20-L33); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/paper1/survivorship_bound.md`, lines 11-12](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### N07

**Claim:** FY2020–2024; 323 published rows; 308 evaluated; 11 pre-listing exclusions; 4 jump exclusions; ±25 %.

**Limit:** Whole-panel counts, not summed test observations; exclusions are registered historical choices, not an endorsement of outcome-based filtering.

- [`experiments/results_pit_v2/REPORT.md`, lines 75-86](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L75-L86); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N08

**Claim:** FY2022, FY2023, FY2024: 78, 78, 79 test firms.

**Limit:** Do not call all 308 panel rows out-of-sample tests.

- [`experiments/results_pit_v2/REPORT.md`, lines 9-11](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L9-L11); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N09

**Claim:** Market-value valid 164; exclusions 27 and 5; unavailable 123.

**Limit:** Feature availability categories differ from whole-row exclusions.

- [`experiments/results_pit_v2/REPORT.md`, lines 77-86](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L77-L86); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N10

**Claim:** Original calendar test years 2023–2025; three rank baselines; six named ML models.

**Limit:** Three/six written in words preserve source counts.

- [`RESULTS.md`, lines 24-33](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L24-L33); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N11

**Claim:** Within-year Spearman IC; equal-weighted year mean; permutation/bootstrap; Bonferroni over six; original unregistered.

**Limit:** Methods reported, not freshly reproduced.

- [`RESULTS.md`, lines 27-33](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L27-L33); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N12

**Claim:** Original baseline +0.150 (0.017); random forest −0.153 (0.018; adjusted 0.11); ridge +0.093 (0.157; adjusted 0.94).

**Limit:** Only explicitly discussed original values enter the manuscript; historical predictive interpretation withdrawn.

- [`RESULTS.md`, lines 39-51](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L39-L51); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N13

**Claim:** 31 of 40 features; 60–70 days; FY2023 deadline 20 May 2024; SASA FY2022 deadline 10 May 2023.

**Limit:** Historical deadline assertions transcribed from RESULTS; no new legal/regulatory claim or filing census.

- [`RESULTS.md`, lines 53-60](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L53-L60); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N14

**Claim:** 14 pre-listing labels; five duplicate placeholder returns of 56.947991 %.

**Limit:** Original labelled-panel audit, distinct from PIT-v2 11 row exclusions.

- [`RESULTS.md`, lines 61-68](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L61-L68); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N15

**Claim:** 31 May following-year primary cutoff; exact dates for 6 company-years; actual mode not full-universe run.

**Limit:** Deadline approximation does not certify every actual publication time.

- [`RESULTS.md`, lines 70-86](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L70-L86); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N16

**Claim:** FY2022 → 1 June 2023; FY2023 → 3 June 2024; FY2024 → 2 June 2025.

**Limit:** Prediction dates transcribed, no calendar recomputation.

- [`experiments/results_pit_v2/REPORT.md`, lines 9-11](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L9-L11); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N17

**Claim:** Primary +0.031; p 0.63; 95 % CI −0.100 … +0.162; yearly +0.145, −0.051, −0.000 for FY2022–FY2024.

**Limit:** Preserve rounded negative zero; CI is not an equivalence interval.

- [`experiments/results_pit_v2/REPORT.md`, lines 13-24](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L13-L24); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N18

**Claim:** All six secondary rows (model, IC, raw p, Bonferroni p) exactly transcribed.

**Limit:** No new model ranking or secondary-family recalculation.

- [`experiments/results_pit_v2/REPORT.md`, lines 26-35](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L26-L35); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N19

**Claim:** Pre-publication statements diagnostic +0.193 (0.002); PIT statement-only +0.041 (0.54).

**Limit:** Same accounting periods but different return window/source/rows; no causal timing estimate.

- [`experiments/results_pit_v2/REPORT.md`, lines 54-73](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L54-L73); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N20

**Claim:** Earlier cutoff +0.102 (0.12); no-market-value +0.044 (0.50); price-only −0.004 (0.95).

**Limit:** Registered descriptive sensitivities; no winning-specification selection.

- [`experiments/results_pit_v2/REPORT.md`, lines 37-45](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L37-L45); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N21

**Claim:** Statement-only RF −0.176; raw p 0.007; adjusted 0.041; four sensitivities, 24 ML tests.

**Limit:** Whole sensitivity-family non-survival is reported, not calculated here; no inverse strategy.

- [`experiments/results_pit_v2/REPORT.md`, lines 37-52](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L37-L52); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N22

**Claim:** 2020-10-01: 100 snapshot codes; 60 in training list; 40 outside.

**Limit:** Explicit owner-authorized count exception to outcome-only sources: existing FIQ-16 literal-code snapshot. Not annual/issuer-equivalent/U1 admission, not 40 delistings, not an effect size.

- [`docs/paper1/survivorship_bound.md`, lines 38-64](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/survivorship_count_evidence.json`, lines 1-28](survivorship_count_evidence.json); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### N23

**Claim:** 0.185 at 80 % power; design summary three years × 78.

**Limit:** Design approximation retained alongside actual 78,78,79 cross-sections; no analytic recalculation.

- [`RESULTS.md`, lines 108-119](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L108-L119); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N24

**Claim:** 200 positive repetitions; detection 0 %,17 %,62 %,93 % at IC 0.1,0.2,0.3,0.4; 1,000 negative repetitions each; FPR 2.8 %,2.6 % at 5 %.

**Limit:** Historical published-harness controls, not newly run PIT-v2 simulations or independently verified calibration.

- [`RESULTS.md`, lines 108-119](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L108-L119); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N25

**Claim:** Original timing guard did not detect leakage; PIT guard checks timestamps.

**Limit:** A reported defect-control distinction; no fresh test success claimed.

- [`RESULTS.md`, lines 110-115](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L110-L115); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### N26

**Claim:** Deadline approximation, market-value coverage, high-inflation nominal-TRY sample, exposed forward registration.

**Limit:** Limitations are inherited or explicitly methodological reasoning, not new estimated effects.

- [`RESULTS.md`, lines 121-131](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L121-L131); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### P01

**Claim:** Feature registry, timestamp/label guards, target window, adjustment-basis handling, null policy.

**Limit:** Methods only. No numeric outcome borrowed from protocol; methods described rather than rerun. Legacy protocol §7 overbroad suspension wording is not imported.

- [`docs/PIT_PROTOCOL.md`, lines 10-16](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PIT_PROTOCOL.md#L10-L16); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/PIT_PROTOCOL.md`, lines 69-102](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PIT_PROTOCOL.md#L69-L102); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/PIT_PROTOCOL.md`, lines 104-144](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PIT_PROTOCOL.md#L104-L144); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/PIT_PROTOCOL.md`, lines 158-167](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PIT_PROTOCOL.md#L158-L167); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/process/RESEARCH_CHARTER.md`, lines 120-127](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/process/RESEARCH_CHARTER.md#L120-L127); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`experiments/pit/guard.py`, lines 1-11](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/pit/guard.py#L1-L11); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`tests/test_pit_guard.py`, lines 1-6](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/tests/test_pit_guard.py#L1-L6); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### P02

**Claim:** Post-hoc chronology and registration commit 079bb832b8f9466ab70ae6ef4d60c02cd3080875; prior forward exposure.

**Limit:** Report attributes its run to that clean commit. Git object resolves; no new run or claim of independent blinded confirmation.

- [`experiments/results_pit_v2/REPORT.md`, lines 1-7](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L1-L7); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/PREREGISTRATION_AMENDMENT_2026-10-04.md`, lines 1-17](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PREREGISTRATION_AMENDMENT_2026-10-04.md#L1-L17); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/PREREGISTRATION_AMENDMENT_2026-10-04.md`, lines 68-106](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/PREREGISTRATION_AMENDMENT_2026-10-04.md#L68-L106); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`RESULTS.md`, lines 131-131](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/RESULTS.md#L131-L131); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### P03

**Claim:** Manifests referenced but not opened; frozen input requirement and fresh-fetch instability.

**Limit:** Only authorized RESULTS and exact PIT-v2 REPORT were read as outcome evidence. No report.json or other result file inspection.

- [`experiments/results_pit_v2/REPORT.md`, lines 3-7](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L3-L7); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`experiments/results_pit_v2/REPORT.md`, lines 92-102](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/experiments/results_pit_v2/REPORT.md#L92-L102); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

### C01

**Claim:** Structural survivorship; extra return selection UNKNOWN; annual values null; no equivalence or selection-effect inference from overlap.

**Limit:** Owner-approved FIQ-16 disclosure is incorporated as a local prerequisite, not assumed merged.

- [`docs/paper1/survivorship_bound.md`, lines 7-35](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/survivorship_bound.md`, lines 38-86](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### C02

**Claim:** FIQ-17 comparison planned, NOT RUN; source/selection contrast definitions; own gates remain.

**Limit:** No study specification or outcome execution is added here; protected replication waits for both confirmatory openings and its own gates.

- [`docs/process/TASKS_FINANCEIQ_2026-10-07.md`, lines 465-484](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/process/TASKS_FINANCEIQ_2026-10-07.md#L465-L484); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/research/OWNER_DECISION_ADDENDUM.md`, lines 54-63](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/research/OWNER_DECISION_ADDENDUM.md#L54-L63); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/paper1/survivorship_bound.md`, lines 97-101](survivorship_bound.md); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### G01

**Claim:** Development through 2022-12-31; locked 2023-01-01..2025-12-31; historical semi-clean exposure; forward exposure checks.

**Limit:** A source of governance dates only, not an outcome source or access grant.

- [`docs/process/RESEARCH_CHARTER.md`, lines 130-143](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/process/RESEARCH_CHARTER.md#L130-L143); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/process/RESEARCH_CHARTER.md`, lines 154-165](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/process/RESEARCH_CHARTER.md#L154-L165); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
- [`docs/research/OWNER_DECISION_ADDENDUM.md`, lines 54-63](https://github.com/Salih04/capstone-financeIQ/blob/efe3ed32ca958074c01ee9488f1f768a9d812c61/docs/research/OWNER_DECISION_ADDENDUM.md#L54-L63); snapshot `efe3ed32ca958074c01ee9488f1f768a9d812c61`.

## Literature citations

Bibliographic fields, including years and DOI digits, match the cited BibTeX
entries at the preparation commit. The manuscript uses only this subset;
PBO is omitted while its page range remains unresolved. No OpenAlex search
self-report is treated as independent evidence.

### L01

**Claim:** Fama–French 1992 and conservative minimum six-month gap.

**Limit:** Publisher Section I.A, Data, accounting-to-return matching paragraph. Not a universal statutory rule.

- [`docs/paper1/references.bib`, lines 43-54](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### L02

**Claim:** Drobetz–Otto 2021; lagged fundamentals and temporal training/validation/testing.

**Limit:** Publisher Data/Methodology sections; own financial results not transferred.

- [`docs/paper1/references.bib`, lines 312-323](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### L03

**Claim:** Kapoor–Narayanan 2023; leakage taxonomy and scientific reproducibility.

**Limit:** Published identity from FIQ-13; author preprint abstract read for taxonomy, no survey counts imported.

- [`docs/paper1/references.bib`, lines 82-93](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### L04

**Claim:** Hernán–Robins 2016; time-zero alignment as a clinical analogy.

**Limit:** Primary article Defining time zero section. No finance causal identification claimed.

- [`docs/paper1/references.bib`, lines 69-80](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### L05

**Claim:** Brown et al. 1992 survivor truncation; Shumway 1997 delisting-return bias.

**Limit:** Primary article abstracts/introduction; no portable bias coefficient, no new financial estimate.

- [`docs/paper1/references.bib`, lines 403-414](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/references.bib`, lines 416-427](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

### L06

**Claim:** White 2000; Hansen 2005; Harvey–Liu–Zhu 2016; Bailey–López de Prado 2014.

**Limit:** General data-snooping/selection context only. Hansen publisher text inaccessible in this pass; identity and test title rely on verified FIQ-13 metadata. No implementation or result from any of these tests claimed.

- [`docs/paper1/references.bib`, lines 159-170](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/references.bib`, lines 172-183](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/references.bib`, lines 56-67](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.
- [`docs/paper1/references.bib`, lines 185-196](references.bib); LOCAL UNPUSHED snapshot `7b444a35298f7b04012d818ff70fcbc57b85d6b3`.

## Primary literature access record

Primary sources read or rechecked on 2026-10-27. The FIQ-13 bibliography remains
the identity record; this access check does not revise its unresolved fields.

| Notes | Content source and exact useful location | Access limit |
| --- | --- | --- |
| L01 | [Fama–French publisher article](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04398.x), §I.A Data, paragraph beginning “To ensure that the accounting variables…” | Minimum six-month convention verified from full text; no claim of a universal release law. |
| L02 | [Drobetz–Otto publisher article](https://link.springer.com/article/10.1057/s41260-021-00237-x), Data, Methodology / hyperparameter tuning | Temporal separation and assumed lag context only. |
| L03 | [Kapoor–Narayanan author preprint](https://arxiv.org/abs/2207.07048), abstract; published identity in FIQ-13 | Preprint inspected for the taxonomy, published version cited by verified identity; no survey counts used. |
| L04 | [Hernán–Robins primary article archive](https://pmc.ncbi.nlm.nih.gov/articles/PMC4832051/), Defining Time Zero | Search-indexed primary text accessible; direct open intermittently presented a browser check. No bypass. Clinical analogy only. |
| L05 | [Brown et al. publisher abstract](https://academic.oup.com/rfs/article-abstract/5/4/553/1590264); [research-paper copy](https://terpconnect.umd.edu/~wermers/ftpsite/FAME/Brown_Goetzmann_Ibbotson_Ross.pdf), abstract/conclusion; [Shumway publisher article](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1997.tb03818.x), opening abstract/summary | Brown publisher access intermittent; primary paper copy corroborates general survivor-truncation mechanism. No numerical borrowing. |
| L06 | [White publisher abstract](https://onlinelibrary.wiley.com/doi/10.1111/1468-0262.00152); [Harvey et al. publisher abstract](https://academic.oup.com/rfs/article/29/1/5/1843824); [Bailey–López de Prado author paper](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), Deflated Sharpe Ratio section | General selection/multiplicity context. Hansen publisher text returned 403; verified FIQ-13 identity/title support only, no unverified specific method claim. |

## Interpretation and completeness checks

- Old-to-corrected and statement-only contrasts remain descriptive and bundled;
  no newly computed change, causal share, annual return or effect bound appears.
- Panel counts, test cross-section sizes, market-value availability categories,
  original pre-listing labels and corrected exclusions retain separate scopes.
- The rounded `−0.000` is preserved; the analytic `three years × 78` power
  approximation is not substituted for actual `78, 78, 79` test sizes.
- Historical controls are reported from RESULTS, not rerun or relabelled as
  independent PIT-v2 calibration. Dependence and historical trial completeness
  are disclosed as limitations, without inventing a new correction.
- FIQ-17 is NOT RUN; annual unknowns remain null. No FIQ-18 result is implied.
  Existing authorized aggregate exposure is disclosed, not called clean.
- PBO pagination, complete selection provenance, annual denominator/evidence,
  exact-filing sensitivity and independent scientific review remain open.
- BIR/JAM are candidate positioning from FIQ-14, not acceptance predictions.
  Final author limits, fees and format must be checked at submission. No
  manuscript submission, contact, OSF action, push, PR or merge occurs here.

## Verification record

See the appended FIQ-15 entry in [README.md](README.md) for commands and actual
results. Canonical linters do not fully scan nested manuscript prose; scoped
link/anchor, source excerpt/digest, bibliography and numerical-token checks
supplement them. None of these checks certifies the scientific validity of
historical inference. The [draft](draft.md) is the editable source; its PDF is
a review layout, not a journal template or evidence of submission readiness.
