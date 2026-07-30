# Serving-heuristic missingness sensitivity (R3-MISS-01)

> **Serving-heuristic sensitivity only — describes how this deterministic ranking recipe responds to missing inputs; it does not measure predictive skill, which remains indistinguishable from the null.**

Predictive skill was not measured. This is a deterministic sensitivity analysis of a fixed ranking recipe's response to omitted inputs. It establishes no predictive edge, alpha, profitability, robustness, reliability, tradability, or deployment validity; the walk-forward IC remains indistinguishable from the null.

## Analysis universe

- Input year: **2025** (authority: forecasting_csv_service.get_options()['default_prediction_year'], cross-checked against max public year)
- Forecast year: **2026** (forecasting_csv_service.inference_forecast target_year = input_year + 1)
- Cohort tickers: **40**
- Selected serving-weight features: **12**
- Service: `backend/app/services/forecasting_csv_service.py` (sha256 `7438ab40a47b5a1122ec8079d977bde7b7482a31f90dee0de79fd0f5f0212cb1`)
- Public dataset: `data/trusted_clean/modeling_dataset_public_2020_2025.csv` (sha256 `891d662f110518508b1474be032e5f4b2274d5c2328f16f56240b4a312914b44`)

## Feature-category authority

- Authority: `data/trusted_clean/feature_passports.json` (feature_passports.json passports[].source_class)
- source_class is a governed provenance classification covering every serving-universe column; used here only as a masking grouping, not a financial-sector taxonomy.

| Category | Selected features |
| --- | --- |
| `derived` | enterprise_value, ev_ebitda, price_drawdown_from_3y_high_pct, price_momentum_2y_pct |
| `unknown` | gross_margin, gross_profit, net_debt, net_income, revenue |
| `vendor_xlsx` | ebitda_growth_pct, net_income_growth_pct |
| `yahoo_fetch` | price_adjclose_t |

## Baseline replay audit

- Unmasked seam replay matches the live service output: **True**
- The unchanged backend service is loaded read-only against an isolated temporary data root via the documented RESEARCH_REPO_ROOT override; the seam replay of the unmasked cohort is byte-compared to the direct service output and fails closed on any difference.

## Rank-delta sign convention

signed_rank_delta = masked_rank - baseline_rank. Ranks are 1-based with rank 1 the highest deterministic score. A POSITIVE signed_rank_delta means the ticker moved to a worse (higher-numbered) rank under masking; a NEGATIVE signed_rank_delta means it moved up (toward rank 1). absolute_rank_delta = abs(signed_rank_delta).

## Missingness semantics

- Representation: null (NaN) written into the service's public input rows
- Service null path: run_forecast drops the feature from the within-year percentile pool, omits its contribution, counts it as missing, and reduces confidence.

## Scenario families (exhaustive, deterministic — no sampling)

| Family | Description | Scenarios |
| --- | --- | ---: |
| A | Dataset-wide category masks: mask all selected features in a category for every ticker. | 4 |
| B | Per-ticker category masks: mask all selected features in a category for one ticker only. | 160 |
| C | Dataset-wide single-feature masks: mask one selected feature for every ticker. | 12 |
| D | Per-ticker single-feature masks: mask one selected feature for one ticker only. | 480 |
| — | Total | 656 |

## Aggregate sensitivity by scenario family

| Family | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| A | 4 | 3.0 | 15 | 0.246356 | 0.4167 |
| B | 160 | 0.4925 | 29 | 0.006159 | 0.4167 |
| C | 12 | 1.466667 | 8 | 0.082096 | 0.0834 |
| D | 480 | 0.169583 | 12 | 0.002053 | 0.0834 |

## Aggregate sensitivity by governed category

| Category | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `derived` | 41 | 0.729268 | 24 | 0.015547 | 0.3333 |
| `unknown` | 41 | 0.89878 | 29 | 0.020326 | 0.4167 |
| `vendor_xlsx` | 41 | 0.391463 | 19 | 0.008131 | 0.1667 |
| `yahoo_fetch` | 41 | 0.195122 | 7 | 0.004064 | 0.0834 |

## Aggregate sensitivity by selected feature

| Feature | Scenarios | Mean abs rank Δ | Max abs rank Δ | Mean abs conf Δ | Max abs conf Δ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ebitda_growth_pct` | 41 | 0.176829 | 9 | 0.004064 | 0.0834 |
| `enterprise_value` | 41 | 0.203659 | 10 | 0.004064 | 0.0834 |
| `ev_ebitda` | 41 | 0.165854 | 9 | 0.003556 | 0.0834 |
| `gross_margin` | 41 | 0.212195 | 9 | 0.004064 | 0.0834 |
| `gross_profit` | 41 | 0.136585 | 8 | 0.004064 | 0.0834 |
| `net_debt` | 41 | 0.190244 | 10 | 0.004064 | 0.0834 |
| `net_income` | 41 | 0.287805 | 12 | 0.004064 | 0.0834 |
| `net_income_growth_pct` | 41 | 0.25 | 11 | 0.004064 | 0.0834 |
| `price_adjclose_t` | 41 | 0.195122 | 7 | 0.004064 | 0.0834 |
| `price_drawdown_from_3y_high_pct` | 41 | 0.257317 | 10 | 0.004064 | 0.0834 |
| `price_momentum_2y_pct` | 41 | 0.192683 | 9 | 0.003861 | 0.0834 |
| `revenue` | 41 | 0.146341 | 10 | 0.004064 | 0.0834 |

## Extreme observed sensitivity (neutral diagnostic)

Deterministic maximum observed rank movement across all scenarios. This is an extreme sensitivity observation, not a claim about model quality, robustness, or reliability.

- Family B / per_ticker / `unknown` (masked ticker `FROTO`): ticker `FROTO` moved 29 rank(s) (absolute 29).

## Row-level evidence

Complete per-ticker-scenario evidence: `experiments/results_missingness/rank_deltas.csv` (26240 rows).

## Limitations and claim boundary

- Serving-heuristic sensitivity only: this measures how one fixed deterministic ranking recipe reacts to omitted inputs, not predictive skill.
- A small rank delta is not robustness, reliability, validation, or stability of predictive skill; the walk-forward IC remains indistinguishable from the null.
- Only the latest public-universe input year and its retrospective cohort are analysed; results do not generalise across years, universes, or regimes.
- Masking uses the service's own null path; no value is fabricated, imputed, zeroed, or sentinel-filled.
- Feature categories are the governed source_class provenance grouping, not a financial-sector taxonomy.
- The selected-weight feature set is fixed from finalized 2020-2024 training; training-time missingness is out of scope.
- Exact byte reproduction is numerical-environment-qualified (Python/platform/package versions).
- Research support only; not investment advice.

> **Serving-heuristic sensitivity only — describes how this deterministic ranking recipe responds to missing inputs; it does not measure predictive skill, which remains indistinguishable from the null.**

Predictive skill was not measured. This is a deterministic sensitivity analysis of a fixed ranking recipe's response to omitted inputs. It establishes no predictive edge, alpha, profitability, robustness, reliability, tradability, or deployment validity; the walk-forward IC remains indistinguishable from the null.

## Ownership

Owner / regeneration command: `make research-missingness`. Generated files must not be hand-edited.
