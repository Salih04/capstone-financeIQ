# Paper 1: BIST literature access record

Checked 2026-11-02, Europe/Zurich. Queue 1; literature only. Research support
only; not investment advice. These sources contextualize the historical audit;
they neither validate FinanceIQ nor establish leakage in another study.

| Key | Primary source and verified location | Permitted manuscript claim | Limits |
| --- | --- | --- | --- |
| Demirel2021BIST | [Journal article](https://dergipark.org.tr/en/pub/gujs/article/679103), Abstract and Cite/APA; DOI 10.35378/gujs.679103 | Demirel, Çam and Ünlü compare MLP, SVM and LSTM for individual-share opening/closing prices in the Istanbul market. | Abstract/metadata verified, not a full methods audit. A price-level forecast is a different target from annual cross-sectional return ranks. No numerical performance is borrowed. |
| Simsek2020Earnings | [Journal article](https://dergipark.org.tr/tr/pub/mbdd/article/700635), Turkish/English abstracts and Kaynak Göster/APA; DOI 10.31460/mbdd.700635 | Şimşek and Yıldırım study earnings-announcement reactions in BIST using an event-study design. | Abstract/metadata verified, not independent replication or full methods review. Event-window reactions do not establish annual predictability. |

Both exact bibliographic identities are added to the manuscript reference list.
The new related-work paragraph deliberately makes only the claims above. It
does not infer PIT validity, transaction-cost robustness or sample-selection
quality from an abstract. No source tables or datasets were downloaded.

Other search candidates were not promoted: Taylor & Francis DOI
10.1080/16081625.2021.2007408 and Elsevier PII S1566014120305872 returned 403
on direct open. Search-indexed publisher text was visible but is not treated as
full-text verification. No access control was bypassed.

## Preparation chronology

Live main at start: `a8f190491ad466c2f92a21b9c3f938f7a5f89be3`.
Manuscript `4b6c88237e38bc240b864b04548eef67bdec5549` and prerequisite
`7b444a35298f7b04012d818ff70fcbc57b85d6b3` were verified pushed in
[PR #62](https://github.com/Salih04/capstone-financeIQ/pull/62), OPEN, not merged.
Main was integrated into an isolated Paper 1 preparation branch, not merged
into main. The existing E1–E11 correction patch was applied to its exact draft;
the old patch and historical readiness records remain unchanged.

The requested status document was absent from live main (404). Its candidate
at `c85ed06e491da07e9d6a5b98701de8064aa65778` in
[PR #61](https://github.com/Salih04/capstone-financeIQ/pull/61) was read as
dated evidence: its local-only manuscript claim, unstarted FIQ-09 claim and
20-gate summary are superseded by live PR #62, merged PR #60 and the 25-row
Paper 2 audit. No PR #61 Kernel planning text was adopted or edited here.
The latest owner message controls the settled price-source and tier-cell rules.

Prior exposure: existing capstone aggregates, manuscript and correction patch,
project context and prior chat were read. No zero-exposure claim. No audit draw,
source retrieval for comparison, protected-data access or new analysis occurred.

## CI delivery amendment — 2026-11-03

The original PR #62 head `9eb0c3cc` triggered 18 `generic-api-key` matches
in bibliographic JSON `key` values under gitleaks 8.30.1. The current delivery
clarifies that field as `citation_id` for all 40 entries. Exact JSON comparison
confirmed every bibliographic value and historical verification field unchanged;
no 2026-10-27 verification is represented as rerun. The original JSON and commits
remain immutable at the already pushed source refs. No scanner exception,
allowlist, workflow edit, forced ref update or history rewrite is used.

A fresh-main delivery avoids replaying the ambiguous-field source commits into
the new-commit scanner. It incorporates their document contents with this schema
clarification, preserving original commit IDs above as provenance rather than
claiming byte identity or direct ancestry. PR #62 is retained as the superseded
discussion/history; the successor's PR and CI are the acceptance surface.
