# Pre-experiment protocol (MSc thesis)

Written in Week 0/1, **before any thesis experiment has been run**, against the
frozen baseline in `docs/thesis/baseline/pre_thesis_baseline.json`.

This document locks the *order* of experiments and the decision rule for each
one. Its purpose is to make the thesis result interpretable whichever way it
comes out — which requires the analysis choices to be fixed while the answers
are still unknown.

## Standing commitments

These bind every stage below.

1. **Order is fixed.** Stage *n+1* does not begin until stage *n* has been run
   and its result recorded, pass or fail. Stages are not reordered to reach an
   interesting result sooner.
2. **BIST signal search is last.** It is stage 7 and it is gated: it does not
   run at all unless stages 1–3 pass. An apparatus that cannot recover a known
   signal, or that reports signal where none exists, cannot be trusted to
   report a null — or a discovery — on real data.
3. **The null result stands until overturned.** The committed finding is
   walk-forward IC statistically indistinguishable from zero after multiplicity
   correction. Nothing in this protocol assumes that is wrong.
4. **Every stage declares its numbers first.** Injection levels, equivalence
   margins, family definitions, and stopping rules are written into the stage's
   pre-registration entry *before* its first run, and are not edited afterwards
   except by a dated amendment that states what changed, why, and what had
   already been observed.
5. **Seeds are declared in `experiments/thesis/provenance.py`**, in version
   control, before the run.
6. **Existing governed artifacts are never overwritten.** Output goes to
   `experiments/results_thesis/<slug>/`.
7. **Descriptive research evidence only.** No stage establishes investment
   value, and no stage's result may be reported as one.

## What this protocol exists to prevent

Stated explicitly, because these are the specific failure modes that would make
a positive finding worthless:

| Forbidden | Why it is forbidden | Structural prevention |
|---|---|---|
| Searching across feature × model × target combinations until something is significant | The number of implicit comparisons becomes unknowable, so no p-value can be interpreted | Each stage's **family** is enumerated below before the run; the multiplicity correction covers the whole enumerated family, not the reported subset. Adding a combination after the fact requires a dated amendment and re-correction over the enlarged family. |
| Choosing IC injection levels after seeing results | Lets the analyst tune the test until the apparatus "passes" | Stage 1 injection levels are **fixed in this document** (below) and are set from the frozen baseline's MDE, not from any observed outcome. |
| Changing the equivalence margin after observing estimates | Converts a failed equivalence test into a passing one by redefinition | Stage 2's margin is **fixed in this document** (below) and derives from the frozen baseline MDE, not from the observed negative-control distribution. |
| Reporting only the stage that worked | Survivorship over one's own experiments | Every stage that runs is recorded with its result, including failures. A stage that ran may not be silently dropped. |
| Re-running with a new seed until the result changes | Seed-shopping | Seeds are declared before the run and are not changed to alter an outcome. |

## Fixed constants

Both derive from the frozen baseline and are set **now**, before any stage runs.

- **Baseline MDE reference.** `MDE_base = 0.182271` — the committed
  `current_three_year_pooled` analytic minimum detectable |IC| at 80% power,
  α = 0.05 two-sided.
- **Stage 1 injection levels.** `IC_inject ∈ {0.00, 0.10, 0.20, 0.30, 0.40}`.
  Chosen to straddle `MDE_base`: two levels below it, one adjacent, two above.
  0.00 is the built-in null rung.
- **Stage 2 equivalence margin.** `δ = 0.05`, i.e. roughly one quarter of
  `MDE_base`. An observed |IC| whose two-sided 90% CI lies entirely within
  ±0.05 is declared equivalent to zero.

These three numbers are the ones most vulnerable to post-hoc adjustment. They
are fixed here so that any later change is visible as a diff.

---

## Stage 1 — Positive control / raw-layer signal injection

Inject a synthetic signal of known strength into a **raw input layer** and
confirm the pipeline recovers it end to end.

- **Estimand:** recovered pooled walk-forward IC, as a function of injected IC.
- **Primary metric:** pooled Spearman IC (the frozen baseline's statistic —
  equal-weighted mean of within-split Spearman ICs).
- **Null:** the pipeline does not recover injected signal, i.e. recovered IC is
  flat in `IC_inject`.
- **Family:** 5 injection levels × 1 primary model (`ridge`, prespecified as the
  linear reference) = **5 tests**.
- **Multiplicity:** Bonferroni across the 5, matching the baseline's convention.
- **Stopping criterion:** run all 5 levels once. Pass requires recovered IC to
  increase monotonically in `IC_inject` **and** the two levels above `MDE_base`
  (0.30, 0.40) to reject at FWER 0.05. No re-runs, no added levels.
- **Injected data never enters the modeling dataset.** It lives only in the
  stage's isolated output directory.

**Gate:** failure means the apparatus cannot detect a signal that is provably
present. Stop and fix the apparatus. Do not proceed.

## Stage 2 — Expanded negative control

Extend the existing placebo family (`experiments/results_placebo/`) to confirm
the apparatus reports nothing when nothing is present.

- **Estimand:** pooled IC under label permutation and under synthetic
  no-signal inputs.
- **Primary metric:** pooled Spearman IC, and the false-positive rate across
  replications at α = 0.05.
- **Null:** true IC = 0. Here the null is the *expected* state, so the test is
  framed as **equivalence**, not as a failure to reject.
- **Family:** 6 ML models × 2 null constructions (permuted labels, synthetic
  noise inputs) = **12 tests**.
- **Multiplicity:** Bonferroni across all 12.
- **Stopping criterion:** a prespecified fixed number of replications, declared
  in the stage entry before the run. Pass requires the empirical false-positive
  rate to be within simulation error of α, and the observed |IC| two-sided 90%
  CI to fall entirely within ±δ (δ = 0.05, fixed above).

**Gate:** failure means the apparatus manufactures signal. Stop.

## Stage 3 — Defect-injection matrix

