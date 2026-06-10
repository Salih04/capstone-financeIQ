# BIST100 Financial Data Expansion — Investigation Report

**Date:** 2026-06-10  
**Status:** Infrastructure ready. Data not yet collected. Training tickers = 40 (unchanged).

---

## 1. Current State

| Dimension | Value |
|---|---|
| Public universe tickers | 40 |
| Training universe tickers | 40 (identical — no extra BIST100 financials yet) |
| Modeling dataset rows | 240 (40 tickers × 6 years, 2020–2025) |
| Years with return targets | 2020–2024 (next-year return known) |
| Inference-only year | 2025 (no T+1 return) |

---

## 2. What Fields the Model Requires

Feature columns used by `experiments/run_experiments.py` and `forecasting_csv_service.py`:

**Income statement** (source: corrected XLSX / manual CSV):
- `revenue`, `gross_profit`, `operating_income`, `ebitda`, `net_income`

**Margins / profitability** (derived or sourced):
- `gross_margin`, `ebitda_margin`, `net_margin`, `roe`, `roa`

**Balance sheet** (source: reference data / manual CSV):
- `total_assets`, `current_assets`, `non_current_assets`
- `equity`, `working_capital`, `net_debt`
- `short_term_liabilities`, `long_term_liabilities`
- `current_ratio`, `leverage_ratio`, `financial_debt_ratio`, `net_debt_to_ebitda`

**Valuation** (source: Yahoo Chart × shares → `build_free_valuation_history`):
- `market_cap`, `enterprise_value`, `pe_ratio`, `pb_ratio`, `ev_ebitda`

**Growth** (pipeline-derived year-over-year):
- `revenue_growth_pct`, `ebitda_growth_pct`, `net_income_growth_pct`, etc.

**Return targets** (source: `stocks_2020_2025.csv` reference data):
- `next_year_return_pct`, `next_year_rank_by_return`, `next_year_return_percentile`
- These are NOT financial statement fields; they come from realized price returns.

---

## 3. Yahoo Chart: Price Only — Confirmed

The existing `scripts/fetch_yahoo_chart_prices.py` uses the Yahoo Finance
**Chart API** (`v8/finance/chart/{TICKER}.IS`) which returns:
- OHLCV (open, high, low, close, volume) — price and trading data only
- Adjusted close prices used to compute `same_year_return_pct`

**Yahoo Chart CANNOT provide:** revenue, income, equity, EBITDA, margins, or
any balance sheet / income statement field. These require a separate source.

---

## 4. Existing Adapters

| Source | Status |
|---|---|
| Yahoo Chart API (`v8/finance/chart`) | ✅ Implemented — prices/returns only |
| Corrected yearly XLSX (`financials_corrected_yearly/*.xlsx`) | ✅ Implemented — income/profitability for 40 tickers |
| Free valuation (`build_free_valuation_history.py`) | ✅ Implemented — market_cap/pe/pb via Yahoo price × shares |
| KAP (kap.borsaistanbul.com) | ❌ No adapter — official filings in PDF/HTML, no public API |
| Fintables / İş Yatırım / Finnet | ❌ No adapter — paid/private data sources |
| yfinance fundamentals | ⚠️ Collector stub created (unofficial, ~2022+ coverage) |

---

## 5. Available Free Sources for BIST100 Financial Expansion

### Option A — Manual KAP Export (Recommended, Official)

KAP (`kap.borsaistanbul.com`) hosts all IFRS filings for every listed company.
Financial statements are available in structured HTML for most filings since 2018.

**How to use:**
1. Navigate to a company's KAP page → Finansal Tablolar.
2. Select the annual (yıllık) period and year.
3. Manually extract revenue, gross profit, EBITDA, net income, equity, total assets.
4. Fill `data/trusted_raw/financials/bist100_expansion_template.csv`.
5. Run the pipeline commands below.

**Limitation:** Manual process, ~30 min per company × year.  
**Trust level:** Highest — direct from official IFRS filing.

### Option B — yfinance (Semi-Automated, Unofficial)

`scripts/data_collection/collect_bist100_financials_yfinance.py` collects IS + BS
via the unofficial yfinance wrapper.

```bash
pip install yfinance   # one-time, not in requirements.txt
PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py
# or for specific tickers:
PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py \
    --tickers VESTL KCHOL SAHOL AKSA
```

**Output:** `data/trusted_raw/financials/bist100_yfinance_candidate.csv`  
**Coverage:** Typically FY2022–FY2025. FY2020–FY2021 frequently missing for BIST stocks.  
**Trust level:** Medium — Yahoo Finance sources from filings but may differ in edge cases.  
**Do NOT run with very short delays** — respect rate limits (`--delay 3.0` recommended).

### Option C — TradingView / Fintables Manual Export

If you have a Fintables, İş Yatırım, Matriks, or TradingView account, you can
export per-company annual financials and fill the template CSV.

---

## 6. Candidate BIST100 Tickers for Expansion

The following are well-known BIST100 members not in the current public_40.
Coverage quality with yfinance noted:

