# R3-PREREG-01 — Fable 5 independent review handoff

**Status: INDEPENDENT RE-REVIEW APPROVED (2026-07-18).** The initial
independent Fable 5 review returned **CHANGES REQUIRED** with RF-1 through RF-6;
those mandatory fixes were implemented in this worktree. The separate-context
Fable 5 re-review, including the interpretation grid, is now **APPROVED**: RF-1
through RF-6 are **resolved**. The reviewed worktree/branch is
`local/r3-prereg-01-execution-e7299d`; no 2026 outcome data existed during
implementation or review. This task is **merge-ready after owner commit** and
nothing here has been committed.

Initial implementer: Opus. Mandatory-fix implementation: Codex, 2026-07-16.
Freeze git SHA: `bd9aa71a39e33e62d43197e034e8db86b82df0a5`.

## Initial independent-review findings addressed

- **RF-1:** freeze-once / refuse-drift behavior, including expected post-freeze
  Git-SHA drift, now occurs before canonical writes.
- **RF-2:** minimum usable cohort is 30 and all absent/insufficient/estimated
  states disclose complete frozen-cohort membership.
- **RF-3:** the nominal-TRY outcome is pinned to Yahoo adjusted closes, actual
  year-end quotation dates, retained raw-snapshot checksums, and independent
  recomputation.
- **RF-4:** unexpected/duplicate/non-finite/malformed inputs and per-row missing
  provenance refuse before statistics; ordinary nulls remain exclusions.
- **RF-5:** n=30–40 detectable-absolute-IC context is precomputed with the
  committed Fisher-z method and selected by realized usable n.
- **RF-6:** manifest construction hashes the requested results directory's CSV;
  outputs contain no absolute worktree path and reproducibility wording is
  environment-qualified.

## What to review

The reviewer should independently confirm each of the following.

### 1. Genuine pre-registration timing

- No 2026 realized-outcome file existed at implementation time.
  `data/trusted_raw/realized_2026_returns.csv` is **absent**; the service's
  optional partial-target file `data/trusted_clean/partial_2026_ytd_returns.csv`
  is also absent. Test: `test_no_2026_outcome_file_at_implementation_time`.
- The freeze was produced against feature year 2025 → target year 2026 with the
  forward year unevaluated (`prediction_status == "unevaluated_forward_forecast"`,
  every row `realized_return_available=False`).

### 2. Outcomes absent throughout implementation

- No step sourced, simulated, or anticipated 2026 outcomes. The evaluator
  returns the structured `outcome_data_absent` state and computes no IC or
  p-value (`test_evaluator_returns_outcome_data_absent_with_no_metric`,
  `test_absent_state_writes_no_result_artifact`).

### 3. Service-path parity (no reimplementation)

- The freeze harness imports the shipped
  `backend/app/services/forecasting_csv_service.py` and calls the exact
  production function behind `GET /forecasting/inference?year=2025` —
  `inference_forecast(input_year=2025, top_n=12)` — through the documented
  `RESEARCH_REPO_ROOT` seam. Function identity is asserted for
  `inference_forecast`, `train_parameters`, `run_forecast`.
- The REQUIRED equivalence test
  (`test_frozen_ranking_equals_live_production_inference`) invokes the real
  service **directly** (independent test-side import), invokes the **freeze
  harness**, and reads the **committed CSV**, then compares eligible tickers,
  scores, order, and ranks three ways. Please confirm this compares against the
  real service, not two copies of experiment code.
- `git diff --stat backend/` is empty; the service source checksum is unchanged
  (`7438ab40…`).

### 4. Frozen cohort and ranking

- Cohort: the 40 public-universe companies scored by production inference for
  feature year 2025. Frozen artifact:
  `experiments/results_forward_2026/forward_ranking_2026.csv` (40 rows).
- Frozen SHA-256: `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f`.
- Freeze-once: a same-state rerun returns `already_frozen_identical` and leaves
  both files untouched. Candidate ranking, Git SHA, service checksum, data
  checksum, universe, CSV bytes, or manifest bytes drifting produces a
  structured non-zero refusal without replacement.

### 5. Tamper resistance

- The evaluator and freeze generator hold the frozen checksum as independent
  anchors; the generator additionally pins the canonical manifest checksum.
  Both refuse manual changes before touching outcomes. The `freeze_manifest.json`
  `source_artifacts` list (including the frozen ranking itself) is re-verified by
  `tests/test_artifact_registry.py::test_embedded_source_artifact_checksums_are_current`.

### 6. Exact future-outcome definition

- Future outcome = nominal-TRY calendar-year return from the Yahoo Chart API
  adjusted close on the final valid quotation on/before 2025-12-31 and
  2026-12-31, searched within each December 20–31 window. The exact price basis,
  distribution/split treatment, date rule, formula, symbol mapping,
  delisting/missing behavior, row-level source fields, and retained start/end
  snapshot checksums are pinned. The evaluator recomputes every usable return
  within `1e-6` percentage points. Nulls stay null and are disclosed.

### 7. Single-test design

