# Stage 2 Prospective Registration

This is the owner-locked registration for the Stage 2 expanded negative-control
experiment. It is companion to
docs/thesis/PRE_EXPERIMENT_PROTOCOL.md and is machine-checked by
tests/test_thesis_stage2_registration.py against
experiments/thesis/stage2_registration.py.

This document is registration only. It does not implement a scientific runner,
make a scientific draw, read the modeling dataset, create a result root, or
produce a Stage 2 outcome. The Stage 2 result root
experiments/results_thesis/negative_control/ does not exist at registration
time.

## Registration status and chronology

This registration is prospective but **not blind**. The following information
was already known before Stage 2 was registered:

- Stage 1 was **FAILED AS WRITTEN — INFORMATIVE**.
- The complete Stage 1b calibration outcome had already been inspected. Stage
  1b is diagnostic/calibration evidence, not a predictive-edge result.
- The legacy dense-Gaussian placebo and the pre-Stage-2 missingness-mask
  diagnostics had already been inspected.
- The known significance defects had been repaired before this registration.

The Stage 1b governed run and independent review were complete and PASS before
this registration. Historical Stage 1 and Stage 1b artifacts were not rerun or
rewritten. No Stage 2 scientific draw, repetition, result, or outcome exists at
amendment or registration time.

The registration is prospective in the sense that the Stage 2 design below is
fixed before any Stage 2 execution. It is not a blind design because the
disclosures in the next section were available when the design was written.

## Pre-run disclosures

### Stage 1 and Stage 1b

The Stage 1 outcome was:

FAILED AS WRITTEN — INFORMATIVE

The complete Stage 1b calibration outcomes were already inspected before this
registration. The observed detection probabilities were:

| theta | detection probability |
|---:|---:|
| 0.00 | 0/400 = 0.0000 |
| 0.10 | 1/400 = 0.0025 |
| 0.20 | 45/400 = 0.1125 |
| 0.30 | 243/400 = 0.6075 |
| 0.35 | 347/400 = 0.8675 |
| 0.40 | 384/400 = 0.9600 |

Mean final evaluated IC was:

| theta | mean final evaluated IC |
|---:|---:|
| 0.00 | 0.090305625773 |
| 0.10 | 0.099628182092 |
| 0.20 | 0.130441418767 |
| 0.30 | 0.182221558521 |
| 0.35 | 0.212800525022 |
| 0.40 | 0.250279183231 |

At theta=0, the mean raw carrier IC was approximately **-0.0043485** and the
mean final IC was approximately **+0.0903056**. This is a known interpretation
limitation of the Stage 1b calibration: theta=0 is not a zero-signal market
world because real non-carrier features remain in the pipeline.

### Legacy placebo and mask diagnostics

The legacy dense-Gaussian placebo had:

- R=25;
- 0 family-wise rejections; and
- 0 failed repetitions.

It is a **historical smoke test only, not Stage 2 calibration**. It is not
treated as evidence for the Stage 2 control definitions.

The pre-Stage-2 design review also computed missingness-mask diagnostics:

- one missingness indicator had pooled IC approximately **+0.225**; and
- **19 of 33** mask columns had |pooled IC| > .05.

These observations motivated the NC0 design below and are disclosed before any
Stage 2 outcome.

### Significance repair and historical-artifact boundary

Before this registration, the following known significance defects were
discovered:

- a non-finite observed statistic could produce the minimum p-value in a
  helper;
- the forward-2026 hand-rolled permutation path had the same failure mode; and
- analyze_model degeneracy behavior was unsafe / generic.

They were repaired before this registration. The old significance source SHA was
5fe0e88f9742c32b94425c493a41661ff541b6f1cc21d3c758293a06f09017e6; the
repaired Stage 2 significance source SHA is
08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3.

The repaired source is pinned below. Historical Stage 1, Stage 1b, and other
artifacts retain their existing provenance and were not rerun or rewritten.
No Stage 2 scientific draw or outcome exists.

## Dated amendment to the pre-experiment protocol

The full amendment is appended to
docs/thesis/PRE_EXPERIMENT_PROTOCOL.md under the date **2026-09-02**. It is
part of this registration and must be read with this document.

The old Stage 2 design:

> **6 models × 2 null constructions = 12 tests, Bonferroni across 12**

