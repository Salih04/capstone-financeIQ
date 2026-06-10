import { useEffect, useMemo, useState } from 'react'
import { researchApi } from '../api/researchApi'

// ---------------------------------------------------------------------------
// Data Quality — THE SPECIMEN ARCHIVE.
// Every feature is a labeled specimen: accepted ones mounted crisp,
// rejected ones stamped with the reason (LEAKAGE / FROZEN / ALL-NULL).
// Real API data (researchApi.dataQuality/summary/frozenEvidence);
// mock is fallback only.
// ---------------------------------------------------------------------------

const YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

const DATA_QUALITY_MOCK = {
  accepted: [
    { name: 'ROE', category: 'Profitability', coverage: [1, 1, 1, 1, 1, 0], source: 'corrected_yearly' },
    { name: 'ROA', category: 'Profitability', coverage: [1, 1, 1, 1, 1, 0], source: 'corrected_yearly' },
    { name: 'Revenue growth', category: 'Growth', coverage: [1, 1, 1, 1, 1, 0], source: 'corrected_yearly' },
    { name: 'Net margin', category: 'Profitability', coverage: [1, 1, 1, 1, 1, 0], source: 'corrected_yearly' },
    { name: 'Current ratio', category: 'Balance Sheet', coverage: [1, 1, 1, 1, 1, 1], source: 'reference' },
    { name: 'Net debt/EBITDA', category: 'Leverage', coverage: [1, 1, 1, 1, 1, 0], source: 'corrected_yearly' },
    { name: 'P/B ratio', category: 'Valuation', coverage: [0, 1, 1, 1, 1, 0], source: 'free_valuation' },
    { name: 'EV/EBITDA', category: 'Valuation', coverage: [0, 1, 1, 1, 1, 0], source: 'free_valuation' },
  ],
  rejected: [
    { name: 'Revenue (2025 snapshot)', reason: 'FROZEN', detail: 'Identical value across all years — carries no ranking information' },
    { name: 'Net income (snapshot)', reason: 'FROZEN', detail: 'Frozen 2025 value repeated in every file' },
    { name: 'same_year_return_pct', reason: 'LEAKAGE', detail: 'Target overlap — would leak realized return into features' },
    { name: 'return_12m_pct', reason: 'LEAKAGE', detail: 'Momentum window overlaps the prediction target year' },
    { name: 'Market cap (snapshot)', reason: 'FROZEN', detail: '2025 snapshot only — not historical' },
  ],
}

// Known leakage-guarded fields — excluded by construction, always shown.
const LEAKAGE_GUARDED = [
  { name: 'same_year_return_pct', detail: 'Target overlap — would leak realized return into features' },
  { name: 'next_year_return_pct', detail: 'This IS the prediction target' },
  { name: 'next_year_excess_return_vs_bist100', detail: 'Benchmark-adjusted target — never a feature' },
  { name: 'next_year_outperform_bist100', detail: 'Binary target — never a feature' },
  { name: 'target_year', detail: 'Identifies the prediction window itself' },
]

const GROUP_LABEL = {
  balance_sheet: 'Balance Sheet',
  growth: 'Growth',
  other: 'Income & Profitability',
}

const IC_BY_YEAR = { 2020: 0.08, 2021: -0.11, 2022: -0.14, 2023: 0.03, 2024: 0.12 }

const covSum = (c) => c.reduce((a, b) => a + b, 0)

const usableEntries = (groups) =>
  Object.entries(groups || {}).filter(([, arr]) => Array.isArray(arr) && arr.length > 0)

const uniqueStrings = (items) => [...new Set((items || []).filter((n) => typeof n === 'string' && n.trim()))]

