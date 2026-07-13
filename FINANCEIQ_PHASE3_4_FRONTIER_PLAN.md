# FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md

Frontier planning record for Phase 3 and Phase 4. Written 2026-07-13 from direct repository inspection at commit `fbab761f` (clean tree), with both suites re-run this session: **root 168/168 passed, backend 85/85 passed** (observed, not assumed). This document holds the post-Phase-2 maturity audit, the full candidate register, the adversarial review dispositions, and the planning outputs (dependency graph, waves, verification matrix, model allocation, prioritized selections).

**Execution source of truth remains `FINANCEIQ_AGENT_TASK_QUEUE.md`** — Phase 3 execution packets live there. This file is the *why/what-else/what-was-rejected* record; it never duplicates a packet. Strategic direction lives in `FINANCEIQ_MOONSHOT_ROADMAP.md` §9. Nothing here overrides the project's core contract: no fabricated data, no leakage, no predictive-edge claims, and the committed conclusion — **no reliable predictive edge** — stays the headline unless new committed evidence changes it through the documented flow (experiments → significance → audit → claims guide → MCC bump).

---

## 1. PASS 1 — Post-Phase-2 maturity audit (evidence-grounded)

### 1.1 What FinanceIQ now is, end to end

A completed capstone plus a shipped "instrument the negative result" layer. The full chain, verified this session:

- **Pipeline:** corrected yearly ingest + Yahoo prices + manual shares → `data/trusted_clean/modeling_dataset_2020_2025.csv` (403 rows / 81 tickers / 321 target rows), leakage/frozen guards, generated dictionary + 61/61 feature passports (`DATA_01_DATA_DICTIONARY_AUDIT.md`, `data/trusted_clean/feature_passports.json`).
- **Evaluation:** walk-forward harness (9 models = 3 baselines + 6 ML), committed per-ticker prediction dumps (n=80/split × 3 test years), permutation + bootstrap significance with Bonferroni family correction, power analysis (detectable |IC| 0.309 one-year / 0.182 three-year), real-TRY and USD parallel target bases (`experiments/results_real_terms/`), regime context with an honest `not_computed_insufficient_regime_diversity` state, friction sensitivity with in-canvas hypothetical stamps, confidence calibration audit (finding: hybrid confidence constant 0.25, calibration not estimable), and registered run manifests with `make research-verify-run`.
- **Governance:** Model Confidence Contract v1.7.0 + `make claims-lint` (route-coverage drift guard, backend response-file scan, exact-line allowlist), run-directory governance (manifest-of-record = leaderboard SHA match), append-only analyst dissent ledger with a score-isolation pin test.
- **Product:** 23 page files / 24 routes (verified in `frontend/src/App.jsx`), including `/autopsy` (six exhibits + friction panel), `/courtroom` (four lenses, no verdict field, citation chips), Instrumented Null panel on `/experiments`, RegimeStrip on `/benchmark` + `/experiments`, passport popover on `/research`, DissentLedger on the Labs pages.
- **Demo:** `docs/DEMO_RUNBOOK.md` with rehearsed transcripts and fallback branches; `make demo-check`.

### 1.2 What exists but is not productized (verified by grep this session)

| Artifact | State | Product surface |
|---|---|---|
| Skeptic challenge report (`/research/skeptic/{ticker}`) | shipped, tested | **None standalone** — only embedded inside Courtroom (`grep -rli skeptic frontend/src` → CourtroomPage only). R2-SKEPTIC-01 explicitly deferred the panel. |
| Real-TRY / USD significance (`experiments/results_real_terms/`) | shipped | **None** (`grep -rli "real_terms\|usd_basis" frontend/src` → empty) |
| Calibration audit (`experiments/results/calibration_report.*`) | shipped | **None** (no page renders the audited finding) |
| Model disagreement (raw material in `predictions_test_*.csv`) | dumps committed | Not computed, not surfaced |
| Alternative target definitions (`leaderboard_by_target.csv`: excess vs BIST100, outperform, top-20pct) | leaderboard-level only | No significance treatment, no surface |
| Run manifests (`experiments/results/runs/`) | 3 committed | No UI/registry surface |

### 1.3 The single biggest untested evaluation gap

The **user-facing serving heuristic (`forecasting_csv_service.train_parameters`/`run_forecast`) is not among the 9 evaluated models** (verified: dump/leaderboard model lists contain 3 baselines + 6 ML only). METHODOLOGY documents the distinction honestly, but the ranking users actually see has never received the walk-forward significance treatment the project built. This is Phase 3's highest-value research task (R3-SERV-01).

### 1.4 Documentation truth drift (the recurring failure mode, recurred again)

All Phase-2 work is committed (`git status` clean at `fbab761f`), yet:

