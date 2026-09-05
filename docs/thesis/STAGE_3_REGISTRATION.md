# Stage 3 registration — defect-injection matrix

**Status: REGISTRATION ONLY.** No Stage 3 injection has been constructed, no
Stage 3 draw has been made, no Stage 3 result exists, and no guard has been
repaired. `experiments/results_thesis/defect_injection/` does not exist at
registration time. No Makefile run target, governed root, or artifact-registry
output contract is added by this registration.

Machine-readable form: `experiments/thesis/stage3_registration.py`.
Machine-checkable guards: `tests/test_thesis_stage3_registration.py`.

**Registration-test boundary.** The registration tests may inspect repository
source, read the frozen dataset read-only, verify frozen source facts, verify
registration constants, prove source semantics structurally (by AST or function
contract), and prove that no Stage 3 result root exists. They may **not**
construct the 4000 transformation, the 4001 rotation, the 4002 added leak
column, the 4003 membership selection, or the 4004 duplication — that is
executing a registered Stage 3 defect. Every frozen injection count below is
therefore a **prospective expectation**, verified behaviorally by the Stage 3
implementation tests in the separate implementation task, not here.

Authoritative base for every guard claim in this document:
`c418563f432f5b253fb3b0e69619c76608ea15ea`.

---

## Registration status and chronology

The registration is prospective but not blind. Stage 1, Stage 1b, the completed
Stage 2 governed run, and the current contents of the repository's protection
surfaces were all known when this registration was written. Three of the five
registered defects are preregistered as **NOT_DETECTED**, because the
authoritative base carries no reachable guard for them. That expectation is
recorded here, before the first draw, and it is not repaired here.

Recording an expected miss does not change the pass rule. Stage 3 PASSes only
if all five completed registered defects are detected. The expected first-draw
outcome is therefore **FAIL — INFORMATIVE**. This is a prospective expectation,
not an observed scientific result.

---

## Owner locks

- **D1 — guard definition.** For each defect class, the guard is a closed
  preregistered mapping to an existing protection surface present on the
  authoritative base. Allowed guard objects: a named validator condition or
  `issues[]` member, a named command failure or exit, a named existing test, or
  a named provenance/integrity guard. Detection counts only if a preregistered
  existing guard fires **before** any model or significance evaluation. No new
  guard may be added before the first governed Stage 3 draw to make the
  experiment pass. Where no applicable existing guard exists, that is registered
  explicitly as `NONE_EXISTING`.
- **D2 — guard-gap disposition.** Proceed protocol-faithfully. The family is not
  narrowed to already-working guards, and no guard gap is repaired before the
  first draw. A completed registered defect that is not detected is a Stage 3
  FAIL and a finding. Any later repair belongs to a separate remediation stage;
  historical first-draw artifacts remain immutable.
- **D3 — closed first-draw family.** Exactly five defect classes, listed below.
  No additional defect class in the first governed draw.
- **D4 — source pin.** Only
  `data/trusted_clean/modeling_dataset_training_2020_2025.csv`, SHA256
  `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78`.
  FI-DATA-EXPAND outputs are **not** Stage 3 inputs; expanded or PIT-corrected
  datasets must use a separate versioned path and separate prospective
  governance.
- **D5 — operational parameters.** Primary estimand is binary guard detection
  per defect class; exactly one injection per class; no severity grid; no
  repeated performance experiment.
- **D6 — Stage 7 gate.** Stage 3 does not silently unlock Stage 7. The existing
  Stage 7 wording — *"Only after stages 1–3 pass"* — remains authoritative.
  Stage 1 remains **FAILED AS WRITTEN — INFORMATIVE**, so Stage 7 remains
  blocked under the current wording even if Stage 3 passes. Any future Stage 7
  reinterpretation or amendment requires separate prospective governance.

---

## Frozen source pin

| Item | Value |
|---|---|
| Path | `data/trusted_clean/modeling_dataset_training_2020_2025.csv` |
| SHA256 | `3923888b548e6195b07e37b10efb38d0cd3e005a55070bc798139cda670eda78` |
| Rows | 403 |
| Columns | 61 |
| Years | 2020–2025 |
| Rows at the minimum year (2020) | 40 |
| Rows with an observed `next_year_return_pct` | 321 |
| Duplicated `(ticker, year)` keys | 0 |

The source is opened read-only. Its SHA256 is verified immediately before and
immediately after every defect.

