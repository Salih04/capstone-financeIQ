# FinanceIQ Examiner Question Bank and Defense Pack

## Q1 — Research question and scope

**Question:** What research question does FinanceIQ actually investigate?

**Answer:** It investigates whether free, validated year-T fundamentals can support prediction of next-year BIST equity returns as research evidence, within the committed 2020–2025 project scope and selected public/training universes @E01.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. This scope does not establish alpha, profitability, investment value, or a tradable strategy.

**Evidence:** E01, E02

## Q2 — Row, feature, and target meaning

**Question:** What does one modeling row represent, and where is T+1 used?

**Answer:** One row represents one company-year; features belong to year T, while the primary target is the realized return in year T+1. Target, benchmark, inference-state, and same-year analysis fields are not predictive features @E02.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. A target definition is not proof that the target is predictable.

**Evidence:** E02

## Q3 — Data construction and no-fabrication contract

**Question:** How were inputs assembled without inventing missing financial values?

**Answer:** The committed pipeline distinguishes corrected yearly financial inputs, free Yahoo year-end price inputs, benchmark inputs, and manual valuation inputs; missing values remain null and are carried as limitations rather than silently filled @E03 @E16.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Source acceptance does not establish source accuracy, completeness, point-in-time correctness, or investment usefulness.

**Evidence:** E03, E04, E16

## Q4 — Leakage and frozen-snapshot handling

**Question:** What controls prevent target leakage and repeated frozen snapshot fields from entering the feature set?

**Answer:** The validation contract rejects same-year and next-year outcome columns as features, identifies frozen feature columns, records rejected leakage fields, and separates corrected yearly columns from the old repeated snapshot source @E04.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Passing a leakage or frozen-column guard is a data-contract result, not production validation or predictive validation.

**Evidence:** E03, E04

## Q5 — Walk-forward evaluation design

**Question:** How are out-of-sample predictions formed and summarized?

**Answer:** The experiment artifacts describe leakage-controlled walk-forward splits, score later target years after earlier training periods, and summarize within-year Spearman ranking evidence across the persisted test panels @E05 @E06.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. “Out-of-sample” here describes the committed split construction, not external validation or production performance.

**Evidence:** E05, E06

## Q6 — What is and is not joined before scoring?

**Question:** Could realized future outcomes have influenced the serving-style score before evaluation?

**Answer:** The serving evaluation records the unchanged service path, uses isolated repository-root replay, and joins realized test outcomes only after the service has produced scores; missing outcomes are excluded and reported @E06 @E19.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. This evidence supports the stated evaluation seam, not a universal point-in-time guarantee for every upstream source.

**Evidence:** E06, E19

## Q7 — Retrospective-universe limitation

**Question:** Was the evaluated universe verified as point-in-time BIST100 membership?

**Answer:** No. The committed limitation is a retrospectively fixed repository cohort, with unresolved survivorship and universe-selection look-ahead risk rather than verified point-in-time membership @E07.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. No point-in-time validity, universe representativeness, or regime generality may be claimed.

**Evidence:** E07, E10, E19

## Q8 — Primary estimand

**Question:** What does the headline Spearman IC measure?

**Answer:** It is an ordinal within-year cross-sectional ranking statistic; the nominal evaluation pools equal-weighted within-year Spearman ICs, and the significance report keeps realized-return shuffling within each year @E08.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. A ranking correlation is not investment value, economic magnitude accuracy, profitability, or a tradable strategy.

**Evidence:** E08, E13

## Q9 — Multiplicity and headline result

**Question:** Does any model survive the prespecified six-model multiple-testing correction?

**Answer:** No. The report records random_forest as the smallest raw-p result with pooled IC -0.153, raw p 0.0183, Bonferroni-adjusted p 0.1098, and no family-wise significance @E08.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. An isolated raw p-value or favorable split cannot be promoted to alpha, profitability, or external validation.

**Evidence:** E08

## Q10 — Power and detectable IC

**Question:** What does the power analysis tell an examiner, and what does it not tell them?

**Answer:** It is a design-limit calculation: the committed current three-year pooled design uses 80 rows per year and has analytic detectable absolute IC 0.182 at the stated 80% power target; the public-40 three-year value 0.260 is a planning sensitivity, not the current dump design @E09.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Detectable IC and power do not estimate the true IC, prove a model, establish profitability, or measure practical investment value.

