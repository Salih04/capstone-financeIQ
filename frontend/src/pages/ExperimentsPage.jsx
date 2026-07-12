import { useMemo, useState } from 'react'
import { useCachedResource, CACHE_TTL } from '../api/useCachedResource'
import { apiErrorText } from '../api/errorText'
import CacheTag from '../components/CacheTag'

// ---------------------------------------------------------------------------
// Experiments — THE SEISMOGRAPH.
// Each walk-forward fold is a horizontal trace hovering around zero.
// The flat line is the finding: IC ≈ 0, baseline wins, sample too small.
// Real API data (researchApi.experiments); mock is fallback only.
// ---------------------------------------------------------------------------

const EXPERIMENTS_MOCK = {
  folds: [
    { id: 'RF_2020-2022→2023', model: 'Random Forest', train: '2020-2022', test: '2023', ic: 0.03, baseline_ic: 0.05, top10_overlap: 3 },
    { id: 'RF_2021-2023→2024', model: 'Random Forest', train: '2021-2023', test: '2024', ic: 0.08, baseline_ic: 0.09, top10_overlap: 4 },
    { id: 'Lasso_2020-2022→2023', model: 'Lasso', train: '2020-2022', test: '2023', ic: -0.04, baseline_ic: 0.05, top10_overlap: 2 },
    { id: 'Lasso_2021-2023→2024', model: 'Lasso', train: '2021-2023', test: '2024', ic: 0.06, baseline_ic: 0.09, top10_overlap: 3 },
    { id: 'Ensemble_2020-2022→2023', model: 'Ensemble', train: '2020-2022', test: '2023', ic: 0.01, baseline_ic: 0.05, top10_overlap: 3 },
    { id: 'Ensemble_2021-2023→2024', model: 'Ensemble', train: '2021-2023', test: '2024', ic: 0.07, baseline_ic: 0.09, top10_overlap: 4 },
    { id: 'Baseline_2020-2022→2023', model: 'Equal-weight', train: '2020-2022', test: '2023', ic: 0.05, baseline_ic: 0.05, top10_overlap: 5 },
    { id: 'Baseline_2021-2023→2024', model: 'Equal-weight', train: '2021-2023', test: '2024', ic: 0.09, baseline_ic: 0.09, top10_overlap: 5 },
  ],
  verdict: 'No ML model consistently beats the equal-weight baseline. Sample too small for reliable ML edge.',
  mean_ic_all_models: 0.033,
  mean_ic_baseline: 0.070,
}

const MODEL_LABELS = {
  baseline_equal_weight: 'Equal-weight',
  baseline_rank_score: 'Rank baseline',
  linear_regression: 'Linear regression',
  ridge: 'Ridge',
  lasso: 'Lasso',
  elasticnet: 'ElasticNet',
  random_forest: 'Random Forest',
}
const modelLabel = (m) => MODEL_LABELS[m] || String(m || '').replace(/_/g, ' ')
const yearOf = (s) => {
  const m = String(s || '').match(/(20\d{2})/)
  return m ? Number(m[1]) : null
}
const num = (v) => (v === null || v === undefined || Number.isNaN(Number(v)) ? null : Number(v))

