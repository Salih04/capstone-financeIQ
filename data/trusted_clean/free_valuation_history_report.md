# Free valuation history report

Reconstruct missing valuation columns from FREE sources (no Fintables). Research/educational only — NOT investment advice.

- Tickers: **40**  Years: 2020–2025
- Year-end price rows: **226/240** (Yahoo ok for 40 tickers)
- Shares outstanding: **missing**  → fill template `data/trusted_raw/shares_outstanding_manual_template.csv`

## Target valuation columns

| column | formula | status | usable values |
|---|---|---|---|
| market_cap | year_end_close × shares_outstanding | missing | 0 |
| pe | market_cap / net_income | missing | 0 |
| pb | market_cap / equity | missing | 0 |
| enterprise_value | market_cap + net_debt | missing | 0 |
| ev_ebitda | enterprise_value / ebitda | missing | 0 |

## Columns entering the model candidate

**none** (dependency missing)

## Rejection summary

- **market_cap**: missing_shares=240, missing_price=14

## Limitation

Shares outstanding is the binding gap: without a real per-ticker-year share count (KAP/company reports), market_cap cannot be computed and all derived ratios stay null. Yahoo provides only year-end PRICE freely, not historical shares. 2024 equity/net_debt are misaligned and were rejected, not imputed.

## ACTION REQUIRED
Provide real shares-outstanding (KAP/company reports) in `data/trusted_raw/shares_outstanding_manual.csv`, then re-run `make valuation`. Until then, valuation ratios cannot enter the model.