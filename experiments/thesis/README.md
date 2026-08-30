# Thesis experiment namespace

Prepared in Week 0/1. **Stage 1 (`positive_control`) is implemented and has
run; Stage 1b (`positive_control_calibration`) is registered but NOT
implemented; the remaining slugs are still placeholders.** This directory holds
the shared provenance helpers, the implemented stages, and the rules below.

## Stage 1b — registered, not implemented

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
has **no scientific performance PASS/FAIL gate**. When Stage 1b is implemented,
that same commit — before the first run — adds the runner, the `thesis-stage1b`
Makefile target, the
`experiments/results_thesis/positive_control_calibration/` output root **to
`artifact_registry.json` `governed_roots`**, one registry entry per emitted
output, and no-orphan-output tests; and it replaces/inverts the
registration-phase absence guards in the same commit. None of that exists yet,
per the `proposed_future` convention below. Adding only per-file registry
entries without the `governed_roots` root is insufficient. Stage 1 stays frozen;
Stage 2 stays blocked.

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
| `positive_control_calibration` | **Registered, not implemented** — Stage 1b. `docs/thesis/STAGE_1B_REGISTRATION.md` + `stage1b_registration.py`. Prospective (not blind) calibration/diagnostic re-scope of Stage 1: same carrier/model/splits/seed framework, adds the `0.35` grid rung, `R = 400` fresh repetitions (ids 200–599), Stage-1-operational-rule detection probability as the primary result, raw-p<0.05 detection probability as a secondary non-gating diagnostic, and no performance gate. No run executed. |
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

- An experiment's output root joins `governed_roots` only once it has actually
  written artifacts. `experiments/results_thesis/positive_control` is registered
  now, with one entry per emitted file and `make thesis-positive-control` as the
  `generator_command`. The other five slugs (`positive_control_calibration`,
  `negative_control`, `defect_injection`, `informativeness`, `monthly_panel`)
  are still absent from the registry, as the `proposed_future` class prescribes:
  *"Intentionally has NO registry entry until the file exists."*
- When the next experiment is implemented, that task adds its output root to
  `governed_roots`, adds one entry per artifact whose `generator_command` is a
  real Makefile target, and adds the target. Doing it earlier breaks the suite.

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