**Evidence:** E09

## Q11 — Baselines versus ML

**Question:** How should apparent baseline or ML wins in descriptive tables be interpreted?

**Answer:** Baselines are retained as context, and the experiment summaries show that baselines usually match or beat ML; any isolated best-ML comparison remains an outcome table, not a model-selection license or a reliable finding @E05 @E08.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. No baseline or ML row establishes alpha, an actionable ranking, or a profitable strategy.

**Evidence:** E05, E08

## Q12 — Stability and robustness

**Question:** What does the ranking-stability analysis add?

**Answer:** It measures resampling variability of frozen ranks, top-k membership, leave-one-out IC movement, leave-eight-out dispersion, and public-40 cohort sensitivity without retraining or producing a new p-value @E10.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Stability of a null-consistent ranking is not predictive robustness, reliability, pick confidence, or out-of-sample skill.

**Evidence:** E10

## Q13 — Missingness sensitivity

**Question:** What does the missingness experiment prove when inputs are masked?

**Answer:** It is an exhaustive deterministic sensitivity audit of one fixed serving recipe: 656 masking scenarios use the service's null path, preserve missingness, and measure rank/confidence response rather than predictive skill @E11.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. A small rank delta is not validation, stability, reliability, robustness, profitability, or deployment validity.

**Evidence:** E11

## Q14 — Alternative return bases and excess returns

**Question:** Do CPI-deflated, USD-basis, or benchmark-relative analyses rescue the result?

**Answer:** No committed alternative-basis table has a family-wise significant selected ML model; the excess-return report keeps its within-year ordinal estimand and labels excess, real-TRY, and USD analyses exploratory robustness evidence @E12 @E13.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Alternative bases do not establish investor-specific value, implementability, a benchmark-hedged trade, or cross-basis confirmation.

**Evidence:** E12, E13

## Q15 — Regime coverage

**Question:** Can the project claim that its finding holds across macroeconomic regimes?

**Answer:** No. The regime artifact reports one observed regime, leaves regime-conditional model statistics uncomputed, and keeps macro series as effective-dated descriptive context @E14.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. No regime robustness, causal effect, market-efficiency conclusion, or production validity is established.

**Evidence:** E14

## Q16 — Negative-control laboratory

**Question:** What does the placebo laboratory demonstrate about the evaluation machinery?

**Answer:** It tests the significance rig on feature panels replaced with seeded independent noise; 25 of 25 repetitions completed and family-wise rejections were 0, so it is a low-resolution machinery check, not a BIST market study @E15.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. The placebo result does not certify exact Type-I calibration, support market skill, or validate a deployed system.

**Evidence:** E15

## Q17 — Per-cell provenance

**Question:** What can the provenance passport establish about the public modeling dataset?

**Answer:** It records lineage for 14,640 public-dataset cells, with 13,682 present and 958 null; 8,243 are cell-verified, 3,715 column-asserted, 2,640 derived-chain, and 42 unknown, with unknown and null records preserved rather than repaired @E16.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Lineage does not certify point-in-time correctness, source accuracy, data rights, completeness, statistical significance, causal validity, or investment usefulness.

**Evidence:** E16

## Q18 — Model disagreement and influential observations

**Question:** Are agreement patterns or influential observations evidence of winning stocks?

**Answer:** No. The disagreement atlas compares within-year ranks without comparing raw model magnitudes, while influence diagnostics remove one persisted observation at a time; both are descriptive sensitivity diagnostics with explicit null/status handling @E17 @E18.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Rank agreement, rank spread, or a large influence value is not a pick, opportunity, causal effect, profitable strategy, or predictive validation.

**Evidence:** E17, E18

## Q19 — Serving versus research

**Question:** Does the user-facing serving heuristic have a stronger validation status than the research models?

**Answer:** No. The serving report invokes the unchanged train_parameters and run_forecast path and records pooled IC 0.050, bootstrap 95% CI [-0.075, 0.174], and raw permutation p 0.4427 for one prespecified test outside the six-model family @E19.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. Serving-path replay is not production validation, deployment validation, or investment-value evidence.

