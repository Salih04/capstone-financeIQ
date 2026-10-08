# Panel v2 PIT preregistration — status

Research support only; not investment advice.

| Field | Value |
| --- | --- |
| Status | **SUPERSEDED** as of 2026-10-07 |
| Superseding authority | [`docs/process/RESEARCH_CHARTER.md`](process/RESEARCH_CHARTER.md) (§4 universe U1, §7, §8 decision K8) |
| Protocol | `FI-PANEL-V2-PIT-v1`, version `panel_v2_pit` |
| Historical branch | `local/panel-v2-pit-prereg-6084b45f` (local and `origin`, same tip) |
| Historical commit inspected | `e3d7012ba315bcce62ec2df0ae3337c4da609f50` ("docs: preregister Panel v2 PIT", 2026-09-06 02:26:30 +0300; parent `6084b45fa8a0242abc7ff8d10cfbdcf872d85c08`) |
| Merged into `main` | No. The commit is not an ancestor of `main`; this record is the only Panel v2 file on `main` |
| Recorded 2026-10-08 by | task FIQ-03 (`docs/process/TASKS_FINANCEIQ_2026-10-07.md`) |

## 1. What SUPERSEDED means here

SUPERSEDED means only that the project will not implement or run this
protocol, because the research charter replaced its question, universe and
design. It does **not** mean that the preregistration was:

- deleted — the branch and commit stay on `origin` unchanged;
- falsified or found invalid — no data was collected and no result exists
  that could confirm or refute anything;
- executed — see §3;
- retroactively amended — nothing on the historical branch was edited, and
  this file does not reinterpret what it registered.

The preregistration remains immutable evidence of what was planned on
2026-09-05/06. Anyone citing it cites commit `e3d7012b`, not this file.

## 2. Why it is superseded

Panel v2 was an **annual** point-in-time panel built on the former capstone
design:

- one row per security × calendar `feature_year`, with a calendar-year-end
  `Europe/Istanbul` cutoff (D1);
- one confirmatory target, the annual year-end return
  `TC-A = 100 * (P_adj(T+1) / P_adj(T) - 1)` (D2);
- re-derivation of the 2020–2025 capstone rows (D7);
- a 40-feature vector frozen from the capstone's `_feature_cols` filter in
  `experiments/run_experiments.py` over the header of
  `data/trusted_clean/modeling_dataset_training_2020_2025.csv`, via
  `docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md` §9;
- a "legacy 17" quarantine list derived from the capstone's
  `data/provenance/cell_provenance_public_2020_2025.csv`.

