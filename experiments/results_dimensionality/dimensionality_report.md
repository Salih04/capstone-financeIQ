# R4-DIM-01 — Feature redundancy & effective dimensionality

## Research-only boundary

Descriptive feature-geometry analysis only. Research support only; not investment advice.

No reliable predictive edge has been established.

This report does not establish predictive edge or alpha, profitability or investment value, tradable strategy validity, feature-selection benefit, model improvement, overfitting diagnosis, causal explanation, production validity, or deployment validity.

## Source and frozen methodology

- Task: `R4-DIM-01`
- Methodology status: `APPROVED_FROZEN`
- Source: `data/trusted_clean/modeling_dataset_training_2020_2025.csv`
- Target eligibility: next_year_return_pct originally non-missing; feature year belongs to the window's frozen feature_years
- Rank normalization: `u = (rank_average - 1) / (n_obs - 1) when n_obs >= 2`
- Missing fill: `analysis-only u = 0.5 for every originally missing or branch-neutral cell`
- Guard: removed by owner amendment; no such guard exists

### Amendment record

- n_obs = 0 and n_obs = 1 rank-completion branches added; n_obs >= 2 average/midrank normalization retained
- mandatory pre-fill feature-year variance guard removed; post-completion Pearson well-definedness is sole numerical guard
- fixed PRIMARY 40-feature assumption replaced by deterministic construction/support eligibility and global intersection
- structurally_ineligible and support_excluded remain separate with support blocking windows
- (ticker, year) uniqueness and sealed per-year I_y are required before scientific computation
- full 40-feature diagnostic scope remains unconditional; matrix exclusion does not erase diagnostic evidence

## Exact 40-feature diagnostic order

1. `benchmark_same_year_return_pct`
2. `current_assets`
3. `current_ratio`
4. `ebitda`
5. `ebitda_growth_pct`
6. `ebitda_margin`
7. `enterprise_value`
8. `equity`
9. `ev_ebitda`
10. `financial_debt_ratio`
11. `gross_margin`
12. `gross_profit`
13. `gross_profit_growth_pct`
14. `leverage_ratio`
15. `long_term_liabilities`
16. `market_cap`
17. `net_debt`
18. `net_debt_to_ebitda`
19. `net_income`
20. `net_income_growth_pct`
21. `net_margin`
22. `non_current_assets`
23. `operating_income`
24. `operating_income_growth_pct`
25. `pb_ratio`
26. `pe_ratio`
27. `price_adjclose_t`
28. `price_data_available`
29. `price_drawdown_from_3y_high_pct`
30. `price_history_years_available`
31. `price_momentum_1y_pct`
32. `price_momentum_2y_pct`
33. `price_vs_bist100_1y_pct`
34. `revenue`
35. `revenue_growth_pct`
36. `roa`
37. `roe`
38. `short_term_liabilities`
39. `total_assets`
40. `working_capital`

## PRIMARY eligibility and sealed row universe

PRIMARY dimension P = `35`.

PRIMARY features: `current_assets`, `current_ratio`, `ebitda`, `ebitda_growth_pct`, `ebitda_margin`, `enterprise_value`, `equity`, `ev_ebitda`, `financial_debt_ratio`, `gross_margin`, `gross_profit`, `gross_profit_growth_pct`, `leverage_ratio`, `long_term_liabilities`, `market_cap`, `net_debt`, `net_debt_to_ebitda`, `net_income`, `net_income_growth_pct`, `net_margin`, `non_current_assets`, `operating_income`, `operating_income_growth_pct`, `pb_ratio`, `pe_ratio`, `price_adjclose_t`, `price_drawdown_from_3y_high_pct`, `price_history_years_available`, `revenue`, `revenue_growth_pct`, `roa`, `roe`, `short_term_liabilities`, `total_assets`, `working_capital`.

### structurally_ineligible

- `benchmark_same_year_return_pct` — benchmark return is merged by year and is constant across supported tickers in a feature year; blocking feature years: [2020, 2021, 2022, 2023].
- `price_data_available` — price feature construction emits supported availability as the fixed numeric value 1.0; blocking feature years: [2020, 2021, 2022, 2023].

### support_excluded

- `price_momentum_1y_pct` — exact support rule failed for at least one feature year; no cohort-size judgment applied; blocking windows: test_2023, test_2024, test_2025.
- `price_momentum_2y_pct` — exact support rule failed for at least one feature year; no cohort-size judgment applied; blocking windows: test_2023, test_2024, test_2025.
- `price_vs_bist100_1y_pct` — exact support rule failed for at least one feature year; no cohort-size judgment applied; blocking windows: test_2023, test_2024, test_2025.

### Eligibility evidence

#### `benchmark_same_year_return_pct`
- `test_2023`: ORDER_CAPABLE years=0/2; total support cells=73; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
- `test_2024`: ORDER_CAPABLE years=0/3; total support cells=150; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=False; support=77; WINDOW_YEAR_ELIGIBLE=False.
- `test_2025`: ORDER_CAPABLE years=0/4; total support cells=228; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=False; support=77; WINDOW_YEAR_ELIGIBLE=False.
  - 2023: order_capable=False; support=78; WINDOW_YEAR_ELIGIBLE=False.
#### `current_assets`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `current_ratio`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `ebitda`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `ebitda_growth_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `ebitda_margin`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `enterprise_value`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=72; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=109; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=147; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
#### `equity`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `ev_ebitda`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=69; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=33; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=105; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=33; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=139; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=33; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=34; WINDOW_YEAR_ELIGIBLE=True.
#### `financial_debt_ratio`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `gross_margin`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `gross_profit`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `gross_profit_growth_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `leverage_ratio`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `long_term_liabilities`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `market_cap`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=72; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=109; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=147; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
#### `net_debt`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=140; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=60; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=201; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=60; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=61; WINDOW_YEAR_ELIGIBLE=True.
#### `net_debt_to_ebitda`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `net_income`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `net_income_growth_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `net_margin`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `non_current_assets`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `operating_income`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `operating_income_growth_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `pb_ratio`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=72; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=109; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=147; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=37; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
#### `pe_ratio`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=58; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=27; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=31; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=91; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=27; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=31; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=33; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=125; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=27; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=31; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=33; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=34; WINDOW_YEAR_ELIGIBLE=True.
#### `price_adjclose_t`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=73; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=228; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=78; WINDOW_YEAR_ELIGIBLE=True.
#### `price_data_available`
- `test_2023`: ORDER_CAPABLE years=0/2; total support cells=73; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
- `test_2024`: ORDER_CAPABLE years=0/3; total support cells=150; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=False; support=77; WINDOW_YEAR_ELIGIBLE=False.
- `test_2025`: ORDER_CAPABLE years=0/4; total support cells=228; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=False; support=35; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=False; support=38; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=False; support=77; WINDOW_YEAR_ELIGIBLE=False.
  - 2023: order_capable=False; support=78; WINDOW_YEAR_ELIGIBLE=False.
