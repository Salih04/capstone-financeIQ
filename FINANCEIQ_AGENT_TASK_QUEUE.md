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
