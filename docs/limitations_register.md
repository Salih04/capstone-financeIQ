# Automated limitations register

> GENERATED — regenerate via make limitations-register; do not hand-edit

This document is an evidence register, not a new statistical conclusion. The auto-extracted section preserves registered artifact text verbatim; the curated section preserves reviewed source quotations verbatim.

## Auto-extracted limitations

### data/trusted_clean/free_valuation_history_report.json

Registered through: `data/trusted_clean/free_valuation_history_report.json`

- Shares outstanding is the binding gap: without a real per-ticker-year share count (KAP/company reports), market_cap cannot be computed and all derived ratios stay null. Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are misaligned and were rejected, not imputed.

### experiments/results/calibration_report.json

Registered through: `experiments/results/calibration_report.json`

- The replay describes the current checked-out confidence code applied to persisted historical outcomes; it is not historically persisted confidence.
- The hybrid confidence component is dataset-state scoped and constant across tickers, so decile calibration cannot be estimated.
- The 2,160 model rows repeat 240 ticker-year realized outcomes across nine models and are not 2,160 independent observations.
- Only three test years and one macro regime are observed; no reliable predictive edge is established.
- No confidence tuning or recalibration was performed on these rows.

### experiments/results/friction_report.json

Registered through: `experiments/results/friction_report.json`

- Cost bps values are explicit assumptions, not measured BIST costs.
- No bid–ask spread, market impact, liquidity, capacity, execution, suspension, or tradeability input is available or inferred.
- The evaluated cohort is the retrospectively fixed 81-ticker training universe with 80 rows per split, not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain unresolved.
- Only three test years are observed in one task-defined macro period; the numerical environment qualification remains applicable.
- The analysis uses nominal TRY outcomes only. CPI-deflated TRY and USD-basis evidence remain separate and are not recomputed here.
- Multiplicity and low-power limits remain unchanged; isolated basket outcomes do not establish signal or practical value.
- Missing selected realized outcomes propagate to null gross and net values; missing predictions are excluded from rank eligibility and never filled.
- Research support only; not investment advice.

### experiments/results/significance_report.json

Registered through: `experiments/results/significance_report.json`

- Only three test years with 80 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- Nominal TRY returns cover one unusual macro regime, so absence of detected signal is not a general market-efficiency claim.
- Research support only; not investment advice.

### experiments/results_contamination/contamination_report.json

Registered through: `experiments/results_contamination/contamination_report.json`

- This is a descriptive tail-handling sensitivity laboratory for eligible growth-percentage input cells; it does not detect corrupted data or establish that any cell is bad.
- Thresholds are per-feature, per-window quantiles estimated only from permitted training feature years; they are not a data-quality validation rule and do not establish causal validity.
- Winsorization and trim-to-null are applied only to fresh isolated copies; canonical/trusted datasets, targets, identifiers, provenance, flags, benchmark/context variables, and committed baseline artifacts are not perturbed.
- The frozen q grid is q={0.025,0.05,0.10} per side; hard support (n-1)q>=1 gates eligibility, while nq>=3 is diagnostic only.
- Existing within-year permutation/bootstrap and six-model Bonferroni arithmetic are reused descriptively; no new delta-IC significance family, bootstrap, or multiplicity correction is created.
- A nominally significant perturbed condition, if any, is a sensitivity finding requiring investigation, not evidence of predictive edge, alpha, profitability, causal validity, or production validity.
- Results are numerical-environment-qualified; byte identity is required within the same numerical environment and is not claimed across different environments.
- The internal significance scope is 80 evaluated tickers per model and split; public-40 framing is distinct and must not be combined with it.
- The canonical evaluation universe remains unchanged; only authoritative non-null cells in the frozen five-feature growth block are perturbable. Rows without growth support remain in canonical evaluation, unperturbed and neither dropped, synthesized, nor relabeled as contaminated. Coverage is reported per window; R4-ROBUST tests tail-handling sensitivity of the growth-supported portion of the canonical analysis, not universal contamination of every evaluated row.
- The conclusion remains: no reliable predictive edge. Research support only; not investment advice.

