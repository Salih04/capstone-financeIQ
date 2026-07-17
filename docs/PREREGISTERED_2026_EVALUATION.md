# Pre-registered 2026 forward-outcome evaluation (R3-PREREG-01)

> The pre-registered 2026 evaluation is nearly powerless by design; its value is
> the discipline of freezing the ranking and interpretation before outcomes
> exist, not the expectation that one approximately 40-row year can establish a
> reliable predictive edge.

This document is the immutable pre-registration for evaluating the FinanceIQ
2026 forward ranking. It is written **before any 2026 outcome data exists**.
Everything the evaluation will do — the frozen input, the outcome
definition, the single test, the threshold, and the interpretation of every
possible result — is fixed here in advance so that no analytic choice can be made
after outcomes mature.

Protocol identifier: **`PREREG-2026-FORWARD-v1`**.

## Why pre-register a nearly powerless test

R3-SERV-01 measured the real serving heuristic retrospectively and found no
reliable predictive edge (pooled walk-forward IC indistinguishable from the
within-year null). The committed power analysis
(`experiments/results/significance_report.md`, METHODOLOGY §Power and
detectability limits) shows that one 40-ticker year detects only an absolute
Spearman IC of about **0.431 at 80% power**. The usable cohort may be 30–40, so
the evaluator selects the already frozen n-specific value in the power table
below; smaller n has weaker power. A single 2026 outcome year therefore cannot,
on its own, establish predictive skill in either direction.

The point of this task is **process integrity, not a result**. By freezing the
ranking and pre-writing the interpretation now, we remove the ability to
retrofit a favorable story onto whatever 2026 happens to deliver. The honest
capstone verdict — no reliable predictive edge — is not changed by this
document, and cannot be changed by the evaluation it describes without the full
governance flow in the last section.

## Frozen artifact and checksum

| Field | Value |
| --- | --- |
| Frozen ranking | `experiments/results_forward_2026/forward_ranking_2026.csv` |
| SHA-256 | `a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f` |
| Rows | 40 (public-universe feature-year-2025 cohort) |
| Freeze manifest | `experiments/results_forward_2026/freeze_manifest.json` |
| Freeze git SHA | `bd9aa71a39e33e62d43197e034e8db86b82df0a5` |
| Protocol identifier | `PREREG-2026-FORWARD-v1` |
| Freeze generator | `experiments/freeze_forward_ranking.py` (owner: `make freeze-forward-2026`) |
| Evaluator | `experiments/evaluate_preregistered_2026.py` (owner: `make evaluate-forward-2026`) |

The frozen ranking is produced by invoking the **unchanged production service**
`backend/app/services/forecasting_csv_service.py::inference_forecast(input_year=2025, top_n=12)`
— the exact function behind `GET /forecasting/inference?year=2025` — through the
documented `RESEARCH_REPO_ROOT` seam. The heuristic is never reimplemented; the
freeze harness only serializes what the service returns, in the service's own
rank order and score precision. The evaluator holds the checksum above as an
independent anchor and refuses to run if the frozen bytes differ.

The original `freeze_git_sha` is the repository state at the original freeze.
It is intentionally the parent/pre-freeze state and must not refresh after a
later commit changes `HEAD`. `make freeze-forward-2026` is freeze-once: if both
artifacts already exist it validates their pinned checksums and internal
provenance, computes a candidate in an isolated location, and returns
`already_frozen_identical` only when both candidate artifacts are byte-identical.
Git, service, input-data, universe, semantic-ranking, or artifact drift produces
a structured non-zero refusal before either canonical file is opened for
writing. A partial pair also refuses. There is no amendment mechanism in the
generator.

Byte reproducibility was observed in the documented local environments.
Reproducibility remains environment-qualified; this protocol claims no universal
cross-platform byte-identity guarantee.

## Target year and future outcome definition

- **Target year:** 2026 (feature year 2025 → target year 2026).
- **Start price:** Yahoo Chart API `adjclose` for the final valid quotation on or
  before 2025-12-31, searched in the repository collector's 2025-12-20 through
  2025-12-31 year-end window.
- **End price:** Yahoo Chart API `adjclose` for the final valid quotation on or
  before 2026-12-31, searched in the 2026-12-20 through 2026-12-31 window.
- **Trading-day rule:** December 31 is the target valuation date. If it is not a
  BIST trading day, use the last valid BIST quotation before it within the stated
  window. The actual quotation dates must be recorded. Do not use the first
  quotation of the year or an arbitrary earlier date.
- **Price basis:** Yahoo adjusted close, currency TRY. Raw close is not an
  allowed substitute. Adjusted close is used exactly as supplied by Yahoo: its
  split and distribution/corporate-action adjustments are retained; dividends
  are not added again and corporate actions are not independently overridden.
