# FINANCEIQ_AGENT_TASK_QUEUE.md

Sequenced task queue for future coding agents. Grounded in the 2026-07-08 audit (`FINANCEIQ_MODEL_VALIDITY_AUDIT.md`, `OPERATING_LAYER_VALIDATION.md`). Every agent: read `CLAUDE.md` → `PRD.md` → `REPO_MAP.md` → `FINANCEIQ_SMALL_MODEL_RULES.md` first, then only the task's listed files. Universal verification: after backend edits run `PYTHONPATH=backend python -m pytest backend/tests` (expect 51 pass); after pipeline/test edits run `PYTHONPATH=. python -m pytest tests/` (expect 97 pass after OPS-01, 95/97 before); after data edits also run `make data-validate`. Rollback for all tasks: `git checkout -- <files>` before commit, `git revert` after — no task below has irreversible side effects unless its rollback note says otherwise.

---

### OPS-01 — Fix stale `call_local_llm` references
- **Objective:** Rename the two test references and one training-script reference from `call_local_llm` to `call_llm` (function was renamed in source).
- **Why:** Restores the root suite to 97/97; every later task's verification gets cleaner.
- **Files:** `tests/test_research_agent.py` (two tests), `research_agent_training/evaluate_local_llm.py:129`. Read first: those two files, `backend/app/services/research_agent.py` (confirm current signature of `call_llm`).
- **Allowed:** Rename the attribute references; adjust monkeypatch targets/kwargs only as far as the new signature requires.
- **Forbidden:** Changing `research_agent.py` itself; weakening what the tests assert (fail-safe behavior).
- **Acceptance:** `PYTHONPATH=. python -m pytest tests/` → 97 passed.
- **Verify:** command above; also `PYTHONPATH=backend python -m pytest backend/tests` (unchanged, 51 pass).
- **Risk:** low. **Model:** small. **Depends:** none.

### OPS-02 — Remove dead `unnecessary/README.md` link in README
- **Objective:** README.md:396 links to `unnecessary/README.md`, which does not exist. Reword to state the quarantined integrations (Finnhub, news API, synthetic seeders, KAP scraper) were removed from the repo entirely.
- **Why:** Dead link undermines an otherwise meticulous README; misleads agents into recreating the directory.
- **Files:** `README.md`. Read first: `README.md` around line 396, `PRD.md` "Resolved" section.
- **Allowed:** Prose edit to that section only. **Forbidden:** Creating `unnecessary/`; touching any code.
- **Acceptance:** No reference to a nonexistent path remains; quarantine *rule* still stated.
- **Verify:** `grep -n "unnecessary/" README.md` → no dead path link.
- **Risk:** low. **Model:** small. **Depends:** none.

### OPS-03 — Correct stale test-count line in TASK_STATE.md
- **Objective:** The ledger's "97 + 51 all passing" line reflects 2026-06-11. Update to the verified current state (95/97 + 51/51, or 97/97 + 51/51 after OPS-01), with date.
- **Why:** PRD.md already flags the ledger as out of date; agents grep this file for status.
- **Files:** `TASK_STATE.md` (grep for the line; do not read whole). Read first: `CLAUDE.md` "Known test-suite state".
- **Allowed:** That status line/row only. **Forbidden:** Rewriting ledger history.
- **Acceptance:** Ledger matches actually-observed test results with a date.
- **Verify:** run both suites, compare to the edited line.
- **Risk:** low. **Model:** small. **Depends:** ideally after OPS-01.

### OPS-04 — Resolve quarterly-template and empty-dir ambiguities (docs only)
- **Objective:** Determine whether `backend/templates/quarterly_fundamentals_template.csv` is consumed by any code (grep imports/paths) and what `backend/experiments/` (empty, untracked) was for; record findings in PRD.md "Needs Verification"/"Resolved".
- **Why:** Two standing uncertainties in PRD.md; cheap to close.
- **Files:** grep across `backend/`; edit `PRD.md` only. Read first: `PRD.md` §Needs Verification.
- **Allowed:** PRD.md prose; nothing else. **Forbidden:** Deleting the template or directory (owner decision).
- **Acceptance:** Each item either moved to "Resolved" with evidence (grep output cited) or kept with a sharper question.
- **Verify:** `grep -rn "quarterly_fundamentals_template" backend/ scripts/` output quoted in the edit.
- **Risk:** low. **Model:** small. **Depends:** none.

### OPS-05 — Make backend Settings tolerate unknown `.env` keys
- **Objective:** `backend/app/config.py` `Settings` rejects unknown keys, so an untracked `backend/.env` with `OPENROUTER_*` aborts pytest collection. Change pydantic-settings config to ignore extras (or explicitly declare the three OPENROUTER keys), preserving all current validation of known keys.
- **Why:** Removes a recurring trap that breaks the documented `cd backend && pytest` flow.
- **Files:** `backend/app/config.py`. Read first: whole file, `backend/tests/conftest.py`, CLAUDE.md gotcha note.
- **Allowed:** `model_config`/field additions in config.py; a regression test. **Forbidden:** Changing any setting's default or type; touching secrets handling.
- **Acceptance:** With a scratch `backend/.env` containing `OPENROUTER_API_KEY=x`, `cd backend && python -m pytest tests/` collects and passes 51+; without it, identical behavior. Update the CLAUDE.md gotcha note afterward.
- **Verify:** both invocation styles of the backend suite; `git diff` shows config-scope-only change.
- **Risk:** medium (config behavior). **Model:** medium. **Depends:** none. **Rollback note:** revert restores the gotcha — also revert the CLAUDE.md note.

### DATA-01 — Cross-check `data_dictionary.md` against actual dataset columns
- **Objective:** Verify every column in `data/trusted_clean/modeling_dataset_2020_2025.csv` header appears in `data/trusted_clean/data_dictionary.md` with correct accepted/rejected status, and that the dictionary names no column that no longer exists. Report drift; fix only the *generator* if the dictionary is generated, else file findings.
- **Why:** The parameter catalog is the product's credibility surface; audit found it unverified.
- **Files:** read CSV header only (`head -1`), `data_dictionary.md`, and whichever `scripts/data_collection/` module writes the dictionary. Read first: `data_quality_report.md`.
- **Allowed:** Report file or generator fix + regeneration via Makefile. **Forbidden:** Hand-editing anything under `data/trusted_clean/`.
- **Acceptance:** Written drift list (possibly empty); any fix regenerates cleanly.
- **Verify:** `make data-validate`; diff of regenerated dictionary limited to expected corrections.
- **Risk:** low (read-mostly). **Model:** medium. **Depends:** none.

