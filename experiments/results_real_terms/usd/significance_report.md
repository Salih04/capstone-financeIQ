# USD-basis return evaluation (R2-REAL-01)

Descriptive historical research evidence only; not investment value or investment advice. The nominal TRY evaluation remains the canonical headline and is not replaced.

# Headline IC significance report

## Pooled, multiplicity-corrected result

The smallest pooled raw p-value among the six ML models belongs to **random_forest**: pooled IC -0.150, two-sided within-year permutation p=0.0213, Bonferroni-adjusted p=0.1278, and bootstrap 95% CI [-0.273, -0.023].

No ML model is statistically distinguishable from the within-year null after Bonferroni correction; the data do not support a reliable predictive edge.

The pooled statistic is the equal-weighted mean of within-year Spearman ICs. Realized returns are shuffled within each test year, and bootstrap samples resample tickers within each year; years are never pooled before resampling.

## Pooled model results

| Model | Kind | Pooled IC | Permutation p | Null percentile | Bootstrap 95% CI | Bonferroni p | FWER significant |
| --- | --- | ---: | ---: | ---: | --- | ---: | --- |
| baseline_equal_weight | baseline | 0.150 | 0.0168 | 99.2% | [0.024, 0.267] | n/a | not in ML family |
| baseline_rank_score | baseline | 0.150 | 0.0168 | 99.2% | [0.024, 0.267] | n/a | not in ML family |
| elasticnet | ml | -0.015 | 0.8122 | 40.6% | [-0.144, 0.117] | 1.0000 | no |
| gradient_boosting | ml | -0.133 | 0.0392 | 2.1% | [-0.256, -0.003] | 0.2352 | no |
| lasso | ml | 0.108 | 0.0978 | 94.9% | [-0.026, 0.237] | 0.5867 | no |
| linear_regression | ml | 0.060 | 0.3557 | 82.1% | [-0.073, 0.191] | 1.0000 | no |
| random_forest | ml | -0.150 | 0.0213 | 1.0% | [-0.273, -0.023] | 0.1278 | no |
| ridge | ml | 0.096 | 0.1439 | 92.5% | [-0.035, 0.224] | 0.8633 | no |
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
| elasticnet | test_2023 (exploratory) | 2023 | 80 | -0.097 | 0.3961 | [-0.315, 0.136] |
| elasticnet | test_2024 (exploratory) | 2024 | 80 | 0.064 | 0.5668 | [-0.158, 0.291] |
| elasticnet | test_2025 (exploratory) | 2025 | 80 | -0.011 | 0.9205 | [-0.245, 0.224] |
| gradient_boosting | test_2023 (exploratory) | 2023 | 80 | -0.181 | 0.1065 | [-0.391, 0.051] |
| gradient_boosting | test_2024 (exploratory) | 2024 | 80 | -0.116 | 0.3080 | [-0.329, 0.106] |
| gradient_boosting | test_2025 (exploratory) | 2025 | 80 | -0.102 | 0.3755 | [-0.324, 0.121] |
| lasso | test_2023 (exploratory) | 2023 | 80 | 0.007 | 0.9495 | [-0.222, 0.233] |
| lasso | test_2024 (exploratory) | 2024 | 80 | 0.198 | 0.0706 | [-0.024, 0.412] |
| lasso | test_2025 (exploratory) | 2025 | 80 | 0.118 | 0.2957 | [-0.117, 0.343] |
| linear_regression | test_2023 (exploratory) | 2023 | 80 | -0.040 | 0.7297 | [-0.269, 0.194] |
| linear_regression | test_2024 (exploratory) | 2024 | 80 | 0.100 | 0.3784 | [-0.131, 0.323] |
| linear_regression | test_2025 (exploratory) | 2025 | 80 | 0.121 | 0.2854 | [-0.119, 0.351] |
| random_forest | test_2023 (exploratory) | 2023 | 80 | -0.135 | 0.2381 | [-0.342, 0.089] |
| random_forest | test_2024 (exploratory) | 2024 | 80 | -0.156 | 0.1698 | [-0.360, 0.064] |
| random_forest | test_2025 (exploratory) | 2025 | 80 | -0.161 | 0.1556 | [-0.375, 0.069] |
| ridge | test_2023 (exploratory) | 2023 | 80 | -0.025 | 0.8291 | [-0.250, 0.207] |
| ridge | test_2024 (exploratory) | 2024 | 80 | 0.232 | 0.0353 | [0.007, 0.444] |
| ridge | test_2025 (exploratory) | 2025 | 80 | 0.080 | 0.4772 | [-0.151, 0.306] |
| robust_rank_aggregation | test_2023 (exploratory) | 2023 | 80 | 0.088 | 0.4389 | [-0.133, 0.292] |
| robust_rank_aggregation | test_2024 (exploratory) | 2024 | 80 | 0.195 | 0.0809 | [-0.020, 0.391] |
| robust_rank_aggregation | test_2025 (exploratory) | 2025 | 80 | 0.100 | 0.3804 | [-0.133, 0.328] |

## Required limitations

- Only three test years with 80 evaluated tickers per model and split; estimates remain noisy.
- The cohort is a retrospectively fixed repository universe, not verified point-in-time BIST100 membership.
- Prediction artifact byte reproducibility is environment-qualified; manifests separate same-environment byte identity from cross-environment semantic checks.
- USD-basis returns use Yahoo year-end TRY-per-USD closes as a descriptive currency basis; they do not establish implementability or investment value.
- Research support only; not investment advice.

The absence of a detectable signal in this small, fixed cohort and single regime does not establish that other markets or better point-in-time datasets are unpredictable.