- `TASK_STATE.md` and the queue's Phase-2 ledger still say "DONE (uncommitted) … no commit by request" for ~12 tasks.
- `CLAUDE.md`/`AGENTS.md` "Known test-suite state" says root 106 / backend 55 (observed now: 168 / 85). `AGENTS.md` is one revision staler than `CLAUDE.md` (still says 51/95-97, "verified 2026-07-08").
- `PRD.md` Current Reality still says backend 51/51, root 95/97, "21 pages".
- `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §2 says "148 automated tests"; §15 checklist says 51/51 and 97/97.
- `FINANCEIQ_SMALL_MODEL_RULES.md` §9/§12 baselines say 51 backend / 97 root.
- `.agent/memory/01-generated-experiment-summary.md` cites a stale sentence that no longer exists in the regenerated `experiment_summary.md` (grep: 0 hits for "static snapshot"/"DEGENERATE"); the lesson stands, its evidence note is stale.
- `TASK.md` still routes the next agent to Phase-1 OPS-01 (corrected by this planning pass).

This is exactly the drift R2-GOV-01 fixed once; it re-accumulated within one phase. Phase 3 therefore starts with a truth-sync task **and** adds structural fixes (a single verification-baseline reference target, a docs link/path lint, an artifact ownership registry, and an MCC↔evidence consistency guard) so the class of failure gets a tripwire instead of periodic manual repair.

### 1.5 Governance gaps that could cause future drift

- **No artifact ownership registry:** ~40 generated files across `experiments/results*/` and `data/trusted_clean/` have generators scattered across 15+ Makefile targets; nothing machine-checks "every generated artifact has an owner and a regeneration path," and nothing detects a report whose `source_artifacts` checksums no longer match the committed inputs.
- **MCC evidence-state is hand-asserted:** `backend/tests/test_confidence_contract.py` pins one boolean (`reliable_predictive_edge_observed is False`); nothing binds `evidence_basis[].finding` strings or `evidence_state` flags to the committed reports they cite. If a future run changed a conclusion, the contract would drift silently.
- **Legacy DB path duplicates ownership:** `scoring_service.py` + `adaptive_weights_service.py` + `sector_service.py` (z-scores with `MIN_PEERS = 2` over unprovenanced DB sector codes) + `ForecastingDetailPage.jsx` legacy `/predict/trends|heatmap` calls form a second scoring path whose data provenance the trusted pipeline never validates. METHODOLOGY documents the risk; no runtime demarcation or owner decision exists.
- **Authenticated verification is structurally blocked:** four consecutive task reports (Autopsy, Courtroom, Demo runbook, Friction) recorded "protected-page visual verification blocked by missing approved Supabase session." There is one legacy Playwright spec (`frontend/tests/e2e-forecasting.spec.js`) that assumes open email/password signup — inconsistent with the Supabase auth + private-lockdown reality. No authenticated E2E/visual harness exists.
- **Conclusions still requiring manual interpretation:** limitations live in per-report `limitations` arrays + METHODOLOGY prose + audit sections; no aggregated register exists, so examiner-grade "what are ALL the known weaknesses" answers are assembled by hand each time.

### 1.6 Unresolved research limitations (planning constraints, all still true)

- Retrospectively fixed cohort; no point-in-time BIST100 membership, delisting/suspension, or symbol-change history (`docs/universe_audit.md`). Any task assuming historical membership is invalid without a sourcing spike.
- `sector` is unpopulated in all trusted datasets (METHODOLOGY §Sector-label provenance). Any sector-based task is invalid without a sourced taxonomy + owner sign-off.
- One macro regime; regime-conditional statistics remain untestable.
- Hybrid confidence constant at 0.25; the R2-CAL-01 follow-up (relabel vs redesign) remains an **owner decision, not authorized work**.
- Reproduction is environment-qualified (byte-identity only within recorded environments).
- Deployment liveness (Render/Vercel/Supabase) remains unverified from the repo.

---

## 2. PASS 2 — Candidate register (43 candidates generated)

Legend — Disposition: **ACCEPT-P** = accepted with execution packet in `FINANCEIQ_AGENT_TASK_QUEUE.md` Phase 3; **ACCEPT-C** = accepted, compact spec (packet written later, after listed gate); **SPIKE** = research spike first; **MERGE** = merged into another candidate; **DEFER** / **REJECT** with reason in §3. Values: L/M/H/VH. Models named per the queue's key (Sol/Terra/Opus/Fable) with §6 mapping to currently available labels.

#### C-01 · R3-GOV-01 — Post-Phase-2 truth sync
3A · P1 · Docs/Verification · Difficulty L · **ACCEPT-P**
Evidence: §1.4 drift list (each item grep/git-verified this session). Creates: docs that match the repo again + `docs/VERIFICATION_BASELINE.md` as the single dated counts ledger other docs cite instead of embedding numbers. Not duplicative: R2-GOV-01 fixed the 2026-07-12 snapshot; this fixes the post-Phase-2 snapshot *and* removes the structural cause (embedded counts). Deps: none. Modules: root `.md` files + `.agent/memory/01`. Research M / Demo L / CV L (protects everything). Claim risk L; tech risk L. Impl **Sol low**; review none (self-verifying commands).

#### C-02 · Machine-readable verification baseline file
**MERGE → C-01** (the baseline doc is a GOV-01 step; a separate task added no distinct capability).

#### C-03 · R3-REL-01 — Artifact ownership & regeneration registry + staleness guard
3A · P1 · Governance/Backend · Difficulty M · **ACCEPT-P**
Evidence: §1.5 first bullet; `significance_report.json`/`friction_report.json` already embed `source_artifacts` checksums nothing re-verifies. Creates: curated `artifact_registry.json` (path → generator command → inputs → hand-edit-forbidden flag) + root test enforcing full coverage of `experiments/results*/` and `data/trusted_clean/` + checksum staleness tripwire. Not duplicative: run manifests cover *runs*; this covers *files* and their owners. Deps: none. Modules: new registry + `tests/test_artifact_registry.py`. Research M / Demo M / CV H ("artifact governance" line). Claim risk L; tech risk M (glob coverage edge cases). Impl **Opus medium**; review Terra low.

#### C-04 · Stale-evidence detector
**MERGE → C-03** (staleness = checksum edges of the registry; not a separate system).

#### C-05 · R3-STAT-01 — Ranking & cohort stability under resampling
3B · P1 · Research/Statistics · Difficulty M-H · **ACCEPT-P**
Evidence: committed dumps (9 models × 80 rows × 3 years); Skeptic check 3 measures cross-model flips but nothing measures resampling fragility; power analysis says small rank gaps are unresolvable. Creates: seeded bootstrap/jackknife suite → per-ticker top-10 membership frequency, rank intervals, and pooled-IC sensitivity to cohort perturbation including public-40 subset restriction (`experiments/results_rank_stability/`, proposed). Not duplicative: significance tests IC vs null; this measures *ranking* and *cohort* fragility. Deps: none. Research VH / Demo H / CV H. Claim risk M (stability ≠ confidence — wording pinned in packet); tech risk M. Impl **Opus high**; review Fable medium (wording + design).

#### C-06 · Cohort-selection sensitivity (public-40 subset, leave-k-out IC)
**MERGE → C-05** (same bootstrap engine, one artifact suite; splitting would duplicate machinery).

#### C-07 · R3-STAT-02 — Model disagreement atlas (artifact)
3B · P2 · Research · Difficulty M · **ACCEPT-P**
Evidence: dumps committed; disagreement never computed (§1.2). Creates: pairwise per-year model rank correlations + per-ticker cross-model rank spread → `experiments/results_disagreement/` (proposed). Not duplicative: Skeptic's instability check is per-ticker boolean-ish; this is the full matrix. Deps: none; UI surface is C-38 later. Research H / Demo M (artifact) / CV M. Claim risk L (disagreement supports the uncertainty narrative); tech risk L. Impl **Terra medium**; review Opus low.

#### C-08 · R3-SERV-01 — Serving-heuristic walk-forward significance parity
3B · P1 · Research/Statistics · Difficulty H · **ACCEPT-P**
Evidence: §1.3 — the user-facing ranking heuristic is absent from the evaluated model set (verified against dump/leaderboard model lists); METHODOLOGY documents the gap in prose only. Creates: the exact serving heuristic evaluated under the same walk-forward + permutation/bootstrap treatment, results in `experiments/results_serving_eval/` (proposed), and a METHODOLOGY paragraph closing the "heuristic ≠ evaluated models" loop with numbers. Not duplicative: no existing artifact evaluates this code path. Deps: none (imports service read-only; calibration bench precedent). Research VH / Demo H / CV VH. Claim risk **H** (whatever IC appears will be quoted); tech risk H (service must be driven unmodified). Impl **Fable high** (or Opus high + Fable review mandatory).

#### C-09 · R3-NULL-01 — Negative-control / placebo laboratory
3B · P1 · Research/Statistics · Difficulty H · **ACCEPT-P**
Evidence: no negative control exists; the significance machinery has never been shown to *reject* a known-null input (standard reviewer question). Creates: seeded placebo-feature runs through the same harness + empirical false-positive-rate report of the family-wise gate → `experiments/results_placebo/` (proposed). Not duplicative: permutation nulls shuffle targets *within* the real run; this feeds the whole machinery known-noise inputs. Deps: none. Research VH / Demo M-H / CV H ("I placebo-tested my own test rig"). Claim risk M (a lucky placebo "hit" must be reported, not hidden); tech risk M-H. Impl **Opus high**; review Fable medium.

#### C-10 · R3-INF-01 — Influence diagnostics (leave-one-out IC influence map)
3B · P2 · Research · Difficulty M · **ACCEPT-P**
Evidence: dumps allow exact LOO recomputation; extreme TRY-era outliers are a documented concern (METHODOLOGY rank-normalization rationale) but per-observation influence on pooled IC was never measured. Creates: deterministic per-ticker-year ΔIC influence artifact → `experiments/results_influence/` (proposed). Not duplicative: coverage_impact measures feature coverage, not observation influence. Deps: none. Research H / Demo M / CV M-H. Claim risk L-M; tech risk L. Impl **Terra medium**; review Opus low.

#### C-11 · R3-TGT-01 — Excess-return-basis significance treatment
3B · P2 · Research · Difficulty M · **ACCEPT-P**
Evidence: `leaderboard_by_target.csv` already evaluates `next_year_excess_return_vs_bist100` at leaderboard level; `next_year_excess_return_vs_bist100` is a dataset column; no significance treatment exists for it (only nominal/real/USD have it). Creates: harness+significance run on the excess basis → `experiments/results_excess/` (proposed), completing the target-definition sensitivity family. Not duplicative: R2-REAL-01 covered currency/inflation bases, not the benchmark-relative basis. Deps: none. Research H / Demo M / CV M. Claim risk M (another quotable IC family — same pairing rules); tech risk M (excess target has nulls where benchmark coverage is missing — n shrinks and must be reported per year). Impl **Opus medium** (Terra acceptable with the R2-REAL-01 pattern); review Opus low.

#### C-12 · Binary-target (outperform / top-20pct) significance
**REJECT** — Spearman-IC + within-year permutation machinery is designed for continuous targets; on binary targets the pooled-IC/permutation design degenerates (mass ties, rank-biserial reinterpretation) and would require a differently designed test family for little added insight beyond C-11. A wrongly reused machinery would be pseudo-rigor.

#### C-13 · R4-DIM-01 — Feature redundancy & effective dimensionality
4A · P2 · Research · Difficulty M · **ACCEPT-C** (gate: Phase 3B core landed)
Evidence: 40 features vs ≤240 training rows/split (audit §10); no committed measurement of how many *effective* dimensions the feature set has. Creates: correlation-cluster + eigenvalue-spectrum artifact; candidate future Autopsy exhibit ("40 features ≈ k effective"). Research H / Demo M / CV M. Claim risk L; tech risk L. Impl **Terra medium**; review Opus low.

#### C-14 · R3-PREREG-01 — Pre-registered 2026 forward-outcome evaluation protocol
3B · P1 · Research governance · Difficulty M-H · **ACCEPT-P**
Evidence: the 2026 forward ranking (`GET /forecasting/inference?year=2025`) is computed at request time and never frozen; 2026 outcomes will mature in early 2027; nothing prevents post-hoc analysis choices when they do. Creates: a frozen, checksummed forward-ranking artifact + a committed, dated protocol (single prespecified test, pre-written interpretation grid for every outcome, power statement: one 40-ticker year detects only |IC| ≥ ~0.431 — the protocol's honesty is the product) + an inert evaluation script that activates only when a sourced outcomes CSV exists. Not duplicative: manifests register past runs; this pre-registers a *future* analysis. Time-sensitive: must land before any 2026 outcome data exists. Research VH / Demo H / CV VH (genuine pre-registration is rare in student work). Claim risk M (protocol wording must pre-forbid edge claims in the "positive" cell); tech risk M. Impl **Opus medium-high**; review **Fable medium (wording grid mandatory)**.

#### C-15 · R3-MISS-01 — Serving-heuristic missingness sensitivity
3B · P2 · Research · Difficulty M · **ACCEPT-P**
Evidence: `run_forecast()` documents missing-features-reduce-confidence; nothing measures how *ranks* move under controlled feature-group masking; sparse-column silent-ranking is a named audit risk (§9). Creates: deterministic offline replay masking feature categories → per-ticker rank-delta matrix → `experiments/results_missingness/` (proposed). Base for the Phase-4 counterfactual explorer (C-38). Not duplicative: coverage_impact is harness-side; this is serving-side, the surface users see. Research H / Demo M-H / CV M-H. Claim risk M (labeled serving-heuristic-only); tech risk M. Impl **Opus medium**; review Terra low.

#### C-16 · R4-ROBUST-01 — Cellwise contamination stress laboratory
4A · P2 · Research · Difficulty H · **ACCEPT-C** (gate: C-09 landed — shares isolated-rerun discipline)
Evidence: growth columns contain documented extreme cells ("% in the trillions", METHODOLOGY); rank normalization is the mitigation but conclusion-invariance under cell trimming/winsorizing was never demonstrated. Creates: isolated-copy perturbation runs (trim/winsorize extreme cells, never touching canonical data) → conclusion-invariance report. Research H / Demo M / CV H. Claim risk M; tech risk H (must be provably isolated). Impl **Fable/Opus high**; review Fable medium.

#### C-17 · R4-PROV-01 — Per-cell provenance (passports v2)
4A · P2 · Data/Pipeline · Difficulty H · **ACCEPT-C** (gate: R3-REL-01 landed; generator-touching)
Evidence: roadmap §3.9 higher-end; row-level flags (`is_inference_row`, `price_data_available`) exist; "which cells were touched by the 2024 manual override / manual shares" is answerable from code+reports but not materialized. Creates: per-cell source-class artifact for the public dataset + query examples. Research M-H / Demo H / CV H. Claim risk L; tech risk H (extends `_data_dictionary()`-adjacent generation; byte-identity gates on all existing outputs). Impl **Opus high**; review Fable medium.

#### C-18 · R3-SPIKE-01 — Point-in-time universe sourcing spike
3C · P2 · Research/Data · Difficulty M · **SPIKE** (memo only; no data, no pipeline change)
Evidence: `docs/universe_audit.md` "Missing evidence" — constituent history, delistings, symbol changes all absent; multiple frontier ideas die without it. Creates: feasibility memo `docs/UNIVERSE_HISTORY_SOURCING_SPIKE.md` (proposed): which free/official sources (Borsa İstanbul index announcements, KAP disclosures) actually publish dated constituent/status history, at what effort, with a proposed manual-CSV schema — or the honest finding that no free source suffices. Gate for any point-in-time task; none may proceed without it. Research H (unblocks a family) / Demo L / CV M. Claim risk L (memo only); tech risk L. Impl **Opus medium** (source-credibility judgment); review Fable low.

#### C-19 · Dataset diff explorer / explainable rebuilds
**DEFER** — reruns are currently gated by all-or-nothing checksums, which has been sufficient (two byte-identical rerun events on record); a cell-level diff tool becomes valuable only when a deliberate rebuild task exists. Revisit alongside any pipeline-changing Phase-4 work (C-16/C-17 both mandate isolation instead of rebuilds).

#### C-20 · External-source cache governance
**REJECT** — Yahoo/CPI inputs already carry sidecars with source + retrieval dates and shape validation (R2-REAL-01 pattern); no concrete gap was found in inspection. A task needs a defect to fix.

#### C-21 · R3-UI-01 — Skeptic challenge panel (per-ticker UI)
3D · P1 · Frontend · Difficulty M · **ACCEPT-P**
Evidence: endpoint shipped + tested; R2-SKEPTIC-01 spec says "Frontend panel is a separate later task"; grep confirms no standalone surface (§1.2). Creates: prosecution-style panel on `CompanyResearchDetailPage.jsx` (already MCC-registered). Research M / Demo VH / CV H. Claim risk M (verbatim footer already fixed by the service); tech risk L. Impl **Terra medium**; review Opus low.

#### C-22 · R3-UI-02 — Return-basis lens (nominal / real-TRY / USD display)
3C · P1 · Backend+Frontend · Difficulty M-H · **ACCEPT-P**
Evidence: roadmap §3.2 higher-end never built; artifacts committed with zero surface (§1.2); METHODOLOGY carries pinned per-basis numbers and the 185.94%→74.07% 2022 illustration. Creates: read-only passthrough of committed per-basis significance + a Benchmark panel that *displays committed results per basis* (never recomputes chart series client-side). Research M / Demo H ("+186% nominal was not a bull market") / CV H. Claim risk **H** (three quotable IC families side by side — pairing rules mandatory); tech risk M. Impl **Opus medium-high**; review Fable low (copy check).

#### C-23 · R3-UI-03 — Calibration audit surfaced
3D · P2 · Backend+Frontend · Difficulty L-M · **ACCEPT-P**
Evidence: calibration report committed; finding ("constant 0.25 → not estimable") invisible in product although the UI *shows* confidence numbers everywhere — the exact honesty gap R2-CAL-01 measured. Creates: passthrough + panel stating the audited finding with replay-SHA framing. Research M / Demo M-H / CV M. Claim risk M ("audited" ≠ "calibrated" — wording pinned); tech risk L. Impl **Terra medium**; review Opus low.

#### C-24 · R4-UI-01 — Evidence registry & freshness page
4C · P2 · Frontend · Difficulty M · **ACCEPT-C** (gate: R3-REL-01) — absorbs C-25.
Evidence: registry (C-03) + manifests + `runtime-status` provide all data; no surface shows "what evidence exists, who generates it, is it fresh." Creates: read-only registry/health page (provenance graph rendering optional second step). Research M / Demo H / CV H. Claim risk L; tech risk M. Impl **Terra medium**; review Opus low.

#### C-25 · Research-state health dashboard
**MERGE → C-24** (freshness column of the same page; two pages would duplicate ownership).

#### C-26 · R3-MEMO-01 — Claim-aware research memo compiler
3D · P1 · Backend/Agent · Difficulty H · **ACCEPT-P**
Evidence: courtroom/skeptic/passports/significance provide citation-complete building blocks; no composed per-ticker research memo exists; claims-lint cannot see ad-hoc prose exports today. Creates: deterministic `POST /research/memo/{ticker}` composing existing artifacts with per-sentence citations, embedded disclaimers, generation stamp (git SHA + source checksums), and a shared citation-resolution helper; MCC scan extended to the new service. Research M-H / Demo VH / CV VH. Claim risk **H** (a memo *looks* like advice unless structurally prevented); tech risk M-H. Impl **Opus high**; review **Fable medium (mandatory)**.

#### C-27 · Shared evidence-citation validator
**MERGE → C-26** (the memo compiler builds the shared resolution module; courtroom citation tests already exist and stay).

#### C-28 · R3-MCC-01 — MCC evidence-state consistency guard
3A · P1 · Governance/Test · Difficulty M · **ACCEPT-P**
Evidence: §1.5 second bullet — contract findings/state are hand-asserted; only one boolean is test-pinned. Creates: root test binding `evidence_basis[].finding` and `evidence_state` flags to the committed reports they cite (e.g. `significant_fwer_0_05`), so a regenerated artifact with a changed conclusion fails CI and forces the documented MCC review flow. Not duplicative: `tests/test_contract_coverage.py` guards *page registration*, not evidence truth. Research M / Demo M (extends the tripwire demo) / CV H. Claim risk L (it *is* claim safety); tech risk L-M. Impl **Terra medium**; review Opus low.

#### C-29 · R3-AGENT-01 — Research-assistant grounded intents for Phase-2 artifacts
3E · P3 · Backend/Agent · Difficulty M · **ACCEPT-C** (gate: R3-UI-01 + R3-UI-03 landed, so intents cite surfaced evidence)
Evidence: `/research/ask` has five grounded intents predating Phase 2; significance/skeptic/calibration/friction artifacts are not queryable through it. Creates: new deterministic intents quoting committed artifacts with citations. Research M / Demo M-H / CV M. Claim risk M; tech risk M. Impl **Terra medium**; review Opus low.

#### C-30 · Small-model rules refresh
**MERGE → C-01** (stale baselines + new forbidden areas are truth-sync content; C-01 packet lists the exact §-edits).

#### C-31 · R3-E2E-01 — Authenticated E2E/visual verification spike
3A · P1 · Ops/Frontend · Difficulty M · **SPIKE**
Evidence: §1.5 fourth bullet — four task reports blocked on the same missing approved-session path; the one existing spec assumes an auth flow that no longer matches reality. Creates: memo `docs/E2E_AUTH_SPIKE.md` (proposed) evaluating, without weakening auth: Playwright `storageState` reuse after a documented manual login; a local-only Supabase test project with a seeded approved user; the backend's existing HS256 legacy-fallback path for API-level assertions. Recommends one approach + a follow-up implementation task. Research L / Demo M / CV M (unblocks *verification* for everything visual). Claim risk L; tech risk M. Impl **Opus medium**; review Terra low.

#### C-32 · R3-LINT-01 — Docs link & path lint
3A · P2 · Ops/Docs · Difficulty L · **ACCEPT-P**
Evidence: the dead `unnecessary/README.md` link was a real incident (OPS-02); DEMO_RUNBOOK and the planning layer now carry dozens of relative links/paths nothing checks. Creates: stdlib `scripts/lint_doc_links.py` + additive `make docs-lint` verifying relative links/cited paths in root+docs Markdown exist (explicit allowlist for intentional examples). Research L / Demo L / CV L-M. Claim risk L; tech risk L. Impl **Sol low** (Terra if the allowlist design needs judgment); review none.

#### C-33 · R3-LEGACY-01 — Legacy DB scoring/sector path demarcation audit
3A · P2 · Backend/Architecture · Difficulty M · **ACCEPT-P**
Evidence: §1.5 third bullet (all file-verified). Creates: decision memo `docs/LEGACY_DB_PATH_AUDIT.md` (proposed) mapping what is reachable, what depends on DB-populated sector codes the trusted path never populates, `MIN_PEERS = 2` risk, and duplicate ownership vs the CSV path — with owner options (runtime "legacy/unvalidated-provenance" labeling, quarantine, retirement). **Audit only; no code change.** Research M / Demo L / CV M. Claim risk M (the memo prevents a live claim hazard); tech risk L. Impl **Opus medium**; review Terra low.

#### C-34 · R3-LIMITS-01 — Automated limitations register
3D · P1 · Research/Docs · Difficulty M · **ACCEPT-P**
Evidence: `significance/calibration/friction/regime/alternative_targets` reports each carry machine-readable `limitations` arrays; universe audit and METHODOLOGY carry more in prose; no aggregate exists (§1.5 last bullet). Creates: generator `scripts/build_limitations_register.py` (proposed) → `docs/limitations_register.md` (generated, owned, regenerable) merging artifact `limitations` arrays with a curated seed list of doc-sourced limitations. Research H / Demo M-H / CV H (examiner-grade). Claim risk L (it aggregates *caveats*); tech risk L-M. Impl **Terra medium**; review Opus low.

#### C-35 · R4-EXAM-01 — Examiner question bank + defense pack
4B · P2 · Docs/Thesis · Difficulty M · **ACCEPT-C** (gate: C-34)
Evidence: claims guide §11/§14 and roadmap §7 hold a handful of rehearsed answers; a systematic weakness-driven question bank grounded in the limitations register does not exist. Creates: `docs/EXAMINER_QUESTION_BANK.md` — each question paired with the evidence-cited answer and artifact path. Research M / Demo H (viva) / CV VH. Claim risk M (answers must quote approved wording); tech risk L. Impl **Terra medium**; review **Opus medium (claims-sensitive)**.

#### C-36 · R4-THESIS-01 — Thesis appendix compiler
4B · P2 · Docs/Tooling · Difficulty M · **ACCEPT-C** (gate: R3-REL-01)
Evidence: manifest-of-record rule + committed reports exist; assembling a citable appendix (manifest, leaderboard, significance, power, calibration, friction, universe audit, limitations register, checksums, reproduction commands) is currently manual. Creates: deterministic bundle generator + versioned output. Research M / Demo M / CV VH. Claim risk M (bundle inherits claim rules); tech risk M. Impl **Terra/Opus medium**; review Fable low.

#### C-37 · R4-RELEASE-01 — Public research release package & checklist
4B · P3 · Governance · Difficulty M · **ACCEPT-C** (gate: C-36)
Evidence: repo is private-by-default with env-gated lockdown; no release checklist (secrets, data licensing of manual CSVs, claim review, MCC version stamp) exists for making any subset public. Creates: release checklist + sanitized-bundle definition. Research L / Demo M / CV H. Claim risk H (public claims are permanent) — **Fable review mandatory**; tech risk M. Impl **Opus medium**.

#### C-38 · R4-CF-01 — Counterfactual ranking explorer (missingness what-if UI)
4C · P3 · Frontend/Backend · Difficulty H · **ACCEPT-C** (gate: C-15 artifact + C-22 pattern)
Evidence: C-15 produces the rank-delta evidence; an interactive "what if this feature were missing" surface is the natural productization; nothing similar exists. Creates: explorer over *precomputed* counterfactual artifacts (no on-the-fly model math in JS). Research M / Demo VH / CV H. Claim risk **H** (interactive rankings invite advice-reading — stamps + no-live-recompute design); tech risk H. Impl **Opus high**; review **Fable medium (mandatory)**.

#### C-39 · R4-A11Y-01 — Plain-language uncertainty explainers + accessibility pass
4C · P3 · Frontend · Difficulty M · **ACCEPT-C** (gate: Phase 3D landed so explainers cover final surfaces)
Evidence: the terminal-dark visual language was never contrast-audited; statistical panels (null histograms, adjusted p) presume literacy the jury/nontechnical audience may lack; MCC-approved wording exists to key plain-language variants to. Creates: per-panel "what does this mean" explainers using approved wording + WCAG contrast/keyboard audit with fixes. Research L / Demo H / CV M. Claim risk M (simplification must not strengthen claims); tech risk L-M. Impl **Terra medium**; review Opus low.

#### C-40 · Courtroom/debate transcript export & replay
**DEFER** — no consumer exists yet; the dissent ledger covers persistence needs; memo compiler (C-26) covers composed exports. Revisit if a thesis-appendix or demo need for replay materializes.

#### C-41 · Demo evidence playlist / replay mode
**REJECT** — duplicate ownership: `docs/DEMO_RUNBOOK.md` already owns the scripted demo path with fallback branches and rehearsal transcripts. A second demo-sequencing artifact would drift against it.

#### C-42 · Rank persistence / T+2 alpha-decay diagnostics
**DEFER** — only one-to-two usable year-pairs exist (2023 predictions vs 2025 outcomes); at n=80 with SE≈0.11–0.16 the decay estimate would be uninterpretable noise stacked on a null signal. Revisit when additional finalized years exist (same gate as regime diversity).

#### C-43 · Dissent-ledger analytics (dissent vs measurable artifacts)
**DEFER** — the `analyst_verdicts` table shipped 2026-07-13 and has no accumulated verdict data; an analytics surface over an empty ledger would be a fake. Revisit once real verdicts exist (owner decides when).

**Count: 43 generated → 26 accepted (18 with packets, 8 compact), 2 research spikes (packeted), 6 merged, 4 deferred, 3 rejected.** (Spike packets are R3-SPIKE-01 and R3-E2E-01, bringing queue packets to 20.)

---

## 3. PASS 4 — Adversarial review record

Reviewed as skeptical principal engineer, financial-ML reviewer, statistician, data-governance reviewer, product critic, security-minded maintainer, thesis examiner, portfolio interviewer, and smaller-model failure analyst. Actions taken:

1. **Killed pseudo-rigor:** C-12 (binary-target significance) rejected — reusing the continuous-IC permutation family on binary targets is exactly the "reuse of significance results outside their valid scope" failure the mission names.
2. **Killed duplicate ownership:** C-41 rejected (DEMO_RUNBOOK owns demo sequencing); C-25 merged into C-24 (one evidence/health page, not two); C-02/C-04/C-06/C-27/C-30 merged where they were steps, not tasks.
3. **Killed data-that-doesn't-exist tasks:** C-43 deferred (empty verdicts table); C-42 deferred (too few year-pairs — the estimate would be noise); anything sector-based was never admitted (sector column verified unpopulated); anything assuming historical BIST100 membership is gated behind C-18's spike, which may honestly conclude "no free source suffices."
4. **Statistician's corrections:** C-05 must report bootstrap frequencies as resampling variability of a *null-consistent* ranking, never as pick-confidence; C-08's heuristic IC is a **single prespecified test** — it must be reported beside, not inside, the six-model Bonferroni family, with that distinction stated in the artifact itself; C-14's protocol must lead with the ~0.431 one-year detectable-IC bound so the pre-registered test is honestly labeled near-powerless; C-11 must report per-year n after excess-target nulls shrink coverage.
5. **Claim-safety escalations:** C-08, C-22, C-26, C-37, C-38 flagged as high claim-risk with mandatory Fable-level wording review; all UI packets pin verbatim caveat copy in the queue (changing wording requires editing the queue first — the R2 convention).
6. **Security-minded checks:** C-31 explicitly forbids weakening auth or committing any credential; C-37 requires a secrets/licensing sweep before any public artifact; C-33 is audit-only because touching auth-adjacent legacy routers without an owner decision is how demarcation becomes breakage.
7. **Smaller-model failure analysis:** every packet lists files that must NOT be touched, a STOP rule for scope growth, and forbids running `make research` outside tasks that own regeneration; harness-running tasks (C-08, C-09, C-11) are marked never-same-context because a shared context invites cross-contaminating results directories; C-01 gets exact per-file edit lists because truth-sync is where small models improvise worst.
8. **Verification honesty:** tasks whose UI cannot be visually verified until C-31's spike resolves say so in acceptance criteria (build + unit tests + recorded API output are the floor; visual check is conditional).
9. **Misleading-success scenarios** were added to every packet (e.g. C-09: "all placebos pass" proves nothing if the placebo generator accidentally injects signal-bearing structure; C-03: a registry that allowlists too broadly reports coverage it doesn't have).

---

## 4. Output A — Dependency graph

```
PHASE 3A (governance)                    PHASE 3B (research)
R3-GOV-01 ──(truth base for all docs)    R3-STAT-01 ─┐
R3-LINT-01 (independent)                 R3-STAT-02 ─┤  all consume committed dumps only;
R3-MCC-01 (independent)                  R3-INF-01  ─┤  fully parallel, separate contexts
R3-REL-01 ──▶ R4-UI-01, R4-THESIS-01     R3-TGT-01  ─┤  (results_* dirs are disjoint)
R3-LEGACY-01 (independent, audit-only)   R3-NULL-01 ─┤
R3-E2E-01 spike ──▶ (follow-up impl      R3-SERV-01 ─┘
          task unblocks visual checks)   R3-PREREG-01 (time-gated: before 2026 data)
                                         R3-MISS-01 ──▶ R4-CF-01