### experiments/results_dimensionality/dimensionality_report.json

Registered through: `experiments/results_dimensionality/dimensionality_report.json`

- Descriptive feature-geometry analysis only; no model, target, or serving input is changed.
- Exact neutral-rank fill is analysis-only and is not model imputation, including for the n_obs = 0 and n_obs = 1 branches.
- Under heterogeneous missingness, no direction is guaranteed for spectral or participation-ratio effects.
- Windows differ in row universes and missingness, so cross-window metrics are not temporal evolution.
- PRIMARY-matrix exclusion does not imply feature uselessness, lack of predictive value, modeling redundancy, lack of temporal information, lack of market-context information, or feature-selection benefit.
- Support-based exclusions may remove redundancy-contributing geometry; exclusion is a construction/support limitation, not a finding about the excluded feature.
- D_eff is not claimed to be an upper or lower bound of any quantity over a larger or different feature set.
- Retrospective cohort, limited historical windows, sparse or mixed-quality source coverage, and environment-qualified reproduction remain limitations.
- No reliable predictive edge, alpha, profitability, investment value, tradable strategy, feature-selection benefit, model improvement, causal diagnosis, production validity, or deployment validity is established.
- Research support only; not investment advice.

### experiments/results_disagreement/disagreement_report.json

Registered through: `experiments/results_disagreement/disagreement_report.json`

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- Only three target years are represented, all within one unusual macro regime; this atlas does not establish regime robustness.
- Rank agreement or disagreement describes model instability, not opportunity, economic value, trading profitability, or predictive validity.
- The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.
- Raw y_pred scales differ by model and are deliberately never compared across models; ties receive average ranks.
- Missing or non-finite predictions are never imputed. Insufficient pairwise or ticker-year evidence is reported as null with an explicit status.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

### experiments/results_excess/significance_report.json

Registered through: `experiments/results_excess/**`

- Only three test years with 40 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- Excess returns subtract the BIST100 nominal TRY index return within one unusual macro regime; they are a descriptive benchmark-relative basis and do not represent an implementable benchmark-hedged position or investment value.
- Research support only; not investment advice.
- The evaluated cohort is the benchmark-covered public 40, not the wider internal training universe used by the nominal basis; rows without a valid excess target remain null and shrink the evaluated n per year rather than being filled.
- The ticker-cluster bootstrap resamples 40 ticker trajectories, so its effective resolution is bounded by 40 clusters over three years; it describes sampling uncertainty and cannot substitute for family-wise multiplicity correction.
- Bonferroni correction here is within-basis only. Nominal return is the sole confirmatory family; the real-TRY, USD, and excess-return bases are exploratory robustness evaluations, and no correction in this repository controls multiplicity across the several target bases.
- Predominantly negative IC signs are not interpreted as inverse alpha, a contrarian strategy, an actionable signal, or validated predictive evidence.
- The compact human-review package supports review of the persisted prediction-to-significance layer only; it does not by itself reproduce feature construction or model fitting, and no claim of complete independent fitting-stage replication is made from it alone.

### experiments/results_influence/influence_report.json

Registered through: `experiments/results_influence/influence_report.json`

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- Only three target years are represented, all within one unusual nominal-TRY macro regime; influence rankings do not establish regime robustness.
- High single-observation influence describes estimator fragility under a tiny sample, not opportunity, economic value, trading profitability, or predictive validity.
- Influence is a retrospective, in-sample sensitivity diagnostic; it is not a causal, forward-looking, or out-of-sample statement about any ticker.
- The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.
- The pooled IC and its inputs remain point estimates from three test years; a large |Δ| does not make the underlying pooled IC distinguishable from the null.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

### experiments/results_missingness/missingness_report.json

Registered through: `experiments/results_missingness/missingness_report.json`

