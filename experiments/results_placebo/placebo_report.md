# Negative-control / placebo laboratory

## Question and estimand

This R3-NULL-01 artifact tests whether the committed significance rig usually *fails to reject* known-null inputs, with any rejection counted as a family-wise false positive. Each of 25 seeded repetitions rebuilds the real modeling panel but replaces every feature column with independent N(0,1) noise, runs the same six-model ML family through the same walk-forward splits, and applies the same permutation + Bonferroni family-wise gate from `experiments/significance.py`. Targets, splits, model definitions, and significance settings are the real ones; only the features are noise.

> Placebo runs test the evaluation machinery, not the market; the expected outcome is failure to reject known-null inputs in approximately (1 − α) of repetitions, and any placebo ‘significance’ is a false positive at rate α or a numerical artifact — never a signal.

## Design

- Repetitions: 25 (base noise seed 314159)
- Panel: 321 rows, 40 features fully replaced by noise
- Feature-years: [2020, 2021, 2022, 2023, 2024]; target years: [2023, 2024, 2025]
- Model family (family-wise gate): linear_regression, ridge, lasso, elasticnet, random_forest, gradient_boosting
- Significance: 10000 permutations, 10000 bootstraps, seed 42, Bonferroni family size 6, alpha 0.05
- Model-family choice: Six-model ML family only -- identical to the real evaluation's Bonferroni selection family in experiments/significance.py. Baseline models and the analytic power analysis are outside the family-wise gate and are omitted to keep the 20x-harness runtime tractable, as the R3-NULL-01 packet permits.

## Result

- Repetitions completed: 25 / 25 (failed: 0)
- Family-wise rejections: **0** (rate 0.0)
- Binomial expectation under alpha=0.05: 1.25 rejections over 25 scored repetitions
- P(X >= observed) = 1.0; P(X <= observed) = 0.2773895731
- Exact two-sided 95% Clopper-Pearson upper bound for 0/25: 0.1371851715
- Interval method: For 0/n events, solve (1 - p_upper)^n = (1 - confidence)/2, so p_upper = 1 - ((1 - confidence)/2)^(1/n).
- Pooled-IC distribution across repetitions/models: min -0.1272101741, mean -0.0149645295, max 0.1512355114

Bonferroni control makes alpha*n an upper reference; observed at or below it is the expected, on-spec outcome and is not evidence of skill.

## Per-repetition records

Optional per-repetition wall-clock output is local runtime data outside this governed results directory; it is excluded so this scientific report is byte-identical across seeded reruns.

| Rep | Seed | Status | Min raw p | Bonferroni min p | Rejected (FWER) |
|---:|---:|---|---:|---:|---|
| 0 | 314159 | complete | 0.5833416658 | 1.0 | no |
| 1 | 314160 | complete | 0.6905309469 | 1.0 | no |
| 2 | 314161 | complete | 0.5829417058 | 1.0 | no |
| 3 | 314162 | complete | 0.3512648735 | 1.0 | no |
| 4 | 314163 | complete | 0.5708429157 | 1.0 | no |
| 5 | 314164 | complete | 0.101189881 | 0.6071392861 | no |
| 6 | 314165 | complete | 0.1395860414 | 0.8375162484 | no |
| 7 | 314166 | complete | 0.204379562 | 1.0 | no |
| 8 | 314167 | complete | 0.1288871113 | 0.7733226677 | no |
| 9 | 314168 | complete | 0.0495950405 | 0.297570243 | no |
| 10 | 314169 | complete | 0.3705629437 | 1.0 | no |
| 11 | 314170 | complete | 0.3472652735 | 1.0 | no |
| 12 | 314171 | complete | 0.2067793221 | 1.0 | no |
| 13 | 314172 | complete | 0.1541845815 | 0.9251074893 | no |
| 14 | 314173 | complete | 0.2255774423 | 1.0 | no |
| 15 | 314174 | complete | 0.303269673 | 1.0 | no |
| 16 | 314175 | complete | 0.0614938506 | 0.3689631037 | no |
| 17 | 314176 | complete | 0.4612538746 | 1.0 | no |
| 18 | 314177 | complete | 0.2880711929 | 1.0 | no |
| 19 | 314178 | complete | 0.1057894211 | 0.6347365263 | no |
| 20 | 314179 | complete | 0.5616438356 | 1.0 | no |
| 21 | 314180 | complete | 0.1188881112 | 0.7133286671 | no |
| 22 | 314181 | complete | 0.0577942206 | 0.3467653235 | no |
| 23 | 314182 | complete | 0.1573842616 | 0.9443055694 | no |
| 24 | 314183 | complete | 0.0191980802 | 0.1151884812 | no |

## Interpretation boundaries

- The rejection count is the result: it is compared with the Binomial(R, alpha) expectation, and every repetition -- including any that rejected -- is retained in full.
- A placebo repetition that rejects is a false positive of the rig at rate alpha or a numerical artifact, never evidence about any market or ticker.
- Features are fully overwritten by independent N(0,1) noise; only the real tickers, feature-years, splits, and targets are kept so the machinery runs unchanged.
- No canonical dataset, prediction dump, leaderboard, or significance artifact is modified; each repetition is scored in a private temporary directory.

## Limitations

- This is a test of the evaluation rig on synthetic noise, not a market study; nothing here supports or refutes any claim about BIST equities.
- The gate uses the six-model ML Bonferroni family and the committed permutation/bootstrap settings; it does not re-run the analytic power analysis or the baseline models.
- Bonferroni control is conservative, so the empirical rejection rate is expected to sit at or below alpha rather than exactly at it.
- R=25 is a low-resolution negative-control smoke test.
- 0/25 does not certify exact family-wise calibration at alpha=0.05.
- It can expose gross anti-conservatism but cannot precisely estimate the Type-I error rate.
- For 0/25, the exact two-sided 95% Clopper-Pearson binomial upper bound is approximately 0.137 (unrounded 0.1371851715) using the documented zero-event closed form.
- Reproduction is numerical-environment-qualified; byte identity holds within a fixed Python and numerical-package environment.
- The conclusion of the project is unchanged: no reliable predictive edge. Research support only; not investment advice.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
