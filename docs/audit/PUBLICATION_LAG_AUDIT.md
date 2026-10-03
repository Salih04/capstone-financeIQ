# Publication-lag and point-in-time audit (2026-10-04)

**Status:** finding confirmed at code and data level; published results are
preserved unchanged; corrected sensitivity results are added alongside them.

**Summary.** The T→T+1 design pairs *fiscal-year-T* financial statements with
the stock return over *calendar year T+1*. Fiscal-year-T statements are not
public on the first day of that window: Turkish listed companies publish them
up to 60 days (solo) or 70 days (consolidated) after 31 December. Every
statement-derived feature was therefore used several weeks before an investor
could have known it. When the walk-forward is rerun with only information that
existed on the first day of the target window, the one nominally significant
published number — the equal-weight baseline's pooled IC of +0.150
(permutation p = 0.019) — falls to between +0.005 and +0.031 (p ≥ 0.63). The
ML null result is unchanged in substance. The project's conclusion, *no
reliable predictive edge*, stands; what changes is that the small positive
baseline signal shown in the published results should no longer be read as
weak evidence of anything.

## 1. What was checked, and how

| Question | Evidence |
| --- | --- |
| Which fiscal period does a year-`Y` fundamental describe? | Values in `data/trusted_raw/financials_corrected_yearly/{Y}stocks.xlsx` compared with published annual results (below) |
| When did those statements become public? | Regulatory deadline (SPK Communiqué II-14.1, art. 10) and dated press coverage of KAP filings for representative companies |
| When is each feature first used? | `experiments/run_experiments.py`: features of `feature_year = T` predict `next_year_return_pct` of year T+1, training on all years whose *target* year precedes the test year |
| What is the target window? | Header of the source return column, e.g. `Return % (2021-01-04 - 2021-12-31)`, recorded as `period_start` / `period_end` in the corrected files; `pipeline.build_returns` shifts it by one year |
| Code-level guard? | `scripts/data_collection/validate.py` prevents target/same-year *return* columns from becoming features. Nothing models statement publication dates. `MANUAL_FINANCIALS.md` states the (incorrect) premise that year-end-`Y` values are "information available at year T" |

### Fiscal-period identification (data level)

| Ticker | File year | Field | Repository value | Published FY figure | Match |
| --- | --- | --- | ---: | ---: | --- |
| BIMAS | 2021 | revenue | 70,526.68 m TL | FY2021 net sales 70,527 m TL | exact |
| BIMAS | 2021 | net_income | 2,932.48 m TL | FY2021 net profit 2,932 m TL | exact |
| EREGL | 2021 | net_income | 15,527.08 m TL | FY2021 net profit 15,527 m TL | exact |

Year-`Y` fundamentals are full fiscal-year-`Y` statements, not a snapshot of
what was published by 31 December `Y`.

### Representative timelines

| Sample | Statement period ends | Target window starts | Statement public | Days of window elapsed before publication |
| --- | --- | --- | --- | ---: |
| EREGL, features 2021 → target 2022 | 2021-12-31 | 2022-01-03 | 2022-02-10 (KAP filing reported that evening) | 38 |
| BIMAS, features 2021 → target 2022 | 2021-12-31 | 2022-01-03 | 2022-03-02 | 58 |
| THYAO, features 2022 → target 2023 | 2022-12-31 | 2023-01-02 | 2023-03-02 | 59 |
| Regulatory maximum (consolidated) | 31 Dec T | first trading day of T+1 | 70 days after year-end (~11 Mar) | ~67 |

Publication dates are taken from dated news reports of the KAP filings, not
from KAP timestamps; the KAP query API was not used (it throttles, and the
project does not automate KAP). The deadline bounds the lag regardless.
Exact per-filing timestamps for all 81 tickers × 5 years are **not**
established.

## 2. Exposure in the published feature set

