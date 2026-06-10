# Experiment summary (next-year return prediction)

Walk-forward, leakage-controlled. Small data (40 stocks/year) — treat
all out-of-sample numbers as noisy and overfitting-prone.

> ⚠️ DATA CAVEAT: the trusted XLSX files share ONE static fundamental
> snapshot (only realized returns vary by year). So the predictor features
> are identical every year and this harness is DEGENERATE on the current
> data — it tests a fixed fundamental ranking against each year's returns,
> not real time-series forecasting. The pipeline is ready for genuinely
> time-varying fundamentals if/when they are provided.

## test_2023

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2023 | ridge                 | ml       | 135.28 | 171.01 |      0.118 |              0.2 |                   82.19 |                  39.52 |             0.592 |
| test_2023 | lasso                 | ml       | 143.17 | 190.88 |      0.112 |              0.2 |                   82.19 |                  39.52 |             0.633 |
| test_2023 | linear_regression     | ml       | 145.88 | 196.03 |      0.061 |              0   |                   14.63 |                  39.52 |             0.551 |
| test_2023 | baseline_equal_weight | baseline |  73.09 | 120.43 |      0.052 |              0   |                   21.63 |                  39.52 |             0.551 |
| test_2023 | baseline_rank_score   | baseline |  73.09 | 120.43 |      0.052 |              0   |                   21.63 |                  39.52 |             0.551 |
| test_2023 | elasticnet            | ml       | 133.5  | 162.97 |      0.031 |              0.2 |                   61.71 |                  39.52 |             0.469 |
| test_2023 | random_forest         | ml       | 138.73 | 185.23 |     -0.098 |              0   |                   14.63 |                  39.52 |             0.551 |

## test_2024

| split     | model                 | kind     |   mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2024 | baseline_equal_weight | baseline | 46.16 |  56.12 |      0.175 |              0   |                   38.93 |                  35.56 |             0.551 |
| test_2024 | baseline_rank_score   | baseline | 46.16 |  56.12 |      0.175 |              0   |                   38.93 |                  35.56 |             0.551 |
| test_2024 | lasso                 | ml       | 90.75 | 114.34 |     -0.002 |              0.2 |                   21.19 |                  35.56 |             0.551 |
| test_2024 | linear_regression     | ml       | 93.19 | 115.93 |     -0.006 |              0.2 |                   21.19 |                  35.56 |             0.551 |
| test_2024 | ridge                 | ml       | 87.89 | 111.76 |     -0.028 |              0   |                    4.97 |                  35.56 |             0.51  |
| test_2024 | elasticnet            | ml       | 87.02 | 108.21 |     -0.125 |              0.2 |                   25.31 |                  35.56 |             0.469 |
| test_2024 | random_forest         | ml       | 87.52 | 122.44 |     -0.41  |              0   |                  -15.24 |                  35.56 |             0.347 |

## test_2025

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2025 | linear_regression     | ml       | 102.58 | 120.45 |      0.133 |              0   |                   16.78 |                   0.35 |             0.429 |
| test_2025 | baseline_equal_weight | baseline |  35.03 |  70.91 |      0.111 |              0.2 |                   41.97 |                   0.35 |             0.592 |
| test_2025 | baseline_rank_score   | baseline |  35.03 |  70.91 |      0.111 |              0.2 |                   41.97 |                   0.35 |             0.592 |
| test_2025 | lasso                 | ml       |  99.11 | 115.09 |     -0.036 |              0   |                   16.78 |                   0.35 |             0.347 |
| test_2025 | ridge                 | ml       |  97.06 | 110.8  |     -0.081 |              0   |                    9.56 |                   0.35 |             0.388 |
| test_2025 | random_forest         | ml       |  97.27 | 112.8  |     -0.089 |              0.2 |                   84.13 |                   0.35 |             0.429 |
| test_2025 | elasticnet            | ml       |  95.38 | 106.61 |     -0.112 |              0.2 |                   43.83 |                   0.35 |             0.429 |
