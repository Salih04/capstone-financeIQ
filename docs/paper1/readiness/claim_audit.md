# Paper 1 claim-to-evidence audit

Checked **2026-10-29**, Europe/Zurich. Draft under review:
`docs/paper1/draft.md` at FIQ-15 candidate
`4b6c88237e38bc240b864b04548eef67bdec5549` (unmerged; see [README](README.md)).
Research support only; not investment advice. This is a documentation audit,
not independent scientific approval.

**Delivery boundary (2026-10-29).** The checks below are the inherited audit
at local commit `87093cba`; the candidate and its prerequisites are absent
from this main-based delivery. They were not imported or re-audited here.
A04/A05 remain open scientific blockers, as recorded in [README.md](README.md).
Matching frozen report text and timestamps does not establish PIT validity.

## Sources and access boundary

Outcome numbers were checked only against the two expressly authorized frozen
reports, byte-identical on main `efe3ed32` and the candidate:

| Source | SHA-256 | Last changed |
| --- | --- | --- |
| `RESULTS.md` | `9356b09bc3afd5448372d4a252708699656f0cde7fa6594167569b65b039d75e` | `ae97a9ffa38e607a26846dfd732057ab72c56be2` |
| `experiments/results_pit_v2/REPORT.md` | `8cf85956b3bf71e14407b01e7313ba8c004de7cc172bc30049194cc5068f63df` | `ae97a9ffa38e607a26846dfd732057ab72c56be2` |

Methods and chronology were checked against non-outcome records already cited
by the crosswalk: `docs/PIT_PROTOCOL.md` (§2-5, §7-8),
`docs/PREREGISTRATION_AMENDMENT_2026-10-04.md` (§1, §6), the charter, the
owner addendum, the FIQ-16 disclosure, and the window-definition lines of
`docs/PREREGISTERED_2026_EVALUATION.md`. Commit metadata for `838485b1`,
`079bb832`, `b0988dfa` and `ae97a9ff` was read with `git log`. No
`report.json`, manifest, data row, other outcome report, protected data or
Kernel material was opened. No analysis, simulation, model run, holdout touch
or FIQ-17/FIQ-18 work occurred.

## Crosswalk integrity (independent re-check)

A fresh scratch script (not committed) re-read every crosswalk source with
`git show COMMIT:PATH`:

- 38 records, 38 unique IDs; JSON IDs equal the Markdown `### Nxx` anchors.
- 62 of 62 source excerpts match their pinned line ranges byte for byte, and
  every file SHA-256 matches.
- All 38 notes are cited by the draft; no draft note lacks a record.

This confirms transcription and pinning, not interpretation.

## Status key

V = verified against the named source. Q = verified, but the draft wording
needs qualification; the proposed edit ID refers to
[editorial_corrections.md](editorial_corrections.md). G = claim-to-evidence gap
that existing sources cannot close. Labels follow the global workflow:
VERIFIED, INFERRED, UNVERIFIED, NEEDS-DECISION.

## Numeric and factual claims