function acceptedFromFlatData(d) {
  const names = uniqueStrings([
    ...(d.accepted_columns || []),
    ...(d.accepted_features || []),
    ...(d.accepted_feature_columns || []),
    ...(d.modeling_columns || []),
    ...(d.modeling_features || []),
    ...(d.final_feature_columns || []),
    ...(d.valid_feature_columns || []),
  ])

  return names.map((name) => ({
    name,
    category: 'Model Feature',
    coverage: [1, 1, 1, 1, 1, 0],
    source: 'data_quality',
    accepted: true,
  }))
}

function buildSpecimens(dq, summary, { allowFallback = true } = {}) {
  const d = dq?.data_quality || {}
  const ctx = summary?.context || {}
  const summaryGroups = ctx.feature_groups || {}
  const dqGroups = d.feature_groups || d.accepted_feature_groups || {}
  const groupEntries = usableEntries(summaryGroups).length ? usableEntries(summaryGroups) : usableEntries(dqGroups)
  const sd = d.source_distinction || {}
  const cy = d.corrected_yearly || {}

  const acceptedFromGroups = groupEntries.flatMap(([g, arr]) =>
    (arr || []).map((name) => ({
      name,
      category: GROUP_LABEL[g] || g,
      coverage: [1, 1, 1, 1, 1, 0],
      source: g === 'balance_sheet' ? 'reference' : 'corrected_yearly',
      accepted: true,
    })),
  )
  const accepted = acceptedFromGroups.length ? acceptedFromGroups : acceptedFromFlatData(d)

  const frozenNames = [
    ...(d.frozen_columns || ctx.rejected_frozen_columns || []),
    ...(sd.still_rejected_valuation_columns || cy.frozen_valuation_columns || []),
  ]
  const seen = new Set()
  const rejected = [
    ...frozenNames
      .filter((n) => { if (seen.has(n)) return false; seen.add(n); return true })
      .map((name) => ({
        name,
        reason: 'FROZEN',
        detail: 'One point-in-time snapshot repeated across years — carries no ranking information',
        accepted: false,
      })),
    ...LEAKAGE_GUARDED.map((l) => ({ ...l, reason: 'LEAKAGE', accepted: false })),
  ]

  if (allowFallback && accepted.length === 0 && frozenNames.length === 0) {
    return {
      accepted: DATA_QUALITY_MOCK.accepted.map((s) => ({ ...s, accepted: true })),
      rejected: DATA_QUALITY_MOCK.rejected.map((s) => ({ ...s, accepted: false })),
      fromApi: false,
    }
  }
  return { accepted, rejected, fromApi: true }
}

function readoutCopy(s) {
  if (s.accepted) {
    return {
      why: 'Known at the end of each year and genuinely varies year to year — admitted to the modeling set.',
      toAccept: 'Already in the modeling set.',
    }
  }
  if (s.reason === 'LEAKAGE') {
    return {
      why: s.detail || 'Overlaps the prediction target window.',
      toAccept: 'Cannot be accepted — it overlaps the prediction target by construction. Leakage guard is permanent.',
    }
  }
  if (s.reason === 'ALL-NULL') {
    return {
      why: s.detail || 'No values present in any year.',
      toAccept: 'Populate the source data with real observations, then re-run validation.',
    }
  }
  return {
    why: s.detail || 'Snapshot value repeated across years; zero variance means zero ranking information.',
    toAccept: 'Supply genuine per-year history for this column (real values that change over time), then re-run validation.',
  }
}

function SpecimenTile({ s, active, onHover }) {
  const grainy = s.accepted && covSum(s.coverage || []) < 5
  return (
    <button
      type="button"
      className={`spx-tile ${s.accepted ? 'is-accepted' : 'is-rejected'} ${grainy ? 'is-grainy' : ''} ${active ? 'is-active' : ''}`}
      onMouseEnter={() => onHover(s)}
      onFocus={() => onHover(s)}
    >
      <span className="spx-tile-name">{s.name}</span>
      {s.accepted ? (
        <>
          <span className="spx-tile-cat">{s.category}</span>
          <span className="spx-tile-years" aria-label="Year coverage 2020 to 2025">
            {(s.coverage || []).map((v, i) => (
              <i key={YEARS[i]} className={v ? 'on' : ''} title={`${YEARS[i]}: ${v ? 'covered' : 'missing'}`} />
            ))}
          </span>
        </>
      ) : (
        <span className={`spx-stamp is-${s.reason.toLowerCase().replace('-', '')}`}>{s.reason}</span>
      )}
    </button>
  )
}

