import { useCallback, useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Building2 } from 'lucide-react'
import { EmptyState } from '../components/ui'
import { cachedGet, CACHE_TTL } from '../api/cache'
import CacheTag from '../components/CacheTag'
import { humanizeWarning, asText } from '../utils/safeRender'

// ---------------------------------------------------------------------------
// Company detail — THE COMPANY SIGNAL AUTOPSY.
// One ticker removed from the universe map and placed under the lens:
// score dissected into calibrated rails, features mounted as evidence strips,
// the agent explanation rendered as a transcript. Real API data preserved
// (researchApi.company / companyScore); no mock substitution.
// ---------------------------------------------------------------------------

const hw = (items) => (Array.isArray(items) ? items.map(humanizeWarning) : [])

const pctOf = (v) => {
  const n = Number(v)
  if (!Number.isFinite(n)) return null
  return Math.max(0, Math.min(100, n <= 1 ? n * 100 : n))
}
const fmtVal = (v) => {
  const n = Number(v)
  if (!Number.isFinite(n)) return asText(v)
  return n <= 1 ? n.toFixed(2) : n.toFixed(1)
}

const RAIL_WHY = {
  ml: 'Rank of validated year-T features against the universe. Ranking signal only — walk-forward IC ≈ 0.',
  confidence: 'How complete and trustworthy the underlying data is for this ticker. Drives crisp vs grainy rendering.',
  llm: 'Optional evidence-support layer. When unavailable, the final score relies on fundamentals + confidence alone.',
  final: 'Weighted composite of the layers above. Diagnostic, not predictive.',
}

function railColor(pct, kind) {
  if (pct == null) return 'var(--ca-faint)'
  if (kind === 'confidence') return pct >= 60 ? 'var(--ca-emerald)' : pct >= 35 ? 'var(--ca-gold)' : 'var(--ca-copper)'
  return pct >= 60 ? 'var(--ca-emerald)' : pct >= 40 ? 'var(--ca-gold)' : 'var(--ca-copper)'
}

