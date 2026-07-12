# Friction sensitivity report (R2-FRICTION-01)

> **Hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0 and no model survives significance correction.**

**Evaluated cohort:** 81-ticker training universe, nominal TRY.

This is descriptive sensitivity analysis over persisted historical evaluation rows. It does not establish execution quality, realizable performance, investment value, or advice.

## Design and assumptions

Each model and target year forms an equal-weight top-10 basket from descending within-model, within-year `y_pred` ranks. Raw prediction magnitudes are neither compared across models nor emitted. Ties are resolved by ticker ascending. Realized `y_true` is used only after basket formation to calculate the basket's nominal TRY mean.

Turnover is half the L1 distance between consecutive annual equal-weight baskets. Assumed cost drag in percentage points is `turnover × cost_bps / 100`; net is gross minus that drag. There is no predecessor for 2023, so nonzero-cost drag and net remain null there. The zero-cost control equals gross.

| Scenario | Assumed bps | Role |
|---|---:|---|
| zero_cost_control | 0.0 | zero-cost arithmetic control |
| illustrative_25bps_assumption | 25.0 | illustrative assumption |
| illustrative_100bps_assumption | 100.0 | illustrative assumption |
| deliberately_adverse_10000bps_control | 10000.0 | deliberately adverse arithmetic stress control |

The two middle values are illustrative assumptions. The 10,000 bps value is deliberately extreme and exists only to negative-control the arithmetic. None is a measured BIST spread, impact, liquidity, or tradeability estimate.

## Per-year gross and assumed-cost net basket means

Every gross figure stays paired with its net counterpart under the report stamp above.

