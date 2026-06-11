import { useEffect, useMemo, useState } from 'react'
import { researchApi } from '../api/researchApi'

// ---------------------------------------------------------------------------
// Benchmark — THE TIDE CHART.
// Two water levels, 2020–2024: BIST100 and Model Top-10. 2022 is the tsunami.
// The gap between them fills emerald (model above) or copper (below).
// IC markers float over each year — all near zero. That is the honest story.
// Real BIST100 returns come from the API when available; the model series
// and IC are the project's historical evaluation constants.
// ---------------------------------------------------------------------------

const BENCHMARK_MOCK = [
  { year: 2020, bist100: 28.4, model_top10: 31.2, excess: 2.8, ic: 0.08, outperform_count: 6 },
  { year: 2021, bist100: 19.1, model_top10: 14.7, excess: -4.4, ic: -0.11, outperform_count: 4 },
  { year: 2022, bist100: 196.3, model_top10: 188.9, excess: -7.4, ic: -0.14, outperform_count: 4 },
  { year: 2023, bist100: 43.8, model_top10: 51.2, excess: 7.4, ic: 0.03, outperform_count: 7 },
  { year: 2024, bist100: 31.2, model_top10: 38.7, excess: 7.5, ic: 0.12, outperform_count: 7 },
]

const fmtPct = (v) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(1)}%`
const fmtIc = (v) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(2)}`
// sign-preserving log compression so 2022's +196% stays on the page
const tlog = (v) => Math.sign(v) * Math.log10(1 + Math.abs(v))

