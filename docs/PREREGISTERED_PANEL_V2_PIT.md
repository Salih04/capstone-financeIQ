# Preregistered panel v2 — PIT annual BIST panel

**Protocol:** `FI-PANEL-V2-PIT-v1`
**Version:** `panel_v2_pit`
**Task:** `FINANCEIQ-PANEL-V2-PIT-PREREGISTRATION-CRITICAL-MICROFIX`
**Mode:** preregistration / governance only
**Authoritative base:** `c418563f432f5b253fb3b0e69619c76608ea15ea`

## 1. Status and boundary

This document completes the registration contract for a new v2 panel
construction. It does not collect data, fetch prices or benchmarks, extract
company values, build a real-valued panel, inspect target overlap values, run a
scientific experiment, or alter the existing v1 data and results.

The registration is complete while collection remains on hold:

| State | Frozen value |
| --- | --- |
| `FULL_PANEL_FEASIBLE` | `CONDITIONAL` — not confirmed |
| `COLLECTION_READY` | `NO` |
| `IMPLEMENTATION_READY` | `NO` — implementation governance is still a prerequisite |
| `OWNER_DECISIONS_REQUIRED` | `NONE` for this registration |
| reliable predictive edge | not established |

This protocol reserves two new roots, both **(proposed)** and neither present at
registration: the generated root `data/panel_v2_pit/` **(proposed)** and the raw
root `data/trusted_raw_pit_v2/` **(proposed)**. Neither is created by a
registration import or by the registration tests, and the tests assert their
absence. The future v2 outputs stay separate from `data/trusted/`,
`data/trusted_clean/`, `data/trusted_raw/`, `data/provenance/`, and
`experiments/`.

## 2. Owner locks D1–D7

### D1 — calendar-year-end PIT cutoff

For feature year **T**, the cutoff is the inclusive end of calendar year T in
`Europe/Istanbul`:

```text
pit_cutoff_timestamp = T-12-31T23:59:59.999999+03:00
```

Only information whose `first_publication_timestamp` is known and is less than
or equal to that cutoff may enter feature T. Retrieval time is not publication
time. The builder must select the latest admissible annual filing by
`fiscal_year_of_record` subject to this cutoff. An FY-T annual report first
published in T+1 is not a feature-T source; the admissible filing will usually
be FY T-1.

These fields are stored separately in evidence and row eligibility records:

`feature_year`, `fiscal_year_of_record`, `source_document_id`,
`first_publication_timestamp`, and `pit_cutoff_timestamp`.

Therefore `feature_year != fiscal_year_of_record` is expected and must never be
silently rewritten into equality.

### D2 — TC-A annual target

The confirmatory target is the separate target-side construction:

```text
TC-A = 100 * (P_adj(T+1) / P_adj(T) - 1)
```

`P_adj(T)` and `P_adj(T+1)` are governed/evidenced year-end security prices.
The target start is not shifted to a first-publication date. Target data is
stored outside the feature panel in `panel_targets.csv` and is never copied
into `panel.csv`.

### D3 — financial debt ratio

`financial_debt_ratio` has no repository derivation, and this registration does
not invent a formula for one. A non-null cell is inadmissible unless it carries
all six registered definition fields — `definition_id`, `definition_text`,
`numerator_definition`, `denominator_definition`,
`definition_source_document_id`, `definition_publication_date` — together with
an `SC-10` origin and the ordinary PIT and source evidence. `definition_id` may
not be empty, null, or a sentinel such as `UNKNOWN`. The cell schema enforces
this per cell.

Whether one `definition_id` holds across the whole panel is a relational
property that no JSON Schema can express. It is registered here and marked
`DEFERRED_TO_IMPLEMENTATION`; no code checks it yet.

If the direct definition is unavailable, the cell is `NULL` with
`DEFINITION_UNAVAILABLE`. The resulting G5 failure is accepted exactly as
Stage-A §10.3 requires, and that gate is not relaxed, tightened, or
re-parameterized here.

### D4 — comparable growth

Every growth input records these separate accounting fields:

| Field | Role |
| --- | --- |
| `accounting_framework_id` | TFRS/IFRS/BOBI/other reporting framework |
| `measurement_basis` | nominal or inflation-restated measurement basis |
| `value_version` | original or restated value version |
| `measuring_unit_date` | purchasing-power date of the reported values |
| `currency_code` | reporting currency |
| `consolidation_basis` | consolidated or unconsolidated basis |

The T and T-1 input cells must share all six fields and must come from the same
first-public filing where the comparative is presented. Unknown or mismatched
bases yield `NULL` (`BASIS_UNKNOWN` or `BASIS_MISMATCH`). No pipeline rebasing
or cross-filing composition is allowed.

A TMS 29-restated T current figure may be compared with the T-1 **RESTATED
COMPARATIVE** presented in that same first-public filing, subject to D1. It may
not be compared with nominal T-1 from the older T-1 filing. Original/restated
and nominal/inflation-restated are never collapsed into one field.

### D5 — legacy 17

The legacy vendor-snapshot set is not asserted from memory. It is the set of
governed columns whose recorded v1 cell provenance carries
`source_class = vendor_xlsx` in
`data/provenance/cell_provenance_public_2020_2025.csv`, and the registration
tests re-derive it from that file. It is exactly 17 columns: `current_assets`,
`current_ratio`, `ebitda_growth_pct`, `equity`, `financial_debt_ratio`,
`gross_profit_growth_pct`, `leverage_ratio`, `long_term_liabilities`,
`net_debt`, `net_debt_to_ebitda`, `net_income_growth_pct`,
`non_current_assets`, `operating_income_growth_pct`, `revenue_growth_pct`,
`short_term_liabilities`, `total_assets`, and `working_capital`.

Those 17 live in the separate `_legacy_unverified` namespace only. They default
to null, never populate a governed v2 feature name, and never resolve a
confirmatory row. The quarantine label `LEGACY_VENDOR_SNAPSHOT` is not one of
the registered SC-1…SC-10 source classes; the manifest schema refuses it, and
the cell evidence schema cannot represent a legacy-namespaced column at all.

Stopping a future builder from writing a legacy value under a governed name is a
runtime gate. No builder exists, so that enforcement is
`DEFERRED_TO_IMPLEMENTATION` and is not claimed here.

### D6 — benchmark continuity

The frozen v1 `XU100.IS` construction is recorded as the **BIST 100 price
index**. For continuity, `index_variant = PRICE_INDEX`. It is not called total
return merely because an old template comment used that wording.

A `TOTAL_RETURN_INDEX` is a distinct benchmark version and cannot extend or be
silently joined to the price-index history. Provider/source, exact instrument
identity, endpoint, calendar convention, and annual-return formula are pinned
as separate manifest fields.

### D7 — v2 re-derivation

All included 2020–2025 rows are re-derived under the v2 PIT, identity,
accounting, price, benchmark, target, and eligibility rules. No governed v1
cell is copied into a governed v2 feature. The old v1 artifacts remain
immutable and any overlap comparison is diagnostic only.

## 3. Frozen source-class taxonomy

The following numbering is authoritative and must not be renumbered after
registration:

| ID | Source class |
| --- | --- |
| `SC-1` | PIT EFFECTIVE-DATED INDEX MEMBERSHIP |
| `SC-2` | SECURITY / ISSUER / LISTING IDENTITY AND SUCCESSION |
| `SC-3` | STATEMENT-FORMAT / ENTITY-CLASS CLASSIFICATION |
| `SC-4` | PIT ANNUAL FINANCIAL STATEMENTS |
| `SC-5` | EFFECTIVE-DATED SHARES OUTSTANDING |
| `SC-6` | SECURITY PRICES + CORPORATE-ACTION ADJUSTMENT EVIDENCE |
| `SC-7` | XU100 BENCHMARK SERIES |
| `SC-8` | REALIZED T+1 TARGET PRICE INPUTS |
| `SC-9` | GROWTH SOURCE / BASE-PERIOD EVIDENCE |
| `SC-10` | FINANCIAL_DEBT_RATIO DIRECT-DEFINITION EVIDENCE |

