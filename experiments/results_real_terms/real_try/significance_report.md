# CPI-deflated real TRY return evaluation (R2-REAL-01)

Descriptive historical research evidence only; not investment value or investment advice. The nominal TRY evaluation remains the canonical headline and is not replaced.

# Headline IC significance report

## Pooled, multiplicity-corrected result

The smallest pooled raw p-value among the six ML models belongs to **random_forest**: pooled IC -0.156, two-sided within-year permutation p=0.0164, Bonferroni-adjusted p=0.0984, and bootstrap 95% CI [-0.276, -0.028].

No ML model is statistically distinguishable from the within-year null after Bonferroni correction; the data do not support a reliable predictive edge.

The pooled statistic is the equal-weighted mean of within-year Spearman ICs. Realized returns are shuffled within each test year, and bootstrap samples resample tickers within each year; years are never pooled before resampling.

## Pooled model results

| Model | Kind | Pooled IC | Permutation p | Null percentile | Bootstrap 95% CI | Bonferroni p | FWER significant |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| baseline_equal_weight | baseline | 0.150 | 0.0168 | 99.2% | [0.024, 0.267] | n/a | not in ML family |
| baseline_rank_score | baseline | 0.150 | 0.0168 | 99.2% | [0.024, 0.267] | n/a | not in ML family |
| elasticnet | ml | -0.019 | 0.7666 | 38.4% | [-0.148, 0.112] | 1.0000 | no |
| gradient_boosting | ml | -0.112 | 0.0820 | 4.1% | [-0.240, 0.023] | 0.4920 | no |
| lasso | ml | 0.107 | 0.1026 | 94.6% | [-0.026, 0.236] | 0.6155 | no |
| linear_regression | ml | 0.038 | 0.5489 | 72.4% | [-0.096, 0.172] | 1.0000 | no |
| random_forest | ml | -0.156 | 0.0164 | 0.8% | [-0.276, -0.028] | 0.0984 | no |
| ridge | ml | 0.095 | 0.1422 | 92.7% | [-0.037, 0.224] | 0.8531 | no |
| robust_rank_aggregation | baseline | 0.128 | 0.0457 | 97.8% | [-0.001, 0.248] | n/a | not in ML family |

## Statistical power and minimum detectable IC

Observed IC, detectable IC, and statistical power answer different questions. Observed IC is the sample estimate from the persisted dumps. Detectable IC is the assumed true |IC| that reaches 80% long-run rejection probability here; it is not a hard significance cutoff. Statistical power is that long-run probability, not the probability that a reported model is true. Practical investment relevance is not evaluated by this calculation.

The analytic calculation uses a two-sided Fisher-z approximation for Spearman IC at alpha=0.05 and target power 80%. It covers one prespecified IC test; it is not the Bonferroni-adjusted family-wise power of the six-model search.

| Design | Scope | Rows/year | Test years | Total rows | Detectable \|IC\| (analytic) | Simulated power at analytic MDE | Agreement |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_one_split | actual prediction-dump design | 80 | 1 | 80 | 0.309 | 0.802 | within ±0.05 |
| current_three_year_pooled | actual prediction-dump design | 80 | 3 | 240 | 0.182 | 0.810 | within ±0.05 |
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

Per-split ICs at n≈40 have SE ≈ 0.16 in the public-40 framing cited by the task queue. The current harness prediction dumps evaluate n=80 per model and split from the internal training universe; with only three test years, these rows remain exploratory and must not be promoted as discoveries.

| Model | Split | Year | n | IC | Permutation p | Bootstrap 95% CI |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| baseline_equal_weight | test_2023 (exploratory) | 2023 | 80 | 0.095 | 0.3972 | [-0.118, 0.290] |
| baseline_equal_weight | test_2024 (exploratory) | 2024 | 80 | 0.212 | 0.0599 | [-0.011, 0.411] |
| baseline_equal_weight | test_2025 (exploratory) | 2025 | 80 | 0.142 | 0.2063 | [-0.094, 0.363] |
| baseline_rank_score | test_2023 (exploratory) | 2023 | 80 | 0.095 | 0.3972 | [-0.118, 0.290] |
| baseline_rank_score | test_2024 (exploratory) | 2024 | 80 | 0.212 | 0.0599 | [-0.011, 0.411] |
| baseline_rank_score | test_2025 (exploratory) | 2025 | 80 | 0.142 | 0.2063 | [-0.094, 0.363] |
| elasticnet | test_2023 (exploratory) | 2023 | 80 | -0.092 | 0.4272 | [-0.314, 0.143] |
| elasticnet | test_2024 (exploratory) | 2024 | 80 | 0.043 | 0.7026 | [-0.179, 0.273] |
| elasticnet | test_2025 (exploratory) | 2025 | 80 | -0.008 | 0.9471 | [-0.240, 0.230] |
| gradient_boosting | test_2023 (exploratory) | 2023 | 80 | -0.143 | 0.2013 | [-0.357, 0.092] |
| gradient_boosting | test_2024 (exploratory) | 2024 | 80 | -0.119 | 0.2991 | [-0.342, 0.117] |
| gradient_boosting | test_2025 (exploratory) | 2025 | 80 | -0.074 | 0.5196 | [-0.299, 0.157] |
| lasso | test_2023 (exploratory) | 2023 | 80 | 0.034 | 0.7675 | [-0.201, 0.266] |
| lasso | test_2024 (exploratory) | 2024 | 80 | 0.170 | 0.1203 | [-0.056, 0.383] |
| lasso | test_2025 (exploratory) | 2025 | 80 | 0.116 | 0.3036 | [-0.116, 0.338] |
| linear_regression | test_2023 (exploratory) | 2023 | 80 | -0.052 | 0.6585 | [-0.276, 0.186] |
| linear_regression | test_2024 (exploratory) | 2024 | 80 | 0.062 | 0.5802 | [-0.167, 0.293] |
| linear_regression | test_2025 (exploratory) | 2025 | 80 | 0.105 | 0.3520 | [-0.129, 0.331] |
| random_forest | test_2023 (exploratory) | 2023 | 80 | -0.193 | 0.0870 | [-0.397, 0.032] |
| random_forest | test_2024 (exploratory) | 2024 | 80 | -0.162 | 0.1538 | [-0.363, 0.049] |
| random_forest | test_2025 (exploratory) | 2025 | 80 | -0.111 | 0.3253 | [-0.330, 0.119] |
| ridge | test_2023 (exploratory) | 2023 | 80 | -0.000 | 0.9962 | [-0.230, 0.231] |
| ridge | test_2024 (exploratory) | 2024 | 80 | 0.203 | 0.0643 | [-0.025, 0.420] |
| ridge | test_2025 (exploratory) | 2025 | 80 | 0.084 | 0.4547 | [-0.143, 0.307] |
| robust_rank_aggregation | test_2023 (exploratory) | 2023 | 80 | 0.088 | 0.4389 | [-0.133, 0.292] |
| robust_rank_aggregation | test_2024 (exploratory) | 2024 | 80 | 0.195 | 0.0809 | [-0.020, 0.391] |
| robust_rank_aggregation | test_2025 (exploratory) | 2025 | 80 | 0.100 | 0.3804 | [-0.133, 0.328] |

## Required limitations

- Only three test years with 80 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- CPI-deflated TRY returns use national December year-on-year CPI as a descriptive basis; they do not represent investor-specific inflation or investment value.
- Research support only; not investment advice.

The absence of a detectable signal in this small, fixed cohort and single regime does not establish that other markets or better point-in-time datasets are unpredictable.
