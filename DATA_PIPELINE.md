# Data pipeline — T → T+1 modeling dataset

Goal: study whether **year-T** financial metrics relate to **year-(T+1)**
realized stock return for BIST companies. Research/educational only — **not
investment advice.**

## Commands

```bash
make extract-yearly-financials   # XLSX -> candidate manual file (validated)
make data                        # build + validate modeling dataset
make research                    # walk-forward experiments
make full-research               # all three in order
```

## Reusing the yearly Excel files (honest extraction)

`scripts/data_collection/extract_yearly_snapshots_to_manual_financials.py` reads
`20YYstocks.xlsx` (handles `(1)` duplicates — picks the richer file, reports
both), normalizes headers, maps recognized financial columns to the manual
schema, and writes `data/trusted_raw/financials/candidate_from_yearly_snapshots.csv`
plus `data/trusted_clean/yearly_snapshot_migration_report.{json,md}`.

It is **candidate** data — it then flows through the same manual-ingestion
validator. The honest outcome on the current files: the income-statement,
profitability and valuation columns (revenue, net income, margins, ROE/ROA, P/E,
P/B, EV/EBITDA, market cap) are **rejected as `frozen_across_years`** because they
are a single 2025 snapshot repeated in every file; return/price/volume columns are
**skipped as leakage/momentum** at extraction. Only the genuinely year-varying
balance-sheet columns survive (and merely override the identical base values).
**Net new features from the XLSX: 0** — proven by the report, not asserted.

So: the yearly XLSX files are safe for **returns, the ticker universe, and
balance-sheet/growth features only**. Real valuation/profitability/momentum
history must be supplied manually (see `MANUAL_FINANCIALS.md`).

Flags: `--start-year`, `--end-year`, `--tickers A,B,C`, `--force-refresh`,
`--skip-download` (default on), `--manual-only`, `--validate-only`.

## Steps

```
reference (data/trusted/stocks_2020_2025.csv, UNRELIABLE — bootstrap only)
   │
   ├─ build_universe        → data/trusted_raw/company_universe.csv  (ticker, is_bist100)
   ├─ build_fundamentals    → data/trusted_clean/company_year_fundamentals.csv
   │        keeps only columns that GENUINELY vary per year; frozen-snapshot
   │        columns (income statement, valuation, momentum) are EXCLUDED.
   ├─ build_returns         → data/trusted_clean/company_year_returns.csv
   │        same_year_return_pct (real, per-year) and next_year_return_pct
   │        (= the same ticker's return in year+1) + ranks/percentiles.
   ├─ load_benchmark        → data/trusted_clean/bist100_benchmark_returns.csv
   │        MANUAL only (template shipped). Never fabricated.
   ├─ build_modeling_dataset→ data/trusted_clean/modeling_dataset_2020_2025.csv
   └─ validate              → data_quality_report.json / .md, data_dictionary.md
```

## How returns are calculated

The reference data already contains a genuine per-year realized annual return
(`annual_return_pct`, a dated calendar-year window). We treat it as the real
target signal:

- `same_year_return_pct(T)` = realized return in year T (analysis only).
- `next_year_return_pct(T)` = realized return in year **T+1** for that ticker
  (the predictive target).
- Ranks/percentiles/top-10/20% flags are computed **within the target year's**
  cross-section.

If you later add true year-end adjusted prices, replace `build_returns` with a
price-based calculation:
`return(Y) = adj_close(last trading day Y) / adj_close(last trading day Y-1) - 1`.
Do not use future prices as features.

## Benchmark

No reliable free anonymous source is wired (Stooq now requires an API key; we do
not use leaked keys or paid APIs). Provide
`data/trusted_clean/bist100_benchmark_returns.csv`
(`year,bist100_return_pct,source,notes`) with **real** values. Until then the
benchmark-relative targets are null and the report says "benchmark missing".

## Leakage prevention

- `next_year_return_pct` and the other `next_year_*` columns are **targets**,
  never features.
- `same_year_return_pct` is **analysis-only**, never a feature.
- Frozen-snapshot columns are excluded so a 2025 value can never masquerade as a
  2020 feature.
- `target_year = year + 1`; rows where the target year has no data are
  `is_inference_row` (kept, flagged, excluded from training).
- The validator fails if any target or same-year column leaks into the feature
  set (`data_quality_report.json → issues`).

## Why the old data was unreliable

The six `*stocks.xlsx` files share one **frozen** snapshot for income-statement,
profitability, valuation and momentum fields (identical across years); only
balance-sheet, leverage, growth %, and realized return vary per year. So the old
`data/trusted/stocks_2020_2025.csv` cannot be used as year-T fundamentals. It is
kept only as the realized-return + universe bootstrap.

## What real prediction still needs

Real year-T historical income statement, profitability and valuation (P/E, P/B,
EV/EBITDA at each year end) per company. Provide them through the manual path in
`data/trusted_raw/` (see `DATA_REQUIREMENTS.md`) and extend `normalize_financials`.
