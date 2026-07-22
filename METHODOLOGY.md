# Methodology

How FinanceIQ scores BIST stocks and validates those scores against realized
performance. Written to be honest about what the scores can and cannot do.

> **Honest result (2026-06):** with 40 validated features and an expanded
> 81-ticker internal training universe, the walk-forward signal is still
> **weak/unstable** — overall Spearman remains close to zero and ML does not
> establish a reliable edge over simple baselines. Scores are research support,
> **not** investment advice.
> Hybrid research score = 0.65·ML + 0.20·confidence + 0.15·AI-evidence, components always shown.
> The AI-evidence term contributes ONLY when the local model returns a meaningful score
> in (0,1]; a null/zero value means "AI evidence unavailable" and its weight is
> redistributed to ML + confidence (the AI can never drag or dominate the final score).

## Data

Primary trusted modeling outputs:

- `data/trusted_clean/modeling_dataset_training_2020_2025.csv`: internal training
  split, 403 rows / 81 tickers / 321 target rows.
- `data/trusted_clean/modeling_dataset_public_2020_2025.csv`: public UI split,
  240 rows / 40 tickers / 200 target rows.

Realized yearly return is treated strictly as **ground truth / target**, never as
a feature for the same row. The 2025 rows are inference-only unless explicit,
validated T+1 outcome data is added later.

### Important data reality: source fields are mixed-quality

Verified by `scripts/validate_trusted_data.py` (`column_variability`):

- **Accepted per-year fundamentals:** corrected income statement, profitability,
  balance-sheet, leverage, liquidity, growth, cash-flow-derived fields, and
  free-reconstructed valuation fields where inputs pass shape/coverage checks.
- **Accepted year-T market features:** Yahoo year-end price, year-T return,
  volatility, drawdown, benchmark-relative return, dividend/split indicators,
  and data-coverage indicators. The `sector` identity column exists but is
  currently unpopulated; it is not an accepted modeling feature.
- **Rejected or guarded fields:** frozen snapshot columns, current-only multiples,
  same-row realized returns, future-derived targets, and any post-target fields.

Consequences, stated honestly:

- The dataset is more realistic than the original frozen snapshot, but still
  small and sparse.
- The expanded 81-ticker universe is used internally for training and evaluation;
  the public UI universe remains the selected 40 BIST companies.
- The product does **not** claim robust predictive alpha. It tests whether
  leakage-safe year-T information has measurable T+1 rank signal.

### Sector-label provenance and sample sizes (DATA-06 audit, 2026-07-12)

The trusted modeling path has no validated sector-label source. In
`scripts/data_collection/pipeline.py`, `build_universe()` deliberately sets
`sector` to null because the legacy reference data does not contain reliable
per-year sectors. The generated `data/trusted_raw/company_universe.csv` therefore
has an empty `sector` column. None of the universe files in `data/config/*.csv`
defines a sector label: they contain ticker membership and notes only.

Current committed-output counts, measured by distinct ticker, are:

| Dataset | Labeled sectors | Unassigned | Total tickers | Rows with blank sector |
|---|---:|---:|---:|---:|
| Public (`modeling_dataset_public_2020_2025.csv`) | 0 | 40 | 40 | 240 / 240 |
| Training (`modeling_dataset_training_2020_2025.csv`) | 0 | 81 | 81 | 403 / 403 |

There are consequently no evidence-backed per-sector stock counts to report;
the only current bucket is **Unassigned** (40 public, 81 training). Assigning
companies to sectors would require a separately sourced, reviewed taxonomy and
owner sign-off. Missing labels must remain null rather than being inferred.

The DB-backed sector analytics are a separate legacy path. The trusted yearly
loader also leaves `Company.sector` and `Company.sector_code` null.
`backend/app/services/sector_service.py` performs no label mapping or
normalization: it groups exact, non-null `Company.sector_code` strings and will
compute z-scores with as few as two populated peers (`MIN_PEERS = 2`). Thus its
labels are consistent only if the active database was populated consistently by
an external/manual workflow; they do not come from the trusted modeling dataset.
The legacy quarterly-forecasting upload likewise accepts its `sector` text from
the uploaded CSV and is not sector provenance for the trusted dataset.

Any sector comparison with fewer than 10 companies is **anecdotal**. Sector
z-scores, percentiles, heatmaps, medians, and adaptive adjustments must not be
read as statistically reliable or as evidence of predictive skill. They remain
research support only, not investment advice.

## Two separate scores

