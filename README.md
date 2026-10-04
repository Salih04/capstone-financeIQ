# FinanceIQ

A reproducible evaluation harness for financial machine learning on Borsa
Istanbul (BIST) equities, 2020–2025, and the record of a result that did not
survive its own audit.

**Result:** an apparent weak signal (equal-weight baseline IC +0.150,
p = 0.017) turned out to use annual financial statements before they were
public. Re-evaluated point-in-time, it is +0.031 (p = 0.63), and no ML model
is distinguishable from chance. In this sample and design there is no
evidence of a large reproducible predictive edge; effects smaller than
|IC| ≈ 0.19 are below what the study can detect.
Full account: [`RESULTS.md`](RESULTS.md).

Research support only; not investment advice.

## 1. Hypothesis

Can one year's public data about a BIST company — financial statements,
valuation, price history — rank companies by their next-year stock return,
out of sample?

## 2. Original design

- 81 companies (a 40-company public cohort plus 41 training-only), fiscal
  years 2020–2024 with realised next-year returns.
- 40 features of year T; target: calendar-year T+1 return.
- Expanding-window walk-forward, test years 2023–2025, ~80 companies each;
  three rank baselines and six ML models.
- Within-year Spearman IC pooled over test years; within-year permutation
  null; bootstrap CIs; Bonferroni over the ML models.
- Earlier data defects were caught and handled: a 2025 snapshot repeated
  across all years in the vendor exports
  ([evidence](data/trusted_clean/frozen_column_evidence.md)), return columns
  that would leak the target, a misaligned 2024 balance-sheet block.
  Values are never imputed.

[`METHODOLOGY.md`](METHODOLOGY.md), [`DATA_PIPELINE.md`](DATA_PIPELINE.md).

## 3. Contamination discovered

A pre-publication audit on 2026-10-04 found that year-T features were full
fiscal-year-T statements, which Turkish listed companies publish 60–70 days
after year-end (FY2023: up to 20 May 2024). The return window began on
1 January, so 31 of 40 features were used weeks before they existed publicly.
It also found market value built from a back-adjusted price times a
historical share count, and pre-listing rows carrying vendor placeholder
returns. [Audit](docs/audit/PUBLICATION_LAG_AUDIT.md).

## 4. Corrected point-in-time protocol

- Each feature's timestamp is when its information became public; a
  machine-readable [registry](data/pit/feature_availability_registry.json)
  records source, period, availability rule and transformation for all 40.
- A [guard](experiments/pit/guard.py) refuses any value whose timestamp is
  after the prediction time, any unregistered feature and any training label
  realised too late. Tests inject future-available features and the original
  design, and check that each is rejected.
- Statements count as public from their statutory deadline (standardized
  conservative cutoff; exact filing dates were verified for only 6
  company-years, so that mode is implemented but not run). Signal and return
  start on the first trading day after 31 May of T+1; end of March was
  rejected because it precedes the FY2023 deadline.
- Market value on one adjustment basis, or excluded; rows without a quote at
  the prediction date, or with corporate-action defects, excluded.

[Protocol](docs/PIT_PROTOCOL.md). Registered before its outcomes, but after
the audit: the boundary between pre-registered and post-hoc work is set out in
the [amendment](docs/PREREGISTRATION_AMENDMENT_2026-10-04.md).

## 5. Corrected result

| | Original (preserved) | Point-in-time |
| --- | --- | --- |
| Equal-weight baseline IC (p) | +0.150 (0.017) | **+0.031 (0.63)** |
| ML models, IC range | −0.153 … +0.093 | −0.021 … +0.073 |
| Smallest ML Bonferroni p | 0.11 | 1.00 |
| Same FY-T statements alone | +0.193 used before publication | +0.041 used after it |

The last row is the clearest evidence: the statements carried the signal only
while they were used before they were public.
[Full report](experiments/results_pit_v2/REPORT.md).

## 6. Power

Minimum detectable |IC| at 80 % power is about 0.19 (3 test years × 78
companies). A registered positive control detected an injected IC of 0.3 only
62 % of the time; negative controls kept false positives at 2.6–2.8 % against
a 5 % level. The harness controls false positives but sees only large
effects: a null here means "no large edge", not "no edge".

## 7. Remaining limitations

- Survivorship: **unresolved.** The 81 companies were chosen in 2026 from
  then-current listings; no delisted company can appear.
- Exact filing timestamps not collected; conservative deadlines used.
- One high-inflation nominal-TRY period; three test years.
- The 2026 forward pre-registration was frozen inside its own outcome window
  with in-window statement information; it stays as registered and will be
  reported with that exposure.

All limitations: [`RESULTS.md` §6](RESULTS.md#6-remaining-limitations).

## Verify

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-root.txt
make data-validate                                              # dataset guards
PYTHONPATH=. .venv/bin/python -m pytest tests/ -q               # root suite
PYTHONPATH=. .venv/bin/python experiments/pit_v2_evaluation.py  # point-in-time result
PYTHONPATH=. .venv/bin/python experiments/pit_lag_sensitivity.py  # audit reruns
cd backend && ../.venv/bin/python -m pytest tests/ -q            # backend suite
```

Each run records git SHA, input checksums and package versions. OLS on
collinear rank features differs in the third decimal across BLAS builds.
CI: [`verify.yml`](.github/workflows/verify.yml),
[`secret-scan.yml`](.github/workflows/secret-scan.yml).

The application around the harness (FastAPI backend, React frontend,
explanation-only LLM assistant) is in [`docs/OPERATIONS.md`](docs/OPERATIONS.md);
process records in [`docs/process/`](docs/process/README.md).

### How this was built

Built with AI coding agents under a spec → review → CI-gate workflow. I own
the research design, methodological decisions, acceptance criteria and
validation.
