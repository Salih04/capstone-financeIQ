# TASK_STATE.md — FinanceIQ

Last updated: 2026-06-10 (rev 3)

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
| yfinance pilot expansion (training) | DONE | 9 training-only tickers (AKSA, AKSEN, DOHOL, EKGYO, KCHOL, ODAS, SAHOL, SMRTG, VESTL); public_40 unchanged; `make integrate-pilot-tickers` |
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
| No reliable predictive edge | pilot brings 49 training tickers (FY2022–2024 only); signal still expected weak — honest result |
| Shares outstanding is manual | no free historical source; capital-event file required |
| 2024 vendor export misaligned | corrected via manual file; upstream fix still ideal |
| `SECRET_KEY` / CORS in compose | tighten before any external backend deployment |

## Next steps (optional, beyond capstone scope)
- KAP cross-check pilot tickers: yfinance data is unofficial; validate AKSA/AKSEN/DOHOL/EKGYO/KCHOL/ODAS/SAHOL/SMRTG/VESTL against kap.borsaistanbul.com IFRS filings.
- Re-run experiments with 49-ticker training set: `PYTHONPATH=. python experiments/run_experiments.py`. Check if walk-forward signal improves over public_40 baseline.
- Add more BIST100 tickers: run `make collect-bist100-financials --tickers <NEW>`, add to `universe_training_bist100.csv`, run `make integrate-pilot-tickers`.
- Quarterly fundamentals with genuine per-period variation (current quarterly exports are frozen).
- Optional: point the research agent at a fine-tuned local model (see `research_agent_training/mlx_training_plan.md`).
