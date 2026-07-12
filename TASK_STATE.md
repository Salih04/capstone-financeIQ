# TASK_STATE.md — FinanceIQ

Last updated: 2026-07-12 (rev 10)

## Status legend
- `DONE` — shipped, tested
- `WIP` — in progress
- `TODO` — planned
- `LIMIT` — known, accepted limitation (not a bug)

---

## Capstone verdict

**The project is complete and its purpose is served.** It is an honest, leakage-safe
T→T+1 equity-research system for 40 public BIST companies (2020–2025), with an
81-ticker internal training universe, a full data pipeline, a validated modeling dataset, a BIST100 benchmark, a free-data valuation
reconstruction, an explainable hybrid research agent, and a polished "Research
Terminal" Fable 5 frontend — all without fabricated data or paid APIs.

The one honest finding (not a failure): **the model shows no reliable predictive
edge** (mean walk-forward Spearman remains weak/unstable; ML does not consistently beat simple baselines). This is the correct, defensible conclusion — the contribution is a
rigorous, transparent pipeline and an honest negative result, not a trading-edge
claim.

| Capstone dimension | Status | Evidence |
|---|---|---|
| Trusted, no-fabrication data pipeline | DONE | `data_quality_report.*`, validation gates |
| T→T+1 modeling dataset | DONE | `modeling_dataset_2020_2025.csv`, VALID |
| Validated features | DONE | **40** (balance-sheet, growth, income/profitability, valuation, price/benchmark year-T features) |
| BIST100 benchmark + excess/outperform targets | DONE | `benchmark_payload`, 2020–2025 |
| Free valuation reconstruction (no Fintables Pro) | DONE | Yahoo price × manual shares → market_cap, P/E, P/B, EV, EV/EBITDA |
| Capital-event shares workflow | DONE | `shares_outstanding_events.csv` → carry-forward |
| 2024 balance-sheet manual correction | DONE | `corrected_balance_sheet_2024.csv` (40 tickers) |
| Walk-forward experiments | DONE | `experiments/`, honest weak-signal verdict |
| Explainable research agent (+ optional OpenRouter/local LLM) | DONE | `/research/*`, grounded intents, never advice |
| Research Terminal frontend | DONE | Fable 5: dashboard, research-agent, companies, experiments, score explorer, data-quality, benchmark, forecasting |
| Frontend cache layer | DONE | Centralized `frontend/src/api/cache.js` (sessionStorage, SWR, dedupe, TTL SHORT/MEDIUM/LONG) + `useCachedResource` + `CacheTag`; `utils/sessionCache.js` is a shim. Never caches auth/`/research/ask`/errors; hard refresh fetches |
| Secondary page caveats | DONE | CompanyPage, ComparePage, ScoreResultPage, CompanyResearchDetailPage, DataHealthPage use TerminalFx caveat strips |
| Forecasting (legacy) restored | DONE | filters union, friendly errors, re-clickable actions |
| Forecasting CSV pipeline | DONE | CSV-backed; no DB required; train→rank→explain functional |
| Universe split (public/training) | DONE | `make split-datasets`; `universe_public_40.csv` + `universe_training_bist100.csv` |
| RAG context layer | DONE | `make build-company-contexts` → per-ticker/year JSON; injected into LLM prompt |
| BIST100 expansion investigation | DONE | Yahoo=price only confirmed; yfinance collector stub + manual template delivered |
| yfinance training expansion | DONE | 41 training-only tickers; final training dataset 403 rows / 81 tickers / 321 target rows |
| Makefile pipeline ordering fix | DONE | `fetch-training-prices` before `valuation`/`data`, then `integrate-pilot-tickers`, `data-validate`, experiments |
| BIST100 expansion preparation | DONE | `bist100_candidates.csv` (44 candidates), `clean_yfinance_candidate.py`, `update_training_universe_from_yfinance.py`, Makefile targets: collect/clean/update/validate |
| Pipeline audit + feature report | DONE | `pipeline_audit_report.*`, `feature_engineering_report.*`, feature/coverage/stability experiment CSVs |
| AI availability diagnostics | DONE | `/research/ai-status`, structured "AI not configured" response, no secret hardcoding |
| Public demo endpoints | DONE | research + CSV-forecasting use `optional_user` (DB-free, never 401/403); fixes "no data after login" |
| Runtime data diagnostic | DONE | public `GET /research/runtime-status` — rows/tickers, contexts, missing files, AI config, no secrets |
| 2026 forward forecast | DONE | public `GET /forecasting/inference?year=2025` → 40-row 2026 ranking (unevaluated); 3-stage Forecasting page (Training 2020–2024 → Prediction 2025 → 2026 ranking) |
| Experimental 2025 partial-target mode | DONE | opt-in `target_mode=include_partial_2025`; labeled non-comparable; separate from forward forecast; needs real `partial_2026_ytd_returns.csv` (absent → unavailable, no fabrication) |
| Render Docker deploy | DONE | `render.yaml` (Docker, repo-root context), `$PORT`-aware Dockerfile CMD, docs aligned |
| Private production lockdown | DONE | env-gated `require_access` (401 anon / 403 unapproved, fail-closed allowlist); docs/openapi gating; in-memory rate limit; frontend Google/signup hidden + approval gate + cache clear; security headers |
| Supabase JWKS verification | DONE | asymmetric Signing Keys (RS256/ES256) via project JWKS from `SUPABASE_URL` (cached); HS256 legacy fallback; fixes 401 for approved users |
| Verification baseline (2026-07-12) | DONE | latest R2-GOV-01 refresh: root `PYTHONPATH=. python -m pytest tests/`: 106 passed; backend `PYTHONPATH=backend python -m pytest backend/tests`: 55 passed; `make data-validate`: VALID (403 rows, 40 features, 321 target rows); VER-02 frontend `npm install`: passed/up to date (audit: 10 vulnerabilities); `npm run build`: passed; `npm run e2e`: not run — no backend available (`curl http://127.0.0.1:8000/health`: connection refused) |
| R2-REPRO-01 run manifests + one-command reproduction (2026-07-12) | DONE | `74f35efe`; registered manifests, `scripts/verify_run.py`, `make research-verify-run`, and methodology provenance guidance |
| R2-UNIV-01 universe & survivorship audit (2026-07-12) | DONE | `26448525`; `docs/universe_audit.md` and retrospective-cohort limitations |
| R2-STAT-01 permutation + bootstrap significance (2026-07-12) | DONE | `c0c5c1d9`; prediction dumps, `experiments/significance.py`, and significance reports |
| R2-STAT-02 power / minimum detectable IC (2026-07-12) | DONE | `a875bf67`; analytic and simulated power analysis in the significance report and methodology |
| R2-CONTRACT-01 Model Confidence Contract v1 + claims lint (2026-07-12) | DONE | `28ba92b2`; `model_confidence_contract.json`, `scripts/lint_claims.py`, `make claims-lint`, and backend contract test |
| R2-CONTRACT-02 MCC coverage drift + versioning (2026-07-12) | DONE (uncommitted) | v1.1.0; route-registration guard, recursive JSX scan, explicit auth exemptions, versioning procedure; root 109/109, backend 56/56, claims lint passed; commit deferred by request |
| R2-LINEAGE-01 feature passports (2026-07-12) | DONE (uncommitted) | generated `feature_passports.json` covers all 61 final-dataset columns; read-only `/research/feature-passports`; Score Explorer passport popover with modeling-vs-serving scope warning; root 111/111, backend 57/57, data VALID, frontend build and claims lint passed; commit deferred by request |
| R2-SKEPTIC-01 skeptic challenge service (2026-07-12) | DONE (uncommitted) | cached artifact-grounded six-check `/research/skeptic/{ticker}` report; retrospective-cohort, coverage, instability, lineage, power, baseline, and family-wise limitations; MCC v1.2.0; root 111/111, backend 67/67, claims lint and live ASELS/ASTOR checks passed; commit deferred by request |
| R2-AUTOPSY-01 Negative Alpha Autopsy (2026-07-12) | DONE (uncommitted) | `/autopsy` renders six artifact-backed exhibits with explicit source/limitation labels; `/research/significance/autopsy` reuses significance evidence and parses committed CSVs only; MCC v1.3.0; root 114/114, backend 69/69, frontend build and claims lint passed; live API passed, protected-page visual blocked by missing approved Supabase session; commit deferred by request |
| R2-CAL-01 confidence calibration bench (2026-07-12) | DONE (uncommitted) | deterministic current-code replay over persisted 2023–2025 predictions; hybrid confidence is dataset-state scoped and constant at 0.25 across 240 ticker-year outcomes, so calibration/monotonicity are not estimable; coverage remains separate; root 125/125, backend 69/69, claims lint passed; no tuning or service/model change; `calibration_report.{json,md}` + `calibration_plot.csv`; commit deferred by request |
| Reliable predictive edge | LIMIT | weak/unstable; needs larger universe + longer history |