- Serving-heuristic sensitivity only: this measures how one fixed deterministic ranking recipe reacts to omitted inputs, not predictive skill.
- A small rank delta is not robustness, reliability, validation, or stability of predictive skill; the walk-forward IC remains indistinguishable from the null.
- Only the latest public-universe input year and its retrospective cohort are analysed; results do not generalise across years, universes, or regimes.
- Masking uses the service's own null path; no value is fabricated, imputed, zeroed, or sentinel-filled.
- Feature categories are the governed source_class provenance grouping, not a financial-sector taxonomy.
- The selected-weight feature set is fixed from finalized 2020-2024 training; training-time missingness is out of scope.
- Exact byte reproduction is numerical-environment-qualified (Python/platform/package versions).
- Research support only; not investment advice.

### experiments/results_placebo/placebo_report.json

Registered through: `experiments/results_placebo/placebo_report.json`

- This is a test of the evaluation rig on synthetic noise, not a market study; nothing here supports or refutes any claim about BIST equities.
- The gate uses the six-model ML Bonferroni family and the committed permutation/bootstrap settings; it does not re-run the analytic power analysis or the baseline models.
- Bonferroni control is conservative, so the empirical rejection rate is expected to sit at or below alpha rather than exactly at it.
- R=25 is a low-resolution negative-control smoke test.
- 0/25 does not certify exact family-wise calibration at alpha=0.05.
- It can expose gross anti-conservatism but cannot precisely estimate the Type-I error rate.
- For 0/25, the exact two-sided 95% Clopper-Pearson binomial upper bound is approximately 0.137 (unrounded 0.1371851715) using the documented zero-event closed form.
- Reproduction is numerical-environment-qualified; byte identity holds within a fixed Python and numerical-package environment.
- The conclusion of the project is unchanged: no reliable predictive edge. Research support only; not investment advice.

### experiments/results_rank_stability/rank_stability_report.json

Registered through: `experiments/results_rank_stability/rank_stability_report.json`

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- The public-40 subset is a fixed repository cohort, not point-in-time index constituents; sector membership, liquidity, tradeability, and corporate-action history are not inferred here.
- Only three target years are represented, all within one unusual nominal-TRY macro regime; stability rankings do not establish regime robustness.
- Stability under resampling is not predictive validity: a stable but null-consistent ranking remains indistinguishable from noise, and an unstable ranking does not establish opportunity.
- Top-k membership frequency is conditional on being drawn and is a resampling artifact; it is not a probability that a ticker will outperform.
- The jackknife dispersion describes the pooled IC estimator's fragility under a tiny three-year sample, not economic value, trading profitability, or out-of-sample skill.
- Ticker-year deletion units are treated as exchangeable only for this descriptive sensitivity diagnostic. Repeated tickers across years and within-year cross-sectional dependence prevent interpretation as sampling uncertainty.
- No new significance test or p-value is produced; the existing multiplicity correction, low-power limits, and null-consistent conclusion are unchanged.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

### experiments/results_real_terms/real_try/significance_report.json

Registered through: `experiments/results_real_terms/**`

- Only three test years with 80 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- CPI-deflated TRY returns use national December year-on-year CPI as a descriptive basis; they do not represent investor-specific inflation or investment value.
- Research support only; not investment advice.

### experiments/results_real_terms/usd/significance_report.json

Registered through: `experiments/results_real_terms/**`

- Only three test years with 80 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- USD-basis returns use Yahoo year-end TRY-per-USD closes as a descriptive currency basis; they do not establish implementability or investment value.
- Research support only; not investment advice.

### experiments/results_regime/regime_context_report.json

Registered through: `experiments/results_regime/**`

- Only three model test years (2023–2025) are observed, all inside one task-defined 2020–2025 macro period.
- No per-regime statistic, causal effect, or regime-specific predictive edge is estimable from one observed period.
- Multiplicity treatment and low-power limits from the nominal and alternative-basis significance reports remain applicable and unchanged.
- The 81-ticker training cohort is retrospectively fixed rather than verified point-in-time BIST100 membership, so survivorship and universe-selection look-ahead risks remain unresolved.
- Nominal TRY, national-CPI-deflated TRY, and USD-basis returns are separate descriptive bases; none represents investor-specific value or implementability.
- Prediction-artifact byte reproducibility remains numerical-environment-qualified.
- Missing macro observations remain null and are never interpolated or imputed.
- Research support only; not investment advice.