PHASE 3C/3D (productization)             PHASE 3E / 4
R3-UI-01 (Skeptic panel)                 R3-AGENT-01 (after UI-01, UI-03)
R3-UI-02 (basis lens)                    R4-DIM-01, R4-ROBUST-01 (after NULL-01), R4-PROV-01 (after REL-01)
R3-UI-03 (calibration panel)             R4-EXAM-01 (after LIMITS-01) ──▶ R4-RELEASE-01
R3-LIMITS-01 ──▶ R4-EXAM-01              R4-THESIS-01 (after REL-01) ──▶ R4-RELEASE-01
R3-MEMO-01 (after UI-01 patterns;        R4-UI-01 (after REL-01)
            uses skeptic/courtroom)      R4-A11Y-01 (after 3D)
```

**Gates:**
- **Research-validity gate:** no Phase-3B artifact may be quoted anywhere (UI, docs, memos) until its report ships with raw+corrected values paired and limitations arrays — same rule that governed R2-STAT-01.
- **Claim-safety gate:** every new user-facing surface (UI-01/02/03, MEMO-01, later 4C) requires MCC registration + version bump + `make claims-lint` green before merge; C-08/C-22/C-26/C-37/C-38 additionally require the named independent wording review.
- **Data/provenance gate:** C-17 and C-16 may not begin until R3-REL-01's registry exists (isolation and ownership provable); C-18's spike gates all point-in-time work.
- **UI-integration gate:** R4-CF-01 and R4-UI-01 build only over committed artifacts/endpoints — no client-side statistics, ever.
- **Never in the same context:** R3-SERV-01 / R3-NULL-01 / R3-TGT-01 (each runs the harness into its own new directory); R3-GOV-01 with any code task; R3-MEMO-01 with any other MCC-bumping task (contract merge conflicts); any two tasks that both bump the MCC version.
- **Artifacts that become prerequisites:** `artifact_registry.json` (REL-01 → UI/THESIS tasks), `docs/limitations_register.md` (LIMITS-01 → EXAM-01), `experiments/results_missingness/` (MISS-01 → CF-01), frozen forward ranking + protocol (PREREG-01 → the eventual 2027 evaluation), E2E spike memo (E2E-01 → visual-verification follow-up).

## 5. Output B — Execution waves

| Wave | Name | Tasks (order within wave) | Exit gate |
|---|---|---|---|
| **3A** | Execution truth & governance hardening | R3-GOV-01 → R3-LINT-01 → R3-MCC-01 → R3-REL-01 → R3-LEGACY-01 → R3-E2E-01 (spike) | Docs match a fresh run; registry test green; MCC bound to evidence; E2E decision memo exists |
| **3B** | Research robustness & sensitivity | R3-STAT-02 → R3-INF-01 → R3-STAT-01 → R3-TGT-01 → R3-NULL-01 → R3-SERV-01 → R3-PREREG-01 | Every new results_* dir registered (REL-01), significance rules applied, canonical artifacts byte-identical |
| **3C** | Evidence & provenance productization | R3-UI-02 → R3-SPIKE-01 | Basis lens live with paired raw/adjusted values; universe-history feasibility answered |
| **3D** | Analyst & examiner workflows | R3-UI-01 → R3-UI-03 → R3-LIMITS-01 → R3-MEMO-01 | Skeptic/calibration surfaced; register generated; memo citation-complete + lint-scanned |
| **3E** | Agentic research safeguards | R3-AGENT-01; E2E implementation follow-up (from spike) | Intents cite committed artifacts only; authenticated visual checks runnable |
| **4A** | Research frontier experiments | R4-DIM-01 → R4-ROBUST-01 → R4-PROV-01 | Isolation proven (no canonical drift); findings folded into Autopsy/limitations register |
| **4B** | Thesis & public-release system | R4-EXAM-01 → R4-THESIS-01 → R4-RELEASE-01 | Appendix reproducible from manifest-of-record; release checklist Fable-reviewed |
| **4C** | Advanced product experience | R4-UI-01 → R4-ATLAS/CF (R4-CF-01) → R4-A11Y-01 | No client-side statistics; stamps/caveats in-canvas; a11y audit recorded |

Wave 3A and 3B may interleave across sessions (different files), but a single agent context stays inside one task. The demo-critical chain is 3A(GOV-01) → 3D(UI-01) → 3B(SERV-01) → 3D(MEMO-01).

## 6. Output C — Verification matrix

Columns: RP=root pytest · BP=backend pytest · FB=frontend build · E2E=e2e/visual (conditional on E2E spike) · DV=`make data-validate` · XR=experiment/significance reproduction (rerun→identical or env-qualified) · CL=`make claims-lint` · MS=manifest/checksum comparison (canonical artifacts unchanged) · AR=artifact-registry test (once REL-01 lands) · HR=human/independent statistical or claims review.

| Task | RP | BP | FB | E2E | DV | XR | CL | MS | AR | HR |
|---|---|---|---|---|---|---|---|---|---|---|
| R3-GOV-01 | ✓ | ✓ | — | — | ✓ | — | ✓ | — | — | — |
| R3-LINT-01 | ✓ | — | — | — | — | — | — | — | — | — |
| R3-MCC-01 | ✓ | ✓ | — | — | — | — | ✓ | — | — | — |
| R3-REL-01 | ✓ | — | — | — | — | — | — | ✓ | ✓ | — |
| R3-LEGACY-01 | — | ✓ | — | — | — | — | — | — | — | Terra |
| R3-E2E-01 (spike) | — | — | — | n/a | — | — | — | — | — | Terra |
| R3-STAT-01 | ✓ | — | — | — | — | ✓×2 | — | ✓ | ✓ | Fable |
| R3-STAT-02 | ✓ | — | — | — | — | ✓×2 | — | ✓ | ✓ | Opus |
| R3-INF-01 | ✓ | — | — | — | — | ✓×2 | — | ✓ | ✓ | Opus |
| R3-TGT-01 | ✓ | — | — | — | ✓ | ✓×2 | — | ✓ | ✓ | Opus |
| R3-NULL-01 | ✓ | — | — | — | ✓ | ✓×2 | — | ✓ | ✓ | Fable |
| R3-SERV-01 | ✓ | ✓ | — | — | ✓ | ✓×2 | ✓ | ✓ | ✓ | **Fable (mandatory)** |
| R3-PREREG-01 | ✓ | — | — | — | — | ✓ | — | ✓ | ✓ | **Fable (mandatory)** |
| R3-MISS-01 | ✓ | ✓ | — | — | — | ✓×2 | — | ✓ | ✓ | Opus |
| R3-UI-01 | — | ✓ | ✓ | cond. | — | — | ✓ | — | — | Opus |
| R3-UI-02 | — | ✓ | ✓ | cond. | — | — | ✓ | ✓ | — | Fable |
| R3-UI-03 | — | ✓ | ✓ | cond. | — | — | ✓ | — | — | Opus |
| R3-LIMITS-01 | ✓ | — | — | — | — | ✓×2 | — | — | ✓ | Opus |
| R3-MEMO-01 | ✓ | ✓ | — | cond. | — | — | ✓ | — | — | **Fable (mandatory)** |
| R3-SPIKE-01 | — | — | — | — | — | — | — | — | — | Fable |

"✓×2" = run the generator twice and compare checksums (determinism proof). Every task additionally ends with `git diff --check` and the queue's universal rollback rule. API response claim scan = CL where the service file is registered in the MCC `scan.backend_response_files` (UI-02, MEMO-01 packets include that registration).

## 7. Output D — Model allocation

The queue's existing key (Sol / Terra / Opus / Fable) maps to currently available labels as follows; pick by task shape, not rank:

- **Sol-class (GPT-5.6 Sol, GPT-5.6 Luna, other small/fast models):** docs edits with exact per-file instructions, verification runs, ledger updates, link lint. Best when the packet enumerates every edit (R3-GOV-01, R3-LINT-01). Never for statistics, migrations, or claim wording.
- **Terra-class (GPT-5.6 Terra, Claude Sonnet 5, GPT-5.5):** additive backend/frontend features with an existing pattern to copy (R3-UI-01, R3-UI-03, R3-STAT-02, R3-MCC-01, R3-LIMITS-01, R3-AGENT-01, R4-UI-01, R4-EXAM-01 draft). Sonnet 5 preferred for JSX-heavy mechanical work; Terra for API/parse-heavy work. GPT-5.5 acceptable for repetitive implementation under a tight packet.
- **Opus-class (Claude Opus 4.8):** new experiment modules, statistics implementation from a fixed design, generator-adjacent code, anything touching guard-adjacent files (R3-REL-01, R3-STAT-01, R3-INF-01 review, R3-TGT-01, R3-NULL-01, R3-MISS-01, R3-UI-02, R3-MEMO-01, R3-LEGACY-01, R3-E2E-01, R3-SPIKE-01, R4-ROBUST-01, R4-PROV-01, R4-CF-01).
- **Fable-class (Fable 5):** tasks where statistical judgment, claim surfaces, and pipeline sensitivity intersect, and independent adversarial review of high-risk wording (R3-SERV-01 implementation or mandatory review; mandatory reviews for R3-PREREG-01, R3-MEMO-01, R3-NULL-01 design, R3-UI-02 copy, R4-RELEASE-01, R4-CF-01; periodic re-planning passes like this one).
- **Independent review rule:** implementer and reviewer must be different model families for the five mandatory-review tasks (matrix column HR). Review = read the diff + artifacts against the packet's claim-safety section and the do-not-claim register; produce written findings before the owner commits.

## 8. Output E — Prioritized selections

- **Safest first 5 (executable immediately after `/clear`, in order):** R3-GOV-01 → R3-LINT-01 → R3-MCC-01 → R3-REL-01 → R3-STAT-02.
- **Highest research value:** R3-SERV-01, R3-NULL-01, R3-STAT-01, R3-PREREG-01, R3-TGT-01.
- **Highest product/demo value:** R3-UI-01, R3-MEMO-01, R3-UI-02, R4-CF-01, R4-UI-01.
- **Highest CV/interview value:** R3-PREREG-01, R3-SERV-01, R3-MEMO-01, R4-EXAM-01, R3-REL-01.
- **Highest risk (handle with mandatory review):** R3-SERV-01, R3-MEMO-01, R4-CF-01, R4-RELEASE-01, R3-UI-02.
- **Best for Sol-class:** R3-GOV-01, R3-LINT-01, R4-EXAM-01 first draft (post-register), TASK_STATE ledger rows after each task.
- **Best for Terra-class:** R3-UI-01, R3-UI-03, R3-STAT-02, R3-MCC-01, R3-LIMITS-01, R3-AGENT-01.
- **Best for Opus-class:** R3-REL-01, R3-STAT-01, R3-NULL-01, R3-MISS-01, R3-UI-02, R3-E2E-01, R3-LEGACY-01, R3-SPIKE-01.
- **Requiring independent (cross-family) review:** R3-SERV-01, R3-PREREG-01, R3-MEMO-01, R3-NULL-01, R3-UI-02, R4-RELEASE-01, R4-CF-01.
- **Execute while Phase-2 context is freshest:** R3-GOV-01 (ledger mapping from commit messages), R3-UI-01 (the explicitly deferred Skeptic panel), R3-MCC-01 (contract internals just touched), R3-PREREG-01 (time-gated before 2026 outcome data can exist).

---

## 9. Self-verification (this planning pass)

- Only Markdown files changed: this file, `FINANCEIQ_AGENT_TASK_QUEUE.md`, `FINANCEIQ_MOONSHOT_ROADMAP.md`, `TASK.md`, `TASK_STATE.md`.
- Every existing path cited above was verified by listing/grep this session; proposed paths are labeled "(proposed)".
- Phase 1/2 tasks were not reopened; both suites re-run green (root 168/168, backend 85/85) before treating them as complete.
- 43 candidates generated (≥20 required); adversarial review rejected 3, deferred 4, merged 6, split 0 (none needed splitting after merges — C-31/C-18 were instead narrowed to spikes), spiked 2.
- 20 execution packets written (≥15 required); the first five are self-contained post-`/clear`.
- Every generated artifact proposed here names an owner generator and regeneration command inside its packet; R3-REL-01 makes that machine-checked.
- No claim herein weakens the no-reliable-edge conclusion; no task depends on sectors, historical membership, or unavailable data without a spike gate.
