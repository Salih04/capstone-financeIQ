# Paper 1 submission-readiness check

Checked **2026-10-29**, Europe/Zurich. **No submission, contact, payment or
venue choice made.** Venue facts below are what official pages showed on this
date; they can change. Research support only; not investment advice.

## 1. Venue requirements (BIR and JAM)

| Requirement | Borsa Istanbul Review (Elsevier platform) | Journal of Asset Management (Springer Nature / Palgrave) | Draft at `4b6c8823` |
| --- | --- | --- | --- |
| Author guide access | BLOCKED: [ScienceDirect guide](https://www.sciencedirect.com/journal/borsa-istanbul-review/publish/guide-for-authors) returned HTTP 403 again; the shop.elsevier.com path tried returned 404. No bypass attempted. | VERIFIED: [submission guidelines](https://link.springer.com/journal/41260/submission-guidelines), fetched after Springer's cookie redirect | — |
| Length | UNKNOWN | "between 3000 and 6000 words" | 3,996 words (4,401 with patch) as counted by `wc -w` incl. references and link text; venue counting rule not stated |
| Abstract / keywords | UNKNOWN | "a short abstract"; "up to six keywords" | Abstract 208 words excluding note links; 6 keywords |
| Review model | UNKNOWN | "double-blind peer review" | **Not anonymized**: names FinanceIQ, capstone, repository paths and commit SHAs; PDF metadata author "Salih" |
| Reference style | UNKNOWN | Chicago (16th or 15th edition), one citation form | Author-year list without volume/pages; needs conversion |
| Format | UNKNOWN | Word or LaTeX with PDF; no LaTeX template; US or UK spelling consistently | Markdown + ReportLab PDF |
| Fees | UNKNOWN (FIQ-14) | "There is no submission fee"; hybrid OA APC per FIQ-14 [J3] | — |
| Conflicts / author bio | UNKNOWN | conflicts statement at submission; ~100-word author description | Absent |
| Generative-AI use | Elsevier-wide policy (updated June 2026, [policy page](https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals)): separate AI declaration statement in the manuscript, placed before the references; AI may not be an author. BIR-specific adoption INFERRED from the platform, not read in its guide. | Springer Nature AI policy ([springer.com](https://www.springer.com/us/editorial-policies/artificial-intelligence--ai-/25428500), seen via search excerpt): LLMs cannot be authors; LLM use documented in Methods; AI-assisted copy editing exempt. Not stated on the JAM guide page itself. | **Absent.** FIQ-13/14/15 records show agent-prepared text and verification; the owner must write an accurate declaration |
| Data availability | UNKNOWN for BIR | Not stated on JAM guide page; Springer Nature research-data policy is separate and not read here | Draft has a reproducibility section but no data statement; depends on FO-4 |

FIQ-14's earlier observations (BIR scope page, JAM APC, KeAi, FRL) are not
re-checked here and keep their own dates.

## 2. Items the owner must supply

| Item | Why | Blocking for |
| --- | --- | --- |
| Venue choice | Determines format, blinding, style, declarations | Any submission |
| AI-use declaration | Both publishers require disclosure of AI use beyond copy editing | Both |
| Data-availability statement after FO-4 | Vendor unnamed in frozen sources; raw third-party files remain tracked on public HEAD (FinanceIQ context record); no redistribution right is established | Both |
| Competing interests, funding, author bio | Venue forms | Both |
| FO-1 selection statement | Selection section relies on "unknown" | Scientific completeness |
| Independent scientific review | Charter §5 rule 9 | Any claim that the analysis is ready |

## 3. Reference completeness

The draft cites 10 of the 40 FIQ-13 entries. Verified entries that address
likely referee questions but are not cited:

| Key (in references.bib) | Relevance | Verified content limit (FIQ-13) |
| --- | --- | --- |
| `Gu2020ML` | Standard ML-asset-pricing reference; temporal train/validation/test | Sections 1.7-1.8 checked |
| `Wolff2024StockPicking` | Uses historical constituents and a three-month fundamental lag | Section 2 checked; its imputation is not adopted |
| `Petersen2009Panel`, `Cameron2008Bootstrap` | Dependence-robust inference (objection R6) | Identity only; content not verified |
| `Levy2026Caution`, `David2019Leakage` | Look-ahead in AI models; leakage in financial ML (editorial) | Identity; Levy scope-limited; David is an editorial |
| `Hou2020Replication`, `Jensen2023Replication`, `McLean2016Predictability` | Replication/positioning | Identity only |
| `Holm1979Sequential`, `Benjamini1995FDR` | Multiplicity, if discussed | Identity only |

Candidate additions **not in references.bib**. Identity checked against
Crossref registry metadata on 2026-10-29 (VERIFIED_METADATA). Their content
was **not** read in this pass; read the primary text before citing for any
specific claim:

| Work | DOI | Why a referee may expect it |
| --- | --- | --- |
| Banz, R. W., and Breen, W. J. (1986). Sample-Dependent Results Using Accounting and Market Data: Some Evidence. *Journal of Finance* 41(4), 779-793 | [10.1111/j.1540-6261.1986.tb04548.x](https://doi.org/10.1111/j.1540-6261.1986.tb04548.x) | Early look-ahead/sample-selection precedent with accounting data |
| Kothari, S. P., Shanken, J., and Sloan, R. G. (1995). Another Look at the Cross-section of Expected Stock Returns. *Journal of Finance* 50(1), 185-224 | [10.1111/j.1540-6261.1995.tb05171.x](https://doi.org/10.1111/j.1540-6261.1995.tb05171.x) | Selection bias in accounting-based return tests |
| Kaufman, S., Rosset, S., Perlich, C., and Stitelman, O. (2012). Leakage in Data Mining: Formulation, Detection, and Avoidance. *ACM TKDD* 6(4) | [10.1145/2382577.2382579](https://doi.org/10.1145/2382577.2382579) | Leakage definition preceding Kapoor–Narayanan |
| Lo, A. W., and MacKinlay, A. C. (1990). Data-Snooping Biases in Tests of Financial Asset Pricing Models. *Review of Financial Studies* 3(3), 431-467 | [10.1093/rfs/3.3.431](https://doi.org/10.1093/rfs/3.3.431) | Data snooping in finance |

Open items carried from FIQ-13: PBO pagination unresolved (unused in the
draft); OpenAlex search assertions unverified; no Borsa Istanbul-specific
empirical literature is cited, which a BIR referee is likely to ask for. No
such BIST citation is proposed here because none was verified in this pass.

## 4. Third-party rights and disclosure

- Charter §5 rule 5: no public redistribution of raw third-party data. The
  draft makes no availability claim, which is correct; a journal data
  statement must not say more than FO-4 establishes.
- The draft names Yahoo `adjclose` as the target source and "the vendor" for
  the original target. Naming the vendor needs the FO-4 record.
- The repository is public; the draft's commit permalinks expose the project
  identity, which conflicts with double-blind review until anonymized.
- The FIQ-16 count uses Borsa Istanbul DataStore Product 3184 evidence already
  in the repository; citing it is a disclosure of source, not redistribution,
  but any table derived from it in the paper should be checked against the
  registration agreement the owner accepted.