// Normalize API leaderboard rows OR mock folds into trace objects:
// [{ model, baseline, points: [{ year, train, ic, baseline_ic, overlap:{hit,of} }] }]
function buildTraces(exp) {
  const rows = (exp?.leaderboard_by_target?.length
    ? exp.leaderboard_by_target.filter((r) => r.target === 'next_year_return_pct')
    : exp?.leaderboard) || []

  if (rows.length > 0) {
    const baselineByYear = {}
    rows.forEach((r) => {
      const y = yearOf(r.split)
      if (r.kind === 'baseline' && y != null && baselineByYear[y] === undefined) {
        baselineByYear[y] = num(r.spearman)
      }
    })
    const byModel = new Map()
    rows.forEach((r) => {
      const y = yearOf(r.split)
      if (y == null) return
      const key = r.model
      if (!byModel.has(key)) byModel.set(key, { model: modelLabel(r.model), baseline: r.kind === 'baseline', points: [] })
      const p5 = num(r.precision_at_5)
      byModel.get(key).points.push({
        year: y,
        train: `≤${y - 1}`,
        ic: num(r.spearman),
        baseline_ic: baselineByYear[y] ?? null,
        overlap: p5 == null ? null : { hit: Math.round(p5 * 5), of: 5 },
      })
    })
    const traces = [...byModel.values()].map((t) => ({ ...t, points: t.points.sort((a, b) => a.year - b.year) }))
    if (traces.length) return { traces, fromApi: true }
  }

  // fallback: mock folds
  const byModel = new Map()
  EXPERIMENTS_MOCK.folds.forEach((f) => {
    if (!byModel.has(f.model)) byModel.set(f.model, { model: f.model, baseline: f.model === 'Equal-weight', points: [] })
    byModel.get(f.model).points.push({
      year: Number(f.test),
      train: f.train,
      ic: f.ic,
      baseline_ic: f.baseline_ic,
      overlap: { hit: f.top10_overlap, of: 10 },
    })
  })
  return { traces: [...byModel.values()], fromApi: false }
}

const fmtIc = (v) => (v == null ? 'N/A' : `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(3)}`)

