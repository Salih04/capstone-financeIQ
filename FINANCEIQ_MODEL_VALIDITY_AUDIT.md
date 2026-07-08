# FINANCEIQ_MODEL_VALIDITY_AUDIT.md

Model, data, and forecasting-claims audit. Grounded in direct file inspection on 2026-07-08 (files cited inline). Claim categories used throughout: **[implemented+verified]**, **[implemented, not verified]**, **[intended, not implemented]**, **[recommended, not implemented]**.

## 1. Current product definition

A completed capstone: a leakage-safe T→T+1 (year-to-next-year) BIST equity **research-support** system. The headline scientific result is **negative and intentional**: walk-forward Spearman IC ≈ 0, ML models do not consistently beat trivial baselines (`experiments/reports/summary.md`, `PRD.md`). It is a decision-support and methodology-demonstration tool, not a prediction engine. Nothing in the repo contradicts this framing.

## 2. Data sources and data flow **[implemented+verified]**

- Vendor yearly XLSX (`data/raw/`) → `backend/scripts/convert_trusted_xlsx.py` → `data/trusted/` (reference only; largely a frozen 2025 snapshot).
- Corrected yearly financials + manual shares CSV (`data/trusted_raw/`) + free Yahoo year-end prices (`scripts/fetch_yahoo_chart_prices.py`) → `scripts/data_collection/` pipeline → `data/trusted_clean/modeling_dataset_2020_2025.csv` (+ `_public_`/`_training_` splits).
- Verified this session: `make data-validate` passes — 403 rows, 40 features, 321 target rows, 82 inference-only rows, benchmark available.

## 3. Frontend / backend / data architecture **[implemented+verified]**

React/Vite frontend (21 pages, routes verified in `frontend/src/App.jsx`) → FastAPI backend (15 routers, registration verified in `backend/app/main.py:78-91`) → Postgres (`yearly_stocks`, loaded at startup) **and** direct CSV reads from `data/trusted_clean/`. The pipeline runs at repo root, independent of the backend. Two distinct scoring paths exist server-side:
- **CSV path (primary/honest)**: `forecasting_csv_service.py` — trains on the training split, ranks the public 40.
- **Legacy DB path**: `scoring_service.py` + `adaptive_weights_service.py` — DB-backed category scoring with correlation-adjusted weights. README states the frontend prefers the validated CSV path **[implemented, not verified** — frontend wiring not traced this pass**]**.

## 4. Parameter catalog **[implemented+verified, with a gap]**

- Accepted year-varying features (from `data_quality_report.md`): corrected income-statement columns (`revenue`, `ebitda`, `net_income`, `operating_income`, `gross_profit`, margins, `roa`, `roe`), balance-sheet columns (2024 fixed via shape-validated override), price-derived features (`price_momentum_1y/2y`, `price_vs_bist100_1y`, `price_drawdown_from_3y_high`), and growth ratios. 40 feature columns total.
- **Rejected**: all vendor valuation columns (`pe`, `pb`, `ev_ebitda`, `market_cap`, `enterprise_value`, …) — frozen snapshot, evidence in `frozen_column_evidence.md` (e.g. ASELS `pe_ratio` = 53.95 repeated across all years). Reconstructed valuation stays null where manual shares are missing.
- **Gap**: `data/trusted_clean/data_dictionary.md` exists but was not cross-checked against the current 40 columns this pass **[implemented, not verified]** (task DATA-02).

## 5. Forecasting / weighting / model approach

- **Walk-forward experiments** **[implemented+verified]**: `experiments/run_experiments.py` — train ≤ year T, test year T+1, splits test_2023/2024/2025; linear + tree models vs equal-weight/rank baselines; metrics MAE, RMSE, Spearman, precision@5, directional accuracy. Results committed in `experiments/leaderboard.csv`.
- **Serving-side "model"** **[implemented+verified at source level]**: `forecasting_csv_service.py` is *not* the experiment ML models. It is a deterministic, explainable heuristic: identify top-quartile returners per year, measure per-feature discrimination, normalize into weights, rank by percentile-scored weighted sum. Hardcoded `DISCLAIMER` string; no buy/sell/hold, no price targets.
- **Hybrid research-agent score** **[implemented+verified at source level]**: `0.65*ml + 0.20*confidence + 0.15*llm`, env-overridable (`research_agent.py:106-107`), with explicit penalties including `weak_backtest_spearman_near_zero (-0.20)` (`research_agent.py:591`) — the system down-weights itself for its own weak backtest. LLM is explanation-only with a deterministic fallback.
- **Adaptive weights** **[implemented, not verified]**: `adaptive_weights_service.py` scales category weights by historical return correlation. Unit-level behavior not exercised this pass.

