# Data pipeline — T → T+1 modeling dataset

> **Current state (2026-06): 40 validated features, 81-ticker training universe.**
> Full run is `make full-research-agent` (extract → benchmark → corrected yearly →
> fetch training prices → valuation → build_all → integrate training-only tickers →
> validate → experiments → split → contexts → audit → research-agent-dataset → tests).
> `make full-research` covers steps 1–8 (through experiments).
> Added since original write-up: corrected per-year income/profitability (17→27),
> free valuation reconstruction (Yahoo year-end price × manual shares →
> market_cap/P-E/P-B/EV/EV-EBITDA), leakage-safe year-T price/benchmark features,
> capital-event shares (`make shares`), 2024 balance-sheet manual correction, and
> yfinance expansion (41 training-only tickers; public UI remains 40).
> Acceptance is sparse-aware; frozen-snapshot and price/return leakage stay rejected.

Goal: study whether **year-T** financial metrics relate to **year-(T+1)**
realized stock return for BIST companies. Research/educational only — **not
investment advice.**

## Commands

```bash
make full-research-agent         # RECOMMENDED: complete pipeline (steps 1-12, see below)
make full-research               # core pipeline through experiments (steps 1-8)

# Individual steps
make extract-yearly-financials   # XLSX -> candidate manual file (validated)
make ingest-corrected-yearly     # ingest corrected income/profitability XLSX
make benchmark                   # collect BIST100 yearly returns (Yahoo)
make prices                      # fetch Yahoo year-end prices (OHLCV only, public universe)
make shares                      # expand capital-event file → per-year shares outstanding
make valuation                   # build market_cap/pe/pb/ev/ev_ebitda from prices × shares
make data                        # ingest-corrected-yearly + build_all (40-ticker base dataset)
make fetch-training-prices       # fetch Yahoo prices for full training universe (incl. pilot tickers)
make integrate-pilot-tickers     # append all training-only yfinance tickers to base dataset
make research                    # walk-forward experiments
make split-datasets              # split into public_40 + training subsets
make build-company-contexts      # generate RAG JSON per ticker/year (run after split-datasets)
make validate-universe           # print public/training counts and coverage
make data-audit                  # write pipeline_audit_report.{json,md}

# yfinance BIST100 training expansion (run BEFORE make full-research-agent to expand universe)
make collect-yfinance-bist100          # fetch yfinance financials for all bist100_candidates.csv (--missing-only)
make collect-yfinance-bist100-force    # re-fetch all candidates (ignore existing raw data)
make clean-yfinance-bist100            # clean raw → bist100_yfinance_candidate_clean.csv + report.md
make update-training-universe-yfinance # add verified tickers to universe_training_bist100.csv
```

### Full pipeline order (`make full-research-agent`)

1. `extract-yearly-financials` — XLSX → candidate
2. `benchmark` — BIST100 returns
3. `ingest-corrected-yearly` — real per-year income/profitability
4. `fetch-training-prices` — Yahoo prices for training universe (public + all training-only tickers)
5. `valuation` / `shares` — free valuation reconstruction
6. `data` / `build_all` — 40-ticker base modeling dataset
7. `integrate-pilot-tickers` — append all training-only tickers from clean financials CSV
8. `data-validate` — validate final 403-row expanded modeling dataset
9. experiments — walk-forward CV (uses training dataset)
10. `split-datasets` — training=81 tickers, public=40 tickers
11. `build-company-contexts` — RAG JSON per ticker/year
12. `data-audit` — CSV inventory/count/missingness/source report
13. `research-agent-dataset` — instruction JSONL
14. tests

### BIST100 training expansion (one-time, run before step 1 above)

```
make collect-yfinance-bist100           # 1. fetch financials for all candidates
make clean-yfinance-bist100             # 2. clean → valid rows only
make update-training-universe-yfinance  # 3. add verified tickers to training universe
make full-research-agent                # 4. full pipeline (preserves expansion)
make validate-universe                  # 5. verify counts
```

