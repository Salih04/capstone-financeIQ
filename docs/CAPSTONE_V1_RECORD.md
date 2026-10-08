# Capstone v1 record

**Status:** complete and frozen. This is the historical record of FinanceIQ’s original annual
Borsa Istanbul equity-ranking study. Research support only; not investment advice.

## Study

Capstone v1 asked whether information for year **T** could rank a company’s calendar-year **T+1**
stock return. The fixed public cohort was 40 companies; the training cohort added 41 names (81 in
total), as recorded in [`data/config/`](../data/config/). The modeled feature years were
2020–2024, with realized return years 2021–2025; walk-forward test return years were 2023–2025,
and the 2025 feature-year rows are inference-only.
The 40-company cohort’s selection rule is undocumented, and its raw source files are labelled a
“winner cohort” ([`data/raw/README.md`](../data/raw/README.md)): whether names were filtered or
ranked using realized returns is unknown. See the [universe audit](universe_audit.md).

The design used annual fiscal-year-T fundamentals, valuation and price features to predict the
next calendar-year return, with expanding-window walk-forward evaluation. The implementation
contains three rank baselines (equal-weight, rank-score and robust rank aggregation) and six
supervised estimators: ordinary least squares, ridge, lasso, elastic net, random forest and
gradient boosting. Model definitions and splits are in
[`experiments/run_experiments.py`](../experiments/run_experiments.py).

## Reproduction map

- **Code:** data preparation in [`scripts/data_collection/`](../scripts/data_collection/);
  original experiments in [`experiments/`](../experiments/), including the PIT guard and
  evaluation runner; application code in [`backend/app/`](../backend/app/) and
  [`frontend/src/`](../frontend/src/).
- **Data:** source and corrected inputs in [`data/raw/`](../data/raw/) and
  [`data/trusted_raw/`](../data/trusted_raw/); generated annual datasets and validation evidence
  in [`data/trusted_clean/`](../data/trusted_clean/); cohort configuration in
  [`data/config/`](../data/config/) and PIT inputs in [`data/pit/`](../data/pit/).
- **Results:** original walk-forward artifacts in [`experiments/results/`](../experiments/results/)
  and publication-lag reruns in [`experiments/pit_audit/`](../experiments/pit_audit/). The
  corrected result is preserved in [`experiments/results_pit_v2/REPORT.md`](../experiments/results_pit_v2/REPORT.md).
  [`RESULTS.md`](../RESULTS.md) is the result index; the
  [2026-10-04 audit](audit/PUBLICATION_LAG_AUDIT.md) documents the timing finding.

Use existing Makefile targets: `make data-validate` validates the retained dataset; `make research`
reruns the original walk-forward on it; `make data` rebuilds the annual dataset; and
`make full-research` rebuilds the legacy pipeline inputs and runs the original experiment. A full
rebuild may refresh source inputs. The Makefile has no PIT-v2 target, so its canonical report and
artifacts remain the reference for the corrected evaluation.

## Limitations and current status

- The 2026-10-04 [publication-lag audit](audit/PUBLICATION_LAG_AUDIT.md) found that annual T
  statements entered the original T+1 return window before they were public.
- Cohort selection is undocumented, and survivorship remains unresolved: the repository has no
  point-in-time membership history or delisted-company coverage for this cohort.
- The short annual evaluation has low statistical power for modest effects; see the canonical
  [results report](../experiments/results_pit_v2/REPORT.md).
- Legacy application routes serving pre-audit results carry the `withdrawn_pre_pit` status; the
  frontend shows a pre-audit notice. The historical baseline interpretation is withdrawn in
  [`RESULTS.md`](../RESULTS.md).
- All new research follows the adopted
  [Research Charter](process/RESEARCH_CHARTER.md); Capstone cohort lists are not a new-study
  universe.

## Proposed annotated tag — not created

- **Name:** `capstone-v1-final`
- **Target:** `7dccc12c8ea939b364cffa9dffd3d32c63d3a04f` — the `main` merge commit that first
  integrated the charter-adoption commit `a89d386520e67978e19f141ac1c7fe246b514634`.
- **Message:** “Mark the main integration boundary where the FinanceIQ Research Charter was adopted
  and Capstone v1 became frozen; subsequent research follows the charter.”
