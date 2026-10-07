# FinanceIQ research charter

Adopted 2026-10-07 by the project owner. In force. Where an older rule, plan or
document conflicts with this charter, this charter wins; older documents are
not edited and stay as dated records.

Research support only; not investment advice.

---

## 1. What changed

FinanceIQ began as a university capstone with a fixed scope: a 40-company
public cohort from selected BIST sectors (81 companies with the training-only
set), annual statements and year-end prices, and one question — does a score
built from year-T fundamentals rank companies by their year-T+1 return? The
capstone is complete. The 2026-10-04 publication-lag audit withdrew its
original evidence and replaced it with a point-in-time evaluation
(`RESULTS.md`).

The project now belongs to its author and continues as an **open research
program on Borsa Istanbul equities aimed at peer-reviewed papers**. The
capstone's scope no longer limits what may be studied, which data may be used,
or which models may be trained. What replaces those limits is research
discipline (§5), not a different fence.

## 2. Capstone v1 — frozen record

- **Frozen:** the 40-company public cohort and 81-company training universe
  (`data/config/universe_public_40.csv`, `data/config/universe_training_bist100.csv`),
  the annual T→T+1 dataset and pipeline, the scoring/forecasting/ML code, the
  web application, the original and point-in-time results.
- **Kept runnable and reproducible.** Bug fixes and reproducibility work only;
  no new features. Legacy app surfaces carry the `withdrawn_pre_pit` label
  (`backend/app/core/evidence_status.py`, `frontend/src/components/PreAuditNotice.jsx`).
- **The cohort's selection rule is undocumented** (`docs/universe_audit.md`).
  Its raw source files are labelled a "winner cohort" (`data/raw/README.md`).
  If the 40 were picked or ranked using realised returns, every capstone result
  carries an outcome-selection bias distinct from survivorship. Consequences:
  no new study uses these lists as a research universe; any reuse of capstone
  results states the limitation; Paper 1 measures it (§6).

## 3. Lifted constraints

These capstone rules no longer apply to new research.

| Capstone constraint | Now |
|---|---|
| Fixed 40/81-company cohort from selected sectors | Rule-based point-in-time universe (§4); every sector, with financial firms as their own stratum |
| Annual statements, year-end prices | Quarterly and interim statements at their publication time, daily prices, corporate actions, event windows, macro series at their release time |
| One target: next-year return ranking | Any target declared in the study record before outcomes are inspected: returns at several horizons, abnormal returns around events, volatility and risk, fundamentals, distress, flows |
| The capstone scoring/ML pipeline as "the primary numerical model" | Any model family: linear and regularised, tree ensembles, neural networks, panel and time-series models, causal and econometric estimators, representation learning across data sources |
| Annual expanding-window walk-forward | Any training and validation scheme that respects availability time: purged and embargoed cross-validation, expanding or rolling windows, nested tuning, multi-task or transfer learning |
| Annual fundamentals plus Yahoo-derived valuation | Any information that was public at its use time: fundamentals, prices, corporate actions, macro, flows, disclosure text, embedding- or LLM-derived features (§5, rule 8) |
| Capstone sector and column filters | Any filter declared in the study record before outcomes are inspected. Data-quality rejections (frozen or misaligned vendor columns) still hold until the data is re-sourced |
| Yahoo year-end prices and manual CSVs only | Any free source with an approved rights decision, acquired through the PIT Kernel. Sponsor or bank data only under a separate written agreement |
| Keep every app page wired to the research outputs | The app is frozen (§2); research results do not have to appear in the UI |

## 4. Research universe

**Decision U1 (primary).** Formation dates are the starts of BIST index
periods (quarterly reviews). The universe at a formation date is the set of
BIST 100 constituents for that index period, taken from effective-dated
membership evidence: Borsa Istanbul DataStore Product 3184 (quarterly index
membership per share since 2000; free of charge, account registration
required, manual download only) cross-checked against the periodic review
announcements archived in `docs/evidence/bist_membership_event_sources.csv`.

- **Why quarter boundaries.** Day-by-day membership cannot be rebuilt for
  2017–2023: intra-period changes were not published for the benchmark indices
  before late 2023 (`docs/BIST_MEMBERSHIP_EVENT_COVERAGE_AUDIT.md`). Quarter-
  boundary membership is published with explicit effective dates. Firms that
  leave the index during a quarter are still followed (next point); firms that
  enter during a quarter join at the next review. Both rules are fixed before
  any outcome is seen.
- **Survivor-inclusive.** A firm enters at its index inclusion. Once it is in
  a formation sample, it is followed through the full holding or event window
  even if it leaves the index, is suspended, merges or delists. A delisting is
  an outcome to record, never a reason to drop the firm.
- **Fail closed.** A formation date whose membership cannot be established
  from evidence is excluded and counted, never filled from a later list. A
  current constituent list is never projected backwards.
- **Strata.** Non-financial firms are the primary stratum. Banks, insurers,
  leasing, factoring and brokerage firms use different statement templates and
  form a separate stratum (or are excluded by a rule declared before outcomes).
  Holding companies are flagged.
- **Robustness universe U2.** All Borsa Istanbul-listed equities with KAP
  filings and price data at the formation date, after a liquidity screen
  computed only from data available before that date.
- **Window.** As long as membership evidence, KAP statements and prices allow.
  The universe card in `docs/process/TASKS_FINANCEIQ_2026-10-07.md` fixes it
  from a feasibility count before any outcome is computed.