---

## Existing protection surfaces

Every surface below exists on the authoritative base. None was written for
Stage 3. Each carries a reachability state, evaluated against a **contained**
construction — a private in-memory frame plus, where a surface needs a file, a
private temporary file outside `data/`.

| Surface | Kind | Signal | Reachability |
|---|---|---|---|
| `GS_DUP_VALIDATE_ISSUE` | validator condition | `issues[]` member `"<n> duplicate ticker-year rows"`; `valid_for_T_to_T1_modeling` false | `REACHABLE_CONTAINED` |
| `GS_TARGET_LEAK_VALIDATE_ISSUE` | validator condition | `issues[]` member `"LEAKAGE: next_year_return_pct present in feature set"` | `STRUCTURALLY_UNREACHABLE` |
| `GS_SAME_YEAR_LEAK_VALIDATE_ISSUE` | validator condition | `issues[]` member `"LEAKAGE: same_year_return_pct present in feature set"` | `STRUCTURALLY_UNREACHABLE` |
| `GS_DUP_ALT_TARGETS` | command failure | `ValueError("<path> contains duplicate ticker/year keys")` | `REACHABLE_CONTAINED` |
| `GS_ALIGNMENT_ALT_TARGETS` | command failure | `ValueError("modeling target_year must align exactly to year + 1")` | `REACHABLE_CONTAINED` |
| `GS_REQUIRED_COLUMNS_ALT_TARGETS` | command failure | `ValueError("<path> is missing required columns: [...]")` | `REACHABLE_CONTAINED` |
| `GS_LEAKAGE_PIPELINE_TEST` | existing test | `AssertionError` from `tests/test_pipeline_guards.py::test_leakage_guards_exclude_targets_and_same_year_return_from_features` | `INPUT_BLIND` |
| `GS_UNIVERSE_SPLIT_TEST` | existing test | `AssertionError` from `tests/test_pipeline_guards.py::test_public_40_vs_expanded_training_universe_split` | `INPUT_BLIND` |
| `GS_UNIVERSE_VALIDATE_SCRIPT` | command failure | `AssertionError` / non-zero exit from `scripts/data_collection/validate_universe.py` | `INPUT_BLIND` |
| `GS_UNIVERSE_SPLIT_LEAK` | command failure | `"[split] FATAL: non-public tickers leaked into public dataset"` | `INPUT_BLIND` |
| `GS_CELL_PROVENANCE_DUP_KEY` | provenance/integrity | `ProvenanceError("duplicate dataset key: (...)")` | `REACHABLE_CONTAINED` |
| `GS_CELL_PROVENANCE_COLUMN_COVERAGE` | provenance/integrity | `ProvenanceError("passports v1 does not cover exactly the dataset columns")`; then `ProvenanceError("columns absent from the frozen resolution table: [...]")` | `REACHABLE_CONTAINED` |
| `GS_CELL_PROVENANCE_LINEAGE_CLOSURE` | provenance/integrity | `ProvenanceError("upstream cell not present in the artifact: <cell_id>")` — **registered as a baseline state, never as a detection signal** | `REACHABLE_CONTAINED` |

Three reachability facts are load-bearing and are proved from the source, not
assumed.

**Structural unreachability of the named target-leakage condition.**
`scripts/data_collection/validate.py` tests
`"next_year_return_pct" in P.feature_columns(df)`.
`scripts/data_collection/pipeline.py::feature_columns` excludes
`set(TARGET_COLS)` by exact name, and `next_year_return_pct` is a member of
`TARGET_COLS`. The condition is therefore unsatisfiable for **every**
DataFrame. The same argument applies to `same_year_return_pct`, which is a
member of `META_COLS`.

**Input blindness.** An `INPUT_BLIND` surface reads only canonical committed
paths and accepts no injected frame. Reaching one would require writing into
`data/trusted_clean`, which the containment boundary forbids. An `INPUT_BLIND`
surface staying silent is therefore **neither an evaluation nor a
non-detection**; recording it as "did not fire" would convert an invalid
evaluation into evidence of guard adequacy.

**Cell provenance is reachable, not input-blind.** An earlier draft of this
registration classified `GS_CELL_PROVENANCE_DUP_KEY` as `INPUT_BLIND` on the
premise that `resolve_input` admits no caller-supplied root. Read from the
source, that premise is wrong and the classification is corrected here.