export default function CompanyResearchDetailPage() {
  const { ticker } = useParams()
  const nav = useNavigate()
  const [detail, setDetail] = useState(null)
  const [score, setScore] = useState(null)
  const [err, setErr] = useState(null)
  const [focus, setFocus] = useState(null) // {type:'rail'|'feature', ...}
  const [meta, setMeta] = useState({ fromCache: false, refreshing: false, savedAt: null })

  // Per-ticker cache keys (path-based) — ASELS and THYAO never collide.
  const load = useCallback(async (force = false) => {
    const enc = encodeURIComponent(ticker)
    const rd = await cachedGet(`/research/company/${enc}`, undefined, { ttlMs: CACHE_TTL.MEDIUM, forceRefresh: force })
    if (rd.value !== undefined) { setDetail(rd.value); setErr(null) } else if (rd.error) setErr(rd.error)
    setMeta({ fromCache: rd.fromCache, refreshing: !!rd.refreshing, savedAt: rd.savedAt })
    const rs = await cachedGet(`/research/company/${enc}/score`, undefined, { ttlMs: CACHE_TTL.MEDIUM, forceRefresh: force })
    if (rs.value !== undefined) setScore(rs.value)
    // background revalidation (stale-while-revalidate)
    if (rd.revalidate) { const f = await rd.revalidate; if (f) { setDetail(f); setMeta((m) => ({ ...m, fromCache: false, refreshing: false, savedAt: Date.now() })) } }
    if (rs.revalidate) { const f = await rs.revalidate; if (f) setScore(f) }
  }, [ticker])

  useEffect(() => { load(false) }, [load])

  if (err) return <EmptyState icon={Building2} title={`${ticker} not found`} description={asText(err)} />

  const ctx = detail?.context || {}
  const sc = score?.score || {}
  const llm = score?.llm || {}
  const tk = String(ticker || '').toUpperCase()

  const rails = [
    { key: 'ml', label: 'ML SCORE', value: sc.ml_score },
    { key: 'confidence', label: 'CONFIDENCE', value: sc.confidence_score },
    { key: 'llm', label: 'LLM SUPPORT', value: sc.llm_research_score },
    { key: 'final', label: 'FINAL RESEARCH SCORE', value: sc.final_research_score, final: true },
  ]
  const positives = Object.entries(ctx.top_positive_features || {})
  const negatives = Object.entries(ctx.top_negative_features || {})
  const limitations = hw(sc.limitations || llm.limitations)
  const warnings = hw(sc.warnings || ctx.warnings)
  const finalPct = pctOf(sc.final_research_score)
  const lowConfidence = (pctOf(sc.confidence_score) ?? 100) < 50

  return (
    <div className={`ca ${lowConfidence ? 'is-grainy-specimen' : ''}`}>
      <style>{CSS}</style>
      <div className="ca-scan" aria-hidden="true" />

      {/* ── specimen header ── */}
      <header className="ca-head">
        <div>
          <div className="ca-kicker">FINANCEIQ · COMPANY SIGNAL AUTOPSY</div>
          <h1>{tk} under the lens. <em>Signal, evidence, uncertainty.</em></h1>
          <div className="ca-tags">
            <span className="ca-tag is-emerald">VALIDATED DATA</span>
            {ctx.is_inference_row && <span className="ca-tag is-gold">INFERENCE-ONLY · NO REALIZED T+1 OUTCOME</span>}
            <span className="ca-tag is-copper">NOT INVESTMENT ADVICE</span>
          </div>
        </div>
        <div className="ca-specimen-label">
          <span className="ca-specimen-row"><span>SPECIMEN</span><strong>{tk}</strong></span>
          <span className="ca-specimen-row"><span>LATEST YEAR</span><strong>{asText(ctx.latest_year)}</strong></span>
          <span className="ca-specimen-row"><span>ROW TYPE</span><strong>{ctx.is_inference_row ? 'INFERENCE' : 'HISTORICAL'}</strong></span>
          <button type="button" className="ca-back" onClick={() => nav('/research/companies')}>
            ← RETURN TO UNIVERSE
          </button>
          <div className="ca-cachetag"><CacheTag fromCache={meta.fromCache} refreshing={meta.refreshing} savedAt={meta.savedAt} onRefresh={() => load(true)} /></div>
        </div>
      </header>

      <div className="ca-main">
        <main className="ca-body">
          {/* ── score anatomy ── */}
          <section className="ca-panel">
            <div className="ca-panel-label">SCORE ANATOMY · DISSECTED LAYERS</div>
            {rails.map((r) => {
              const pct = pctOf(r.value)
              const color = railColor(pct, r.key)
              const on = focus?.type === 'rail' && focus.key === r.key
              return (
                <button
                  key={r.key}
                  type="button"
                  className={`ca-rail ${r.final ? 'is-final' : ''} ${on ? 'is-on' : ''} ${pct == null ? 'is-null' : ''}`}
                  onMouseEnter={() => setFocus({ type: 'rail', key: r.key, label: r.label, value: r.value, pct, color })}
                  onFocus={() => setFocus({ type: 'rail', key: r.key, label: r.label, value: r.value, pct, color })}
                >
                  <span className="ca-rail-label">{r.label}</span>
                  <span className="ca-rail-track">
                    {[25, 50, 75].map((t) => <i key={t} className="ca-rail-tick" style={{ left: `${t}%` }} />)}
                    {pct == null
                      ? <span className="ca-rail-nodata">NO DATA — WEIGHT FOLDED INTO REMAINING LAYERS</span>
                      : <span className="ca-rail-fill" style={{ width: `${pct}%`, background: color }} />}
                  </span>
                  <span className="ca-rail-val" style={{ color }}>{pct == null ? '—' : fmtVal(r.value)}</span>
                </button>
              )
            })}
            <p className="ca-panel-note">Diagnostic layers, not a prediction. Walk-forward IC ≈ 0 across the universe.</p>
          </section>

          {/* ── feature evidence field ── */}
          <section className="ca-panel">
            <div className="ca-panel-label">FEATURE EVIDENCE · MOUNTED STRIPS</div>
            <div className="ca-evidence">
              <div className="ca-evidence-rail is-pos">
                <span className="ca-evidence-railname">POSITIVE SIGNALS ↑</span>
                <div className="ca-evidence-strips">
                  {positives.length === 0 && <span className="ca-evidence-empty">none recorded</span>}
                  {positives.map(([name, val]) => (
                    <button key={name} type="button"
                      className={`ca-strip is-pos ${focus?.type === 'feature' && focus.name === name ? 'is-on' : ''}`}
                      onMouseEnter={() => setFocus({ type: 'feature', name, value: val, dir: 'positive' })}
                      onFocus={() => setFocus({ type: 'feature', name, value: val, dir: 'positive' })}>
                      {name}
                    </button>
                  ))}
                </div>
              </div>
              <div className="ca-evidence-zero" />
              <div className="ca-evidence-rail is-neg">
                <div className="ca-evidence-strips">
                  {negatives.length === 0 && <span className="ca-evidence-empty">none recorded</span>}
                  {negatives.map(([name, val]) => (
                    <button key={name} type="button"
                      className={`ca-strip is-neg ${focus?.type === 'feature' && focus.name === name ? 'is-on' : ''}`}
                      onMouseEnter={() => setFocus({ type: 'feature', name, value: val, dir: 'negative' })}
                      onFocus={() => setFocus({ type: 'feature', name, value: val, dir: 'negative' })}>
                      {name}
                    </button>
                  ))}
                </div>
                <span className="ca-evidence-railname">NEGATIVE SIGNALS ↓</span>
              </div>
            </div>
          </section>

          {/* ── agent transcript ── */}
          <section className="ca-panel">
            <div className="ca-panel-label">RESEARCH AGENT · EVIDENCE TRANSCRIPT</div>
            <div className="ca-transcript">
              <div className="ca-block">
                <div className="ca-block-tag">SUMMARY</div>
                <p>{asText(llm.summary)}</p>
              </div>
              {llm.reasoning && (
                <div className="ca-block">
                  <div className="ca-block-tag">EVIDENCE</div>
                  <p>{asText(llm.reasoning)}</p>
                </div>
              )}
              {(limitations.length > 0 || warnings.length > 0) && (
                <div className="ca-block is-warn">
                  <div className="ca-block-tag">LIMITATIONS</div>
                  <ul>
                    {limitations.map((l, i) => <li key={`l${i}`}>{asText(l)}</li>)}
                    {warnings.map((w, i) => <li key={`w${i}`}>{asText(w)}</li>)}
                  </ul>
                </div>
              )}
              <div className="ca-block is-meta">
                <div className="ca-block-tag">SOURCE / MODEL CONTEXT</div>
                <div className="ca-meta-grid">
                  <span>PROVIDER</span><strong>{asText(score?.provider_used)}</strong>
                  <span>FALLBACK</span><strong>{asText(score?.fallback_used)}</strong>
                  <span>MODEL</span><strong>{asText(sc.model_name)}</strong>
                  <span>TARGET</span><strong>{asText(sc.target_name)}</strong>
                  <span>SCORE SOURCE</span><strong>{asText(sc.score_source)}</strong>
                </div>
              </div>
            </div>
          </section>
        </main>

        {/* ── Signal Readout ── */}
        <aside className="ca-readout" key={focus ? `${focus.type}-${focus.key || focus.name}` : 'resting'} aria-live="polite">
          <div className="ca-readout-kicker">SIGNAL READOUT</div>
          {!focus && (
            <>
              <div className="ca-readout-name">{tk}</div>
              <div className="ca-readout-big" style={{ color: railColor(finalPct, 'final') }}>
                {finalPct == null ? '—' : fmtVal(sc.final_research_score)}
                <em>FINAL RESEARCH SCORE</em>
              </div>
              <div className="ca-readout-row"><span>CONFIDENCE</span><strong>{asText(sc.confidence_level || sc.confidence_score)}</strong></div>
              <div className="ca-readout-row"><span>LATEST YEAR</span><strong>{asText(ctx.latest_year)}</strong></div>
              <div className="ca-readout-row"><span>MODEL</span><strong>{asText(sc.model_name)}</strong></div>
              <div className="ca-readout-row"><span>SOURCE</span><strong>{asText(sc.score_source)}</strong></div>
              <div className="ca-readout-warn">HISTORICAL RANKING SIGNAL ONLY</div>
            </>
          )}
          {focus?.type === 'rail' && (
            <>
              <div className="ca-readout-name">{focus.label}</div>
              <div className="ca-readout-big" style={{ color: focus.color }}>
                {focus.pct == null ? 'N/A' : fmtVal(focus.value)}
                <em>{focus.pct == null ? 'LAYER UNAVAILABLE' : 'CALIBRATED 0–100 RAIL'}</em>
              </div>
              <p className="ca-readout-note">{RAIL_WHY[focus.key]}</p>
              {focus.key === 'llm' && focus.pct == null && (
                <p className="ca-readout-note">LLM evidence missing — final score uses fundamentals + data confidence only.</p>
              )}
            </>
          )}
          {focus?.type === 'feature' && (
            <>
              <div className="ca-readout-name" style={{ fontSize: 16 }}>{focus.name}</div>
              <div className="ca-readout-big" style={{ color: focus.dir === 'positive' ? 'var(--ca-emerald)' : 'var(--ca-copper)' }}>
                {fmtVal(focus.value)}
                <em>{focus.dir === 'positive' ? 'POSITIVE EVIDENCE STRIP' : 'NEGATIVE EVIDENCE STRIP'}</em>
              </div>
              <p className="ca-readout-note">
                Percentile rank of this validated year-T feature within the universe. It moved the ranking{' '}
                {focus.dir === 'positive' ? 'upward' : 'downward'} — historically, not predictively.
              </p>
            </>
          )}
        </aside>
      </div>

      <footer className="ca-caveat">
        <span className="ca-caveat-pulse" aria-hidden="true" />
        Company research snapshot · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.ca {
  --ca-ink: #0a0e0d; --ca-paper: #e8ece6; --ca-dim: #9fae9f; --ca-faint: #6b7a70;
  --ca-emerald: #4da583; --ca-gold: #c8a35a; --ca-copper: #a8674b;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(900px 480px at 70% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--ca-ink) 55%, #080b0a 100%);
  color: var(--ca-paper); overflow: hidden; animation: caIn 0.7s ease both;
}
.ca * { box-sizing: border-box; }
.ca-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.ca > *:not(.ca-scan) { position: relative; z-index: 2; }
.ca.is-grainy-specimen .ca-body { filter: contrast(0.97); }

/* ── specimen header ── */
.ca-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 30px; flex-wrap: wrap; margin-bottom: 24px; }
.ca-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--ca-faint); margin-bottom: 13px; }
.ca-head h1 { margin: 0 0 14px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.ca-head h1 em { font-style: italic; color: var(--ca-emerald); }
.ca-tags { display: flex; gap: 8px; flex-wrap: wrap; }
.ca-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.18em; border: 1px solid; border-radius: 2px; padding: 4px 9px; }
.ca-tag.is-emerald { color: var(--ca-emerald); border-color: rgba(77,165,131,0.5); }
.ca-tag.is-gold { color: var(--ca-gold); border-color: rgba(200,163,90,0.5); }
.ca-tag.is-copper { color: var(--ca-copper); border-color: rgba(168,103,75,0.5); }
.ca-specimen-label {
  border: 1px solid rgba(200,211,202,0.2); border-left: 3px solid var(--ca-gold);
  background: rgba(14,20,19,0.75); padding: 14px 16px; min-width: 250px;
  display: flex; flex-direction: column; gap: 7px;
  background-image: repeating-linear-gradient(0deg, rgba(232,236,230,0.012) 0 1px, transparent 1px 4px);
}
.ca-specimen-row { display: flex; justify-content: space-between; gap: 16px; font-family: var(--font-mono); }
.ca-specimen-row span { font-size: 9px; letter-spacing: 0.2em; color: var(--ca-faint); }
.ca-specimen-row strong { font-size: 12px; color: var(--ca-paper); letter-spacing: 0.04em; }
.ca-back { margin-top: 8px; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.18em;
  background: transparent; color: var(--ca-emerald); border: 1px solid rgba(77,165,131,0.5); border-radius: 2px;
  padding: 8px 0; cursor: pointer; transition: background 0.18s, box-shadow 0.18s, transform 0.1s; }
