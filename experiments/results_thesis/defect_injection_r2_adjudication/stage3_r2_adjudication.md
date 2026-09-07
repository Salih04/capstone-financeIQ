# Stage 3 R2 accounting-only adjudication

- Amendment: `FINANCEIQ-THESIS-STAGE3-R2-INTEGRITY-ACCOUNTING`
- Original authoritative decision: **INCONCLUSIVE** (permanent)
- Readjudicated decision: **FAIL** (computed from the frozen per-defect statuses and the R2 integrity result; not preregistered)
- Corrected integrity condition: `clean_comparator_byte_and_logical_identity` = True via **DERIVED** evidence
- A3 clean logical identity is **DERIVED**, never `OBSERVED_FINGERPRINT_EQUALITY`; attempt-1 did not persist fingerprint values.
- Expectation-match is excluded from the evidence chain.
- The other sixteen frozen integrity conditions are carried unchanged and are not recomputed. No per-defect status or `detected_by` value is recomputed.

## R2 predicate

| Clause | Passed |
|---|---|
| A0_CARDINALITY | True |
| A1_PINNED_CLEAN_SOURCE_RE_READ | True |
| A2_ZERO_CLEAN_DETECTION_SIGNALS | True |
| A3_DERIVED_CLEAN_LOGICAL_IDENTITY | True |

## Frozen per-defect statuses (unchanged)

| Defect | Status |
|---:|---|
| 4000 | NOT_DETECTED |
| 4001 | NOT_DETECTED |
| 4002 | DETECTED |
| 4003 | NOT_DETECTED |
| 4004 | DETECTED |

## Scientific boundary

No dataset load, defect injection, guard evaluation, model fit, IC computation, second governed Stage 3 draw, or `--repeat-after-crash` execution occurred. Stage 7 remains **BLOCKED**. Research support only; not investment advice.