### Fundamental Score
Built only from financial-statement, valuation, growth, balance-sheet, and
cash-flow metrics. Cross-sectional **rank normalization within each year**:
every metric is ranked into a percentile, lower-is-better metrics (P/E, leverage,
…) are inverted, value multiples are ranked over positive values only, and
missing values are excluded and tracked (never filled with fake zeros). Category
scores are averaged into a 0–100 score. Rank normalization is robust to the
dataset's extreme outliers (growth % in the trillions) without deleting data.

### Market/Price Features
Year-T price-derived features can be used in the T→T+1 experiment only when the
measurement window ends inside year T. Same-row realized return and future price
movement are target-only and never feature inputs.

## Literature motivation (references, not data)

- **Fama–French five-factor** (value, profitability, investment, size): motivates
  using valuation multiples, margins/returns-on-capital, growth/investment, and
  size as cross-sectional return descriptors.
- **q-factor model** (Hou–Xue–Zhang): profitability and investment as the core
  drivers — reflected in our Profitability and Growth categories.
- **Expected profitability and returns**: profitable firms have historically
  carried a return premium; we test whether that holds on BIST here.
- **Financial ratios and stock returns / MCDM ranking**: multi-criteria ranking
  of firms by financial ratios — our rank-normalized category averaging is a
  transparent MCDM-style aggregation.
- **Decision-tree / ML on financial ratios**: motivates the experiment loop,
  where ML models must beat simple ratio baselines to be used at all.

These are **motivation only**. We do not claim to reproduce any paper's results.

## Same-year explanation ≠ future prediction

Two clearly separated questions:

1. **Explanatory (same year):** did high-Fundamental-Score companies also have
   high realized return *that same year*? Measured by Pearson/Spearman
   correlation, top-k hit rate, and quintile spread (`/research/validation`).
   This is descriptive, **not** a forecast.
2. **Predictive (next year):** the `experiments/` walk-forward harness is built
   with strict leakage controls (no same-year target, no future data in
   training). It compares simple baselines and ML models on year-T features
   against year-(T+1) outcomes.

## Serving-side experimental ranking heuristic ≠ walk-forward models

The CSV-backed ranking shown by the forecasting service is a deterministic,
explainable heuristic, not one of the linear or tree models evaluated by the
`experiments/` walk-forward harness. Its source is
`backend/app/services/forecasting_csv_service.py`; the relevant functions are
`train_parameters()` and `run_forecast()`.

`train_parameters()` uses the internal training split and finalized T→T+1
targets by default (2020–2024). Within each training year, it marks companies
at or above the 75th percentile of realized next-year return as historical
top-quartile "winners." For each usable numeric feature, it calculates a
non-negative discrimination score from the absolute standardized difference
between the winner mean and the overall training mean, multiplied by the
feature's non-null coverage among winners. It then normalizes each score by the
largest feature score and selects the highest-weighted features (12 by default).

`run_forecast()` applies those selected weights to the public-universe rows for
one input year. It percentile-ranks each available feature across that year's
public companies, multiplies each percentile by the calculated heuristic weight,
and divides the summed contributions by the total selected weight to produce a
bounded ranking score. Missing features are omitted from a company's
contributions and reduce its reported confidence; they are never fabricated.
The service also exposes the contributing features, missing features, and an
experimental-ranking disclaimer. It does not emit buy/sell/hold signals or
price targets.

This mechanism describes which feature values **historically co-occurred with
top-quartile returners in this small sample**; it does **not** establish that
they predict future winners. Its weights are not validated predictive model
parameters, and the walk-forward experiment result remains weak/unstable
(Spearman IC near zero, with no reliable predictive edge). The ranking is
therefore research support only, not investment advice.

### Serving-heuristic walk-forward evaluation (R3-SERV-01)

`make research-serving-eval` now measures this exact service path without
changing or copying it. For each canonical split, the harness restricts
`train_parameters()` to the prior feature years, passes the exact 80-ticker
eligible evaluation panel to the unchanged `run_forecast()` through an isolated
`RESEARCH_REPO_ROOT`, and keeps realized test outcomes outside the service until
scoring is complete. Missing features retain the service's omission and
confidence behavior; rows without realized outcomes are excluded before the
within-year percentiles are calculated. The evaluated target years are
2023–2025, with 80 eligible tickers in each year from the retrospective internal
training cohort.

The user-facing serving heuristic's walk-forward IC is 0.050 (95% CI
[-0.075,0.174], permutation p=0.4427); this is not distinguishable from the
within-year null, and in either case does not establish investment value,
implementability, or a reliable predictive edge. This is a **single
prespecified test, outside the six-model Bonferroni family**: its permutation
p-value is raw and is not family-corrected. The canonical six-model family
remains separate, no model is added retrospectively, and the Model Confidence
Contract conclusion does not change.

