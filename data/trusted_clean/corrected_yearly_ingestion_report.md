# Corrected yearly financial ingestion report

Verified per-year income/profitability history from corrected XLSX exports. Research/educational only — NOT investment advice.

- Source: `data/trusted_raw/financials_corrected_yearly` (sheet `clean_data`)
- Rows read: **240**  |  candidate rows written: **240**
- Coverage by year: {2020: 40, 2021: 40, 2022: 40, 2023: 40, 2024: 40, 2025: 40}

## Accepted columns (genuinely year-varying)

ebitda, ebitda_margin, gross_profit, gross_profit_margin, net_income, net_profit_margin, operating_income, revenue, roa, roe

## Rejected columns

day_return, period_return, price, return_1m, return_1w, return_1y, return_3m, return_3y, return_5y, return_6m, return_ytd, volume

## Frozen valuation columns (still rejected)

enterprise_value, ev_ebitda, ev_sales, market_capitalization, pb, pe, peg_ratio

## 2024 misalignment evidence (cells rejected, not imputed)

total_assets: 7 cells, current_assets: 40 cells, non_current_assets: 40 cells, short_term_liabilities: 40 cells, long_term_liabilities: 40 cells, equity: 40 cells, working_capital: 40 cells, net_debt: 40 cells, leverage_ratio: 40 cells, financial_debt_ratio: 40 cells, revenue_growth: 40 cells, gross_profit_growth: 40 cells, ebitda_growth: 40 cells, operating_income_growth: 40 cells, net_income_growth: 40 cells

## Per-column detail

| column | status | reason | frozen_tickers | misaligned_cells |
|---|---|---|---|---|
| `revenue` | accepted | - | 4 | 0 |
| `gross_profit` | accepted | - | 3 | 0 |
| `operating_income` | accepted | - | 4 | 1 |
| `ebitda` | accepted | - | 4 | 0 |
| `net_income` | accepted | - | 2 | 0 |
| `gross_profit_margin` | accepted | - | 5 | 0 |
| `ebitda_margin` | accepted | - | 4 | 0 |
| `net_profit_margin` | accepted | - | 2 | 0 |
| `roe` | accepted | - | 4 | 1 |
| `roa` | accepted | - | 2 | 0 |
| `price` | rejected | leakage_field | 40 | - |
| `period_return` | rejected | leakage_field | 0 | - |
| `day_return` | rejected | leakage_field | 40 | - |
| `volume` | rejected | leakage_field | 40 | - |
| `return_1w` | rejected | leakage_field | 40 | - |
| `return_1m` | rejected | leakage_field | 40 | - |
| `return_3m` | rejected | leakage_field | 40 | - |
| `return_6m` | rejected | leakage_field | 40 | - |
| `return_ytd` | rejected | leakage_field | 40 | - |
| `return_1y` | rejected | leakage_field | 40 | - |
| `return_3y` | rejected | leakage_field | 40 | - |
| `return_5y` | rejected | leakage_field | 40 | - |
| `pe` | rejected | frozen_snapshot | 40 | - |
| `pb` | rejected | frozen_snapshot | 40 | - |
| `ev_ebitda` | rejected | frozen_snapshot | 40 | - |
| `ev_sales` | rejected | frozen_snapshot | 38 | - |
| `peg_ratio` | rejected | frozen_snapshot | 27 | - |
| `market_capitalization` | rejected | frozen_snapshot | 40 | - |
| `enterprise_value` | rejected | frozen_snapshot | 40 | - |