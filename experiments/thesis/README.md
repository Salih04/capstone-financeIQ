# Thesis experiment namespace

Prepared in Week 0/1. **Stage 1 (`positive_control`) is implemented and has
run; Stage 1b (`positive_control_calibration`) is registered, implemented, and
has completed its one governed run; Stage 2 (`negative_control`) is implemented
and has completed its one governed run; Stage 3 (`defect_injection`) is
registered but not implemented or run; the remaining two slugs are still
placeholders.** This directory holds the shared provenance helpers, the
implemented stages, and the rules below.

## Stage 1b — governed run complete; diagnostic/calibration only

`docs/thesis/STAGE_1B_REGISTRATION.md` is the frozen, owner-approved,
prospective (but **not blind**) registration for Stage 1b, a diagnostic /
calibration experiment. `experiments/thesis/stage1b_registration.py` holds its
machine-checkable constants; `tests/test_thesis_stage1b_registration.py` proves
code == registration. **One governed Stage 1b run has completed and its outcome
has been inspected.** It used exactly one attempt (no rerun), completed the
6 × 400 matrix, passed integrity, and produced an identical replay. The result
is diagnostic/calibration only. Stage 1b reuses the Stage 1 carrier (`equity`), model
(`ridge`), splits, significance machinery, seed framework, and the
Stage-1-operational-rule detection point; adds the single grid rung `0.35`; uses `R = 400`
fresh repetitions with global ids `200 … 599` (non-overlapping with Stage 1's
`0 … 199`); excludes the historical `current_ratio` and theta=0.90 arms; and
has **no scientific performance PASS/FAIL gate**.

The runner is `experiments/thesis/positive_control_calibration.py`, invoked by
`make thesis-stage1b`; `make thesis-stage1b-replay` is its determinism probe and
writes nothing. Both were added *before* the governed run together with the
`governed_roots` entry and one ownership contract per emitted output. **The Stage
1b result root is present from that one governed run**, and nothing but the one
governed run may create it.

Two properties the runner is built around, both machine-checked in
`tests/test_thesis_stage1b_implementation.py`:

- **The operating divisor is a frozen literal.** The primary rule is the
  unchanged Stage 1 operating point `min(1, 5 * p_raw) < 0.05`. The `5` comes
  from `stage1b_registration.STAGE1_OPERATIONAL_DIVISOR` and is never recomputed
  from a grid length or a family size; the six theta levels are not a hypothesis
  family, and the AST-level test proves the detection functions reference
  nothing else.
- **Seed identity comes from the frozen map.** Report order is numeric, but seed
  level indices come from `stage1b_registration.level_index_for` — never from
  `enumerate` — so `0.40` keeps index 4 and `0.35` takes the new index 5. The
  runner contains no `enumerate` call at all.

The runner takes no scientific parameters: the grid, `R`, seeds, permutations,
bootstraps, alpha, carrier, model, and detection rules are frozen in the
registration and cannot be reduced or overridden at runtime. It refuses to do
anything without an explicit `--run` or `--repeat-after-crash`, so ordinary
verification cannot trip the governed run. A durable
`attempt_provenance.json` marker is written first, and scientific files go into
an attempt-specific `.staging/` directory. Integrity and claim-safety checks
inspect the actual recursive staging surface before promotion; the final
`artifact_manifest.json` is written last as completion evidence. A failed or
interrupted attempt remains visibly incomplete and normal `--run` refuses it;
only `--repeat-after-crash` may clean the known Stage 1b leftovers and retry
with the identical registered configuration and seed schedule.

Stage 1 stays frozen. The one governed run is complete, its closed integrity
contract passes, and independent review passed; all Stage 2 unblock conditions
are YES. Stage 2 design remains outside this task.

## Stage 2 — governed run complete; apparatus result only

The frozen registration is [`docs/thesis/STAGE_2_REGISTRATION.md`](../../docs/thesis/STAGE_2_REGISTRATION.md),
with machine-checkable constants in [`stage2_registration.py`](stage2_registration.py)
and the implementation in [`negative_control.py`](negative_control.py). The
Stage 2 run completed **exactly once** through `make thesis-stage2`; its
immutable result namespace is
[`experiments/results_thesis/negative_control/`](../../experiments/results_thesis/negative_control/)
and includes the human-readable
[`negative_control_report.md`](../../experiments/results_thesis/negative_control/negative_control_report.md).
The post-run audit passed and the Stage 2 scientific decision is **PASS**.

| Control | Analyzable / registered | Invalid | Rejections | Rate / status |
|---|---:|---:|---:|---|
| `NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN` | 1000 / 1000 | 0 | 26 | 26/1000 = 0.026; PASS (`X < 65`) |
| `NC1_TARGET_PERMUTATION` | 1000 / 1000 | 0 | 28 | 28/1000 = 0.028; PASS (`X < 65`) |

