# Paper 3 candidate — fund-flow pressure versus fundamental news

2026-11-03, Europe/Zurich · Queue 5 · **DESIGN ONLY / NOT ADOPTED**.
Research support only; not investment advice. No acquisition, holdings query,
sample enumeration, empirical feasibility count, experiment or holdout access.
This card is not a pre-registration, execution grant or Kernel work plan.

## Question and contribution candidate

In BIST equities, are returns associated with fund-flow-implied demand distinct
from reactions around first public financial-statement news, and do their
subsequent paths differ? Proposed primary objects are associations and signed
response paths, not a causal allocation of each price move into “uninformed”
and “fundamental” components. A reversal can be consistent with temporary
pressure without identifying its cause; fundamentals need not be fully captured
by one earnings-surprise measure.

Literature motivation, checked from primary abstracts on 2026-11-03:
[Coval & Stafford, NBER WP 11357 (2005)](https://www.nber.org/papers/w11357)
studies flow-related institutional pressure in shared holdings; its published
version is JFE 86(2), 479–512 (2007), as recorded on the NBER page.
[Lou (2012), RFS 25(12), 3457–3489](https://academic.oup.com/rfs/article-abstract/25/12/3457/1594242)
constructs stock demand from flow-induced fund trading and distinguishes
expected from unexpected flows. These motivate a question, not borrowed
Turkish effect sizes, a validated instrument, or evidence of an investment edge.

## Population, time and evidence requirements

Candidate equity population: Charter U1 at quarterly period starts, survivor-
inclusive through each study window. Product 3184 tier cells are narrowest:
XU100 membership iff XU030/XU050/XU100, with 30/20/50 = 100 each quarter.
No current fund or index list projected backwards. Fund inclusion must itself
be historically effective-dated, retaining closures, mergers and terminated
funds; a TEFAS-covered fund population is not necessarily all Turkish funds.
Strata/holdings flags require adopted effective-dated mappings.

TEFAS is a **candidate source family**, not verified stock-level flow data.
The [official BIST data-products description](https://www.borsaistanbul.com/veriler/veri-yayini/veri-yayin-urunleri)
lists fund information and portfolio-distribution categories; it does not
establish free historical TEFAS constituent holdings, a usable PIT archive,
daily subscriptions/redemptions, or a licence for this design. Rights for this
new TEFAS use, exact variables/products, archived timestamps, coverage and
publication lags remain **UNSET/UNVERIFIED**. Existing closed KAP, BIST
announcement and 3184 rights decisions are preserved, not reopened. Price
source policy remains LSEG primary / DataStore cross-check / Yahoo dev-only.

Required evidence before any later feasibility task: fund assets/NAV and units,
distributions and fees, subscriptions/redemptions if truly available, dated fund
holdings with publication times, fund/security identity continuity, official
market calendar, corporate actions, daily total returns and first KAP filing
times/basis. Public-availability time differs from NAV valuation, order,
settlement and effective dates. Historical current-screen values are not
evidence of historical public availability.

## Candidate measures and estimands — all prospective

Prefer actual evidenced net subscriptions less redemptions. If unavailable,
the candidate estimate

`estimated_flow(f,t) = assets(f,t) − assets(f,t−1) × (1 + fund_total_return(f,t))`

is explicitly a residual accounting proxy, not observed cash flow. It needs
compatible assets, return/distribution/fee and timing definitions; residuals
can reflect valuation, distributions or reporting changes. No automatic zero,
interpolation or backfill; an unidentified proxy means no stock-level study.

Candidate stock pressure = sum of eligible fund flows weighted by each fund's
latest holdings **publicly available strictly before** the flow window,
normalized by a predeclared lagged stock traded-value measure. Never use
holdings reported later merely because their accounting date precedes the event.
Holdings staleness cutoff, normalization/history, fund set, sampling frequency
and winsorization policy are UNSET. Missing holdings cannot be replaced by
sector weights or today's portfolio. Fund investor count or AUM change alone
is not an issuer-level demand observation.

Candidate response: same-window and fixed subsequent abnormal-return paths,
contrasted across flow pressure and KAP-news exposure. Freeze exact horizons,
expected-return model, earnings-surprise definition and co-announcement taxonomy
before outcomes. Paper 2's approved surprise could be a candidate only if its
basis/PIT prerequisites and separate study authorization hold; do not silently
inherit its sample, access or one confirmatory opening. Do not call a regression
residual fundamental news. Prespecify fund and issuer dependence, common dates,
overlapping windows and generated-regressor uncertainty before inferential use.

Identification threats: return-chasing flows; common macro shocks; manager
information; discretionary rebalancing; mechanical correlation through return-
adjusted AUM; stale holdings; publication/settlement delays; liquidity selection;
fund entry/exit and terminal-value omissions. Leave-one-security-out return
adjustments, predetermined holdings and expected-flow innovations are candidate
diagnostics, not automatically exogenous instruments. No causal claim without
a separately justified identification design and precommitted exclusion tests.

## Registration and stopping gates

1. Owner chooses descriptive study versus a separately defensible causal design,
   and approves exact outcome-free feasibility scope. Dates, fund rule, rights,
   holding staleness and every measure above remain UNSET. No acquisition is
   authorized by placing this task in the queue.
2. Any authorized feasibility uses only the permitted metadata and exact output
   schema. The four FIQ-11 OD-1 protected aggregates do not include fund holdings,
   fund/security joins or price coverage. If needed stock-level PIT holdings or
   compatible flow definitions cannot be evidenced, stop with NOT FEASIBLE;
   a fund-level descriptive question would be a new owner choice.
3. Before empirical work, commit a BEFORE record, exact inputs/lineage, exposure
   inventory, hypotheses/estimands, multiplicity, trial/stopping rules and
   dependence/calibration plan. Every failed/abandoned configuration is retained.
   Development ≤2022-12-31; locked 2023–2025 and later data retain Charter/access
   restrictions. Actual OSF timestamp and study-specific window are UNSET;
   no Paper 2 quarantine interval is treated as open data for this candidate.
4. One confirmatory opening, if ever approved, binds this study's immutable ID,
   registration and cross-study exposure ledger. Reading outcomes here could
   contaminate Paper 2/Study 3/forward research; no default permission is inferred.
   Cleanliness needs evidence, not dates. Independent scientific review precedes
   paper use; author submission is separate.

Owner choices (all **UNSET**): (A) pursue descriptive design / defer;
(B) approve a later exact outcome-free feasibility card / defer;
(C) only if feasible, choose scope and prospective registration. This card
performs none of these actions. No Kernel request or outcome feedback is sent.
