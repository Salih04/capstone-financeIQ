# SMRTG “Not Found” Investigation

## 1. Executive Summary

The most likely root cause is a confirmed public/training universe mismatch. The frontend research map advertises and links to `SMRTG`, but the backend research detail endpoint intentionally loads only `data/trusted_clean/modeling_dataset_public_2020_2025.csv`, which contains the public 40-company universe. `SMRTG` exists in raw yfinance data, the base modeling dataset, and the training split, but it is marked `is_public_universe=false` and is absent from the public modeling split, public model-output artifact, and prebuilt company contexts. The backend therefore returns 404, and the frontend converts that 404 into the user-visible `SMRTG not found` / `No validated record exists for this ticker.` empty state.

## 2. User-Visible Symptom

Observed screen:

- Opening `/research/companies/SMRTG` renders an empty state.
- Title: `SMRTG not found`
- Description: `No validated record exists for this ticker.`

The same symptom can occur for other non-public tickers exposed by the mock research map.

## 3. Request and Data Flow

1. `frontend/src/App.jsx:58-59` routes `/research/companies` to `CompaniesResearchPage` and `/research/companies/:ticker` to `CompanyResearchDetailPage`.
2. `frontend/src/pages/CompaniesResearchPage.jsx:1-4` re-exports `SearchPage`.
3. `frontend/src/pages/SearchPage.jsx:11-52` defines a local `COMPANIES_MOCK` list, including `SMRTG` at line 51. This page says it is a 40-ticker map, but the mock list includes tickers outside `data/config/universe_public_40.csv`.
4. `frontend/src/pages/SearchPage.jsx:247` navigates to `/research/companies/${ticker}`.
5. `frontend/src/pages/CompanyResearchDetailPage.jsx:91-144` reads `ticker` from route params and normalizes only for display with `String(ticker || '').toUpperCase()`.
6. `frontend/src/pages/CompanyResearchDetailPage.jsx:126-132` URL-encodes the raw route ticker and calls:
   - `GET /research/company/{ticker}`
   - `GET /research/company/{ticker}/score`
7. `frontend/src/api/cache.js:138-170` delegates cache misses to `api.get(path, config)`.
8. `frontend/src/api/client.js:20-22` sends requests to `VITE_API_URL` when configured, otherwise `/api`.
9. `backend/app/main.py:90-91` registers the research-agent router.
10. `backend/app/routers/research_agent.py:73-84` handles `GET /research/company/{ticker}`.
11. `backend/app/services/research_agent.py:316-328` loads the modeling dataset. Because `data/trusted_clean/modeling_dataset_public_2020_2025.csv` exists, `_public_modeling_csv()` selects it at `backend/app/services/research_agent.py:47-49`.
12. `backend/app/services/research_agent.py:497-505` uppercases the ticker, filters the loaded dataframe, and raises `KeyError` if no row exists.
13. `backend/app/routers/research_agent.py:78-79` catches that `KeyError` and returns HTTP 404.
14. `frontend/src/pages/CompanyResearchDetailPage.jsx:81-88` maps HTTP 404 to `kind: 'not_found'`.
15. `frontend/src/pages/CompanyResearchDetailPage.jsx:148-152` renders the exact empty state.

There is no database query in this failing research-detail path. The backend uses pandas/CSV artifacts, not SQLAlchemy, for `/research/company/{ticker}`.

## 4. Where the Error Is Generated

Frontend empty-state text:

- `frontend/src/pages/CompanyResearchDetailPage.jsx:144` computes display ticker `tk`.
- `frontend/src/pages/CompanyResearchDetailPage.jsx:148-152` renders:
  - title: `${tk} not found`
  - description: `No validated record exists for this ticker.`

Frontend classification of backend 404:

- `frontend/src/pages/CompanyResearchDetailPage.jsx:81-88`, `errInfo(error)`, treats `status === 404` as `kind: 'not_found'`.

Backend 404 source:

- `backend/app/routers/research_agent.py:73-84`, endpoint `company(ticker)`, calls `RA.build_company_context(ticker, state)`.
- `backend/app/services/research_agent.py:497-505`, `build_company_context()`, filters the loaded modeling dataframe by uppercase ticker and raises `KeyError(f"ticker {t} not in modeling dataset")` when empty.
- `backend/app/routers/research_agent.py:78-79` converts the `KeyError` into `HTTPException(404, str(exc))`.

Score endpoint has the same root lookup:

- `backend/app/routers/research_agent.py:87-95`, endpoint `company_score(ticker)`.
- `backend/app/services/research_agent.py:939-943`, `generate_company_insight()`, calls `build_company_context()` before scoring.

Confirmed read-only service invocation:

