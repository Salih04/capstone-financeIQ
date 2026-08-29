# Stage 1 — raw-layer positive control

This stage injects a synthetic relationship into one raw column and measures how much of it survives the pipeline. It is apparatus validation on manufactured input, not evidence about BIST equities: recovering an injected quantity says only that the instrument responds to a known input, and the repository's committed walk-forward null is untouched by anything measured here.

Protocol: `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` · git `794804e0` · seed 42 · implementation `44c897568f17`

## Design

- Injection site: one raw feature column of the modeling CSV, in its own units, before run_experiments.build_panel() performs feature construction
- Mechanism: within-year permutation of the carrier's own observed values into the order of a Gaussian-copula latent score s = rho*z + sqrt(1-rho^2)*eps, where z is the unit-scaled normal score of the future-return ranking and rho = 2*sin(pi*theta/6)
- Preregistered grid: [0.0, 0.1, 0.2, 0.3, 0.4] (MDE_base 0.182271)
- Model: `ridge` · family 5 · Bonferroni across the 5 preregistered levels
- Carriers: primary `equity`, secondary `current_ratio`
- Repetitions per descriptive level: 200 · permutations 10000

## Confirmatory arm (the preregistered Stage 1 test)

- Recovered IC by level: [0.09406142009, 0.116002328212, 0.109438802294, 0.151687843758, 0.304713005705]
- Adjusted p by level: [0.763923607639, 0.378462153785, 0.46495350465, 0.115488451155, 0.000499950005]
- Monotone increasing: **False**
- Both gate levels reject: **False**
- Stage 1 gate: **NOT PASSED**

## Gate informativeness diagnostic (POST-RUN)

Using the existing primary descriptive repetitions as coherent five-level draws (200 draws): P(strictly monotone recovered IC) = 0.295; P(both required high-grid levels reject) = 0.56; P(original Stage 1 gate passes) = 0.195.
This is a descriptive post-run diagnostic of gate informativeness. It does not alter the gate, its thresholds, or the Stage 1 status.

## Detection curve — primary carrier

| injected IC | detections / reps | detection rate | 95% CI | mean recovered IC | recovery bias |
|---|---|---|---|---|---|
| 0.00 | 0/200 | 0.000 | [0.000, 0.019] | 0.0909 | +0.0909 |
| 0.10 | 0/200 | 0.000 | [0.000, 0.019] | 0.1001 | +0.0001 |
| 0.20 | 34/200 | 0.170 | [0.124, 0.228] | 0.1366 | -0.0634 |
| 0.30 | 123/200 | 0.615 | [0.546, 0.680] | 0.1803 | -0.1197 |
| 0.40 | 186/200 | 0.930 | [0.886, 0.958] | 0.2432 | -0.1568 |

### >=80% detection on the preregistered grid

Lowest grid level reaching 80% detection: **0.4** (observed 0.93).

Read off the preregistered grid only. The true crossing lies somewhere at or below this level; this design cannot localize it further without adding levels, which the protocol forbids.

## Attenuation by stage — primary carrier

Raw IC values are shown at every checkpoint. The raw, feature-construction, and model-input/imputation rows are identity/invariant checkpoints; only the carrier-signal to fitted-prediction transition is a substantive attenuation measurement.

| injected IC | ic_injected (design_constant) | ic_raw_carrier (identity_invariant) | ic_panel_carrier (identity_invariant) | ic_model_input_carrier (identity_invariant) | ic_model_prediction (substantive_transition) | ic_final_evaluation (evaluation_identity) |
|---|---|---|---|---|---|---|
| 0.00 | 0.0000 | 0.0005 | 0.0005 | 0.0005 | 0.0909 | 0.0909 |
| 0.10 | 0.1000 | 0.1020 | 0.1020 | 0.1020 | 0.1001 | 0.1001 |
| 0.20 | 0.2000 | 0.2107 | 0.2107 | 0.2107 | 0.1366 | 0.1366 |
| 0.30 | 0.3000 | 0.3004 | 0.3004 | 0.3004 | 0.1803 | 0.1803 |
| 0.40 | 0.4000 | 0.3939 | 0.3939 | 0.3939 | 0.2432 | 0.2432 |

### Background-adjusted diagnostic (heuristic only)

The background-adjusted quantity is `(recovered IC - theta=0 background IC) / injected IC`. It is a heuristic descriptive diagnostic, not a mathematically exact decomposition of Spearman IC. The ratio is emitted as NA for identity/invariant checkpoints and the injected design constant (where it sits near 1.0 by construction and is not a measured coefficient) and where the theta=0 background dominates; the full per-checkpoint columns and the suppression reason are in `attenuation_by_stage.csv`.

| injected IC | final theta=0 background IC | heuristic adjusted final IC | heuristic ratio |
|---|---|---|---|
| 0.00 | 0.090871241231 | None | None |
| 0.10 | 0.090871241231 | 0.009217610718 | None |
| 0.20 | 0.090871241231 | 0.045769926098 | 0.22884963049 |
| 0.30 | 0.090871241231 | 0.089406945702 | 0.29802315234 |
| 0.40 | 0.090871241231 | 0.152330126567 | 0.380825316418 |

## Analytic vs empirical power — primary carrier

