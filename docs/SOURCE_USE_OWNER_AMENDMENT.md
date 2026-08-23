# Owner source-use and private-archive governance amendment (FI-SOURCE-OWNER-AMENDMENT-01)

> This document records an **internal project governance decision by the
> repository owner**. It is **not** a legal opinion, **not** a third-party
> licence grant, and **not** external permission from Borsa Istanbul, KAP/MKK,
> Yahoo, Fintables, or any other vendor. No external legal review occurred. No
> data was acquired by this task. The repository's standing scientific position
> is unchanged: **no reliable predictive edge has been established**.

Decision identifier: **`FI-SOURCE-OWNER-AMENDMENT-01`**.

| Field | Value |
| --- | --- |
| Decision | `FI-SOURCE-OWNER-AMENDMENT-01` |
| Kind | **Internal owner governance decision** — source-access governance only |
| Authored at repository HEAD | `6814f647b9a15a6d1bb9a4f247e27ce52f515027` (branch `main`, clean worktree including untracked) |
| Protected boundary at authoring | 351 members, digest `98195607983a35d3ffc8996934be9ac1b808250a659fea126a1a9636e800cee5` (unchanged by this task) |
| Active sourcing protocol | [`docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`](PREREGISTERED_DATA_EXPANSION_STAGE_A.md), protocol identifier `FI-DATA-EXPAND-STAGE-A-v1` (**not modified** by this task) |
| Data acquired by this task | **None.** No external source was contacted; no dataset, target, benchmark, model, or result was regenerated or changed |
| Files changed by this task | 2 — this document (new) and `TASK_STATE.md` |

## 1. The owner decision

The owner has explicitly decided, as an **internal project governance gate**:

> Publicly disclosed, non-confidential financial facts obtained from reliable
> sources may be collected, used, transformed, and retained in a **private
> research archive** for FinanceIQ academic research and model development,
> **without requiring source-by-source written permission** as an internal
> project gate.

This removes an internal blocker that the project had previously imposed on
itself. It creates no external right and asserts none.

### 1.1 What owner approval covers

- Publicly disclosed Borsa Istanbul factual data.
- Publicly disclosed KAP/MKK factual data.
- Public market and index data.
- Paid or subscription exports the **owner legitimately accessed** under the
  owner's own entitlement.
- Private, local research archival of the above.
- SHA-256 checksums of acquired bytes.
- Provenance manifests.
- Deterministic derived and model-ready datasets built from the above.

### 1.2 What owner approval does **not** cover

- Public redistribution of third-party raw datasets.
- Publication of raw vendor files.
- Credential sharing.
- Bypass of authentication or access controls.
- Circumvention of CAPTCHA, rate limits, or any other access control.
- Use of another person's paid entitlement.
- Any representation that a third-party licence was granted.
- Any representation that external legal review occurred.

Each item above remains prohibited after this amendment. The amendment cannot be
cited as authority for any of them.

## 2. `INTERNAL_OWNER_AUTHORIZED` is not `EXTERNALLY_LICENSED`

These two classifications are **not synonymous** and must never be recorded,
summarized, or reported as if they were.

| Classification | Meaning | Who granted it | What it does **not** establish |
| --- | --- | --- | --- |
| `INTERNAL_OWNER_AUTHORIZED` | The repository owner has decided, internally, that this use is acceptable for FinanceIQ research | The owner | Any third-party licence, permission, waiver, contractual right, or legal conclusion |
| `EXTERNALLY_LICENSED` | An identified external rights holder granted an identified, evidenced permission | The external rights holder | Nothing here — this class is **not claimed by this amendment for any source** |

`FI-SOURCE-OWNER-AMENDMENT-01` establishes `INTERNAL_OWNER_AUTHORIZED` only. As
of this document, **no source in this repository is classified
`EXTERNALLY_LICENSED`**, and no future record may promote a source to that class
on the strength of this amendment.

## 3. Provenance remains mandatory

Owner authorization relaxes the internal permission gate. It does **not** relax
provenance. Every newly acquired source must record, where applicable:

| Field | Requirement |
| --- | --- |
| Provider | The organization or platform the bytes came from |
| Source / product / document identifier | The vendor's own identifier for the specific product, report, or disclosure |
| Source URL or stable identifier | The retrievable address, or a stable non-URL identifier where no URL exists |
| Access method | How it was obtained (manual download, owner account export, published file, etc.) |
| Access date | The date the bytes were obtained |
| Effective / as-of date | The date the *facts* are effective for, which is not the access date |
| Owner/account access class | Public, or owner's own entitled subscription/paid access |
| Raw filename | The filename as stored in the private archive |
| Raw SHA-256 | Digest of the raw bytes |
| Byte size | Size of the raw file |
| Private/public storage classification | Where the bytes are permitted to live (see §4) |
| Redistribution status | Whether redistribution is permitted; default **not permitted** |
| Parser / transformation identity | The exact committed code that reads and transforms the raw file |
| Derived outputs | The repository artifacts produced from it |
| Acquisition notes | Anything a later reader needs to reproduce or adjudicate the acquisition |

**Unknown provenance fails closed.** A value whose provenance cannot be recorded
is not admitted, is not imputed, and is not substituted. This is the existing
no-fabrication contract, restated so that owner authorization cannot be misread
as an exemption from it.

