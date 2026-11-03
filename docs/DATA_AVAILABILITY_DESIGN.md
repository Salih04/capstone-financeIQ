# FIQ-09 Phase 1 — data availability design

Prepared 2026-11-03, Europe/Zurich · Queue 4 · **PROPOSED / NOT APPROVED**.
Research support only; not investment advice. Design and metadata inventory only.
Public-HEAD removal is a proposal, not an executed migration or sanitized-state
claim. No tracked data, tests, build configuration or baseline is changed here.

## 1. Authority, evidence and remaining gates

Latest owner Work Mode instruction authorizes preparation despite missing owner
inputs: mark them UNSET and continue. It supersedes the older FIQ-09 card's
instruction to stop drafting when FO-4 is absent; it does **not** grant phase 2.
Governing records: [Charter](process/RESEARCH_CHARTER.md),
[source-use amendment](SOURCE_USE_OWNER_AMENDMENT.md),
[FIQ-09 card](process/TASKS_FINANCEIQ_2026-10-07.md),
and [inventory method/limits](fiq09/README.md).

Pinned live main: `a8f190491ad466c2f92a21b9c3f938f7a5f89be3`.
The new [complete path-metadata inventory](fiq09/inventory_2026-11-03.csv)
has **1,210 paths**, 133,024,698 Git-blob bytes. Versus its predecessor
`6b7606d0`, six paths were added, none removed and two blob OIDs changed;
the 274 R-category candidates are unchanged. The 2,014 static edges in
[the prior reference index](fiq09/references_2026-11-02.csv) were checked
against current source OIDs; every referenced source OID still matches.
This validates continued applicability of those static hits, not complete
consumer discovery. New paths are unclassified. Payloads were not read;
raw SHA-256, retrieval dates and permissions remain unknown/null.

FO-4 Fintables/Yahoo exact terms note: **UNSET / absent at pinned main**.
KO-2 independently recoverable vault/restore evidence: **UNVERIFIED**.
Design adoption and phase-2 execution authorization: **UNSET**.
Closed KAP, BIST-announcement and Product 3184 rights decisions are not reopened.
These are distinct from public redistribution and the particular output licence.
Fintables public raw redistribution remains NO. New-research prices remain
LSEG primary / DataStore cross-check / Yahoo development-only; no new source
choice, acquisition or rights conclusion is made by this design.

## 2. Conservative proposed public boundary

Propose that **all third-party raw and near-verbatim facts leave public HEAD**,
regardless of directory, extension, vendor, whether transformed to CSV, or whether
currently described as generated, clean, template or fixture. This is an internal
conservative publication rule, not a representation of a newly granted licence.
No derived CI fixture is prepared or admitted before FO-4.

| Inventory class / route | Proposed phase-2 disposition, subject to exact manifest and gates |
| --- | --- |
| R1 annual, R2 quarterly and R3 corrected XLSX | Private archive originals; exclude raw bytes from public tree and packages. Preserve frozen versions for owner reproduction. |
| R4 Yahoo JSON; R5 annual/combined CSV; R6 membership extraction | Treat as raw/near-verbatim, even where a parser renamed fields or changed format. Propose private storage and public provenance-only references. |
| S2/S3/S4/S5/D5 extracted or cleaned vendor facts and macro inputs | Presume raw-equivalent until independently reviewed; no automatic exemption for filtering or type normalization. |
| S1/S6/S7 facts, share/manual inputs; D1–D8 data, company contexts, reports and benchmark inputs | Unresolved mixed/derived payloads: review locally under authorization, trace each upstream source and its licence/output restrictions. Propose removal of any retained verbatim facts; no clearance inferred from a D label. |
| T1 examples/templates, served backend template, fixtures and copied bundles outside data/ | Same source-fact review; a template is not presumed synthetic or clear. No new synthetic financial source facts are invented. |
| M1–M5 manifests, cell provenance, source docs; C cohort configuration; O results/history; new/unclassified paths | Review for observation-bearing content and licence/privacy separately. Metadata/code/aggregate history is not automatically raw, and is not silently deleted. Preserve append-only historical scientific records; resolve any conflict before migration. |

The 274 R candidates are a **minimum review set, not the final removal list**.
An exact removal manifest must identify each admitted path and disposition after
consumer and payload classification. Unknown rights never mean publishable.
The present inventory does not certify the other 936 paths free of source facts.

## 3. What would replace removed bytes