| Ticker | Company | Sector | yfinance Coverage | Notes |
|---|---|---|---|---|
| VESTL | Vestel Elektronik | Consumer Electronics | FY2022+ | Non-bank; comparable metrics |
| KCHOL | Koç Holding | Conglomerate | FY2022+ | Consolidated multi-sector |
| SAHOL | Sabancı Holding | Conglomerate | FY2022+ | Consolidated multi-sector |
| AKSA | Aksa Akrilik | Chemicals | FY2022+ | Pure-play manufacturer |
| DOHOL | Doğan Holding | Media/Energy | FY2022+ | Mixed sector |
| KOZAL | Koza Altın | Mining | FY2022+ | Gold mining |
| EKGYO | Emlak Konut GYO | Real Estate | FY2022+ | REIT structure |
| GARAN | Garanti Bankası | Banking | FY2022+ | ⚠️ Bank: no gross profit/EBITDA |
| AKBNK | Akbank | Banking | FY2022+ | ⚠️ Bank: no gross profit/EBITDA |
| ISCTR | İş Bankası | Banking | FY2022+ | ⚠️ Bank: no gross profit/EBITDA |

**Banks should be handled as a separate sector** — their financial structure
(no cost of goods sold, no EBITDA) makes direct comparison with industrial
companies misleading. Consider excluding banks from the training expansion
unless the model is restructured to support bank-specific features.

---

## 7. What Is Still Missing for Training Expansion

Financial statements alone are NOT enough. To add a new ticker to the
**training** universe (not just inference), it also needs:

1. **Annual return targets** (`next_year_return_pct`) for 2020–2024.
   These come from the reference file `data/trusted/stocks_2020_2025.csv`.
   New tickers must be added to this file with their historical annual price returns,
   OR a separate return-computation script must derive them from Yahoo Chart prices
   (which already supports any BIST100 ticker via `TICKER.IS`).

2. **Update `data/config/universe_training_bist100.csv`** — add the verified
   ticker with `is_training_universe=true`.

3. **Re-run the full pipeline:**
   ```bash
   PYTHONPATH=. python -m scripts.data_collection.build_all
   PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets
   PYTHONPATH=. python scripts/build_company_contexts.py
   ```

4. **Confirm** that `modeling_dataset_training_2020_2025.csv` contains > 40 tickers.
   Until that condition is met, the expansion is NOT complete.

---

## 8. Input Specification for External Export Files

If importing from Fintables, Matriks, or manual KAP extraction, use the format
defined in:

```
data/trusted_raw/financials/bist100_expansion_template.csv
```

Key constraints:
- Grain: **one row per ticker-year**
- Currency: **Turkish Lira (TRY)** — absolute values (not thousands, not millions)
- Margins/ratios: **percentage** (e.g., gross_margin = 25.3, not 0.253)
- Blank cells for missing values, never `0`
- Include `source` (e.g., "KAP 2022 annual IFRS filing") and `retrieved_at` (YYYY-MM-DD)

Place the filled CSV in `data/trusted_raw/financials/` with any filename ending in `.csv`.
The pipeline automatically discovers and ingests all CSV files in that directory.

---

## 9. Pipeline Commands After Data Collection

```bash
# Step 1: Collect via yfinance (optional, unofficial)
pip install yfinance
PYTHONPATH=. python scripts/data_collection/collect_bist100_financials_yfinance.py

# Step 2: (Manual) Verify bist100_yfinance_candidate.csv against KAP filings.
#         Fill any missing years manually in bist100_expansion_template.csv.

# Step 3: Update universe config
# Edit data/config/universe_training_bist100.csv
# Add: VESTL,true,false,bist100_expansion (is_training_universe=true, is_public_universe=false)

# Step 4: Rebuild pipeline
PYTHONPATH=. python -m scripts.data_collection.build_all
PYTHONPATH=. python -m scripts.data_collection.split_universe_datasets
PYTHONPATH=. python scripts/build_company_contexts.py

# Step 5: Verify expansion
python -c "import pandas as pd; df=pd.read_csv('data/trusted_clean/modeling_dataset_training_2020_2025.csv'); print('Training tickers:', df.ticker.nunique())"
```

---

## 10. Confirmation: Yahoo Is Price/Return Only

Yahoo Finance Chart API (`v8/finance/chart`) provides:
- ✅ Daily OHLCV price history
- ✅ Adjusted close (for return computation)
- ❌ Income statement (revenue, EBITDA, net income)
- ❌ Balance sheet (equity, total assets)
- ❌ Profitability ratios (ROE, ROA, margins)

The `fetch_yahoo_chart_prices.py` script explicitly uses only the chart endpoint
and writes only `{ticker, year, year_end_price, adj_close, source: yahoo_chart_api}`
to `data/trusted_raw/prices/yahoo_year_end_prices.csv`. No financial statement
fields are ever fetched or written by this script.

---

*Experimental research. Not investment advice. Training tickers = 40 until expansion is verified.*