### DATA-02 — Test that missing features reduce confidence, never get filled
- **Objective:** Add backend tests pinning `forecasting_csv_service.py` behavior on rows with null features: confidence drops, no value is imputed, explanation mentions missingness.
- **Why:** "Missing reduces confidence" is a core product claim currently untested at serving level (audit §9).
- **Files:** `backend/tests/test_forecasting_csv_service.py` (extend), `backend/app/services/forecasting_csv_service.py` (read only). Read first: the service in full, existing test fixtures.
- **Allowed:** New tests + fixtures only. **Forbidden:** Changing service behavior; if a test reveals imputation, STOP and report — that is a strong-model/owner issue.
- **Acceptance:** New tests pass and fail if imputation were introduced.
- **Verify:** backend suite green with increased count.
- **Risk:** low-medium. **Model:** medium. **Depends:** none.

### DATA-03 — Clear failure messages for malformed manual CSV inputs
- **Objective:** Confirm (and where absent, add) explicit, human-readable errors when `data/trusted_raw/` manual CSVs have wrong headers/shapes, in `scripts/data_collection/manual_ingest.py` and `ingest_corrected_yearly_financials.py`, with tests.
- **Why:** Manual CSVs are the only human-typed inputs; silent misparse is the top data-corruption vector.
- **Files:** the two ingest modules, `tests/test_manual_ingest.py`, `tests/test_corrected_yearly_ingestion.py`. Read first: both modules in full, `validate.py`.
- **Allowed:** Error-message/validation additions that reject bad input; tests. **Forbidden:** Any change that accepts previously-rejected input, imputes, or alters accepted-data output (byte-identical `data/trusted_clean/` on rerun).
- **Acceptance:** Root suite green; `make data && make data-validate` reproduces identical dataset (compare row/feature counts: 403/40/321).
- **Verify:** root suite; `make data-validate` summary unchanged.
- **Risk:** medium. **Model:** strong (touches guard-adjacent code). **Depends:** none. **Rollback note:** regenerated outputs under `data/trusted_clean/` must be reverted together with code.

### DATA-04 — Make the "DEGENERATE data" caveat conditional
- **Objective:** `experiments/run_experiments.py:425-430` hardcodes a caveat claiming features are identical every year. Compute actual per-feature cross-year variance at report time and emit either the degenerate warning or an accurate "corrected features vary by year; N frozen columns excluded" note.
- **Why:** Biggest remaining honesty gap: the committed report *overstates* degeneracy post-correction (audit §12).
- **Files:** `experiments/run_experiments.py`. Read first: whole file, `data_quality_report.md`, `frozen_column_evidence.md`.
- **Allowed:** Report-generation logic only; no change to model training/eval code paths. **Forbidden:** Touching metrics computation, splits, or model list; hand-editing `experiments/reports/summary.md`.
- **Acceptance:** Diff confined to report-writing block; a dry run regenerates a summary whose caveat matches measured variance; leaderboard numbers unchanged.
- **Verify:** `make research`, then diff `experiments/leaderboard.csv` (must be identical) and review `reports/summary.md` caveat.
- **Risk:** high (regenerates committed experiment outputs). **Model:** strong. **Depends:** none. **Rollback note:** revert code *and* regenerated `experiments/` outputs as one unit.

### DATA-05 — Re-run experiments and refresh honest summary
- **Objective:** After DATA-04, run `make research`, commit regenerated `experiments/` outputs, and update the one-paragraph verdict in PRD.md/TASK_STATE.md if (and only if) the IC ≈ 0 conclusion wording needs adjusting.
- **Why:** Aligns committed evidence with corrected data and corrected caveat.
- **Files:** generated `experiments/` outputs; PRD.md/TASK_STATE.md prose. Read first: DATA-04 diff, current summary.
- **Allowed:** Regeneration + prose sync. **Forbidden:** Cherry-picking favorable numbers; deleting historical results; any claim upgrade beyond what new tables show.
- **Acceptance:** New summary's caveat is accurate; verdict wording matches new tables; no invented numbers.
- **Verify:** `make research` exit 0; manual table-vs-prose comparison recorded in the final report.
- **Risk:** high. **Model:** strong. **Depends:** DATA-04.

### DATA-06 — Audit sector labels and `sector_service.py`
- **Objective:** Establish where the dataset `sector` column comes from, whether `backend/app/services/sector_service.py` uses consistent labels, and how many stocks each sector has; document that within-sector comparisons at n<10 are anecdotal (add that caveat to any sector UI copy).
- **Why:** Audit §13 flagged sector comparison as unverified; tiny per-sector samples mislead easily.
- **Files:** `sector_service.py`, dataset header + `data/config/*.csv`, relevant frontend page if sector UI exists. Read first: `sector_service.py` in full.
- **Allowed:** Documentation, UI caveat wording, tests. **Forbidden:** Changing sector assignment logic without owner sign-off.
- **Acceptance:** Written provenance note (in METHODOLOGY.md or audit file) + per-sector counts; caveat present wherever sectors are compared.
- **Verify:** backend suite; grep for the new caveat copy.
- **Risk:** medium. **Model:** medium. **Depends:** none.

### MOD-01 — Surface IC dispersion wherever aggregate IC is shown
- **Objective:** Wherever the UI/API reports the headline IC ≈ 0 (Experiments page, dashboard), also present the per-split range (−0.17 to +0.22 across test_2023/24/25) with a "individually indistinguishable from zero at n≈40" note.
- **Why:** Prevents both over- and under-claiming; per-audit §19 uncertainty labeling.
- **Files:** `frontend/src/pages/ExperimentsPage.jsx`, possibly `DashboardPage.jsx`; backend only if the numbers aren't already in the payload. Read first: ExperimentsPage in full, `experiments/leaderboard.csv`.
- **Allowed:** Copy + display of numbers already present in committed results. **Forbidden:** New statistics computed ad hoc in the frontend; touching the seismograph fallback logic; softening the weak-signal message.
- **Acceptance:** Range shown with source (leaderboard) and sample-size note; real-API path unchanged (demo fallback intact).
- **Verify:** `npm run build`; visual check via `npm run dev`.
- **Risk:** low-medium. **Model:** medium. **Depends:** VER-02 (build must be known-green first).