is superseded **prospectively before any Stage 2 outcome**. The old block is not silently rewritten, and no historical Stage 1 or Stage 1b outcome is altered.

The amended design records that:

- the real evaluation's within-repetition operating family is six ML models;
- the model-family divisor is the frozen literal **6**;
- the two confirmatory controls form a separate progression-decision family;
- the across-control gate uses exact one-sided binomial tests with Bonferroni
  alpha=.025 per control;
- the Stage 1 divisor **5 is not used** for the Stage 2 control gate;
- delta=.05 is retained as descriptive/non-gating equivalence information; this
  is a weakening of the previously written Stage 2 pass rule; and
- no Stage 2 result exists at amendment time.

## Frozen source and panel contract

The future runner must use the following source and dataset identity:

| Item | Frozen value |
|---|---|
| Dataset path | data/trusted_clean/modeling_dataset_training_2020_2025.csv |
| Dataset SHA-256 | 3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78 |
| Repaired significance SHA-256 | 08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3 |
| Canonical panel/splits source | experiments/run_experiments.py |
| Canonical panel/splits source SHA-256 | 265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543 |
| Thesis provenance source SHA-256 | 5a06c5c2e753cef0fe57e348250e7847b393c6173cd54c8be273f97976dc29f8 |
| Target column | next_year_return_pct |
| Canonical feature years | 2020, 2021, 2022, 2023, 2024 |
| Canonical target years | 2021, 2022, 2023, 2024, 2025 |
| Canonical feature columns | 40 |
| Canonical imputation | NaN -> 0.5 in the existing fitting path |

The canonical panel uses within-feature-year average ranks expressed as
percentiles. The row universe, feature matrix, target null locations, and
walk-forward split definitions are inputs to the Stage 2 mechanisms, not
runtime choices.

### Canonical splits

These are pinned from experiments/run_experiments.py:

| Split | Training target years | Test feature year | Test target year |
|---|---|---:|---:|
| test_2023 | 2021, 2022 | 2022 | 2023 |
| test_2024 | 2021, 2022, 2023 | 2023 | 2024 |
| test_2025 | 2021, 2022, 2023, 2024 | 2024 | 2025 |

No split may be added, removed, reordered for identity, or changed after
registration.

## Confirmatory control family

There are exactly two confirmatory progression controls:

1. NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN
2. NC1_TARGET_PERMUTATION

Both are **CONFIRMATORY / GATING**. They form a separate decision family of
size 2. The diagnostic arm below is outside this family and cannot enter its
multiplicity correction or gate.

### NC1 — target permutation

Name: NC1_TARGET_PERMUTATION

Role: **CONFIRMATORY / GATING**

For every repetition, NC1 will:

1. operate on the frozen canonical source/panel pipeline;
2. permute only observed next-year target values;
3. permute independently within every target year;
4. preserve target-null locations exactly;
5. include all years used by training and testing;
6. retrain all six models under the permuted target; and
7. evaluate all registered splits normally.

Test-year-only target permutation is **FORBIDDEN**. Holding y_pred fixed and
permuting only a test year's y_true is one draw from the same within-year
reference distribution already used by significance.py; it is circular and
does not test retraining or apparatus behavior.

NC1 preserves:

- the target multiset within each year;
- target missingness/null locations;
- the feature matrix;
- the row universe; and
- the train/test split definitions.

NC1 destroys within-year feature/target association and the training signal from
the real target mapping. Its scope limitation is explicit: it is a null for
within-year rank association and **does not establish absence of feature-side
leakage**.

### NC0 — row-permuted real mask with rank-Gaussian noise

Name: NC0_ROW_PERMUTED_MASK_RANK_GAUSSIAN

Role: **CONFIRMATORY / GATING**

For every repetition, NC0 will:

1. generate fresh iid N(0,1) for every canonical row × feature cell;
2. for each feature year separately, take the canonical real 40-column
   missingness matrix;
3. apply **one independently seeded row permutation within that year jointly
   across all 40 feature columns**;
4. apply the permuted mask to the fresh noise;
5. apply the **same canonical within-year average-rank percentile transform**
   used by the panel pipeline;
6. keep the real target unchanged;
7. keep canonical imputation unchanged: NaN -> 0.5; and
8. retrain and evaluate the full six-model pipeline.

