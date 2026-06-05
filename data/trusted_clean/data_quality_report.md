# Data quality report

- Rows: **240**  |  Features: **27**  |  Rows with target: **200**  |  Inference-only: **40**
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
- Files: ['candidate_from_yearly_snapshots.csv', 'corrected_yearly_financials_candidate.csv']
- Rows ingested: 240
- Accepted as features: ['gross_margin', 'ebitda_margin', 'net_margin', 'roe', 'roa', 'revenue', 'gross_profit', 'operating_income', 'ebitda', 'net_income']
- Overrides from snapshot: {}
- Rejected: {}
- Misaligned columns: []
- Issues: ['240 duplicate ticker-year rows across manual files']

## Frozen reference columns EXCLUDED from features (unreliable snapshot)

daily_change_pct, ebitda, ebitda_margin_pct, enterprise_value, ev_ebitda, ev_sales, fcf_financing, free_cash_flow, gross_margin_pct, gross_profit, icf, market_cap, net_income, net_margin_pct, ocf, operating_income, pb, pe, peg, price, return_1m_pct, return_1w_pct, return_1y_pct, return_3m_pct, return_3y_pct, return_5y_pct, return_6m_pct, return_ytd_pct, revenue, roa_pct, roe_pct, roic_pct, volume

## Provisional feature columns (year-T, genuinely varying)

current_assets, current_ratio, ebitda, ebitda_growth_pct, ebitda_margin, equity, financial_debt_ratio, gross_margin, gross_profit, gross_profit_growth_pct, leverage_ratio, long_term_liabilities, net_debt, net_debt_to_ebitda, net_income, net_income_growth_pct, net_margin, non_current_assets, operating_income, operating_income_growth_pct, revenue, revenue_growth_pct, roa, roe, short_term_liabilities, total_assets, working_capital

## Issues

None.