The conflicting partial source-class numbering was discarded. The exact names
are machine-pinned in `scripts/panel_v2/registration.py` and checked by
`tests/test_panel_v2_registration.py`.

SC-1…SC-10 is the **entire** taxonomy and is never extended. No sentinel —
`MISSING`, `NOT_APPLICABLE`, `LEGACY`, `LEGACY_VENDOR_SNAPSHOT`, `UNKNOWN`,
`NONE`, `UNVERIFIED` — may be encoded as a `source_class`. Missing and
not-applicable state is carried by `is_null`, `null_reason`, and the
applicability rule instead. A cell may record `source_class = null` only when it
is a null cell; the schema rejects a null source class on any cell that carries
a value. The same ten identifiers appear in this document, in
`scripts/panel_v2/registration.py`, in both schemas, and in the registration
tests, and the tests compare all five surfaces.

## 4. Feasibility and collection hold

The authoritative feasibility result is **conditional, not confirmed**. It is
not a reason to fabricate availability and not a reason to abandon
preregistration.

| Source classes | Prospective disposition |
| --- | --- |
| SC-1, SC-2, SC-5, SC-6, SC-8 | hard collection blockers until complete evidence/access is established |
| SC-4, SC-7 | access/depth gates |
| SC-3, SC-9, SC-10 | normalization/definition gates |

Source feasibility, access, rights, and license checks are prerequisites to
collection. Borsa İstanbul, MKK, and KAP restricted access or licensing may
require applicable external rights or agreements. No commercial or restricted
source may be used merely because an internal owner authorized the project.

The collection gate remains `NO` until every required source class is cleared,
the evidence is complete enough for fail-closed eligibility, and the future
implementation has artifact ownership and dry-run governance in place.

## 5. PIT cell evidence and source manifest

`docs/panel_v2/pit_cell_evidence.schema.json` defines one record per
`security_id × feature_year × column`, including null cells. It requires the
PIT identity/timing fields, source identity and checksum fields, accounting
bases, transformation lineage, frozen-screen state, conflict state, and
`pit_ok`. An unknown first-public timestamp cannot become admissible by using a
retrieval timestamp.

**Column domain.** This is feature-cell evidence, so `column` is an enum of
exactly the registered 40 governed features. It is not an arbitrary string. No
target column, no `next_year_*` name, no `target_year`, no PIT metadata name, no
eligibility field, no identity helper, and no `_legacy_unverified` name can be
recorded as a governed feature cell. Legacy cells live only in the separate
`legacy_unverified.csv` sidecar. `additionalProperties` is `false`.

**Non-null cells fail closed.** For `is_null = false` the schema requires a
numeric `value`, a null `null_reason`, `pit_ok = true`, a `source_class` drawn
from the value-originating classes, non-empty source identity and extraction
fields, a 64-hex `document_sha256`, `frozen_screen_status` of `PASSED` or
`NOT_APPLICABLE`, and non-null `first_publication_timestamp`,
`knowledge_timestamp`, `retrieval_timestamp`, and `pit_cutoff_timestamp`, each
carrying an explicit timezone offset. A non-null cell with `pit_ok = false`, or
with any temporal field missing, is unrepresentable.

**Null cells.** For `is_null = true` the schema requires a null `value` and a
registered `null_reason`.

**What the schema layer cannot do.** `pit_ok` must be *computed* by the
implementation and never trusted from input. Its predicate is
`knowledge_timestamp <= pit_cutoff_timestamp`, both normalized to
`Europe/Istanbul`. JSON Schema Draft 2020-12 has no relational comparison
between two instance values, so it cannot prove that ordering. The ordering
check is therefore classified **`DEFERRED_TO_IMPLEMENTATION`** and is **not**
claimed to be enforced today. The implementation validator, when it is written,
must fail closed when the first-public or knowledge timestamp is absent, when
the cutoff is absent, when the knowledge or first-public timestamp is after the
cutoff, when a timezone cannot be normalized, or when the evidence chronology is
internally inconsistent. That validator does not exist at this commit.