## 6. Dataset limitations

Yearly granularity only; 2020–2025; quarterly exports frozen and excluded. Vendor valuation history unusable (frozen). Shares outstanding is manual — derived valuation is null until supplied. One benchmark (BIST100 via yfinance), TRY nominal returns during a period of extreme Turkish inflation and currency depreciation (2022 BIST100 return recorded as +185.94% — nominal, not real).

## 7. Sample-size limitations

321 target rows total; ~40 stocks per test year; 3 usable test splits. Precision@5 has granularity 0.2 — a single stock changes it by 20 points. Spearman on n=40 has a standard error near 0.16, so per-split ICs in the observed range (−0.17 to +0.22) are individually indistinguishable from zero. Any claim of model superiority from these tables would be statistically indefensible — which is exactly the conclusion the project draws.

## 8. Time-period limitations

Three test years (2023–2025), all within one extraordinary macro regime (post-2021 TRY depreciation, 2022–2024 hyperinflationary accounting). No regime diversity; nothing here generalizes to other markets or calmer periods. 2025 rows are inference-only (no realized T+1 target yet) — 82 rows correctly flagged `is_inference_row`.

## 9. Missing-data risks

Core contract (missing stays null, never imputed) is enforced in the pipeline and stated everywhere **[implemented+verified at the validation level]** — `make data-validate` passes with explicit rejected-column accounting. Serving-side, `forecasting_csv_service.py` documents that missing values reduce confidence rather than being filled **[implemented, not verified** — needs a targeted test, task DATA-03**]**. Residual risk: percentile ranking over sparse columns can silently rank a stock on very few populated features.

## 10. Overfitting risks

High by construction (40 features vs ≤ ~240 training rows per split). Mitigations present: walk-forward splits, baseline comparison, feature-stability reports (`experiments/results/feature_stability_*.csv`). The honest reading of the leaderboard is that tree models overfit badly (consistently negative IC) and nothing beats baselines reliably. Risk is contained because **no product claim depends on model skill**.

## 11. Leakage risks

The strongest part of the project. Same-year return columns rejected as features (`data_quality_report.md` lists 12 rejected leakage columns); walk-forward discipline in experiments; guards in `scripts/data_collection/validate.py` + `manual_ingest.py`; frozen-snapshot detection with per-ticker evidence. **[implemented+verified]** at the validation-gate level (gates pass); the guard *code* itself was not re-reviewed line-by-line this pass.

## 12. Metric validity risks

- **Stale hardcoded caveat**: `experiments/reports/summary.md` claims the harness is "DEGENERATE — features identical every year." That text is written unconditionally by `run_experiments.py:425-430`. Git history shows the last experiment run (2026-06-10) *postdates* the corrected-yearly ingest (2026-06-06), and the data-quality report confirms features now vary by year. So the committed metrics likely reflect partially-varying features while the report calls itself degenerate — the caveat currently **overstates** the problem. It should be made conditional on measured feature variance (task DATA-04). Until then, treat the leaderboard numbers as "weak signal on corrected data, caveat text stale."
- Returns are nominal TRY; MAE/RMSE magnitudes (e.g. 200+ on test_2025 tree models) are dominated by inflation-era dispersion and are not comparable across years.
- Directional accuracy vs a median of +35% is nearly meaningless (almost everything was "up" in nominal TRY).

## 13. Sector-comparison risks

`sector` exists as a dataset column (excluded from features) and `backend/app/services/sector_service.py` exists, but sector inference/filtering correctness was **not audited this pass** **[implemented, not verified]**. Known risks: ~40-stock universe means single-digit stocks per sector — any within-sector ranking is anecdotal; sector labels' provenance not validated. Task DATA-06 covers this.

## 14. Winner-selection risks

