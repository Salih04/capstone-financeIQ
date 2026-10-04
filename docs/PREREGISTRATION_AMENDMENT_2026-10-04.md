# Amendment 2026-10-04: information timing (post-hoc)

**Dated:** 2026-10-04. **Kind:** post-hoc amendment and registration of a
corrected evaluation. It does not edit, replace or reinterpret any earlier
pre-registration; those documents are byte-identical to their committed
versions (hashes in §5). Everything below the line "registered before
outcomes" in §6 was committed before any PIT-v2 outcome statistic was
computed; the commit order in Git is the evidence.

## 1. What the earlier documents assumed

| Document | Date | Timing premise |
| --- | --- | --- |
| Published walk-forward evaluation (`experiments/run_experiments.py`, `experiments/results/`) | June–July 2026 | Year-T features predict the calendar-year T+1 return starting on the first trading day of January T+1. Not a pre-registration; the result most often quoted from it (equal-weight baseline IC +0.150, p = 0.017) was reported as a weak positive signal. |
| [`MANUAL_FINANCIALS.md`](../MANUAL_FINANCIALS.md) | 2026 | "Values must reflect year-end of `year` — information available at year T" |
| [`PREREGISTERED_2026_EVALUATION.md`](PREREGISTERED_2026_EVALUATION.md) (`PREREG-2026-FORWARD-v1`) | 2026-07-18 | Written "before any 2026 outcome data exists". Frozen ranking (2026-07-15) built from FY2025 statements; outcome window 31 Dec 2025 → 31 Dec 2026 |
| [`thesis/PRE_EXPERIMENT_PROTOCOL.md`](thesis/PRE_EXPERIMENT_PROTOCOL.md) and stage registrations | 2026-08/09 | Controls run on the same T→T+1 panel; Stage 3 already registered "T/T+1 misalignment" and "future-year feature leakage" as defect classes the guards do not detect |

## 2. The incorrect assumption

Fiscal-year-T financial statements are **not** public on 31 December T. Listed
companies file them on KAP up to 60 (solo) or 70 (consolidated) days after
year-end; for FY2023, the first inflation-accounting year, the deadline was
20 May 2024; SASA's FY2022 deadline was 10 May 2023. 31 of the 40 published
features used those statements, so the published evaluation scored companies
with information released weeks into the return window it predicted.

A second defect in the same features: `market_cap` (and P/E, P/B, EV,
EV/EBITDA) multiplied Yahoo's back-adjusted close by historical share counts.

## 3. When and how it was found

On 2026-10-04 during a pre-publication audit (commit `838485b1`, 01:53 CEST):
year-T fundamentals matched published full-year figures exactly (BIMAS, EREGL
FY2021), and dated press reports showed those statements appearing in
February–March. Full audit: [`audit/PUBLICATION_LAG_AUDIT.md`](audit/PUBLICATION_LAG_AUDIT.md).

## 4. Affected analyses

| Analysis | Effect |
| --- | --- |
| Published leaderboard and significance report | Look-ahead in 31 features. The baseline IC +0.150 is attributable to statement information released inside the window (audit §3–4). The ML null is not invalidated (look-ahead biases toward finding signal) |
| Retrospective labs that read the published panel (contamination, placebo, dimensionality, missingness, serving, calibration) or its predictions (rank stability, influence, disagreement, friction) | Same feature timing; their outputs describe the published panel, not an investable one. The regime lens reads only macro context files and is unaffected |
| `PREREG-2026-FORWARD-v1` | The ranking uses FY2025 statements published in Feb–Mar 2026, inside the outcome window that starts 31 Dec 2025, and was frozen 6.5 months into that window. "Before any 2026 outcome data exists" holds only for the year-end outcome price |
| Thesis Stages 1–3 (positive, negative, defect-injection controls) | Not invalidated as controls: the negative control permutes outcomes, the positive control injects synthetic signal. Their statements about the published harness's false-positive rate and power stand; they say nothing about timing, which Stage 3 already recorded as undetected |

## 5. Unchanged artefacts

