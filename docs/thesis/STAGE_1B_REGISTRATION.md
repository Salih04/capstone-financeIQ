# Stage 1b Prospective Registration

This is the complete registration for the Stage 1b diagnostic/calibration
experiment. It is companion to `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` and is
machine-checked by `tests/test_thesis_stage1b_registration.py` against the
constants in `experiments/thesis/stage1b_registration.py`.

Stage 1b is registered but not implemented or run. Importing its constants
module performs no experiment, reads no dataset, and writes no result.

## Status when this registration was written

This section records what was already known at registration time.

- Stage 1 was **FAILED AS WRITTEN — INFORMATIVE**. Its outcomes had already
  been inspected in the governed Stage 1 report before this registration was
  written.
- In the governed Stage 1 primary `equity` arm, per-repetition detection was
  approximately **0.615 at θ = 0.30** and **0.930 at θ = 0.40**.
- The original Stage 1 gate-pass diagnostic was approximately **0.195** (39 of
  200 coherent descriptive draws).
- Stage 1's theta=0 background/final evaluated IC was non-zero (approximately
  **0.0909** in the governed report). This is a known interpretation
  limitation: theta=0 is not a zero-signal market world because the real
  non-carrier features remain in the pipeline.
- No Stage 1b repetition had been executed, and no Stage 1b estimate, outcome,
  or result artifact had been inspected or generated. The future result root
  `experiments/results_thesis/positive_control_calibration/` did not exist.
- Stage 1b is therefore **prospective but NOT blind**. The only Stage-1-
  outcome-informed Stage 1b design choices are:
  1. adding theta=0.35 to increase descriptive resolution inside the already
     observed 0.30–0.40 bracket; and
  2. increasing from R=200 to R=400 to improve pointwise Monte-Carlo precision.

These choices cannot flip a Stage 1b verdict because Stage 1b has **no
scientific performance PASS/FAIL gate**.

## Scope and arm registration

Stage 1b runs **only** the primary `equity` carrier on the following displayed
grid, with R=400 for every level:

`0.00, 0.10, 0.20, 0.30, 0.35, 0.40`

The global repetition IDs are exactly **200..599**, inclusive. Stage 1b
explicitly excludes the historical Stage 1 arms:

- the `current_ratio` missingness arm; and
- the theta=0.90 sanity arm.

Those remain historical Stage 1 diagnostics and are not Stage 1b grid levels,
carriers, repetitions, estimates, or gates.

The injection reuses the Stage 1 carrier's own observed values. Within each
year, those values are assigned to the order of
`s = rho*z + sqrt(1-rho^2)*eps`, where
`rho = 2*sin(pi*theta/6)`. Missingness is preserved exactly; no value is
fabricated, and no `data/trusted*`, `data/trusted_clean*`, or
`data/provenance*` path is mutated.

## Stage 1b estimand and detection semantics

For each theta on the one realized equity panel, Stage 1b describes the
vector-valued chain:

```text
nominal theta
  -> realized raw equity carrier IC
  -> ridge prediction IC and final evaluation IC
  -> Stage-1-operational-rule detection probability
```

The primary result name is **Stage-1-operational-rule detection probability**.
It is defined by the unchanged numerical Stage 1 operating rule:

```text
detected_stage1_rule = min(1, 5 * p_raw) < 0.05
```

Equivalently, under the discrete permutation p-value convention, the operating
point is `p_raw < 0.01`. The divisor 5 is the historical Stage 1
confirmatory-family divisor. It is retained unchanged solely as a **fixed
operating point** so the Stage 1b descriptive curve is comparable to Stage 1.

### The divisor 5 is a frozen literal, not a grid-length

`STAGE1_OPERATIONAL_DIVISOR = 5` is a **frozen literal inherited from the
historical Stage 1 operating rule**. The Stage 1b implementation **must not**
derive this divisor from `len(IC_GRID)`, from `len` of the Stage 1b theta grid,
from `positive_control.CONFIRMATORY_FAMILY_SIZE`, or from the number of Stage 1b
levels.

