# Results

FinanceIQ asked whether one year's public company data can rank BIST stocks by
their next-year return. The study found an apparent weak signal, an audit then
showed that signal used financial statements before they were public, and a
point-in-time (PIT) re-evaluation removed it. Both results are kept.

**Current conclusion:** in this sample and design, the corrected evaluation
found no evidence of a large reproducible predictive edge; effects smaller
than |IC| ≈ 0.19 remain outside the study's detection power.

| Stage | What happened | Evidence |
| --- | --- | --- |
| 1. Hypothesis | Year-T fundamentals, valuation and momentum rank next-year returns | §1 |
| 2. Apparent weak signal | Equal-weight baseline IC +0.150 (p = 0.017); ML null | §2, preserved unchanged |
| 3. Audit | Statements used up to 10 weeks (FY2023: 20) before publication; market value on mixed adjustment bases | [`docs/audit/PUBLICATION_LAG_AUDIT.md`](docs/audit/PUBLICATION_LAG_AUDIT.md) |
| 4. PIT correction | Availability-aware protocol, registered before its outcomes | [`docs/PIT_PROTOCOL.md`](docs/PIT_PROTOCOL.md), [`amendment`](docs/PREREGISTRATION_AMENDMENT_2026-10-04.md) |
| 5. Revised conclusion | Baseline IC +0.031 (p = 0.63); ML null | §4, [`experiments/results_pit_v2/REPORT.md`](experiments/results_pit_v2/REPORT.md) |

## 1. Original hypothesis and design

| | |
| --- | --- |
| Unit | Company × year, 81 BIST companies, 2020–2025 |
| Features | 40 columns describing year T: fiscal-year-T statements, valuation, prices and momentum to 31 Dec T, benchmark return |
| Target | Vendor dated calendar-year T+1 return (nominal TRY) |
| Metric | Spearman rank correlation of prediction and realised return within a test year (IC) |
| Evaluation | Expanding-window walk-forward, test years 2023–2025, ~80 companies each |
| Models | Three rank baselines and six ML models (OLS, ridge, lasso, elastic net, random forest, gradient boosting) |
| Inference | Pooled IC = mean of within-year ICs; within-year permutation null; bootstrap CI; Bonferroni over the six ML models |

The original walk-forward was not pre-registered. Later pre-registrations
(the 2026 forward test and the thesis controls) were built on its design.

## 2. Original result (preserved, historically produced)

From [`experiments/results/significance_report.md`](experiments/results/significance_report.md):

| Model | Kind | Pooled IC | Permutation p | Bonferroni p |
| --- | --- | ---: | ---: | ---: |
| Equal-weight baseline | baseline | +0.150 | 0.017 | n/a |
| Robust rank aggregation | baseline | +0.128 | 0.046 | n/a |
| Ridge | ML | +0.093 | 0.157 | 0.94 |
| Lasso | ML | +0.090 | 0.170 | 1.00 |
| OLS | ML | +0.046 | 0.480 | 1.00 |
| Elastic net | ML | −0.020 | 0.754 | 1.00 |
| Gradient boosting | ML | −0.105 | 0.104 | 0.63 |
| Random forest | ML | −0.153 | 0.018 | 0.11 |

At the time this was read as a weak positive baseline signal and an ML null.
The baseline reading is withdrawn (§3); the numbers are not edited.

## 3. What the audit found

- **Publication lag.** Year-T features are full fiscal-year-T statements
  (they match published annual figures exactly). Listed companies file them
  60–70 days after year-end in normal years, by 20 May 2024 for FY2023 (first
  inflation-accounting year), and SASA by 10 May 2023 for FY2022. The target
  window started on the first trading day of January, so 31 of 40 features
  were used before they existed publicly.
- **Mixed adjustment bases.** Market cap multiplied Yahoo's back-adjusted
  close by historical share counts (AEFES 2024 understated ~10× by a 2025
  bonus issue), contaminating P/E, P/B, EV and EV/EBITDA.
- **Pre-listing rows.** 14 labelled rows predate the security's first quote;
  five share the same vendor placeholder "return" (56.947991 %).
- Discovered 2026-10-04 (commit `838485b1`). Exploratory reruns showed the
  baseline IC falling to ≈ 0 under every PIT-safe specification, but could not
  separate look-ahead from staleness.

## 4. Corrected evaluation (PIT-v2)

