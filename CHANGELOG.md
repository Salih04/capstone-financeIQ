# CHANGELOG

All notable changes to FinanceIQ, most recent first.

## Unreleased

### Added
- **Centralized frontend cache layer** — `frontend/src/api/cache.js`
  (sessionStorage-backed, stale-while-revalidate, in-flight dedupe, TTL
  constants SHORT/MEDIUM/LONG), `useCachedResource` hook, and a Fable 5
  `CacheTag` chip (cached / refreshing / last-updated + force-refresh). Old
  `utils/sessionCache.js` is now a thin shim over it. Integrated into Benchmark,
  Experiments, Data Quality, Forecasting (options keyed by `target_mode`, train
  keyed by body), and Company Research Detail (per-ticker). Auth/session/token
  endpoints and `POST /research/ask` are never cached; failures never cached.
- **Public runtime diagnostic** — `GET /research/runtime-status` reports loaded
  dataset rows/tickers, company-context count, missing required files, and AI
  provider configuration without exposing secrets.
- **Repo-root path resolver helpers** — `backend/app/core/paths.py` exposes
  `get_trusted_clean_dir`, `get_public/training_modeling_dataset_path`,
  `get_company_contexts_dir`, and `assert_required_runtime_files`; research
  services resolve all data paths through this single strategy.
- **Experimental 2025 partial 2026-YTD target mode** — opt-in
  `target_mode=include_partial_2025` on `/forecasting/options` and
  `/forecasting/train`. Clearly labeled, never comparable to finalized annual
  targets, requires real `data/trusted_clean/partial_2026_ytd_returns.csv`
  (absent by default → reports unavailable, excludes 2025, no fabrication).
  Frontend: toggle, `2025*` marker, warning copy, target-mode readout.
- **Render Docker Blueprint** — `render.yaml` (Docker runtime, repo-root build
  context, Postgres + env vars). `docs/RENDER_DEPLOY.md` documents the backend
  service: Docker, Dockerfile path `backend/Dockerfile`, build context `.`, and
  `$PORT`-aware Uvicorn start command.
- **Fable 5 frontend documentation pass** — docs now describe the completed dark
  research-terminal redesign: deep ink surfaces, subtle grain, muted emerald
  signal states, oxidized copper/amber warning states, monospace data typography,
  right-side Signal Readout panels, and persistent research-only caveats.
- **Page concepts documented** — dashboard weak-signal overview, Research Agent
  query instrument, Companies research map, Experiments seismograph, Score
  Explorer dissection table, Data Quality specimen archive, Benchmark tide chart,
  and Forecasting signal tuner.
- **Secondary caveat strips documented** — CompanyPage, ComparePage,
  ScoreResultPage, CompanyResearchDetailPage, and DataHealthPage use the shared
  TerminalFx caveat grammar:
  `● [page context] · Research only · Not investment advice`.

### Changed
- Deployment docs now describe the migrated folder layout for Render, Vercel,
  Docker Compose, and Supabase production callback URLs.
- Research Agent docs now call out the preserved `POST /research/ask` contract
  with body `{ question: "<query text>" }`, instrument-style response blocks,
  five intent selectors, restored free-text query, hybrid weights, and
  AI/fallback status.
- Frontend route documentation now reflects the current Research Terminal route
  map: `/research-agent`, `/research/companies`, `/experiments`, `/research`,
  `/data-quality`, `/benchmark`, and `/forecasting`.
- Mock/demo frontend data is documented as fallback only; real API behavior is
  described as preserved.

### Fixed
- **Backend research data not loading after login** — research and CSV-forecasting
  endpoints required `get_current_user`, but the backend could not verify the
  Supabase JWT unless `SUPABASE_JWT_SECRET` was set, so the frontend got 403 and
  pages fell back to demo data. These demo-public endpoints now use an
  `optional_user` dependency (DB-free, never 401/403). Login-gated frontend routes
  and DB-backed legacy forecasting endpoints are unchanged.
- **Render Docker path/context** — Dockerfile CMD now honors `$PORT`; `render.yaml`
  and docs pin the repo-root build context required by the Dockerfile's
  `COPY data/ experiments/ research_agent_training/`.