Current verified outcome: training dataset has 403 rows / 81 tickers / 321 target rows; public dataset stays 240 rows / 40 tickers / 200 target rows.

**Candidate list:** `data/config/bist100_candidates.csv` — 44 curated candidates, including banks. Banks flagged with `is_bank=true`; their revenue = net interest income and EBITDA is undefined.

**KAP cross-check recommended** before trusting any yfinance value in research decisions.

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
   ├─ price_features        → leakage-safe year-T price/momentum/benchmark-relative features
   ├─ validate              → data_quality_report.json / .md, data_dictionary.md,
   │                          feature_engineering_report.*, pipeline_audit_report.*
   ├─ split_universe        → modeling_dataset_public_2020_2025.csv (40 tickers, inference)
   │                          modeling_dataset_training_2020_2025.csv (experiments only)
   └─ build_company_contexts→ data/trusted_clean/company_contexts/{ticker}_{year}.json
                               (pre-built RAG context injected into research agent LLM prompt)
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

`make benchmark` collects BIST100 yearly returns:
1. **Yahoo Finance** XU100.IS (yfinance if installed, else the public chart JSON
   endpoint via stdlib — no key, no paid API).
2. **Manual fallback**: `data/trusted_raw/bist100_daily.csv` or
   `bist100_historical.csv` (`date,close`; also `Tarih/Şimdi`, `Tarih/Kapanış`,
   `Price/Close`; Turkish numbers `10.628,60` handled).
3. Else keep the template and report missing.

Yearly return = `(last_close(Y)/first_close(Y) - 1) * 100`. Output
`data/trusted_raw/bist100_benchmark_returns.csv` (pipeline reads it before
`data/trusted_clean/…`). When present it enables `next_year_bist100_return_pct`,
`next_year_excess_return_vs_bist100`, `next_year_outperform_bist100`. Report:
`data/trusted_clean/bist100_benchmark_report.{json,md}`. Never fabricated.

## data/raw/quarterly_fintables/

Raw Fintables **quarterly** stock exports (2020Q1–2021Q4), added for future
quarterly fundamentals work. Not yet wired into the yearly T→T+1 pipeline.

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

## Forward forecast: 2025 inference → 2026 ranking

2025 rows (`has_target=false`, `is_inference_row=true`) are the inference inputs
for the next-year forecast. `GET /forecasting/inference?year=2025` trains
finalized 2020–2024, then ranks the 40 public 2025 rows to produce the
**2026 forecast ranking** (`prediction_status="unevaluated_forward_forecast"`).
No 2026 realized return is fabricated; the ranking is unevaluated until real 2026
returns exist. `/forecasting/options` exposes `inference_years=[2025]`,
`default_prediction_year=2025`, `default_target_year=2026`.

## Experimental: 2025 partial 2026-YTD target (opt-in)

Default pipeline: 2025 is `is_inference_row` (no finalized full-year 2026 T+1
target). An optional experimental mode adds 2025 using a **partial 2026 YTD**
return — clearly labeled, never comparable to finalized annual targets, never
folded into the headline result.

Required source (absent by default — no fabrication):
`data/trusted_clean/partial_2026_ytd_returns.csv`

| column | meaning |
|---|---|
| `ticker` | public-universe ticker |
| `year` | `2025` (the feature year) |
| `target_year` | `2026` |
| `partial_ytd_return_pct` | `(latest_2026_close / 2025_year_end_close − 1) × 100`, real prices only |
| `as_of_date` | YTD cutoff date (e.g. `2026-03-31`) |
| `source` | provider (Yahoo Chart / official) |

When present, `forecasting_csv_service` merges it onto 2025's
`next_year_return_pct` for training only under `target_mode=include_partial_2025`.
When absent, `/forecasting/options?target_mode=include_partial_2025` and
`/forecasting/train` report `includes_partial_targets=false` with an
`excluded_years` reason. Finalized 2020–2024 behavior is unchanged.

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