- **Formula and units:**
  `realized_return_pct = (end_adjusted_close_try / start_adjusted_close_try - 1) * 100`,
  expressed in percentage points. The evaluator independently recomputes this
  value and permits at most `1e-6` percentage-point absolute disagreement.
- **Return basis:** nominal TRY calendar-year adjusted-close return only. It is
  neither benchmark-relative nor CPI-adjusted nor USD-denominated.
- **Missing quotation and delisting:** if either required adjusted-close quote
  is unavailable, the realized return remains null and the ticker is excluded
  with its reason disclosed. Delisting is not assigned zero or −100%, and no
  terminal value is invented.
- **Symbol changes:** the frozen ticker remains the cohort identity. The source
  symbol must be recorded. A symbol other than `<frozen_ticker>.IS` is permitted
  only with a non-empty, auditable mapping note; mappings are never silent.

This convention is grounded in `scripts/fetch_yahoo_chart_prices.py`, which
requests `includeAdjustedClose=true`, retains both close and `adjclose`, and
selects the last valid quote on or before December 31; in
`scripts/data_collection/price_features.py`, which defines the cached year-end
adjusted close as the price input; and in `DATA_PIPELINE.md`, which specifies
the adjusted-close last-trading-day formula for a price-based annual return.
The legacy canonical training target remains its existing dated annual-return
field; this future sidecar does not change production forecasting or historical
artifacts.

### Approved future outcome source and sourcing procedure

The outcome prices must come from the project's existing **free, manual Yahoo
sourcing pattern**, recorded into the sidecar from retained Yahoo Chart API raw
snapshots (no paid API and no scraper). Both the start and end raw snapshots must
be retained and checksum-addressed. Every usable row carries its own complete
provenance; file-level provenance is not sufficient.

The evaluator will look for a sourced outcome file that **does not exist yet**
(it is absent until sourced ~early 2027):

```text
# Absent until sourced. Predeclared path and schema — do not create before 2026 closes.
data/trusted_raw/realized_2026_returns.csv
```

### Expected outcome-file schema

The sourced outcome file must contain every column below (extra columns are
ignored; any missing required column is malformed and the evaluator refuses):

```text
ticker                    # frozen cohort identity, upper-cased
target_year               # integer; exactly 2026
realized_return_pct       # nominal TRY calendar-year return %, may be null
start_adjusted_close_try  # Yahoo adjclose at the actual 2025 year-end quote
end_adjusted_close_try    # Yahoo adjclose at the actual 2026 year-end quote
start_price_date          # ISO actual quotation date, 2025-12-20..2025-12-31
end_price_date            # ISO actual quotation date, 2026-12-20..2026-12-31
price_basis               # exactly yahoo_adjusted_close
currency                  # exactly TRY
valuation_date_rule       # exactly last_valid_quote_on_or_before_dec31_within_dec20_dec31
return_convention         # exactly nominal_try_calendar_year_adjusted_close_return_pct
source                    # exactly yahoo_chart_api
source_url_or_record_id   # non-empty Yahoo URL or retained source-record identifier
as_of_date                # ISO retrieval/audit date, not earlier than end_price_date
start_snapshot_sha256     # 64-character SHA-256 of retained start raw snapshot
end_snapshot_sha256       # 64-character SHA-256 of retained end raw snapshot
source_symbol             # Yahoo symbol used when sourcing (normally TICKER.IS)
symbol_mapping_note       # required explanation when source_symbol differs
exclusion_reason          # reason for a null outcome where available
```

### Null-preserving behavior

Missing stays missing. An ordinary null `realized_return_pct` is **excluded**
from the test, never imputed, interpolated, or replaced with zero or a proxy.
Positive or negative infinity and non-numeric non-null values are malformed and
refused, not treated as missing. Excluded tickers and reasons are reported.

YTD/partial-2026 outcomes, another date window, raw-close returns,
benchmark-relative returns, CPI-adjusted returns, USD returns, and any other
price convention are explicitly prohibited substitutes.

## Cohort and eligibility rule

- **Cohort:** the 40 public-universe companies scored by the production
  forward-inference path for feature year 2025. This is the entire frozen
  ranking; it is fixed at freeze time and independent of any future outcome.
- **Ranking eligibility (freeze time):** every public-universe 2025 row the
  service scores is eligible and frozen. No ticker is added or removed after
  freezing.
- **Evaluation eligibility (outcome time):** a frozen ticker contributes to the
  test only if it has a real, finite realized 2026 return in the sourced file.
  Tickers with null outcomes are excluded per the null-preserving rule above.
- **Unexpected rows:** a ticker outside the frozen 40 is malformed and refused;
  no inner join may silently discard it. Duplicate tickers are refused before
  merging.
- **Usable-row floor:** if fewer than **30** frozen tickers have a usable
  realized outcome, the test is not attempted and the result is
  `insufficient_data` (see the interpretation grid). No IC or p-value is
  computed below 30.