### MOD-02 — Document the serving heuristic in METHODOLOGY.md
- **Objective:** Add a section describing `forecasting_csv_service.py`'s actual algorithm (top-quartile winner discrimination → normalized weights → percentile ranking), explicitly distinguishing it from the walk-forward experiment models and stating it has no validated predictive skill.
- **Why:** Audit §14/§16: the serving heuristic is the most likely thing to be over-described in a demo.
- **Files:** `METHODOLOGY.md`. Read first: `forecasting_csv_service.py` docstring + train/run functions.
- **Allowed:** Docs only. **Forbidden:** Code changes.
- **Acceptance:** Section matches source behavior (cite function names); includes the "historically co-occurred with winners, not predicts winners" framing.
- **Verify:** none required beyond source cross-read; `git diff` docs-only.
- **Risk:** low. **Model:** small. **Depends:** none.

### UI-01 — Disclaimer coverage on remaining pages
- **Objective:** Add the standard "research support, not investment advice" line to authenticated pages lacking it (grep for "investment advice" this session hit only 10 of 21 pages; missing: `LabelingLabPage.jsx`, `ValidationLabPage.jsx`, `AdminPage.jsx`, `ComparePage.jsx`, `ScoreResultPage.jsx`, `SearchPage.jsx`, `AIResearchAssistantPage.jsx`, `ResearchAgentPage.jsx`, `CompaniesResearchPage.jsx` — re-verify before editing; some may inherit the disclaimer from a shared layout or phrase it differently).
- **Why:** Claim-boundary consistency (audit §18).
- **Files:** the listed pages + any shared layout/footer component. Read first: `DashboardPage.jsx` disclaimer pattern, shared components in `frontend/src/components/` if present.
- **Allowed:** Copy insertion matching the existing visual language; a shared component if one already fits. **Forbidden:** New dependencies; layout restructuring; removing existing caveats.
- **Acceptance:** `grep -rl "investment advice" frontend/src/pages` covers all data-displaying pages (or the shared layout demonstrably renders on them).
- **Verify:** `npm run build`; the grep above.
- **Risk:** low. **Model:** small. **Depends:** VER-02 recommended first.

### UI-02 — Dataset-scope line on ranking views
- **Objective:** Add "Based on ~40 public BIST companies, yearly data 2020–2025, nominal TRY returns" scope copy to Forecasting and Research ranking views.
- **Why:** Small-sample and inflation context is the most-needed caveat identified by the audit (§6–§8, §12).
- **Files:** `ForecastingPage.jsx`, `ForecastingDetailPage.jsx`, `ResearchPage.jsx`. Read first: each page's existing caveat placement.
- **Allowed:** Copy only. **Forbidden:** Numbers not backed by `data_quality_report.md`.
- **Acceptance:** Copy present and consistent across the three pages; matches report numbers.
- **Verify:** `npm run build`; visual check.
- **Risk:** low. **Model:** small. **Depends:** VER-02 recommended first.

### BE-01 — Demo smoke-check script
- **Objective:** Add a read-only script (e.g. `scripts/demo_smoke.py` or a `make demo-check` target — new target, no renames) that hits `/health`-equivalent, one `/research/*` endpoint, and one forecasting endpoint on a running backend, and reports whether responses carry real CSV-backed data versus fallback.
- **Why:** Audit §20 item 4 is the only pre-demo check with no automation.
- **Files:** new script + Makefile addition. Read first: `backend/app/main.py`, `backend/app/routers/research.py` + `forecasting.py` route signatures (never assume routes — check).
- **Allowed:** New read-only script, new Makefile target. **Forbidden:** Renaming existing targets; any state-mutating endpoint calls; new dependencies beyond stdlib/requests-if-already-present.
- **Acceptance:** Against `docker compose up` or local uvicorn, script prints per-endpoint PASS/FAIL; exits nonzero on failure.
- **Verify:** run it against a locally started backend; document output.
- **Risk:** medium (needs running stack). **Model:** medium. **Depends:** none.

### BE-02 — Fresh-database bootstrap verification
- **Objective:** Verify and document that a fresh Postgres + `alembic upgrade head` + `python -m scripts.load_trusted_yearly` produces a working backend (the documented Docker path), recording exact commands and row counts in `docs/` or README.
- **Why:** Demo-day risk: DB bootstrap is documented but not recently re-verified.
- **Files:** docs only; execution via docker compose db service. Read first: `backend/scripts/start_backend.sh`, `backend/alembic/` heads, `load_trusted_yearly.py`.
- **Allowed:** Running the documented commands against a *scratch* database; docs updates. **Forbidden:** New migrations; editing shipped migrations; running against any non-scratch DB.
- **Acceptance:** Documented transcript: migration head applied, `yearly_stocks` row count, backend boots.
- **Verify:** the transcript itself; backend suite still green.
- **Risk:** medium. **Model:** medium. **Depends:** none. **Rollback note:** drop the scratch database.

### VER-01 — Record a full verification baseline
- **Objective:** Run root suite, backend suite, `make data-validate`, `npm run build` and record dated results in TASK_STATE.md (one row).
- **Why:** Gives every later task a trustworthy baseline to diff against.
- **Files:** TASK_STATE.md (one line). Read first: CLAUDE.md commands section.
- **Allowed:** Running listed commands; one ledger line. **Forbidden:** "Fixing" anything found — report only.
- **Acceptance:** Ledger line with all four results and date.
- **Verify:** the commands are the verification.
- **Risk:** low. **Model:** small. **Depends:** none (but after OPS-01 the expected root count is 97/97).

