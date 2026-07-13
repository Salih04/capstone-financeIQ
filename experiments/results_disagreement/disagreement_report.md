# Model disagreement atlas

## Scope and estimand

This R3-STAT-02 artifact compares each model's within-year, within-model prediction ranks. For every target year it reports the 9×9 pairwise Spearman matrix; for every ticker-year it reports the max−min rank spread and IQR across the nine model ranks. It does not compare raw prediction magnitudes across models.

**Model disagreement measures instability of a signal already indistinguishable from the null; high agreement between models is not evidence of predictive validity.**

## Provenance and regeneration

Generator: `experiments/disagreement_atlas.py` via `make research-disagreement`.

| Source artifact | SHA-256 | Rows |
|---|---|---:|
| experiments/results/predictions_test_2023.csv | `c954822ec52c4bdc7704cc0c7d9ac26c58817b2a75ec92c842915603eb5b72c8` | 720 |
| experiments/results/predictions_test_2024.csv | `cf88016a3f310811baaf3fed677230ffd98db4db0ea1417393c9afe87bb4c457` | 720 |
| experiments/results/predictions_test_2025.csv | `295dac3a1b056aa20b9320ff0844ec3cd6aca61fd602f195258a4bc7182cafb1` | 720 |

The machine-readable report contains the complete ticker-year spread records. `disagreement_matrix.csv` contains the complete, deterministic pairwise matrix with explicit insufficient-data statuses.

## Descriptive summaries

| Target year | Off-diagonal Spearman median | Rank-spread median | Rank-IQR median | Pairwise insufficient cells | Ticker insufficient rows |
|---:|---:|---:|---:|---:|---:|
| 2023 | 0.1136178112 | 50.0 | 30.0 | 0 | 0 |
| 2024 | 0.2551636883 | 46.5 | 22.5 | 0 | 0 |
| 2025 | 0.0387847446 | 51.5 | 29.5 | 0 | 0 |

## Interpretation boundaries

- The matrix and spread rows are descriptive rank-agreement diagnostics only; they do not test predictive performance.
- Raw prediction magnitudes are never compared across models because their scales differ by model.
- Any absent or insufficient rank evidence is retained as an explicit null/status rather than filled or inferred.

## Limitations

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- Only three target years are represented, all within one unusual macro regime; this atlas does not establish regime robustness.
- Rank agreement or disagreement describes model instability, not opportunity, economic value, trading profitability, or predictive validity.
- The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.
- Raw y_pred scales differ by model and are deliberately never compared across models; ties receive average ranks.
- Missing or non-finite predictions are never imputed. Insufficient pairwise or ticker-year evidence is reported as null with an explicit status.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
