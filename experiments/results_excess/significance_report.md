# Excess return vs BIST100 (nominal TRY, percentage points) evaluation (R3-TGT-01)

Descriptive historical research evidence only; not investment value or investment advice. The nominal TRY evaluation remains the canonical headline and is not replaced.

Target: `next_year_excess_return_vs_bist100`. Generator: `experiments/run_excess_basis.py`. Regenerate with `make research-excess` using the recorded frozen splits, model specifications, and seeds.

## Family-level conclusion

No model in the prespecified six-model ML family is distinguishable from the within-year null after Bonferroni correction across the family, and none is distinguishable under the post-review trajectory-preserving sensitivity after the same six-model correction. The excess return basis establishes no reliable predictive edge.

A bootstrap interval is descriptive uncertainty evidence and does not replace the closed-family correction. No model survives family-wise correction, and no reliable predictive edge is established.

## Reporting policy

All six prespecified ML-family members are reported symmetrically. No model is selected or privileged using the observed excess-target IC, raw p-value, adjusted p-value, bootstrap interval, or any other outcome-derived statistic.

Models appear below in the frozen prespecified order (linear_regression, ridge, lasso, elasticnet, random_forest, gradient_boosting), which is fixed in advance and is never reordered by an observed statistic.

## Estimand: within-year ordinal ranking

The within-year Spearman IC evaluates ordinal cross-sectional ranking: whether a model orders the evaluated cohort correctly inside one evaluation year. It does not evaluate benchmark-relative magnitude accuracy, and it does not estimate alpha, economic outperformance, investment value, or a tradable strategy.

The nominal target column is traced from repository authority (`experiments/run_experiments.py::TARGETS[0]`) rather than assumed, and the derivation `next_year_excess_return_vs_bist100 = next_year_return_pct - next_year_bist100_return_pct` is read from `scripts/data_collection/pipeline.py`. The audit below then checks, on the exact evaluated rows, that the subtraction is one common value inside each evaluation year and that the two targets rank the cohort identically. The run fails if either condition does not hold.

| Evaluation year | Evaluated rows | Common BIST100 return subtracted (pp) | Within-year subtrahend spread | Rank mismatches |
| ---: | ---: | ---: | ---: | ---: |
| 2023 | 40 | 31.96 | 5.68e-14 | 0 |
| 2024 | 40 | 28.94 | 1.42e-14 | 0 |
| 2025 | 40 | 12.64 | 2.84e-14 | 0 |

Nominal target column: `next_year_return_pct`. Excess target column: `next_year_excess_return_vs_bist100`. Total rank mismatch count across 2023, 2024, and 2025: **0**.

Within each evaluation year the benchmark subtraction is one common constant, so the next_year_excess_return_vs_bist100 ranks equal the next_year_return_pct ranks in every year and the total rank mismatch count is 0. The within-year Spearman IC reported here is therefore the same ordinal ranking estimand as on the nominal basis, evaluated on a different cohort. Identical evaluation ranks do not make the two analyses identical: the shifted target can still change what the models fit, and an unchanged ordinal estimand is not evidence of alpha, benchmark-relative magnitude accuracy, investment value, or a tradable strategy.

Benchmark subtraction may still affect fitting: it shifts the target by a year-level constant across the training panel, so models trained on pooled years can learn different coefficients than on the nominal basis. It does not alter within-year evaluation ranks, so the evaluated estimand is unchanged.

## Permutation analyses: prespecified primary and post-review sensitivity

Two permutation analyses are reported side by side. They answer different questions and neither replaces the other.

**`primary_independent_within_year_permutation`** (prespecified, unchanged). Null: Within each evaluation year, realized cross-sectional outcomes are exchangeable relative to the model predictions, with each year permuted independently. It uses 10,000 draws at seed 42, a two-sided absolute tail, the Monte Carlo correction `(extreme_count + 1) / (draw_count + 1)`, the equal-year pooled IC, and 6-model Bonferroni adjustment. Human review did not change its seed, draw count, tail, correction, statistic, or family size, and it was not renamed or replaced.

**`trajectory_preserving_ticker_permutation_sensitivity`** (post_review_sensitivity). Null: Ticker identities are exchangeable as complete cross-year trajectories: one permutation of the ticker universe is drawn per replication and applied identically in every evaluation year, so a ticker's realized outcomes move together and any cross-year persistence in the realized panel is preserved under the null. It uses 10,000 draws at frozen seed 42, a two-sided absolute tail, the same Monte Carlo correction `(extreme_count + 1) / (draw_count + 1)`, the equal-year pooled IC, and the same 6-model Bonferroni adjustment applied independently to its own raw p-values.

Added after human review at the reviewer's request. It is a sensitivity analysis, not a prespecified analysis and not a replacement for the primary independently-within-year permutation, which is retained unchanged.