**Evidence:** E19

## Q20 — Pre-registered future evaluation

**Question:** What is already known about the 2026 forward evaluation, and what remains absent?

**Answer:** The protocol freezes the 2026 ranking and interpretation before outcomes, preserves nulls without imputation, and refuses to compute the primary test below the 30-row usable floor; the future outcome file remains absent until real outcomes are sourced @E20.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. A frozen protocol is process control, not a result, external validation, point-in-time proof, or production evidence.

**Evidence:** E20

## Q21 — Grounded research assistant

**Question:** What does the research assistant do, and what role does the optional LLM play?

**Answer:** The assistant answers through the research endpoint using structured validated context, preserves grounded factual answers, and falls back deterministically when no provider is configured; an optional LLM is explanation-only and does not become the numerical model or write the modeling dataset @E21.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. A grounded answer, UI display, mock fallback, or LLM explanation is not human acceptance, external validation, or production validity.

**Evidence:** E21

## Q22 — What the project does not establish

**Question:** What is the safest final defense answer when an examiner asks whether FinanceIQ found an investable edge?

**Answer:** The defensible answer is that FinanceIQ is a transparent research-support system whose committed evidence reports a weak, null-consistent result and documents the limits needed to prevent overclaiming; the project reports what it measured and what remains unknown @E01 @E08 @E22.

**Boundary:** No reliable predictive edge has been established. Research support only; not investment advice. No alpha, profitability, investment value, tradable-strategy validity, external validation, production/deployment validation, point-in-time validity, or external professional statistical attestation has been established or claimed.

**Evidence:** E01, E07, E08, E14, E16, E19, E22

## 9. Frozen E01–E22 evidence catalog

Catalog facts are bounded summaries of the cited committed source sections. The
implementation must not add a numeric fact to Facts without a citation that
directly supports it. It must not cite a governance summary when a primary
artifact below supports the same scientific fact.

## E01 — Research question and project scope

**Purpose:** Establish the question, research-support framing, selected BIST scope, and non-goals.

**Facts:** FinanceIQ is defined as a T-to-T+1 BIST equity-research system using free validated inputs and walk-forward experiments; its core question asks whether fundamentals can predict next-year returns, while investment advice and predictive-edge claims are non-goals.

**Citations:** PRD.md::heading=Core Problem; PRD.md::heading=Non-Goals

**Limit:** PRD scope does not prove data correctness, statistical significance, external validation, or live deployment.

## E02 — Modeling row and target dictionary

**Purpose:** Define row identity, feature-year, target-year, and target/exclusion roles.

**Facts:** The data dictionary states that each row is one company-year, features belong to T, the primary target is realized return in T+1, and target/same-year outcome fields are not predictive features.

**Citations:** data/trusted_clean/data_dictionary.md::heading=Data dictionary — modeling_dataset_2020_2025.csv

**Limit:** A schema role is not evidence that future outcomes are predictable.

## E03 — Dataset quality and source distinction

**Purpose:** Establish committed dataset shape, target coverage, benchmark availability, corrected-yearly distinction, rejected snapshot fields, and null-preserving quality status.

**Facts:** The committed quality report records 403 rows, 40 features, 321 rows with target, 82 inference-only rows, benchmark availability, corrected-yearly acceptance, frozen reference exclusions, leakage exclusions, and no listed issues.

**Citations:** data/trusted_clean/data_quality_report.md::heading=Data quality report

**Limit:** The report is a repository validation artifact; it does not certify external source accuracy or point-in-time membership.

## E04 — Leakage and frozen-feature validator

**Purpose:** Establish the producer-side controls that reject target leakage, duplicates, and frozen feature columns.

**Facts:** The validator requires key columns, checks duplicate ticker-year rows, rejects same-year and next-year outcomes from the feature set, reports frozen feature columns, records missingness and target coverage, and writes a valid-for-T-to-T+1 status.

**Citations:** scripts/data_collection/validate.py::symbol=validate; data/trusted_clean/data_quality_report.md::heading=Data quality report

**Limit:** A passing validator covers the implemented contract only; it does not establish predictive performance or production validity.

## E05 — Walk-forward experiment and baseline context

