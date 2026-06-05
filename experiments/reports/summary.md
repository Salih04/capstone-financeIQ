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
| test_2023 | lasso                 | ml       | 138.12 | 192.84 |      0.131 |              0.2 |                   82.19 |                  44.38 |              0.65 |
| test_2023 | ridge                 | ml       | 131.03 | 172.35 |      0.119 |              0.2 |                   82.19 |                  44.38 |              0.65 |
| test_2023 | linear_regression     | ml       | 141    | 197.65 |      0.09  |              0   |                   14.63 |                  44.38 |              0.6  |
| test_2023 | elasticnet            | ml       | 128.07 | 162.29 |      0.053 |              0.2 |                   61.71 |                  44.38 |              0.6  |
| test_2023 | random_forest         | ml       | 140.91 | 194.8  |     -0.097 |              0   |                   24.25 |                  44.38 |              0.65 |
| test_2023 | baseline_equal_weight | baseline |  82.62 | 132.23 |     -0.2   |              0   |                   16.08 |                  44.38 |              0.4  |
| test_2023 | baseline_rank_score   | baseline |  82.62 | 132.23 |     -0.2   |              0   |                   16.08 |                  44.38 |              0.4  |

## test_2024

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2024 | baseline_equal_weight | baseline |  45.96 |  57    |      0.16  |              0   |                   46.89 |                   35.4 |              0.55 |
| test_2024 | baseline_rank_score   | baseline |  45.96 |  57    |      0.16  |              0   |                   46.89 |                   35.4 |              0.55 |
| test_2024 | ridge                 | ml       |  96.45 | 121.69 |     -0.074 |              0   |                   -8.9  |                   35.4 |              0.5  |
| test_2024 | lasso                 | ml       | 101.26 | 127.33 |     -0.086 |              0.2 |                    7.31 |                   35.4 |              0.55 |
| test_2024 | elasticnet            | ml       |  95.26 | 116.94 |     -0.132 |              0.2 |                   12.67 |                   35.4 |              0.5  |
| test_2024 | linear_regression     | ml       | 103.69 | 130.56 |     -0.15  |              0.2 |                    7.31 |                   35.4 |              0.5  |
| test_2024 | random_forest         | ml       |  97.99 | 129.82 |     -0.382 |              0   |                  -15.24 |                   35.4 |              0.35 |

## test_2025

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2025 | baseline_equal_weight | baseline |  35.19 |  75.77 |      0.088 |              0.2 |                   48.36 |                   1.64 |              0.55 |
| test_2025 | baseline_rank_score   | baseline |  35.19 |  75.77 |      0.088 |              0.2 |                   48.36 |                   1.64 |              0.55 |
| test_2025 | linear_regression     | ml       | 121.22 | 142.3  |      0.08  |              0.2 |                   28.82 |                   1.64 |              0.4  |
| test_2025 | random_forest         | ml       | 110.48 | 132.83 |     -0.001 |              0.4 |                   98.77 |                   1.64 |              0.5  |
| test_2025 | ridge                 | ml       | 105.05 | 119.51 |     -0.016 |              0   |                   12.85 |                   1.64 |              0.4  |
| test_2025 | elasticnet            | ml       | 102.67 | 111.85 |     -0.038 |              0.2 |                   43.83 |                   1.64 |              0.45 |
| test_2025 | lasso                 | ml       | 113.58 | 128.69 |     -0.042 |              0.2 |                   28.82 |                   1.64 |              0.4  |