Sensitivity algorithm, per draw:

1. Use the balanced 40-ticker x 3-year panel of persisted prediction rows.
2. Sort and validate the unique ticker universe.
3. Generate one permutation of ticker identities per draw.
4. Apply that same ticker permutation mapping in 2023, 2024, and 2025.
5. Keep the prediction rows fixed.
6. Move each realized-outcome ticker trajectory as a complete block across all years.
7. Recompute the Spearman IC independently within each year.
8. Take the equal-year mean of the valid yearly ICs.
9. Repeat for 10,000 draws from the frozen documented seed.
10. Compute the two-sided Monte Carlo p-value (extreme_count + 1) / (draw_count + 1).
11. Apply the same frozen six-model Bonferroni correction min(1, raw_p * 6).

Each mapping is a duplicate-free one-to-one permutation of the 40-ticker universe: this is a permutation test, not a bootstrap. The following inputs are refused rather than degraded (ExcessPermutationError, ExcessPanelError): ragged ticker coverage; missing years; duplicate ticker/year rows; malformed ticker or year values; unequal ticker sets across years; non-finite targets or predictions; insufficient tickers; insufficient valid permutation draws; independently generated per-year permutation mappings; mappings that are not duplicate-free one-to-one permutations.

## Evaluated cohort

The evaluated cohort is the benchmark-covered public 40: the 40 tickers that carry a valid BIST100-relative excess target. It is a subset of the wider internal training universe used by the nominal basis. Rows without a valid excess target remain null and are never filled.

| Test year | Evaluated rows (excess basis) | Nominal-basis rows (context) |
| ---: | ---: | ---: |
| 2023 | 40 | 80 |
| 2024 | 40 | 80 |
| 2025 | 40 | 80 |

The 80-row column is nominal-basis context on a different target and a wider cohort. It is not this evaluation's design. The evaluated design is 40 rows per evaluation year in 2023, 2024, and 2025.

Aggregate leaderboard reconstruction status: **match**. The existing aggregate is read-only; any disagreement is reported in the JSON artifact and is not patched.

## Prespecified six-model ML family

All six members are reported with the same schema, in the frozen order. Both analyses appear for every member: raw and Bonferroni-adjusted p-values are paired for the prespecified primary permutation and, separately, for the post-review trajectory-preserving sensitivity. No member is singled out as strongest, and no minimum-p member is identified.

| Model | Pooled IC | Permutation p (raw) | Bonferroni-adjusted p | Sensitivity permutation p (raw) | Sensitivity Bonferroni-adjusted p | Either corrected analysis rejects at FWER 0.05 | Ticker-cluster bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| linear_regression | -0.117 | 0.2074 | 1.0000 | 0.2231 | 1.0000 | no | [-0.264, 0.047] |
| ridge | -0.038 | 0.6820 | 1.0000 | 0.6963 | 1.0000 | no | [-0.222, 0.155] |
| lasso | -0.095 | 0.2993 | 1.0000 | 0.3300 | 1.0000 | no | [-0.249, 0.072] |
| elasticnet | -0.063 | 0.4873 | 1.0000 | 0.5565 | 1.0000 | no | [-0.281, 0.166] |
| random_forest | -0.211 | 0.0223 | 0.1338 | 0.0416 | 0.2496 | no | [-0.420, 0.014] |
| gradient_boosting | -0.211 | 0.0217 | 0.1302 | 0.0411 | 0.2466 | no | [-0.424, 0.010] |

0 of 6 family members survive the Bonferroni gate at a family-wise alpha of 0.05 under the prespecified primary permutation, and 0 of 6 survive it under the post-review trajectory-preserving sensitivity. Both counts are computed from the adjusted p-values above; neither is assumed.

Neither the prespecified primary permutation nor the post-review trajectory-preserving sensitivity rejects for any of the six family members after the six-model Bonferroni correction at a family-wise alpha of 0.05.

## Non-family baselines

These three baselines sit outside the ML family. They are context only: their p-values are unadjusted and are not part of the corrected family, under either analysis.

| Baseline | Pooled IC | Permutation p (raw, unadjusted) | Sensitivity permutation p (raw, unadjusted) | Ticker-cluster bootstrap 95% interval |
| --- | ---: | ---: | ---: | --- |
| baseline_equal_weight | -0.095 | 0.3048 | 0.3827 | [-0.317, 0.132] |
| baseline_rank_score | -0.095 | 0.3048 | 0.3827 | [-0.317, 0.132] |
| robust_rank_aggregation | -0.100 | 0.2796 | 0.3653 | [-0.304, 0.117] |

## Resampling procedure

The pooled statistic is the equal-weighted mean of within-year Spearman ICs. Realized returns are shuffled within each test year for the permutation test; years are never pooled before permuting.