NC0 preserves each feature-year missingness rate and the row-wise co-missingness
pattern multiset. It destroys mask-to-target row alignment. The target,
feature-year row universe, canonical splits, and six registered models remain
unchanged. NC0 is a target-alignment/missingness-channel null; it does not
establish absence of other feature-side leakage.

The raw-noise values are fresh for every canonical row × feature cell. The mask
permutation is one joint permutation across all 40 columns for each feature
year, not 40 independent column permutations.

#### Rejected NC0 alternatives

The following alternatives are registered as rejected, not as hidden
confirmatory arms:

| Alternative | Disposition |
|---|---|
| LEGACY DENSE GAUSSIAN | Valid mathematical null, but it removes the real missingness/imputation path and runs an easier design matrix than the real apparatus. |
| EXACT UNPERMUTED REAL MASK | Not a confirmatory null because pre-run diagnostics showed the mask itself is target-associated. |
| RAW N(0,1) + mask without rank transform | Forbidden because imputation value 0.5 becomes an artificial off-centre feature cluster not present in the canonical rank-percentile panel. |

### NC0 diagnostic arm

Name: NC0_MASK_ALIGNED_DIAGNOSTIC

Role: **DIAGNOSTIC / NON-GATING / OUTSIDE CONFIRMATORY FAMILY**

This diagnostic is included in the registration with R=1000 and IDs
3000-3999. It uses fresh rank-Gaussian noise with the exact real per-cell
missingness mask retained in its real row alignment, with the target unchanged.
Its purpose is to measure mask-mediated target association and
imputation-channel behavior.

It is **not an exact null-FPR test** because the real mask is target-associated.
Its outcome may not affect confirmatory multiplicity, Stage 2 PASS/FAIL,
confirmatory control definitions, or the progression gate.

## NC2 and NC3 status

NC2 is defined as **cross-year/cohort target derangement that moves target
values across years while preserving a ticker/cohort relation**.

Status: **EXCLUDED FROM STAGE 2 CONFIRMATORY FAMILY**.

There is no NC2 execution in Stage 2. It is not a clean null for the
within-year Spearman estimand: it can preserve persistent ticker return
structure or alter year distributions, and it has low marginal value versus NC1
and later alignment-defect testing.

NC3 is defined as **single-feature-at-a-time within-year permutation while other
features remain aligned**.

Status: **DEFERRED DIAGNOSTIC**.

There is no NC3 execution in Stage 2. NC3 is not a negative-control null; it is
feature importance/ablation because the remaining real features retain real
target association. If independently permuting all features within year is
discussed, it is a separate diagnostic construction, not NC3 confirmatory and
not a third confirmatory family member.

## Repetitions, IDs, and RNG

The base seed is:

BASE_SEED = provenance.SEEDS["negative_control"] = 42

No Stage 1 or Stage 1b repetition is pooled with Stage 2.

| Allocation | IDs |
|---|---:|
| Stage 1 historical | 0-199 |
| Stage 1b historical | 200-599 |
| Reserved gap | 600-999 |
| NC0 confirmatory | 1000-1999 inclusive |
| NC1 confirmatory | 2000-2999 inclusive |
| NC0 diagnostic | 3000-3999 inclusive |

R_CONFIRMATORY_PER_CONTROL = 1000 exactly and R_DIAGNOSTIC = 1000. NC0, NC1,
and the diagnostic each have a complete contiguous ID matrix. There is no
pooling with Stage 1 or Stage 1b.

### Construction seeds

Construction seeds are frozen as:

seed(stream, repetition_id) = BASE_SEED * 1_000_003 + stream * 10_007 + repetition_id

The stream identities are:

| Stream | ID |
|---|---:|
| NC0_NOISE | 10 |
| NC0_MASK_ROW_PERMUTATION | 11 |
| NC1_TARGET_PERMUTATION | 20 |
| NC0_DIAGNOSTIC_NOISE | 30 |

Use fixed sorted year, row, and feature-column order. Do not use
enumerate(sorted(...)) to invent stream identities. The registration tests
assert no construction-seed collisions, disjoint construction streams, no
Stage 1/Stage 1b overlap, and preservation of the reserved gap.

### Significance seeds

For repetition repetition_id:

significance_seed(repetition_id) = significance.DEFAULT_SEED + repetition_id = 42 + repetition_id