---

## Core data pipeline

| Task | Status | Notes |
|---|---|---|
| Yearly XLSX → clean CSV | DONE | trusted reference / target bootstrap |
| T→T+1 build (`make data`) | DONE | universe → features → returns → benchmark → manual merge → validate |
| Corrected yearly income/profitability | DONE | revenue, margins, ROE, ROA, … |
| Free valuation builder (`make valuation`) | DONE | market_cap, enterprise_value, pe_ratio, pb_ratio, ev_ebitda |
| Leakage-safe price features | DONE | year-T adj close, 1Y/2Y momentum, drawdown, benchmark-relative return |
| Capital-event shares (`make shares`) | DONE | events → per-year carry-forward; free-float rejected |
| 2024 balance-sheet correction | DONE | money/ratio shape-validated; overrides only 2024 |
| Sparse-aware feature acceptance | DONE | sparse-but-varying accepted; frozen/leakage rejected |
| Leakage + frozen-snapshot guards | DONE | enforced in `validate.py` / `manual_ingest.py` |
| yfinance integration (`make integrate-pilot-tickers`) | DONE | appends 41 training-only tickers; guarded by `check-pilot-financials` |
| Pipeline ordering in `full-research` / `full-research-agent` | DONE | `fetch-training-prices` → `valuation` → `data` → `integrate-pilot-tickers` → `data-validate` |
| `integrate_pilot_tickers.py` generalized | DONE | now handles any training-only tickers; warns on missing financials; fails clearly if no rows; [pilot] → [integrate] |
| `collect_bist100_financials_yfinance.py` expanded | DONE | `--candidates-csv`, `--missing-only`, `--force-refresh` flags; reads `bist100_candidates.csv` by default |