#### `price_drawdown_from_3y_high_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=73; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=228; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=78; WINDOW_YEAR_ELIGIBLE=True.
#### `price_history_years_available`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=73; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=228; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=35; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=38; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=78; WINDOW_YEAR_ELIGIBLE=True.
#### `price_momentum_1y_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=36; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=112; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=76; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=189; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=76; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
#### `price_momentum_2y_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=0; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=73; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=True; support=73; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=149; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2022: order_capable=True; support=73; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=76; WINDOW_YEAR_ELIGIBLE=True.
#### `price_vs_bist100_1y_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=36; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=112; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=76; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=189; WINDOW_ORDER_CAPABLE=False.
  - 2020: order_capable=True; support=0; WINDOW_YEAR_ELIGIBLE=False.
  - 2021: order_capable=True; support=36; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=76; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=77; WINDOW_YEAR_ELIGIBLE=True.
#### `revenue`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `revenue_growth_pct`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=80; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=120; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=160; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
#### `roa`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `roe`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `short_term_liabilities`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
#### `total_assets`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=161; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=241; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=80; WINDOW_YEAR_ELIGIBLE=True.
#### `working_capital`
- `test_2023`: ORDER_CAPABLE years=2/2; total support cells=81; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
- `test_2024`: ORDER_CAPABLE years=3/3; total support cells=150; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
- `test_2025`: ORDER_CAPABLE years=4/4; total support cells=219; WINDOW_ORDER_CAPABLE=True.
  - 2020: order_capable=True; support=40; WINDOW_YEAR_ELIGIBLE=True.
  - 2021: order_capable=True; support=41; WINDOW_YEAR_ELIGIBLE=True.
  - 2022: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.
  - 2023: order_capable=True; support=69; WINDOW_YEAR_ELIGIBLE=True.

### Sealed per-year I_y membership

- `2020`: count=26; members=AEFES:2020, ARCLK:2020, ASELS:2020, BIMAS:2020, CCOLA:2020, CIMSA:2020, DOAS:2020, ENKAI:2020, EREGL:2020, FROTO:2020, GUBRF:2020, HEKTS:2020, KONTR:2020, MAVI:2020, OYAKC:2020, PETKM:2020, SASA:2020, SISE:2020, TCELL:2020, TOASO:2020, TRALT:2020, TRMET:2020, TSKB:2020, TTKOM:2020, TURSG:2020, ULKER:2020.
- `2021`: count=31; members=AEFES:2021, ARCLK:2021, ASELS:2021, BIMAS:2021, BRSAN:2021, CCOLA:2021, CIMSA:2021, DOAS:2021, ENKAI:2021, EREGL:2021, FROTO:2021, GUBRF:2021, HEKTS:2021, KONTR:2021, KUYAS:2021, MAVI:2021, MGROS:2021, MIATK:2021, OYAKC:2021, PETKM:2021, SASA:2021, SISE:2021, TAVHL:2021, TCELL:2021, TOASO:2021, TRALT:2021, TRMET:2021, TSKB:2021, TTKOM:2021, TUPRS:2021, TURSG:2021.
- `2022`: count=33; members=AEFES:2022, ARCLK:2022, ASELS:2022, BIMAS:2022, BRSAN:2022, CANTE:2022, CCOLA:2022, CIMSA:2022, DOAS:2022, ENKAI:2022, EREGL:2022, FROTO:2022, GUBRF:2022, HEKTS:2022, KONTR:2022, KUYAS:2022, MAVI:2022, MGROS:2022, MIATK:2022, OYAKC:2022, PETKM:2022, PGSUS:2022, SASA:2022, SISE:2022, TAVHL:2022, TCELL:2022, TOASO:2022, TRALT:2022, TRMET:2022, TSKB:2022, TTKOM:2022, TUPRS:2022, TURSG:2022.
- `2023`: count=32; members=AEFES:2023, ARCLK:2023, ASELS:2023, ASTOR:2023, BIMAS:2023, BRSAN:2023, BTCIM:2023, CANTE:2023, CCOLA:2023, CIMSA:2023, DOAS:2023, ENKAI:2023, EREGL:2023, FROTO:2023, KONTR:2023, KUYAS:2023, MAVI:2023, MIATK:2023, OYAKC:2023, PGSUS:2023, SASA:2023, SISE:2023, TAVHL:2023, TCELL:2023, TOASO:2023, TRALT:2023, TRMET:2023, TSKB:2023, TTKOM:2023, TUPRS:2023, TURSG:2023, ULKER:2023.

## Independent windows

### `test_2023`

Feature years: 2020, 2021; training target years: 2021, 2022; held-out feature year: 2022; held-out target year: 2023.
Target-eligible rows: **81**; PRIMARY rank rows: **57**.
Row members are sealed by unique `(ticker, year)` identity: [{"ticker": "AEFES", "year": 2020}, {"ticker": "ARCLK", "year": 2020}, {"ticker": "ASELS", "year": 2020}, {"ticker": "ASTOR", "year": 2020}, {"ticker": "BIMAS", "year": 2020}, {"ticker": "BRSAN", "year": 2020}, {"ticker": "BTCIM", "year": 2020}, {"ticker": "CANTE", "year": 2020}, {"ticker": "CCOLA", "year": 2020}, {"ticker": "CIMSA", "year": 2020}, {"ticker": "DOAS", "year": 2020}, {"ticker": "DSTKF", "year": 2020}, {"ticker": "ENKAI", "year": 2020}, {"ticker": "EREGL", "year": 2020}, {"ticker": "FROTO", "year": 2020}, {"ticker": "GUBRF", "year": 2020}, {"ticker": "HEKTS", "year": 2020}, {"ticker": "KONTR", "year": 2020}, {"ticker": "KRDMD", "year": 2020}, {"ticker": "KUYAS", "year": 2020}, {"ticker": "MAVI", "year": 2020}, {"ticker": "MGROS", "year": 2020}, {"ticker": "MIATK", "year": 2020}, {"ticker": "OYAKC", "year": 2020}, {"ticker": "PASEU", "year": 2020}, {"ticker": "PETKM", "year": 2020}, {"ticker": "PGSUS", "year": 2020}, {"ticker": "SASA", "year": 2020}, {"ticker": "SISE", "year": 2020}, {"ticker": "TAVHL", "year": 2020}, {"ticker": "TCELL", "year": 2020}, {"ticker": "THYAO", "year": 2020}, {"ticker": "TOASO", "year": 2020}, {"ticker": "TRALT", "year": 2020}, {"ticker": "TRMET", "year": 2020}, {"ticker": "TSKB", "year": 2020}, {"ticker": "TTKOM", "year": 2020}, {"ticker": "TUPRS", "year": 2020}, {"ticker": "TURSG", "year": 2020}, {"ticker": "ULKER", "year": 2020}, {"ticker": "AEFES", "year": 2021}, {"ticker": "ARCLK", "year": 2021}, {"ticker": "ASELS", "year": 2021}, {"ticker": "ASTOR", "year": 2021}, {"ticker": "BIMAS", "year": 2021}, {"ticker": "BRSAN", "year": 2021}, {"ticker": "BTCIM", "year": 2021}, {"ticker": "CANTE", "year": 2021}, {"ticker": "CCOLA", "year": 2021}, {"ticker": "CIMSA", "year": 2021}, {"ticker": "DOAS", "year": 2021}, {"ticker": "DSTKF", "year": 2021}, {"ticker": "EGEEN", "year": 2021}, {"ticker": "ENKAI", "year": 2021}, {"ticker": "EREGL", "year": 2021}, {"ticker": "FROTO", "year": 2021}, {"ticker": "GUBRF", "year": 2021}, {"ticker": "HEKTS", "year": 2021}, {"ticker": "KONTR", "year": 2021}, {"ticker": "KRDMD", "year": 2021}, {"ticker": "KUYAS", "year": 2021}, {"ticker": "MAVI", "year": 2021}, {"ticker": "MGROS", "year": 2021}, {"ticker": "MIATK", "year": 2021}, {"ticker": "OYAKC", "year": 2021}, {"ticker": "PASEU", "year": 2021}, {"ticker": "PETKM", "year": 2021}, {"ticker": "PGSUS", "year": 2021}, {"ticker": "SASA", "year": 2021}, {"ticker": "SISE", "year": 2021}, {"ticker": "TAVHL", "year": 2021}, {"ticker": "TCELL", "year": 2021}, {"ticker": "THYAO", "year": 2021}, {"ticker": "TOASO", "year": 2021}, {"ticker": "TRALT", "year": 2021}, {"ticker": "TRMET", "year": 2021}, {"ticker": "TSKB", "year": 2021}, {"ticker": "TTKOM", "year": 2021}, {"ticker": "TUPRS", "year": 2021}, {"ticker": "TURSG", "year": 2021}, {"ticker": "ULKER", "year": 2021}].
Row-universe invariant: `PASS`; analytical key=`(ticker, year)`; duplicate keys=0.