Full split definitions, per-year counts and exploratory ICs, selected service
parameters, source checksums, six-model family context, limitations, and the
pending independent-review status are in
`experiments/results_serving_eval/serving_eval_report.json` and
`experiments/results_serving_eval/serving_eval_report.md`. Interpretation remains
constrained by three low-power test years, a retrospectively fixed cohort with
survivorship/universe-selection risk, null feature and outcome coverage, nominal
TRY returns in one macro regime, and environment-qualified reproducibility.
Research support only; not investment advice.

## Confidence calibration bench (R2-CAL-01)

`make research-calibration` audits the user-facing hybrid research score's 0.20
`confidence_score` component from `research_agent.confidence_score`; it does not
substitute the forecasting service's separate per-row selected-feature coverage
quantity. Audited as of the 2026-07-12 replay at git SHA
`a95e1e1c92fe6ffbe3e1660f7caf66b2a110401c`, the current hybrid confidence was
**0.25 (low)** for every row evaluated from the persisted 2023–2025 prediction
dumps. Those dumps contain 2,160 model rows but only 240 distinct ticker-year
outcomes because the same 80 outcomes per year are evaluated by nine models.

Within each model and target year, the bench compares predicted rank with
realized-return rank and keeps raw score magnitudes model-local because their
scales differ. Ten confidence bins were requested, but only one was possible;
therefore the higher-confidence/lower-rank-error relationship and its seeded
bootstrap interval are **not estimable**. The plain finding is: **hybrid
confidence is not informative about rank error at this scale because the
replayed quantity has no cross-row variation.** Separately measured feature
coverage did vary from 0.375 to 1.000 (median 0.6625), but it was not relabeled
as hybrid confidence or used for post-hoc tuning. Missing coverage inputs remain
null, and missing confidence inputs reduce the diagnostic rather than being
filled. Confidence is not a probability of return, profit, or success, is not
recommendation strength, and does not establish validated predictive
reliability. Full provenance, model-native score ranges, rank errors, and the
plot-ready single-bin artifact are in `experiments/results/calibration_report.*`
and `calibration_plot.csv`. The no-reliable-predictive-edge conclusion remains
unchanged.

## Alternative return-basis evaluation (R2-REAL-01)

`make alternative-targets` preserves the canonical nominal TRY targets and
derives two parallel target columns in the separately generated
`data/trusted_clean/modeling_targets_alternative.csv`. Real TRY return is
`(1 + nominal) / (1 + CPI) - 1`, using TÜİK's December year-on-year national CPI
for target year T+1. USD-basis return is
`(1 + nominal) * USDTRY_T / USDTRY_T+1 - 1`, using Yahoo `TRY=X` year-end closes
quoted as TRY per USD. The manual CPI input has a source and retrieval-date
sidecar; Yahoo responses are cached. A missing nominal target, CPI year, or FX
year remains null and is never interpolated or imputed. All 321 existing nominal
target rows have both alternative targets in this run.

`make research-real-terms` reuses the nominal harness's features, walk-forward
splits, nine models, and seeded significance machinery, but writes only to
`experiments/results_real_terms/`. On the CPI-deflated real TRY basis, the
smallest pooled raw p-value in the six-model ML family is random forest at
pooled IC **−0.156**, raw permutation **p=0.0164**, and Bonferroni-adjusted
**p=0.0984**. On the USD basis, the corresponding selected model is random
forest at pooled IC **−0.150**, raw permutation **p=0.0213**, and
Bonferroni-adjusted **p=0.1278**. Neither basis survives the existing
family-wise gate. These are descriptive historical research results from three
80-row test years in the retrospective training cohort; they do not establish
signal, investment value, implementability, or a reliable predictive edge.

As an inflation-basis illustration only, the repository's 2022 BIST100 return
of **185.94% nominal TRY** becomes **74.07% CPI-deflated TRY** under the same
64.27% December year-on-year CPI transformation. This comparison is not a
strategy-performance or investment-value statement. Full derivation provenance,
coverage, prediction dumps, corrected tests, and limitations are in
`data/trusted_clean/alternative_targets_report.*` and
`experiments/results_real_terms/`. The nominal artifacts and the conclusion —
no reliable predictive edge — remain unchanged.

## Excess-return-basis evaluation (R3-TGT-01)