- **Membership disclosure:** every `estimated`, `insufficient_data`, and absent
  state records the exact included tickers, exact excluded tickers, exclusion
  reasons where available, frozen cohort size, usable cohort size, and
  missing-outcome count. Lists follow frozen rank order, are disjoint, and cover
  all 40 frozen tickers.

## The single pre-registered statistical test

There is **exactly one** primary test. No secondary tests, no alternative
statistics, no model selection.

1. **Statistic — Spearman rank IC.** The Spearman rank correlation (average ranks
   for ties, identical to the canonical `experiments/significance.py`
   definition) between the frozen `frozen_score` and the realized 2026 return
   over the usable rows.
2. **Inference — within-year seeded permutation p-value.** Because 2026 is a
   single year, the null is generated by permuting the realized outcomes among
   the frozen-ranked tickers and recomputing the Spearman IC. Two-sided
   p-value `= (1 + #{|IC_perm| >= |IC_obs|}) / (1 + N_perm)` with
   `N_perm = 10000`, seed `42`.
3. **Significance threshold — α = 0.05**, two-sided. "Statistically
   distinguishable" means the permutation p-value is below 0.05; it does **not**
   mean the result is economically meaningful, robust, or a predictive edge.

The frozen ranking is **the** model. There is:

- **No retrospective model selection.** The frozen scores are evaluated exactly
  as frozen. No refitting, reweighting, top-k slicing, or feature reselection is
  permitted after outcomes exist.
- **No alternative basket, target, or cohort selection after outcomes mature.**
  The basket is the full frozen 40; the target is nominal-TRY 2026 return; the
  cohort is fixed. Choosing a favorable subset, an alternative return basis, or a
  different horizon after seeing outcomes is forbidden and would void the
  pre-registration.

### Treatment of missing outcomes

Rows with null realized returns are excluded and their count is reported. If
exclusions push the usable count below the 30-row floor, the result is
`insufficient_data` and no IC or p-value is produced. Missing outcomes are
never imputed.

## Pre-specified sample-size-aware power context

The evaluator selects exactly one row from this frozen table using the realized
usable cohort size. Values use the committed
`experiments.significance.minimum_detectable_ic` method: two-sided Fisher-z
approximation for one within-year Spearman IC, variance `1/(n-3)`, α=0.05, and
target power 80%, rounded to six decimals.

| Usable n | Detectable absolute IC at 80% power |
| ---: | ---: |
| 30 | 0.492355 |
| 31 | 0.484960 |
| 32 | 0.477886 |
| 33 | 0.471110 |
| 34 | 0.464614 |
| 35 | 0.458377 |
| 36 | 0.452383 |
| 37 | 0.446618 |
| 38 | 0.441066 |
| 39 | 0.435716 |
| 40 | 0.430555 |

This table is descriptive power context, not a second hypothesis test. It
introduces no additional p-value and is never a pass/fail, meaningfulness, or
validation threshold. Smaller n requires a larger detectable absolute IC and
therefore has weaker power. The primary Spearman/permutation test is unchanged.
An observed absolute IC exceeding the displayed number does not by itself imply
reliability, practical relevance, or a reliable predictive edge.

## Artifact ownership and regeneration restrictions

| Artifact | Kind | Owner | Regeneration rule |
| --- | --- | --- | --- |
| `experiments/results_forward_2026/forward_ranking_2026.csv` | Immutable frozen ranking | `make freeze-forward-2026` | **Freeze-once.** Identical rerun reports `already_frozen_identical` without writes; any drift refuses. |
| `experiments/results_forward_2026/freeze_manifest.json` | Deterministic freeze manifest | `make freeze-forward-2026` | Freeze-once with the ranking; pinned canonical bytes are never refreshed. |
| `docs/PREREGISTERED_2026_EVALUATION.md` | Human-reviewed protocol | Human editor | Immutable once outcome data exists. Later changes are dated, appended amendments — never rewrites. |
| `experiments/evaluate_preregistered_2026.py` | Inert evaluator | Human editor | Logic is fixed pre-outcome; changing the test after outcomes exist voids the pre-registration. |
| `data/trusted_raw/realized_2026_returns.csv` | Future sourced outcome input | Human (manual sourcing) | Absent until sourced; created once from real prices, never fabricated. |
| `experiments/results_forward_2026/evaluation_2026_report.json` | Future generated evaluation report | `make evaluate-forward-2026` | Does not exist until valid outcomes are present; produced only in the `estimated` state. |

The frozen ranking's checksum is committed in the evaluator and this document;
the canonical manifest checksum is pinned in the freeze generator. Any change is
detected and refused without replacement. A future amendment is out of scope for
this task and requires a separately reviewed protocol amendment completed before
any outcome is inspected. No amendment workflow is implemented here.

