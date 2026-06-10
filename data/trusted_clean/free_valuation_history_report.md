# Free valuation history report

Reconstruct missing valuation columns from FREE sources (no Fintables). Research/educational only — NOT investment advice.

- Tickers: **81**  Years: 2020–2025
- Year-end price rows: **465/486** (Yahoo ok for 0 tickers)
- Shares outstanding: **manual**

## Target valuation columns

| column | formula | status | usable values |
|---|---|---|---|
| market_cap | year_end_close × shares_outstanding | accepted | 226 |
| pe | market_cap / net_income | accepted | 185 |
| pb | market_cap / equity | accepted | 226 |
| enterprise_value | market_cap + net_debt | accepted | 226 |
| ev_ebitda | enterprise_value / ebitda | accepted | 210 |

## Columns entering the model candidate

market_cap, enterprise_value, pe, pb, ev_ebitda

## Rejection summary

- **market_cap**: missing_shares=246, missing_price=21
- **pe**: non_positive_net_income=36, absurd_value=5
- **ev_ebitda**: non_positive_ebitda=9, absurd_value=7

## Limitation

Shares outstanding is the binding gap: without a real per-ticker-year share count (KAP/company reports), market_cap cannot be computed and all derived ratios stay null. Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are misaligned and were rejected, not imputed.