# Stage 3 R2 integrity-accounting amendment

**Amendment ID:** `FINANCEIQ-THESIS-STAGE3-R2-INTEGRITY-ACCOUNTING`  
**Dated:** 2026-09-06  
**Status:** **REGISTERED / NOT IMPLEMENTED / NOT ADJUDICATED**

This is a narrow, inert preregistration package. It registers a retrospective
accounting contract for the existing frozen Stage 3 attempt-1. It does not
implement an adjudicator, repair the Stage 3 runner, execute adjudication, or
generate a scientific observation.

## Authority and frozen historical state

The authoritative base is `d4e7196fc43098f18b888ad602d1f1cd06101829`.
Attempt-1 evidence was frozen at `31643f19d58639b6aa4575625b4460dbdb4ab9b8`,
with post-run governance at `972f30adcf0f0419cec6fd71bfedb7967fad9ed2`.
Attempt-1 is `attempt_number=1`, `attempt_type=initial`, `status=complete`,
and `prior_incomplete_attempt=false`. Its original authoritative decision is
permanently **INCONCLUSIVE**. The sole failed integrity condition is
`clean_comparator_byte_and_logical_identity`.

The observed attempt-1 matrix is retained as historical evidence only:

| Defect | Observed status |
|---|---|
| 4000 `FUTURE_YEAR_FEATURE_LEAKAGE` | `NOT_DETECTED` |
| 4001 `T_TPLUS1_MISALIGNMENT` | `NOT_DETECTED` |
| 4002 `TARGET_LEAKAGE_INTO_FEATURES` | `DETECTED` |
| 4003 `LOOKAHEAD_UNIVERSE_MEMBERSHIP` | `NOT_DETECTED` |
| 4004 `DUPLICATE_ROW_INFLATION` | `DETECTED` |

This matrix happens to match the prospective expectation map, but expectation
agreement is explicitly excluded from the R2 evidence chain. It must not relabel
the original decision.

## Proven accounting defect and Option A

Attempt-1 implemented the clean fingerprint gate as:

```text
len(clean_fingerprints) == len(set(clean_fingerprints)) == 1
```

For five identical fingerprints this evaluates as `5 == 1 and 1 == 1`, so it
cannot pass for the registered five-defect family. The root-cause classification
is `C_FINGERPRINT_ACCOUNTING_FALSE_POSITIVE`. attempt-1 did **not** persist the
fingerprint values themselves.

The owner-locked choice is **R2 Option A**: missing persisted fingerprint values
do not permanently block re-adjudication. The semantic condition may be derived
from existing frozen evidence, but that derivation is labelled **DERIVED**, not
`OBSERVED_FINGERPRINT_EQUALITY`. The original artifacts are never rewritten.

## R2 predicate

R2 is accounting-only. It may read the existing frozen attempt-1 evidence and
correct only the failed integrity-accounting condition. All other sixteen frozen
integrity conditions must remain true as recorded; they are not recomputed.

### A0 — cardinality

Exactly five frozen defect records must exist, covering registered IDs 4000,
4001, 4002, 4003, and 4004 exactly once. Allowed evidence is limited to the
frozen report defect records and frozen integrity conditions for exact family and
completeness.

### A1 — pinned clean source re-read contract

For every frozen defect record:

```text
source_sha256_before == source_sha256_after == registered DATASET_SHA256
```

The completed run must also prove that its load-time source-integrity gates
completed without raising. R2 does not load the dataset, reconstruct a
DataFrame, or recompute `_frame_fingerprint`.