`make research-excess` applies the existing significance treatment to the
trusted `next_year_excess_return_vs_bist100` target (nominal TRY stock return
minus the BIST100 nominal TRY index return, in percentage points). The isolated
runner uses the same year-local feature ranking and missing-feature rules,
frozen walk-forward splits, nine model specifications and hyperparameters, and
fixed stochastic seeds as the canonical harness. It performs no hyperparameter
search or result-driven model-family selection and writes only to
`experiments/results_excess/`; canonical nominal models, prediction dumps,
leaderboards, significance reports, and trusted datasets remain read-only.

The evaluated cohort is the **benchmark-covered public 40** — the 40 tickers
carrying a valid BIST100-relative excess target — not the wider internal
training universe used by the nominal basis. That leaves **40 evaluated rows per
model in each of the 2023, 2024, and 2025 test years**, versus 80 nominal-basis
rows per test year. Missing excess targets remain null and are excluded rather
than filled. Aggregate metrics are reconstructed from the new per-ticker
prediction dumps. The reconstructed 27-row excess leaderboard matches the
existing aggregate target leaderboard at zero relative tolerance and `1e-12`
absolute tolerance; any future disagreement is emitted in the report and must
not be patched silently.

### What the within-year IC does and does not estimate

The reported statistic is a **within-year Spearman IC, so the estimand is ordinal
cross-sectional ranking** inside one evaluation year. It does not evaluate
benchmark-relative magnitude accuracy, and it does not estimate alpha, economic
outperformance, investment value, or a tradable strategy.

The runner proves the ordinal claim rather than asserting it. The nominal target
column is traced from repository authority — `run_experiments.TARGETS[0]`,
cross-checked against the pipeline assignment
`next_year_excess_return_vs_bist100 = next_year_return_pct - next_year_bist100_return_pct`
read out of `scripts/data_collection/pipeline.py` by AST parse — and a persisted
**estimand-invariance audit** then checks, on the exact evaluated rows, that the
subtraction is one common value inside each year and that both targets rank the
cohort identically:

| Evaluation year | Evaluated rows | Common BIST100 return subtracted (pp) | Rank mismatches |
| ---: | ---: | ---: | ---: |
| 2023 | 40 | 31.96 | 0 |
| 2024 | 40 | 28.94 | 0 |
| 2025 | 40 | 12.64 | 0 |

Total rank mismatch count: **0**. The run fails with `ExcessEstimandError` if
either the common within-year subtraction or the rank invariance does not hold.
Benchmark subtraction may still affect *fitting* — it shifts the target by a
year-level constant across the training panel, so pooled-year fits can learn
different coefficients — but it does not alter within-year evaluation ranks.

### Two permutation analyses, reported side by side

Significance uses the same equal-year Spearman IC and Bonferroni correction
across the same six-model ML family. Two permutation analyses are reported; they
answer different questions and neither replaces the other.

**`primary_independent_within_year_permutation`** (prespecified, unchanged by
human review). Null: within each evaluation year, realized cross-sectional
outcomes are exchangeable relative to the model predictions, with each year
permuted independently. It retains its seed (42), 10,000 draws, two-sided
absolute tail, the Monte Carlo correction `(extreme_count + 1) / (draw_count + 1)`,
the equal-year pooled IC, and six-model Bonferroni adjustment.

**`trajectory_preserving_ticker_permutation_sensitivity`** (added after human
review; a sensitivity analysis, **not** a prespecified replacement). Null: ticker
identities are exchangeable as complete cross-year trajectories. Each of the
10,000 draws generates **one** permutation of the sorted 40-ticker universe and
applies that **same mapping in 2023, 2024, and 2025**; prediction rows stay
fixed, each realized-outcome trajectory moves as a complete block, the Spearman
IC is recomputed independently within each year, and the equal-year mean is the
null statistic. Every mapping is a duplicate-free one-to-one permutation — this
is a permutation test, not a bootstrap — and ragged coverage, missing years,
duplicate ticker/year rows, malformed keys, unequal ticker sets across years,
non-finite values, too few tickers, too few valid draws, and independently
generated per-year mappings are all refused with `ExcessPermutationError`.

Uncertainty intervals come from a **ticker-cluster bootstrap**: each of the
10,000 resamples draws 40 ticker identities with replacement, and that **single
sampled ticker vector is shared by all three evaluation years**, so a ticker's
complete 2023–2025 trajectory moves together and a ticker drawn twice contributes
its whole trajectory twice. Years are never resampled independently.

All six family members are reported symmetrically for both analyses:

