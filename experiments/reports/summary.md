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
| test_2023 | elasticnet            | ml       | 122.76 | 153.15 |      0.055 |              0.2 |                   74.23 |                  44.38 |              0.55 |
| test_2023 | ridge                 | ml       | 124.25 | 157.7  |      0.028 |              0.2 |                   74.23 |                  44.38 |              0.55 |
| test_2023 | lasso                 | ml       | 127.38 | 166.41 |     -0.009 |              0.2 |                   74.23 |                  44.38 |              0.6  |
| test_2023 | linear_regression     | ml       | 129.1  | 168.14 |     -0.013 |              0.2 |                   74.23 |                  44.38 |              0.55 |
| test_2023 | baseline_equal_weight | baseline |  82.62 | 132.23 |     -0.192 |              0   |                   18.13 |                  44.38 |              0.45 |
| test_2023 | baseline_rank_score   | baseline |  82.62 | 132.23 |     -0.192 |              0   |                   18.13 |                  44.38 |              0.45 |
| test_2023 | random_forest         | ml       | 140.41 | 197.73 |     -0.247 |              0   |                  -10.32 |                  44.38 |              0.5  |

## test_2024

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2024 | baseline_equal_weight | baseline |  45.97 |  57.01 |      0.163 |              0   |                   36.87 |                   35.4 |              0.55 |
| test_2024 | baseline_rank_score   | baseline |  45.97 |  57.01 |      0.163 |              0   |                   36.87 |                   35.4 |              0.55 |
| test_2024 | ridge                 | ml       |  95.89 | 117.64 |     -0.202 |              0.2 |                   22.3  |                   35.4 |              0.45 |
| test_2024 | elasticnet            | ml       |  94.87 | 113.9  |     -0.216 |              0.2 |                   22.3  |                   35.4 |              0.45 |
| test_2024 | lasso                 | ml       |  99.96 | 122.92 |     -0.231 |              0.2 |                   22.3  |                   35.4 |              0.4  |
| test_2024 | linear_regression     | ml       | 102.21 | 125.11 |     -0.241 |              0.2 |                   22.3  |                   35.4 |              0.45 |
| test_2024 | random_forest         | ml       |  97.11 | 138.71 |     -0.462 |              0   |                   -7.67 |                   35.4 |              0.35 |

## test_2025

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2025 | linear_regression     | ml       | 110.28 | 130.35 |      0.215 |              0.2 |                   25.01 |                   1.64 |              0.45 |
| test_2025 | elasticnet            | ml       | 105.75 | 112.25 |      0.13  |              0   |                    9.96 |                   1.64 |              0.5  |
| test_2025 | random_forest         | ml       | 104.59 | 114.13 |      0.094 |              0.6 |                  124.91 |                   1.64 |              0.5  |
| test_2025 | lasso                 | ml       | 111.04 | 121.19 |      0.057 |              0.2 |                   25.32 |                   1.64 |              0.4  |
| test_2025 | ridge                 | ml       | 108.17 | 117.46 |      0.039 |              0.2 |                   25.32 |                   1.64 |              0.45 |
| test_2025 | baseline_equal_weight | baseline |  35.2  |  75.77 |      0.037 |              0   |                    1.33 |                   1.64 |              0.55 |
| test_2025 | baseline_rank_score   | baseline |  35.2  |  75.77 |      0.037 |              0   |                    1.33 |                   1.64 |              0.55 |