.ca-back:hover { background: rgba(77,165,131,0.1); box-shadow: 0 0 14px rgba(77,165,131,0.18); }
.ca-back:active { transform: translateY(1px); }
.ca-back:focus-visible { outline: 1px solid var(--ca-emerald); outline-offset: 2px; }
.ca-cachetag { display: flex; justify-content: flex-end; margin-top: 6px; }

/* ── layout ── */
.ca-main { display: grid; grid-template-columns: 1fr 300px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .ca-main { grid-template-columns: 1fr; } }
.ca-body { display: flex; flex-direction: column; gap: 18px; }
.ca-panel { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 18px 20px; }
.ca-panel-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.28em; color: var(--ca-faint); margin-bottom: 14px; }
.ca-panel-note { margin: 12px 0 0; font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.06em; color: var(--ca-gold); }

/* ── score rails ── */
.ca-rail { display: grid; grid-template-columns: 190px 1fr 64px; gap: 14px; align-items: center; width: 100%;
  padding: 10px 12px; margin-bottom: 6px; border: 1px solid rgba(200,211,202,0.12); border-radius: 2px;
  background: rgba(14,20,19,0.55); color: inherit; font: inherit; text-align: left; cursor: pointer;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s; }
.ca-rail:hover, .ca-rail:focus-visible { border-color: rgba(77,165,131,0.5); background: rgba(18,26,24,0.8); outline: none; }
.ca-rail.is-on { border-color: var(--ca-emerald); box-shadow: inset 3px 0 0 var(--ca-emerald); }
.ca-rail.is-final { border-color: rgba(200,163,90,0.4); background: rgba(20,26,22,0.7); }
.ca-rail.is-final.is-on { border-color: var(--ca-gold); box-shadow: inset 3px 0 0 var(--ca-gold); }
.ca-rail.is-null { border-style: dashed; }
.ca-rail-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em; color: var(--ca-dim); }
.ca-rail.is-final .ca-rail-label { color: var(--ca-paper); }
.ca-rail-track { position: relative; height: 9px; background: rgba(200,211,202,0.07); border-radius: 1px; overflow: hidden; }
.ca-rail-tick { position: absolute; top: 0; bottom: 0; width: 1px; background: rgba(200,211,202,0.18); }
.ca-rail-fill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 1px; transition: width 0.6s ease; }
.ca-rail-nodata { position: absolute; inset: 0; display: flex; align-items: center; padding-left: 8px;
  font-family: var(--font-mono); font-size: 7.5px; letter-spacing: 0.14em; color: var(--ca-copper); }
