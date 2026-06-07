# Data requirements & manual ingestion

> **Update (2026-06):** Most of what this doc asked for is now ingested. Real
> per-year income/profitability are accepted (corrected yearly files); valuation is
> reconstructed for free (Yahoo year-end price × manual shares). Remaining manual
> inputs: **shares outstanding** via the capital-event file
> (`data/trusted_raw/shares_outstanding_events.csv`, run `make shares`) and **2024
> balance-sheet** fixes via `data/trusted_raw/financials/corrected_balance_sheet_2024.csv`.
> With these supplied the dataset reaches **32 validated features**.

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

### BIST100 benchmark — `data/trusted_raw/bist100_benchmark_returns.csv` (preferred) or `data/trusted_clean/bist100_benchmark_returns.csv`

```
year,bist100_return_pct
```
Real BIST100 yearly total returns, one row per year. Templates are emitted in
both locations (`*.template.csv`). When present, the pipeline adds
`next_year_bist100_return_pct`, `next_year_excess_return_vs_bist100`,
`next_year_outperform_bist100`. Never fabricated.

### Reusing the yearly Excel files

`make extract-yearly-financials` pulls any genuinely year-varying columns from
`3.Datasets/20YYstocks.xlsx` into a candidate manual file. Frozen
(snapshot) and return/momentum columns are auto-rejected — see the migration
report. This does **not** replace supplying real per-year statements above.

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
