# FIQ-16: frozen Capstone v1 selection and survivorship

Evidence date: **2026-10-27**. Base: `efe3ed32ca958074c01ee9488f1f768a9d812c61`.
**Scoped documentation delivered; annual evidence table incomplete; FIQ-17 NOT EXECUTED.**
Research support only; not investment advice.

## What is established

| Claim | Status / confidence | Evidence and limit |
| --- | --- | --- |
| 81 training firms, 40 reported firms | VERIFIED / high, configuration only | Existing configuration counted without reading outcomes; [count record](survivorship_count_evidence.json). Not historical eligibility. |
| Selected in 2026 from then-current listings under an undocumented rule | VERIFIED as a repository statement / high provenance | [RESULTS §6](../../RESULTS.md#6-remaining-limitations); [2026-07-12 audit](../universe_audit.md) dates the configuration's introduction. Exact selection procedure remains UNKNOWN. |
| Structural survivorship bias | INFERRED mechanism from the documented selection frame / high | Securities already delisted before selection cannot enter a then-current-listing frame. This conditions historical coverage on survival to selection. An index exit alone does not imply delisting; this does not prove that every historical index leaver is absent. |
| Additional selection using realised returns | UNKNOWN / unresolved FO-1 detail | [Raw-source label](../../data/raw/README.md) says “winner cohort”; neither that label nor the owner's accepted wording proves a return filter or ranking. No return-based selection rule is invented. |
| Selection effect on performance | UNVERIFIED / no measurement | Charter §6 and FIQ-17 plan a frozen-design replication. Neither the sign nor magnitude has been measured in this pass. |

Owner authority: the accepted wording in [Branch · FINANCEIQ-2](https://chatgpt.com/c/6ae096dd-14f4-83ed-85fe-8cacbd3639a2)
and the current 2026-10-27 instruction authorize this scoped disclosure, not a claim
that FO-1's complete selection history or FIQ-16's full annual count is closed.
The July audit is a dated record: its then-absence of historical evidence must not
be read as absence of all later membership documents.

## Text for Paper 1 (scientific prose only)

> The capstone universe (81 firms, 40 reported) was selected in 2026 from
> then-current listings under an undocumented rule. The selection frame excludes
> firms already delisted by the selection date and therefore introduces structural
> survivorship bias. Whether an additional filter or ranking used realised returns
> is unknown. Quantifying the selection effect by re-running the frozen design on
> a rule-based, survivor-inclusive point-in-time universe (U1) is planned under
> FIQ-17; it has not been executed. Its magnitude and direction remain unknown.
> Future work will use predeclared point-in-time eligibility and follow firms
> through their holding or event windows after index exit or delisting.

İç metin: Paper 1, tamamlanmış Capstone v1 değerlendirmesini denetler: raporlanan
40 şirketlik kohort ve 81 şirketlik eğitim evreni. Evren 2026'da o günkü listelerden,
belgelenmemiş bir kuralla seçilmiştir. Seçim tarihinde zaten kot dışına çıkmış
şirketleri yapısı gereği dışlar; bu, yapısal hayatta kalma yanlılığıdır. Gerçekleşmiş
getirilerle ek seçim yapılıp yapılmadığı bilinmiyor. Aynı dondurulmuş tasarımın,
çıkanları da izleyen kurala bağlı PIT U1 evreninde yeniden çalıştırılması FIQ-17
kapsamında planlanmıştır; henüz yürütülmemiştir. Etkinin yönü ve büyüklüğü bilinmiyor.

## Bounded 2020-10-01 coverage comparison

This is **literal security-code overlap at one date**, independently recounted
on 2026-10-27 from existing FinanceIQ files. It is not a synthetic exercise,
an issuer-equivalence comparison, a complete year, or a performance bound.
The dossier's numbers are supported only in this bounded sense.

| Date / scope | Existing XU100 codes | In Capstone 81 | Outside Capstone 81 | In reported 40 | Capstone 81 outside snapshot |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2020-10-01 projection | 100 | 60 | 40 | 30 | 21 |

Source: [archived Q4 projection](../evidence/bist_membership_p3184_2020_q4_rows.csv),
`source_id=P3184-2020-Q4-01`, using `is_xu100=TRUE`; config sources and SHA-256
identities are in the [count record](survivorship_count_evidence.json).
XU030 and XU050 are nested within XU100: filtering only the literal XU100 cell
would omit constituents. No new source acquisition or alias inference occurred.

The [2026-08-25 reconciliation, §16.3 and §19-20](../BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md)
reports exact-set corroboration against existing first-party event evidence.
Its row-content reconciliation does not close provider revision semantics,
prove canonical source designation, admit a U1 formation, or promote 2020 to a
complete eligible year. The CSV's older row-status labels are not silently
updated here. The 40 codes absent from the 81 list are **not 40 delistings**.

## Annual table: unknown is not zero

Annual denominator: **UNRESOLVED**. A year-start snapshot, annual union and four
separate quarterly formations are different quantities. No annual aggregation
rule is adopted here. A single Q4 projection cannot fill 2020, let alone 2021-25.

| Year | Evidenced full-year denominator | In 81 | Outside 81 | Evidenced delisted outside 81 | Evidenced merged outside 81 | Unresolved identity/event count | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2020 | null | null | null | null | null | null | Single Q4 projection only; full-year rule/evidence incomplete |
| 2021 | null | null | null | null | null | null | Not established in this bounded pass |
| 2022 | null | null | null | null | null | null | Not established in this bounded pass |
| 2023 | null | null | null | null | null | null | Protected metadata/output gates; no new inspection |
| 2024 | null | null | null | null | null | null | Protected metadata/output gates; no new inspection |
| 2025 | null | null | null | null | null | null | Protected metadata/output gates; no new inspection |

No historical membership was reconstructed from present membership or the
Capstone list. Missing counts and event classifications remain null. Even a
complete membership table would not establish delisting returns or the
performance effect of selection. “Bound” here denotes an evidence boundary,
not a numerical upper/lower bound on performance.

## Program boundary and gates

The separate program note belongs in the [README](../../README.md) and
[Charter §2-4](../process/RESEARCH_CHARTER.md), not in the scientific paragraph.
U1 is the primary rule; U2 is the declared robustness direction, whose detailed
rules are still unresolved under the [26 October decision addendum](../research/OWNER_DECISION_ADDENDUM.md).
The Capstone company/sector/model limits do not bind new studies. No new universe
choice, full-draft adoption, model evaluation or access grant follows from this note.

FIQ-17 remains planned with its own prerequisites, committed specification,
applicable registration, ledger and access gates. The owner addendum requires
both Paper 2 and Study 3 confirmatory openings before protected 2023-25 U1
outcome calculations. This pass performs no study execution and changes no
frozen Capstone data, code, application or results.

The count-only dependency is isolated in the [KERNEL REQUEST](kernel_request_fiq16.md).
Further FinanceIQ work can continue with citation verification and journal fit;
annual-table and selection-effect closure are not asserted.
