# Results

FinanceIQ asks whether one year's public company data can rank BIST stocks by
the next calendar year's return. This page states what was found, how sure we
are, and what the evidence cannot show, without requiring the governance files
behind it. Every number links to the artefact that produced it.

**Answer: no reliable predictive edge was found.** The only nominally
significant number in the published evaluation, an equal-weight baseline
correlation of +0.15, does not survive a point-in-time correction: it depends
on annual financial statements that were not yet public when the return
window it predicts began.

## 1. Question and design

| | |
| --- | --- |
| Unit | Company × year |
| Features | 40 columns describing year T: fundamentals (fiscal-year-T statements), valuation, prices and momentum up to 31 Dec T, benchmark return |
| Target | Calendar-year T+1 stock return (vendor dated return; nominal TRY) |
| Primary metric | Spearman rank correlation between prediction and realised return within a test year (information coefficient, IC) |
| Evaluation | Expanding-window walk-forward, three test years (2023, 2024, 2025), 80 companies per test year |
| Models | Three rank baselines (equal-weight mean of feature percentiles, rank score, robust median) and six ML models (OLS, ridge, lasso, elastic net, random forest, gradient boosting) |
| Inference | Pooled IC = mean of within-year ICs; within-year permutation null; bootstrap CI resampling tickers within year; Bonferroni over the six ML models |

Data: 81 BIST companies, 2020–2025, 321 labelled company-years for training
and testing. Sources and cleaning rules: [`DATA_PIPELINE.md`](DATA_PIPELINE.md),
[`METHODOLOGY.md`](METHODOLOGY.md).

## 2. Published result (preserved)

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

No ML model is distinguishable from the within-year null after correction.

## 3. Point-in-time correction (2026-10-04)

The year-T fundamentals are fiscal-year-T statements (they match published
annual figures exactly), and Turkish listed companies publish those up to
60–70 days after year-end. The T+1 return window starts on the first trading
day of January. Re-running the identical harness with only information that
existed on that day:

| Specification | Equal-weight IC (p) | Best ML IC (p) |
| --- | --- | --- |
| Published, 40 features | **+0.150 (0.019)** | +0.093 (0.16) |
| Price, momentum and benchmark only | +0.031 (0.63) | +0.060 (0.35) |
| Fundamentals lagged to fiscal year T−1 | +0.005 (0.93) | −0.005 (0.94) |
| Diagnostic, not point-in-time: FY-T statements alone | +0.193 (0.002) | +0.161 (0.013) |

p-values are unadjusted and exploratory. The published row's p differs from §2
(0.019 vs 0.017) only because the permutation draws differ (seed 20261004,
10,000 permutations); the IC is identical. The signal in the published baseline
is carried by statement information released during the target window; once
features are restricted to what was public, nothing remains. Lagging the
statements also makes them staler, so the audit cannot fully separate
look-ahead from information decay; a window starting after publication would,
but needs intra-year prices the repository does not hold.
Full audit: [`docs/audit/PUBLICATION_LAG_AUDIT.md`](docs/audit/PUBLICATION_LAG_AUDIT.md).

## 4. Can the harness detect a real effect? (power)

| Check | Result | Source |
| --- | --- | --- |
| Minimum detectable \|IC\| at 80% power, three pooled years × 80 companies | 0.18 (analytic) | `significance_report.md` |
| Positive control: synthetic signal injected into one feature, 200 repetitions per level | detection 0% at IC 0.1, 17% at 0.2, 62% at 0.3, 93% at 0.4 | `experiments/results_thesis/positive_control/` |
| Negative control: permuted targets / rank-Gaussian noise, 1,000 repetitions each | false-positive rate 2.8% and 2.6% against a 5% family level | `experiments/results_thesis/negative_control/` |
| Defect injection: do the pipeline's guards catch planted errors? | Target leakage and duplicate rows detected; future-year feature leakage, T/T+1 misalignment and look-ahead universe membership **not** detected (as registered); decision INCONCLUSIVE on an integrity condition | `experiments/results_thesis/defect_injection/` |

Read together: the harness controls false positives, but it could only have
detected an effect of roughly IC 0.3–0.4, larger than anything plausible for
annual cross-sectional equity signals. A null here means "no large edge", not
"no edge". The defect-injection stage had already shown that the existing
guards do not detect timing leakage; the publication-lag audit is an instance
of exactly that class.

## 5. Interpretation

- **Supported:** with this data and design, no model ranks next-year returns
  better than chance after correcting for multiple models, and the one
  positive baseline number is explained by information that was not yet
  public.
- **Not supported:** that BIST is efficient, that fundamentals are useless, or
  that a better model would fail. The study is small, covers one unusual
  macro period (high nominal-TRY inflation), and can detect only large
  effects.
- **Why it is still useful:** the harness is reproducible, pre-registered
  where it matters, reports power and controls alongside every estimate, and
  found a flaw in its own published number.

## 6. Known limitations

| Issue | Status |
| --- | --- |
| Statement publication lag in the canonical features | Quantified; PIT-correct reruns added; canonical pipeline unchanged (owner decision) |
| Market cap = back-adjusted price × historical share count | Unsolved; distorts market cap, P/E, P/B, EV, EV/EBITDA by factors set by later corporate actions |
| Pre-listing rows with vendor placeholder returns | Unsolved in the dataset (14 labelled rows); excluding them changes no conclusion |
| Retrospective universe, survivorship | Unsolved; no point-in-time index membership or delisting history applied |
| Two return definitions (vendor vs Yahoo adjusted close) | Rank ρ = 0.994, but 28 of 307 rows differ by > 10 pp |
| 2026 forward pre-registration | Frozen 2026-07-15, inside its own outcome window, from statements published in that window; amendment is an owner decision |
| Three test years, one macro regime, nominal TRY | Inherent to the data |

## 7. Reproduce

```bash
pip install -r requirements-root.txt          # pinned numpy 1.26.4 / scikit-learn 1.5.1
make data-validate                            # validate the committed dataset
PYTHONPATH=. python experiments/run_experiments.py --help
PYTHONPATH=. python experiments/pit_lag_sensitivity.py   # reproduces §2 and §3
PYTHONPATH=. python -m pytest tests/ -q       # root suite
```

`pit_lag_sensitivity.py` refuses to report if its unchanged specification
does not reproduce the published leaderboard (exact for eight models; OLS
within 0.003 IC, which is BLAS-dependent on collinear rank features).

Research support only; not investment advice.
