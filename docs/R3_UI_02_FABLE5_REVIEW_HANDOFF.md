# R3-UI-02 — Return-basis lens · Independent Fable 5 copy-review handoff

Status: **APPROVED — independent Fable 5 copy review completed 2026-07-18 (recorded under Reviewer decision). Originally PENDING; committed at 18514ac5.**

- **Task:** R3-UI-02 — Return-basis lens (nominal / real-TRY / USD display).
- **Worktree / branch:** `return-basis-lens-ui-f7c7bf` / `local/return-basis-lens-ui-f7c7bf`.
  The packet named worktree/branch `r3-ui-02-return-basis`; the harness placed this
  session in a sibling worktree at the same commit (`68d2681a`) and the task forbade
  switching worktrees, so the work was done here. Both worktrees were clean and
  byte-identical at start. Reviewer: confirm this discrepancy is acceptable before commit.
- **Reviewer model:** Fable 5 (cross-family independent review; copy check mandatory).

## What to review

The claim risk on this task is that three quotable IC families now sit side by side.
Read the **rendered panel and the composed payload**, not just the code.

### 1. Every UI number against its exact source JSON path

| Rendered value | Panel display | Source file | Exact JSON path | Formatting effect |
|---|---|---|---|---|
| Nominal pooled IC | −0.153 | `experiments/results/significance_report.json` | `headline.observed_ic` = −0.15328380688030444 | display rounding only (3 dp) |
| Nominal raw p | 0.0183 | same | `headline.permutation_p_value_two_sided` = 0.0182981701829817 | display rounding only (4 dp) |
| Nominal adjusted p | 0.1098 | same | `headline.bonferroni_adjusted_p_value` = 0.10978902109789021 | display rounding only (4 dp) |
| Real-TRY pooled IC | −0.156 | `experiments/results_real_terms/real_try/significance_report.json` | `headline.observed_ic` = −0.15562044542255335 | display rounding only |
| Real-TRY raw p | 0.0164 | same | `headline.permutation_p_value_two_sided` = 0.0163983601639836 | display rounding only |
| Real-TRY adjusted p | 0.0984 | same | `headline.bonferroni_adjusted_p_value` = 0.0983901609839016 | display rounding only |
| USD pooled IC | −0.150 | `experiments/results_real_terms/usd/significance_report.json` | `headline.observed_ic` = −0.1504698753771919 | display rounding only |
| USD raw p | 0.0213 | same | `headline.permutation_p_value_two_sided` = 0.0212978702129787 | display rounding only |
| USD adjusted p | 0.1278 | same | `headline.bonferroni_adjusted_p_value` = 0.1277872212778722 | display rounding only |
| 2022 nominal return | 185.94% | `METHODOLOGY.md` §Alternative return-basis evaluation (R2-REAL-01); cross-ref `experiments/results_regime/regime_context_report.json` 2022 `bist100_return_pct.value` = 185.94 | authored constant; byte-matches committed regime field (test-pinned) | display `%` suffix only |
| 2022 real-TRY return | 74.07% | `METHODOLOGY.md` §Alternative return-basis evaluation (R2-REAL-01) | authored constant (no structured-JSON home; equals the documented CPI-deflation of the two committed regime values — the service does **not** compute it) | display `%` suffix only |

Backend performs **no arithmetic**; all significance numbers are verbatim passthrough
from the headline blocks. Confirm each rendered figure equals its source, and confirm
you are comfortable that the real-TRY 74.07% is sourced from the METHODOLOGY authority
(the only place it exists as a written figure) rather than recomputed. The raw values
are unrounded in the payload; only the panel rounds for display.

### 2. Raw / adjusted pairing

- Every basis object contains `raw_p_value` and `adjusted_p_value` in the **same** object.
- The service raises (`503`) if either is `None` for any basis — pinned by
  `test_missing_adjusted_p_cannot_produce_a_valid_response`.
- The panel renders the two p-values in one shared row (`.rb-prow`) and never renders
  raw p when adjusted p is absent (`paired` guard in `ReturnBasisLens`).

