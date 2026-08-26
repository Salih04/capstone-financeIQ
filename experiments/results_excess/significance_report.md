# Excess return vs BIST100 (nominal TRY, percentage points) evaluation (R3-TGT-01)

Descriptive historical research evidence only; not investment value or investment advice. The nominal TRY evaluation remains the canonical headline and is not replaced.

Target: `next_year_excess_return_vs_bist100` — the nominal TRY return minus the BIST100 nominal TRY index return, in percentage points. Benchmark-relative coverage shrinks the evaluated panel; rows without a valid excess target remain null and are never filled. Evaluated rows per test year:

| Test year | Evaluated rows (excess basis) | Nominal-basis rows (context) |
| ---: | ---: | ---: |
| 2023 | 40 | 80 |
| 2024 | 40 | 80 |
| 2025 | 40 | 80 |

# Headline IC significance report

## Pooled, multiplicity-corrected result

The smallest pooled raw p-value among the six ML models belongs to **gradient_boosting**: pooled IC -0.211, two-sided within-year permutation p=0.0217, Bonferroni-adjusted p=0.1302, and bootstrap 95% CI [-0.387, -0.023].

No ML model is statistically distinguishable from the within-year null after Bonferroni correction; the data do not support a reliable predictive edge.

The pooled statistic is the equal-weighted mean of within-year Spearman ICs. Realized returns are shuffled within each test year, and bootstrap samples resample tickers within each year; years are never pooled before resampling.

## Pooled model results

| Model | Kind | Pooled IC | Permutation p | Null percentile | Bootstrap 95% CI | Bonferroni p | FWER significant |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| baseline_equal_weight | baseline | -0.095 | 0.3048 | 14.8% | [-0.273, 0.091] | n/a | not in ML family |
| baseline_rank_score | baseline | -0.095 | 0.3048 | 14.8% | [-0.273, 0.091] | n/a | not in ML family |
| elasticnet | ml | -0.063 | 0.4873 | 24.6% | [-0.249, 0.126] | 1.0000 | no |
| gradient_boosting | ml | -0.211 | 0.0217 | 1.0% | [-0.387, -0.023] | 0.1302 | no |
| lasso | ml | -0.095 | 0.2993 | 15.3% | [-0.283, 0.102] | 1.0000 | no |
| linear_regression | ml | -0.117 | 0.2074 | 10.7% | [-0.303, 0.075] | 1.0000 | no |
| random_forest | ml | -0.211 | 0.0223 | 1.1% | [-0.385, -0.023] | 0.1338 | no |
| ridge | ml | -0.038 | 0.6820 | 34.8% | [-0.223, 0.152] | 1.0000 | no |
| robust_rank_aggregation | baseline | -0.100 | 0.2796 | 13.8% | [-0.276, 0.089] | n/a | not in ML family |

## Statistical power and minimum detectable IC

Observed IC, detectable IC, and statistical power answer different questions. Observed IC is the sample estimate from the persisted dumps. Detectable IC is the assumed true |IC| that reaches 80% long-run rejection probability here; it is not a hard significance cutoff. Statistical power is that long-run probability, not the probability that a reported model is true. Practical investment relevance is not evaluated by this calculation.

The analytic calculation uses a two-sided Fisher-z approximation for Spearman IC at alpha=0.05 and target power 80%. It covers one prespecified IC test; it is not the Bonferroni-adjusted family-wise power of the six-model search.

| Design | Scope | Rows/year | Test years | Total rows | Detectable \|IC\| (analytic) | Simulated power at analytic MDE | Agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_one_split | actual prediction-dump design | 40 | 1 | 40 | 0.431 | 0.794 | within ±0.05 |
| current_three_year_pooled | actual prediction-dump design | 40 | 3 | 120 | 0.260 | 0.791 | within ±0.05 |
| public_40_one_split_sensitivity | planning sensitivity; not the current dump design | 40 | 1 | 40 | 0.431 | 0.787 | within ±0.05 |
| public_40_three_year_sensitivity | planning sensitivity; not the current dump design | 40 | 3 | 120 | 0.260 | 0.793 | within ±0.05 |

The seeded Gaussian-copula rank simulation checks several assumed true ICs for each design; full curves are in `significance_report.json`. Agreement means the simulated rejection rate at the analytic MDE is within 0.05 of 80%, not that the approximation or underlying design assumptions are proven correct.

### Forty-ticker-per-year planning projection

The pipeline is ready for more data; this is pipeline capability, not a promise that more data will produce predictive skill or practical returns.

| Additional test years | Total test years | Tickers/year | Detectable \|IC\| (analytic) |
| ---: | ---: | ---: | ---: |
| 0 | 3 | 40 | 0.260 |
| 1 | 4 | 40 | 0.226 |
| 2 | 5 | 40 | 0.203 |
| 3 | 6 | 40 | 0.186 |
| 5 | 8 | 40 | 0.161 |
| 7 | 10 | 40 | 0.145 |

Power-analysis limits:

- Only three test years are observed; treating within-year IC estimates as independent is an approximation.
- The calculation assumes equal per-year sample sizes and a stable true IC across years, neither of which establishes regime generality.
- The 40-ticker table is a planning sensitivity for the public-universe scale, not the current 80-row prediction-dump design.
- The cohort is retrospective rather than verified point-in-time membership, and reproducibility remains numerical-environment-qualified.
- Power bounds detection under assumptions; it neither estimates the true IC nor establishes practical investment relevance.

