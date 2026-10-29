# Paper 1 reviewer objection matrix

Checked **2026-10-29**, Europe/Zurich, against FIQ-15 candidate
`4b6c88237e38bc240b864b04548eef67bdec5549`. Research support only; not
investment advice. These are anticipated objections written by an agent, not
referee reports, an editorial decision or a forecast of acceptance.

Severity: **H** = a referee could reasonably treat it as disqualifying unless
answered; **M** = likely revision request; **L** = presentation. "Existing
answer" uses only frozen sources; "Fixable now" means fixable by wording from
existing evidence (edit IDs in [editorial_corrections.md](editorial_corrections.md)),
without new analysis.

| # | Objection | Sev. | Existing answer in sources | Residual gap | Fixable now |
| --- | --- | --- | --- | --- | --- |
| R1 | "Your before/after contrast changes timing, return window, return source, rows and features at once; nothing is identified." | H | Draft already says the contrast is bundled and non-causal (REPORT L64-73). | Feature-set change (40 → 38) not listed in the bundle. | Yes: E1, E2. Identification itself is not fixable without a new, registered decomposition. |
| R2 | "The correction was 'registered before outcomes' but designed by people who knew the answer." | H | Amendment §6 states the post-hoc status and lists what was seen. | Draft understates it: the +0.005 and +0.193 sensitivities, price inspection, and near-zero PIT-safe reruns were known. | Yes: E7. Timing of exploratory reruns is G-6. |
| R3 | "The ±25 % jump filter conditions on the outcome path." | H | Draft states it is retrospective row admission; 4 rows. | Rule chosen after daily price inspection (amendment §6). Effect of the 4 rows is not reported in the two sources. | Partly: E9. Effect size would need an authorized sensitivity, not run. |
| R4 | "Your power claim is inconsistent: 80 % at 0.185 analytically, but 17 % detection at 0.2 in the harness." | H | RESULTS reports both; says the harness "can only see large effects". | Not reconciled; α/sidedness of MDE unstated (G-4). | Partly: E5 discloses and stops over-reading 0.185. Reconciliation needs the registered code's own documentation. |
| R5 | "A null on 3 cross-sections of ~78 survivor-selected firms says little." | H | Draft: MDE, survivor-conditioned null is not evidence about U1, "no large edge" wording. | None beyond R4. | Already answered; keep. |
| R6 | "Within-year permutation and ticker bootstrap assume exchangeability; sector/factor dependence inflates size." | M | Draft limitation paragraph. | Wording on "common market shocks" is imprecise for rank IC; negative controls cannot test dependence. | Yes: E6, E10. A dependence-robust test is new analysis (not run). |
| R7 | "Survivorship and 'winner cohort' selection could drive everything; you never measure it." | H | Selection section: mechanism established, effect UNKNOWN, FIQ-17 NOT RUN. | FO-1 provenance incomplete; annual table null; FIQ-17 gated behind both Paper 2 and Study 3 confirmatory openings (addendum OD-7 = B). | No. Scope choice — see [scope_proposal.md](scope_proposal.md). |
| R8 | "The six-month lag is textbook (Fama–French 1992; Banz–Breen 1986). What is new?" | H | Draft positions the paper as an auditable case, not a new principle; cites Fama–French. | Canonical look-ahead/selection precedents (Banz–Breen 1986; Kothari–Shanken–Sloan 1995) absent; ML asset-pricing anchor Gu–Kelly–Xiu 2020 in the bib but uncited. | Partly: add verified references after content reading (see [submission_readiness.md](submission_readiness.md) §3). Contribution framing is an owner choice. |
| R9 | "Single-country, single small panel; external validity?" | M | Draft limitation; nominal-TRY regime. | IAS 29 basis change from FY2023 not discussed. | Yes: E11. |
| R10 | "Locked holdout 2023-2025 was already seen; FY2024 window runs into 2026 and the forward test window." | M | Draft: semi-clean, forward registration exposed. | Window overlap with the 2026 forward window not stated (G-2, G-3). | Yes: E8 (labelled as inferred from the exit rule). |
| R11 | "Statutory deadlines are not filing times; late filers leak." | M | Draft and protocol disclose; 6 exact dates only. | Source also says none found in sample; draft omits that. | Yes: E3. Exact-filing sensitivity is FIQ-18 (not run). |
| R12 | "Market-value counts don't add up." | L | — | 164 + 27 + 5 + 123 = 319 of 323 (G-1). | Disclosure only: E4. Classification needs the frozen report record. |
| R13 | "How many configurations were ever tried on this panel?" | M | Draft: no complete trial-family reconstruction. | Charter §5 rule 6 count unavailable for capstone history (G-7). | Disclosure already present; complete count is FIQ-12 work. |
| R14 | "The 'publication-time vs selection-time' taxonomy is asserted, not tested." | M | Draft: distinct mechanisms needing different evidence. | Only the timing half has numbers. | Framing choice: keep both mechanisms but state that only one is quantified (draft already does). |
| R15 | "Data are not available; repository shows vendor files." | M | Draft: no rights-clearance claim. | Vendor unnamed in sources (G-8); raw third-party files are tracked on public HEAD (context record); FO-4/FIQ-09 open. | No. Owner rights decision before any data statement. |
| R16 | "Was AI used to write this?" | M | — | Elsevier requires a separate AI declaration; Springer Nature requires documentation in Methods; draft has none. | Owner must write the declaration (facts about tool use are the owner's). |
| R17 | "Manuscript is not anonymized for double-blind review." | M | — | Draft names FinanceIQ, commit SHAs, repository paths; JAM uses double-blind review. | Mechanical at submission time; owner choice of venue first. |
| R18 | "Title says information 'arrives too early'; it was used before it arrived." | L | — | Title semantics. | Optional retitle, owner choice (suggestion in editorial_corrections.md). |
| R19 | "Rounded −0.000 and 'Permutation p' header differ from REPORT's 'p'." | L | RESULTS L94-96 uses "Permutation p" for the same values. | None. | No change needed. |
| R20 | "Why only Bonferroni on 6 when you ran 30 ML tests (primary + 4 sensitivities)?" | M | REPORT L47-52 gives 24-test family for sensitivities; registered family is 6. | Primary + sensitivities joint family not reported. | Disclosure already present; any new family-wide adjustment would be a new calculation (not run). |

## Objections deliberately not "fixed"

- No new statistic, interval, family adjustment, decomposition or power
  calculation is added to answer R1, R3, R4, R6 or R20.
- R7 is not answered with an estimate, bound or sign; the placeholder stays
  NOT RUN.
- R15-R17 depend on owner facts and decisions.