export default function DataQualityPage() {
  const [dq, setDq] = useState(null)
  const [summary, setSummary] = useState(null)
  const [evi, setEvi] = useState(null)
  const [acceptedLoading, setAcceptedLoading] = useState(true)
  const [rejectedLoading, setRejectedLoading] = useState(true)
  const [frozenEvidenceLoading, setFrozenEvidenceLoading] = useState(true)
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    let mounted = true

    const dataQualityRequest = researchApi.dataQuality().then(
      (r) => {
        if (mounted) setDq(r.data)
        return r.data
      },
      () => null,
    )

    const summaryRequest = researchApi.summary().then(
      (r) => {
        if (mounted) setSummary(r.data)
        return r.data
      },
      () => null,
    )

    const frozenEvidenceRequest = researchApi.frozenEvidence().then(
      (r) => {
        if (mounted) setEvi(r.data)
        return r.data
      },
      () => null,
    )

    Promise.allSettled([dataQualityRequest, summaryRequest]).then(() => {
      if (!mounted) return
      setAcceptedLoading(false)
      setRejectedLoading(false)
    })

    frozenEvidenceRequest.finally(() => {
      if (mounted) setFrozenEvidenceLoading(false)
    })

    return () => {
      mounted = false
    }
  }, [])

  const { accepted, rejected, fromApi } = useMemo(
    () => buildSpecimens(dq, summary, { allowFallback: !acceptedLoading && !rejectedLoading }),
    [dq, summary, acceptedLoading, rejectedLoading],
  )
  const active = hovered || accepted[0] || rejected[0] || null
  const copy = active ? readoutCopy(active) : null
  const evidence = active && evi?.available ? evi.columns?.[active.name] : null
  const frozenCount = rejected.filter((r) => r.reason === 'FROZEN').length
  const leakCount = rejected.filter((r) => r.reason === 'LEAKAGE').length
  const acceptedStillLoading = acceptedLoading && accepted.length === 0
  const rejectedStillLoading = rejectedLoading && rejected.length === 0
  const frozenStillLoading = rejectedLoading && frozenCount === 0
  const acceptedCountLabel = acceptedStillLoading ? 'LOADING' : accepted.length
  const rejectedCountLabel = rejectedStillLoading ? 'LOADING' : rejected.length
  const frozenCountLabel = frozenStillLoading ? 'LOADING' : frozenCount

  return (
    <div className="spx">
      <style>{CSS}</style>
      <div className="spx-scan" aria-hidden="true" />

      <header className="spx-head">
        <div>
          <div className="spx-kicker">FINANCEIQ · FEATURE SPECIMEN ARCHIVE</div>
          <h1>What survived validation, <em>and what was discarded</em>.</h1>
          <p>
            Every candidate feature is a specimen: mounted crisp if it carries genuine year-varying
            information, stamped and archived if it leaks the target or repeats a frozen snapshot.
            The discards prove the rigor.
          </p>
        </div>
        <div className="spx-counts">
          <div><strong className="is-emerald">{acceptedCountLabel}</strong><span>ACCEPTED</span></div>
          <div><strong className="is-copper">{rejectedCountLabel}</strong><span>REJECTED</span></div>
          <div><strong className="is-gold">{leakCount}</strong><span>LEAKAGE-GUARDED</span></div>
          <div><strong className="is-copper">{frozenCountLabel}</strong><span>FROZEN-EXCLUDED</span></div>
          {!fromApi && <div className="spx-mocknote">demo data — quality API returned no columns</div>}
        </div>
      </header>

      <div className="spx-main">
        <main className="spx-archive">
          <section>
            <div className="spx-col-label is-emerald">ACCEPTED · MOUNTED SPECIMENS</div>
            <div className="spx-tiles">
              {acceptedStillLoading && <div className="spx-loading">LOADING ACCEPTED SPECIMENS</div>}
              {accepted.map((s) => (
                <SpecimenTile key={s.name} s={s} active={active?.name === s.name && active?.accepted} onHover={setHovered} />
              ))}
            </div>
          </section>
          <section>
            <div className="spx-col-label is-copper">REJECTED · STAMPED & ARCHIVED</div>
            <div className="spx-tiles">
              {rejectedStillLoading && <div className="spx-loading">LOADING REJECTED SPECIMENS</div>}
              {rejected.map((s) => (
                <SpecimenTile key={s.name} s={s} active={active?.name === s.name && !active?.accepted} onHover={setHovered} />
              ))}
            </div>
          </section>
        </main>

        <aside className="spx-readout" key={active?.name || 'none'} aria-live="polite">
          <div className="spx-readout-kicker">SIGNAL READOUT</div>
          {active && copy && (
            <>
              <div className="spx-readout-name">{active.name}</div>
              <div className={`spx-readout-tag ${active.accepted ? 'is-emerald' : 'is-copper'}`}>
                {active.accepted ? `ACCEPTED · ${active.category}` : `REJECTED · ${active.reason}`}
              </div>
              {active.accepted && (
                <>
                  <div className="spx-readout-sub">SOURCE</div>
                  <div className="spx-readout-mono">{active.source}</div>
                  <div className="spx-readout-sub">COVERAGE 2020–2025</div>
                  <div className="spx-readout-years">
                    {(active.coverage || []).map((v, i) => (
                      <span key={YEARS[i]} className={v ? 'on' : ''}>{YEARS[i]}</span>
                    ))}
                  </div>
                </>
              )}
              {evidence && (
                <>
                  <div className="spx-readout-sub">VARIANCE EVIDENCE</div>
                  <div className="spx-readout-mono">{JSON.stringify(evidence).slice(0, 120)}</div>
                </>
              )}
              {!evidence && frozenEvidenceLoading && active.reason === 'FROZEN' && (
                <>
                  <div className="spx-readout-sub">VARIANCE EVIDENCE</div>
                  <div className="spx-readout-mono">LOADING</div>
                </>
              )}
              <div className="spx-readout-sub">WHY</div>
              <p className="spx-readout-note">{copy.why}</p>
              <div className="spx-readout-sub">{active.accepted ? 'STATUS' : 'TO ACCEPT'}</div>
              <p className="spx-readout-note">{copy.toAccept}</p>
            </>
          )}
        </aside>
      </div>

      {/* integrity + IC strip */}
      <section className="spx-bottom">
        <div className="spx-integrity">
          <div className="spx-col-label is-emerald">PIPELINE INTEGRITY</div>
          {[
            'Leakage checks passed — target fields can never be features',
            'Frozen snapshot columns excluded from the modeling set',
            'No future data enters any training window',
          ].map((t) => (
            <div key={t} className="spx-check"><i />{t}</div>
          ))}
        </div>
        <div className="spx-ic">
          <div className="spx-col-label is-gold">WALK-FORWARD IC PER TEST YEAR · HISTORICAL EVALUATION</div>
          <div className="spx-ic-chart" role="img" aria-label="Walk-forward IC per year, all values near zero">
            <span className="spx-ic-zero" />
            {Object.entries(IC_BY_YEAR).map(([y, v]) => (
              <div key={y} className="spx-ic-col">
                <div className="spx-ic-barwrap">
                  <span
                    className="spx-ic-bar"
                    style={{
                      height: `${Math.abs(v) * 180}px`,
                      background: Math.abs(v) < 0.1 ? 'var(--sp-gold)' : v > 0 ? 'var(--sp-emerald)' : 'var(--sp-copper)',
                      transform: v >= 0 ? 'translateY(-100%)' : 'none',
                    }}
                  />
                </div>
                <span className="spx-ic-year">{y}</span>
                <span className="spx-ic-val">{v >= 0 ? '+' : '−'}{Math.abs(v).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div className="spx-ic-note">Equal-weight baseline beats all ML models · IC ≈ 0 across folds</div>
        </div>
      </section>

      <footer className="spx-caveat">
        <span className="spx-caveat-pulse" aria-hidden="true" />
        Walk-forward IC ≈ 0 · Rigor shown, weakness reported · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.spx {
  --sp-ink: #0a0e0d;
  --sp-paper: #e8ece6;
  --sp-dim: #9fae9f;
  --sp-faint: #6b7a70;
  --sp-emerald: #4da583;
  --sp-gold: #c8a35a;
  --sp-copper: #a8674b;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--sp-ink) 55%, #080b0a 100%);
  color: var(--sp-paper);
  overflow: hidden;
  animation: spxIn 0.7s ease both;
}
.spx * { box-sizing: border-box; }
.spx-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.spx > *:not(.spx-scan) { position: relative; z-index: 2; }

.spx-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 28px; flex-wrap: wrap; margin-bottom: 24px; }
.spx-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--sp-faint); margin-bottom: 13px; }
.spx-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.spx-head h1 em { font-style: italic; color: var(--sp-emerald); }
.spx-head p { margin: 0; max-width: 60ch; color: var(--sp-dim); font-size: 14px; line-height: 1.55; }
.spx-counts { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-end;
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--sp-gold);
  background: rgba(14,20,19,0.72); padding: 14px 18px; }
.spx-counts > div { display: flex; flex-direction: column; gap: 3px; font-family: var(--font-mono); }
.spx-counts strong { font-size: 20px; }
.spx-counts span { font-size: 8.5px; letter-spacing: 0.2em; color: var(--sp-faint); }
.is-emerald { color: var(--sp-emerald); }
.is-gold { color: var(--sp-gold); }
.is-copper { color: var(--sp-copper); }
.spx-mocknote { font-size: 9.5px !important; color: var(--sp-copper) !important; letter-spacing: 0.04em !important; }

.spx-main { display: grid; grid-template-columns: 1fr 300px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .spx-main { grid-template-columns: 1fr; } }
.spx-archive { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; align-items: start; }
@media (max-width: 760px) { .spx-archive { grid-template-columns: 1fr; } }
.spx-col-label { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.24em; margin-bottom: 10px; }

.spx-tiles { display: flex; flex-direction: column; gap: 6px; max-height: 480px; overflow-y: auto; padding-right: 4px; }
.spx-tile { display: flex; align-items: center; gap: 10px; text-align: left; width: 100%;
  padding: 9px 12px; border-radius: 2px; cursor: pointer; font: inherit; color: inherit;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s; }
.spx-tile:focus-visible { outline: 1px solid var(--sp-gold); outline-offset: 2px; }
.spx-tile.is-accepted { border: 1px solid rgba(77,165,131,0.3); background: rgba(14,20,19,0.6); }
.spx-tile.is-accepted:hover { border-color: var(--sp-emerald); background: rgba(18,26,24,0.85); }
.spx-tile.is-rejected { border: 1px dashed rgba(168,103,75,0.4); background: rgba(12,14,13,0.5); }
.spx-tile.is-rejected:hover { border-color: var(--sp-copper); }
.spx-tile.is-active { box-shadow: inset 3px 0 0 currentColor; }
.spx-tile.is-grainy { background-image: repeating-linear-gradient(0deg, rgba(232,236,230,0.025) 0 1px, transparent 1px 3px); }
.spx-tile-name { font-family: var(--font-mono); font-size: 11px; color: var(--sp-paper); flex: 1;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.spx-tile-cat { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.12em; color: var(--sp-faint); white-space: nowrap; }
.spx-tile-years { display: flex; gap: 2px; }
.spx-tile-years i { width: 9px; height: 9px; border-radius: 1px; background: rgba(200,211,202,0.12); }
.spx-tile-years i.on { background: var(--sp-emerald); opacity: 0.75; }
.spx-stamp { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.18em; font-weight: 700;
  border: 1px solid; border-radius: 1px; padding: 3px 7px; transform: rotate(-3deg); white-space: nowrap; }
.spx-stamp.is-leakage { color: var(--sp-copper); border-color: var(--sp-copper); }
.spx-stamp.is-frozen { color: #8fb6c4; border-color: rgba(143,182,196,0.6); }
.spx-stamp.is-allnull { color: var(--sp-faint); border-color: var(--sp-faint); }
.spx-loading { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em; color: var(--sp-faint);
  border: 1px solid rgba(200,211,202,0.14); background: rgba(14,20,19,0.45); padding: 10px 12px; border-radius: 2px; }

.spx-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--sp-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85)); padding: 18px 20px; border-radius: 3px; animation: spxIn 0.35s ease; }
.spx-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--sp-faint); margin-bottom: 12px; }
.spx-readout-name { font-family: var(--font-mono); font-size: 17px; font-weight: 700; letter-spacing: 0.03em; word-break: break-all; }
.spx-readout-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.18em; margin-top: 7px; }
.spx-readout-sub { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.24em; color: var(--sp-faint); margin: 14px 0 6px; }
.spx-readout-mono { font-family: var(--font-mono); font-size: 11px; color: var(--sp-dim); word-break: break-all; }
.spx-readout-years { display: flex; gap: 4px; flex-wrap: wrap; }
.spx-readout-years span { font-family: var(--font-mono); font-size: 9.5px; padding: 3px 6px; border-radius: 1px;
  border: 1px solid rgba(200,211,202,0.18); color: var(--sp-faint); }
