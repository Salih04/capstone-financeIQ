# FIQ-09 — metadata/code inventory continuation

**2026-11-02 · Phase 1 inventory only · incomplete consumer closure.**
Freshly fetched main: **6b7606d0e60d8c0ecd2cb9bd8d57beee7f02c926**.
Research support only; not investment advice.

The live owner instruction authorizes this limited continuation. It does not
approve a data-availability design, phase 2, removal, backup access or raw-payload
inspection. The governing [FIQ-09 card](../process/TASKS_FINANCEIQ_2026-10-07.md)
still requires **FO-4 and KO-2**. The expected
`docs/SOURCE_TERMS_REVIEW_2026-10.md` is **missing from this main**. Real independent
backup/restore evidence for KO-2 was not inspected or verified. Therefore no
substantive design was written and no phase-2 work was started. Existing local
proposals do not establish approval or close either gate.

FO-4 is strictly the Fintables/Yahoo **terms review**; the owner's quality concern
is recorded separately in the [Capstone record](../CAPSTONE_V1_RECORD.md) and
[RESULTS](../../RESULTS.md). **Fintables public raw redistribution: NO.** The
owner explicitly states KAP, BIST announcement and DataStore Product 3184 rights
decisions are already closed. None is reopened here. External permission metadata
remaining UNKNOWN is an evidence limitation, not a request to repeat those decisions
or a representation that internal owner authority grants an external licence.

## Pinned read-only findings

| Finding | Direct metadata/static evidence |
| --- | --- |
| Current tracked tree | 1,204 unique paths; 132,255,182 Git blob bytes from `git ls-tree -r -l -z` at the pinned main |
| Comparison with 2026-10-27 inventory base efe3ed32 | 31 added paths, 0 removed paths, 46 changed blob OIDs; every one of the 274 R-path candidates has unchanged mode/type/OID/size |
| Raw/near-verbatim candidates by path rules | 6 annual raw XLSX; 8 quarterly XLSX; 6 corrected annual XLSX; 246 Yahoo price/macro cache JSON; 7 annual/combined CSV conversions; 1 Product 3184 row extraction = 274 |
| Source/config scope inspected | 307 regular code/config files; 408 matching locations in 85 files; 2,014 artifact-to-location edges |
| Edge classification | 149 comment/docstring, 11 read/package hints, 7 write hints, 1,847 unresolved lexical edges; these are not 2,014 confirmed readers |
| Payload access | No data/result blob opened by the inventory scan; raw SHA-256 and retrieval dates remain empty/unknown; Git OIDs are not raw SHA-256 |

Machine-readable evidence, containing paths and metadata rather than observations:

- [All tracked paths and dated/path-based categories](inventory_2026-11-02.csv).
- [Per-artifact static references, source OID and line number](references_2026-11-02.csv).
- [Every tracked path's source-scan/exclusion status](scan_paths_2026-11-02.csv).

**Classification is provisional.** Categories carried from the dated 2026-10-27
inventory are not payload validation. Its “generated/clean/template” labels prove
neither source-fact absence nor publication rights. Seven additional S2/S3/S4/S5/D5
paths retain extraction/near-verbatim risk: yfinance candidate and cleaned candidate;
two workbook-fact candidate CSVs; Yahoo year-end prices; Yahoo year-end FX; CPI input.
All other source/manual/derived classes also remain review candidates. Eight
templates/examples and the served backend quarterly template remain unverified.
The 31 newly tracked paths have no inherited classification and remain explicitly
unclassified. The inventory is not a removal list or publication clearance.

## Consumers and routes established from code, not executed

The reference CSV lists every static hit per artifact; directory matches fan out
to candidate files and composed-year hints do not prove an individual file is read.
The following routes were additionally inspected in source at the pinned base:

| Input / route | Code evidence and entry points |
| --- | --- |
| Annual raw XLSX | `backend/app/trusted_data.py:167–178` parses Excel; `backend/scripts/convert_trusted_xlsx.py:32–74` selects annual files and converts them. `backend/scripts/validate_trusted_data.py:62–68` validates originals. `backend/app/services/dataset_service.py:11,33–39,43–58` reads annual files for ticker availability; `backend/app/services/forecasting_service.py:138–146,192` discovers/reads workbooks. `scripts/data_collection/extract_yearly_snapshots_to_manual_financials.py:43,127–146` scans and reads source tables. |
| Annual and combined CSV conversion | `backend/scripts/load_trusted_yearly.py:36–58,84–85` resolves/creates/reads the combined CSV, then upserts the database. `scripts/data_collection/pipeline.py:117` reads its configured legacy CSV. Source references in backend research/forecasting modules remain listed individually in the CSV; a path constant alone is not a confirmed direct read. |
| Corrected annual workbooks | `scripts/data_collection/ingest_corrected_yearly_financials.py:36,121`; Makefile targets `ingest-corrected-yearly` and `data`. `tests/test_corrected_yearly_ingestion.py:22–28` skips without workbooks and calls ingestion; running this test can write outputs, so it was not run locally. |
| Quarterly raw workbooks | `scripts/data_collection/inspect_quarterly_snapshots.py:20,46–59`; Makefile `inspect-quarterly`. No diagnostic was executed. |
| Yahoo cache JSON | `scripts/fetch_yahoo_chart_prices.py:154,171–176` reads existing price cache JSON; `scripts/fetch_usdtry_year_end.py:21–30` reads FX cache JSON. Makefile `fetch-training-prices` / `fetch-usdtry` enter these scripts, which can also acquire/write. No fetcher was executed. |
| Raw-fact conversions outside the R set | `scripts/data_collection/clean_yfinance_candidate.py:35–36,49–54,168–171,193–195` filters/normalizes retained rows; this is not proof that facts cease to be raw-equivalent. Its Makefile consumers and further filename references are in the index. |
| Backend boot and packaging | `backend/scripts/start_backend.sh` calls the yearly loader. `backend/Dockerfile:9–11` copies data/experiments/training trees; `.dockerignore` does not exclude raw data. Compose lines 36–38 and Render configuration set runtime paths. These are packaging/configuration exposure routes, not evidence of an inspected image or live deployment. |
| Served template | `backend/app/main.py:121–122` serves `backend/templates/quarterly_fundamentals_template.csv`; its payload was not opened. It remains in review scope despite being outside data directories. |
| Software verification | `.github/workflows/verify.yml` collects/runs suites and validates retained data. Changes since the old inventory add synthetic jobs/count gates, not a raw-data migration. No test, Makefile or CI exclusion/count was changed here. |

**Coverage limits / no exhaustive claim:** 51 Kernel/SC5/thesis/unrelated research
paths and 127 result/report paths remain excluded from source reading under the
preserved boundary; 719 other paths are not code/config under the scanner's rules.
Those exclusions are explicit in the scan manifest, not evidence of no consumer.
Dynamic roots/env values, cross-line path construction, glob enumeration, imports,
transitive callers, external consumers, SQL copies and history/images can evade
lexical matching. Comment/docstring hits include `backend/app/models/trusted.py`
and linter path strings; they must not be called readers. Even a zero-hit raw path
remains unresolved. Static inventory continuation is delivered; **all-consumer
closure and FIQ-09 completion are not claimed**.

## Evidence method and next gate

The existing local preparation branch `codex/fiq-09-metadata-preparation-20261027`
at commit 125194a0 is dated evidence, absent from current main. Its stdlib scanner
and metadata CSV were inspected, not adopted as a design. An external scratch
driver reused its path-group and lexical-match functions against the fresh Git
tree, carrying the old categories only as dated labels. It inspected regular
FinanceIQ code/config blobs and additionally included GitHub workflow/script/
gate configuration. It imported no application/test/data consumer and executed
no collection hooks. The scan retained no matched source text or financial values.
Scratch code was kept outside this repository; the three CSVs pin every scanned
source OID, path, line and rule classification for review.

Local verification of this documentation candidate: `make docs-lint`,
`make claims-lint` and `git diff --check` passed. Additional checks passed for
all three nested Markdown documents' local links/cited paths, all 1,204 inventory
rows against pinned tree metadata, reference/source-OID integrity, and preservation
of the complete old byte prefix in RESULTS.md and the Capstone record. These are
documentation/software checks, not data-accuracy evidence. An initial scratch
checker import failed because its module was not registered for Python dataclasses;
the checker was corrected and rerun successfully. No repository linter was changed.

Remaining prerequisites are the exact FO-4 terms record and verified KO-2 evidence,
followed by the separately authorized and approved design gate in the existing card.
No owner approval is inferred from these findings. No data-availability design,
manifest migration policy, fixture/test redesign, raw hash computation, vault read,
data deletion, history rewrite, source-data edit, experiment, holdout read, Kernel
write/feedback, deployment or merge was performed by this continuation.