Of the 40 model features, **31** are computed from fiscal-year-T statements
alone (income statement, balance sheet, margins, growth, ROE/ROA, liquidity,
leverage) or combine them with a year-end price (`pe_ratio`, `pb_ratio`,
`ev_ebitda`, `enterprise_value`). **9** use only prices up to 31 December T,
the benchmark's year-T return and market capitalisation.

A second defect affects two of those nine. `market_cap` is
`year-end adjusted close × shares outstanding at T`. Yahoo's adjusted close is
back-adjusted for splits, bonus issues and dividends *after* T, while the
share count is the historical one, so the product is understated by a factor
fixed by later corporate actions: AEFES's 2024 market cap is recorded as
₺11.2 bn and its 2025 as ₺92.3 bn, a jump that is a 10-for-1 bonus issue, not
a revaluation; EREGL 2020 is understated ~2.8×. The same factor contaminates
`price_adjclose_t` (a price *level*), `pe_ratio`, `pb_ratio`, `ev_ebitda` and
`enterprise_value`. Momentum and drawdown ratios are unaffected (the factor
cancels within a ticker).

## 3. Corrected reruns

`experiments/pit_lag_sensitivity.py` imports the published harness
(`run_experiments.py`: same panel construction, splits, nine models and
metrics) and the pooled-IC permutation test of the significance report
(equal-weighted mean of within-year Spearman ICs, 10,000 within-year
permutations, seed 20261004). The `original` specification reproduces the
published leaderboard exactly for eight models and within 0.003 IC for OLS
(collinear rank features make OLS BLAS-sensitive), using the pinned
`requirements-root.txt` environment. Outputs: `experiments/pit_audit/`.

| Specification | Features | Equal-weight IC (p) | ML models: IC range (smallest p) |
| --- | ---: | --- | --- |
| **Published** (`original`) | 40 | **+0.150 (0.019)** | −0.153 … +0.093 (0.017, random forest, negative) |
| Prices/benchmark/market cap only (`pit_price_only`) | 9 | +0.006 (0.93) | −0.027 … +0.063 (0.33) |
| …without adjustment-dependent levels (`pit_strict`) | 7 | +0.031 (0.63) | −0.031 … +0.060 (0.35) |
| Statements lagged to FY T−1, public ≥ 9 months before the window (`pit_lagged_fund`) | 40 | +0.005 (0.93) | −0.097 … −0.005 (0.14) |
| *Diagnostic, not PIT:* FY-T statement features alone | 31 | +0.193 (0.002) | −0.105 … +0.161 (0.013) |
| Published, excluding pre-listing rows | 40 | +0.164 (0.013) | −0.184 … +0.106 (0.005, random forest, negative) |
| `pit_strict`, excluding pre-listing rows | 7 | +0.031 (0.63) | −0.036 … +0.062 (0.35) |
| `pit_lagged_fund`, excluding pre-listing rows | 40 | +0.015 (0.82) | −0.123 … −0.002 (0.06) |

p-values are two-sided and **unadjusted**; this table is an exploratory
sensitivity analysis with many specifications, not a new confirmatory test.

## 4. Interpretation

- **The published baseline signal is attributable to fiscal-year-T statement
  information.** The statement features alone carry IC +0.19; the same
  features one year older carry +0.005, and price-only information carries
  ≈ 0. That pattern is what publication-lag look-ahead predicts: annual results
  released in February–March move prices inside the target window, and the
  features already "know" those results.
- **What this audit cannot separate.** Lagging the statements by a year also
  makes them staler. A window that starts after publication (for example
  1 April T+1 → 31 March T+2) would distinguish look-ahead from information
  decay, but it needs intra-year prices the repository does not hold. Until
  then the precise statement is: the positive baseline IC does not survive any
  point-in-time-correct specification available from the repository's data.
- **The published ML null is not invalidated.** Look-ahead biases *toward*
  finding signal; the ML models found none with it, and find none without it.
  The negative random-forest IC (−0.153, p = 0.017, Bonferroni 0.11) also
  disappears under every PIT specification.