The separate `NC0_MASK_ALIGNED_DIAGNOSTIC` produced 42 derived family
rejections out of 1000, or **42/1000 = 0.042**. It is **NON-GATING**, outside
the confirmatory family, and **NOT an FPR estimate**. Replay was not required
and was not run.

This PASS supports only the conclusion that, in this fixed dataset / pipeline
context, the significance apparatus did not exhibit registered gross
false-positive inflation under the two frozen null constructions. It does not
establish absence of leakage, absence of all dependence, predictive edge,
alpha, investment value, universal calibration, or production readiness.
Interpretation remains limited by low power near true FPR 0.06 (registered
power about 0.270), a descriptive/non-gating equivalence delta of 0.05, and an
unresolved FinanceIQ SESOI. Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**;
Stage 1b remains diagnostic/calibration only; historical Stage 1 and Stage 1b
artifacts were not rerun or rewritten. Stage 3 and further model-development
work must not reinterpret Stage 2 outside its registered scope.

## Stage 3 — registered; not implemented; not run

The [Stage 3 registration](../../docs/thesis/STAGE_3_REGISTRATION.md) is complete
prospectively. Its five-class family is frozen as IDs 4000–4004: future-year
feature leakage, T/T+1 misalignment, target leakage into features, look-ahead
universe membership, and duplicate-row inflation. The expected guard gaps are
exactly 4000, 4001, and 4003 (`NOT_DETECTED`); 4002 and 4004 are expected
`DETECTED`, each by an existing surface found on the authoritative base — 4002
by the reachable cell-provenance column-coverage guard, 4004 by the duplicate-key
guards. These are prospective expectations only. The expected first-draw
outcome, **FAIL — INFORMATIVE**, is prospective and not an observed scientific
result.