export default function BenchmarkPage() {
  const [api, setApi] = useState(null)
  const [hovered, setHovered] = useState(null)

  useEffect(() => {
    researchApi.benchmark().then((r) => setApi(r.data)).catch(() => {})
  }, [])

  // merge: live BIST100 returns override mock when present
  const rows = useMemo(() => {
    const live = api?.returns_by_year || {}
    return BENCHMARK_MOCK.map((r) => {
      const v = Number(live[r.year])
      return Number.isFinite(v) ? { ...r, bist100: v, excess: +(r.model_top10 - v).toFixed(1) } : r
    })
  }, [api])

  const active = rows.find((r) => r.year === hovered) || rows[rows.length - 1]
  const beat = rows.filter((r) => r.excess > 0).length

  // ── chart geometry ──
  const W = 720
  const H = 300
  const PAD_L = 56
  const PAD_R = 24
  const TOP = 56     // room for IC markers
  const BOT = H - 34
  const maxT = Math.max(...rows.flatMap((r) => [tlog(r.bist100), tlog(r.model_top10)])) * 1.08
  const px = (i) => PAD_L + (i / (rows.length - 1)) * (W - PAD_L - PAD_R)
  const py = (v) => BOT - (Math.max(tlog(v), 0) / maxT) * (BOT - TOP)

  const areaPath = (key) =>
    `M${px(0)},${BOT} ` +
    rows.map((r, i) => `L${px(i)},${py(r[key])}`).join(' ') +
    ` L${px(rows.length - 1)},${BOT} Z`

  return (
    <div className="td">
      <style>{CSS}</style>
      <div className="td-scan" aria-hidden="true" />

      <header className="td-head">
        <div>
          <div className="td-kicker">FINANCEIQ · BENCHMARK TIDE CHART</div>
          <h1>Two tides, one <em>honest</em> gap.</h1>
          <p>
            BIST100 versus the model's top-10 basket, 2020–2024. The model finishes above the index in{' '}
            {beat}/5 years — but with walk-forward IC ≈ 0, that gap is not evidence of ranking skill.
            Both readings stay on the chart.
          </p>
        </div>
        <div className="td-legend">
          <span><i className="td-dot is-gold" /> BIST100</span>
          <span><i className="td-dot is-emerald" /> MODEL TOP-10</span>
          <span><i className="td-dot is-copper" /> IC MARKER (SIZE = |IC|)</span>
          {api?.available === false && <span className="td-mocknote">benchmark API unavailable — evaluation constants shown</span>}
        </div>
      </header>

      <div className="td-main">
        <main className="td-chartbox">
          <svg className="td-svg" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet"
            role="img" aria-label="BIST100 versus model top-10 annual returns, 2020 to 2024, log scale">
            {/* gridlines at 10/50/200% */}
            {[10, 50, 200].map((g) => (
              <g key={g}>
                <line x1={PAD_L} y1={py(g)} x2={W - PAD_R} y2={py(g)} stroke="rgba(200,211,202,0.1)" strokeDasharray="2 7" />
                <text x={PAD_L - 6} y={py(g) + 3} textAnchor="end" className="td-axis">+{g}%</text>
              </g>
            ))}
            <line x1={PAD_L} y1={BOT} x2={W - PAD_R} y2={BOT} stroke="rgba(200,211,202,0.3)" />
            <text x={PAD_L - 6} y={BOT + 3} textAnchor="end" className="td-axis">0%</text>
            <text x={W - PAD_R} y={TOP - 38} textAnchor="end" className="td-axis">LOG-COMPRESSED SCALE · 2022 IS REAL, NOT AN ERROR</text>

            {/* differential band, segment by segment */}
            {rows.slice(0, -1).map((r, i) => {
              const n = rows[i + 1]
              const above = (r.model_top10 - r.bist100 + n.model_top10 - n.bist100) / 2 >= 0
              return (
                <polygon
                  key={r.year}
                  points={`${px(i)},${py(r.bist100)} ${px(i + 1)},${py(n.bist100)} ${px(i + 1)},${py(n.model_top10)} ${px(i)},${py(r.model_top10)}`}
                  fill={above ? 'rgba(77,165,131,0.28)' : 'rgba(168,103,75,0.3)'}
                />
              )
            })}

            {/* water bodies */}
            <path d={areaPath('bist100')} fill="rgba(200,163,90,0.10)" stroke="none" />
            <path d={areaPath('model_top10')} fill="rgba(77,165,131,0.08)" stroke="none" />
            <polyline points={rows.map((r, i) => `${px(i)},${py(r.bist100)}`).join(' ')}
              fill="none" stroke="#c8a35a" strokeWidth="1.8" />
            <polyline points={rows.map((r, i) => `${px(i)},${py(r.model_top10)}`).join(' ')}
              fill="none" stroke="#4da583" strokeWidth="1.8" />

            {/* IC markers floating above */}
            {rows.map((r, i) => (
              <g key={`ic${r.year}`}>
                <line x1={px(i)} y1={TOP - 18} x2={px(i)} y2={py(Math.max(r.bist100, r.model_top10))}
                  stroke="rgba(200,211,202,0.08)" />
                <circle cx={px(i)} cy={TOP - 18} r={3 + Math.abs(r.ic) * 36}
                  fill={r.ic >= 0 ? 'rgba(77,165,131,0.5)' : 'rgba(168,103,75,0.55)'}
                  stroke={r.ic >= 0 ? '#4da583' : '#a8674b'} strokeWidth="1" />
                <text x={px(i)} y={TOP - 32} textAnchor="middle" className="td-icnum">{fmtIc(r.ic)}</text>
              </g>
            ))}

            {/* year hit zones + labels */}
            {rows.map((r, i) => {
              const on = active.year === r.year
              return (
                <g key={`y${r.year}`}>
                  <rect
                    x={px(i) - (W - PAD_L - PAD_R) / (rows.length - 1) / 2}
                    y={TOP - 40} width={(W - PAD_L - PAD_R) / (rows.length - 1)} height={BOT - TOP + 60}
                    fill="transparent" style={{ cursor: 'pointer' }}
                    tabIndex={0} role="button" aria-label={`Year ${r.year}`}
                    onMouseEnter={() => setHovered(r.year)} onFocus={() => setHovered(r.year)}
                  />
                  {on && <line x1={px(i)} y1={TOP - 12} x2={px(i)} y2={BOT} stroke="rgba(232,236,230,0.35)" strokeDasharray="2 4" />}
                  <text x={px(i)} y={BOT + 18} textAnchor="middle"
                    className={`td-year ${on ? 'is-on' : ''}`}>{r.year}</text>
                  {[['bist100', '#c8a35a'], ['model_top10', '#4da583']].map(([k, c]) => (
                    <circle key={k} cx={px(i)} cy={py(r[k])} r={on ? 4.5 : 3} fill={c} />
                  ))}
                </g>
              )
            })}
          </svg>

          {/* bottom strip: excess at a glance */}
          <div className="td-strip">
            {rows.map((r) => {
              const on = active.year === r.year
              return (
                <button key={r.year} type="button"
                  className={`td-yearcard ${on ? 'is-on' : ''}`}
                  onMouseEnter={() => setHovered(r.year)} onFocus={() => setHovered(r.year)}>
                  <span className="td-yearcard-y">{r.year}</span>
                  <span className="td-yearcard-x" style={{ color: r.excess >= 0 ? '#4da583' : '#a8674b' }}>
                    {fmtPct(r.excess)}
                  </span>
                  <span className="td-yearcard-l">EXCESS</span>
                </button>
              )
            })}
          </div>
        </main>

        <aside className="td-readout" key={active.year} aria-live="polite">
          <div className="td-readout-kicker">SIGNAL READOUT</div>
          <div className="td-readout-year">{active.year}</div>
          <div className="td-readout-row"><span>BIST100 RETURN</span><strong style={{ color: '#c8a35a' }}>{fmtPct(active.bist100)}</strong></div>
          <div className="td-readout-row"><span>MODEL TOP-10 RETURN</span><strong style={{ color: '#4da583' }}>{fmtPct(active.model_top10)}</strong></div>
          <div className="td-readout-row"><span>EXCESS RETURN</span><strong style={{ color: active.excess >= 0 ? '#4da583' : '#a8674b' }}>{fmtPct(active.excess)}</strong></div>
          <div className="td-readout-row"><span>SPEARMAN IC</span><strong style={{ color: Math.abs(active.ic) < 0.1 ? '#c8a35a' : active.ic > 0 ? '#4da583' : '#a8674b' }}>{fmtIc(active.ic)}</strong></div>
          <div className="td-readout-row"><span>OUTPERFORMING TICKERS</span><strong>{active.outperform_count} / 40</strong></div>
          <p className="td-readout-note">
            {Math.abs(active.ic) < 0.1
              ? 'IC this small is statistically indistinguishable from zero — the basket result is not attributable to ranking skill.'
              : 'Even this fold-level IC sits inside the noise band of a 40-stock sample.'}
          </p>
        </aside>
      </div>

      <footer className="td-caveat">
        <span className="td-caveat-pulse" aria-hidden="true" />
        Model above BIST100 in {beat}/5 years · Walk-forward IC ≈ 0 — gap not attributable to ranking skill · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.td {
  --td-ink: #0a0e0d; --td-paper: #e8ece6; --td-dim: #9fae9f; --td-faint: #6b7a70;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--td-ink) 55%, #080b0a 100%);
  color: var(--td-paper); overflow: hidden; animation: tdIn 0.7s ease both;
}
.td * { box-sizing: border-box; }
.td-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.td > *:not(.td-scan) { position: relative; z-index: 2; }

.td-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 30px; flex-wrap: wrap; margin-bottom: 22px; }
.td-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--td-faint); margin-bottom: 13px; }
.td-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.td-head h1 em { font-style: italic; color: #4da583; }
.td-head p { margin: 0; max-width: 60ch; color: var(--td-dim); font-size: 14px; line-height: 1.55; }
.td-legend { display: flex; flex-direction: column; gap: 7px; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.14em; color: var(--td-dim); }
.td-legend span { display: flex; align-items: center; gap: 8px; }
.td-dot { width: 8px; height: 8px; border-radius: 50%; }
.td-dot.is-gold { background: #c8a35a; } .td-dot.is-emerald { background: #4da583; } .td-dot.is-copper { background: #a8674b; }
.td-mocknote { color: #a8674b !important; }

.td-main { display: grid; grid-template-columns: 1fr 300px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .td-main { grid-template-columns: 1fr; } }
.td-chartbox { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 16px; }
.td-svg { width: 100%; height: auto; display: block; }
.td-axis { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.14em; fill: var(--td-faint); }
.td-icnum { font-family: var(--font-mono); font-size: 9px; fill: var(--td-dim); }
.td-year { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.1em; fill: var(--td-dim); }
.td-year.is-on { fill: var(--td-paper); font-weight: 700; }
.td-svg rect:focus-visible { outline: none; stroke: #c8a35a; stroke-width: 1; }

.td-strip { display: flex; gap: 8px; margin-top: 14px; flex-wrap: wrap; }
.td-yearcard { flex: 1; min-width: 90px; display: flex; flex-direction: column; gap: 3px; align-items: flex-start;
  border: 1px solid rgba(200,211,202,0.14); border-radius: 2px; background: rgba(14,20,19,0.55);
  padding: 10px 12px; cursor: pointer; font: inherit; color: inherit;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s; }
.td-yearcard:hover, .td-yearcard:focus-visible { border-color: rgba(200,163,90,0.45); outline: none; }
.td-yearcard.is-on { border-color: #c8a35a; box-shadow: inset 0 -2px 0 #c8a35a; background: rgba(22,29,27,0.85); }
.td-yearcard-y { font-family: var(--font-mono); font-size: 11px; color: var(--td-dim); }
.td-yearcard-x { font-family: var(--font-mono); font-size: 16px; font-weight: 700; }
.td-yearcard-l { font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.24em; color: var(--td-faint); }

.td-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid #4da583;
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85));
  padding: 18px 20px; border-radius: 3px; animation: tdIn 0.35s ease; }
.td-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--td-faint); margin-bottom: 12px; }
.td-readout-year { font-family: var(--font-mono); font-size: 30px; font-weight: 700; letter-spacing: 0.04em; margin-bottom: 12px; }
.td-readout-row { display: flex; justify-content: space-between; gap: 12px; font-family: var(--font-mono);
  font-size: 10px; letter-spacing: 0.1em; color: var(--td-dim);
  border-top: 1px dashed rgba(200,211,202,0.14); padding: 9px 0; }
.td-readout-row strong { color: var(--td-paper); font-size: 13px; }
.td-readout-note { margin: 12px 0 0; font-size: 11.5px; line-height: 1.55; color: var(--td-dim); }

.td-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--td-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.td-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: #c8a35a; animation: tdPulse 2.2s ease-in-out infinite; flex-shrink: 0; }

@keyframes tdIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes tdPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .td, .td *, .td *::before, .td *::after { animation: none !important; transition: none !important; }
}
`
