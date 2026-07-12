# FINANCEIQ_AGENT_TASK_QUEUE.md

Sequenced task queue for future coding agents. Grounded in the 2026-07-08 audit (`FINANCEIQ_MODEL_VALIDITY_AUDIT.md`, `OPERATING_LAYER_VALIDATION.md`) and re-planned 2026-07-12 from direct repo inspection after the Stage-0/Stage-1/Stage-2 completions below. Every agent: read `CLAUDE.md` → `PRD.md` → `REPO_MAP.md` → `FINANCEIQ_SMALL_MODEL_RULES.md` first, then only the task's listed files.

**Universal verification (updated 2026-07-12):** after backend edits run `PYTHONPATH=backend python -m pytest backend/tests` (expect **55 pass**, or more if your task adds tests); after pipeline/test edits run `PYTHONPATH=. python -m pytest tests/` (expect **106 pass**, or more); after data edits also run `make data-validate` (expect VALID — 403 rows, 40 features, 321 target rows); after any user-facing copy or response-constant change run `make claims-lint` (expect exit 0). Rollback for all tasks: `git checkout -- <files>` before commit, `git revert` after — no task below has irreversible side effects unless its rollback note says otherwise.

**Model recommendation key** (used in every spec): **Sol** = small/fast model — docs, copy, ledger edits, verification runs. **Terra** = mid model — standard additive backend/frontend features with existing patterns to copy. **Opus** = strong model — guard-adjacent code, statistics, migrations, new services. **Fable** = frontier model — tasks where pipeline changes and claim surfaces intersect, or where a wrong judgment call creates investment-advice risk. Effort levels: low / medium / high.

---

## Phase 1 — COMPLETE (do not reopen)

All Phase-1 tasks are done and verified. Evidence ledger (commit SHAs from `git log`, states from `TASK_STATE.md` 2026-07-12 verification row and current artifacts):

| Task | Status | Evidence |
|---|---|---|
| OPS-01 stale `call_local_llm` refs | DONE | zero `call_local_llm` references remain in `tests/`/`research_agent_training/` (grep 2026-07-12); root suite 97/97 per TASK_STATE verification row |
| OPS-02 dead `unnecessary/` link | DONE | `a93bb766` |
| OPS-03 stale ledger test-count line | DONE (superseded) | VER-01 baseline row in TASK_STATE (2026-07-12); note: ledger "Last updated" header is still stale — folded into R2-GOV-01 |
| OPS-04 PRD ambiguities | DONE | `558e115e` |
| OPS-05 Settings tolerates unknown `.env` keys | DONE | `843a02ef`; backend suite now 54/54 |
| DATA-01 dictionary cross-check | DONE | `438e113e`, `DATA_01_DATA_DICTIONARY_AUDIT.md` (61/61 columns) |
| DATA-02 missing-features-reduce-confidence tests | DONE | `33697229` |
| DATA-03 malformed-CSV failure messages | DONE | `dd5f774b` |
| DATA-04 conditional DEGENERATE caveat | DONE | `854332a6` + follow-up `0ef21bf4` (generated `experiment_summary.md` path) |
| DATA-05 re-run experiments, refresh summary | DONE | `fe185e06` (environment-qualified; see `.agent/memory/02-…`) |
| DATA-06 sector audit | DONE | `0822a8ea`; METHODOLOGY §"Sector-label provenance": **`sector` is unpopulated in all trusted datasets** — no per-sector features or checks are currently possible |
| MOD-01 IC dispersion in UI | DONE | `4a9266c3` |
| MOD-02 serving heuristic documented | DONE | `c10f6b79`, METHODOLOGY §"Serving-side experimental ranking heuristic" |
| UI-01 disclaimer coverage | DONE | `5822de8e`; now contract-enforced by `make claims-lint` |
| UI-02 dataset-scope lines | DONE | `f70009c4` |
| BE-01 demo smoke check | DONE | `97e9be01` → `scripts/demo_smoke.py`, `make demo-check` |
| BE-02 fresh-DB bootstrap verification | DONE | `5db00f8d` + `773f5548`, `docs/FRESH_DATABASE_BOOTSTRAP_VERIFICATION.md` |
| VER-01 verification baseline | DONE | `ad016f64`, TASK_STATE row (root 97, backend 51→54, data VALID, build green) |
| VER-02 frontend build/e2e status | DONE | `149d8d9c` (build green; e2e not run — no backend at the time) |
| DOC-01 first repo-memory lessons | DONE | `47d1b62b`, two lessons in `.agent/memory/` |

---

# Phase 2 — Roadmap execution queue

Implements `FINANCEIQ_MOONSHOT_ROADMAP.md`. The Stage-0 gate is **satisfied**. Phase 2 is now partially complete; the remaining queue below was re-specified 2026-07-12 against the artifacts the completed tasks actually produced.

## Phase 2 completions (do not reopen)

| Task | Status | Evidence |
|---|---|---|
| R2-REPRO-01 run manifests + one-command reproduction | DONE | `74f35efe`; `experiments/results/runs/<stamp>_<sha>/manifest.json` (2 committed), `scripts/verify_run.py`, `make research-verify-run`, METHODOLOGY §"Reproducibility and run provenance" |
| R2-UNIV-01 universe & survivorship audit | DONE | `26448525`; `docs/universe_audit.md`, METHODOLOGY Limitations (retrospective cohort, 226/240 price coverage, missing years for ASTOR/CANTE/DSTKF/MIATK/PASEU) |
| R2-STAT-01 permutation + bootstrap significance | DONE | `c0c5c1d9`; `experiments/results/predictions_test_{2023,2024,2025}.csv` (ticker,year,model,y_true,y_pred; n=80/split), `experiments/significance.py`, `make research-significance`, `significance_report.{json,md}`. Headline: no ML model survives Bonferroni family-wise correction; smallest raw ML p is random forest at pooled IC **−0.153** (adj p=0.1098); equal-weight baseline pooled IC 0.150 is descriptive context **outside** the correction family |
| R2-STAT-02 power / minimum detectable IC | DONE | `a875bf67`; analytic+simulated power in the significance report: detectable \|IC\| ≈ **0.309** (one 80-row year), **0.182** (three-year design), 0.431/0.260 at public-40 scale; METHODOLOGY §"Power and detectability limits", claims guide §11 |
| R2-CONTRACT-01 Model Confidence Contract v1 + claims lint | DONE | `28ba92b2`; `model_confidence_contract.json` (v1.0.0), `scripts/lint_claims.py`, `make claims-lint`, backend contract test |
| R2-GOV-01 truth sync + experiment-artifact governance | DONE (uncommitted) | 2026-07-12; observed root 106/106, backend 55/55, data VALID; truth-sync and run-directory governance docs updated |
| R2-CONTRACT-02 MCC coverage drift guard + versioning procedure | DONE (uncommitted) | 2026-07-12; `model_confidence_contract.json` v1.1.0, recursive JSX scan, explicit auth exemptions, root route-coverage guard, and MCC versioning procedure; commit deferred by request |
| R2-LINEAGE-01 feature passports | DONE (uncommitted) | 2026-07-12; generated `feature_passports.json` covers 61/61 columns, read-only API passthrough, Score Explorer passport popover; root 111/111, backend 57/57, data VALID, frontend build and claims lint passed; commit deferred by request |
| R2-SKEPTIC-01 skeptic challenge service | DONE (uncommitted) | 2026-07-12; deterministic cached six-check `/research/skeptic/{ticker}` report, structured evidence citations and insufficient-data handling, MCC v1.2.0; root 111/111, backend 67/67, claims lint and live ASELS/ASTOR checks passed; commit deferred by request |
| R2-AUTOPSY-01 Negative Alpha Autopsy | DONE (uncommitted) | 2026-07-12; six artifact-backed exhibits at `/autopsy`, typed `/research/significance/autopsy` passthrough, explicit source/limitation labels, MCC v1.3.0; root 114/114, backend 69/69, frontend build and claims lint passed; live API passed, page visual blocked by missing approved Supabase session; commit deferred by request |