Public manifest proposal (no observation values): repository-relative path;
content SHA-256 and size; provider/product/document ID; original publication,
effective/as-of and retrieval dates with precision; access class and rights-record
ID; private/public storage classification; parser/transformation commit;
upstream hashes; obtained-by instructions; original version and reproduction
status. Unknown fields remain null. Git blob OIDs already recorded here are
not raw SHA-256 and must not be relabelled. Compute raw digests only in a later
authorized local inventory, not by opening payloads in this task.

Obtain instructions reference the provider, required legitimate entitlement and
manual steps where applicable; no credentials, owner-private absolute paths,
redistribution service or automatic DataStore fetcher. A manifest pointer is not
evidence a journal reader can obtain an identical historical vendor version.
Preserve those original bytes and toolchain privately, with licensed owner access.

## 4. Consumer closure and software preservation plan

Use the inventory reference index to create a later exact per-file consumer map:
readers, writers, imports, glob/dynamic roots, tests, Make targets, backend boot,
containers/build contexts, served downloads and docs/notebooks. Resolve lexical
hits, comments and ambiguous edges by source inspection; inspect excluded paths
only under their separate applicable authorization. No all-consumer closure is
claimed now. Specific established risk routes remain:

- Annual CSV/yearly loader at backend startup and its original XLSX fallback.
- Corrected-input ingestion and root tests that can regenerate outputs.
- Raw cache fetchers that both read and acquire data.
- Backend Docker/build copying of data, Compose/Render roots and served templates.
- `make data-validate`, suite collection and existing hosted count gates.

Proposed test split after approval: public code/document/synthetic contract tests
plus separately executed machine-of-record tests against authorized private
originals. Every existing test gets an explicit keep/replace/private disposition;
the complete collected inventory and executed/skipped/deselected counts must
reconcile to [the dated baseline](VERIFICATION_BASELINE.md). No new deselect list,
test deletion, relaxed guard or lower test-count expectation is approved here.

`make data-validate` must still validate the exact frozen owner-local dataset;
missing private inputs must report unavailable/fail explicitly, never fetch a
replacement, fabricate observations or pass an empty validation. Its proposed
public-CI disposition requires owner approval of a separate, clearly labelled
machine-of-record result if it cannot run without private inputs. No CI green
claim may imply it validated withheld bytes. Before FO-4, use **no derived-data
CI fixture**; after FO-4, any proposed fixture needs exact lineage, allowed
output evidence and separate approval, never an automatic exception.

Before phase 2, compare candidate and base suite collections in equivalent
environments, run the private-owner data validation and all required public
checks, and preserve the frozen computation's input digests. Confirm packaging,
runtime boot and download routes no longer expose removed data. These are
software/reproduction checks, not evidence of scientific validity or data accuracy.

## 5. Protect every checkout before any removal commit

An index-only removal preserves the initiating checkout's local bytes, but
pulling a deletion into **another checkout may delete its tracked copy**.
Therefore no removal is safe merely because the author uses an index-only
operation. Proposed sequence after all gates:

1. Inventory affected checkouts/worktrees and exact versions without cleaning
   or overwriting dirty work. Notify their owners only with sending authorization.
2. Copy every required version to the private vault outside repositories and
   sync roots; verify raw digests and an independently recoverable backup.
3. Perform a restore test into an isolated directory and verify owner-local
   reproducibility before any affected checkout pulls the removal commit.
4. After explicit per-checkout confirmation, prepare the exact removal commit
   and ignore rules, preserving initiating local copies. Restore other checkouts
   from verified private copies as needed; never assume Git pull preserves them.
5. Run approved CI/private checks and verify distribution/runtime artifacts.
   Recovery uses the verified private archive, not a public reintroduction of raw
   files. Preserve change and restore history in append-only records.

History rewriting, cache/release/image purging, deployment and moving the repos
are separate consequential actions, not Phase 1 or automatically Phase 2. A
clean future HEAD does not erase earlier public exposure or existing copies.

## 6. Adoption / phase-2 gate

Owner must accept: (1) exact classification/removal and public-manifest boundary,
(2) FO-4/KO-2 evidence and consumer/test/checkout-recovery plan, and (3) the
separate phase-2 execution scope and any explicit count/disposition changes.
All are **UNSET**. Until then no removal, fixture, private-archive read,
baseline/CI mutation, acquisition or migration occurs. This proposal completes
an authorized design candidate, not FIQ-09 or its consumer-closure acceptance.
