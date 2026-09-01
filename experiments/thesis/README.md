# Thesis experiment namespace

Prepared in Week 0/1. **Stage 1 (`positive_control`) is implemented and has
run; Stage 1b (`positive_control_calibration`) is registered and implemented but
has NOT been run; the remaining slugs are still placeholders.** This directory
holds the shared provenance helpers, the implemented stages, and the rules
below.

## Stage 1b — registered and implemented, NOT run

`docs/thesis/STAGE_1B_REGISTRATION.md` is the frozen, owner-approved,
prospective (but **not blind**) registration for Stage 1b, a diagnostic /
calibration experiment. `experiments/thesis/stage1b_registration.py` holds its
machine-checkable constants; `tests/test_thesis_stage1b_registration.py` proves
code == registration. **No Stage 1b run has been executed and no Stage 1b
outcome inspected.** Stage 1b reuses the Stage 1 carrier (`equity`), model
(`ridge`), splits, significance machinery, seed framework, and the
Stage-1-operational-rule detection point; adds the single grid rung `0.35`; uses `R = 400`
fresh repetitions with global ids `200 … 599` (non-overlapping with Stage 1's
`0 … 199`); excludes the historical `current_ratio` and theta=0.90 arms; and
has **no scientific performance PASS/FAIL gate**.

The runner is `experiments/thesis/positive_control_calibration.py`, invoked by
`make thesis-stage1b`; `make thesis-stage1b-replay` is its determinism probe and
writes nothing. Both are the implementation commit's work, added *before* the
first run together with the `governed_roots` entry and one ownership contract per
emitted output. **The Stage 1b result root is still absent**: it does not exist,
and nothing but the one governed run may create it.

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

Stage 1 stays frozen; Stage 2 stays blocked until the one governed run is
completed, its closed integrity contract passes, and it is independently
reviewed.

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
| `positive_control_calibration` | **Registered and implemented, not run** — Stage 1b. `docs/thesis/STAGE_1B_REGISTRATION.md` + `stage1b_registration.py` + `positive_control_calibration.py`, run via `make thesis-stage1b`. Prospective (not blind) calibration/diagnostic re-scope of Stage 1: same carrier/model/splits/seed framework, adds the `0.35` grid rung, `R = 400` fresh repetitions (ids 200–599), Stage-1-operational-rule detection probability as the primary result, raw-p<0.05 detection probability as a secondary non-gating diagnostic, and no performance gate. No run executed; the result root is absent. |
| `negative_control` | Expand the existing placebo/negative-control family. Confirms the apparatus reports nothing when nothing is there. |
| `defect_injection` | Deliberately introduce known defects (leakage, misalignment, look-ahead) and confirm the guards catch each one. |
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
- Stage 1b's root is in `governed_roots` now, but its per-file ownership lives in
  `prospective_entries[]`, because an `entries[]` entry must match at least one
  real file and no Stage 1b file exists yet. That block is the registry's answer
  to a registration that fixes ownership *before* the run which creates the
  files: same entry shape, same `make <target>` rule, not yet subject to
  `coverage_rule`. The run commit moves those items verbatim into `entries[]`.
- The remaining four slugs (`negative_control`, `defect_injection`,
  `informativeness`, `monthly_panel`) have no registry entry of either kind, as
  the `proposed_future` class prescribes.
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