## Research agent

| Task | Status | Notes |
|---|---|---|
| Deterministic fallback (no LLM) | DONE | always works |
| OpenRouter integration | DONE | default `openai/gpt-oss-120b:free`, `OPENROUTER_API_KEY` / `OPENAI_API_KEY` accepted |
| LM Studio / Ollama legacy integration | DONE | robust JSON repair, never 500 |
| AI status endpoint | DONE | `/research/ai-status`, optional `?smoke=true`, deterministic fallback if unconfigured |
| Grounded intents | DONE | benchmark outperformers, top-ranked, data-quality, valuation, diagnostics |
| Hybrid score + decision-support verdict | DONE | bounded; deterministic warnings win |
| Training prep (no training) | DONE | `research_agent_training/` generate/validate/evaluate/iterate |

## Fable 5 frontend

The frontend is a dark BIST research terminal, not a generic dashboard. Visual
language: deep ink surfaces, subtle grain/scanlines, muted emerald signal states,
oxidized copper/amber weak-signal states, monospace data typography, tracked
caps labels, right-side Signal Readout panels where applicable, and no floating
tooltips. The interface keeps walk-forward IC ≈ 0 visible as the main research
finding.

| Page | Status | Notes |
|---|---|---|
| Dashboard `/dashboard` | DONE | Particle field / weak signal overview; "A weak signal, reported honestly."; BIST100 vs model, feature intake, data quality, visible IC ≈ 0 |
| AI Research Assistant `/research-agent` | DONE | Research query instrument; five intents, restored custom query, preserved `POST /research/ask`, instrument-style blocks, hybrid weights and AI/fallback status |
| Companies `/research/companies`, `/companies` | DONE | Research map; "The universe, laid flat."; X=research score, Y=coverage, sector-colored nodes, dim-on-filter, map/table toggle, mock fallback only |
| Experiments `/experiments` | DONE | Seismograph; walk-forward traces around zero, baseline honesty, flat IC trace shown as finding, mock fallback only |
| Score Explorer `/research` | DONE | Dissection table; composite diagnostic score unfolds into feature/category detail; `/research/years`, `/research/scores`, `/research/company` preserved |
| Data Quality `/data-quality` | DONE | Specimen archive; accepted/rejected feature specimens, `LEAKAGE`/`FROZEN`/`ALL-NULL` stamps, progressive hydration/cache fixes |
| Benchmark `/benchmark` | DONE | Tide chart; BIST100 vs model water bodies, 2022 +196% sign-preserving log scale, small IC markers |
| Forecasting `/forecasting` | DONE | Signal tuner; options/train/run/explain preserved, frequency-spectrum weights, inference-only amber pulse, experimental wording only |

## Known limitations (accepted)

| Item | Notes |
|---|---|
| No reliable predictive edge | small/expanded training data; weak walk-forward signal — honest result |
| Shares outstanding is manual | no free historical source; capital-event file required |
| 2024 vendor export misaligned | corrected via manual file; upstream fix still ideal |
| `SECRET_KEY` / CORS in compose | tighten before any external backend deployment |

## Next steps (optional, beyond capstone scope)

### BIST100 training expansion (pipeline ready — run locally)

```bash
pip install yfinance
make collect-yfinance-bist100           # 1. fetch financials for all 44 candidates
make clean-yfinance-bist100             # 2. drop rows with missing core fields; write report
make update-training-universe-yfinance  # 3. add verified tickers to universe_training_bist100.csv
make fetch-training-prices              # 4. fetch Yahoo prices for expanded universe
make full-research-agent                # 5. full pipeline (preserves expansion)
make validate-universe                  # 6. verify counts
```

Current verified state: training dataset 403 rows / 81 tickers / 321 target rows. Public stays 40.
Banks (AKBNK, GARAN, ISCTR, VAKBN, YKBNK, HALKB, QNBFB, ALBRK, SKBNK) flagged — revenue = net interest income; interpret separately.
KAP cross-check recommended before claiming any result.

### Other optional items
- Quarterly fundamentals with genuine per-period variation (current quarterly exports are frozen).
- Optional: point the research agent at a fine-tuned local model (see `research_agent_training/mlx_training_plan.md`).
