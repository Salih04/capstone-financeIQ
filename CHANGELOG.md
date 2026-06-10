# CHANGELOG

All notable changes to FinanceIQ, most recent first.

## [3.1.0] — 2026-06 — Research Terminal + honest T→T+1 research system

### Added
- **T→T+1 modeling pipeline** (`make data` / `scripts.data_collection`) — leakage-safe
  year-T features → year-(T+1) realized return. Validated `modeling_dataset_2020_2025.csv`
  + `data_quality_report.{json,md}`; no fabrication, frozen-snapshot columns excluded.
- **Corrected yearly financials** — real per-year income/profitability (revenue,
  gross/operating income, EBITDA, net income, margins, ROE, ROA): **17 → 27 features**.
- **BIST100 benchmark** (Yahoo, free) → excess-return / outperform-BIST100 targets.
- **Free valuation builder** (`make valuation`) — reconstructs market_cap, enterprise_value,
  pe_ratio, pb_ratio, ev_ebitda from free Yahoo year-end price × manual shares × validated
  financials. No Fintables Pro. **27 → 32 features** once shares are supplied.
- **Capital-event shares workflow** (`make shares`) — record only capital CHANGES in
  `shares_outstanding_events.csv`; carried forward per year. Free-float rejected for market cap.
- **2024 balance-sheet correction** (`corrected_balance_sheet_2024.csv`) — money/ratio
  shape-validated; overrides only 2024 balance-sheet fields; recomputes P/B, EV, EV/EBITDA.
- **Research Agent** (`/research/*`, `/research-agent`) — explainable hybrid score
  (0.65·ML + 0.20·confidence + 0.15·LLM), decision-support verdict, grounded intents
  (benchmark outperformers, top-ranked, data-quality, valuation), OpenRouter support
  (`openai/gpt-oss-120b:free` default; `OPENAI_API_KEY` accepted), legacy LM Studio/Ollama
  support, robust JSON repair, and deterministic fallback. Never investment advice.
- **Research Terminal frontend** — redesigned dashboard, data-quality (source distinction),
  experiments, benchmark, companies pages; business-friendly copy.
- **AutoResearch training prep** (`research_agent_training/`) — dataset generate/validate/
  evaluate/iterate. No training, no model downloads, no paid APIs.

### Changed
- Sparse-aware manual-feature acceptance (sparse-but-varying accepted; frozen/leakage rejected).
- Walk-forward experiments report an honest verdict: no reliable predictive edge yet.
- Docker backend startup now runs Alembic before trusted data loading; legacy volumes
  without `alembic_version` are stamped once before normal upgrades.

### Fixed
- Research Agent `/ask` 500 (numpy int64 serialization); Score Explorer stale benchmark text;
  Forecasting filters (union of cohort + uploaded fundamentals) + friendly errors + re-clickable actions.
- Vercel frontend deployment docs/config clarified: set `VITE_API_URL` to a public backend
  URL or login POSTs will hit the static site and return `405 Method Not Allowed`.

### Notes
- Honest finding: model signal remains weak/unstable (~40 stocks/year). The deliverable is a
  rigorous, transparent pipeline + honest negative result, not alpha.

---

## [3.2.0] — 2026-06-10

### Added
- **CSV-backed Forecasting pipeline** — completely replaces the broken DB-dependent
  legacy path. Root cause: `WinnerCohortRow` / `QuarterlyFundamental` tables empty in
  production → dropdowns empty → all buttons broken.
  - `app/services/forecasting_csv_service.py`: `get_options`, `train_parameters`,
    `run_forecast`, `explain_ticker` — reads `modeling_dataset_public_2020_2025.csv`
    directly. Deterministic, honest, no DB required.
  - `GET /forecasting/options`, `POST /forecasting/train`, `POST /forecasting/run`,
    `GET /forecasting/explain/{ticker}` — new CSV-backed endpoints alongside legacy.
  - `ForecastingPage.jsx` rewritten: options load on mount from CSV, Step 1 derives
    feature weights, Step 2 ranks stocks, click reveals explainability panel.
    Dark research terminal style. No buy/sell signals. Clearly experimental.
- **Universe split + public/training separation** — `make split-datasets` produces
  `modeling_dataset_public_2020_2025.csv` (frontend, inference) and
  `modeling_dataset_training_2020_2025.csv` (experiments, walk-forward only).
  Config: `data/config/universe_public_40.csv` + `data/config/universe_training_bist100.csv`.