**Purpose:** Establish the persisted walk-forward design, noisy small-data caveat, baseline context, and target families.

**Facts:** The experiment summaries call the evaluation walk-forward and leakage-controlled, warn that the small yearly cohort is noisy and overfitting-prone, report that baselines usually match or beat ML, and list the evaluated target families.

**Citations:** experiments/reports/summary.md::heading=Experiment summary (next-year return prediction); experiments/results/experiment_summary.md::heading=Experiment summary (benchmark-aware, walk-forward)

**Limit:** Summary tables are descriptive persisted outputs; a best row does not license retrospective model selection.

## E06 — Evaluation seam and within-year treatment

**Purpose:** Establish that scores are produced before realized outcomes are joined and that within-year ranking/resampling is preserved.

**Facts:** The serving evaluation records the unchanged service path, isolated repository-root replay, earlier training feature/target years, later test years, and outcome joining after scoring; the primary significance treatment shuffles outcomes within each year.

**Citations:** experiments/results_serving_eval/serving_eval_report.md::heading=Real service path invoked; experiments/results_serving_eval/serving_eval_report.md::heading=Walk-forward design and cohort; experiments/results/significance_report.md::heading=Pooled, multiplicity-corrected result

**Limit:** The evidence supports the documented harness seam, not universal point-in-time correctness of every upstream source.

## E07 — Retrospective cohort limitation

**Purpose:** Preserve the unresolved retrospective-universe, survivorship, and point-in-time boundary.

**Facts:** The significance limitations state that the cohort is retrospectively fixed rather than verified point-in-time BIST100 membership; the serving and rank-stability reports retain survivorship and universe-selection limitations.

**Citations:** experiments/results/significance_report.md::heading=Required limitations; experiments/results_rank_stability/rank_stability_report.md::heading=Limitations

**Limit:** No point-in-time universe claim may be made from this evidence.

## E08 — Headline significance and multiplicity

**Purpose:** Establish the primary nominal result, six-model Bonferroni treatment, confidence interval context, and null-consistent conclusion.

**Facts:** The significance report records random_forest as the smallest pooled raw-p result with pooled IC -0.153, raw permutation p 0.0183, adjusted p 0.1098, bootstrap interval [-0.273, -0.028], and no ML model surviving family-wise correction.

**Citations:** experiments/results/significance_report.md::heading=Pooled, multiplicity-corrected result; experiments/results/significance_report.md::heading=Pooled model results

**Limit:** The report does not establish a reliable predictive edge, practical investment relevance, or a universal market-efficiency result.

## E09 — Power and minimum detectable IC

**Purpose:** Distinguish observed IC, detectable IC, power, planning sensitivity, and practical relevance.

**Facts:** The committed report separates those concepts, uses a Fisher-z design calculation and seeded rank simulation, records the current three-year pooled design and public-40 planning sensitivity, and says power does not estimate the true IC or practical investment relevance.

**Citations:** experiments/results/significance_report.md::heading=Statistical power and minimum detectable IC; experiments/results/significance_report.md::heading=Forty-ticker-per-year planning projection

**Limit:** Detectable IC is a design limit under assumptions, not a significance threshold, result, or investment-value measure.

## E10 — Ranking and cohort stability

**Purpose:** Establish what stability diagnostics measure and their non-predictive boundary.

**Facts:** The rank-stability artifact measures within-year resampling rank variability, top-k membership, leave-one-out and leave-eight-out pooled-IC dispersion, and public-40 cohort sensitivity without retraining, raw cross-model score comparison, or new p-values.

**Citations:** experiments/results_rank_stability/rank_stability_report.md::heading=Scope and estimands; experiments/results_rank_stability/rank_stability_report.md::heading=Interpretation boundaries

**Limit:** A stable ranking can remain null-consistent; stability is not pick confidence or predictive validity.

## E11 — Serving-heuristic missingness sensitivity

**Purpose:** Establish the fixed-recipe missingness audit, exhaustive scenario count, null semantics, and limited interpretation.

**Facts:** The artifact reports 656 deterministic scenarios, masks selected inputs through the service null path, preserves nulls without fabrication or imputation, and measures rank/confidence response only.