| Item | Frozen value |
|---|---|
| Exact callable | `scripts.data_collection.build_cell_provenance.generate` |
| Root parameter | `root`, defaulting to `build_cell_provenance.REPO_ROOT` |
| Private-root semantics | the injected frame is written to `<private_root>/data/trusted_clean/modeling_dataset_public_2020_2025.csv`, and the other nine declared inputs of `ALLOWED_INPUT_RELS` are copied unmodified beneath the same private root; `generate(root=<private_root>)` then reads and writes only inside that root, so `data/provenance` and every canonical path are untouched |
| Required relative dataset path | `data/trusted_clean/modeling_dataset_public_2020_2025.csv` |
| Declared inputs | exactly the 10 members of `ALLOWED_INPUT_RELS` |
| Repository authority | `tests/test_cell_provenance.py::regenerated`, which already copies `SOURCE_ARTIFACT_RELS` into `tmp_path_factory.mktemp("provenance_repo")` and calls `bcp.generate(sandbox)` on the authoritative base |
| Containment mode | `PRIVATE_PROVENANCE_ROOT` |

`generate`, `resolve_input`, `open_checked_file`, and `prepare_output_dir` all
take that `root`, and every containment assertion is evaluated against it. Only
the **relative** path is frozen. A contained construction therefore reaches the
module, so a silent provenance surface is a real non-detection and must be
accounted for as one.

**The lineage-closure condition is a baseline state, not a signal.**
`upstream_cells_for` gates a lineage hop on the dataset-wide `present_years`
set rather than on the per-ticker year set. The public dataset the tool declares
is a complete 40-ticker × 6-year grid, so the closure holds there. The pinned
Stage 3 source is the **training** dataset: 81 tickers, 403 rows, a minimum of
3 years per ticker — an incomplete grid. `GS_CELL_PROVENANCE_LINEAGE_CLOSURE`
therefore fires identically on the clean comparator and on every injected frame,
carries no information about any injection, and is registered as a known
baseline terminal state — never a detection signal, and never a containment
failure. Both registered provenance detection signals are decided at the frozen
column-set declarations, which `generate` evaluates *before* any cell is
resolved and before `validate_records` runs.

---

## Injection safety and containment

Every injection is isolated. No injection may mutate canonical trusted data,
`data/trusted_clean`, `data/config`, Stage 1 / 1b / 2 artifacts, source
modules, or repository state.

- **Construction.** Each defect is built on a fresh `pandas.read_csv` copy of
  the pinned source, held in memory.
- **Private temporary files.** Where a registered surface requires a path — the
  `derive_alternative_targets._load_modeling` surfaces do — the frame is written
  to a private temporary directory created outside `data/` and outside
  `experiments/results_thesis/`, and the directory is removed afterwards.
- **Validator output redirection.** `validate()` writes four report files into
  `data/trusted_clean`: `data_quality_report.json`, `data_quality_report.md`,
  `feature_engineering_report.json`, and `feature_engineering_report.md`. Any
  evaluation of a validator-issue surface **must** first redirect
  `pipeline.QUALITY_JSON`, `pipeline.QUALITY_MD`, `validate.FEATURE_JSON`, and
  `validate.FEATURE_MD` to the private temporary directory, and must restore
  them on **all** exit paths, including exception paths. Evaluating a validator
  surface by writing into `data/trusted_clean` is forbidden; if redirection
  cannot be established, the defect is **INCONCLUSIVE**. `validate()` also
  reads `data/trusted/stocks_2020_2025.csv` through `pipeline.load_reference`;
  that read is read-only and permitted.
- **Private provenance root.** The cell-provenance surfaces are reached through
  `PRIVATE_PROVENANCE_ROOT`: the injected frame is written to
  `<private_root>/data/trusted_clean/modeling_dataset_public_2020_2025.csv`, the
  other nine declared inputs of `ALLOWED_INPUT_RELS` are copied unmodified
  beneath the same private root, and `generate(root=<private_root>)` reads and
  writes only inside that root. Canonical data and `data/provenance` are never
  touched.
- **Restoration policy.** After each defect, the temporary directory is removed,
  every redirected attribute is restored, and the SHA256 of the pinned source
  and of the four canonical report files is re-verified.
- **Clean comparator.** A fresh read of the pinned source, evaluated through the
  same registered surfaces, required to emit zero registered detection signals.
  If the clean comparator emits any registered signal, Stage 3 is
  **INCONCLUSIVE**.