| Draft location | Claim | Source check | Status |
| --- | --- | --- | --- |
| Abstract; Data | 81 firms, 40 reported, selected in 2026 from then-current listings, undocumented rule | RESULTS L127; charter §2; FIQ-16 table | V |
| Abstract; Original design | Original equal-weight IC +0.150, permutation p 0.017 | RESULTS L41; REPORT L58 | V |
| Abstract; Corrected findings | +0.031, p 0.63, 95 % CI −0.100 … +0.162 | REPORT L17; RESULTS L90 | V |
| Abstract | Correction bundles timing with return window, source and rows | REPORT L67-70 | Q (E1): bundle also changes the feature set, 40 columns → 38 admitted (RESULTS L25; REPORT L41; amendment L100) |
| Abstract; Corrected findings | No ML model distinguishable after family adjustment | REPORT L30-35 (all Bonferroni 1.00) | V |
| Abstract; Power | MDE \|IC\| 0.185 at 80 % power | REPORT L23-24; RESULTS L112 | V, with G-4 |
| Data | 40 features; nominal-TRY vendor calendar-year target | RESULTS L25-26 | V |
| Data | 323 published rows, 308 evaluated, 11 pre-listing, 4 jump | REPORT L77-81 (323 − 11 − 4 = 308) | V |
| Data | Test cross-sections 78, 78, 79 | REPORT L10 | V |
| Data | Market value 164 valid, 27, 5, 123 | REPORT L82-85 | Q (E4): the four categories sum to 319, not 323; source does not classify 4 rows (G-1) |
| Original design | Test years 2023-2025, three baselines, six named ML models | RESULTS L28-29 | V |
| Original design | Within-year Spearman IC, pooled mean, permutation, bootstrap, Bonferroni; not preregistered | RESULTS L27-32 | V |
| Original design | RF −0.153 (Bonferroni 0.11), ridge +0.093 (0.94) | RESULTS L43, L48 | V |
| Audit | 31 of 40 features before publication | RESULTS L59-60 | V |
| Audit | 60-70 days; FY2023 20 May 2024; SASA FY2022 10 May 2023 as deadlines | RESULTS L56-58 says "file … by"; protocol §3 table and amendment §6 item 3 call both dates statutory deadlines | V (deadline reading rests on the protocol, not RESULTS alone) |
| Audit | 14 pre-listing labels; five 56.947991 % placeholders | RESULTS L64-65 | V |
| Protocol | Registry fields; guard rejects late values, unregistered features, late training labels | protocol §4, §6; RESULTS L72-76 | V (methods; guard tests not rerun here) |
| Protocol | Standardized cutoff 31 May T+1; entry first trading day after | RESULTS L76-80; protocol §2-4 | V |
| Protocol | Exact filing dates for 6 company-years; mode not run on full universe | RESULTS L78; protocol §2 ("6 of 323 … not run on the full universe") | V |
| Protocol | Late filer could be assigned too early | RESULTS L125; protocol §3 | Q (E3): source also reports none found in the sample |
| Protocol | Target: Yahoo adjclose, first close after cutoff to last close on or before next cutoff | protocol §4-5; amendment §6 item 4 | V |
| Protocol | Prediction dates 1 Jun 2023, 3 Jun 2024, 2 Jun 2025 | REPORT L10-11 | V |
| Corrected findings | Yearly +0.145, −0.051, −0.000 | REPORT L19 | V |
| Corrected findings | Six-row secondary table | REPORT L30-35 (every cell, sign and precision) | V |
| Corrected findings | Diagnostic +0.193 (0.002); S4 +0.041 (0.54) | REPORT L61-62; RESULTS L98-100 | V, with G-5 |
| Corrected findings | S1 +0.102 (0.12), S2 +0.044 (0.50), S3 −0.004 (0.95) | REPORT L42-44 | V |
| Corrected findings | S4 RF −0.176, raw 0.007, within-spec 0.041; 24 tests; does not survive | REPORT L45-50 | V |
| Selection | Structural survivor conditioning; extra return selection UNKNOWN | FIQ-16 table; RESULTS L127; protocol §7 | V (mechanism INFERRED from frame, as FIQ-16 states) |
| Selection | FIQ-17 NOT RUN; no estimate | task card FIQ-17; addendum OD-7 | V; placeholder preserved |
| Selection | 2020-10-01: 100 codes, 60 in 81, 40 outside | FIQ-16 count record (60 + 21 = 81 consistent) | V (literal codes, one date) |
| Power | MDE described as "three years × 78" | REPORT L23-24; RESULTS L112; protocol §8 says "for the realised design" | V, with G-4 |
| Power | Positive controls 0/17/62/93 %; negative 2.8 %/2.6 %, 1,000 reps | RESULTS L113-114 | V; Q (E5): not reconciled with analytic MDE |
| Power | Original guards missed timing leakage | RESULTS L115 | V |
| Registration | Designed after contaminated result; registered before own outcomes at `079bb832…` | amendment §6; REPORT L3-5; `git log` (registration 2026-10-04 15:25 +0200, report commit 15:32, audit commit 01:53 same day) | V; Q (E7): pre-registration knowledge understated |
| Registration | Development ≤ 2022-12-31; locked 2023-2025; semi-clean | charter §5 rule 7 | V; Q (E8): forward-window overlap not stated |
| Limitations | Deadline approximation, small sample, nominal TRY, market-value coverage | RESULTS L125-130 | V; Q (E11): IAS 29 basis change omitted |
| Limitations | Jump exclusion uses in-window movement | protocol §5; amendment §6 item 6 | V; Q (E9): rule set after price inspection |
| Limitations | Within-year permutation and ticker resampling | protocol §8 ("bootstrap of tickers within year") | V; Q (E10) wording precision |
| Reproducibility | Manifests not opened; fresh fetch can change adjclose | REPORT L6-7, L100-102 | V |
| References | Ten works, years, venues, DOIs | references.bib; FIQ-13 table | V (identity); content limits per crosswalk L01-L06 |