**Citations:** experiments/results_missingness/missingness_report.md::heading=Baseline replay audit; experiments/results_missingness/missingness_report.md::heading=Scenario families (exhaustive, deterministic — no sampling); experiments/results_missingness/missingness_report.md::heading=Limitations and claim boundary

**Limit:** The audit does not measure predictive skill, robustness, reliability, deployment validity, or generalization across universes and regimes.

## E12 — Alternative real-TRY and USD bases

**Purpose:** Establish parallel alternative-basis evidence and its exploratory status.

**Facts:** The comparison report records selected-model pooled IC values of -0.156 on CPI-deflated real TRY and -0.150 on USD basis, with no Bonferroni family-wise significance on either basis, and states that no reliable predictive edge is established.

**Citations:** experiments/results_real_terms/comparison_report.md::heading=Alternative-basis comparison (R2-REAL-01)

**Limit:** These are descriptive historical bases, not investor-specific inflation, currency, implementability, or investment-value analyses.

## E13 — Excess-return estimand and cross-basis multiplicity

**Purpose:** Establish the benchmark-relative target interpretation, within-year ordinal estimand, exploratory cross-basis policy, and non-trading boundary.

**Facts:** The excess report says no six-model member survives correction, defines within-year ordinal ranking, identifies nominal return as the sole confirmatory family, labels excess/real/USD bases exploratory, and rejects benchmark-hedged or investment-value interpretation.

**Citations:** experiments/results_excess/significance_report.md::heading=Family-level conclusion; experiments/results_excess/significance_report.md::heading=Estimand: within-year ordinal ranking; experiments/results_excess/significance_report.md::heading=Cross-basis multiplicity

**Limit:** Equal within-year ranks across a shifted target do not establish magnitude accuracy, alpha, or an implementable hedge.

## E14 — Regime lens

**Purpose:** Establish one-regime coverage, absent regime-conditional statistics, and descriptive macro context.

**Facts:** The regime artifact reports status not_computed_insufficient_regime_diversity, one observed regime against a required threshold, no per-regime model statistics, and null-preserving effective-dated macro context.

**Citations:** experiments/results_regime/regime_context_report.md::heading=Diagnostic status; experiments/results_regime/regime_context_report.md::heading=Findings; experiments/results_regime/regime_context_report.md::heading=Limitations

**Limit:** No regime robustness, causal effect, or regime-specific predictive edge is estimable here.

## E15 — Negative-control placebo laboratory

**Purpose:** Establish the machinery-only null test and its low-resolution limitation.

**Facts:** The placebo artifact replaces features with seeded independent noise, runs the same six-model family and gate, completes 25 of 25 repetitions, and records 0 family-wise rejections.

**Citations:** experiments/results_placebo/placebo_report.md::heading=Question and estimand; experiments/results_placebo/placebo_report.md::heading=Result; experiments/results_placebo/placebo_report.md::heading=Limitations

**Limit:** The placebo is not a market study and 0/25 does not certify exact family-wise calibration.

## E16 — Per-cell provenance passport

**Purpose:** Establish lineage coverage, source classes, transformations, null preservation, and unknown handling for the public dataset.

**Facts:** The passport covers 14,640 cells, with 13,682 present and 958 null; evidence levels are 8,243 cell_verified, 3,715 column_asserted, 2,640 derived_chain, and 42 unknown; unknown and null cells are reported, not repaired.

**Citations:** data/provenance/cell_provenance_report.md::heading=Per-cell provenance — public modeling dataset (passports v2); data/provenance/cell_provenance_report.md::heading=Evidence level; data/provenance/cell_provenance_report.md::heading=Transformation; data/provenance/cell_provenance_report.md::heading=Unknown provenance; data/provenance/cell_provenance_report.md::heading=Caveats

**Limit:** Lineage evidence does not certify upstream correctness, rights clearance, point-in-time correctness, predictive validity, causal validity, or investment usefulness.

## E17 — Model disagreement atlas

**Purpose:** Establish rank-only disagreement diagnostics and their non-opportunity interpretation.

**Facts:** The atlas compares within-year, within-model ranks, reports pairwise rank agreement and ticker-year spread/IQR, does not compare raw prediction magnitudes, and adds no significance test.

