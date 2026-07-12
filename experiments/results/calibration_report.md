# Confidence calibration report (R2-CAL-01)

**Verdict:** Hybrid confidence is not informative about rank error at this scale: the replayed value is constant across all evaluated rows, so calibration and monotonicity are not estimable.

Diagnostic only: confidence is not a probability of return, profit, or success; it is not recommendation strength and does not establish validated predictive reliability.

## Audited quantity

The audited value is the hybrid research score's 0.20 `confidence_score` component from `research_agent.confidence_score`, consumed by `generate_company_insight`. It is a dataset-artifact-state diagnostic, not a ticker-specific coverage estimate. The separate forecasting-service confidence is selected-feature coverage and was not substituted for the hybrid component.

Replayed value: **0.250 (low)** for every evaluated row. Reasons: small_sample (-0.25), no_manual_valuation_profitability_features (-0.20), weak_backtest_spearman_near_zero (-0.20), frozen_columns_present (-0.10).

## Design and sample

The bench read the three persisted prediction dumps without retraining: 2160 model rows, 240 distinct ticker-year outcomes, 9 models, target years 2023, 2024, 2025. Scope: 81-ticker training universe; 80 evaluated rows per split; nominal TRY realized returns.

For every model and target year, descending model-native `y_pred` becomes predicted rank and descending persisted `y_true` becomes realized rank. Absolute rank error is their distance. Raw score magnitudes stay model-local because their scales differ. Realized returns are evaluation outcomes only. Feature coverage is computed separately on the corresponding feature-year row and is never filled when an input row is absent.

## Calibration finding

Ten bins were requested; **1** was realizable because confidence had **1** distinct value. The higher-confidence/lower-error association and its seeded bootstrap interval are therefore not estimable. This is evidence about the current confidence semantics, not evidence that rank errors are small.

Coverage remained a separate observed diagnostic across 240 ticker-years (min/median/max 0.375/0.662/1.000); 0 input rows were missing. Coverage variation must not be relabeled as hybrid confidence after the fact.

## Plot-ready bin

| calibration_status   |   confidence_bin |   confidence_min |   confidence_max |   mean_confidence |   n_model_rows |   n_ticker_years |   mean_rank_error |   median_rank_error |   mean_feature_coverage |
|:---------------------|-----------------:|-----------------:|-----------------:|------------------:|---------------:|-----------------:|------------------:|--------------------:|------------------------:|
| not_estimable        |                1 |             0.25 |             0.25 |              0.25 |           2160 |              240 |           26.0796 |                  23 |                0.772708 |

## Model-native score scales and rank error

| model                   |   model_rows | target_years       |   score_magnitude_model_native_min |   score_magnitude_model_native_max |   mean_absolute_rank_error |   median_absolute_rank_error |
|:------------------------|-------------:|:-------------------|-----------------------------------:|-----------------------------------:|---------------------------:|-----------------------------:|
| baseline_equal_weight   |          240 | [2023, 2024, 2025] |                           0.173638 |                           0.809202 |                    24.8833 |                         22.5 |
| baseline_rank_score     |          240 | [2023, 2024, 2025] |                           0.173638 |                           0.809202 |                    24.8833 |                         22.5 |
| elasticnet              |          240 | [2023, 2024, 2025] |                          -0.747669 |                         365.941    |                    26.9167 |                         24   |
| gradient_boosting       |          240 | [2023, 2024, 2025] |                          26.1811   |                         681.891    |                    28.1833 |                         24   |
| lasso                   |          240 | [2023, 2024, 2025] |                        -171.874    |                         603.832    |                    24.9583 |                         22   |
| linear_regression       |          240 | [2023, 2024, 2025] |                        -186.856    |                         629.123    |                    25.7    |                         22   |
| random_forest           |          240 | [2023, 2024, 2025] |                          37.1191   |                         635.838    |                    29.0417 |                         27   |
| ridge                   |          240 | [2023, 2024, 2025] |                        -101.715    |                         416.436    |                    25.1    |                         22   |
| robust_rank_aggregation |          240 | [2023, 2024, 2025] |                           0.078924 |                           0.930032 |                    25.05   |                         22   |

## Provenance and limitations

Audited as of replay 2026-07-12 at git SHA `a95e1e1c92fe6ffbe3e1660f7caf66b2a110401c`. The report records service-code and input checksums in the JSON artifact. Replayed confidence describes that code on past rows; it is not a historically persisted observation.

- The replay describes the current checked-out confidence code applied to persisted historical outcomes; it is not historically persisted confidence.
- The hybrid confidence component is dataset-state scoped and constant across tickers, so decile calibration cannot be estimated.
- The 2,160 model rows repeat 240 ticker-year realized outcomes across nine models and are not 2,160 independent observations.
- Only three test years and one macro regime are observed; no reliable predictive edge is established.
- No confidence tuning or recalibration was performed on these rows.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