- **RAG context layer** — `make build-company-contexts` generates structured JSON per
  ticker/year (`data/trusted_clean/company_contexts/`). Research agent injects pre-built
  context into LLM prompt instead of computing live.
- **BIST100 expansion investigation** — confirmed Yahoo Chart is price/return-only (no IS/BS).
  No KAP/Fintables/Finnet adapter existed. Delivered:
  - `scripts/data_collection/collect_bist100_financials_yfinance.py`: yfinance collector
    stub, clearly marked unofficial, rate-limited, banks flagged, never fabricates.
  - `data/trusted_raw/financials/bist100_expansion_template.csv`: manual import spec
    for KAP/Fintables/TradingView export.
  - `data/trusted_clean/bist100_expansion_report.md`: full investigation report.
  - `make collect-bist100-financials` Makefile target.
  - Training tickers remain = 40; expansion not claimed.

### Fixed
- Forecasting page: all buttons now functional without XLSX import or DB population.
- `run_forecast` score crash on null value: guarded with `typeof item.score === 'number'`.
- `openStock()` field name corrected: `ticker` not `stock_code`.
- `experiments/run_experiments.py`: uses training dataset when available; added
  `is_public_universe`, `is_training_universe`, `universe_source` to non-feature set.
- `research_agent.py`: uses public CSV for inference; loads pre-built RAG JSON
  preferentially over live computation.

### Notes
- Training tickers = 40 (unchanged). New tickers need both financials AND return
  targets before `make data && make split-datasets` shows > 40.
- Walk-forward Spearman still ≈ 0 — no reliable predictive edge. Honest result.

---

## [3.0.0] — 2026-05 (commit 88b318c…35e2d0a)

### Added
- **Forecasting module** (`/forecasting`, `/forecasting/detail`) — full upload → train → predict → evaluate pipeline
  - `POST /upload-data` — import yearly BIST winner xlsx preset
  - `POST /train-model` — compute sector parameter rankings via 8-method ML ensemble (Spearman, Pearson, MI, RF, RFE, Lasso, SHAP, K-Means cluster)
  - `POST /predict` + `GET /get-stocks` — generate ranked stock list for sector/year
  - `POST /predict/evaluate` — rolling time-CV evaluation (rank stability + overlap@K)
  - `GET /predict/trends` — per-stock yearly return series
  - `GET /predict/heatmap` — sector × feature heatmap
  - `POST /get-portfolio-analysis` — corporate portfolio weak/strong split + actions
  - `GET /get-stock-detail` + `GET /get-explanation` — per-run per-stock explainability
  - `GET /predict/history` — run history
  - `GET /parameters/catalog` — 17-parameter catalog with formulas (Turkish labels)
- **Quarterly fundamentals** — `POST /fundamentals/upload-csv` parses 28-column CSV; computes 17 derived financial ratios (ROE, ROA, OCF, margins, leverage, liquidity, efficiency)
- **News page** (`/news`) — `GET /news/updates`
- **Validation Lab** (`/validation`) and **Labeling Lab** (`/labeling`)
- **Data Health** page (`/data-health`)
- **User onboarding fields** — `user_type`, `risk_level`, `investment_scope`, `sector_focus` added to `users` table; backward-compatible hotfix in `main.py`
- Risk multiplier applied to final scores (low=0.85, medium=1.0, high=1.15)
- Multiple `model_type` modes: `scoring` (default), `xgboost`, `arima`, `prophet`, `dbscan`, `gmm`
- SHAP-based explainability via `shap.TreeExplainer` (falls back to RF importances if unavailable)
- `GET /fundamentals/template` — downloadable CSV template

### Changed
- API title bumped to "Stock Scoring V3 API" version 3.0.0
- DB wait-loop on startup (15 retries × 2s) before `Base.metadata.create_all`
- Median imputation applied at xlsx import time (per-column, global median)

### Fixed (commit 35e2d0a — "Fix reliability, performance, and transparency")
- Scoring reliability: time-based train/validation splits, cross-validation enforced
- Removed leakage of future data into training features
- Evaluation metrics reported per model
- Rolling-window CV replaces static holdout

---

## [2.x] — earlier (commits fb69da0, 9a430c0, 79e6a67)

Initial clean commit. Core modules: auth, companies, financials, scoring (v1/v2), ingestion, admin, reports. Frontend with Login, Dashboard, Search, Company, ScoreResult, Compare, Reports, Admin pages.

---

## [1.x] — initial sync (commit ed4ff15)

Project scaffolded. Basic FastAPI + React skeleton, Docker Compose, Alembic setup.
