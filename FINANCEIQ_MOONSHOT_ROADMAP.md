# FINANCEIQ_MOONSHOT_ROADMAP.md

Controlled moonshot roadmap for FinanceIQ. Written 2026-07-12 from direct repo inspection (files cited inline). This is a **candidate** roadmap — nothing here is committed work, and nothing here overrides the project's core contract: no fabricated data, no leakage, no predictive-edge claims, IC ≈ 0 stays the honest headline unless new committed evidence changes it.

Relationship to other documents:

- `FINANCEIQ_MODEL_VALIDITY_AUDIT.md` — the evidence base. Every weakness this roadmap addresses is documented there with claim-category labels.
- `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` — the claim boundary. Nothing in this roadmap may produce a claim that guide forbids.
- `FINANCEIQ_AGENT_TASK_QUEUE.md` — execution. Phase 1 (OPS/DATA/UI/VER tasks) preserves current truth; **Phase 2** (appended there) implements this roadmap.
- `PRD.md` — product definition. This roadmap extends "Intended Direction"; it does not change Non-Goals.

---

## 1. Deep project assessment

### 1.1 What FinanceIQ currently is

A completed capstone that asked a falsifiable question — *can free, validated, leakage-safe yearly fundamentals predict next-year BIST returns?* — and answered it honestly: **no reliable signal** (walk-forward Spearman ≈ 0.042 overall, per-split range −0.17 to +0.22 at n≈40 per split; `METHODOLOGY.md`, `experiments/leaderboard.csv`). Around that answer it built:

- A no-fabrication pipeline that **automatically detected** that vendor fundamentals were a frozen 2025 snapshot (`data/trusted_clean/frozen_column_evidence.md`) and rebuilt trustworthy data from corrected files, Yahoo prices, and manual share counts.
- A walk-forward experiment harness with baselines (`experiments/run_experiments.py`), committed results, and feature-stability artifacts (`experiments/results/feature_stability_*.csv`).
- A serving layer that is deliberately deterministic and explainable (`backend/app/services/forecasting_csv_service.py`), plus a hybrid research agent that **penalizes its own score for its own weak backtest** (`weak_backtest_spearman_near_zero (-0.20)`, `backend/app/services/research_agent.py:591`).
- A 21-page "Research Terminal" frontend that displays IC ≈ 0 as the finding, not a footnote.
- 148 tests across two suites, a reproducible Makefile pipeline, and a documentation layer (audit, claims guide, task queue, small-model rules) that most production teams don't have.

### 1.2 What it is not

Not a return predictor, not an advice engine, not proof that markets are unpredictable, not production-verified (deployment liveness unconfirmed), and not a statistically powered study — 321 target rows across three test years in one extraordinary macro regime cannot support general conclusions in either direction (`FINANCEIQ_MODEL_VALIDITY_AUDIT.md` §7–§8).

### 1.3 What is already impressive

1. **The frozen-snapshot forensics.** Validation gates catching bad vendor data with per-ticker evidence is a genuinely rare, demo-worthy artifact.
2. **The self-skeptical scoring.** A scoring system that applies an explicit penalty for its own weak backtest is honesty implemented in code, not prose.
3. **The claim discipline.** The audit/claims-guide/small-model-rules triad makes overclaiming structurally difficult even for future agents.
4. **Leakage control as architecture.** Rejected same-year return columns, walk-forward splits, inference-row flagging, and `feature_registry.py` guards form a coherent system, not scattered checks.

### 1.4 What is fragile, incomplete, or potentially misleading

- **The negative result is asserted, not instrumented.** "IC ≈ 0" currently has no confidence interval, no permutation baseline, no power analysis. A skeptical examiner can ask "is 0.042 distinguishable from noise — and could this dataset have detected a real signal at all?" and the repo has no committed answer. This is the single biggest gap between "honest" and "rigorous."
- **Nominal TRY targets during hyperinflation** (2022 benchmark return recorded near +186% nominal) make MAE/RMSE incomparable across years and directional accuracy nearly meaningless (audit §12). The finding survives, but its interpretability suffers.
- **The stale DEGENERATE caveat** in `experiments/reports/summary.md` overstates data degeneracy post-correction (audit §12; task DATA-04). Committed evidence prose lags committed evidence tables.
- **Confidence is a component, not an evaluated quantity.** The 0.20 confidence weight in the hybrid score has never been checked against realized outcomes — the UI shows confidence numbers whose calibration is unknown.
- **Universe selection is unaudited.** `METHODOLOGY.md` itself states there is no survivorship/look-ahead audit of how the 40 public companies were chosen.
- **Experiments are re-runnable but not registered.** No run manifests, no dataset hashing, no environment capture — reproducibility currently depends on git discipline rather than artifacts.
- **Serving heuristic vs experiment models** is a subtle distinction (audit §14) that any demo can accidentally blur.

