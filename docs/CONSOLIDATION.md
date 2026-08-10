# FinanceIQ Research Consolidation

## Purpose and reading key

This document is a context-preservation guide for a future technical reader returning to FinanceIQ after an interruption. It explains the research position, the reasoning behind the R4-DIM-01 and R4-ROBUST-01 evidence families, and the boundaries around future work. It is not a replacement for the generated reports, a packet transcript, a governance ledger, or a project timeline.

The labels below distinguish what a reader can treat as repository-durable from what still depends on temporary review context:

- **DURABLE** — preserved in tracked source, canonical reports, registries, or standing project limitations.
- **FRAGMENTED** — recoverable from several durable sources, but easy to misinterpret without this synthesis.
- **AT_RISK** — important context currently preserved mainly by review evidence or by a source-level guard whose consequence is not explained elsewhere.
- **UNSUPPORTED** — a claim or action that the present evidence does not justify.

The exact scientific boundary is:

> **No reliable predictive edge has been established.**

FinanceIQ is research support, not investment advice. The evidence does not establish alpha, profitability, investment value, causal validity, feature-selection benefit, predictive validity, deployment validity, or production readiness.

## Current state in one page

FinanceIQ tested whether free, validated, leakage-safe fundamentals and related features could support T→T+1 BIST equity return prediction in a walk-forward design. The structured numerical pipeline is primary; the optional LLM layer is explanation-only and does not write into the modeling data. The main evaluation uses a retrospectively fixed training universe, three test years, and one unusual macro regime. Those limits are part of the result, not footnotes to be discarded.

The canonical significance report is null-consistent. The six-model ML family has no model that remains statistically distinguishable from the within-year null after the stated Bonferroni correction. Baselines are reported as context, not as validated edges. The small number of test years and the retrospective cohort make the estimates noisy and limit regime or point-in-time claims. The appropriate conclusion is therefore negative but bounded: the study did not detect a reliable predictive edge in this design, and it does not claim that other universes, regimes, or better data are unpredictable.

R4-DIM-01 and R4-ROBUST-01 are **CLOSED / INTEGRATED** on authoritative `main`. Their reviewed implementations and generated artifacts are present in the integrated Git state. Some older task-ledger surfaces may still describe them as outstanding; that is documentation/ledger drift, not uncertainty about their current closure or integration status. Their closure does not establish any stronger scientific claim.

The repository identity at the time of this consolidation is `main` at `bbdd7eeeadf2583661bf39d0175f215564cfa4fe`, equal to `origin/main`, with a clean worktree before drafting. Detailed numbers and artifact ownership remain in the canonical paths listed at the end of this document.

The project deliberately stops here rather than opening another experiment automatically. The negative result is a substantive research outcome. A new analysis would require a separately specified question, frozen methodology, explicit authority, and evidence that it addresses a known limitation rather than searching until a favorable result appears.

## What has actually been established

### Durable empirical observations

The walk-forward program establishes a descriptive result about this persisted dataset, cohort, target, model family, and evaluation design:

- The pooled ML results are weak and null-consistent after multiplicity correction. The most favorable raw ML result does not survive the six-model family-wise correction.
- Simple baselines are competitive with, and in the observed design often as good as or better than, the ML models. This is not evidence for a baseline investment strategy.
- Per-split results are exploratory at this sample size. The three test years, approximately 80 evaluated rows per model and split, and one task-defined macro period do not support claims of stable cross-regime performance.
- The cohort is retrospectively fixed rather than verified point-in-time index membership. Survivorship and universe-selection risks remain unresolved.
- Numerical byte identity is environment-qualified. Same-environment reproducibility evidence is not cross-environment proof.

The canonical sources are [`experiments/results/significance_report.md`](../experiments/results/significance_report.md), [`docs/limitations_register.md`](limitations_register.md), and [`docs/EXAMINER_QUESTION_BANK.md`](EXAMINER_QUESTION_BANK.md). They contain the detailed statistics, estimand description, power limits, and claim boundary. This document does not reproduce their tables.

### Methodological findings

R4-DIM-01 provides a descriptive view of the geometry of a frozen feature construction. It records a 40-feature diagnostic universe, a 35-feature PRIMARY matrix after structural and support rules, common per-year row universes, and effective-rank summaries. It does not turn those summaries into a model-selection result.

R4-ROBUST-01 provides a descriptive tail-handling sensitivity laboratory for five frozen growth features. It evaluates isolated winsorization and trim-to-null surfaces over a frozen quantile grid, using the existing experiment and significance machinery. It preserves the full canonical evaluation universe and reports coverage separately. It does not decide that any cell is corrupted or bad.

