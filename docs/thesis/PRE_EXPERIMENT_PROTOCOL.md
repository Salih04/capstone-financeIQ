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

*No amendments recorded.*