#### Missingness diagnostics

See `feature_missingness.csv` for unconditional full-40 pre-imputation counts and rates.

#### Pair-overlap evidence

See `pair_overlap.csv` for complete full-40 pre-imputation n_AB evidence.

Overlap summary: {"maximum": 81, "mean": 67.99871794871795, "median": 73.0, "minimum": 0, "off_diagonal_pair_count": 780, "population_std": 20.327100727781374}.

#### Redundancy thresholds

##### Inclusive threshold `0.70`

Rule: `abs(correlation) >= 0.70`.

1. `current_assets, current_ratio, ebitda, enterprise_value, equity, ev_ebitda, financial_debt_ratio, gross_profit, leverage_ratio, long_term_liabilities, net_debt, net_debt_to_ebitda, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets, working_capital` — size=19, edge_count=49, min_abs_corr=0.0031399912778020417, median_abs_corr=0.49037941561273446.
2. `ebitda_growth_pct, gross_profit_growth_pct, revenue_growth_pct` — size=3, edge_count=2, min_abs_corr=0.5361315322601209, median_abs_corr=0.7329220058096834.
3. `ebitda_margin, net_margin` — size=2, edge_count=1, min_abs_corr=0.7692539227618336, median_abs_corr=0.7692539227618336.
4. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
5. `market_cap, pb_ratio` — size=2, edge_count=1, min_abs_corr=0.7045019469022502, median_abs_corr=0.7045019469022502.
6. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
7. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
8. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
9. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
10. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
11. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
12. `roa` — size=1, edge_count=0, singleton pair statistics=null.
13. `roe` — size=1, edge_count=0, singleton pair statistics=null.

##### Inclusive threshold `0.80`

Rule: `abs(correlation) >= 0.80`.

1. `current_assets, ebitda, equity, gross_profit, long_term_liabilities, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets` — size=11, edge_count=19, min_abs_corr=0.6116295505543857, median_abs_corr=0.7745731620272072.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9085836722200361, median_abs_corr=0.9085836722200361.
4. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
5. `enterprise_value, net_debt` — size=2, edge_count=1, min_abs_corr=0.9666463148713477, median_abs_corr=0.9666463148713477.
6. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
7. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
8. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
9. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
10. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
11. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
12. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
14. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
15. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
16. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
17. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
18. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
19. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
20. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
21. `roa` — size=1, edge_count=0, singleton pair statistics=null.
22. `roe` — size=1, edge_count=0, singleton pair statistics=null.
23. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

##### Inclusive threshold `0.90`

Rule: `abs(correlation) >= 0.90`.

1. `current_assets, equity, long_term_liabilities, non_current_assets, short_term_liabilities, total_assets` — size=6, edge_count=6, min_abs_corr=0.6738682948102922, median_abs_corr=0.8898473615351071.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda, gross_profit, operating_income, revenue` — size=4, edge_count=3, min_abs_corr=0.7920940273649207, median_abs_corr=0.877987602458569.
4. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9085836722200361, median_abs_corr=0.9085836722200361.
5. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
6. `enterprise_value, net_debt` — size=2, edge_count=1, min_abs_corr=0.9666463148713477, median_abs_corr=0.9666463148713477.
7. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
8. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
9. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
10. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
11. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
12. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_income` — size=1, edge_count=0, singleton pair statistics=null.
14. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
15. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
16. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
17. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
18. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
19. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
20. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
21. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
22. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
23. `roa` — size=1, edge_count=0, singleton pair statistics=null.
24. `roe` — size=1, edge_count=0, singleton pair statistics=null.
25. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

#### Spectrum and effective ranks

Raw eigenvalues: `[0.0013466034916855964,0.0030187157975211125,0.0036734757678710504,0.00473978121607483,0.005383348139806336,0.007573870970036107,0.009013359097983526,0.01682094202644027,0.019838690400628432,0.021032172928239338,0.03689892777936205,0.03909621310089288,0.046539894410053004,0.06783330426911235,0.07205765442834292,0.08502648721562077,0.11598719491189231,0.1449040760157816,0.16923162024680666,0.21618691594668524,0.26819186191415056,0.31640444078025787,0.3746946444531469,0.4334968349826408,0.5392485278075593,0.6873306717906446,0.8506017667523232,0.9230201706421197,1.1352872078464633,1.5668677704287517,2.3628344798642957,3.277450441887952,3.75664109311487,6.842098229300285,10.579628610273694]`.
Post-tolerance eigenvalues: `[0.0013466034916855964,0.0030187157975211125,0.0036734757678710504,0.00473978121607483,0.005383348139806336,0.007573870970036107,0.009013359097983526,0.01682094202644027,0.019838690400628432,0.021032172928239338,0.03689892777936205,0.03909621310089288,0.046539894410053004,0.06783330426911235,0.07205765442834292,0.08502648721562077,0.11598719491189231,0.1449040760157816,0.16923162024680666,0.21618691594668524,0.26819186191415056,0.31640444078025787,0.3746946444531469,0.4334968349826408,0.5392485278075593,0.6873306717906446,0.8506017667523232,0.9230201706421197,1.1352872078464633,1.5668677704287517,2.3628344798642957,3.277450441887952,3.75664109311487,6.842098229300285,10.579628610273694]`.
lambda_max=10.579628610273694; zero_tolerance=1.0579628610273694e-07.
Participation-ratio effective dimensionality D_eff=6.253314353621025.
Roy–Vetterli spectral-entropy effective rank erank=9.657901656955673.

### `test_2024`

