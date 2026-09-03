# Stage 2 expanded negative-control report

This report characterizes the registered apparatus constructions. It is research support only, not investment advice.

**Stage 2 gate status:** PASS

## Confirmatory controls

| Control | Analyzable / registered | Rejections X | FPR X / 1000 | Wilson 95% | Complete |
| --- | ---: | ---: | ---: | --- | --- |
| NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN | 1000 / 1000 | 26 | 0.026000 | [0.017804, 0.037824] | yes |
| NC1_TARGET_PERMUTATION | 1000 / 1000 | 28 | 0.028000 | [0.019442, 0.040170] | yes |

The confirmatory rule is family rejection when min(1, 6 × minimum raw two-sided p) < 0.05. A complete control fails at X ≥ 65; incomplete denominators are inconclusive.
The Wilson intervals and the equivalence delta are descriptive and non-gating.

## Diagnostic arm

NC0_MASK_ALIGNED_DIAGNOSTIC is DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY. Its output is isolated from the confirmatory gate.

## Integrity

Closed integrity contract passed: **True**.

## Limitations

- These controls characterize apparatus behavior under the registered constructions only.
- The diagnostic uses a target-associated real mask and is not an exact null-FPR test.
- Passing this stage would not establish absence of feature-side PIT or alignment leakage.
- Research support only; not investment advice.