- **Failure behavior.** A defect whose containment cannot be established, whose
  restoration fails, or whose registered surfaces cannot all be executed exactly
  as registered is **INCONCLUSIVE**. It is never recorded as `NOT_DETECTED` and
  never recorded as `DETECTED`.

---

## Frozen guard map

Detection is decided by whether a preregistered `EXACT_DETECTION_SIGNAL` is
actually emitted, before any model or significance evaluation — not by whether
the registered expectation was met. A surface that fires against expectation
counts as detection.

### 4000 — FUTURE_YEAR_FEATURE_LEAKAGE

| Field | Value |
|---|---|
| `DEFECT_ID` | 4000 |
| `CLEAN_BASELINE_CONDITION` | every `total_assets` cell at `(ticker, T)` holds the year-T reported value; no registered surface fires on the clean comparator |
| `EXACT_INJECTION_MECHANISM` | for every row `(ticker, T)` that has a partner row `(ticker, T+1)` inside the frame, overwrite `total_assets` with the frame's `total_assets` value at `(ticker, T+1)`; rows without a T+1 partner keep the clean value |
| Row universe | all 403 rows; none added, none removed |
| Columns modified | `total_assets` only |
| Frozen counts | 322 rows receive a future value; exactly 202 rows change value |
| `CONTAINMENT_BOUNDARY` | in-memory frame + private temp CSV + validator-output redirection |
| `EXPECTED_GUARD` | **`NONE_EXISTING`** |
| `EXACT_DETECTION_SIGNAL` | `NONE` |
| `EXPECTED_RESULT` | `NOT_DETECTED` |
| `SECONDARY_IC_APPLICABLE` | yes |

This class is deliberately **not** equated with target-column leakage. The
leaked variable is a feature, sourced from the same feature one year ahead. The
target column is not copied, not read, and not a function of the injected value.

Guard gap: no surface on the authoritative base compares a feature cell against
its upstream year-of-record. `GS_ALIGNMENT_ALT_TARGETS` checks only the
`target_year` column arithmetic, which this injection leaves intact.
`build_cell_provenance` records lineage state (`present` / `null`) for the
public dataset and performs no value-year verification, and its `resolve_input`
refuses any path outside its frozen declared inputs.

Integrity invariants: pinned-source SHA unchanged; 403 × 61 shape preserved; no
duplicate key created; `target_year == year + 1` on every row;
`next_year_return_pct` byte-identical to clean; exactly one column differs;
exactly 202 rows' `total_assets` differ; no null introduced or removed.

### 4001 — T_TPLUS1_MISALIGNMENT

| Field | Value |
|---|---|
| `DEFECT_ID` | 4001 |
| `CLEAN_BASELINE_CONDITION` | the `next_year_return_pct` on row `(ticker, T)` is that ticker's realized return in T+1, and `target_year == year + 1` everywhere |
| `EXACT_INJECTION_MECHANISM` | for each ticker take the ascending-year ordered subsequence of rows whose `next_year_return_pct` is observed, of length k, and cyclically rotate those observed values forward by exactly one position: `v_new[i] = v_old[(i - 1) mod k]` |
| Row universe | all 403 rows; none added, none removed |
| Columns modified | `next_year_return_pct` only |
| Frozen counts | exactly 320 rows change value; 321 observed targets preserved |
| `CONTAINMENT_BOUNDARY` | in-memory frame + private temp CSV + validator-output redirection |
| `EXPECTED_GUARD` | **`NONE_EXISTING`** |
| `EXACT_DETECTION_SIGNAL` | `NONE` |
| `EXPECTED_RESULT` | `NOT_DETECTED` |
| `SECONDARY_IC_APPLICABLE` | yes |

The derived target columns — `next_year_rank_by_return`,
`next_year_return_percentile`, `next_year_top_10pct_returner`,
`next_year_top_20pct_returner`, `next_year_excess_return_vs_bist100`,
`next_year_outperform_bist100` — are deliberately **not** recomputed.
Recomputation would be a second, unregistered modification. No implementation
may recompute them.

**Stale-collateral disclosure and consumer boundary (D8).** Leaving those six
columns un-recomputed makes them **stale collateral**: they still carry values
consistent with the clean target and inconsistent with the rotated one. That is
disclosed, not repaired, and stale collateral is **forbidden from influencing
the Stage 3 estimand**. The boundary is executable:

- 4001 primary detection uses only the registered guard surfaces in
  `EVALUATED_SURFACES`;
- 4001 secondary IC uses only the canonical predictor features selected by
  `experiments.run_experiments._feature_cols`, plus `next_year_return_pct` as
  the single target;
- no other `next_year_*` column may be a predictor, an alternate target, an
  alignment authority, a detection signal, or a secondary IC input;
- if any implementation path consumes such a stale derived target column, defect
  4001 is classified **INCONCLUSIVE** — never `DETECTED` and never
  `NOT_DETECTED`.

Repository authority, not registration convention, makes this hold:
`_feature_cols` excludes every column whose name starts with `next_year_`, so no
`next_year_*` column — primary or stale derived — can enter the canonical model
input; and the registered secondary target is pinned to the single literal
`next_year_return_pct` via
`build_panel_for_target(target_col='next_year_return_pct', target_path=None)`.
The multi-target `TARGETS` iteration in `_eval_target` is not part of the
registered secondary path, and the alternative-target table is forbidden.

Distinctness: this is not target leakage, because the target is not copied into
any feature; and it is not duplicate-row inflation, because the row universe,
the key columns, `target_year`, `has_target`, `is_inference_row`, the null
locations, and the per-ticker target multiset are all preserved exactly.

Guard gap: `GS_ALIGNMENT_ALT_TARGETS` is the only alignment surface on the
authoritative base, and it compares the `target_year` column against
`year + 1`. This injection leaves `target_year` untouched, so the label
arithmetic still holds while the value provenance is wrong. No surface verifies
which year a target value was realized in.

### 4002 — TARGET_LEAKAGE_INTO_FEATURES

| Field | Value |
|---|---|
| `DEFECT_ID` | 4002 |
| `CLEAN_BASELINE_CONDITION` | no column outside `TARGET_COLS` carries the target value |
| `EXACT_INJECTION_MECHANISM` | add exactly one new column `leaked_next_year_return_pct` whose value on every row equals that row's `next_year_return_pct`, nulls preserved exactly; no existing column modified, no row added |
| Row universe | all 403 rows; injected frame is 403 × 62 |
| `CONTAINMENT_BOUNDARY` | in-memory frame + private temp CSV + validator-output redirection |
| Named surface for this class | `GS_TARGET_LEAK_VALIDATE_ISSUE` (structurally unreachable, not repaired) |
| `EXPECTED_GUARD` | **`GS_CELL_PROVENANCE_COLUMN_COVERAGE`** |
| `EXACT_DETECTION_SIGNAL` | `ProvenanceError` from `build_cell_provenance.generate` whose message is exactly `"passports v1 does not cover exactly the dataset columns"`; **and** `ProvenanceError` from `build_cell_provenance.build_records` whose message is exactly `"columns absent from the frozen resolution table: ['leaked_next_year_return_pct']"` |
| Detection rule | detection counts if at least one registered signal is emitted before any model or significance evaluation; `generate` reaches the passports-coverage condition first, so that signal is the expected one and the frozen-resolution-table signal is recorded when reached |
| `EXPECTED_RESULT` | `DETECTED` |
| `SECONDARY_IC_APPLICABLE` | no |

This is the smallest canonical target-to-feature perturbation. It does not
broaden into arbitrary future variables. The column name is not in
`IDENTITY_COLS`, `TARGET_COLS` or `META_COLS` and does not start with
`next_year_`, so it enters `pipeline.feature_columns` under the repository's own
feature rule and `experiments.run_experiments._feature_cols` under the secondary
metric's canonical model-input rule, without relying on any name-prefix
accident.

Detecting surface: the injected column is an **undeclared** column.
`build_cell_provenance` freezes the dataset's column set twice — once as the
`feature_passports.json` passport names inside `generate`, once as
`COLUMN_SPECS` inside `build_records` — and `leaked_next_year_return_pct` is
absent from both. Reached through a private provenance root, the module fails
closed on the added column before it resolves a single cell. This is an existing
provenance/schema guard, registered as found; **no guard was added or repaired**.
The clean pinned source trips neither declaration: the public and training
modeling datasets carry the same 61 column names in the same order, and that set
equals both `COLUMN_SPECS` and the passport names.