### What remains explicitly unestablished

Neither R4 family establishes that a feature is useful or useless for prediction, that dimensionality reduction would improve a model, that tail handling is correct in the world, that the data are uncontaminated, or that unchanged outputs would persist prospectively. Neither establishes causal explanation, economic value, tradability, profitability, generalization to other markets or regimes, point-in-time validity, or deployment validity.

Review approval also has a bounded meaning. The independent reviews checked scope, guards, provenance, serialization, protected boundaries, and claim safety. They are not scientific attestation of predictive value, external validity, or production readiness.

## R4-DIM-01 — how to interpret the dimensionality evidence

The DIM analysis asks a narrower question than “which features should a model use?” It describes the effective geometry of a frozen set of feature-year matrices under explicit eligibility and row-universe rules. The canonical report is [`experiments/results_dimensionality/dimensionality_report.md`](../experiments/results_dimensionality/dimensionality_report.md), with the machine-readable report and companion CSV artifacts in the same directory. The producer is [`experiments/feature_dimensionality.py`](../experiments/feature_dimensionality.py); its outputs are generated artifacts and must not be hand-edited.

### PRIMARY means order-capable

PRIMARY eligibility depends on whether a feature can provide ticker-level ordering within a feature year, not merely whether values are non-missing. Missingness is support information. It is not, by itself, ordering information.

For example, `benchmark_same_year_return_pct` is merged by year and is constant across supported tickers in a feature year. `price_data_available` is emitted as the fixed numeric value `1.0` when supported. Both can be populated, but neither distinguishes one ticker from another within that year. Including either in a within-year feature-geometry matrix would add a column without ticker-level order capability and would misdescribe the object being measured. They are therefore structurally ineligible. This is a statement about the construction, not a claim that the benchmark concept or price-data availability is economically useless or nonpredictive.

### Structural exclusion and support exclusion are different

A feature can be order-capable and still fail the exact support requirement in one or more feature years. Such a feature is support-excluded from the PRIMARY construction. In the frozen result, the three price-momentum features are in that category for the evaluated windows.

Support exclusion means that the chosen analytical construction could not provide the required supported cells across its required years. It does not mean the feature has no information, is redundant, or would fail a predictive experiment. Conversely, structural exclusion means the feature cannot contribute the required within-year ordering under this construction; it is not a ranking of economic importance.

### Why the common `I_y` universe matters

All PRIMARY features use the same sealed per-year `(ticker, year)` universe, written as `I_y`, across the matrix construction. Without that intersection, each feature could be analyzed on a different set of tickers. Differences in missingness or coverage could then appear as differences in correlation or effective dimension. The common `I_y` rule makes the matrices comparable on the same rows for each year and prevents missingness-driven membership from masquerading as feature geometry.

The cost is that the construction is conservative and support-limited. That cost should be read as an explicit limitation, not silently relaxed after inspecting results.

### What `D_eff` and effective rank do—and do not—say

`D_eff` and `erank` summarize the dimensional structure of the selected, support-constrained matrices. They can describe concentration or dispersion in the observed feature geometry. They do not measure predictive usefulness, establish feature-selection benefit, diagnose overfitting, or prove that a lower-dimensional model would perform better.

Likewise, row intersection or exclusion does not provide a proven upper or lower bound on effective dimensionality for a larger feature universe, a different cohort, or a different missingness policy. Under heterogeneous missingness, changing the supported rows can change spectral quantities in either direction. The safe interpretation is local: these are descriptive summaries of the frozen matrices that were actually constructed.

## R4-ROBUST-01 — how to interpret the tail-handling evidence

ROBUST is a tail-handling sensitivity study, not a contamination detector. Its canonical report is [`experiments/results_contamination/contamination_report.md`](../experiments/results_contamination/contamination_report.md), with JSON, cell, metric, prediction, and manifest companions in [`experiments/results_contamination/`](../experiments/results_contamination/). The generator is [`experiments/contamination_lab.py`](../experiments/contamination_lab.py), and ownership is recorded in [`artifact_registry.json`](../artifact_registry.json). The registered route is `make research-contamination`, but its provenance guard currently makes a later-head regeneration fail closed, as described below.

Only the five frozen growth features are stressed. The study uses per-feature, per-window thresholds estimated from permitted training feature years and a frozen `q={0.025,0.05,0.10}` grid. This keeps the intervention narrow and avoids turning a broad data-cleaning exercise into an unbounded alternative pipeline.

Trimming is cellwise rather than row deletion. A trim-to-null surface changes the selected input cell in an isolated copy; it does not remove a ticker, delete a row, change a target, alter identifiers, or shrink the evaluation panel. The complete evaluation universe remains present, including rows without growth-feature support. Coverage is reported separately so results for the growth-supported portion are not misrepresented as results for every evaluated row.

