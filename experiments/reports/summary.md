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
| test_2023 | lasso                 | ml       | 137.78 | 197.12 |      0.191 |              0.2 |                   82.19 |                  44.38 |              0.6  |
| test_2023 | linear_regression     | ml       | 145.22 | 205.73 |      0.173 |              0.2 |                   61.71 |                  44.38 |              0.6  |
| test_2023 | ridge                 | ml       | 127.29 | 173.09 |      0.154 |              0.2 |                   61.71 |                  44.38 |              0.65 |
| test_2023 | elasticnet            | ml       | 126.04 | 162.83 |      0.125 |              0.2 |                   61.71 |                  44.38 |              0.6  |
| test_2023 | random_forest         | ml       | 140.11 | 195.34 |     -0.095 |              0   |                   14.63 |                  44.38 |              0.6  |
| test_2023 | baseline_equal_weight | baseline |  82.62 | 132.23 |     -0.219 |              0   |                   16.08 |                  44.38 |              0.35 |
| test_2023 | baseline_rank_score   | baseline |  82.62 | 132.23 |     -0.219 |              0   |                   16.08 |                  44.38 |              0.35 |

## test_2024

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2024 | baseline_equal_weight | baseline |  45.97 |  57.01 |      0.146 |              0   |                   33.95 |                   35.4 |              0.5  |
| test_2024 | baseline_rank_score   | baseline |  45.97 |  57.01 |      0.146 |              0   |                   33.95 |                   35.4 |              0.5  |
| test_2024 | lasso                 | ml       | 100.67 | 129.63 |     -0.016 |              0.2 |                   20.86 |                   35.4 |              0.55 |
| test_2024 | ridge                 | ml       |  96.67 | 122.37 |     -0.033 |              0.2 |                   20.86 |                   35.4 |              0.5  |
| test_2024 | linear_regression     | ml       | 103.12 | 133.6  |     -0.071 |              0   |                   13.36 |                   35.4 |              0.55 |
| test_2024 | elasticnet            | ml       |  94.61 | 117.31 |     -0.078 |              0.2 |                   26.22 |                   35.4 |              0.5  |
| test_2024 | random_forest         | ml       | 100.82 | 137.82 |     -0.357 |              0   |                  -15.24 |                   35.4 |              0.35 |

## test_2025

| split     | model                 | kind     |    mae |   rmse |   spearman |   precision_at_5 |   top_bucket_avg_return |   median_actual_return |   directional_acc |
|:----------|:----------------------|:---------|-------:|-------:|-----------:|-----------------:|------------------------:|-----------------------:|------------------:|
| test_2025 | baseline_equal_weight | baseline |  35.19 |  75.77 |      0.104 |              0.2 |                   48.36 |                   1.64 |              0.55 |
| test_2025 | baseline_rank_score   | baseline |  35.19 |  75.77 |      0.104 |              0.2 |                   48.36 |                   1.64 |              0.55 |
| test_2025 | linear_regression     | ml       | 112.23 | 142.74 |      0.067 |              0   |                   12.18 |                   1.64 |              0.5  |
| test_2025 | ridge                 | ml       | 108.61 | 120.18 |     -0.023 |              0   |                    9.12 |                   1.64 |              0.45 |
| test_2025 | lasso                 | ml       | 114.26 | 130.12 |     -0.025 |              0   |                   12.18 |                   1.64 |              0.55 |
| test_2025 | elasticnet            | ml       | 104.13 | 112.45 |     -0.053 |              0   |                    8.39 |                   1.64 |              0.45 |
| test_2025 | random_forest         | ml       | 108.88 | 130.76 |     -0.191 |              0.4 |                   98.77 |                   1.64 |              0.4  |