Separate guard-surface fact, not repaired here:
`GS_TARGET_LEAK_VALIDATE_ISSUE` is the surface the repository *names* for this
defect class, and it remains `STRUCTURALLY_UNREACHABLE` — its condition tests
the exact literal name `next_year_return_pct` against `feature_columns`, which
removes that exact name unconditionally, so no value-carrying copy under any
other name can trigger it. The stronger prefix-based check in
`GS_LEAKAGE_PIPELINE_TEST` is `INPUT_BLIND`: it reads the committed quality
report, not an injected frame. Detection for 4002 therefore comes from a
*different* existing surface; the named validator condition stays a documented,
existing-but-useless surface for this class.

### 4003 — LOOKAHEAD_UNIVERSE_MEMBERSHIP

| Field | Value |
|---|---|
| `DEFECT_ID` | 4003 |
| `CLEAN_BASELINE_CONDITION` | universe membership is the ticker-level, time-invariant assignment produced by `split_universe_datasets` from `data/config/universe_*.csv`; no row's membership depends on an outcome realized after year T |
| `EXACT_INJECTION_MECHANISM` | for each `target_year` compute the median of the observed `next_year_return_pct` values in that `target_year` using `pandas.Series.median()`; mark a row a member iff its target is null **or** its `next_year_return_pct >= that target_year median`; set `is_training_universe` and `is_public_universe` to the membership flag; set `universe_source` to `lookahead_survivor` for members and `lookahead_dropped` for non-members; then restrict the frame to member rows |
| Row universe | exactly 243 rows retained, 160 removed; no row added, no row duplicated |
| Columns modified | `is_training_universe`, `is_public_universe`, `universe_source` |
| Tie rule | `>=` — ties are retained as members |
| `CONTAINMENT_BOUNDARY` | in-memory frame + private temp CSV + validator-output redirection |
| `EXPECTED_GUARD` | **`NONE_EXISTING`** |
| `EXACT_DETECTION_SIGNAL` | `NONE` |
| `EXPECTED_RESULT` | `NOT_DETECTED` |
| `SECONDARY_IC_APPLICABLE` | yes |

The frozen canonical dataset is not changed. Rows whose target is unobserved are
retained, because an unobservable outcome cannot be selected on; the look-ahead
selection applies only to rows with an observed target. Restricting the frame to
the membership flag is exactly how `split_universe_datasets` derives a universe
dataset, so the defect exercises the repository's own universe semantics.

Guard gap: the repository holds no point-in-time universe-membership record.
`data/config/universe_public_40.csv` and
`data/config/universe_training_bist100.csv` are ticker-keyed with no year
column, so no surface can distinguish membership known at T from membership
decided with T+1 information. Every existing universe surface is additionally
`INPUT_BLIND` — `GS_UNIVERSE_SPLIT_TEST`, `GS_UNIVERSE_VALIDATE_SCRIPT`, and
`GS_UNIVERSE_SPLIT_LEAK` each read hardcoded canonical paths and none accepts an
injected frame. Their silence is recorded as **NOT EVALUATED**, never as
non-detection. No universe guard is repaired first. The reachable
cell-provenance surfaces *are* evaluated for this defect and are silent by
construction: dropping rows changes neither the column set nor the uniqueness of
the `(ticker, year)` key, and provenance records no membership semantics at all.

### 4004 — DUPLICATE_ROW_INFLATION

| Field | Value |
|---|---|
| `DEFECT_ID` | 4004 |
| `CLEAN_BASELINE_CONDITION` | the pinned source has zero duplicated `(ticker, year)` keys |
| `EXACT_INJECTION_MECHANISM` | append an exact copy of every row whose `year` equals the minimum year present in the pinned source (2020), preserving every column value including the key columns; duplicates are appended after the original rows and no value is altered |
| Row universe | 403 clean rows + 40 appended duplicates = 443 rows; the duplicated block is fully determined by `year == 2020`, so there is no sampling and no ambiguity |
| `CONTAINMENT_BOUNDARY` | in-memory frame + private temp CSV + validator-output redirection |
| `EXPECTED_GUARD` | **`GS_DUP_ALT_TARGETS`** |
| Confirming guard | `GS_DUP_VALIDATE_ISSUE` |
| Confirming provenance guard | `GS_CELL_PROVENANCE_DUP_KEY` |
| `EXACT_DETECTION_SIGNAL` | a `ValueError` raised by `derive_alternative_targets._load_modeling` whose message ends with `" contains duplicate ticker/year keys"`; **and** `validate()` `issues[]` containing the exact string `"40 duplicate ticker-year rows"` with `valid_for_T_to_T1_modeling` false; **and** a `ProvenanceError` from `build_cell_provenance.build_records` whose message starts with `"duplicate dataset key: "` |
| Detection rule | detection counts if at least one registered signal is emitted before any model or significance evaluation; all three are recorded |
| `EXPECTED_RESULT` | `DETECTED` |
| `SECONDARY_IC_APPLICABLE` | no |