For each resample, N ticker identities are drawn with replacement from the N cohort tickers. That single ticker vector is applied to every evaluation year, so each sampled ticker contributes its complete trajectory and repeated tickers keep their multiplicity. Years are never resampled independently. The statistic is the equal-year mean of the valid within-year Spearman ICs.

Bootstrap unit: `ticker_cluster`; cluster key: `ticker`; 40 clusters over trajectory years 2023, 2024, 2025; 10000 resamples at seed 42; interval convention: percentile; 2.5th and 97.5th quantiles of the resample distribution.

Interval role: descriptive sampling uncertainty; it does not replace or weaken the Bonferroni family-wise correction.

## Statistical power and minimum detectable IC

Observed IC, detectable IC, and statistical power answer different questions. Observed IC is the sample estimate from the persisted dumps. Detectable IC is the assumed true |IC| that reaches 80% long-run rejection probability here; it is not a hard significance cutoff. Statistical power is that long-run probability, not the probability that a reported model is true. Practical investment relevance is not evaluated by this calculation.

The analytic calculation uses a two-sided Fisher-z approximation for Spearman IC at alpha=0.05 and target power 80%. It covers one prespecified IC test; it is not the Bonferroni-adjusted family-wise power of the six-model family.

### Current design (observed)

The current evaluated design is 40 rows per evaluation year across 2023, 2024, and 2025, 120 evaluated rows per model in total. It is read from the persisted prediction dumps rather than assumed. The two rows below are two views of that one design, not two designs.

| View of the current design | Rows/year | Test years | Total rows | Detectable \|IC\| (analytic) | Simulated power at analytic MDE | Agreement |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| single_evaluation_year | 40 | 1 | 40 | 0.431 | 0.794 | within ±0.05 |
| pooled_evaluation_years | 40 | 3 | 120 | 0.260 | 0.791 | within ±0.05 |

The seeded Gaussian-copula rank simulation checks several assumed true ICs for each view; full curves are in `significance_report.json`. Agreement means the simulated rejection rate at the analytic MDE is within 0.05 of 80%, not that the approximation or underlying design assumptions are proven correct.

The detectable |IC| at the current design is large relative to any plausible annual equity-ranking IC, so the family-wide failure to reject is a low-power non-rejection. It does not establish that the true IC is zero, and it is not evidence of predictive validity in either direction.

### Hypothetical planning horizons (not current evidence)

Hypothetical planning horizons for the public-universe scale; never a description of the evidence that exists today.

The pipeline is ready for more data; this is pipeline capability, not a promise that more data will produce predictive skill or practical returns.

These rows are hypothetical. They describe evidence that does not exist yet. They are deduplicated against the observed design on the pair (rows_per_year, test_years), so none of them restates the current design.

| Additional test years (hypothetical) | Total test years | Planning rows/year | Detectable \|IC\| (analytic) |
| ---: | ---: | ---: | ---: |
| 1 | 4 | 40 | 0.226 |
| 2 | 5 | 40 | 0.203 |
| 3 | 6 | 40 | 0.186 |
| 5 | 8 | 40 | 0.161 |
| 7 | 10 | 40 | 0.145 |

Power-analysis limits:

- Only three test years are observed; treating within-year IC estimates as independent is an approximation.
- The calculation assumes equal per-year sample sizes and a stable true IC across years, neither of which establishes regime generality.
- The evaluated design is 40 rows per evaluation year across 2023, 2024, and 2025; the additional-test-year table is a hypothetical planning horizon and is not current evidence.
- The cohort is retrospective rather than verified point-in-time membership, and reproducibility remains numerical-environment-qualified.
- Power bounds detection under assumptions; it neither estimates the true IC nor establishes practical investment relevance.
- A low-power non-rejection is not a demonstration that the true IC is zero, and no power figure here is a statement of predictive validity.

## Exploratory per-year results

The excess-basis dumps evaluate n=40 per model and year from the benchmark-covered public 40. Each year below is a marginal view of the same shared ticker-cluster resample. With only three test years these rows remain exploratory and must not be promoted as discoveries.