## 4. Raw storage rule — `PRIVATE_LOCAL_RAW`

The default storage classification for **new** raw third-party or vendor data is
**`PRIVATE_LOCAL_RAW`**: the bytes stay in a private local research archive.

New raw third-party or vendor bytes are **not** placed in Git merely because the
repository is private. Repository visibility is a setting that can change; it is not
a redistribution licence.

The repository may retain:

- provenance manifests,
- checksums,
- provenance records,
- transformation code,
- derived data where that derived data is separately acceptable under the
  project's existing data governance.

Any future decision to commit raw third-party files must be recorded separately,
per source, with its own justification. This amendment does not pre-authorize it.

## 5. Existing repository data is untouched

This amendment is **prospective**. It does **not** retrospectively delete, move,
bless, reclassify, or resolve any existing raw or vendor file already in the
repository.

The findings of the prior source audit
(`FI_SOURCE_AUDIT_01_PROVENANCE_GAPS_FOUND`) are preserved unchanged. In
particular, and still open:

| Existing artifact | Status after this amendment |
| --- | --- |
| `data/raw/yearly_xlsx` | **Provider provenance remains unresolved.** [`data/raw/README.md`](../data/raw/README.md) describes the set as "original yearly BIST winner cohort XLSX files" and names no provider, product identifier, access method, or as-of date |
| `data/raw/quarterly_fintables` | **Fintables owner-access provenance remains to be confirmed.** The files are recorded as frozen quarterly Fintables exports kept for audit evidence, not modeling; the owner's access class and entitlement are not yet evidenced in the repository |
| `data/trusted_raw/shares_outstanding_manual.csv` | **Upstream provenance remains unresolved.** Its `source` column carries the free-text value `user provided merged capital research` on 240 rows and is empty on 246 rows; no upstream document, identifier, or as-of date is recorded |

Also unchanged by this task:

- **No Git history rewrite is authorized.**
- **No raw file migration is authorized.** Nothing under `data/raw/` or
  `data/trusted_raw/` is moved, removed, or reclassified here.

Resolving these three gaps remains separate future work, and each remains
governed by §3.

## 6. Effect on `FI-DATA-EXPAND-04A`

The owner's **internal access-governance blocker** — the self-imposed
requirement for source-by-source written permission before collecting publicly
disclosed factual BIST/KAP information into a private research archive — is
**superseded by `FI-SOURCE-OWNER-AMENDMENT-01`**.

That is the entire effect. Specifically, this amendment:

- does **not** claim that Borsa Istanbul or KAP/MKK granted a licence;
- keeps newly acquired raw data **private** (§4);
- keeps public redistribution **prohibited by project policy** (§1.2);
- permits **no** bypass of any access control (§1.2);
- keeps **provenance mandatory** (§3);
- requires that **source-specific explicit technical restrictions still be
  obeyed** — a source's own stated technical terms, robots directives, rate
  limits, and access conditions are unaffected by an internal owner decision.

The previous `FI-DATA-EXPAND-04A-R` result stands as **historical evidence**. It
is not rewritten, not deleted, and not reinterpreted; it recorded the state of
the internal gate at the time it was written.

## 7. Effect on Stage A

[`docs/PREREGISTERED_DATA_EXPANSION_STAGE_A.md`](PREREGISTERED_DATA_EXPANSION_STAGE_A.md)
(`FI-DATA-EXPAND-STAGE-A-v1`) is **not modified by this task**.

Stage A §1 states that nothing in Stage A authorizes acquisition by itself and
that a separate authorization is required for each acquisition activity it
describes. **This amendment supplies that owner authorization** for the
source-access dimension.

It changes **source-access governance only**. It does **not** change:

| Stage-A element | Status |
| --- | --- |
| Candidate search floor (2017, search-only) | UNCHANGED |
| Point-in-time membership rule | UNCHANGED |
| Frozen target hierarchy | UNCHANGED |
| The governed 40-feature vector and its hashes | UNCHANGED |
| Missingness rule (concept groups with exact minima) | UNCHANGED |
| Model family and hyperparameters | UNCHANGED |
| Multiplicity family | UNCHANGED |
| No-peeking boundary | UNCHANGED |
| Stopping rule | UNCHANGED |
| Scientific interpretation (null and positive-result escalation) | UNCHANGED |

Stage A's own sourcing requirements remain binding in full, including the
benchmark acquisition rule (§11), the fundamentals acquisition rule (§12), and
the manual/owner-export ingestion contract in
[`MANUAL_FINANCIALS.md`](../MANUAL_FINANCIALS.md) and
[`DATA_REQUIREMENTS.md`](../DATA_REQUIREMENTS.md). Where Stage A is stricter than
this amendment, Stage A governs.

## 8. What this document does not do

- It does not acquire, fetch, download, or inspect any external data.
- It does not grant, imply, or evidence any third-party licence or permission.
- It does not constitute legal advice or record any legal review.
- It does not authorize public redistribution of any third-party dataset.
- It does not authorize access-control circumvention of any kind.
- It does not change, add, remove, or reclassify any existing repository data.
- It does not change any dataset, feature, target, benchmark observation,
  prediction, coefficient, IC, p-value, interval, or ranking.
- It does not weaken the no-fabrication contract or any leakage guard.
- It does not claim, imply, or anticipate a predictive edge. The repository's
  position remains that **no reliable predictive edge has been established**.