- Exactly one primary test: Spearman rank IC of the frozen ranking vs realized
  2026 returns, with a within-year seeded permutation p-value (10,000
  permutations, seed 42, two-sided) at α = 0.05. No retrospective model
  selection; no alternative basket/target/cohort after outcomes mature. Please
  confirm the doc forecloses these degrees of freedom.

### 8. Power limitation

- The protocol **leads** with the required power boundary. Its frozen n=30–40
  table uses the committed Fisher-z α=0.05 / 80%-power method; n=40 is 0.430555
  (approximately 0.431), and smaller n is weaker. The selected number is
  descriptive context, not another test or a validation threshold.

### 9. Interpretation-grid completeness (mandatory)

- The grid pre-writes all five cells: positive/distinguishable,
  positive/not-distinguishable, negative/distinguishable,
  negative/not-distinguishable, and undefined/insufficient
  (`test_interpretation_grid_is_complete`, `test_interpretation_cell_helper_is_total`).
  `insufficient_data` means fewer than 30 usable rows and carries no metric.

### 10. Positive-significant wording

- The strongest cell (positive & distinguishable) still explicitly denies a
  reliable predictive edge, calls out the single 30–40-row year and n-specific
  detectable |IC| context, and states that no product/MCC claim changes
  automatically. Verified in both the doc and the evaluator's `estimated` output
  (`test_positive_significant_cell_still_denies_reliable_edge`). Please read the
  rendered grid, not only the code.

### 11. Claim governance

- Any future claim change requires the full
  evidence → audit → methodology → claims-guide → MCC review flow. The evaluation
  never auto-updates a claim. Any future correction requires a separately
  reviewed protocol amendment completed before outcomes are inspected; this
  task implements no amendment workflow.

### 12. Determinism and provenance

- The frozen CSV carries the original git SHA, service source checksum, and input-dataset
  checksums as constant columns; the manifest records the same plus the frozen
  ranking's own checksum. No wall-clock timestamp is written (it would break
  byte-determinism); the freeze identifier is derived from the protocol id + git
  SHA. That SHA remains the parent/pre-freeze state after later commits; a
  changed HEAD refuses instead of refreshing it.

## No-claim register check

The reviewer should confirm the protocol, frozen artifact, manifest, and
evaluator output contain **no** buy/sell/hold guidance, expected-return figure,
market-beating claim, profitable-trading claim, or validated-alpha language, in
any interpretation cell (`test_protocol_contains_no_investment_advice_wording`).

## Verification observed before the mandatory fixes (2026-07-15)

- Focused tests `tests/test_preregistered_2026.py`: 28 passed.
- Registry tests `tests/test_artifact_registry.py`: 16 passed.
- Root suite `PYTHONPATH=. python -m pytest tests/`: 314 passed.
- Backend suite `PYTHONPATH=backend python -m pytest backend/tests`: 85 passed.
- `make freeze-forward-2026` ×2: byte-identical CSV + manifest.
- `make evaluate-forward-2026`: `outcome_data_absent`, exit 0, no metric artifact.
- `make claims-lint`: PASSED (MCC v1.7.0; no bump — no new backend response surface).
- `make docs-lint`: 8 violations, all pre-existing and unrelated (the SMRTG
  investigation doc plus two stale operating-doc paths); zero introduced here.
- Protected service/canonical/trusted/manifest/MCC checksums: unchanged.
- `git diff --check`: clean.

## Verification observed after RF-1 through RF-6 (2026-07-16)

- Focused preregistration tests: **70 passed**.
- Artifact-registry tests: **16 passed**.
- Complete root suite: **356 passed**.
- Complete backend suite: **85 passed** (27 deprecation warnings).
- Isolated first freeze: `frozen_created`; isolated same-state rerun:
  `already_frozen_identical`, `artifacts_unchanged=true`.
- `make evaluate-forward-2026`: exit 0, deterministic
  `outcome_data_absent`, frozen=40, usable=0, missing=40, no metric/report.
- `make claims-lint`: passed with MCC v1.7.0 unchanged.
- `make docs-lint`: the same eight pre-existing violations only; none cite the
  R3-PREREG-01 protocol or handoff.
- JSON parsed, Markdown parsed, and the frozen CSV validated at 40 rows with the
  pinned schema.
- Protected checksum comparison: **315/315 files byte-identical**, including the
  service, trusted data, canonical experiments, run manifests, frozen pair, and
  MCC. Ranking SHA-256 remains
  `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f`;
  freeze-manifest SHA-256 remains
  `6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea`.
- No 2026 outcome file, evaluation report, or scratch output exists. No commit or
  push occurred.

## Review record

- Initial reviewer: independent Fable 5 review supplied by the owner
- Initial review date: 2026-07-16
- Initial outcome: **CHANGES REQUIRED — RF-1 through RF-6**
- Mandatory-fix implementation and requested verification: complete
- Independent re-reviewer/date/outcome: independent Fable 5 re-review, 2026-07-18, **APPROVED — RF-1 through RF-6 resolved**
- Reviewed worktree/branch: `local/r3-prereg-01-execution-e7299d`
- Frozen ranking checksum at review: `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f` (unchanged)
- Freeze-manifest checksum at review: `6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea` (unchanged)
- 2026 outcome data during implementation or review: none existed
- Merge-ready: **YES, after owner commit**