| Model | Year | n | IC | Permutation p | Ticker-cluster bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | --- |
| linear_regression | 2023 | 40 | -0.057 | 0.7202 | [-0.395, 0.298] |
| linear_regression | 2024 | 40 | -0.204 | 0.2056 | [-0.504, 0.119] |
| linear_regression | 2025 | 40 | -0.091 | 0.5712 | [-0.403, 0.225] |
| ridge | 2023 | 40 | 0.105 | 0.5225 | [-0.232, 0.422] |
| ridge | 2024 | 40 | 0.049 | 0.7613 | [-0.293, 0.388] |
| ridge | 2025 | 40 | -0.269 | 0.0906 | [-0.554, 0.043] |
| lasso | 2023 | 40 | 0.051 | 0.7474 | [-0.303, 0.398] |
| lasso | 2024 | 40 | -0.147 | 0.3564 | [-0.457, 0.178] |
| lasso | 2025 | 40 | -0.189 | 0.2389 | [-0.496, 0.137] |
| elasticnet | 2023 | 40 | 0.116 | 0.4795 | [-0.216, 0.426] |
| elasticnet | 2024 | 40 | -0.006 | 0.9679 | [-0.354, 0.344] |
| elasticnet | 2025 | 40 | -0.299 | 0.0608 | [-0.603, 0.031] |
| random_forest | 2023 | 40 | -0.035 | 0.8304 | [-0.367, 0.311] |
| random_forest | 2024 | 40 | -0.333 | 0.0345 | [-0.611, -0.028] |
| random_forest | 2025 | 40 | -0.266 | 0.0956 | [-0.559, 0.069] |
| gradient_boosting | 2023 | 40 | -0.047 | 0.7746 | [-0.372, 0.290] |
| gradient_boosting | 2024 | 40 | -0.359 | 0.0204 | [-0.620, -0.053] |
| gradient_boosting | 2025 | 40 | -0.228 | 0.1607 | [-0.545, 0.125] |
| baseline_equal_weight | 2023 | 40 | -0.381 | 0.0144 | [-0.615, -0.083] |
| baseline_equal_weight | 2024 | 40 | 0.055 | 0.7259 | [-0.272, 0.376] |
| baseline_equal_weight | 2025 | 40 | 0.042 | 0.8008 | [-0.323, 0.397] |
| baseline_rank_score | 2023 | 40 | -0.381 | 0.0144 | [-0.615, -0.083] |
| baseline_rank_score | 2024 | 40 | 0.055 | 0.7259 | [-0.272, 0.376] |
| baseline_rank_score | 2025 | 40 | 0.042 | 0.8008 | [-0.323, 0.397] |
| robust_rank_aggregation | 2023 | 40 | -0.328 | 0.0369 | [-0.590, -0.011] |
| robust_rank_aggregation | 2024 | 40 | 0.053 | 0.7387 | [-0.260, 0.370] |
| robust_rank_aggregation | 2025 | 40 | -0.023 | 0.8869 | [-0.371, 0.329] |

## Cross-basis multiplicity

Nominal return is the sole confirmatory family. The real-TRY, USD, and excess-return analyses are exploratory robustness evaluations. Within-basis Bonferroni corrections do not control multiplicity across the several target bases, so the number of bases examined inflates the chance that some basis eventually produces a small p-value.

Confirmatory family: `nominal_try_return` (`next_year_return_pct`). Exploratory robustness bases: `real_try_return`, `usd_return`, `excess_vs_bist100`. This evaluation is `excess_vs_bist100`, an exploratory robustness evaluation.

A future significant alternative-basis result must not be described as confirmatory without a separately prespecified cross-basis correction.

The canonical nominal artifacts are not altered by this task.

## Coincident baseline specifications

`baseline_equal_weight` and `baseline_rank_score` produce bitwise-identical prediction values on every evaluated ticker and year in the persisted dumps, which necessarily makes their ranks and their ICs identical as well.

Equality level established from the persisted dumps: `identical_prediction_values`; maximum absolute prediction difference 0.0 across all evaluated rows. Only the strongest level the persisted evidence actually supports is stated; weaker or stronger characterisations are not used.

Coincident baseline results must not be interpreted as independent baseline diversity: two baselines that agree at this level contribute one distinct comparison, not two.

Both specifications are retained for frozen-specification continuity. Neither is removed, because no repository authority has explicitly permitted removing a frozen model specification.

## Interpretation of predominantly negative IC signs

6 of 6 prespecified ML-family members have a negative pooled equal-year IC on this basis.

Predominantly negative IC signs may reflect sampling variation, feature-orientation effects, or systematic construction effects. They are not interpreted as inverse alpha, a contrarian strategy, an actionable signal, or validated predictive evidence.

The note is family-level. No member is selected or privileged by the sign or magnitude of its IC, and the tree-based members are not singled out.

## Scope of the compact human-review package

- The compact package supports review of the persisted prediction-to-significance layer: the row-level prediction dumps, the dump-reconstructed leaderboard, the significance report, and the artifact manifest.
- It does not alone provide standalone reproduction of feature construction and model fitting.
- The repository technical review separately covers governed source paths, protected hashes, split tracing, and implementation behavior.
- No claim of complete independent fitting-stage replication is made from the compact package alone.

## Required limitations

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

The absence of a detectable signal in this small, fixed cohort and single regime does not establish that other markets or better point-in-time datasets are unpredictable.

This excess-return-basis evaluation is a descriptive historical research result; it does not establish signal, investment value, or a reliable predictive edge. Any isolated year or uncorrected p-value remains exploratory and must not be promoted as a finding.
