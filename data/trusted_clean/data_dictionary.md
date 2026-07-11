# Data dictionary — modeling_dataset_2020_2025.csv

Research/educational only. NOT investment advice.

Each row = one company-year. Features belong to year T; the primary
target is the realized return in year T+1.

| column | role | leakage_risk |
|---|---|---|
| `ticker` | identifier | none |
| `company_name` | identifier | none |
| `year` | identifier | none |
| `sector` | metadata | none |
| `indices` | metadata | none |
| `is_bist100` | metadata | none |
| `benchmark_same_year_return_pct` | feature_allowed | provisional_reference_fundamental |
| `current_assets` | feature_allowed | provisional_reference_fundamental |
| `current_ratio` | feature_allowed | provisional_reference_fundamental |
| `ebitda` | feature_allowed | provisional_reference_fundamental |
| `ebitda_growth_pct` | feature_allowed | provisional_reference_fundamental |
| `ebitda_margin` | feature_allowed | provisional_reference_fundamental |
| `enterprise_value` | feature_allowed | provisional_reference_fundamental |
| `equity` | feature_allowed | provisional_reference_fundamental |
| `ev_ebitda` | feature_allowed | provisional_reference_fundamental |
| `financial_debt_ratio` | feature_allowed | provisional_reference_fundamental |
| `gross_margin` | feature_allowed | provisional_reference_fundamental |
| `gross_profit` | feature_allowed | provisional_reference_fundamental |
| `gross_profit_growth_pct` | feature_allowed | provisional_reference_fundamental |
| `leverage_ratio` | feature_allowed | provisional_reference_fundamental |
| `long_term_liabilities` | feature_allowed | provisional_reference_fundamental |
| `market_cap` | feature_allowed | provisional_reference_fundamental |
| `net_debt` | feature_allowed | provisional_reference_fundamental |
| `net_debt_to_ebitda` | feature_allowed | provisional_reference_fundamental |
| `net_income` | feature_allowed | provisional_reference_fundamental |
| `net_income_growth_pct` | feature_allowed | provisional_reference_fundamental |
| `net_margin` | feature_allowed | provisional_reference_fundamental |
| `non_current_assets` | feature_allowed | provisional_reference_fundamental |
| `operating_income` | feature_allowed | provisional_reference_fundamental |
| `operating_income_growth_pct` | feature_allowed | provisional_reference_fundamental |
| `pb_ratio` | feature_allowed | provisional_reference_fundamental |
| `pe_ratio` | feature_allowed | provisional_reference_fundamental |
| `price_adjclose_t` | feature_allowed | provisional_reference_fundamental |
| `price_data_available` | feature_allowed | provisional_reference_fundamental |
| `price_drawdown_from_3y_high_pct` | feature_allowed | provisional_reference_fundamental |
| `price_history_years_available` | feature_allowed | provisional_reference_fundamental |
| `price_momentum_1y_pct` | feature_allowed | provisional_reference_fundamental |
| `price_momentum_2y_pct` | feature_allowed | provisional_reference_fundamental |
| `price_vs_bist100_1y_pct` | feature_allowed | provisional_reference_fundamental |
| `revenue` | feature_allowed | provisional_reference_fundamental |
| `revenue_growth_pct` | feature_allowed | provisional_reference_fundamental |
| `roa` | feature_allowed | provisional_reference_fundamental |
| `roe` | feature_allowed | provisional_reference_fundamental |
| `short_term_liabilities` | feature_allowed | provisional_reference_fundamental |
| `total_assets` | feature_allowed | provisional_reference_fundamental |
| `working_capital` | feature_allowed | provisional_reference_fundamental |
| `next_year_return_pct` | target | is_target |
| `next_year_rank_by_return` | target | is_target |
| `next_year_return_percentile` | target | is_target |
| `next_year_top_10pct_returner` | target | is_target |
| `next_year_top_20pct_returner` | target | is_target |
| `next_year_bist100_return_pct` | benchmark | is_target |
| `next_year_excess_return_vs_bist100` | benchmark | is_target |
| `next_year_outperform_bist100` | benchmark | is_target |
| `same_year_return_pct` | same_year_analysis_only | is_same_year_outcome |
| `target_year` | metadata | none |
| `has_target` | metadata | none |
| `is_inference_row` | metadata | none |
| `is_public_universe` | metadata | none |
| `is_training_universe` | metadata | none |
| `universe_source` | metadata | none |

## Roles
- **identifier / metadata**: not used as predictive features.
- **feature_allowed**: year-T provisional fundamentals (genuinely vary by year).
- **target**: next-year realized-return outcomes (never a feature).
- **same_year_analysis_only**: `same_year_return_pct` — analysis only, never a feature.
- **benchmark**: BIST100-relative targets (present only if benchmark CSV provided).
- **excluded**: reference columns proven to be a frozen snapshot (see data_quality_report).