// ── one seismograph band ────────────────────────────────────────────────────
function TraceBand({ trace, years, hovered, onHover }) {
  const W = 720
  const H = 64
  const MID = H / 2
  const SCALE = 0.5 // IC ±0.5 fills the band
  const px = (year) => {
    if (years.length === 1) return W / 2
    const i = years.indexOf(year)
    return 70 + (i / (years.length - 1)) * (W - 140)
  }
  const py = (ic) => MID - (Math.max(-SCALE, Math.min(SCALE, ic ?? 0)) / SCALE) * (MID - 8)
  const pts = trace.points.filter((p) => p.ic != null)
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${px(p.year)},${py(p.ic)}`).join(' ')
  const color = trace.baseline ? 'var(--xp-gold)' : 'var(--xp-emerald)'

  return (
    <div className={`xp-band ${trace.baseline ? 'is-baseline' : ''}`}>
      <div className="xp-band-label">
        <span className="xp-band-model">{trace.model.toUpperCase()}</span>
        <span className="xp-band-meta">
          {trace.points.map((p) => `${p.train}→${p.year}`).join(' · ')}
        </span>
        {trace.baseline && <span className="xp-band-flag">BASELINE · WINS</span>}
      </div>
      <svg className="xp-band-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
        <line x1={0} y1={MID} x2={W} y2={MID} stroke="rgba(232,236,230,0.3)" strokeWidth="1" />
        <line x1={0} y1={py(0.25)} x2={W} y2={py(0.25)} stroke="rgba(200,211,202,0.08)" strokeDasharray="2 6" />
        <line x1={0} y1={py(-0.25)} x2={W} y2={py(-0.25)} stroke="rgba(200,211,202,0.08)" strokeDasharray="2 6" />
        {pts.length > 1 && <path d={path} fill="none" stroke={color} strokeWidth="1.6" />}
        {pts.map((p) => {
          const active = hovered && hovered.trace === trace.model && hovered.point.year === p.year
          return (
            <circle
              key={p.year}
              cx={px(p.year)}
              cy={py(p.ic)}
              r={active ? 6 : 4}
              fill={color}
              fillOpacity={active ? 1 : 0.7}
              stroke={active ? 'var(--xp-paper)' : color}
              strokeWidth={1}
              style={{ cursor: 'pointer' }}
              tabIndex={0}
              role="button"
              aria-label={`${trace.model}, test ${p.year}, IC ${fmtIc(p.ic)}`}
              onMouseEnter={() => onHover({ trace: trace.model, baseline: trace.baseline, point: p })}
              onFocus={() => onHover({ trace: trace.model, baseline: trace.baseline, point: p })}
            />
          )
        })}
        <text x={W - 6} y={MID - 5} textAnchor="end" className="xp-zero-label">IC 0</text>
      </svg>
    </div>
  )
}

export default function ExperimentsPage() {
  const { data: exp, error, fromCache, refreshing, savedAt, refresh } =
    useCachedResource('/research/experiments', { ttlMs: CACHE_TTL.LONG })
  const [hovered, setHovered] = useState(null)

  const failed = !!error && !exp
  const { traces, fromApi } = useMemo(() => buildTraces(failed ? null : exp), [exp, failed])
  const years = useMemo(
    () => [...new Set(traces.flatMap((t) => t.points.map((p) => p.year)))].sort((a, b) => a - b),
    [traces],
  )

  const meanMl = useMemo(() => {
    const v = traces.filter((t) => !t.baseline).flatMap((t) => t.points.map((p) => p.ic)).filter((x) => x != null)
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
  }, [traces])
  const meanBase = useMemo(() => {
    const v = traces.filter((t) => t.baseline).flatMap((t) => t.points.map((p) => p.ic)).filter((x) => x != null)
    return v.length ? v.reduce((a, b) => a + b, 0) / v.length : null
  }, [traces])

  const verdict = exp?.verdict || EXPERIMENTS_MOCK.verdict
  const active = hovered || (traces[0]?.points[0] ? { trace: traces[0].model, baseline: traces[0].baseline, point: traces[0].points[0] } : null)

  return (
    <div className="xp">
      <style>{CSS}</style>
      <div className="xp-scan" aria-hidden="true" />

      <header className="xp-head">
        <div>
          <div className="xp-kicker">FINANCEIQ · WALK-FORWARD SEISMOGRAPH</div>
          <h1>The trace is flat. <em>That is the finding.</em></h1>
          <p>
            Each band is one model under walk-forward evaluation: train on years 1…N, predict year N+1,
            measure Spearman IC. Traces hover around zero — indistinguishable from noise. The instrument
            records this honestly instead of smoothing it away.
          </p>
        </div>
        <div className="xp-meanbox">
          <div className="xp-mean">
            <span>MEAN IC · ML MODELS</span>
            <strong className="is-copper">{fmtIc(meanMl ?? EXPERIMENTS_MOCK.mean_ic_all_models)}</strong>
          </div>
          <div className="xp-mean">
            <span>MEAN IC · BASELINE</span>
            <strong className="is-gold">{fmtIc(meanBase ?? EXPERIMENTS_MOCK.mean_ic_baseline)}</strong>
          </div>
          <div className="xp-dispersion">
            <strong>−0.17 to +0.22</strong> across test_2023/24/25 · individually indistinguishable
            from zero at n≈40 · source: experiments/leaderboard.csv
          </div>
          {!fromApi && (
            <div className="xp-mocknote">
              demo data — {apiErrorText(error) || 'experiments API returned no folds'}
            </div>
          )}
          <CacheTag fromCache={fromCache} refreshing={refreshing} savedAt={savedAt} onRefresh={refresh} />
        </div>
      </header>

      <div className="xp-main">
        <main className="xp-drum">
          <div className="xp-drum-scale">
            <span>+0.5</span><span>IC 0</span><span>−0.5</span>
          </div>
          {traces.map((t) => (
            <TraceBand key={t.model} trace={t} years={years} hovered={hovered} onHover={setHovered} />
          ))}
        </main>

        <aside className="xp-readout" key={active ? `${active.trace}-${active.point.year}` : 'none'} aria-live="polite">
          <div className="xp-readout-kicker">SIGNAL READOUT</div>
          {active && (
            <>
              <div className="xp-readout-model">{active.trace.toUpperCase()}</div>
              <div className="xp-readout-fold">train {active.point.train} → test {active.point.year}</div>
              <div className="xp-readout-ic" style={{ color: active.baseline ? 'var(--xp-gold)' : Math.abs(active.point.ic ?? 0) < 0.1 ? 'var(--xp-copper)' : 'var(--xp-emerald)' }}>
                {fmtIc(active.point.ic)}
                <em>SPEARMAN IC · THIS FOLD</em>
              </div>
              <div className="xp-readout-row">
                <span>BASELINE IC · SAME FOLD</span>
                <strong>{fmtIc(active.point.baseline_ic)}</strong>
              </div>
              <div className="xp-readout-row">
                <span>Δ VS BASELINE</span>
                <strong style={{ color: active.point.ic != null && active.point.baseline_ic != null && active.point.ic - active.point.baseline_ic >= 0 ? 'var(--xp-emerald)' : 'var(--xp-copper)' }}>
                  {active.point.ic != null && active.point.baseline_ic != null ? fmtIc(active.point.ic - active.point.baseline_ic) : 'N/A'}
                </strong>
              </div>
              <div className="xp-readout-row">
                <span>TOP-{active.point.overlap?.of ?? 'K'} RANK OVERLAP</span>
                <strong>{active.point.overlap ? `${active.point.overlap.hit}/${active.point.overlap.of}` : 'N/A'}</strong>
              </div>
              <p className="xp-readout-note">
                The committed leaderboard spans −0.17 to +0.22 across test_2023/24/25;
                each fold is individually indistinguishable from zero at n≈40. Single-fold
                spikes are noise, not skill.
              </p>
            </>
          )}
        </aside>
      </div>

      <section className="xp-verdict">
        <div className="xp-verdict-label">EXPERIMENT VERDICT</div>
        <p>
          Equal-weight baseline outperforms all ML models on rank correlation. With ~40 stocks/year,
          this is the correct and defensible result.
        </p>
        <p className="xp-verdict-api">{String(verdict)}</p>
      </section>

      <footer className="xp-caveat">
        <span className="xp-caveat-pulse" aria-hidden="true" />
        Walk-forward IC ≈ 0 · range −0.17 to +0.22 · each indistinguishable from zero at n≈40 ·
        Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.xp {
  --xp-ink: #0a0e0d;
  --xp-paper: #e8ece6;
  --xp-dim: #9fae9f;
  --xp-faint: #6b7a70;
  --xp-emerald: #4da583;
  --xp-gold: #c8a35a;
  --xp-copper: #a8674b;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--xp-ink) 55%, #080b0a 100%);
  color: var(--xp-paper);
  overflow: hidden;
  animation: xpIn 0.7s ease both;
}
.xp * { box-sizing: border-box; }
.xp-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.xp > *:not(.xp-scan) { position: relative; z-index: 2; }

.xp-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 32px; flex-wrap: wrap; margin-bottom: 26px; }
.xp-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--xp-faint); margin-bottom: 13px; }
.xp-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.xp-head h1 em { font-style: italic; color: var(--xp-emerald); }
.xp-head p { margin: 0; max-width: 62ch; color: var(--xp-dim); font-size: 14px; line-height: 1.55; }
.xp-meanbox { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--xp-gold);
  background: rgba(14,20,19,0.72); padding: 14px 16px; min-width: 240px; }
.xp-mean { display: flex; justify-content: space-between; align-items: baseline; gap: 18px; font-family: var(--font-mono); margin-bottom: 8px; }
.xp-mean span { font-size: 9.5px; letter-spacing: 0.18em; color: var(--xp-faint); }
.xp-mean strong { font-size: 17px; }
.xp-mean .is-gold { color: var(--xp-gold); }
.xp-mean .is-copper { color: var(--xp-copper); }
.xp-dispersion { max-width: 34ch; border-top: 1px dashed rgba(200,211,202,0.16); padding-top: 8px;
  font-family: var(--font-mono); font-size: 9.5px; line-height: 1.5; color: var(--xp-dim); }
.xp-dispersion strong { color: var(--xp-paper); font-weight: 600; }
.xp-mocknote { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.06em; color: var(--xp-copper); border-top: 1px dashed rgba(168,103,75,0.4); padding-top: 8px; }

.xp-main { display: grid; grid-template-columns: 1fr 300px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .xp-main { grid-template-columns: 1fr; } }

.xp-drum { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 14px 16px; position: relative; }
.xp-drum-scale { display: flex; flex-direction: column; justify-content: space-between; position: absolute; left: 16px; top: 14px; bottom: 14px;
  font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.2em; color: var(--xp-faint); pointer-events: none; opacity: 0.6; }
.xp-band { display: grid; grid-template-columns: 190px 1fr; gap: 14px; align-items: center;
  border-bottom: 1px solid rgba(200,211,202,0.08); padding: 6px 0 6px 44px; }
.xp-band:last-child { border-bottom: 0; }
.xp-band.is-baseline { background: rgba(200,163,90,0.04); }
.xp-band-label { display: flex; flex-direction: column; gap: 3px; }
.xp-band-model { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.14em; color: var(--xp-paper); }
.xp-band-meta { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.04em; color: var(--xp-faint); }
.xp-band-flag { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.2em; color: var(--xp-gold); }
.xp-band-svg { width: 100%; height: 64px; display: block;
  background:
    repeating-linear-gradient(0deg, rgba(232,236,230,0.018) 0 1px, transparent 1px 5px),
    rgba(8,11,10,0.4);
  border-radius: 2px; }
.xp-band-svg circle { outline: none; transition: r 0.15s; }
.xp-band-svg circle:focus-visible { stroke: var(--xp-paper); stroke-width: 2; }
.xp-zero-label { font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.2em; fill: var(--xp-faint); }

.xp-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--xp-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85)); padding: 18px 20px; border-radius: 3px; animation: xpIn 0.35s ease; }
.xp-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--xp-faint); margin-bottom: 12px; }
.xp-readout-model { font-family: var(--font-mono); font-size: 17px; font-weight: 700; letter-spacing: 0.06em; }
.xp-readout-fold { font-family: var(--font-mono); font-size: 10.5px; color: var(--xp-dim); margin-top: 4px; letter-spacing: 0.04em; }
.xp-readout-ic { margin: 14px 0 16px; display: flex; flex-direction: column; gap: 3px; font-family: var(--font-mono); font-size: 34px; line-height: 1; }
.xp-readout-ic em { font-style: normal; font-size: 9px; letter-spacing: 0.2em; color: var(--xp-faint); }
.xp-readout-row { display: flex; justify-content: space-between; gap: 12px; font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.1em; color: var(--xp-dim); border-top: 1px dashed rgba(200,211,202,0.14); padding: 8px 0; }
.xp-readout-row strong { color: var(--xp-paper); font-size: 12px; }
.xp-readout-note { margin: 12px 0 0; font-size: 11.5px; line-height: 1.55; color: var(--xp-dim); }

.xp-verdict { margin-top: 24px; border: 1px solid rgba(200,163,90,0.4); border-left: 3px solid var(--xp-gold);
  background: rgba(14,20,19,0.6); border-radius: 3px; padding: 16px 20px; max-width: 860px; }
.xp-verdict-label { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.28em; color: var(--xp-gold); margin-bottom: 9px; }
.xp-verdict p { margin: 0 0 8px; font-size: 13.5px; line-height: 1.6; color: var(--xp-paper); }
.xp-verdict-api { font-family: var(--font-mono); font-size: 11px !important; color: var(--xp-dim) !important; }

.xp-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--xp-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.xp-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--xp-gold); animation: xpPulse 2.2s ease-in-out infinite; }

@keyframes xpIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes xpPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .xp, .xp *, .xp *::before, .xp *::after { animation: none !important; transition: none !important; }
}
`