Deliberately introduce known defects and confirm the existing guards catch each
one.

- **Estimand:** per-defect detection — does the guard fire?
- **Primary metric:** binary detection per defect class; secondarily, the
  inflation in apparent IC that the undetected defect would have produced.
- **Null:** the guard does not detect the injected defect.
- **Family:** one test per defect class. The classes are enumerated in the
  stage entry before the run — at minimum: future-year leakage, T/T+1
  misalignment, target leakage into features, look-ahead universe membership,
  and duplicate-row inflation.
- **Multiplicity:** none required — each defect is a separate prespecified
  binary check with an expected answer, not a search.
- **Stopping criterion:** every enumerated defect is injected exactly once.
  Pass requires **100% detection**. A single miss is a finding in its own
  right and is reported as one.

**Gate:** an undetected defect class invalidates any downstream null *and* any
downstream positive. Stop and repair the guard.

## Stage 4 — External known-signal calibration

Run the unmodified pipeline against an external dataset with a documented,
independently established effect.

- **Estimand:** recovered effect size on the external data.
- **Primary metric:** pooled Spearman IC, compared against the externally
  published value.
- **Null:** the pipeline does not recover the externally established effect.
- **Family:** 1 external dataset × 6 ML models = **6 tests**, prespecified.
- **Multiplicity:** Bonferroni across 6.
- **Stopping criterion:** one pass over the external dataset. The dataset and
  its published effect size are named in the stage entry **before** the run, so
  the comparison target cannot be selected to match the result.
- Constrained by the repository's free-source policy; if no admissible external
  dataset is available, this stage is recorded as **not run, with the reason**,
  and that limitation is carried into the thesis.

## Stage 5 — Informativeness / power frontier

Map what this design could detect, independent of what it does detect.

- **Estimand:** minimum detectable |IC| as a function of n, cross-section
  count, and frequency.
- **Primary metric:** analytic MDE at 80% power, α = 0.05 two-sided, validated
  against simulation — the method already in `experiments/significance.py`.
- **Null:** not applicable. This stage is descriptive, not inferential, and
  reports no p-value.
- **Family:** none — no hypothesis test is performed.
- **Multiplicity:** not applicable.
- **Stopping criterion:** the prespecified grid of designs is evaluated once.
- This stage **may not be used to select** the design that produces the most
  favourable downstream result. It is an input to the monthly-redesign decision
  and to the thesis's honest statement of what it could and could not have
  found.

## Stage 6 — Monthly redesign

Rebuild the panel at monthly frequency, per `docs/thesis/DATA_FEASIBILITY.md`.

- **Estimand:** pooled cross-sectional IC at monthly frequency.
- **Primary metric:** pooled Spearman IC across monthly cross-sections, with a
  dependence-aware standard error (monthly ICs are **not** independent — see
  the feasibility report).
- **Null:** true IC = 0.
- **Family:** 6 ML models × 1 primary target (`next_year_return_pct`'s monthly
  analogue) = **6 tests**. Alternative target bases are a separate,
  separately-corrected family and are **not** pooled with this one to harvest a
  minimum p-value.
- **Multiplicity:** Bonferroni across 6.
- **Stopping criterion:** one pass over the completed monthly panel. The panel's
  end date is pinned in the manifest before the run.
- Stages 1–3 must have passed on the monthly panel as well, not only on the
  annual one. A frequency change is an apparatus change.

## Stage 7 — BIST signal search (gated)

Only after stages 1–3 pass, and only with the family declared in advance.

- **Estimand:** pooled walk-forward IC on real BIST data.
- **Primary metric:** pooled Spearman IC.
- **Null:** true IC = 0.
- **Family:** the **full** enumerated grid of feature sets × models × targets
  that will be searched, written down before the first run. The correction
  applies to the entire enumerated grid, not to the subset eventually reported.
- **Multiplicity:** Bonferroni over the full declared grid. If the grid is
  large enough that Bonferroni is uninformative, the stage entry must say so in
  advance and pre-register a false-discovery-rate procedure instead — chosen
  before, not after, seeing the p-values.
- **Stopping criterion:** one pass over the declared grid. **No expansion after
  seeing results.** If the grid is exhausted without rejection, that is the
  result.
- **Expected outcome:** consistent with the frozen baseline, non-rejection.
  This stage is designed so that a null is publishable and a positive is
  credible — which is the entire point of running stages 1–6 first.

---

## Amendments

Any change to a stage after its pre-registration entry is written must be added
here as a dated amendment recording: what changed, why, what had already been
observed at the time of the change, and how the multiplicity correction was
updated. An undated or unexplained change to a fixed constant invalidates the
stage.

### 2026-08-27 — Stage 1 implementation entry

**Status when written:** Stage 1 had not been run. No injected-signal result of
any kind had been observed. One runtime benchmark of the unmodified pipeline was
executed while sizing the repetition count; it re-derived the already-committed
baseline number (ridge pooled walk-forward IC 0.0927, permutation p 0.157, not
significant) and produced no Stage 1 quantity. Nothing below is chosen from a
Stage 1 outcome.

**What changed.** Nothing in the *Fixed constants* section. `MDE_base`, the
injection grid `IC_inject ∈ {0.00, 0.10, 0.20, 0.30, 0.40}`, the equivalence
margin δ, the primary model (`ridge`), the confirmatory family size (5), and the
Bonferroni convention are all carried over unedited. This entry adds the
implementation detail the original Stage 1 text left open, plus two arms that
make **no confirmatory claim**.

**Why.** Stage 1 as written fixes the levels and the decision rule but not the
injection site or the mechanism, and a single run per level cannot estimate a
detection *probability*. Both gaps are filled here, before the run, so the
choices are visible as a diff rather than as a post-hoc rationalisation.

#### Injection site