`derive_alternative_targets._load_modeling` is fail-fast: after its required
column condition is evaluated, the registered duplicate-key signal raises
before control can reach the later `target_year` alignment condition. Therefore
`GS_ALIGNMENT_ALT_TARGETS` is explicitly not an evaluated surface for defect
4004; treating that unreachable-after-failure condition as executed would be a
false completeness claim. The separate contained `validate()` call still
records the confirming duplicate issue.

Integrity invariants: pinned-source SHA unchanged; injected frame is 443 × 61;
exactly 40 duplicated `(ticker, year)` keys; every duplicated row is
value-identical to its original; `target_year == year + 1` on every row; the
first 403 rows byte-identical to the clean comparator.

---

## Expected first-draw guard gaps

| Defect | Expected result |
|---|---|
| 4000 `FUTURE_YEAR_FEATURE_LEAKAGE` | `NOT_DETECTED` |
| 4001 `T_TPLUS1_MISALIGNMENT` | `NOT_DETECTED` |
| 4002 `TARGET_LEAKAGE_INTO_FEATURES` | `DETECTED` |
| 4003 `LOOKAHEAD_UNIVERSE_MEMBERSHIP` | `NOT_DETECTED` |
| 4004 `DUPLICATE_ROW_INFLATION` | `DETECTED` |

The expected guard gaps are therefore exactly 4000, 4001, and 4003. 4002 and
4004 are expected `DETECTED`, each by an existing surface found on the
authoritative base.

Expected first-draw outcome: **FAIL — INFORMATIVE**. This is a prospective
expectation and **not an observed scientific result**. Under D2 the future draw
is to be conducted faithfully. The family is not narrowed to the one working
guard, no gap is repaired before the draw, and any later repair belongs to a
separate remediation stage with its own prospective governance. The first-draw
artifacts remain immutable.

---

## Seed schedule

| Item | Value |
|---|---|
| Base seed | 42, from `provenance.SEEDS["defect_injection"]` |
| Formula | `injection_seed(defect_id) = BASE_SEED * 1_000_003 + defect_id` |
| 4000 | 42004126 |
| 4001 | 42004127 |
| 4002 | 42004128 |
| 4003 | 42004129 |
| 4004 | 42004130 |

Registered IDs 4000–4004 do not overlap Stage 1 (0–199), Stage 1b (200–599),
the reserved band (600–999), or Stage 2 (1000–3999).

All five injections are entirely deterministic: every class is registered as
**`NO_RNG`**. The formula is frozen so that no implementation may invent one
later, but it is unused in the first governed draw. An implementation that
consumes an RNG for any of the five registered defects is an integrity failure,
not a design choice.

---

## Primary estimand and decision rule

The primary estimand is binary guard detection per defect class: whether a
preregistered existing guard emits its exact registered detection signal for the
completed registered injection, **before** any model or significance evaluation.

- **PASS** — all five completed registered defects are detected by their
  preregistered existing guards.
- **FAIL** — at least one completed registered defect is not detected.
- **INCONCLUSIVE** — at least one registered defect cannot be evaluated exactly
  as preregistered due to integrity, containment, execution, or completeness
  failure.

Integrity and INCONCLUSIVE take precedence over the scientific PASS/FAIL
decision. Integrity is evaluated first.

The primary decision does not depend on model performance, an IC threshold,
p-values, permutation significance, or multiplicity.

---

## Secondary metric

**Only** for an undetected defect, the apparent IC distortion is computed and
reported descriptively, using Ridge (`alpha = 1.0`), the existing canonical
walk-forward splits, and the target and modeling semantics already frozen in the
repository.

