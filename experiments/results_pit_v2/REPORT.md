# PIT-v2 results (2026-10-04)

Post-hoc stage, registered before outcomes in
[`docs/PREREGISTRATION_AMENDMENT_2026-10-04.md`](../../docs/PREREGISTRATION_AMENDMENT_2026-10-04.md)
(commit `079bb832`); run from that clean commit. Protocol:
[`docs/PIT_PROTOCOL.md`](../../docs/PIT_PROTOCOL.md). Machine-readable output:
[`report.json`](report.json) (input hashes, environment, every statistic).

Mode: `STANDARDIZED_CONSERVATIVE_CUTOFF`. Test cross-sections: fiscal years
2022, 2023, 2024 (78, 78, 79 companies), predicted from 1 June 2023,
3 June 2024 and 2 June 2025 respectively.

## Primary estimand

| Model | Pooled IC | Permutation p | 95 % bootstrap CI |
| --- | ---: | ---: | --- |
| **Equal-weight baseline** | **+0.031** | **0.63** | −0.100 … +0.162 |

By test year: +0.145 (FY2022), −0.051 (FY2023), −0.000 (FY2024).

**Registered interpretation (cell 1):** in this sample and design, the
corrected evaluation found no evidence of a large reproducible predictive
edge; effects smaller than |IC| ≈ 0.185 (80 % power, three years of 78
companies) remain outside the study's detection power.

## Secondary family (six ML models, Bonferroni over six)

| Model | Pooled IC | p | Bonferroni p |
| --- | ---: | ---: | ---: |
| OLS | +0.073 | 0.27 | 1.00 |
| Ridge | +0.001 | 0.99 | 1.00 |
| Lasso | +0.056 | 0.39 | 1.00 |
| Elastic net | −0.021 | 0.75 | 1.00 |
| Random forest | −0.021 | 0.75 | 1.00 |
| Gradient boosting | +0.028 | 0.68 | 1.00 |

## Registered sensitivities (descriptive; p unadjusted unless stated)

| Specification | Features | Equal-weight IC (p) | ML IC range | Smallest ML p (Bonferroni over six) |
| --- | ---: | --- | --- | --- |
| Primary | 38 | +0.031 (0.63) | −0.021 … +0.073 | 0.27 (1.00) |
| S1 cutoff at end of deadline month (31 Mar; 31 May for FY2023) | 38 | +0.102 (0.12) | −0.039 … +0.126 | 0.053 (0.32) |
| S2 without market-value features | 33 | +0.044 (0.50) | −0.084 … +0.027 | 0.21 (1.00) |
| S3 price features only | 6 | −0.004 (0.95) | +0.036 … +0.109 | 0.098 (0.59) |
| S4 statement features only | 27 | +0.041 (0.54) | −0.176 … −0.003 | **0.007 (0.041), random forest, negative** |

Read with the registration: sensitivities make no claim on their own. Across
the four sensitivities there are 24 ML tests; the S4 random-forest result
would not survive a correction over all of them (24 × 0.0069 ≈ 0.17). It is
negative in every test year (−0.27, −0.20, −0.05) and mirrors the published
random forest (−0.153). Per the pre-written grid it is a statistical
observation only, not a contrarian signal.

## What changed relative to the published number

| Design | Equal-weight IC (p) |
| --- | --- |
| Published (FY-T statements scored from 1 January T+1) | +0.150 (0.017) |
| Phase-2 audit: statements lagged one fiscal year | +0.005 (0.93) |
| **PIT-v2 primary: FY-T statements scored after they are public** | **+0.031 (0.63)** |
| PIT-v2 S4: FY-T statements only, scored after they are public | +0.041 (0.54) |
| Phase-2 diagnostic, not PIT: FY-T statements only, scored from 1 January T+1 | +0.193 (0.002) |

The audit could not separate look-ahead from staleness, because lagging the
statements by a year also aged them. PIT-v2 uses the *same* fiscal-year-T
statements, only timed after publication, and the signal is gone (+0.193 →
+0.041). That pattern is what look-ahead predicts. It is not an isolated test:
PIT-v2 also changes the return window (June–May instead of the calendar year),
the return source (Yahoo `adjclose` instead of the vendor return) and the rows
evaluated. It does not prove the
statements are uninformative: a window that starts at the statutory deadline
rather than at 31 May (S1, +0.102, p = 0.12) is closer to publication, and the
study cannot detect effects of that size.

## Data handled

| Item | Count (evaluable fiscal years 2020–2024, 323 published rows) |
| --- | ---: |
| Rows evaluated (primary) | 308 |
| Excluded: no quote at the prediction date (pre-listing) | 11 |
| Excluded: one-day move beyond ±25 % in the target window | 4 |
| Market value valid on one adjustment basis | 164 |
| Market value excluded: share record disagrees with Yahoo split history | 27 |
| Market value excluded: unexplained close jump after year-end | 5 |
| Market value unavailable: no share count (training-only companies) | 123 |
| Statement values masked as not yet public (primary / S1) | 0 / 31 (SASA FY2022) |

`price_history_years_available` counts years of quotes in the fetched history,
which starts on 2 January 2017; for companies listed earlier it is a capped
value, not listing age.

## Reproduce

```bash
pip install -r requirements-root.txt
PYTHONPATH=. python -m pytest tests/test_pit_guard.py tests/test_pit_prices.py -q
PYTHONPATH=. python experiments/pit_v2_evaluation.py
```

The derived price panels in `data/pit/derived/` are the registered inputs;
rebuilding them from a fresh Yahoo fetch can change `adjclose` slightly
(see `data/pit/README.md`).