Feature years: 2020, 2021, 2022; training target years: 2021, 2022, 2023; held-out feature year: 2023; held-out target year: 2024.
Target-eligible rows: **161**; PRIMARY rank rows: **90**.
Row members are sealed by unique `(ticker, year)` identity: [{"ticker": "AEFES", "year": 2020}, {"ticker": "ARCLK", "year": 2020}, {"ticker": "ASELS", "year": 2020}, {"ticker": "ASTOR", "year": 2020}, {"ticker": "BIMAS", "year": 2020}, {"ticker": "BRSAN", "year": 2020}, {"ticker": "BTCIM", "year": 2020}, {"ticker": "CANTE", "year": 2020}, {"ticker": "CCOLA", "year": 2020}, {"ticker": "CIMSA", "year": 2020}, {"ticker": "DOAS", "year": 2020}, {"ticker": "DSTKF", "year": 2020}, {"ticker": "ENKAI", "year": 2020}, {"ticker": "EREGL", "year": 2020}, {"ticker": "FROTO", "year": 2020}, {"ticker": "GUBRF", "year": 2020}, {"ticker": "HEKTS", "year": 2020}, {"ticker": "KONTR", "year": 2020}, {"ticker": "KRDMD", "year": 2020}, {"ticker": "KUYAS", "year": 2020}, {"ticker": "MAVI", "year": 2020}, {"ticker": "MGROS", "year": 2020}, {"ticker": "MIATK", "year": 2020}, {"ticker": "OYAKC", "year": 2020}, {"ticker": "PASEU", "year": 2020}, {"ticker": "PETKM", "year": 2020}, {"ticker": "PGSUS", "year": 2020}, {"ticker": "SASA", "year": 2020}, {"ticker": "SISE", "year": 2020}, {"ticker": "TAVHL", "year": 2020}, {"ticker": "TCELL", "year": 2020}, {"ticker": "THYAO", "year": 2020}, {"ticker": "TOASO", "year": 2020}, {"ticker": "TRALT", "year": 2020}, {"ticker": "TRMET", "year": 2020}, {"ticker": "TSKB", "year": 2020}, {"ticker": "TTKOM", "year": 2020}, {"ticker": "TUPRS", "year": 2020}, {"ticker": "TURSG", "year": 2020}, {"ticker": "ULKER", "year": 2020}, {"ticker": "AEFES", "year": 2021}, {"ticker": "ARCLK", "year": 2021}, {"ticker": "ASELS", "year": 2021}, {"ticker": "ASTOR", "year": 2021}, {"ticker": "BIMAS", "year": 2021}, {"ticker": "BRSAN", "year": 2021}, {"ticker": "BTCIM", "year": 2021}, {"ticker": "CANTE", "year": 2021}, {"ticker": "CCOLA", "year": 2021}, {"ticker": "CIMSA", "year": 2021}, {"ticker": "DOAS", "year": 2021}, {"ticker": "DSTKF", "year": 2021}, {"ticker": "EGEEN", "year": 2021}, {"ticker": "ENKAI", "year": 2021}, {"ticker": "EREGL", "year": 2021}, {"ticker": "FROTO", "year": 2021}, {"ticker": "GUBRF", "year": 2021}, {"ticker": "HEKTS", "year": 2021}, {"ticker": "KONTR", "year": 2021}, {"ticker": "KRDMD", "year": 2021}, {"ticker": "KUYAS", "year": 2021}, {"ticker": "MAVI", "year": 2021}, {"ticker": "MGROS", "year": 2021}, {"ticker": "MIATK", "year": 2021}, {"ticker": "OYAKC", "year": 2021}, {"ticker": "PASEU", "year": 2021}, {"ticker": "PETKM", "year": 2021}, {"ticker": "PGSUS", "year": 2021}, {"ticker": "SASA", "year": 2021}, {"ticker": "SISE", "year": 2021}, {"ticker": "TAVHL", "year": 2021}, {"ticker": "TCELL", "year": 2021}, {"ticker": "THYAO", "year": 2021}, {"ticker": "TOASO", "year": 2021}, {"ticker": "TRALT", "year": 2021}, {"ticker": "TRMET", "year": 2021}, {"ticker": "TSKB", "year": 2021}, {"ticker": "TTKOM", "year": 2021}, {"ticker": "TUPRS", "year": 2021}, {"ticker": "TURSG", "year": 2021}, {"ticker": "ULKER", "year": 2021}, {"ticker": "AEFES", "year": 2022}, {"ticker": "AGESA", "year": 2022}, {"ticker": "AGHOL", "year": 2022}, {"ticker": "AKBNK", "year": 2022}, {"ticker": "AKENR", "year": 2022}, {"ticker": "AKSA", "year": 2022}, {"ticker": "AKSEN", "year": 2022}, {"ticker": "ALARK", "year": 2022}, {"ticker": "ALBRK", "year": 2022}, {"ticker": "ANHYT", "year": 2022}, {"ticker": "ARCLK", "year": 2022}, {"ticker": "ASELS", "year": 2022}, {"ticker": "ASTOR", "year": 2022}, {"ticker": "BERA", "year": 2022}, {"ticker": "BIMAS", "year": 2022}, {"ticker": "BRSAN", "year": 2022}, {"ticker": "BTCIM", "year": 2022}, {"ticker": "CANTE", "year": 2022}, {"ticker": "CCOLA", "year": 2022}, {"ticker": "CEMTS", "year": 2022}, {"ticker": "CIMSA", "year": 2022}, {"ticker": "DEVA", "year": 2022}, {"ticker": "DOAS", "year": 2022}, {"ticker": "DOHOL", "year": 2022}, {"ticker": "DSTKF", "year": 2022}, {"ticker": "EGEEN", "year": 2022}, {"ticker": "EKGYO", "year": 2022}, {"ticker": "ENJSA", "year": 2022}, {"ticker": "ENKAI", "year": 2022}, {"ticker": "EREGL", "year": 2022}, {"ticker": "FROTO", "year": 2022}, {"ticker": "GARAN", "year": 2022}, {"ticker": "GUBRF", "year": 2022}, {"ticker": "HALKB", "year": 2022}, {"ticker": "HEKTS", "year": 2022}, {"ticker": "ISCTR", "year": 2022}, {"ticker": "ISGYO", "year": 2022}, {"ticker": "KCHOL", "year": 2022}, {"ticker": "KONTR", "year": 2022}, {"ticker": "KRDMD", "year": 2022}, {"ticker": "KRVGD", "year": 2022}, {"ticker": "KUYAS", "year": 2022}, {"ticker": "LOGO", "year": 2022}, {"ticker": "MAVI", "year": 2022}, {"ticker": "MGROS", "year": 2022}, {"ticker": "MIATK", "year": 2022}, {"ticker": "MPARK", "year": 2022}, {"ticker": "NETAS", "year": 2022}, {"ticker": "NTGAZ", "year": 2022}, {"ticker": "ODAS", "year": 2022}, {"ticker": "OTKAR", "year": 2022}, {"ticker": "OYAKC", "year": 2022}, {"ticker": "PASEU", "year": 2022}, {"ticker": "PETKM", "year": 2022}, {"ticker": "PGSUS", "year": 2022}, {"ticker": "PRKME", "year": 2022}, {"ticker": "SAHOL", "year": 2022}, {"ticker": "SASA", "year": 2022}, {"ticker": "SELEC", "year": 2022}, {"ticker": "SISE", "year": 2022}, {"ticker": "SKBNK", "year": 2022}, {"ticker": "SMRTG", "year": 2022}, {"ticker": "SOKM", "year": 2022}, {"ticker": "TAVHL", "year": 2022}, {"ticker": "TBORG", "year": 2022}, {"ticker": "TCELL", "year": 2022}, {"ticker": "THYAO", "year": 2022}, {"ticker": "TOASO", "year": 2022}, {"ticker": "TRALT", "year": 2022}, {"ticker": "TRMET", "year": 2022}, {"ticker": "TSKB", "year": 2022}, {"ticker": "TTKOM", "year": 2022}, {"ticker": "TUPRS", "year": 2022}, {"ticker": "TURSG", "year": 2022}, {"ticker": "ULKER", "year": 2022}, {"ticker": "ULUSE", "year": 2022}, {"ticker": "VAKBN", "year": 2022}, {"ticker": "VESTL", "year": 2022}, {"ticker": "YKBNK", "year": 2022}, {"ticker": "ZOREN", "year": 2022}].
Row-universe invariant: `PASS`; analytical key=`(ticker, year)`; duplicate keys=0.