### VER-02 — Frontend install, build, and e2e status
- **Objective:** `cd frontend && npm install && npm run build`, then `npm run e2e` if a backend is available; record pass/fail and any errors verbatim (do not fix in this task).
- **Why:** Production build is unverified in the current worktree (audit §20 item 5); UI tasks are blocked on knowing it's green.
- **Files:** none edited except a TASK_STATE.md status line. Read first: `frontend/package.json`, `frontend/playwright.config.*` if present.
- **Allowed:** Install + build + test execution; status note. **Forbidden:** Dependency upgrades; lockfile edits beyond what `npm install` itself does (if lockfile changes, report, don't commit).
- **Acceptance:** Build result recorded; e2e result or "not run: no backend" recorded.
- **Verify:** command exit codes.
- **Risk:** low. **Model:** small. **Depends:** none.

### DOC-01 — Seed first repo-memory lessons
- **Objective:** After any two of the above tasks complete, write the first 1–3 lesson files under `.agent/memory/` per its README (e.g. the `backend/.env` pytest trap if OPS-05 isn't done yet; the "run backend tests from repo root" pattern).
- **Why:** Makes confirmed traps durable for future small models.
- **Files:** `.agent/memory/*.md`. Read first: `.agent/memory/README.md`.
- **Allowed:** New lesson files following the format. **Forbidden:** Duplicating CLAUDE.md content; speculation.
- **Acceptance:** Each lesson is confirmed-by-execution, one per file, one-line summary on top.
- **Verify:** n/a (docs).
- **Risk:** low. **Model:** small. **Depends:** any two completed tasks.

---

**Suggested order:** OPS-01 → VER-01 → VER-02 → OPS-02 → OPS-03 → UI-01 → UI-02 → MOD-02 → OPS-04 → DATA-01 → DATA-02 → OPS-05 → BE-01 → DATA-06 → BE-02 → MOD-01 → DATA-03 → DATA-04 → DATA-05 → DOC-01 (interleave as convenient; respect listed dependencies).

---

# Phase 2 — Roadmap execution queue

Implements `FINANCEIQ_MOONSHOT_ROADMAP.md` (added 2026-07-12). Phase 1 above is truth-preservation; Phase 2 is capability-building. **Stage-0 gate: do not start any Phase 2 task until OPS-01, DATA-04 + DATA-05, and UI-01 are done** — building new surfaces on top of a stale caveat compounds the honesty debt.

Universal rules for Phase 2 (in addition to the Phase-1 header rules):
- Every new evaluation output goes to a **new, separately named** artifact/directory — never overwrite `experiments/leaderboard.csv`, `experiments/reports/summary.md`, or anything in `data/trusted_clean/` except via existing Makefile regeneration.
- Every new UI surface ships with its caveat copy taken **verbatim** from the roadmap's per-idea "honest wording" — wording changes require editing the roadmap first.
- New Makefile targets are additive; renames remain forbidden.
- New data series (CPI, USDTRY, macro) follow the manual-CSV pattern of `data/trusted_raw/shares_outstanding_events.csv`: sourced, dated, shape-validated, null-if-missing, never imputed.
- No new paid dependencies. Python additions must be stdlib/numpy/pandas/scikit-learn (already present); frontend additions must use existing dependencies.

### R2-REPRO-01 — Experiment run manifests + one-command reproduction check
- **Priority:** P1 (highest of Phase 2). **Stage:** 1. **Owner role:** Research/Backend. **Risk:** medium.
- **Why this matters / weakness fixed:** Reproducibility currently rides on git discipline; the DEGENERATE-caveat incident (audit §12) proved committed prose can drift from the run that produced it. Manifests make every table traceable and re-checkable — the foundation every later Phase-2 task builds on.
- **Target files:** `experiments/run_experiments.py` (append manifest writing inside `run()`, after existing outputs — line ~326; no change to metrics code), new `scripts/verify_run.py`, `Makefile` (new additive target, e.g. `research-verify-run`), `METHODOLOGY.md` (short "Reproducibility" section).
- **Current problem:** No record of git SHA, dataset hash, seeds, or environment for any committed experiment output.
- **Desired outcome:** Each `make research` writes `experiments/results/runs/<UTCstamp>_<shortsha>/manifest.json` containing: git SHA + dirty flag, SHA-256 of `data/trusted_clean/modeling_dataset_2020_2025.csv`, feature column list, model names/params, numpy/pandas/sklearn versions, and SHA-256 of each output file. `verify_run.py <manifest>` recomputes the dataset hash, re-runs the harness into a temp dir, and diffs leaderboard metrics to tolerance.
- **Step-by-step:** (1) Read `run_experiments.py` in full — note `MODELS` dict at :231 and `run()` at :326. (2) Implement `_write_manifest(outputs: list[Path])` using only stdlib (`hashlib`, `subprocess` for git, `importlib.metadata`). (3) Call it last in `run()`. (4) Write `verify_run.py` (stdlib + pandas): load manifest → check dataset hash → invoke harness with output dir override (add an `--out` argument ONLY if the harness lacks one; keep default behavior byte-identical) → compare leaderboards. (5) Add Makefile target. (6) Document in METHODOLOGY.md.
- **Acceptance criteria:** `make research` produces a manifest; running `verify_run.py` on it exits 0 with a "reproduced within tolerance" line; default `make research` outputs are otherwise unchanged (diff leaderboard.csv → identical).
- **Verification / commands:** `PYTHONPATH=. python -m pytest tests/` (green, count unchanged or +new tests); `make research` then `python scripts/verify_run.py experiments/results/runs/<latest>/manifest.json`; `git diff --stat` confined to listed files + new run dir.
- **Dependencies:** DATA-04/DATA-05 first (Stage-0 gate — the first registered run must carry the corrected caveat). **Failure modes:** nondeterminism breaks reproduction (all stochastic models are seeded with `random_state=42` per `run_experiments.py:239-242`, verified 2026-07-12, so failures point at data or environment drift — report, don't paper over with loose tolerances); `--out` refactor accidentally changing default paths. **Rollback:** revert code + delete `runs/` dir (generated).
- **Demo after completion:** point at any chart → "produced by run X, dataset hash Y, reproduce with one command." **Do not overclaim:** provenance ≠ validity; the manifest certifies inputs, not methodology. **CV impact:** high — "experiment registry with one-command reproduction" is senior-engineer vocabulary.

### R2-STAT-01 — Permutation test + bootstrap CI for the headline IC (NRIS core)
- **Priority:** P1. **Stage:** 2. **Owner role:** Research. **Risk:** medium.
- **Why this matters / weakness fixed:** "IC ≈ 0" currently has no significance treatment (roadmap §1.4). This task turns the project's central claim into a measured, defensible statistic — the highest research-value-per-hour task in the queue.
- **Target files:** new `experiments/significance.py`, new outputs `experiments/results/significance_report.{json,md}`, `Makefile` (additive target `research-significance` or similar), `METHODOLOGY.md` (results paragraph), root `tests/test_significance.py`.
- **Current problem:** The committed `experiments/results/test_*.json` files hold **aggregate metrics only** (verified 2026-07-12: keys `split/train_n/test_n/models`, per-model metric dicts — no per-ticker predictions). So there is no null distribution, no CI, no multiplicity correction, and no persisted predictions to compute them from.
- **Desired outcome:** First, an additive per-ticker prediction dump; then, for each model and pooled across splits: (a) permutation p-value — shuffle realized returns within each test year ≥ 1,000×, recompute Spearman, report the observed value's percentile; (b) bootstrap 95% CI on IC — resample tickers within year with replacement; (c) a family-wise note correcting for the 6 ML models compared (Bonferroni is fine at MVP). Report leads with the pooled, corrected result.
- **Step-by-step:** (1) Read `run_experiments.py` in full (`_metrics` :185, `MODELS` :231, `run()` :326). Add an **additive** prediction-persistence block writing `experiments/results/predictions_<split>.csv` (columns: ticker, year, model, y_true, y_pred) alongside the existing outputs — no change to metrics computation, splits, or the model list. All stochastic models are already seeded (`random_state=42`, `run_experiments.py:239-242`, verified), so re-running `make research` must reproduce the committed leaderboard. (2) Build `significance.py` to consume the prediction CSVs — never to retrain models. (3) Implement permutation + bootstrap with a fixed seed, vectorized (pandas/numpy). (4) Write the Markdown report with a fixed template: pooled corrected result first, per-split labeled "exploratory," and a mandatory sentence that per-split ICs at n≈40 have SE ≈ 0.16. (5) Unit tests: on synthetic data with a known planted signal, permutation p is small; on shuffled data, p is uniform-ish (sanity bounds, seeded). (6) Makefile target + METHODOLOGY.md paragraph quoting the actual numbers produced.
- **Acceptance criteria:** `experiments/leaderboard.csv` identical after the re-run that produces the prediction dumps (`shasum` before/after); the `run_experiments.py` diff is confined to the additive dump block; significance report exists and derives from the dumped predictions; tests green; the report never uses the words "proves" or "confirms market efficiency."
- **Verification / commands:** `PYTHONPATH=. python -m pytest tests/`; `shasum experiments/leaderboard.csv` before/after `make research`; run the new significance target twice → identical output (seeded); `git diff` confined to listed files + new generated outputs.
- **Dependencies:** R2-REPRO-01 recommended first (register the run that produces the dumps). **Failure modes:** shuffling across years instead of within (destroys the panel structure and fakes the null); leaderboard drift on re-run (would mean nondeterminism or data drift — STOP and report, do not commit); accidentally quoting a small per-split p as a discovery — the template guards this. **Rollback:** revert code *and* regenerated `experiments/` outputs as one unit (same rule as DATA-04/05).
- **Demo after completion:** the null-distribution histogram with observed IC inside it. **Do not overclaim:** absence of detectable signal ≠ proof markets are unpredictable; small dataset, one regime. **CV impact:** very high — permutation-tested negative result reads as graduate-level rigor.

### R2-STAT-02 — Power analysis: minimum detectable IC
- **Priority:** P1. **Stage:** 2. **Owner role:** Research. **Risk:** low.
- **Why this matters / weakness fixed:** Completes NRIS: the strongest defense of a null result is showing what effect size the study could ever have detected. Answers the examiner question "maybe your data was just too small to see it" — with *yes, and here is exactly how small*.
- **Target files:** extend `experiments/significance.py` + its report; `METHODOLOGY.md`; `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` §11 (add the power sentence to the rehearsed uncertainty answer).
- **Current problem:** Audit §7 states SE ≈ 0.16 informally; nothing computes or commits the detectable-effect threshold.
- **Desired outcome:** Committed computation of minimum detectable |IC| at 80% power / α=0.05 for: one split (n≈40), pooled three splits, and a projection table ("with k more years of 40 tickers, detectable |IC| becomes …") — the projection framed strictly as *pipeline readiness*, never as promised results.
- **Step-by-step:** (1) Implement analytic power for Spearman via Fisher z-approximation (document the approximation in the report). (2) Cross-check with a small simulation (seeded) — generate correlated ranks at various true ρ, measure rejection rates. (3) Add the projection table. (4) Update the two docs with the produced numbers, cited to the report file.
- **Acceptance criteria:** Report section present with both analytic and simulated values agreeing within tolerance; docs quote the report, not hand-derived numbers.
- **Verification / commands:** root pytest; rerun target → identical (seeded); doc numbers grep-match the report.
- **Dependencies:** R2-STAT-01. **Failure modes:** projection table misread as a promise ("with more data it will work") — the framing sentence from the claims guide §5 must sit directly above the table. **Rollback:** revert files.
- **Demo after completion:** one sentence in the demo script: "we could only ever have detected a signal three times larger than anything plausible here — so we report the null with its limits." **Do not overclaim:** power analysis bounds detection, it does not estimate the true effect. **CV impact:** high.

### R2-CONTRACT-01 — Model Confidence Contract v1 + claims lint
- **Priority:** P1. **Stage:** 2 (also hardens Stage 0). **Owner role:** Backend/Product. **Risk:** medium.
- **Why this matters / weakness fixed:** Claim discipline is currently cultural (grep audits, task UI-01). This makes it infrastructure: a failing test when copy outruns evidence. It is also the roadmap's most distinctive engineering artifact (§3.3).
- **Target files:** new `model_confidence_contract.json` at the repo root (beside the other FINANCEIQ_* governance files), new `scripts/lint_claims.py`, new backend test `backend/tests/test_confidence_contract.py`, `Makefile` (additive `claims-lint` target), `METHODOLOGY.md` cross-reference.
- **Current problem:** Nothing stops a future edit from adding "predicts" to a page or shipping decimal scores for sparse-coverage tickers.
- **Desired outcome:** v1 contract (hand-written, versioned) encoding at minimum: forbidden vocabulary on user-facing surfaces while pooled IC CI contains 0 (`predicts`, `will outperform`, `expected return`, `buy`, `sell`, `hold` as recommendations); required disclaimer presence per data-displaying page; required `unevaluated_forward_forecast` labeling on inference rows. `lint_claims.py` (stdlib only) scans `frontend/src/pages/*.jsx` and backend response constants, exits nonzero on violation with file:line output. Backend test asserts the forecasting service `DISCLAIMER` and inference labeling satisfy the contract.
- **Step-by-step:** (1) Inventory current copy: `grep -rn "predict\|investment advice\|forecast" frontend/src/pages backend/app/services` — build the allowlist of legitimate contexts (e.g. "no validated predictive skill" contains "predict" and is fine; match on word + absence of negation patterns, and keep an explicit per-file:line allowlist in the contract to avoid regex cleverness). (2) Write contract JSON with `version`, `evidence_basis` (cites leaderboard + significance report when it exists), `rules[]`. (3) Write the linter; run; fix nothing silently — report any existing violations as findings (they become UI-01-style tasks). (4) Backend test. (5) Makefile target; document.
- **Acceptance criteria:** Linter runs clean on current tree OR outputs a committed findings list; deliberately adding "predicts stocks" to a page makes it fail with correct file:line; backend suite green with +1 test.
- **Verification / commands:** `python scripts/lint_claims.py` (exit 0); mutation check (add violation, expect exit 1, revert); `PYTHONPATH=backend python -m pytest backend/tests`.
- **Dependencies:** UI-01 (disclaimer coverage) first, else the linter's baseline is noisy. **Failure modes:** overzealous regex blocking honest sentences (allowlist mechanism is the fix); false comfort — lint checks vocabulary, not meaning (documented limitation in the contract itself). **Rollback:** delete the three new files + Makefile line; no product code touched.
- **Demo after completion:** live-edit a page to say "predicts winners," run the lint, watch it fail. **Do not overclaim:** the contract is a tripwire, not a proof of honesty. **CV impact:** very high — genuinely original, interviewers remember it.

### R2-REAL-01 — Real-terms & USD return targets (parallel evaluation)
- **Priority:** P2. **Stage:** 2. **Owner role:** Data/Research. **Risk:** high (touches pipeline).
- **Why this matters / weakness fixed:** Nominal TRY targets in a hyperinflation window are the biggest interpretability weakness (audit §6/§12). Whether the null result holds in real/USD terms is an open, answerable question either answer improves the thesis.
- **Target files:** new `data/trusted_raw/macro/cpi_yearly_tr.csv` (manual, sourced — TÜİK annual CPI, retrieval date in a header comment or sidecar `.md`), USDTRY year-end via the existing `scripts/fetch_yahoo_chart_prices.py` pattern (new small fetch script or parameter — read it first), new pipeline stage `scripts/data_collection/derive_alternative_targets.py`, additive Makefile target, new outputs `data/trusted_clean/alternative_targets_report.{json,md}` + target columns in a **separate CSV** (`modeling_targets_alternative.csv`) — NOT new columns in the main modeling dataset (keeps the headline dataset byte-identical), harness invocation into `experiments/results_real_terms/`.
- **Current problem:** All committed metrics use nominal TRY returns; cross-year comparability is broken by inflation.
- **Desired outcome:** Three target bases per company-year with targets present only where inputs exist (missing CPI/FX year → null, never interpolated); walk-forward results for each basis in the separate results dir; a comparison note in METHODOLOGY.md.
- **Step-by-step:** (1) Read `build_all.py`, `validate.py`, and the shares manual-CSV ingestion for the validation pattern to copy. (2) Create the CPI CSV (≤ 6 rows: 2020–2025) with source citation; shape-validate like `corrected_balance_sheet_2024.csv`. (3) USDTRY year-end fetch mirroring existing Yahoo usage. (4) Derivation stage with explicit formulas in docstring (real = (1+nominal)/(1+CPI)−1; USD = (1+nominal)·FX_T/FX_T+1−1 — verify direction against a hand-computed 2022 example in the tests). (5) Tests for: null propagation, formula correctness on known values, no mutation of existing outputs. (6) Run the harness per basis using `build_panel_for_target` (`run_experiments.py:115`) — confirm it can point at the alternative CSV without editing metric code; if it can't, STOP and report the minimal refactor needed rather than improvising. (7) METHODOLOGY.md paragraph with the actual per-basis pooled ICs, wired to R2-STAT-01 significance treatment.
- **Acceptance criteria:** `make data-validate` unchanged (403/40/321); main dataset byte-identical; new report + results dirs exist; root suite green with new tests; no imputation anywhere (test-pinned).
- **Verification / commands:** `make data-validate`; `shasum data/trusted_clean/modeling_dataset_2020_2025.csv` before/after → identical; root pytest; the new Makefile target runs end-to-end.
- **Dependencies:** R2-STAT-01 (so per-basis results get significance treatment before being quoted anywhere). **Failure modes:** FX direction inverted (hand-checked test guards); CPI vintage/base-year error; a lucky real-terms split promoted to a claim — forbidden per roadmap §6. **Rollback:** revert code + delete new generated dirs; main outputs untouched by design.
- **Demo after completion:** nominal-vs-real 2022 bar chart ("+186% nominal was not a bull market"). **Do not overclaim:** basis changes interpretation, not the conclusion, unless significance says otherwise. **CV impact:** high — inflation-aware evaluation shows financial-domain maturity.

### R2-SKEPTIC-01 — Skeptic Agent service + challenge report endpoint
- **Priority:** P2. **Stage:** 3. **Owner role:** Backend/Agent. **Risk:** medium.
- **Why this matters / weakness fixed:** Operationalizes self-skepticism: every ranking gets attacked (leakage probe, staleness, sparsity, sector-n, instability, backtest reminder) before a human sees it. Fixes audit §9 (sparse-column silent ranking) and §13 (sector small-n) at the product level.
- **Target files:** new `backend/app/services/skeptic_service.py`, route addition in `backend/app/routers/research_agent.py` (or `research.py` — read both first; both mount under `/research`), new `backend/tests/test_skeptic_service.py`, frontend panel later (separate task).
- **Current problem:** Caveats are static copy; nothing computes per-ticker contestability.
- **Desired outcome:** `GET /research/skeptic/{ticker}` returns `{ticker, checks: [{check_id, verdict: pass|warn|fail, evidence, severity}], footer}` where the six checks run purely on existing artifacts (`data_quality_report.json`, `frozen_column_evidence.json`, modeling CSV row, `experiments/leaderboard.csv`) — deterministic, no LLM, no new data. Fixed footer verbatim from roadmap §3.4 ("surviving these checks means *not obviously broken*, not *predictive*…").
- **Step-by-step:** (1) Read `research_agent.py` service + `services/research/` evidence loaders — reuse their file-access patterns and path env handling (`RESEARCH_REPO_ROOT`). (2) Implement checks as small pure functions, each unit-tested on fixtures (a sparse ticker, a frozen-column ticker, a small-sector ticker). (3) Router + response schema; respect `PUBLIC_DEMO_MODE` read-open convention. (4) Contract test pinning the response shape. (5) Verify the footer passes R2-CONTRACT-01 lint.
- **Acceptance criteria:** Backend suite green with new tests; endpoint returns real evidence for a real ticker and structured "insufficient data" (not fabricated verdicts) for missing inputs; no score computation altered.
- **Verification / commands:** `PYTHONPATH=backend python -m pytest backend/tests`; manual `curl localhost:8000/research/skeptic/ASELS` against a running backend, output recorded.
- **Dependencies:** none hard; MCC lint recommended first. **Failure modes:** check thresholds invented without evidence (each threshold must cite its source report or be labeled heuristic in the response); endpoint accidentally heavy (reads should be cached like other services — follow existing patterns). **Rollback:** revert; purely additive.
- **Demo after completion:** query a top-ranked ticker → watch the system prosecute its own ranking. **Do not overclaim:** never "validated by the Skeptic." **CV impact:** very high — adversarial self-checking is a differentiator.

### R2-AUTOPSY-01 — Negative Alpha Autopsy page
- **Priority:** P2. **Stage:** 3. **Owner role:** Frontend/Research. **Risk:** medium.
- **Why this matters / weakness fixed:** The negative result is displayed but never explained. Five committed-artifact exhibits (instability, overfit, sparsity, power, regime) turn "it failed" into "here is the anatomy of why" — the project's best interview surface. Also fixes the under-exposure of `experiments/results/` (`OPERATING_LAYER_VALIDATION.md` §6).
- **Target files:** new backend endpoint (likely in `backend/app/routers/research.py` + a small service) serving `feature_stability_by_split.csv`, `feature_stability_summary.csv`, `coverage_impact.csv`, `leaderboard.csv` as JSON; new `frontend/src/pages/AutopsyPage.jsx` + route in `frontend/src/App.jsx` + API function in `frontend/src/api/researchApi.js`; demo fallback per existing page conventions.
- **Current problem:** Feature-stability and coverage artifacts are invisible; tree-model overfit (consistently negative IC) is shown nowhere as a lesson.
- **Desired outcome:** A five-exhibit page in the Research Terminal visual language: (1) *Instability* — feature-weight sign flips across splits; (2) *Overfit* — baseline-vs-tree IC bars (trees negative in all three splits per leaderboard); (3) *Sparsity* — coverage impact; (4) *Power* — minimum detectable IC (from R2-STAT-02; render "pending" state if absent); (5) *Regime* — single-regime statement. Each exhibit: one chart + one finding paragraph distinguishing "consistent with" from "proves."
- **Step-by-step:** (1) VER-02 must be done (build known-green). (2) Read `ExperimentsPage.jsx` fully — copy its data-fetch/fallback/caveat patterns exactly. (3) Backend: read-only CSV→JSON endpoint(s), tested. (4) Page with the five exhibits; caveat strip verbatim from roadmap §3.5. (5) Route + nav wiring; disclaimer per UI-01 pattern. (6) `npm run build`; visual check via `npm run dev` with backend running; screenshot in the task report.
- **Acceptance criteria:** Page renders real artifact data with backend up, labeled demo fallback without; build green; no existing page modified beyond nav; every exhibit paragraph passes claims lint.
- **Verification / commands:** backend pytest; `cd frontend && npm run build`; manual visual check recorded.
- **Dependencies:** VER-02; R2-STAT-02 for exhibit 4 (soft — "pending" state acceptable). **Failure modes:** over-narration (claiming causal knowledge); inventing numbers for the power exhibit before STAT-02 lands (forbidden — render pending). **Rollback:** revert; additive.
- **Demo after completion:** the autopsy walk — likely the strongest 3 minutes of any demo. **Do not overclaim:** explains this failure; promises nothing about other data. **CV impact:** very high.

### R2-CAL-01 — Confidence calibration bench
- **Priority:** P3. **Stage:** 3. **Owner role:** Research. **Risk:** medium.
- **Why this matters / weakness fixed:** The hybrid score's 0.20 confidence component is displayed but never evaluated — the one place the project's own honesty standard isn't yet met (roadmap §1.4).
- **Target files:** new `experiments/calibration_bench.py` + report `experiments/results/calibration_report.{json,md}`; `METHODOLOGY.md` findings paragraph; additive Makefile target.
- **Current problem:** Unknown whether higher stated confidence corresponds to smaller realized rank error over the 321 target rows.
- **Desired outcome:** Reliability analysis: bin scored rows by confidence decile; per bin, mean |predicted rank − realized rank|; monotonicity check + a plot-ready CSV; a plain verdict sentence committed ("confidence is / is not informative about rank error at this scale"), whatever it turns out to be.
- **Step-by-step:** (1) Determine where per-row confidence is computed (`forecasting_csv_service.py` and/or `research_agent.py` — read both). Per-row confidence is **not persisted** for historical rows, so compute it by replaying the service on historical rows, with the replay date and code version documented in the report. (2) Join with realized returns from the modeling CSV (targets only, no leakage concern — this is meta-evaluation on past rows); rank error can reuse R2-STAT-01's `predictions_<split>.csv` dumps where model ranks are needed. (3) Bench script, seeded, deterministic. (4) Report + METHODOLOGY paragraph stating the measured verdict. (5) If uncalibrated: file a follow-up owner-decision task; do NOT tune confidence on the same rows (meta-overfitting).
- **Acceptance criteria:** Report committed; verdict sentence matches the numbers; no service code changed; root suite green.
- **Verification / commands:** root pytest; rerun bench → identical output.
- **Dependencies:** none hard. **Failure modes:** replay mismatch (service behavior changed since rows were scored — document the replay date); quiet recalibration (forbidden). **Rollback:** delete new files.
- **Demo after completion:** the reliability diagram, whichever way it points — an *audited* confidence number is rarer than a good one. **Do not overclaim:** "calibrated" only if measured so. **CV impact:** high.

### R2-COURT-01 — Research Courtroom (deterministic core)
- **Priority:** P3. **Stage:** 4. **Owner role:** Agent/Frontend. **Risk:** medium-high.
- **Why this matters / weakness fixed:** The signature demo: four personas (Bull/Bear/Skeptic/Risk) debate a ticker using only cited, validated evidence — and there is structurally no verdict slot, so the flashiest feature cannot give advice. Showcases the underused `company_contexts` RAG artifacts.
- **Target files:** new `backend/app/services/courtroom_service.py` (+ route `POST /research/courtroom` in the research-agent router), new `frontend/src/pages/CourtroomPage.jsx` + route + API function, new backend tests.
- **Current problem:** The agent layer is single-voice Q&A; grounded-evidence machinery has little product presence.
- **Desired outcome:** Deterministic mode (works with `RESEARCH_LLM_PROVIDER=none`): each persona built from templated sentences over concrete fields — Bull takes the ticker's top-percentile validated features, Bear the bottom-percentile, Skeptic embeds R2-SKEPTIC-01's report, Risk states missingness/small-n/nominal-TRY/IC evidence and always renders last. Every sentence carries a citation chip `{field, value, source_file}`. Equal evidence budget per persona (e.g. 4 items each). Optional LLM mode may only rephrase the same grounded bullets (reuse the existing explanation-only constraint in `research_agent.py`). Closing panel: fixed no-verdict copy verbatim from roadmap §3.7.
- **Step-by-step:** (1) Read `services/research_agent.py` + `services/research/` + one file from `data/trusted_clean/company_contexts/` to map available fields. (2) Persona builders as pure functions, unit-tested (given a fixture context, assert citation completeness — every sentence must resolve to a field). (3) Route + schema; PUBLIC_DEMO_MODE convention. (4) Page after R2-AUTOPSY-01 patterns; Risk panel visually persistent. (5) Claims lint on all template sentences. (6) Backend tests incl. "no verdict key exists in the response schema" as an explicit test.
- **Acceptance criteria:** Works LLM-off; every rendered sentence citation-resolvable; no verdict field anywhere in schema or UI; suites green; lint green.
- **Verification / commands:** backend pytest; `npm run build`; manual run with `RESEARCH_LLM_PROVIDER=none` recorded.
- **Dependencies:** R2-SKEPTIC-01 (embedded), VER-02, R2-CONTRACT-01 (lint the templates). **Failure modes:** rhetoric outrunning evidence (equal budgets + citation tests guard); users reading Bull as a recommendation (no-verdict design + Risk-last ordering are the mitigation). **Rollback:** revert; additive.
- **Demo after completion:** pick a ticker, run the debate, end on the Risk panel — the philosophy as product. **Do not overclaim:** never summarize a debate as "the AI thinks X is a buy." **CV impact:** very high.

### R2-UNIV-01 — Universe selection & survivorship audit
- **Priority:** P2. **Stage:** 1. **Owner role:** Research/Documentation. **Risk:** low.
- **Why this matters / weakness fixed:** `METHODOLOGY.md` Limitations openly states no survivorship/look-ahead audit of the 40-company selection exists. A ranking study with an unaudited universe has a known hole; closing or precisely characterizing it is cheap and high-credibility.
- **Target files:** `METHODOLOGY.md` (replace the limitation line with findings), possibly a short `docs/universe_audit.md` if findings are long; read-only inspection of `data/config/universe_public_40.csv`, `universe_training_bist100.csv`, `bist100_candidates.csv`, git history of those files, `data/trusted_clean/universe_split_report.json`.
- **Current problem:** Unknown whether the 40 tickers were chosen with information unavailable at window start (e.g., picked in 2025 among then-surviving, then-large companies → survivorship tilt in every metric).
- **Desired outcome:** A written audit answering: when was the universe fixed (git evidence)? by what stated criteria? were any constituents delisted/suspended in-window (check: do all 40 have prices in all years — the price coverage data already exists)? Explicit conclusion sentence, e.g. "the universe was selected in [date] from companies listed throughout 2020–2025; results therefore carry survivorship conditioning and describe *surviving* firms only" — if that's what the evidence shows.
- **Step-by-step:** (1) `git log --follow` on the three config CSVs; read commit messages. (2) Cross-check price coverage per ticker-year from the committed quality reports (do not re-run pipeline). (3) Grep TASK_STATE.md for universe-selection history. (4) Write findings with citations; keep "Needs verification" for anything git can't answer (e.g., why exactly these 40 — may be owner memory). (5) Update METHODOLOGY.md limitation to the precise, evidenced statement.
- **Acceptance criteria:** Every claim in the audit cites a file or commit; the vague limitation is replaced by a precise one; no code/data changed.
- **Verification / commands:** `git diff` docs-only; cited commits/files exist.
- **Dependencies:** none. **Failure modes:** guessing the selection rationale (forbidden — mark unknown as unknown). **Rollback:** revert docs.
- **Demo after completion:** one strong sentence for the methodology Q&A. **Do not overclaim:** documenting survivorship conditioning doesn't remove it. **CV impact:** medium-high — anticipating the sharpest reviewer question.

---

### Phase 2 compact tasks (full specs in `FINANCEIQ_MOONSHOT_ROADMAP.md` §3)

- **R2-LINEAGE-01** (Stage 1, Data/Backend, medium risk): extend `_data_dictionary()` in `scripts/data_collection/build_all.py:30` (writes `data_dictionary.md` at :46) to also emit `feature_passports.json` (per-column source class, transform chain, gates passed, caveats); backend passthrough endpoint; passport popover on `/research` Score Explorer first. Regenerate via Makefile only; hand edits to `data/trusted_clean/` remain forbidden. Verify: `make data-validate` unchanged, suites green. Popover footer: "Provenance record — not a guarantee of source accuracy."
- **R2-REGIME-01** (Stage 3, Data/Frontend, medium risk): `data/trusted_raw/macro/macro_context_yearly.csv` (CPI, policy rate, USDTRY, BIST100 — sourced, shape-validated; shares CPI file with R2-REAL-01); regime strip on `/benchmark` and `/experiments` charts; default state prominently says regime-conditional diagnostics are untestable with a single regime. Verify: builds green, no chart data altered.
- **R2-LOOP-01** (Stage 3, Backend/Frontend, medium-high risk): analyst verdict ledger on the existing Labeling/Validation Lab pages — agree/disagree/abstain + typed reason per ticker-year; new table via append-only Alembic migration; verdicts never enter score computation (pin with a test); aggregate dissent view. Read `labeling.py`/`validation.py` routers first — map what already exists before adding.
- **R2-FRICTION-01** (Stage 4, Research/Frontend, **high** risk — claim surface): friction simulator over the per-ticker `predictions_<split>.csv` files produced by R2-STAT-01 (the committed `test_*.json` hold aggregate metrics only — no baskets can be built from them); turnover + parameterized cost bps; per-year bars only, **no cumulative-wealth curves ever**; caveat stamped inside the chart canvas ("hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0"); panel lives on the Autopsy page. MCC lint mandatory. Depends: R2-STAT-01, R2-AUTOPSY-01, R2-CONTRACT-01.
- **R2-DEMO-01** (Stage 4, Documentation/Product, low risk): glass-box demo runbook building on BE-01's smoke script — scripted path runtime-status → frozen evidence → seismograph + null histogram → autopsy → skeptic/courtroom → MCC lint failure finale; with fallback branches (LLM down, backend down → labeled demo data). Commit as `docs/DEMO_RUNBOOK.md`.

**Phase 2 suggested order:** [Stage-0 gate: OPS-01, DATA-04/05, UI-01] → R2-REPRO-01 → R2-UNIV-01 → R2-STAT-01 → R2-STAT-02 → R2-CONTRACT-01 → R2-LINEAGE-01 → R2-REAL-01 → R2-SKEPTIC-01 → R2-AUTOPSY-01 → R2-CAL-01 → R2-REGIME-01 → R2-LOOP-01 → R2-COURT-01 → R2-FRICTION-01 → R2-DEMO-01.