## Universal rules for remaining Phase-2 tasks

- Every new evaluation output goes to a **new, separately named** artifact/directory — never overwrite `experiments/leaderboard.csv`, `experiments/results/significance_report.*`, `experiments/results/predictions_test_*.csv`, or anything in `data/trusted_clean/` except via existing Makefile regeneration.
- Any task that re-runs `make research` must first record `shasum experiments/leaderboard.csv` and confirm it is unchanged afterward; drift = STOP and report (see `.agent/memory/02-environment-qualified-experiment-reruns.md` — byte reproduction is environment-qualified).
- Every new UI surface: (a) its caveat copy is specified **in the task below, verbatim** — wording changes require editing this file first; (b) the new page path must be added to `model_confidence_contract.json` `required_disclaimer.pages` (contract version bump per R2-CONTRACT-02 procedure); (c) `make claims-lint` must pass; (d) any new backend service that ships user-facing response copy must be added to the contract's `scan.backend_response_files`.
- New Makefile targets are additive; renames remain forbidden.
- New data series (CPI, USDTRY, macro) follow the manual-CSV pattern of `data/trusted_raw/shares_outstanding_events.csv`: sourced, dated, shape-validated, null-if-missing, never imputed.
- No new paid dependencies. Python additions must be stdlib/numpy/pandas/scikit-learn (already present); frontend additions must use existing dependencies.
- The prediction dumps evaluate the **81-ticker training universe (n=80 rows per split)**, not the public 40. Any surface built on them must label the universe explicitly; do not describe dump-derived numbers as "the public 40."
- The equal-weight baseline's pooled IC 0.150 (unadjusted p=0.0168) is the single most misquotable number in the repo. It is descriptive context outside the ML correction family. **No task may surface it without the exact qualifier sentence from METHODOLOGY** ("reported as descriptive baseline context outside the six-model ML correction family, not as a validated edge").

---

### R2-GOV-01 — Truth sync + experiment-artifact governance
- **Priority:** P1. **Stage:** 1 (hygiene). **Owner role:** Documentation/Verification. **Risk:** low.
- **Why this matters:** Three docs now lag the repo they describe, which is exactly the drift failure mode this project treats as a cardinal sin. Also, `experiments/results/runs/` will accumulate one directory per `make research` forever with no stated retention or which-manifest-is-of-record policy.
- **Current evidence:** `CLAUDE.md` "Known test-suite state" still says root 95/97 with `call_local_llm` failures — but zero such references remain (grep 2026-07-12) and TASK_STATE's verification row records 97 passed. `TASK_STATE.md` header still says "Last updated: 2026-06-11 (rev 6)" and has **no rows for any R2-\* completion**. Two run dirs are committed under `experiments/results/runs/` with no governance note anywhere.
- **Target files:** `CLAUDE.md` (test-state note only), `TASK_STATE.md` (header + new Phase-2 rows), `METHODOLOGY.md` (≤ 10-line "Run-directory governance" note under the existing Reproducibility section), optionally one `.agent/memory/` lesson.
- **Steps:** (1) Re-run both suites and `make data-validate`; record honest counts. (2) Update CLAUDE.md's "Known test-suite state" block to the observed state (do not delete the `backend/.env` gotcha history — mark it resolved by OPS-05). (3) Add TASK_STATE rows: R2-REPRO-01/UNIV-01/STAT-01/STAT-02/CONTRACT-01 with dates + SHAs from the ledger above; refresh the "Last updated" header. (4) Write the governance note: the manifest whose SHA matches the committed `leaderboard.csv` is the **manifest of record**; superseded run dirs may be deleted only in the same commit that replaces the leaderboard; never hand-edit a manifest. (5) Optional memory lesson if a new trap was confirmed.
- **Acceptance criteria:** No doc claims a test count that a fresh run contradicts; every completed R2 task has a ledger row; the run-retention rule exists in exactly one place.
- **Verification commands:** `PYTHONPATH=. python -m pytest tests/`; `PYTHONPATH=backend python -m pytest backend/tests`; `make data-validate`; `git diff` docs-only.
- **Generated artifacts:** none.
- **Claim-safety:** prose only; no numbers beyond observed test output; `make claims-lint` unaffected but run it anyway (docs are outside its scan — note that in your report, not as a lint pass).
- **Failure modes:** "fixing" a count without running the suite (forbidden — run it); rewriting ledger history instead of appending.
- **Rollback:** revert the doc edits.
- **Demo value:** low. **Research value:** medium (provenance discipline). **CV value:** low directly, but protects everything else.
- **Model/effort:** **Sol, low.** **Commit:** yes (docs). **/clear after:** yes.