The original-versus-induced-missingness distinction is essential. Original missingness is a property of the canonical input and remains missing. Induced missingness is the deliberate result of the isolated stress operator. Combining them would make it impossible to tell whether a result came from the source data or from the experiment.

There is no arbitrary `ROBUST_PASS`/`ROBUST_FAIL` threshold. The study reports observed cell effects, prediction and IC deltas, inherited significance fields, coverage, and the frozen claim boundary. A discretionary delta threshold would create a new judgment rule after the design was frozen. Unchanged conclusions are sensitivity evidence about this pipeline under these perturbations. They are not proof of predictive robustness, absence of contamination, data correctness, or future performance.

## At-risk context that must not be lost

### Rank normalization can annihilate winsorization

The final independent ROBUST review found a scientifically material but non-blocking behavior: under some `q=0.025` winsorization conditions, including `test_2023` and `test_2024`, genuine stressed-cell changes coexisted with prediction outputs byte-identical to canonical.

The affected cells were real, and the perturbation was applied. It was not necessarily ineffective at the raw-cell level. The canonical pipeline then rank-normalizes each feature within feature-year. If clamping extreme values creates no relevant new ties, it can preserve the ordering of the affected observations. The downstream rank-based model inputs can therefore remain effectively unchanged, and the predictions can remain identical. This is an observed property of the pipeline, not evidence of an implementation bug.

The observation matters for any future robustness design: a raw-magnitude perturbation may be low-information after an order-preserving preprocessing step. It must not be generalized beyond the reviewed surfaces and windows, and it does not authorize regeneration, a methodology change, or a claim that extreme cells are harmless generally. The current generated report remains generator-owned and unchanged.

### ROBUST regeneration intentionally fails closed on later HEADs

`experiments/contamination_lab.py` pins `EXPECTED_HEAD` to `dee3618d0ae75b33d852ba91a2d0a2c6492d3c62`, the previously authorized scientific state. Current `main` is later, at `bbdd7eeeadf2583661bf39d0175f215564cfa4fe`. A future attempt to regenerate the ROBUST family from current `main` is therefore expected to stop with an unexpected-starting-HEAD failure.

That behavior is deliberate provenance protection, not an accidentally broken command. It prevents a later checkout from silently producing artifacts under an older scientific authority. A future regeneration or provenance rebase requires separate explicit authority, a new frozen input/provenance boundary, isolated generation, and independent review. Do not edit `EXPECTED_HEAD` merely to make the command run.

### Historical evidence is not a live constant

The ROBUST-era verification-baseline transition to 1081 was grounded in measured latest-main evidence. The historical R3 handoff’s `356/356` root-suite statement is dated review evidence and was deliberately left unchanged. Replacing it with 1081 would rewrite what was observed at the earlier review date, not correct a current result.

The related root-total discrepancy was reconciled additively: the later total was accounted for by the measured DIM contribution plus the ROBUST contribution. That was a procedural reconciliation, not a scientific or ROBUST defect. The general rule is durable: preserve dated history, keep current assertions current, and use a narrowly bounded historical exclusion or exception if lint scope needs repair.

### Integrated closure and stale ledger surfaces

The DIM and ROBUST implementations and generated artifacts are durable on authoritative `main`, and both workstreams are **CLOSED / INTEGRATED**. An older task-ledger row still lists them as outstanding. That row is stale documentation relative to the authoritative Git state and should not be interpreted as an unresolved owner decision.

For practical reading, R4-DIM-01 and R4-ROBUST-01 are already **CLOSED / INTEGRATED** on authoritative `main`, with owner validation and reviewed integration evidence completed. Any future ledger truth-sync is a separate documentation-maintenance question only. This repository state establishes task closure and artifact integration; it does not strengthen the scientific conclusion or establish predictive validity.

## Open methodological questions

These are unresolved questions, not defects and not invitations to search for a favorable result:

- Can any separately authorized analysis relate descriptive DIM geometry to model behavior without turning `D_eff`, effective rank, correlation, or exclusion into a feature-selection claim? The current evidence does not answer this.
- Is the rank-layer inertness of some `q=0.025` winsorization surfaces sufficiently important to disclose in a regenerated canonical ROBUST report, or is this consolidation-level caveat sufficient? The answer requires owner authority because the report is generator-owned.
- Should the authorized ROBUST scientific state ever be regenerated from a later HEAD? No authority to rebase the pin is currently recorded; until that changes, fail-closed behavior is correct.
- What evidence would be needed for stronger predictive claims? Prospective years, a genuinely point-in-time universe, broader regimes, and a higher-power design could address limitations, but none would guarantee a positive result.
- Are the remaining limitations structural scientific constraints, reproducibility debt, or both? The repository does not justify collapsing them into one category.
- How should any future documentation maintenance reconcile stale task-ledger rows with the already-authoritative **CLOSED / INTEGRATED** state while preserving dated historical evidence? This is a documentation-maintenance question, not a question about whether DIM or ROBUST are closed.

