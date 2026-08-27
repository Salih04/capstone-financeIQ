# Thesis experiment namespace

Prepared in Week 0/1. **No experiment in this namespace is implemented yet.**
This directory currently holds only the shared provenance helpers and the rules
below.

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
| `positive_control` | Inject a known signal at the raw layer and confirm the pipeline recovers it. Validates that the measurement apparatus can detect an effect that is genuinely present. |
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

- `experiments/results_thesis/` is **not** in `governed_roots` yet, and has no
  registry entry, because it contains no artifacts yet. The registry's own
  `proposed_future` class documents exactly this: *"Intentionally has NO
  registry entry until the file exists."*
- When an experiment is implemented, that task adds its output root to
  `governed_roots`, adds one entry whose `generator_command` is a real Makefile
  target, and adds the target. Doing it earlier breaks the suite.

## Claim discipline

Results produced here are descriptive research evidence. They establish no
predictive edge and no investment value. The repository's finding — walk-forward
IC statistically indistinguishable from zero after multiplicity correction —
stands until a pre-registered experiment overturns it, and the pre-registration
protocol in `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` governs the order in which
that may be attempted.