Bonferroni correction covers the six ML models only; baselines are shown as context and are not part of that model-selection family. Their p-values are unadjusted and descriptive; they do not establish a reliable edge in only three test years from a retrospectively fixed cohort.

## Exploratory per-split results

Per-split ICs at n≈40 have SE ≈ 0.16 in the public-40 framing cited by the task queue. The current harness prediction dumps evaluate n=40 per model and split from the internal training universe; with only three test years, these rows remain exploratory and must not be promoted as discoveries.

| Model | Split | Year | n | IC | Permutation p | Bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| baseline_equal_weight | test_2023 (exploratory) | 2023 | 40 | -0.381 | 0.0144 | [-0.616, -0.082] |
| baseline_equal_weight | test_2024 (exploratory) | 2024 | 40 | 0.055 | 0.7259 | [-0.282, 0.377] |
| baseline_equal_weight | test_2025 (exploratory) | 2025 | 40 | 0.042 | 0.8008 | [-0.327, 0.391] |
| baseline_rank_score | test_2023 (exploratory) | 2023 | 40 | -0.381 | 0.0144 | [-0.616, -0.082] |
| baseline_rank_score | test_2024 (exploratory) | 2024 | 40 | 0.055 | 0.7259 | [-0.282, 0.377] |
| baseline_rank_score | test_2025 (exploratory) | 2025 | 40 | 0.042 | 0.8008 | [-0.327, 0.391] |
| elasticnet | test_2023 (exploratory) | 2023 | 40 | 0.116 | 0.4795 | [-0.208, 0.431] |
| elasticnet | test_2024 (exploratory) | 2024 | 40 | -0.006 | 0.9679 | [-0.348, 0.344] |
| elasticnet | test_2025 (exploratory) | 2025 | 40 | -0.299 | 0.0608 | [-0.593, 0.029] |
| gradient_boosting | test_2023 (exploratory) | 2023 | 40 | -0.047 | 0.7746 | [-0.371, 0.302] |
| gradient_boosting | test_2024 (exploratory) | 2024 | 40 | -0.359 | 0.0204 | [-0.619, -0.048] |
| gradient_boosting | test_2025 (exploratory) | 2025 | 40 | -0.228 | 0.1607 | [-0.540, 0.122] |
| lasso | test_2023 (exploratory) | 2023 | 40 | 0.051 | 0.7474 | [-0.293, 0.406] |
| lasso | test_2024 (exploratory) | 2024 | 40 | -0.147 | 0.3564 | [-0.458, 0.179] |
| lasso | test_2025 (exploratory) | 2025 | 40 | -0.189 | 0.2389 | [-0.496, 0.143] |
| linear_regression | test_2023 (exploratory) | 2023 | 40 | -0.057 | 0.7202 | [-0.392, 0.296] |
| linear_regression | test_2024 (exploratory) | 2024 | 40 | -0.204 | 0.2056 | [-0.505, 0.122] |
| linear_regression | test_2025 (exploratory) | 2025 | 40 | -0.091 | 0.5712 | [-0.402, 0.237] |
| random_forest | test_2023 (exploratory) | 2023 | 40 | -0.035 | 0.8304 | [-0.361, 0.310] |
| random_forest | test_2024 (exploratory) | 2024 | 40 | -0.333 | 0.0345 | [-0.608, -0.018] |
| random_forest | test_2025 (exploratory) | 2025 | 40 | -0.266 | 0.0956 | [-0.558, 0.077] |
| ridge | test_2023 (exploratory) | 2023 | 40 | 0.105 | 0.5225 | [-0.231, 0.431] |
| ridge | test_2024 (exploratory) | 2024 | 40 | 0.049 | 0.7613 | [-0.292, 0.384] |
| ridge | test_2025 (exploratory) | 2025 | 40 | -0.269 | 0.0906 | [-0.545, 0.039] |
| robust_rank_aggregation | test_2023 (exploratory) | 2023 | 40 | -0.328 | 0.0369 | [-0.593, -0.003] |
| robust_rank_aggregation | test_2024 (exploratory) | 2024 | 40 | 0.053 | 0.7387 | [-0.267, 0.367] |
| robust_rank_aggregation | test_2025 (exploratory) | 2025 | 40 | -0.023 | 0.8869 | [-0.371, 0.326] |

## Required limitations

- Only three test years with 40 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- Excess returns subtract the BIST100 nominal TRY index return within one unusual macro regime; they are a descriptive benchmark-relative basis and do not represent an implementable benchmark-hedged position or investment value.
- Research support only; not investment advice.
- BIST100 benchmark-relative coverage exists for only part of the evaluation panel; rows without a valid excess target remain null and shrink the evaluated n per year rather than being filled.

The absence of a detectable signal in this small, fixed cohort and single regime does not establish that other markets or better point-in-time datasets are unpredictable.

This excess-return-basis evaluation is a descriptive historical research result; it does not establish signal, investment value, or a reliable predictive edge. Any isolated split or uncorrected p-value remains exploratory and must not be promoted as a finding.
