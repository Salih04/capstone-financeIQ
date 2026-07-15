# Serving-heuristic walk-forward evaluation (R3-SERV-01)

**Conclusion:** The user-facing serving heuristic's walk-forward IC is 0.050 (95% CI [-0.075,0.174], permutation p=0.4427); this is not distinguishable from the within-year null, and in either case does not establish investment value, implementability, or a reliable predictive edge.

**Test framing:** single prespecified test, outside the six-model Bonferroni family.

## Real service path invoked

- `backend/app/services/forecasting_csv_service.py::train_parameters`
- `backend/app/services/forecasting_csv_service.py::run_forecast`

The unchanged backend service is loaded against an isolated temporary data root through the documented RESEARCH_REPO_ROOT override.
No heuristic or scoring formula is copied into the experiment harness, and realized test outcomes are joined only after scoring.

## Walk-forward design and cohort

| Split | Training feature years | Training target years | Test feature year | Target year | Training n | Panel n | Eligible n | Missing-outcome exclusions |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| test_2023 | 2020, 2021 | 2021, 2022 | 2022 | 2023 | 81 | 81 | 80 | RGYAS |
| test_2024 | 2020, 2021, 2022 | 2021, 2022, 2023 | 2023 | 2024 | 161 | 81 | 80 | RGYAS |
| test_2025 | 2020, 2021, 2022, 2023 | 2021, 2022, 2023, 2024 | 2024 | 2025 | 241 | 80 | 80 | none |

Missing features remain null and follow run_forecast omission/confidence behavior; missing outcomes are excluded before within-year service percentiles are computed.

Within each target year, the service score is compared with realized nominal-TRY T+1 outcomes using Spearman IC. The pooled statistic gives each year equal weight.

## Serving result

- Pooled IC: **0.050**
- Bootstrap 95% CI: **[-0.075, 0.174]**
- Raw two-sided within-year permutation p-value: **0.4427**
- Treatment: 10,000 permutations and 10,000 bootstraps, seed 42

This raw p-value is not family-corrected and must not be presented as such.

### Exploratory per-year IC

| Split | Target year | n | IC | Raw permutation p | Bootstrap 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| test_2023 | 2023 | 80 | 0.103 | 0.3570 | [-0.097, 0.306] |
| test_2024 | 2024 | 80 | -0.021 | 0.8579 | [-0.233, 0.198] |
| test_2025 | 2025 | 80 | 0.068 | 0.5510 | [-0.167, 0.291] |

## Separate six-model ML family context

Separate canonical ml family context; the serving heuristic is not a seventh model.

| Canonical ML model | Pooled IC | Raw p | Bonferroni p | FWER significant |
| --- | ---: | ---: | ---: | --- |
| linear_regression | 0.046 | 0.4803 | 1.0000 | no |
| ridge | 0.093 | 0.1570 | 0.9419 | no |
| lasso | 0.090 | 0.1700 | 1.0000 | no |
| elasticnet | -0.020 | 0.7540 | 1.0000 | no |
| random_forest | -0.153 | 0.0183 | 0.1098 | no |
| gradient_boosting | -0.105 | 0.1044 | 0.6263 | no |

No ML model is statistically distinguishable from the within-year null after Bonferroni correction; the data do not support a reliable predictive edge.

## Source provenance

| Source | SHA-256 | Role |
| --- | --- | --- |
| `backend/app/services/forecasting_csv_service.py` | `7438ab40a47b5a1122ec8079d977bde7b7482a31f90dee0de79fd0f5f0212cb1` | authoritative serving implementation invoked read-only |
| `experiments/serving_eval.py` | `6f8a1c47b2357e91ecaae56758f5d570229a70bcc5e1e7f50b4204ca56918922` | R3-SERV-01 isolated evaluation harness |
| `experiments/run_experiments.py` | `265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543` | canonical split definitions |
| `experiments/significance.py` | `5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6` | canonical Spearman and resampling treatment |
| `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78` | raw feature-year and prior-outcome input |
| `experiments/leaderboard.csv` | `8b3dfce2ca9ee702411c76cfcf699723cfde076df073837b4ca9db74e5936822` | protected canonical leaderboard |
| `experiments/results/significance_report.json` | `0358ed01b70b99d491f3babb4810604c09e64ef4726f12ee0b7ea0a8af12fc29` | separate six-model family context |
| `experiments/results/runs/20260712T222717.997241Z_97e4fc33/manifest.json` | `fbeb253dfdc29a64f34b9a9724531fcd149c094bd79cd818a56f9568b317165f` | current clean reproducibility manifest of record |
| `experiments/results/predictions_test_2023.csv` | `c954822ec52c4bdc7704cc0c7d9ac26c58817b2a75ec92c842915603eb5b72c8` | canonical evaluated cohort and outcome reference for 2023 |
| `experiments/results/predictions_test_2024.csv` | `cf88016a3f310811baaf3fed677230ffd98db4db0ea1417393c9afe87bb4c457` | canonical evaluated cohort and outcome reference for 2024 |
| `experiments/results/predictions_test_2025.csv` | `295dac3a1b056aa20b9320ff0844ec3cd6aca61fd602f195258a4bc7182cafb1` | canonical evaluated cohort and outcome reference for 2025 |

## Limitations and claim boundary

- Only three target years are observed, with 80 eligible tickers per year; estimates remain low-power and noisy.
- The cohort is retrospectively fixed and is not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain.
- Missing feature values remain null and reduce service coverage; no value is fabricated or imputed by this harness.
- Rows without realized outcomes are excluded and reported; the result does not generalize to those missing observations.
- Outcomes are nominal TRY returns from one unusual macro regime; regime robustness and economic implementation are not established.
- Exact artifact reproduction is numerical-environment-qualified even though seeded same-environment reruns are byte-deterministic.
- The raw serving p-value belongs to one prespecified test outside the six-model Bonferroni family and is not family-corrected.
- Research support only; not investment advice.

One prespecified retrospective serving-path test cannot establish investment value, implementability, or a reliable predictive edge.

## Artifact ownership and review

Owner/regeneration command: `make research-serving-eval`. Generated files must not be hand-edited.

Independent review: **PENDING**. Handoff: `docs/R3_SERV_01_FABLE5_REVIEW_HANDOFF.md`. This task is not merge-ready until that separate review is performed.
