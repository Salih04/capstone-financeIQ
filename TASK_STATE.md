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
| Remaining tasks | R4-ROBUST-01 remains outstanding; R4-DIM-01 implementation verified on branch `local/r4-dim-01-feature-dimensionality`; Wave 4A completion still requires remaining gates |
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


## FI-SOURCE-OWNER-AMENDMENT-01 owner source-use and private-archive governance (2026-08-23; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-SOURCE-OWNER-AMENDMENT-01 — governance-only owner decision record` |
| Starting HEAD | `6814f647b9a15a6d1bb9a4f247e27ce52f515027` (branch `main` == `origin/main`, worktree clean including untracked) |
| Deliverable | `docs/SOURCE_USE_OWNER_AMENDMENT.md` — decision identifier `FI-SOURCE-OWNER-AMENDMENT-01` |
| Owner internal-use authorization | `APPROVED — publicly disclosed, non-confidential financial facts from reliable sources may be collected, used, transformed and retained for FinanceIQ academic research and model development without source-by-source written permission as an INTERNAL project gate. Covers publicly disclosed Borsa Istanbul data, publicly disclosed KAP/MKK data, public market/index data, and paid/subscription exports the owner legitimately accessed under the owner's own entitlement` |
| Private-archive authorization | `APPROVED — private local research archival, SHA-256 checksums, provenance manifests, and deterministic derived/model-ready datasets` |
| Public redistribution | `NOT APPROVED — public redistribution of third-party raw datasets and publication of raw vendor files remain prohibited by project policy` |
| Also NOT approved | `credential sharing; bypass of authentication/access controls; CAPTCHA/rate-limit/access-control circumvention; use of another person's paid entitlement; any representation that a third-party licence was granted; any representation that external legal review occurred` |
| Classification distinction | `INTERNAL_OWNER_AUTHORIZED != EXTERNALLY_LICENSED — this amendment establishes the former only; as of this decision NO source in the repository is classified EXTERNALLY_LICENSED, and this amendment may never be cited to promote one` |
| External licence claim | `NONE — no licence, permission, waiver or legal conclusion from Borsa Istanbul, KAP/MKK, Yahoo, Fintables or any vendor is claimed or implied; no external legal review occurred; this is not legal advice` |
| Provenance requirement | `MANDATORY AND UNRELAXED — provider, source/product/document identifier, source URL or stable identifier, access method, access date, effective/as-of date, owner/account access class, raw filename, raw SHA-256, byte size, private/public storage classification, redistribution status, parser/transformation identity, derived outputs, acquisition notes. Unknown provenance FAILS CLOSED — no imputation, no substitution` |
| Raw storage default | `PRIVATE_LOCAL_RAW — new raw third-party/vendor bytes are NOT committed to Git merely because the repository is private. Repository may retain manifests, checksums, provenance records, transformation code, and separately-acceptable derived data. Any future decision to commit raw third-party files must be recorded separately per source` |
| Retrospective effect | `NONE — no existing raw/vendor file is deleted, moved, blessed, or reclassified; no Git history rewrite authorized; no raw file migration authorized` |
| `FI_SOURCE_AUDIT_01_PROVENANCE_GAPS_FOUND` findings | `PRESERVED AND STILL OPEN — data/raw/yearly_xlsx provider provenance unresolved (data/raw/README.md names no provider, product identifier, access method or as-of date); data/raw/quarterly_fintables owner-access provenance to be confirmed; data/trusted_raw/shares_outstanding_manual.csv upstream provenance unresolved (source column is the free-text value "user provided merged capital research" on 240 rows and empty on 246 rows)` |
| Effect on `FI-DATA-EXPAND-04A` | `INTERNAL ACCESS-GOVERNANCE BLOCKER SUPERSEDED — the self-imposed source-by-source written-permission gate for collecting publicly disclosed factual BIST/KAP information into a private research archive no longer blocks. That is the entire effect: no BIST/KAP licence is claimed, raw data stays private, public redistribution stays prohibited, no access control may be bypassed, provenance stays mandatory, and source-specific explicit technical restrictions must still be obeyed` |
| `FI-DATA-EXPAND-04A-R` | `RETAINED AS HISTORICAL EVIDENCE — not rewritten, not deleted, not reinterpreted` |
| Stage-A protocol | `UNCHANGED — docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md (FI-DATA-EXPAND-STAGE-A-v1) byte-identical, SHA-256 c5eedb6fc5e14e7ee13ec6ab4a7cd08fc70ca2066847fe3a1799752762c2513a before and after; absent from git diff. This amendment supplies the owner authorization the Stage-A sourcing workflow requires and changes source-access governance only` |
| Stage-A elements explicitly unchanged | `candidate search floor; point-in-time membership rule; target hierarchy; 40-feature vector; missingness rule; model family; multiplicity; no-peeking boundary; stopping rule; scientific interpretation` |
| External access | `NONE — no BIST, KAP/MKK, Yahoo, Fintables or vendor site accessed; no network fetch of any kind; no membership data collected; no document downloaded` |
| Data acquired | `NONE` |
| Datasets / models / artifacts | `UNCHANGED — make data, make benchmark, make research, make research-excess NOT RUN; no dataset, target, prediction, coefficient, IC, p-value, interval, or ranking changed` |
| Member count | `351 -> 351` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after; recomputed live from experiments/run_excess_basis.py authority` |
| Re-pins | `0 — no boundary authority or test digest literal touched` |
| Tracked files changed | `2 — docs/SOURCE_USE_OWNER_AMENDMENT.md (new), TASK_STATE.md` |
| Docs / claims lint | `PASSED — make docs-lint, make claims-lint (MCC v1.10.0); both lint_doc_links self-tests PASSED; git diff --check clean` |
| Out of scope | Resolving the three open provenance gaps; any acquisition; any raw-file migration or history rewrite; Stage B; the FI-DATA-PATH-02D stale benchmark `output` leaf — each a separate task |
| Claim boundary | Governance decision record only: no modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval, or ranking changed; no reliable predictive edge established |


## FI-DATA-EXPAND-04B / R3-SPIKE-01a historical BIST membership sourcing spike (2026-08-23; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B / R3-SPIKE-01a — membership/identity/provenance sourcing spike only` |
| Starting HEAD | `7bd1dfad16eb750481603f18eca916e4ab09cfc4` (branch `main` == `origin/main`, worktree clean including untracked) |
| Starting gate | `PASSED — repo path, branch, HEAD == origin/main == expected SHA, clean tree, Stage-A present, owner amendment present, boundary 351, digest matched expected` |
| Deliverables | `docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md` (new), `docs/evidence/bist_membership_source_manifest.csv` (new, 73 rows) |
| Decision | `FI_DATA_EXPAND_04B_OWNER_PURCHASE_DECISION_REQUIRED` |
| Product 3184 visible coverage | `2000-2026 inclusive, 66 catalogue objects enumerated through the product page's own pagination (4 pages: 20+20+20+6). The "since 2000" title was corroborated from the listing, not assumed` |
| Product 3184 downloadable coverage | `NONE — 0 of 66 objects acquired. Every object is ACCESS_RESTRICTED for the same reason` |
| 2017-2020 status | `VISIBLE, NOT DOWNLOADABLE — 2017:5, 2018:8, 2019:4, 2020:7 objects. Files are present, not absent; no substitution, backward extrapolation, interpolation, Wikipedia, screener or price-inferred membership was used or needed` |
| Blocking gate | `ENTITLEMENT/CONTRACT, NOT PRICE — all 66 objects list at 0.00 TRY with accessType G, but the only acquisition control is "Sepete Ekle"; completing it needs an account, and the Giris/Kayit dialog requires accepting a Kullanici Kayit Sozlesmesi plus a KVKK notice. Owner has NO existing logged-in DataStore session (verified in both the isolated browser and the owner's own Chrome profile: logged-out, empty basket)` |
| Actions NOT taken | `no account created, no credentials entered, no basket addition, no order submitted, no agreement or consent banner accepted, no payment, no authentication/CAPTCHA/rate-limit/access-control circumvention, no guessed download URL probed` |
| Format authority | `Borsa Istanbul DataStore file-format specification v1.4 (15.06.2016) s.2.1.29, acquired to PRIVATE_LOCAL_RAW, SHA-256 ab76e9708e35684410c3f082b6f8bcd6cf6cecc539f76e587c559d771f9f00cc` |
| Time semantics | `QUARTERLY, POSITIONAL — exsrk[YYYY].zip -> exsrk[YYYY].xls with fields Pay Kodu, Pay Adi, 1.Ceyrek, 2.Ceyrek, 3.Ceyrek, 4.Ceyrek. NO date field, NO effective-date field, NO ISIN or other stable identifier. Whether a quarter cell means quarter-start, quarter-end, whole-quarter or any-point-in-quarter membership is NOT documented and stays UNKNOWN` |
| Nested-index semantics | `DOCUMENTED AND DECISIVE — BIST 30 subset BIST 50 subset BIST 100, and only the narrowest index of membership is written. XU030 MUST be expanded to XU050 and XU100; XU050 MUST be expanded to XU100. Reading the BIST 100 column literally without expansion would silently drop every BIST 30 and BIST 50 constituent` |
| Point-in-time adequacy | `POINT_IN_TIME_CONFIRMED UNREACHABLE for every year from Product 3184 alone — Stage-A s.5.2 makes effective_from/effective_to mandatory and the product has no date field at all. Documented ceiling for 2000-2016 is QUARTERLY_ONLY_REQUIRES_EVENT_AUGMENTATION; for 2017-2026 it is UNKNOWN because spec v1.4 predates those objects. Realized status every year: UNKNOWN (not acquired). No year classified INSUFFICIENT_DATA` |
| Event augmentation | `REQUIRED — established from the specification, not assumed. Route NOT ASSESSED: borsaistanbul.com responded and a /duyurular route was discovered from the site's own homepage links, but whether it publishes effective-dated, per-ticker index-composition changes back to 2017, distinguishing extraordinary from periodic changes, is UNKNOWN. One guessed KAP index path returned HTTP 404 and is recorded as a failed guess, not as evidence of absence` |
| Open source gaps | `spec v1.4 currency for 2017-2026 objects unverified (byte-size discontinuities at 2019 Q3->Q4 and 2026 Q1->Q2); 2020 has two pairs of distinct objects sharing filename and publication date but differing in size (ids 982925/982927 on 27-04-2020, 1132519/1132521 on 01-10-2020) and which is authoritative is UNKNOWN; legacy 2000-2015 objects carry a date field of 31-12-(YYYY-1) against a filename year of YYYY, all bulk-uploaded 08-06-2015, and which identifies the covered year is not established` |
| Identity / succession | `NONE RESOLVED, NONE ATTEMPTED — requires the membership rows, which were not acquired. All CATALOG_ENTRY rows carry identity_status=NOT_ASSESSED. Structural gap already known: the product carries share code and bulletin name only, with no ISIN or other stable identifier, so Stage-A s.6 cases will need a separate evidenced identity source` |
| Private raw archive | `6 objects, all PRIVATE_LOCAL_RAW under ~/Documents/FinanceIQ-private-source-archive (outside the repository): 1 format-specification PDF + 5 catalogue-listing JSON snapshots. All SHA-256 hashed in the manifest and referenced only symbolically as PRIVATE_LOCAL_RAW:bist-membership/raw/<name>` |
| Repository raw bytes | `NONE — no ZIP, XLSX, PDF or HTML source byte tracked in Git; no absolute archive path written into any tracked file` |
| Membership data in repo | `NONE — ticker_or_share_code and company_name are NA on all 73 manifest rows because no membership file was opened` |
| Redistribution | `INTERNAL_OWNER_AUTHORIZED per FI-SOURCE-OWNER-AMENDMENT-01, NOT EXTERNALLY_LICENSED; no licence, permission or waiver from Borsa Istanbul is claimed or implied; public redistribution of third-party raw data remains prohibited` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no return, benchmark-relative outcome, model score, prediction, IC or p-value opened, loaded or inspected; no data/trusted_clean/modeling_dataset* or experiments/results_* file read` |
| External access | `Borsa Istanbul DataStore product page, its own catalogue-listing endpoint, and its public format-specification PDF; one reachability check of borsaistanbul.com; one failed guessed KAP path. NO Yahoo, NO benchmark series, NO fundamentals, NO Products 3180/3181` |
| Datasets / models / artifacts | `UNCHANGED — make data, make benchmark, make research, make research-excess NOT RUN; no dataset, target, feature, prediction, coefficient, IC, p-value, interval, or ranking changed` |
| Stage A | `UNCHANGED — docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md byte-identical, SHA-256 c5eedb6fc5e14e7ee13ec6ab4a7cd08fc70ca2066847fe3a1799752762c2513a before and after; not weakened, reworded or reinterpreted to fit the source` |
| Owner amendment | `UNCHANGED — docs/SOURCE_USE_OWNER_AMENDMENT.md byte-identical, SHA-256 953f2a5a594e748889a78658fd3f2ab2e52872121f5135123b4576ca81909b7f before and after` |
| Stage B | `NOT AUTHORED` |
| Member count | `351 -> 351` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after; recomputed live from experiments/run_excess_basis.py authority` |
| Re-pins | `0 — no boundary authority or test digest literal touched` |
| Tracked files changed | `3 — docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md (new), docs/evidence/bist_membership_source_manifest.csv (new), TASK_STATE.md` |
| Docs / claims lint | `PASSED — make docs-lint, make claims-lint (MCC v1.10.0); both lint_doc_links self-tests PASSED; git diff --check clean` |
| Out of scope | Acquiring any exsrk file (owner decision); assessing the Borsa/KAP event-announcement route; benchmark acquisition (Products 3180/3181, XU100 series, Yahoo); fundamentals acquisition; identity/succession classification; Stage B — each a separate task |
| Claim boundary | Sourcing-feasibility evidence only: no modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval, or ranking changed; no predictive edge is claimed, implied, or anticipated; no reliable predictive edge established |