| Artefact | SHA-256 |
| --- | --- |
| `docs/PREREGISTERED_2026_EVALUATION.md` | `7e911cd02e802d691f64186b03475b2a7fd5a5ea3daf93c23136a325951a156d` |
| `experiments/results/leaderboard.csv` (= `experiments/leaderboard.csv`) | `8b3dfce2ca9ee702411c76cfcf699723cfde076df073837b4ca9db74e5936822` |
| `experiments/results/significance_report.md` | `76f3ff7010821167cc71b4d812090c617299c4fbbf117ff949cd0c80750b356a` |
| `experiments/results/significance_report.json` | `0358ed01b70b99d491f3babb4810604c09e64ef4726f12ee0b7ea0a8af12fc29` |
| `experiments/results_forward_2026/forward_ranking_2026.csv` | `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f` |
| `experiments/results_forward_2026/freeze_manifest.json` | `6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea` |
| `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` | `24dc48567fe1525f86413cedcd8cf0bfb9d061945ed0b56c18067266c2edd7cb` |
| `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78` |

The published run manifests under `experiments/results/runs/` and the
Phase-2 sensitivity outputs under `experiments/pit_audit/` are also unchanged.
The published conclusion remains in the record as historically produced.

`PREREG-2026-FORWARD-v1` will be evaluated exactly as registered when its
outcome data exists. Its result will be reported with the exposure in §4; this
amendment changes neither its test nor its interpretation grid and adds no
secondary forward window.

## 6. Decisions made after seeing the audit

These choices were made by people who had already seen the audit's
sensitivity numbers (baseline IC +0.150 under the published timing, +0.005
with statements lagged a year, +0.193 for FY-T statements alone under the
published timing). PIT-v2 is therefore **post-hoc**: it is registered before
its own outcomes were computed, but it is not blind to the question it
answers. Before registration the daily price data was inspected for listing
dates, split events, one-day jumps and share-count consistency; no
feature–return association was computed.

1. Canonical methodology becomes availability-aware PIT evaluation
   ([`PIT_PROTOCOL.md`](PIT_PROTOCOL.md)); lagging statements by a fiscal year
   is **not** adopted as the canonical fix.
2. Actual-filing-date mode is implemented but covers 6 company-years; the
   full-universe run uses the standardized conservative cutoff mode. The two
   are never mixed.
3. Primary cutoff: 31 May of T+1 for every fiscal year. End of March was
   rejected because it precedes the FY2023 and SASA FY2022 deadlines.
4. Target: Yahoo `adjclose` from the close of the first trading day after the
   cutoff to the last close on or before the next cutoff (protocol §5).
5. Market value rebuilt on one adjustment basis; rows where that cannot be
   shown are excluded (protocol §6).
6. Rows without a quote at the prediction date, and rows with a one-day move
   beyond ±25 % inside the target window, are excluded.
7. Universe unchanged (81 companies); survivorship stays unresolved.

### Registered before outcomes

**Primary estimand.** Pooled IC (equal-weighted mean of the three within-year
Spearman ICs, test fiscal years 2022–2024) of `baseline_equal_weight` under
the primary specification (`uniform_05_31`, all 38 admitted features,
quarantined rows excluded). Two-sided within-year permutation p-value, 10,000
permutations, seed 20261004, α = 0.05.

**Secondary family.** The six ML models under the primary specification,
Bonferroni-adjusted over six. The other two rank baselines are reported
without a test claim.

**Sensitivities (descriptive, unadjusted, no claim on their own).**
S1 `deadline_month_end` cutoff; S2 without market-value features; S3 price
features only; S4 statement features only.

**Interpretation, written before the run.**

| Outcome | Wording |
| --- | --- |
| Baseline p ≥ 0.05 and no ML Bonferroni p < 0.05 | "In this sample and design, the corrected evaluation found no evidence of a large reproducible predictive edge; effects smaller than the minimum detectable \|IC\| (reported) remain outside the study's detection power." |
| Baseline p < 0.05 with positive IC | "The PIT-corrected equal-weight baseline is distinguishable from the within-year null. The specification was designed after the contaminated result was known, so this is exploratory evidence that needs an untouched forward test, not a validated edge." |
| Any negative IC with p < 0.05 | Reported as a statistical observation only; no contrarian or inverted-strategy claim. |
| Any ML Bonferroni p < 0.05 | Reported as distinguishable within this post-hoc design; same caveat as the positive baseline row. |

In every case: no investment claim, and the published result stays in the
record next to the corrected one.
