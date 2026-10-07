# Study Record Template

Research support only; not investment advice.

Use one copy per study. Complete and freeze **BEFORE** before inspecting outcomes; complete **AFTER** when analyses are finished.

## BEFORE — registration

- **Study ID / version / date:** [ID] / [version] / [date and time]
- **Research question:** [one precise question]
- **Estimand:** [target population, outcome, horizon, and summary or contrast]
- **Universe rule version:** [rule name, version, and effective date; never use the frozen capstone cohort as a new research universe]
- **Data snapshots and cutoffs:** [source, immutable snapshot ID/hash, observation period, and latest permitted public/availability time for each source]
- **Boundaries:** Development [dates; default through 2022-12-31] · Locked holdout [dates; default 2023-01-01–2025-12-31] · Forward holdout [everything published after OSF registration]. State any boundary change made before evaluation and why.
- **Analysis plan:** [targets, features, models/estimators, fitting and validation scheme, metrics, exclusions, and declared missing-input handling]
- **Multiplicity plan:** [hypothesis family and correction method]. Set **N** from the experiment ledger to all configurations tried that could answer this question, including exploratory, post-hoc, null, and abandoned trials. State the cutoff, treatment of related families, and how the correction uses N.
- **Stopping rule:** [fixed date, sample/trial limit, or other rule; state what can end the study]
- **Null result:** [pre-set estimate/uncertainty or practical-effect criterion that will count as null; do not equate “not significant” with proof of no effect]
- **Evidence that would change the conclusion:** [specific result, replication, or new evidence and the direction required]

## AFTER — results and record

- **Registered analyses:** [analyses completed as specified; identify the registration/version]
- **Post-hoc analyses:** [each additional analysis, labelled post-hoc, with its rationale]
- **Results:** [estimates, uncertainty, metrics, multiplicity-adjusted findings, and null-result assessment]
- **Deviations from registration:** [what changed, when, why, and whether outcomes were already inspected; write “none” if none]
- **Limitations:** [data, measurement, design, inference, and generalisation limits]
- **Experiment-ledger trial count:** [study-wide total] configurations tried; **N = [count]** relevant configurations through [cutoff]. Give the ledger reference, multiplicity family, and correction applied; reconcile N with the BEFORE plan.