### experiments/results_serving_eval/serving_eval_report.json

Registered through: `experiments/results_serving_eval/serving_eval_report.json`

- Only three target years are observed, with 80 eligible tickers per year; estimates remain low-power and noisy.
- The cohort is retrospectively fixed and is not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain.
- Missing feature values remain null and reduce service coverage; no value is fabricated or imputed by this harness.
- Rows without realized outcomes are excluded and reported; the result does not generalize to those missing observations.
- Outcomes are nominal TRY returns from one unusual macro regime; regime robustness and economic implementation are not established.
- Exact artifact reproduction is numerical-environment-qualified even though seeded same-environment reruns are byte-deterministic.
- The raw serving p-value belongs to one prespecified test outside the six-model Bonferroni family and is not family-corrected.
- Research support only; not investment advice.

### experiments/results_thesis/negative_control/negative_control_report.json

Registered through: `experiments/results_thesis/negative_control/negative_control_report.json`

- These controls characterize apparatus behavior under the registered constructions only.
- The diagnostic uses a target-associated real mask and is not an exact null-FPR test.
- Passing this stage would not establish absence of feature-side PIT or alignment leakage.
- Research support only; not investment advice.

### experiments/results_thesis/positive_control/positive_control_report.json

Registered through: `experiments/results_thesis/positive_control/positive_control_report.json`

- Signal is injected into one carrier column; the recovered IC therefore reflects the pipeline's ability to isolate one informative feature among 40, not its ability to aggregate signal spread across many.
- The injection permutes the carrier's values within each year, which destroys that column's joint structure with the other features. The theta=0 rung shares the damage, so comparisons along the curve are internally consistent, but the absolute recovered IC is not the IC an equally strong naturally-occurring feature would give.
- The theta=0 rung is not a zero-IC world: the other 39 features retain whatever weak real structure they carry, so recovered IC at theta=0 estimates that background rather than zero.
- Only three test cross-sections of about 80 rows exist. Detection rates are measured over 200 repetitions and carry binomial uncertainty of roughly +/-3 percentage points.
- The detection threshold is read off five preregistered grid points. The true crossing is not localized, and no interpolated value is reported.
- Each Wilson detection-rate interval is conditional on the one fixed realized panel. It captures only the repetition-to-repetition variation over the declared repetitions -- across repetitions the synthetic injection draw changes and the permutation-test RNG changes, so it carries injection-draw randomness plus permutation Monte-Carlo randomness -- and excludes resampling uncertainty from drawing a different equity panel or time sample.
- The realized equity panel is fixed across repetitions. The synthetic injection changes across repetitions and the permutation-test RNG also changes across repetitions, so the empirical detection-rate variation includes injection-draw randomness plus permutation Monte-Carlo randomness; it still does not include resampling uncertainty from drawing another market panel or time sample. Fisher-z analytic/simulation power instead integrates over cross-sectional sampling variability, so the two curves condition on different randomness; their residual difference cannot be attributed simply to the test, and the curves are diagnostic rather than interchangeable power estimates.
- The raw, feature-construction, and model-input/imputation checkpoints for the primary 100%-coverage carrier are identity/invariant checks, not empirical claims of no attenuation. The substantive measured transition is carrier signal to fitted model prediction.
- The secondary carrier changes row population: its observed-carrier checkpoint n differs from the post-imputation full-cross-section n. Its stagewise ratio therefore mixes missingness/imputation dilution with changed evaluation population and is not a pure attenuation coefficient.
- Any background-adjusted ratio is a heuristic descriptive diagnostic, not a mathematically exact decomposition of Spearman IC. The ratio is emitted as NA for identity/invariant checkpoints and the injected design constant -- where it would sit near 1.0 by construction and could be misread as a measured attenuation coefficient -- and for levels where the theta=0 background dominates.
- The temporary run_experiments.TRAINING_MODELING override is process-global and this experiment is single-threaded; concurrent execution is outside this task's scope.
- Results describe this pipeline on this panel with this carrier. They do not generalize to other designs, frequencies, universes, or feature sets, and they establish nothing about BIST returns or investment value.

