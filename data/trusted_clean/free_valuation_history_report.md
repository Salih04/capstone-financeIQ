# Free valuation history report

Reconstruct missing valuation columns from FREE sources (no Fintables). Research/educational only — NOT investment advice.

- Tickers: **40**  Years: 2020–2025
- Year-end price rows: **226/240** (Yahoo ok for 0 tickers)
- Shares outstanding: **manual**

## Target valuation columns

| column | formula | status | usable values |
|---|---|---|---|
| market_cap | year_end_close × shares_outstanding | accepted | 208 |
| pe | market_cap / net_income | accepted | 168 |
| pb | market_cap / equity | accepted | 172 |
| enterprise_value | market_cap + net_debt | accepted | 172 |
| ev_ebitda | enterprise_value / ebitda | accepted | 159 |

## Columns entering the model candidate

market_cap, enterprise_value, pe, pb, ev_ebitda

## Rejection summary

- **market_cap**: missing_price=14, missing_shares=27
- **enterprise_value**: suspect_2024_net_debt=36
- **pe**: non_positive_net_income=35, absurd_value=5
- **pb**: suspect_2024_equity=36
- **ev_ebitda**: missing_enterprise_value=36, non_positive_ebitda=7, absurd_value=6

## Limitation

Shares outstanding is the binding gap: without a real per-ticker-year share count (KAP/company reports), market_cap cannot be computed and all derived ratios stay null. Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are misaligned and were rejected, not imputed.