Signal is injected into one existing **raw** feature column of
`data/trusted_clean/modeling_dataset_training_2020_2025.csv`, in that column's
own units, before `run_experiments.build_panel()` performs feature
construction. No new variable is created; no target column is touched. The
injected table is written to a private temporary directory and is never written
under `data/`.

Carrier columns are fixed by rule, not by outcome:

- **Primary (confirmatory):** the alphabetically first feature column whose
  observed coverage is 100% in every panel year → **`equity`**. Full coverage
  makes the intended→realized IC map exact, so the primary arm measures
  *pipeline* attenuation uncontaminated by carrier missingness.
- **Secondary (descriptive only):** the alphabetically first feature column
  whose overall coverage is below 0.60 → **`current_ratio`** (≈0.49 in each
  test year). This arm exists to quantify the missingness/imputation
  attenuation channel and carries no confirmatory claim.

#### Injection mechanism

For each feature year `Y`, with `O` the rows whose carrier cell is observed and
`T ⊆ O` those whose `next_year_return_pct` is also observed:

1. `z = Φ⁻¹(rank(y_T)/(|T|+1))`, rescaled to unit standard deviation — normal
   scores of the future-return ranking.
2. `ρ = 2·sin(π·θ/6)` — the Gaussian-copula Spearman identity, the *same*
   relation already used by `experiments/significance.py::simulate_fisher_power`.
3. `s = ρ·z + √(1−ρ²)·ε` on `T`, and `s = ε` on `O∖T`, with `ε ~ N(0,1)` iid
   from a declared seed.
4. The carrier's own observed values are re-assigned within `Y` in ascending
   order of `s`.

Step 4 is a within-year permutation of the column's own values, so the within-year
marginal distribution and the missingness pattern are preserved exactly, the
target and all other columns are bit-identical, and `θ = 0` reduces to a plain
random permutation with no forced correlation. The cost, stated rather than
hidden, is that the carrier's correlations with the other 39 features are
destroyed; the `θ = 0` rung carries the identical damage, so it is the correct
background for comparison.

#### Arms

| Arm | Levels | Reps | Confirmatory? | Family |
|---|---|---|---|---|
| Primary confirmatory | 5 grid levels | 1 (repetition index 0) | **Yes** | 5 tests, Bonferroni ×5 |
| Primary descriptive | 5 grid levels | 200 | No | not corrected; no claim |
| Secondary descriptive (`current_ratio`) | 5 grid levels | 200 | No | not corrected; no claim |
| Strong-signal sanity | θ = 0.90 only | 200 | No | not corrected; no claim |

- The **confirmatory arm is the preregistered Stage 1 test, unchanged**: one run
  per level, five tests, Bonferroni across five, and the pass rule stated in the
  Stage 1 entry above. The gate decision is taken on this arm alone.
- The **descriptive arms** estimate detection probability, recovery bias, and
  stage-by-stage attenuation. They make no confirmatory claim, so they add
  nothing to the confirmatory family and cannot convert a failed gate into a
  passed one.
- The **strong-signal sanity arm** at θ = 0.90 is a smoke test with an expected
  answer, in the same spirit as Stage 3's binary checks. It is **outside the
  preregistered grid**, is excluded from the power curve, and may not be used to
  determine the ≥80% detection threshold. The threshold is read off the five
  preregistered grid levels only, with no interpolation and no added level.

#### Fixed numbers

- Repetitions per level in each descriptive arm: **R = 200**, fixed here.
- Permutations and bootstrap resamples: **10,000** each — the governed defaults
  in `experiments/significance.py`, unchanged.
- Detection at repetition `j` means `min(1, 5·p_j) < 0.05`, i.e. the same
  Bonferroni-×5 rule as the confirmatory arm.
- Seeds derive from `provenance.seed_for("positive_control")` = 42 by declared
  formula; repetition 0's permutation seed is the governed default 42.

No significance threshold, no equivalence margin, and no grid level is altered
by this entry.

#### POST-RUN chronology note (added 2026-08-27, after the Stage 1 run)

The amendment text above is preserved exactly as it was first written; this note
does not revise it. It records only how strongly the chronology can be
evidenced.

File mtimes and the matching implementation/artifact hashes recorded in the run
provenance (`experiments/results_thesis/positive_control/positive_control_report.json`
and `artifact_manifest.json`) are consistent with the amendment having been
written before the run. Temporal pre-registration is **not** cryptographically
proven in Git history: at the time of the run this repository's history did not
contain a commit of the amendment predating the run, and no later commit can
retroactively establish pre-run pre-registration. The chronology claim rests on
the mtime and hash evidence and is stated at that strength — corroborated, not
Git-proven.

### 2026-08-29 — Stage 1b prospective calibration amendment

**This amendment does not rewrite any Stage 1 text.** The Stage 1 entry, its
fixed constants, its pass rule, and its recorded result are unchanged. Stage 1
remains **FAILED AS WRITTEN — INFORMATIVE**.

Full registration: `docs/thesis/STAGE_1B_REGISTRATION.md`. Machine-checked
constants: `experiments/thesis/stage1b_registration.py`, verified by
`tests/test_thesis_stage1b_registration.py`.

