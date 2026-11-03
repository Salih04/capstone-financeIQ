# New research — official daily-price source options

**DECIDED · 2026-11-02 · no file acquired yet.**
Research support only; not investment advice.

## Owner decision (2026-11-02)

- **Primary: LSEG Workspace (Datastream) through UB Basel.** University-licensed,
  no cost to the owner (charter §5 rule 5). Daily unadjusted prices and volume,
  corporate-action adjustment data and total-return indices for BIST equities,
  including delisted ones, plus Turkey sovereign CDS and government bond yields.
  Licensed data: research use, the license's export limits, no redistribution,
  raw exports only in the vault. Access: individual license on request (owner
  card KO-6).
- **Second source: Borsa Istanbul DataStore**, through the academic request
  route (C) and/or a zero-cost daily-price product (B), manual download only
  (owner card KO-7). Use: official venue cross-check of LSEG raw closes on a
  fixed-seed sample, and gap filling where LSEG coverage is missing. Same
  upstream venue, so agreement is a consistency check, not independent proof.
- **Yahoo:** pipeline development and synthetic-twin profiling only; never a
  source for a reported result.
- **Fallback (no new decision needed):** if no LSEG data is obtained by
  2026-11-30, through either an individual license or the library reading-room
  workstation, DataStore becomes primary and LSEG becomes the cross-check once
  available.

The route analysis below is kept as the evidence record.

The owner has not selected a free official daily-price source for the new research
program. These are possible access routes, **not confirmed free datasets**, and
are not independent upstream sources from one another. Only official explanatory
pages were researched; no historical price file, sample, account, order or source
agreement was opened/accepted. No acquisition plan or Kernel sequence is created.

## Evidence-based alternatives (unranked)

| Possible route | Exact first-party evidence checked 2026-11-02 | Free access, coverage and rights uncertainties |
| --- | --- | --- |
| A — BIST public daily equity bulletins | [Günlük Bülten](https://www.borsaistanbul.com/veriler/gunluk-bulten), “Pay Piyasası Bültenleri” and archive note: the page describes bulletins from 22 August 2011 onward. [Technical FAQ](https://www.borsaistanbul.com/en/faq/technical-side-equities-market-data-dissemination), “Is there any way, from the website, to get prices of listed equities?” directs users to daily bulletins. | Official venue origin and a public navigation route are evidenced. Actual free file access, continuous daily history, security-level fields, delisted/suspended securities, corrections, adjustment basis and corporate actions have NOT been tested. The FAQ includes old session conventions, so it is not a current schema specification. A public page is not evidence of permission for bulk automation, local archival or redistribution of price files. BIST announcement rights already closed by the owner do not establish the scope of this distinct price-bulletin product. |
| B — DataStore daily/end-of-day price product, if its exact product is free | [Historical Data Sales](https://www.borsaistanbul.com/en/data/historical-data-sales) identifies DataStore as the historical/reference-data channel. [2021 Integrated Annual Report](https://borsaistanbul.com/files/Faaliyet_Raporu_2021.pdf), paragraph beginning “2021 Mart ayı itibarıyla”, reports free DataStore data with exceptions for intraday, ITCH and adjusted prices. | The report is dated evidence, not a 2026 price list. Identify the exact unadjusted daily-price product, current cost, dates, OHLC/volume fields, corporate-action supplements, revision policy and delisted coverage. An adjusted-price product may be paid; no price or zero-cost entitlement is confirmed here. DataStore remains manual-only. Product 3184 is membership, not daily prices: its already closed rights/access decision is preserved and cannot be transferred to a different product. |
| C — BIST academic zero-cost provision, subject to eligibility and explicit confirmation | The same [2021 report](https://borsaistanbul.com/files/Faaliyet_Raporu_2021.pdf), academic-data sentence immediately following the DataStore paragraph, describes academic requests as free except ITCH. The older [2017 report](https://www.borsaistanbul.com/files/borsa_2017_integrated-annual-report.pdf), “Historical Data Sales and the Supports Provided to Universities”, describes free or substantially discounted academic data. | This is evidence of historical academic provision, not a standing entitlement for Salih or this project. Current eligibility, zero fee (a discount alone is insufficient), exact price/action files, historical/delisted coverage, delivery and permitted private/aggregate use need confirmation. No request was sent and no agreement is proposed as accepted. It could be the same underlying BIST product as B; do not count it as an independent price-validation source. |

## Boundaries and owner choice still open

- **KAP is not an official daily-price series provider.** Its
  [General Information](https://www.kap.org.tr/tr/about/genel-bilgi) describes a
  disclosure/financial-report archive, not a daily OHLC/total-return service.
  That page alone cannot establish a universal absence claim, but provides no
  daily-price product to select. The owner's KAP role distinction is retained;
  individual disclosures mentioning prices are not a price panel.
- **KER-13c's planned source is Yahoo**, per the dated
  [Kernel task card](../process/TASKS_PIT_KERNEL_2026-10-07.md), “KER-13c”.
  This is a plan, not verified current implementation or a free official BIST
  price feed. Yahoo, yfinance wrappers and commercial portal displays do not
  satisfy “official venue source” merely by showing BIST prices.
- No paid source or API is authorized. The closed rights decisions for **KAP,
  BIST announcements and DataStore Product 3184 stay closed**. Only the distinct,
  still-unspecified daily-price requirement remains undecided; this is not a
  request to repeat those decisions. Source correctness and FO-4 terms are
  separate questions; Fintables raw public redistribution stays NO.

**Remaining owner decision:** choose whether to pursue A, a demonstrably zero-cost
product under B, a confirmed zero-cost academic route C, or defer the daily-price
requirement if none meets the constraints. Before adoption, bind the exact product,
cost evidence, permitted operations, observation/availability times, immutable
lineage, security identity, historical/delisted coverage, price basis and action
handling to the intended study. Unknown availability stays unknown; do not replace
the research universe with current constituents or the capstone cohort. This
document chooses none, authorizes no retrieval and sends no information to Kernel.