## Interpretation grid (pre-written for every result)

The interpretation of the 2026 result is decided **now**. Whatever the evaluation
returns, the reading is taken verbatim from this grid. No interpretation is
improvised after outcomes arrive.

Every cell — including the most favorable — carries the same hard boundary:

- this is **one** retrospective, 30–40-row outcome year;
- the n-specific detectable absolute IC is selected from the pre-specified table
  (approximately **0.431 at n=40**, higher at smaller n), so the test is nearly
  powerless;
- one result **cannot** establish a reliable predictive edge;
- **no** product, investment, or Model Confidence Contract claim changes
  automatically;
- any future claim change requires the full
  evidence → audit → methodology → claims-guide → MCC review flow.

| Result cell | Evaluator status | Pre-committed interpretation |
| --- | --- | --- |
| **Positive and statistically distinguishable** (IC > 0, permutation p < 0.05) | `estimated`, `positive_and_statistically_distinguishable` | The frozen ranking's 2026 rank IC is positive and distinguishable from the within-year null in this single year. This is **not** evidence of a reliable predictive edge: it is one retrospective 30–40-row year, the n-specific detectable \|IC\| context is ~0.431 at n=40 and weaker at smaller n, and the descriptive threshold is not a validation criterion. A single favorable draw is fully consistent with noise. It establishes no implementability and changes no product or MCC claim. A positive, distinguishable draw is at most a prompt to **plan** additional pre-registered outcome years — never a validated result on its own — and any claim change must go through evidence → audit → methodology → claims-guide → MCC review. |
| **Positive and not distinguishable** (IC > 0, permutation p ≥ 0.05) | `estimated`, `positive_and_not_distinguishable` | The rank IC is positive but indistinguishable from the within-year null. Consistent with no edge; a positive point estimate at this sample size carries essentially no evidential weight. No claim changes. |
| **Negative and statistically distinguishable** (IC < 0, permutation p < 0.05) | `estimated`, `negative_and_statistically_distinguishable` | The rank IC is negative and distinguishable from the null in this single year. This is **not** a "contrarian signal" or an inverted strategy: it is one noisy retrospective year at a near-powerless sample size, and it establishes no investment value in any direction. No claim changes. |
| **Negative and not distinguishable** (IC < 0, permutation p ≥ 0.05) | `estimated`, `negative_and_not_distinguishable` | The rank IC is negative and indistinguishable from the null. Consistent with the pre-existing no-reliable-edge verdict. No claim changes. |
| **Undefined or insufficient data** | `outcome_data_absent`, `insufficient_data`, or a refusal state | No valid metric is produced: outcomes are absent, fewer than 30 usable rows remain, or an integrity/schema/provenance check failed. No IC or p-value is reported and no result artifact is written. Membership and exclusions are disclosed where applicable. The pre-existing verdict stands unchanged. |

None of the four estimated cells, and not the undefined cell, licenses any
buy/sell/hold guidance, expected-return figure, market-beating claim,
profitable-trading claim, or validated-alpha language. This document produces
none of those, in any cell — it is research support, not investment advice.

## Claim-governance procedure after evaluation

When 2026 outcomes are eventually sourced and `make evaluate-forward-2026`
returns an `estimated` state:

1. Record the returned state (IC, permutation p, usable-row count, interpretation
   cell) as evidence — the evaluator writes
   `experiments/results_forward_2026/evaluation_2026_report.json`.
2. Read the interpretation **only** from the grid above; do not compose new
   wording.
3. A result **never** auto-updates any claim. Changing any user-facing claim, the
   `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md`, or the Model Confidence Contract requires
   the full documented flow: **evidence → audit → methodology → claims-guide → MCC
   review**, with human sign-off at each stage.
4. This protocol is immutable once outcome data exists. Any future correction
   requires a separate, independently reviewed protocol amendment completed
   before outcomes are inspected; it may never silently rewrite the frozen
   inputs, the test, or the grid. This task implements no amendment workflow.

## Independent review

Status: initial independent review returned **CHANGES REQUIRED (RF-1 through
RF-6)**; mandatory fixes were implemented. The independent Fable 5 re-review is
now **APPROVED** (2026-07-18): RF-1 through RF-6 are **resolved**. The reviewed
worktree/branch is `local/r3-prereg-01-execution-e7299d`; the frozen ranking
checksum
(`a8a8c39cb8956b13c388d6d0be83470678a1b5c2395476d87d849b05b5b5518f`) and the
freeze-manifest checksum
(`6a96408c55789646ce8f5b66fa8be243ac6ac8a2292e1783ecb60c88b87f54ea`) are
unchanged, and no 2026 outcome data existed during implementation or review.
This task is **merge-ready after owner commit**.

## Amendments

*(None. No amendment workflow is created by R3-PREREG-01.)*