**Chronology.** Initial Stage 1b design work began on 2026-08-29 (this
amendment's date). The registration was then independently reviewed and repaired
after that date; the reviewed-registration date is 2026-08-31. This reviewed
registration is committed before any Stage 1b implementation or run, and the
registration commit itself is the authoritative prospective Git chronology
anchor. Unlike Stage 1, Stage 1b prospective ordering will be Git-proven by that
registration commit preceding the implementation and run commits. No claim is
made that the final text was wholly written on a single date, and no
implementation or run commit SHA exists yet.

**Status when written.** Stage 1b was designed **after** completed Stage 1
outcomes were known — it is prospective but **not blind**. Stage 1 outcomes had
already been inspected: the primary `equity` per-repetition detection was
approximately 0.615 at θ = 0.30 and 0.930 at θ = 0.40, the original Stage 1
gate-pass diagnostic was approximately 0.195, and the theta=0 background/final
evaluated IC was non-zero, a known interpretation limitation. No Stage 1b
repetition had been executed, no Stage 1b estimate computed, and no Stage 1b
result artifact generated when this amendment and the registration were written;
`experiments/results_thesis/positive_control_calibration/` did not exist.

**What Stage 1b is.** A prospective diagnostic / calibration experiment that
characterizes, for each grid level `θ` on the fixed realized `equity` panel, the
chain *nominal theta → realized raw carrier IC → ridge final IC →
Stage-1-operational-rule detection probability*. The primary estimand is
descriptive and vector-valued.

**What carries over from Stage 1, unchanged.** The frozen panel; the ridge
model; the walk-forward splits; `experiments/significance.py`; 10,000
permutations; 10,000 bootstraps; the Stage 1 seed-derivation framework
(`derive_injection_seed` / `derive_permutation_seed`); the carrier `equity`; the
within-year own-value permutation injection with the same Gaussian-copula
relationship and exact missingness preservation; and the numerical operating
point `detected_stage1_rule = min(1, 5 * p_raw) < 0.05`.

**What changes.**

- **Grid.** `{0.00, 0.10, 0.20, 0.30, 0.35, 0.40}`. The **only** new rung is
  `0.35` — the mechanical midpoint of the already observed 0.30–0.40 Stage 1
  detection bracket (approximately 0.615 at 0.30 and 0.930 at 0.40). It is
  **not** derived from `MDE_BASE`, **not** a realistic market IC, **not** a
  SESOI, and **not** tuned to create a pass. The approximately 0.80 value is a
  Stage 1 descriptive reference only. Legacy Stage 1 level indices are
  preserved; `0.35` takes stable new level index 5; no existing seed stream is
  renumbered.
- **Repetitions.** `R = 400` fresh repetitions per level, global repetition ids
  `200 … 599` — non-overlapping with Stage 1's ids `0 … 199`. Stage 1
  repetitions are never pooled into Stage 1b estimates. The non-overlap proof is
  in the registration.
- **No scientific performance gate.** Stage 1b has **no** PASS/FAIL performance
  gate. Removing the gate does **not** reinterpret Stage 1 as passed; it
  reflects that Stage 1's literal gate is a low-power instrument on this panel
  (post-run diagnostic: P(original Stage 1 gate passes) = 0.195). Run validity
  is governed **only** by the complete closed integrity contract in the
  registration. A flat, non-monotone, weak, surprising, or high-background
  diagnostic curve is a scientific result, not an integrity failure. Stage 1b
  does not compute an 80%-detection gate, `confirmatory_gate`,
  `gate_informativeness`, strict-monotonicity pass/fail, or `GATE_LEVELS`
  rejection criterion, and no Stage 1b threshold crossing is a success
  criterion. Such a curve does not itself invalidate the run.
- **Secondary diagnostic.** **Raw-p<0.05 detection probability — secondary,
  non-gating diagnostic** may be reported. The primary result is
  **Stage-1-operational-rule detection probability**. The historical divisor 5
  is retained as a fixed operating point only; Stage 1b's six levels are not a
  hypothesis family and no family-wise-error-control claim is made across them.
  Wilson intervals are pointwise per theta only.
- **SESOI.** Remains **UNRESOLVED**. No final SESOI is defined here.

**Stage 2.** Remains **BLOCKED** until the one prospective Stage 1b run is
completed, all deterministic integrity checks pass, the governed Stage 1b
artifacts are complete and reproducible, and the run is independently reviewed.

**Fixed-panel boundary.** Across Stage 1b repetitions the realized equity panel
is fixed. The synthetic injection draw changes and the permutation-test RNG
changes. Empirical calibration and detection curves therefore reflect
injection-draw randomness and permutation Monte-Carlo randomness conditional on
this one realized panel. They exclude uncertainty from another equity universe,
market panel, time period, PIT universe, or monthly sample. Pointwise Wilson
intervals are not unconditional market-level power intervals. The permutation
seed does not depend on theta or level index, so the permutation RNG stream is
shared across theta levels for the same repetition id; the intervals are
therefore marginal and are not simultaneous or between-level comparison
intervals.

**Precision boundary.** For R=400, the approximate worst-case pointwise Wilson
half-width is about 4.9 percentage points near p=0.50 and about 3.9 percentage
points near p=0.80. R=400 improves grid-point precision but does not identify an
exact between-grid crossing; no interpolation is confirmatory.

**Run rule.** Exactly one governed prospective Stage 1b run after this amendment
and the registration are committed and independently reviewed. The seed schedule
is frozen in the registration. A deterministic replay with identical settings
is verification, not a new scientific run. An execution crash may be repeated
only with identical registered settings, and both attempts must be recorded. Any
post-outcome change to grid, R, carrier, model, seed policy, detection rule, or
inference requires a dated amendment stating what was already observed.

### 2026-09-02 — Stage 2 dated amendment and registration

This amendment is appended prospectively after the one governed Stage 1b run
completed with PASS integrity, its independent review was PASS, its governance
bookkeeping was merged, and the fail-closed significance remediation was merged
and verified. It does not silently rewrite the original Stage 2 block above.
The complete machine-checkable registration is
docs/thesis/STAGE_2_REGISTRATION.md and its constants are in
experiments/thesis/stage2_registration.py.

#### Status and explicit supersession

Before this amendment, the old Stage 2 design stated:

> 6 models × 2 null constructions = 12 tests, Bonferroni across 12

That old design is **superseded prospectively before any Stage 2 outcome**. The
old text remains above as historical protocol text; this amendment is the
operative Stage 2 design. No Stage 2 result exists at amendment time.

The amended multiplicity structure is:

- the real evaluation's within-repetition operating family is six ML models;
- the model-family divisor is the frozen literal 6;
- the two confirmatory controls form a separate progression-decision family;
- the across-control gate uses exact one-sided binomial tests with Bonferroni
  alpha=.025 per control; and
- the Stage 1 divisor 5 is not used.

The equivalence limb delta=.05 is retained as descriptive/non-gating. Recording
it this way is a weakening of the previously written Stage 2 pass rule. Delta
is not a FinanceIQ SESOI; SESOI remains UNRESOLVED.

#### Pre-run disclosures

The following was already known before this Stage 2 registration:

1. Stage 1 outcome: **FAILED AS WRITTEN — INFORMATIVE**.

2. The complete Stage 1b calibration outcomes had already been inspected:

   Detection probabilities at theta:

   | theta | detection probability |
   |---:|---:|
   | 0.00 | 0/400 = 0.0000 |
   | 0.10 | 1/400 = 0.0025 |
   | 0.20 | 45/400 = 0.1125 |
   | 0.30 | 243/400 = 0.6075 |
   | 0.35 | 347/400 = 0.8675 |
   | 0.40 | 384/400 = 0.9600 |

   Mean final evaluated IC:

   | theta | mean final evaluated IC |
   |---:|---:|
   | 0.00 | 0.090305625773 |
   | 0.10 | 0.099628182092 |
   | 0.20 | 0.130441418767 |
   | 0.30 | 0.182221558521 |
   | 0.35 | 0.212800525022 |
   | 0.40 | 0.250279183231 |

   At theta=0, mean raw carrier IC was approximately -0.0043485 and mean final
   IC was approximately +0.0903056.

3. The legacy dense-Gaussian placebo had R=25, 0 family-wise rejections, and 0
   failed repetitions. It is a historical smoke test only, not Stage 2
   calibration.

4. The pre-Stage-2 design review computed one missingness indicator pooled IC
   approximately +0.225, and 19 of 33 mask columns had |pooled IC| > .05.
   These observations motivated the NC0 design below.

5. Known significance defects were discovered before Stage 2:

   - a non-finite observed statistic could produce the minimum p-value in a
     helper;
   - the forward-2026 hand-rolled permutation path had the same failure mode;
     and
   - analyze_model degeneracy behavior was unsafe / generic.

   They were repaired before this registration. The old significance SHA was
   5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6. The
   repaired Stage 2 significance SHA is
   08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3.
   Historical Stage 1, Stage 1b, and other artifacts were not rerun or
   rewritten.

6. No Stage 2 scientific draw or outcome exists.

#### Frozen source, controls, and mechanism definitions

The source dataset is
data/trusted_clean/modeling_dataset_training_2020_2025.csv with SHA-256
3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78. The
canonical panel/splits source is experiments/run_experiments.py with SHA-256
265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543. The
repaired significance source is pinned to the SHA above.

There are exactly two confirmatory controls:

- NC1_TARGET_PERMUTATION, CONFIRMATORY / GATING;
- NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN, CONFIRMATORY / GATING.

NC1 operates on the frozen canonical source/panel pipeline. For every
repetition it permutes only observed next-year target values independently
within every target year, preserves target-null locations exactly, includes all
years used by training and testing, retrains all six models under the permuted
target, and evaluates all registered splits normally. Test-year-only target
permutation is FORBIDDEN.

NC1 preserves the target multiset within year, target missingness/null
locations, feature matrix, row universe, and train/test split definitions. It
destroys within-year feature/target association and training signal from the
real target mapping. It is a null for within-year rank association and does not
establish absence of feature-side leakage. Holding y_pred fixed and permuting
only a test year's y_true is circular because it is one draw from the same
within-year reference distribution already used by significance.py; it does not
test retraining/apparatus behavior.

NC0, for every repetition:

1. generates fresh iid N(0,1) for every canonical row × feature cell;
2. takes the canonical real 40-column missingness matrix separately for each
   feature year;
3. applies one independently seeded row permutation within that year jointly
   across all 40 feature columns;
4. applies the permuted mask to the fresh noise;
5. applies the same canonical within-year average-rank percentile transform;
6. keeps the real target unchanged;
7. keeps canonical imputation unchanged, NaN -> 0.5; and
8. retrains/evaluates the full six-model pipeline.

NC0 preserves each feature-year missingness rate and the row-wise co-missingness
pattern multiset. It destroys mask-to-target row alignment. The raw N(0,1)
construction without the rank transform is forbidden because imputation value
0.5 would form an artificial off-centre cluster not present in the canonical
rank-percentile panel.

The following NC0 alternatives are rejected and are not confirmatory arms:

- LEGACY DENSE GAUSSIAN is a valid mathematical null, but removes the real
  missingness/imputation path and runs an easier design matrix than the real
  apparatus.
- EXACT UNPERMUTED REAL MASK is not a confirmatory null because pre-run
  diagnostics showed that the mask itself is target-associated.

NC0_MASK_ALIGNED_DIAGNOSTIC is included as a diagnostic, non-gating arm outside
the confirmatory family. It uses R=1000, IDs 3000-3999, fresh rank-Gaussian
noise, and the exact real per-cell missingness mask retained in real row
alignment, with target unchanged. It measures mask-mediated target association
and imputation-channel behavior. It is not an exact null-FPR test because the
real mask is target-associated. Its outcome cannot affect confirmatory
multiplicity, Stage 2 PASS/FAIL, control definitions, or the gate.

NC2 is defined as cross-year/cohort target derangement that moves target values
across years while preserving a ticker/cohort relation. It is **EXCLUDED FROM
STAGE 2 CONFIRMATORY FAMILY** and has no Stage 2 execution because it is not a
clean null for the within-year Spearman estimand: it can preserve persistent
ticker return structure or alter year distributions, with low marginal value
versus NC1 and later alignment-defect testing.

NC3 is defined as single-feature-at-a-time within-year permutation while other
features remain aligned. It is a **DEFERRED DIAGNOSTIC** with no Stage 2
execution because it is feature importance/ablation, not a negative-control
null. Independently permuting all features within year, if discussed, is a
separate diagnostic construction, not NC3 confirmatory and not a third
confirmatory family member.

#### Repetitions and RNG

BASE_SEED = provenance.SEEDS["negative_control"] = 42.

Stage 1 uses IDs 0-199; Stage 1b uses IDs 200-599; the reserved gap is
600-999. Stage 2 NC0 uses IDs 1000-1999 inclusive, NC1 uses IDs 2000-2999
inclusive, and NC0_MASK_ALIGNED_DIAGNOSTIC uses IDs 3000-3999 inclusive.
R_CONFIRMATORY_PER_CONTROL=1000 and R_DIAGNOSTIC=1000. There is no pooling
with Stage 1 or Stage 1b.

Construction seeds are:

seed(stream, repetition_id) = BASE_SEED * 1_000_003
                           + stream * 10_007
                           + repetition_id

with fixed streams NC0_NOISE=10, NC0_MASK_ROW_PERMUTATION=11,
NC1_TARGET_PERMUTATION=20, and NC0_DIAGNOSTIC_NOISE=30. Fixed sorted year,
row, and feature-column order is required. Stream identity must not be
invented with enumerate(sorted(...)).

Significance seeds are:

significance_seed(repetition_id) = significance.DEFAULT_SEED + repetition_id
                                  = 42 + repetition_id

The same registered significance seed is supplied to all six model analyses for
that repetition. Construction streams are disjoint, no construction or
significance collision is permitted, and Stage 2 streams must not overlap
Stage 1/1b governed streams. Each model uses 10,000 permutations and 10,000
bootstraps.

#### Model family and splits

The six ML models are exactly linear_regression, ridge, lasso, elasticnet,
random_forest, and gradient_boosting. No model may be added or removed. The
within-repetition family divisor is the frozen literal 6. It is not derived
from control count, diagnostic count, grid length, or surviving models. Each
model's permutation p is two-sided.

For each complete repetition:

min_raw_p = minimum valid raw two-sided permutation p across the six models
family_reject = min(1, 6 * min_raw_p) < 0.05

Headline tie-breaking is minimum raw p, then model name ascending. The
canonical splits remain exactly:

| Split | Training target years | Test feature year |
|---|---|---:|
| test_2023 | 2021, 2022 | 2022 |
| test_2024 | 2021, 2022, 2023 | 2023 |
| test_2025 | 2021, 2022, 2023, 2024 | 2024 |

#### Completeness, exact gate, and equivalence

The denominator is strictly complete. Before significance analysis, every model
and evaluated split is checked for target with fewer than two distinct finite
values, prediction with fewer than two distinct finite values, and a non-finite
observed Spearman statistic. Partial-model degeneracy is
INVALID / DEGENERATE_PARTIAL_MODEL; all-model degeneracy is INVALID /
DEGENERATE_ALL_MODELS; and an unexpected exception is INTEGRITY_FAILURE and
aborts/fails closed. Invalid repetitions may not disappear, become p=1, count
as non-rejections, reduce divisor 6, or reduce the denominator while allowing
PASS. Model-level degeneracy is recorded explicitly.

MIN_ANALYZABLE_DENOMINATOR=1000 exactly. If either confirmatory control has
fewer than 1000 analyzable repetitions, Stage 2 is INCONCLUSIVE and cannot PASS
or FAIL through the scientific FPR gate.

For each control c, X_c is the number of the 1000 complete repetitions in which
the six-model family rejects. The descriptive FPR estimate is X_c / 1000 with
a pointwise two-sided 95% Wilson interval. The Wilson interval is not the gate.

The two controls form a decision family of size 2 with family-level target 0.05.
For each control, H0: FPR_c <= 0.05 and H1: FPR_c > 0.05. The exact one-sided
boundary test is X_c ~ Binomial(1000, 0.05), with Bonferroni alpha=.025 per
control. The exact critical count is 65 because:

P[Binomial(1000,.05) >= 65] = 0.02074989936553777 <= .025

while:

P[Binomial(1000,.05) >= 64] = 0.028428397283993795 > .025

A control fails iff X_c >= 65. Stage 2 fails iff NC0 fails or NC1 fails. Stage
2 passes iff both controls have exactly 1000 analyzable repetitions, NC0 X <=
64, NC1 X <= 64, and the integrity contract passed. The Bonferroni family
control is valid under arbitrary dependence between NC0 and NC1; the controls
are not assumed independent.

Declared per-control power to trigger the exact >=65 rule is 0.2703680264 at
true FPR=.06, 0.8982904410 at true FPR=.075, and 0.9999627573 at true FPR=.10.
Stage 2 has low power against mild inflation around .06. R=1000 is not a
magical resolution threshold.

EQUIVALENCE_DELTA=.05 is descriptive/non-gating. Report mean pooled IC per
confirmatory control per model with a two-sided 90% CI against ±.05. A violation
is a reportable finding requiring investigation before Stage 3 progression, but
does not by itself cause Stage 2 scientific FAIL. This weakens the previous
Stage 2 pass rule. SESOI remains UNRESOLVED and is not required for Stage 2.

#### Closed integrity contract

The following is the complete and closed integrity list:

1. frozen source dataset path and SHA match;
2. repaired significance.py SHA matches
   08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3;
3. registered Stage 2 source/module hashes match;
4. complete expected repetition-ID matrices;
5. no duplicates;
6. exact seed formulas reproduce;
7. no collisions / forbidden overlap;
8. writes confined to the Stage 2 result namespace;
9. Stage 1 and Stage 1b result roots untouched;
10. no data/trusted*, data/trusted_clean*, or data/provenance mutation;
11. whole-repo protected digest outside the Stage 2 result root unchanged where
    current infrastructure supports it;
12. runtime source override restored on all exit paths;
13. deterministic replay contract;
14. finite valid statistics OR explicit registered degeneracy classification;
15. all expected model cells present for analyzable repetitions.

NC1 integrity invariants are preservation of the target multiset per target year,
target missingness/null mask, feature matrix, row set, and canonical splits;
permutation of both train and test years; and no test-only construction.

NC0 integrity invariants are byte-identical target, fresh independent noise,
one joint row permutation of the mask per feature year, the same joint
permutation across all feature columns, preserved per-feature-year missingness
counts, preserved row-wise co-missingness multiset, the frozen canonical
rank-percentile transform after masking, and unchanged six models/splits.
Diagnostic invariants are separate from confirmatory invariants.

There is no integrity threshold on FPR, rejection count, IC, p-value
uniformity, Wilson interval location, gate result, NC0/NC1 agreement,
equivalence result, or degeneracy magnitude beyond completeness classification
itself. High FPR is valid science, not an invalid run. Integrity is evaluated
first; the scientific gate is evaluated only after integrity.

#### Claim boundary and registration-only boundary

Stage 2 may establish only apparatus behavior under the registered null
constructions. It does not establish predictive edge, alpha, investment value,
production readiness, absence of leakage, absence of predictability, universal
FPR calibration, or naturally occurring IC calibration. Passing Stage 2 does not
prove absence of feature-side PIT/alignment leakage; that belongs to later
defect-injection stages. This remains research support only, not investment
advice.

The Stage 2 registration module makes no scientific draw and creates no result
root. At registration time, the current artifact registry does not require a
prospective Stage 2 generated-output contract because no output files exist.
Before any future Stage 2 execution, its implementation task must add the
runner, Makefile target, governed result root, and one ownership contract per
emitted file before the run. No Stage 2 result root exists at this amendment
time, and no Stage 1 or Stage 1b artifact is changed.

### 2026-09-04 — Stage 3 dated amendment and registration

**What changed.** The Stage 3 stage entry above is refined into a closed,
machine-checkable registration. The old block is not silently rewritten; it
remains above as written, and this amendment records the refinement
prospectively before any Stage 3 injection or draw. The full registration is
`docs/thesis/STAGE_3_REGISTRATION.md`, with machine-readable constants in
`experiments/thesis/stage3_registration.py`.

**What had already been observed.** Stage 1, Stage 1b, and the completed Stage 2
governed run were all known, as were the current contents of the repository's
protection surfaces. No Stage 3 injection has been constructed, no Stage 3 draw
has been made, and no Stage 3 result exists at amendment time.

**Closed first-draw family.** Exactly five defect classes, one injection each,
no severity grid and no repeated performance experiment:
`FUTURE_YEAR_FEATURE_LEAKAGE` (4000), `T_TPLUS1_MISALIGNMENT` (4001),
`TARGET_LEAKAGE_INTO_FEATURES` (4002), `LOOKAHEAD_UNIVERSE_MEMBERSHIP` (4003),
`DUPLICATE_ROW_INFLATION` (4004). The stage entry's "at minimum" enumeration is
closed to exactly these five for the first governed draw.

**Source pin.** Only
`data/trusted_clean/modeling_dataset_training_2020_2025.csv`, SHA256
`3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.
FI-DATA-EXPAND outputs are not Stage 3 inputs; expanded or PIT-corrected
datasets require a separate versioned path and separate prospective governance.

**Guard definition.** For each defect class the guard is a closed preregistered
mapping to an existing protection surface present on authoritative base
`c418563f432f5b253fb3b0e69619c76608ea15ea` — a named validator condition or
`issues[]` member, a named command failure or exit, a named existing test, or a
named provenance/integrity guard. Detection counts only if a preregistered
existing guard fires before any model or significance evaluation. No new guard
may be added before the first governed draw to make the experiment pass. Where
no applicable existing guard exists, the registration records `NONE_EXISTING`
explicitly.

**Registered guard gaps.** Three of the five defects are preregistered as
`NOT_DETECTED`, because the authoritative base carries no reachable guard for
them: for `FUTURE_YEAR_FEATURE_LEAKAGE` (4000) no surface compares a feature
cell against its upstream year-of-record; for `T_TPLUS1_MISALIGNMENT` (4001) the
only alignment surface checks the `target_year` column arithmetic rather than
target value provenance; and for `LOOKAHEAD_UNIVERSE_MEMBERSHIP` (4003) no
point-in-time universe-membership record exists anywhere in the repository. The
expected first-draw guard gaps are therefore exactly 4000, 4001, and 4003. The
expected first-draw outcome is **FAIL — INFORMATIVE**. This is a prospective
expectation, not an observed scientific result. The family is not narrowed to
the working guards, no gap is repaired before the draw, any later repair belongs
to a separate remediation stage, and first-draw artifacts remain immutable.

**Expected detections.** `TARGET_LEAKAGE_INTO_FEATURES` (4002) and
`DUPLICATE_ROW_INFLATION` (4004) are preregistered as `DETECTED`, each by an
existing surface found on the authoritative base and neither by a guard added or
repaired here. The expected first-draw map is 4000 `NOT_DETECTED`, 4001
`NOT_DETECTED`, 4002 `DETECTED`, 4003 `NOT_DETECTED`, 4004 `DETECTED`.

**Provenance guard reachability.** `scripts/data_collection/build_cell_provenance.py`
is a reachable provenance/integrity guard, not an input-blind one: `generate`,
`resolve_input`, `open_checked_file`, and `prepare_output_dir` all take a
caller-supplied `root` and evaluate every containment assertion against it, and
only the *relative* input path is frozen. It is therefore reached by
materializing the ten declared relative inputs under a private temporary root —
the pattern `tests/test_cell_provenance.py::regenerated` already exercises on
the authoritative base. Under that containment mode, `PRIVATE_PROVENANCE_ROOT`,
the module freezes the dataset's column set twice (the `feature_passports.json`
passport names inside `generate`, `COLUMN_SPECS` inside `build_records`) and
fails closed on 4002's added `leaked_next_year_return_pct` column before it
resolves a single cell; it also fails closed on 4004's duplicated
`(ticker, year)` key. The named target-leakage validator condition for 4002
remains `STRUCTURALLY_UNREACHABLE` and is recorded as a separate,
existing-but-useless guard-surface fact; it is not repaired. The module's later
lineage-closure condition fires identically on the clean comparator and on every
injected frame for the pinned training source, whose per-ticker year grid is
incomplete, so it is registered as a baseline terminal state — never a detection
signal and never a containment failure.

**Registration-test boundary.** The registration tests inspect source, read the
frozen dataset read-only, verify frozen source facts and registration constants,
prove source semantics structurally, and prove that no Stage 3 result root
exists. They construct no injected frame: the 4000 transformation, the 4001
rotation, the 4002 leak column, the 4003 membership selection, and the 4004
duplication are all Stage 3 defect constructions and belong to the separate
implementation tests. Every frozen injection count in the registration is
consequently a prospective expectation.

**Secondary consumer authority.** The secondary IC depends on
`experiments/run_experiments.py`, which is pinned by full SHA256
`265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543` and is
unchanged from the authoritative base. The registered split tuple must equal
`experiments.run_experiments.SPLITS` exactly — same names, order,
`train_target_years`, and `test_feature_year`; a subset is not sufficient.

**4001 stale collateral.** The 4001 injection rotates observed
`next_year_return_pct` within ticker and recomputes nothing, so the six other
derived `next_year_*` target columns — `next_year_rank_by_return`,
`next_year_return_percentile`, `next_year_top_10pct_returner`,
`next_year_top_20pct_returner`, `next_year_excess_return_vs_bist100`,
`next_year_outperform_bist100` — remain **stale collateral**. That is disclosed,
not repaired. They are forbidden from influencing the Stage 3 estimand: 4001
primary detection uses only the registered guard surfaces, 4001 secondary IC uses
only the canonical predictor features plus `next_year_return_pct` as target, and
no other `next_year_*` column may be a predictor, alternate target, alignment
authority, detection signal, or secondary IC input. An implementation path that
consumes one classifies 4001 **INCONCLUSIVE**. Repository authority makes this
hold: `_feature_cols` excludes every `next_year_`-prefixed column, and the
registered secondary target is the single literal `next_year_return_pct`.

**Decision rule.** PASS requires all five completed registered defects to be
detected by their preregistered existing guards; FAIL if at least one completed
registered defect is not detected; INCONCLUSIVE if at least one registered
defect cannot be evaluated exactly as preregistered due to integrity,
containment, execution, or completeness failure. Integrity and INCONCLUSIVE take
precedence over the scientific PASS/FAIL decision. The primary decision does not
depend on model performance, an IC threshold, p-values, permutation
significance, or multiplicity.

**Secondary metric.** The stage entry's secondary "inflation in apparent IC" is
made explicit and bounded: only for an undetected defect, apparent IC distortion
is computed descriptively with Ridge, the existing canonical walk-forward
splits, and the target and modeling semantics already frozen in the repository.
For each canonical test split it is the signed difference
`delta_ic(split) = injected_ic(split) - clean_ic(split)`, where each IC is the
Spearman correlation between Ridge prediction and observed target. Values are
not pooled across splits or defects and have no aggregate threshold. It is
NON-GATING and DESCRIPTIVE ONLY — no p-value, no significance test, no
multiplicity correction, no predictive-edge inference — and it is never
computed for a detected or inconclusive defect.

**Multiplicity.** Unchanged and none required: each defect is a separate
prespecified binary check with an expected answer, not a search.

**Seeds.** Base seed 42 from `provenance.SEEDS["defect_injection"]`;
`injection_seed(defect_id) = BASE_SEED * 1_000_003 + defect_id`. IDs 4000–4004
do not overlap Stage 1 (0–199), Stage 1b (200–599), the reserved band
(600–999), or Stage 2 (1000–3999). All five injections are `NO_RNG`; RNG
consumption in the first draw is an integrity failure.

**Containment.** Every injection is built on a private in-memory copy of the
pinned source. Where a registered surface requires a path, the frame is written
to a private temporary directory outside `data/` and outside
`experiments/results_thesis/`. Evaluating a validator-issue surface requires
redirecting the four `validate()` report outputs to that private directory and
restoring them on all exit paths; evaluating one by writing into
`data/trusted_clean` is forbidden and makes the defect INCONCLUSIVE. Evaluating
a cell-provenance surface requires the `PRIVATE_PROVENANCE_ROOT` mode described
above, under which no canonical path and no `data/provenance` output is touched.
Canonical digests are re-verified after every defect. An `INPUT_BLIND` surface —
one that reads only canonical committed paths — staying silent is neither an
evaluation nor a non-detection.

**Stage 7 gate.** Stage 3 does not silently unlock Stage 7. The existing Stage 7
wording — "Only after stages 1–3 pass" — remains authoritative and is not
amended. Stage 1 remains FAILED AS WRITTEN — INFORMATIVE, so Stage 7 remains
blocked under the current wording even if Stage 3 passes. Any future Stage 7
reinterpretation or amendment requires separate prospective governance.

**Claim boundary.** Stage 3 may establish only whether the preregistered
existing guard map detects the five preregistered synthetic defects under the
frozen construction. It does not establish absence of all leakage, universal
pipeline safety, predictive edge, alpha, investment value, production readiness,
correctness of expanded datasets, or correctness of future unknown defect
classes. A FAIL is informative and expected if existing guard gaps are real.
This remains research support only, not investment advice.

**Registration-only boundary.** The Stage 3 registration module makes no
injection, no scientific draw, and creates no result root. At registration time
the artifact registry does not require a prospective Stage 3 generated-output
contract, because no output files exist. Before any future Stage 3 execution,
its implementation task must add the runner, Makefile target, governed result
root, and one ownership contract per emitted file before the run. No Stage 3
result root exists at this amendment time, and no Stage 1, Stage 1b, or Stage 2
artifact is changed.