| Model | Year | Scenario | Gross nominal TRY % | Turnover | Cost drag pp | Net nominal TRY % |
|---|---:|---|---:|---:|---:|---:|
| baseline_equal_weight | 2023 | zero_cost_control | 44.003 | null | 0.000 | 44.003 |
| baseline_equal_weight | 2023 | illustrative_25bps_assumption | 44.003 | null | null | null |
| baseline_equal_weight | 2023 | illustrative_100bps_assumption | 44.003 | null | null | null |
| baseline_equal_weight | 2023 | deliberately_adverse_10000bps_control | 44.003 | null | null | null |
| baseline_equal_weight | 2024 | zero_cost_control | 51.130 | 0.400 | 0.000 | 51.130 |
| baseline_equal_weight | 2024 | illustrative_25bps_assumption | 51.130 | 0.400 | 0.100 | 51.030 |
| baseline_equal_weight | 2024 | illustrative_100bps_assumption | 51.130 | 0.400 | 0.400 | 50.730 |
| baseline_equal_weight | 2024 | deliberately_adverse_10000bps_control | 51.130 | 0.400 | 40.000 | 11.130 |
| baseline_equal_weight | 2025 | zero_cost_control | 28.283 | 0.500 | 0.000 | 28.283 |
| baseline_equal_weight | 2025 | illustrative_25bps_assumption | 28.283 | 0.500 | 0.125 | 28.158 |
| baseline_equal_weight | 2025 | illustrative_100bps_assumption | 28.283 | 0.500 | 0.500 | 27.783 |
| baseline_equal_weight | 2025 | deliberately_adverse_10000bps_control | 28.283 | 0.500 | 50.000 | -21.717 |
| baseline_rank_score | 2023 | zero_cost_control | 44.003 | null | 0.000 | 44.003 |
| baseline_rank_score | 2023 | illustrative_25bps_assumption | 44.003 | null | null | null |
| baseline_rank_score | 2023 | illustrative_100bps_assumption | 44.003 | null | null | null |
| baseline_rank_score | 2023 | deliberately_adverse_10000bps_control | 44.003 | null | null | null |
| baseline_rank_score | 2024 | zero_cost_control | 51.130 | 0.400 | 0.000 | 51.130 |
| baseline_rank_score | 2024 | illustrative_25bps_assumption | 51.130 | 0.400 | 0.100 | 51.030 |
| baseline_rank_score | 2024 | illustrative_100bps_assumption | 51.130 | 0.400 | 0.400 | 50.730 |
| baseline_rank_score | 2024 | deliberately_adverse_10000bps_control | 51.130 | 0.400 | 40.000 | 11.130 |
| baseline_rank_score | 2025 | zero_cost_control | 28.283 | 0.500 | 0.000 | 28.283 |
| baseline_rank_score | 2025 | illustrative_25bps_assumption | 28.283 | 0.500 | 0.125 | 28.158 |
| baseline_rank_score | 2025 | illustrative_100bps_assumption | 28.283 | 0.500 | 0.500 | 27.783 |
| baseline_rank_score | 2025 | deliberately_adverse_10000bps_control | 28.283 | 0.500 | 50.000 | -21.717 |
| elasticnet | 2023 | zero_cost_control | 59.245 | null | 0.000 | 59.245 |
| elasticnet | 2023 | illustrative_25bps_assumption | 59.245 | null | null | null |
| elasticnet | 2023 | illustrative_100bps_assumption | 59.245 | null | null | null |
| elasticnet | 2023 | deliberately_adverse_10000bps_control | 59.245 | null | null | null |
| elasticnet | 2024 | zero_cost_control | 19.386 | 0.400 | 0.000 | 19.386 |
| elasticnet | 2024 | illustrative_25bps_assumption | 19.386 | 0.400 | 0.100 | 19.286 |
| elasticnet | 2024 | illustrative_100bps_assumption | 19.386 | 0.400 | 0.400 | 18.986 |
| elasticnet | 2024 | deliberately_adverse_10000bps_control | 19.386 | 0.400 | 40.000 | -20.614 |
| elasticnet | 2025 | zero_cost_control | 33.790 | 0.500 | 0.000 | 33.790 |
| elasticnet | 2025 | illustrative_25bps_assumption | 33.790 | 0.500 | 0.125 | 33.665 |
| elasticnet | 2025 | illustrative_100bps_assumption | 33.790 | 0.500 | 0.500 | 33.290 |
| elasticnet | 2025 | deliberately_adverse_10000bps_control | 33.790 | 0.500 | 50.000 | -16.210 |
| gradient_boosting | 2023 | zero_cost_control | 51.228 | null | 0.000 | 51.228 |
| gradient_boosting | 2023 | illustrative_25bps_assumption | 51.228 | null | null | null |
| gradient_boosting | 2023 | illustrative_100bps_assumption | 51.228 | null | null | null |
| gradient_boosting | 2023 | deliberately_adverse_10000bps_control | 51.228 | null | null | null |
| gradient_boosting | 2024 | zero_cost_control | 12.933 | 0.400 | 0.000 | 12.933 |
| gradient_boosting | 2024 | illustrative_25bps_assumption | 12.933 | 0.400 | 0.100 | 12.833 |
| gradient_boosting | 2024 | illustrative_100bps_assumption | 12.933 | 0.400 | 0.400 | 12.533 |
| gradient_boosting | 2024 | deliberately_adverse_10000bps_control | 12.933 | 0.400 | 40.000 | -27.067 |
| gradient_boosting | 2025 | zero_cost_control | 11.981 | 0.700 | 0.000 | 11.981 |
| gradient_boosting | 2025 | illustrative_25bps_assumption | 11.981 | 0.700 | 0.175 | 11.806 |
| gradient_boosting | 2025 | illustrative_100bps_assumption | 11.981 | 0.700 | 0.700 | 11.281 |
| gradient_boosting | 2025 | deliberately_adverse_10000bps_control | 11.981 | 0.700 | 70.000 | -58.019 |
| lasso | 2023 | zero_cost_control | 42.850 | null | 0.000 | 42.850 |
| lasso | 2023 | illustrative_25bps_assumption | 42.850 | null | null | null |
| lasso | 2023 | illustrative_100bps_assumption | 42.850 | null | null | null |
| lasso | 2023 | deliberately_adverse_10000bps_control | 42.850 | null | null | null |
| lasso | 2024 | zero_cost_control | 17.177 | 0.500 | 0.000 | 17.177 |
| lasso | 2024 | illustrative_25bps_assumption | 17.177 | 0.500 | 0.125 | 17.052 |
| lasso | 2024 | illustrative_100bps_assumption | 17.177 | 0.500 | 0.500 | 16.677 |
| lasso | 2024 | deliberately_adverse_10000bps_control | 17.177 | 0.500 | 50.000 | -32.823 |
| lasso | 2025 | zero_cost_control | 54.605 | 0.900 | 0.000 | 54.605 |
| lasso | 2025 | illustrative_25bps_assumption | 54.605 | 0.900 | 0.225 | 54.380 |
| lasso | 2025 | illustrative_100bps_assumption | 54.605 | 0.900 | 0.900 | 53.705 |
| lasso | 2025 | deliberately_adverse_10000bps_control | 54.605 | 0.900 | 90.000 | -35.395 |
| linear_regression | 2023 | zero_cost_control | 49.359 | null | 0.000 | 49.359 |
| linear_regression | 2023 | illustrative_25bps_assumption | 49.359 | null | null | null |
| linear_regression | 2023 | illustrative_100bps_assumption | 49.359 | null | null | null |
| linear_regression | 2023 | deliberately_adverse_10000bps_control | 49.359 | null | null | null |
| linear_regression | 2024 | zero_cost_control | 15.982 | 0.300 | 0.000 | 15.982 |
| linear_regression | 2024 | illustrative_25bps_assumption | 15.982 | 0.300 | 0.075 | 15.907 |
| linear_regression | 2024 | illustrative_100bps_assumption | 15.982 | 0.300 | 0.300 | 15.682 |
| linear_regression | 2024 | deliberately_adverse_10000bps_control | 15.982 | 0.300 | 30.000 | -14.018 |
| linear_regression | 2025 | zero_cost_control | 12.287 | 0.800 | 0.000 | 12.287 |
| linear_regression | 2025 | illustrative_25bps_assumption | 12.287 | 0.800 | 0.200 | 12.087 |
| linear_regression | 2025 | illustrative_100bps_assumption | 12.287 | 0.800 | 0.800 | 11.487 |
| linear_regression | 2025 | deliberately_adverse_10000bps_control | 12.287 | 0.800 | 80.000 | -67.713 |
| random_forest | 2023 | zero_cost_control | 7.499 | null | 0.000 | 7.499 |
| random_forest | 2023 | illustrative_25bps_assumption | 7.499 | null | null | null |
| random_forest | 2023 | illustrative_100bps_assumption | 7.499 | null | null | null |
| random_forest | 2023 | deliberately_adverse_10000bps_control | 7.499 | null | null | null |
| random_forest | 2024 | zero_cost_control | 13.096 | 0.500 | 0.000 | 13.096 |
| random_forest | 2024 | illustrative_25bps_assumption | 13.096 | 0.500 | 0.125 | 12.971 |
| random_forest | 2024 | illustrative_100bps_assumption | 13.096 | 0.500 | 0.500 | 12.596 |
| random_forest | 2024 | deliberately_adverse_10000bps_control | 13.096 | 0.500 | 50.000 | -36.904 |
| random_forest | 2025 | zero_cost_control | 15.652 | 0.800 | 0.000 | 15.652 |
| random_forest | 2025 | illustrative_25bps_assumption | 15.652 | 0.800 | 0.200 | 15.452 |
| random_forest | 2025 | illustrative_100bps_assumption | 15.652 | 0.800 | 0.800 | 14.852 |
| random_forest | 2025 | deliberately_adverse_10000bps_control | 15.652 | 0.800 | 80.000 | -64.348 |
| ridge | 2023 | zero_cost_control | 38.103 | null | 0.000 | 38.103 |
| ridge | 2023 | illustrative_25bps_assumption | 38.103 | null | null | null |
| ridge | 2023 | illustrative_100bps_assumption | 38.103 | null | null | null |
| ridge | 2023 | deliberately_adverse_10000bps_control | 38.103 | null | null | null |
| ridge | 2024 | zero_cost_control | 27.466 | 0.600 | 0.000 | 27.466 |
| ridge | 2024 | illustrative_25bps_assumption | 27.466 | 0.600 | 0.150 | 27.316 |
| ridge | 2024 | illustrative_100bps_assumption | 27.466 | 0.600 | 0.600 | 26.866 |
| ridge | 2024 | deliberately_adverse_10000bps_control | 27.466 | 0.600 | 60.000 | -32.534 |
| ridge | 2025 | zero_cost_control | 21.856 | 0.900 | 0.000 | 21.856 |
| ridge | 2025 | illustrative_25bps_assumption | 21.856 | 0.900 | 0.225 | 21.631 |
| ridge | 2025 | illustrative_100bps_assumption | 21.856 | 0.900 | 0.900 | 20.956 |
| ridge | 2025 | deliberately_adverse_10000bps_control | 21.856 | 0.900 | 90.000 | -68.144 |
| robust_rank_aggregation | 2023 | zero_cost_control | 44.289 | null | 0.000 | 44.289 |
| robust_rank_aggregation | 2023 | illustrative_25bps_assumption | 44.289 | null | null | null |
| robust_rank_aggregation | 2023 | illustrative_100bps_assumption | 44.289 | null | null | null |
| robust_rank_aggregation | 2023 | deliberately_adverse_10000bps_control | 44.289 | null | null | null |
| robust_rank_aggregation | 2024 | zero_cost_control | 53.962 | 0.500 | 0.000 | 53.962 |
| robust_rank_aggregation | 2024 | illustrative_25bps_assumption | 53.962 | 0.500 | 0.125 | 53.837 |
| robust_rank_aggregation | 2024 | illustrative_100bps_assumption | 53.962 | 0.500 | 0.500 | 53.462 |
| robust_rank_aggregation | 2024 | deliberately_adverse_10000bps_control | 53.962 | 0.500 | 50.000 | 3.962 |
| robust_rank_aggregation | 2025 | zero_cost_control | 27.370 | 0.700 | 0.000 | 27.370 |
| robust_rank_aggregation | 2025 | illustrative_25bps_assumption | 27.370 | 0.700 | 0.175 | 27.195 |
| robust_rank_aggregation | 2025 | illustrative_100bps_assumption | 27.370 | 0.700 | 0.700 | 26.670 |
| robust_rank_aggregation | 2025 | deliberately_adverse_10000bps_control | 27.370 | 0.700 | 70.000 | -42.630 |