The same registered significance seed is supplied to all six model analyses for
that repetition. Significance seeds are unique by repetition ID where
uniqueness is intended; sharing one across the six models within a repetition
is intentional.

Every model analysis uses 10,000 permutations and 10,000 bootstrap resamples.

## Model family and within-repetition rule

The six ML models are exactly:

- linear_regression
- ridge
- lasso
- elasticnet
- random_forest
- gradient_boosting

No model may be added or removed after registration. Baselines are not members
of this Stage 2 confirmatory model family.

The within-repetition model-family divisor is the frozen literal **6**. It is
not derived from the number of controls, diagnostic count, Stage 2 grid length,
or surviving model count. Each model's permutation p-value is **two-sided**.

For one complete repetition:

min_raw_p = minimum valid raw two-sided permutation p across all six registered models

family_reject = min(1, 6 * min_raw_p) < 0.05

The headline model is selected by minimum raw p, then model name ascending.

The Stage 1 divisor 5 is not used in this rule. Stage 1's divisor and Stage 2's
control-family correction are separate contracts.

## Strict completeness and degeneracy

Stage 2 uses a **STRICT COMPLETE DENOMINATOR**. Each confirmatory control must
have exactly 1000 analyzable repetitions.

Before significance analysis, the future runner must check each model and
evaluated split for:

- target having fewer than two distinct finite values;
- prediction having fewer than two distinct finite values; and
- a non-finite observed Spearman statistic.

The repaired significance.py fail-closed behavior is required. Model-level
degeneracy is recorded explicitly.

Repetition rules:

- any partial-model degeneracy is INVALID / DEGENERATE_PARTIAL_MODEL;
- all-model degeneracy is INVALID / DEGENERATE_ALL_MODELS;
- an unexpected exception is INTEGRITY_FAILURE and aborts/fails closed;
- invalid repetitions may not disappear;
- invalid repetitions may not be converted to p=1;
- invalid repetitions may not be counted as a non-rejection;
- invalid repetitions may not reduce divisor 6; and
- invalid repetitions may not reduce the denominator and still allow PASS.

MIN_ANALYZABLE_DENOMINATOR = 1000 exactly. If either confirmatory control has
fewer than 1000 analyzable repetitions, Stage 2 is **INCONCLUSIVE**. It cannot
PASS or FAIL through the scientific FPR gate. Degeneracy counts remain
reportable apparatus findings.

## Primary estimand and exact progression gate

For each confirmatory control c, let X_c be the number of the 1000 complete
repetitions in which the six-model family rule rejects.

The FPR estimate is:

X_c / 1000

Report a point estimate and a pointwise two-sided 95% Wilson interval. The
Wilson interval is descriptive and is **not** the progression gate.

There are exactly two confirmatory progression controls, {NC0, NC1}. They form
a decision family of size 2 with a family-level false-progression-block target
of 0.05. Bonferroni gives:

per-control alpha = 0.025

For each control:

H0: FPR_c <= 0.05
H1: FPR_c > 0.05

Under the complete denominator:

X_c ~ Binomial(1000, 0.05) under the boundary null

Use the exact one-sided binomial upper tail. The frozen critical count is:

EXACT_K_CRIT_R1000 = 65

The exact boundary probabilities are:

P[Binomial(1000,.05) >= 65] = 0.02074989936553777 <= .025
P[Binomial(1000,.05) >= 64] = 0.028428397283993795 > .025

Therefore:

- a control fails iff X_c >= 65;
- Stage 2 fails iff NC0 fails or NC1 fails; and
- Stage 2 passes iff both controls have exactly 1000 analyzable repetitions,
  NC0 X <= 64, NC1 X <= 64, and the integrity contract passed.

Stage 2 is INCONCLUSIVE if either analyzable denominator is below 1000.

The Bonferroni family control is valid under arbitrary dependence between NC0
and NC1. The controls are not assumed independent.

### Declared operating characteristics

Per-control power to trigger the exact >=65 rule is registered as:

| True FPR | Power |
|---:|---:|
| 0.06 | 0.2703680264 |
| 0.075 | 0.8982904410 |
| 0.10 | 0.9999627573 |

Stage 2 has low power against mild inflation around 0.06. R=1000 is not a
magical resolution threshold.

## Equivalence limb