| Model | Pooled IC | Primary raw p | Primary Bonferroni p | Sensitivity raw p | Sensitivity Bonferroni p | Either rejects at FWER 0.05 | Ticker-cluster 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| linear_regression | −0.117 | 0.2074 | 1.0000 | 0.2231 | 1.0000 | no | [−0.264, 0.047] |
| ridge | −0.038 | 0.6820 | 1.0000 | 0.6963 | 1.0000 | no | [−0.222, 0.155] |
| lasso | −0.095 | 0.2993 | 1.0000 | 0.3300 | 1.0000 | no | [−0.249, 0.072] |
| elasticnet | −0.063 | 0.4873 | 1.0000 | 0.5565 | 1.0000 | no | [−0.281, 0.166] |
| random_forest | −0.211 | 0.0223 | 0.1338 | 0.0416 | 0.2496 | no | [−0.420, 0.014] |
| gradient_boosting | −0.211 | 0.0217 | 0.1302 | 0.0411 | 0.2466 | no | [−0.424, 0.010] |

No model is selected or privileged using the observed excess-target IC, raw
p-value, adjusted p-value, bootstrap interval, or any other outcome-derived
statistic, and there is no headline model. The conclusion is computed from the
adjusted p-values above, not assumed: **0 of 6 family members reject under the
primary permutation and 0 of 6 reject under the sensitivity**, so **no ML model
survives the six-model Bonferroni correction under either analysis** and **no
reliable predictive edge is established** on this basis. A bootstrap interval is
descriptive uncertainty evidence and cannot override the closed-family
inference, so an interval that happens to approach zero does not upgrade any
model. Three non-family baselines are reported separately with unadjusted
p-values, under both analyses, and are not part of the corrected family.

### Cross-basis multiplicity

Bonferroni correction here is **within-basis only**. `next_year_return_pct`
(nominal TRY) is the **sole confirmatory family**; the real-TRY, USD, and
excess-return analyses are **exploratory robustness evaluations**. No correction
in this repository controls multiplicity across the several target bases, so the
number of bases examined inflates the chance that some basis eventually produces
a small p-value. A future significant alternative-basis result must not be
described as confirmatory without a separately prespecified cross-basis
correction. This task alters no nominal artifact.

### Coincident baselines, IC signs, and review-package scope

`baseline_equal_weight` and `baseline_rank_score` produce **bitwise-identical
prediction values** on every evaluated ticker and year in the persisted dumps
(maximum absolute difference 0.0), which necessarily makes their ranks and their
ICs identical too — the strongest of the three levels the runner tests, and the
only one it states. Both specifications are retained for frozen-specification
continuity; no repository authority has permitted removing a frozen
specification. Coincident results must not be read as independent baseline
diversity: two baselines that agree at this level contribute one distinct
comparison, not two.

All six family members have a negative pooled IC on this basis. Predominantly
negative IC signs may reflect sampling variation, feature-orientation effects, or
systematic construction effects. They are **not** interpreted as inverse alpha, a
contrarian strategy, an actionable signal, or validated predictive evidence, and
the tree-based members are not singled out.

The compact human-review package supports review of the persisted
**prediction-to-significance layer** — row-level dumps, the dump-reconstructed
leaderboard, the significance report, and the artifact manifest. It does not
alone provide standalone reproduction of feature construction and model fitting;
the repository technical review separately covers governed source paths,
protected hashes, split tracing, and implementation behavior. No claim of
complete independent fitting-stage replication is made from the compact package
alone.

Symmetry is enforced by construction, not by cleanup. The shared
`significance.build_report` helper internally picks the family member with the
smallest raw permutation p-value, so the R3-TGT-01 runner **never calls it**;
deleting that field afterwards would still mean the selection had run. The
report is assembled instead from per-model, non-selecting analyses, and no
helper choosing a minimum raw p, minimum adjusted p, strongest IC, or narrowest
interval is executed at any layer. The nominal report path is unchanged.

Power is reported for the design that was actually evaluated, read from the
persisted dumps: `current_design` is **40 rows per evaluation year across 2023,
2024, and 2025** (120 evaluated rows per model), marked `observed`, and reported
once. The per-year and pooled rows are two views of that single design rather
than two designs. Longer-horizon rows are kept in a separate, explicitly
hypothetical planning structure, deduplicated against the observed design on
(rows per year, test years), so no planning row restates current evidence; the
80-row figure appears only as nominal-basis context on a different target and a
wider cohort. The detectable |IC| at this design is large, so the family-wide
non-rejection is a low-power non-rejection: it does not establish that the true
IC is zero, and no power figure is a statement of predictive validity.