| Item | Value |
|---|---|
| Model | `ridge`, `alpha = 1.0` |
| Target | `next_year_return_pct` |
| Rank transform | within-year average-rank percentile |
| Imputation | `NaN -> 0.5` |
| Split source | `experiments/run_experiments.py`, SHA256 `265f58678d522eea0c48fbccba415ed30b3e20abc6bb7ae0a8e33857c5feb543`, unchanged from the authoritative base |
| Split symbol | `experiments.run_experiments.SPLITS` |
| Feature selector | `experiments.run_experiments._feature_cols` |
| Target selector | `build_panel_for_target(target_col='next_year_return_pct', target_path=None)` |
| `test_2023` | train target years `(2021, 2022)`, test feature year 2022 |
| `test_2024` | train target years `(2021, 2022, 2023)`, test feature year 2023 |
| `test_2025` | train target years `(2021, 2022, 2023, 2024)`, test feature year 2024 |

The registered split tuple must **equal** the canonical `SPLITS` surface
exactly — same names, same order, same `train_target_years`, same
`test_feature_year`, and no other field. A subset is not sufficient; no
additional and no omitted split is allowed. The alternative-target table is
forbidden, and the registered secondary path never iterates
`experiments.run_experiments.TARGETS`.
| Comparator | the same construction on the clean comparator frame |
| IC | Spearman correlation between Ridge prediction and observed target, separately within each canonical test split |
| Distortion | signed `delta_ic(split) = injected_ic(split) - clean_ic(split)` |
| Reporting scope | one signed delta per canonical split; retain negative, zero, and positive values; no pooling across splits or defects and no aggregate threshold |

The secondary metric is **NON-GATING** and **DESCRIPTIVE ONLY**. No p-value, no
significance test, no multiplicity correction, and no predictive-edge inference
is produced from it. It is never computed for a `DETECTED` or `INCONCLUSIVE`
defect.

---

## Closed integrity contract

1. `frozen_source_dataset_path_and_sha_match`
2. `registered_stage3_module_hashes_match`
3. `exactly_five_registered_defect_ids`
4. `no_duplicate_defect_ids_or_defect_names`
5. `correct_seed_schedule`
6. `no_forbidden_id_overlap`
7. `writes_confined_to_stage3_result_namespace`
8. `stage1_stage1b_stage2_result_roots_untouched`
9. `no_trusted_data_or_config_mutation`
10. `no_source_module_mutation`
11. `injection_containment_restored_after_each_defect`
12. `clean_comparator_byte_and_logical_identity`
13. `expected_guard_mapping_evaluated_exactly_once`
14. `no_defect_silently_omitted`
15. `secondary_ic_only_on_undetected_defects`
16. `no_invalid_evaluation_converted_to_non_detection`
17. `deterministic_replay_contract`

The seventeenth condition defines the required replay semantics prospectively:
if a replay is performed it must reproduce every per-defect status and every
registered invariant exactly. No governed-run implementation and no recovery
implementation is invented at registration; registration defines required
semantics only.

### Explicit integrity exclusions

There is no integrity threshold on apparent IC magnitude, IC distortion size,
model performance, how many defects were detected, or whether the first draw
PASSes or FAILs. A real guard gap is valid science, not an invalid run.
Integrity is evaluated first; the scientific decision is evaluated only after
integrity.

---

## Claim boundary

Stage 3 may establish only whether the preregistered existing guard map detects
the five preregistered synthetic defects under the frozen construction.

It does **not** establish absence of all leakage, universal pipeline safety,
predictive edge, alpha, investment value, production readiness, correctness of
expanded datasets, or correctness of future unknown defect classes.

A FAIL is informative and expected if existing guard gaps are real.

This remains research support only, not investment advice.

---

## Registration-only and future governance boundary

The Stage 3 registration module makes no injection, no scientific draw, and
creates no result root. `experiments/results_thesis/defect_injection/` does not
exist at registration time. No Makefile run target is added, no governed root is
added to `artifact_registry.json`, and no prospective output contract is
declared: at registration time no Stage 3 output file exists, so prospective
artifact contracts are **NOT_REQUIRED_AT_REGISTRATION** under the current
`proposed_future` rule.

Before any future Stage 3 execution, the implementation task must add the
runner, a real Makefile target, the Stage 3 result root to
`artifact_registry.json` governed roots, and one ownership contract for every
emitted file, in the same pre-run governance step. This registration does not
waive that requirement.

No Stage 3 result root exists, no Stage 3 runner exists, no defect has been
injected, no guard has been repaired, and no Stage 1, Stage 1b, or Stage 2
artifact is changed by this registration.