### R2-STAT-UI-01 — The Instrumented Null panel (significance + power into the product)
- **Priority:** P1. **Stage:** 2→3 bridge. **Owner role:** Backend/Frontend. **Risk:** medium (claim surface).
- **Why this matters:** The project's strongest new evidence — permutation p-values, bootstrap CIs, power thresholds, null histograms — exists only as committed files and METHODOLOGY prose. `grep -rn "significance\|permutation\|power\|detectable" frontend/src/pages/` returns **nothing** (verified 2026-07-12). The single most persuasive artifact (observed IC inside its null distribution) is invisible in the product. This was the roadmap's whole point ("turn the negative result from a sentence into an instrument") and it is currently half-done: instrumented, not displayed.
- **Current evidence:** `experiments/results/significance_report.json` (keys: `analysis`, `headline`, `limitations`, `models`, `power_analysis`, `schema_version`, `source_artifacts`; METHODOLOGY states null histograms are included). `ExperimentsPage.jsx` already shows per-split IC dispersion (MOD-01, `4a9266c3`) — the natural host.
- **Target files:** new read-only endpoint in `backend/app/routers/research.py` + a small loader in `backend/app/services/research/` (read the subpackage's existing CSV/JSON access + caching patterns first and copy them; both `research.py` and `research_agent.py` mount under `/research` — check prefixes, never assume); new backend test; `frontend/src/pages/ExperimentsPage.jsx` (extend — no new page); `frontend/src/api/researchApi.js`.
- **Steps:** (1) Read `significance_report.json` structure fully; design the endpoint as a filtered passthrough (headline + per-model {pooled IC, CI, raw p, adjusted p, null-histogram bins} + power_analysis + limitations) — no server-side statistics, ever. (2) Backend test pinning response shape and the presence of `limitations`. (3) Frontend panel on ExperimentsPage in the Research Terminal language: per-model strip with pooled IC dot inside its bootstrap CI bar; one null-distribution histogram (canvas/SVG with existing deps) with the observed IC marked; a power footer line. (4) Demo fallback per the page's existing conventions (labeled, fallback-only). (5) Copy (verbatim, changes require editing this spec): headline — "**No ML model is statistically distinguishable from the within-year null after family-wise correction.**"; power footer — "**This design could only detect |IC| ≥ 0.182 (three-year, 80-row design; 0.309 for a single year) at 80% power — a design limit, not an estimate of the true IC.**"; baseline row, if shown, must carry the METHODOLOGY qualifier sentence verbatim; per-split values, if shown, labeled "**exploratory — SE ≈ 0.16 at this n**". (6) Run `make claims-lint`; add contract allowlist entries only for method-description lines, with review reasons.
- **Acceptance criteria:** Panel renders real report data with backend up and labeled fallback without; no number on the panel differs from `significance_report.json`; backend suite green +new tests; `npm run build` green; `make claims-lint` exit 0; the panel never renders a p-value without its adjusted companion.
- **Verification commands:** `PYTHONPATH=backend python -m pytest backend/tests`; `cd frontend && npm run build`; `make claims-lint`; manual `npm run dev` visual check recorded (screenshot in report).
- **Generated artifacts:** none (reads committed reports).
- **Claim-safety:** the raw-vs-adjusted pairing rule above is mandatory; forbidden framings: "statistically significant" applied to any ML model, any presentation of the baseline as an edge, any "proves market efficiency" phrasing.
- **Failure modes:** cherry-rendering the random-forest raw p=0.0183 without the adjusted 0.1098 (this is the exact multiple-comparisons trap the report exists to prevent); recomputing statistics in JS (forbidden — display only); fallback data drifting from real data shape.
- **Rollback:** revert; purely additive.
- **Demo value:** very high — the null histogram is the project's best single slide, now live in the product. **Research value:** high. **CV value:** very high.
- **Model/effort:** **Terra, medium** (patterns exist to copy; the judgment calls are pre-made in this spec). **Commit:** yes. **/clear after:** yes.

### R2-CONTRACT-02 — MCC coverage drift guard + versioning procedure
- **Priority:** P1. **Stage:** 2 hardening. **Owner role:** Backend/Product. **Risk:** low-medium.
- **Why this matters:** MCC v1.0.0 is a tripwire with a blind spot: its `required_disclaimer.pages` list is a hand-maintained snapshot of today's 21 pages, and its scan covers `frontend/src/pages/*.jsx` plus exactly one backend file. Every remaining Phase-2 task adds pages (Autopsy, Courtroom) or copy-bearing services (Skeptic, Courtroom) — without a drift guard, the contract silently stops covering the newest, riskiest surfaces. This task makes the contract self-policing before those surfaces exist.
- **Current evidence:** `model_confidence_contract.json` `required_disclaimer.pages` (17 pages + 2 route aliases); `scan.backend_response_files` = `[forecasting_csv_service.py]`; `frontend/src/components/` contains copy-bearing components (`TerminalFx.jsx` caveat strips, `layout/`) that are entirely outside the scan; contract `limitations` already admit the scope gap.
- **Target files:** new root test `tests/test_contract_coverage.py` (or backend test — pick where App.jsx parsing fits better; justify in report), `model_confidence_contract.json` (version bump to 1.1.0), `scripts/lint_claims.py` (only if the glob extension needs code), `METHODOLOGY.md` §MCC (≤ 8 lines on the version procedure).
- **Steps:** (1) Write the drift test: parse `frontend/src/App.jsx` route elements → every routed page component file must appear in the contract's `pages` or `route_aliases` (allow an explicit `exempt_pages` contract key for non-data pages like `LoginPage.jsx`/`AuthCallbackPage.jsx` — add it, with reasons per entry). The test fails when someone adds a route without registering it. (2) Extend the lint scan glob to `frontend/src/components/**/*.jsx`; run it; report violations as findings and add allowlist entries only for legitimate lines (each with a reason). Fix nothing silently. (3) Document the version procedure in the contract itself and METHODOLOGY: any change to `rules`, `scan`, `pages`, or `evidence_state` bumps minor version + `effective_date`; allowlist-only line-number refreshes bump patch. (4) Bump to 1.1.0.
- **Acceptance criteria:** Deliberately adding a fake route to App.jsx (test-local fixture or temp mutation, reverted) makes the drift test fail; component-dir scan is green or has a committed findings list; both suites green; `make claims-lint` exit 0.
- **Verification commands:** `PYTHONPATH=. python -m pytest tests/` (or backend suite, per placement); `make claims-lint`; mutation check recorded.
- **Generated artifacts:** none.
- **Claim-safety:** this task *is* claim safety; it must not weaken any existing rule or remove allowlist review reasons.
- **Failure modes:** regex-parsing App.jsx too cleverly (keep it dumb: match `element={<X` + import paths; if the file's structure defeats simple parsing, STOP and report rather than building a JSX parser); exempting a data-bearing page.
- **Rollback:** revert; the contract file and test are self-contained.
- **Demo value:** medium (extends the "watch the lint fail" demo). **Research value:** medium. **CV value:** high — "self-policing claims governance" is a genuinely original line.
- **Model/effort:** **Terra, medium.** **Commit:** yes. **/clear after:** yes.

### R2-LINEAGE-01 — Feature Passports (per-column lineage, machine-readable)
- **Priority:** P2. **Stage:** 1 (last Stage-1 item). **Owner role:** Data/Backend/Frontend. **Risk:** medium (touches the dictionary generator).
- **Why this matters:** The pipeline's lineage story (accepted/rejected machinery, frozen evidence, ingestion reports) is scattered across seven report files. A per-column passport makes "every value is real, sourced, and auditable" a clickable fact, and gives DATA-01's drift problem a durable structural fix — the passport is generated from the same load that validation runs on.
- **Current evidence:** `_data_dictionary()` at `scripts/data_collection/build_all.py:30`, called at `:89`; since DATA-01 (`438e113e`) it regenerates in **both** build and `--validate-only` modes from the loaded dataset — the passport generator inherits that property for free. Dataset has **61 columns** (40 features + targets/metadata; `DATA_01_DATA_DICTIONARY_AUDIT.md`). Role/leakage facts come from `scripts.data_collection.validate.feature_registry`; caveat facts from `data_quality_report.md` / `frozen_column_evidence.md`.
- **Target files:** `scripts/data_collection/build_all.py` (extend `_data_dictionary()` to also emit `data/trusted_clean/feature_passports.json`); new root test `tests/test_feature_passports.py`; backend passthrough endpoint (likely `research.py` router + `services/research/` loader — read first); backend test; `frontend/src/pages/ResearchPage.jsx` (Score Explorer popover, first surface only).
- **Steps:** (1) Read `build_all.py` and `validate.py`'s feature_registry fully. (2) Passport schema per column: `{name, registry_role, source_class (vendor_xlsx|corrected_yearly_csv|yahoo_fetch|manual_shares|derived|metadata), transform_chain (short strings), leakage_risk, acceptance_status, caveats[], evidence_files[]}` — every field must be derivable from existing registry/reports; **if a source class cannot be determined from code/reports, emit `"unknown"` — never guess.** (3) Emit inside `_data_dictionary()` so dictionary and passports can never diverge; regenerate via `make data-validate`. (4) Root test: passport count == dataset column count; every passport role matches feature_registry; no `caveats` invented (spot-pin frozen columns cite `frozen_column_evidence`). (5) Backend passthrough endpoint + shape test. (6) Popover on Score Explorer feature rows with footer (verbatim): "**Provenance record — documents source and validation path, not a guarantee of source accuracy.**" (7) `make claims-lint` (popover copy is in a scanned page).
- **Acceptance criteria:** `make data-validate` still VALID with unchanged counts; `feature_passports.json` regenerates deterministically (run twice, identical); dictionary markdown byte-identical to before (or the diff is explained and confined to generation-order artifacts — report it); suites green +new tests; popover renders real passports with backend up.
- **Verification commands:** `make data-validate` ×2 + `shasum data/trusted_clean/feature_passports.json` between runs; `PYTHONPATH=. python -m pytest tests/`; `PYTHONPATH=backend python -m pytest backend/tests`; `cd frontend && npm run build`; `make claims-lint`.
- **Generated artifacts:** `data/trusted_clean/feature_passports.json` (generated — never hand-edit; regenerate via Makefile only).
- **Claim-safety:** the footer above is mandatory; passports must not describe any feature as "predictive" (registry roles are the vocabulary).
- **Failure modes:** inventing source classes for ambiguous columns (use `"unknown"`); the generator accidentally changing the dictionary's existing content; hand-editing the JSON to fix a wrong passport (forbidden — fix the generator).
- **Rollback:** revert code **and** the generated JSON together; dictionary must be re-verified after revert.
- **Demo value:** high (click any feature → its passport). **Research value:** medium-high. **CV value:** high — "feature-store-grade lineage on a no-fabrication pipeline."
- **Model/effort:** **Opus, medium-high** (touches the generator that guards data truth). **Commit:** yes. **/clear after:** yes.

### R2-SKEPTIC-01 — Skeptic Agent service + challenge report endpoint (revised checks)
- **Priority:** P2. **Stage:** 3. **Owner role:** Backend/Agent. **Risk:** medium.
- **Why this matters:** Operationalizes self-skepticism: every ranking gets attacked before a human sees it. **Revision vs the original spec:** the planned sector-concentration check is impossible — DATA-06 established that `sector` is unpopulated in every trusted dataset (METHODOLOGY §Sector-label provenance). It is replaced by a cohort-integrity check built on the universe audit, which is both feasible and sharper.
- **Current evidence:** all six checks below run on committed artifacts that now exist: `data/trusted_clean/data_quality_report.{md,json}`, `frozen_column_evidence.{md,json}`, the modeling CSVs, `experiments/results/predictions_test_*.csv` (per-model per-ticker, n=80/split), `experiments/results/significance_report.json`, `docs/universe_audit.md` (price-coverage gaps: ASTOR 2020-22, CANTE 2020, DSTKF 2020-24, MIATK 2020, PASEU 2020-23).
- **Target files:** new `backend/app/services/skeptic_service.py`; route in `backend/app/routers/research.py` **or** `research_agent.py` (read both first — both mount `/research`; place it beside the closest existing evidence-serving pattern and justify); new `backend/tests/test_skeptic_service.py`; `model_confidence_contract.json` (`scan.backend_response_files` += the new service; version bump per R2-CONTRACT-02). Frontend panel is a **separate later task** — do not build UI here.
- **The six checks** (each a pure function returning `{check_id, verdict: pass|warn|fail|insufficient_data, evidence: [{fact, source_file}], severity}`):
  1. **Staleness/frozen probe** — does any input to this ticker's display derive from a column listed in `frozen_column_evidence.json`? (Should be none — that's the point of proving it per-ticker.)
  2. **Missingness attack** — fraction of the ticker's feature columns populated in its latest row; warn below a threshold **taken from `data_quality_report`'s coverage stats, cited, or explicitly labeled `heuristic` in the response**.
  3. **Instability probe** — from the prediction dumps: does the ticker's within-year predicted rank flip across models/splits by more than half the field? Deterministic, computed once and cached following existing service caching patterns.
  4. **Cohort-integrity challenge** (replaces sector check) — cites `docs/universe_audit.md`: retrospectively fixed cohort, survivorship risk, and per-ticker price-coverage gaps (fail→warn for the five gap tickers listed above).
  5. **Universe-scale reminder** — n=40 public / n=80 evaluated rows per split; any rank difference smaller than the power-analysis detectable band is unresolvable (cite `significance_report.json` power numbers).
  6. **Backtest reminder** — always present, always last: no ML model survives family-wise correction (cite the report's headline verbatim).
- **Fixed footer (verbatim, mandatory):** "**Surviving these checks means *not obviously broken*, not *predictive* — walk-forward IC remains ≈ 0 and no model survives family-wise correction.**"
- **Steps:** (1) Read `services/research_agent.py` + `services/research/` loaders — reuse path/env handling (`RESEARCH_REPO_ROOT`) and caching. (2) Implement checks as pure functions over loaded artifacts; unit-test each on fixtures (a sparse ticker, a coverage-gap ticker like ASTOR, a stable ticker). (3) `GET /research/skeptic/{ticker}` returning `{ticker, checks[], footer}`; structured `insufficient_data` verdicts for missing inputs — never fabricated. (4) Respect `PUBLIC_DEMO_MODE` read-open convention. (5) Response-shape contract test. (6) Contract update + `make claims-lint`.
- **Acceptance criteria:** Backend suite green +new tests; real evidence for a real ticker (record `curl` output for ASELS and one coverage-gap ticker, e.g. ASTOR); every `evidence` item resolves to an actual file; no score computation altered anywhere; lint green after contract update.
- **Verification commands:** `PYTHONPATH=backend python -m pytest backend/tests`; `make claims-lint`; manual `curl localhost:8000/research/skeptic/ASELS` recorded.
- **Generated artifacts:** none.
- **Claim-safety:** the footer is non-negotiable; "pass" verdicts must never be describable as validation (check the response's wording against the contract's forbidden patterns).
- **Failure modes:** inventing thresholds (each is cited or labeled heuristic); heavy per-request recomputation (cache like existing services); resurrecting the sector check (impossible — evidence above).
- **Rollback:** revert; purely additive.
- **Demo value:** very high — the system prosecutes its own ranking. **Research value:** high (the instability probe surfaces real per-ticker noise). **CV value:** very high.
- **Model/effort:** **Opus, high.** **Commit:** yes. **/clear after:** yes.

### R2-AUTOPSY-01 — Negative Alpha Autopsy page (six exhibits, all real numbers)
- **Priority:** P2. **Stage:** 3. **Owner role:** Frontend/Research. **Risk:** medium.
- **Why this matters:** The negative result is displayed but never *explained*. Every exhibit's numbers now exist in committed artifacts — including power and significance, which were "pending" in the original spec. This page converts "it failed" into "here is the anatomy of why," the project's best interview surface.
- **Current evidence:** `experiments/results/feature_stability_by_split.csv`, `feature_stability_summary.csv`, `coverage_impact.csv`, `leaderboard.csv` (trees negative IC in all three splits), `significance_report.json` (incl. power + null histograms), METHODOLOGY regime prose. Build known green (VER-02).
- **Target files:** backend read-only endpoint(s) serving the three stability/coverage CSVs as JSON (reuse/extend the R2-STAT-UI-01 significance endpoint rather than duplicating it); new `frontend/src/pages/AutopsyPage.jsx` + route in `frontend/src/App.jsx` + API functions in `frontend/src/api/researchApi.js`; `model_confidence_contract.json` (add the page to `required_disclaimer.pages`; version bump); backend tests.
- **The six exhibits** (each: one chart + one finding paragraph that distinguishes "consistent with" from "proves"):
  1. **Instability** — feature-weight sign flips across splits (`feature_stability_by_split.csv`).
  2. **Overfit** — baseline-vs-tree IC bars; trees consistently negative (`leaderboard.csv`).
  3. **Sparsity** — coverage impact (`coverage_impact.csv`).
  4. **Significance** — the multiple-comparisons lesson, stated plainly: *the smallest raw p-value in the model family belongs to random forest at pooled IC **−0.153** — the most "significant" model is significantly bad before correction, and nothing survives after it.* (From `significance_report.json`; both raw and adjusted p shown together, always.)
  5. **Power** — minimum detectable |IC| 0.182/0.309 (80-row design) with the design-limit framing sentence from METHODOLOGY verbatim.
  6. **Regime** — single extraordinary macro regime, 2020–2025; regime robustness untestable (statement, no fake chart).
- **Page caveat strip (verbatim, from roadmap §3.5):** "**This page documents evidence consistent with why no reliable signal was found: unstable feature relationships, overfitting under small n, sparse coverage, low statistical power, and a single macro regime. It explains the negative result; it does not promise a positive one under other conditions.**" Plus the standard research-support disclaimer.
- **Steps:** (1) Read `ExperimentsPage.jsx` fully — copy data-fetch/fallback/caveat patterns exactly. (2) Backend CSV→JSON endpoints + tests (no computation server-side beyond parsing). (3) Page in the Research Terminal language; universe labels per the universal rule (dump-derived exhibits say "81-ticker training universe, n=80/split"). (4) Route + nav wiring; contract page registration; `make claims-lint`. (5) `npm run build`; visual check with backend running; screenshot in report.
- **Acceptance criteria:** All six exhibits render real artifact data with backend up, labeled fallback without; no number differs from its source file; no existing page modified beyond nav; suites + build + lint green.
- **Verification commands:** `PYTHONPATH=backend python -m pytest backend/tests`; `cd frontend && npm run build`; `make claims-lint`; visual check recorded.
- **Generated artifacts:** none.
- **Claim-safety:** exhibit 4's raw/adjusted pairing rule is mandatory; no exhibit may claim causal knowledge ("consistent with," never "because").
- **Failure modes:** over-narration; inventing a regime chart (exhibit 6 is deliberately a statement); duplicating the significance endpoint instead of reusing it.
- **Rollback:** revert; additive.
- **Demo value:** very high — likely the strongest 3 minutes of any demo. **Research value:** very high. **CV value:** very high.
- **Model/effort:** **Opus, high** (Terra acceptable if R2-STAT-UI-01's endpoint landed first and is reusable as-is). **Depends:** R2-STAT-UI-01 (endpoint reuse), R2-CONTRACT-02 (registration procedure). **Commit:** yes. **/clear after:** yes.

### R2-CAL-01 — Confidence calibration bench
- **Priority:** P2. **Stage:** 3. **Owner role:** Research. **Risk:** medium.
- **Why this matters:** The hybrid score's 0.20 confidence component is displayed but never evaluated — the one place the project's own honesty standard isn't yet met. Whatever the bench finds, publishing it (rather than tuning it) is the product feature.
- **Current evidence:** per-row confidence is **not persisted** historically (`experiments/results/research_agent_model_outputs.csv` carries `ml_score`/`ml_rank` only — verified in roadmap §3.12); model ranks per ticker-year are now available from `predictions_test_*.csv`; realized returns are in the modeling CSVs (targets only — this is meta-evaluation on past rows, no leakage concern).
- **Target files:** new `experiments/calibration_bench.py`; new outputs `experiments/results/calibration_report.{json,md}`; additive Makefile target (e.g. `research-calibration`); `METHODOLOGY.md` findings paragraph; new root test.
- **Steps:** (1) Read `forecasting_csv_service.py` and `research_agent.py` confidence computation fully; decide which confidence quantity is actually user-facing and bench that one (state the choice + code refs in the report). (2) **Replay** the service on historical rows to obtain per-row confidence; record replay date, git SHA, and code version in the report — replayed confidence describes *today's code* on past rows, and the report must say so. (3) Join with realized returns; rank error = |predicted rank − realized rank| within year; bin by confidence decile; monotonicity check (seeded, deterministic); emit a plot-ready CSV inside the report dir. (4) Commit a plain verdict sentence, whichever way it points: "confidence is / is not informative about rank error at this scale." (5) METHODOLOGY paragraph quoting the report. (6) If uncalibrated: file a follow-up owner-decision task in this queue; **do not tune confidence on the same rows** (meta-overfitting is the named failure).
- **Acceptance criteria:** Report committed; rerun → byte-identical (seeded); verdict sentence matches the numbers; **no service code changed**; root suite green +new test; `make data-validate` untouched.
- **Verification commands:** `PYTHONPATH=. python -m pytest tests/`; run the new target twice + `shasum` both report files; `git diff` shows no `backend/app/services/` change.
- **Generated artifacts:** `experiments/results/calibration_report.{json,md}` + plot CSV (new dir/file names only; never overwrite existing results).
- **Claim-safety:** "calibrated" may appear only if measured so; the METHODOLOGY paragraph must carry "audited as of run X" framing; UI copy changes (if any needed) are a separate task gated by the contract.
- **Failure modes:** replay mismatch presented as historical truth (the replay-date framing is the fix); quiet recalibration (forbidden); binning so coarse the verdict is vacuous (use deciles over the 321 target rows; if bins are too thin, report that as the finding).
- **Rollback:** delete the new files; nothing else touched.
- **Demo value:** high — an *audited* confidence number is rarer than a good one. **Research value:** very high. **CV value:** high.
- **Model/effort:** **Opus, medium-high.** **Commit:** yes. **/clear after:** yes.

### R2-REAL-01 — Real-terms & USD return targets (parallel evaluation)
- **Priority:** P2. **Stage:** 2 (last Stage-2 item). **Owner role:** Data/Research. **Risk:** **high** (touches pipeline + creates quotable numbers).
- **Why this matters:** Nominal TRY targets in a hyperinflation window are the biggest interpretability weakness (2022 benchmark ≈ +186% nominal). Whether the null holds in real/USD terms is open and answerable; either answer strengthens the thesis — but only with the significance machinery (now built) applied before anything is quoted.
- **Current evidence:** `build_panel_for_target()` exists at `experiments/run_experiments.py:296` (re-verify — the file grew since the roadmap cited :115); the manual-CSV validation pattern lives in the shares/corrected-balance-sheet ingestion; `make research-significance` machinery is reusable per target basis; Yahoo fetch pattern in `scripts/fetch_yahoo_chart_prices.py`.
- **Target files:** new `data/trusted_raw/macro/cpi_yearly_tr.csv` (≤ 6 rows, TÜİK annual CPI, source + retrieval date in a sidecar `.md`); USDTRY year-end via a new small fetch script mirroring the existing Yahoo pattern; new `scripts/data_collection/derive_alternative_targets.py`; new output `data/trusted_clean/modeling_targets_alternative.csv` + `alternative_targets_report.{json,md}` (**separate CSV — the main dataset stays byte-identical**); additive Makefile targets; harness runs into `experiments/results_real_terms/`; root tests; `METHODOLOGY.md` comparison paragraph.
- **Steps:** (1) Read `build_all.py`, `validate.py`, and the shares ingestion for the validation pattern. (2) CPI CSV with citation; shape-validate like `corrected_balance_sheet_2024.csv`. (3) USDTRY fetch (free Yahoo, same source class). (4) Derivation stage with formulas in the docstring — real = (1+nominal)/(1+CPI)−1; USD = (1+nominal)·FX_T/FX_{T+1}−1 — **verify FX direction against a hand-computed 2022 example pinned in a test**. Missing CPI/FX year → null target, never interpolated. (5) Tests: null propagation, formula correctness, byte-identity of all existing `data/trusted_clean/` outputs. (6) Run the harness per basis via `build_panel_for_target`; if it cannot point at the alternative CSV without touching metric code, **STOP and report the minimal refactor** rather than improvising. (7) Run the significance machinery per basis into the new results dir. (8) METHODOLOGY paragraph quoting per-basis pooled ICs **with their corrected p-values, never without**.
- **Acceptance criteria:** `make data-validate` unchanged (403/40/321); `shasum` of the main modeling CSV identical before/after; `shasum experiments/leaderboard.csv` identical; new report + results dirs exist; root suite green +new tests; no imputation (test-pinned).
- **Verification commands:** `make data-validate`; the two `shasum` checks; `PYTHONPATH=. python -m pytest tests/`; new Makefile targets end-to-end; `make claims-lint` (METHODOLOGY is outside its scan — human-review the paragraph against the do-not-claim register instead, and say so).
- **Generated artifacts:** the alternative-targets CSV + report (generated; regenerate via Makefile only); `experiments/results_real_terms/` (new, separate; never merged into headline outputs).
- **Claim-safety:** roadmap §6 row applies verbatim — a lucky real-terms split must never become "we found signal in real terms"; every quoted basis result carries its significance treatment; the nominal-vs-real 2022 comparison is an inflation illustration, not a performance statement.
- **Failure modes:** FX direction inverted (hand-checked test guards); CPI vintage/base-year error (cite the exact TÜİK series in the sidecar); headline outputs drifting (shasum gates); promotion of an uncorrected per-split IC.
- **Rollback:** revert code + delete new generated dirs; main outputs untouched by design.
- **Demo value:** high ("+186% nominal was not a bull market"). **Research value:** high. **CV value:** high — inflation-aware evaluation shows domain maturity.
- **Model/effort:** **Fable, high** — pipeline guards, new data series, and a new quotable claim surface intersect here; this is the queue's highest-judgment task. **Commit:** yes. **/clear after:** yes.

### R2-REGIME-01 — Regime Lens (macro context strip; honest "untestable" default)
- **Priority:** P3. **Stage:** 3. **Owner role:** Data/Frontend. **Risk:** medium.
- **Why this matters:** Regime homogeneity is a hard limitation currently buried in prose. The lens makes the limitation itself the visible, taught concept — and creates the slot future data plugs into.
- **Current evidence:** audit §8; METHODOLOGY limitations; R2-REAL-01 creates `data/trusted_raw/macro/` and the CPI series this task shares.
- **Target files:** extend `data/trusted_raw/macro/` with `macro_context_yearly.csv` (CPI — shared file with R2-REAL-01, do not duplicate it — plus policy rate, USDTRY, BIST100 yearly return; each value sourced + dated in a sidecar, null if unsourced); backend passthrough endpoint; a regime-strip component used on `BenchmarkPage.jsx` and `ExperimentsPage.jsx` charts; tests.
- **Steps:** (1) After R2-REAL-01 lands, extend (not duplicate) the macro CSV with the extra columns; shape-validate. (2) Passthrough endpoint + test. (3) Strip component rendering the macro series under existing time-axis charts **without altering any chart data**; prominent default statement (verbatim): "**2020–2025 spans a single extraordinary Turkish macro regime (high inflation, deep TRY depreciation). Model behavior across regimes is therefore untested — this lens shows regime context and will only compute regime-conditional diagnostics when regime diversity exists.**" (4) Contract registration for any new copy; lint.
- **Acceptance criteria:** Charts' underlying data unchanged (diff the fetch payloads); builds + suites + lint green; every macro value carries a source or is null.
- **Verification commands:** `cd frontend && npm run build`; backend pytest; `make claims-lint`.
- **Generated artifacts:** the macro CSV (manual raw input, not generated — hand-maintained under `data/trusted_raw/`, which is the one place manual files live).
- **Claim-safety:** no per-regime statistics of any kind while one regime exists (a "per-regime" number would be a re-labeled aggregate — the named trap).
- **Failure modes:** fabricating a policy-rate value to fill a year (null instead); the strip visually implying causation between macro moves and IC.
- **Rollback:** revert; additive.
- **Demo value:** medium-high. **Research value:** high (thesis framing). **CV value:** medium-high.
- **Model/effort:** **Terra, medium.** **Depends:** R2-REAL-01 (shared macro file). **Commit:** yes. **/clear after:** yes.

### R2-LOOP-01 — Analyst-in-the-loop dissent ledger
- **Priority:** P3. **Stage:** 3. **Owner role:** Backend/Frontend. **Risk:** medium-high (only Alembic-touching task).
- **Why this matters:** Converts the under-explained Labeling/Validation Lab pages into a real research workflow, and creates the only ethically clean use of human judgment here: measuring disagreement, never overriding scores.
- **Current evidence:** `LabelingLabPage.jsx` / `ValidationLabPage.jsx` exist with routers `labeling.py` / `validation.py`; both pages carry the standard disclaimer (contract allowlist confirms); no verdict persistence exists.
- **Target files:** read `labeling.py`/`validation.py` + both pages fully first — map what already exists before adding; new Alembic migration (append-only — new table `analyst_verdicts`: ticker, year, verdict agree|disagree|abstain, reason_type enum, free-text note, user, timestamp); new endpoints; minimal UI addition on the existing pages; aggregate dissent view (simple table first); tests including the **pin test: verdicts never enter any score computation** (assert scoring service outputs are identical with and without verdict rows).
- **Steps:** (1) Map existing surface. (2) Migration + model + endpoints (auth per existing conventions; writes require auth even in demo mode — read how other write endpoints gate). (3) UI verdict controls + dissent aggregate. (4) The score-isolation pin test. (5) Ledger copy (verbatim): "**Records disagreement for research; never a score input.**" (6) Contract registration + lint.
- **Acceptance criteria:** Backend suite green +tests; migration applies on a scratch DB (`alembic upgrade head` transcript recorded per BE-02's pattern); pin test proves score isolation; lint green.
- **Verification commands:** `PYTHONPATH=backend python -m pytest backend/tests`; scratch-DB migration transcript; `cd frontend && npm run build`; `make claims-lint`.
- **Generated artifacts:** none (DB schema change).
- **Claim-safety:** aggregated verdicts must never be presented as a crowd signal; the ledger copy above is mandatory on every dissent view.
- **Failure modes:** migration edited after commit (append-only, forever); verdicts leaking into any ranking path (the pin test is the tripwire); building a rich UI before the schema is right.
- **Rollback:** **special** — before commit, `git checkout` + drop the scratch table; after commit, a new *down*-migration via `git revert` is not enough — write a follow-up migration; flag this in the task report.
- **Demo value:** medium. **Research value:** high. **CV value:** medium-high.
- **Model/effort:** **Opus, high** (the migration + auth surface demands it). **Commit:** yes. **/clear after:** yes.

### R2-COURT-01 — Research Courtroom (deterministic core, no verdict slot)
- **Priority:** P3. **Stage:** 4. **Owner role:** Agent/Frontend. **Risk:** medium-high.
- **Why this matters:** The signature demo: four personas debate a ticker using only cited, validated evidence — and there is structurally no verdict slot, so the flashiest feature cannot give advice.
- **Current evidence:** `services/research_agent.py` (explanation-only LLM constraint, deterministic fallback), `services/research/` evidence loaders, `make build-company-contexts` target exists. **Prerequisite check:** verify `data/trusted_clean/company_contexts/` exists in the worktree; if absent, generate via the Makefile target (generated artifact — regeneration is the allowed path) and record it.
- **Target files:** new `backend/app/services/courtroom_service.py` + `POST /research/courtroom` route (router choice per Skeptic's precedent); new `frontend/src/pages/CourtroomPage.jsx` + route + API function; backend tests; contract updates (page + service registration; version bump).
- **Design (binding):** Deterministic mode works with `RESEARCH_LLM_PROVIDER=none`. Personas are pure functions over a ticker's context + quality reports: **Bull** = top-percentile validated features; **Bear** = bottom-percentile; **Skeptic** = R2-SKEPTIC-01's challenge report embedded verbatim; **Risk** = missingness, small-n, nominal-TRY basis, significance evidence — and always renders last. Every sentence carries a citation chip `{field, value, source_file}`. Equal evidence budget per persona (4 items each). Optional LLM mode may only rephrase the same grounded bullets. **The response schema contains no verdict/recommendation/winner field, and a test asserts that key-absence explicitly.** Closing panel (verbatim): "**A structured debate over historical, validated evidence. No persona forecasts returns; no verdict is issued; nothing here is investment advice.**"
- **Steps:** (1) Read the agent service + one company-context JSON to map fields. (2) Persona builders, unit-tested for citation completeness (every sentence resolves to a field). (3) Route + schema + no-verdict-key test + PUBLIC_DEMO_MODE convention. (4) Page after AutopsyPage patterns; Risk panel visually persistent. (5) Contract registration; `make claims-lint` on all template sentences. (6) Manual run with `RESEARCH_LLM_PROVIDER=none` recorded.
- **Acceptance criteria:** Works LLM-off; every rendered sentence citation-resolvable; no verdict field anywhere (test-pinned); suites + build + lint green.
- **Verification commands:** `PYTHONPATH=backend python -m pytest backend/tests`; `cd frontend && npm run build`; `make claims-lint`; the LLM-off transcript.
- **Generated artifacts:** possibly regenerated `company_contexts/` (via Makefile only; note in report).
- **Claim-safety:** never summarize a debate as a conclusion; equal budgets and Risk-last ordering are design requirements, not suggestions; LLM mode must be incapable of introducing uncited sentences (reject, don't repair).
- **Failure modes:** rhetoric outrunning evidence (citation tests guard); a "Bull wins" reading (no-verdict design is the mitigation); building before Skeptic exists (hard dependency).
- **Rollback:** revert; additive.
- **Demo value:** very high — the philosophy as product. **Research value:** medium. **CV value:** very high.
- **Model/effort:** **Opus, high.** **Depends:** R2-SKEPTIC-01 (embedded), R2-AUTOPSY-01 (page patterns), R2-CONTRACT-02. **Commit:** yes. **/clear after:** yes.

### R2-FRICTION-01 — Friction simulator (the inverted backtester)
- **Priority:** P3. **Stage:** 4. **Owner role:** Research/Frontend. **Risk:** **high — the queue's most dangerous claim surface.**
- **Why this matters:** Backtesting discipline is the one classic quant-hygiene topic with no artifact here. Built *around a null signal*, its purpose is inverted: show that even occasionally-lucky per-split baskets do not survive turnover and costs, and teach why gross hypothetical numbers overstate everything.
- **Current evidence:** prerequisite met — `predictions_test_{2023,2024,2025}.csv` exist (ticker, year, model, y_true, y_pred; n=80/split, training universe). Note: `y_pred` scales differ by model (baseline emits 0–1 scores, regressors emit return-scale values) — baskets must be built from **within-year, within-model ranks of y_pred**, never from y_pred magnitudes.
- **Target files:** new `experiments/friction_sim.py` + outputs `experiments/results/friction_report.{json,md}` (+ plot CSV); additive Makefile target; a panel on `AutopsyPage.jsx` (not a standalone page); root tests; contract updates.
- **Design (binding):** top-k basket per model per test year from y_pred ranks; turnover between consecutive years' baskets; parameterized cost bps (defaults labeled as assumptions with a comment citing that they are assumptions, not measured BIST costs); outputs per-year gross vs net basket mean-return bars only — **no cumulative-wealth curves, ever**; every chart canvas carries the stamp rendered *inside* the drawing area (verbatim): "**Hypothetical illustration — not a backtest of a viable strategy; underlying signal IC ≈ 0 and no model survives significance correction.**" Universe label mandatory: "81-ticker training universe, nominal TRY."
- **Steps:** (1) Read the dumps + leaderboard; build the deterministic simulator (seedless — it's arithmetic, no sampling; if any sampling is added, seed it). (2) Tests: turnover arithmetic on a hand-built fixture; cost application; determinism (rerun → identical). (3) Report generation with the stamp text embedded in the markdown too. (4) Autopsy panel with in-canvas stamp; contract registration; lint. (5) Never run `make research` here — the dumps are inputs, not regenerated.
- **Acceptance criteria:** Rerun → byte-identical report; no cumulative-return series anywhere in code, report, or UI (grep for `cumprod`/`cumulative` as a self-check, recorded); stamp present in every rendered chart and in the report; suites + build + lint green.
- **Verification commands:** `PYTHONPATH=. python -m pytest tests/`; new target twice + `shasum`; `cd frontend && npm run build`; `make claims-lint`.
- **Generated artifacts:** `experiments/results/friction_report.{json,md}` (new names only).
- **Claim-safety:** highest in the queue. Forbidden outputs: any net-return figure without its gross companion and stamp; any annualized/compounded number; any sentence where friction results read as achievable performance. The MCC forbidden-vocabulary rules apply to the report markdown as well — human-review it against the do-not-claim register and say so in the report.
- **Failure modes:** a screenshot-safe chart that isn't (the in-canvas stamp is the defense); ranking by y_pred magnitude across models (scale trap above); scope creep into portfolio optimization (out of scope, forever).
- **Rollback:** delete new files; revert panel.
- **Demo value:** medium-high. **Research value:** high. **CV value:** high — "I built the cost machinery to kill my own lucky baskets" is a memorable line.
- **Model/effort:** **Fable, high** — judgment about what must *not* be shown is the core skill here. **Depends:** R2-AUTOPSY-01 (panel host), R2-CONTRACT-02. **Commit:** yes. **/clear after:** yes.

### R2-DEMO-01 — Glass-box demo runbook + reproducibility quickstart
- **Priority:** P3. **Stage:** 4 (last). **Owner role:** Documentation/Product. **Risk:** low.
- **Why this matters:** The demo assets will exist scattered across eight surfaces; a scripted path with fallback branches is the difference between a wow and a fumble. Also owns the last documentation gap: a one-screen reproducibility quickstart (manifest → `make research-verify-run`) currently lives only inside METHODOLOGY.
- **Current evidence:** `make demo-check` (BE-01), `make research-verify-run`, `make claims-lint`, runtime-status endpoint, all Stage-2/3 surfaces per this queue's completion state at execution time.
- **Target files:** new `docs/DEMO_RUNBOOK.md`; `README.md` (short reproducibility quickstart section linking METHODOLOGY — additive prose only).
- **Steps:** (1) Inventory which queue surfaces actually shipped (do not script a demo of an unbuilt page — check `App.jsx` routes). (2) Scripted path: `make demo-check` → runtime-status → frozen-evidence specimen archive → seismograph + Instrumented Null panel → Autopsy → Skeptic/Courtroom (if shipped) → finale: live-edit a page to say "predicts winners," run `make claims-lint`, watch it fail, revert. (3) Fallback branches: LLM down (deterministic modes), backend down (labeled demo data), single-page demo (Autopsy only). (4) Timing notes per segment; the §5/§14 claims-guide answers cross-referenced, not duplicated. (5) README quickstart: three commands, no claims.
- **Acceptance criteria:** Every step names a real route/target that exists at write time; the lint-failure finale is rehearsed and its transcript recorded; no forbidden claim anywhere in the runbook (human-review against the claims guide).
- **Verification commands:** run `make demo-check` + the finale sequence once, honestly recorded; `make claims-lint` (must end green after the revert).
- **Generated artifacts:** none.
- **Claim-safety:** the runbook quotes claim wording only from the claims guide/contract; it never introduces new phrasings.
- **Failure modes:** scripting unbuilt surfaces; the finale mutation accidentally committed (revert is part of the script).
- **Rollback:** revert docs.
- **Demo value:** very high (it *is* the demo). **Research value:** low. **CV value:** medium.
- **Model/effort:** **Terra, medium** (Sol acceptable if all referenced surfaces shipped). **Depends:** whatever has shipped; hard floor: R2-STAT-UI-01. **Commit:** yes. **/clear after:** yes.

---

## Phase 2 remaining order (dependency-sorted)

R2-GOV-01 → R2-STAT-UI-01 → R2-CONTRACT-02 → R2-LINEAGE-01 → R2-SKEPTIC-01 → R2-AUTOPSY-01 → R2-CAL-01 → R2-REAL-01 → R2-REGIME-01 → R2-LOOP-01 → R2-COURT-01 → R2-FRICTION-01 → R2-DEMO-01

Hard dependencies: AUTOPSY needs STAT-UI (endpoint reuse) and CONTRACT-02 (registration procedure); COURT needs SKEPTIC + AUTOPSY; FRICTION needs AUTOPSY + CONTRACT-02; REGIME needs REAL (shared macro CSV); DEMO runs last. Everything else may interleave. CAL-01, REAL-01, and LOOP-01 have no dependents besides REGIME — they can shift later without blocking the demo path (STAT-UI → SKEPTIC → AUTOPSY → COURT → DEMO is the critical demo chain).

**Standing instruction for every executing agent:** on completion, add your task's row to the completion ledger above (ID, DONE, commit SHA + key artifact), add a TASK_STATE.md row, and recommend `/clear`. Do not begin a second queue task in the same context.
