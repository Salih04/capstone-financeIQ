# Stage 1b — positive-control calibration / diagnostic

Stage 1b characterizes how the frozen measurement pipeline responds to a synthetic relationship of known nominal strength injected into one raw column. It is apparatus characterization on manufactured input, not evidence about BIST equities: a recovered quantity here measures the instrument, and the repository's committed walk-forward null is untouched by anything reported here.

Registration: `docs/thesis/STAGE_1B_REGISTRATION.md` · protocol: `docs/thesis/PRE_EXPERIMENT_PROTOCOL.md` · git `9681646e` · seed 42 · implementation `61a34acd5778`

## Design

- Carrier: `equity` only · model `ridge`
- Grid (report order): [0.0, 0.1, 0.2, 0.3, 0.35, 0.4] · new rung 0.35
- Seed level-index map: {'0.0': 0, '0.1': 1, '0.2': 2, '0.3': 3, '0.4': 4, '0.35': 5} (frozen; report order is numeric, seed identity is the map)
- Repetitions: 400 per level, global ids 200–599
- Permutations 10000 · bootstraps 10000 · alpha 0.05
- Primary: Stage-1-operational-rule detection probability — `detected_stage1_rule = min(1, 5 * p_raw) < 0.05`
- Secondary: raw-p<0.05 detection probability — secondary, non-gating diagnostic — `raw p < 0.05` (gating: False)
- Scientific performance gate: **False**
- Not computed: Stage 1 confirmatory_gate, Stage 1 gate_informativeness, strict-monotonicity pass/fail, GATE_LEVELS rejection criterion, 80%-detection gate or interpolated threshold crossing
- Excluded historical Stage 1 arms: current_ratio missingness arm; theta=0.9

The divisor 5 is the frozen historical Stage 1 operating divisor, kept as one fixed operating point so this descriptive curve stays comparable to Stage 1. The six theta levels are not a hypothesis family and no family-wise-error-control claim is made across them.

## Calibration and detection by theta

| theta | mean realized raw carrier IC | mean final evaluated IC | primary detections / reps | primary rate | pointwise 95% Wilson | secondary rate |
|---|---|---|---|---|---|---|
| 0.00 | -0.00434849601 | 0.090305625773 | 0/400 | 0.0 | [0.0, 0.009512294334] | 0.0025 |
| 0.10 | 0.102416596163 | 0.099628182092 | 1/400 | 0.0025 | [0.000441447787, 0.014023285076] | 0.085 |
| 0.20 | 0.201434488856 | 0.130441418767 | 45/400 | 0.1125 | [0.085148458786, 0.147223569323] | 0.5275 |
| 0.30 | 0.303809043034 | 0.182221558521 | 243/400 | 0.6075 | [0.558841383341, 0.654113473377] | 0.9125 |
| 0.35 | 0.35281815782 | 0.212800525022 | 347/400 | 0.8675 | [0.830753680303, 0.897254783361] | 0.9675 |
| 0.40 | 0.408354038501 | 0.250279183231 | 384/400 | 0.96 | [0.936017752282, 0.97523093693] | 0.995 |

Wilson intervals are pointwise per theta. They are marginal intervals, not simultaneous or between-level comparison intervals, and no between-theta inference is drawn from them.

## Registered descriptive summaries

| theta | quantity | mean | SD | median | p05 | p95 |
|---|---|---|---|---|---|---|
| 0.00 | realized raw carrier IC | -0.00434849601 | 0.067700144829 | -0.002234941873 | -0.121988691177 | 0.098909061966 |
| 0.00 | final evaluated IC | 0.090305625773 | 0.01215560758 | 0.091275853045 | 0.070382922608 | 0.108042562512 |
| 0.10 | realized raw carrier IC | 0.102416596163 | 0.066112555564 | 0.10515055301 | -0.00526366149 | 0.205753868395 |
| 0.10 | final evaluated IC | 0.099628182092 | 0.019432697249 | 0.096960295888 | 0.073554497655 | 0.136879941381 |
| 0.20 | realized raw carrier IC | 0.201434488856 | 0.058325205601 | 0.200517391834 | 0.106018556104 | 0.299537544947 |
| 0.20 | final evaluated IC | 0.130441418767 | 0.029645593161 | 0.129110233513 | 0.087510954976 | 0.186733651365 |
| 0.30 | realized raw carrier IC | 0.303809043034 | 0.05755521222 | 0.303436179995 | 0.210453044349 | 0.3946986016 |
| 0.30 | final evaluated IC | 0.182221558521 | 0.042859752336 | 0.178707851065 | 0.120969663659 | 0.254268175635 |
| 0.35 | realized raw carrier IC | 0.35281815782 | 0.055636098693 | 0.351467487753 | 0.259936429359 | 0.444905466996 |
| 0.35 | final evaluated IC | 0.212800525022 | 0.044267350772 | 0.21118571714 | 0.142252868563 | 0.286311329611 |
| 0.40 | realized raw carrier IC | 0.408354038501 | 0.055175199467 | 0.407563685169 | 0.315470079455 | 0.501511380515 |
| 0.40 | final evaluated IC | 0.250279183231 | 0.047514762659 | 0.246339816232 | 0.170402817717 | 0.327473005722 |