## FI-DATA-EXPAND-04B-EVENT-01 first-party BIST/KAP index-event coverage and effective-date audit (2026-08-24; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-EVENT-01 — outcome-blind membership/effective-date sourcing audit only` |
| Starting HEAD | `cca5dc319a8837ea58f132735d7d5f0b8a7c9152` (branch `main` == `origin/main`, worktree clean including untracked) |
| Starting gate | `PASSED — repo path, branch, HEAD == origin/main == expected SHA, clean tree, Stage-A present, owner amendment present, 04B report present, 04B manifest present, boundary 351, digest matched expected (recomputed live)` |
| Deliverables | `docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md` (new), `docs/evidence/bist_membership_event_sources.csv` (new, 610 rows), `TASK_STATE.md` |
| Decision | `FI_DATA_EXPAND_04B_EVENT_STREAM_PARTIAL` |
| Event mechanism found | `TWO first-party streams. (1) https://www.borsaistanbul.com/duyurular — Drupal pager, 84 pages x 25, 2098 unique items 2012-01-02..2026-08-21, stable /duyuru/<node-id>/<slug> ids, keyword search only, and provably NOT the complete regulatory stream (carries 12 of the >=76 numbered 2021/NN circulars). (2) https://www.borsaistanbul.com/endeksler/endeks-duyurulari — the purpose-built index-announcement archive, 585 rows 2013-06-21..2026-08-20, full row set embedded and filtered client-side, with date, page-size, index-group and announcement-type filters` |
| Announcement-type taxonomy | `PUBLISHED BY THE SOURCE, not imposed by this audit — announcementType 1..5: Kural Seti Degisiklikleri (69), Endeks Iceriklerinde Yapilan Donemsel Degisiklikler (287), Endeks Iceriklerinde Yapilan Donem Ici Degisiklikler (202), Endekslere ve Referans Oranlara Iliskin Diger Duyurular (20), Islem Goren Sirketlere Yonelik Endeks Duyurulari (7)` |
| Years audited | `Primary 2017, 2018, 2019, 2020. Continuity/taxonomy/mechanism checked 2013-2026. Adjacent quarters 2016Q2-2016Q4 and 2021Q1 archived as boundary evidence` |
| Scheduled review coverage | `COMPLETE for the candidate window — 16/16 quarterly BIST Pay Endeksleri review announcements exist for 2017Q1..2020Q4, each itemising additions and removals per ticker per index for BIST 100, BIST 50 and BIST 30. Additions equal removals in every transcribed table (rulebook art. 6(c)/(d)); reserve-list size 5 through 2019Q4 and 3 from 2020Q1, matching the 2019-10-28 rule change (node 11419, circular 2019/68)` |
| Extraordinary event coverage | `ABSENT for the candidate window — EVIDENCED NEGATIVE RESULT, NOT AN ASSUMPTION. The intra-period category has ZERO rows before 2021-12-07 anywhere in the archive, and its earliest row tagged to the benchmark group BIST Pay Endeksleri / Gosterge Endeksler (XU030/XU050/XU100) is 2023-09-28. Whether no such change occurred in 2017-2020 or whether changes occurred and never entered this archive is NOT established and is not assumed either way` |
| Effective-date quality | `EXPLICIT AND DETERMINISTIC for periodic changes — every announcement states its index period as a literal date range (2017Q1 = 02/01/2017-31/03/2017, 2017Q2 = 03/04/2017-30/06/2017, ...). publication_date is NEVER equated with effective_date; they differ in every row. Period starts are trading days, NOT calendar-quarter starts. Rulebook art. 2.15/2.16 supply the rule. Extraordinary effective dates are deterministic GIVEN the trigger (art. 7: second business day after KAP publication; art. 7.1: day of closure/transfer) but the triggers themselves are unavailable for 2017-2020` |
| Per-year event-stream status | `2017 2018 2019 2020 2021 2022 = PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN; 2023 = PARTIAL_EVENT_COVERAGE (benchmark-group intra-period coverage opens 2023-09-28, mid-year); 2024 2025 = PERIODIC_REVIEWS_FOUND_BUT_EXTRAORDINARY_COMPLETENESS_UNKNOWN. NO year classified EVENT_STREAM_COMPLETE` |
| Per-year point-in-time status | `2017 2018 2019 2020 2021 2022 2023 = INSUFFICIENT_DATA; 2024 2025 = UNKNOWN (both event classes published with explicit effective dates, but no Product 3184 row acquired and extraordinary exhaustiveness unevidenced, so the test cannot be run). NO year classified POINT_IN_TIME_RECONSTRUCTIBLE` |
| Identity / succession | `INSUFFICIENT_IDENTITY_EVIDENCE on every ticker row — the series publishes share code and bulletin name only, no ISIN or stable identifier. One encountered case: node 11867 (2019Q3) prints A.V.O.D where the rest of the series prints AVOD; recorded verbatim, normalisation NOT asserted. NO merger, rename, code-change, delisting or relisting event exists in the 2017-2020 stream, because the category that would carry them is empty for those years. No continuity inferred from name similarity anywhere` |
| Reserve-list semantics | `A YEDEK entry is eligibility, NOT membership and NOT a state. 7 tickers (14 manifest rows) appear in both the CIKARILACAK and YEDEK columns of the same table in the same document, e.g. ALCTL in node 11511 (XU100, 2017Q1)` |
| Reconstruction algorithm | `SPECIFIED, NOT BUILT — 10 steps in the report s.10. Two steps are this audit's construction and are flagged as such rather than presented as published rules: same-day event ordering, and reserve consumption order (published in rank order, NOT stated to be consumed in rank order). Any unreconciled Product 3184 vs event-stream difference marks that security-period INSUFFICIENT_DATA and is never repaired` |
| Private raw archive | `29 objects, all PRIVATE_LOCAL_RAW under ~/Documents/FinanceIQ-private-source-archive (outside the repository): 20 quarterly review announcements, 4 rule-set update announcements, 2 period-correct BIST Pay Endeksleri Temel Kurallari PDFs (Ekim 2019, 20 Aralik 2018), 1 index-announcement archive snapshot, 2 general-listing pager snapshots. All SHA-256 hashed with byte size and access date, referenced only symbolically as PRIVATE_LOCAL_RAW:bist-membership/{events,raw}/<name>` |
| Repository raw bytes | `NONE — no HTML, PDF, XLSX or ZIP source byte tracked in Git; no absolute archive path written into any tracked file` |
| Governed provenance namespace | `UNTOUCHED — nothing written under data/provenance/` |
| Manifest row count | `610 — ADD 190, REMOVE 190, reserve-list OTHER_MEMBERSHIP_RELEVANT 195, mechanism/rulebook/rule-set OTHER_MEMBERSHIP_RELEVANT 9, evidenced-negative-result OTHER_MEMBERSHIP_RELEVANT 6, REVIEW_SCHEDULE 20. ADD/REMOVE by index: XU100 224, XU050 126, XU030 30; XU100 restricted to 2017-2020 contributes 198 rows` |
| Not transcribed, deliberately | `BIST Likit Banka and BIST Banka Disi Likit 10 tables present in the later announcements — no first-party index code was established for them, so no code was invented; each affected REVIEW_SCHEDULE row records the omission` |
| KAP / MKK | `KAP is the TRIGGER authority under rulebook art. 7 but is NOT a source of index-composition announcements for the candidate window: the earliest archive row targeting a KAP disclosure is 2023-09-27; every 2013-2022 row targets a borsaistanbul.com node. No 2017-2020 Borsa index-composition disclosure was found, claimed or inferred. MKK not required by any resolved question` |
| Actions NOT taken | `no Product 3184 file downloaded, no DataStore registration or login, no contract or consent accepted, no purchase, no fundamentals collected, no benchmark returns collected, no future returns inspected, no model scores/ICs/p-values inspected, no model run, no Stage B authored, no Stage A modification, no owner-amendment modification, no integration into any modeling dataset` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no return, benchmark-relative outcome, model score, prediction, IC or p-value opened, loaded or inspected; no data/trusted_clean/modeling_dataset* or experiments/results_* file read` |
| Datasets / models / artifacts | `UNCHANGED — make data, make benchmark, make research, make research-excess NOT RUN; no dataset, target, feature, prediction, coefficient, IC, p-value, interval or ranking changed` |
| Stage A | `UNCHANGED — docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md byte-identical, SHA-256 c5eedb6fc5e14e7ee13ec6ab4a7cd08fc70ca2066847fe3a1799752762c2513a before and after` |
| Owner amendment | `UNCHANGED — docs/SOURCE_USE_OWNER_AMENDMENT.md byte-identical, SHA-256 953f2a5a594e748889a78658fd3f2ab2e52872121f5135123b4576ca81909b7f before and after` |
| 04B report / manifest | `UNCHANGED — docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md SHA-256 0cba78d18be5e7e2061cc38478cbe251a8a4db775a5acfe4e8e4505f3b5b1c63 and docs/evidence/bist_membership_source_manifest.csv SHA-256 c1426e666529f4c2c5f05422a7dd13c387f8869273c6ff3277dd19e4620979d7 before and after; not rewritten, no link edits needed` |
| Stage B | `NOT AUTHORED` |
| Member count | `351 -> 351` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after; recomputed live from experiments/run_excess_basis.py authority` |
| Re-pins | `0 — no boundary authority or test digest literal touched` |
| Tracked files changed | `3 — docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md (new), docs/evidence/bist_membership_event_sources.csv (new), TASK_STATE.md` |
| Out of scope | Acquiring any Product 3184 file (owner decision); KAP trigger-event feasibility for 2017-2020; benchmark acquisition (Products 3180/3181, XU100 series, Yahoo); fundamentals acquisition; Stage B — each a separate task |
| Claim boundary | Sourcing-feasibility evidence only: a complete periodic announcement series does not make a historical universe valid, more covered years do not improve any estimate, event reconstruction does not establish model validity, and sourcing success does not imply predictive edge. No modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval or ranking changed; no reliable predictive edge established |