The serving heuristic explicitly trains on "top-quartile returners" — survivor-flavored by design and vulnerable to a handful of extreme TRY-era winners dominating feature-discrimination weights. Acceptable **only** because output is framed as an experimental ranking with a disclaimer. Any UI copy implying "these characteristics predict winners" (rather than "historically co-occurred with winners") would overclaim.

## 15. Claims that are safe to make

- "We built a leakage-safe, fully reproducible T→T+1 research pipeline with validation gates, and it detected that the vendor's historical fundamentals were a frozen snapshot." **[implemented+verified]**
- "Walk-forward evaluation over 2023–2025 shows Spearman IC ≈ 0; ML does not beat naive baselines on this data." **[implemented+verified** against committed results**]**
- "Every score is decomposed into components with caveats and data-quality evidence." **[implemented; UI-level presence spot-checked via disclaimer grep across 10 pages]**
- "Missing data is never fabricated; nulls propagate to reduced confidence." **[implemented+verified at pipeline level]**

## 16. Claims that must be avoided

- Any predictive-edge claim ("the model identifies winners", "X% accuracy at picking top stocks").
- Quoting precision@5 or per-split positive ICs as achievements (they are noise at n=40).
- Any real-money, backtested-profit, or "would have returned X%" claim — none exists in the repo.
- Production-readiness or live-deployment claims (deployment liveness is unverified).
- Presenting the serving heuristic's weights as learned model parameters with validated skill.

## 17. Recommended academically honest wording

"FinanceIQ is a decision-support research terminal for BIST industrial companies. Its contribution is methodological: a no-fabrication data pipeline that detected and quarantined unreliable vendor data, a leakage-controlled walk-forward evaluation, and a transparent negative result — on five years of yearly fundamentals for ~40–81 companies, next-year returns are not reliably predictable (IC ≈ 0). The system therefore presents explainable rankings with explicit uncertainty instead of forecasts."

## 18. Recommended UI disclaimers

Current state: "not investment advice" copy verified present in 10 page files, plus the hardcoded API `DISCLAIMER`. Recommended additions (wording-only tasks): a persistent footer/banner disclaimer on *every* authenticated page (LabelingLab, ValidationLab, Admin, Compare, ScoreResult had no grep hit — task UI-01); explicit "based on 40 companies, 2020–2025, yearly data" scope line near any ranking; "nominal TRY returns, high-inflation period" note on return charts.

## 19. Recommended fallback logic

- **Rule-based scoring**: already the primary serving path (`forecasting_csv_service.py` is deterministic) — no change needed, document it as the fallback story.
- **Explainable weights**: implemented (per-feature weights + explanations returned by the service). Keep.
- **Confidence bands / uncertainty labels**: partially present (confidence component, inference-row flagging). **[recommended, not implemented]**: show per-split IC dispersion (−0.17…+0.22) wherever an aggregate IC is displayed, and label all rankings "experimental."
- **Avoid pretending precision**: display ranks or quartiles, not decimal scores, in demo-facing views **[recommended, not implemented]**.

## 20. Minimum validation checks before demo

1. `make data-validate` → passes (verified this session).
2. `PYTHONPATH=backend python -m pytest backend/tests` → 51/51 (verified this session).
3. `PYTHONPATH=. python -m pytest tests/` → expect 95/97 with the two known stale-reference failures (verified; fix is task OPS-01).
4. Backend boots and `/research` + forecasting endpoints respond with real CSV data (not the demo fallback) — **not verified this session**; do before demo.
5. Frontend production build succeeds — **not verified** (no `node_modules` in this worktree).

## 21. Good enough for capstone demo

Yes, as-is: reproducible pipeline with gates, honest negative result displayed deliberately, explainable rankings with disclaimers, dual-suite test coverage, documented data forensics (frozen-snapshot detection is genuinely demo-worthy).

## 22. Not good enough for real investment advice

Everything. Tiny sample, one market, one macro regime, yearly frequency, nominal-TRY targets, no transaction costs, no statistical significance, IC ≈ 0. The repo itself says so; keep it that way.

## 23. Recommended next technical tasks

In priority order: OPS-01 (fix two stale test references — restores all-green), DATA-04 (make the DEGENERATE caveat conditional — the biggest remaining honesty gap), UI-01 (disclaimer coverage on remaining pages), VER-01/VER-02 (demo smoke checks + frontend build). Full sequencing in `FINANCEIQ_AGENT_TASK_QUEUE.md`.