#### Missingness diagnostics

See `feature_missingness.csv` for unconditional full-40 pre-imputation counts and rates.

#### Pair-overlap evidence

See `pair_overlap.csv` for complete full-40 pre-imputation n_AB evidence.

Overlap summary: {"maximum": 161, "mean": 119.13076923076923, "median": 120.0, "minimum": 31, "off_diagonal_pair_count": 780, "population_std": 25.49083951948786}.

#### Redundancy thresholds

##### Inclusive threshold `0.70`

Rule: `abs(correlation) >= 0.70`.

1. `current_assets, ebitda, equity, gross_profit, long_term_liabilities, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets` — size=11, edge_count=44, min_abs_corr=0.6368043214132708, median_abs_corr=0.8016875970401783.
2. `current_ratio, enterprise_value, ev_ebitda, financial_debt_ratio, leverage_ratio, net_debt, net_debt_to_ebitda, working_capital` — size=8, edge_count=9, min_abs_corr=0.18339594286753694, median_abs_corr=0.6038960485867095.
3. `ebitda_growth_pct, gross_profit_growth_pct, revenue_growth_pct` — size=3, edge_count=2, min_abs_corr=0.5636783670357902, median_abs_corr=0.743363349045555.
4. `ebitda_margin, gross_margin, net_margin` — size=3, edge_count=2, min_abs_corr=0.43534759571463844, median_abs_corr=0.7165796297554333.
5. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
6. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
7. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
8. `pb_ratio, pe_ratio` — size=2, edge_count=1, min_abs_corr=0.7342512962207981, median_abs_corr=0.7342512962207981.
9. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
10. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
11. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
12. `roa` — size=1, edge_count=0, singleton pair statistics=null.
13. `roe` — size=1, edge_count=0, singleton pair statistics=null.

##### Inclusive threshold `0.80`

Rule: `abs(correlation) >= 0.80`.

1. `current_assets, ebitda, equity, gross_profit, long_term_liabilities, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets` — size=11, edge_count=28, min_abs_corr=0.6368043214132708, median_abs_corr=0.8016875970401783.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9092014955443063, median_abs_corr=0.9092014955443063.
4. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
5. `enterprise_value, net_debt` — size=2, edge_count=1, min_abs_corr=0.9446963646915142, median_abs_corr=0.9446963646915142.
6. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
7. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
8. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
9. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
10. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
11. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
12. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
14. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
15. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
16. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
17. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
18. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
19. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
20. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
21. `roa` — size=1, edge_count=0, singleton pair statistics=null.
22. `roe` — size=1, edge_count=0, singleton pair statistics=null.
23. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

##### Inclusive threshold `0.90`

Rule: `abs(correlation) >= 0.90`.