The Stage 1b grid has six levels, but its primary descriptive operating point
remains

```text
min(1, 5 * p_raw) < 0.05
```

approximately `p_raw < 0.01`, subject to the discrete governed permutation
p-values. Recomputing the divisor from the six-level grid would silently change
the operating point to approximately `p_raw < 0.00833` and is **forbidden**.
This remains the **"Stage-1-operational-rule detection probability"**, **not** a
six-level FWER procedure. It happens that `5` equals the *Stage 1* grid length
and the *Stage 1* `CONFIRMATORY_FAMILY_SIZE`; it does **not** equal the Stage 1b
`len(IC_GRID)`, and the cross-module test pins exactly that.

Stage 1b's six theta levels are **not a hypothesis family**. Stage 1b makes
**no family-wise-error-control claim across its six levels**. Pointwise 95%
Wilson intervals are reported per theta. The secondary result name is
**raw-p<0.05 detection probability — secondary, non-gating diagnostic**. It is
not a gate and cannot invalidate the run.

The primary result is descriptive, not a null-hypothesis decision. A flat,
non-monotone, weak, surprising, or high-background Stage 1b diagnostic curve is
a **scientific result**, not an integrity failure. No hidden performance gate
may be introduced. It does not itself invalidate the run.

## Status of the 0.35 rung and the historical 0.80 reference

`theta=0.35` is **not** derived from `MDE_BASE`, is **not** a realistic market
IC, is **not** a SESOI, and is **not** a tuned pass point. It is the mechanical
midpoint of the already observed Stage 1 0.30–0.40 detection bracket.

The approximately 0.80 value is mentioned only as a **Stage 1 descriptive
reference**: Stage 1 observed approximately 0.615 at 0.30 and 0.930 at 0.40,
so adding 0.35 provides descriptive resolution in that bracket. Stage 1b does
**not** compute an 80%-detection gate, threshold crossing, or success
criterion. No Stage 1b threshold crossing may be used as a success criterion.

Stage 1b does not compute or apply Stage 1's `confirmatory_gate`,
`gate_informativeness`, strict-monotonicity pass/fail, or `GATE_LEVELS`
rejection criterion. Those are historical Stage 1 quantities only.

## Fixed constants