`docs/panel_v2/source_manifest.schema.json` defines the future append-only
manifest. It separately pins annual statement sources, shares, price ledgers,
benchmark versions, target-side price inputs, declared acquisition windows,
source rights/license state, realized coverage, the governed feature-vector
identity, and the legacy quarantine declaration. It does not authorize
acquisition by itself.

Its `feature_resolution` block freezes the vector identity as consts: the 40
names in order, a count of 40, both registered SHA-256 hashes, and
`matches_registered_hash = true`. A manifest built over a different feature
vector fails validation instead of asserting its own correctness, so it cannot
masquerade as this registered panel version.

The manifest must carry an access/license status for every retained source.
Unassessed, restricted, blocked, or unlicensed material cannot silently become
collection-ready.

## 6. Applicability and row eligibility

`docs/panel_v2/applicability_rules.csv` contains 48 rules in 12 columns: one
`APPLICABILITY` rule for each of the 40 governed features (`AR-001`…`AR-040`)
and eight `ADMISSIBILITY` gates (`AR-041`…`AR-048`).

The applicability contract is **not** authored here. Its authority is Stage-A
§10.3 (group membership) and §10.4 (the exhaustive not-applicable conditions),
and the registration tests parse those Stage-A tables and check every one of the
48 rows against them rather than against this registration's own constants.
Stage-A §10.4 declares exactly thirteen conditional members; the CSV carries
exactly thirteen `CONDITIONAL` feature rules. Structural non-applicability is
limited to those predeclared accounting-sign, base-period, and
evidenced-trading-history conditions. Per Stage-A §10.5, a source-class gap for a
concept that *is* defined for the issuer-year is missing data, not
non-applicability.

The `applicability` column takes three values. `ALWAYS_APPLICABLE` and
`CONDITIONAL` restate the Stage-A §10.4 verdict for the feature the rule scopes.
`PER_FEATURE_APPLICABILITY` is the only admissible value for a panel-wide gate
scoped to `(all governed features)`: such a gate constrains whether an already
applicable cell may carry a value, and it must not assert one applicability
verdict over features whose Stage-A verdicts differ.

Two rules were corrected against that authority:

| Rule | Was | Now |
| --- | --- | --- |
| `AR-042` (five G4 growth features) | `ALWAYS_APPLICABLE`, with the unregistered composite reason `BASIS_MISMATCH_OR_BASIS_UNKNOWN` | `CONDITIONAL` on the verbatim Stage-A §10.4 growth condition — the issuer-year is the earliest evidenced feature year, so no evidenced T-1 base period exists — with `NOT_APPLICABLE` when the condition holds and the two registered reasons `BASIS_MISMATCH;BASIS_UNKNOWN` when an applicable cell has no admissible same-basis pair |
| `AR-044` (`price_drawdown_from_3y_high_pct`) | `ALWAYS_APPLICABLE`, contradicting §10.4, and describing a source-supply gap as non-applicability | `CONDITIONAL` on the verbatim §10.4 condition — first-party evidence shows the security was not trading for the full T-2 through T window — matching `AR-029`. Inside an *applicable* window a missing evidenced `SUCCESS` observation stays §10.5 missingness (`WINDOW_INCOMPLETE`), never non-applicability and never a zero drawdown |

Two further rows were corrected by the same audit. `AR-041` now names both
registered PIT reasons (`PIT_INADMISSIBLE;PIT_UNVERIFIABLE`) instead of one, and
`AR-010` now reports an unsupplied SC-10 value as `MISSING_SOURCE_CLASS_GAP`
under §10.5, leaving `DEFINITION_UNAVAILABLE` to the `AR-043` definition gate.
The G5 consequence is identical either way: the cell is null and the group
fails. Stage-A was not edited, and no exemption was created.

The six concept groups are:

| Group | Concept | Rule |
| --- | --- | --- |
| G1 | SIZE_SCALE | every applicable member must be non-null |
| G2 | PROFITABILITY | every applicable member must be non-null |
| G3 | VALUATION | every applicable member must be non-null |
| G4 | GROWTH | every applicable member must be non-null and basis-valid |
| G5 | LEVERAGE_LIQUIDITY | every applicable member must be non-null; debt ratio definition is required |
| G6 | PRICE_MOMENTUM | every applicable member must be non-null with complete required windows |

An empty applicable set is never vacuously satisfied. Confirmatory eligibility
requires resolved identity, effective-dated membership, comparable statement
format, PIT-valid evidence, no unadjudicated conflict, and all six groups
satisfied. The complete-case robustness cohort is named prospectively as rows
with zero not-applicable cells; it is not selected after outcomes.

## 7. Frozen feature vector

The governed v2 vector has exactly 40 names in this order:

```text
benchmark_same_year_return_pct
current_assets
current_ratio
ebitda
ebitda_growth_pct
ebitda_margin
enterprise_value
equity
ev_ebitda
financial_debt_ratio
gross_margin
gross_profit
gross_profit_growth_pct
leverage_ratio
long_term_liabilities
market_cap
net_debt
net_debt_to_ebitda
net_income
net_income_growth_pct
net_margin
non_current_assets
operating_income
operating_income_growth_pct
pb_ratio
pe_ratio
price_adjclose_t
price_data_available
price_drawdown_from_3y_high_pct
price_history_years_available
price_momentum_1y_pct
price_momentum_2y_pct
price_vs_bist100_1y_pct
revenue
revenue_growth_pct
roa
roe
short_term_liabilities
total_assets
working_capital
```

Frozen hashes:

| Representation | SHA-256 |
| --- | --- |
| 40 names joined by `\n`, no trailing newline | `041566fc685b043c8618af859c268aa736fa5ae87b0d2679a2b35df779659575` |
| compact JSON array | `f8064f43ca5a446e21b2357fdafa4a9f6a1b7dfcbe7e79b8bc0835125c452543` |

This list is not authored here. Its authority is Stage-A §9, which resolves the
vector from `experiments/run_experiments.py`'s `_feature_cols` filter over
`data/trusted_clean/modeling_dataset_training_2020_2025.csv`. The registration
tests re-derive it twice — once by parsing Stage-A §9, and once by lifting the
`_feature_cols` exclusion set out of the experiments source by AST and applying
it to the modeling dataset's header row — and require both derivations to agree
with each other and with the two hashes above. Neither derivation depends on
this registration.

PIT provenance, accounting metadata, source class, identity, target, and
eligibility metadata are not vector members, and neither is any
`_legacy_unverified` name. The realized builder must re-resolve the list and
hash before any fitting and must state whether it matches these frozen values.

## 8. Target overlap reconciliation

Overlap is compared only for an exact stable `security_id` and an exact target
window. The arithmetic is decimal and the comparison uses canonical decimal
serialization.

- If both source series are exact under their source definitions, equality of
  canonical decimal serializations is required.
- If a source explicitly declares rounding precision, only the representation
  interval mathematically implied by that precision may be used.
- Unknown rounding produces no representation bound.
- A discrepancy outside the exact or representation-only bound is a
  definition/source-series break.
- No empirical tolerance is chosen or tuned after inspection. The registration
  contains no arbitrary numeric tolerance.
- The series are never averaged, frozen v1 is never rewritten, and the
  diagnostic cannot choose the predictive outcome or target cohort.

## 9. Structural no-peek

`panel.csv` contains features and row identity only. `panel_targets.csv` is a
separate target artifact.

**What is proved now.** The `scripts/panel_v2` package contains exactly two
modules, `__init__.py` and `registration.py`. The registration test parses both
by AST and proves that neither contains any I/O-capable call, and that their
combined import closure is `{__future__, types}` — so no reader is reachable at
any depth, transitively or otherwise. It further proves that no registration
artifact passes a target filename or target column name to a reader call. The
registration module is import-inert and creates no output root.

**What is not proved, and is not claimed.** `feasibility.py`, `eligibility.py`,
a builder module, and `splits.py` **do not exist** at this commit. A test that
inspected them "if present" and passed otherwise would manufacture a structural
guarantee out of an absent file, so no such test is written. The registration
test instead asserts their absence and records the obligation:

> `FUTURE_NO_PEEK_ENFORCEMENT = DEFERRED_TO_IMPLEMENTATION`. When any of those
> readers is introduced, implementation tests must examine its transitive import
> and read closure and prove it cannot access `panel_targets.csv` before the
> target stage.

The registration audit itself runs without opening `panel_targets.csv`, creating
a panel, loading values, or inspecting any target overlap value.

## 10. B1–B8 prospective dispositions

Registration freezes prospective repair contracts. It does not implement them,
and it does not close them. Each defect therefore carries two independent
statuses: what this registration has frozen, and whether any code enforces it.

| Defect | Registered intent | Registration status | Enforcement status |
| --- | --- | --- | --- |
| B1 | `price_history_years_available` is scoped to the declared T-2..T window | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B2 | an incomplete drawdown window yields NULL, never zero | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B3 | the legacy 17 stay null and quarantined and never populate a governed name | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B4 | TC-A is a separately identified literal annual target | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B5 | the security price ledger is append-only and never overwritten | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B6 | `NO_DATA`, `NOT_TRADING`, and `ERROR` never default to a value | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B7 | one future split declaration home is required before any run | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |
| B8 | realized coverage is carried by `manifest.json`, not by file or version names | `REGISTERED_DESIGN_CONTRACT` | `DEFERRED_TO_IMPLEMENTATION` |

The distinction is deliberate. **Registration has frozen intended behaviour** is
a statement about this document and the constants beside it. **Code now enforces
intended behaviour** is a statement about a builder, writer, and validator that
do not exist. Only the first is true here.

No B-item is claimed as closed, and none is asserted to be resolved by design.
`B1_B8_RUNTIME_ENFORCED` is `NO` and `B1_B8_IMPLEMENTATION_TESTS_EXIST` is `NO`.
B7's implementation file is deliberately deferred; only its single-home rule is
frozen.

## 11. P1–P23 resolution index

The registration module carries a machine-readable disposition for every prior
design item: protocol/path, immutable boundary, taxonomy, cell schema, row
eligibility, D1 cutoff, source manifest, concept groups, source gaps, legacy
quarantine, accounting comparability, debt ratio, prices, benchmark, TC-A and
overlap, target separation, no-peek, 40-feature hash, conflicts, forbidden
writers, zero-row dry-run, artifact ownership, and Stage 3 isolation.

The zero-row dry-run and artifact ownership are required before implementation
or collection but are intentionally not implemented in this registration-only
change.

## 12. Immutability and later implementation boundary

The following remain untouched and protected: existing trusted data and
provenance, existing experiment artifacts, Stage 3 code and results,
`Makefile`, `artifact_registry.json`, and
`docs/VERIFICATION_BASELINE.md`. Those implementation/pre-run governance files
belong to a later authorized step.

Before first collection, a later implementation must add artifact ownership,
Makefile targets, the dry-run proof, an append-only raw manifest/ledger, and the
runtime no-peek guard. It must not reuse the legacy year-end writers to create
the v2 panel.

No new data, target, benchmark, company value, panel row, model fit, IC,
p-value, ranking, or scientific result is produced by this registration.


## 13. Controls that are registered but not executed

Each control below is frozen by this registration and is **not** running
anywhere. The three states are recorded together so no later summary can quietly
upgrade a frozen contract into an enforced one.

| Control | State |
| --- | --- |
| source rounding reconciliation | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| append-only acquisition writer behaviour | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| no-overwrite behaviour | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| explicit acquisition status | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| corporate-action adjustment validation | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| full PIT timestamp ordering | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| panel-wide `financial_debt_ratio` definition consistency | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| future transitive no-peek | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |
| B1–B8 runtime fixes | `REGISTERED` / `IMPLEMENTATION_REQUIRED` / `NOT_YET_EXECUTED` |

No acquisition adapter and no builder is implemented by this task.

Research support only — not investment advice. No reliable predictive edge has
been established.
