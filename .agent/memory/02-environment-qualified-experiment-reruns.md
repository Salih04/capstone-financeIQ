**Byte-identical experiment reruns confirmed in one environment do not establish cross-environment reproducibility.**

DATA-05 refreshed the committed experiment artifacts after two byte-identical
`make research` runs in the current environment. Keep that result qualified:
it establishes repeatability for that environment only. Do not describe the
outputs as cross-environment reproducible until a run records the dataset hash,
git revision, dependency versions, and output hashes, then verifies a rerun.

Evidence: DATA-05's 2026-07-12 execution result and commit
`fe185e06` (`Refresh environment-qualified experiment outputs`).
`FINANCEIQ_AGENT_TASK_QUEUE.md` R2-REPRO-01 documents the still-missing
manifest and one-command reproduction check; it is the owner of that broader
claim.
