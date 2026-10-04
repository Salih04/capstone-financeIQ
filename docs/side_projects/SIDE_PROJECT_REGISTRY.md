# FinanceIQ Side Project Registry

## FinanceIQ PIT Kernel

**P3 PIT/Data Infrastructure → DEFER TO FINANCEIQ PIT KERNEL**

Status: PLANNED / SEPARATE_SIDE_PROJECT

Main FinanceIQ must not independently rebuild PIT/data-infrastructure capabilities owned by the FinanceIQ PIT Kernel.

Kernel-owned capabilities include:

- publication / known_at timelines
- statement vintages and restatements
- bitemporal facts and as_of semantics
- historical shares outstanding
- corporate-action reconstruction
- raw vs adjusted price lineage
- security master / listing history
- historical rule-based universe
- no-lookahead / PIT contamination proofs

If a FinanceIQ roadmap item needs one of these capabilities, mark it:

`DEPENDENCY: FINANCEIQ_PIT_KERNEL`

Do not create a second implementation in the main FinanceIQ application.

Building the PIT Kernel does not authorize outcome inspection, PIT-v2 scientific execution, or changes to the frozen V1 result.