EQUIVALENCE_DELTA = 0.05

The equivalence limb is **descriptive/non-gating**. Report mean pooled IC per
confirmatory control per model with a two-sided 90% CI against ±0.05.

A violation is a reportable finding requiring investigation before Stage 3
progression, but it does not by itself cause Stage 2 scientific FAIL.

This explicitly weakens the previously written Stage 2 pass rule. Delta 0.05 is
not a FinanceIQ SESOI. SESOI remains **UNRESOLVED**, and SESOI is not required
for Stage 2.

## Closed integrity contract

The following is a **closed list**. Integrity is evaluated first; the scientific
gate is evaluated only after integrity passes. No other statistical or
scientific condition can invalidate the run.

1. frozen source dataset path and SHA match;
2. repaired significance.py SHA matches
   08062b5e2e9af9d9a91200665811492c373dc6fa8db1acd0a849cb3d3d932ab3;
3. registered Stage 2 source/module hashes match;
4. complete expected repetition-ID matrices;
5. no duplicates;
6. exact seed formulas reproduce;
7. no collisions or forbidden overlap;
8. writes are confined to the Stage 2 result namespace;
9. Stage 1 and Stage 1b result roots are untouched;
10. no data/trusted*, data/trusted_clean*, or data/provenance* mutation;
11. the whole-repo protected digest outside the Stage 2 result root is
    unchanged where current infrastructure supports it;
12. runtime source override is restored on all exit paths;
13. deterministic replay contract;
14. finite valid statistics or an explicit registered degeneracy
    classification; and
15. all expected model cells are present for analyzable repetitions.

The mechanism invariants for NC1 are:

- target multiset per target year preserved;
- target missingness/null mask preserved;
- feature matrix unchanged;
- row set unchanged;
- canonical splits unchanged;
- train and test years permuted; and
- no test-only construction.

The mechanism invariants for NC0 are:

- target byte-identical;
- fresh independent noise construction;
- one joint row permutation of the mask per feature year;
- the same joint row permutation applied across all feature columns;
- per-feature-year missingness counts preserved;
- row-wise co-missingness multiset preserved;
- canonical rank-percentile transform applied after masking exactly as frozen;
  and
- six registered models and splits unchanged.

Diagnostic invariants are separate from confirmatory invariants.

### Explicit integrity exclusions

There is no integrity threshold on:

- FPR;
- rejection count;
- IC;
- p-value uniformity;
- Wilson interval location;
- gate result;
- NC0/NC1 agreement;
- equivalence result; or
- degeneracy magnitude beyond completeness classification itself.

High FPR is valid science, not an invalid run.

## Claim boundary

Stage 2 may establish only apparatus behavior under the registered null
constructions. It does **not** establish:

- predictive edge;
- alpha;
- investment value;
- production readiness;
- absence of leakage;
- absence of predictability;
- universal FPR calibration; or
- naturally occurring IC calibration.

Passing Stage 2 does not prove absence of feature-side PIT or alignment leakage.
That belongs to later defect-injection stages.

This is research support only, not investment advice.

## Registration-only and future governance boundary

experiments/thesis/stage2_registration.py is intentionally stdlib-only and has
no scientific execution path. Its seed functions are arithmetic only. It does
not import the dataset, fit a model, call significance.py, create an output
directory, or write a file.

The current artifact registry remains unchanged at registration time:
negative_control has no generated files, so it does not have an entries[]
contract. Prospective artifact contracts are **NOT_REQUIRED_AT_REGISTRATION**
under the current proposed_future rule. Before any future Stage 2 execution,
the implementation task must add the runner, a real Makefile target, the Stage 2
result root to artifact_registry.json governed roots, and one ownership contract
for every emitted file in the same pre-run governance step. This registration
does not waive that requirement.

No Stage 2 result root exists, no Stage 2 scientific runner exists, no Stage 2
repetition has been generated, and no Stage 1 or Stage 1b artifact is changed
by this registration.

### Implementation-time governance wiring — 2026-09-03

Implementation has now frozen the seven future filenames. `artifact_registry.json`
now contains prospective ownership contracts for those filenames. The Stage 2
result root remains absent, and no Stage 2 run or scientific draw has occurred.
This is the implementation-phase fulfillment of the pre-run obligation already
anticipated by the registration. No scientific registration clause is changed.