1. `current_assets, equity, long_term_liabilities, non_current_assets, short_term_liabilities, total_assets` — size=6, edge_count=7, min_abs_corr=0.6891896562177894, median_abs_corr=0.8868724826982878.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda, operating_income` — size=2, edge_count=1, min_abs_corr=0.9635476191838994, median_abs_corr=0.9635476191838994.
4. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9092014955443063, median_abs_corr=0.9092014955443063.
5. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
6. `enterprise_value, net_debt` — size=2, edge_count=1, min_abs_corr=0.9446963646915142, median_abs_corr=0.9446963646915142.
7. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
8. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
9. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
10. `gross_profit, revenue` — size=2, edge_count=1, min_abs_corr=0.9440263516961351, median_abs_corr=0.9440263516961351.
11. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
12. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
14. `net_income` — size=1, edge_count=0, singleton pair statistics=null.
15. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
16. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
17. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
18. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
19. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
20. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
21. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
22. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
23. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
24. `roa` — size=1, edge_count=0, singleton pair statistics=null.
25. `roe` — size=1, edge_count=0, singleton pair statistics=null.
26. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

#### Spectrum and effective ranks

Raw eigenvalues: `[0.0035135120315447394,0.00465719622724497,0.004961021751506615,0.0076199251292851326,0.009637803322396478,0.01387945093220304,0.016095089821958692,0.022630075236536304,0.03267225313263987,0.03680680070614419,0.03935222064402699,0.04864742858991207,0.056476447645951465,0.07008380162255554,0.0795431987602401,0.11033700950075911,0.1306410682784772,0.1345092117388169,0.1497529677216353,0.22644637437339957,0.277600505439087,0.31021534182239396,0.3813057468613783,0.5839281618565295,0.6199981886270373,0.7114933441235265,0.8154243228859394,0.9326350618013564,1.0304914306140733,1.4461373901933352,2.073665217828802,3.183555778578379,4.210576204910717,6.447770006679809,10.776940440610396]`.
Post-tolerance eigenvalues: `[0.0035135120315447394,0.00465719622724497,0.004961021751506615,0.0076199251292851326,0.009637803322396478,0.01387945093220304,0.016095089821958692,0.022630075236536304,0.03267225313263987,0.03680680070614419,0.03935222064402699,0.04864742858991207,0.056476447645951465,0.07008380162255554,0.0795431987602401,0.11033700950075911,0.1306410682784772,0.1345092117388169,0.1497529677216353,0.22644637437339957,0.277600505439087,0.31021534182239396,0.3813057468613783,0.5839281618565295,0.6199981886270373,0.7114933441235265,0.8154243228859394,0.9326350618013564,1.0304914306140733,1.4461373901933352,2.073665217828802,3.183555778578379,4.210576204910717,6.447770006679809,10.776940440610396]`.
lambda_max=10.776940440610396; zero_tolerance=1.0776940440610396e-07.
Participation-ratio effective dimensionality D_eff=6.241673716104843.
Roy–Vetterli spectral-entropy effective rank erank=9.82573121248293.

### `test_2025`

Feature years: 2020, 2021, 2022, 2023; training target years: 2021, 2022, 2023, 2024; held-out feature year: 2024; held-out target year: 2025.
Target-eligible rows: **241**; PRIMARY rank rows: **122**.
Row members are sealed by unique `(ticker, year)` identity: [{"ticker": "AEFES", "year": 2020}, {"ticker": "ARCLK", "year": 2020}, {"ticker": "ASELS", "year": 2020}, {"ticker": "ASTOR", "year": 2020}, {"ticker": "BIMAS", "year": 2020}, {"ticker": "BRSAN", "year": 2020}, {"ticker": "BTCIM", "year": 2020}, {"ticker": "CANTE", "year": 2020}, {"ticker": "CCOLA", "year": 2020}, {"ticker": "CIMSA", "year": 2020}, {"ticker": "DOAS", "year": 2020}, {"ticker": "DSTKF", "year": 2020}, {"ticker": "ENKAI", "year": 2020}, {"ticker": "EREGL", "year": 2020}, {"ticker": "FROTO", "year": 2020}, {"ticker": "GUBRF", "year": 2020}, {"ticker": "HEKTS", "year": 2020}, {"ticker": "KONTR", "year": 2020}, {"ticker": "KRDMD", "year": 2020}, {"ticker": "KUYAS", "year": 2020}, {"ticker": "MAVI", "year": 2020}, {"ticker": "MGROS", "year": 2020}, {"ticker": "MIATK", "year": 2020}, {"ticker": "OYAKC", "year": 2020}, {"ticker": "PASEU", "year": 2020}, {"ticker": "PETKM", "year": 2020}, {"ticker": "PGSUS", "year": 2020}, {"ticker": "SASA", "year": 2020}, {"ticker": "SISE", "year": 2020}, {"ticker": "TAVHL", "year": 2020}, {"ticker": "TCELL", "year": 2020}, {"ticker": "THYAO", "year": 2020}, {"ticker": "TOASO", "year": 2020}, {"ticker": "TRALT", "year": 2020}, {"ticker": "TRMET", "year": 2020}, {"ticker": "TSKB", "year": 2020}, {"ticker": "TTKOM", "year": 2020}, {"ticker": "TUPRS", "year": 2020}, {"ticker": "TURSG", "year": 2020}, {"ticker": "ULKER", "year": 2020}, {"ticker": "AEFES", "year": 2021}, {"ticker": "ARCLK", "year": 2021}, {"ticker": "ASELS", "year": 2021}, {"ticker": "ASTOR", "year": 2021}, {"ticker": "BIMAS", "year": 2021}, {"ticker": "BRSAN", "year": 2021}, {"ticker": "BTCIM", "year": 2021}, {"ticker": "CANTE", "year": 2021}, {"ticker": "CCOLA", "year": 2021}, {"ticker": "CIMSA", "year": 2021}, {"ticker": "DOAS", "year": 2021}, {"ticker": "DSTKF", "year": 2021}, {"ticker": "EGEEN", "year": 2021}, {"ticker": "ENKAI", "year": 2021}, {"ticker": "EREGL", "year": 2021}, {"ticker": "FROTO", "year": 2021}, {"ticker": "GUBRF", "year": 2021}, {"ticker": "HEKTS", "year": 2021}, {"ticker": "KONTR", "year": 2021}, {"ticker": "KRDMD", "year": 2021}, {"ticker": "KUYAS", "year": 2021}, {"ticker": "MAVI", "year": 2021}, {"ticker": "MGROS", "year": 2021}, {"ticker": "MIATK", "year": 2021}, {"ticker": "OYAKC", "year": 2021}, {"ticker": "PASEU", "year": 2021}, {"ticker": "PETKM", "year": 2021}, {"ticker": "PGSUS", "year": 2021}, {"ticker": "SASA", "year": 2021}, {"ticker": "SISE", "year": 2021}, {"ticker": "TAVHL", "year": 2021}, {"ticker": "TCELL", "year": 2021}, {"ticker": "THYAO", "year": 2021}, {"ticker": "TOASO", "year": 2021}, {"ticker": "TRALT", "year": 2021}, {"ticker": "TRMET", "year": 2021}, {"ticker": "TSKB", "year": 2021}, {"ticker": "TTKOM", "year": 2021}, {"ticker": "TUPRS", "year": 2021}, {"ticker": "TURSG", "year": 2021}, {"ticker": "ULKER", "year": 2021}, {"ticker": "AEFES", "year": 2022}, {"ticker": "AGESA", "year": 2022}, {"ticker": "AGHOL", "year": 2022}, {"ticker": "AKBNK", "year": 2022}, {"ticker": "AKENR", "year": 2022}, {"ticker": "AKSA", "year": 2022}, {"ticker": "AKSEN", "year": 2022}, {"ticker": "ALARK", "year": 2022}, {"ticker": "ALBRK", "year": 2022}, {"ticker": "ANHYT", "year": 2022}, {"ticker": "ARCLK", "year": 2022}, {"ticker": "ASELS", "year": 2022}, {"ticker": "ASTOR", "year": 2022}, {"ticker": "BERA", "year": 2022}, {"ticker": "BIMAS", "year": 2022}, {"ticker": "BRSAN", "year": 2022}, {"ticker": "BTCIM", "year": 2022}, {"ticker": "CANTE", "year": 2022}, {"ticker": "CCOLA", "year": 2022}, {"ticker": "CEMTS", "year": 2022}, {"ticker": "CIMSA", "year": 2022}, {"ticker": "DEVA", "year": 2022}, {"ticker": "DOAS", "year": 2022}, {"ticker": "DOHOL", "year": 2022}, {"ticker": "DSTKF", "year": 2022}, {"ticker": "EGEEN", "year": 2022}, {"ticker": "EKGYO", "year": 2022}, {"ticker": "ENJSA", "year": 2022}, {"ticker": "ENKAI", "year": 2022}, {"ticker": "EREGL", "year": 2022}, {"ticker": "FROTO", "year": 2022}, {"ticker": "GARAN", "year": 2022}, {"ticker": "GUBRF", "year": 2022}, {"ticker": "HALKB", "year": 2022}, {"ticker": "HEKTS", "year": 2022}, {"ticker": "ISCTR", "year": 2022}, {"ticker": "ISGYO", "year": 2022}, {"ticker": "KCHOL", "year": 2022}, {"ticker": "KONTR", "year": 2022}, {"ticker": "KRDMD", "year": 2022}, {"ticker": "KRVGD", "year": 2022}, {"ticker": "KUYAS", "year": 2022}, {"ticker": "LOGO", "year": 2022}, {"ticker": "MAVI", "year": 2022}, {"ticker": "MGROS", "year": 2022}, {"ticker": "MIATK", "year": 2022}, {"ticker": "MPARK", "year": 2022}, {"ticker": "NETAS", "year": 2022}, {"ticker": "NTGAZ", "year": 2022}, {"ticker": "ODAS", "year": 2022}, {"ticker": "OTKAR", "year": 2022}, {"ticker": "OYAKC", "year": 2022}, {"ticker": "PASEU", "year": 2022}, {"ticker": "PETKM", "year": 2022}, {"ticker": "PGSUS", "year": 2022}, {"ticker": "PRKME", "year": 2022}, {"ticker": "SAHOL", "year": 2022}, {"ticker": "SASA", "year": 2022}, {"ticker": "SELEC", "year": 2022}, {"ticker": "SISE", "year": 2022}, {"ticker": "SKBNK", "year": 2022}, {"ticker": "SMRTG", "year": 2022}, {"ticker": "SOKM", "year": 2022}, {"ticker": "TAVHL", "year": 2022}, {"ticker": "TBORG", "year": 2022}, {"ticker": "TCELL", "year": 2022}, {"ticker": "THYAO", "year": 2022}, {"ticker": "TOASO", "year": 2022}, {"ticker": "TRALT", "year": 2022}, {"ticker": "TRMET", "year": 2022}, {"ticker": "TSKB", "year": 2022}, {"ticker": "TTKOM", "year": 2022}, {"ticker": "TUPRS", "year": 2022}, {"ticker": "TURSG", "year": 2022}, {"ticker": "ULKER", "year": 2022}, {"ticker": "ULUSE", "year": 2022}, {"ticker": "VAKBN", "year": 2022}, {"ticker": "VESTL", "year": 2022}, {"ticker": "YKBNK", "year": 2022}, {"ticker": "ZOREN", "year": 2022}, {"ticker": "AEFES", "year": 2023}, {"ticker": "AGESA", "year": 2023}, {"ticker": "AGHOL", "year": 2023}, {"ticker": "AKBNK", "year": 2023}, {"ticker": "AKENR", "year": 2023}, {"ticker": "AKSA", "year": 2023}, {"ticker": "AKSEN", "year": 2023}, {"ticker": "ALARK", "year": 2023}, {"ticker": "ALBRK", "year": 2023}, {"ticker": "ANHYT", "year": 2023}, {"ticker": "ARCLK", "year": 2023}, {"ticker": "ASELS", "year": 2023}, {"ticker": "ASTOR", "year": 2023}, {"ticker": "BERA", "year": 2023}, {"ticker": "BIMAS", "year": 2023}, {"ticker": "BRSAN", "year": 2023}, {"ticker": "BTCIM", "year": 2023}, {"ticker": "CANTE", "year": 2023}, {"ticker": "CCOLA", "year": 2023}, {"ticker": "CEMTS", "year": 2023}, {"ticker": "CIMSA", "year": 2023}, {"ticker": "DEVA", "year": 2023}, {"ticker": "DOAS", "year": 2023}, {"ticker": "DOHOL", "year": 2023}, {"ticker": "DSTKF", "year": 2023}, {"ticker": "EGEEN", "year": 2023}, {"ticker": "EKGYO", "year": 2023}, {"ticker": "ENJSA", "year": 2023}, {"ticker": "ENKAI", "year": 2023}, {"ticker": "EREGL", "year": 2023}, {"ticker": "FROTO", "year": 2023}, {"ticker": "GARAN", "year": 2023}, {"ticker": "GUBRF", "year": 2023}, {"ticker": "HALKB", "year": 2023}, {"ticker": "HEKTS", "year": 2023}, {"ticker": "ISCTR", "year": 2023}, {"ticker": "ISGYO", "year": 2023}, {"ticker": "KCHOL", "year": 2023}, {"ticker": "KONTR", "year": 2023}, {"ticker": "KRDMD", "year": 2023}, {"ticker": "KRVGD", "year": 2023}, {"ticker": "KUYAS", "year": 2023}, {"ticker": "LOGO", "year": 2023}, {"ticker": "MAVI", "year": 2023}, {"ticker": "MGROS", "year": 2023}, {"ticker": "MIATK", "year": 2023}, {"ticker": "MPARK", "year": 2023}, {"ticker": "NETAS", "year": 2023}, {"ticker": "NTGAZ", "year": 2023}, {"ticker": "ODAS", "year": 2023}, {"ticker": "OTKAR", "year": 2023}, {"ticker": "OYAKC", "year": 2023}, {"ticker": "PASEU", "year": 2023}, {"ticker": "PETKM", "year": 2023}, {"ticker": "PGSUS", "year": 2023}, {"ticker": "PRKME", "year": 2023}, {"ticker": "SAHOL", "year": 2023}, {"ticker": "SASA", "year": 2023}, {"ticker": "SELEC", "year": 2023}, {"ticker": "SISE", "year": 2023}, {"ticker": "SKBNK", "year": 2023}, {"ticker": "SMRTG", "year": 2023}, {"ticker": "SOKM", "year": 2023}, {"ticker": "TAVHL", "year": 2023}, {"ticker": "TBORG", "year": 2023}, {"ticker": "TCELL", "year": 2023}, {"ticker": "THYAO", "year": 2023}, {"ticker": "TOASO", "year": 2023}, {"ticker": "TRALT", "year": 2023}, {"ticker": "TRMET", "year": 2023}, {"ticker": "TSKB", "year": 2023}, {"ticker": "TTKOM", "year": 2023}, {"ticker": "TUPRS", "year": 2023}, {"ticker": "TURSG", "year": 2023}, {"ticker": "ULKER", "year": 2023}, {"ticker": "ULUSE", "year": 2023}, {"ticker": "VAKBN", "year": 2023}, {"ticker": "VESTL", "year": 2023}, {"ticker": "YKBNK", "year": 2023}, {"ticker": "ZOREN", "year": 2023}].
Row-universe invariant: `PASS`; analytical key=`(ticker, year)`; duplicate keys=0.

#### Missingness diagnostics

See `feature_missingness.csv` for unconditional full-40 pre-imputation counts and rates.

#### Pair-overlap evidence

See `pair_overlap.csv` for complete full-40 pre-imputation n_AB evidence.

Overlap summary: {"maximum": 241, "mean": 170.73717948717947, "median": 160.0, "minimum": 64, "off_diagonal_pair_count": 780, "population_std": 37.562241027647254}.

#### Redundancy thresholds

##### Inclusive threshold `0.70`

Rule: `abs(correlation) >= 0.70`.

1. `current_assets, ebitda, equity, gross_profit, long_term_liabilities, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets` — size=11, edge_count=43, min_abs_corr=0.6497416300269746, median_abs_corr=0.7892555399675509.
2. `current_ratio, enterprise_value, financial_debt_ratio, leverage_ratio, net_debt, net_debt_to_ebitda, working_capital` — size=7, edge_count=7, min_abs_corr=0.12604729669709797, median_abs_corr=0.6250358240170941.
3. `ebitda_growth_pct, gross_profit_growth_pct, revenue_growth_pct` — size=3, edge_count=2, min_abs_corr=0.5786523764241388, median_abs_corr=0.7512286064395761.
4. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
5. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
6. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
7. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
8. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
9. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
10. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
11. `pb_ratio, pe_ratio` — size=2, edge_count=1, min_abs_corr=0.747380576647781, median_abs_corr=0.747380576647781.
12. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
13. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
14. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
15. `roa, roe` — size=2, edge_count=1, min_abs_corr=0.720865980878685, median_abs_corr=0.720865980878685.

##### Inclusive threshold `0.80`

Rule: `abs(correlation) >= 0.80`.

1. `current_assets, ebitda, equity, gross_profit, long_term_liabilities, net_income, non_current_assets, operating_income, revenue, short_term_liabilities, total_assets` — size=11, edge_count=23, min_abs_corr=0.6497416300269746, median_abs_corr=0.7892555399675509.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9096482675288545, median_abs_corr=0.9096482675288545.
4. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
5. `enterprise_value, net_debt` — size=2, edge_count=1, min_abs_corr=0.8851596521853182, median_abs_corr=0.8851596521853182.
6. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
7. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
8. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
9. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
10. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
11. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
12. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
14. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
15. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
16. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
17. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
18. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
19. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
20. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
21. `roa` — size=1, edge_count=0, singleton pair statistics=null.
22. `roe` — size=1, edge_count=0, singleton pair statistics=null.
23. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

##### Inclusive threshold `0.90`

Rule: `abs(correlation) >= 0.90`.

1. `current_assets, equity, long_term_liabilities, non_current_assets, short_term_liabilities, total_assets` — size=6, edge_count=6, min_abs_corr=0.6948344395707772, median_abs_corr=0.8785920076101695.
2. `current_ratio` — size=1, edge_count=0, singleton pair statistics=null.
3. `ebitda, operating_income` — size=2, edge_count=1, min_abs_corr=0.9163529115510888, median_abs_corr=0.9163529115510888.
4. `ebitda_growth_pct, gross_profit_growth_pct` — size=2, edge_count=1, min_abs_corr=0.9096482675288545, median_abs_corr=0.9096482675288545.
5. `ebitda_margin` — size=1, edge_count=0, singleton pair statistics=null.
6. `enterprise_value` — size=1, edge_count=0, singleton pair statistics=null.
7. `ev_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
8. `financial_debt_ratio` — size=1, edge_count=0, singleton pair statistics=null.
9. `gross_margin` — size=1, edge_count=0, singleton pair statistics=null.
10. `gross_profit, revenue` — size=2, edge_count=1, min_abs_corr=0.9490757963643304, median_abs_corr=0.9490757963643304.
11. `leverage_ratio` — size=1, edge_count=0, singleton pair statistics=null.
12. `market_cap` — size=1, edge_count=0, singleton pair statistics=null.
13. `net_debt` — size=1, edge_count=0, singleton pair statistics=null.
14. `net_debt_to_ebitda` — size=1, edge_count=0, singleton pair statistics=null.
15. `net_income` — size=1, edge_count=0, singleton pair statistics=null.
16. `net_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
17. `net_margin` — size=1, edge_count=0, singleton pair statistics=null.
18. `operating_income_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
19. `pb_ratio` — size=1, edge_count=0, singleton pair statistics=null.
20. `pe_ratio` — size=1, edge_count=0, singleton pair statistics=null.
21. `price_adjclose_t` — size=1, edge_count=0, singleton pair statistics=null.
22. `price_drawdown_from_3y_high_pct` — size=1, edge_count=0, singleton pair statistics=null.
23. `price_history_years_available` — size=1, edge_count=0, singleton pair statistics=null.
24. `revenue_growth_pct` — size=1, edge_count=0, singleton pair statistics=null.
25. `roa` — size=1, edge_count=0, singleton pair statistics=null.
26. `roe` — size=1, edge_count=0, singleton pair statistics=null.
27. `working_capital` — size=1, edge_count=0, singleton pair statistics=null.

