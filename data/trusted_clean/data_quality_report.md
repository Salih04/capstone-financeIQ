# Data quality report

- Rows: **240**  |  Features: **17**  |  Rows with target: **200**  |  Inference-only: **40**
- Benchmark available: **False**
- Valid for T→T+1 modeling: **True**

## Rows by year

| year | rows | tickers | target coverage |
|---|---|---|---|
| 2020 | 40 | 40 | 1.0 |
| 2021 | 40 | 40 | 1.0 |
| 2022 | 40 | 40 | 1.0 |
| 2023 | 40 | 40 | 1.0 |
| 2024 | 40 | 40 | 1.0 |
| 2025 | 40 | 40 | 0.0 |

## Manual financial history
- Present: **False**
- Files: []
- Rows ingested: 0
- Accepted as features: []
- Overrides from snapshot: {}
- Rejected: {}
- Misaligned columns: []
- Issues: ['manual financial history missing (data/trusted_raw/financials/ empty)']

## Frozen reference columns EXCLUDED from features (unreliable snapshot)

daily_change_pct, ebitda, ebitda_margin_pct, enterprise_value, ev_ebitda, ev_sales, fcf_financing, free_cash_flow, gross_margin_pct, gross_profit, icf, market_cap, net_income, net_margin_pct, ocf, operating_income, pb, pe, peg, price, return_1m_pct, return_1w_pct, return_1y_pct, return_3m_pct, return_3y_pct, return_5y_pct, return_6m_pct, return_ytd_pct, revenue, roa_pct, roe_pct, roic_pct, volume

## Provisional feature columns (year-T, genuinely varying)

current_assets, current_ratio, ebitda_growth_pct, equity, financial_debt_ratio, gross_profit_growth_pct, leverage_ratio, long_term_liabilities, net_debt, net_debt_to_ebitda, net_income_growth_pct, non_current_assets, operating_income_growth_pct, revenue_growth_pct, short_term_liabilities, total_assets, working_capital

## Issues

None.