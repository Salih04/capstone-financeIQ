# yfinance Pilot Expansion Report

**Date:** 2026-06-10  
**Status:** Pilot integrated into TRAINING dataset only. Public dataset unchanged (40 tickers).

---

## Data Source Caveat

> ⚠️ Data sourced from **yfinance (unofficial Yahoo Finance wrapper)**.  
> This is NOT official KAP/IFRS data. Values may differ from official filings.  
> **KAP cross-check is strongly recommended** before trusting these figures for any decision.  
> Reference: [kap.borsaistanbul.com](https://kap.borsaistanbul.com)

---

## Cleaning Summary

| Metric | Value |
|---|---|
| Raw rows (from collector) | 40 |
| Rows dropped (all-empty financial core) | 4 |
| Clean rows retained | 36 |
| Tickers retained | 9 |
| Years retained | 2022, 2023, 2024, 2025 |
| Core fields all non-null | ✅ (revenue, net_income, total_assets, equity, roe, roa) |

### Rows dropped and why

| Ticker | Year | Reason |
|---|---|---|
| Various | 2021 | All-empty financial rows (yfinance coverage absent for 2021) |
| — | 2020 | No data available from yfinance for BIST stocks at FY2020 |

The raw collector produced some 2021 stub rows with all-null financials. These were dropped by the cleaning filter:
- Keep only rows where `revenue`, `net_income`, `total_assets`, `equity` are all non-null
- AND at least one of `roe`, `roa` is non-null

No values were imputed. No data was fabricated.

---

## Retained Tickers and Year Coverage

| Ticker | Company | Sector | Years Retained | yfinance Coverage | Notes |
|---|---|---|---|---|---|
| AKSA | Aksa Akrilik | Chemicals | 2022, 2023, 2024, 2025 | FY2022+ | Non-bank; comparable |
| AKSEN | Aksa Enerji | Energy | 2022, 2023, 2024, 2025 | FY2022+ | Non-bank |
| DOHOL | Doğan Holding | Conglomerate | 2022, 2023, 2024, 2025 | FY2022+ | Mixed sector |
| EKGYO | Emlak Konut GYO | Real Estate | 2022, 2023, 2024, 2025 | FY2022+ | REIT structure |
| KCHOL | Koç Holding | Conglomerate | 2022, 2023, 2024, 2025 | FY2022+ | Multi-sector |
| ODAS | Odaş Elektrik | Energy | 2022, 2023, 2024, 2025 | FY2022+ | Non-bank |
| SAHOL | Sabancı Holding | Conglomerate | 2022, 2023, 2024, 2025 | FY2022+ | Multi-sector |
| SMRTG | Smart Güneş Enerjisi | Energy | 2022, 2023, 2024, 2025 | FY2022+ | Non-bank |
| VESTL | Vestel Elektronik | Consumer Electronics | 2022, 2023, 2024, 2025 | FY2022+ | Non-bank |

### Missing years per ticker

All 9 tickers are missing FY2020 and FY2021. yfinance typically provides BIST fundamentals from FY2022 only.

---

## Return Targets

Return targets (`next_year_return_pct`) for pilot tickers are derived from **Yahoo Chart API year-end prices** (adjclose), not from the reference file `stocks_2020_2025.csv`.

| Feature year | Target year | Status |
|---|---|---|
| 2022 | 2023 | ✅ Derived from Yahoo prices (adjclose 2022→2023) |
| 2023 | 2024 | ✅ Derived from Yahoo prices (adjclose 2023→2024) |
| 2024 | 2025 | ✅ Derived from Yahoo prices (adjclose 2024→2025) |
| 2025 | 2026 | `is_inference_row=True` — no future prices available |

Cross-sectional ranks/percentiles for pilot tickers are computed within the pilot cohort only. They are NOT merged into the public_40 cross-section.

---

## Universe Impact

| Universe | Before | After |
|---|---|---|
| Public (frontend inference) | 40 tickers | **40 tickers (unchanged)** |
| Training (experiments only) | 40 tickers | **49 tickers** |
| Training-only tickers | 0 | 9 (AKSA, AKSEN, DOHOL, EKGYO, KCHOL, ODAS, SAHOL, SMRTG, VESTL) |

Pilot tickers have `is_public_universe=false` — they will **never** appear in frontend endpoints.

---

## Files

| File | Description |
|---|---|
| `data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv` | Cleaned pilot financials (36 rows × 22 cols) |
| `data/config/universe_training_bist100.csv` | Updated with 9 pilot tickers |
| `data/trusted_clean/modeling_dataset_2020_2025.csv` | Augmented with pilot rows (appended only) |
| `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | Training split — 49 tickers |
| `data/trusted_clean/modeling_dataset_public_2020_2025.csv` | Public split — 40 tickers (unchanged) |

---

## Limitations (accepted)

- FY2020 and FY2021 unavailable — only 3 training years (2022–2024) per pilot ticker
- Data from yfinance, not official KAP IFRS filings
- Cross-sectional ranks computed separately from public_40 cohort
- Banks excluded from pilot (GARAN, AKBNK, etc. have non-comparable IS structure)
- Conglomerates (KCHOL, SAHOL, DOHOL) consolidated across many sectors

*Experimental research. Not investment advice. KAP cross-check recommended.*
