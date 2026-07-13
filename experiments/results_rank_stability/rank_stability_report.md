# Ranking & cohort stability diagnostics

## Scope and estimands

This R3-STAT-01 artifact measures, from the persisted walk-forward dumps only, three separate and un-combined quantities: (a) each ticker's within-year rank-position variability and top-10 membership stability under seeded within-year ticker bootstraps; (b) each model's pooled within-year Spearman IC dispersion under leave-1-out and seeded leave-8-out jackknife over ticker-year observations; and (c) each model's pooled IC recomputed on the public-40 cohort with per-year n. The pooled IC reuses `experiments/significance.py` verbatim. It does not retrain models, change any production ranking, compare raw prediction magnitudes across models, or produce any new significance test or p-value.

**Stability frequencies describe resampling variability of a ranking already indistinguishable from the null; a frequently-top-ranked ticker is not a validated pick.**

Top-k membership frequency is a mechanical consequence of frozen predictions. A ticker with full-cohort rank <= k gets frequency 1.0 by construction. Frequencies are near-deterministic transforms of fixed full-cohort rank and n, not evidence of model/data-driven stability.

## Provenance and regeneration

Generator: `experiments/rank_stability.py` via `make research-rank-stability`. Seed 42; 2000 within-year bootstrap draws per model-year; 2000 leave-8-out samples per model. Resampling unit: ticker within a single test year (never rows pooled across years).

| Source artifact | SHA-256 | Rows |
|---|---|---:|
| experiments/results/predictions_test_2023.csv | `c954822ec52c4bdc7704cc0c7d9ac26c58817b2a75ec92c842915603eb5b72c8` | 720 |
| experiments/results/predictions_test_2024.csv | `cf88016a3f310811baaf3fed677230ffd98db4db0ea1417393c9afe87bb4c457` | 720 |
| experiments/results/predictions_test_2025.csv | `295dac3a1b056aa20b9320ff0844ec3cd6aca61fd602f195258a4bc7182cafb1` | 720 |
| data/config/universe_public_40.csv | `db7ffc577d7d10d34b47aaaa578226ef9d4bf19920816d250a7703dc9bbf51db` | 40 |

The machine-readable report and `stability_by_ticker.csv` carry the complete per-ticker rank intervals, top-10 frequencies, and explicit insufficient-data statuses.

## Per-model pooled-IC uncertainty and cohort sensitivity

| Model | Kind | Full pooled IC | LOO IC mean (p2.5–p97.5 of deletion estimates) | k=8 IC std | Public-40 pooled IC | Public-40 per-year n |
|---|---|---:|---|---:|---:|---|
| baseline_equal_weight | baseline | 0.149672565 — reported as descriptive baseline context outside the six-model ML correction family, not as a validated edge | 0.1496645222 [0.1412886679, 0.1589247318] | 0.0119125838 | -0.0947080266 | 2023:40, 2024:40, 2025:40 |
| baseline_rank_score | baseline | 0.149672565 | 0.1496645222 [0.1412886679, 0.1589247318] | 0.0119358291 | -0.0947080266 | 2023:40, 2024:40, 2025:40 |
| elasticnet | ml | -0.0198241823 | -0.0198233231 [-0.0281570411, -0.0097307858] | 0.012588172 | -0.061969733 | 2023:40, 2024:40, 2025:40 |
| gradient_boosting | ml | -0.1052534007 | -0.1052479192 [-0.1150617536, -0.0961359337] | 0.0123986259 | -0.1759844859 | 2023:40, 2024:40, 2025:40 |
| lasso | ml | 0.0895453259 | 0.0895409668 [0.0809115937, 0.0996774248] | 0.0123036632 | 0.0123221954 | 2023:40, 2024:40, 2025:40 |
| linear_regression | ml | 0.0458661966 | 0.0458635279 [0.0369226206, 0.055525336] | 0.0130171617 | 0.0030644387 | 2023:40, 2024:40, 2025:40 |
| random_forest | ml | -0.1532838069 | -0.1532756809 [-0.161786313, -0.1445824034] | 0.0118052164 | -0.1480288216 | 2023:40, 2024:40, 2025:40 |
| ridge | ml | 0.0926550373 | 0.0926505855 [0.0844441939, 0.1018261998] | 0.012435367 | 0.0404684698 | 2023:40, 2024:40, 2025:40 |
| robust_rank_aggregation | baseline | 0.1277566152 | 0.1277494652 [0.1194171225, 0.1369535601] | 0.0118342357 | -0.0995148458 | 2023:40, 2024:40, 2025:40 |

These deletion ranges are not confidence intervals for the IC and should not be interpreted as uncertainty intervals for predictive performance.

The public-40 column is a cohort-composition sensitivity reported with per-year n; it is not a comparison establishing that either cohort is a better or more tradeable universe.

## Interpretation boundaries

- Top-k membership frequency is a mechanical consequence of frozen predictions. A ticker with full-cohort rank <= k gets frequency 1.0 by construction. Frequencies are near-deterministic transforms of fixed full-cohort rank and n, not evidence of model/data-driven stability.
- Top-k membership frequency and rank intervals describe resampling variability of a ranking already indistinguishable from the within-year null; they are not pick-confidence.
- The jackknife dispersion measures how much the pooled IC moves under small cohort perturbations; it is not a confidence interval on any stock outperforming.
- The public-40 pooled IC is a cohort-composition sensitivity, reported with per-year n; it is not a claim that one cohort is a better or more tradeable universe.
- Raw prediction magnitudes are never compared across models because their scales differ by model; only within-year ranks enter the diagnostics.
- Distinct quantities are kept separate and are never collapsed into one confidence score; any absent or thin observation, year, or cohort stays an explicit null with a status.

## Limitations

- This is the retrospective 81-ticker training universe with 80 evaluated rows per model-year, not verified point-in-time BIST100 membership; survivorship and universe-selection risks remain.
- The public-40 subset is a fixed repository cohort, not point-in-time index constituents; sector membership, liquidity, tradeability, and corporate-action history are not inferred here.
- Only three target years are represented, all within one unusual nominal-TRY macro regime; stability rankings do not establish regime robustness.
- Stability under resampling is not predictive validity: a stable but null-consistent ranking remains indistinguishable from noise, and an unstable ranking does not establish opportunity.
- Top-k membership frequency is conditional on being drawn and is a resampling artifact; it is not a probability that a ticker will outperform.
- The jackknife dispersion describes the pooled IC estimator's fragility under a tiny three-year sample, not economic value, trading profitability, or out-of-sample skill.
- Ticker-year deletion units are treated as exchangeable only for this descriptive sensitivity diagnostic. Repeated tickers across years and within-year cross-sectional dependence prevent interpretation as sampling uncertainty.
- No new significance test or p-value is produced; the existing multiplicity correction, low-power limits, and null-consistent conclusion are unchanged.
- This report uses nominal-TRY persisted dumps only and does not replace or merge the parallel real-TRY or USD-basis evidence.
- Reproduction is numerical-environment-qualified; deterministic byte identity is demonstrated only in the current environment.
- Research support only; not investment advice.

The conclusion remains: no reliable predictive edge. Research support only; not investment advice.
