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
| test_2023 | baseline_equal_weight | baseline |  82.63 | 132.21 |      0.031 |              0   |                   -0.98 |                  44.38 |              0.55 |
| test_2023 | baseline_rank_score   | baseline |  82.63 | 132.21 |      0.031 |              0   |                   -0.98 |                  44.38 |              0.55 |
| test_2023 | ridge                 | ml       | 135.87 | 178.12 |     -0.203 |              0   |                  -15.68 |                  44.38 |              0.55 |
| test_2023 | elasticnet            | ml       | 129.58 | 168.36 |     -0.207 |              0.2 |                   36.76 |                  44.38 |              0.45 |
| test_2023 | random_forest         | ml       | 139.67 | 197.23 |     -0.223 |              0   |                  -10.32 |                  44.38 |              0.55 |
| test_2023 | lasso                 | ml       | 143.8  | 192.7  |     -0.236 |              0   |                   -0.95 |                  44.38 |              0.45 |
| test_2023 | linear_regression     | ml       | 145.34 | 196    |     -0.295 |              0   |                   13.82 |                  44.38 |              0.4  |

## test_2024

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2024 | baseline_equal_weight | baseline |  45.94 |  56.99 |      0.414 |              0.2 |                   62.42 |                   35.4 |              0.6  |
| test_2024 | baseline_rank_score   | baseline |  45.94 |  56.99 |      0.414 |              0.2 |                   62.42 |                   35.4 |              0.6  |
| test_2024 | lasso                 | ml       | 100.55 | 134.84 |     -0.324 |              0   |                   -8.9  |                   35.4 |              0.45 |
| test_2024 | ridge                 | ml       |  96.81 | 128.38 |     -0.331 |              0   |                   -8.9  |                   35.4 |              0.4  |
| test_2024 | elasticnet            | ml       |  94.47 | 119.79 |     -0.342 |              0   |                   -8.9  |                   35.4 |              0.4  |
| test_2024 | linear_regression     | ml       | 101.67 | 136.77 |     -0.349 |              0   |                   -5.02 |                   35.4 |              0.45 |
| test_2024 | random_forest         | ml       |  98.09 | 138.9  |     -0.418 |              0   |                  -24    |                   35.4 |              0.4  |

## test_2025

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2025 | baseline_equal_weight | baseline |  35.18 |  75.75 |      0.379 |              0.2 |                   61.98 |                   1.64 |              0.6  |
| test_2025 | baseline_rank_score   | baseline |  35.18 |  75.75 |      0.379 |              0.2 |                   61.98 |                   1.64 |              0.6  |
| test_2025 | random_forest         | ml       | 102.11 | 117.28 |      0.077 |              0.2 |                   22.88 |                   1.64 |              0.45 |
| test_2025 | elasticnet            | ml       | 102.3  | 112.52 |     -0.209 |              0   |                  -16.3  |                   1.64 |              0.45 |
| test_2025 | linear_regression     | ml       | 116.24 | 135.41 |     -0.302 |              0   |                   -9.13 |                   1.64 |              0.4  |
| test_2025 | ridge                 | ml       | 103.75 | 118.74 |     -0.322 |              0   |                  -14.17 |                   1.64 |              0.4  |
| test_2025 | lasso                 | ml       | 104.9  | 122.77 |     -0.353 |              0   |                  -14.17 |                   1.64 |              0.4  |
