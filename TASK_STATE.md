# TASK_STATE.md — FinanceIQ

Last updated: 2026-06-11 (rev 6)

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
| Frontend session cache | DONE | `1.frontend/src/utils/sessionCache.js`, 5-minute in-memory TTL, hard refresh still fetches |
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
| Tests | DONE | root 97 + backend 15 passing |
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