| Constant | Registered value | Authority / meaning |
|---|---|---|
| Source dataset | `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | `run_experiments.TRAINING_MODELING` |
| Source SHA-256 | `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78` | Governed Stage 1 report and current file hash |
| Panel | frozen walk-forward panel; 3 splits; about 80 rows per split | Stage 1 `SPLITS` / `build_panel()` |
| Carrier | `equity` only | Stage 1 primary carrier |
| Model | `ridge` | Stage 1 model |
| Alpha threshold | `0.05`, two-sided | Stage 1 protocol |
| Stage-1-operational-rule divisor | `5` | Historical Stage 1 confirmatory-family divisor, retained as a fixed operating point only |
| Permutations | `10,000` | `significance.DEFAULT_PERMUTATIONS` |
| Bootstraps | `10,000` | `significance.DEFAULT_BOOTSTRAPS` |
| Grid | `{0.00, 0.10, 0.20, 0.30, 0.35, 0.40}` | This registration |
| Repetitions | `R = 400` at each level | Fresh Stage 1b repetitions |
| Result root | `experiments/results_thesis/positive_control_calibration/` | Isolated future namespace; must be absent now |
| Seed | `42` | `provenance.seed_for("positive_control_calibration")` |
| Detection interval | Pointwise 95% Wilson | No simultaneous or between-level interval claim |

### Governance wiring required before the first Stage 1b execution

Before the **first** Stage 1b execution, the implementation commit **must** add
**all** of the following, in that same commit and before any run:

1. the Stage 1b runner;
2. a Makefile target (e.g. `thesis-stage1b`);
3. the Stage 1b future result root
   (`experiments/results_thesis/positive_control_calibration/`) added to
   `artifact_registry.json` → `governed_roots`;
4. one `artifact_registry.json` entry for **every** emitted governed output;
5. tests proving registry coverage / no orphan outputs.

Adding only per-file registry entries **without** adding the result root to
`governed_roots` is **insufficient**. None of items 1–5 exist at registration
time, and this registration does not create the result root. The first Stage 1b
run is **forbidden** until this governance wiring is committed and reviewed.

## RNG and non-overlap contract

The displayed/report grid may remain numerically ordered, but seed derivation
must use this explicit theta-to-level-index mapping:

| theta | level_index |
|---:|---:|
| 0.00 | 0 |
| 0.10 | 1 |
| 0.20 | 2 |
| 0.30 | 3 |
| 0.40 | 4 |
| 0.35 | 5 |

Implementations **must not** use `enumerate(sorted_grid)` for seed derivation:
that would silently move legacy theta=0.40 from index 4 to index 5.

**Named drift site.** `positive_control.run_arm()` (the Stage 1 helper) currently
derives `level_index` with `enumerate(levels)`. That behavior **must not be
reused unchanged** for the numerically sorted Stage 1b grid, because sorted
Stage 1b order would assign

```text
0.35 -> 4
0.40 -> 5
```

and silently break legacy stream identity. The future Stage 1b implementation
**must** obtain `level_index` from `stage1b_registration.LEVEL_INDEX` or
`stage1b_registration.level_index_for(theta)`. This must **not** be solved by
forcing an unnatural report/display grid order: scientific and report ordering
may be numeric; only the **seed derivation** is required to be mapping-based.

The base seed is **42**. The approved Stage 1 formulas are reused:

- injection seed = `base_seed*1_000_003 + level_index*10_007 + repetition`;
- permutation seed = `significance.DEFAULT_SEED + repetition`.

Stage 1 legacy streams are level indices 0..4 × repetition IDs 0..199. Stage 1b
uses those same legacy indices plus new index 5 × repetition IDs 200..599.
Non-overlap comes from the fresh repetition-ID range plus this explicit fixed
level-index mapping. Stage 1b estimates use only IDs 200..599; Stage 1 IDs are
not pooled into them.

## Closed integrity contract

The following is the complete and closed list of conditions that can invalidate
the governed Stage 1b run. No other statistical or scientific condition can
invalidate it.

### A. Mechanical / provenance checks

1. Registered source dataset hash matches.
2. Source remains unchanged from the registered pre-run hash through run
   completion.
3. Complete 6 × 400 matrix is present.
4. No missing/duplicate repetition cells exist.
5. Declared seed formulas are reproduced. Declared seed formulas reproduced
   exactly.
6. No seed collision exists.
7. No Stage 1 repetition/seed overlap exists.
8. Stage 1b writes only to its isolated namespace,
   `experiments/results_thesis/positive_control_calibration/`.
9. Stage 1 historical namespace is not overwritten:
   `experiments/results_thesis/positive_control/`.
10. No data/trusted*, data/trusted_clean*, or data/provenance* mutation occurs.
11. Required outputs finite.
12. Replay deterministic with identical settings.
13. Runtime override restored on every exit path.

### B. Mechanism invariant checks

14. Carrier observed-value multiset preserved within year.
15. Carrier missingness mask preserved.
16. Targets unchanged.
17. Non-carrier features unchanged.
18. equity reaches the modeled feature path.
19. Identity/invariant checkpoint ICs agree within the already governed Stage 1
    numerical tolerance.
20. Ridge prediction IC and final evaluation IC agree within the already
    governed Stage 1 numerical tolerance.

**Integrity exclusions.** No integrity check may inspect or threshold:

- recovered IC magnitude;
- detection probability;
- monotonicity;
- Wilson interval position;
- the Stage 1b theta=0 diagnostic;
- a crossing location; or
- any performance statistic.

The secondary raw-p diagnostic is non-gating, and there is no scientific
performance gate. These exclusions prevent a hidden performance gate from being
introduced under another name.

## Fixed-panel uncertainty boundary

Across Stage 1b repetitions the realized equity panel is fixed. The synthetic
injection draw changes and the permutation-test RNG changes. Therefore the
empirical calibration and detection curves reflect:

- injection-draw randomness; and
- permutation Monte-Carlo randomness,

conditional on this one realized panel. They exclude uncertainty from drawing
another:

- equity universe;
- market panel;
- time period;
- PIT universe; or
- monthly sample.

Pointwise Wilson intervals are therefore **not unconditional market-level power
intervals**. The permutation seed
(`derive_permutation_seed(base_seed, repetition)`) does not depend on theta or
level index, so the permutation RNG stream is **shared across theta levels for
the same repetition** identifier — not "where applicable", always. Consequently
the pointwise Wilson intervals are **marginal** intervals: they do not
constitute simultaneous or between-level comparison intervals and provide no
between-theta comparison inference.

## R=400 precision boundary

The actual approximate worst-case pointwise Wilson scale for R=400 is:

- near p=0.50: about **4.9 percentage-point half-width**;
- near p=0.80: about **3.9 percentage-point half-width**.

R=400 improves grid-point precision but does not identify an exact
between-grid crossing. No interpolation is confirmatory.

## Single-run and replay rule

- There is one governed prospective Stage 1b run.
- The seed schedule is frozen in this registration.
- A deterministic replay with identical settings is verification, not a new
  scientific run.
- An execution crash may be repeated only with identical registered settings,
  and both attempts must be recorded.
- Any post-outcome change to the grid, R, carrier, model, seed policy, detection
  rule, or inference requires a dated amendment recording what had already been
  observed.

The result root remains absent until the implementation/run task. Stage 1b is
apparatus characterization only; a descriptive curve cannot turn the historical
Stage 1 result into a pass.

## Registration-phase guards — sunset on implementation

The following tests in `tests/test_thesis_stage1b_registration.py` are
**registration-phase only**:

- the result root
  `experiments/results_thesis/positive_control_calibration/` does not exist;
- `positive_control_calibration` is absent from `artifact_registry.json`
  runtime outputs;
- the `thesis-stage1b` Makefile target is absent.

They assert the *current* pre-implementation state. The future implementation
commit **must replace/invert them in the same commit** that adds the governed
runner. Required future state, all present **before the first execution**:

- the runner exists;
- the Makefile target exists;
- the governed root exists in `artifact_registry.json` → `governed_roots`;
- the emitted-artifact schema / per-file registry entries are registered.

Execution is still **not performed** until that implementation commit has been
reviewed and committed. These guards must not be deleted or weakened before
then.

## SESOI and claim boundary

Stage 1b does not establish, assume, estimate, or imply:

- a realistic BIST IC magnitude;
- a universal IC benchmark; or
- a smallest effect size of interest.

SESOI remains **UNRESOLVED**. `theta` is a synthetic copula design constant.
`theta=0` is not a “zero-signal market world”; real non-carrier features remain
in the pipeline. Stage 1b is apparatus characterization only.

There is no predictive-edge, alpha, profitability, investment-value, or
production-readiness claim. This is research support, not investment advice.
The repository's committed walk-forward finding remains unchanged.

## Git chronology anchor

Initial Stage 1b design work began on 2026-08-29. This reviewed registration is
committed before any Stage 1b implementation or run. The registration commit
itself is the authoritative prospective Git chronology anchor. This document was
independently reviewed and repaired after 2026-08-29; the reviewed-registration
date is 2026-08-31. No claim is made that the final registration text was wholly
written on a single earlier date.

Unlike Stage 1, Stage 1b prospective ordering will be **Git-proven** by this
registration commit preceding the implementation and run commits. No Stage 1b
implementation or run commit SHA exists yet; the implementation task may
record/reference the registration commit SHA after the owner commits it.

## Stage 2 status

Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE** and its implementation and
historical artifacts are frozen. Stage 2 remains **BLOCKED** until the one
prospective Stage 1b run is completed, the closed integrity contract passes,
the governed Stage 1b artifacts are complete and reproducible, and the run is
independently reviewed.