### 3. Nominal / real / USD family identification

- `nominal` → `experiments/results/significance_report.json` (canonical nominal-TRY).
- `real_try` → CPI-deflated real TRY.
- `usd` → USD basis. Each appears exactly once (`test_each_basis_appears_exactly_once`).
- All three select `random_forest` as the family-selected model ("smallest pooled raw
  permutation p-value among the six ML models"), matching each source headline.

### 4. Mandatory copy — verbatim

- **Panel header caveat** (backend-owned, `real_terms.PANEL_CAVEAT`, rendered in the
  panel and never hidden in a tooltip/accordion):
  > The no-reliable-edge conclusion was re-evaluated separately on CPI-deflated TRY and USD bases; neither survives family-wise correction. Basis changes the unit of measurement, not the conclusion.
- **2022 illustration qualifier** (backend-owned, `real_terms.ILLUSTRATION_QUALIFIER`,
  rendered immediately adjacent to the numbers):
  > an inflation-basis illustration only, not a strategy-performance or investment-value statement.

### 5. No client-side statistics

- No client-side return conversion, p-value correction, IC computation, or model
  selection. The panel only formats numbers the backend already composed.
- Fetched through `researchApi.returnBasis()` → `GET /research/return-basis`.

### 6. No chart-rebasing implication

- The tide chart's data (`BENCHMARK_MOCK` + live `/research/benchmark`) and geometry are
  unchanged. The lens is a **display panel**, not a toggle — there is no basis selector
  and nothing re-bases the chart series.

### 7. No contrarian reading of negative IC

- Negative ICs are presented as "does not survive family-wise correction," never as a
  contrarian, undervalued, or opportunity signal. Confirm no such framing leaked in.

### 8. Neutral styling

- No green success color, upward arrows, endorsement glow, or good/bad labels. Negative
  IC uses the neutral paper color. Confirm visually.

### 9. MCC registration / version

- `model_confidence_contract.json` bumped **v1.7.0 → v1.8.0**, effective 2026-07-18.
- `backend/app/services/research/real_terms.py` added to `scan.backend_response_files`.
- `BenchmarkPage.jsx` remains in `required_disclaimer.pages`.
- Five version-pin tests updated to 1.8.0. `make claims-lint` PASSED (v1.8.0).

### 10. Source artifacts unchanged

- No file under `experiments/**`, `data/trusted_clean/alternative_targets_report.*`,
  METHODOLOGY, chart datasets, or canonical prediction dumps was modified. `git diff
  --check` clean; `frontend/dist` gitignored.

## Verification run (this session)

- `backend/tests/test_return_basis_api.py`: 14/14.
- Root MCC/contract tests (coverage + four claim-safety): 15/15.
- Full backend suite (`PYTHONPATH=backend python -m pytest backend/tests`): 99/99.
- `cd frontend && npm run build`: succeeded.
- `make claims-lint`: PASSED (MCC v1.8.0).
- Visual browser verification **not performed** (protected-page Supabase auth gate /
  full-stack env, consistent with prior tasks). Recorded endpoint payload + successful
  build stand in; no screenshot is claimed.

## Reviewer decision

**APPROVED (2026-07-18).** Independent Fable 5 copy review performed outside the repository record and verified against committed HEAD 18514ac51f7e7912caf5a04b3b6526e77ce53f98 by the REV-01 governance session: exact worktree/branch/base verification; byte-exact verification of both mandatory sentences; number-by-number extraction from all source artifacts (all nine per-basis values and the 185.94% / 74.07% / 64.27% illustration match at full precision, the 74.07% accepted as METHODOLOGY-owned); raw/adjusted pairing structural; no recomputation; chart integrity preserved; 503 semantics correct; MCC v1.8.0 scoped; backend, root claim-safety, frontend-build, and claims-lint verification green; protected artifacts unchanged; no required fixes. The worktree-name discrepancy flagged at the top of this document is accepted. R3-UI-02 was committed as-is at 18514ac5 and is closed. Implementation date 2026-07-18; review date 2026-07-18 (distinct events).