## FI-DATA-EXPAND-04B-KAP-TRIGGER-01 KAP trigger-event and reserve-consumption feasibility audit (2026-08-24; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-KAP-TRIGGER-01 — outcome-blind trigger-event and reserve-semantics sourcing audit only` |
| Starting HEAD | `dae9d364406bcfef1b3a540236078f78ad9c79d4` (branch `main` == `origin/main`, worktree clean including untracked) |
| Starting gate | `PASSED — repo path, branch, HEAD == origin/main == expected SHA, clean tree, Stage-A present, owner amendment present, 04B report/manifest present, event audit/manifest present, boundary 351, digest matched expected (recomputed live from experiments/run_excess_basis.py authority)` |
| Deliverables | `docs/BIST_MEMBERSHIP_KAP_TRIGGER_AUDIT.md` (new), `docs/evidence/bist_membership_kap_trigger_sources.csv` (new, 191 rows), `TASK_STATE.md` |
| Decision | `FI_DATA_EXPAND_04B_KAP_TRIGGER_PARTIAL` |
| Prior finding CORRECTED on first-party evidence | `FI-DATA-EXPAND-04B-EVENT-01 s.2.3/s.5 recorded that KAP is NOT a source of index-composition announcements for 2017-2020 and that no such disclosure was found. KAP carries 107 Borsa Istanbul "Endeks Sirketlerinde Degisiklik" disclosures for 2017-2020 (23/27/26/31), earliest inspected 581584 of 18.01.2017. The prior negative was CORRECT about the borsaistanbul.com/endeksler/endeks-duyurulari archive (its intra-period category is genuinely empty before 2021-12-07) and WRONG to extend that to KAP. The prior report and manifest are NOT edited by this task; the correction is recorded in the new report and manifest only` |
| KAP search mechanism | `https://www.kap.org.tr/tr/bildirim-sorgu (Detayli Sorgulama). Transport POST /tr/api/disclosure/members/byCriteria. Filters: inclusive YYYY-MM-DD fromDate/toDate; mkkMemberOidList and inactiveMkkMemberOidList company filters; disclosureClass ALL/FR/ODA/DUY/DG; subjectList over a published 202-entry subjectOid taxonomy; sector, market and (present-day) index filters. Source-stated result cap 2000 rows, which never bound. Stable numeric disclosureIndex; PDF at /tr/api/BildirimPdf/<id>; structured body plus attachment list at /tr/api/notification/attachment-detail/<id>; attachments at /tr/api/file/download/<objId>. Publication date AND time to the second` |
| Method finding (fail-closed) | `CRITICAL — under throttling the query endpoint returns an EMPTY BODY, which a naive client parses as zero results. An empty body is NOT evidence of zero disclosures. Several first-pass counts were empty-body artefacts and were discarded. Every reported count comes from a client that accepts a result only when the body parses as a JSON array and otherwise retries with backoff; a query that never returns an array is recorded SEARCH_INCOMPLETE and is never converted into a negative` |
| Period-correct rule authority | `EIGHT BIST Pay Endeksleri Temel Kurallari revisions were announced 2015-11-27..2020-09-18. FIVE new versions were retrieved via the versioned PDF links carried by their own rule-set announcements (Kasim 2015 node 11703, Mayis 2018 node 12514, Haziran 2018 node 12485, Aralik 2018/10.12 node 12289, Nisan 2020 node 12553) plus circular 2020/60 (node 12592). The Aralik 2018/20.12 and Ekim 2019 versions were REUSED from the prior audit, not reacquired. The Ocak 2020 version (node 12574) is NOT RETRIEVABLE: that node links the UNVERSIONED path /files/bist-pay-endeksleri-temel-kurallari.pdf which today serves the Aralik 2018 text. Recorded as a gap; no substitution made` |
| Rules that changed inside the window | `Reserve count BIST 100 5 -> 3 and BIST 30 2 -> 3, BIST 50 3 -> 3 at Ekim 2019 (matches the reserve-list sizes independently transcribed by the prior audit). BIST 100 periodic thresholds ranks 90/110 -> 95/105 at Ekim 2019. Ekim 2019 DELETES the A/B/C/D list-transition trigger (old art. 7.3) and DELETES the reserve-replacement sentence from art. 7.2 — so applying the Ekim 2019 rules to 2017 would miss two trigger classes that were live in 2017. Art. 7 chapeau gains a deeming rule at Ekim 2019; the second-business-day consequence is identical in all versions. Art. 8.3 (any matter not regulated is determined AND announced by the General Directorate) is unchanged in every version` |
| Search universe | `TWO populations. (a) PRIMARY, issuer-side and population-free: the Endeks Sirketlerinde Degisiklik subject queried per year with NO company filter, capturing every index-membership change Borsa announced on KAP for any security. (b) CROSS-CHECK ONLY, membership-derived from docs/evidence/bist_membership_event_sources.csv XU100 ADD/REMOVE/reserve rows: 2017=38, 2018=52, 2019=44, 2020=68, union=119 tickers. Population (b) is NOT the constituent list — it holds only shares that changed or were reserves at a period boundary, roughly a third of the index. The full point-in-time constituent set is still unacquired, so a per-security exhaustive search over ~100 constituents per quarter CANNOT be defined and none is claimed. 19 of the 119 tickers do not resolve to a current KAP member (later merged or delisted). No model-ready data was loaded to obtain any ticker` |
| Trigger events found | `EIGHT BIST 100 membership-changing intra-period events, none available to the prior audit. 2017: MAVI in / AYEN out eff 2017-06-21 (IPO fast entry, arts. 5.6.b/7.5/7.6 cited); NTTUR out / HURGZ in eff 2017-10-20 (Net Holding-Net Turizm merger). 2018: ENJSA in / CRFSA out eff 2018-02-14; MPARK in / KLGYO out eff 2018-02-19; SOKM in / DGATE out eff 2018-05-24 (all IPO fast entry, arts. 7.5/7.6); KIPA out / ITTFH in eff 2018-09-03 (Migros-Kipa merger). 2019: ZERO. 2020: ADANA out / SARKY in eff 2020-05-21 (Oyak Cimento merger, art. 7.11 cited); ANACM+SODA+TRKCM out eff 2020-10-01 with NO BIST 100 replacement named (Sise Cam merger). Events 1-7 are balanced; event 8 is not. 38 per-ticker-per-index manifest rows, of which 17 are XU100` |
| Effective-date derivation | `HIGH QUALITY, and no derivation was needed. Every one of the 107 disclosures PRINTS Gecerlilik Tarihi per row and the printed date IS the effective date. No business-day arithmetic, no weekday approximation, no Borsa holiday calendar was used or required. Publication date AND time are recorded, so the art. 7 16:30 cut-off is checkable rather than assumed; every event was published after 16:30 (earliest 16:41:20). NO EFFECTIVE_DATE_UNRESOLVED row arises from dating` |
| Reserve consumption | `RESERVE_CONSUMPTION_REQUIRES_EVENT_CONFIRMATION. The reserve list IS ranked — Borsa's own 20.05.2020 disclosure calls Sarkuysan the share "determined as the 1.yedek for the BIST 100 index" for 2020Q2, the first located first-party statement that the published order carries a rank. NO rulebook version in the window states a consumption ORDER; every one says only "yerlerine yedek paylar alinir"/"yedeklerden tamamlanir". The printed order is not self-evidently a rank: in 2016-2019 announcements the ADD/REMOVE columns are not alphabetical and neither is the reserve column, while from 2020Q1 ADD/REMOVE ARE alphabetical and the reserve column is not; the row number is never labelled by the source. Borsa NAMES the replacement in events 2, 6 and 7 — but NOT in event 8. Already-consumed-reserve skipping and nested-index interaction are UNKNOWN (unobserved in the window). Art. 8.3 leaves the unregulated part to a General Directorate determination that is ANNOUNCED, so consumption is deterministic CONDITIONAL on the disclosure and not from the rules alone` |
| Same-day ordering | `UNRESOLVED — FAIL-CLOSED. Event 8 takes effect 2020-10-01, which is also the first day of the 2020Q4 index period (01/10/2020-31/12/2020) announced 2020-09-18. On that date a merger removes three BIST 100 constituents with no named replacement while the periodic review applies its own additions and removals. Three readings are possible (review already anticipated the removals; removals apply after the review and are filled from the 2020Q4 reserve list ECZYT/EGGUB/KONYA; the index ran below 100). No first-party ordering rule was located and no announcement resolves it. Reconstruction is marked fail-closed at 2020-10-01; the prior audit's s.10 step 6 same-day ordering remains that audit's construction, unsupported by first-party evidence` |
| Identity / succession | `NTTUR->HURGZ, KIPA->ITTFH, ADANA->SARKY: SUCCESSION_RULE_CONFIRMED for the removal, DISTINCT_SECURITY for the entry, each asserted by Borsa's own causal sentence. Mardin Cimento -> OYAK CIMENTO: SAME_SECURITY_CONTINUITY_CONFIRMED — the merger attachment lists the surviving entity under the PRE-EXISTING share code MRDIN with the bulletin name changed, so continuity comes from the source's own code, not name similarity. ANACM/SODA/TRKCM -> Sise Cam: SUCCESSION_RULE_CONFIRMED for the removals, INSUFFICIENT_IDENTITY_EVIDENCE for any BIST 100 replacement. NO ISIN in this disclosure type; the mkkMemberOid GUID is a KAP MEMBER identifier, not a security identifier. No continuity inferred from names anywhere. The prior A.V.O.D/AVOD case is untouched and remains unresolved` |
| Negative-evidence standard | `NOT SATISFIED FOR EXHAUSTIVENESS, and for a demonstrated reason. (1) The 2017Q2 periodic review Borsa published on its own site 2017-03-20 (node 11492) is ABSENT FROM KAP: subject BIST Pay Endeksleri 2017 returns 6 rows, subject Endeks Sirketlerinde Degisiklik 2017 returns 23, and an unfiltered whole-DUY-class query for 2017-03-17..2017-03-25 returns 170 rows — none carries it, while the other three 2017 reviews and all twelve 2018-2020 reviews are present. If a scheduled announcement can be missing from this channel inside the window, an intra-period one can be too. (2) No first-party completeness or retention statement was located; the subject itself returns 0 rows for 2009-2015 and 11 for 2016, so it cannot reach earlier years. Classification: TRIGGER_EVENT_FOUND 8 disclosures / 38 rows; NO_TRIGGER_EVENT_EVIDENCED 99 index-change disclosures + 30 trigger-fact disclosures read in full; SEARCH_INCOMPLETE 3; AMBIGUOUS 1 (EMNIS 2018-09-26)` |
| Independent cross-check | `The Pazar Degisikligi and Kottan Cikarma subjects carry the art. 7.1/7.2 trigger FACTS independently of the index consequence. 30 of them exist in 2017-2020 (26 market transfers, 4 delistings) and 29 pair with an Endeks Sirketlerinde Degisiklik disclosure published within 45 days sharing a share code. The one exception, EMNIS on 2018-09-26, is recorded AMBIGUOUS rather than explained away; EMNIS is not in the membership-derived universe for any candidate year. The Birlesme subject (443 disclosures in the window, 261 naming a universe ticker) was queried but NOT used to derive events: those are process filings, and the KAP route makes derivation unnecessary because Borsa publishes the consequence itself` |
| Per-year trigger-stream status | `2017 2018 2019 2020 = TRIGGER_STREAM_PARTIAL. NO year is TRIGGER_STREAM_COMPLETE or TRIGGER_STREAM_COMPLETE_WITH_ZERO_EVENTS — the latter requires the complete applicable search population under s.8, and the constituent list needed to define a per-security population is unacquired` |
| Per-year point-in-time status | `2017 2018 2019 2020 = INSUFFICIENT_DATA. NO year is POINT_IN_TIME_RECONSTRUCTIBLE. Now evidenced and deterministic: the extraordinary-event stream, the per-event index-level consequence, the PRINTED effective date, publication timestamps precise enough to test the art. 7 cut-off, period-correct rule text for the whole window except 2020-01-20..2020-04-06, and reserve consumption in three of four merger cases. Still missing: a point-in-time seed constituent list (Product 3184, owner decision), a first-party basis for asserting KAP exhaustiveness, a same-day ordering rule, and the resolution of event 8` |
| Private raw archive | `141 objects added, all PRIVATE_LOCAL_RAW under ~/Documents/FinanceIQ-private-source-archive (outside the repository): 107 KAP disclosure bodies as structured JSON, 17 KAP disclosure attachments, 5 KAP query result sets, 1 KAP query-surface snapshot, 5 newly retrieved period-correct rulebook PDFs, 1 circular 2020/60 PDF, 5 rule-set announcement snapshots. All SHA-256 hashed with byte size and access date in ~/Documents/FinanceIQ-private-source-archive/bist-membership/manifests/kap_trigger_objects_2026-08-24.csv, referenced only symbolically as PRIVATE_LOCAL_RAW:bist-membership/{raw,kap-triggers}/<name>` |
| Repository raw bytes | `NONE — no HTML, JSON, PDF or XLSX source byte tracked in Git; no absolute archive path written into any tracked file` |
| Governed provenance namespace | `UNTOUCHED — nothing written under data/provenance/` |
| Manifest row count | `191 — benchmark-index event rows 38, index-change disclosures reviewed with no benchmark effect 99, art. 7.1/7.2 trigger-fact cross-check rows 30, period-correct rule authority 13, per-year search-scope/negative-evidence records 4, KAP mechanism and taxonomy 3, archive-completeness findings 2, prior-finding correction 1, AMBIGUOUS 1. NA convention unchanged from the 04B manifests; no cell is blank; Turkish characters transliterated to ASCII for consistency with the sibling manifests` |
| Actions NOT taken | `no Product 3184 file downloaded, no DataStore registration or login, no KAP account created, no contract or consent accepted, no purchase, no fundamentals collected, no benchmark returns collected, no future returns inspected, no model scores/ICs/p-values inspected, no model run, no Stage B authored, no Stage A modification, no owner-amendment modification, no edit to the prior 04B or event-audit evidence, no integration into any modeling dataset` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no return, benchmark-relative outcome, model score, prediction, IC or p-value opened, loaded or inspected; no data/trusted_clean/modeling_dataset* or experiments/results_* file read for its values` |
| Datasets / models / artifacts | `UNCHANGED — make data, make benchmark, make research, make research-excess NOT RUN; no dataset, target, feature, prediction, coefficient, IC, p-value, interval or ranking changed` |
| Stage A | `UNCHANGED — docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md byte-identical, SHA-256 c5eedb6fc5e14e7ee13ec6ab4a7cd08fc70ca2066847fe3a1799752762c2513a before and after` |
| Owner amendment | `UNCHANGED — docs/SOURCE_USE_OWNER_AMENDMENT.md byte-identical, SHA-256 953f2a5a594e748889a78658fd3f2ab2e52872121f5135123b4576ca81909b7f before and after` |
| 04B report / manifest | `UNCHANGED — docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md SHA-256 0cba78d18be5e7e2061cc38478cbe251a8a4db775a5acfe4e8e4505f3b5b1c63 and docs/evidence/bist_membership_source_manifest.csv SHA-256 c1426e666529f4c2c5f05422a7dd13c387f8869273c6ff3277dd19e4620979d7 before and after` |
| Event audit / manifest | `UNCHANGED — docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md SHA-256 7c7bfdf78f115a2536287b694bf37b6cde98ba065df985fe821cf4a33472435a and docs/evidence/bist_membership_event_sources.csv SHA-256 db2b2b3a09455f52f0c9a744367b8ec404712fb31479c7a6020db6116a8f2a42 before and after; the corrected finding is recorded in the NEW report only` |
| Stage B | `NOT AUTHORED` |
| Member count | `351 -> 351` |
| Boundary digest | `UNCHANGED — 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 before and after; recomputed live from experiments/run_excess_basis.py authority` |
| Re-pins | `0 — no boundary authority or test digest literal touched` |
| Tracked files changed | `3 — docs/BIST_MEMBERSHIP_KAP_TRIGGER_AUDIT.md (new), docs/evidence/bist_membership_kap_trigger_sources.csv (new), TASK_STATE.md` |
| Out of scope | Acquiring any Product 3184 file (owner decision); resolving BIST 100 membership on 2020-10-01 from the Borsa daily bulletin or the numbered circular series; benchmark acquisition (Products 3180/3181, XU100 series, Yahoo); fundamentals acquisition; Stage B — each a separate task |
| Claim boundary | Sourcing-feasibility evidence only: finding the extraordinary-event stream does not make a historical universe valid, more covered years do not improve any estimate, event reconstruction does not establish model validity, and sourcing success does not imply predictive edge. No modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval or ranking changed; no reliable predictive edge established |

## FI-DATA-EXPAND-04B-COLLISION-2020-01 Şişecam/Q4 2020-10-01 BIST 30/50/100 collision audit (2026-08-24; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-COLLISION-2020-01 — outcome-blind first-party collision audit only` |
| Starting HEAD | `4d60c7b8cb5da3c0a8942ae88660efc25e99392` (branch `main` == `origin/main`, worktree clean including untracked) |
| Starting gate | `PASSED — exact repo, branch, HEAD == origin/main == expected SHA, clean tree, prior evidence present, boundary 351, digest matched expected` |
| Deliverables | `docs/BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md`, `docs/evidence/bist_membership_2020_10_01_sources.csv` (8 rows), `TASK_STATE.md` |
| Decision | `FI_DATA_EXPAND_04B_COLLISION_2020_RESOLVED` |
| First-party resolution | `Borsa announcement 14118 explicitly anticipated the Şişecam merger in the 2020Q4 selection; KAP 877486 confirms 2020-10-01 distribution; official 2020-10-01 Günlük Bülten flags SISE in XU100/XU030 and reports 100/30 members` |
| Exact index changes | `XU100 ADD AKSGY/ALCTL/ARDYZ/INDES/PETUN/PNSUT; REMOVE ANACM/GLYHO/KARSN/KLMSN/SODA/TRKCM. XU050 ADD ALKIM/ECILC/TRGYO/TURSG; REMOVE ANACM/FROTO/SODA/TRKCM. XU030 ADD GUBRF/OYAKC; REMOVE SODA/TRKCM. Reserves remain published eligibility lists.` |
| Identity / succession | `SISE absorbing/surviving code: SUCCESSION_RULE_CONFIRMED + DISTINCT_SECURITY relative to absorbed codes. ANACM/DENCM/SODA/TRKCM: SUCCESSION_RULE_CONFIRMED. No continuity inferred from names.` |
| Reserve consumption | `RESERVE_CONSUMPTION_EVENT_CONFIRMED — no XU100/XU050/XU030 reserve consumed because of the merger; general sequential reserve order remains unstated.` |
| Same-day ordering | `FINAL_STATE_DETERMINISTIC_ORDERING_UNSPECIFIED — merger and Q4 period both begin 2020-10-01; Borsa publishes final affected treatment but not internal sequence.` |
| Q4 reconciliation | `RECONCILIATION_REQUIRES_PRODUCT_3184_ROWS — event patch is deterministic; Product 3184 rows and full XU050 seed remain owner/data-access work.` |
| Negative evidence | `SEARCH_INCOMPLETE — bounded 2020/58–2020/62 screen found no correction/superseding index notice; no global circular-series absence claim.` |
| Private raw archive | `1 new object — thb202010011.zip, 58182 bytes, SHA-256 32b8b67be897570d48b7f0d0b764b7b5560e39fdad2355711381e2a7d9dda9dd` |
| Repository raw bytes | `NONE — no HTML, JSON, PDF, or ZIP source bytes tracked in Git; no data/provenance change` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no returns, benchmark-relative outcomes, model outputs, or modeling artifacts inspected; no model/data/research command run` |
| Stage A / owner amendment / prior evidence | `UNCHANGED — no prior evidence file edited` |
| Member count / boundary | `351 -> 351; digest unchanged at 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` |
| Out of scope | `Product 3184 acquisition, Stage B, models, returns/outcomes, data/provenance, and any prior evidence rewrite` |

## FI-DATA-EXPAND-04B-P3184-2020-01 Product 3184 2020 acquisition / revision / Q4 reconciliation (2026-08-24; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-P3184-2020-01 — outcome-blind Product 3184 2020 catalogue inspection and acquisition attempt only` |
| Starting HEAD | `c719982fd7eae31dc57c4e4d769d7122d63e3d3e` (branch `main` == `origin/main`, worktree clean including untracked) |
| Starting gate | `PASSED — exact repo, branch, HEAD == origin/main == expected SHA, clean tree, all prior 04B evidence present, boundary 351, digest matched expected` |
| Deliverables | `docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md`, `docs/evidence/bist_membership_p3184_2020_sources.csv` (11 rows), `docs/evidence/bist_membership_p3184_2020_q4_rows.csv` (schema header, 0 data rows), `TASK_STATE.md` |
| Decision | `FI_DATA_EXPAND_04B_P3184_2020_LOGIN_REQUIRED` |
| DataStore access | `NO_EXISTING_OWNER_SESSION — product page renders the anonymous Giriş control, basket 0/0.00, every catalogue object inLibrary=false; continuation requires account registration plus acceptance of the Kullanıcı Kayıt Sözleşmesi, which is a new contractual entitlement outside owner authorization` |
| 2020 object inventory | `COMPLETE — 7 objects at catalogue positions 25-31 of 66, all named exsrk2020.zip, all 0.0 TRY, accessType G, period Q, provider date field 30-12-2020; publications 02-01-2020, 27-04-2020 (x2), 22-05-2020, 28-07-2020, 01-10-2020 (x2)` |
| Revision semantics | `REVISION_SEMANTICS_UNRESOLVED — no revision/version/supersession/language field exists; two publication dates each carry two differently sized objects; declared size is non-monotonic across 2020 (28-07 object 59,259 bytes exceeds both 01-10 objects at 58,631 and 58,823), so "newest is canonical" is unsupported` |
| Material 2020 hazard | `Last 2020 object was published 2020-10-01, the exact Şişecam merger effective date and Q4 review start; no later 2020 republication exists, so whether the Q4 column is pre-event, post-event, or unpopulated is decidable only from acquired bytes` |
| Raw acquisition | `NO exsrk2020.zip OBJECT ACQUIRED — 4 catalogue-metadata JSON pages archived privately; their SHA-256 digests are byte-identical to the 2026-08-23 BM-003..BM-006 snapshots, confirming no catalogue drift` |
| Format verification | `NOT_VERIFIED_NO_FILE_ACQUIRED — flagged: the product page currently declares 3 fields (PAY KODU, PAY ADI, BULUNDUĞU ENDEKS) while format specification v1.4 documents 6 (Pay Kodu, Pay Adı, 1.-4. Çeyrek); applicability of either layout to exsrk2020.zip is UNKNOWN` |
| Q4 rows / index counts | `0 rows extracted; literal and nested-expanded XU030/XU050/XU100 counts UNAVAILABLE (not zero); neither NESTED_COUNTS_RECONCILED nor NESTED_COUNTS_MISMATCH issued` |
| Collision reconciliation | `NOT_PERFORMED — prior audit FI_DATA_EXPAND_04B_COLLISION_2020_RESOLVED stands unchanged and unreinterpreted; its RECONCILIATION_REQUIRES_PRODUCT_3184_ROWS prerequisite is unchanged; SISE/ANACM/DENCM/SODA/TRKCM row-level checks remain outstanding` |
| XU050 seed state | `XU050_SEED_STATE_UNRESOLVED` |
| Revision canonicalization | `REVISION_CANONICALIZATION_UNRESOLVED — no raw object acquired, no mechanical comparison possible, no filesystem timestamp used as authority` |
| Q4 state | `Q4_STATE_UNRESOLVED — 2020 is NOT promoted toward Stage-B eligibility and a separate year-level closure adjudication remains required` |
| Private raw archive | `4 new objects under ~/Documents/FinanceIQ-private-source-archive/bist-membership/raw/p3184-2020/, catalogue metadata only, containing no membership row, ticker, company name, or index code` |
| Repository raw bytes | `NONE — no ZIP, XLS, XLSX, PDF, HTML, or JSON source bytes tracked in Git; no data/ or data/provenance change` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no modeling dataset, results namespace, next_year_* column, benchmark-relative outcome, IC, p-value, or model output inspected; make data / benchmark / research / research-excess not run` |
| Stage A / owner amendment / prior evidence | `UNCHANGED — no prior evidence file edited` |
| Member count / boundary | `351 -> 351; digest unchanged at 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` |
| Out of scope | `Account registration or agreement acceptance (owner decision), Stage B, models, returns/outcomes, fundamentals, data/provenance, and any prior evidence rewrite` |
| Claim boundary | Sourcing-feasibility and catalogue-inventory evidence only: enumerating catalogue objects does not make a historical universe valid, does not improve any estimate, and does not establish model validity. No modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval or ranking changed; no reliable predictive edge established |

## FI-DATA-EXPAND-04B-P3184-Q4-RESOLUTION Product 3184 2020 Q4 documentation reconciliation (2026-08-25; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-P3184-Q4-RESOLUTION — documentation and evidence reconciliation only, using an owner-supplied private local evidence archive; no DataStore access, browser automation, or authentication performed` |
| Deliverables | `docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md (§16 addendum added)`, `docs/evidence/bist_membership_p3184_2020_sources.csv (11 -> 14 rows)`, `docs/evidence/bist_membership_p3184_2020_q4_rows.csv (0 -> 100 data rows)`, `TASK_STATE.md` |
| Evidence basis | `Private local archive ~/Documents/FinanceIQ-private-source-archive/P3184_2020/exsrk2020_all/ — exsrk2020.zip (58823 bytes, SHA-256 5ad33b895bea97647ed6809f45609f2fc0782fa9f887117aa59c26ae1cf145a8) and exsrk2020 (1).zip (58631 bytes, SHA-256 ed59e80e386c9b54058215996ef186849aa3bca144e0cc7f59227f92a889d73c), both for the 01-10-2020 publication; extracted exsrk2020.xls per file (45963bdbb706eee8105fa70967ffc02ba7d029649ca53c19a18547101bac3ac2 and de44aa20b70d2021d8301a726a157e3d92525a7a91690ed1ebfece06259ceb34, respectively)` (digests written in full 2026-08-25; the abbreviated forms previously here truncated to a tail belonging to a different archive file — see the provenance-repair entry below) |
| Revision canonicalization | `REVISION_CANONICALIZATION_UNRESOLVED -> REVISION_CANONICALIZATION_RESOLVED — both 01-10-2020 catalogue candidates extracted and converted; 436 lines x 7 columns each; converted CSV exports cell-identical (in fact byte-identical, SHA-256 4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892); binary workbook files differed, but the exact binary-level cause was not fully attributed` (binary-cause wording corrected 2026-08-25 — see the provenance-repair entry below; the status itself is unchanged and rests on cell equality alone) |
| Q4 state | `Q4_STATE_UNRESOLVED -> Q4_STATE_RESOLVED — 100 Q4 (2020-10-01) membership rows extracted; XU030=30, XU050=20, XU100=50 literal; nested-expanded XU030=30/XU050=50/XU100=100, XU030 and XU100 match the official 2020-10-01 Günlük Bülten counts (§16.3)` |
| Glass group snapshot | `SISE present (XU030); ANACM, DENCM, SODA, TRKCM absent from the Q4 2020 snapshot — consistent with the prior collision audit's surviving/absorbed-code finding; no merger mechanics inferred beyond membership presence/absence` |
| Remaining limitations | `Full §9 row-level reconciliation (exact ADD/REMOVE sets, reserve consumption) not performed beyond the presence/absence check; XU050_SEED_STATE_UNRESOLVED remains open pending an independent first-party 50-count; ~~the other five 2020 catalogue objects (02-01, 27-04 x2, 22-05, 28-07) were not acquired and remain outside this evidence set~~ → superseded 2026-08-25: archive material for all five now exists in the private evidence archive at status ARCHIVE_PRESENT_NOT_OBJECT_BOUND (declared-size catalogue binding only, no content-level reconciliation performed) — see the FI-DATA-EXPAND-04B-P3184-2020-PROVENANCE-REPAIR entry below; 2020 is NOT promoted to Stage-B eligibility by this addendum` |
| Repository raw bytes | `NONE — no ZIP or XLS bytes added to Git; only documentation and evidence CSV files changed` |
| Stage A / owner amendment / boundary calculations / provenance framework | `UNCHANGED — not modified by this task` |
| Member count / boundary | `351 -> 351 (not touched by this task)` |
| Out of scope | `DataStore access, browser automation, authentication, dataset regeneration, application/backend code, tests, full year-level 2020 closure adjudication` |