## Closed integrity contract

All deterministic conditions passed: **True** (failures: none).

No integrity check inspects or thresholds recovered IC magnitude, detection probability, monotonicity, Wilson interval position, Stage 1b theta=0 diagnostic, crossing location, any performance statistic. Run validity is governed by this closed deterministic list only; there is no scientific performance gate.

| check | passed |
|---|---|
| registered source dataset hash matches | True |
| source remains unchanged | True |
| complete 6 × 400 matrix | True |
| no missing/duplicate repetition cells | True |
| declared seed formulas reproduced | True |
| no seed collision | True |
| no Stage 1 repetition/seed overlap | True |
| Stage 1b writes only to its isolated namespace | True |
| Stage 1 historical namespace is not overwritten | True |
| no data/trusted*, data/trusted_clean*, or data/provenance* mutation | True |
| required outputs finite | True |
| replay deterministic | True |
| runtime override restored on every exit path | True |
| carrier observed-value multiset preserved within year | True |
| carrier missingness mask preserved | True |
| targets unchanged | True |
| non-carrier features unchanged | True |
| equity reaches the modeled feature path | True |
| identity/invariant checkpoint ICs agree within the already governed Stage 1 numerical tolerance | True |
| ridge prediction IC and final evaluation IC agree within the already governed Stage 1 numerical tolerance | True |

## Replay

Replay probe on the registered cell theta=0.0, repetition 200: identical = True. Ordered-record digest `2fabdb5d2f9875fc`.

One governed prospective run with the frozen seed schedule. A deterministic replay with identical settings is verification, not a new scientific run.

## Limitations

- Stage 1b is apparatus characterization on synthetic input. It establishes no predictive edge, no alpha, no investment value, and no production readiness, and the repository's committed walk-forward finding is unchanged by it.
- The primary result is descriptive. Stage 1b has no scientific performance PASS/FAIL gate: a flat, non-monotone, weak, surprising, or high-background curve is a scientific result, not an integrity failure.
- The realized equity panel is fixed across repetitions. The synthetic injection draw changes and the permutation-test RNG changes, so the reported variation carries injection-draw randomness plus permutation Monte-Carlo randomness conditional on this one realized panel. It excludes uncertainty from drawing another equity universe, market panel, time period, PIT universe, or monthly sample.
- Wilson intervals are pointwise per theta. The permutation seed does not depend on theta or level index, so the permutation RNG stream is shared across theta levels for the same repetition id; the intervals are marginal and are not simultaneous or between-level comparison intervals. No between-theta inference is drawn from them.
- For R=400 the approximate worst-case pointwise Wilson half-width is about 4.9 percentage points near p=0.50 and about 3.9 percentage points near p=0.80. R=400 improves grid-point precision but does not identify an exact between-grid crossing, and no interpolation is confirmatory.
- The divisor 5 in the primary rule is the frozen historical Stage 1 operating divisor, retained as one fixed operating point for comparability. Stage 1b's six theta levels are not a hypothesis family and no family-wise-error-control claim is made across them.
- theta=0 is not a zero-signal market world: the real non-carrier features remain in the pipeline, so the theta=0 rung describes that background rather than zero.
- theta is a synthetic copula design constant. It is not a realistic BIST IC, not a universal IC benchmark, and not a smallest effect size of interest; SESOI remains UNRESOLVED.
- The injection permutes the carrier's own observed values within each year, which destroys that column's joint structure with the other features. Every rung including theta=0 carries the same damage, so the curve is internally consistent, but the absolute recovered IC is not the IC an equally strong naturally-occurring feature would give.
- The temporary run_experiments.TRAINING_MODELING override is process-global and this stage is single-threaded; concurrent execution is outside its scope.
