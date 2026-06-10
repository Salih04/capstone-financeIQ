# TASK_STATE.md — FinanceIQ

Last updated: 2026-06-10 (rev 4)

## Status legend
- `DONE` — shipped, tested
- `WIP` — in progress
- `TODO` — planned
- `LIMIT` — known, accepted limitation (not a bug)

---

## Capstone verdict

**The project is complete and its purpose is served.** It is an honest, leakage-safe
T→T+1 equity-research system for 40 BIST companies (2020–2025), with a full data
pipeline, a validated modeling dataset, a BIST100 benchmark, a free-data valuation
reconstruction, an explainable hybrid research agent, and a polished "Research
Terminal" frontend — all without fabricated data or paid APIs.

The one honest finding (not a failure): **the model shows no reliable predictive
edge** (mean walk-forward Spearman ≈ 0, ML does not beat a simple baseline). With
~40 stocks/year this is the correct, defensible conclusion — the contribution is a
rigorous, transparent pipeline and an honest negative result, not alpha.

| Capstone dimension | Status | Evidence |
|---|---|---|
| Trusted, no-fabrication data pipeline | DONE | `data_quality_report.*`, validation gates |
| T→T+1 modeling dataset | DONE | `modeling_dataset_2020_2025.csv`, VALID |
| Validated features | DONE | **32** (balance-sheet, growth, income/profitability, valuation) |
| BIST100 benchmark + excess/outperform targets | DONE | `benchmark_payload`, 2020–2025 |
| Free valuation reconstruction (no Fintables Pro) | DONE | Yahoo price × manual shares → market_cap, P/E, P/B, EV, EV/EBITDA |
| Capital-event shares workflow | DONE | `shares_outstanding_events.csv` → carry-forward |
| 2024 balance-sheet manual correction | DONE | `corrected_balance_sheet_2024.csv` (40 tickers) |
| Walk-forward experiments | DONE | `experiments/`, honest weak-signal verdict |
| Explainable research agent (+ optional OpenRouter/local LLM) | DONE | `/research/*`, grounded intents, never advice |
| Research Terminal frontend | DONE | dashboard, research-agent, data-quality, experiments, benchmark, companies |
| Forecasting (legacy) restored | DONE | filters union, friendly errors, re-clickable actions |
| Forecasting CSV pipeline | DONE | CSV-backed; no DB required; train→rank→explain functional |
| Universe split (public/training) | DONE | `make split-datasets`; `universe_public_40.csv` + `universe_training_bist100.csv` |
| RAG context layer | DONE | `make build-company-contexts` → per-ticker/year JSON; injected into LLM prompt |
| BIST100 expansion investigation | DONE | Yahoo=price only confirmed; yfinance collector stub + manual template delivered |
| yfinance pilot expansion (9 training-only tickers) | DONE | AKSA AKSEN DOHOL EKGYO KCHOL ODAS SAHOL SMRTG VESTL; base=276 rows/49 tickers |
| Makefile pilot-ordering fix | DONE | `full-research` now calls `fetch-training-prices` + `integrate-pilot-tickers`; `check-pilot-financials` guard fails early if clean file missing |
| BIST100 expansion preparation | DONE | `bist100_candidates.csv` (44 candidates), `clean_yfinance_candidate.py`, `update_training_universe_from_yfinance.py`, Makefile targets: collect/clean/update/validate |
| Tests | DONE | root 93 + backend 12 passing |
| Reliable predictive edge | LIMIT | weak/unstable; needs larger universe + longer history |

---

## Core data pipeline

| Task | Status | Notes |
|---|---|---|
| Yearly XLSX → clean CSV | DONE | trusted reference / target bootstrap |
| T→T+1 build (`make data`) | DONE | universe → features → returns → benchmark → manual merge → validate |
| Corrected yearly income/profitability | DONE | 17 → 27 features (revenue, margins, ROE, ROA, …) |
| Free valuation builder (`make valuation`) | DONE | 27 → 32 (market_cap, enterprise_value, pe_ratio, pb_ratio, ev_ebitda) |
| Capital-event shares (`make shares`) | DONE | events → per-year carry-forward; free-float rejected |
| 2024 balance-sheet correction | DONE | money/ratio shape-validated; overrides only 2024 |
| Sparse-aware feature acceptance | DONE | sparse-but-varying accepted; frozen/leakage rejected |
| Leakage + frozen-snapshot guards | DONE | enforced in `validate.py` / `manual_ingest.py` |
| yfinance pilot integration (`make integrate-pilot-tickers`) | DONE | appends 9 training-only tickers; guarded by `check-pilot-financials` |
| Pilot ordering in `full-research` / `full-research-agent` | DONE | `fetch-training-prices` → `integrate-pilot-tickers` wired into `full-research`; split in `full-research-agent` |
| `integrate_pilot_tickers.py` generalized | DONE | now handles any training-only tickers; warns on missing financials; fails clearly if no rows; [pilot] → [integrate] |
| `collect_bist100_financials_yfinance.py` expanded | DONE | `--candidates-csv`, `--missing-only`, `--force-refresh` flags; reads `bist100_candidates.csv` by default |

## Research agent

| Task | Status | Notes |
|---|---|---|
| Deterministic fallback (no LLM) | DONE | always works |
| OpenRouter integration | DONE | default `openai/gpt-oss-120b:free`, `OPENAI_API_KEY` accepted |
| LM Studio / Ollama legacy integration | DONE | robust JSON repair, never 500 |
| Grounded intents | DONE | benchmark outperformers, top-ranked, data-quality, valuation, diagnostics |
| Hybrid score + decision-support verdict | DONE | bounded; deterministic warnings win |
| Training prep (no training) | DONE | `research_agent_training/` generate/validate/evaluate/iterate |

## Known limitations (accepted)

| Item | Notes |
|---|---|
| No reliable predictive edge | ~40 stocks/year; weak walk-forward signal — honest result |
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

Expected: training tickers may increase toward ~80-100 (yfinance coverage-dependent). Public stays 40.
Banks (AKBNK, GARAN, ISCTR, VAKBN, YKBNK, HALKB, QNBFB, ALBRK, SKBNK) flagged — revenue = net interest income; interpret separately.
KAP cross-check recommended before claiming any result.

### Other optional items
- Quarterly fundamentals with genuine per-period variation (current quarterly exports are frozen).
- Optional: point the research agent at a fine-tuned local model (see `research_agent_training/mlx_training_plan.md`).