Cluster keys are validated strictly before any grouping or integer conversion.
Years must be finite mathematical integers inside the exact set {2023, 2024,
2025}; nulls, booleans, strings, non-numeric objects, NaN, ±infinity, and
fractional values such as 2023.5 are refused with `ExcessBootstrapError` rather
than floored, rounded, or cast. Tickers must be non-empty strings without
leading or trailing whitespace, unique per year, and present in every evaluation
year. Generated output is confined by a bounded destination policy: the default
`experiments/results_excess`, or — for isolated tests and deterministic
verification only — a `financeiq-r3-tgt-01-*` directory under the root reported
by `tempfile.gettempdir()`, with symlinked destinations, symlinked path
components, and the temporary root itself refused before any file is written.

The generated manifest records the target, generator, frozen model
specifications, splits, seeds, model-family membership, effective estimator
parameters read directly from each fitted estimator, feature-column checksum,
CSV and report schema versions, the Python/NumPy/pandas/SciPy/scikit-learn
versions and platform, source checksums, output checksums, and the
`make research-excess` regeneration command. Regeneration is deterministic
within that recorded environment; byte identity across different environments is
not claimed. Nominal findings and artifacts are untouched, and this is isolated
research fitting rather than production retraining. This is a descriptive
historical research result; it does not establish signal, investment value,
implementability, or a reliable predictive edge.

## Regime Lens (R2-REGIME-01)

`make research-regime` validates effective-dated annual CPI, year-end TCMB
one-week repo policy rates, USDTRY closes, and BIST100 nominal returns without
changing any chart series, return target, ranking, or model artifact. **2020–2025
spans a single extraordinary Turkish macro regime (high inflation, deep TRY
depreciation). Model behavior across regimes is therefore untested — this lens
shows regime context and will only compute regime-conditional diagnostics when
regime diversity exists.** The observed 2023–2025 test years all map to that
single task-defined, inclusive 2020–2025 period, so the workflow emits
`not_computed_insufficient_regime_diversity` and computes no per-regime model
statistics.

The macro series are descriptive sensitivity context, not evidence that macro
moves caused model behavior. Nominal TRY, CPI-deflated TRY, and USD-basis
analyses remain parallel; none establishes a reliable predictive edge. The
existing multiplicity and low-power treatment, retrospective-universe and
survivorship risks, basis limitations, and numerical-environment qualification
remain unchanged. Full sources, effective dates, null handling, and claim-safe
limitations are in `data/trusted_raw/macro/macro_context_yearly.md` and
`experiments/results_regime/regime_context_report.*`. Research support only;
not investment advice.

## Honest findings (current data)

- Walk-forward signal remains weak/unstable. The expanded pipeline improved the
  test bed, but not enough to justify claiming reliable signal.
- Before expansion, overall Spearman was about **0.007**. After adding the
  expanded training universe and leakage-safe price/benchmark features, overall
  Spearman is about **0.042**. This is still close to zero.
- The best ML run can look better in isolated folds, but stability is limited.
  The correct conclusion is uncertainty, not a predictive edge.

## Headline IC significance treatment (R2-STAT-01)

`make research` now persists deterministic evaluated-row artifacts at
`experiments/results/predictions_test_2023.csv` through
`predictions_test_2025.csv` (ticker, target year, model, realized return, and
prediction). `make research-significance` consumes those dumps without
retraining. For each model it computes an equal-weighted mean of the three
within-year Spearman ICs, shuffles realized returns independently within each
test year 10,000 times for a two-sided permutation p-value, and resamples
tickers with replacement within year 10,000 times for a 95% bootstrap interval.
The six ML-model p-values are Bonferroni-corrected as one selection family.

The smallest pooled raw ML p-value is for random forest: pooled IC **−0.153**,
raw permutation **p=0.0183**, Bonferroni-adjusted **p=0.1098**, and model-specific
bootstrap 95% CI **[−0.273, −0.028]**. The unadjusted interval and raw p-value do
not override the family-wise test: no ML model is statistically distinguishable
from the within-year null after correction, so the results do not support a
reliable predictive edge. The equal-weight baseline has pooled IC **0.150**,
unadjusted **p=0.0168**, and bootstrap 95% CI **[0.024, 0.267]**; it is reported
as descriptive baseline context outside the six-model ML correction family, not
as a validated edge.

The current harness uses the internal training universe and has **n=80**
evaluated rows per model in each split, rather than the public-40 shorthand in
earlier audit prose. There are still only three test years. Results describe a
retrospectively fixed repository cohort, not verified point-in-time BIST100
membership, and exact prediction-artifact reproduction remains qualified by the
recorded numerical environment. Full values, exploratory per-split rows, null
histograms, source checksums, and limitations are in
`experiments/results/significance_report.json` and `.md`. This is research
support only, not investment advice.

### Power and detectability limits (R2-STAT-02)