.ca-rail-val { font-family: var(--font-mono); font-size: 13px; font-weight: 700; text-align: right; }

/* ── evidence field ── */
.ca-evidence { display: flex; flex-direction: column; gap: 0; }
.ca-evidence-rail { display: flex; flex-direction: column; gap: 8px; padding: 10px 0; }
.ca-evidence-railname { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.24em; color: var(--ca-faint); }
.ca-evidence-zero { height: 1px; background: rgba(232,236,230,0.25); margin: 2px 0; }
.ca-evidence-strips { display: flex; gap: 7px; flex-wrap: wrap; }
.ca-evidence-empty { font-family: var(--font-mono); font-size: 10px; color: var(--ca-faint); }
.ca-strip { font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.04em;
  border-radius: 2px; padding: 6px 11px; cursor: pointer; color: var(--ca-paper);
  transition: box-shadow 0.15s, border-color 0.15s, transform 0.1s; }
.ca-strip:active { transform: translateY(1px); }
.ca-strip:focus-visible { outline: 1px solid currentColor; outline-offset: 2px; }
.ca-strip.is-pos { background: rgba(77,165,131,0.1); border: 1px solid rgba(77,165,131,0.45); }
.ca-strip.is-pos:hover, .ca-strip.is-pos.is-on { box-shadow: 0 0 12px rgba(77,165,131,0.25); border-color: var(--ca-emerald); }
.ca-strip.is-neg { background: rgba(168,103,75,0.1); border: 1px dashed rgba(168,103,75,0.5); }
.ca-strip.is-neg:hover, .ca-strip.is-neg.is-on { box-shadow: 0 0 12px rgba(168,103,75,0.25); border-color: var(--ca-copper); }