- `RA.load_research_state()` loaded 240 rows / 40 tickers.
- `RA.build_company_context('SMRTG')` raised `KeyError: 'ticker SMRTG not in modeling dataset'`.
- `RA.build_company_context('ASELS')` returned a valid 2025 context.

## 5. Meaning of “Validated Record”

For this page, “validated record” is frontend wording, not a database status column. The backend enforces it by loading only the public validated modeling CSV:

- `backend/app/services/research_agent.py:29-30` defines `MODELING_CSV` and `PUBLIC_MODELING_CSV`.
- `backend/app/services/research_agent.py:47-49` prefers `PUBLIC_MODELING_CSV`.
- `backend/app/services/research_agent.py:316-328` reads that CSV into `state["modeling"]`.

In the data pipeline, validation is represented by generated modeling artifacts and flags:

- `scripts/data_collection/pipeline.py:393-394` sets `has_target = next_year_return_pct.notna()` and `is_inference_row = ~has_target`.
- `scripts/data_collection/split_universe_datasets.py:75-88` adds `is_public_universe`, `is_training_universe`, and `universe_source`, then writes public/training splits.
- `scripts/data_collection/split_universe_datasets.py:90-98` validates that non-public tickers do not leak into the public dataset.
- `scripts/data_collection/validate.py:131-196` validates required columns, duplicate ticker-years, leakage, frozen-feature exclusion, target coverage, and sets `valid_for_T_to_T1_modeling`.

Important distinction:

- A row can exist in `modeling_dataset_2020_2025.csv` or `modeling_dataset_training_2020_2025.csv` and still be hidden from the research detail endpoint if `is_public_universe=false`.
- `has_target=false` does not by itself hide a public ticker. `ASELS` has a 2025 inference-only row (`has_target=false`, `is_inference_row=true`) and still loads because it is public.
- `SMRTG` has historical target rows for 2022-2024 in the training/base data, but it is hidden because it is non-public.

## 6. SMRTG Repository Evidence

Confirmed occurrences and what they prove:

- `frontend/src/pages/SearchPage.jsx:51` includes `SMRTG` in local mock map data. This creates a clickable route to a ticker the backend public endpoint does not serve.
- `frontend/src/pages/DashboardPage.jsx:31-35`, `frontend/src/pages/ForecastingPage.jsx:29-36`, and `frontend/src/pages/AIResearchAssistantPage.jsx:60-67` also contain mock/static `SMRTG` low-score examples.
- `data/config/bist100_candidates.csv:22` maps `SMRTG` to `Smart Güneş Enerjisi — solar energy`.
- `scripts/data_collection/collect_bist100_financials_yfinance.py:82-85` includes `SMRTG` in the default yfinance candidate list.
- `data/config/universe_training_bist100.csv:95` marks `SMRTG,false,true,yfinance_unofficial_pilot`.
- `data/config/universe_public_40.csv:1-41` has no `SMRTG` row.
- `data/trusted_clean/universe_split_report.json:2-17` confirms 40 public tickers, 81 training tickers, 41 training-only tickers hidden from frontend endpoints, and zero non-public leaks into public output.
- `data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv:133-136` contains clean SMRTG financial rows for 2022-2025.
- `data/trusted_clean/modeling_dataset_2020_2025.csv:145`, `:226`, `:306`, `:386` contain SMRTG rows for 2022-2025 with `is_public_universe=False`.
- `data/trusted_clean/modeling_dataset_training_2020_2025.csv:145`, `:226`, `:306`, `:386` contain SMRTG rows for 2022-2025 with `universe_source=training_only`.
- `data/trusted_clean/modeling_dataset_public_2020_2025.csv` was checked directly: 240 rows / 40 tickers, `contains_SMRTG=False`.
- `experiments/results/research_agent_model_outputs.csv` was checked directly: 40 tickers, `contains_SMRTG=False`. `experiments/run_experiments.py:157-181` writes this output from the public modeling dataset.
- `scripts/build_company_contexts.py:3-4` says contexts read public universe outputs only, and `scripts/build_company_contexts.py:210-212` filters to public tickers. No `data/trusted_clean/company_contexts/SMRTG_*.json` files exist; `ASELS_2020.json` through `ASELS_2025.json` do exist.
- `data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2022.json`, `_2023.json`, `_2024.json`, `_2025.json` exist and contain `symbol: SMRTG.IS` and `shortName: SMART GUNES ENERJISI TEK.`
- `data/trusted_raw/prices/yahoo_year_end_prices.csv:355-358` has SMRTG prices for 2022-2025.
- `data/trusted_raw/prices/yahoo_year_end_prices_report.md:25` and `:30` show SMRTG 2020 and 2021 price fetches failed with HTTP 400.
- `data/trusted_raw/shares_outstanding_manual.csv:374-379` has SMRTG rows with `missing_prior_event`.
- `data/trusted_raw/financials/free_valuation_history_candidate.csv:374-379` rejects SMRTG valuation rows for missing shares, and for 2020-2021 also missing price.