The registered dataset is
`data/trusted_clean/modeling_dataset_training_2020_2025.csv` with SHA256
`3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.

### A2 — zero clean detection signals

For every frozen defect record:

```text
clean_comparator.detection_signals == []
```

Any non-empty clean detection signal refuses R2 and leaves the original
`INCONCLUSIVE` authoritative.

### A3 — derived clean logical identity

For all five defects, logical identity may be derived only from the frozen
record showing:

- the same pinned source SHA before and after;
- `mechanism_invariants.passed == true`;
- `mechanism_invariants.checks.source_shape_clean == true`;
- `clean_comparator.cleanup_proven == true`;
- `clean_comparator.containment_passed == true`;
- `clean_comparator.invocation_accounting_passed == true`.

This clause is labelled **DERIVED**. It is not observed fingerprint equality,
because attempt-1 did not persist fingerprint values. If any required frozen
input is absent or mismatched, R2 fails closed and the original decision stays
`INCONCLUSIVE`.

## R2 decision and scientific boundary

The future `readjudicated_decision` value is deliberately not preregistered.
The future adjudicator alone may compute it from the frozen per-defect statuses
and the registered R2 predicate. The contract does not hardcode `FAIL` from the
observed matrix. If the retained frozen integrity conditions or A0–A3 fail, the
future result remains `INCONCLUSIVE`.

R2 must not reinject a defect, reevaluate guard surfaces, load source data to
reconstruct fingerprints, refit Ridge, recompute secondary IC, change any
per-defect status or `detected_by` value, change mechanism invariants or
containment results, recompute the other sixteen integrity conditions, use
expectation-match as evidence, or perform a second scientific draw. No second Stage 3 draw and no `--repeat-after-crash` execution is authorized.

The forward runner correction is registered separately for future code repair:

```text
len(clean_fingerprints) == DEFECT_FAMILY_SIZE
and len(set(clean_fingerprints)) == 1
and all(clean comparator detection_signals are empty)
```

Any hypothetical future execution must persist each per-defect clean
fingerprint. This forward predicate is not exercised by R2 attempt-1
re-adjudication.

## Frozen artifact pins

Any mismatch at adjudication time means **R2 REFUSES**:

| Frozen path | SHA256 |
|---|---|
| `experiments/results_thesis/defect_injection/artifact_manifest.json` | `eeb25c9dd9cc0310679dc36470d3a7a913e8595de26649288e23d491db10ed4f` |
| `experiments/results_thesis/defect_injection/attempts/attempt-1.json` | `657d1c777782ed41ec985073cfbf902b9398e56e63f1ae6b88b3fc8d8edb287e` |
| `experiments/results_thesis/defect_injection/defect_injection_report.json` | `877f9367e768ce93c888bf0fec1dd5e7a9caa19369a9bfb5d47a818d2dd43a15` |
| `experiments/results_thesis/defect_injection/defect_injection_report.md` | `d96be144a8ce7ccef37d2daee7a45179aa557002d4faa8262b947d0695109b7c` |
| `experiments/results_thesis/defect_injection/defect_results.csv` | `bde017fa38af1f1446f1cada3c1d2973c5c5b797aa1bfefa2f6dc7dad113b852` |

The Stage 3 registration document and module are also pinned. A module or
document hash mismatch, or a registered Stage 3 configuration mismatch, is an
R2 falsifier:

- `docs/thesis/STAGE_3_REGISTRATION.md` —
  `8153dfe0428faf902a01e83cd2d4c9b66a2c74da1a364dd76cea5f4682a2c621`
- `experiments/thesis/stage3_registration.py` —
  `839c6b8679b703508e0d50f36dde3a0de9861bf9706250138d75ab63f0549f1b`
- registered configuration SHA256 —
  `4594521fde98c92a52400c9a02139c570b3d5241a2abfbd0d6006c213b51c677`

## Recovery defect: registered, not implemented

The known recovery defect is that completion logic incorrectly requires
`integrity_passed == true`, which can classify a complete-but-INCONCLUSIVE
attempt as incomplete. The existing repeat-after-crash path can therefore
delete `defect_injection_report.json`, `defect_injection_report.md`,
`defect_results.csv`, and `artifact_manifest.json`.

The later repair must:

1. separate completion/durability from the integrity verdict;
2. refuse repeat-after-crash if **any** attempt record has `status == complete`;
3. make the cleanup primitive refuse deletion if a complete attempt exists; and
4. remove any operator message that directs a complete run toward
   repeat-after-crash.

This amendment registers those requirements but does not implement them.

## Residual disclosures and falsifiers

The following unrelated Stage 3 accounting limitations remain disclosed and are
not silently repaired:

- attempt-1 fingerprint values were not persisted;
- some integrity conditions are implementation accounting assertions rather than
  independently persisted measurements; and
- the Stage 3 report does not populate the limitations register like some
  earlier thesis reports.

The operator's pre-run shell gate proved a clean worktree immediately before the
governed draw. A later report value `git.dirty=true` may reflect newly created
result artifacts and is not evidence of dirty-at-start.

R2 refuses or remains `INCONCLUSIVE` if any frozen artifact hash, configuration,
registration hash, retained integrity condition, clean signal, pinned source
SHA, or A3 field mismatches; if frozen statuses depend on the accounting bug; if
adjudication requires data loading, injection, guard/model/IC recomputation; if
a second governed draw occurs; or if repeat-after-crash is executed against
attempt-1.

## Result namespace and downstream gate

R2 prospectively registers exactly two generated artifacts under the separate
root `experiments/results_thesis/defect_injection_r2_adjudication/`:

- `stage3_r2_adjudication.json` — the future authoritative R2 adjudication
  record;
- `stage3_r2_adjudication.md` — its future human-readable companion.

The root is absent now. It has no `attempts/` directory and no scientific-run
manifest. No R2 result is created during registration.

Stage 7 remains **BLOCKED**. Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**,
Stage 3 has not passed, and R2 registration cannot unlock any downstream stage.
This amendment establishes no predictive or investment claim. Research support
only, not investment advice.
