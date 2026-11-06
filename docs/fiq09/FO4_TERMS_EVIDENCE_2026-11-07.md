# FIQ-09 / FO-4 — source-terms evidence note (draft)

Evidence checked: 2026-11-07, Europe/Zurich. **EVIDENCE PREPARATION ONLY — FO-4 OWNER DECISION UNSET; NOT LEGAL ADVICE.**
Research support only; not investment advice. This note reviews public provider-language only. It does not classify historical bytes, amend existing licenses, grant source access or authorize phase 2. No vendor data were read, acquired, compared or redistributed.

## Scope and authority

- [FIQ-09 Phase 1 design](../DATA_AVAILABILITY_DESIGN.md) is PROPOSED / NOT APPROVED. Its metadata-only inventory is not an exact removal manifest. The 274 R-path candidates are a minimum review set, not an approved deletion list.
- [Source-use owner amendment](../SOURCE_USE_OWNER_AMENDMENT.md) is an internal governance decision: `INTERNAL_OWNER_AUTHORIZED` does **not** establish `EXTERNALLY_LICENSED` or override contractual limits. Existing closed KAP, BIST announcement and DataStore 3184 decisions are not reopened by FO-4.
- FO-4 is the owner terms review for the historical Fintables/Yahoo inputs, separate from the owner-reported and unmeasured Capstone v1 data-accuracy concern. Source terms do not establish the accuracy or inaccuracy of a financial value.
- No source terms are interpreted as retroactively governing a historical export without account, acquisition-date, product and agreement evidence.

## Public-source evidence, observed 2026-11-07

| Provider | Public source and specific text location | Supported reading | What remains unresolved |
| --- | --- | --- | --- |
| Fintables | [User Agreement](https://fintables.com/legal/kullanici-sozlesmesi), §§2.2, 3 | §2.2 limits covered Borsa Istanbul data to the user's personal use and prohibits third-party distribution except scoped, non-systematic limited quotations; §3 describes a personal, non-transferable, time-limited license and reserves content/data rights. This does **not** authorize public source exports, systematic republishes or near-verbatim public data. | Which historical agreement, product, account tier and export rights applied when FinanceIQ obtained each legacy file; whether any separate research or derivative-output permission exists; what uses the user's own account actually covered. |
| Fintables | Same [User Agreement](https://fintables.com/legal/kullanici-sozlesmesi), §§2.11–2.12 | The document disclaims guarantees of source completeness, continuity and correctness in stated circumstances. It supplies **no observation-level evidence of error**. | No comparison, vendor-vintage or sampling evidence has been inspected. Accuracy is a separate scientific audit question. |
| Yahoo Finance | [Yahoo Finance Help: Exchanges and data providers](https://help.yahoo.com/kb/finance/article-exchanges-data-delays-sln2310.html) | The official help search result explicitly warns not to redistribute Yahoo Finance information. This supports the existing conservative **no public raw/near-verbatim redistribution** stance. Direct page retrieval during this check returned HTTP 429; therefore the wording was corroborated only from the official indexed result, not an independently archived copy. | The exact acquisition path, vintage, applicable Yahoo Finance product/data-provider terms and permissions for the historical FinanceIQ cache. This help text is not a grant of private academic use or derived-output publication rights. |
| Yahoo general APIs | [Yahoo Developer API Terms](https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html) | This is a general Yahoo developer-API terms document with its own applicability caveats; it does not by itself prove that an unofficial Yahoo Finance chart route was licensed or permitted. No such API authorization is inferred. | Whether any specifically applicable Yahoo Finance API or content terms govern historical acquisition; account or direct source evidence remains necessary. |

## Interim operational treatment (not an FO-4 decision)

1. Keep existing conservative **NO** for public redistribution of Fintables/Yahoo raw and raw-equivalent data; do not infer rights from the public availability of facts or from an internal owner statement.
2. Do not assert a blanket authorization for private institutional research, automated collection, raw export, or public derived datasets based on these public pages. Identify the actual export method, applicable historical agreement, subscription/account status and any separate permission before final rights classification.
3. Preserve the frozen Capstone v1 and all original historical records. Do not delete data, modify CI/test expectations, create source-data fixtures, inspect raw payloads or open restricted holdouts under this note.
4. Keep FO-4 **UNSET**, KO-2 backup/restore evidence **UNVERIFIED**, FIQ-09 design **PROPOSED**, and phase-2 execution **NOT AUTHORIZED**. Later action needs an exact path manifest, consumer closure, rights/distribution disposition and independent recoverable backup evidence.

## Owner review checklist (future, not silently decided)

- Verify which Fintables and Yahoo products, accounts and terms applied at the historical acquisition dates. Record evidence links/copies, date and revision without disclosing credentials.
- Decide and document allowed **internal private retention/transformation** separately from **public raw, near-verbatim and derived-output publication**. External rights/contractual constraints remain independently binding.
- Reconcile FO-4 with the exact FIQ-09 migration scope and KO-2 before any phase-2 authorization. This document is **not** an approved FO-4 or a phase-2 instruction.