Why U1: BIST 100 is the liquid core of the market, standard in the literature,
and its quarterly membership is published by Borsa Istanbul free of charge
(`docs/BIST_MEMBERSHIP_P3184_2020_RECONCILIATION.md`: the Product 3184 files
are free; access needs an account and acceptance of a registration agreement,
which is the owner's decision). Index leavers usually stay listed, so their
prices should remain available; the universe card verifies this. Rejected: the
40-company cohort (selection unknown); today's constituent list projected
backwards (survivorship look-ahead); all listed firms as the primary universe
(delisted small caps are largely missing from free price sources).

**Ownership.** The PIT Kernel stores membership intervals, identities, filings
and prices, outcome-blind. FinanceIQ owns the universe rule and applies it to
Kernel snapshots.

## 5. Discipline that replaces the limits

Kept from the capstone:

1. **No fabricated data.** Stored data is never imputed or synthesised;
   missing stays null. A model may handle missing inputs internally only if the
   study record declares the method and it is fitted on training data alone.
2. **Point in time.** Every feature value must have been public at the moment
   it is used. New research takes availability times from PIT Kernel snapshots;
   the legacy pipeline keeps its guards (`make data-validate`).
3. **Kernel blinding.** The PIT Kernel never sees outcomes
   (`NO_NEW_OUTCOME_INSPECTION=true`); data flows one way, Kernel → FinanceIQ.
4. **Claims.** All outward copy is research support, not investment advice.
   The Model Confidence Contract (`model_confidence_contract.json`) governs
   outward claims. A claim that a model has predictive ability needs a
   confirmatory, pre-registered result on the locked holdout (rule 7).
5. **Rights.** No paid data, no secrets in git, no public redistribution of
   raw third-party data, no bypassing authentication, CAPTCHAs, WAFs or rate
   limits. Borsa Istanbul DataStore is manual-download only.

New:

6. **Every trial counts.** Each evaluated configuration — data snapshot hash,
   universe rule version, features, target, model, hyperparameters, seed,
   metric — is appended to an experiment ledger. Results report how many
   configurations were tried, and the multiplicity adjustment uses that count
   (e.g. Holm or Benjamini–Hochberg, White's reality check or Hansen's SPA test,
   deflated performance metrics).
7. **Exploration and confirmation are separate.** The development window is
   open to any exploration. The locked holdout is touched only by a
   pre-registered confirmatory analysis, once. Default boundaries:
   development up to 2022-12-31; locked holdout 2023-01-01 to 2025-12-31;
   forward holdout = everything published after the OSF registration date.
   The 2023–2025 holdout is semi-clean — capstone results on the 40-company
   cohort for those years have been seen — and papers say so; only the forward
   holdout is fully clean. IAS 29 restatement starts with fiscal 2023, so a
   model trained on the development window meets a new measurement basis in
   the holdout; the research protocol must address this (e.g. unit-invariant
   ratios, basis-aware features). The boundaries may move only before any
   model is evaluated on the U1 universe.
8. **LLM-derived features.** Allowed as versioned derived features (model id
   pinned, prompt hash, outputs stored with lineage). A model trained after the
   evaluation period may already know the outcome, so confirmatory use needs a
   model whose training cutoff precedes the evaluation window, or an argument
   that this leakage cannot reach the target; otherwise the feature is
   exploratory only. LLM output is never stored as a source fact.
9. **Process.** One study record before (question, estimand, data and
   cutoffs, analysis plan, multiplicity, stopping rule) and one after (what was
   registered versus post-hoc, results, deviations, limitations) per study.
   Independent review only for analyses that enter a paper. `TASK_STATE.md` and
   `FINANCEIQ_AGENT_TASK_QUEUE.md` are frozen ledgers; no new R3/R4 task IDs.

## 6. Research program

| Study | Question | Status |
|---|---|---|
| Paper 1 — audit | How much do two look-aheads inflate an ML-for-finance evaluation in an emerging market: publication timing (measured by the point-in-time audit) and cohort selection (measured by re-running the frozen capstone design on U1, specification committed before the run)? | Draft can start; selection measurement waits for U1 data |
| Paper 2 — disclosure event study | How do prices react to KAP financial-statement disclosures relative to a pre-specified earnings surprise, and how much of a firm's move is attributable to market, rates, FX and flow factors versus firm-specific news? Did the IAS 29 transition change the relation? | Design, then pre-registration on OSF |
| Study 3 — open modeling | On the U1 quarterly point-in-time panel, does any model family carry out-of-sample information about pre-specified targets after multiplicity adjustment? | Exploration in the development window, then a confirmatory pre-registration |
| Later | Fund-flow pressure; sponsor or bank data; CDS and credit spreads | Deferred |

## 7. What this charter does not change

- No history is deleted; existing pre-registrations stay as dated records.
- The quarantine list stands (Finnhub, news API, synthetic seeders, the legacy
  KAP scraper). New acquisition code lives in the PIT Kernel under per-source
  rights decisions, not in this repository.
- Nothing under `data/trusted/` or `data/trusted_clean/` is hand-edited.

## 8. Superseded decisions

In `docs/process/GAP_CLOSURE_PLAN_2026-10-07.md`: K1 (FinanceIQ frozen as a
product with a narrow research line → open research program, §1), K4 (Kernel v1
= the Paper 2 slice → the U1 slice: membership, identities, filings, statements,
prices, corporate actions, macro), K6 (paper order → §6), K8 (Panel v2 parked
→ superseded by U1), K15 (survivorship left unresolved → U1 rebuild). The
capstone scope in `docs/process/PRD.md` is now the Capstone v1 record.