## FI-DATA-EXPAND-04B-P3184-2020-PROVENANCE-REPAIR Product 3184 2020 provenance and evidence-wording correction (2026-08-25; append-only)

| State item | Status |
| --- | --- |
| Task | `FI-DATA-EXPAND-04B-P3184-2020-PROVENANCE-REPAIR — provenance identity, evidence wording, and acquisition-boundary repair of the FI-DATA-EXPAND-04B-P3184-Q4-RESOLUTION entry above. No conclusion expanded, no status promoted, no new membership fact derived` |
| Trigger | `Failed final audit of the §16 addendum: inverted object<->archive-file attribution, an over-attributed binary-difference claim, and a false acquisition boundary for five catalogue objects` |
| Deliverables | `docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md (§2/§16.1/§16.2/§16.3/§16.6 corrected, §17 added)`, `docs/evidence/bist_membership_p3184_2020_sources.csv (14 data records / 15 physical lines including header, 8 data rows edited, no rows added or removed)`, `TASK_STATE.md` |
| Files NOT modified | `ZIP files, XLS files, docs/evidence/bist_membership_p3184_2020_q4_rows.csv, data/ and data/trusted_clean/, model files, prior 04B evidence, collision audit and its manifest, Stage A, owner amendment` |
| Binary wording correction | `WITHDRAWN — the sentence attributing extracted-workbook byte differences to a specific container-metadata region, naming specific metadata fields, citing specific byte offsets, and declaring the difference to lie outside the sheet data is removed from this ledger, the reconciliation document, and the sources manifest. It asserted a binary-level cause the recorded evidence does not establish. The withdrawn wording is not reproduced; it is recoverable from Git history. Retained wording: "Converted CSV exports were cell-identical. Binary workbook files differed, but the exact binary-level cause was not fully attributed."` |
| Cell-equality evidence (retained, strengthened) | `The two 01-10-2020 candidates' converted CSV exports are byte-identical: SHA-256 4385ae8e6e7b7335add4a1072ad455c6cee317f75b9d2dc5000f7c61ed008892, 436 lines x 7 columns each. "436 data rows" corrected to "436 lines" — the export includes a header line and quarter banner lines, so 436 is not a membership-row count` |
| Provenance rebinding correction | `INVERTED -> REBOUND from actual on-disk file identity. exsrk2020 (1).zip = 58631 bytes, SHA-256 ed59e80e386c9b54058215996ef186849aa3bca144e0cc7f59227f92a889d73c, contains exsrk2020.xls de44aa20b70d2021d8301a726a157e3d92525a7a91690ed1ebfece06259ceb34 (420864 bytes). exsrk2020.zip = 58823 bytes, SHA-256 5ad33b895bea97647ed6809f45609f2fc0782fa9f887117aa59c26ae1cf145a8, contains exsrk2020.xls 45963bdbb706eee8105fa70967ffc02ba7d029649ca53c19a18547101bac3ac2 (421888 bytes). Each ZIP is bound to its extracted workbook by ZIP-member CRC-32, not by directory naming` |
| Catalogue-object binding limit | `PRESERVED AS UNCERTAIN — "private archive file identity confirmed; catalogue object assignment based on declared size match only." Object 3184#1132521 declares 58,631 and 3184#1132519 declares 58,823 (report s.4); no provider-side digest, per-object download URL, or other independent identifier exists in the catalogue record (s.4.1). The seven 2020 declared sizes are pairwise distinct and match the seven archive files one-to-one, which makes the assignment consistent, NOT proven` |
| Acquisition boundary correction | `Rows P3184-2020-07..-11 (objects 3184#1068011, 3184#1006269, 3184#982927, 3184#982925, 3184#872590) previously carried raw_sha256=NA, raw_bytes=NA, raw_storage_class=NOT_ACQUIRED and the note "unverified because the object was not downloaded". That boundary was false — a corresponding ZIP and its extracted workbook material exist on disk for each. Each row now records the archive file name, SHA-256, byte count, and the extracted workbook SHA-256 and size` |
| What was NOT done for rows 07..-11 | `No row-level reconciliation, no ADD/REMOVE determination, no canonical-revision or supersession conclusion, no membership value read/derived/recorded. Extractions inspected structurally only — presence, digest, size, archive-member binding` |
| New provenance vocabulary (documented in report s.17.4) | `ARCHIVE_PRESENT_NOT_OBJECT_BOUND — archive file present and identified by SHA-256, binding to this catalogue object id unproven (declared-size match only), no content-level reconciliation performed; applied to P3184-2020-07..-11. ACQUIRED_OBJECT_BINDING_BY_DECLARED_SIZE — file identity confirmed and content converted and compared, but catalogue-object assignment still declared-size-only; applied to P3184-2020-12 and -13. Neither asserts proven object identity` |
| Q4 evidence row | `P3184-2020-Q4-EVIDENCE catalogue_object_id 3184#1132521 -> 3184#1132521|3184#1132519 — the two candidates' converted exports are byte-identical, so the extraction is supported identically by either and is not bound to one object. Q4 rows CSV itself NOT modified` |
| Statuses unchanged | `REVISION_CANONICALIZATION_RESOLVED and Q4_STATE_RESOLVED stand on unchanged cell-equality and row-extraction evidence. REVISION_SEMANTICS_UNRESOLVED (s.5) and XU050_SEED_STATE_UNRESOLVED (s.10) remain open. The s.9 row-level reconciliation checklist remains open exactly as s.16.4 left it; the five newly bounded objects close no part of it` |
| Stage-B eligibility | `2020 NOT promoted. s.12's requirement for a separate year-level closure adjudication is unchanged` |
| Repository raw bytes | `NONE — no ZIP or XLS bytes added to Git; only two documentation/evidence files and this ledger changed` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true — no modeling dataset, results namespace, next_year_* column, benchmark-relative outcome, IC, p-value, or model output inspected; make data / benchmark / research / research-excess not run` |
| Member count / boundary | `351 -> 351; digest unchanged at 98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5 (not touched by this task)` |
| Out of scope | `DataStore access, browser automation, authentication, acquiring further objects, row-level 2020-10-01 reconciliation, dataset regeneration, application/backend code, tests, full year-level 2020 closure adjudication` |
| Claim boundary | Provenance-record correction only: repairing evidence attribution does not make a historical universe valid, does not improve any estimate, and does not establish model validity. No modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval or ranking changed; no reliable predictive edge established |

## P3184-2020-PROVENANCE-NORMALIZE Product 3184 2020 provenance schema normalization (2026-08-25; append-only)

| Field | Value |
| --- | --- |
| Task | `P3184-2020-PROVENANCE-NORMALIZE — structural provenance normalization of the FI-DATA-EXPAND-04B-P3184-2020-PROVENANCE-REPAIR entry above. No conclusion expanded, no status promoted, no new membership fact derived, no bytes read from any object file` |
| Deliverables | `docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md (s.18 addendum added)`, `docs/evidence/bist_membership_p3184_2020_sources.csv (14 -> 19 data rows; 20 -> 23 columns)`, `docs/evidence/bist_membership_source_manifest.csv (73 -> 80 data rows; columns unchanged)`, `TASK_STATE.md` |
| Why normalized | `Rows P3184-2020-07..-11 combined a 2026-08-24 catalogue observation and a 2026-08-25 archive-file inspection into one structured row under one access_date_utc/access_method pair -- a schema defect (two provenance events in one row), not a factual one. One-observation-per-row rule applied, matching the existing -05/-06 shape` |
| Rows restored to pure catalogue shape | `P3184-2020-07..-11 -> raw_filename/raw_sha256/raw_bytes=NA, raw_storage_class=NOT_ACQUIRED, archive_symbol=NA, provenance_status=VISIBLE_NOT_ACQUIRED; catalogue facts (object id, publication date, declared size, catalogue order, access method/class, price) unchanged from the provenance-repair entry above` |
| New archive-evidence rows | `P3184-2020-14 (3184#1068011, exsrk2020 (2).zip) / -15 (3184#1006269, exsrk2020 (3).zip) / -16 (3184#982927, exsrk2020 (5).zip) / -17 (3184#982925, exsrk2020 (4).zip) / -18 (3184#872590, exsrk2020 (6).zip) -- carry forward byte-for-byte the archive file identity, extracted-workbook identity, and CRC-32 binding previously embedded in -07..-11; provenance_status=ARCHIVE_PRESENT_NOT_OBJECT_BOUND (reused token, now on a properly-shaped row); content_reconciliation_status=STRUCTURAL_ONLY (not converted/compared, unlike -12/-13); revision_status stays REVISION_SEMANTICS_UNRESOLVED` |
| New P3184-file-only axes | `archive_identity_status {NO_LOCAL_FILE, LOCAL_FILE_DIGEST_CONFIRMED, NA}, catalogue_binding_status {UNBOUND, BINDING_BY_DECLARED_SIZE, NA}, content_reconciliation_status {NONE, STRUCTURAL_ONLY, CONVERTED_AND_COMPARED, NA} -- added to bist_membership_p3184_2020_sources.csv only, not the global manifest. No row is ROW_LEVEL_RECONCILED; NA used only for -01..-04 (catalogue-listing pages) and -Q4-EVIDENCE (derived multi-candidate row), where the object-file axes do not truthfully apply. provenance_status retained unchanged as a compatibility summary token` |
| VISIBLE_NOT_ACQUIRED redefinition | `OLD (row-write-time bound, became false when -07..-11 were edited in place at s.17.3): "no bytes for it were held at the time the row was written". NEW (observation-centered): describes the evidence attached to that observation record only -- this catalogue-observation event carried no acquired object bytes; does not assert no bytes exist elsewhere at any other time. Archive bytes for the same object, where they exist, are recorded as a separate row (e.g. P3184-2020-12 for -05, P3184-2020-14 for -07)` |
| Global manifest append | `BM-074..BM-080 appended, record_type=ARCHIVE_ACQUISITION_STATE_UPDATE, one-to-one deterministic order matching BM-031..BM-037: BM-074/1132521<-BM-031, BM-075/1132519<-BM-032, BM-076/1068011<-BM-033, BM-077/1006269<-BM-034, BM-078/982927<-BM-035, BM-079/982925<-BM-036, BM-080/872590<-BM-037. BM-031..BM-037 NOT modified -- remain accurate for the 2026-08-23 catalogue-only observation. Each BM-07x note states: earlier BM-03x row remains accurate for its earlier observation; new row updates later archive-state evidence only; local archive file identity is digest-confirmed; catalogue-object assignment remains declared-size based only; not provider proof. No superseded_by column added` |
| Global manifest new token values (documented, existing columns only) | `identity_status=BINDING_BY_DECLARED_SIZE -- new documented value (column previously only carried NA/NOT_ASSESSED/UNKNOWN, none of which could truthfully express digest-confirmed-file/declared-size-only-binding). provenance_status=ACQUIRED -- existing token reused in its existing sense (file obtained, bytes identified by SHA-256); no new meaning invented for it. No new global-manifest column added` |
| Timestamp handling | `access_date_utc=NA on all 12 new rows (P3184-2020-14..-18, BM-076..BM-080 plus BM-074/BM-075) -- the true owner acquisition/download time for these files was never recorded and is not invented; filesystem mtime and ZIP-member time are explicitly not treated as acquisition authority. Notes state inspection occurred during the 2026-08-25 provenance-normalization work at day-level only. P3184-2020-12/-13 and BM-031..-037 unchanged; the s.17 caution against reinterpreting the -12/-13 recorded access value as the original owner download time still stands` |
| ZIP member timestamp corroboration | `All seven 2020 archive ZIPs' exsrk2020.xls member timestamp matches its mapped catalogue publication date (day-level, read-only inspection, no bytes modified): (6)->02-01-2020 11:14, (4)->27-04-2020 12:52, (5)->27-04-2020 13:02, (3)->22-05-2020 12:55, (2)->28-07-2020 14:39, exsrk2020.zip->01-10-2020 09:42, (1)->01-10-2020 09:46. Recorded as corroboration only in each affected row's note; no timezone, not a provider digest, independently settable, does not promote catalogue_binding_status beyond BINDING_BY_DECLARED_SIZE` |
| 22-05 / 28-07 scope | `Treated as within-file republication/revision checkpoints, not proven extraordinary membership events; no event-level analysis or membership-change conclusion drawn for either date in this task` |
| Future gates documented, not resolved | `Snapshot semantics: future row-level reconciliation must pre-register and validate the publication_date x quarter_column unit before computing any exact delta between publications. Deterministic conversion: XLS->CSV conversion for the five newly-split files must be reproduced from verified XLS inputs with tool/version/command/input-output SHA-256/shape recorded before treating existing converted CSVs as authoritative; not performed here; existing conversions used only as structural corroboration` |
| No-peeking | `NO_NEW_OUTCOME_INSPECTION=true -- no membership value read, derived, or recorded for any of the five newly-split files; no modeling dataset, benchmark, experiment result, or model output touched` |
| Statuses unchanged | `Q4_STATE_RESOLVED (s.16.3) untouched, scoped to the 100 extracted 2020-10-01 rows. REVISION_CANONICALIZATION_RESOLVED (s.16.2) remains scoped to the 01-10-2020 pair only; the five normalized objects are not part of it. REVISION_SEMANTICS_UNRESOLVED (s.5) and XU050_SEED_STATE_UNRESOLVED (s.10) remain open. 27-04-2020 pair remains unresolved. s.9 row-level ADD/REMOVE and reserve-consumption reconciliation remain open. 2020 NOT promoted toward Stage-B eligibility` |
| Repository raw bytes | `NONE -- no ZIP or XLS bytes added to Git; no provider-proof or cryptographic object-binding claim made anywhere; every catalogue-object binding for these seven files remains declared-size match only` |
| CSV sanity checks performed | `python csv module: bist_membership_p3184_2020_sources.csv -- 23 header columns, 19 data rows, 0 ragged rows, 0 duplicate source_id. bist_membership_source_manifest.csv -- 24 header columns, 80 data rows, 0 ragged rows, 0 duplicate source_id. BM-031..BM-037 content diffed unchanged. No broad repository test suite run per task scope; operator layer performs authoritative validation` |
| Out of scope | `DataStore access, browser automation, authentication, acquiring further objects, row-level 2020-10-01 reconciliation, XLS->CSV conversion reproduction, membership-value inspection of any of the five files, dataset regeneration, application/backend code, tests, full year-level 2020 closure adjudication, editing bist_membership_p3184_2020_q4_rows.csv` |
| Claim boundary | Structural provenance normalization only: reshaping how existing evidence is recorded does not make a historical universe valid, does not improve any estimate, and does not establish model validity. No modeling row, feature, target, benchmark observation, prediction, coefficient, IC, p-value, interval or ranking changed; no reliable predictive edge established |

## P3184-2020-PROVENANCE-NORMALIZE-CORRECTION Product 3184 2020 documentation-integrity correction (2026-08-25; append-only)

| Field | Value |
| --- | --- |
| Task | `Bounded correction of the P3184-2020-PROVENANCE-NORMALIZE candidate above, applying a semantic review verdict of CHANGES REQUIRED. Three documentation-integrity defects fixed; no data row mapping, hash, byte count, provenance axis, status token, or scientific conclusion changed. Authorized files only: BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md, bist_membership_source_manifest.csv, TASK_STATE.md` |
| F-1: s.18.8 citation fix | `Two incorrect attributions corrected in s.18.8. (a) Filesystem-mtime non-authority was misattributed to s.3 (the login/registration gate, which contains no such rule) -- corrected to s.11, which actually states file modification timestamps were not used as authority. ZIP-member-time non-authority is now stated as established by this normalization addendum itself (s.18.9), not inherited from s.11. (b) The claim that "s.17's caution against reading the -12/-13 access value as download time still stands" was false -- s.17 contains no such caution. Attribution to s.17 removed; the rule is now stated directly in s.18.8 for the first time: P3184-2020-12/-13's recorded value is an inspection/access timestamp, not original acquisition/download time` |
| F-2: s.17.3 / s.17.4 supersession markers | `Applied the document's existing strikethrough + arrow convention (no text deleted). s.17.3: the sentence claiming rows -07..-11 "now record" archive-file detail is struck through and marked superseded -> s.18.3 (that detail was relocated to new rows -14..-18 during normalization). s.17.4 VISIBLE_NOT_ACQUIRED: old row-write-time-bound clause and old row scope (-05/-06 only) struck through, superseded -> s.18.6; current meaning (describes the evidence attached to that observation record, not a claim that no bytes exist elsewhere) now covers P3184-2020-05 through -11. s.17.4 ARCHIVE_PRESENT_NOT_OBJECT_BOUND: old row assignment ("Applied to -07..-11") struck through, superseded -> s.18.3/s.18.5; current live rows carrying the token are P3184-2020-14 through -18. Semantic definitions of both tokens preserved unchanged` |
| F-3: BM-074/BM-075 note correction | `Global manifest notes for BM-074 and BM-075 only were corrected; no other field of either row changed, and BM-076..BM-080 and BM-001..BM-073 are untouched. Prior wording ("the exact UTC acquisition/inspection timestamp is not evidenced") conflated original owner acquisition/download time (still unknown) with the later 2026-08-25T00:24:00Z inspection/access timestamp that IS recorded on the linked P3184-2020-12/-13 archive rows. Corrected notes now state both facts separately and explain that access_date_utc=NA on BM-074/BM-075 is a deliberate policy choice for the state-update event, not an absence of any recorded timestamp anywhere. access_date_utc itself remains NA on both rows -- only note prose changed. s.18.8 of the reconciliation doc updated in parallel to state this NA-by-policy rule explicitly` |
| F-4: stale external report (out of scope, follow-up only) | `docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md is a historical SHA-pinned report and was NOT edited by this correction. It still states provenance manifest = 73 rows / PRIVATE_LOCAL_RAW = 6 objects, which no longer describes the live global manifest (80 rows / 13 PRIVATE_LOCAL_RAW rows after the seven BM-074..BM-080 archive-state rows appended by P3184-2020-PROVENANCE-NORMALIZE). The report was not false at its own snapshot -- it is pinned to an earlier repository state and simply has not been refreshed. Refreshing it, or formally adjudicating its historical-report status, is a separate report-refresh task and is explicitly not performed here` |
| Not done | `No data row mapping, raw SHA-256, raw byte size, catalogue-object mapping, P3184 orthogonal axis, record_type, identity_status, provenance_status, or scientific status changed anywhere. bist_membership_p3184_2020_sources.csv (P3184 source CSV) NOT edited. DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md NOT edited. No git add/commit/push/merge/reset/stash/clean performed. No broad test suite run` |
| Preserved | `Q4_STATE_RESOLVED (scope only), REVISION_CANONICALIZATION_RESOLVED (01-10-2020 pair only), REVISION_SEMANTICS_UNRESOLVED (open), XU050_SEED_STATE_UNRESOLVED (open), 27-04-2020 pair (unresolved), row-level ADD/REMOVE reconciliation (open), reserve-consumption reconciliation (open), 22-05-2020 and 28-07-2020 (not proven extraordinary events), Stage-B (not promoted), PROVIDER_PROOF (NOT ESTABLISHED), NO_NEW_OUTCOME_INSPECTION=true` |
| Claim boundary | Documentation-integrity correction only: fixing citations, adding supersession markers, and disambiguating acquisition-vs-inspection timestamp wording does not change any provenance fact, does not promote any status, and does not establish predictive value. No reliable predictive edge established. Not committed, pushed, merged, deployed, or accepted -- targeted validation and reviewer follow-up remain the operator's next step |

## F-4 historical-report adjudication closure (2026-08-25; append-only, read-only adjudication)

| Field | Value |
| --- | --- |
| Task | Close the F-4 follow-up recorded above (`docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md` staleness). Read-only adjudication only. No file edited except this one row. `docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md`, any CSV, and all other docs/code/config/artifacts were read but not modified |
| Adjudication | `docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md` is an **immutable historical snapshot**, not a live manifest dashboard. Evidence: its title reads "Historical BIST membership sourcing evidence"; it pins authoring HEAD `7bd1dfad16eb750481603f18eca916e4ab09cfc4`; it records "Protected boundary at authoring" (351 members, digest `98195607...`, itself frozen at authoring time); current file SHA-256 independently reverified as `0cba78d18be5e7e2061cc38478cbe251a8a4db775a5acfe4e8e4505f3b5b1c63`, matching the value later TASK_STATE rows intentionally preserved; later docs (F-3/F-4 correction row above) describe the report as prior evidence being extended, not revised; a repository search of `scripts/`, `tests/`, `Makefile`, `backend/`, `frontend/`, and `artifact_registry.json` for references to the report found **no programmatic consumer** |
| Snapshot vs. live state | The report's 73-row provenance manifest / 6 `PRIVATE_LOCAL_RAW`-object statements are historical facts about its own authored snapshot and remain true as a description of that snapshot. Current live state is separately represented by the live global manifest: **80 data rows / 13 `PRIVATE_LOCAL_RAW` rows** after BM-074..BM-080. The two figures describe different points in time by design, not a contradiction |
| Disposition | Refreshing the historical report to 80/13 is **not required** and would blur snapshot semantics (a snapshot pinned to a HEAD and a protected-boundary digest is falsified by being rewritten to a later state). F-4 disposition: **HISTORICAL_SNAPSHOT_CONFIRMED / NO_REPORT_REFRESH_REQUIRED / FOLLOW_UP_CLOSED** |
| Scope boundary | `NO_NEW_OUTCOME_INSPECTION=true`. No scientific state change. No model, data, manifest, or raw-evidence change. `docs/DATA_EXPANSION_MEMBERSHIP_SOURCING_REPORT.md` remains byte-identical (SHA-256 unchanged, reverified above). This adjudication authorizes **no** Stage-B promotion and **no** further membership reconstruction |
| Not done | No git add/commit/push/merge/reset/stash/clean performed. No file other than this `TASK_STATE.md` row edited |

## P3184-2020-Q4-RECONCILIATION-CLOSEOUT Product 3184 2020 Q4 row-level reconciliation closeout (2026-08-25; append-only, documentation only)

| Field | Value |
| --- | --- |
| Task | `P3184-2020-Q4-RECONCILIATION-CLOSEOUT — record the Q4 row-level reconciliation result against already-recorded evidence. Documentation update only. No new file acquired, no ZIP/XLS byte read, no row in bist_membership_p3184_2020_q4_rows.csv modified. Authorized files: docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md, TASK_STATE.md` |
| Method | The already-recorded `is_xu030`/`is_xu050`/`is_xu100` flags in the 100-row Q4 evidence CSV were compared, by script, against the already-published additions/removals/reserves table in `BIST_MEMBERSHIP_2020_10_01_COLLISION_AUDIT.md` §6 and the official final XU030/XU100 code sets in its §9. No new source was read; both inputs were already committed evidence |
| XU030 / XU100 exact-set reconciliation | `MATCH` — Q4 rows' 100 `is_xu100=TRUE` tickers are set-identical to the official final XU100 code set (0 diff either direction); Q4 rows' 30 `is_xu030=TRUE` tickers are set-identical to the official final XU030 code set (0 diff either direction). See reconciliation doc §19.1 |
| ADD reconciliation | `MATCH` — all 6 announcement-14118 XU100 additions (`AKSGY, ALCTL, ARDYZ, INDES, PETUN, PNSUT`) carry `is_xu100=TRUE`; both XU030 additions (`GUBRF, OYAKC`) carry `is_xu030=TRUE`. See §19.2 |
| REMOVE reconciliation | `MATCH` — all 6 announcement-14118 XU100 removals (`ANACM, GLYHO, KARSN, KLMSN, SODA, TRKCM`) and both XU030 removals (`SODA, TRKCM`) are absent from all 100 Q4 rows entirely, reconfirming §16.4's presence/absence snapshot at row level. See §19.2 |
| Reserve check | `NOT_CONSUMED` — XU100 published reserves (`ECZYT, EGGUB, KONYA`) absent from all 100 Q4 rows; XU030 published reserves (`SOKM, SASA, VESTL`) present in the Q4 rows but each carries `is_xu030=FALSE` (narrowest observed index XU050/XU100), i.e. not promoted into XU030. Corroborates the collision audit's `RESERVE_CONSUMPTION_EVENT_CONFIRMED` (no reserve consumed) finding rather than contradicting it. See §19.3 |
| Preserved (not closed by this task) | `REVISION_SEMANTICS_UNRESOLVED` (§5, open — this closeout reconciles row content against a published event table, it makes no revision/supersession claim); `XU050_SEED_STATE_UNRESOLVED` (§10, open — XU050 ADD/REMOVE/reserve was out of the requested scope and not checked here; no independent first-party 50-count exists to close the seed state regardless); provider-object binding limits (`ACQUIRED_OBJECT_BINDING_BY_DECLARED_SIZE` / `ARCHIVE_PRESENT_NOT_OBJECT_BOUND`, declared-size match only, unchanged); Stage-B promotion (not granted; §12/§16.6/§17.5/§18.13 unchanged) |
| Validation | `make claims-lint` and `make docs-lint` — see run log below |
| Not done | No DataStore access, no browser automation, no authentication, no new object acquisition, no XLS/ZIP byte read, no edit to bist_membership_p3184_2020_q4_rows.csv or bist_membership_p3184_2020_sources.csv, no XU050 ADD/REMOVE/reserve check, no revision-semantics resolution, no year-level 2020 closure adjudication, no git add/commit/push |
| Claim boundary | Documentation update recording an already-derivable reconciliation result; it changes no evidence byte and establishes no provider-proof or predictive claim. Research support only; not investment advice. `NO_NEW_OUTCOME_INSPECTION=true`. No reliable predictive edge established |

## THESIS-S1-POSCTRL Stage 1 raw-layer positive control (2026-08-27; append-only)

| Field | Value |
| --- | --- |
| Task | Stage 1 of `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`: inject a known-strength synthetic signal into a **raw** feature column before feature construction and measure end-to-end recovery. File mtimes and matching implementation/artifact hashes are consistent with the amendment having been written before the run, but temporal pre-registration is not cryptographically proven in Git history. The fixed constants (IC grid, MDE_base, delta, family size, model) were carried over unedited |
| Branch | `local/financeiq-raw-layer-control-1dc18f`, worktree `financeiq-engineering-audit-a41604`, from main `794804e0` |
| Injection | Within-year permutation of carrier `equity`'s own observed values into the order of a Gaussian-copula latent score `s = rho*z + sqrt(1-rho^2)*eps`, `rho = 2*sin(pi*theta/6)` — the identity `significance.simulate_fisher_power` already uses. Marginal, missingness, target, and all non-carrier columns preserved exactly; injected table written to a private temp dir, never under `data/` |
| Confirmatory arm (preregistered) | 5 levels x 1 repetition, ridge, Bonferroni x5. Recovered IC `[0.09406142009, 0.116002328212, 0.109438802294, 0.151687843758, 0.304713005705]`; adjusted p `[0.763923607639, 0.378462153785, 0.46495350465, 0.115488451155, 0.000499950005]`. Monotone increasing **False**; both gate levels reject **False**. **Stage 1 gate: NOT PASSED as literally written** |
| Descriptive arm (200 reps/level, no confirmatory claim) | Mean recovered IC by level: 0.0909, 0.1001, 0.1366, 0.1803, 0.2432 — strictly increasing. Detection rate by level: 0.00→0.000; 0.10→0.000; 0.20→0.170; 0.30→0.615; 0.40→0.930. Lowest preregistered grid level reaching 80% detection: **0.40** (observed 0.930, CI [0.886, 0.958]); no interpolation, no added level |
| Gate informativeness (POST-RUN diagnostic) | From the existing 200 primary descriptive repetitions as coherent five-level draws: P(strictly monotone recovered IC) = **0.295** (59/200); P(both required high-grid levels reject) = **0.560** (112/200); P(original Stage 1 gate passes) = **0.195** (39/200). This does not alter the gate or Stage 1 status |
| Attenuation localisation | For the 100%-coverage primary carrier, raw, feature-construction, and model-input/imputation are **identity/invariant checkpoints**, not empirical claims of absent attenuation. The substantive transition is carrier signal → fitted model prediction; at injected IC 0.30 the mean recovered model IC is 0.1803 (unadjusted recovered IC, not a ratio) |
| Missingness channel | Secondary descriptive carrier `current_ratio` (~49% coverage in test years): its observed-carrier checkpoint `n` differs from post-imputation full-cross-section `n`, so the stagewise ratio mixes missingness/imputation dilution with changed evaluation population and is not a pure attenuation coefficient. Detection at theta=0.40 falls from 0.930 to 0.600 |
| Controls | Zero-signal (theta=0): raw carrier IC 0.0005, **0/200 detections** — no forced correlation, consistent with the committed null. Strong-signal sanity (theta=0.90, outside the grid, excluded from the power curve): recovered 0.7640, detection 1.000. Deterministic replay: `make thesis-positive-control-replay` → identical, digest `cb4caee0676f21e3` |
| Analytic vs empirical | Analytic power evaluated at the **injected** IC badly overstates detection (0.983 vs 0.615 at theta=0.30) because it assumes zero attenuation. Evaluated at the **recovered** IC it agrees at the upper levels (0.577 vs 0.615; 0.884 vs 0.930) but still overstates at theta<=0.10 (0.147 vs 0.000). Diagnosed cause: the analytic model treats the cross-section as resampled (implied IC sd 0.0658), whereas this design holds the realized panel fixed while the synthetic injection and the permutation-test RNG both change across repetitions (observed across-rep sd 0.013–0.049), so the empirical variation carries injection-draw plus permutation Monte-Carlo randomness but no market-panel/time resampling. The two curves condition on different randomness and are not interchangeable |
| Diagnosis of the gate failure | The apparatus **does** respond to injected signal (monotone mean curve, 100% detection at theta=0.90, 93% at theta=0.40). At injected IC 0.30, the descriptive arm's mean recovered model IC is ~0.18 and the one-shot rejection rate is 0.615. The gate failed as written; **no threshold, level, or rule was altered to make it pass** |
| Artifacts | `experiments/results_thesis/positive_control/` — superseded by the 2026-08-27 review-fix regeneration below; original run hashes were attenuation_by_stage.csv `3f1eb9dc320d8c0f`; detection_curve.csv `fed684602b3a9a04`; positive_control_report.json `5a38c37d495a57df`; positive_control_report.md `353d24c565202644`; repetitions.csv `23eb51d8b0c264ee` |
| Validation | Focused Stage 1 `49 passed`; artifact registry `16 passed`; replay `identical` (digest `cb4caee0676f21e3`); `make claims-lint`, `make docs-lint`, `make data-validate`, and `git diff --check` passed. Root suite: `1129 passed, 1 failed` only at the known dirty-worktree allowlist guard (`tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact`); backend suite not run because backend files were untouched |
| Not done | Stages 2–7 not implemented and not run; Stage 2 remains gated on the owner's adjudication of the Stage 1 gate result. No git add/commit/push/PR/merge performed. No governed historical results root, frozen baseline, or modeling dataset modified |
| Claim boundary | Apparatus validation on manufactured input. Establishes no predictive edge, no alpha, and no investment value; the committed walk-forward null is unchanged. `NO_NEW_OUTCOME_INSPECTION=false` (this task inspected only synthetic-injection outcomes, never a new real-data outcome). Research support only; not investment advice |

### THESIS-S1-POSCTRL review-fix pass (2026-08-27; append-only)

| Field | Value |
| --- | --- |
| Scope | Independent-review findings only; no scientific parameter, estimand, IC grid, seed, repetition count, ridge model, alpha, Bonferroni family, MDE_BASE, or confirmatory gate touched. Stage 1 remains **FAILED AS WRITTEN**; Stage 2 remains BLOCKED; Stage 1B remains REQUIRED |
| Chronology wording | Corrected the "amendment written and dated before the run" overclaim here and in `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`. Original amendment text preserved verbatim; a labeled POST-RUN chronology note now states the ordering is corroborated by file mtimes and matching implementation/artifact hashes but is **not cryptographically proven in Git history**, and that no future commit can retroactively prove pre-run pre-registration |
| Identity-checkpoint ratio | `background_adjusted_ratio_heuristic` is now emitted as NA for `identity_invariant` checkpoints and the injected design constant (previously ~1.0 by construction, misreadable as a measured attenuation coefficient), matching the existing suppression of `mean_ratio_to_injected`. `ratio_suppressed_reason` now reads "identity/invariant checkpoint — attenuation ratio not interpreted" |
| Empirical-repetition wording | Report/limitations/README/TASK_STATE now state accurately: the realized equity panel is fixed; the synthetic injection changes across repetitions; the permutation-test RNG also changes across repetitions; so empirical detection-rate variation carries injection-draw plus permutation Monte-Carlo randomness; it still excludes resampling uncertainty from another market panel/time sample |
| Alpha pin | `tests/test_thesis_positive_control.py::test_preregistered_constants_match_the_protocol` now pins `pc.ALPHA == 0.05` against the protocol strings "α = 0.05 two-sided" and "min(1, 5·p_j) < 0.05"; a drift of `pc.ALPHA` away from the preregistered value now fails |
| Copula coupling (LOW, optional) | Left the existing identity check; added a minimal `inspect.getsource` pin that fails if `significance.simulate_fisher_power`'s Gaussian-copula identity drifts from the injection's. Full behavioural coupling would require exposing the copula map from `significance.py`, which is out of scope. Residual reported |
| Regeneration | `make thesis-positive-control` re-run; only the Stage 1 namespace regenerated. **No scientific numeric drift**: confirmatory recovered IC, adjusted p, gate=NOT PASSED, monotone=False, both-gate-reject=False, full detection curve, and gate diagnostic P(strict monotone)=0.295 / P(both high-grid reject)=0.560 / P(original gate passes)=0.195 all bit-identical to the original run. Replay digest `cb4caee0676f21e3` unchanged |
| New artifact hashes | schema_version 2→3; positive_control_report.json `3f6a00bf550d381f`; positive_control_report.md `9f99a4caa3a1baf1`; attenuation_by_stage.csv `b76b123786352aae`; implementation_sha256 `dfa4c25c9753fdc1`. Unchanged: detection_curve.csv `fed684602b3a9a04`, repetitions.csv `23eb51d8b0c264ee`. `docs/limitations_register.md` regenerated via `make limitations-register` |
| Validation | `pytest tests/test_thesis_positive_control.py tests/test_artifact_registry.py -q` → `65 passed`; `make thesis-positive-control-replay` → identical; `make claims-lint`, `make docs-lint`, `make data-validate`, `git diff --check` all passed. Root dirty-worktree allowlist guard still fails while uncommitted — expected, not a defect |
| Not done | No git mutation of any kind. Full behavioural copula coupling not implemented (out of scope). Independent final semantic review still required |

### FINANCEIQ_POSITIVE_CONTROL_STAGE1_FINAL_REGEN_2026_08_29

- Date: 2026-08-29
- Status: Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**; this entry supersedes the earlier review-fix artifact-hash record only. No scientific result, gate, estimand, threshold, model, seed schedule, or detection curve changed.
- Final report schema transition: **3 → 4**.
- Final regeneration provenance:
  - `positive_control_report.json` SHA-256: `04e3a7ac754c2f48b2114666cef258cd978789b2a264001a37a24a41fcc55008`
  - `positive_control_report.md` SHA-256: `a0534727d1e04a738ba2faec0878a6e108f6ad8a46e4dbe19989ec267e9c6312`
  - `attenuation_by_stage.csv` SHA-256: `1eac340bf9050b4d88efd8e62f9c574ca92f7f81009b66e85d7cfa3d34660889`
  - `detection_curve.csv` SHA-256: `fed684602b3a9a04bc64e2bc6a822924de86bba4a3b4ee46b6065f247b0d7793`
  - `repetitions.csv` SHA-256: `23eb51d8b0c264ee8919ff42916e1365284b6526b520e2f3cd76fc92ded493cf`
  - `artifact_manifest.json` SHA-256: `d639c5b3e6e50ce62a0bada78bf3378adaa378ab3ae637e2d6161aaae9ee5a39`
  - `experiments/thesis/positive_control.py` SHA-256: `44c897568f17618b7db0a42103384f43d24da5fb296bf092b422ef51a495e27d`
- Final semantic repair: identity/invariant checkpoints expose raw IC statistics but suppress interpreted attenuation ratios and background-adjusted attenuation heuristics in both CSV and JSON/report representations.
- Scientific invariants preserved: confirmatory result remains failed; detection and repetition scientific rows were unchanged by the schema/reporting regeneration.
- Temporal pre-registration remains **not cryptographically proven in Git history**. File mtimes and matching implementation/artifact hashes are corroborating evidence only; this final regeneration does not retroactively establish pre-run pre-registration.

### FINANCEIQ-STAGE1B-REGISTRATION-ONLY (2026-08-29; append-only)

- Stage 1b registration prepared: `docs/thesis/STAGE_1B_REGISTRATION.md` (new), dated Stage 1b amendment appended to `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`, machine-checkable constants in `experiments/thesis/stage1b_registration.py` (new), focused tests in `tests/test_thesis_stage1b_registration.py` (new), `positive_control_calibration` slug + seed added to `experiments/thesis/provenance.py`, `experiments/thesis/README.md` note.
- Owner-approved design frozen: carrier `equity`, ridge, frozen panel / walk-forward splits, `experiments/significance.py`, 10,000 permutations, 10,000 bootstraps, Stage 1 seed-derivation framework, and the fixed Stage-1-operational-rule divisor 5. Grid `{0.00, 0.10, 0.20, 0.30, 0.35, 0.40}` — only new rung `0.35`. `R = 400` fresh repetitions, global ids 200–599 (non-overlapping with Stage 1's 0–199). Legacy level indices preserved; `0.35` → stable new index 5. Primary result = Stage-1-operational-rule detection probability, `min(1, 5·p_raw) < 0.05`; raw-p<0.05 detection probability is a labeled non-gating secondary diagnostic. The six levels are not a hypothesis family and no family-wise-error-control claim is made across them. No scientific performance PASS/FAIL gate.
- No Stage 1b run executed. No Stage 1b outcome inspected or generated. `experiments/results_thesis/positive_control_calibration/` does not exist. No Makefile target and no `artifact_registry.json` entry added (deferred to the implementation task per the `proposed_future` convention).
- Stage 1 unchanged and still **FAILED AS WRITTEN — INFORMATIVE**. Stage 2 remains **BLOCKED**.
- Registration requires independent methodology/governance review and owner commit before execution.
- Validation: `pytest tests/test_thesis_stage1b_registration.py -q` → 25 passed; `pytest tests/test_thesis_positive_control.py tests/test_artifact_registry.py -q` → 66 passed; `make claims-lint`, `make docs-lint`, `git diff --check` passed. No git add/commit/push/merge/reset/stash/clean performed.

### FINANCEIQ-STAGE1B-REGISTRATION-FINAL-MICROFIX (2026-08-31; append-only)

- Bounded preregistration repair after independent Opus review. No Stage 1b run, no Stage 1b outputs, no Stage 1 historical-artifact changes, no new scientific scope. Files touched: `docs/thesis/STAGE_1B_REGISTRATION.md`, `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`, `experiments/thesis/stage1b_registration.py`, `experiments/thesis/README.md`, `tests/test_thesis_stage1b_registration.py`.
- H1: `STAGE1_OPERATIONAL_DIVISOR = 5` documented as a frozen literal; forbidden to derive it from `len(IC_GRID)` / Stage 1b grid length / `CONFIRMATORY_FAMILY_SIZE` / level count (a six-level recompute would move the operating point to ~p_raw<0.00833). Cross-module test pins `5 == stage1.CONFIRMATORY_FAMILY_SIZE != len(reg.IC_GRID)`.
- M1: named the real enumerate() drift site — `positive_control.run_arm()` uses `enumerate(levels)`; sorted Stage 1b order would send 0.35→4, 0.40→5. Seed derivation must use `LEVEL_INDEX` / `level_index_for(theta)`; report order may stay numeric. Carry-forward test binds `stage1.derive_injection_seed(42, level_index_for(0.40)=4, 200) == 42_040_354`.
- Governance-before-first-run expanded: runner + `thesis-stage1b` target + `artifact_registry.json` `governed_roots` root + per-artifact entries + no-orphan tests, all in one commit before the first run; per-file entries without the `governed_roots` root are insufficient.
- Registration-phase guard sunset declared in the registration and in test comments (result-root absence, registry absence, Make-target absence) — future implementation commit inverts them in the same commit; not deleted or weakened now.
- Chronology wording corrected: design began 2026-08-29, reviewed-registration date 2026-08-31, registration commit is the authoritative prospective Git chronology anchor; Stage 1b ordering will be Git-proven unlike Stage 1. No fabricated commit SHA.
- Low fixes: README `other four slugs` → `other five slugs` (verified: `positive_control_calibration`, `negative_control`, `defect_injection`, `informativeness`, `monthly_panel`); removed "where applicable" hedge (permutation seed is theta-independent → marginal Wilson intervals); PRE_EXPERIMENT_PROTOCOL bullet-continuation indentation repaired; `LEVEL_INDEX` frozen with `MappingProxyType` (stdlib only, `level_index_for` unchanged); artifact-backed detection-disclosure test (θ=0.30→0.615, θ=0.40→0.930 read from the governed Stage 1 report); pinned `PROSPECTIVE_NOT_BLIND`, `NO_STAGE_1B_OUTCOME_INSPECTED`, `STAGE_1_STATUS`, `STAGE_2_STATUS`, `INJECTION_MECHANISM`, `DETECTION_INTERVAL`.
- Validation: `pytest tests/test_thesis_stage1b_registration.py -q` → 35 passed; `pytest tests/test_thesis_positive_control.py tests/test_artifact_registry.py -q` → 66 passed; `make claims-lint`, `make docs-lint`, `git diff --check` clean. Root suite otherwise green; `tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact` fails only because this registration diff is intentionally uncommitted (guard not modified). `experiments/results_thesis/positive_control_calibration/` still absent. No git add/commit/push/merge/reset/stash/clean performed.

### FINANCEIQ-STAGE1B-IMPLEMENTATION-ONLY (2026-08-31; append-only)

- **Stage 1b implementation prepared. No Stage 1b governed run executed, no Stage 1b outcome inspected or generated.** `experiments/results_thesis/positive_control_calibration/` does not exist. Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**; Stage 2 remains **BLOCKED**.
- Prospective registration commit (authoritative Git chronology anchor): `bd63d9723b87e08c0ac549a4b9c4bc00b857b5f7`. Implementation based on verified main: `9cb253661ddbf3244a042c7aac89b2f0910b1eda`. Implementation work was carried out in worktree `financeiq-calibration-design-31144b` on branch `local/financeiq-stage1b-impl-b85ce9` at that same base, not in the `financeiq-stage1b-implementation-4c7e91` path named by the task brief; base commit and branch content are otherwise as specified.
- New runner `experiments/thesis/positive_control_calibration.py`. The historical Stage 1 runner is untouched: its pure helpers (`inject_carrier`, `run_repetition`, `derive_injection_seed`, `derive_permutation_seed`, `_wilson_interval`, `_summarize`, `CHECKPOINTS`, `CHECKPOINT_ROLES`, `ROUND_DIGITS`) are reused, and its Stage-1-only semantics are not.
- Frozen operating divisor: detection uses `reg.STAGE1_OPERATIONAL_DIVISOR = 5` as a literal. `positive_control.CONFIRMATORY_FAMILY_SIZE` is not referenced anywhere in executable code, and an AST test proves `operating_point_p_value` / `detected_by_stage1_rule` / `detected_by_raw_p` reference only the divisor and alpha. Stage 1's `bonferroni_adjusted_p_value` / `detected` fields are dropped from every Stage 1b record.
- Seed identity: level indices come from `stage1b_registration.level_index_for`; the runner contains no `enumerate` call at all. Report order is numeric (`0.00 … 0.40`); seed identity keeps `0.40 → 4` and `0.35 → 5`. `injection_seed_for(0.40, 200) == 42_040_354` pinned. 2400 distinct injection seeds, disjoint from the permutation stream and from all Stage 1 streams.
- Registered scope implemented literally: carrier `equity` only (the Stage 1 coverage rule is re-applied at run time and must still select `equity`), ridge only, grid `{0.00, 0.10, 0.20, 0.30, 0.35, 0.40}`, `R = 400`, ids `200 … 599`, 10,000 permutations, 10,000 bootstraps, alpha 0.05, pointwise 95% Wilson. `current_ratio` and theta=0.90 are absent; `run_repetition` refuses any off-grid theta or out-of-range repetition id.
- Not computed, and machine-checked absent: `confirmatory_gate`, `gate_informativeness`, `detection_threshold`, `GATE_LEVELS`, `MDE_BASE`, `SANITY_IC`, strict-monotonicity pass/fail, any 80% crossing, attenuation/background heuristics. `HAS_PERFORMANCE_GATE` stays false; no report key names a performance endpoint.
- Result contract fixed before execution — five governed files: `positive_control_calibration_report.json`, `positive_control_calibration_report.md`, `repetitions.csv`, `calibration_curve.csv`, `artifact_manifest.json`. Registered per-theta summaries (mean, SD, median, p05, p95) for the realized raw equity carrier IC and the final evaluated IC, primary Stage-1-operational-rule detection rate with pointwise Wilson interval, secondary non-gating raw-p<0.05 rate, full checkpoint chain, closed integrity block, and a deterministic ordered-record replay digest.
- Closed integrity contract implemented as a pure evaluator keyed by the registered condition strings; a test pins `tuple(mechanical) == MECHANICAL_PROVENANCE_CHECKS` and `tuple(mechanism) == MECHANISM_INVARIANT_CHECKS`. All 13 mechanical and 7 mechanism conditions are evaluated. "Identity/invariant checkpoint ICs agree within the already governed Stage 1 numerical tolerance" is implemented as `10 ** -positive_control.ROUND_DIGITS` (1e-12) — the Stage 1 emission granularity at which the governed Stage 1 report's identity checkpoints already agree exactly; it is derived, not newly chosen. No check inspects IC magnitude, detection rate, monotonicity, Wilson position, the theta=0 diagnostic, or a crossing location, and a test proves a never-detecting and an always-detecting record set produce the same verdict.
- CLI safety: `--run` is mandatory. Bare invocation prints the registered plan and exits 0 without reading the dataset. `run()` accepts no scientific parameter, so R, permutations, bootstraps, grid, seeds, carrier, model, and detection rules cannot be reduced or overridden at runtime; there is no adaptive stopping and no rerun-on-result behaviour. Nothing is written until every integrity condition passes, so a failed run leaves the result root absent. Import is inert and creates nothing.
- Governance wiring added in this same change, before any run: Makefile targets `thesis-stage1b` (governed run) and `thesis-stage1b-replay` (determinism probe, writes nothing); the Stage 1b root (still absent on disk) added to `artifact_registry.json` `governed_roots`; one frozen ownership contract per emitted file.
- **Registry placement — resolved tension, no scientific change.** The registration requires one `artifact_registry.json` entry per emitted output *before* the run, while `tests/test_artifact_registry.py::test_every_entry_matches_at_least_one_file` and `scripts/build_limitations_register.py` both require every `entries[]` item to resolve to a real file. Putting the five Stage 1b contracts in `entries[]` now would break both. They are therefore declared in a new top-level `prospective_entries[]` block with the identical entry shape, the same `make <target>` rule, and a stated `prospective_entry_rule` requiring the run commit to move them verbatim into `entries[]`. Nothing was weakened: no existing registry test was modified, and the implementation test asserts the contracts exist, cover exactly the emitted set, and are absent from `entries[]`.
- Registration-phase guards inverted in the same change, not deleted: `test_future_generator_and_registry_entries_are_deferred` is replaced by `test_governance_wiring_is_present_and_the_run_has_not_happened` (runner present, Make target present, governed root registered, per-file contracts registered, none in `entries[]`, result root still absent), and the sunset test's tail now asserts the target and runner exist. Result-root absence is re-labelled an implementation-phase guard that sunsets only at the governed run.
- `tests/test_thesis_positive_control.py::test_every_governed_results_root_is_protected` was generalized (not weakened): its hardcoded single-root exception became a set derived from `provenance.EXPERIMENT_SLUGS`, plus a new assertion that every governed `results_thesis/` root has a declared slug and is not in `PROTECTED_RESULTS_ROOTS`. Required because a second governed thesis root now exists. No Stage 1 implementation or artifact was touched.
- Files changed: `experiments/thesis/positive_control_calibration.py` (new), `tests/test_thesis_stage1b_implementation.py` (new), `tests/test_thesis_stage1b_registration.py` (guard inversion), `tests/test_thesis_positive_control.py` (governed-root generalization), `artifact_registry.json`, `Makefile`, `experiments/thesis/README.md`, `TASK_STATE.md`. `docs/thesis/STAGE_1B_REGISTRATION.md`, `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md`, `experiments/thesis/positive_control.py`, `experiments/significance.py`, Stage 1 result artifacts, `data/`, `backend/`, and `frontend/` are unchanged. No registration amendment was required.
- Validation: `pytest tests/test_thesis_stage1b_registration.py tests/test_thesis_stage1b_implementation.py tests/test_thesis_positive_control.py tests/test_artifact_registry.py -q` → 155 passed. `PYTHONPATH=. pytest tests/ -q` → 1219 passed, 1 failed — `tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact` only, because this implementation diff is intentionally uncommitted; that guard was not modified. `make claims-lint`, `make docs-lint`, `git diff --check` clean. `make thesis-stage1b` was NOT invoked and no CLI mode that creates the governed output root was run. The write path was exercised once in an isolated scratch directory with fabricated records and `run_grid`/`_replay_probe` replaced, asserting before and after that the governed root does not exist; that scratch directory was removed.
- Requires independent review and owner commit/merge before execution. Stage 1b is **not** complete.

### FINANCEIQ-STAGE1B-IMPLEMENTATION-SAFETY-MICROFIX (2026-09-01; append-only)

- Added fail-closed lifecycle safety without running Stage 1b: normal `--run` refuses any non-empty existing Stage 1b root; `--repeat-after-crash` is the only recovery mode for an incomplete marker-backed attempt and refuses final-manifest completion evidence.
- Added operational `attempt_provenance.json` with registered configuration and seed-schedule identity, initial/crash-recovery attempt type and number, prior-incomplete status, and completion status. The marker is governance/provenance metadata, not a scientific emitted artifact; `artifact_manifest.json` remains completion authority.
- Replaced sequential final-root writes with attempt staging, recursive filesystem-backed output inspection, known-namespace cleanup on recovery, promotion only after integrity and claim-safety checks, and final manifest write last. Outside-namespace workspace changes are also checked; no scientific integrity/performance conditions were added.
- Added binding prospective-entry transition tests requiring exact dictionary equality when a prospective path becomes real, run-orchestration order tests, recursive unexpected-output tests, scratch lifecycle tests, and Stage 1 safe-field-discard AST coverage.
- Validation after this microfix: focused Stage 1b implementation/registry checks passed; prior full root run passed 1,230 tests with only the expected dirty-worktree changed-path allowlist failure. `make claims-lint`, `make docs-lint`, and `git diff --check` passed. Stage 1b was not run, and `experiments/results_thesis/positive_control_calibration/` remains absent.

### FINANCEIQ-STAGE1B-BOOKKEEPING-CLOSEOUT (2026-09-02; append-only)

| State item | Status |
|---|---|
| Governed run | `cb3cf211a21ec39d65deec6f49230306cfd882f7` |
| Merged main | `98855aeaccddfff707dd0a9c2732f151b0e07e4f` |
| Attempt history | `EXACTLY ONE ATTEMPT / NO RERUN` |
| Matrix | `COMPLETE — 6 × 400` |
| Integrity | `PASSED` |
| Replay | `IDENTICAL` |
| Result scope | `DIAGNOSTIC / CALIBRATION ONLY` |
| Independent review | `PASS` |
| Stage 2 unblock conditions | `ALL YES` |
| Findings | `MEDIUM ledger drift; LOW unexplained git.dirty disclosure; LOW two-step guard sunset` |

### FINANCEIQ-STAGE1B-INDEPENDENT-REVIEW-CLOSEOUT (2026-09-02; append-only)

- Independent review of governed run `cb3cf211a21ec39d65deec6f49230306cfd882f7` at merged main `98855aeaccddfff707dd0a9c2732f151b0e07e4f` is **PASS**.
- The run completed exactly one attempt with no rerun and the complete 6 × 400 matrix; integrity passed and replay was identical.
- The result is diagnostic/calibration only. Stage 2 unblock conditions are all **YES**.
- Independent-review findings are preserved as: **MEDIUM ledger drift**; **LOW unexplained git.dirty disclosure**; **LOW two-step guard sunset**.
- This closeout changes bookkeeping only: Stage 1/1b result artifacts, Stage 2 design, and `experiments/significance.py` were not changed; no commit was made.

### FINANCEIQ-SIGNIFICANCE-REMEDIATION-PRECOMMIT-HYGIENE (2026-09-02; append-only)

- `experiments/significance.py` was remediated from old SHA `5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6` to new SHA `08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3`.
- The remediation is fail-closed validation only; deterministic finite-input behavior is unchanged.
- Historical Stage 1, Stage 1b, excess-basis, serving-eval, and contamination artifacts remain evidence under the old implementation and are not rewritten.
- `contamination_lab`'s expected SHA is repinned only as a forward-run gate. No historical scientific rerun occurred, and no Stage 2 run occurred.
- Stage 2 registration must pin the repaired SHA after this remediation merges.

### FINANCEIQ-STAGE2-LEDGER-CLOSE (2026-09-03; append-only)

| State item | Status |
|---|---|
| Stage 2 registration | `COMPLETED` |
| Stage 2 implementation | `COMPLETED` |
| Governed run | `COMPLETED EXACTLY ONCE` |
| Post-run audit | `PASS` |
| Scientific decision | `PASS` |
| NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN | `1000/1000 analyzable; invalid 0; 26 family rejections; 26/1000 = 0.026; PASS; registered critical fail count >=65` |
| NC1_TARGET_PERMUTATION | `1000/1000 analyzable; invalid 0; 28 family rejections; 28/1000 = 0.028; PASS; registered critical fail count >=65` |
| NC0_MASK_ALIGNED_DIAGNOSTIC | `1000/1000 analyzable; 42 derived family rejections; 42/1000 = 0.042; NON-GATING; NOT an FPR estimate; outside confirmatory family` |
| Result commit | `67f29dc19e2c45784d895b84f8f9c6b42c25899b` |
| Merge / main SHA | `30ea68a5649d4ac8a847831426b02afa14171abe` |
| Pull request | `#38` |
| PR verification | `33778492352 — success; exact head 67f29dc19e2c45784d895b84f8f9c6b42c25899b` |
| Post-merge verification | `33779508174 — success; event push; exact head 30ea68a5649d4ac8a847831426b02afa14171abe` |
| Replay | `NOT REQUIRED / NOT RUN` |
| Result artifacts | `IMMUTABLE — experiments/results_thesis/negative_control/ was not edited` |
| Fixed context | `FROZEN DATASET / PIPELINE CONTEXT` |
| Required limitations | `Low power near true FPR 0.06; registered power about 0.270. Equivalence delta 0.05 is descriptive / non-gating. FinanceIQ SESOI remains unresolved. Diagnostic is non-null, non-gating, and not an FPR estimate.` |
| Historical Stage 1 / Stage 1b artifacts | `NOT RERUN OR REWRITTEN` |
| Stage 1 status | `FAILED AS WRITTEN — INFORMATIVE` |
| Stage 1b status | `DIAGNOSTIC / CALIBRATION ONLY` |
| Stage 2 closure | `FULLY CLOSED` |

Stage 2 PASS supports only the conclusion that the significance apparatus did
not exhibit registered gross false-positive inflation under the two frozen null
constructions in this frozen dataset / pipeline context. It does not establish
absence of leakage, absence of all dependence, predictive edge, alpha,
investment value, universal calibration, or production readiness. Stage 3 and
further model-development work must not reinterpret Stage 2 outside its
registered scope.

## FINANCEIQ-PANEL-V2-PIT-PREREGISTRATION-RECONCILE-AND-COMPLETE (2026-09-05; append-only)

| Field | Value |
| --- | --- |
| Task | `FINANCEIQ-PANEL-V2-PIT-PREREGISTRATION-RECONCILE-AND-COMPLETE` — preregistration/governance only |
| Worktree | `/Users/salihcamci/Desktop/Projects/First_Priority_Projects/FinanceIQ/.claude/worktrees/financeiq-engineering-audit-a41604` |
| Branch / base | `local/financeiq-panel-v2-pit-preregistration-1642d6` at authoritative base `c418563f432f5b253fb3b0e69619c76608ea15ea` |
| Registration status | `PASS` — protocol `FI-PANEL-V2-PIT-v1` completed; `FULL_PANEL_FEASIBLE=CONDITIONAL` not confirmed; `COLLECTION_READY=NO` |
| Owner locks | D1–D7 preserved. D1 uses the inclusive Europe/Istanbul calendar-year-end cutoff and requires separate `feature_year`, `fiscal_year_of_record`, `source_document_id`, `first_publication_timestamp`, and `pit_cutoff_timestamp`. |
| Source taxonomy | Exact frozen SC-1…SC-10 taxonomy restored after discarding the interrupted conflicting numbering. Hard blockers: SC-1, SC-2, SC-5, SC-6, SC-8; access/depth gates: SC-4, SC-7; normalization/definition gates: SC-3, SC-9, SC-10 |
| Reconciled contracts | TC-A annual target and exact/representation-only decimal overlap diagnostics; separate TMS 29/TAS 29 accounting fields; XU100 BIST 100 `PRICE_INDEX` continuity; legacy 17 quarantine; concept-group eligibility; B1–B8 prospective dispositions; executable no-peek source audit |
| Changed paths | `docs/PREREGISTERED_PANEL_V2_PIT.md`; `docs/panel_v2/pit_cell_evidence.schema.json`; `docs/panel_v2/source_manifest.schema.json`; `docs/panel_v2/applicability_rules.csv`; `scripts/panel_v2/__init__.py`; `scripts/panel_v2/registration.py`; `tests/test_panel_v2_registration.py`; `TASK_STATE.md` |
| Discarded interruption artifact | `docs/panel_v2/pit_row_eligibility.schema.json` does not exist and was not retained: it was a provisional interruption artifact outside the smallest required registration set. Row-eligibility fields stay declared in `scripts/panel_v2/registration.py` as `ROW_ELIGIBILITY_FIELDS`. No governed data root was created |
| Verification | `/opt/anaconda3/bin/python -m pytest tests/test_panel_v2_registration.py -q` → `17 passed`; both registration JSON schemas parsed successfully; CSV has 48 rows with 12 columns; no target file was opened; no target overlap value was inspected |
| Untouched boundary | No data collection, price/benchmark fetch, company-value extraction, real panel build, scientific run, old-data mutation, `Makefile` edit, `artifact_registry.json` edit, or `docs/VERIFICATION_BASELINE.md` edit; no commit/push/merge |
| Claim boundary | Registration/governance only. It establishes no predictive edge, no availability, no source-rights clearance, and no scientific result. Research support only; not investment advice. |

## FINANCEIQ-PANEL-V2-PIT-PREREGISTRATION-CRITICAL-MICROFIX (2026-09-05; append-only)

| Field | Value |
| --- | --- |
| Task | `FINANCEIQ-PANEL-V2-PIT-PREREGISTRATION-CRITICAL-MICROFIX` — registration microfix only; closes the independent review findings C1, C2, H1–H5, M1–M3 against the same candidate |
| Branch / base | `local/financeiq-panel-v2-pit-preregistration-1642d6` at authoritative base `c418563f432f5b253fb3b0e69619c76608ea15ea` |
| C1 — evidence column domain | `pit_cell_evidence.column` is now a Draft 2020-12 enum of exactly the registered 40 governed features, not an arbitrary string. Target columns, `next_year_*`, `target_year`, PIT metadata, eligibility fields, identity helpers, and `_legacy_unverified` names are all unrepresentable as governed feature cells; legacy cells stay in the separate `legacy_unverified.csv` sidecar |
| C1 — non-null fail-closed | For `is_null=false` the schema requires numeric `value`, null `null_reason`, `pit_ok=true`, a value-originating `source_class`, non-empty source identity/extraction fields, 64-hex `document_sha256`, admissible `frozen_screen_status`, and non-null timezone-bearing `first_publication_timestamp`, `knowledge_timestamp`, `retrieval_timestamp`, and `pit_cutoff_timestamp` |
| C1 — timestamp ordering | Classified `DEFERRED_TO_IMPLEMENTATION`, not claimed as enforced. Draft 2020-12 cannot relationally compare two instance timestamps. `pit_ok` is registered as computed-never-trusted with predicate `knowledge_timestamp <= pit_cutoff_timestamp` in `Europe/Istanbul`, and five fail-closed conditions are registered for an implementation validator that does not exist |
| C2 — financial_debt_ratio | A non-null cell now requires `SC-10` origin plus `definition_id`, `definition_text`, `numerator_definition`, `denominator_definition`, `definition_source_document_id`, and `definition_publication_date`; `definition_id` may not be empty or a sentinel. No formula was invented. Panel-wide `definition_id` consistency is registered and `DEFERRED_TO_IMPLEMENTATION`. G5 consequences remain exactly Stage-A §10.3 |
| H1 — no-peek | Removed the conditional "inspect the future reader if it exists" pattern. Proved now: both `scripts/panel_v2` modules contain no I/O call and their whole import closure is `{__future__, types}`; no registration artifact passes a target name to a reader. `feasibility.py`, `eligibility.py`, `builder.py`, and `splits.py` are asserted absent, and `FUTURE_NO_PEEK_ENFORCEMENT = DEFERRED_TO_IMPLEMENTATION` |
| H2 — AR-042 / AR-044 | Corrected to Stage-A §10.4. `AR-042`: `ALWAYS_APPLICABLE` → `CONDITIONAL` on the verbatim growth condition, and the unregistered token `BASIS_MISMATCH_OR_BASIS_UNKNOWN` → `BASIS_MISMATCH;BASIS_UNKNOWN`. `AR-044`: `ALWAYS_APPLICABLE` → `CONDITIONAL` on the verbatim T-2..T trading condition, matching `AR-029`. The full 48-row audit also corrected `AR-041` (`PIT_INADMISSIBLE;PIT_UNVERIFIABLE`), `AR-010` (`MISSING_SOURCE_CLASS_GAP` per §10.5), the five growth rows' truncated condition text, and the four panel-wide gates (now `PER_FEATURE_APPLICABILITY`). Stage-A was not edited and no exemption was created |
| H3 — vector and legacy authority | The governed 40 are re-derived twice from authorities independent of this candidate — Stage-A §9, and the AST-lifted `_feature_cols` exclusion set applied to the modeling dataset header — and both reproduce the frozen hashes. The legacy 17 are re-derived from `data/provenance/cell_provenance_public_2020_2025.csv` where `source_class = vendor_xlsx`. The manifest schema freezes vector identity as consts (`prefixItems` + `items:false` + const hashes + `matches_registered_hash:true`) and adds a required `legacy_quarantine` block |
| H4 — B1–B8 | `CLOSED_BY_DESIGN` removed from every surface. Each defect now carries two independent statuses; all eight are `REGISTERED_DESIGN_CONTRACT` + `DEFERRED_TO_IMPLEMENTATION`. `B1_B8_RUNTIME_ENFORCED = NO`, `B1_B8_IMPLEMENTATION_TESTS_EXIST = NO` |
| H5 — source-class taxonomy | Sentinels `NONE` and `LEGACY_VENDOR_SNAPSHOT` removed from the cell schema enum. The taxonomy is exactly `SC-1`…`SC-10` in the document, `registration.py`, both schemas, and the tests; `source_class` may be null only on a null cell |
| M1 / M2 / M3 | Artifact tuple now names `scripts/panel_v2/__init__.py` (the package marker is `__init__.py`; no `init.py` exists or was created). Docs lint's three violations fixed within the mutation surface — the two reserved roots marked `(proposed)`, the provisional schema path reworded as non-existent — with no dummy files created. Nine implementation-only controls registered as `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| Target overlap | Untouched and still passing: exact Decimal/canonical equality, mechanically derived representation interval only where a source declares rounding precision, no bound under unknown rounding, no arbitrary numeric tolerance. No overlap value was inspected |
| Owner locks | D1–D7 preserved exactly. No owner decision is open |
| Changed paths | `TASK_STATE.md`; `docs/PREREGISTERED_PANEL_V2_PIT.md`; `docs/panel_v2/applicability_rules.csv`; `docs/panel_v2/pit_cell_evidence.schema.json`; `docs/panel_v2/source_manifest.schema.json`; `scripts/panel_v2/__init__.py`; `scripts/panel_v2/registration.py`; `tests/test_panel_v2_registration.py` |
| Verification | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /opt/anaconda3/bin/python -m pytest -p no:cacheprovider tests/test_panel_v2_registration.py -q` → `27 passed`. Both schemas checked against the Draft 2020-12 metaschema and exercised with accept/reject fixtures (33/33 cell, 14/14 manifest) using an out-of-tree harness, so no undeclared `jsonschema` dependency enters the root suite. Docs lint and claims lint pass; `git diff --check` clean |
| Untouched boundary | No data collection, price/benchmark fetch, company-value extraction, real panel build, target-overlap inspection, scientific run, or old-data mutation. `Makefile`, `artifact_registry.json`, `docs/VERIFICATION_BASELINE.md`, `data/**`, `experiments/**`, and `scripts/data_collection/**` unchanged. Raw and generated v2 roots absent. No stage, commit, or push |
| Claim boundary | Registration/governance only. It establishes no predictive edge, no source availability, no rights clearance, and no scientific result. Research support only; not investment advice |

### FINANCEIQ-THESIS-STAGE3-REGISTRATION-CLOSEOUT (2026-09-04; append-only)

- Stage 3 is prospectively registered: **REGISTERED / NOT IMPLEMENTED / NOT
  RUN**. This closeout records **NO STAGE 3 RUN**, **NO STAGE 3 RESULT**, and
  **NO GUARD REPAIR**; implementation remains future work.
- The closed first-draw family is exactly: `4000
  FUTURE_YEAR_FEATURE_LEAKAGE`, `4001 T_TPLUS1_MISALIGNMENT`, `4002
  TARGET_LEAKAGE_INTO_FEATURES`, `4003 LOOKAHEAD_UNIVERSE_MEMBERSHIP`, and
  `4004 DUPLICATE_ROW_INFLATION`.
- The only frozen source is
  `data/trusted_clean/modeling_dataset_training_2020_2025.csv`, SHA256
  `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.
- The expected guard gaps are exactly `4000`, `4001`, and `4003`
  (`NOT_DETECTED`). `4002` and `4004` are expected `DETECTED`, each by an
  existing surface found on the authoritative base: `4002` by the reachable
  cell-provenance column-coverage guard (reached through a private provenance
  root), `4004` by the duplicate-key guards. These are prospective expectations
  only. The expected first-draw outcome **FAIL — INFORMATIVE** is not an
  observed scientific outcome.
- `scripts/data_collection/build_cell_provenance.py` is classified as a
  reachable provenance/integrity guard, not input-blind: its root is a caller
  parameter and only the relative input path is frozen. No guard was added or
  repaired; the named target-leakage validator condition remains structurally
  unreachable and is recorded as a separate existing-but-useless surface.
- The registration tests construct no injected frame. Behavioral verification of
  every frozen injection count belongs to the future Stage 3 implementation
  tests.
- `experiments/run_experiments.py` is pinned by full SHA256
  `265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543`, unchanged
  from the authoritative base, and the registered secondary splits equal
  `experiments.run_experiments.SPLITS` exactly. The six stale derived
  `next_year_*` target columns are disclosed and fenced out of the Stage 3
  estimand; consuming one classifies `4001` `INCONCLUSIVE`.
- No Stage 3 result root, runner, Makefile target, or generated-output contract
  exists. Stage 7 remains blocked under the existing “Only after stages 1–3
  pass” wording because Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**.
- Claim boundary: registration only; no predictive-edge, alpha, investment,
  production-readiness, or universal-safety claim. Research support only, not
  investment advice.

### FINANCEIQ-THESIS-STAGE3-IMPLEMENTATION-ONLY (2026-09-05; append-only)

- This is implementation-only work on authoritative main
  `bed1178989f75ef95003d8b2ee3d5ed279481fa0`; the merged registration remains
  frozen. Stage 3 is **IMPLEMENTED / NOT RUN**: **NO GOVERNED STAGE 3 DRAW**,
  **NO STAGE 3 RUN**, **NO STAGE 3 RESULT**, and **NO GUARD REPAIR**.
- The exact closed family remains `4000 FUTURE_YEAR_FEATURE_LEAKAGE`, `4001
  T_TPLUS1_MISALIGNMENT`, `4002 TARGET_LEAKAGE_INTO_FEATURES`, `4003
  LOOKAHEAD_UNIVERSE_MEMBERSHIP`, and `4004 DUPLICATE_ROW_INFLATION`. The
  prospective map remains 4000 `NOT_DETECTED`, 4001 `NOT_DETECTED`, 4002
  `DETECTED`, 4003 `NOT_DETECTED`, and 4004 `DETECTED`; the expected
  **FAIL — INFORMATIVE** outcome is prospective expectations only and not an
  observed scientific outcome.
- The expected guard gaps are exactly 4000, 4001, and 4003; 4002 and 4004 are
  expected `DETECTED`. `experiments/run_experiments.py` remains pinned by full
  SHA256 `265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543`.
- The frozen source remains
  `data/trusted_clean/modeling_dataset_training_2020_2025.csv` with SHA256
  `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.
- `experiments/thesis/defect_injection.py` implements the explicit runner and
  CLI, private in-memory/private-temp containment, private provenance root
  reachability, restoration/cleanup proof, fail-closed `INCONCLUSIVE` behavior,
  the 4001 stale-derived-target consumer boundary (consumption classifies 4001
  `INCONCLUSIVE`), and the existing 4002/4004 guard surfaces. No new guard was
  added and no existing guard was repaired. The secondary IC is descriptive,
  exact-canonical-split, per-split Spearman with Ridge alpha 1.0 and
  `delta_ic = injected - clean`; it is unpooled, non-gating, and has no
  threshold or significance test.
- `Makefile` exposes `make thesis-stage3`, the private replay probe, and the
  identical-configuration crash-recovery target. `artifact_registry.json`
  owns the exact result root prospectively; the
  `experiments/results_thesis/defect_injection/` result root remains absent
  until owner authorization. The result root remains absent. README status and
  this ledger now record the implementation boundary. Stage 7 remains blocked.
- Focused implementation tests: `tests/test_thesis_stage3_implementation.py`
  passed 29 tests without calling the governed target or creating the result
  root. The exact full-root command passed 1386 tests and had one failure only
  at `tests/test_contamination_lab.py::test_changed_path_allowlist_is_exact`,
  which correctly reports the new Stage 3/status files outside that existing
  lab-specific dirty-worktree allowlist; that fail-closed guard was not
  broadened. `make data-validate`, `make claims-lint`, `make docs-lint`, and
  `git diff --check` passed. Owner decision remains required for the allowlist
  versus clean-commit integration step before the readiness review is green.