### experiments/results_thesis/positive_control_calibration/positive_control_calibration_report.json

Registered through: `experiments/results_thesis/positive_control_calibration/positive_control_calibration_report.json`

- Stage 1b is apparatus characterization on synthetic input. It establishes no predictive edge, no alpha, no investment value, and no production readiness, and the repository's committed walk-forward finding is unchanged by it.
- The primary result is descriptive. Stage 1b has no scientific performance PASS/FAIL gate: a flat, non-monotone, weak, surprising, or high-background curve is a scientific result, not an integrity failure.
- The realized equity panel is fixed across repetitions. The synthetic injection draw changes and the permutation-test RNG changes, so the reported variation carries injection-draw randomness plus permutation Monte-Carlo randomness conditional on this one realized panel. It excludes uncertainty from drawing another equity universe, market panel, time period, PIT universe, or monthly sample.
- Wilson intervals are pointwise per theta. The permutation seed does not depend on theta or level index, so the permutation RNG stream is shared across theta levels for the same repetition id; the intervals are marginal and are not simultaneous or between-level comparison intervals. No between-theta inference is drawn from them.
- For R=400 the approximate worst-case pointwise Wilson half-width is about 4.9 percentage points near p=0.50 and about 3.9 percentage points near p=0.80. R=400 improves grid-point precision but does not identify an exact between-grid crossing, and no interpolation is confirmatory.
- The divisor 5 in the primary rule is the frozen historical Stage 1 operating divisor, retained as one fixed operating point for comparability. Stage 1b's six theta levels are not a hypothesis family and no family-wise-error-control claim is made across them.
- theta=0 is not a zero-signal market world: the real non-carrier features remain in the pipeline, so the theta=0 rung describes that background rather than zero.
- theta is a synthetic copula design constant. It is not a realistic BIST IC, not a universal IC benchmark, and not a smallest effect size of interest; SESOI remains UNRESOLVED.
- The injection permutes the carrier's own observed values within each year, which destroys that column's joint structure with the other features. Every rung including theta=0 carries the same damage, so the curve is internally consistent, but the absolute recovered IC is not the IC an equally strong naturally-occurring feature would give.
- The temporary run_experiments.TRAINING_MODELING override is process-global and this stage is single-threaded; concurrent execution is outside its scope.

## Curated seed limitations

### retrospective cohort

Source: `METHODOLOGY.md`
Locator: `## Limitations`

Exact source text:
```text
Results therefore describe a retrospectively fixed repository
  cohort and retain unresolved survivorship and universe-selection look-ahead
  risk; missing history was not inferred or filled.
```

### sector unpopulated

Source: `METHODOLOGY.md`
Locator: `### Important data reality: source fields are mixed-quality`

Exact source text:
```text
`sector` identity column exists but is
  currently unpopulated; it is not an accepted modeling feature.
```

### one regime

Source: `METHODOLOGY.md`
Locator: `## Regime Lens (R2-REGIME-01)`

Exact source text:
```text
2020–2025
spans a single extraordinary Turkish macro regime (high inflation, deep TRY
depreciation). Model behavior across regimes is therefore untested — this lens
shows regime context and will only compute regime-conditional diagnostics when
regime diversity exists.
```

### environment-qualified reproduction

Source: `METHODOLOGY.md`
Locator: `## Reproducibility and run provenance`

Exact source text:
```text
When the numerical
environment differs, byte drift is reported explicitly and only semantic
leaderboard reproduction within that strict tolerance can pass.
```

### manual shares

Source: `FINANCEIQ_MODEL_VALIDITY_AUDIT.md`
Locator: `## 6. Dataset limitations`

Exact source text:
```text
Shares outstanding is manual — derived valuation is null until supplied.
```

### deployment unverified

Source: `FINANCEIQ_MODEL_VALIDITY_AUDIT.md`
Locator: `## 16. Claims that must be avoided`

Exact source text:
```text
Production-readiness or live-deployment claims (deployment liveness is unverified).
```