## Claim-to-evidence gaps that existing sources cannot close

| ID | Gap | Why it matters | What would close it | Label |
| --- | --- | --- | --- | --- |
| G-1 | Market-value categories account for 319 of 323 rows; RESULTS L128 says "the rest excluded or never available" (159 rows) against 155 classified | A reviewer will add the column | Owner or report author states the 4-row category from frozen `report.json`; this lane is not authorized to open it | UNVERIFIED |
| G-2 | Last corrected window (FY2024) runs to the last close on or before 31 May 2026 by the protocol rule; no frozen source prints the window end dates | Locked-period and forward-window exposure statements depend on it | Owner confirms window ends from the registered run record | INFERRED from rule |
| G-3 | Overlap between the corrected FY2024 window and the 2026 forward window (31 Dec 2025 → 31 Dec 2026) is a date inference; overlap of firms with the 40-firm forward cohort is not checked | Cross-study exposure accounting (charter §5 rule 4; addendum OD-2) | Exposure-ledger entry under FIQ-11/12 rules | INFERRED |
| G-4 | MDE significance level and sidedness not printed in either report; amendment fixes α = 0.05 two-sided for the permutation test only. Analytic MDE (80 % near 0.185) and harness detection (17 % at 0.2) are not reconciled | Central to how the null is read | Owner/author documents the MDE formula and harness test from registered code; no recomputation here | UNVERIFIED |
| G-5 | Diagnostic +0.193 and S4 +0.041 differ in window, source and rows; the sources do not state whether they use the same statement columns (S4 has 27) or the same firms | The draft's strongest timing argument | Read the registered sensitivity definitions; not an outcome read | UNVERIFIED |
| G-6 | Timing of the RESULTS L66-68 exploratory PIT-safe reruns relative to registration is not stated | Strength of the "registered before outcomes" claim | Audit commit record (`838485b1`) chronology check by owner | UNVERIFIED |
| G-7 | Complete historical trial count (all configurations ever evaluated on this panel) is not documented; the reported 6 and 24 test families are scoped | Charter §5 rule 6 and every multiple-testing reviewer | FIQ-12 ledger reconstruction or explicit "incomplete" disclosure (already disclosed in draft) | UNVERIFIED |
| G-8 | Vendor identity for the original target and statements is not named in the two sources ("vendor") | Journals require named data sources and a data statement | FO-4 terms review names sources and rights | NEEDS-DECISION (FO-4) |
| G-9 | FO-1 selection provenance and the FIQ-16 annual table remain incomplete (all-null rows) | Selection section | FO-1 owner statement; Kernel count request | NEEDS-DECISION (FO-1) |

None of these gaps is filled by estimate in this pass.
