# Proposed Paper 1 editorial corrections

Prepared **2026-10-29**, Europe/Zurich. Research support only; not investment
advice.

## How these are delivered

The corrections are a unified diff, [draft_corrections.patch](draft_corrections.patch),
against `docs/paper1/draft.md` at FIQ-15 candidate
`4b6c88237e38bc240b864b04548eef67bdec5549`. **They are not applied** in this
commit, for three reasons:

1. FIQ-15 is an unmerged candidate under its own review; its draft bytes stay
   as delivered.
2. `docs/paper1/draft.pdf` is a ReportLab layout verified against that exact
   text, and its generator is not in the repository. Applying the patch
   without regenerating the PDF would leave a stale reviewed PDF beside it.
3. Every edit is a wording choice the owner may reject one by one.

Apply after review with:

```bash
git apply docs/paper1/readiness/draft_corrections.patch
```

Then regenerate or withdraw `draft.pdf`, and append the change to the FIQ-15
README. `git apply --check` passed against the candidate. The patched draft
keeps all 38 note links, the NOT RUN selection placeholder, every UNKNOWN,
the crosswalk, the chronology and the reference list; it adds no crosswalk
note. Word count changes from 3,996 to 4,401, inside the JAM 3,000-6,000 range
(counting convention still to be checked at submission).

## Rules followed

- Each new sentence cites an existing crosswalk note whose pinned excerpt
  contains the stated fact. A scratch token check confirmed every added
  number, date and phrase against those excerpts (the 31 May cutoff is carried
  by N15).
- No new estimate, test, interval, adjustment, decomposition or count. The one
  arithmetic statement (E4: 319 of 323) sums four reported figures to show a
  gap; it estimates nothing.
- Inferences are worded as inferences ("plausibly anticipated", "under the
  protocol's exit rule").

## Edits

| ID | Location | Change | Source in existing notes | Objection |
| --- | --- | --- | --- | --- |
| E1 | Abstract | Add "admitted feature set" to the bundled changes | P02 (amendment L100: 38 admitted features); N06 (40 columns) | R1 |
| E2 | Protocol, entry-date paragraph | Name the 38-feature admitted set in place of 40 columns | P02; N06 | R1 |
| E3 | Protocol, cutoff paragraph | Add source statement that no late filing was found, and that this is not a census | N26 (RESULTS L125) | R11 |
| E4 | Data, market-value paragraph | State the four categories cover 319 of 323 rows and are not an exhaustive partition | N09 | R12 |
| E5 | Power paragraph | Disclose that the analytic MDE and the harness detection rates are not reconciled; stop reading 0.185 as the smallest reliably detected effect | N23, N24 | R4 |
| E6 | Controls paragraph | Permuted/noise targets cannot reveal dependence-induced size distortion | N24 (design of the controls) | R6 |
| E7 | Registration paragraph | State what was known before registration: +0.005, +0.193, price inspection; exploratory near-zero PIT-safe reruns; direction plausibly anticipated | P02 (amendment §6), N05 (RESULTS L66-68) | R2 |
| E8 | Holdout paragraph | 2026 forward window 31 Dec 2025 → 31 Dec 2026; FY2024 corrected window from 2 June 2025 to the last close on or before the next 31 May cutoff; overlap means added exposure | P02 (amendment L16), N15, N16, P01 (protocol exit rule) | R10 |
| E9 | Jump-exclusion paragraph | Rule registered after daily prices were inspected for one-day jumps | P02 (amendment L75-77) | R3 |
| E10 | Inference paragraph | Replace "sectoral dependence, common market shocks" with sector/factor-correlated shocks incl. heterogeneous exposure to market moves; add few-periods caveat | Methods reasoning (a purely additive common shock leaves within-year ranks unchanged) | R6 |
| E11 | Limitations paragraph | FY2023 first inflation-accounting year; charter dates IAS 29 restatement from fiscal 2023; no basis-specific analysis in the frozen reports | N13 (RESULTS L57-58), G01 (charter L161) | R9 |

## Considered and not proposed

| Item | Reason |
| --- | --- |
| Calling the 20 May 2024 / 10 May 2023 dates "filing" instead of "deadline" | Protocol §3 and amendment §6 confirm they are statutory deadlines. Optional: add P01 next to N13 in that sentence. |
| "Actual-filing-date mode was not run on the full universe" | Protocol §2 uses the same qualifier. |
| "Analytic" MDE and "ticker resampling" | Both confirmed by protocol §8. |
| Adding Gu–Kelly–Xiu 2020, Wolff–Echterling 2024, Petersen 2009, Cameron et al. 2008, Banz–Breen 1986, Kothari–Shanken–Sloan 1995 | Needs new L-notes, content reading and, for the last two, new BibTeX entries. Listed in [submission_readiness.md](submission_readiness.md) §3. |
| Declarations (AI use, data availability, competing interests, funding) | Facts belong to the owner and the venue; see submission_readiness.md. |
| Retitling | Optional owner choice. The title says information "arrives too early"; the defect is that it was used before it arrived. One possible form: "Used before it was public: a reproducible audit of publication timing and survivor selection in Borsa Istanbul equity prediction". |
| Rewording the selection placeholder | It is preserved verbatim by instruction and by design. |