The charter (adopted 2026-10-07) replaces this with the rule-based
**quarterly U1 universe**: formation dates at BIST index-period starts,
BIST 100 constituents from effective-dated membership evidence,
survivor-inclusive and fail-closed (charter §4), with targets, features and
models declared per study record (charter §3, §5). Charter §8 records
decision K8 of `docs/process/GAP_CLOSURE_PLAN_2026-10-07.md` ("Panel v2
parked") as "superseded by U1". Charter §7 keeps existing pre-registrations
as dated records, which this file follows.

## 3. Execution status

There is no repository evidence that Panel v2 was executed. The record
itself froze `FULL_PANEL_FEASIBLE = CONDITIONAL`, `COLLECTION_READY = NO`
and `IMPLEMENTATION_READY = NO`, and stated that it collected no data, built
no panel and ran no experiment. On `main` its two reserved roots were never
created: `data/panel_v2_pit/` and `data/trusted_raw_pit_v2/` are absent. Its
`scripts/panel_v2` package is absent on `main` as well. No builder, validator or acquisition adapter was ever written. For
this closure no data was acquired, no outcome inspected and no model or
metric run.

## 4. Commitment check before closing

FIQ-03 required a check for any dated or binding commitment that a
unilateral closure would break. The full registration document, both
schemas and the applicability CSV were read at `e3d7012b`. None was found:

- no OSF or other external, timestamped registration is referenced;
- no deadline or dated obligation appears;
- `OWNER_DECISIONS_REQUIRED = NONE`; the owner locks D1–D7 were the owner's
  own decisions, and the same owner adopted the superseding charter;
- every forward obligation (§9 future no-peek enforcement, §12 "before first
  collection", §13 controls, B1–B8 runtime fixes) is conditional on an
  implementation or collection step that never started, so closing the
  protocol leaves none of them unmet.

## 5. Reusable design artifacts

All paths below exist only at commit `e3d7012b` and are absent on `main`.
Reuse means carrying an idea into a new, versioned contract under its own
study record or PIT Kernel decision; nothing here is adopted automatically,
and the Panel v2 constants (feature vector, hashes, protocol IDs) must not
be cited as if they governed U1 work.

### 5.1 Source-manifest schema

`e3d7012b:docs/panel_v2/source_manifest.schema.json` (absent on `main`)

| Reusable | Obsolete (annual panel / capstone) |
| --- | --- |
| Append-only `documents[]` record: `source_document_id`, `source_class`, `source_ref`, `first_publication_timestamp` kept separate from `retrieval_timestamp`, `document_sha256`, `extraction_method` | `version_id`, `protocol_id`, `registration_doc` consts tied to `panel_v2_pit` |
| Per-source `rights_status` and `license_status` (`UNASSESSED`/`CLEARED`/`RESTRICTED`/`BLOCKED`), so unassessed material cannot become collection-ready | `raw_root` / `generated_root` consts naming the never-created v2 roots |
| `declared_acquisition_windows` with `declared_by`, `authorization_ref` and `declared_before_acquisition = true` | `declared_window` in whole years (`start_year`/`end_year`) |
| `benchmark_series`: `PRICE_INDEX` and `TOTAL_RETURN_INDEX` are distinct versions that may not be joined; pinned provider, instrument, endpoint, calendar and return formula | `target_series` fixed to the annual `TC-A` formula |
| `price_series` with `corporate_action_evidence_required = true` and a ledger hash | `feature_resolution` consts: the 40 capstone features and their two hashes |
| Realized `coverage` recorded in the manifest, never in version or file names (B8) | `legacy_quarantine` const list of the capstone's 17 vendor columns |

### 5.2 PIT cell-evidence schema

`e3d7012b:docs/panel_v2/pit_cell_evidence.schema.json` (absent on `main`)

| Reusable | Obsolete (annual panel / capstone) |
| --- | --- |
| Separate `first_publication_timestamp`, `as_of_timestamp`, `knowledge_timestamp`, `retrieval_timestamp`, each timezone-bearing; retrieval time never stands in for publication time | `feature_year` as an integer calendar year (minimum 2017) |
| `pit_ok` computed, never trusted from input, with predicate `knowledge_timestamp <= pit_cutoff_timestamp` and five registered fail-closed conditions | `pit_cutoff_timestamp` pattern hard-wired to `YYYY-12-31T23:59:59.999999+03:00` |
| Non-null cells fail closed: numeric value, `pit_ok = true`, source identity, SHA-256, admissible screen status | `column` enum of the 40 capstone features |
| Null cells carry a registered `null_reason`; `source_class` may be null only on a null cell; no sentinel source classes | `applicability_rule_id` pattern `AR-001`…`AR-048` |
| Six accounting-basis fields: `accounting_framework_id` (incl. TMS 29 / IAS 29 restated), `measurement_basis`, `value_version`, `measuring_unit_date`, `currency_code`, `consolidation_basis` — directly relevant to the IAS 29 break in charter §5 rule 7 | |
| Definition-evidence gate for a ratio with no repository derivation (`definition_id` and five metadata fields, sentinels refused) | |
| `frozen_screen_status` and `conflict_group_id` (conflicts preserved, never resolved by last write) | |

### 5.3 Applicability rules

`e3d7012b:docs/panel_v2/applicability_rules.csv` (absent on `main`)

| Reusable | Obsolete (annual panel / capstone) |
| --- | --- |
| Two rule kinds: `APPLICABILITY` (is the concept defined for this issuer-period?) and `ADMISSIBILITY` (may an applicable cell carry a value?) | The 40 feature rows `AR-001`…`AR-040`, bound to the capstone vector |
| Not-applicable kept distinct from applicable-but-missing, each with its own null reason; a source gap is missingness, never non-applicability | Year-end windows (`T-2` through `T`, "T-1 year end") |
| Sign guards declared, not inferred from data (e.g. `ev_ebitda` when `ebitda <= 0`, `pb_ratio` when `equity <= 0`) | Authority delegated to Stage-A §10.3–10.5 of the annual data-expansion design |
| Growth needs an evidenced same-filing, same-basis comparative; an incomplete window yields null, never zero | Concept groups G1–G6 and their all-members-non-null eligibility rule over the capstone vector |

### 5.4 Other infrastructure-level contracts in the registration document

`e3d7012b:docs/PREREGISTERED_PANEL_V2_PIT.md` (absent on `main`)

- §3 source-class taxonomy SC-1…SC-10 as an idea: a closed list of source
  classes with no sentinel values. SC-8 (realized annual T+1 target inputs)
  and the annual framing of SC-4 are design-specific.
- D4 comparable growth: compare a restated current figure only with the
  restated comparative in the same first-public filing; never rebase across
  filings.
- D6 benchmark continuity: price index and total-return index are distinct
  series.
- §8 target overlap reconciliation: exact decimal comparison, a
  representation bound only where the source declares rounding, no tolerance
  tuned after inspection.
- §9 structural no-peek: features and targets in separate artifacts, plus an
  AST import-closure audit proving registration code cannot reach a reader.
- §10 / §13 discipline of recording "registered" and "enforced" as separate
  statuses, so no summary upgrades a frozen contract into an enforced one.

Per charter §5 and `AGENTS.md`, any acquisition-side reuse (manifests,
append-only ledgers, rights records) belongs in the PIT Kernel, not in this
repository.
