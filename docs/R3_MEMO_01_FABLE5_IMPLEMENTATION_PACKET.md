# R3-MEMO-01 — Fable 5 implementation and independent-review packet

Frozen 2026-07-18 by a Fable 5 packet-authoring session. This document is the
single authoritative specification for implementing and independently reviewing
R3-MEMO-01, the claim-aware research memo compiler. It supersedes the shorter
R3-MEMO-01 entry in `FINANCEIQ_AGENT_TASK_QUEUE.md` wherever the two disagree;
the audited differences are recorded in §3 with repository evidence.

Labels used throughout: **VERIFIED FACT** (checked against the repository this
session), **DESIGN DECISION** (frozen by this packet), **RECOMMENDATION**
(strong preference, owner may override by editing this packet before
implementation), **OWNER DECISION** (genuinely unresolved; implementation must
not proceed past it without the owner's answer).

---

## 1. Packet status and authority

- Status: **FROZEN**. The implementation agent executes this packet mechanically
  and stops on any condition in §23. It does not re-derive product decisions.
- Authority chain for claims: `model_confidence_contract.json` (v1.8.0 at
  freeze) → `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md` → `METHODOLOGY.md`. Nothing in
  this packet weakens the committed conclusion: **no reliable predictive edge
  was established.**
- This packet is documentation only. Authoring it changed exactly one file:
  `docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md`. No application code, test,
  artifact, dataset, contract, registry, queue, or TASK_STATE file was modified.
- The implementation and review prompts (§27, §28) are self-contained and do not
  depend on the conversation that produced this packet.

## 2. Repository verification (packet-authoring session, 2026-07-18)

All VERIFIED FACT:

- Worktree: `.claude/worktrees/r3-memo-01-packet-freeze-ed3408` (harness-suffixed
  variant of the planned `r3-memo-01-packet-freeze` label; suffix accepted).
- Branch: `local/r3-memo-01-packet-freeze-ed3408`.
- HEAD: `541024207bc38594ed6fca65b16d02baed86c44e` — identical to `main`.
- The GOV-02 governance truth-sync commit ("Close reviews and sync governance
  truth") is HEAD itself.
- Working tree clean at start and at packet freeze (only this file added).
- `make docs-lint`: PASSED at the starting state.
- `make claims-lint`: PASSED — Model Confidence Contract **v1.8.0** satisfied.
- Suite/data baselines: see `docs/VERIFICATION_BASELINE.md` (dated 2026-07-18,
  observed at the GOV-02 pre-commit state); both suites green, data VALID.

## 3. Current R3-MEMO-01 plan reconstruction and audit

The current plan lives in `FINANCEIQ_AGENT_TASK_QUEUE.md` §"R3-MEMO-01 —
Claim-aware research memo compiler" and `FINANCEIQ_PHASE3_4_FRONTIER_PLAN.md`
§C-26. Reconstruction and per-element disposition:

| Plan element (queue/frontier text) | Disposition | Evidence and reasoning |
|---|---|---|
| Goal: deterministic, citation-complete per-ticker memo composing committed evidence; "a composed memo is the closest this product ever comes to looking like advice" | **KEEP** | Matches product boundary §4. |
| Route `POST /research/memo/{ticker}` | **REWRITE → `GET /research/memo/{ticker}`** | The only POST evidence route, `POST /research/courtroom` (`backend/app/routers/research.py`), is POST because it takes a body (`ticker`, optional `year`). The memo takes no body and is read-only and cacheable; the closest precedent is `GET /research/skeptic/{ticker}`. A body-less POST would be the inconsistent pattern. |
| New `backend/app/services/memo_service.py` (proposed) | **KEEP** | Consistent with `skeptic_service.py`/`courtroom_service.py` placement for cross-artifact composition services (the `services/research/` subpackage holds single-artifact passthroughs). |
| Section order: Identity & coverage → Evidence quality → Skeptic verbatim → Significance & power → Limitations → Provenance stamp | **KEEP + NARROW additions** | Order kept. Since the queue entry was written, four additional committed claim surfaces became mandatory context (serving evaluation, return basis, regime, calibration — all committed and reviewed at HEAD). §13 freezes the full order. |
| Provenance stamp includes "generation timestamp" | **REWRITE** | A wall-clock timestamp defeats byte-determinism (§15). Provenance is source-artifact checksums + MCC version + schema version; no wall-clock field. |
| "Optional LLM mode may only rephrase grounded bullets" | **REMOVE (excluded entirely from R3-MEMO-01)** | The core memo must be deterministic with all LLM providers disabled. No repository evidence makes an LLM renderer necessary: the courtroom already demonstrated a fully deterministic citation-complete surface, and `research_agent.py` LLM paths are separate. Excluding the LLM removes an entire class of uncited-claim risk. Reintroduction is a separate future task with its own packet. |
| "Reuse/extract the courtroom's resolution helper into a shared module both services import" | **NARROW** | The citation machinery is implemented inside `backend/app/services/memo_service.py` (proposed) for this task. Refactoring `courtroom_service.py` — an approved, committed, test-pinned claim surface — is not required for memo correctness and would widen the diff into a protected surface. Extracting a shared module is deferred to a future refactor task. |
| Export path / exported markdown files | **REMOVE (deferred)** | The queue already made export conditional. §5 lists it as a non-goal. The deterministic markdown *response format* in §8 is not a file export. |
| "No new page here" / optional thin frontend trigger deferred | **KEEP** | No frontend change of any kind in this task (§5, §17). |
| Dependency "R3-MEMO-01 after R3-UI-01 (shared skeptic surface conventions)" | **REWRITE (dependency void for this scope)** | VERIFIED FACT: R3-UI-01, R3-UI-03, and R3-LIMITS-01 have no implementation evidence in the queue, no TASK_STATE rows, and their expected files are absent (no skeptic panel in `frontend/src/pages/`, no `backend/app/services/research/calibration.py`, no `docs/limitations_register.md`). The UI-01 ordering existed to share *frontend* skeptic conventions; this task has no frontend scope, so the gate does not bind. Consequences frozen: limitations come from per-report `limitations` arrays (the queue's own fallback), and calibration evidence is read directly from the committed `experiments/results/calibration_report.json` (no dependency on the unbuilt passthrough). |
| Closing line verbatim: "Composed from committed research artifacts. No part of this memo is a recommendation; the underlying evaluation found no reliable predictive edge." | **KEEP (mandatory, verbatim)** | §11. |
| Acceptance: LLM-off memo for ASELS + one sparse ticker; citation-completeness, key-absence, insufficient-data tests; MCC bump; Fable review | **KEEP + expanded** | §20–§22. Sparse ticker fixed to DSTKF (§21, verified sparsest public ticker). |
| Memos are responses, not committed files | **KEEP** | §5, §15. |

## 4. Binding product purpose

DESIGN DECISION (all binding):

- The memo is an **evidence memo**: a deterministic, citation-complete,
  claim-bounded composition of already-committed research evidence for one
  public-cohort company. It summarizes what the repository measured; it never
  decides, suggests, scores, ranks, rates, or recommends anything.
- The memo's first content is the research boundary, not any company fact.
- The memo is fully available and correct with every LLM provider disabled
  (`RESEARCH_LLM_PROVIDER=none`). There is no LLM involvement anywhere in the
  memo path.
- Every numerical or factual statement resolves to structured citations into
  committed machine-readable artifacts or existing backend evidence services.
- The memo presents contradictory-looking evidence as explicit tension; it never
  resolves tension into a conclusion of its own.
- The committed conclusion the memo must always preserve, verbatim where
  quoted: **"No ML model is statistically distinguishable from the within-year
  null after Bonferroni correction; the data do not support a reliable
  predictive edge."** (`experiments/results/significance_report.json`
  `headline.conclusion`.)

The memo must never present the repository as establishing: alpha; validated
forecasting skill; a profitable strategy; investment value; a contrarian
opportunity; a company recommendation; buy/sell/hold guidance; portfolio
allocation advice; expected future performance; price targets; strategy
performance; commercial readiness; deployment validity; regime robustness; or
calibrated predictive confidence.

## 5. Explicit non-goals (all excluded from R3-MEMO-01)

PDF export; downloadable report export; email delivery; frontend trigger; new
frontend page; any frontend change; memo history; persistence of any memo;
asynchronous jobs; scheduled generation; multi-company batch reports;
user-editable assumptions; interactive scenario controls; client-side
composition; client-side statistics; new statistical experiments; artifact
regeneration; new predictive models; database schema changes or migrations;
sector analysis of any kind; price targets; portfolio actions; any LLM
involvement; company score or rank display (§26 OD-1); the 2022 return-basis
illustration (§26 OD-4); courtroom bull/bear persona content; friction/autopsy
exhibits; dissent-ledger content; disagreement/influence/rank-stability/placebo
/forward-2026 artifacts (§6 exclusions).

No repository evidence makes any excluded item an unavoidable dependency
(VERIFIED: the memo composes only committed files and existing read-only
services; nothing in §16 requires generation, persistence, or UI). If the
implementation discovers otherwise, that is a §23 stop condition, not a scope
expansion.

## 6. Evidence inventory

Legend: canonical = generated by the pipeline/harness with a registry owner in
`artifact_registry.json`; service = existing backend read-only evidence service.
"Safe to quote" always means "verbatim, with the pairing/boundary rules in
§11–§13"; nothing here is safe to excerpt without its boundary copy.

### Included evidence

| # | Logical name | Source (path/service) | Fields used | Status/owner | Scope | Unavailable semantics | Reason for inclusion |
|---|---|---|---|---|---|---|---|
| E1 | Company identity & context | `data/trusted_clean/company_contexts/<TICKER>_<YEAR>.json` (latest year, courtroom `_context_path` convention) | `ticker`, `year`, `universe`, `data_quality.missing_fields`, `data_quality.warnings` | canonical; `make build-company-contexts` | company | 404 if no context/public row exists for the ticker (§14) | Identity anchor; the only company-specific descriptive block |
| E2 | Data-quality frame | `data/trusted_clean/data_quality_report.json` | `feature_columns`, `n_features`, `frozen_feature_columns_remaining`, `rejected_old_snapshot_columns` (names/counts only) | canonical; `make data-validate` | global | 503 (§14) | Grounds "what data exists" without recomputing coverage |
| E3 | Feature-passport lineage | `backend/app/services/research/feature_passports.py` `payload()` | passport count; count of `source_class == "unknown"` (len-only, no arithmetic) | service over canonical | global | 503 (service raises `FeaturePassportsMissing`) | Provenance summary; footer copy already frozen by R2-LINEAGE-01 |
| E4 | Skeptic challenge report | `backend/app/services/skeptic_service.py` `skeptic_report(ticker)` | entire response verbatim (`ticker`, `checks[]`, `footer`) | service over canonical | company + global | per-check `insufficient_data` verdicts pass through verbatim; service `ValueError` → 422 | The queue mandates verbatim embedding; already citation-structured (`fact`/`source_file`) |
| E5 | Six-model significance & power | `backend/app/services/research/significance.py` `payload()` | `headline` (verbatim), per-ML-model `pooled.observed_ic` + `pooled.permutation_p_value_two_sided` + `pooled.bonferroni_adjusted_p_value` + `pooled.significant_fwer_0_05`, `power_analysis.designs` detectable-IC values, `limitations` | service over canonical (`experiments/results/significance_report.json`) | global | 503 (`SignificanceReportMissing`) | The central claim boundary; raw+adjusted pairing is structural in the source |
| E6 | Serving-heuristic evaluation | `experiments/results_serving_eval/serving_eval_report.json` (direct read; no service exists) | `serving_result.conclusion` (verbatim), `serving_result.test_label` (verbatim), `serving_result.pooled_ic`, `serving_result.raw_permutation_p_value_two_sided`, `limitations` | canonical; `make research-serving-eval`; reviewed APPROVED 2026-07-18 | global | 503 | The surface users actually see, measured; outside-family framing is mandatory context |
| E7 | Return-basis evidence | `backend/app/services/research/real_terms.py` `payload()` | `caveat` (verbatim), `conclusion` (verbatim), `bases[]` (basis_id, selected_model, pooled_ic, raw_p_value, adjusted_p_value, significant_fwer_0_05) | service composing four canonical reports, with built-in cross-check refusal | global | 503 (`ReturnBasisReportMissing`, including on cross-report disagreement) | Basis sensitivity without the excluded 2022 illustration; raw/adjusted structurally inseparable in the source |
| E8 | Regime context | `backend/app/services/research/regime.py` `payload()` | `statement` (verbatim), `conditional_diagnostics.status` + `.reason` | service over canonical (`experiments/results_regime/regime_context_report.json`) | global | 503 (`RegimeContextReportMissing`) | Makes "one macro regime; robustness untested" explicit |
| E9 | Calibration finding | `experiments/results/calibration_report.json` (direct read; no service exists — R3-UI-03 unbuilt) | `calibration.verdict` (verbatim), `claim_safety.statement` (verbatim), `limitations` | canonical; `make research-calibration` | global | 503 | Prevents the confidence-as-probability misreading |
| E10 | Limitations union | `limitations[]` arrays of E5, E6, E8, and E9. The return-basis comparison report does not carry a `limitations` array; basis-sensitivity caveats are carried by the mandatory §11 `return_basis` boundary instead. | verbatim entries, path-then-index ordered | canonical | global | each missing array collapses to that report's 503 above | The queue's fallback while `docs/limitations_register.md` does not exist |
| E11 | MCC evidence state | `model_confidence_contract.json` | `version`, `evidence_state.conclusion`, `evidence_state.reliable_predictive_edge_observed` | hand-curated, reviewed | global | 503; **refuse (503) if `reliable_predictive_edge_observed` is not `false`** — the memo may not be generated under a changed evidence state without a new review | Binds the memo to the governed claim boundary |

### Excluded evidence (exclusion is binding for v1)

| Candidate | Why excluded |
|---|---|
| Company fundamental/market score, `score_rank`, hybrid research score (`backend/app/services/research/scoring.py`, `company.py`, `research_agent.py`) | §26 OD-1, RECOMMENDATION frozen as exclusion: a score headline is the single largest composition risk (score next to null-consistent significance reads as a graded pick). VERIFIED: the queue's own binding section list for the memo contains no score section. |
| `research_agent.generate_company_insight` (`GET /research/company/{ticker}/score`) | VERIFIED FACT: its response includes a `decision_support_verdict` field — recommendation-shaped by name. Structurally banned from the memo path (§16, §10). |
| Courtroom bull/bear personas | Rhetorical best/worst framings are argument, not evidence; the memo embeds the skeptic report directly. Courtroom remains its own surface. |
| Friction report (`experiments/results/friction_report.json`) | Basket/turnover/cost numbers are the most strategy-performance-shaped values in the repository; in a per-company memo they read as strategy results. Autopsy panel already displays them with in-drawing stamps. |
| Autopsy exhibit CSVs | Chart-shaped bulk rows; add volume, not per-company interpretation. |
| Dissent ledger (`analyst_verdicts`) | DB-backed and mutable: any inclusion breaks byte-determinism at fixed HEAD and imports human verdict language into a machine memo. |
| Disagreement / influence / rank-stability / placebo / forward-2026 artifacts | Global diagnostics (or pre-registered future evaluation) whose per-ticker excerpts invite pick-confidence readings ("frequently top-ranked") the sources themselves warn against. |
| 2022 nominal-vs-real illustration | §26 OD-4, frozen exclusion: global inflation illustration, already surfaced with its qualifier on BenchmarkPage; adjacent to company facts it reads as company context. |
| Macro series values (CPI, USDTRY, policy rate) | Regime `statement` carries the interpretation; raw macro values next to one company imply macro-company causation. |
| Sector anything | VERIFIED: `sector` is unpopulated in all trusted datasets (METHODOLOGY §Sector-label provenance); legacy DB sector paths have unresolved provenance (`docs/LEGACY_DB_PATH_AUDIT.md`). Sector remains **unavailable**, never approximated. |

## 7. Canonical evidence hierarchy

DESIGN DECISION — conflict resolution for memo generation, highest authority
first:

1. Committed machine-readable research artifacts (registry-owned files under
   `experiments/results*/` and `data/trusted_clean/`).
2. Existing backend read-only passthrough/composition services (they add
   refusal/validation, never new values).
3. `model_confidence_contract.json` (claim boundary and evidence state).
4. `METHODOLOGY.md` (interpretation authority for authored copy only).
5. Feature-passport and trusted-data reports (lineage facts).
6. Task and handoff documents (never citable by the memo).
7. Frontend fallbacks (never citable; never read).
8. LLM prose (does not exist in this task; never citable).

Conflict rule: if two sources at any level disagree about a value the memo
would render (e.g., a service-composed number vs. the underlying artifact, or
`real_terms` cross-check failure, or MCC evidence state vs. significance
headline), the memo service **refuses with 503** and names both sources in the
error detail. It never selects the more convenient value, never averages, never
falls back to the older value. Honest failure beats plausible output.

## 8. Frozen API and schema

DESIGN DECISION.

**Route:** `GET /research/memo/{ticker}` in `backend/app/routers/research.py`,
dependency `require_access` (read-open under `PUBLIC_DEMO_MODE`, same as every
other research route). Optional query parameter `format` with values `json`
(default) and `markdown`. `format=markdown` returns `text/markdown` produced by
the deterministic renderer in §16 — a pure function of the exact JSON payload,
no additional content. No other parameters. No POST, no body, no year
parameter (latest context year is used, courtroom convention).

**Response schema `financeiq.memo.v1`** (concrete shape; field-by-field rules
in the table below):

```json
{
  "task": "R3-MEMO-01",
  "schema_version": 1,
  "memo_type": "evidence_memo",
  "ticker": "ASELS",
  "company_year": 2025,
  "headline": "<MEMO_HEADLINE §11, verbatim>",
  "research_boundary": "<RESEARCH_BOUNDARY §11, verbatim>",
  "disclaimer": "<PRIMARY_DISCLAIMER §11, verbatim>",
  "evidence_status": "complete | partial",
  "unavailable_sections": [
    {"section_id": "…", "reason": "…", "source_file": "…"}
  ],
  "sections": [
    {
      "section_id": "identity_and_coverage",
      "title": "<frozen §13>",
      "status": "available | insufficient_data",
      "boundary": "<frozen boundary copy §11, verbatim>",
      "statements": [
        {"text": "…", "citation_ids": ["C001"]}
      ],
      "missing_evidence": []
    }
  ],
  "skeptic_report": { "…entire skeptic_service.skeptic_report(ticker) response, verbatim…" },
  "citations": [
    {
      "citation_id": "C001",
      "evidence_family": "company_context",
      "source_artifact": "data/trusted_clean/company_contexts/ASELS_2025.json",
      "field_path": "data_quality.missing_fields",
      "value": [],
      "scope": "company",
      "sha256": "<hex of the source file bytes>",
      "label": "Validated company context, ASELS 2025"
    }
  ],
  "source_artifacts": [
    {"path": "experiments/results/significance_report.json", "sha256": "…"}
  ],
  "claim_safety": {
    "statement": "<CLOSING §11, verbatim>",
    "investment_value_established": false,
    "reliable_predictive_edge_established": false
  },
  "closing": "<CLOSING §11, verbatim>",
  "mcc": {"version": "<read from model_confidence_contract.json>",
          "conclusion": "no reliable predictive edge"}
}
```

## 9. Allowed-key register

Every key of the response, exhaustively. Type / required / authoritative source
/ unavailable behavior / claim-safety rationale:

| Key | Type | Req | Source | Unavailable behavior | Rationale |
|---|---|---|---|---|---|
| `task` | const `"R3-MEMO-01"` | yes | packet | n/a | Report-precedent task stamp |
| `schema_version` | const `1` | yes | packet | n/a | Version pin for contract tests |
| `memo_type` | const `"evidence_memo"` | yes | packet | n/a | Names the product boundary in-band |
| `ticker` | string (validated `[A-Z0-9.]{1,16}`) | yes | request | 422 on malformed | Skeptic precedent |
| `company_year` | int | yes | latest company-context `year` | 404 if none | Identity anchor |
| `headline` | const string §11 | yes | packet | n/a | One fixed headline for every company (§11) |
| `research_boundary` | const string §11 | yes | packet | n/a | Boundary before any fact |
| `disclaimer` | const string §11 | yes | MCC `approved_wording.primary_disclaimer` | 503 if MCC unreadable | Product-wide primary disclaimer |
| `evidence_status` | `"complete"`/`"partial"` | yes | computed from section statuses | n/a | `partial` whenever any section is `insufficient_data` |
| `unavailable_sections` | array | yes (may be empty) | computed | n/a | Missing evidence is named, never silently dropped |
| `sections` | array, fixed order §13, all nine always present | yes | composition | per-section `insufficient_data` | Order is a claim-safety control |
| `sections[].section_id`,`title`,`status`,`boundary`,`statements`,`missing_evidence` | per §8 | yes | packet + composition | `insufficient_data` + `missing_evidence` populated | Statements carry citation ids; boundaries are frozen copy |
| `skeptic_report` | object | yes | `skeptic_service.skeptic_report` verbatim | per-check `insufficient_data` inside | Verbatim embedding, queue-mandated |
| `citations` | array of citation objects §12 | yes | composition | resolution failure → owning section `insufficient_data` | Citation completeness |
| `source_artifacts` | array `{path, sha256}` | yes | file bytes at load | 503 if a required artifact is unreadable | Evidence vintage without wall-clock |
| `claim_safety` | object (three keys above, exactly) | yes | packet + MCC | 503 if MCC state conflicts (§6 E11) | Explicit-negation booleans, serving-report precedent |
| `closing` | const string §11 | yes | packet | n/a | Queue-mandated, non-optional |
| `mcc` | `{version, conclusion}` | yes | `model_confidence_contract.json` | 503 | Binds memo to governed conclusion |

No other key may appear at any level except inside `skeptic_report` (whose keys
are the skeptic service's own) and inside cited `value` fields (verbatim
artifact values). A schema contract test pins the exact top-level key set.

## 10. Forbidden-key register

DESIGN DECISION. The following keys must not appear **anywhere** in the memo
response at any nesting depth (Except inside citation value payloads, which are
verbatim scalar or list copies of already-reviewed artifact values. The
`skeptic_report` subtree has exactly one documented exemption: each embedded
skeptic check carries a `verdict` key whose value is the check-status enum
`pass`, `warn`, or `insufficient_data`. This is a method-status verdict frozen
by R2-SKEPTIC-01, not an investment verdict. The key-absence test must assert
that no other key from either forbidden register appears anywhere in the
`skeptic_report` subtree and that every `verdict` value in that subtree is one
of `pass`, `warn`, or `insufficient_data`.):

`verdict`, `recommendation`, `action`, `buy`, `sell`, `hold`, `increase`,
`reduce`, `price_target`, `target_price`, `expected_return`, `upside`,
`downside`, `opportunity`, `conviction`, `investment_value`, `strategy_return`,
`portfolio_weight`, `allocation`, `risk_reward`, `outperform`, `underperform`,
`fair_value`, `forecast_probability`, `success_probability`.

Semantically equivalent aliases are equally forbidden, including but not
limited to: `rating`, `grade`, `outlook`, `signal`, `signal_strength`, `pick`,
`top_pick`, `overweight`, `underweight`, `position`, `entry`, `exit`,
`stop_loss`, `take_profit`, `alpha`, `edge`, `attractiveness`, `score`,
`rank`, `decision_support_verdict`, `advice`, `call`, `stance`, `thesis`.

Notes: `score`/`rank` are forbidden as memo keys because the memo excludes the
score surface (§6); `investment_value_established` and
`reliable_predictive_edge_established` in `claim_safety` are allowed exact keys
(explicit-negation booleans, serving-report precedent) and are not aliases of
the forbidden bare keys. Enforcement is by **recursive key-absence tests over
the real composed response** (exact-name match on the first list, exact-name
match on the alias list), not only by vocabulary lint (§20 T2). The
`skeptic_report` subtree is scanned with the same test.

## 11. Mandatory backend-owned copy (exact strings)

All constants live in `backend/app/services/memo_service.py` (proposed).
Changing any string requires editing this packet first.

- `MEMO_HEADLINE` (the only headline; identical for every company, every
  evidence state — availability may vary, the headline may not):
  > Research evidence memo — research support only, NOT investment advice. The committed conclusion is unchanged: no reliable predictive edge was established.
- `RESEARCH_BOUNDARY`:
  > This memo composes committed, historical research evidence for one company. It contains no recommendation, no forecast, no price target, and no investment-value assessment. Walk-forward evaluation found no reliable predictive edge: no ML model is statistically distinguishable from the within-year null after family-wise correction.
- `PRIMARY_DISCLAIMER` — must byte-equal MCC `approved_wording.primary_disclaimer`:
  > Experimental ranking signal — research support only, NOT investment advice. Do not use for buy/sell/hold decisions.
- `CLOSING` (queue-mandated, verbatim, non-optional, rendered last):
  > Composed from committed research artifacts. No part of this memo is a recommendation; the underlying evaluation found no reliable predictive edge.
- Section boundary strings (each rendered inside its section, never collapsed):
  - `identity_and_coverage`: > Descriptive historical identity and coverage only; inclusion in this memo is not a selection, endorsement, or ranking.
  - `evidence_quality` (byte-equal to the R2-LINEAGE-01 footer): > Provenance record — documents source and validation path, not a guarantee of source accuracy.
  - `skeptic_challenge`: the skeptic service's own `footer` field, verbatim (already frozen by R2-SKEPTIC-01; the memo re-renders it, it does not restate it).
  - `significance_and_power`: > Raw p-values appear only together with their Bonferroni-adjusted values. Detectable-IC thresholds are design limits, not estimates of the true IC.
  - `serving_evaluation` (byte-equal to the report's `serving_result.test_label`): > single prespecified test, outside the six-model Bonferroni family
  - `return_basis` (byte-equal to `real_terms.PANEL_CAVEAT`): > The no-reliable-edge conclusion was re-evaluated separately on CPI-deflated TRY and USD bases; neither survives family-wise correction. Basis changes the unit of measurement, not the conclusion.
  - `regime_context` (byte-equal to the regime report `statement`): > 2020–2025 spans a single extraordinary Turkish macro regime (high inflation, deep TRY depreciation). Model behavior across regimes is therefore untested — this lens shows regime context and will only compute regime-conditional diagnostics when regime diversity exists.
  - `calibration` (byte-equal to the calibration report `claim_safety.statement`): > Diagnostic only: confidence is not a probability of return, profit, or success; it is not recommendation strength and does not establish validated predictive reliability.
  - `limitations`: > Limitations are reproduced verbatim from their source reports; none is optional and the strongest caveat is never summarized away.

Copy principles enforced by tests (§20): the memo begins with the research
boundary; no raw p renders without its adjusted companion or, for the serving
result, its outside-family label; negative IC is never framed as inverse
opportunity; confidence is never a probability of success; basis results are
measurement sensitivity; regime robustness explicitly not established; sector
remains unavailable; missing stays null; the closing denies recommendation and
investment-value status.

## 12. Citation contract

DESIGN DECISION.

Citation object (every field required unless noted):

```json
{
  "citation_id": "C007",
  "evidence_family": "significance | serving_eval | return_basis | regime | calibration | company_context | data_quality | feature_passports | skeptic | mcc",
  "source_artifact": "repo-relative path (or 'backend/app/services/skeptic_service.py' for embedded service output, skeptic/courtroom precedent)",
  "field_path": "dotted JSON path into the source, e.g. headline.observed_ic",
  "value": "<the exact source value, verbatim, unrounded>",
  "scope": "company | global",
  "sha256": "hex digest of the source file bytes (omitted only for the service-source skeptic citations, whose underlying artifacts are cited inside the embedded report)",
  "label": "human-readable one-line label"
}
```

Rules (each pinned by a §20 test):

1. Every statement `text` containing a number or a factual assertion carries at
   least one `citation_ids` entry, and every id resolves to a `citations`
   element (T5).
2. Citation resolution is by **value**, not path: at composition time the
   service re-reads `field_path` from the loaded source and asserts equality
   with `value`; mismatch makes the owning section `insufficient_data`, never a
   silently retained claim (T6, T7).
3. No citation to frontend constants, to LLM output (none exists), to a handoff
   document, or to any file outside §6's inventory.
4. `METHODOLOGY.md` citations are **not permitted** in the memo: every included
   value has a structured home (VERIFIED in §6); authored copy is packet-owned,
   not cited. (This is deliberately narrower than the mission's allowance —
   nothing in the frozen inventory needs a METHODOLOGY citation.)
5. No invented citation; a citation that fails to resolve may never be dropped
   while its statement survives — statement and citation live or die together.
6. Global evidence carries `scope: "global"`; company-specific carries
   `scope: "company"`. The markdown renderer prints "(repository-level
   evidence)" after every global-scope statement in company sections; the JSON
   scope field is the machine-readable equivalent (T25 checks the rendering).
7. Ids are `C001…Cnnn` in order of first use within the fixed section order —
   deterministic by construction.
8. The response returns **both** full citation objects and per-statement id
   references (decision: both; a registry alone would force clients to join,
   and inline-only would duplicate checksums).

## 13. Composition and ordering rules

DESIGN DECISION — fixed section order (ids and titles frozen):

1. `identity_and_coverage` — "Company identity and data coverage"
2. `evidence_quality` — "Evidence quality and lineage"
3. `skeptic_challenge` — "Skeptic challenge report" (embedded verbatim)
4. `significance_and_power` — "Model-family significance and power"
5. `serving_evaluation` — "Serving-heuristic walk-forward evaluation"
6. `return_basis` — "Return-basis sensitivity"
7. `regime_context` — "Macro-regime context"
8. `calibration` — "Confidence calibration finding"
9. `limitations` — "Limitations (verbatim from source reports)"

Then `closing`. The order runs boundary-first, company-facts early,
repository-level nulls after, limitations last-but-one, closing last — so no
company fact is ever the last word.

Compositional risk controls (each maps to §24 scenarios and §20 tests):

- No score/rank exists anywhere (kills score-next-to-null-significance and
  rank-next-to-prose risks at the schema level).
- Global vs company scope is labeled per citation and rendered per statement
  (kills global-evidence-as-company-evidence).
- Every historical descriptive statement in `identity_and_coverage` uses the
  frozen boundary sentence; templates must use past-tense descriptive wording
  ("was", "recorded"), never predictive wording.
- The serving IC (positive 0.050) and family ICs (negative) appear in separate
  sections each with its own framing; no statement compares them.
- No statement adjacency may imply endorsement: statements within a section are
  rendered in citation order with their boundary visible; the hostile-editor
  review (§28) reads the full rendered memo for adjacency effects.
- Contradiction display: if sources conflict, §7 refuses; if evidence is merely
  in tension (e.g., full coverage next to null-consistent significance), both
  statements render with their boundaries — the memo never adds a reconciling
  sentence.

## 14. Unavailable and insufficient-data semantics

DESIGN DECISION — exhaustive mapping:

| Condition | Behavior |
|---|---|
| Malformed ticker (fails `[A-Z0-9.]{1,16}` after strip/upper) | **422** (skeptic precedent) |
| Well-formed ticker with no company context and no public-dataset row | **404**, detail names the missing context path (matches `/research/company` 404 precedent for unknown tickers) |
| Ticker outside public cohort but inside training universe | **404** (same as above — the memo serves the public cohort only; training-only tickers have no company context) |
| Company context exists but is malformed / identity mismatch | **200**, `evidence_status: "partial"`, `identity_and_coverage` → `insufficient_data` with `missing_evidence` naming the file (courtroom precedent), remaining sections unaffected |
| Partial feature coverage / missing fields on the company row | **200**, statements render the nulls explicitly ("null"/"unavailable"); never zero, never empty-string, never a neutral placeholder value |
| Ticker absent from prediction dumps (skeptic instability probe) | pass-through: the embedded skeptic check is `insufficient_data`, memo stays 200 |
| Missing/malformed global artifact: significance report, serving report, return-basis reports, regime report, calibration report, data-quality report, passports, MCC | **503** with the loader's message (research-loader precedent). A broken install must not produce a plausible partial memo |
| Missing adjusted p-value in any six-model entry | **503** (the significance loader already refuses; the memo adds its own guard — T11) |
| Missing raw p or `test_label` in the serving report | **503** — the serving number may never render without its outside-family label |
| Artifact cross-check disagreement (`real_terms` comparison mismatch; citation value-resolution mismatch on a global artifact; MCC `reliable_predictive_edge_observed` ≠ false; significance headline `significant_fwer_0_05` ≠ false) | **503**, both sources named (§7) |
| Malformed citation at composition time (company-scoped) | owning section `insufficient_data`, memo 200 partial |
| Calibration/regime/basis evidence present but missing the exact verbatim fields of §11 | **503** (the frozen copy is byte-pinned to source fields; drift means the artifact changed and needs re-review) |
| LLM unavailable | not applicable — no LLM in the path |

HTTP 409 is deliberately unused: the repository's refusal precedent maps every
inconsistency to 503 (`real_terms`), and one refusal semantic is easier to test
and harder to mishandle. No exception is ever converted into a
plausible-looking memo; no default value substitutes for missing evidence.

## 15. Determinism contract

DESIGN DECISION.

- **Byte-identical requirement:** two calls to `GET /research/memo/{ticker}`
  (both formats) at the same HEAD with unchanged artifacts return byte-identical
  bodies. Pinned by test (T18) for both fixtures.
- No wall-clock timestamp anywhere in the response. Evidence vintage is the
  `source_artifacts` checksum list — it changes exactly when the evidence
  changes. (This resolves the queue's "generation timestamp" — see §3.)
- No git subprocess calls; no environment-dependent values; no dict-ordering
  hazards (composition uses fixed literal orders); JSON serialization via
  FastAPI defaults (stable for fixed input).
- Section order, statement order, citation order, limitation order (source path,
  then array index), and `source_artifacts` order (fixed literal list order)
  are all frozen.
- Number formatting: the JSON payload carries source values **verbatim and
  unrounded**. Only the markdown renderer rounds for display: IC three
  decimals, p-values four decimals (R3-UI-02 handoff precedent), counts as
  integers, nulls rendered as the word "unavailable". No percentage values
  exist in the frozen inventory.
- The markdown renderer is a pure function of the JSON payload: same input,
  same bytes; it may reorder nothing and add no sentence not present as a
  frozen template or payload string.
- Caching: in-process `lru_cache` keyed by `(path, mtime)` per existing loader
  precedent only. No response-level cache with TTL (would add a staleness
  dimension the checksums could not describe).

## 16. Implementation architecture

DESIGN DECISION — narrowest correct construction:

- **Router:** one route in `backend/app/routers/research.py`, mapping
  `ValueError` → 422, a memo-specific not-found error → 404, and a
  `MemoEvidenceUnavailable` error → 503 (loader precedent).
- **Service:** all logic in `backend/app/services/memo_service.py` (proposed):
  frozen copy constants, evidence loading, citation construction/resolution,
  section composition, and the markdown renderer. Citation machinery stays
  internal (§3 NARROW decision — no shared-module refactor of the courtroom in
  this task).
- **Reuse (mandatory):** `skeptic_service.skeptic_report()`,
  `research.significance.payload()`, `research.real_terms.payload()`,
  `research.regime.payload()`, `research.feature_passports.payload()`. Direct
  artifact reads only where no service exists: the calibration report, the
  serving-eval report, the data-quality report, the company context, and the
  MCC. Path constants and `resolve_repo_root()` usage copy the
  skeptic/courtroom pattern.
- **Provenance:** sha256 computed from source file bytes at load time and
  carried into `source_artifacts` and citations.
- **Prohibited inside the memo path (each pinned by tests):** statistical
  arithmetic of any kind; return recomputation; p-value adjustment; ranking;
  scoring; aggregation of numeric evidence (allowed operations are field
  selection, `len()` of cited lists, string templating, equality comparison
  for resolution, and sha256 of file bytes); client-provided evidence; any
  import of `forecasting_service`, `scoring_service`, `sector_service`,
  `adaptive_weights_service`, `comparison_service`, `explanation_service`, or
  `research_agent` (the legacy/DB/recommendation-shaped families named in
  `docs/LEGACY_DB_PATH_AUDIT.md`, plus the hybrid path whose response contains
  `decision_support_verdict`); any DB session; any frontend/mock data; any
  sector value; any LLM call.
- If a needed value has no governed source, it is rendered unavailable or the
  packet's owner-decision path is taken — never computed in-service.
- Trustworthiness note (VERIFIED): the company-score data path was assessed and
  **excluded** (§6), so its trustworthiness question does not arise in v1.

## 17. Exact expected-file scope

| File | Class | Content |
|---|---|---|
| `backend/app/services/memo_service.py` (proposed) | **new** | Service per §16 |
| `backend/tests/test_memo_api.py` (proposed) | **new** | Backend test suite per §20 |
| `tests/test_memo_claim_safety.py` (proposed) | **new** | Root claim-safety pins per §20 (pattern: `tests/test_courtroom_claim_safety.py`, minus the page assertions — no page exists) |
| `backend/app/routers/research.py` | **modified** | One new route + error mapping only |
| `model_confidence_contract.json` | **modified** | §19 bump: version 1.9.0, scan entry, allowlist entry |
| `tests/test_courtroom_claim_safety.py`, `tests/test_autopsy_claim_safety.py`, `tests/test_friction_claim_safety.py`, `tests/test_dissent_ledger_claim_safety.py`, `backend/tests/test_confidence_contract.py` | **modified** | Version-pin string 1.8.0 → 1.9.0 only (VERIFIED: these five files pin the MCC version) |
| `FINANCEIQ_AGENT_TASK_QUEUE.md` | **modified** | Append-only implementation-evidence bullet under R3-MEMO-01 (standing instruction) |
| `TASK_STATE.md` | **modified** | Append-only completion row (standing instruction) |
| `docs/R3_MEMO_01_FABLE5_REVIEW_HANDOFF.md` (proposed) | **new** | Review handoff per the R3-SERV-01/R3-UI-02 pattern, containing the §28 source-number table filled with observed values |

Nothing else. Any additional changed or untracked file at final verification is
a §23 stop condition. No generator change is needed (VERIFIED: every consumed
artifact is committed); if the implementation concludes otherwise, it stops at
owner-decision-required rather than expanding scope.

## 18. Protected and forbidden files

Forbidden to modify (enforced by `git status`/`git diff` at review):

- Everything under `frontend/`.
- Everything under `experiments/`, `data/`, `scripts/`, `research_agent_training/`.
- `Makefile` (no new target is needed — the memo is a runtime response).
- `METHODOLOGY.md`, `PRD.md`, `FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md`,
  `docs/VERIFICATION_BASELINE.md`, `artifact_registry.json`.
- All backend services except the new `backend/app/services/memo_service.py` (proposed);
  in particular `skeptic_service.py`, `courtroom_service.py`,
  `forecasting_csv_service.py`, and the `services/research/` subpackage are
  read-only imports.
- All Alembic migrations and models.

Protected checksums (must be byte-identical before/after implementation; the
reviewer re-verifies): every registry-owned artifact under the governed roots
listed in `artifact_registry.json`, plus `backend/app/services/forecasting_csv_service.py`
(sha256 `7438ab40a47b5a1122ec8079d977bde7b7482a31f90dee0de79fd0f5f0212cb1`, from
the R3-SERV-01 handoff, re-verifiable at HEAD).

## 19. MCC procedure

DESIGN DECISION — R3-MEMO-01 **requires a minor MCC bump** performed by the
implementation task (queue precedent: every new copy-bearing backend service
joined the scan with a version bump):

1. `model_confidence_contract.json`: version `1.8.0` → `1.9.0`; `effective_date`
   → implementation date.
2. `scan.backend_response_files` += `backend/app/services/memo_service.py` (proposed).
3. `scan.allowlist` += exactly one entry: the `PRIMARY_DISCLAIMER` constant line
   in the new service (it contains "buy/sell/hold", which trips `MCC-CLAIM-001`),
   reason "Authoritative primary disclaimer forbids recommendation use."
   (precedent: the four existing allowlist entries for the same sentence). No
   other allowlist entry is authorized; if the lint flags any other line of the
   new service, reword the service copy instead.
4. `required_disclaimer.pages` unchanged (no new page).
5. Update the five version-pin tests (§17).
6. Key-absence coverage (§10) is deliberately **not** encoded as MCC vocabulary
   patterns — it lives in the new tests, because key names like `upside` would
   over-trigger as prose words. The MCC's vocabulary rules still scan all memo
   copy via the new scan entry.
7. Evidence-state binding: the memo refuses when
   `evidence_state.reliable_predictive_edge_observed` ≠ false (§6 E11) — this is
   runtime binding, not a contract edit.
8. Human review of the bump against the authority is part of the mandatory
   independent review (§28), satisfying the contract's `versioning_procedure.review`.
9. Only this task bumps the MCC in its context (queue hard rule: one
   MCC-bumping task per context).

## 20. Test matrix

Objective / fixture / expected / misleading implementation prevented / file.
"api" = `backend/tests/test_memo_api.py` (proposed); "root" =
`tests/test_memo_claim_safety.py` (proposed).

| # | Test | Fixture | Expected | Prevents | File |
|---|---|---|---|---|---|
| T1 | Schema contract: exact top-level key set, section ids and order, per-section keys | live ASELS memo | keys match §8/§13 exactly | recommendation-shaped extension keys sneaking in as "extra info" | api |
| T2 | Forbidden-key absence: recursive scan of the full response (incl. `skeptic_report`) for §10 exact names + aliases | ASELS + DSTKF | Zero forbidden-key hits, with the single documented exemption of the skeptic per-check `verdict` status key. Every exempted value must be one of `pass`, `warn`, or `insufficient_data`. | verdict/score/rank/rating fields at any depth | api |
| T3 | Recommendation-language scan of all string values in the response body against the MCC `MCC-CLAIM-001` patterns plus `\bverdict\b`, `\brecommend`, `\bopportunit`, `\bundervalued\b`, `\bcontrarian\b` (allowing only the frozen `PRIMARY_DISCLAIMER` negation) | ASELS | zero non-allowlisted hits | advice-flavored template drift | api + root |
| T4 | Exact mandatory copy: every §11 constant byte-equal in the response; `disclaimer` byte-equals MCC `approved_wording.primary_disclaimer`; `closing` rendered last in markdown | ASELS | byte equality | paraphrased or softened caveats | api |
| T5 | Citation completeness: every statement with a digit or factual template has ≥1 citation id; every id resolves; no orphan citations | ASELS + DSTKF | complete | uncited numeric sentences | api |
| T6 | Citation resolution by value: for every citation, re-read `field_path` from `source_artifact` and assert equality with `value` | ASELS | all equal | citing the right file but wrong/stale value | api |
| T7 | Source-field byte/value matching for the headline numbers: significance headline IC/raw/adjusted, serving IC/raw-p, per-basis triples — asserted against the committed JSON files directly | live artifacts | full-precision equality | display constants drifting from artifacts | api |
| T8 | Raw/adjusted pairing: every six-model statement carries both p-values; response structure makes raw inseparable from adjusted (one object) | ASELS | paired | the multiple-comparisons trap (raw p alone) | api |
| T9 | Outside-family framing: serving statement includes the verbatim `test_label`; serving section contains no `bonferroni`/adjusted field for the serving result | ASELS | label present, no fake adjustment | serving p misread as family-corrected | api |
| T10 | Missing-artifact behavior: monkeypatched-away calibration report (and separately serving report, regime report) | tmp-path fixture | 503, loader message, no partial memo | plausible memo from a broken install | api |
| T11 | Missing-adjusted-p refusal: significance payload with a model whose `bonferroni_adjusted_p_value` is None | synthetic fixture | 503 | raw-only significance rendering | api |
| T12 | Conflicting-source refusal: MCC `reliable_predictive_edge_observed` flipped to true; separately significance `significant_fwer_0_05` flipped to true | monkeypatched fixtures | 503 naming both sources | memo generated under a changed conclusion | api |
| T13 | Null preservation: DSTKF nulls render as null/"unavailable", never 0/""/placeholder | DSTKF | explicit nulls | silent imputation in templating | api |
| T14 | Sparse-company fixture: DSTKF memo is `partial` or carries per-check `insufficient_data` skeptic entries; unavailable evidence named in `unavailable_sections`/`missing_evidence` | DSTKF | named gaps | sparse memo looking equally certain | api |
| T15 | Unknown-ticker behavior: syntactically valid unknown ticker → 404; malformed → 422 | `"ZZZZ"` / `"AKBNK"` (verified training-universe-only ticker with no public company context) / `"bad ticker!"` | 404 / 404 / 422 | fabricated memo for a nonexistent company | api |
| T16 | No legacy-source use: static assertion that `memo_service` imports none of the §16 banned modules and opens no DB session | source scan | zero banned imports | sector/legacy/verdict leakage via indirect dependency | root |
| T17 | No LLM dependency: memo path never reads LLM config/providers; source scan for `call_llm`/provider config plus a live call with `RESEARCH_LLM_PROVIDER=none` | ASELS | identical behavior, no LLM symbols | silent LLM coupling | api + root |
| T18 | Determinism: two consecutive calls (json and markdown) byte-identical; response contains no timestamp-shaped string (regex for ISO dates outside `company_year`/vintage-free fields) | ASELS + DSTKF | byte-identical | wall-clock defeating determinism | api |
| T19 | MCC version tests: contract version 1.9.0 pinned; new service present in `scan.backend_response_files`; the five existing pin tests updated | contract file | pass | unregistered claim surface | root + the five §17 pin files |
| T20 | Claims-lint integration: `make claims-lint` green with the new scan entry and single allowlist line | repo | exit 0 | copy drift invisible to lint | verification step |
| T21 | Protected-artifact checksums: sha256 of every §6 source artifact unchanged before/after implementation session | repo | identical | quiet artifact regeneration | root (reuses registry checksum machinery) + review |
| T22 | Route registration: `GET /research/memo/{ticker}` mounted under `/research` with `require_access`; 200 in demo mode without auth | test client | mounted, open-read | orphan or auth-divergent route | api |
| T23 | No statistical recomputation: source scan of `memo_service` forbids `numpy`, `scipy`, `statistics`, `pandas` numeric ops beyond loading (allowed: json/csv read, sha256, len); plus a semantic test that every rendered number exists verbatim in a source artifact | source + ASELS | zero computed numbers | "helpful" derived statistics | api + root |
| T24 | No recommendation-shaped aliases: §10 alias list scanned as exact key names recursively (separate from T2's primary list to keep both lists visible) | ASELS + DSTKF | zero hits | alias laundering (`rating`, `outlook`, `stance`…) | api |
| T25 | Rendered-memo snapshot/semantic structure: markdown for both fixtures — section order, boundary strings present and uncollapsed, global-scope marker rendered, closing last; snapshot committed as test data inside the test file (not as a repo artifact) | ASELS + DSTKF | matches | JSON-safe but markdown-unsafe rendering | api |

## 21. Mandatory rendered-review fixtures

Both fixtures are mandatory for the independent review; the reviewer inspects
the **rendered markdown output** (and the JSON), not only code and tests.

**Fixture 1 — ASELS** (well-covered: VERIFIED 40/40 populated features on its
latest public row; contexts for 2020–2025; no universe-audit price gap):

- Expected available: all nine sections; `evidence_status: "complete"` (unless
  the skeptic instability probe lacks dump rows — verify, do not assume).
- Must be source-checked: significance headline triple (−0.15328380688030444 /
  0.0182981701829817 / 0.10978902109789021), serving pair (0.050 pooled IC …
  raw p 0.4427 inside the verbatim conclusion sentence), the three basis
  triples, detectable-IC values, calibration verdict string, regime statement.
- Caveats that must be prominent: boundary-first opening; skeptic footer;
  serving `test_label`; closing.
- Dangerous readings to hunt: "0/40 missing fields" adjacent to identity reading
  as endorsement; the serving +0.050 next to family −0.153 reading as "the
  product's heuristic works"; full coverage reading as data quality ⇒ signal.
- Citation checks: spot-resolve ≥10 citations by hand, including at least one
  per evidence family.

**Fixture 2 — DSTKF** (sparse: VERIFIED 37/40 populated features on its latest
public row — the sparsest latest-row coverage in the public cohort — and the
widest documented price-coverage gap, 2020–2024, in `docs/universe_audit.md`):

- Expected: explicit nulls in coverage statements; skeptic
  `cohort_integrity_challenge` warn with the DSTKF gap-years evidence;
  `missingness_attack` verdict per the artifact-derived threshold (verify);
  any per-section `insufficient_data` honestly listed in
  `unavailable_sections`.
- Must be source-checked: the null fields render as "unavailable", not 0; the
  memo does not look equally certain as ASELS's.
- Dangerous readings: sparse memo with precise-looking global numbers implying
  company-level precision; gap-years statement softened.
- Citation checks: resolve the company-context citations and one skeptic
  evidence fact to `docs/universe_audit.md`.

## 22. Acceptance criteria (all binary)

1. Schema version is exactly 1; top-level key set matches §9.
2. Byte-determinism test (T18) passes for both fixtures, both formats.
3. Every claim-bearing string is backend-owned and byte-equals §11.
4. Every numeric claim is citation-complete (T5) with zero unresolved citations
   (T6).
5. Zero forbidden or alias keys (T2, T24); zero recommendation-shaped prose
   (T3).
6. No research recomputation anywhere in the memo path (T23); no client-side
   composition exists (no frontend change at all).
7. Raw and adjusted p-values paired everywhere (T8); serving raw p labeled with
   the verbatim outside-family `test_label` (T9).
8. Confidence rendered only via the verbatim calibration verdict + statement
   (not estimable / not informative at this scale).
9. Missing evidence remains unavailable/null (T13, T14); unknown ticker cannot
   yield a memo (T15).
10. No sector analysis or sector value anywhere.
11. Protected artifacts byte-unchanged (T21; §18).
12. `make docs-lint` green; `make claims-lint` green at MCC v1.9.0.
13. Root and backend suites green (compare observed counts with
    `docs/VERIFICATION_BASELINE.md`; new tests added on top).
14. MCC procedure of §19 followed exactly (one bump, one allowlist line, five
    pin tests updated).
15. Independent Fable-class review (§28) of the rendered outputs recorded with
    a disposition.
16. No visual/browser verification claim unless actually performed; the
    rendered-markdown transcripts stand in and must be labeled as such.

## 23. Stop conditions (implementation agent)

Stop, report, and leave the tree clean if any of the following occurs:

- A required value has no governed source, or §6's inventory proves wrong in
  any particular.
- Two sources disagree on a value the memo would render (beyond what §14 maps
  to 503 — i.e., the disagreement is in committed artifacts themselves).
- An adjusted p-value is unavailable where §14 expects one.
- Correct behavior would require: statistical recomputation; a frontend change;
  artifact regeneration; touching a legacy/recommendation-shaped service; a
  database migration; sector data; any LLM dependency; or changing the
  committed conclusion.
- The expected-file scope of §17 does not suffice.
- Any protected checksum changes.
- `make docs-lint` or `make claims-lint` fails for any reason not introduced
  and immediately fixable within §17's file scope (a new-reason failure after
  your edits that you cannot attribute = stop).
- The skeptic or research services' response shapes differ from what §6 records
  (report, don't adapt silently — the shapes are test-pinned upstream).

## 24. Misleading-success register

Format — failure / why tests might miss it / required prevention / required
reviewer check:

1. **Tests pass but the memo reads like advice.** Tests check structure, not
   gestalt. / Frozen copy + order (§11, §13). / Hostile-editor read of both
   rendered fixtures.
2. **All citations exist but cite the wrong evidence field.** Path-only
   resolution would pass. / T6 value-resolution. / Spot-resolve ≥10 citations
   by hand.
3. **Global evidence presented as company-specific.** Scope field could be set
   wrong uniformly. / §12 rule 6 + T25 marker rendering. / Read every
   company-section statement asking "is this about DSTKF or about the repo?"
4. **A score becomes the de-facto headline.** Score is excluded, but coverage
   counts could be styled as a grade. / §10 forbids score-shaped keys; §11
   boundary in identity section. / Check no statement ranks or grades the
   company.
5. **Negative IC framed as contrarian.** Vocabulary lint misses novel phrasing.
   / T3 includes `contrarian`/`undervalued`; frozen templates. / Hunt for any
   "inverse"/"opposite"/"fade" flavored sentence.
6. **Raw p displayed without family context.** A new template could quote one
   number. / T8 structural pairing. / Verify every p in the markdown has its
   companion or label.
7. **Serving p called adjusted.** Mislabeled template. / T9 forbids an
   adjusted field for serving; verbatim `test_label`. / Read the serving
   section against `serving_eval_report.json`.
8. **Confidence read as probability.** Paraphrase drift. / §11 calibration
   boundary byte-pinned. / Confirm verbatim verdict + statement, no paraphrase.
9. **Missing data silently omitted.** Statement dropped with its citation,
   nothing flags it. / §12 rule 5 + `unavailable_sections`. / Diff DSTKF's
   section list against ASELS's; every gap must be named.
10. **Sparse memo appears equally certain.** All sections render, nulls hidden
    in JSON only. / T13/T14 + markdown "unavailable" rendering. / Compare both
    rendered fixtures side by side.
11. **An LLM produces uncited connective claims.** N/A by design — but a future
    edit could add it. / T17 source scan. / Confirm no LLM symbol in the
    service.
12. **Optional LLM failure changes facts.** Same. / No LLM path exists. /
    Confirm behavior identical with `RESEARCH_LLM_PROVIDER=none`.
13. **A timestamp defeats determinism.** "generated_at" feels natural to add.
    / §15 + T18 regex. / Grep the response for date-shaped strings.
14. **Mock fallback looks like evidence.** Frontend mocks can't enter (no
    frontend), but a test fixture constant could leak into the service. / T7
    asserts against committed artifacts. / Check the service has no numeric
    literals except formatting precision.
15. **A legacy portfolio action leaks in.** `forecasting_service` portfolio
    endpoint emits "increase"/"reduce" (VERIFIED in `docs/LEGACY_DB_PATH_AUDIT.md`).
    / T16 import ban. / Confirm zero legacy imports and zero DB usage.
16. **Sector-adjusted anything enters via an indirect dependency.** A reused
    service might someday join sector paths. / T16 + §16 ban list. / Trace
    every import of the memo service transitively one level.
17. **Citation ids resolve but artifact checksums are stale.** Value matches an
    old cached copy. / mtime-keyed caches + `source_artifacts` sha256 from the
    bytes actually read. / Recompute two checksums manually.
18. **Individually safe sentences become misleading when adjacent.** No unit
    test sees adjacency. / §13 ordering + boundaries between every section. /
    The explicit adjacency read in §28 step 8.
19. **Unsupported "risk" language implies an investment assessment.** "High
    risk"/"low risk" wording converts diagnostics into ratings. / Templates
    avoid the word "risk" except inside verbatim skeptic/source strings; T3
    scan. / Search the markdown for "risk" outside quoted evidence.
20. **Safe JSON, unsafe markdown.** The renderer could add headings like
    "Verdict". / Renderer is a pure function; T25 snapshot. / Review the
    markdown, not only the JSON.
21. **Reviewer checks code but not rendered memos.** Historical failure mode of
    memo-like features. / §28 makes rendered inspection mandatory for both
    fixtures. / The review disposition must quote from both rendered memos.
22. **Build success treated as research validity.** Green suites read as "the
    memo is true". / §22 item 16 + closing line. / The review report must
    restate that all green means claim-safe composition, not predictive
    validity.

## 25. Model allocation

- **Implementation:** Opus, high effort (queue recommendation KEPT; the frozen
  packet pre-makes the judgment calls, so Fable is not required and per the
  routing rule must not be used for mechanical coding). Terra is **not**
  sufficient: citation-resolution machinery plus refusal semantics sit directly
  on a high-claim-risk surface.
- **Independent review:** Fable-class, medium effort, separate context,
  mandatory before the owner considers a commit (queue KEPT; first
  implementation of the highest-claim-risk feature).
- **Smaller models after freeze:** Sol may perform the append-only ledger rows
  and handoff-doc formatting *within* the implementation session's scope but
  must not touch service code or the MCC.
- **Human owner checks:** read both rendered fixture memos end to end; approve
  the MCC 1.9.0 bump; perform the manual commit (§29). The owner, not any
  model, decides commit and push.

## 26. Owner decisions

Each carries a RECOMMENDATION frozen into this packet; the owner may override
only by editing this packet before implementation starts.

- **OD-1 — Company score/rank in the memo.** RECOMMENDATION: **exclude**
  (frozen). The queue's own binding section list has no score section; a score
  next to null-consistent significance is composition risk #1. Reopening
  requires a new task with its own MCC review.
- **OD-2 — Optional LLM prose.** RECOMMENDATION: **exclude entirely** (frozen).
  Deterministic-only. Any future LLM renderer is a separate packet.
- **OD-3 — Deterministic markdown representation in backend scope.**
  RECOMMENDATION: **include** (frozen): `format=markdown` per §8. Without it,
  "rendered memo review" would mean raw JSON, and the review's hostile-editor
  step loses its object.
- **OD-4 — 2022 return-basis illustration in the memo.** RECOMMENDATION:
  **exclude** (frozen). Global illustration, already surfaced with its
  qualifier on BenchmarkPage; adjacency to company facts misleads.
- **OD-5 — Rank exposure.** Subsumed by OD-1: **exclude** (frozen).
- **OD-6 — Demo-critical or thesis-optional.** Genuinely open; no repository
  consequence inside this task. RECOMMENDATION: treat as demo-critical (the
  queue's demo chain ends at MEMO-01), which argues for scheduling the
  implementation soon after this freeze.
- **OD-7 — Friction/autopsy/dissent evidence in a future memo v2.** Out of
  scope now (§6 exclusions frozen for v1); revisit only with a new packet.

## 27. Complete implementation prompt

The following prompt is self-contained for a separate implementation session.

```text
Implement FinanceIQ task R3-MEMO-01 (claim-aware research memo compiler)
EXACTLY as frozen in docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md.
Read that packet fully first; it overrides the shorter R3-MEMO-01 entry in
FINANCEIQ_AGENT_TASK_QUEUE.md wherever they disagree. Then read, in order:
CLAUDE.md, PRD.md, REPO_MAP.md, FINANCEIQ_SMALL_MODEL_RULES.md,
FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md, model_confidence_contract.json,
backend/app/services/skeptic_service.py, backend/app/services/courtroom_service.py,
backend/app/routers/research.py, backend/app/services/research/significance.py,
backend/app/services/research/real_terms.py, backend/app/services/research/regime.py,
backend/app/services/research/feature_passports.py,
tests/test_courtroom_claim_safety.py, backend/tests/test_skeptic_service.py.

PRECONDITIONS (verify before any edit; stop if any fails):
- FinanceIQ repository; clean working tree; HEAD equals main; a
  harness-generated suffix on the worktree/branch name is acceptable and is
  not a stop reason.
- make docs-lint green; make claims-lint green at MCC v1.8.0. If the MCC
  version is not 1.8.0, STOP: the packet's bump target (1.9.0) was frozen
  against 1.8.0 and the packet must be re-audited first.
- docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md exists and its §2 HEAD
  ancestry is part of your history (git log --oneline | grep -i "governance").
- Record sha256 checksums of every packet §6 source artifact before starting;
  they must be byte-identical at the end.

SCOPE — create/modify ONLY (packet §17):
NEW: backend/app/services/memo_service.py; backend/tests/test_memo_api.py;
tests/test_memo_claim_safety.py; docs/R3_MEMO_01_FABLE5_REVIEW_HANDOFF.md.
MODIFIED: backend/app/routers/research.py (one GET route + error mapping);
model_confidence_contract.json (v1.9.0 bump per packet §19: scan entry for the
new service + exactly one allowlist entry for the primary-disclaimer constant
line); the five MCC version-pin tests (tests/test_courtroom_claim_safety.py,
tests/test_autopsy_claim_safety.py, tests/test_friction_claim_safety.py,
tests/test_dissent_ledger_claim_safety.py, backend/tests/test_confidence_contract.py)
updated 1.8.0 -> 1.9.0; append-only evidence bullet in
FINANCEIQ_AGENT_TASK_QUEUE.md under R3-MEMO-01 and append-only row in
TASK_STATE.md. NOTHING ELSE. No frontend file, no experiments/, no data/, no
scripts/, no Makefile, no METHODOLOGY.md, no artifact regeneration, no other
service, no migration, no LLM code path.

BUILD (all details are in the packet; do not re-decide them):
- GET /research/memo/{ticker}?format=json|markdown per packet §8; service
  logic per §16; schema per §8/§9; forbidden keys per §10; mandatory copy
  byte-exact per §11; citations per §12; section order and boundaries per §13;
  error mapping per §14 (422 malformed ticker; 404 unknown/out-of-cohort
  ticker; 503 for any missing/malformed/conflicting global artifact and for
  MCC evidence-state conflict; 200 partial with named unavailable sections for
  company-specific gaps); determinism per §15 (no wall-clock timestamp
  anywhere; byte-identical repeat calls; markdown renderer is a pure function
  of the JSON payload with the packet's rounding rules).
- Reuse existing services exactly as §16 lists; direct artifact reads only for
  the calibration report, serving-eval report, data-quality report, company
  contexts, and the MCC. No statistical arithmetic anywhere: allowed
  operations are field selection, len() of cited lists, string templating,
  equality comparison for citation resolution, and sha256 of file bytes.
- Implement the full test matrix of packet §20 (T1-T25).

STOP CONDITIONS: packet §23, verbatim. Also stop if any service response shape
differs from what packet §6 records, if claims-lint flags any new-service line
other than the single authorized allowlist line, or if you need any file
outside the scope list. On stop: leave the tree clean, report the exact
blocker with file/line evidence, and do not improvise.

VERIFICATION (run all; report honestly):
1. PYTHONPATH=. python -m pytest tests/
2. PYTHONPATH=backend python -m pytest backend/tests
3. make claims-lint          (must report MCC v1.9.0 satisfied)
4. make docs-lint
5. make data-validate        (must be unchanged/VALID; you touched no data)
6. Compare observed suite results against docs/VERIFICATION_BASELINE.md plus
   your new tests; report exact observed numbers without editing the baseline.
7. Byte-determinism: two curl/TestClient calls per fixture per format,
   compare bytes.
8. Record the rendered markdown memos for ASELS and DSTKF in full in
   docs/R3_MEMO_01_FABLE5_REVIEW_HANDOFF.md, plus a source-number table
   mapping every rendered number to its artifact field and full-precision
   value, plus the before/after sha256 list proving every packet §6 artifact
   unchanged.
9. git diff --check and git status --short: only the scoped files changed.

FINAL REPORT: (1) what changed, file by file; (2) exact commands and observed
results, pass/fail; (3) anything not done or needing verification; (4) the two
rendered memos; (5) statement that no commit or push was made. Do NOT commit
or push; the owner commits manually after the independent review. Do not
perform your own "independent review" — that runs in a separate session with
the packet's §28 prompt. Status at handoff: PENDING INDEPENDENT FABLE-CLASS
REVIEW; not merge-ready.
```

## 28. Complete independent-review prompt

The following prompt is self-contained for a separate Fable-class review
session. The reviewer must not be the implementation agent.

```text
You are the independent Fable-class reviewer for FinanceIQ task R3-MEMO-01
(claim-aware research memo compiler). You did not implement it. Your authority
is docs/R3_MEMO_01_FABLE5_IMPLEMENTATION_PACKET.md; read it fully first, then
docs/R3_MEMO_01_FABLE5_REVIEW_HANDOFF.md, then the diff. The committed
repository conclusion is "no reliable predictive edge"; nothing you approve
may weaken it. Do not commit, push, fix code, change the MCC, or start
another task. Read-only, except your review disposition appended to the
handoff document.

PROCEDURE (all steps mandatory; report evidence for each):
1. Verify branch, HEAD, worktree; record them. A generated name suffix is
   acceptable. Enumerate the complete diff AND all untracked files; every
   changed/added path must be in packet §17's scope list; anything else is a
   finding.
2. Packet compliance: walk §8-§20 requirement by requirement against the
   implementation. Any deviation is a finding with file/line and the violated
   packet clause.
3. Source-number table: independently re-extract every number rendered in
   both fixture memos (ASELS, DSTKF) from the committed artifacts
   (experiments/results/significance_report.json,
   experiments/results_serving_eval/serving_eval_report.json,
   experiments/results_real_terms/ reports via the return-basis service,
   experiments/results_regime/regime_context_report.json,
   experiments/results/calibration_report.json,
   data/trusted_clean/data_quality_report.json, the two company contexts).
   Full-precision match required in JSON; packet §15 rounding only in
   markdown.
4. Citation-resolution audit: resolve at least 10 citations per fixture by
   hand (field_path -> value -> sha256), covering every evidence family.
5. Forbidden-key audit: run the recursive key scan yourself against live
   responses for both fixtures (packet §10 lists both registers).
6. Refusal semantics: exercise 422 (malformed ticker), 404 (unknown ticker),
   503 (temporarily monkeypatch/move one global artifact in a scratch test,
   never editing committed files), and the MCC evidence-state conflict test.
7. Determinism: two calls per fixture per format; byte-compare. Confirm no
   timestamp-shaped content.
8. Hostile-editor reading of BOTH rendered markdown memos end to end: hunt
   advice flavor, contrarian framing of negative IC, confidence-as-
   probability, global-evidence-as-company-evidence, adjacency effects,
   "risk"-rating language, softened caveats, any sentence quotable as
   investment value. Packet §24 lists 22 named failure modes; check each
   explicitly.
9. No-recomputation inspection: read memo_service.py fully; confirm the
   allowed-operations boundary (field selection, len, templating, equality,
   sha256) and zero statistical arithmetic.
10. Legacy-source exclusion: confirm no import of forecasting_service,
    scoring_service, sector_service, adaptive_weights_service,
    comparison_service, explanation_service, or research_agent; no DB
    session; no sector value anywhere.
11. MCC scope: exactly one version bump 1.8.0 -> 1.9.0, one new scan entry,
    one allowlist line (the primary-disclaimer constant), five pin tests
    updated, pages list unchanged. Human-review the bump against
    FINANCEIQ_DEMO_AND_CLAIMS_GUIDE.md as the contract's versioning
    procedure requires.
12. Protected files: recompute sha256 for every packet §6 source artifact and
    for backend/app/services/forecasting_csv_service.py; all must match the
    pre-implementation values recorded in the handoff.
13. Run: PYTHONPATH=. python -m pytest tests/ ; PYTHONPATH=backend python -m
    pytest backend/tests ; make claims-lint ; make docs-lint. Compare with
    docs/VERIFICATION_BASELINE.md plus the new tests; report observed
    results exactly.
14. Confirm LLM-off correctness: RESEARCH_LLM_PROVIDER=none (or unset)
    changes nothing; no LLM symbol in the memo path.
15. State explicitly what was NOT verified (e.g., no browser/visual
    verification — none is expected; no frontend exists for this feature).

Return exactly one disposition: APPROVED, APPROVED_WITH_REQUIRED_FIXES (with
file/line findings, each citing the violated packet clause), or REJECTED.
Your report must quote at least one passage from each rendered fixture memo
as evidence that you read the rendered output. Approval means claim-safe
composition per the packet - it is not a statement of predictive validity.
```

## 29. Manual commit-scope recommendation

For the owner, after an APPROVED review (no commit is performed by any agent):

- One commit containing exactly the §17 scope. Suggested theme (queue
  convention): **"Add citation-complete research memo compiler"**.
- Before committing: re-run the four verification commands; confirm
  `git status --short` shows only §17 paths; confirm the review disposition is
  recorded in the handoff document and, per precedent, close the loop with
  append-only queue/TASK_STATE entries (the implementation session drafts
  them; the review closure bullet is appended after review, R3-SERV-01
  precedent).
- Do not squash unrelated work into this commit; the MCC bump must be in the
  same commit as the service it registers (lint atomicity).

## 30. Final frozen decisions (summary of record)

1. Evidence memo, not analyst memo; deterministic; zero LLM involvement.
2. `GET /research/memo/{ticker}` (+ `format=markdown`) in the research router;
   service in `backend/app/services/memo_service.py` (proposed).
3. Schema `financeiq.memo.v1` per §8/§9; forbidden-key registers per §10 with
   recursive key-absence tests.
4. One fixed headline for every company; §11 copy byte-frozen; queue closing
   line kept verbatim.
5. Citations: value-resolved, checksum-carrying, both inline ids and full
   registry; no METHODOLOGY citations needed or permitted.
6. Section order §13; company score, rank, hybrid score, courtroom personas,
   friction, autopsy, dissent ledger, global diagnostic artifacts, 2022
   illustration, macro values, and sector all excluded from v1.
7. Refusals: 422/404/503 per §14; 409 unused; conflicts always refuse; no
   plausible memo from missing evidence.
8. Byte-determinism at fixed HEAD; no wall-clock timestamp; artifact checksums
   are the evidence vintage.
9. MCC v1.8.0 → v1.9.0 in the implementation task, single allowlist line, five
   pin tests.
10. Tests T1–T25; fixtures ASELS and DSTKF; rendered-markdown review mandatory.
11. Implementation Opus/high; independent review Fable-class/medium in a
    separate session; owner commits manually.
12. The committed conclusion — **no reliable predictive edge** — is preserved
    unchanged by every element of this packet.

R3-MEMO-01 packet frozen 2026-07-18 at HEAD `54102420`.