Analytic references come from `experiments/significance.py`, called unchanged, at the Bonferroni-adjusted per-test alpha. The empirical repetitions hold the realized equity panel fixed; across repetitions the synthetic injection changes and the permutation-test RNG changes, so the empirical detection-rate variation carries injection-draw randomness plus permutation Monte-Carlo randomness, but not resampling uncertainty from another market panel or time sample. Fisher-z analytic/simulation power instead integrates over cross-sectional sampling variability. The curves therefore condition on different randomness, so their residual difference cannot be attributed simply to the test. They are useful diagnostics but are not interchangeable power estimates.

| injected IC | empirical detection | analytic power at injected IC | analytic power at recovered IC | simulated power at recovered IC |
|---|---|---|---|---|
| 0.00 | 0.0 | None | 0.116886625944 | 0.113 |
| 0.10 | 0.0 | 0.146681104902 | 0.146994502893 | 0.1442 |
| 0.20 | 0.17 | 0.693374654794 | 0.313488084276 | 0.306 |
| 0.30 | 0.615 | 0.983350576473 | 0.577083568223 | 0.5726 |
| 0.40 | 0.93 | 0.999944016147 | 0.884168879483 | 0.882 |

## Secondary descriptive carrier (missingness channel)

Carrier `current_ratio` carries the same injection at roughly half coverage. It makes no confirmatory claim; it exists to isolate how much signal the NaN -> 0.5 rank imputation removes.

Its observed-carrier checkpoint n = 120 differs from the post-imputation full-cross-section checkpoint n = 240. The secondary stagewise ratio therefore mixes missingness/imputation dilution with a changed evaluation population; it is not a pure attenuation coefficient.

| injected IC | raw carrier IC (n) | after imputation (n) | recovered IC | detection rate |
|---|---|---|---|---|
| 0.00 | -0.003695375136 (120) | -0.000921770981 (240) | 0.095308622487 | 0.0 |
| 0.10 | 0.105410873126 (120) | 0.067779573496 (240) | 0.101368074339 | 0.005 |
| 0.20 | 0.197911084164 (120) | 0.13041902153 (240) | 0.118049539527 | 0.035 |
| 0.30 | 0.308008502637 (120) | 0.205348505018 (240) | 0.140608820263 | 0.17 |
| 0.40 | 0.401865041854 (120) | 0.263803893684 (240) | 0.17970025323 | 0.6 |

## Strong-signal sanity control

Outside the preregistered grid and excluded from the power curve. At injected IC 0.90 the pipeline recovers 0.76399636516 with detection rate 1.0.

## Limitations

- Signal is injected into one carrier column; the recovered IC therefore reflects the pipeline's ability to isolate one informative feature among 40, not its ability to aggregate signal spread across many.
- The injection permutes the carrier's values within each year, which destroys that column's joint structure with the other features. The theta=0 rung shares the damage, so comparisons along the curve are internally consistent, but the absolute recovered IC is not the IC an equally strong naturally-occurring feature would give.
- The theta=0 rung is not a zero-IC world: the other 39 features retain whatever weak real structure they carry, so recovered IC at theta=0 estimates that background rather than zero.
- Only three test cross-sections of about 80 rows exist. Detection rates are measured over 200 repetitions and carry binomial uncertainty of roughly +/-3 percentage points.
- The detection threshold is read off five preregistered grid points. The true crossing is not localized, and no interpolated value is reported.
- Each Wilson detection-rate interval is conditional on the one fixed realized panel. It captures only the repetition-to-repetition variation over the declared repetitions -- across repetitions the synthetic injection draw changes and the permutation-test RNG changes, so it carries injection-draw randomness plus permutation Monte-Carlo randomness -- and excludes resampling uncertainty from drawing a different equity panel or time sample.
- The realized equity panel is fixed across repetitions. The synthetic injection changes across repetitions and the permutation-test RNG also changes across repetitions, so the empirical detection-rate variation includes injection-draw randomness plus permutation Monte-Carlo randomness; it still does not include resampling uncertainty from drawing another market panel or time sample. Fisher-z analytic/simulation power instead integrates over cross-sectional sampling variability, so the two curves condition on different randomness; their residual difference cannot be attributed simply to the test, and the curves are diagnostic rather than interchangeable power estimates.
- The raw, feature-construction, and model-input/imputation checkpoints for the primary 100%-coverage carrier are identity/invariant checks, not empirical claims of no attenuation. The substantive measured transition is carrier signal to fitted model prediction.
- The secondary carrier changes row population: its observed-carrier checkpoint n differs from the post-imputation full-cross-section n. Its stagewise ratio therefore mixes missingness/imputation dilution with changed evaluation population and is not a pure attenuation coefficient.
- Any background-adjusted ratio is a heuristic descriptive diagnostic, not a mathematically exact decomposition of Spearman IC. The ratio is emitted as NA for identity/invariant checkpoints and the injected design constant -- where it would sit near 1.0 by construction and could be misread as a measured attenuation coefficient -- and for levels where the theta=0 background dominates.
- The temporary run_experiments.TRAINING_MODELING override is process-global and this experiment is single-threaded; concurrent execution is outside this task's scope.
- Results describe this pipeline on this panel with this carrier. They do not generalize to other designs, frequencies, universes, or feature sets, and they establish nothing about BIST returns or investment value.