The same significance report now computes minimum detectable absolute Spearman
IC using a two-sided Fisher-z approximation at α=0.05 and 80% power, with a
seeded Gaussian-copula rank simulation as a cross-check. For the actual dump
design, the analytic minimum detectable |IC| is **0.309 for one 80-row test
year** and **0.182 for the equal-weighted three-year design**; simulated power
at those thresholds is 0.802 and 0.810, respectively. A public-universe-scale
planning sensitivity gives **0.431 for one 40-ticker year** and **0.260 for
three 40-ticker years**. All simulated checks are within the report's ±0.05
absolute-power tolerance.

These quantities are deliberately separate. Observed IC is a sample estimate
from the prediction dumps; detectable IC is an assumed true effect that would
be rejected in 80% of repeated studies under the approximation; power is that
long-run rejection probability. The detectable threshold is not a hard
significance cutoff and does not estimate the true IC. The calculation is for
one prespecified test and is not Bonferroni-adjusted family-wise power across
the six ML models. It also says nothing about economic value, transaction
costs, robustness, or practical investment relevance. With only three observed
test years, retrospective-universe limitations, one macro regime, and
environment-qualified numerical reproduction, the correct conclusion remains
no reliable predictive edge. The 40-ticker projection in
`experiments/results/significance_report.md` describes pipeline readiness for
more data, not a promise that additional years will produce predictive skill.

## Model Confidence Contract and claims lint (R2-CONTRACT-01)

`model_confidence_contract.json` is the machine-readable v1 claim boundary for
user-facing pages and forecasting response copy. It cites the committed
leaderboard and significance report as its evidence basis, records that no ML
model survives family-wise correction, and separates approved diagnostic,
research-support, statistical-uncertainty, and limitation wording from forbidden
investment or predictive claims. Power-analysis thresholds remain study-design
quantities; the contract does not treat them as observed edge, economic value,
or evidence that more data will produce predictive skill.

Run `make claims-lint` (or `python scripts/lint_claims.py`) after changing page
copy or forecasting response constants. The stdlib-only check requires the
research-support / not-investment-advice disclaimer on every routed data-page
implementation, pins the `unevaluated_forward_forecast` inference label, and
rejects unreviewed prediction, outperformance, expected-return, buy/sell/hold,
market-beating, or profitable-trading language with `file:line` diagnostics.
Legitimate negated, methodological, route-name, and CSS-token uses are explicit
exact-line allowlist entries in the contract, so changes require review.

### Contract versioning procedure (R2-CONTRACT-02)

Changes to MCC rules, scan coverage, data-page registration (including aliases
and exemptions), or evidence state require a minor-version bump and updated
effective date. Allowlist-only line-number or exact-text refreshes require a
patch bump. Every version change requires human review against the authority
and cited evidence before release.

This mechanism is a tripwire, not proof of honest meaning. Passing it does not
validate methodology, predictive skill, practical investment relevance, or the
semantics of wording outside its configured surfaces; claims still require human
review against `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` and the cited evidence.

## Reproducibility and run provenance

Every `make research` run writes a registered manifest under
`experiments/results/runs/<UTC timestamp>_<git short SHA>/manifest.json`. The
manifest records the git SHA and dirty-tree flag; Python, platform, and numerical
package versions; all fixed seeds; feature columns; model and walk-forward split
configuration; SHA-256 checksums for the canonical, training, and public datasets
and other run inputs; configuration-file checksums; wall-clock duration; and a
SHA-256 checksum for every generated experiment artifact.

Run `make research-verify-run` to reproduce the latest manifest in an isolated
temporary directory, or pass a specific path as
`make research-verify-run RESEARCH_MANIFEST=<manifest>`. Verification requires
input and configuration checksums to match, compares the headline leaderboard at
`atol=1e-12` with zero relative tolerance, and requires all artifact bytes to be
identical when Python, platform, and package versions match. When the numerical
environment differs, byte drift is reported explicitly and only semantic
leaderboard reproduction within that strict tolerance can pass.

Registration documents provenance; it does not certify methodology or establish
predictive validity. The weak/unstable, no-reliable-edge conclusion and the
research-support-only boundary remain unchanged.

### Run-directory governance

A manifest is of record only when its `leaderboard.csv` SHA-256 matches the
committed `experiments/leaderboard.csv`. Run-directory age or name does not
override that checksum rule; if multiple manifests match, each remains a
co-record. Superseded run directories may be deleted only in the same commit
that replaces the committed leaderboard, so the replacement manifest and
leaderboard remain reviewable together. Manifests are generated provenance
records and must never be hand-edited.

