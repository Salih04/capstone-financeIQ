# Alternative target derivation report (R2-REAL-01)

The canonical nominal TRY targets are preserved byte-for-byte. CPI-deflated TRY and USD-basis targets are additive, descriptive research evidence only — not investment value or investment advice.

## Design

- Real TRY: `((1 + nominal_try_pct/100) / (1 + cpi_december_yoy_pct/100) - 1) * 100`
- USD basis: `((1 + nominal_try_pct/100) * usdtry_T / usdtry_T1 - 1) * 100`
- FX direction: TRY per USD; T divided by T+1
- Missing values: null propagation; no interpolation or imputation

## Coverage

- Rows: **403**
- Nominal target rows: **321**
- Real target rows: **321**
- USD target rows: **321**

These transformations do not establish a reliable predictive edge. Significance and multiplicity treatment are applied separately in `experiments/results_real_terms/` before any result is quoted.