### 1.5 Claims that must stay carefully worded

Fully specified in `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §5 and audit §16. Roadmap-specific additions in §6 below.

### 1.6 The next maturity level

The theme of this roadmap in one sentence: **turn the negative result from a sentence into an instrument.** FinanceIQ's current maturity is "honest finding, well-guarded." The next level is "measured finding, stress-tested, self-defending" — where the IC ≈ 0 claim carries confidence intervals and power analysis, the UI is contractually bound to the evaluation's strength, an adversarial agent attacks every ranking before a human sees it, and every experiment is a citable, reproducible artifact. None of that requires new predictive skill. All of it compounds the project's real asset: credibility.

---

## 2. Roadmap design principles

1. **Nothing may manufacture signal.** Every idea below either measures uncertainty better, explains failure better, guards claims harder, or makes the system more reproducible. If an idea's success would depend on the model "working," it does not belong here.
2. **Free data only, manual-CSV pattern respected.** New series (CPI, USDTRY, macro context) enter exactly like `shares_outstanding_events.csv`: manually curated, sourced, shape-validated, null-if-missing. No scrapers, no paid APIs.
3. **Deterministic core, LLM optional.** Every agentic feature must have a template/deterministic fallback that works with `RESEARCH_LLM_PROVIDER=none`, matching the existing research-agent pattern.
4. **The headline result is immutable evidence.** Alternative evaluations (real returns, cost simulations) write to *separate, labeled* output directories and never overwrite `experiments/leaderboard.csv` silently.
5. **Every feature ships with its own caveat copy.** Wording is specified at design time (see per-idea "honest wording"), not retrofitted.

---

## 3. The controlled moonshot roadmap

Twelve major ideas. Each addresses a documented weakness from §1.4 or the audit. Execution detail lives in `FINANCEIQ_AGENT_TASK_QUEUE.md` Phase 2 (task IDs cross-referenced).

### 3.1 Null-Result Instrumentation Suite (NRIS) — *research validity, evaluation* — tasks R2-STAT-01, R2-STAT-02

- **What:** A statistical harness around the existing walk-forward results: (a) **permutation tests** — shuffle T+1 targets within each test year, re-score each model ~1,000×, and report where the observed IC falls in the null distribution; (b) **block-bootstrap confidence intervals** on per-split and pooled Spearman IC (resampling tickers, respecting the panel structure); (c) a **power analysis** answering "what is the minimum |IC| this dataset could reliably detect?" (analytically, SE(ρ) ≈ 1/√(n−3) ≈ 0.16 at n=40 → detectable |IC| is roughly ≥ 0.3–0.35 per split; the harness computes it properly, pooled and per split).
- **Why it matters:** It converts "IC ≈ 0, trust us" into "IC = 0.042, 95% CI [−x, +x], permutation p = y, and this dataset only had power to detect |IC| ≳ z" — a claim that holds up under hostile examination, and the strongest available framing of a negative result: *we measured the limits of our own measurement.*
- **Weakness addressed:** §1.4 first bullet — the negative result is asserted, not instrumented.
- **MVP path:** Note: the committed `experiments/results/test_*.json` files hold **aggregate metrics only** (no per-ticker predictions — verified 2026-07-12). So the MVP is two steps: an additive per-ticker prediction dump in the harness (`experiments/results/predictions_<split>.csv`; models are already seeded, so the leaderboard must reproduce identically), then a new module `experiments/significance.py` consuming those dumps; new additive Makefile target; outputs to `experiments/results/significance_report.{json,md}`. No change to metrics computation. Details in task R2-STAT-01.
- **Higher-end:** Reality-check / SPA-style multiple-comparison correction across the 6 ML models (the leaderboard implicitly runs a model search; correcting for it makes "nothing beats baselines" airtight); stationary block bootstrap over years once more years exist.
- **Risks / how it could mislead:** A permutation p-value that happens to be small for one model in one split could be trumpeted as signal. Mitigation: the report template always leads with the pooled, multiplicity-corrected result and labels per-split values "exploratory."
- **Honest wording:** "We tested our own negative result: observed rank IC is statistically indistinguishable from a target-shuffled null, and the dataset's power analysis shows only effects larger than |IC| ≈ 0.3 per split were detectable at all. The finding is 'no detectable signal at this scale,' not 'no signal exists.'"
- **Demo value:** high (a null-distribution histogram with the observed IC inside it is the single most persuasive slide the project can produce). **Research value:** very high — this is the difference between a student project and a defensible study. **Engineering value:** medium (clean, isolated module).

### 3.2 Real-Terms & Currency Lens — *evaluation, regime awareness* — task R2-REAL-01

- **What:** Add two manually curated, sourced series via the established manual-CSV pattern: yearly Turkish CPI (TÜİK, public) and year-end USDTRY (Yahoo, same source class as existing price fetches). Derive three parallel target variants for every company-year: nominal TRY return (current headline), CPI-deflated real return, and USD-terms return. Re-run the walk-forward harness on each variant into a separate output directory (`experiments/results_real_terms/`), never overwriting the headline.
- **Why it matters:** The audit (§6, §12) identifies nominal-TRY-during-hyperinflation as the biggest interpretability problem: a +35% "median return" year is not a bull market, it's inflation. Whether IC ≈ 0 survives in real/USD terms is a genuinely open, answerable research question — and either answer strengthens the project.
- **Weakness addressed:** §1.4 second bullet.
- **MVP path:** `data/trusted_raw/macro/cpi_yearly_tr.csv` (+ documented source and retrieval date), USDTRY year-end via the existing `fetch_yahoo_chart_prices.py` pattern; new pipeline stage computing derived target columns with explicit provenance flags; harness invocation parameterized by target column (`build_panel_for_target` already exists in `experiments/run_experiments.py:115`, which makes this cheap).
- **Higher-end:** Sector-relative real returns; a UI toggle on `/benchmark` and `/experiments` switching all return displays between nominal/real/USD with the active basis always labeled on-chart.
- **Risks / how it could mislead:** If real-terms IC happens to look slightly better in one split, it must not be promoted to a headline ("we found signal in real terms!") without the NRIS significance treatment. Deflator vintage errors could silently distort targets — CPI CSV needs the same shape-validation rigor as the shares file.
- **Honest wording:** "Returns are shown in nominal TRY, CPI-deflated, and USD terms because 2021–2024 Turkish inflation makes nominal magnitudes misleading. The predictive conclusion (no reliable signal) is evaluated separately in each basis."
- **Demo value:** high (the nominal-vs-real 2022 chart is instantly understood). **Research value:** high. **Engineering value:** medium.

### 3.3 Model Confidence Contract (MCC) — *uncertainty, product UX, auditability* — task R2-CONTRACT-01

- **What:** A machine-readable contract (`model_confidence_contract.json`, generated by the pipeline, versioned) binding UI language strength to evaluation strength. Example rules: *if the pooled IC confidence interval contains 0, no user-facing surface may use "predict," "expect," "likely to outperform"*; *if a ticker's score used < N populated features, its rank must render as a quartile, not a decimal*; *inference-only rows must carry the `unevaluated_forward_forecast` label*. Enforced two ways: a backend test that validates API response copy against the contract, and a CI-style lint script that greps `frontend/src/pages/*.jsx` for forbidden claim vocabulary outside approved caveat contexts.
- **Why it matters:** Today the honesty lives in culture and docs (grep-based disclaimer audits, task UI-01). The MCC makes it *infrastructure*: a future contributor cannot ship confident copy over a weak evaluation without a test failing. No student dashboard has this; very few production ML systems do.
- **Weakness addressed:** Claim-boundary enforcement is manual (audit §18); confidence displayed without calibration (§1.4 fourth bullet).
- **MVP path:** Static hand-written v1 contract JSON reflecting current committed results + `scripts/lint_claims.py` (stdlib only) + one backend test asserting the forecasting API's `DISCLAIMER` and score-precision rules match the contract; wire into no existing Makefile target (new additive target only).
- **Higher-end:** Contract auto-generated from NRIS output (CI width → allowed vocabulary tier); frontend reads the contract at build time and selects copy variants; contract version displayed in the UI footer ("claims governed by MCC v3").
- **Risks / how it could mislead:** A contract that's too coarse could block legitimate explanatory language; a passing lint could create false comfort that *all* copy is honest (it only checks vocabulary, not meaning). Document it as a tripwire, not a proof.
- **Honest wording:** "UI language is contractually bound to evaluation strength: because the current walk-forward IC is indistinguishable from zero, the interface is prohibited — by a tested, machine-readable contract — from using predictive vocabulary."
- **Demo value:** very high (show the test failing when you try to add the word "predicts"). **Research value:** medium-high (publishable as an honesty-engineering pattern). **Engineering value:** very high.

### 3.4 Skeptic Agent — *agentic research, model diagnostics* — task R2-SKEPTIC-01

- **What:** A deterministic adversarial persona in the research-agent layer. For any ticker/ranking, it runs a fixed battery of challenges using only existing validated artifacts: (1) leakage probe — flag features whose same-year correlation with returns is suspiciously high; (2) frozen/staleness check against `frozen_column_evidence.json`; (3) missingness attack — what fraction of this score rests on how few populated features; (4) sector-concentration check — is the rank driven by a sector with n < 10 (audit §13); (5) instability check — does the ticker's rank flip across per-split model variants; (6) backtest reminder — always cites the IC evidence against trusting the ranking at all. Output: a structured "challenge report" (`GET /research/skeptic/{ticker}`), rendered as a prosecution-style panel in the UI. LLM optionally narrates the findings; deterministic templates otherwise.
- **Why it matters:** It operationalizes the project's stance. Instead of the *user* having to remember the caveats, the system attacks its own output before presenting it. It also has real research utility: the missingness and instability probes surface data problems the aggregate reports hide.
- **Weakness addressed:** Sparse-column silent-ranking risk (audit §9), sector small-n risk (§13), serving-heuristic overtrust (§14).
- **MVP path:** New service `backend/app/services/skeptic_service.py` composing existing data-quality reads (no new data); router addition under the `/research` prefix; deterministic only; ~6 checks, each returning `{check, verdict, evidence, severity}`; backend tests pinning each check on fixture data.
- **Higher-end:** Skeptic verdicts feed a per-ticker "contestability score" shown beside every ranking; Skeptic participates in the Research Courtroom (§3.7); challenge history logged for the analyst ledger (§3.11).
- **Risks / how it could mislead:** A ranking that "survives" the Skeptic could be read as validated. Mitigation: the report's fixed footer states "surviving these checks means *not obviously broken*, not *predictive* — backtest IC remains ≈ 0."
- **Honest wording:** exactly that footer.
- **Demo value:** very high. **Research value:** high. **Engineering value:** high.

### 3.5 Negative Alpha Autopsy — *diagnostics, dashboard, report generation* — task R2-AUTOPSY-01

- **What:** A dedicated frontend surface (extend `/experiments` or add a route) that explains *why* the models failed, built entirely from artifacts already committed: feature-weight instability across years (`experiments/results/feature_stability_by_split.csv`), tree-model overfit evidence (consistently negative IC in `leaderboard.csv`), coverage impact (`coverage_impact.csv`), sample-size power (from NRIS), and regime homogeneity (three test years, one macro regime). Structured as a five-exhibit autopsy: *Instability, Overfit, Sparsity, Power, Regime* — each with the concrete chart and one-paragraph finding.
- **Why it matters:** Currently the negative result is *shown* (seismograph, IC trace) but not *explained*. The autopsy converts "our model failed" into "here is the anatomy of why prediction failed at this data scale," which is the project's actual intellectual contribution and its best interview material.
- **Weakness addressed:** Feature-stability and coverage artifacts exist but are surfaced nowhere (`OPERATING_LAYER_VALIDATION.md` §6 notes `experiments/results/` is under-exposed).
- **MVP path:** Backend endpoint serving the three existing results CSVs as JSON (read-only, no computation); one new page following the Research Terminal visual language; demo-data fallback per existing page conventions.
- **Higher-end:** Auto-generated PDF/Markdown "autopsy report" for thesis appendices; per-exhibit "what would have to change" notes (e.g., "instability exhibit would need ≥ N years of stable sign to reverse").
- **Risks / how it could mislead:** Over-narrating (claiming to *know* why, when the evidence is circumstantial). Each exhibit must distinguish "consistent with" from "proves."
- **Honest wording:** "This page documents evidence consistent with why no reliable signal was found: unstable feature relationships, overfitting under small n, sparse coverage, low statistical power, and a single macro regime. It explains the negative result; it does not promise a positive one under other conditions."
- **Demo value:** very high — likely the single best new demo asset. **Research value:** very high. **Engineering value:** medium.

### 3.6 Regime Lens — *robustness, regime detection* — task R2-REGIME-01

- **What:** A macro-context layer: a manually curated yearly macro CSV (CPI, policy rate, USDTRY, BIST100 return — all free, sourced) rendered as a regime strip across every time-axis chart, plus a diagnostics view conditioning model behavior on regime variables. Its first and most prominent screen states the honest core finding: **all three test years sit inside one extraordinary regime, so regime robustness is untestable with this data** — and then shows exactly what would become testable as years accumulate.
- **Why it matters:** Audit §8 calls regime homogeneity a hard limitation. The Regime Lens turns the limitation itself into a visible, taught concept rather than a buried caveat — and creates the slot where future years of data plug in.
- **Weakness addressed:** §1.4 (regime homogeneity invisible in the UI); complements Real-Terms Lens (§3.2, shared macro CSV).
- **MVP path:** `data/trusted_raw/macro/macro_context_yearly.csv` (validated, sourced); backend passthrough endpoint; regime strip component added to `/benchmark` and `/experiments` charts.
- **Higher-end:** Per-regime IC decomposition (activates only when ≥ 2 regimes exist — the code ships with an honest "insufficient regime diversity" state as its default); crisis-year annotations.
- **Risks / how it could mislead:** With one regime, any "per-regime" number is a re-labeled aggregate. The default-state design (explicitly saying "untestable yet") is the mitigation and the point.
- **Honest wording:** "2020–2025 spans a single extraordinary Turkish macro regime (high inflation, deep TRY depreciation). Model behavior across regimes is therefore untested — this lens shows the regime context and will only compute regime-conditional diagnostics when regime diversity exists."
- **Demo value:** medium-high. **Research value:** high (esp. for thesis framing). **Engineering value:** medium.

### 3.7 Research Courtroom — *agentic workflows, human-in-the-loop, demo* — task R2-COURT-01

- **What:** For a chosen ticker, four fixed personas argue from evidence: **Bull** (strongest grounded positives: percentile ranks, margins, momentum), **Bear** (weakest grounded negatives), **Skeptic** (§3.4's challenge report verbatim), **Risk** (missingness, small-n, inflation basis, IC evidence). Each persona may cite only fields present in `data/trusted_clean/company_contexts/` and the data-quality reports; every sentence carries a citation chip resolving to the underlying value. Deterministic template mode works with `RESEARCH_LLM_PROVIDER=none`; the LLM mode only rephrases grounded bullet evidence into prose (existing explanation-only constraint). There is deliberately **no verdict** — the closing panel states the tool ranks arguments by evidence coverage, not by which side is "right," and repeats the not-investment-advice line.
- **Why it matters:** It is the most memorable possible demonstration of the project's philosophy: even the flashiest AI feature is structurally incapable of giving advice, because it has no verdict slot and no ungrounded sentence. It also showcases the RAG contexts (`make build-company-contexts`) that currently have little UI presence.
- **Weakness addressed:** Research-agent layer is a single-voice Q&A today; the grounded-evidence machinery is underused as a product surface.
- **MVP path:** Deterministic persona builders in a new service (reusing `research/` subpackage evidence loaders); one new page; `POST /research/courtroom` under the existing prefix; per-persona caveat footers.
- **Higher-end:** User can cross-examine (follow-up questions routed per persona through `POST /research/ask` machinery); transcript export for the analyst ledger (§3.11).
- **Risks / how it could mislead:** Rhetorical framing can make weak evidence feel strong; a "Bull wins" reading is advice by another name. Mitigations: no verdict by design, equal evidence-count budgets per persona, Risk persona always speaks last.
- **Honest wording:** "A structured debate over historical, validated evidence. No persona forecasts returns; no verdict is issued; nothing here is investment advice."
- **Demo value:** very high (the signature 'wow'). **Research value:** medium. **Engineering value:** high.

### 3.8 Experiment Registry & Thesis Mode — *experiment tracking, reproducibility, thesis positioning* — task R2-REPRO-01

- **What:** Every experiment run writes a manifest: git SHA, dirty-tree flag, SHA-256 of the modeling dataset, feature-column list, model configs, seeds, package versions, wall-clock, and output hashes — to `experiments/results/runs/<timestamp>_<shortsha>/manifest.json`. A verification command recomputes the dataset hash and re-runs the harness to confirm metric reproduction ("Thesis Mode": each registered run becomes a citable artifact with a one-command reproduction check). The headline leaderboard gains a provenance line: *produced by run X on dataset hash Y*.
- **Why it matters:** §1.4 sixth bullet — reproducibility currently rides on git discipline. For a thesis or any external scrutiny, "here is the manifest, here is the one command that reproduces Table 3" is the difference between claimed and demonstrated reproducibility. It also protects against the exact failure mode already observed in this repo (report prose drifting from the run that produced it — the DEGENERATE caveat incident).
- **Weakness addressed:** audit §12 (stale caveat / provenance drift), reproducibility gap.
- **MVP path:** Manifest writer appended to `experiments/run_experiments.py:326` `run()` (additive, after outputs are written — no change to metrics code); `scripts/verify_run.py` for the reproduction check; additive Makefile target.
- **Higher-end:** Manifest browser in the UI (`/experiments` sidebar: "this chart = run 2026-07-…"); dataset-hash check wired into `make data-validate`; thesis appendix generator emitting a Markdown bundle (manifest + tables + NRIS report) per run.
- **Risks / how it could mislead:** A manifest can lend false authority to a flawed run — provenance ≠ validity. Keep the manifest's own wording neutral ("records inputs; does not certify methodology").
- **Honest wording:** "Every experiment is registered with its exact inputs and reproducible by one command. Registration documents provenance; the methodology's validity is argued separately in METHODOLOGY.md."
- **Demo value:** medium. **Research value:** very high. **Engineering value:** very high.

### 3.9 Data Lineage Passport — *feature store, data lineage* — task R2-LINEAGE-01

- **What:** A per-column (MVP) and eventually per-cell provenance system: every feature in the modeling dataset carries a machine-readable passport — source class (vendor XLSX / corrected yearly CSV / Yahoo fetch / manual shares / derived), transformation chain, validation gates passed, acceptance status, and known caveats. Generated by extending the existing `data_dictionary.md` generator into structured JSON; surfaced in the UI as a "passport" popover wherever a feature value is displayed (Score Explorer, Forecasting explain view).
- **Why it matters:** The pipeline already *has* implicit lineage (the accepted/rejected machinery, frozen evidence, ingestion reports) — but it's scattered across seven report files. Unifying it makes "every value is real, sourced, and auditable" (`FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §10) a clickable fact instead of a sentence, and gives DATA-01 (dictionary drift) a durable structural fix.
- **Weakness addressed:** audit §4 gap (dictionary unverified against columns); demo claim §10 currently unverifiable interactively.
- **MVP path:** Extend `_data_dictionary()` in `scripts/data_collection/build_all.py:30` (which writes `data_dictionary.md`) to also emit `data/trusted_clean/feature_passports.json`; backend passthrough endpoint; popover component on one page first (`/research` Score Explorer).
- **Higher-end:** Per-cell passports (row-level source flags already partially exist, e.g. `is_inference_row`); lineage diff between pipeline runs; "show me every value that touched the 2024 manual override" query.
- **Risks / how it could mislead:** Passport says where a value came from, not that the source was correct. Passport copy must say "provenance, not accuracy certification."
- **Honest wording:** on-popover footer: "Provenance record — documents source and validation path, not a guarantee of source accuracy."
- **Demo value:** high. **Research value:** medium-high. **Engineering value:** high.

### 3.10 Friction-Aware Portfolio Illustration — *portfolio construction, backtesting discipline* — task R2-FRICTION-01

- **What:** A simulator that takes the model's historical top-k baskets per test year and applies explicit, user-visible friction assumptions — turnover between annual rebalances, commission + spread costs (parameterized, defaults labeled as assumptions), and an "overconfidence penalty" view showing rank-decimal precision vs realized rank error. Its purpose is deliberately inverted from a normal backtester: it exists to show that even the occasionally-lucky per-split baskets **do not survive friction**, and to teach why gross hypothetical returns overstate everything. Every screen is stamped "hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0."
- **Why it matters:** Backtesting discipline is the one classic quant-hygiene topic the repo currently has no artifact for (audit §22 mentions "no transaction costs" as a gap). Building the costs machinery *around a null signal* is both honest and pedagogically sharp.
- **Weakness addressed:** no cost/turnover treatment anywhere; risk that per-split `top_bucket_avg_return` values in `leaderboard.csv` get quoted as achievements (audit §16).
- **MVP path:** Pure-Python module in `experiments/` consuming the per-ticker `predictions_<split>.csv` dumps added by NRIS (§3.1 — the committed `test_*.json` hold aggregate metrics only); outputs a friction report per model/split; small UI panel on the autopsy page (§3.5) rather than a standalone page.
- **Higher-end:** Interactive sliders (cost bps, k, rebalance) with the honest-result stamp persistent; net-vs-gross tornado chart.
- **Risks / how it could mislead:** Highest-risk idea in this roadmap: any net-return chart can be screenshotted out of context as a performance claim. Mitigations: no cumulative-wealth curves ever; per-year bars only; the caveat stamp rendered *inside* the chart canvas so screenshots carry it; MCC (§3.3) vocabulary rules apply.
- **Honest wording:** the in-canvas stamp above, verbatim.
- **Demo value:** medium-high. **Research value:** high. **Engineering value:** medium.

### 3.11 Analyst-in-the-Loop Ledger — *human-in-the-loop workflows* — task R2-LOOP-01

- **What:** Upgrade the existing `LabelingLabPage.jsx` / `ValidationLabPage.jsx` surfaces into a structured analyst-verdict system: for any ticker-year, an authenticated user records agree/disagree/abstain with a scored ranking plus a typed reason (evidence-quality, missing-context, sector-knowledge, other). Verdicts persist (new table via Alembic append), never touch the modeling dataset, and generate an aggregate "human dissent" view: where do humans most distrust the machine, and did dissent correlate with anything measurable.
- **Why it matters:** Converts two under-explained existing pages into a genuine research workflow, and creates the only ethically clean use of human judgment here: measuring disagreement, not overriding scores.
- **Weakness addressed:** LabelingLab/ValidationLab exist with no documented research purpose; UI-01 flagged them as disclaimer-uncovered pages.
- **MVP path:** Read both pages + their routers (`labeling.py`, `validation.py`) to map what exists; add verdict schema + endpoint + minimal UI; Alembic migration (append-only).
- **Higher-end:** Dissent-weighted skeptic severity; export of verdict history for the thesis ("n analysts reviewed m rankings; dissent concentrated in sparse-coverage tickers").
- **Risks / how it could mislead:** Aggregated human verdicts could be misread as a crowd-sourced signal. Ledger copy: "records disagreement for research; is not a score input."
- **Honest wording:** as above; verdicts never enter any score computation (enforced by test).
- **Demo value:** medium. **Research value:** high. **Engineering value:** medium-high.

### 3.12 Confidence Calibration Bench — *uncertainty & calibration* — task R2-CAL-01

- **What:** Evaluate the confidence component (0.20 weight of the hybrid score) as a predictive quantity about *rank error*: over the 321 realized target rows, does higher stated confidence correspond to smaller |predicted rank − realized rank|? Produce a reliability diagram and a calibration verdict. Second stage: conformal-style rank intervals ("this stock's rank: 12, 80% interval [3, 31]") — which at n=40 will be honestly, visibly wide, and that width *is* the product feature.
- **Why it matters:** §1.4 fourth bullet: the UI currently displays confidence numbers of unknown calibration — the one place where the project's own honesty standard isn't yet met. Wide conformal intervals are also the most truthful possible ranking display.
- **Weakness addressed:** unevaluated confidence component; audit §19's "avoid pretending precision."
- **MVP path:** Offline analysis script in `experiments/` that **replays** the scoring services over historical rows (per-row confidence is absent from the committed experiment outputs — verified: `experiments/results/research_agent_model_outputs.csv` carries `ml_score`/`ml_rank` only; check serving-side persistence before assuming none exists) and joins with realized returns; calibration report committed with the replay date/version; if confidence proves uncalibrated, the *finding* is published and the UI copy adjusted (per MCC) — not the number quietly fixed.
- **Higher-end:** Rank intervals rendered in the Forecasting page ranking view; confidence component re-derivation proposal (owner decision, strong-model task).
- **Risks / how it could mislead:** Post-hoc calibration tuning on the same 321 rows would be overfitting the meta-level. Any recalibration must be walk-forward too.
- **Honest wording:** "Confidence values were themselves audited: [calibrated/not calibrated as of run X]. Rank intervals are wide because the data supports nothing narrower."
- **Demo value:** medium-high. **Research value:** very high. **Engineering value:** medium.

### 3.13 Compact ideas (smaller, still specific)

- **Universe Survivorship Audit** (R2-UNIV-01, Stage 1): document how the 40 public tickers were selected, when, and against what listing status; check for delistings/suspensions in-window; add the finding to METHODOLOGY.md "Limitations" with evidence. Directly answers METHODOLOGY's own open item.
- **Glass-Box Demo Runbook** (R2-DEMO-01, Stage 4): builds on Phase-1 BE-01 — a scripted demo path that *starts* from `/research/runtime-status` and the data-quality specimen archive (proving live data), walks the frozen-evidence 'wow', the autopsy, then the courtroom; committed as a runbook doc with fallback branches if the LLM/API is down.
- **Sector Honesty Chips** (fold into DATA-06): per-sector n displayed on every sector-filtered view ("Energy, n=4 — anecdotal").

---

## 4. Prioritization framework

| Stage | Theme | Contents | Gate to next stage |
|---|---|---|---|
| **Stage 0 — Preserve honesty, fix documentation truth** | Truth debt | Phase-1 queue: OPS-01..05, DATA-04/05 (stale DEGENERATE caveat), UI-01/02, MOD-01/02 | Root suite 97/97; caveat text matches measured variance; disclaimer coverage complete |
| **Stage 1 — Reproducible and defensible** | Provenance | R2-REPRO-01 (registry), R2-UNIV-01 (survivorship audit), R2-LINEAGE-01 (passports), Phase-1 VER-01/02, BE-01/02 | Any committed table reproducible by one command from a manifest |
| **Stage 2 — Research-grade evaluation** | Instrumented null | R2-STAT-01/02 (NRIS), R2-REAL-01 (real terms), R2-CONTRACT-01 (MCC v1) | IC claim carries CI + permutation p + power statement; claims lint green |
| **Stage 3 — Advanced diagnostics & workflows** | Self-defending system | R2-SKEPTIC-01, R2-AUTOPSY-01, R2-CAL-01, R2-REGIME-01, R2-LOOP-01 | Every ranking ships with a challenge report; autopsy page live on real artifacts |
| **Stage 4 — Honest wow** | Demo compounding | R2-COURT-01, R2-FRICTION-01, R2-DEMO-01 | Courtroom runs verdict-free with LLM off; friction charts carry in-canvas stamps |

Ordering rationale: Stages 0–1 cost little and de-risk everything later (a courtroom built on a stale caveat is a liability, not a feature). Stage 2 is the highest research-value-per-hour block in the whole roadmap. Stages 3–4 are where demo value concentrates, and they consume Stage 2 outputs (autopsy uses NRIS power numbers; courtroom embeds the Skeptic).

---

## 5. Signature moonshots — what makes this not a student dashboard

Five concepts, taken together, form a coherent thesis: **honesty as a system property, not a disclaimer.**

1. **The Instrumented Null (NRIS, §3.1)** — most projects hide weak results; this one measures its own measurement, reporting the confidence interval, the permutation null, and the minimum effect it ever had the power to detect.
2. **The Model Confidence Contract (§3.3)** — the UI is *contractually, testably* forbidden from sounding more confident than the evaluation warrants. Claim discipline as failing CI, not as culture.
3. **The Skeptic Agent (§3.4)** — an adversary built into the product that attacks every ranking with leakage, staleness, sparsity, and instability probes before a human sees it.
4. **The Negative Alpha Autopsy (§3.5)** — a five-exhibit anatomical explanation of *why* prediction failed at this scale, built from artifacts the repo already committed.
5. **The Research Courtroom (§3.7)** — a four-persona evidence debate with citation chips and, by design, no verdict slot: the flashiest feature is structurally incapable of giving advice.

---

## 6. Do-not-claim register (roadmap additions)

The base register is `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §5 and audit §16 — all of it still binding. Building this roadmap adds new claim risks; the following are forbidden unless committed evidence changes:

| Never claim | Even after building | Say instead |
|---|---|---|
| "Predicts stock returns" / "identifies winners" | anything here | "Leakage-aware evaluation framework that found no reliable signal" |
| "Statistically proven that BIST is unpredictable" | NRIS | "No detectable signal at this data scale; power limited to \|IC\| ≳ 0.3" |
| "Signal found in real/USD terms" (from one lucky split) | Real-Terms Lens | "Conclusion re-evaluated per return basis; significance treatment applied" |
| "Validated by the Skeptic Agent" | Skeptic Agent | "Not obviously broken per automated challenges; backtest IC unchanged" |
| "Net returns of X% after costs" | Friction simulator | "Hypothetical illustration of how friction erodes even lucky baskets" |
| "AI analysts recommend…" / any courtroom verdict | Research Courtroom | "Structured evidence debate; no verdict is produced by design" |
| "Human-validated rankings" | Analyst ledger | "Analyst dissent recorded for research; never a score input" |
| "Calibrated confidence" (before the bench runs) | Calibration bench | "Confidence calibration audited; result: [as measured]" |
| "Production-ready" / "deployed at scale" | anything | "Deployed demo prototype; research support, not investment advice" |

Safe identity phrases (use freely): *research platform; leakage-aware evaluation framework; equity-ranking experiment; financial data-forensics and model-diagnostics system; honest negative-result ML case study; decision-support prototype — not investment advice.*

---

## 7. Interviewer-facing narrative

Extends `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §6–§7 (which stay authoritative for the *current* system); the additions below assume Stage 2–3 of this roadmap has shipped — do not use them before the referenced artifacts exist.

**CV line (one sentence):** Built FinanceIQ, a full-stack equity-research platform (FastAPI/PostgreSQL/React, reproducible Python pipeline) whose validation gates automatically exposed frozen vendor data, and whose leakage-controlled walk-forward evaluation produced — and transparently reports — a defensible negative result (rank IC ≈ 0).

**The 90-second story:** "I set out to test whether free yearly fundamentals could predict next-year returns on Turkish equities. The first real finding came from the pipeline itself: my validation gates caught that the vendor's 'historical' fundamentals were one frozen snapshot copied across years. I rebuilt trustworthy data from corrected sources, then ran leakage-controlled walk-forward experiments against naive baselines. The answer was no reliable signal — rank IC statistically indistinguishable from zero. Instead of burying that, I made it the product: the UI leads with the weak signal, the scoring engine literally penalizes itself for its own backtest, and the interface is [being] bound by a tested contract that forbids predictive language the evaluation can't support. What I'm proudest of isn't a model — it's that the system defends its own honesty."

**Anticipated challenges and answers:**
- *"So it doesn't work?"* — "The prediction hypothesis failed; the system works exactly as designed. Distinguishing those two is the point. I can show you the permutation test and the power analysis that make the null result rigorous rather than an excuse." (After Stage 2.)
- *"Why should a negative result impress me?"* — "Because the failure modes I engineered against — leakage, frozen data, overfitting, overclaiming — are the ones that make real quant systems silently wrong. I have committed artifacts for each."
- *"What would you do with more resources?"* — point at this roadmap: instrumented significance, real-terms evaluation, adversarial self-checks — "more rigor per data point, before more data."

**Demo order (post-Stage-3):** runtime-status (live data proof) → frozen-evidence specimen archive (the forensics wow) → seismograph + NRIS null histogram (the instrumented null) → Negative Alpha Autopsy (the explanation) → Skeptic/Courtroom (the philosophy as product) → close on the Model Confidence Contract test failing when you type "predicts."

---

## 8. Maintenance of this document

- Update the assessment (§1) only from repo evidence; cite files. If a Phase-2 task lands, move its idea's status inline (e.g. "shipped in commit X — see …").
- Never let this file make a performance claim; it inherits the claims guide's boundary.
- If future committed evidence ever *does* show significant signal, the change flows: experiments → NRIS report → audit update → claims-guide update → only then this file and any UI copy (with MCC version bump).
