# Leave-one-out IC influence diagnostics

## Scope and estimand

This R3-INF-01 artifact measures, for every model and every ticker-year observation in the persisted walk-forward dumps, the change in that model's pooled within-year Spearman IC when the single observation is removed and its year is re-scored on the remaining usable rows (`delta_pooled_ic = loo_pooled_ic - full_pooled_ic`). The pooled IC is the equal-weighted mean of the three within-year Spearman ICs, reused verbatim from `experiments/significance.py`. It does not retrain models, change any ranking, or compare raw prediction magnitudes across models.

**Influence values describe the sensitivity of a null-consistent estimate to single observations; they do not identify mispriced stocks or opportunities.**

## Provenance and regeneration

Generator: `experiments/influence_map.py` via `make research-influence`. Seedless leave-one-out arithmetic; no sampling.

| Source artifact | SHA-256 | Rows |
|---|---|---:|
| experiments/results/predictions_test_2023.csv | `c954822ec52c4bdc7704cc0c7d9ac26c58817b2a75ec92c842915603eb5b72c8` | 720 |
| experiments/results/predictions_test_2024.csv | `cf88016a3f310811baaf3fed677230ffd98db4db0ea1417393c9afe87bb4c457` | 720 |
| experiments/results/predictions_test_2025.csv | `295dac3a1b056aa20b9320ff0844ec3cd6aca61fd602f195258a4bc7182cafb1` | 720 |

The machine-readable report and `influence_by_observation.csv` contain the complete per-observation Δ records with explicit insufficient-data statuses.

## Per-model influence summary

| Model | Kind | Full pooled IC | Complete obs | Top-5 \|Δ\| share | Most influential (ticker-year, Δ) | Status |
|---|---|---:|---:|---:|---|---|
| baseline_equal_weight | baseline | 0.149672565 | 240 | 0.0707474424 | AKENR 2024, 0.0113488285 | complete |
| baseline_rank_score | baseline | 0.149672565 | 240 | 0.0707474424 | AKENR 2024, 0.0113488285 | complete |
| elasticnet | ml | -0.0198241823 | 240 | 0.0781833354 | MIATK 2023, -0.0132686518 | complete |
| gradient_boosting | ml | -0.1052534007 | 240 | 0.0760320756 | SMRTG 2025, -0.0127000012 | complete |
| lasso | ml | 0.0895453259 | 240 | 0.0807700937 | KONTR 2024, 0.0139898662 | complete |
| linear_regression | ml | 0.0458661966 | 240 | 0.0789133903 | KONTR 2024, 0.0132361427 | complete |
| random_forest | ml | -0.1532838069 | 240 | 0.0769220555 | SMRTG 2025, -0.013810696 | complete |
| ridge | ml | 0.0926550373 | 240 | 0.0812407294 | KONTR 2024, 0.0149843125 | complete |
| robust_rank_aggregation | baseline | 0.1277566152 | 240 | 0.0741112674 | PASEU 2024, 0.012367399 | complete |

## Interpretation boundaries

- Δ values are a sensitivity diagnostic of an estimate already indistinguishable from the within-year null; they do not test predictive performance.
- Both signs are reported: some single observations prop the pooled IC up and others pull it down, and neither direction is evidence about a ticker.
- Raw prediction magnitudes are never compared across models because their scales differ by model; only within-year ranks enter the Spearman IC.
- Any absent or insufficient observation, year, or model is retained as an explicit null with a status rather than filled or inferred.

## Limitations

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- Only three target years are represented, all within one unusual nominal-TRY macro regime; influence rankings do not establish regime robustness.
- High single-observation influence describes estimator fragility under a tiny sample, not opportunity, economic value, trading profitability, or predictive validity.
- Influence is a retrospective, in-sample sensitivity diagnostic; it is not a causal, forward-looking, or out-of-sample statement about any ticker.
- The analysis adds no significance test and does not change the existing multiplicity correction, low-power limits, or null-consistent conclusion.
- The pooled IC and its inputs remain point estimates from three test years; a large |Δ| does not make the underlying pooled IC distinguishable from the null.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