## Candidate future work — all NOT AUTHORIZED

The following are candidates only. None is authorized by R4-CONSOLIDATE-01.

### Scientific and methodological

- **NOT AUTHORIZED — ROBUST disclosure/regeneration.** If the owner authorizes it, add the rank-layer explanation through the supported generator, with a fresh provenance gate and review. Do not hand-edit generated reports.
- **NOT AUTHORIZED — ROBUST provenance rebase.** If authority is granted, update the scientific pin only through a new packet, fresh current-main identity, isolated regeneration, deterministic comparison, and independent review.
- **NOT AUTHORIZED — point-in-time universe evidence.** Source and validate historical membership separately; do not change cohorts, reconstruct membership from memory, scrape, or retrofit current results.
- **NOT AUTHORIZED — prospective-data or power study.** A prospective-year or higher-power design could address current limitations, but it must be preregistered and cannot be framed as a route to a desired positive result.

### Reproducibility and engineering

- **NOT AUTHORIZED — DIM/ROBUST ledger truth-sync.** If separately authorized, reconcile stale task-ledger surfaces with the already-authoritative **CLOSED / INTEGRATED** state while preserving dated historical evidence. This would be documentation maintenance only and must not alter scientific claims or historical records.
- **NOT AUTHORIZED — historical-verification governance.** If desired, repair lint scope through its existing historical-exclusion mechanism or a narrowly pinned exception while leaving the dated `356` document unchanged.

Any future work must preserve nulls as nulls, keep generated artifacts generator-owned, avoid paid APIs and scrapers, and maintain the research-support-only boundary.

## Stop boundary

The current project should not respond to the null result by tuning models, selecting features from DIM, expanding the cohort opportunistically, or changing the methodology after inspecting outcomes. ROBUST should not be relabeled as contamination detection, and unchanged predictions should not be presented as proof of clean data or predictive robustness. Generated DIM/ROBUST reports should not be hand-edited. `EXPECTED_HEAD` should not be changed just to make regeneration run. Dated verification evidence should not be rewritten to match a later baseline.

Raw p-values, negative IC signs, baseline comparisons, effective-rank values, and sensitivity deltas must remain in their stated context. None is alpha, inverse alpha, profitability, investment value, or a tradable recommendation. The current-main closure of R4-DIM-01 and R4-ROBUST-01 is an established task-state fact backed by owner-controlled integration; it does not strengthen the scientific conclusion. External validation, human statistical attestation, point-in-time validity, or production validity should not be claimed without separate authority and evidence.

## Compact source map and restart checklist

Start with [`PRD.md`](../PRD.md), [`REPO_MAP.md`](../REPO_MAP.md), and [`AGENTS.md`](../AGENTS.md) for project boundaries. Then consult:

- Headline walk-forward evidence: [`experiments/results/significance_report.md`](../experiments/results/significance_report.md).
- DIM canonical family: [`experiments/results_dimensionality/dimensionality_report.md`](../experiments/results_dimensionality/dimensionality_report.md), its JSON and CSV companions, and [`experiments/feature_dimensionality.py`](../experiments/feature_dimensionality.py).
- ROBUST canonical family: [`experiments/results_contamination/contamination_report.md`](../experiments/results_contamination/contamination_report.md), its JSON/CSV/manifest companions, and [`experiments/contamination_lab.py`](../experiments/contamination_lab.py).
- Cross-cutting limitations and claim boundary: [`docs/limitations_register.md`](limitations_register.md) and [`docs/EXAMINER_QUESTION_BANK.md`](EXAMINER_QUESTION_BANK.md).
- Artifact ownership: [`artifact_registry.json`](../artifact_registry.json); generator routes: [`Makefile`](../Makefile).
- Dated verification counts: [`docs/VERIFICATION_BASELINE.md`](VERIFICATION_BASELINE.md). Treat its suite counts as dated observations, not permanent constants.

Before any future scientific regeneration, confirm the exact branch, HEAD, clean state, generator-owned inputs, frozen methodology, provenance pin, and explicit authority. Use isolated outputs, preserve canonical artifacts, and obtain the required independent review before integration. If authority, source evidence, or provenance disagrees, stop and fail closed.