### Artifact registry

`artifact_registry.json` (curated, reviewed input — not generated) maps every
file under `experiments/results*/` and `data/trusted_clean/` to the single
Makefile command that regenerates it, its artifact class, and whether
hand-editing is forbidden. `tests/test_artifact_registry.py` fails on any
orphaned or multiply-owned artifact, unsupported regeneration command, or stale
`source_artifacts` checksum. The registry records ownership only; it certifies
neither methodology nor predictive value.

## Leakage controls

Enforced in `app/services/research/feature_registry.py`:
- Realized return is target-only.
- Same-row realized return is barred from features.
- Next-year prediction uses only prior-year features.
- Selected year never silently falls back to the latest year.
- 2025 is inference-only unless explicit validated T+1 outcomes are added.

## Forward forecast: 2025 → 2026 (inference, not a backtest)

The training/backtest window ends at **2024** because finalized T+1 labels are
available through 2025. 2025 is **not missing** — its rows are used as
**inference inputs**:

- Train the signal on finalized annual T+1 targets, 2020–2024.
- Apply the learned weights to 2025 financial rows → a **2026 forward-looking
  ranking** of the 40 public companies.
- 2026 realized returns do not exist yet, so this ranking is
  `unevaluated_forward_forecast` — never presented as a backtest or realized result.

Endpoint: `GET /forecasting/inference?year=2025` (public). Each row carries
`input_year=2025`, `target_year=2026`, `is_inference=true`,
`realized_return_available=false`. This is the main forward output and is kept
separate from the experimental partial-target mode below.

### Pre-registered 2026 evaluation (R3-PREREG-01)

Before any 2026 outcomes exist, this forward ranking is frozen verbatim (via the
unchanged inference path) and its single evaluation is pre-registered in
`docs/PREREGISTERED_2026_EVALUATION.md`: one Spearman rank IC against realized
2026 returns with a within-year seeded permutation p-value, plus a pre-written
interpretation for every result cell. The pre-registered test is nearly powerless
by design: the minimum usable cohort is 30, and the pre-frozen n=30–40 Fisher-z
table ranges from detectable \|IC\| 0.492 to 0.431 at 80% power. The n-specific
value is descriptive context, never a second test or validation threshold. The
outcome is the nominal-TRY Yahoo adjusted-close calendar-year return, independently
recomputed from retained year-end snapshots. Freeze reruns are write-free when
identical and refuse any Git/service/data/ranking drift. Reproducibility remains
environment-qualified; no result changes a product or MCC claim automatically.

## Experimental: 2025 partial 2026-YTD target mode (opt-in)

The headline methodology is **finalized annual T+1 only** (2020–2024 training). It
is the sole basis for every model-quality claim (Spearman, IC, walk-forward).

An OPTIONAL experimental mode (`target_mode=include_partial_2025`) can include
2025 using a **partial 2026 year-to-date return** as a stand-in target:

- `target_year = 2026`, `target_status = "partial_ytd"`, `comparable_to_full_year = false`.
- Warning attached everywhere: *"2025 uses partial 2026 YTD return and is not
  directly comparable to finalized annual targets."*
- It is **never** mixed into the headline finalized result. Any Spearman/IC that
  uses partial 2025 must be reported separately and labeled experimental/partial.
- 2025 never appears as a normal finalized training year; `trainable_years`
  stays 2020–2024 in all modes.
- Requires real 2026 price data (`data/trusted_clean/partial_2026_ytd_returns.csv`).
  Absent by default → mode reports unavailable and excludes 2025. No fabrication.

## Limitations

- Small dataset, even after expansion. All out-of-sample numbers are noisy;
  overfitting is easy.
- The universe audit verifies the configured 40-company public cohort and
  81-ticker training split, but not historical BIST100 membership. Git first
  records the 40-name cohort in June 2026, after the 2020–2025 study window; the
  repository contains no point-in-time constituent, delisting, suspension, or
  membership-effective-date history and does not state the original selection
  rule. Actual Yahoo coverage is 226/240 public ticker-years (35/40 tickers
  complete). Results therefore describe a retrospectively fixed repository
  cohort and retain unresolved survivorship and universe-selection look-ahead
  risk; missing history was not inferred or filled. See
  `docs/universe_audit.md` for the file- and commit-cited evidence.
- BIST100 benchmark/excess-return fields exist where source coverage is valid;
  they are not available for every expanded training row.
- Supervised ML is **not** presented as a reliable trained predictor.

## Disclaimer

Research and educational tool. **Not financial advice.** Scores describe
historical cross-sectional patterns in a small dataset and do not predict future
returns.