#### Spectrum and effective ranks

Raw eigenvalues: `[0.004089237189356827,0.009112210612098642,0.009714601295589174,0.010138613513475073,0.016965267554094103,0.024378762371510664,0.027836368505833833,0.03702442598918671,0.04013866435611876,0.044848024260406995,0.051219864484790954,0.06069278950531055,0.07387304560836438,0.07854266015478227,0.09629079080972852,0.11058456243145129,0.13796012826340137,0.1552775111023845,0.17359981410671713,0.2250407994743915,0.2639874718408619,0.32338227166188904,0.36714137365983096,0.5598775518590191,0.6805010574755318,0.8099911387019437,0.8637314109752238,0.8918388645887775,1.1490535826943677,1.4840293781062723,2.127463523709411,2.975163103196304,4.159219476688609,6.129506722896252,10.827784930356717]`.
Post-tolerance eigenvalues: `[0.004089237189356827,0.009112210612098642,0.009714601295589174,0.010138613513475073,0.016965267554094103,0.024378762371510664,0.027836368505833833,0.03702442598918671,0.04013866435611876,0.044848024260406995,0.051219864484790954,0.06069278950531055,0.07387304560836438,0.07854266015478227,0.09629079080972852,0.11058456243145129,0.13796012826340137,0.1552775111023845,0.17359981410671713,0.2250407994743915,0.2639874718408619,0.32338227166188904,0.36714137365983096,0.5598775518590191,0.6805010574755318,0.8099911387019437,0.8637314109752238,0.8918388645887775,1.1490535826943677,1.4840293781062723,2.127463523709411,2.975163103196304,4.159219476688609,6.129506722896252,10.827784930356717]`.
lambda_max=10.827784930356717; zero_tolerance=1.0827784930356718e-07.
Participation-ratio effective dimensionality D_eff=6.364805095596244.
Roy–Vetterli spectral-entropy effective rank erank=10.195949875227726.

