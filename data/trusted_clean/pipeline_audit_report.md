# FinanceIQ Pipeline Audit

- CSV files: **34**
- Files by class: `{'config': 3, 'trusted_reference': 8, 'clean_generated': 3, 'modeling_ready': 1, 'public_modeling_ready': 1, 'training_modeling_ready': 1, 'raw': 17}`
- Public universe: **40** tickers
- Training universe: **81** tickers
- Training-only: **41** tickers

## Current Quality Summary

- rows: `403`
- n_features: `40`
- rows_with_target: `321`
- inference_only_rows: `82`
- benchmark_available: `True`
- valid_for_T_to_T1_modeling: `True`
- issues: `[]`

## CSV Inventory

| class | path | rows | tickers | years | duplicate ticker-year | avg missing | target fields |
|---|---|---:|---:|---|---:|---:|---|
| config | `data/config/bist100_candidates.csv` | 44 | 44 |  |  | 0.0 | `{}` |
| config | `data/config/universe_public_40.csv` | 40 | 40 |  |  | 0.0 | `{}` |
| config | `data/config/universe_training_bist100.csv` | 81 | 81 |  |  | 0.0 | `{}` |
| trusted_reference | `data/trusted/2020stocks.csv` | 40 | 40 | 2020-2020 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/2021stocks.csv` | 40 | 40 | 2021-2021 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/2022stocks.csv` | 40 | 40 | 2022-2022 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/2023stocks.csv` | 40 | 40 | 2023-2023 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/2024stocks.csv` | 40 | 40 | 2024-2024 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/2025stocks.csv` | 40 | 40 | 2025-2025 | 0 | 0.0 | `{}` |
| trusted_reference | `data/trusted/bist100_benchmark_returns.template.csv` | 0 |  |  |  | 0.0 | `{}` |
| trusted_reference | `data/trusted/stocks_2020_2025.csv` | 240 | 40 | 2020-2025 | 0 | 0.0 | `{}` |
| clean_generated | `data/trusted_clean/bist100_benchmark_returns.template.csv` | 0 |  |  |  | 0.0 | `{}` |
| clean_generated | `data/trusted_clean/company_year_fundamentals.csv` | 240 | 40 | 2020-2025 | 0 | 0.0 | `{}` |
| clean_generated | `data/trusted_clean/company_year_returns.csv` | 240 | 40 | 2020-2025 | 0 | 0.0926 | `{'next_year_return_pct_nonnull': 200, 'next_year_rank_by_return_nonnull': 200, 'next_year_return_percentile_nonnull': 200, 'next_year_top_10pct_returner_nonnull': 200, 'next_year_top_20pct_returner_nonnull': 200}` |
| modeling_ready | `data/trusted_clean/modeling_dataset_2020_2025.csv` | 403 | 81 | 2020-2025 | 0 | 0.1954 | `{'has_target': 321, 'is_inference_row': 82, 'next_year_return_pct_nonnull': 321, 'next_year_rank_by_return_nonnull': 321, 'next_year_return_percentile_nonnull': 321, 'next_year_top_10pct_returner_nonnull': 321, 'next_year_top_20pct_returner_nonnull': 321, 'next_year_bist100_return_pct_nonnull': 200, 'next_year_excess_return_vs_bist100_nonnull': 200, 'next_year_outperform_bist100_nonnull': 200}` |
| public_modeling_ready | `data/trusted_clean/modeling_dataset_public_2020_2025.csv` | 240 | 40 | 2020-2025 | 0 | 0.0654 | `{'has_target': 200, 'is_inference_row': 40, 'next_year_return_pct_nonnull': 200, 'next_year_rank_by_return_nonnull': 200, 'next_year_return_percentile_nonnull': 200, 'next_year_top_10pct_returner_nonnull': 200, 'next_year_top_20pct_returner_nonnull': 200, 'next_year_bist100_return_pct_nonnull': 200, 'next_year_excess_return_vs_bist100_nonnull': 200, 'next_year_outperform_bist100_nonnull': 200}` |
| training_modeling_ready | `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | 403 | 81 | 2020-2025 | 0 | 0.1954 | `{'has_target': 321, 'is_inference_row': 82, 'next_year_return_pct_nonnull': 321, 'next_year_rank_by_return_nonnull': 321, 'next_year_return_percentile_nonnull': 321, 'next_year_top_10pct_returner_nonnull': 321, 'next_year_top_20pct_returner_nonnull': 321, 'next_year_bist100_return_pct_nonnull': 200, 'next_year_excess_return_vs_bist100_nonnull': 200, 'next_year_outperform_bist100_nonnull': 200}` |
| raw | `data/trusted_raw/bist100_benchmark_returns.csv` | 6 |  | 2020-2025 |  | 0.0 | `{}` |
| raw | `data/trusted_raw/bist100_benchmark_returns.template.csv` | 0 |  |  |  | 0.0 | `{}` |
| raw | `data/trusted_raw/company_universe.csv` | 40 | 40 |  |  | 0.2 | `{}` |
| raw | `data/trusted_raw/financials/bist100_expansion_template.csv` | 10 | 2 | 2020-2024 | 0 | 0.8929 | `{}` |
| raw | `data/trusted_raw/financials/bist100_yfinance_candidate.csv` | 183 | 41 | 2021-2025 | 0 | 0.2407 | `{}` |
| raw | `data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv` | 163 | 41 | 2021-2025 | 0 | 0.1704 | `{}` |
| raw | `data/trusted_raw/financials/candidate_from_yearly_snapshots.csv` | 240 | 40 | 2020-2025 | 0 | 0.0161 | `{}` |
| raw | `data/trusted_raw/financials/corrected_balance_sheet_2024.csv` | 40 | 40 | 2024-2024 | 0 | 0.0821 | `{}` |
| raw | `data/trusted_raw/financials/corrected_yearly_financials_candidate.csv` | 240 | 40 | 2020-2025 | 0 | 0.0007 | `{}` |
| raw | `data/trusted_raw/financials/free_valuation_history_candidate.csv` | 486 | 81 | 2020-2025 | 0 | 0.3011 | `{}` |
| raw | `data/trusted_raw/financials/templates/company_financials_template.csv` | 0 |  |  | 0 | 0.0 | `{}` |
| raw | `data/trusted_raw/financials/templates/example_2tickers_2years.csv` | 4 | 2 | 2023-2024 | 0 | 0.0 | `{}` |
| raw | `data/trusted_raw/prices/yahoo_year_end_prices.csv` | 465 | 81 | 2020-2025 | 0 | 0.0 | `{}` |
| raw | `data/trusted_raw/shares_outstanding_events.csv` | 76 | 40 |  |  | 0.0 | `{}` |
| raw | `data/trusted_raw/shares_outstanding_events_template.csv` | 93 | 40 |  |  | 0.0 | `{}` |
| raw | `data/trusted_raw/shares_outstanding_manual.csv` | 486 | 81 | 2020-2025 | 0 | 0.3374 | `{}` |
| raw | `data/trusted_raw/shares_outstanding_manual_template.csv` | 240 | 40 | 2020-2025 | 0 | 0.5 | `{}` |