Read-only XLSX scan:

- Scanned 20 `data/**/*.xlsx` files for `SMRTG`, `SMRTG.IS`, `SMART`, `GÜNEŞ`, and `GUNES`; no hits were found. This supports that SMRTG entered through the yfinance pilot/training expansion, not the raw yearly XLSX public source files.

## 7. Comparison With a Working Ticker

Working ticker used: `ASELS`.

ASELS evidence:

- `data/config/universe_public_40.csv:4` includes `ASELS,true,true,public_40`.
- `data/trusted_clean/modeling_dataset_public_2020_2025.csv` contains six ASELS rows for 2020-2025.
- `experiments/results/research_agent_model_outputs.csv:2` contains ASELS with 2025 `ml_rank=1` and `ml_score=0.7604`.
- `data/trusted_clean/company_contexts/ASELS_2020.json` through `ASELS_2025.json` exist.
- Direct service invocation returned an ASELS context with `latest_year=2025`, `has_target=False`, `is_inference_row=True`, and `feature_count=40`.

SMRTG difference:

- SMRTG is in `universe_training_bist100.csv` as `is_public_universe=false`.
- SMRTG is absent from `modeling_dataset_public_2020_2025.csv`.
- SMRTG is absent from `research_agent_model_outputs.csv`.
- SMRTG has no prebuilt public company context JSON.
- `build_company_context('SMRTG')` raises before scoring or LLM fallback can run.

This proves the issue is not simply “low score” or `has_target=false`. ASELS has a 2025 inference-only latest row but still loads because it is public.

## 8. Root Cause

Confirmed root cause:

The frontend exposes `SMRTG` from mock/static UI data, but the backend research detail endpoint only serves tickers present in the public validated modeling dataset. SMRTG is intentionally training-only (`is_public_universe=false`) and is filtered out of the public CSV that `RA.build_company_context()` queries.

Supporting evidence:

- Frontend link source: `frontend/src/pages/SearchPage.jsx:51` and `:247`.
- Backend public-only dataset selection: `backend/app/services/research_agent.py:47-49`, `:316-328`.
- Backend 404 condition: `backend/app/services/research_agent.py:503-505`.
- Universe split rule: `scripts/data_collection/split_universe_datasets.py:84-98`.
- SMRTG config: `data/config/universe_training_bist100.csv:95`.
- Split report: `data/trusted_clean/universe_split_report.json:2-17`.

Confidence level: high. The root cause is proven from repository code and local data artifacts without needing a running database.

Cannot verify without external state:

- Whether a deployed backend has stale generated CSV artifacts or stale browser cache.
- Whether a deployed database contains a `companies` row for SMRTG. This is not needed for the failing research detail endpoint because that endpoint is CSV-backed.

## 9. Secondary Contributing Factors

- The research map is hard-coded mock data (`frontend/src/pages/SearchPage.jsx:4-9`, `:11-52`) while the backend has a real `/research/companies` endpoint (`backend/app/routers/research_agent.py:63-65`). This allows frontend/backend universe drift.
- Several non-public tickers are present in the mock map, not just SMRTG. Examples include `KCHOL`, `AKBNK`, `GARAN`, `SAHOL`, `ISCTR`, `YKBNK`, `VAKBN`, `VESTL`, `OTKAR`, `ALARK`, `KOZAL`, `EKGYO`, `AGHOL`, `DOHOL`, `IHLAS`, and `SMRTG`.
- `scripts/build_company_contexts.py:210-212` builds contexts only for public tickers, so even optional RAG enrichment cannot rescue training-only detail pages.
- `experiments/run_experiments.py:157-181` writes model outputs from the public modeling dataset, so training-only tickers do not get public detail-page ML ranks.
- SMRTG valuation data has missing shares (`data/trusted_raw/shares_outstanding_manual.csv:374-379`), causing valuation candidate rows to be rejected (`data/trusted_raw/financials/free_valuation_history_candidate.csv:374-379`). This is not the page-level root cause, but it is a data completeness issue that would matter if SMRTG were promoted to public.
- SMRTG only has yfinance financial coverage for 2022-2025, not 2020-2021. This is documented by the yfinance pilot caveats in `scripts/data_collection/integrate_pilot_tickers.py:29-35`.

## 10. Recommended Fixes

Safest to most invasive:

