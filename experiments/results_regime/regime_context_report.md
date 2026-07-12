# Regime Lens report (R2-REGIME-01)

**2020–2025 spans a single extraordinary Turkish macro regime (high inflation, deep TRY depreciation). Model behavior across regimes is therefore untested — this lens shows regime context and will only compute regime-conditional diagnostics when regime diversity exists.**

This is descriptive sensitivity context only. It does not estimate causal effects, investment value, or regime-specific model performance.

## Effective-dated macro context

| Year | CPI YoY | Year-end policy rate | TRY per USD | BIST100 nominal return |
|---:|---:|---:|---:|---:|
| 2020 | 14.60% | 17.00% | 7.37 | 27.38% |
| 2021 | 36.08% | 14.00% | 13.29 | 24.23% |
| 2022 | 64.27% | 9.00% | 18.70 | 185.94% |
| 2023 | 64.77% | 42.50% | 29.52 | 31.96% |
| 2024 | 44.38% | 47.50% | 35.31 | 28.94% |
| 2025 | 30.89% | 38.00% | 42.95 | 12.64% |

Every non-null value carries an effective date and source in `regime_context_report.json`; missing values stay null.

## Diagnostic status

- Status: **not_computed_insufficient_regime_diversity**
- Observed distinct regimes: **1**; required before activation: **2**.
- No per-regime model statistics were computed.

## Findings

- Regime-conditional model diagnostics are untestable with the observed regime diversity and were not computed.
- The macro series are displayed as effective-dated descriptive context only; no causal effect is inferred.
- Nominal TRY, CPI-deflated TRY, and USD-basis evidence remain parallel negative-result analyses; none establishes a reliable predictive edge.

## Limitations

- Only three model test years (2023–2025) are observed, all inside one task-defined 2020–2025 macro period.
- No per-regime statistic, causal effect, or regime-specific predictive edge is estimable from one observed period.
- Multiplicity treatment and low-power limits from the nominal and alternative-basis significance reports remain applicable and unchanged.
- The 81-ticker training cohort is retrospectively fixed rather than verified point-in-time BIST100 membership, so survivorship and universe-selection look-ahead risks remain unresolved.
- Nominal TRY, national-CPI-deflated TRY, and USD-basis returns are separate descriptive bases; none represents investor-specific value or implementability.
- Prediction-artifact byte reproducibility remains numerical-environment-qualified.
- Missing macro observations remain null and are never interpolated or imputed.
- Research support only; not investment advice.