## Findings

- The zero-cost control reproduces each observed gross basket mean exactly.
- The deliberately adverse arithmetic control produces negative net values in 15 of 18 model-year transitions; this is a stress-control property, not a market-cost estimate.
- No cost scenario changes the existing significance, power, calibration, or model evidence.

## Claim-safety boundaries and limitations

- Cost bps values are explicit assumptions, not measured BIST costs.
- No bid–ask spread, market impact, liquidity, capacity, execution, suspension, or tradeability input is available or inferred.
- The evaluated cohort is the retrospectively fixed 81-ticker training universe with 80 rows per split, not verified point-in-time BIST100 membership; survivorship and universe-selection look-ahead risks remain unresolved.
- Only three test years are observed in one task-defined macro period; the numerical environment qualification remains applicable.
- The analysis uses nominal TRY outcomes only. CPI-deflated TRY and USD-basis evidence remain separate and are not recomputed here.
- Multiplicity and low-power limits remain unchanged; isolated basket outcomes do not establish signal or practical value.
- Missing selected realized outcomes propagate to null gross and net values; missing predictions are excluded from rank eligibility and never filled.
- Research support only; not investment advice.

Nominal TRY is the only basis evaluated in this report. The CPI-deflated TRY and USD-basis significance reports remain parallel evidence and are not substituted or merged. Existing multiplicity, power, survivorship, retrospective-cohort, single-regime, and environment limitations remain in force.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