1. Replace or filter `COMPANIES_MOCK` in `frontend/src/pages/SearchPage.jsx` with the real `/research/companies` payload so only backend-detailable public tickers are clickable.
2. If mock data must remain, make it a strict subset of `data/config/universe_public_40.csv` and remove training-only tickers such as SMRTG.
3. Add a backend-visible reason for training-only tickers, for example a 404 detail that distinguishes “not in public universe” from “unknown ticker.”
4. Add tests or a build check that every ticker rendered by `/research/companies` UI exists in the public modeling dataset.
5. If SMRTG should appear publicly, first verify official/KAP financials and shares outstanding, then change the universe config and rerun the full pipeline, experiments, split generation, and company-context build. Do not simply flip `is_public_universe` without source validation.

## 11. Verification Plan

For the safe frontend fix:

1. Confirm `/research/companies` returns only public tickers from the backend.
2. Confirm the UI no longer renders or links to SMRTG unless SMRTG is promoted to public.
3. Open several low-score public tickers and verify detail pages load.
4. Open `/research/companies/SMRTG` directly and confirm it either remains a clear 404 or shows a specific “training-only/not public” message if that behavior is implemented.

For a future SMRTG public promotion:

1. Verify official financial and shares data for SMRTG.
2. Rebuild data: `make data`, `make valuation`, `python -m scripts.data_collection.split_universe_datasets`, `python experiments/run_experiments.py`, and `python scripts/build_company_contexts.py`.
3. Confirm `data/trusted_clean/modeling_dataset_public_2020_2025.csv` contains SMRTG rows with `is_public_universe=True`.
4. Confirm `experiments/results/research_agent_model_outputs.csv` contains SMRTG.
5. Confirm `data/trusted_clean/company_contexts/SMRTG_*.json` files exist.
6. Verify `GET /research/company/SMRTG` and `GET /research/company/SMRTG/score` return 200.
7. Verify the frontend detail page renders feature evidence and score panels.

## 12. Files Inspected

- `frontend/src/App.jsx`
- `frontend/src/pages/CompaniesResearchPage.jsx`
- `frontend/src/pages/SearchPage.jsx`
- `frontend/src/pages/CompanyResearchDetailPage.jsx`
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/pages/ForecastingPage.jsx`
- `frontend/src/pages/AIResearchAssistantPage.jsx`
- `frontend/src/api/cache.js`
- `frontend/src/api/client.js`
- `frontend/src/api/researchApi.js`
- `backend/app/main.py`
- `backend/app/routers/research_agent.py`
- `backend/app/routers/research.py`
- `backend/app/routers/companies.py`
- `backend/app/services/research_agent.py`
- `backend/app/services/forecasting_csv_service.py`
- `backend/app/services/dataset_service.py`
- `backend/app/core/paths.py`
- `backend/app/database.py`
- `backend/app/models/company.py`
- `backend/app/models/trusted.py`
- `backend/scripts/load_trusted_yearly.py`
- `scripts/build_company_contexts.py`
- `scripts/data_collection/pipeline.py`
- `scripts/data_collection/validate.py`
- `scripts/data_collection/audit_pipeline.py`
- `scripts/data_collection/split_universe_datasets.py`
- `scripts/data_collection/integrate_pilot_tickers.py`
- `scripts/data_collection/clean_yfinance_candidate.py`
- `scripts/data_collection/collect_bist100_financials_yfinance.py`
- `scripts/fetch_yahoo_chart_prices.py`
- `experiments/run_experiments.py`
- `Makefile`
- `data/config/bist100_candidates.csv`
- `data/config/universe_public_40.csv`
- `data/config/universe_training_bist100.csv`
- `data/trusted_clean/universe_split_report.json`
- `data/trusted_clean/data_quality_report.md`
- `data/trusted_clean/pipeline_audit_report.md`
- `data/trusted_clean/bist100_expansion_report.md`
- `data/trusted_clean/bist100_yfinance_pilot_report.md`
- `data/trusted_clean/modeling_dataset_2020_2025.csv`
- `data/trusted_clean/modeling_dataset_training_2020_2025.csv`
- `data/trusted_clean/modeling_dataset_public_2020_2025.csv`
- `experiments/results/research_agent_model_outputs.csv`
- `data/trusted_raw/financials/bist100_yfinance_candidate.csv`
- `data/trusted_raw/financials/bist100_yfinance_candidate_clean.csv`
- `data/trusted_raw/financials/free_valuation_history_candidate.csv`
- `data/trusted_raw/prices/yahoo_year_end_prices.csv`
- `data/trusted_raw/prices/yahoo_year_end_prices_report.md`
- `data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2022.json`
- `data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2023.json`
- `data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2024.json`
- `data/trusted_raw/prices/yahoo_chart_raw/SMRTG.IS_2025.json`
- `data/trusted_raw/shares_outstanding_manual.csv`
- `data/**/*.xlsx` read-only ticker scan
