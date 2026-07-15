# R3-SERV-01 independent Fable 5 review handoff

Status: **PENDING — not yet independently reviewed and not merge-ready.**

This handoff is for a separate Fable 5 review context/model family. It records
what must be checked before the owner considers a manual commit. It is not a
self-review, approval, or evidence that the implementation is merge-ready.

## Scope and fixed conclusion

R3-SERV-01 measures the real user-facing serving heuristic under the canonical
walk-forward and significance discipline. It does not change service behavior,
training behavior, ranking behavior, canonical artifacts, trusted data, the
frontend, backend runtime, or the Model Confidence Contract.

The generated conclusion is pre-committed and must remain exactly:

> The user-facing serving heuristic's walk-forward IC is 0.050 (95% CI [-0.075,0.174], permutation p=0.4427); this is not distinguishable from the within-year null, and in either case does not establish investment value, implementability, or a reliable predictive edge.

## Evidence to inspect

- Implementation: `experiments/serving_eval.py`
- Focused pin/guard tests: `tests/test_serving_eval.py`
- Authoritative read-only service: `backend/app/services/forecasting_csv_service.py`
- Generated report: `experiments/results_serving_eval/serving_eval_report.json`
- Human-readable report: `experiments/results_serving_eval/serving_eval_report.md`
- Prediction dumps: `experiments/results_serving_eval/predictions_serving_2023.csv`, `experiments/results_serving_eval/predictions_serving_2024.csv`, and `experiments/results_serving_eval/predictions_serving_2025.csv`
- Methodology subsection: `METHODOLOGY.md` under “Serving-heuristic walk-forward evaluation (R3-SERV-01)”
- Artifact ownership: `artifact_registry.json`
- Generator target: `Makefile` target `research-serving-eval`

## Mandatory review questions

1. **Exact service-path parity.** Confirm the harness invokes
   `forecasting_csv_service.train_parameters()` and
   `forecasting_csv_service.run_forecast()` from the authoritative service file.
   Confirm there is no copied, approximated, forked, or manually reproduced
   scoring formula. Inspect the fixture pin test: it calls the service directly,
   calls the harness, asserts both production functions were invoked, and
   compares outputs row by row at the service's serialization precision.
2. **Walk-forward leakage boundaries.** Confirm the three split definitions are
   exactly training feature years 2020–2021 → feature year 2022 / target 2023;
   2020–2022 → 2023 / 2024; and 2020–2023 → 2024 / 2025. Confirm the isolated
   training CSV contains no test-feature-year row and the isolated scoring CSV
   has all realized test outcomes blanked before the service is called.
3. **Training-year restriction.** Confirm each `train_parameters()` call is
   bounded to the split's prior feature years and that the reported training
   row counts (81, 161, 241) come from the service response.
4. **Evaluated cohort parity.** Confirm each serving dump has the same exact 80
   ticker/outcome rows as the corresponding canonical nine-model dump. Confirm
   the raw feature-year panels contain 81/81/80 rows and that only missing-outcome
   RGYAS rows are excluded in 2023 and 2024.
5. **Missing-data handling.** Confirm missing features remain null and are
   handled only by the unchanged service omission/confidence behavior. Confirm
   missing outcomes are excluded before within-year service percentiles are
   computed, never imputed, and recorded in the report.
6. **Statistical parity.** Confirm the harness imports the existing
   `experiments.significance.analyze_model` path for within-year Spearman IC,
   10,000 seeded within-year permutations, and 10,000 seeded within-year
   bootstraps. Confirm undefined/constant-output cases return explicit
   `insufficient_data` rather than a numeric p-value.
7. **Single-test family framing.** Confirm the serving p=0.4427 is labeled
   “single prespecified test, outside the six-model Bonferroni family,” is raw,
   has no serving adjusted-p field, and is not added as a seventh family member.
   Confirm all six canonical ML models are shown separately with their raw and
   adjusted values, so the serving result is not compared selectively with one
   convenient model.
8. **Pre-committed wording.** Confirm the exact sentence above appears in both
   generated reports and METHODOLOGY. A distinguishable result fixture must
   still end with the same no-investment-value/no-reliable-edge boundary.
9. **Misquotation risk.** Read the whole Markdown report as a hostile editor.
   Flag any sentence that could be excerpted as investment value, product
   validation, contrarian alpha, a recommendation, or validated predictive
   skill. The small retrospective cohort, survivorship/universe-selection risk,
   missingness, nominal-TRY/single-regime, low-power, and environment-qualified
   limitations must remain visible.
10. **Artifact determinism and protection.** Confirm two consecutive generator
    runs are byte-identical, every new generated file has exactly one registry
    owner, and the protected service/canonical/trusted checksum comparison is
    unchanged.

## Deterministic generated checksums

| Artifact | SHA-256 |
| --- | --- |
| `experiments/results_serving_eval/predictions_serving_2023.csv` | `f6dc2ae951e3e9b4a1ecc7690d36c47f574e859de19dbad7302e76d855de22d2` |
| `experiments/results_serving_eval/predictions_serving_2024.csv` | `023e2f15559817d2afe3a91d282ce417c7a300f9cb6b4e90a136d0e1cab049d0` |
| `experiments/results_serving_eval/predictions_serving_2025.csv` | `7459e0e19c0fa2e5970542c5b5eb391c1488899401e043c22bc6ac203e64dd93` |
| `experiments/results_serving_eval/serving_eval_report.json` | `b2644e754f19a96d61b7f4bcaecbc9b8108b4d5dbdf43f6cc83e015a0f001937` |
| `experiments/results_serving_eval/serving_eval_report.md` | `925e67e783c444651eabf2607ac0e7b206146237a0e7bcad0d50a62016ac6d88` |

## Protected checksum anchors

| Protected file | SHA-256 |
| --- | --- |
| `backend/app/services/forecasting_csv_service.py` | `7438ab40a47b5a1122ec8079d977bde7b7482a31f90dee0de79fd0f5f0212cb1` |
| `experiments/leaderboard.csv` | `8b3dfce2ca9ee702411c76cfcf699723cfde076df073837b4ca9db74e5936822` |
| `experiments/results/significance_report.json` | `0358ed01b70b99d491f3babb4810604c09e64ef4726f12ee0b7ea0a8af12fc29` |
| `experiments/results/predictions_test_2023.csv` | `c954822ec52c4bdc7704cc0c7d9ac26c58817b2a75ec92c842915603eb5b72c8` |
| `experiments/results/predictions_test_2024.csv` | `cf88016a3f310811baaf3fed677230ffd98db4db0ea1417393c9afe87bb4c457` |
| `experiments/results/predictions_test_2025.csv` | `295dac3a1b056aa20b9320ff0844ec3cd6aca61fd602f195258a4bc7182cafb1` |
| `data/trusted_clean/modeling_dataset_training_2020_2025.csv` | `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78` |
| `experiments/results/runs/20260712T222717.997241Z_97e4fc33/manifest.json` | `fbeb253dfdc29a64f34b9a9724531fcd149c094bd79cd818a56f9568b317165f` |

The implementation verification compares 291 protected files in total,
including every tracked file under `data/trusted/` and `data/trusted_clean/`.

## Reviewer disposition to return

Return one of:

- `APPROVE FOR OWNER CONSIDERATION` with evidence for every question above; or
- `MANDATORY FIXES` with file/line-specific findings and the exact violated
  packet requirement.

Do not commit, push, modify the backend service, change the MCC, or start another
task during this review.
