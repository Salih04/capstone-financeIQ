# Stage 3 defect-injection report

- Decision: **INCONCLUSIVE**
- Source: `data/trusted_clean/modeling_dataset_training_2020_2025.csv`
- Source SHA256: `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`
- Primary estimand: binary detection by the frozen existing guard map.
- Integrity and containment are evaluated before the PASS/FAIL decision.
- The secondary IC is per-split, descriptive, non-gating, and is not a significance test.

## Per-defect status

| ID | Defect | Status | Expected | Detected by | Secondary IC |
|---:|---|---|---|---|---|
| 4000 | FUTURE_YEAR_FEATURE_LEAKAGE | NOT_DETECTED | NOT_DETECTED | none | computed |
| 4001 | T_TPLUS1_MISALIGNMENT | NOT_DETECTED | NOT_DETECTED | none | computed |
| 4002 | TARGET_LEAKAGE_INTO_FEATURES | DETECTED | DETECTED | GS_CELL_PROVENANCE_COLUMN_COVERAGE | not computed |
| 4003 | LOOKAHEAD_UNIVERSE_MEMBERSHIP | NOT_DETECTED | NOT_DETECTED | none | computed |
| 4004 | DUPLICATE_ROW_INFLATION | DETECTED | DETECTED | GS_DUP_VALIDATE_ISSUE, GS_DUP_ALT_TARGETS, GS_CELL_PROVENANCE_DUP_KEY | not computed |

## Claim boundary

This report can establish only whether the five preregistered synthetic constructions were detected by the preregistered existing guards. It does not establish absence of all leakage, universal pipeline safety, predictive edge, alpha, investment value, or production readiness. Research support only; not investment advice.
