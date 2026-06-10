# Data quality report

- Rows: **403**  |  Features: **40**  |  Rows with target: **321**  |  Inference-only: **82**
- Benchmark available: **True**
- Valid for T→T+1 modeling: **True**

## Rows by year

| year | rows | tickers | target coverage |
|---|---|---|---|
| 2020 | 40 | 40 | 1.0 |
| 2021 | 41 | 41 | 1.0 |
| 2022 | 81 | 81 | 0.988 |
| 2023 | 81 | 81 | 0.988 |
| 2024 | 80 | 80 | 1.0 |
| 2025 | 80 | 80 | 0.0 |

## BIST100 benchmark
- Source: **yfinance**
- Target years covered: [2021, 2022, 2023, 2024, 2025]
- Return values: {2021: 24.23, 2022: 185.94, 2023: 31.96, 2024: 28.94, 2025: 12.64}
- Excess/outperform targets enabled: **True**


## Manual financial history
- Present: **False**
- Files: []
- Rows ingested: 0
- Accepted as features: []
- Overrides from snapshot: {}
- Rejected: {}
- Misaligned columns: []
- Issues: []


## Source distinction (corrected yearly vs old snapshot)
- Accepted corrected-yearly columns: ['ebitda', 'ebitda_margin', 'gross_profit', 'gross_profit_margin', 'net_income', 'net_profit_margin', 'operating_income', 'revenue', 'roa', 'roe']
- Old snapshot rejected but corrected accepted: ['ebitda', 'gross_profit', 'net_income', 'operating_income', 'revenue', 'roa', 'roe']
- Still missing / rejected valuation: ['enterprise_value', 'ev_ebitda', 'ev_sales', 'market_capitalization', 'pb', 'pe', 'peg_ratio']
- 2024 misaligned columns rejected: ['current_assets', 'ebitda_growth', 'equity', 'financial_debt_ratio', 'gross_profit_growth', 'leverage_ratio', 'long_term_liabilities', 'net_debt', 'net_income_growth', 'non_current_assets', 'operating_income_growth', 'revenue_growth', 'short_term_liabilities', 'total_assets', 'working_capital']
- 2024 balance sheet corrected: yes (40 rows)
- Leakage columns rejected: ['price', 'period_return', 'day_return', 'volume', 'return_1w', 'return_1m', 'return_3m', 'return_6m', 'return_ytd', 'return_1y', 'return_3y', 'return_5y']

> Some names (revenue, ebitda, roe, ...) appear as BOTH rejected and accepted because the OLD snapshot source repeated one value across years (rejected), while the CORRECTED yearly source genuinely changes year by year (accepted and now used by the model).

## Frozen reference columns EXCLUDED from features (unreliable snapshot)

daily_change_pct, ebitda, ebitda_margin_pct, enterprise_value, ev_ebitda, ev_sales, fcf_financing, free_cash_flow, gross_margin_pct, gross_profit, icf, market_cap, net_income, net_margin_pct, ocf, operating_income, pb, pe, peg, price, return_1m_pct, return_1w_pct, return_1y_pct, return_3m_pct, return_3y_pct, return_5y_pct, return_6m_pct, return_ytd_pct, revenue, roa_pct, roe_pct, roic_pct, volume

## Provisional feature columns (year-T, genuinely varying)

benchmark_same_year_return_pct, current_assets, current_ratio, ebitda, ebitda_growth_pct, ebitda_margin, enterprise_value, equity, ev_ebitda, financial_debt_ratio, gross_margin, gross_profit, gross_profit_growth_pct, leverage_ratio, long_term_liabilities, market_cap, net_debt, net_debt_to_ebitda, net_income, net_income_growth_pct, net_margin, non_current_assets, operating_income, operating_income_growth_pct, pb_ratio, pe_ratio, price_adjclose_t, price_data_available, price_drawdown_from_3y_high_pct, price_history_years_available, price_momentum_1y_pct, price_momentum_2y_pct, price_vs_bist100_1y_pct, revenue, revenue_growth_pct, roa, roe, short_term_liabilities, total_assets, working_capital

## Issues

None.