# FinanceIQ

A reproducible, pre-registered evaluation harness for financial machine
learning, applied to Borsa Istanbul (BIST) equities 2020–2025, with a
documented null result.

**Result in one line:** no model ranks next-year returns better than chance
after correcting for multiple comparisons, and the one positive baseline
number in the published evaluation disappears once features are restricted to
information that was public when the return window began.
Details: [`RESULTS.md`](RESULTS.md).

Research support only; not investment advice.

## 1. Research question

Can one year's public data about a BIST company — financial statements,
valuation, price history — rank companies by the following calendar year's
stock return, out of sample?

## 2. Why naive historical data was unsafe

The first dataset looked like six years of history and was not. Most
fundamentals in the yearly vendor exports were a **2025 snapshot repeated in
every year**: a 2020 row carried 2025 income, valuation and momentum figures.
Training on it would have let the model read the future directly. The pipeline
now detects columns that do not vary across years, records the evidence
([`data/trusted_clean/frozen_column_evidence.md`](data/trusted_clean/frozen_column_evidence.md))
and rejects them; values are never imputed or filled.

## 3. Leakage and data-quality discoveries

| Discovery | Handling |
| --- | --- |
| Frozen 2025 snapshot repeated across years | Detected and rejected per column |
| Price/return columns that would leak the target | Rejected at ingest; the validator fails the build if any target or same-year return becomes a feature |
| Misaligned 2024 balance-sheet block | Affected cells rejected, replaced only by a shape-validated manual correction |
| **Financial-statement publication lag** (2026-10 audit) | Year-T statements are published 5–10 weeks into the T+1 return window. Quantified and corrected in a sensitivity analysis; published results preserved ([audit](docs/audit/PUBLICATION_LAG_AUDIT.md)) |
| Back-adjusted price × historical share count | Market cap and price-based ratios distorted by later corporate actions; documented, not yet fixed |
| Pre-listing rows with vendor placeholder returns | Documented; excluding them changes no conclusion |

## 4. Dataset

- 81 BIST companies (a 40-company public cohort plus 41 training-only),
  feature years 2020–2024 with realised next-year returns, 321 labelled
  company-years; 2025 features are inference-only.
- 40 features: fiscal-year statements, free-derived valuation, prices and
  momentum to 31 December, BIST100 benchmark return.
- Free sources only: vendor yearly exports (cleaned), Yahoo year-end prices,
  manually curated share counts. Missing stays missing.
- Build and validation: [`DATA_PIPELINE.md`](DATA_PIPELINE.md),
  `make data`, `make data-validate`.

## 5. Walk-forward methodology

Features of year T predict the return of year T+1. Each test year is predicted
by models trained only on earlier target years (expanding window):

| Test year | Train target years |
| --- | --- |
| 2023 | 2021–2022 |
| 2024 | 2021–2023 |
| 2025 | 2021–2024 |

Features are rank-normalised within each year. Nine models: three rank
baselines and six ML models from OLS to gradient boosting.
[`METHODOLOGY.md`](METHODOLOGY.md) has the full specification.

## 6. Statistical testing

- Metric: within-year Spearman rank IC, pooled as an equal-weighted mean over
  test years.
- Null: realised returns permuted within each test year (never across years).
- Uncertainty: bootstrap resampling tickers within year.
- Multiplicity: Bonferroni over the six ML models.
- Controls: a positive control (injected synthetic signal), negative controls
  (permuted targets, noise) and planted-defect injection, each registered
  before it ran ([`docs/thesis/`](docs/thesis/README.md)).

## 7. Results

| Model | Pooled IC | Permutation p | Bonferroni p |
| --- | ---: | ---: | ---: |
| Equal-weight baseline | +0.150 | 0.017 | n/a |
| Best ML (ridge) | +0.093 | 0.157 | 0.94 |
| Worst ML (random forest) | −0.153 | 0.018 | 0.11 |

Point-in-time correction (same harness, only information public on the first
day of the return window): equal-weight baseline +0.005 to +0.031
(p ≥ 0.63), every ML model |IC| ≤ 0.10 and p ≥ 0.13 (unadjusted).
Both tables, with sources: [`RESULTS.md`](RESULTS.md).

## 8. Power and interpretation

With three test years of 80 companies the smallest reliably detectable
|IC| is about 0.18; the positive control reached 80 % detection only at an
injected IC of 0.4. So the result means **no large edge**, not no edge. It
covers one high-inflation period in nominal TRY and a retrospectively chosen
universe, and it says nothing about market efficiency in general.

## 9. Reproducibility

- Pinned numerical environment (`requirements-root.txt`: numpy 1.26.4,
  scikit-learn 1.5.1); each experiment run writes a manifest with git SHA,
  input checksums and package versions
  ([`experiments/results/runs/`](experiments/results/runs/)).
- Results are reproduced byte-for-byte on the machine of record; across
  platforms, OLS on collinear rank features differs in the third decimal.
- Pre-registrations freeze inputs and decision rules before outcomes exist;
  [`docs/PREREGISTERED_2026_EVALUATION.md`](docs/PREREGISTERED_2026_EVALUATION.md)
  is the forward test (see its timing limitation below).
- CI ([`.github/workflows/verify.yml`](.github/workflows/verify.yml)) runs the
  root and backend suites, data validation, claim and documentation lints;
  [`secret-scan.yml`](.github/workflows/secret-scan.yml) gates new commits.

## 10. Known limitations

- Canonical features still pair fiscal-year-T statements with the T+1 window;
  the corrected analysis is a sensitivity study, not the canonical pipeline.
- Market cap and its ratios use back-adjusted prices with historical share
  counts.
- No point-in-time index membership, delisting or survivorship data.
- The 2026 forward ranking was frozen on 2026-07-15, inside its own outcome
  window, from statements published in that window.
- Small sample: three test years, ~80 companies per year.

Full matrix: [`docs/audit/PUBLICATION_LAG_AUDIT.md` §6](docs/audit/PUBLICATION_LAG_AUDIT.md#6-point-in-time-limitations-matrix).

## 11. How to verify

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-root.txt
make data-validate                                       # dataset passes its guards
PYTHONPATH=. .venv/bin/python experiments/pit_lag_sensitivity.py   # published + PIT-corrected numbers
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q        # root suite
cd backend && ../.venv/bin/python -m pytest tests/ -q     # backend suite
```

The application around the harness (FastAPI backend, React "Research
Terminal" frontend, optional explanation-only LLM research assistant,
deployment) is documented in [`docs/OPERATIONS.md`](docs/OPERATIONS.md).
How the project was run — agent rules, task ledger, plans — is in
[`docs/process/`](docs/process/README.md).

### How this was built

Built with AI coding agents under a spec → review → CI-gate workflow. I own
the research design, the engineering decisions, the acceptance criteria and
the validation: I wrote the specifications and pre-registrations, reviewed
changes before they merged, and decided what counts as evidence. Agents wrote
much of the code; they did not decide the methodology.