Protocol: [`docs/PIT_PROTOCOL.md`](docs/PIT_PROTOCOL.md). Every feature has a
public-availability timestamp in a machine-readable
[registry](data/pit/feature_availability_registry.json); a guard refuses any
value whose timestamp is after the prediction time, and tests inject
future-available features to show it fails. Statements count as public from
the statutory filing deadline (standardized conservative cutoff mode; exact
filing dates exist for only 6 company-years, so that mode is not run).
Primary cutoff: 31 May T+1; the signal and the return start on the first
trading day after it. Market value uses one adjustment basis or is excluded.
Pre-listing and corporate-action-defect rows are excluded.

Registered before outcomes in
[`docs/PREREGISTRATION_AMENDMENT_2026-10-04.md`](docs/PREREGISTRATION_AMENDMENT_2026-10-04.md).
It is post-hoc: designed after the contaminated result and the audit were
known.

| Model | Pooled IC | Permutation p | 95 % CI | Bonferroni p |
| --- | ---: | ---: | --- | ---: |
| **Equal-weight baseline (primary)** | **+0.031** | **0.63** | −0.100 … +0.162 | n/a |
| OLS | +0.073 | 0.27 | −0.056 … +0.195 | 1.00 |
| Lasso | +0.056 | 0.39 | −0.073 … +0.181 | 1.00 |
| Gradient boosting | +0.028 | 0.68 | −0.099 … +0.156 | 1.00 |
| Ridge | +0.001 | 0.99 | −0.129 … +0.130 | 1.00 |
| Elastic net | −0.021 | 0.75 | −0.151 … +0.108 | 1.00 |
| Random forest | −0.021 | 0.75 | −0.149 … +0.106 | 1.00 |

Test years FY2022–FY2024 (78, 78, 79 companies). The same fiscal-year-T
statements that carried IC +0.193 when used before publication carry +0.041
(p = 0.54) when used after it. That is consistent with look-ahead, and not with
stale data, as the source of the original signal; the corrected design also
changes the return window and source and the rows evaluated, so it is evidence
rather than an isolated test. Registered sensitivities and the
negative random-forest IC in the statements-only sensitivity (−0.176,
Bonferroni-within-specification 0.041, not significant over all 24
sensitivity tests) are in the [full report](experiments/results_pit_v2/REPORT.md).

## 5. Power: what a null here means

| Check | Result |
| --- | --- |
| Minimum detectable \|IC\| at 80 % power, PIT-v2 design (3 years × 78) | 0.185 |
| Positive control (published harness): synthetic signal injected, 200 repetitions per level | detected 0 % at IC 0.1, 17 % at 0.2, 62 % at 0.3, 93 % at 0.4 |
| Negative control: permuted targets / noise, 1,000 repetitions each | false-positive rate 2.8 % and 2.6 % at a 5 % level |
| Defect injection | timing leakage was **not** detected by the original guards (as registered); the PIT guard now checks timestamps |

The harness controls false positives but can only see large effects. Typical
annual cross-sectional equity signals are usually smaller than |IC| 0.19, so a null
here means "no large edge", not "no edge".

## 6. Remaining limitations

| Issue | Status |
| --- | --- |
| Exact filing timestamps | Not collected for the full universe; conservative statutory deadlines used instead. A company filing after its deadline would be treated as public too early; none was found in the sample |
| Staleness of the cutoff | Statements are up to 11 weeks older than necessary in normal years; S1 (closer to publication) gives baseline IC +0.102, p = 0.12 — not detectable at this sample size |
| Survivorship and universe | **Unresolved.** 81 companies chosen in 2026 from then-current listings; no delisted or failed company can appear; no point-in-time index membership |
| Market value | Valid on one basis for 164 of 323 rows; the rest excluded or never available (training-only companies have no share counts) |
| Corporate actions in returns | Yahoo `adjclose`; rights issues and misdated adjustments are not reliably handled, so rows with a one-day move beyond ±25 % are excluded (4) |
| Sample | Three test years, ~78 companies, one high-inflation nominal-TRY regime |
| 2026 forward pre-registration | Unchanged; frozen inside its own outcome window with in-window statement information; will be evaluated as registered and reported with that exposure |

## 7. Reproduce

```bash
pip install -r requirements-root.txt                      # pinned numpy 1.26.4 / scikit-learn 1.5.1
PYTHONPATH=. python -m pytest tests/ -q                   # root suite
PYTHONPATH=. python experiments/pit_v2_evaluation.py      # §4 (registered run)
PYTHONPATH=. python experiments/pit_lag_sensitivity.py    # audit reruns
```

Research support only; not investment advice.