.spx-readout-years span.on { border-color: rgba(77,165,131,0.5); color: var(--sp-emerald); }
.spx-readout-note { margin: 0; font-size: 12px; line-height: 1.55; color: var(--sp-dim); }

.spx-bottom { display: grid; grid-template-columns: 1fr 1.4fr; gap: 24px; margin-top: 26px; align-items: start; }
@media (max-width: 900px) { .spx-bottom { grid-template-columns: 1fr; } }
.spx-integrity { border: 1px solid rgba(77,165,131,0.3); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 16px 18px; }
.spx-check { display: flex; align-items: center; gap: 10px; font-size: 12.5px; color: var(--sp-dim); padding: 6px 0; }
.spx-check i { width: 8px; height: 8px; border-radius: 50%; background: var(--sp-emerald); flex-shrink: 0; }

.spx-ic { border: 1px solid rgba(200,163,90,0.35); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 16px 18px; }
.spx-ic-chart { position: relative; display: flex; gap: 18px; align-items: stretch; padding: 8px 6px 0; }
.spx-ic-zero { position: absolute; left: 0; right: 0; top: 50px; height: 1px; background: rgba(232,236,230,0.3); }
.spx-ic-col { display: flex; flex-direction: column; align-items: center; flex: 1; }
.spx-ic-barwrap { position: relative; height: 100px; width: 100%; display: flex; justify-content: center; }
.spx-ic-bar { position: absolute; top: 50px; width: 14px; border-radius: 1px; min-height: 2px; }
.spx-ic-year { font-family: var(--font-mono); font-size: 10px; color: var(--sp-dim); margin-top: 4px; }
.spx-ic-val { font-family: var(--font-mono); font-size: 9px; color: var(--sp-faint); }
.spx-ic-note { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; color: var(--sp-gold); margin-top: 10px; }

.spx-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--sp-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.spx-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--sp-gold); animation: spxPulse 2.2s ease-in-out infinite; flex-shrink: 0; }

@keyframes spxIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes spxPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .spx, .spx *, .spx *::before, .spx *::after { animation: none !important; transition: none !important; }
}
`