- Frontend page navigation keeps already-loaded Research Terminal data in a
  session cache, so returning to data-quality, experiments, research, or companies
  pages no longer resets to full loading states. The cache is now centralized in
  `frontend/src/api/cache.js` (sessionStorage, SWR, dedupe);
  `frontend/src/utils/sessionCache.js` is a backward-compatible shim. Hard refresh
  still fetches normally.

---

## [3.3.0] — 2026-06-10 — Expanded data/model/AI pipeline

### Added
- **Expanded internal training universe** — public UI remains the selected 40 BIST
  companies, while walk-forward experiments and forecasting training can use the
  validated 81-ticker internal training split.
- **Yahoo price feature layer** (`make fetch-training-prices`) — yearly price,
  return, volatility, drawdown, benchmark-relative, dividend/split, and sector
  metadata fields are collected into raw CSVs and converted into leakage-safe
  year-T features.
- **Pipeline audit and feature reports** — `make data-audit` writes
  `pipeline_audit_report.*`; feature engineering writes
  `feature_engineering_report.*` with accepted/rejected feature rationale.
- **Full research-agent pipeline** — `make full-research-agent` now runs price
  collection, valuation, dataset build, pilot integration, validation, splitting,
  contexts, audit, experiments, and tests in order.
- **AI availability diagnostics** — `/research/ai-status` reports configured
  provider/model status and returns structured "AI not configured" responses when
  keys are absent.

### Changed
- Modeling-ready training data is now 403 rows / 81 tickers / 321 target rows;
  public inference data stays 240 rows / 40 tickers / 200 target rows.
- Validated model feature count is now 40 after leakage-safe price and benchmark
  features are added.
- Walk-forward experiments compare baseline ranking, linear/ridge/lasso/elastic
  net, random forest, gradient boosting, and robust rank aggregation where
  dependencies are available.

### Notes
- Honest finding remains conservative: overall Spearman improved only from about
  0.007 to about 0.042 and remains weak/unstable. ML still does not establish a
  reliable predictive edge.

---

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
  financials. No Fintables Pro. **27 → 32 features** once shares are supplied
  (later expanded to 40 in 3.3.0).
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
- Honest finding at this stage: model signal remained weak/unstable on the public
  40-stock universe. The deliverable is a rigorous, transparent pipeline + honest
  negative result, not a trading-edge claim.

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
    Dark research terminal style. Research support only. Clearly experimental.
- **Universe split + public/training separation** — `make split-datasets` produces
  `modeling_dataset_public_2020_2025.csv` (frontend, inference) and
  `modeling_dataset_training_2020_2025.csv` (experiments, walk-forward only).
  Config: `data/config/universe_public_40.csv` + `data/config/universe_training_bist100.csv`.
- **RAG context layer** — `make build-company-contexts` generates structured JSON per
  ticker/year (`data/trusted_clean/company_contexts/`). Research agent injects pre-built
  context into LLM prompt instead of computing live.
- **BIST100 expansion investigation** — confirmed Yahoo Chart is price/return-only (no IS/BS).
  No KAP/Fintables/Finnet adapter existed at this stage. Delivered:
  - `scripts/data_collection/collect_bist100_financials_yfinance.py`: yfinance collector
    stub, clearly marked unofficial, rate-limited, banks flagged, never fabricates.
  - `data/trusted_raw/financials/bist100_expansion_template.csv`: manual import spec
    for KAP/Fintables/TradingView export.
  - `data/trusted_clean/bist100_expansion_report.md`: full investigation report.
  - `make collect-bist100-financials` Makefile target.
  - Training tickers remained = 40 in this release; superseded by the verified
    81-ticker internal training split in 3.3.0.

### Fixed
- Forecasting page: all buttons now functional without XLSX import or DB population.
- `run_forecast` score crash on null value: guarded with `typeof item.score === 'number'`.
- `openStock()` field name corrected: `ticker` not `stock_code`.
- `experiments/run_experiments.py`: uses training dataset when available; added
  `is_public_universe`, `is_training_universe`, `universe_source` to non-feature set.
- `research_agent.py`: uses public CSV for inference; loads pre-built RAG JSON
  preferentially over live computation.

### Notes
- Training tickers were 40 in this release. Expansion is now verified in 3.3.0.
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