- **The 2026 forward pre-registration is exposed to the same issue.** The
  ranking was frozen on 2026-07-15 (`bd9aa71a`) from fiscal-year-2025
  statements that were published in February–March 2026, inside the
  pre-registered outcome window (31 Dec 2025 → 31 Dec 2026), and six and a half
  months of that window had already elapsed. The ranking does not read 2026
  prices, but the pre-registration's statement that it was "written before any
  2026 outcome data exists" is true only of the year-end outcome price. Any
  amendment (for example a secondary window starting at the freeze date) is an
  owner decision under the pre-registration's own rules and has **not** been
  made.

## 5. What was changed

Nothing published was overwritten. `experiments/results/`, the leaderboard,
the significance report, the frozen 2026 ranking and all pre-registration
documents are byte-identical. Added: `experiments/pit_lag_sensitivity.py`,
`experiments/pit_audit/`, this document, and the corresponding sections of
`RESULTS.md` and `README.md`. The canonical pipeline still builds FY-T
features for target year T+1; switching the canonical design is a
methodology decision for the owner (options in §6).

## 6. Point-in-time limitations matrix

| Issue | Status | Evidence / what remains |
| --- | --- | --- |
| Target leakage (return columns as features) | **SOLVED** | `validate.py` fails the build if any `next_year_*` or same-year return column enters the feature set |
| Frozen vendor snapshots masquerading as history | **SOLVED** | Frozen columns detected and rejected (`frozen_column_evidence.md`); balance-sheet/valuation/growth columns of the corrected files are rejected because they are constant across years |
| Financial-statement publication lag | **PARTIALLY SOLVED** | Quantified here; PIT-correct sensitivity specifications implemented and run. Canonical pipeline unchanged; per-filing KAP timestamps not collected; post-publication target window needs intra-year prices |
| Adjusted price × historical share count | **UNSOLVED** | Market cap and the four ratios built on it are distorted by post-T corporate actions (§2). Fix requires either unadjusted closes with historical shares, or adjusted closes with share counts adjusted by the same factors |
| Pre-listing observations | **UNSOLVED** (in the dataset), **checked** (in this audit) | 16 rows precede the ticker's first Yahoo quote; 14 carry targets that are vendor placeholders (five unlisted tickers share 56.947991 % for 2021). Excluding them does not change any conclusion (§3) |
| Two target-instrument definitions | **PARTIALLY SOLVED** | Training target: vendor dated calendar-year return. 2026 evaluation: Yahoo adjusted-close year-end return. Rank agreement ρ = 0.994 on 307 overlapping rows, but 28 differ by > 10 pp (e.g. CCOLA 2024: +26.7 % vs −88.6 %, a split-adjustment disagreement). Documented in the pre-registration; not reconciled |
| Retrospective universe construction | **UNSOLVED** for published results | The 40-ticker public cohort was first recorded in June 2026, after the study window; membership-evidence acquisition (`docs/BIST_MEMBERSHIP_*`, Stage-A sourcing) is in progress and not applied to published results |
| Survivorship bias | **UNSOLVED** | No delisting, suspension or failed-company history in the repository; delisted names cannot appear in the cohort |
| Corporate actions in returns | **PARTIALLY SOLVED** | Returns use adjusted series (vendor or Yahoo), so splits/bonus issues do not create spurious returns in most rows; the CCOLA-type disagreements above show the adjustment is not uniformly reliable |
| 2026 forward pre-registration timing | **UNSOLVED** | Frozen mid-window with in-window statement information (§4); amendment is an owner decision |

## 7. Options for the owner (not taken)

1. Make the PIT-lagged specification canonical (FY T−1 statements + year-T
   prices) and keep the current results as a labelled historical artefact.
2. Collect end-of-March prices (Yahoo, the project's existing free source) and
   move the target window to 1 April T+1 → 31 March T+2, which keeps FY-T
   statements and removes the lag without staleness.
3. Rebuild `market_cap` from unadjusted closes and dated share counts.
4. Amend the 2026 pre-registration with a secondary, genuinely forward window.
