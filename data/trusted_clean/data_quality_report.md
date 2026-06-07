# Data quality report

- Rows: **240**  |  Features: **32**  |  Rows with target: **200**  |  Inference-only: **40**
- Benchmark available: **True**
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

## BIST100 benchmark
- Source: **yahoo_chart_api**
- Target years covered: [2021, 2022, 2023, 2024, 2025]
- Return values: {2021: 24.23, 2022: 185.94, 2023: 31.96, 2024: 28.94, 2025: 13.05}
- Excess/outperform targets enabled: **True**


## Manual financial history
- Present: **True**
- Files: ['candidate_from_yearly_snapshots.csv', 'corrected_yearly_financials_candidate.csv', 'free_valuation_history_candidate.csv']
- Rows ingested: 240
- Accepted as features: ['gross_margin', 'ebitda_margin', 'net_margin', 'roe', 'roa', 'revenue', 'gross_profit', 'operating_income', 'ebitda', 'net_income', 'market_cap', 'enterprise_value', 'pe_ratio', 'pb_ratio', 'ev_ebitda']
- Overrides from snapshot: {}
- Rejected: {}
- Misaligned columns: []
- Source note: Multiple manual sources detected. Corrected yearly source was prioritized for income/profitability fields; legacy snapshot source only filled fields it uniquely provided. This overlap is expected, not an error.
- Issues: []


## Source distinction (corrected yearly vs old snapshot)
- Accepted corrected-yearly columns: ['ebitda', 'ebitda_margin', 'gross_profit', 'gross_profit_margin', 'net_income', 'net_profit_margin', 'operating_income', 'revenue', 'roa', 'roe']
- Old snapshot rejected but corrected accepted: ['ebitda', 'gross_profit', 'net_income', 'operating_income', 'revenue', 'roa', 'roe']
- Still missing / rejected valuation: ['enterprise_value', 'ev_ebitda', 'ev_sales', 'market_capitalization', 'pb', 'pe', 'peg_ratio']
- 2024 misaligned columns rejected: ['current_assets', 'ebitda_growth', 'equity', 'financial_debt_ratio', 'gross_profit_growth', 'leverage_ratio', 'long_term_liabilities', 'net_debt', 'net_income_growth', 'non_current_assets', 'operating_income_growth', 'revenue_growth', 'short_term_liabilities', 'total_assets', 'working_capital']
- 2024 balance sheet corrected: no (0 rows)
- Leakage columns rejected: ['price', 'period_return', 'day_return', 'volume', 'return_1w', 'return_1m', 'return_3m', 'return_6m', 'return_ytd', 'return_1y', 'return_3y', 'return_5y']

> Some names (revenue, ebitda, roe, ...) appear as BOTH rejected and accepted because the OLD snapshot source repeated one value across years (rejected), while the CORRECTED yearly source genuinely changes year by year (accepted and now used by the model).

## Frozen reference columns EXCLUDED from features (unreliable snapshot)

daily_change_pct, ebitda, ebitda_margin_pct, enterprise_value, ev_ebitda, ev_sales, fcf_financing, free_cash_flow, gross_margin_pct, gross_profit, icf, market_cap, net_income, net_margin_pct, ocf, operating_income, pb, pe, peg, price, return_1m_pct, return_1w_pct, return_1y_pct, return_3m_pct, return_3y_pct, return_5y_pct, return_6m_pct, return_ytd_pct, revenue, roa_pct, roe_pct, roic_pct, volume

## Provisional feature columns (year-T, genuinely varying)

current_assets, current_ratio, ebitda, ebitda_growth_pct, ebitda_margin, enterprise_value, equity, ev_ebitda, financial_debt_ratio, gross_margin, gross_profit, gross_profit_growth_pct, leverage_ratio, long_term_liabilities, market_cap, net_debt, net_debt_to_ebitda, net_income, net_income_growth_pct, net_margin, non_current_assets, operating_income, operating_income_growth_pct, pb_ratio, pe_ratio, revenue, revenue_growth_pct, roa, roe, short_term_liabilities, total_assets, working_capital

## Issues

None.