The only frozen source is
`data/trusted_clean/modeling_dataset_training_2020_2025.csv`, SHA256
`3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.
There is no Stage 3 result root, runner, Makefile target, or generated-output
contract. No guard was repaired: the named target-leakage validator condition
stays structurally unreachable and is recorded as a separate
existing-but-useless surface. The registration tests construct no injected
frame, so every frozen injection count is a prospective expectation verified by
the future implementation tests. Stage 7 remains blocked under its existing
wording. This registration establishes no predictive or investment claim; it
remains research support only, not investment advice.

## Output isolation

Every thesis experiment writes to `experiments/results_thesis/<slug>/` and
nowhere else. `provenance.output_dir(slug)` is the only sanctioned way to get
that path: it refuses unknown slugs and refuses any path that resolves inside a
pre-existing governed results root (`experiments/results/`,
`experiments/results_excess/`, and the rest of `PROTECTED_RESULTS_ROOTS`).

No existing governed artifact may be modified, regenerated, or overwritten by
work in this namespace. Historical results stay as they are, including the ones
that record null findings.

## Prepared experiments

| Slug | Purpose |
|---|---|
| `positive_control` | **Implemented** — `positive_control.py`, run via `make thesis-positive-control`. Injects a known-strength synthetic signal into one raw feature column before feature construction and measures how much survives each pipeline stage. Validates that the measurement apparatus responds to an effect that is provably present. |
| `positive_control_calibration` | **Governed run complete — diagnostic/calibration only** — Stage 1b. `docs/thesis/STAGE_1B_REGISTRATION.md` + `stage1b_registration.py` + `positive_control_calibration.py`, run via `make thesis-stage1b`. Prospective (not blind) calibration/diagnostic re-scope of Stage 1: same carrier/model/splits/seed framework, adds the `0.35` grid rung, `R = 400` fresh repetitions (ids 200–599), Stage-1-operational-rule detection probability as the primary result, raw-p<0.05 detection probability as a secondary non-gating diagnostic, and no performance gate. Exactly one attempt (no rerun) completed the 6 × 400 matrix; integrity passed, replay was identical, and independent review was PASS. Stage 2 unblock conditions are all YES. |
| `negative_control` | **Governed run complete — scientific decision PASS** — Stage 2. The two confirmatory controls were run exactly once with NC0 `26/1000 = 0.026` and NC1 `28/1000 = 0.028`, both below the registered critical count of 65; the separate diagnostic is `42/1000 = 0.042`, **NON-GATING** and **NOT an FPR estimate**. See the [frozen registration](../../docs/thesis/STAGE_2_REGISTRATION.md) and [immutable result report](../../experiments/results_thesis/negative_control/negative_control_report.md). The result is limited to the registered significance-apparatus claim in the fixed dataset / pipeline context and does not establish leakage absence, predictive edge, alpha, or investment value. Replay was not required and was not run. |
| `defect_injection` | **REGISTERED / NOT IMPLEMENTED / NOT RUN** — frozen five-class Stage 3 family with prospective guard gaps at 4000, 4001 and 4003, prospective detections at 4002 and 4004, and a prospective expected first-draw outcome of **FAIL — INFORMATIVE**, not an observed scientific result. The frozen source is pinned in the [registration](../../docs/thesis/STAGE_3_REGISTRATION.md); no result root exists and Stage 7 remains blocked. Research support only, not investment advice. |
| `informativeness` | Map the power/informativeness frontier: what effect size this design could detect, as a function of n, years, and frequency. |
| `monthly_panel` | Monthly-frequency redesign of the panel, subject to the data feasibility findings in `docs/thesis/DATA_FEASIBILITY.md`. |

## Seeds

Seeds live in `provenance.SEEDS`, in version control, declared before the
experiment runs. An experiment calls `provenance.seed_for(slug)`; it must not
hardcode a seed, derive one from the clock, or leave one implicit.
`seed_for` raises for an undeclared slug rather than defaulting.

## SHA256 provenance

Every experiment ends by calling `provenance.write_manifest(...)`, which emits
`artifact_manifest.json` containing:

- the seed actually used,
- a `{path, sha256, size_bytes}` descriptor for each file written,
- a `source_artifacts` list of `{path, sha256, size_bytes, role}` for each input read.

`source_artifacts` is the shape that
`tests/test_artifact_registry.py::test_embedded_source_artifact_checksums_are_current`
auto-discovers, so once an experiment's output root is registered, a drifting
input fails the root suite and names the file.

## Registry rules

`artifact_registry.json` requires that every entry match at least one real file
on disk, and that every file under a governed root be owned by exactly one
entry. Consequently:

- `experiments/results_thesis/positive_control` is registered in `entries[]`,
  with one entry per emitted file and `make thesis-positive-control` as the
  `generator_command`. Its files exist, which is what `entries[]` requires.
- Stage 1b's root is in `governed_roots`, and its five emitted files are now
  present and owned by `entries[]`. The `prospective_entries[]` block was the
  pre-run ownership contract: it fixed ownership before the run, and the
  governed run moved those items verbatim into `entries[]`.
- Stage 2's root is in `governed_roots`, and its seven emitted files are now
  present and owned by `entries[]`; the immutable result report and manifest
  are under `experiments/results_thesis/negative_control/`.
- Registered Stage 3 (`defect_injection`) has no result root and no registry
  entry of either kind; implementation and pre-run output governance remain
  future work.
- The remaining two placeholder slugs (`informativeness`, `monthly_panel`) have
  no registry entry of either kind, as the `proposed_future` class prescribes.
- When one of them is implemented, that task adds its output root to
  `governed_roots`, adds the Makefile target, and declares ownership — in
  `prospective_entries[]` if the registration requires ownership before the run,
  otherwise in `entries[]` once the files exist.

## Claim discipline

Results produced here are descriptive research evidence. They establish no
predictive edge and no investment value. The repository's finding — walk-forward
IC statistically indistinguishable from zero after multiplicity correction —
stands until a pre-registered experiment overturns it, and the pre-registration
protocol in `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` governs the order in which
that may be attempted.

## Stage 1 injection safety

`positive_control.py` manufactures a relationship between a raw feature column
and the future-return ranking, which makes containment a correctness property
rather than a nicety. Four things hold by construction and are asserted in
`tests/test_thesis_positive_control.py`:

- the injected table is written to a private temporary directory and deleted
  when the repetition ends — never under `data/`;
- the carrier column's own observed values are permuted within each year, so no
  value is fabricated, the within-year marginal is preserved exactly, and null
  stays null;
- the target column and every non-carrier column come out bit-identical;
- the pipeline's dataset path is restored on every exit path, including on an
  exception, so ordinary `make research` behaviour is unchanged the moment a
  repetition ends.

The temporary `run_experiments.TRAINING_MODELING` override is process-global and
not thread-safe. Stage 1 is intentionally single-threaded; concurrent execution
is outside this task's scope.

`theta = 0` sets the copula correlation to exactly zero, so the null rung is a
plain random permutation that forces no correlation at all.

For the 100%-coverage primary carrier, the raw, feature-construction, and
model-input/imputation checkpoints are identity/invariant checkpoints. Their
equality is not evidence of empirically absent attenuation; the substantive
measured transition is carrier signal to fitted model prediction. The
background-adjusted ratio diagnostic is emitted as NA for those identity
checkpoints and for the injected design constant, because it sits near 1.0 there
by construction and would read as a measured attenuation coefficient. The
secondary missingness arm changes row population: observed-carrier checkpoint
`n` differs from post-imputation full-cross-section `n`, so its stagewise ratio
mixes missingness/imputation dilution with changed evaluation population and is
not a pure attenuation coefficient.

Detection-rate Wilson intervals are conditional on the fixed realized panel.
The realized equity panel is held fixed across repetitions; the synthetic
injection changes across repetitions and the permutation-test RNG also changes
across repetitions, so the empirical detection-rate variation carries
injection-draw randomness plus permutation Monte-Carlo randomness. It does not
include resampling uncertainty from drawing a different equity panel or time
sample. The analytic Fisher-z and empirical curves condition on different
randomness and are diagnostic rather than interchangeable power estimates.