/* ── transcript ── */
.ca-transcript { display: flex; flex-direction: column; gap: 12px; }
.ca-block { border-left: 2px solid rgba(77,165,131,0.5); padding: 2px 0 2px 14px; }
.ca-block.is-warn { border-left-color: rgba(200,163,90,0.55); }
.ca-block.is-meta { border-left-color: rgba(200,211,202,0.25); }
.ca-block-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.26em; color: var(--ca-faint); margin-bottom: 6px; }
.ca-block p { margin: 0; font-size: 13px; line-height: 1.65; color: var(--ca-paper); white-space: pre-wrap; }
.ca-block ul { margin: 0; padding-left: 16px; font-size: 12px; line-height: 1.65; color: var(--ca-dim); }
.ca-meta-grid { display: grid; grid-template-columns: auto 1fr; gap: 4px 18px; font-family: var(--font-mono); }
.ca-meta-grid span { font-size: 9px; letter-spacing: 0.18em; color: var(--ca-faint); align-self: center; }
.ca-meta-grid strong { font-size: 11px; color: var(--ca-dim); word-break: break-all; }

/* ── readout ── */
.ca-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--ca-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85));
  padding: 18px 20px; border-radius: 3px; animation: caIn 0.35s ease; }
.ca-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--ca-faint); margin-bottom: 12px; }
.ca-readout-name { font-family: var(--font-mono); font-size: 24px; font-weight: 700; letter-spacing: 0.04em; word-break: break-all; }
.ca-readout-big { font-family: var(--font-mono); font-size: 34px; line-height: 1; margin: 12px 0 14px;
  display: flex; flex-direction: column; gap: 4px; }
.ca-readout-big em { font-style: normal; font-size: 9px; letter-spacing: 0.2em; color: var(--ca-faint); }
.ca-readout-row { display: flex; justify-content: space-between; gap: 12px; font-family: var(--font-mono);
  font-size: 10px; letter-spacing: 0.1em; color: var(--ca-dim);
  border-top: 1px dashed rgba(200,211,202,0.14); padding: 8px 0; }
.ca-readout-row strong { color: var(--ca-paper); font-size: 11.5px; text-align: right; word-break: break-all; }
.ca-readout-warn { margin-top: 12px; font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.18em;
  color: var(--ca-gold); border: 1px solid rgba(200,163,90,0.45); border-radius: 2px; padding: 7px 10px; }
.ca-readout-note { margin: 10px 0 0; font-size: 12px; line-height: 1.6; color: var(--ca-dim); }

/* ── caveat ── */
.ca-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--ca-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.ca-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--ca-gold); animation: caPulse 2.2s ease-in-out infinite; flex-shrink: 0; }

@keyframes caIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes caPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .ca, .ca *, .ca *::before, .ca *::after { animation: none !important; transition: none !important; }
}
`