**Citations:** experiments/results_disagreement/disagreement_report.md::heading=Scope and estimand; experiments/results_disagreement/disagreement_report.md::heading=Interpretation boundaries; experiments/results_disagreement/disagreement_report.md::heading=Limitations

**Limit:** Agreement or disagreement is descriptive instability evidence, not predictive validity, economic value, or a stock opportunity.

## E18 — Leave-one-out influence diagnostics

**Purpose:** Establish the observation-sensitivity diagnostic and its non-causal boundary.

**Facts:** The influence report removes each persisted ticker-year observation without retraining, recomputes the existing pooled-IC quantity, reports both directions of change, and keeps insufficient-data states explicit.

**Citations:** experiments/results_influence/influence_report.md::heading=Scope and estimand; experiments/results_influence/influence_report.md::heading=Per-model influence summary; experiments/results_influence/influence_report.md::heading=Interpretation boundaries

**Limit:** Influence is retrospective sensitivity of an estimator, not a causal, forward-looking, out-of-sample, or ticker-opportunity statement.

## E19 — User-facing serving heuristic evaluation

**Purpose:** Establish serving-versus-research distinction and the serving result without upgrading it.

**Facts:** The serving report invokes the unchanged service path, records pooled IC 0.050, bootstrap 95% CI [-0.075, 0.174], raw p 0.4427, 10,000 permutations, 10,000 bootstraps, and a single prespecified test outside the six-model family.

**Citations:** experiments/results_serving_eval/serving_eval_report.md::heading=Real service path invoked; experiments/results_serving_eval/serving_eval_report.md::heading=Serving result; experiments/results_serving_eval/serving_eval_report.md::heading=Limitations and claim boundary

**Limit:** This is isolated service-path evaluation, not production/deployment validation, investment value, or reliable predictive evidence.

## E20 — Pre-registered 2026 forward protocol

**Purpose:** Establish freeze-before-outcome discipline, null-preserving future evaluation, and absent-outcome state.

**Facts:** The protocol freezes the ranking and interpretation before outcomes, retains missing outcomes as null, defines one primary test, refuses testing below 30 usable rows, and states that the future outcome file is absent until sourced.

**Citations:** docs/PREREGISTERED_2026_EVALUATION.md::heading=Frozen artifact and checksum; docs/PREREGISTERED_2026_EVALUATION.md::heading=Null-preserving behavior; docs/PREREGISTERED_2026_EVALUATION.md::heading=The single pre-registered statistical test; docs/PREREGISTERED_2026_EVALUATION.md::heading=Interpretation grid (pre-written for every result)

**Limit:** A pre-registration is process evidence and cannot be presented as a future result or validation.

## E21 — Grounded research assistant contract

**Purpose:** Establish the research-agent endpoint, structured grounding, deterministic fallback, optional LLM role, and non-advice boundary.

**Facts:** The guide requires validated evidence and structured context, preserves grounded factual answers, uses deterministic fallback when no provider is configured, and says the optional LLM is not a numerical model; the API exposes POST /research/ask and the route delegates to the research-agent service.

**Citations:** docs/research_agent_guide.md::heading=Agent Behavior; docs/research_agent_guide.md::heading=Grounding Rules; backend/app/routers/research_agent.py::symbol=ask; backend/app/services/research_agent.py::symbol=_grounded_success_response; backend/app/services/research_agent.py::symbol=answer_research_question

**Limit:** Endpoint presence and grounded response structure do not establish human acceptance, external validation, or production validity.

## E22 — Claim governance and reproducibility boundary

**Purpose:** Consolidate the non-claim, environment, artifact-ownership, and review-scope limits needed for a safe defense.

**Facts:** The committed scientific artifacts repeatedly retain research-support-only wording, environment-qualified reproduction, retrospective-cohort limits, generator ownership, and the unchanged conclusion that no reliable predictive edge is established.

**Citations:** experiments/results/significance_report.md::heading=Required limitations; data/provenance/cell_provenance_report.md::heading=Caveats; docs/limitations_register.md::heading=Automated limitations register

**Limit:** This catalog entry summarizes claim boundaries; it is not a new approval, statistical attestation, or deployment verification.
