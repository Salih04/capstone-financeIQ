# TASK_STATE.md — FinanceIQ

Last updated: 2026-07-13 (rev 14)

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
| R2-REAL-01 real-terms + USD return targets (2026-07-12) | DONE (uncommitted) | TÜİK December CPI + cached Yahoo `TRY=X` year-end quotes derive separate CPI-deflated TRY and USD-basis targets for all 321 nominal outcomes with null propagation/no imputation; isolated significance reports show random-forest pooled IC −0.156 (Bonferroni p=0.0984) real TRY and −0.150 (Bonferroni p=0.1278) USD, neither family-wise significant; two-run checksums identical; canonical datasets and nominal experiment artifacts unchanged; root 136/136, data VALID, claims lint passed; no commit by request |
| R2-REGIME-01 Regime Lens (2026-07-12) | DONE (uncommitted) | effective-dated CPI, year-end TCMB policy rate, USDTRY, and BIST100 context with source-or-null validation; deterministic `regime_context_report.{json,md}` and `/research/regime-context` feed the shared Benchmark/Experiments strip without altering chart payloads; all three test years occupy one task-defined period, so regime-conditional diagnostics are untestable and not computed; root 146/146, backend 71/71, data VALID, frontend build and claims lint passed; canonical nominal/real-terms artifacts unchanged; no commit by request |
| R2-LOOP-01 analyst-in-the-loop dissent ledger (2026-07-13) | DONE (uncommitted) | append-only `analyst_verdicts` migration; authenticated verdict writes plus deterministic read-only aggregate counts on the existing Labeling/Validation Labs; mandatory no-score-input/no-crowd-signal boundary; scoring output pin-tested identical with and without verdict rows; MCC v1.5.0; isolated Postgres migration applied through `20260713_0007`; root 149/149, backend 76/76, frontend build and claims lint passed; protected research/data artifact checksums unchanged; no commit by request |
| R2-COURT-01 Research Courtroom (2026-07-13) | DONE (uncommitted) | deterministic Bull/Bear/Skeptic/Risk evidence lenses over company contexts, feature passports, Skeptic output, quality evidence, and the corrected significance report; four citation-complete items per lens, Risk always last, no adjudication field, and missing/malformed inputs return `insufficient_data`; `POST /research/courtroom` + `/courtroom`; MCC v1.6.0; root 152/152, backend 83/83, frontend build, claims lint, and live LLM-off API passed; page visual blocked by the real Supabase auth gate without an approved session; protected research/data checksums unchanged; no commit by request |
| R2-FRICTION-01 friction simulator (2026-07-13) | DONE (uncommitted) | deterministic within-model/year rank-only top-10 nominal TRY baskets, half-L1 turnover, zero/illustrative/deliberately adverse assumed-cost controls, `friction_report.{json,md}` + `friction_plot.csv`, and an in-drawing stamped Autopsy panel; no raw score pooling, execution inference, or core model/ranking change; two-run checksums identical; MCC v1.7.0; root 168/168, backend 85/85, frontend build and claims lint passed; protected experiment/trusted-data artifacts unchanged; no commit by request |
| R2-DEMO-01 glass-box demo runbook + reproducibility quickstart (2026-07-13) | DONE (uncommitted) | shipped-route inventory and timed runbook for runtime proof, frozen-evidence specimen archive, seismograph/Instrumented Null, Negative Alpha Autopsy, deterministic Skeptic/Courtroom, explicit fallback branches, and a rehearsed MCC-CLAIM-001 failure/revert finale; README adds the three-command manifest quickstart; smoke and live read-only ASELS APIs passed after rebuilding stale local containers; root 168/168, backend 85/85, frontend build and claims lint passed; visual protected-route verification blocked at `/login` because the frontend container lacks `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`; `make research-verify-run` blocked honestly on changed `experiments/run_experiments.py` and `Makefile` checksums; protected experiment/trusted-data artifacts unchanged; no commit by request |
| Phase 3/4 frontier planning pass (2026-07-13) | DONE | docs-only at `fbab761f`; suites re-verified (root 168/168, backend 85/85, observed); new `FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md` (post-Phase-2 audit, 43-candidate register, adversarial dispositions, dependency graph, waves, verification matrix, model allocation); `FINANCEIQ_AGENT_TASK_QUEUE.md` gains the Phase-3 section (Phase-2 closure note, 20 execution packets, later backlog, dependency order); roadmap §9 strategic direction + new do-not-claim rows; TASK.md now routes the next agent to R3-GOV-01; no source, data, config, or generated artifact touched; commit left to owner |
| R3-GOV-01 post-Phase-2 truth sync (2026-07-13) | DONE (awaiting owner commit) | `docs/VERIFICATION_BASELINE.md` is the current counts ledger: root 168/168, backend 85/85, data VALID (403 rows, 40 features, 321 target rows), claims lint passed; stale operating-doc counts now cite the baseline; Phase-2 commit reconciliation appended below; docs-only, no behavior or generated-artifact change |
| R3-STAT-02 model disagreement atlas (2026-07-13) | DONE (awaiting owner commit) | isolated seedless rank-only 9×9 per-year Spearman matrices and per-ticker-year nine-model rank spread/IQR in `experiments/results_disagreement/`; source dump checksums embedded and verified; missing ranks yield explicit insufficient-data nulls; no raw cross-model score comparison, retraining, ranking/service change, or predictive-validity claim; registry ownership is `make research-disagreement` |
| R3-INF-01 leave-one-out IC influence diagnostics (2026-07-13) | DONE (awaiting owner commit) | seedless per-observation ΔIC (`loo_pooled_ic − full_pooled_ic`) for 9 models × 80 tickers × 3 years = 2160 rows in `experiments/results_influence/`; pooled IC reuses `experiments/significance.py` `spearman_ic` verbatim (pinned equal to `analyze_model` in tests); both signs and per-model top-5 |Δ| concentration reported; missing/boundary rows yield explicit insufficient-data nulls; run-twice byte-identical; canonical + `results_disagreement` + `data/trusted_clean` artifacts byte-unchanged; no retraining, ranking, service, or significance change and no mispriced-stock/opportunity/edge claim; registry ownership is `make research-influence` |
| R3-SERV-01 serving-heuristic walk-forward significance parity (2026-07-15) | WIP (implementation verified; independent Fable review PENDING) | unchanged `train_parameters()` + `run_forecast()` service path evaluated on the exact 80-ticker canonical panels for 2023–2025 with prior-year training only; pooled IC 0.050, 95% CI [-0.075,0.174], raw p=0.4427, one prespecified test outside the six-model Bonferroni family; focused + registry 32/32, root 286/286, backend 85/85, claims lint green, two-run byte identity, 291 protected files unchanged; docs lint has eight pre-existing violations outside this task; not merge-ready, review handoff pending, no commit by request |
| R3-PREREG-01 pre-registered 2026 forward-outcome protocol (2026-07-15; mandatory fixes 2026-07-16; independent re-review APPROVED 2026-07-18) | DONE (independent Fable 5 re-review APPROVED; RF-1–RF-6 resolved; merge-ready after owner commit) | frozen 40-row ranking remains sha256 `a8a8c39c…`; freeze-once is write-free when identical and refuses Git/service/data/universe/ranking/artifact drift before canonical writes; evaluator minimum n=30 with complete included/excluded membership, strict frozen-cohort/non-finite/per-row-provenance validation, nominal-TRY Yahoo adjusted-close year-end schema, retained snapshot checksums, and return recomputation; pre-frozen n=30–40 Fisher-z power context is descriptive only; requested-results manifest hashing fixed and environment-qualified; focused 70/70, registry 16/16, root 356/356, backend 85/85, claims lint green, docs lint same eight pre-existing violations, 315 protected files unchanged; `outcome_data_absent`, no metric/report/outcome file; independent Fable 5 re-review APPROVED (2026-07-18) on `local/r3-prereg-01-execution-e7299d` with RF-1–RF-6 resolved, frozen ranking checksum `a8a8c39c…` and freeze-manifest checksum `6a96408c…` unchanged, and no 2026 outcome data present during implementation or review; merge-ready after owner commit, handoff `docs/R3_PREREG_01_FABLE5_REVIEW_HANDOFF.md`, no commit or push |
| R3-UI-02 return-basis lens (2026-07-18) | WIP (implementation verified; independent Fable 5 copy review PENDING; NOT merge-ready) | read-only `backend/app/services/research/real_terms.py` + `GET /research/return-basis` compose committed per-basis significance (nominal `experiments/results/significance_report.json`; real-TRY & USD `experiments/results_real_terms/*/significance_report.json`; `comparison_report.json` conclusion + cross-check; `alternative_targets_report.json` design) with raw and adjusted p structurally inseparable and a `503` when either is absent; RF pooled IC −0.153/−0.156/−0.150 with paired raw 0.0183/0.0164/0.0213 and Bonferroni-adjusted 0.1098/0.0984/0.1278, none family-wise significant; 2022 illustration 185.94% nominal → 74.07% real (METHODOLOGY authority; 185.94%/64.27% byte-match the committed regime report, pinned) with verbatim qualifier; display-only `ReturnBasisLens` panel on `BenchmarkPage.jsx` via new `researchApi.returnBasis()` — tide chart untouched, no toggle/rebase/client-side recomputation, neutral negative-IC styling; MCC v1.7.0 → v1.8.0 (service added to scan; five version-pin tests updated); new backend test 14/14, root MCC/contract 15/15, backend 99/99, frontend build and claims lint (v1.8.0) green; `git diff --check` clean, dist gitignored, no source research artifact/chart dataset/canonical result changed; visual browser verification not performed (auth/env), recorded endpoint payload + build stand in; handoff `docs/R3_UI_02_FABLE5_REVIEW_HANDOFF.md`; **PENDING INDEPENDENT FABLE 5 COPY REVIEW**, no commit or push |
| R3-SERV-01 independent review closure (2026-07-18) | CLOSED — APPROVED (independent Fable 5 REV-01 review; implementation commit bd9aa71a, reviewed at HEAD 18514ac5) | no required fixes; service-path parity, walk-forward boundaries, outside-family raw-p framing, pre-committed conclusion, checksums, and claim safety all verified; fresh root 356/356, backend 99/99, claims lint green (MCC v1.8.0); prior WIP/PENDING row of 2026-07-15 superseded, not deleted |
| R3-UI-02 independent review closure (2026-07-18) | CLOSED — APPROVED (independent Fable 5 copy review, verified against HEAD 18514ac5 by REV-01) | both mandatory sentences byte-exact; all per-basis and illustration values full-precision source matches; raw/adjusted inseparable with 503 semantics; no recomputation/rebase/toggle/contrarian framing; MCC v1.8.0 scoped; 14/14 + 99/99 + claims lint + frontend build green; prior WIP/PENDING row of 2026-07-18 superseded, not deleted |
| R3-TGT-01 owner amendment — isolated excess-target fitting (2026-07-22) | AUTHORIZED (governance record only; no implementation accepted) | appended append-only to the R3-TGT-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md`; narrows the earlier "Do not retrain models" constraint **for this task only** to permit isolated leakage-safe walk-forward fitting of the existing frozen nine specifications against `next_year_excess_return_vs_bist100` using the frozen splits, preprocessing, hyperparameters, and seeds, with row-level dumps confined to `experiments/results_excess/**` and aggregate excess leaderboards reconstructed only from those dumps; canonical nominal models, prediction dumps, leaderboards, significance artifacts, production models, and deployment behavior remain protected and unchanged; hyperparameter search, model-family changes, result-driven specification selection, and treating nominal predictions as excess-target predictions remain forbidden; disagreement with the pre-existing read-only excess leaderboard must be reported, never patched; isolated research fitting, not production retraining; the committed no-reliable-edge conclusion is unaltered; independent review still required before any owner commit consideration; owner authorization preceded acceptance of the implementation (the implementation agent stopped, requested permission, then proceeded under the explicit owner decision), with this governance text reconciled afterward |
| R3-TGT-01 excess-return-basis significance treatment (2026-07-22) | VERIFICATION_COMPLETE / REVIEW_PENDING (uncommitted; NOT approved, NOT merge-ready) | implementation and generated outputs present in the working tree on `local/r3-tgt-01-excess-implementation`: modified `METHODOLOGY.md`, `Makefile`, `artifact_registry.json` and new `experiments/run_excess_basis.py`, `tests/test_excess_basis.py`, `experiments/results_excess/**`; implementation agent reported root suite 374 passed, data validation valid, claims lint green, and deterministic byte-identical two-run output (these figures are recorded as reported by that agent and were not re-executed in this governance pass, which did not rerun the excess experiment); independent review not yet completed; no staging, no commit, no push |
| R3-TGT-01 independent repository technical review (2026-07-22) | TECHNICAL_REVIEW_APPROVED / HUMAN_STATISTICAL_REVIEW_PENDING (uncommitted; NOT COMMIT_READY, NOT merge-ready, NOT closed) | separate-context independent repository technical review of branch `local/r3-tgt-01-excess-implementation` at base HEAD `26051a35992ea65b789c35f715d7c3aa5cae434c`, conducted in review worktree `local/r3-tgt-01-independent-review`; **technical reviewer disposition APPROVED** for repository-technical scope only (isolated excess-target fitting, row-level dumps, ticker-cluster bootstrap, within-year permutation, six-model Bonferroni family, family-symmetric reporting, generated provenance, write isolation, malformed-input refusal, deterministic regeneration, protected-artifact gate, methodology, claim safety); fresh independently observed counts: focused **134 passed**, root **490 passed**; data validation VALID (403 modeling rows, 40 features, 321 target rows, benchmark available); docs lint passed; claims lint passed against MCC v1.8.0; two isolated generations byte-identical across all seven outputs and against the implementation checkout; protected gate 351 files with zero missing, zero added, zero SHA-256 mismatches; 27-row excess leaderboard reproduced with zero mismatches at rtol=0/atol=1e-12; no ML model survives the six-model family-wise correction and no reliable predictive edge is established; the earlier 374-passed row above is preserved as historical implementation-agent evidence and is not superseded or rewritten; **implementation remains uncommitted**, **qualified independent human statistical/domain review remains mandatory**, the task is **not COMMIT_READY**, and no human-review disposition exists yet; no staging, no commit, no push |
| R3-TGT-01 human statistical/domain review (2026-07-22) | HUMAN_REVIEW_CHANGES_REQUIRED | three owner-supplied dispositions recorded append-only in the R3-TGT-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md`, with no identity, qualification, or human status asserted beyond what the owner supplied: **Review A — CHANGES_REQUIRED (binding)** on two concerns — (1) because subtracting the same annual BIST100 return from every stock within a year leaves cross-sectional outcome ranks unchanged, the within-year Spearman estimand must be described as ordinal cross-sectional ranking performance and not as benchmark-relative magnitude prediction, alpha, economic outperformance, or investment value; (2) the original independently-within-year permutation does not preserve repeated-ticker trajectories across years, so a trajectory-preserving shared-ticker permutation sensitivity must be added and corrected over the same frozen six-model family; **Review B — APPROVED with non-blocking recommendations** (disclose multiplicity across nominal, real-TRY, USD, and excess bases; document the coincident baseline results without presenting them as independent baseline diversity; disclose the limited scope of the supplied human-review package); **Review C — ADVISORY ONLY / NOT A HUMAN STATISTICAL SIGN-OFF** (ticker-cluster bootstrap appropriate, existing family-wise non-rejection defensible, no outcome-selected headline present, negative IC must not be read as inverse alpha or a contrarian signal, and the package did not independently reproduce the complete fitting and feature-construction layer) — **Review C does not satisfy the qualified-human review gate**; the conservative disposition governs and the human statistical/domain gate remains unsatisfied |
| R3-TGT-01 owner correction decision (2026-07-22) | NARROW_STATISTICAL_CORRECTION_AUTHORIZED | owner adopts the conservative CHANGES_REQUIRED disposition and authorizes a narrow correction pass limited to exactly eight items: clarify the within-year Spearman estimand as ordinal cross-sectional ranking; preserve the existing independently-within-year permutation as the original primary analysis with its exact null hypothesis documented; add a reviewer-requested post-review trajectory-preserving ticker-permutation sensitivity (one ticker permutation per iteration, same mapping applied across 2023/2024/2025, complete realized-return trajectories preserved, year-local Spearman retained, equal-year aggregation retained, 10,000 permutations, frozen seed, frozen six-model Bonferroni correction reapplied); report primary and sensitivity results side by side; designate the nominal-return family as the sole confirmatory family with real-TRY, USD, and excess-return analyses as exploratory robustness whose within-basis corrections do not control multiplicity across target bases; explain the duplicate/coincident baseline results only at the level supported by the persisted evidence; add a cautious note that predominantly negative IC signs may reflect sampling variation, feature orientation, or construction effects and are not inverse alpha, a contrarian strategy, or actionable evidence; and disclose that the compact human-review package principally supports review of the persisted prediction-to-significance layer, not standalone reproduction of feature construction and model fitting. Explicitly prohibited: modifying the trusted dataset; adding companies or years; changing splits; changing features; changing model specifications, hyperparameters, or seeds; fitting additional models; changing the six-model inferential family; deleting or silently replacing the original permutation analysis; presenting the reviewer-requested sensitivity as preregistered or prespecified; changing prediction dumps or the 27-row leaderboard; and making alpha, investment-value, recommendation, or production-validity claims. **Dataset decision: R3-TGT-01 dataset expansion is not required and is not authorized in this correction pass**; any future expansion must be a separate preregistered task, preferably adding genuinely prospective evaluation years rather than retrospectively enlarging the current task |
| R3-TGT-01 current task state (2026-07-22) | HUMAN_REVIEW_REOPENED / TECHNICAL_REREVIEW_REQUIRED (uncommitted; NOT COMMIT_READY, NOT approved, NOT merge-ready, NOT closed) | the 2026-07-22 independent repository technical approval applies **only to the pre-amendment implementation** and **must be rerun after the correction**; the task is **not COMMIT_READY**; **no final human approval exists**; dataset expansion is deferred to a separate future preregistered task; all prior R3-TGT-01 rows above are preserved unchanged as historical record and are not superseded or rewritten; this governance pass appended review and owner-decision records only — it changed no implementation, test, methodology, artifact-registry, generated-artifact, trusted-dataset, backend, or frontend file, regenerated nothing, and performed no staging, commit, or push |
| R3-TGT-01 independent repository technical rereview (2026-07-23) | TECHNICAL_REREVIEW_APPROVED (repository-technical scope only; uncommitted; NOT COMMIT_READY, NOT merge-ready, NOT closed) | fresh independent repository technical rereview of the **amended** R3-TGT-01 snapshot on branch `local/r3-tgt-01-excess-implementation` at base HEAD `26051a35992ea65b789c35f715d7c3aa5cae434c`; verdict **APPROVED** for repository-technical scope only — it **does not satisfy or replace the renewed qualified-human statistical/domain review**. Independently verified: governance records append-only and coherent; the human-review amendment stayed within authorized scope; the within-year nominal-versus-excess rank audit reproduced (2023 40 tickers/0 mismatches, 2024 40 tickers/0 mismatches, 2025 40 tickers/0 mismatches, total 120 rows/0 rank mismatches); the original independently-within-year permutation analysis preserved exactly (10,000 draws, seed 42, two-sided absolute-tail rule, Monte Carlo +1 correction, equal-year pooled IC, frozen six-model Bonferroni family, baselines outside the family); the trajectory-preserving shared-ticker permutation sensitivity technically implemented correctly (one one-to-one ticker mapping per draw, identical mapping across 2023–2025, predictions fixed, complete realized-return trajectories moved, year-local Spearman recomputed, equal-year aggregation, 10,000 draws, seed 42, six-model Bonferroni correction); exact family conclusions — primary 0 of 6 reject, trajectory sensitivity 0 of 6 reject, either analysis 0 of 6 reject; an algorithmically independent 50,000-draw direct-permutation calculation found all six sensitivity p-values statistically compatible with the persisted values and preserved the 0-of-6 family conclusion; ticker-cluster bootstrap intervals reproduced; cross-basis multiplicity, coincident-baseline, negative-IC, package-scope, and scientific-claim disclosures technically accurate; all seven governed excess artifacts reproduced deterministically; prediction dumps, leaderboard, canonical nominal artifacts, trusted dataset, and the protected 351-file boundary unchanged; validation — focused suite **165 passed**, full root suite **521 passed**, docs-lint passed, claims-lint passed, data-validation passed, two-run generation determinism passed. Non-blocking findings recorded without elevation: a previous implementation report inaccurately described `Makefile` and `artifact_registry.json` as governance appends (they are pre-existing implementation/build-governance changes, and no unauthorized amendment edit was found); focused tests do not independently pin the pre-amendment primary authority or use a different sensitivity RNG design, but the independent technical rereview supplied those checks; argsort-based permutation generation has a negligible finite-grid tie caveat; the study remains limited by 40 tickers, three evaluation years, retrospective cohort membership, low power, and one unusual macro regime. Memory-citation disclosure: prior review summaries were used solely to seed adversarial checks, no concern or qualification arises from that use because all material findings were independently reconstructed and verified from repository evidence, and memory summaries are neither statistical evidence nor a substitute for repository verification. All prior R3-TGT-01 rows above are preserved unchanged as historical record |
| R3-TGT-01 renewed human review readiness (2026-07-23) | QUALIFIED_HUMAN_REREVIEW_READY (uncommitted; NOT COMMIT_READY, NOT approved, NOT merge-ready, NOT closed) | no blocking repository-technical defect remains, so the task **may proceed to renewed qualified-human statistical/domain review**; the technical rereview approval is repository-technical only and confers no statistical, domain, or scientific approval; final human approval has **not** been received; nothing here establishes a predictive edge, alpha, investment value, or production validity |
| R3-TGT-01 current task state (2026-07-23) | FINAL_HUMAN_APPROVAL_PENDING / NOT_COMMIT_READY (uncommitted; NOT approved, NOT merge-ready, NOT closed) | the task is **not** HUMAN_REVIEW_APPROVED, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; renewed qualified-human statistical/domain review remains outstanding; this governance pass appended technical-rereview records only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, trusted-dataset, nominal-artifact, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, or push |
| R3-TGT-01 qualified-human attestation availability (2026-07-23) | QUALIFIED_HUMAN_ATTESTATION_UNAVAILABLE | a verifiable qualified-human statistical/domain attestation for R3-TGT-01 **could not be obtained**; **no AI system, repository reviewer, advisory model, owner statement, or unsigned methodological opinion is being reclassified as a qualified-human sign-off**; no reviewer identity, affiliation, credential, qualification, or signature is asserted or invented; **no human-review approval exists** |
| R3-TGT-01 owner governance amendment (2026-07-23) | HUMAN_REVIEW_GATE_WAIVED_BY_OWNER | the owner **explicitly waives the qualified-human attestation requirement for this internal repository task because it is unavailable**; the waiver is an **internal governance decision** that changes the **governance completion rule, not the scientific evidence** — no result, artifact, dataset, methodology, or claim changes; the task must **never** be described as qualified-human reviewed, human-statistician approved, externally validated, or independently human attested; **any future genuine qualified-human review must be recorded separately and must not be backdated**; the waiver establishes **no predictive edge, alpha, profitability, investment value, tradable-strategy evidence, deployment validity, or production validity**; low power, 40 tickers, three evaluation years, retrospective cohort membership, and cross-basis multiplicity limitations **remain active**; dataset expansion remains outside R3-TGT-01 and is **not required for closure**; recorded append-only in the R3-TGT-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md` |
| R3-TGT-01 replacement review standard (2026-07-23) | AI_ADVISORY_COUNCIL_AND_TECHNICAL_REVIEW_ACCEPTED | replacement completion standard accepted by the owner in place of the waived gate: (a) **independent repository technical rereview APPROVED**; (b) **multiple independent advisory statistical assessments supporting the corrected methodology**; (c) **owner methodological acceptance**; (d) **final repository commit-readiness audit**. Two further advisory dispositions recorded append-only, advisory only, neither a qualified-human attestation and neither asserting any identity or credential: **Advisory assessment D — STATISTICAL-MERITS APPROVED / NOT HUMAN SIGN-OFF** (independent verification with a different implementation, seed 7, 20,000 draws; pooled ICs reproduced; all primary and sensitivity p-values compatible within Monte Carlo uncertainty; nominal-versus-excess ranks 0 mismatches; baseline prediction values identical; both analyses retained the 0-of-6 conclusion; both original binding concerns considered statistically resolved); **Advisory assessment E — METHODOLOGICAL APPROVAL / NOT SIGNED QUALIFIED-HUMAN ATTESTATION** (revised ordinal estimand explanation resolves the first concern; shared-ticker sensitivity resolves the repeated-ticker concern; retaining the original analysis as primary is methodologically sound; the new analysis is adequately labeled non-prespecified; both six-model families yield 0-of-6 rejections; the formal human gate cannot close on that assessment alone) |
| R3-TGT-01 scientific disposition (2026-07-23) | ORIGINAL_BINDING_CONCERNS_SUBSTANTIVELY_RESOLVED | the prior HUMAN_REVIEW_CHANGES_REQUIRED disposition was substantively addressed through corrected ordinal estimand language; zero nominal-versus-excess rank mismatches across 120 evaluation rows; preservation of the original independently-within-year primary permutation; addition of the reviewer-requested trajectory-preserving shared-ticker sensitivity; symmetric six-model reporting; a separate six-model Bonferroni correction for each analysis; cross-basis multiplicity disclosure; coincident-baseline disclosure; negative-IC claim restrictions; and package-scope clarification. Independent repository technical rereview returned **APPROVED with no blocking defect**; advisory assessments independently reproduced or statistically validated the pooled IC values, primary permutation p-values, trajectory-preserving sensitivity p-values, rank invariance, baseline coincidence, and the 0-of-6 family-level conclusion under both analyses, while **explicitly stating they are not qualified-human attestations**. The owner accepts these corrections as sufficient for the internal project decision **while preserving all scientific limitations**; **this resolves review concerns, not the absence of predictive edge** |
| R3-TGT-01 current task state (2026-07-23, post-waiver) | FINAL_COMMIT_READINESS_AUDIT_REQUIRED (uncommitted; NOT approved, NOT merge-ready, NOT closed) | the task **may proceed to final commit-readiness review under the amended standard**, and is **not COMMIT_READY until that final audit passes**; **no human-review approval exists**; the owner waiver is an **internal governance decision**; the task is **not** HUMAN_REVIEW_APPROVED, **not** QUALIFIED_HUMAN_VALIDATED, **not** EXTERNAL_VALIDATION_COMPLETE, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; all prior R3-TGT-01 rows above are preserved unchanged as historical record; this governance pass appended owner-waiver and advisory-review records only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, trusted-dataset, nominal-artifact, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, or push |
| R3-TGT-01 final commit-readiness audit (2026-07-23) | FINAL_COMMIT_READINESS_AUDIT_APPROVED | final repository commit-readiness audit of the **complete uncommitted R3-TGT-01 change set** returned **APPROVED**; scope was **repository coherence and commit readiness only** under the **owner-amended internal governance standard** — **not a qualified-human statistical attestation, not external validation, and not scientific proof of predictive value**. Audit snapshot: detached audit checkout `/tmp/financeiq-r3-tgt-01-final-commit-audit-20260723`; base HEAD `26051a35992ea65b789c35f715d7c3aa5cae434c`; complete change-set digest `67f2f059b4c906ac47d719867aa59580adfd0b762e565f91db979e644e7cf8a4`. Independently verified: the complete change set is coherent and complete; no missing, unrelated, orphaned, or partially implemented path was found; governance truthfully records the original review history, the human-review CHANGES_REQUIRED disposition, the implemented corrections, technical rereview approval, qualified-human attestation unavailability, the owner waiver, the replacement review standard, and **no claim that human approval occurred**; scientific claim boundaries are internally consistent (ordinal within-year cross-sectional ranking; no benchmark-relative magnitude or alpha interpretation; primary permutation retained; trajectory sensitivity labeled post-review and non-prespecified; nominal basis the sole confirmatory family; other target bases exploratory; no cross-basis multiplicity control claimed; no inverse-alpha or contrarian interpretation; non-rejection is not proof of zero true IC; **no reliable predictive edge established**); exact family conclusions — primary **0 of 6 reject**, trajectory-preserving sensitivity **0 of 6 reject**, either analysis **0 of 6 reject**; rank audit — 2023 40 rows/0 mismatches, 2024 40 rows/0 mismatches, 2025 40 rows/0 mismatches, total **120 rows / 0 mismatches**; all seven governed excess artifacts and manifest records coherent; the 27-row leaderboard and all three prediction dumps independently verified; the protected **351-file boundary** had zero missing, zero added, and zero changed files; two isolated research-excess generations reproduced all seven outputs byte-identically; validation — focused tests **165 passed**, full root suite **521 passed**, docs-lint passed, claims-lint passed, data-validation passed, `git diff --check` passed; security and repository hygiene checks found no blocking issue. **Blocking findings: none.** Non-blocking findings: focused tests share the production significance helper for part of primary preservation and use a production-equivalent argsort RNG design for the sensitivity (independent audit calculations supplied distinct checks and preserved the 0-of-6 conclusion); the argsort permutation generator has a negligible finite-grid tie-bias caveat that does not threaten the one-to-one mappings or conclusions observed here; `scripts/lint_doc_links.py` still labels `experiments/results_excess/` as a future-output allowlist entry although the path now exists (registry and root tests independently enforce ownership and presence); the existing pytest-asyncio default-loop-scope deprecation warning remains unrelated and non-blocking. Limitations preserved explicitly and undiminished: **no qualified-human attestation was obtained**; the human gate was waived only by the owner for this internal repository task; **the waiver changes governance, not evidence**; 40 tickers; three evaluation years; retrospective cohort membership; low statistical power; one unusual macro regime; cross-basis multiplicity; post-review sensitivity status; environment-qualified byte reproducibility; limited compact-package coverage; non-rejection does not prove that true IC is zero; and nothing establishes alpha, profitability, investment value, a tradable strategy, deployment validity, or production validity |
| R3-TGT-01 amended completion standard (2026-07-23) | ALL_OWNER_AMENDED_COMPLETION_REQUIREMENTS_SATISFIED | all four requirements of the owner-amended completion standard are now satisfied: (1) **independent repository technical rereview APPROVED**; (2) **multiple independent advisory statistical assessments supported the corrected methodology**; (3) **owner methodological acceptance recorded**; (4) **final repository commit-readiness audit APPROVED**. Satisfaction of this standard is a **governance** fact only; **no qualified-human approval exists**, the **owner waiver remains active**, and nothing here establishes a predictive edge, alpha, investment value, or production validity |
| R3-TGT-01 commit disposition (2026-07-23) | COMMIT_READY_UNDER_OWNER_AMENDED_INTERNAL_STANDARD | the **complete current R3-TGT-01 change set may be staged and committed manually by the owner**; COMMIT_READY applies **only under the amended internal standard**; it does **not** mean qualified-human reviewed, and it does **not** mean merge-complete or closed; the task is **not** HUMAN_REVIEW_APPROVED, **not** QUALIFIED_HUMAN_VALIDATED, **not** EXTERNAL_VALIDATION_COMPLETE, **not** MERGE_COMPLETE, and **not** CLOSED |
| R3-TGT-01 current task state (2026-07-23, post-audit) | MANUAL_COMMIT_PENDING (uncommitted; NOT merge-complete, NOT closed) | **the commit has not yet occurred**; the owner must create it manually; **final post-commit verification remains required after the owner creates the commit**; **no qualified-human approval exists** and the **owner waiver remains active**; all prior R3-TGT-01 rows above are preserved unchanged as historical record; this governance pass appended final-audit and commit-readiness records only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, trusted-dataset, nominal-artifact, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, or push |
| R3-TGT-01 implementation commit (2026-07-23) | IMPLEMENTATION_COMMIT_RECORDED | the owner-created implementation commit `ac4ba8a80d6143fe3fccebc5637fc4d3dab79e43` (parent `26051a35992ea65b789c35f715d7c3aa5cae434c`, subject `Add R3-TGT-01 excess-return robustness analysis`) contains **exactly the 14 approved R3-TGT-01 task files** with **11,845 insertions and 1 deletion** and **no unrelated file**; COMMIT_READY was applied **only under the owner-amended internal standard**; **no qualified-human approval exists**, the **owner waiver remains active**, and nothing here establishes predictive edge, alpha, profitability, investment value, tradable-strategy validity, deployment validity, or production validity |
| R3-TGT-01 post-commit verification (2026-07-23) | POST_COMMIT_VERIFICATION_PASSED | immediately after the implementation commit: `git status` clean; `git diff HEAD^ HEAD --check` passed; docs-lint passed; claims-lint passed against **Model Confidence Contract v1.8.0**; data validation passed (**403 modeling rows, 40 governed features, 321 target rows, 82 inference-only rows, benchmark available**); **focused excess-basis suite 165 passed**; the existing pytest-asyncio default-loop-scope deprecation warning was non-blocking and unrelated; the implementation commit is locally complete and verified |
| R3-TGT-01 local branch disposition (2026-07-23) | LOCAL_IMPLEMENTATION_COMPLETE | the R3-TGT-01 implementation commit is **locally complete and verified**; the branch has **not** been pushed or merged; **no qualified-human approval exists**; the task is **not** MERGE_COMPLETE and **not** CLOSED; scientific limitations and the owner waiver remain active and undiminished |
| R3-TGT-01 current task state (2026-07-23, post-commit) | OWNER_PUSH_OR_INTEGRATION_PENDING (committed locally; NOT pushed, NOT merged, NOT closed) | **owner push or integration remains pending**; **no push or merge is recorded**; **no qualified-human approval exists** and the **owner waiver remains active**; the task is **not** HUMAN_REVIEW_APPROVED, **not** QUALIFIED_HUMAN_VALIDATED, **not** EXTERNAL_VALIDATION_COMPLETE, **not** MERGE_COMPLETE, and **not** CLOSED; no predictive edge, alpha, or production validity is established; all prior R3-TGT-01 rows above are preserved unchanged as historical record; this governance pass appended post-commit records only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, trusted-dataset, nominal-artifact, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, amend, or push |
| R3-TGT-01 pull request (2026-07-23) | PR_1_MERGED | pull request **#1** `Add R3-TGT-01 excess-return robustness analysis` (base `main`, head `local/r3-tgt-01-excess-implementation`) is **MERGED** via **merge commit**; merged timestamp `2026-07-22T22:56:06Z`; pre-merge checks all successful — PR **MERGEABLE**, merge state **CLEAN**, **Vercel** check passed, **Vercel Preview Comments** check passed, **0 failing and 0 pending checks**; **no qualified-human approval exists** and the **owner waiver remains active**; all prior R3-TGT-01 rows above are preserved unchanged as historical record |
| R3-TGT-01 merge commit (2026-07-23) | MERGE_COMMIT_RECORDED | the merge commit is `1961decf3955011d7824c7142ccbb4d21c9357f2` (merge of `26051a35` and `91408e6c`); the merged scope was **exactly two branch commits and fourteen task files, with no unrelated file and no rebase or squash rewriting of the audited commits** |
| R3-TGT-01 audited commit ancestry (2026-07-23) | AUDITED_COMMITS_PRESENT_ON_MAIN | implementation commit `ac4ba8a8` (`Add R3-TGT-01 excess-return robustness analysis`) and post-commit governance commit `91408e6c` (`Record R3-TGT-01 post-commit verification`) are **both ancestors of `origin/main`**; **both audited commit hashes were preserved by the merge-commit strategy** (no rebase or squash rewriting) |
| R3-TGT-01 post-merge verification (2026-07-23) | POST_MERGE_VERIFICATION_PASSED | after local `main` was fast-forwarded to `origin/main`: `git diff --check` passed; **docs-lint passed**; **claims-lint passed** against **Model Confidence Contract v1.8.0**; **data validation passed** (**403 modeling rows, 40 governed features, 321 target rows, 82 inference-only rows, benchmark available, valid T-to-T+1 modeling dataset**); **focused excess-basis suite 165 passed in 18.55 seconds**; **full root suite 521 passed in 120.71 seconds**; the existing pytest-asyncio default-loop-scope deprecation warning was unrelated and non-blocking |
| R3-TGT-01 integration disposition (2026-07-23) | MERGE_COMPLETE | the implementation was committed, post-commit verification passed, the branch was published, **PR #1 was merged into `main`**, **both audited commits are present on `origin/main`**, and post-merge verification passed; **no blocking implementation, repository, governance, or integration defect remains for the bounded R3-TGT-01 task**; **no qualified-human approval exists**, the **owner waiver remains active**, and nothing here establishes reliable predictive edge, alpha, investment value, or production validity |
| R3-TGT-01 final task state (2026-07-23) | CLOSED_UNDER_OWNER_AMENDED_INTERNAL_STANDARD | R3-TGT-01 is **MERGE_COMPLETE and CLOSED under the owner-amended internal governance standard**; CLOSED means **only** that the authorized R3-TGT-01 repository task is complete and no further implementation is required within this task — **dataset expansion, future prospective years, or genuine qualified-human review must be separately authorized and recorded**, and **closure does not strengthen the statistical evidence or external-validation status**; the task is retained as **QUALIFIED_HUMAN_ATTESTATION_UNAVAILABLE** and **HUMAN_REVIEW_GATE_WAIVED_BY_OWNER**, with **no external validation** and **active scientific limitations** (40 tickers, three evaluation years, retrospective cohort membership, low statistical power, one unusual macro regime, cross-basis multiplicity, post-review sensitivity status; non-rejection does not prove the true IC is zero); the task is **not** HUMAN_REVIEW_APPROVED, **not** QUALIFIED_HUMAN_VALIDATED, **not** EXTERNAL_VALIDATION_COMPLETE, **not** PREDICTIVE_EDGE_ESTABLISHED, **not** ALPHA_ESTABLISHED, and **not** PRODUCTION_VALIDATED; all prior R3-TGT-01 rows above are preserved unchanged as historical record; this governance pass appended merge and closure records only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, trusted-dataset, nominal-artifact, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, amend, merge, or push |
| R3-MISS-01 implementation (2026-07-24) | IMPLEMENTATION_COMPLETE / ROOT_SUITE_BLOCKED | deterministic serving-heuristic missingness sensitivity **complete** in worktree `r3-miss-01-missingness-sensitivity-ad3e40` on branch `local/r3-miss-01-missingness-sensitivity-ad3e40` at `4fc1136a` (uncommitted: `M Makefile`, `M artifact_registry.json`, `?? experiments/missingness_sensitivity.py`, `?? experiments/results_missingness/`, `?? tests/test_missingness_sensitivity.py`); this governance session ran in the sibling worktree `r3-tgt-01-excess-basis-2e6992` on branch `local/r3-miss-01-amendment-fbc80d` at the same commit, naming discrepancy recorded honestly per R3-UI-02 precedent; unchanged serving seam replayed read-only via `RESEARCH_REPO_ROOT`, **unmasked replay == service output (True)**; input year 2025, forecast year 2026, public cohort 40 tickers, 12 selected features across four governed source classes; four exhaustive scenario families (A 4, B 160, C 12, D 480) = **656 scenarios / 26,240 row-level observations**, deterministic no sampling; `experiments/results_missingness/` contains **exactly** `missingness_report.json`, `missingness_report.md`, `rank_deltas.csv`; independently re-verified this pass — **focused 37 passed, backend 99 passed**, docs-lint/claims-lint (MCC v1.8.0)/data-validate passed; two-run byte-identity attested by the implementation session (not re-executed here, this pass regenerates nothing); service, backend, frontend, datasets, models, weights, feature definitions, canonical artifacts, and all other result namespaces untouched; mandatory boundary recorded verbatim — *serving-heuristic sensitivity only; it does not measure predictive skill, which remains indistinguishable from the null*; full root suite **554 passed / 4 failed** blocks commit; independent review must wait until the full root suite passes; NOT approved, NOT COMMIT_READY, no staging/commit/push |
| R3-MISS-01 blocker classification (2026-07-24) | CROSS_TASK_PROVENANCE_COMPATIBILITY_DEFECT | the four root-suite failures are R3-TGT-01 provenance/test compatibility defects, not evidence that the R3-MISS-01 serving replay or generated results are incorrect; **class 1 (frozen boundary vs dynamic discovery)** — `test_protected_boundary_and_determinism_survive_the_corrections` (in `tests/test_excess_basis.py`) freezes `protected_count == 351` while its helper dynamically discovers every `experiments/results_*` namespace, so the three new authorized missingness artifacts raise the count (observed `assert 354 == 351`), with `test_protected_artifacts_are_byte_identical_across_regeneration` and `test_generated_artifacts_are_isolated_complete_and_claim_safe` failing from the same drift; **class 2 (stale whole-Makefile-SHA provenance)** — `test_embedded_source_artifact_checksums_are_current` (in `tests/test_artifact_registry.py`) (and the `test_excess_basis.py` embedded-source checksum assertion) fail because R3-TGT-01 excess provenance embeds the SHA-256 of the entire `Makefile`, so the mandatory additive `research-missingness` target marks that provenance stale even though the research-excess recipe, statistical implementation, predictions, leaderboard, and results are unchanged |
| R3-MISS-01 owner amendment (2026-07-24) | NARROW_R3_TGT_COMPATIBILITY_REPAIR_AUTHORIZED | owner authorizes a narrow compatibility repair recorded append-only in the R3-MISS-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md`; permitted paths only — `experiments/run_excess_basis.py` (only if the production provenance/protected-boundary implementation shares the defect), `tests/test_excess_basis.py`, `experiments/results_excess/artifact_manifest.json`, `experiments/results_excess/significance_report.json`, `experiments/results_excess/significance_report.md`; no other prior-task file authorized; report/provenance files must be regenerated through the governed runner, never hand-edited; nine durable invariants recorded (unrelated namespace must not invalidate the boundary; unrelated Makefile target must not stale provenance; recipe/statistical-input changes still detected; protected-boundary file mutations still detected; no `results_missingness` special-case and no 351→354 hardcode; no weakening of registry ownership/stale-detection/output-confinement/mutation-detection; R3-TGT-01 dumps/leaderboard/ICs/p-values/intervals/conclusions/claim boundaries unchanged; all three R3-MISS-01 artifacts byte-identical; governed-runner regeneration only); prohibited — service/dataset/model/feature/weight/split/seed/company/year changes, changing R3-MISS-01 scenario results, weakening tests to ignore failures, hardcoding the new file count, one-off `results_missingness` exclusion, modifying prediction dumps/leaderboards, altering statistical conclusions, and staging/committing/pushing |
| R3-MISS-01 current task state (2026-07-24) | COMPATIBILITY_REPAIR_REQUIRED / REVIEW_PENDING / NOT_COMMIT_READY | R3-MISS-01 is **not** APPROVED, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; the authorized narrow R3-TGT-01 compatibility repair must land and the **full root suite must pass** before independent review may begin; all prior rows above are preserved unchanged as historical record; this governance/amendment pass appended implementation-evidence and owner-authorization records to `FINANCEIQ_AGENT_TASK_QUEUE.md` and `TASK_STATE.md` only — it changed no implementation, test, methodology, Makefile, artifact-registry, generated-artifact, dataset, backend, frontend, or MCC file, regenerated nothing, and performed no staging, commit, or push |
| R3-MISS-01 compatibility repair (2026-07-24) | COMPATIBILITY_REPAIR_COMPLETE | independently re-verified this pass in worktree `r3-miss-01-missingness-sensitivity-ad3e40` at `4fc1136a`: the narrow R3-TGT-01 repair (frozen-boundary member set + pinned digest replacing dynamic `results_*` discovery; normalized `research-excess` target recipe/prerequisite provenance replacing whole-Makefile SHA-256) is present in `experiments/run_excess_basis.py` and `tests/test_excess_basis.py`; no literal `results_missingness` exclusion and no 351→354 hardcode found by grep; the three R3-MISS-01 artifacts are byte-identical to their previously recorded hashes; see `FINANCEIQ_AGENT_TASK_QUEUE.md` R3-MISS-01 section for the full evidence block |
| R3-MISS-01 full-suite state (2026-07-24) | ROOT_SUITE_GREEN | independently re-run this pass: `PYTHONPATH=. python -m pytest tests/ -q` → **570 passed, 0 failed** (188.46s); focused excess **177 passed**; focused missingness **37 passed**; artifact-registry **16 passed**; backend **99 passed**; `make docs-lint` PASSED; `make claims-lint` PASSED (MCC v1.8.0); `make data-validate` VALID (403 modeling rows, 40 features, 321 target rows, benchmark available); `git diff --check` passed; nothing staged, committed, or pushed |
| R3-MISS-01 review readiness (2026-07-24) | INDEPENDENT_TECHNICAL_REVIEW_READY | the root-suite blocker recorded 2026-07-24 is resolved; the repair satisfies the nine owner-authorized durable invariants on inspection; R3-MISS-01 is ready for independent technical review, which has not yet occurred |
| R3-MISS-01 current state (2026-07-24) | REVIEW_PENDING / NOT_COMMIT_READY | R3-MISS-01 is **not** APPROVED, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; this recording pass changed only `FINANCEIQ_AGENT_TASK_QUEUE.md` and `TASK_STATE.md`; it did not touch implementation, tests, the Makefile, the artifact registry, generated artifacts, datasets, backend, frontend, or MCC files, regenerated nothing, and performed no staging, commit, or push; the repair does not establish predictive robustness, reliability, stability, edge, alpha, profitability, investment value, tradable-strategy validity, deployment validity, or production validity |
| R3-MISS-01 independent technical review (2026-07-24) | CHANGES_REQUIRED | independent reviewer examined the full uncommitted change set in worktree `r3-miss-01-missingness-sensitivity-ad3e40` at `4fc1136a`; branch/HEAD confirmed, complete change set present, nothing staged; independently confirmed serving-seam replay correct against the real unchanged service (unmasked replay == complete service response), input year 2025 / forecast 2026 / cohort 40, all 12 selected serving features covered, all four scenario families exhaustive, 656 scenarios / 26,240 row-level observations coherent, JSON+Markdown aggregates reconstruct exactly from the CSV, mandatory scientific label present in JSON+Markdown+every CSV row, deterministic missingness generation, the original four root failures reconstructed, R3-TGT-01 historical boundary reconstructs to the genuine 351-member set and pinned digest, R3-TGT-01 dumps/leaderboard/statistics/multiplicity/intervals/rank-audit/0-of-6 conclusions unchanged, full repaired suite 570 passing, backend/registry/lints/data-validation pass — **but none of these makes the task commit-ready**; verdict `CHANGES_REQUIRED`; see the R3-MISS-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md` for the full evidence block |
| R3-MISS-01 blocking defect count (2026-07-24) | THREE_BLOCKING_DEFECTS | (1) missingness output confinement — `experiments/missingness_sensitivity.py` accepts an arbitrary caller-supplied `--results-dir` and confines filenames only relative to it; reviewer wrote all three artifacts under a `backend/` subdirectory outside `experiments/results_missingness`; traversal/absolute-path/symlink escapes must fail closed. (2) Makefile provenance authority — the custom research-excess parser is not GNU-Make-equivalent; in the adversarial case GNU Make executed the later duplicate recipe while provenance hashed the earlier one, so the effective recipe change went undetected; repair must use GNU Make (or a demonstrably equivalent mechanism), not another partial parser. (3) frozen-boundary symlink safety — replacing a protected member with a symlink to an identical external file preserved the digest and was accepted; all members and ancestors must be genuine repository-contained non-symlink regular files, failing closed on symlink members/ancestors/escapes/missing/modified |
| R3-MISS-01 mandatory repair (2026-07-24) | OUTPUT_CONFINEMENT_MAKE_PROVENANCE_SYMLINK_SAFETY | owner authorizes a narrow repair; new edits only to `experiments/missingness_sensitivity.py`, `tests/test_missingness_sensitivity.py`, `experiments/results_missingness/{missingness_report.json,missingness_report.md,rank_deltas.csv}`, `experiments/run_excess_basis.py`, `tests/test_excess_basis.py`, `experiments/results_excess/{artifact_manifest.json,significance_report.json,significance_report.md}`; generated files regenerated only via `make research-missingness` and `make research-excess`, never hand-edited; **not** authorized — Makefile, artifact_registry.json, service/backend, frontend, datasets, feature passports, models, weights, splits, seeds, companies, years, canonical nominal artifacts, excess prediction dumps, excess leaderboard, MCC, or any other path; if Makefile/registry changes appear necessary, stop and request a separate owner amendment; 17 durable invariants recorded in the queue section |
| R3-MISS-01 hardening (2026-07-24) | FRACTIONAL_YEAR_VALIDATION_AUTHORIZED | `load_public_frame()` casts numeric years before proving mathematical integrality; values such as `2025.5` must be rejected rather than truncated; non-blocking in the committed dataset but authorized for correction in the same repair pass — fractional, non-finite, malformed, or non-integral years must fail before integer conversion |
| R3-MISS-01 current state (2026-07-24) | REPAIR_REQUIRED / REVIEW_PENDING / NOT_COMMIT_READY | R3-MISS-01 is **not** APPROVED, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; the mandatory three-defect repair plus the authorized fractional-year hardening must land and be re-reviewed before commit; scientific claim boundary preserved verbatim — *serving-heuristic sensitivity only; it does not measure predictive skill, which remains indistinguishable from the null* — green tests and correct sensitivity measurements do not establish predictive robustness, reliability, edge, alpha, profitability, investment value, tradable-strategy validity, deployment validity, or production validity; this recording pass changed only `FINANCEIQ_AGENT_TASK_QUEUE.md` and `TASK_STATE.md`, touched no implementation/test/Makefile/registry/generated-artifact/dataset/backend/frontend/MCC file, regenerated nothing, and performed no staging, commit, or push |
| R3-MISS-01 mandatory review repair (2026-07-24) | MANDATORY_REPAIR_COMPLETE | the mandatory three-defect repair plus the authorized fractional-year hardening is complete in worktree `r3-miss-01-missingness-sensitivity-ad3e40` at `4fc1136a`; independently re-run/re-hashed this pass; a fresh independent technical re-review is required; see the R3-MISS-01 section of `FINANCEIQ_AGENT_TASK_QUEUE.md` for the full evidence block |
| R3-MISS-01 blocking defects (2026-07-24) | THREE_BLOCKERS_REPAIRED | (1) missingness output confinement — canonical output restricted to exactly `experiments/results_missingness`, noncanonical requires a separate explicit bounded `--temp-root` authority, traversal/absolute/symlinked-destination/symlinked-ancestor/symlink-escape all fail closed, exactly three governed filenames, failed writes roll back partial files, `make research-missingness` unchanged. (2) effective GNU Make provenance — ad hoc Makefile parser removed; GNU Make itself is the authority via controlled `--print-data-base --dry-run` subprocesses for effective prerequisites/expanded recipe/duplicate-rule/continuation/comment/blank-line/variable handling; unrelated targets/vars do not change the authority; recipe/prerequisite changes detected; statistical sources separately hashed; whole-Makefile SHA not reintroduced. (3) frozen-boundary symlink & path safety — normalized/validated authority paths, absolute/traversal rejected, every member and ancestor lstat-checked without following symlinks, symlinked members/ancestors/non-regular/duplicate/missing/modified/escape fail closed; historical boundary remains 351 members; pinned digest remains `634d7151e75f0ec7a85e412f748ac81499a4fad5e9eac71ab1a5c920f0137dd9` |
| R3-MISS-01 hardening (2026-07-24) | FRACTIONAL_YEAR_VALIDATION_REPAIRED | year values validated for finiteness and mathematical integrality before integer conversion; `2025.5`, NaN, infinities, empty strings, malformed strings, and truncation/rounding-requiring values rejected; valid integer years and permitted canonical integer strings still accepted |
| R3-MISS-01 full-suite state (2026-07-24) | ROOT_SUITE_GREEN_AFTER_MANDATORY_REPAIR | independently re-run this pass: full root suite `PYTHONPATH=. python -m pytest tests/ -q` → **638 passed, 0 failed** (221.91s); focused missingness **78 passed**; focused excess **204 passed**; artifact-registry **16 passed**; backend **99 passed**; `make docs-lint` PASSED; `make claims-lint` PASSED (MCC v1.8.0); `make data-validate` VALID (403 modeling rows, 40 features, 321 target rows, 82 inference-only, benchmark available); isolated two-run missingness determinism byte-identical and equal to committed target artifacts (JSON `e351dbf5…`); isolated excess determinism byte-identical except embedded output-path (normalized diff 0, same-path double-run identical), path-independent outputs equal to committed target bytes; target in-place double-run intentionally not performed (override forbids regenerating artifacts) — reproducibility confirmed non-destructively; `git diff --check` clean; nothing staged, committed, or pushed |
| R3-MISS-01 re-review readiness (2026-07-24) | FRESH_INDEPENDENT_TECHNICAL_REREVIEW_READY | all three blocking defects repaired and the authorized fractional-year hardening applied; scientific evidence for R3-MISS-01 and R3-TGT-01 preserved (byte-identical `.md`/`.csv` artifacts; JSON deltas explained solely by truthful embedded source checksums / GNU Make provenance); R3-MISS-01 is ready for a fresh independent technical re-review, which has not yet occurred |
| R3-MISS-01 current state (2026-07-24) | REREVIEW_PENDING / NOT_COMMIT_READY | R3-MISS-01 is **not** APPROVED, **not** COMMIT_READY, **not** MERGE_COMPLETE, and **not** CLOSED; a fresh independent technical re-review must occur before commit; scientific claim boundary preserved verbatim — *serving-heuristic sensitivity only; it does not measure predictive skill, which remains indistinguishable from the null* — green tests and correct sensitivity measurements do not establish predictive robustness, reliability, edge, alpha, profitability, investment value, tradable-strategy validity, deployment validity, or production validity; this recording pass changed only `FINANCEIQ_AGENT_TASK_QUEUE.md` and `TASK_STATE.md`, touched no implementation/test/Makefile/registry/generated-artifact/dataset/backend/frontend/MCC file, regenerated no committed artifact, and performed no staging, commit, or push |
| R3-STAT-01 ranking and cohort stability under resampling (2026-08-04) | CLOSED | implementation commit `1f47c6fec9fa2205871ccb78705836c2d3095dd2`; independent Fable 5 review `APPROVED` at reviewed `main` HEAD `5d010c3763f457bd276c4760991a9ffecdbc3fc5`; task-owned files preserved; independent arithmetic reproduced all `2,160 / 2,160` bootstrap JSON rows, all `2,160 / 2,160` bootstrap CSV rows, all `2,160 / 2,160` JSON/CSV parity rows, and all `9 / 9` full-universe pooled IC values; the reviewer independently produced all `2,160` exact leave-one-out values and all `18,000` seeded leave-eight-out values; persisted distribution summaries matched `9 / 9` models for each deletion design; all `27 / 27` public-40 per-year IC values, all `9 / 9` public-40 pooled IC values, and all `4 / 4` embedded input hashes matched; total arithmetic mismatches were zero; deterministic regeneration remained byte-identical; focused `45 / 45` and root `927 / 927` tests passed; docs-lint and claims-lint passed under MCC `v1.10.0`; stability is variability of a null-consistent ranking and does not validate stock picks; repository evidence only, with no deployed-runtime or real-user validation; no prior R3-STAT-01 TASK_STATE row existed, so this first row does not supersede a prior row |
| Reliable predictive edge | LIMIT | weak/unstable; needs larger universe + longer history |

---

## Phase-2 post-commit reconciliation (appended by R3-GOV-01)

The Phase-2 status rows above preserve what was true when each task finished. The owner's later commits supersede the historical `DONE (uncommitted)` / `commit deferred` wording:

| Task | Committed SHA |
|---|---|
| R2-GOV-01 | `d743e7d2` |
| R2-STAT-UI-01 | `2985a86b` |
| R2-CONTRACT-02 | `253eedc5` |
| R2-LINEAGE-01 | `6af2c5be` |
| R2-SKEPTIC-01 | `53a92a41` |
| R2-AUTOPSY-01 | `a95e1e1c` |
| R2-CAL-01 | `646fdae7` |
| R2-REAL-01 | `7124bdd8` |
| R2-REGIME-01 | `d83741c2` |
| R2-LOOP-01 | `57ea8c05` |
| R2-COURT-01 | `ef6a8030` |
| R2-FRICTION-01 | `b9fe263e` |
| R2-DEMO-01 | `97e4fc33` |

Post-Phase-2 reproducibility state was then recorded by `fbab761f`.

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

### R3-MISS-01 fresh independent technical re-review (2026-07-24; append-only)

| State item | Status |
|---|---|
| Fresh independent technical re-review | `CHANGES_REQUIRED` |
| Blocking defect count | `FIVE_BLOCKING_DEFECTS` |
| Output publication repair | `SYMLINK_SAFE_TRANSACTIONAL_PUBLICATION_AUTHORIZED` |
| GNU Make provenance repair | `NON_EXECUTING_EXECUTION_SEMANTICS_REPAIR_AUTHORIZED` |
| Frozen-boundary repair | `DESCRIPTOR_ANCHORED_HASHING_REPAIR_AUTHORIZED` |
| Review state | `REREVIEW_REQUIRED` |
| Current state | `REPAIR_REQUIRED / NOT_COMMIT_READY` |

### R3-MISS-01 five-blocker mandatory repair completion (2026-07-24; append-only)

| State item | Status |
|---|---|
| Five-blocker mandatory repair | `COMPLETE` |
| Canonical output confinement | `DESCRIPTOR_ANCHORED_REPAIRED` |
| Artifact publication | `TRANSACTIONAL_PUBLICATION_REPAIRED` |
| Make provenance | `NON_EXECUTING_STATIC_CONTRACT_REPAIRED` |
| Frozen-boundary hashing | `DESCRIPTOR_ANCHORED_REPAIRED` |
| Full root suite | `666 PASSED / 0 FAILED` |
| Re-review readiness | `FRESH_INDEPENDENT_TECHNICAL_REREVIEW_READY` |
| Current state | `REREVIEW_PENDING / NOT_COMMIT_READY` |

### R3-MISS-01 post-five-blocker fresh independent re-review (2026-07-29; append-only)

| State item | Status |
|---|---|
| Fresh independent technical re-review | `CHANGES_REQUIRED` |
| Scientific preservation | `CONFIRMED` |
| Required suite status | `GREEN` |
| Remaining blocking defects | `FIVE` |
| Temporary-output authority | `POST_AUTHORIZATION_SYMLINK_RACE_REPAIR_REQUIRED` |
| Publication transaction | `CLEANUP_COMMIT_POINT_REPAIR_REQUIRED` |
| Make provenance | `GLOBAL_AND_AMBIGUOUS_SEMANTICS_REPAIR_REQUIRED` |
| Frozen boundary | `ANCESTOR_REVALIDATION_REPAIR_REQUIRED` |
| Service replay guard | `COMPLETE_RESPONSE_ASSERTION_REPAIR_REQUIRED` |
| Repair authorization | `SECOND_MANDATORY_REPAIR_AUTHORIZED` |
| Review state | `FRESH_REREVIEW_REQUIRED` |
| Current state | `REPAIR_REQUIRED / NOT_COMMIT_READY` |

### R3-MISS-01 second mandatory repair completion (2026-07-29; append-only)

| State item | Status |
|---|---|
| Second mandatory repair | `COMPLETE` |
| Temporary output authority | `CONTINUOUS_DESCRIPTOR_AUTHORITY_REPAIRED` |
| Publication transaction | `EXPLICIT_COMMIT_POINT_REPAIRED` |
| Make provenance | `STRICT_NON_EXECUTING_SUBSET_REPAIRED` |
| Frozen-boundary hashing | `FULL_ANCESTOR_REVALIDATION_REPAIRED` |
| Complete service replay | `CANONICAL_FULL_RESPONSE_ASSERTION_REPAIRED` |
| Focused missingness | `133 PASSED / 0 FAILED` |
| Focused excess | `253 PASSED / 0 FAILED` |
| Full root suite | `742 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Re-review readiness | `FRESH_INDEPENDENT_TECHNICAL_REREVIEW_READY` |
| Current state | `REREVIEW_PENDING / NOT_COMMIT_READY` |

### R3-MISS-01 second-repair fresh independent re-review (2026-07-29; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Passing repairs | `TRANSACTION / FROZEN_BOUNDARY / COMPLETE_REPLAY` |
| Remaining blockers | `TWO` |
| Output authority | `REAL_DIRECTORY_REPLACEMENT_REPAIR_REQUIRED` |
| Make provenance | `GLOBAL_SEMANTICS_REPAIR_REQUIRED` |
| Repair authorization | `NARROW_REPAIR_AUTHORIZED` |
| Current state | `REPAIR_REQUIRED / NOT_COMMIT_READY` |

### R3-MISS-01 two-blocker narrow repair completion (2026-07-29; append-only)

| State item | Status |
|---|---|
| Two-blocker narrow repair | `COMPLETE` |
| Output authority | `DESCRIPTOR_IDENTITY_CHAIN_REPAIRED` |
| Make provenance | `GLOBAL_SEMANTICS_REPAIRED` |
| Full root suite | `794 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Current state | `REREVIEW_PENDING / NOT_COMMIT_READY` |

### R3-MISS-01 final fresh independent re-review (2026-07-29; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Remaining blockers | `TWO` |
| Final directory identity | `REPAIR_REQUIRED` |
| Make target parsing | `REPAIR_REQUIRED` |
| Repair authorization | `FINAL_NARROW_REPAIR_AUTHORIZED` |
| Current state | `REPAIR_REQUIRED / NOT_COMMIT_READY` |

### R3-MISS-01 final two-blocker repair completion (2026-07-29; append-only)

| State item | Status |
|---|---|
| Final two-blocker repair | `COMPLETE` |
| Final directory identity | `REPAIRED` |
| Ambiguous Make targets | `REPAIRED` |
| Full root suite | `861 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Current state | `REREVIEW_PENDING / NOT_COMMIT_READY` |

### R3-MISS-01 legacy publication blocker (2026-07-29; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Remaining blockers | `ONE` |
| Structured publication | `PASSED` |
| Make provenance | `PASSED` |
| Legacy publication | `FINAL_DIRECTORY_SYMLINK_REPAIR_REQUIRED` |
| Repair authorization | `FINAL_LEGACY_REPAIR_AUTHORIZED` |
| Current state | `REPAIR_REQUIRED / NOT_COMMIT_READY` |

### R3-MISS-01 final legacy publication repair completion (2026-07-30; append-only)

| State item | Status |
|---|---|
| Final legacy publication repair | `COMPLETE` |
| Final-component normalization | `PARENT_ONLY / REPAIRED` |
| Retained legacy authority | `DURABLE_CLAIM_REPAIRED` |
| Path-only fallback | `REMOVED` |
| Legacy publication authorization | `EXPLICIT_ASSERTION_REPAIRED` |
| Focused missingness | `202 PASSED / 0 FAILED` |
| Artifact registry | `16 PASSED / 0 FAILED` |
| Full root suite | `893 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Documentation / claims / data validation | `PASSED` |
| Review readiness | `FRESH_INDEPENDENT_TECHNICAL_REREVIEW_READY` |
| Current state | `REREVIEW_PENDING / NOT_COMMIT_READY` |

### R3-MISS-01 final independent approval (2026-07-30; append-only)

| State item | Status |
|---|---|
| Independent verdict | `APPROVED` |
| Inspected change scope | `14 AUTHORIZED PATHS` |
| Independent publication attacks | `15/15 FAILED CLOSED` |
| Governed-file leakage | `ZERO` |
| Focused missingness | `202 PASSED / 0 FAILED` |
| Focused excess | `335 PASSED / 0 FAILED` |
| Artifact registry | `16 PASSED / 0 FAILED` |
| Full root suite | `893 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Documentation / claims / data validation | `PASSED` |
| Deterministic missingness regeneration | `BYTE_IDENTICAL` |
| Scientific preservation | `CONFIRMED` |
| Immutable leaderboard / predictions | `CONFIRMED` |
| Current state | `COMMIT_READY / OWNER_MANUAL_COMMIT_PENDING` |

### R3-MISS-01 post-merge closure (2026-07-30; append-only)

| State item | Status |
|---|---|
| Pull request | `#2 MERGED` |
| Merge commit | `fa0999577a9e0509bf3f2c53077734f7bcd5a201` |
| Focused post-merge suites | `553 PASSED / 0 FAILED` |
| Full root suite | `893 PASSED / 0 FAILED` |
| Backend suite | `99 PASSED / 0 FAILED` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED` |
| Data validation | `PASSED` |
| Artifact hashes | `MATCH APPROVED RECORD` |
| Scientific preservation | `CONFIRMED` |
| Final state | `MERGED / POST_MERGE_VERIFIED / CLOSED` |

### R3-UI-01 post-merge closure (2026-07-30; append-only)

| State item | Status |
|---|---|
| Pull request | `#3 MERGED` |
| Merge commit | `9d8622d16b697284b0930e42d969340ce016c59d` |
| Changed scope | `2 AUTHORIZED FRONTEND FILES` |
| Initial independent verdict | `CHANGES_REQUIRED — INDEX KEY` |
| Stable-key repair | `COMPLETE` |
| Fresh independent re-review | `APPROVED` |
| Frontend build | `PASSED` |
| Claims lint | `PASSED — MCC v1.8.0` |
| Backend suite | `99 PASSED / 0 FAILED` |
| ASELS / ASTOR contract verification | `CONFIRMED` |
| Live authenticated browser verification | `NOT PERFORMED / NON-BLOCKING` |
| Final state | `MERGED / POST_MERGE_VERIFIED / CLOSED` |

### R3-UI-03 cross-task frozen-boundary authorization (2026-07-30; append-only)

| State item | Status |
|---|---|
| MCC change | `v1.8.0 → v1.9.0 REQUIRED` |
| Frozen-boundary conflict | `CONFIRMED` |
| MCC boundary membership | `RETAINED` |
| Boundary exemption | `REJECTED` |
| Excess digest re-pin | `AUTHORIZED` |
| Governed excess regeneration | `AUTHORIZED` |
| Scientific-result changes | `FORBIDDEN` |
| Review state | `FRESH INDEPENDENT REVIEW REQUIRED` |
| Current state | `REPAIR AUTHORIZED / NOT COMMIT READY` |

### R3-UI-03 frozen-boundary compatibility repair completion (2026-07-30; append-only)

| State item | Status |
|---|---|
| MCC version | `v1.9.0` |
| Protected-boundary members | `351 / UNCHANGED` |
| Old boundary digest | `634d7151e75f0ec7a85e412f748ac81499a4fad5e9eac71ab1a5c920f0137dd9` |
| New boundary digest | `0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba` |
| Changed boundary member | `model_confidence_contract.json ONLY` |
| Boundary exemption | `NONE` |
| Governed excess regeneration | `COMPLETE` |
| Scientific findings | `UNCHANGED` |
| Focused excess | `335 PASSED / 0 FAILED` |
| Calibration API | `9 PASSED / 0 FAILED` |
| Backend suite | `108 PASSED / 0 FAILED` |
| MCC / claim-safety pins | `17 PASSED / 0 FAILED` |
| Disposable staged root suite | `893 PASSED / 0 FAILED` |
| Frontend build / lints / data validation | `PASSED` |
| Review state | `FRESH INDEPENDENT REVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 first independent review and repair authorization (2026-07-30; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Frozen-boundary compatibility | `PASSED` |
| Scientific preservation | `CONFIRMED` |
| Remaining blockers | `TWO` |
| Contradictory artifact behavior | `503 REPAIR REQUIRED` |
| Malformed nested artifact behavior | `503 REPAIR REQUIRED` |
| Documentation lint citation | `REPAIR AUTHORIZED` |
| Repair scope | `CALIBRATION SERVICE / ROUTE IF NEEDED / TESTS / GOVERNANCE` |
| Review state | `FRESH REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 blocking-findings repair completion (2026-07-31; append-only)

| State item | Status |
|---|---|
| Calibration fail-closed repair | `COMPLETE` |
| Missing / malformed / contradictory artifacts | `PUBLIC ROUTE 503` |
| Invalid UTF-8 / unreadable artifact | `PUBLIC ROUTE 503` |
| Unrelated programming errors | `NOT DISGUISED` |
| Documentation lint defect | `REPAIRED` |
| Calibration API suite | `160 PASSED / 0 FAILED` |
| Backend suite | `259 PASSED / 0 FAILED` |
| MCC / claim-safety pins | `17 PASSED / 0 FAILED` |
| Frontend build / lints / data validation | `PASSED` |
| Staged root suite in Python 3.11 environment | `885 PASSED / 8 ENVIRONMENT-MATCHED FAILURES` |
| Clean-HEAD control | `SAME 8 FAILURES` |
| Boundary / artifacts / scientific findings | `UNCHANGED` |
| Review state | `FRESH INDEPENDENT REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 second re-review and final repair authorization (2026-08-01; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Previous 503 blockers | `REPAIRED` |
| Documentation lint | `PASSED` |
| Changed root suite | `893 PASSED / 0 FAILED` |
| Clean-HEAD root suite | `893 PASSED / 0 FAILED` |
| Remaining blockers | `ONE` |
| Nested element validation | `REPAIR REQUIRED` |
| Repair scope | `CALIBRATION SERVICE + FOCUSED TESTS` |
| Review state | `FRESH REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 final nested-validation repair completion (2026-08-01; append-only)

| State item | Status |
|---|---|
| Remaining nested-validation blocker | `REPAIRED` |
| Returned fields explicitly validated | `ALL` |
| Additional adversarial mutations | `71` |
| Total mutation matrix | `134 CASES` |
| Calibration API suite | `302 PASSED / 0 FAILED` |
| Backend suite | `401 PASSED / 0 FAILED` |
| Excess-basis suite | `335 PASSED / 0 FAILED` |
| Disposable staged root suite | `893 PASSED / 0 FAILED` |
| Documentation / claims lint | `PASSED` |
| Frontend production build | `PASSED` |
| Protected boundary and artifacts | `UNCHANGED` |
| Review state | `FRESH INDEPENDENT REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 third re-review and repair authorization (2026-08-02; append-only)

| State item | Status |
|---|---|
| Independent verdict | `CHANGES_REQUIRED` |
| Standard root suite | `893 PASSED / 0 FAILED` |
| Remaining blockers | `THREE` |
| Whole-block passthrough | `REPAIR REQUIRED` |
| NaN / Infinity serialization escape | `REPAIR REQUIRED` |
| Bootstrap request count | `REPAIR REQUIRED` |
| Correct parametrized matrix | `144 CASES` |
| Correct focused total before repair | `302 TESTS` |
| Repair scope | `CALIBRATION SERVICE + FOCUSED TESTS` |
| Review state | `FRESH REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 third-blocker repair completion (2026-08-02; append-only)

| State item | Status |
|---|---|
| Whole-block passthrough blocker | `REPAIRED` |
| Unknown response keys | `REJECTED WITH 503` |
| NaN / Infinity blocker | `REPAIRED` |
| Bootstrap-count blocker | `REPAIRED` |
| Mutable cached response references | `REMOVED` |
| Parametrized mutation matrix | `185 CASES` |
| Additional non-parametrized tests | `26` |
| Calibration API suite | `396 PASSED / 0 FAILED` |
| Backend suite | `495 PASSED / 0 FAILED` |
| Excess-basis suite | `335 PASSED / 0 FAILED` |
| Disposable staged root suite | `893 PASSED / 0 FAILED` |
| Documentation / claims lint | `PASSED` |
| Frontend production build | `PASSED` |
| Accidental index staging | `REVERSED / NO RESIDUE` |
| Protected boundary and artifacts | `UNCHANGED` |
| Review state | `FRESH INDEPENDENT REREVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-UI-03 final independent approval (2026-08-02; append-only)

| State item | Status |
|---|---|
| Final independent verdict | `APPROVED` |
| Changed scope | `17 AUTHORIZED PATHS` |
| Calibration API suite | `396 PASSED / 0 FAILED` |
| Backend suite | `495 PASSED / 0 FAILED` |
| Excess-basis suite | `335 PASSED / 0 FAILED` |
| MCC / claim-safety suite | `348 PASSED / 0 FAILED` |
| Disposable staged root suite | `893 PASSED / 0 FAILED` |
| Frontend build / lints / data validation | `PASSED` |
| Protected-boundary members | `351 / UNCHANGED` |
| Protected-boundary digest | `0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba` |
| Scientific findings | `UNCHANGED — 0/6` |
| Live authenticated browser verification | `NOT PERFORMED / NON-BLOCKING` |
| Current state | `INDEPENDENTLY APPROVED / COMMIT READY` |

### R3-UI-03 post-merge closure (2026-08-02; append-only)

| State item | Status |
|---|---|
| Pull request | `#4 MERGED` |
| Implementation commit | `f1de4d71` |
| Merge commit | `663f2825c8835fbf4fd059ca98e859357929b52a` |
| Changed scope | `17 AUTHORIZED PATHS` |
| Final independent review | `APPROVED` |
| Root suite | `893 PASSED / 0 FAILED` |
| Backend suite | `495 PASSED / 0 FAILED` |
| Frontend production build | `PASSED — 2,445 MODULES` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED — MCC v1.9.0` |
| Data validation | `PASSED — 403 ROWS / 40 FEATURES / 321 TARGET ROWS` |
| Protected-boundary members | `351 / UNCHANGED` |
| Protected-boundary digest | `0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba` |
| Scientific conclusion | `UNCHANGED — NO RELIABLE PREDICTIVE EDGE / 0 OF 6` |
| Live authenticated browser verification | `NOT PERFORMED / NON-BLOCKING` |
| Final state | `MERGED / POST_MERGE_VERIFIED / CLOSED` |

### Research Courtroom Evidence Lens overlap closure (2026-08-02; append-only)

| State item | Status |
|---|---|
| Pull request | `#5 MERGED` |
| Fix commit | `112ce758` |
| Merge commit | `ab01dc9f58ded173465f59b561de35b59922a91b` |
| Changed scope | `2 FRONTEND FILES` |
| Frontend production build | `PASSED` |
| Claims lint | `PASSED — MCC v1.9.0` |
| Manual production verification | `PASSED` |
| Final state | `MERGED / VERIFIED / CLOSED` |

### R3-LIMITS-01 valuation schema prerequisite authorization (2026-08-02; append-only)

| State item | Status |
|---|---|
| Producer schema defect | `CONFIRMED — SCALAR limitations` |
| Corrected schema | `NON-EMPTY list[str]` |
| Limitation wording | `BYTE-VERBATIM PRESERVED` |
| Protected-boundary membership | `RETAINED` |
| Boundary exemption | `REJECTED` |
| Digest re-pin | `AUTHORIZED` |
| Governed excess regeneration | `AUTHORIZED` |
| Scientific-result changes | `FORBIDDEN` |
| Review state | `FRESH INDEPENDENT REVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-LIMITS-01 valuation prerequisite compatibility completion (2026-08-02; append-only)

| State item | Status |
|---|---|
| Valuation limitations schema | `NON-EMPTY list[str]` |
| Limitation wording | `BYTE-VERBATIM PRESERVED` |
| Valuation Markdown | `BYTE-IDENTICAL` |
| Protected-boundary members | `351 / UNCHANGED` |
| Changed protected member | `free_valuation_history_report.json ONLY` |
| Old boundary digest | `0b0083a458ff24e9414ed23c12fb58f40ebe22c94539e6979b0c7affcf6d76ba` |
| New boundary digest | `e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f` |
| Boundary exemption | `NONE` |
| Governed excess regeneration | `COMPLETE` |
| Scientific findings | `UNCHANGED — 0/6` |
| Valuation tests | `9 PASSED / 0 FAILED` |
| Excess-basis tests | `335 PASSED / 0 FAILED` |
| Root suite | `895 PASSED / 0 FAILED` |
| Data / docs / claims validation | `PASSED` |
| Review state | `FRESH INDEPENDENT REVIEW REQUIRED` |
| Current state | `NOT COMMIT READY` |

### R3-LIMITS-01 closure (2026-08-02; append-only)

| State item | Status |
|---|---|
| Pull request | `#8 MERGED` |
| Implementation commit | `1c040640` |
| Merge commit | `b56b573b` |
| Registered JSON artifacts | `14` |
| Auto-extracted limitations | `101 VERBATIM ENTRIES` |
| Curated limitations | `6 POSITIONALLY VALIDATED` |
| Generated document hash | `022335f7e6335d60e0e5ebd68773363f487d547042a5de4fb72176717bb90904` |
| Deterministic double-generation | `PASSED` |
| Limitations-register tests | `32 PASSED / 0 FAILED` |
| Artifact-registry tests | `16 PASSED / 0 FAILED` |
| Root suite | `927 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.9.0` |
| Final state | `MERGED / VERIFIED / CLOSED` |

### R3-MEMO-01 implementation authorization (2026-08-02; append-only)

| State item | Status |
|---|---|
| Task | `R3-MEMO-01` |
| Implementation model | `OPUS 5 — HIGH` |
| Mandatory review | `FABLE 5 — MEDIUM` |
| Current MCC | `v1.9.0` |
| MCC boundary membership | `RETAINED` |
| Current protected members | `351` |
| Current boundary digest | `e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f` |
| Boundary exemption | `FORBIDDEN` |
| Scientific-result changes | `FORBIDDEN` |
| Current state | `AUTHORIZED / NOT COMMIT READY` |

### R3-MEMO-01 implementation evidence (2026-08-02; append-only)

| State item | Status |
|---|---|
| Task | `R3-MEMO-01 — claim-aware research memo compiler` |
| Route | `POST /research/memo/{ticker}` (require_access; no body, no prompt, no source path) |
| Service | `backend/app/services/memo_service.py` (deterministic, LLM-off) |
| Shared citation contract | `backend/app/services/citations.py` (Courtroom + memo) |
| Courtroom preservation | `RESPONSE BYTES AND SCHEMA UNCHANGED — 20 cases compared against HEAD` |
| Section order | `identity_and_coverage → evidence_quality → skeptic_challenge → significance_and_power → limitations → provenance_stamp` |
| Citation completeness | `EVERY EVIDENCE SENTENCE ≥ 1 VALUE-RESOLVED CITATION` |
| Forbidden keys (recommendation/verdict/rating/target/outlook) | `ABSENT AT EVERY DEPTH` |
| Raw/adjusted p-value pairing | `STRUCTURALLY INSEPARABLE — 6 ML models + 1 labelled serving test` |
| Recorded fixtures | `ASELS (dense, 40/40) and DSTKF (sparse, 37/40, unique minimum)` |
| MCC | `v1.9.0 → v1.10.0` (one scan entry, one exact allowlist line, five pins) |
| Protected members compared vs `main` | `351 — exactly one differs: model_confidence_contract.json` |
| Boundary digest | `e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f → 03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd` |
| Boundary exemption | `NONE ADDED` |
| Excess regeneration | `2 FILES / 9 JSON LEAVES — boundary digest, generator source, dependent hash only` |
| Scientific leaves | `UNCHANGED — survivors remain 0/6 primary, sensitivity and either` |
| Leaderboard and prediction dumps | `BYTE-IDENTICAL` |
| `significance_report.md` | `BYTE-IDENTICAL` |
| Memo tests | `42 PASSED / 0 FAILED` |
| Backend suite | `537 PASSED / 0 FAILED` |
| Root suite (independent staged clone) | `927 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.10.0` |
| Data validation | `VALID — unchanged` |
| Current state | `IMPLEMENTATION COMPLETE / FABLE REVIEW REQUIRED / NOT COMMIT READY` |

### R3-MEMO-01 independent Fable approval (2026-08-02; append-only)

| State item | Status |
|---|---|
| Mandatory reviewer | `FABLE 5 — APPROVED` |
| Changed paths | `17 AUTHORIZED PATHS` |
| ASELS response hash | `b7c5ff54a43b8242c95a0624d3e74c3c55e3b22883b291400eecbd238f3a207d` |
| DSTKF response hash | `bb4311848b5176ee91d464f1b4fa168d241f5020ed3329ef426f13561a4d8dd5` |
| Citation resolution | `242 / 242 PASSED` |
| Adversarial citation checks | `11 / 11 FAILED CLOSED` |
| Courtroom preservation | `20 / 20 BYTE-IDENTICAL` |
| Memo tests | `42 PASSED / 0 FAILED` |
| Focused Courtroom/Skeptic/MCC | `60 PASSED / 0 FAILED` |
| Backend suite | `537 PASSED / 0 FAILED` |
| Staged-clone root suite | `927 PASSED / 0 FAILED` |
| MCC | `v1.9.0 → v1.10.0` |
| Protected members | `351` |
| Old boundary digest | `e55c62bfb729ce73dc008e90a2875fa252c3c399bf1f29112eafea16eba14c2f` |
| New boundary digest | `03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd` |
| Changed protected members | `1 — model_confidence_contract.json` |
| Scientific findings | `UNCHANGED — 0/6 PRIMARY, SENSITIVITY, EITHER` |
| Current state | `INDEPENDENTLY APPROVED / COMMIT READY` |

### R3-MEMO-01 post-merge closure (2026-08-02; append-only)

| State item | Status |
|---|---|
| Pull request | `#9 MERGED` |
| Implementation commit | `8a2bc7b4` |
| Merge commit | `5fb7d7ad932067ebbfe7ec83aba051c0022d145e` |
| Mandatory review | `FABLE 5 — APPROVED` |
| Response sections | `6 FIXED SECTIONS` |
| Citation review | `242 / 242 RESOLVED` |
| Adversarial citation checks | `11 / 11 FAILED CLOSED` |
| Courtroom preservation | `20 / 20 BYTE-IDENTICAL` |
| MCC | `v1.10.0` |
| Protected members | `351` |
| Protected-boundary digest | `03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd` |
| Memo tests | `42 PASSED / 0 FAILED` |
| Focused tests | `60 PASSED / 0 FAILED` |
| Backend suite | `537 PASSED / 0 FAILED` |
| Root suite | `927 PASSED / 0 FAILED` |
| Data / docs / claims validation | `PASSED — MCC v1.10.0` |
| Scientific findings | `UNCHANGED — 0/6 PRIMARY, SENSITIVITY, EITHER` |
| Final state | `MERGED / POST-MERGE VERIFIED / CLOSED` |

### R3-MEMO-01 actual post-merge verification (2026-08-02; append-only)

| State item | Status |
|---|---|
| Sequencing correction | `INITIAL CLOSURE PRECEDED FULL POST-MERGE RERUN` |
| Implementation commit | `8a2bc7b4` |
| Merge commit | `5fb7d7ad932067ebbfe7ec83aba051c0022d145e` |
| Closure commit | `c62d9c50` |
| Memo tests | `42 PASSED / 0 FAILED` |
| Focused tests | `60 PASSED / 0 FAILED` |
| Backend suite | `537 PASSED / 0 FAILED` |
| Root suite | `927 PASSED / 0 FAILED` |
| Data validation | `PASSED` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED — MCC v1.10.0` |
| Diff validation | `PASSED` |
| Corrected final state | `MERGED / ACTUAL POST-MERGE VERIFIED / CLOSED` |

### R3-PREREG-01 current-main integration closure (2026-08-03; append-only)

| State item | Status |
|---|---|
| Integration commit | `68d2681a64a917cfb87a0e30f7e03c3b61b406b1` |
| Integration relationship | `ANCESTOR OF CURRENT MAIN` |
| Approved task files | `7 / 7 BYTE-IDENTICAL` |
| Frozen ranking SHA-256 | `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f` |
| Freeze manifest SHA-256 | `6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea` |
| Freeze-once current-main result | `EXPECTED REFUSAL — freeze_git_sha_drift` |
| Frozen artifacts after refusal | `UNCHANGED` |
| 2026 outcome files | `ABSENT` |
| Evaluator state | `outcome_data_absent / metric_computed=false` |
| Frozen cohort | `40` |
| Usable outcome cohort | `0` |
| Focused PREREG + registry tests | `86 PASSED / 0 FAILED` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED — MCC v1.10.0` |
| Final state | `INTEGRATED / CURRENT-MAIN VERIFIED / FROZEN / CLOSED` |

### R3-PREREG-01 docs-lint correction (2026-08-03; append-only)

| State item | Status |
|---|---|
| Initial closure commit | `a9a8fb9c` |
| Initial docs-lint result | `FAILED — 2 ABSENT-PATH REFERENCES` |
| Protocol or artifact impact | `NONE` |
| Outcome files created | `NONE` |
| Linter weakening | `NONE` |
| Correction | `ABSENT INPUTS REWORDED AS DESCRIPTIVE TEXT` |
| Corrected documentation lint | `PASSED` |
| Corrected claims lint | `PASSED — MCC v1.10.0` |
| Corrected diff validation | `PASSED` |
| Final state | `INTEGRATED / CURRENT-MAIN VERIFIED / FROZEN / CLOSED` |

### R3-STAT-02 current-main review closure (2026-08-03; append-only)

| State item | Status |
|---|---|
| Implementation commit | `2e834b85a393135bbe25b0bc782c0fc59b75851c` |
| Reviewed current-main HEAD | `d7f151dbcaf85c840c792779511bb714fa396a5f` |
| Integration relationship | `IMPLEMENTATION IS ANCESTOR OF MAIN` |
| Historical awaiting-commit status | `STALE — SUPERSEDED APPEND-ONLY` |
| Independent current-main review | `APPROVED` |
| Task-owned files | `5 / 5 BYTE-IDENTICAL` |
| Rank design | `WITHIN-YEAR / WITHIN-MODEL ONLY` |
| Raw cross-model score comparison | `NONE` |
| Retraining or production mutation | `NONE` |
| Deterministic regeneration | `COMMITTED = RUN 1 = RUN 2` |
| Protected scientific artifacts | `BYTE-IDENTICAL` |
| Focused tests | `27 PASSED / 0 FAILED` |
| Complete root suite | `927 PASSED / 0 FAILED` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED — MCC v1.10.0` |
| Remaining limitation | `MINOR NON-BLOCKING TEST-COVERAGE GAP` |
| Final state | `INTEGRATED / REVIEW APPROVED / DETERMINISTIC / CLOSED` |

### R3-INF-01 independent current-main review closure (2026-08-03; append-only)

| State item | Status |
|---|---|
| Implementation commit | `ea2a5f5565b634d13c99c8186cda7ed3c9ef7523` |
| Reviewed current-main HEAD | `469159638999fc0b28ef707fef0905a4f9a148f2` |
| Integration relationship | `FIRST-PARENT ANCESTOR OF MAIN` |
| Historical awaiting-commit status | `STALE — SUPERSEDED APPEND-ONLY` |
| Independent Fable review | `APPROVED` |
| Task-owned files | `5 / 5 BYTE-IDENTICAL` |
| Independently reproduced deltas | `2,160 / 2,160` |
| Independently reproduced concentrations | `9 / 9` |
| Significance parity | `9 / 9 MODELS` |
| Pooled-IC convention | `EQUAL-WEIGHTED WITHIN-YEAR SPEARMAN` |
| Regeneration | `COMMITTED = RUN 1 = RUN 2` |
| Protected artifacts | `11 / 11 BYTE-IDENTICAL` |
| Focused tests | `32 PASSED / 0 FAILED` |
| Complete root suite | `927 PASSED / 0 FAILED / 0 ERRORS / 0 SKIPS` |
| Documentation lint | `PASSED` |
| Claims lint | `PASSED — MCC v1.10.0` |
| Remaining limitation | `DIRECT CONCENTRATION UNIT ORACLE ABSENT — NON-BLOCKING` |
| Final state | `INTEGRATED / REVIEW APPROVED / DETERMINISTIC / CLOSED` |

## R3-NULL-01 — CLOSED (2026-08-04)

- **Task:** Negative-control / placebo laboratory.
- **Implementation commit:** `bcb5664e322033fbf966866fde6c931c08716cd5`.
- **Reviewed current-main HEAD:** `c78690d03a5c3b46710d7bc19aa92841ef819933`; implementation commit is an ancestor and first-parent ancestor of the reviewed HEAD.
- **Independent review:** Fable 5, high effort, single agent — **PASS WITH NON-BLOCKING NOTES**; `CLOSURE_RECOMMENDATION: READY_FOR_APPEND_ONLY_GOVERNANCE_CLOSURE`.
- **Verification:** focused suite **44 passed**; authoritative root suite **1464 passed, 27 warnings**; claims lint passed; docs lint passed; independent discrete-permutation/Bonferroni oracle reported `mismatch_count=0`; two disposable regeneration runs under `PYTHONHASHSEED=0` and `PYTHONHASHSEED=1` were byte-identical to the committed JSON and Markdown reports; all **981 protected tracked files** remained byte-identical.
- **Evidence integrity:** authoritative read-only V3 evidence bundle `r3-null-01-final-review-bundle-v3.V5Lecb` verified **38/38** SHA256 manifest entries with payload/manifest count parity during independent review.
- **Bounded statistical result:** **0/25** family-wise placebo rejections; `alpha × R = 1.25` is an upper reference under conservative Bonferroni control; the exact two-sided 95% zero-event Clopper-Pearson upper bound is `0.1371851715`. This remains a low-resolution negative-control smoke test and does not certify exact calibration or precisely estimate the Type-I error rate.
- **Closure disposition:** no implementation, statistical, reproducibility, isolation, claim-safety, integration, or evidence-integrity blocker remains for the bounded R3-NULL-01 repository task. No code, test, generated-report, Makefile, or artifact-registry change is required for closure.
- **What CLOSED means here:** only the authorized repository task and its internal verification obligations are complete. Nothing establishes alpha, a market signal, predictive validity, reliable predictive edge, profitability, investment value, tradability, production validity, or deployment validity. This AI repository review is not qualified-human statistical approval, external validation, or independent human attestation.

## R3-SPIKE-01 — CLOSED (2026-08-04)

- **Task:** Point-in-time BIST 100 universe-history sourcing spike.
- **Implementation commit:** `926a055f8714675f4ca12c3e37b586b2660adbd0`.
- **Authorized output:** `docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md` only.
- **Memo verdict:** `FEASIBLE_WITH_DOCUMENTED_GAPS`.
- **Independent review:** Fable 5, low effort, single agent — **APPROVED** after one bounded Internet Archive citation correction.
- **Verification:** exact one-file boundary; `git diff --check` passed; docs lint passed; claims lint passed under Model Confidence Contract v1.10.0.
- **Evidence finding:** free first-party, effective-dated scheduled BIST 100 change-event evidence exists, but no required historical period reaches `CONFIRMED`; no complete historical constituent snapshot or complete extraordinary-change stream was established.
- **Repository interpretation:** the current FinanceIQ public and training cohorts remain retrospective and are not made point-in-time valid by this memo.
- **Closure disposition:** the authorized memo-only spike is complete. No dataset, source archive, scraper, parser, configuration, model, pipeline, backend, frontend, test, generated artifact, or current result was changed.
- **Next-step boundary:** the memo recommends a separately authorized `R3-SPIKE-01a` evidence-completion spike before any historical collection or reconstruction task. This closure does not itself authorize that successor work.
- **Claim boundary:** the memo does not establish predictive edge, alpha, profitability, investment value, tradability, future performance, or point-in-time validity of existing FinanceIQ results.

## R3-AGENT-01 current-main closure (2026-08-08; append-only)

| State item | Status |
|---|---|
| Implementation commit | `17c3e87d93d774951e405d2f6419e773d2fed228` — ancestor of current `main` `82efd199457541631fd1448107979799465d2a3c` |
| Independent implementation rereview | `R3_AGENT_01_FINAL_IMPLEMENTATION_REVIEW: APPROVED`; binding-audit SHA-256 `7691d33016adffcde506b76e7476f379ce98f79171dedd4d48037764f4089f02` |
| Grounded intents | `4` deterministic additions; `5` canonical intents preserved; compatibility and fail-closed ticker contracts preserved |
| MCC / scientific boundary | `v1.10.0`; no MCC scan change, scientific artifact change, frontend change, predictive-edge, alpha, profitability, investment-value, external-validation, or production-validation claim |
| Verification | Frozen routing `13/13`; focused intents `44 passed`; grounded/API `31 passed`; current-main root `1027/1027`; backend `552/552`; claims lint, docs lint, `git diff --check` passed |
| Remaining follow-up | Authenticated E2E implementation remains separate, incomplete, and unauthorized by this closure; Phase 3E not complete |
| Scientific conclusion | No reliable predictive edge has been established |
| Final state | `INTEGRATED / INDEPENDENT_REVIEW_APPROVED / CURRENT_MAIN_VERIFIED / R3_AGENT_01_CLOSED` |

## R4-PROV-01 current-main closure (2026-08-08; append-only)

| State item | Status |
|---|---|
| Implementation and integration | Reviewed old-base commit `80a96f2db2c9863607a989e2586e8f2c47d7131f`; byte-equivalent current-main integration `82efd199457541631fd1448107979799465d2a3c` |
| Independent reviews | Packet `R4_PROV_01_PACKET_REVIEW: APPROVED`; implementation `R4_PROV_01_IMPLEMENTATION_REVIEW: APPROVED`; binding-audit SHA-256s `8149715737983b8fab24dbb7ae5c4c33c6ae27cf0a5e08d39e692f45a957fbb0` and `8f2f9c41628cc37d240be7e8e6edc4ba822e9d8059db409a7503d8f44b132161` |
| Provenance scope | Public modeling dataset only; `240 × 61 = 14,640` cells; `13,682` present; `958` null; `8,243` cell_verified; `3,715` column_asserted; `2,640` derived_chain; `42` unknown; `multi_candidate_count = 0` |
| Generated artifacts | Three `data/provenance/` artifacts present with committed SHA-256s: CSV `62a4102fb3df84774fd6f6e1a9d96412a42b9fb0df1947bf7290c54925a727eb`; JSON `441d500eedd270c47460f7c645e5de5c9864d12ba159d145ad90ae314280474a`; Markdown `b61456012d9887bb5e95e9cf2b55ad398c117f6360c9228aec14f36266289d7b` |
| Preservation / registry | Additive outside historical 351-member boundary; boundary not re-pinned or weakened; scientific values, feature-passports v1, limitations register unchanged; MCC `v1.10.0`; registry `13 governed roots / 88 entries`, schema `1.0.0`, task `R3-REL-01` |
| Verification | Focused R4 `656/656`; root `1027/1027`; backend `552/552`; data validation `VALID`; deterministic regeneration exact; claims lint, docs lint, `git diff --check` passed; repository clean; main/origin/live remote equal |
| Remaining tasks | R4-DIM-01 and R4-ROBUST-01 remain separate outstanding tasks; neither authorized or completed by this closure; Wave 4A not complete |
| Claim boundary | No point-in-time correctness, rights clearance, predictive validity, alpha, profitability, investment value, or production validity established; no reliable predictive edge established |
| Final state | `INTEGRATED / INDEPENDENT_REVIEW_APPROVED / DETERMINISTIC / CURRENT_MAIN_VERIFIED / R4_PROV_01_CLOSED` |

## CI-BOOTSTRAP-01 verification CI (2026-08-11; append-only)

| State item | Status |
|---|---|
| Scope | Pinned root verification environment (`requirements-root.txt`), GitHub Actions workflow (`.github/workflows/verify.yml`), verification-baseline truth refresh, coverage staging. No product, pipeline, model, data, or claim-surface change |
| Environment of record | CPython 3.12.3 (conda-forge), macOS 26.6 arm64; `numpy 1.26.4`, `pandas 2.2.2`, `scipy 1.13.1`, `scikit-learn 1.5.1`, `pytest 8.3.3`; local `pydantic 2.9.0`, `pydantic-settings 2.5.0`, `bcrypt 4.2.0` run ahead of the `backend/requirements.txt` pins and the delta is recorded in `docs/VERIFICATION_BASELINE.md` |
| Baseline refresh | Previous baseline dated 2026-07-18 at `18514ac5`, 51 commits stale; backend count corrected `99` → `552`; root `1081` unchanged; MCC `v1.8.0` → `v1.10.0`; `make docs-lint` row added |
| Docs lint | Was red at `18514ac5` on a dated review-closure count; four dated R3 review/packet documents added to `TRUTH_DRIFT_EXCLUSIONS`; historical counts preserved, not rewritten. Stale-fixture self-test generalized to materialize cited paths and still rejects deliberate drift |
| Coverage | `pytest-cov 5.0.0` reporting only; XML archived as a build artifact; Codecov upload staged but commented out pending a `CODECOV_TOKEN` secret; no threshold gates a run; coverage output gitignored so the contamination worktree guard stays exact |
| Verification | Clean-clone (no `.env`, no untracked files) run of the full CI sequence: root `1081/1081`, backend `552/552`, data validation `VALID`, claims lint `v1.10.0` PASSED, docs lint PASSED, docs-lint self-test PASSED; root suite also `1081/1081` under coverage instrumentation; Linux/cp312 wheel resolution of `requirements-root.txt` verified (76 wheels, transitive) |
| Not established | The workflow has not yet run on GitHub Actions; "CI green" is a local clean-clone simulation until the first remote run |
| Claim boundary | No scientific artifact, MCC scan, or user-facing copy changed; no predictive-edge, alpha, profitability, or production-validity claim; no reliable predictive edge established |

## CI-BOOTSTRAP-01 first remote run (2026-08-11; append-only)

| State item | Status |
|---|---|
| First run | GitHub Actions run `31514453938` (PR #10) FAILED at the root-suite step; install, pinned resolution, and every earlier step succeeded |
| Failure class 1 | Nine numerical byte-identity / 1e-12 parity tests (`test_contamination_lab.py`, `test_excess_basis.py`) — Linux x86_64 reproduces macOS arm64 artifacts to ~11 significant digits, not byte-for-byte; already documented as environment-qualified |
| Failure class 2 | Six output-authority fixtures (`test_missingness_sensitivity.py`) that assert on inode recycling; APFS and ext4 disagree |
| Resolution | `.github/ci-deselect.txt` lists the 15 ids with stated environment reasons; CI runs 1066/1081 and fails the build if any listed id stops resolving. No test skipped, weakened, or removed; the full suite remains the machine-of-record gate |
| Claim boundary | Deselection is environmental, not evidential: no guard was relaxed and no scientific artifact, threshold, or claim surface changed |

## CI-BOOTSTRAP-01 green (2026-08-11; append-only)

| State item | Status |
|---|---|
| Green run | GitHub Actions `31534431511` on `ci/verify-workflow` (PR #10), ubuntu-latest: root `1066 passed / 15 deselected` (5:17), backend `552 passed`, data `VALID`, claims lint `v1.10.0`, docs lint and stale-fixture self-test PASSED |
| Machine of record | Full root suite `1081/1081` on macOS arm64 conda CPython 3.12.3; the 15 CI-deselected ids pass there and remain the local gate |
| Coverage | Reported and archived as a build artifact; Codecov upload staged but commented out pending a `CODECOV_TOKEN` secret; no threshold gates a run |
| Remaining | Merge of PR #10 is the owner's decision; enabling Codecov requires the owner to create the repository entry and add the secret |

## FI-DATA-PATH-01 universe-split provenance repair (2026-08-17; append-only)

| State item | Status |
|---|---|
| Defect | `scripts/data_collection/split_universe_datasets.py` serialized `str(TRAINING_OUT)` / `str(PUBLIC_OUT)`, so `universe_split_report.json` embedded the absolute repository location of whichever machine last ran it (committed value: `/Users/salihcamci/Downloads/capstone-financeIQ/...`, a path that no longer exists) |
| Fix | Report `outputs` entries emitted as repo-relative POSIX paths via `relative_to(REPO_ROOT).as_posix()`, matching `audit_pipeline.py` and the other `data_collection` producers |
| Regeneration | `make split-datasets` |
| Split CSVs | `BYTE-IDENTICAL — modeling_dataset_training_2020_2025.csv 3923888b…70eda78, modeling_dataset_public_2020_2025.csv 891d662f…4312914b44` |
| Report change | `2 JSON LEAVES — outputs.training, outputs.public; every count, flag, and note unchanged` |
| Protected members compared vs `main` | `351 — exactly one differs: data/trusted_clean/universe_split_report.json` |
| Boundary digest | `03f9a7923e2ff3f6aff02d4d1efe83a621a5e0e26a6ebe949b2336cccadeddfd → 74a8ea09f43a260a3e4e8633ae93ff2d7c0e3c0626f5826cfba2fa1e8dc2eb03` |
| Boundary exemption | `NONE ADDED` |
| Independent pins updated | `4 — FROZEN_PROTECTED_BOUNDARY_SHA256 plus the three hard-coded test authorities, each with a truthful provenance comment` |
| Excess regeneration | `2 FILES / 8 JSON LEAVES — boundary digest, generator source hash and size, dependent report hash only` |
| Leaderboard, prediction dumps, `significance_report.md` | `BYTE-IDENTICAL` |
| Scientific leaves | `UNCHANGED — 0/6 survive Bonferroni, primary and sensitivity` |
| Data validation | `VALID — 403 rows, 40 features, 321 target rows, benchmark available` |
| Root suite | `1081 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.10.0` |
| Residual | Stale `/Users/salihcamci/Downloads/capstone-financeIQ` strings remain in four other generated reports (`pipeline_audit_report.json`, `quarterly_snapshot_inspection.json`, `yearly_snapshot_migration_report.{json,md}`); each is a separate producer and boundary member, out of scope here |
| Claim boundary | Path/provenance only: no modeling row, feature, target, or statistic changed; no reliable predictive edge established |

## FI-DATA-PATH-02B yearly-snapshot provenance repair (2026-08-18; append-only)

| State item | Status |
|---|---|
| Defect | `scripts/data_collection/extract_yearly_snapshots_to_manual_financials.py` serialized every discovered, selected, skipped, and output path with `str(Path)` at 10 sites, so `yearly_snapshot_migration_report.json` and its Markdown rendering embedded the absolute repository location of whichever machine last ran it (committed value: `/Users/salihcamci/Downloads/capstone-financeIQ/...`, a path that no longer exists) |
| Fix | Local `_relative_or_absolute(path)` helper following `experiments/contamination_lab.py`: repo-local paths emit repo-relative POSIX text, paths legitimately outside the repo (`--input-dir`, tmp_path fixtures) keep an absolute representation instead of raising. Applied to all 10 sites incl. the `rows_per_file` mapping keys; the Markdown report inherits the change through the same fields |
| Regeneration | `make extract-yearly-financials` |
| Candidate CSV | `BYTE-IDENTICAL — data/trusted_raw/financials/candidate_from_yearly_snapshots.csv 304ca2dd46e8b1108897d485aa7377f4d24adb6fcf5bbe3bffce78c47b98eebd before and after; absent from git diff` |
| Report change | `PATH LEAVES ONLY — output_rows 240, ticker_year_coverage, candidate_columns_written, columns_discovered/mapped/skipped, columns_rejected_misaligned, ambiguous_columns, annual_return_col_per_year, issues, next_command all unchanged` |
| Discovery-surface note | `input_folders_searched gained data/raw — truthful: the c1faa3ae reorganization created that directory after the reports were last regenerated. It contributes no file; files_discovered, files_skipped, year_files, and selected_file_per_year are unchanged` |
| Stale-path hits in the two reports | `35 (json) + 7 (md) BEFORE -> 0 + 0 AFTER for /Users/salihcamci/, /Downloads/capstone-financeIQ, /Desktop/Projects/First_Priority_Projects/FinanceIQ` |
| Report digests | `json b93bf915…5e38b584 → 288dcbb4…866635ed; md 59940b67…bf3eb516 → 971a2c64…8dd6378f` |
| Protected members compared vs `main` | `351 — exactly two differ: data/trusted_clean/yearly_snapshot_migration_report.{json,md}` |
| Boundary digest | `74a8ea09f43a260a3e4e8633ae93ff2d7c0e3c0626f5826cfba2fa1e8dc2eb03 → daa9ad3d216061bda7bc00b3630919f5cfffb82c2ac3fcdc830ec631a28494d6` |
| Boundary exemption | `NONE ADDED` |
| Independent pins updated | `4 — FROZEN_PROTECTED_BOUNDARY_SHA256 plus the three hard-coded test authorities, each with a truthful provenance comment; the test literals stay independent of the source constant` |
| Excess regeneration | `2 FILES / 9 JSON LEAVES — boundary digest (x4), generator source hash and size (x2 files), dependent significance_report.json hash; leaf key sets identical, 0 non-provenance leaves` |
| Leaderboard, prediction dumps, `significance_report.md` | `BYTE-IDENTICAL` |
| Scientific leaves | `UNCHANGED — 0/6 survive Bonferroni, primary and trajectory-preserving sensitivity` |
| Data validation | `VALID` |
| Root suite | `1081 PASSED / 0 FAILED` |
| Backend suite | `552 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED` |
| Out of scope | `quarterly_snapshot_inspection.json + inspect_quarterly_snapshots.py (02A), pipeline_audit_report.json (02C), bist100_benchmark_report.json (02D), and the artifact_registry.json yearly input-path inaccuracy — each a separate producer and task` |
| Claim boundary | Path/provenance only: no modeling row, feature, target, or statistic changed; no reliable predictive edge established |

## FI-DATA-PATH-02A quarterly-snapshot provenance repair (2026-08-18; append-only)

| State item | Status |
|---|---|
| Defect | `scripts/data_collection/inspect_quarterly_snapshots.py` serialized the inspected quarterly directory with `str(QDIR)`, so `quarterly_snapshot_inspection.json` embedded the absolute repository location of whichever machine last ran it (committed value: `/Users/salihcamci/Downloads/capstone-financeIQ/data/raw/quarterly_fintables`, a path that no longer exists) |
| Fix | Local `_relative_or_absolute(path)` helper following `experiments/contamination_lab.py` and the FI-DATA-PATH-02B producer: repo-local paths emit repo-relative POSIX text, a path legitimately outside the repo keeps an absolute representation instead of raising. Applied to the single `dir` site; no other path handling touched |
| Exact report | `data/trusted_clean/quarterly_snapshot_inspection.json` |
| Regeneration | `make inspect-quarterly` |
| Report change | `EXACTLY 1 JSON LEAF — dir: /Users/salihcamci/Downloads/capstone-financeIQ/data/raw/quarterly_fintables → data/raw/quarterly_fintables; files, periods, rows_per_period, frozen_columns, varying_columns, issues, and the FROZEN SNAPSHOT verdict all unchanged` |
| Markdown companion | `BYTE-IDENTICAL — data/trusted_clean/quarterly_snapshot_inspection.md 95675c8dd2110af3d6e7eff6876112e6bb359fb34857005e7973f6fe1486d87e before and after; absent from git diff` |
| Quarterly XLSX inputs | `READ-ONLY / BYTE-IDENTICAL — all 8 files under data/raw/quarterly_fintables unchanged before and after` |
| Stale-path hits in the quarterly JSON | `1 BEFORE -> 0 AFTER for /Users/salihcamci/, /Downloads/capstone-financeIQ, /Desktop/Projects/First_Priority_Projects/FinanceIQ` |
| Report digests | `json 1e11e602983f4f67892bdb3f06bb8d5f86c9f9b8c891b5329ac3cca7003c3f68 → 520b555e6e17bac8ad4471ebd7f0917a87ce739d52c9f03675dff34a6be41f60` |
| Protected members compared vs `main` | `351 — exactly one differs: data/trusted_clean/quarterly_snapshot_inspection.json; membership set unchanged` |
| Boundary digest | `daa9ad3d216061bda7bc00b3630919f5cfffb82c2ac3fcdc830ec631a28494d6 → b0fce8a3d96dc845efcff4d25c3d537b0bfb7bb42d088512410a874c4550c9b0` |
| Boundary exemption | `NONE ADDED` |
| Independent pins updated | `4 — FROZEN_PROTECTED_BOUNDARY_SHA256 plus the three hard-coded test authorities, each with a truthful provenance comment; the test literals stay independent of the source constant` |
| Excess regeneration | `2 FILES / 9 JSON LEAVES — boundary digest (x4), generator source hash and size (x2 files), dependent significance_report.json hash; leaf key sets identical, 0 non-provenance leaves` |
| Leaderboard, prediction dumps, `significance_report.md` | `BYTE-IDENTICAL` |
| Scientific leaves | `UNCHANGED — 0/6 survive Bonferroni, primary and trajectory-preserving sensitivity` |
| Data validation | `VALID — 403 rows, 40 features, 321 target rows, benchmark available` |
| Root suite | `1081 PASSED / 0 FAILED` |
| Backend suite | `552 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.10.0` |
| Out of scope | `pipeline_audit_report.json (02C), bist100_benchmark_report.json (02D), and the artifact_registry.json yearly input-path inaccuracy — each a separate producer and task` |
| Claim boundary | Path/provenance only: no modeling row, feature, target, or statistic changed; no reliable predictive edge established |


## FI-DATA-PATH-02C pipeline-audit canonical refresh (2026-08-18; append-only)

| State item | Status |
|---|---|
| Defect | `data/trusted_clean/pipeline_audit_report.{json,md}` on `main` was a descriptively stale snapshot: its tracked-CSV inventory predated five tracked CSVs, and `universe_split.outputs` still carried two absolute paths (`/Users/salihcamci/Downloads/capstone-financeIQ/...`, a location that no longer exists) |
| Producer | `NOT MODIFIED — scripts/data_collection/audit_pipeline.py already emits its own repo-local paths relatively; the two absolute strings were transitively embedded from an older universe_split_report.json snapshot and clear on regeneration. Makefile and artifact_registry.json also unmodified` |
| Fix | Canonical regeneration only: `make data-audit`. No generated JSON or Markdown was hand-edited |
| Determinism | `VERIFIED — a second make data-audit produced byte-identical JSON and Markdown` |
| Report digests | `json 598fe2717b7b9e13ce7e802472e85fe63ebd0c0e48c7521d686afa664675c82d -> 9e902e44389e7b0d843e8afaa749a70b86f7f05f8edea01db8370729ede9964a; md 2589bc9c0a14afd90f2d6529cb3dfc819171923843b4412318e55228413a252c -> b33f5f78c691a3f9b0aeb8852650639cdb28a0349b7945c691ff728fbec10bac` |
| CSV inventory | `34 -> 39 tracked CSVs` |
| Newly represented tracked CSVs | `5 — data/provenance/cell_provenance_public_2020_2025.csv; data/trusted_clean/modeling_targets_alternative.csv; data/trusted_raw/macro/cpi_yearly_tr.csv; data/trusted_raw/macro/macro_context_yearly.csv; data/trusted_raw/macro/usdtry_year_end.csv — all already tracked and all belonging under current producer semantics` |
| Classification counts | `clean_generated 3 -> 4, raw 17 -> 20, other 0 -> 1; config 3, trusted_reference 8, modeling_ready 1, public_modeling_ready 1, training_modeling_ready 1 all unchanged` |
| Stale-path hits in the regenerated reports | `2 BEFORE -> 0 AFTER for /Users/salihcamci/, /Downloads/capstone-financeIQ, /Desktop/Projects/First_Priority_Projects/FinanceIQ; universe_split.outputs.training and .public are now repo-relative` |
| Semantic leaf diff | `97 LEAVES, ALL DESCRIPTIVE — PATH_PROVENANCE 2, FILE_INVENTORY 56, MISSINGNESS_STATISTIC 21, ROW_COUNT 5, COLUMN_COUNT 5, CLASSIFICATION 8, SCIENTIFIC_MODEL_RESULT 0, OTHER 0; 0 leaves under any pre-existing file entry moved` |
| Sections byte-identical | `report, current_quality_summary, experiment_leaderboard_rows, guardrails` |
| Docs citation repair | `MECHANICAL — docs/LEGACY_DB_PATH_AUDIT.md:117 pipeline_audit_report.json:274-274 -> :304-304; the cited leaf is still the fully-missing sector entry and the claim wording is unchanged` |
| Protected members compared vs `main` | `351 — exactly two differ: data/trusted_clean/pipeline_audit_report.json and .md; membership set unchanged` |
| Member count | `351 -> 351` |
| Boundary digest | `b0fce8a3d96dc845efcff4d25c3d537b0bfb7bb42d088512410a874c4550c9b0 -> 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` |
| Boundary exemption | `NONE ADDED` |
| Independent pins updated | `4 — FROZEN_PROTECTED_BOUNDARY_SHA256 plus the three hard-coded test authorities, each with a truthful provenance comment; the test literals stay independent of the source constant` |
| Excess regeneration | `2 FILES / 9 JSON LEAVES — boundary digest (x2 per file), generator source hash and size (x2 files), dependent significance_report.json hash in the manifest; 0 non-provenance leaves moved, and 310 + 883 scientific leaves are identical` |
| Leaderboard, prediction dumps, `significance_report.md` | `BYTE-IDENTICAL` |
| Scientific leaves | `UNCHANGED — 0/6 survive Bonferroni, primary and trajectory-preserving sensitivity` |
| Data validation | `VALID — 403 rows, 40 features, 321 target rows, benchmark available` |
| Root suite | `1081 PASSED / 0 FAILED` |
| Backend suite | `552 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.10.0; both lint_doc_links self-tests PASSED` |
| Out of scope | `bist100_benchmark_report.json + collect_bist100_benchmark.py (02D) and the artifact_registry.json yearly input-path inaccuracy — each a separate producer and task. make benchmark was NOT run and no benchmark artifact was touched` |
| Claim boundary | Descriptive inventory/missingness refresh only: no modeling row, feature, target, prediction, coefficient, IC, p-value, interval, or ranking changed; no reliable predictive edge established |


## FI-DATA-PATH-02D benchmark-producer path forward-fix (2026-08-19; append-only)

| State item | Status |
|---|---|
| Defect | `scripts/data_collection/collect_bist100_benchmark.py` serialized the report's top-level `output` field with `str(OUT_CSV)`, so every governed benchmark refresh re-embeds the absolute checkout path of whichever machine last ran it (committed value: `/Users/salihcamci/Downloads/capstone-financeIQ/data/trusted_raw/bist100_benchmark_returns.csv`, a location that no longer exists) |
| Scope | `FORWARD SOURCE FIX ONLY — governance decision FI_DATA_PATH_02D_SOURCE_FIX_ONLY_RECOMMENDED` |
| Fix | Local `_relative_or_absolute(path)` helper following `experiments/contamination_lab.py` and the FI-DATA-PATH-02A/02B producers: repo-local paths emit repo-relative POSIX text, a path legitimately outside the repo keeps an absolute representation instead of raising. Applied to the single `output` site; no other path handling touched |
| Producer forward-fix | `IMPLEMENTED` |
| Future generated `output` | `data/trusted_raw/bist100_benchmark_returns.csv — repo-relative POSIX` |
| Current committed report | `DELIBERATELY NOT REGENERATED — data/trusted_clean/bist100_benchmark_report.json remains known-stale in its inert output leaf` |
| Why not regenerated | Hand-editing generated artifacts is forbidden; canonical `make benchmark` performs live Yahoo acquisition, which would constitute a scientific-data refresh; `--manual-only` is unsafe because the required manual daily inputs are absent. The stale `output` leaf is inert and no consumer reads it |
| Acquisition surface | `BYTE-UNCHANGED — fetch_yahoo, load_manual_daily, yearly_returns, validate, ensure_template, parse_tr_number, _norm all AST-extracted and SHA-256 compared old vs new; identical. main() differs by exactly 1 line (the output leaf)` |
| Verification method | `NON-NETWORK STATIC/UNIT PROBE — module imported with socket.connect/connect_ex/create_connection/getaddrinfo hard-blocked; helper(OUT_CSV) == data/trusted_raw/bist100_benchmark_returns.csv; outside-repo path returns absolute without ValueError. main(), fetch_yahoo(), urllib, and yfinance.download() were never invoked` |
| `make benchmark` | `NOT RUN` |
| Yahoo / XU100.IS / yfinance / query1.finance.yahoo.com | `NOT ACCESSED` |
| Benchmark CSV | `UNCHANGED — ccfa2bbc5a654245b39ff97dc535f59c31c08c9b9216f93dfb84c2df2a323a6b before and after; absent from git diff` |
| Report digests | `UNCHANGED — json 2d79329ad96de30b19600412f8a4cd12d3d1e5a0ad159f58c37f373f343ace66 before and after; md 14de7c4e6aa5751c43a4cfa43e36cb4fc82b5702edbda8c71a2bf2c587c81f46 before and after` |
| Benchmark observations | `UNCHANGED — 6 data rows, years 2020-2025, values 27.38 / 24.23 / 185.94 / 31.96 / 28.94 / 12.64` |
| Member count | `351 -> 351` |
| Protected membership set | `IDENTICAL — member list diffed before and after, no additions or removals` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after` |
| Re-pins | `0 — FROZEN_PROTECTED_BOUNDARY_SHA256 and all three hard-coded test digest literals untouched` |
| `experiments/results_excess` artifacts | `UNTOUCHED — make research-excess NOT RUN; no boundary authority moved` |
| Boundary exemption | `NONE ADDED` |
| Tracked files changed | `2 — scripts/data_collection/collect_bist100_benchmark.py, TASK_STATE.md` |
| Data validation | `VALID — 403 rows, 40 features, 321 target rows, benchmark available` |
| Root suite | `1081 PASSED / 0 FAILED` |
| Backend suite | `552 PASSED / 0 FAILED` |
| Docs / claims lint | `PASSED — MCC v1.10.0; both lint_doc_links self-tests PASSED` |
| Future obligation | The next governed benchmark refresh must resolve the stale `output` leaf naturally, by regenerating through the fixed producer rather than by hand-editing the report |
| PLANNING ONLY / NOT CURRENT AUTHORITY | Predicted report JSON SHA if only the `output` leaf changes: `fbfe91541099bc31938cecae49a2176f66aabc17242e34dc2e901da67702a843`. Predicted candidate boundary digest after that future governed refresh: `8640c6705939a12f31518725642d8f1765dfa24530417356e5e68e0af12ae172`. Neither value is pinned, asserted, or authoritative in this task |
| Out of scope | `artifact_registry.json entries 74/75 input declaration mismatch; the yearly artifact_registry input-path inaccuracy; the unused --force CLI argument; a report-only benchmark architecture; any benchmark data refresh; Yahoo acquisition policy — each a separate task` |
| Claim boundary | Producer path/provenance only: no modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval, or ranking changed; no reliable predictive edge established |


## FI-DATA-EXPAND-03 Stage-A expansion sourcing preregistration (2026-08-19; append-only)

| State item | Status |
|---|---|
| Task | `FI-DATA-EXPAND-03 — Stage-A sourcing preregistration only` |
| Prior adjudication carried in | `FI_DATA_EXPAND_02_METHOD_CHANGES_REQUIRED` |
| Starting HEAD | `6fde2084767a20b3fa906e9ac029bcb8bd9a22ed` (branch `main` == `origin/main`, worktree clean including untracked) |
| Deliverable | `docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md` — protocol identifier `FI-DATA-EXPAND-STAGE-A-v1` |
| Stage scope | `STAGE A ONLY — source/provenance/integrity/eligibility rules frozen before acquisition; Stage B NOT created` |
| Expansion direction | `TEMPORAL_REGIME_FIRST` — 3 confirmatory evaluation years and a single governed `regime_id` (`observed_2020_2025_macro_period`) mean added tickers cannot add temporal/regime variation; tau-based decomposition recorded as sensitivity-only; tau > 0 NOT claimed |
| Candidate search floor | `2017 = CANDIDATE_SEARCH_FLOOR` — authorizes searching only; authorizes NO year for analysis. Six gates (membership, identity, fundamentals, benchmark, data quality, provenance); any failure classifies `INSUFFICIENT_DATA` with no substitution, no proxy year, no back-fill |
| Universe rule | `RULE-DERIVED, NOT COUNT-DERIVED` — every ticker-year satisfying membership/identity/comparability/data-quality is included; no ticker target, no 60-80 goal, no power-chosen minimum N |
| Point-in-time membership | Existing sourcing-spike standard frozen: first-party effective-dated evidence preferred, `effective_from`/`effective_to` semantics mandatory, fail closed on unresolved gaps (`UNKNOWN` excluded), no backward projection of present-day membership, extraordinary/non-periodic events accounted for, ticker alone insufficient identity authority, ISIN or other evidenced stable identifier preferred |
| Identity / corporate events | Predeclared for ticker change, rename, merger, successor, delisting, IPO, post-cutoff listing, split/demerger/share-class ambiguity; no identity resolution may be inferred from apparent relatedness; unresolved identity fails closed |
| Bank / financial-firm treatment | `OPTION A — EXCLUDED FROM CONFIRMATORY COHORT`, decided from repository evidence before acquisition: `DATA_PIPELINE.md` and `data/config/bist100_candidates.csv` (`is_bank=true`; revenue = net interest income, EBITDA undefined), `data/trusted_clean/bist100_expansion_report.md` §6 ("handled as a separate sector", "no gross profit/EBITDA", exclude unless the model is restructured), 9 of the governed 40 concepts undefined/non-comparable under bank/insurance reporting, and NO comparable bank feature contract exists in the repository. Identification is evidence-based on reported statement format (`sector` is unpopulated and must not be inferred); unevidenced format fails closed. Disclosed: the current public cohort contains `TSKB` and `TURSG`, whose eligibility must be adjudicated from statement-format evidence at Stage B, not assumed |
| Frozen target hierarchy | `PRESERVED — confirmatory next_year_return_pct (nominal TRY); exploratory next_year_excess_return_vs_bist100, next_year_real_return_pct, next_year_usd_return_pct`; R3-TGT-01 authority preserved; excess NOT promoted; basis switch requires separate prior governance; no basis may be chosen after seeing expanded outcomes |
| Frozen feature authority | `40 governed features resolved from experiments/run_experiments.py::_feature_cols` against `data/trusted_clean/modeling_dataset_training_2020_2025.csv`; ordered list recorded in full; newline-joined SHA-256 `041566fc685b043c8618af859c268aa736fa5ae87b0d2679a2b35df779659575`; compact-JSON SHA-256 `f8064f43ca5a446e21b2357fdafa4a9f6a1b7dfcbe7e79b8bc0835125c452543`; the earlier 51-column exploratory count is rejected; Stage B must re-resolve, re-declare and re-hash the realized vector before fitting |
| Missingness rule | `>=26-of-40 RAW COUNT REJECTED`. Replaced by six concept groups (`SIZE_SCALE` 7, `PROFITABILITY` 9, `VALUATION` 3, `GROWTH` 5, `LEVERAGE_LIQUIDITY` 8, `PRICE_MOMENTUM` 8; 40 members, each feature in exactly one group). Exact minimum per group = **all applicable members**, each individually mandatory; an empty applicable set is never vacuously satisfied. Zero free parameters: the minimum is forced by the no-fabrication contract plus the committed `_fit_sklearn` `np.nan_to_num(X, nan=0.5)` neutral-rank imputation, not chosen. Structural non-applicability declared exactly (`pe_ratio` net_income<=0, `pb_ratio` equity<=0, `ev_ebitda` and `net_debt_to_ebitda` ebitda<=0, growth group at the earliest evidenced year, 1y/2y/3y price members by evidenced listing history; price/benchmark anchors never NA). Source-class structural missingness is missing data, NOT non-applicability, and is confirmatory-ineligible. Stage B must disclose imputed-cell counts and run a prespecified zero-imputed-cell complete-case robustness cohort |
| Missingness rationale inputs | Only already-established pre-expansion facts: public cohort 240 / min 27 / median 39 / max 40; training-only cohort 163 / min 15 / median 25 / max 26; the 14 structurally-null training-only features named. Used solely to show a raw count separates rows by source class rather than concept. No expanded data inspected; no threshold selected using IC, returns, significance, or model performance; no cohort size computed under the new rule |
| Benchmark sourcing rule | Governance principle only, nothing fetched: any pre-2020 benchmark acquisition is a NEW scientific-data acquisition — declared window before acquisition, source identity recorded, raw acquisition preserved where policy permits, derivation fixed before use, no silent refresh of the committed 2020-2025 observations, exact overlap comparison, explicit adjudication of any overlap revision, provenance manifest, no hand-edit of the generated report. The FI-DATA-PATH-02D stale `output` leaf remains a separate known issue and is NOT repaired here |
| Fundamentals sourcing rule | Feature-year T information as of the declared cutoff; no later frozen snapshot used as historical fact; no period file with known frozen/repeated values; source and effective/as-of date recorded; manual exports only under the documented ingestion contract; no fabricated values; no retrospective substitution from a later fiscal period. Recorded as motivation only and NOT adjudicated or repaired: within the current public cohort 4 of 40 tickers carry a single `revenue` value across all six years, and `TSKB`/`TURSG` carry identical `revenue`, `gross_profit` and `ebitda` values |
| Power / tau treatment | `DESCRIPTIVE / SENSITIVITY ONLY` — tau=0.093 explicitly NOT frozen as truth (numeral coincides with an observed pooled ridge IC and is not an estimate of tau); tau grid 0 / 0.05 / 0.093 / 0.15 / 0.25; neutral hypothetical absolute-IC grid 0.02 / 0.05 / 0.075 / 0.10 / 0.15 / 0.20; no uncited literature IC claim; "effective N" barred as a governance headline; MDE stated as conditional on assumptions and the realized Stage-B design |
| Regime treatment | `DESCRIPTIVE_ONLY` — one governed `regime_id` for 2020-2025; no confirmatory crisis/COVID/inflation/high-rate/low-rate label from narrative; any future deterministic rule requires separate governance before expanded equity outcomes are inspected and must use non-equity macro variables only; `bist100_return_pct` may never define a regime later evaluated on equity performance |
| Uncertainty procedure | Primary metric equal-year-weighted mean within-year Spearman IC; primary inference within-year permutation, 10,000 draws, seed 42, two-sided absolute tail, Monte Carlo +1 correction — read from `experiments/significance.py` (`DEFAULT_PERMUTATIONS`, `DEFAULT_SEED`, `(#{|null|>=|obs|}+1)/(draws+1)`); prespecified descriptive robustness: ticker-cluster bootstrap interval, leave-one-year-out pooled IC stability, random-effects tau with interval; year-cluster bootstrap and cluster-robust SE explicitly barred from primary status at a likely Y=6-9 |
| Multiplicity family | `6 ML models x 1 primary target (next_year_return_pct, nominal TRY) x 1 primary metric`; Bonferroni, FWER alpha=0.05, family size 6; six models and committed hyperparameters/seeds frozen with no tuning, no search, no post-acquisition additions; baselines remain outside the family; secondary analyses labelled; no new cross-basis multiplicity claim; anything unnamed before Stage B is `DESCRIPTIVE_ONLY` |
| No-peeking boundary | Stage B may inspect only source availability, source IDs, document hashes, membership effective dates, provenance completeness, coverage counts, missingness/data-quality gate outcomes, eligible/ineligible ticker-year identities, schema integrity. Stage B must not inspect `next_year_*` values, realized returns, benchmark-relative outcomes, ICs, predictions, scores, p-values, effect signs, rankings, or significance summaries for newly acquired years. Operational test recorded: the Stage-B freeze must be completable without loading a `next_year_*` column for any newly acquired year |
| Stopping rule | Collection ends when the search window is exhausted and every candidate year is classified by the sourcing/data-quality gates; predictive results are never an input; adding years/tickers, dropping years, changing the missingness rule, switching basis, or enlarging the model family after seeing results are all forbidden; future calendar years enter only through a separate prospective protocol |
| Null interpretation | Pre-written: failure to reject the declared within-year null under the realized Stage-B design; may exclude effects above the achieved assumption-conditional MDE band; does NOT establish no true effect, zero IC, absence of an economically interesting small effect, or generalization across unobserved regimes |
| Positive-result escalation | Pre-written mandatory ordered sequence: contamination/leakage audit; point-in-time re-verification of every contributing ticker-year; full declared multiplicity confirmation; leave-one-year-out and per-model survival review; independent untouched forward year under freeze-once governance; separate MCC/governance review. Until all six are satisfied the position remains `no reliable predictive edge established` |
| Stage-B contract stub | Present and intentionally UNPOPULATED (eligible year list, ticker-year universe, manifest hashes, realized feature-vector hash, cohort assignment, fold schedule, realized n per year, realized sensitivity/MDE table, final interpretation grid) |
| External access | `NONE — no Yahoo, no KAP, no Borsa Istanbul, no yfinance, no network fetch of any kind; no membership records, fundamentals, or benchmark values collected` |
| Datasets / models / artifacts | `UNCHANGED — make data, make benchmark, make research, make research-excess NOT RUN; no dataset, target, prediction, coefficient, IC, p-value, interval, or ranking changed` |
| Member count | `351 -> 351` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after; recomputed live from experiments/run_excess_basis.py authority` |
| Re-pins | `0 — no boundary authority or test digest literal touched` |
| Tracked files changed | `2 — docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md (new), TASK_STATE.md` |
| Docs / claims lint | `PASSED — make docs-lint, make claims-lint (MCC v1.10.0); both lint_doc_links self-tests PASSED; git diff --check clean` |
| Out of scope | Stage B itself; any acquisition; the FI-DATA-PATH-02D stale benchmark `output` leaf; the repeated-value anomaly in the committed public-cohort `revenue`/`gross_profit`/`ebitda` cells; any Option-B bank feature contract — each a separate task |
| Claim boundary | Preregistration document only: no modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval, or ranking changed; no predictive edge is claimed, implied, or anticipated; no reliable predictive edge established |
