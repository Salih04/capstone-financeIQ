# Data requirements & manual ingestion

The automated pipeline produces a valid T→T+1 **structure** and **real next-year
return targets**, but the year-T **fundamentals are provisional** (only the
genuinely-varying balance-sheet / leverage / growth columns from the reference
data). For real predictive modelling you must supply true historical statements.

## What is already real

- **Targets:** next-year realized return per ticker-year (from the dated
  per-year return in the reference data). 200 rows have a target; the 2025 rows
  are inference-only.
- **Universe / metadata:** 40 BIST100 tickers, `is_bist100` derived from indices.

## What you must provide for real prediction

Per company-year (one row per ticker per year), real **year-end** values:

### `data/trusted_raw/financials/<TICKER>.csv` (manual export)

Columns (leave blank if genuinely unavailable — do **not** fill with zeros):

```
ticker,year,revenue,gross_profit,operating_income,ebitda,net_income,
total_assets,current_assets,non_current_assets,short_term_liabilities,
long_term_liabilities,equity,operating_cash_flow,investing_cash_flow,
financing_cash_flow,free_cash_flow,
market_cap_at_year_end,enterprise_value_at_year_end,pe_at_year_end,
pb_at_year_end,ev_sales_at_year_end,ev_ebitda_at_year_end,
source,retrieved_at
```

Margins/ratios/growth are **derived** by `normalize_financials`, so you only need
the raw statement lines + year-end valuation. Valuation must match the year end —
never copy current multiples into past years; leave null instead.

### `data/trusted_clean/bist100_benchmark_returns.csv`

```
year,bist100_return_pct,source,notes
```
Real BIST100 yearly total returns. Template:
`bist100_benchmark_returns.template.csv`.

## Acceptable export sources

Manually export from a platform you have rights to use — Fintables, İş Yatırım,
TradingView, Matriks, Finnet, or official KAP filings. Save the raw export under
`data/trusted_raw/` with its source + retrieval date. Do not scrape aggressively
or breach any site's terms. No Finnhub, no leaked keys, no paid API unless you
configure your own.

## After providing data

```bash
make data        # re-runs build + validation; report shows new coverage
```

The validator (`data_quality_report.json`) will show which columns became real
historical (no longer frozen) and whether the dataset is valid for T→T+1
modelling.
