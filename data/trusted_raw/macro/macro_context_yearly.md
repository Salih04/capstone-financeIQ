# Macro context input provenance (R2-REGIME-01)

This hand-maintained annual table is descriptive context only. It does not define causal relationships, investment value, or regime-specific model skill. Missing observations stay null and are never interpolated or imputed. Retrieval and repository verification date: **2026-07-12**.

The identifier `observed_2020_2025_macro_period` is a date-based identifier for the single period specified by `FINANCEIQ_AGENT_TASK_QUEUE.md` and `FINANCEIQ_MODEL_VALIDITY_AUDIT.md` §8. It is not a data-derived regime classification. The inclusive assignment boundary is 2020-01-01 through 2025-12-31.

## Source catalog

| Source ID | Field | Definition and effective date | Source |
|---|---|---|---|
| `tuik_cpi_december_yoy` | `cpi_december_yoy_pct` | National December year-on-year CPI; effective date is the corresponding December 31 observation period. | Existing R2-REAL-01 input and year-specific official links in [`cpi_yearly_tr.md`](cpi_yearly_tr.md); values are validated against [`cpi_yearly_tr.csv`](cpi_yearly_tr.csv). |
| `tcmb_one_week_repo` | `policy_rate_year_end_pct` | TCMB one-week repo auction policy rate in force at calendar year-end; effective date is the latest official rate-change date on or before December 31. | [TCMB 1 Week Repo history](https://www.tcmb.gov.tr/wps/wcm/connect/en/tcmb%2Ben/main%2Bmenu/core%2Bfunctions/monetary%2Bpolicy/central%2Bbank%2Binterest%2Brates/1%2Bweek%2Brepo). |
| `yahoo_try_x_year_end` | `usdtry_year_end_try_per_usd` | Last valid Yahoo `TRY=X` close on or before calendar year-end, quoted as TRY per USD; effective date is the recorded trading `price_date`. | Existing R2-REAL-01 input [`usdtry_year_end.csv`](usdtry_year_end.csv) and its cached Yahoo chart responses under `yahoo_chart_raw/`; values and dates are validated against that input. |
| `yfinance_xu100_calendar_return` | `bist100_return_pct` | Calendar-year nominal TRY BIST100 return; period end is December 31. | Existing validated benchmark input [`../bist100_benchmark_returns.csv`](../bist100_benchmark_returns.csv) and [`../../trusted_clean/bist100_benchmark_report.json`](../../trusted_clean/bist100_benchmark_report.json); values are validated against the input CSV. |

## Policy-rate observations

| Year | Year-end rate | Effective date |
|---:|---:|---:|
| 2020 | 17.00% | 2020-12-25 |
| 2021 | 14.00% | 2021-12-17 |
| 2022 | 9.00% | 2022-11-25 |
| 2023 | 42.50% | 2023-12-22 |
| 2024 | 47.50% | 2024-12-27 |
| 2025 | 38.00% | 2025-12-12 |

The CPI, USDTRY, and BIST100 columns are a validated projection of already committed source inputs, not independently curated duplicate observations. The deterministic workflow fails if any projected value or effective date drifts from its source.