## Limitations and non-claims

- Descriptive feature-geometry analysis only; no model, target, or serving input is changed.
- Exact neutral-rank fill is analysis-only and is not model imputation, including for the n_obs = 0 and n_obs = 1 branches.
- Under heterogeneous missingness, no direction is guaranteed for spectral or participation-ratio effects.
- Windows differ in row universes and missingness, so cross-window metrics are not temporal evolution.
- PRIMARY-matrix exclusion does not imply feature uselessness, lack of predictive value, modeling redundancy, lack of temporal information, lack of market-context information, or feature-selection benefit.
- Support-based exclusions may remove redundancy-contributing geometry; exclusion is a construction/support limitation, not a finding about the excluded feature.
- D_eff is not claimed to be an upper or lower bound of any quantity over a larger or different feature set.
- Retrospective cohort, limited historical windows, sparse or mixed-quality source coverage, and environment-qualified reproduction remain limitations.
- No reliable predictive edge, alpha, profitability, investment value, tradable strategy, feature-selection benefit, model improvement, causal diagnosis, production validity, or deployment validity is established.
- Research support only; not investment advice.

### Interpretation firewall

- PRIMARY-matrix exclusion does not imply feature uselessness, lack of predictive value, modeling redundancy, lack of temporal information, lack of market-context information, or feature-selection benefit.
- Support-based exclusion may remove geometry that could otherwise contribute redundancy structure.
- D_eff is not claimed to be an upper or lower bound over a larger or different feature set.
- Cross-window D_eff and erank differences are not evidence of temporal geometry change.

## Reproducibility and source checksums

Byte identity is claimed only for consecutive runs in a matching Python/platform/numerical-package environment.

- `data/trusted_clean/modeling_dataset_training_2020_2025.csv` — `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`
- `data/trusted_clean/feature_engineering_report.json` — `8fdce200d6e68c487b8ea2585f1489acd8413a8eec095c740b922acc3cb73cc9`
- `data/trusted_clean/data_dictionary.md` — `d855b0f8d8bb119e68a742fb0f9574ccc0728a9598fcd85bcec6e1ad8d3322d4`
- `experiments/feature_dimensionality.py` — `df41e5c028e1fe95f27b9acc9061a86d2d1e8b51add703b515bc36472c602a9f`

- `experiments/results_dimensionality/correlation_matrix.csv` — `f2980a2ebdc2460de5be1cc7a1c2c99f85da8fc0fb7bf72089998aac7aba16d9`
- `experiments/results_dimensionality/pair_overlap.csv` — `bc84d924e6887728a16c2b8a6daf43f292326a52fcf34f34a69143ecded12092`
- `experiments/results_dimensionality/feature_missingness.csv` — `19d85b6aac1edb2c6edc2ecb220bd1d9e3b4f50d04606f71e6f3eeae87319a82`
