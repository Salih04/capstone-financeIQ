import { useEffect, useMemo, useRef, useState } from 'react'

// ---------------------------------------------------------------------------
// FinanceIQ Dashboard — "Signal from noise"
// Self-contained screen: local mock data only, no API wiring yet.
// The page boots as static, crystallizes into data, and the walk-forward IC
// readout deliberately never settles — the honest core finding (IC ≈ 0).
// ---------------------------------------------------------------------------

const MOCK = {
  dataset: {
    tickers: 40,
    features: 32,
    years: [2020, 2021, 2022, 2023, 2024, 2025],
    inferenceYear: 2025,
  },
  benchmark: [
    { year: 2020, bist100: 28.4, model_top10: 31.2, spearman: 0.08 },
    { year: 2021, bist100: 19.1, model_top10: 14.7, spearman: -0.11 },
    { year: 2022, bist100: 196.3, model_top10: 188.9, spearman: -0.14 },
    { year: 2023, bist100: 43.8, model_top10: 51.2, spearman: 0.03 },
    { year: 2024, bist100: 31.2, model_top10: 38.7, spearman: 0.12 },
  ],
  topTickers: [
    { ticker: 'ASELS', score: 78.4, ml: 0.81, confidence: 0.74, coverage: 0.94 },
    { ticker: 'THYAO', score: 71.2, ml: 0.68, confidence: 0.79, coverage: 0.97 },
    { ticker: 'EREGL', score: 69.8, ml: 0.72, confidence: 0.65, coverage: 0.89 },
    { ticker: 'SISE', score: 65.1, ml: 0.61, confidence: 0.71, coverage: 0.92 },
    { ticker: 'KCHOL', score: 61.4, ml: 0.58, confidence: 0.68, coverage: 0.78 },
  ],
  bottomTickers: [
    { ticker: 'TTKOM', score: 28.1, ml: 0.24, confidence: 0.31, coverage: 0.61 },
    { ticker: 'DOHOL', score: 24.7, ml: 0.21, confidence: 0.28, coverage: 0.44 },
    { ticker: 'SMRTG', score: 19.3, ml: 0.17, confidence: 0.22, coverage: 0.38 },
  ],
  dataQuality: {
    accepted: 32,
    rejected: 15,
    leakageGuarded: 8,
    frozenExcluded: 7,
  },
}

const MEAN_IC =
  MOCK.benchmark.reduce((s, r) => s + r.spearman, 0) / MOCK.benchmark.length

const ALL_TICKERS = [
  ...MOCK.topTickers.map((t) => ({ ...t, band: 'top' })),
  ...MOCK.bottomTickers.map((t) => ({ ...t, band: 'bottom' })),
]

const EMERALD = '#4da583'
const GOLD = '#c8a35a'
const COPPER = '#a8674b'
const INK_LINE = 'rgba(200, 211, 202, 0.13)'

function scoreColor(score) {
  if (score >= 60) return EMERALD
  if (score >= 40) return GOLD
  return COPPER
}

function grainFilter(coverage) {
  if (coverage >= 0.85) return undefined
  if (coverage >= 0.55) return 'url(#fiq-grain-light)'
  return 'url(#fiq-grain-heavy)'
}

function pct1(v) {
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

function ic2(v) {
  return `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(2)}`
}

// ---------------------------------------------------------------------------
// Animated grain canvas — the literal noise floor of the page.
// ---------------------------------------------------------------------------
function GrainCanvas({ booted, reduceMotion }) {
  const ref = useRef(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const W = 144
    const H = 84
    canvas.width = W
    canvas.height = H
    const maxAlpha = booted ? 22 : 96

    const paint = () => {
      const img = ctx.createImageData(W, H)
      const d = img.data
      for (let i = 0; i < d.length; i += 4) {
        const v = 14 + ((Math.random() * 34) | 0)
        d[i] = v
        d[i + 1] = v + 3
        d[i + 2] = v
        d[i + 3] = (Math.random() * maxAlpha) | 0
      }
      ctx.putImageData(img, 0, 0)
    }

    paint()
    if (reduceMotion) return undefined

    let raf
    let last = 0
    const loop = (t) => {
      if (t - last > 95) {
        last = t
        paint()
      }
      raf = requestAnimationFrame(loop)
    }
    raf = requestAnimationFrame(loop)
    return () => cancelAnimationFrame(raf)
  }, [booted, reduceMotion])

  return <canvas ref={ref} className="fiq-grain" aria-hidden="true" />
}

// ---------------------------------------------------------------------------
// Walk-forward IC meter — a needle on a ±0.5 rail that never stops drifting.
// ---------------------------------------------------------------------------
function SignalMeter({ icValue }) {
  const x = 50 + (icValue / 0.5) * 50 // percent across the rail
  return (
    <div className="fiq-meter" role="img" aria-label={`Walk-forward IC approximately zero, current readout ${ic2(icValue)}`}>
      <div className="fiq-meter-head">
        <span className="fiq-meter-label">WALK-FORWARD IC</span>
        <span className="fiq-meter-value">{ic2(icValue)}</span>
      </div>
      <div className="fiq-meter-rail">
        <span className="fiq-meter-zero" />
        <span className="fiq-meter-needle" style={{ left: `${Math.max(2, Math.min(98, x))}%` }} />
        {MOCK.benchmark.map((r) => (
          <span
            key={r.year}
            className="fiq-meter-tick"
            style={{ left: `${50 + (r.spearman / 0.5) * 50}%` }}
            title={`${r.year}: ${ic2(r.spearman)}`}
          />
        ))}
      </div>
      <div className="fiq-meter-scale">
        <span>−0.5</span>
        <span>0</span>
        <span>+0.5</span>
      </div>
      <div className="fiq-meter-verdict">Walk-forward IC ≈ 0: weak predictive signal</div>
      <div className="fiq-meter-dispersion">
        −0.17 to +0.22 across test_2023/24/25 · individually indistinguishable from zero at n≈40
        · source: experiments/leaderboard.csv
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// The field — 8 named tickers placed by ML score × confidence.
// High-coverage names render crisp; thin-coverage names stay grainy.
// ---------------------------------------------------------------------------
function SignalField({ hovered, onHover }) {
  const FW = 640
  const FH = 420
  const px = (ml) => 60 + ((ml - 0.1) / 0.8) * (FW - 110)
  const py = (conf) => FH - 52 - ((conf - 0.1) / 0.8) * (FH - 104)

  return (
    <svg
      className="fiq-field-svg"
      viewBox={`0 0 ${FW} ${FH}`}
      preserveAspectRatio="xMidYMid meet"
      role="group"
      aria-label="Research field: ML score versus confidence for 8 highlighted tickers"
    >
      <defs>
        <filter id="fiq-grain-light" x="-30%" y="-30%" width="160%" height="160%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="n" seed="7" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="5" />
        </filter>
        <filter id="fiq-grain-heavy" x="-40%" y="-40%" width="180%" height="180%">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" result="n" seed="3" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="11" />
        </filter>
        <radialGradient id="fiq-node-halo">
          <stop offset="0%" stopColor="rgba(77,165,131,0.34)" />
          <stop offset="100%" stopColor="rgba(77,165,131,0)" />
        </radialGradient>
      </defs>

      {/* survey gridlines */}
      {[0.25, 0.5, 0.75].map((g) => (
        <g key={g}>
          <line x1={px(0.1 + g * 0.8)} y1={36} x2={px(0.1 + g * 0.8)} y2={FH - 52} stroke={INK_LINE} strokeDasharray="2 7" />
          <line x1={60} y1={py(0.1 + g * 0.8)} x2={FW - 50} y2={py(0.1 + g * 0.8)} stroke={INK_LINE} strokeDasharray="2 7" />
        </g>
      ))}
      <line x1={60} y1={FH - 52} x2={FW - 50} y2={FH - 52} stroke="rgba(200,211,202,0.3)" />
      <line x1={60} y1={36} x2={60} y2={FH - 52} stroke="rgba(200,211,202,0.3)" />
      <text x={FW - 50} y={FH - 30} textAnchor="end" className="fiq-axis-label">
        ML SCORE →
      </text>
      <text x={42} y={40} className="fiq-axis-label" transform={`rotate(-90 42 40)`} textAnchor="end">
        CONFIDENCE →
      </text>

      {ALL_TICKERS.map((t, i) => {
        const cx = px(t.ml)
        const cy = py(t.confidence)
        const r = 7 + t.coverage * 14
        const active = hovered === t.ticker
        const color = scoreColor(t.score)
        return (
          <g
            key={t.ticker}
            className={`fiq-node ${active ? 'is-active' : ''}`}
            style={{ animationDelay: `${0.55 + i * 0.12}s` }}
            filter={grainFilter(t.coverage)}
            tabIndex={0}
            role="button"
            aria-label={`${t.ticker}, research score ${t.score}, confidence ${Math.round(t.confidence * 100)} percent, coverage ${Math.round(t.coverage * 100)} percent`}
            onMouseEnter={() => onHover(t.ticker)}
            onFocus={() => onHover(t.ticker)}
          >
            {t.coverage >= 0.85 && <circle cx={cx} cy={cy} r={r * 2.1} fill="url(#fiq-node-halo)" />}
            <circle
              cx={cx}
              cy={cy}
              r={r}
              fill={color}
              fillOpacity={0.28 + t.confidence * 0.5}
              stroke={color}
              strokeWidth={active ? 2.4 : 1.3}
              strokeDasharray={t.coverage < 0.55 ? '3 4' : undefined}
            />
            <circle cx={cx} cy={cy} r={2.6} fill={color} />
            <text x={cx + r + 7} y={cy + 4} className="fiq-node-label" fill={active ? '#e8ece6' : '#9fae9f'}>
              {t.ticker}
            </text>
            {active && (
              <circle cx={cx} cy={cy} r={r + 7} fill="none" stroke={color} strokeWidth={1} strokeDasharray="1 5" className="fiq-node-ring" />
            )}
          </g>
        )
      })}
    </svg>
  )
}

// ---------------------------------------------------------------------------
// Fixed detail panel — the only place hover detail is allowed to appear.
// ---------------------------------------------------------------------------
function DetailPanel({ ticker }) {
  const t = ALL_TICKERS.find((x) => x.ticker === ticker)
  if (!t) return null
  const color = scoreColor(t.score)
  const rows = [
    { label: 'ML score', value: t.ml, text: t.ml.toFixed(2) },
    { label: 'Confidence', value: t.confidence, text: `${Math.round(t.confidence * 100)}%` },
    { label: 'Data coverage', value: t.coverage, text: `${Math.round(t.coverage * 100)}%` },
  ]
  return (
    <aside className="fiq-panel" key={t.ticker} aria-live="polite">
      <div className="fiq-panel-kicker">SIGNAL READOUT</div>
      <div className="fiq-panel-ticker">
        {t.ticker}
        <span className="fiq-panel-band" style={{ color }}>
          {t.band === 'top' ? 'TOP RANK' : 'BOTTOM RANK'}
        </span>
      </div>
      <div className="fiq-panel-score">
        <span className="fiq-panel-score-num" style={{ color }}>
          {t.score.toFixed(1)}
        </span>
        <span className="fiq-panel-score-cap">diagnostic research score / 100</span>
      </div>
      {rows.map((r) => (
        <div className="fiq-panel-row" key={r.label}>
          <span className="fiq-panel-row-label">{r.label}</span>
          <span className="fiq-panel-bar">
            <span className="fiq-panel-bar-fill" style={{ width: `${r.value * 100}%`, background: color }} />
          </span>
          <span className="fiq-panel-row-val">{r.text}</span>
        </div>
      ))}
      <p className="fiq-panel-note">
        {t.coverage < 0.55
          ? 'Thin coverage: this readout stays grainy by design. Treat the ranking signal as low-trust.'
          : t.band === 'top'
            ? 'Crisp coverage, but ranking strength does not imply predictive edge — committed test-fold IC spans −0.17 to +0.22, individually indistinguishable from zero at n≈40.'
            : 'Low diagnostic score under solid coverage. Historical evaluation only.'}
      </p>
    </aside>
  )
}

// ---------------------------------------------------------------------------
// Walk-forward ledger — BIST100 vs Model Top 10 per year, IC dot per row.
// ---------------------------------------------------------------------------
function WalkForwardLedger({ year, onYear }) {
  const maxRet = 200
  const w = (v) => `${Math.min(100, (Math.abs(v) / maxRet) * 100)}%`
  const selected = MOCK.benchmark.find((r) => r.year === year)

  return (
    <section className="fiq-ledger">
      <header className="fiq-section-head">
        <h2>WALK-FORWARD LEDGER · 2020–2024</h2>
        <span className="fiq-section-sub">
          {selected.year}: BIST100 {pct1(selected.bist100)} · model top 10 {pct1(selected.model_top10)} · Spearman {ic2(selected.spearman)}
        </span>
      </header>

      <div className="fiq-ledger-rows">
        {MOCK.benchmark.map((r) => {
          const active = r.year === year
          return (
            <button
              key={r.year}
              type="button"
              className={`fiq-ledger-row ${active ? 'is-active' : ''}`}
              onClick={() => onYear(r.year)}
              onMouseEnter={() => onYear(r.year)}
            >
              <span className="fiq-ledger-year">{r.year}</span>
              <span className="fiq-ledger-bars">
                <span className="fiq-ledger-track">
                  <span className="fiq-ledger-bar fiq-bar-bist" style={{ width: w(r.bist100) }} />
                  <span className="fiq-ledger-bar-val">{pct1(r.bist100)}</span>
                </span>
                <span className="fiq-ledger-track">
                  <span className="fiq-ledger-bar fiq-bar-model" style={{ width: w(r.model_top10) }} />
                  <span className="fiq-ledger-bar-val">{pct1(r.model_top10)}</span>
                </span>
              </span>
              <span className="fiq-ledger-ic" aria-label={`Spearman ${ic2(r.spearman)}`}>
                <span className="fiq-ic-axis">
                  <span className="fiq-ic-zero" />
                  <span
                    className="fiq-ic-dot"
                    style={{
                      left: `${50 + (r.spearman / 0.2) * 50}%`,
                      background: Math.abs(r.spearman) < 0.1 ? GOLD : r.spearman > 0 ? EMERALD : COPPER,
                    }}
                  />
                </span>
                <span className="fiq-ic-num">{ic2(r.spearman)}</span>
              </span>
            </button>
          )
        })}
        <div className="fiq-ledger-row fiq-ledger-inference" aria-label="2025 is inference-only">
          <span className="fiq-ledger-year">2025</span>
          <span className="fiq-ledger-inference-note">inference-only · no realized T+1 outcome yet · excluded from evaluation</span>
        </div>
      </div>

      <div className="fiq-ledger-legend">
        <span><i className="fiq-dot" style={{ background: GOLD }} /> BIST100 return</span>
        <span><i className="fiq-dot" style={{ background: EMERALD }} /> Model top 10 return</span>
        <span><i className="fiq-dot" style={{ background: COPPER }} /> Spearman / IC, ±0.2 rail</span>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Feature intake strip — what survived validation, what was cut and why.
// ---------------------------------------------------------------------------
function QualityStrip() {
  const q = MOCK.dataQuality
  const total = q.accepted + q.rejected + q.leakageGuarded + q.frozenExcluded
  const segs = [
    { key: 'accepted', n: q.accepted, label: 'accepted', color: EMERALD, note: 'year-varying features admitted to the modeling set' },
    { key: 'rejected', n: q.rejected, label: 'rejected', color: COPPER, note: 'failed validation checks; dropped before training' },
    { key: 'leakage', n: q.leakageGuarded, label: 'leakage guarded', color: GOLD, note: 'flagged for look-ahead risk and fenced out of T→T+1' },
    { key: 'frozen', n: q.frozenExcluded, label: 'frozen excluded', color: '#7a8a80', note: 'static across years; carries no ranking information' },
  ]
  return (
    <section className="fiq-quality">
      <header className="fiq-section-head">
        <h2>FEATURE INTAKE · {total} CANDIDATES</h2>
        <span className="fiq-section-sub">leakage-safe T→T+1 validation</span>
      </header>
      <div className="fiq-quality-bar" role="img" aria-label={`Feature intake: ${q.accepted} accepted, ${q.rejected} rejected, ${q.leakageGuarded} leakage guarded, ${q.frozenExcluded} frozen excluded`}>
        {segs.map((s) => (
          <span key={s.key} className="fiq-quality-seg" style={{ flexGrow: s.n, background: s.color }}>
            <span className="fiq-quality-n">{s.n}</span>
          </span>
        ))}
      </div>
      <ul className="fiq-quality-list">
        {segs.map((s) => (
          <li key={s.key}>
            <i className="fiq-dot" style={{ background: s.color }} />
            <strong>{s.n} {s.label}</strong> — {s.note}
          </li>
        ))}
      </ul>
    </section>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const reduceMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  )
  const [booted, setBooted] = useState(reduceMotion)
  const [hovered, setHovered] = useState('ASELS')
  const [year, setYear] = useState(2024)
  const [icDrift, setIcDrift] = useState(0)

  useEffect(() => {
    if (booted) return undefined
    const id = setTimeout(() => setBooted(true), 1150)
    return () => clearTimeout(id)
  }, [booted])

  useEffect(() => {
    if (reduceMotion) return undefined
    const id = setInterval(() => setIcDrift((Math.random() - 0.5) * 0.05), 680)
    return () => clearInterval(id)
  }, [reduceMotion])

  return (
    <div className={`fiq ${booted ? 'is-booted' : 'is-booting'}`}>
      <style>{CSS}</style>
      <GrainCanvas booted={booted} reduceMotion={reduceMotion} />
      <div className="fiq-scan" aria-hidden="true" />

      <div className="fiq-boot" aria-hidden={booted}>
        <div className="fiq-boot-text">TUNING RESEARCH SIGNAL</div>
        <div className="fiq-boot-bar"><span /></div>
      </div>

      <div className="fiq-stage">
        <header className="fiq-head">
          <div className="fiq-head-title">
            <div className="fiq-kicker">FINANCEIQ · BIST EQUITY RESEARCH INSTRUMENT</div>
            <h1>
              A weak signal, reported <em>honestly</em>.
            </h1>
            <p>
              T→T+1 historical evaluation over {MOCK.dataset.tickers} selected BIST stocks. The model ranks;
              the walk-forward test shows no reliable predictive edge. This page tunes that weak signal into
              view instead of hiding it.
            </p>
          </div>
          <SignalMeter icValue={MEAN_IC + icDrift} />
        </header>

        <div className="fiq-strip" role="list" aria-label="Dataset summary">
          <span role="listitem"><strong>{MOCK.dataset.tickers}</strong> BIST stocks</span>
          <span role="listitem"><strong>{MOCK.dataset.features}</strong> accepted features</span>
          <span role="listitem"><strong>2020–2025</strong> coverage</span>
          <span role="listitem"><strong>{MOCK.dataset.inferenceYear}</strong> inference-only</span>
          <span role="listitem" className="fiq-strip-flag">historical evaluation · diagnostic only</span>
        </div>

        <div className="fiq-main">
          <section className="fiq-field">
            <header className="fiq-section-head">
              <h2>SIGNAL FIELD · TOP 5 / BOTTOM 3 BY RESEARCH SCORE</h2>
              <span className="fiq-section-sub">crisp = high coverage · grainy = thin coverage · hover a node</span>
            </header>
            <SignalField hovered={hovered} onHover={setHovered} />
          </section>
          <DetailPanel ticker={hovered} />
        </div>

        <div className="fiq-lower">
          <WalkForwardLedger year={year} onYear={setYear} />
          <QualityStrip />
        </div>
      </div>

      <footer className="fiq-caveat">
        <span className="fiq-caveat-pulse" aria-hidden="true" />
        Research only · Not investment advice
        <span className="fiq-caveat-sep">·</span>
        Walk-forward IC ≈ 0 · range −0.17 to +0.22 · each indistinguishable from zero at n≈40
      </footer>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Styles — scoped under .fiq, full-bleed over the AppShell content area.
// ---------------------------------------------------------------------------
const CSS = `
.fiq {
  --fiq-ink: #0a0e0d;
  --fiq-ink-2: #0e1413;
  --fiq-paper: #e8ece6;
  --fiq-dim: #9fae9f;
  --fiq-faint: #6b7a70;
  --fiq-emerald: ${EMERALD};
  --fiq-gold: ${GOLD};
  --fiq-copper: ${COPPER};
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.07), transparent 60%),
    radial-gradient(800px 500px at 8% 108%, rgba(168,103,75,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--fiq-ink) 55%, #080b0a 100%);
  color: var(--fiq-paper);
  font-family: 'Avenir Next', 'Segoe UI', system-ui, sans-serif;
  overflow: hidden;
}
.fiq * { box-sizing: border-box; }

.fiq-grain {
  position: absolute; inset: 0; width: 100%; height: 100%;
  pointer-events: none; image-rendering: pixelated; z-index: 1;
}
.fiq-scan {
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px);
}

/* ---- boot / crystallize ---- */
.fiq-boot {
  position: absolute; inset: 0; z-index: 5; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 16px;
  background: rgba(8,11,10,0.55); backdrop-filter: blur(2px);
  transition: opacity 0.7s ease, visibility 0.7s;
}
.fiq.is-booted .fiq-boot { opacity: 0; visibility: hidden; }
.fiq-boot-text {
  font-family: ui-monospace, 'SF Mono', Menlo, monospace; font-size: 12px;
  letter-spacing: 0.42em; color: var(--fiq-dim); animation: fiqFlicker 0.9s steps(3) infinite;
}
.fiq-boot-bar { width: 180px; height: 2px; background: rgba(200,211,202,0.14); overflow: hidden; }
.fiq-boot-bar span { display: block; height: 100%; width: 40%; background: var(--fiq-emerald); animation: fiqSweep 1.1s ease-in-out infinite; }

.fiq-stage { position: relative; z-index: 2; transition: filter 1.3s ease, opacity 1.3s ease; }
.fiq.is-booting .fiq-stage { filter: blur(10px) saturate(0.3) contrast(1.3); opacity: 0.45; }
.fiq.is-booted .fiq-stage { filter: none; opacity: 1; }

/* ---- header ---- */
.fiq-head {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 40px; flex-wrap: wrap; margin-bottom: 26px;
}
.fiq-head-title { max-width: 620px; }
.fiq-kicker {
  font-family: ui-monospace, 'SF Mono', Menlo, monospace; font-size: 11px;
  letter-spacing: 0.34em; color: var(--fiq-faint); margin-bottom: 14px;
}
.fiq-head h1 {
  margin: 0 0 12px; font-size: clamp(28px, 3.4vw, 44px); line-height: 1.04;
  font-weight: 650; letter-spacing: -0.015em;
}
.fiq-head h1 em { font-style: italic; color: var(--fiq-emerald); }
.fiq-head p { margin: 0; max-width: 56ch; color: var(--fiq-dim); font-size: 14.5px; line-height: 1.55; }

/* ---- IC meter ---- */
.fiq-meter {
  min-width: 270px; max-width: 330px; flex: 1;
  border: 1px solid rgba(200,211,202,0.16); border-radius: 4px;
  padding: 16px 18px 13px; background: rgba(14,20,19,0.72);
  box-shadow: 0 0 0 1px rgba(0,0,0,0.4), inset 0 0 30px rgba(77,165,131,0.04);
}
.fiq-meter-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 12px; }
.fiq-meter-label { font-family: ui-monospace, Menlo, monospace; font-size: 10px; letter-spacing: 0.3em; color: var(--fiq-faint); }
.fiq-meter-value {
  font-family: ui-monospace, Menlo, monospace; font-size: 22px; color: var(--fiq-gold);
  animation: fiqFlicker 2.3s steps(5) infinite;
}
.fiq-meter-rail { position: relative; height: 22px; background: rgba(200,211,202,0.06); border-radius: 2px; }
.fiq-meter-zero { position: absolute; left: 50%; top: -3px; bottom: -3px; width: 1px; background: rgba(232,236,230,0.45); }
.fiq-meter-needle {
  position: absolute; top: 1px; bottom: 1px; width: 3px; margin-left: -1.5px;
  background: var(--fiq-gold); box-shadow: 0 0 9px rgba(200,163,90,0.8);
  transition: left 0.6s cubic-bezier(.3,1.4,.4,1);
}
.fiq-meter-tick { position: absolute; top: 7px; bottom: 7px; width: 1px; background: rgba(159,174,159,0.5); }
.fiq-meter-scale { display: flex; justify-content: space-between; margin-top: 5px; font-family: ui-monospace, Menlo, monospace; font-size: 9.5px; color: var(--fiq-faint); }
.fiq-meter-verdict { margin-top: 10px; font-size: 11.5px; letter-spacing: 0.04em; color: var(--fiq-paper); border-top: 1px dashed rgba(200,211,202,0.18); padding-top: 9px; }
.fiq-meter-dispersion { margin-top: 6px; font-family: ui-monospace, Menlo, monospace; font-size: 9.5px; line-height: 1.45; color: var(--fiq-dim); }

/* ---- dataset strip ---- */
.fiq-strip {
  display: flex; flex-wrap: wrap; gap: 10px 34px; align-items: baseline;
  font-family: ui-monospace, Menlo, monospace; font-size: 12px; color: var(--fiq-dim);
  border-top: 1px solid rgba(200,211,202,0.14); border-bottom: 1px solid rgba(200,211,202,0.14);
  padding: 11px 2px; margin-bottom: 30px;
}
.fiq-strip strong { color: var(--fiq-paper); font-size: 15px; font-weight: 600; margin-right: 5px; }
.fiq-strip-flag { margin-left: auto; color: var(--fiq-gold); letter-spacing: 0.08em; }

/* ---- main: field + panel ---- */
.fiq-main { display: flex; gap: 26px; align-items: stretch; margin-bottom: 34px; flex-wrap: wrap; }
.fiq-field { flex: 1.7; min-width: 420px; }
.fiq-field-svg { width: 100%; height: auto; display: block; }

.fiq-section-head { display: flex; justify-content: space-between; align-items: baseline; gap: 16px; flex-wrap: wrap; margin-bottom: 12px; }
.fiq-section-head h2 {
  margin: 0; font-family: ui-monospace, Menlo, monospace; font-size: 11px;
  letter-spacing: 0.26em; font-weight: 600; color: var(--fiq-paper);
}
.fiq-section-sub { font-size: 11px; color: var(--fiq-faint); letter-spacing: 0.04em; }

.fiq-axis-label { font-family: ui-monospace, Menlo, monospace; font-size: 9px; letter-spacing: 0.3em; fill: var(--fiq-faint); }
.fiq-node { cursor: pointer; outline: none; opacity: 0; animation: fiqEmerge 0.9s ease forwards; }
.fiq.is-booting .fiq-node { animation-play-state: paused; }
.fiq-node:focus-visible circle:first-of-type { stroke: var(--fiq-paper); }
.fiq-node-label { font-family: ui-monospace, Menlo, monospace; font-size: 11px; letter-spacing: 0.08em; }
.fiq-node.is-active .fiq-node-label { font-weight: 700; }
.fiq-node-ring { animation: fiqSpinDash 6s linear infinite; }

/* ---- detail panel ---- */
.fiq-panel {
  flex: 1; min-width: 280px; max-width: 360px;
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--fiq-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.9), rgba(10,14,13,0.85));
  padding: 20px 22px; border-radius: 3px;
  animation: fiqCrystal 0.45s ease;
}
.fiq-panel-kicker { font-family: ui-monospace, Menlo, monospace; font-size: 10px; letter-spacing: 0.32em; color: var(--fiq-faint); margin-bottom: 10px; }
.fiq-panel-ticker { font-size: 30px; font-weight: 700; letter-spacing: 0.02em; display: flex; align-items: baseline; gap: 12px; }
.fiq-panel-band { font-family: ui-monospace, Menlo, monospace; font-size: 10px; letter-spacing: 0.24em; }
.fiq-panel-score { margin: 14px 0 18px; display: flex; flex-direction: column; gap: 2px; }
.fiq-panel-score-num { font-family: ui-monospace, Menlo, monospace; font-size: 44px; line-height: 1; }
.fiq-panel-score-cap { font-size: 10.5px; letter-spacing: 0.14em; color: var(--fiq-faint); text-transform: uppercase; }
.fiq-panel-row { display: grid; grid-template-columns: 92px 1fr 44px; gap: 10px; align-items: center; margin-bottom: 9px; font-size: 12px; }
.fiq-panel-row-label { color: var(--fiq-dim); }
.fiq-panel-bar { height: 5px; background: rgba(200,211,202,0.1); border-radius: 2px; overflow: hidden; }
.fiq-panel-bar-fill { display: block; height: 100%; border-radius: 2px; transition: width 0.5s ease; }
.fiq-panel-row-val { font-family: ui-monospace, Menlo, monospace; text-align: right; color: var(--fiq-paper); }
.fiq-panel-note { margin: 16px 0 0; font-size: 12px; line-height: 1.55; color: var(--fiq-dim); border-top: 1px dashed rgba(200,211,202,0.18); padding-top: 12px; }

/* ---- lower band ---- */
.fiq-lower { display: flex; gap: 26px; flex-wrap: wrap; align-items: flex-start; }
.fiq-ledger { flex: 1.6; min-width: 440px; }
.fiq-quality { flex: 1; min-width: 300px; }

.fiq-ledger-rows { display: flex; flex-direction: column; gap: 4px; }
.fiq-ledger-row {
  display: grid; grid-template-columns: 56px 1fr 150px; gap: 16px; align-items: center;
  width: 100%; text-align: left; padding: 9px 12px; border: 1px solid transparent;
  background: rgba(14,20,19,0.45); color: inherit; font: inherit; cursor: pointer;
  border-radius: 3px; transition: border-color 0.2s, background 0.2s;
}
.fiq-ledger-row:hover, .fiq-ledger-row:focus-visible { border-color: rgba(200,163,90,0.45); background: rgba(20,27,25,0.7); outline: none; }
.fiq-ledger-row.is-active { border-color: var(--fiq-gold); background: rgba(22,29,27,0.85); }
.fiq-ledger-year { font-family: ui-monospace, Menlo, monospace; font-size: 14px; color: var(--fiq-paper); }
.fiq-ledger-bars { display: flex; flex-direction: column; gap: 4px; }
.fiq-ledger-track { position: relative; height: 9px; background: rgba(200,211,202,0.07); border-radius: 1px; }
.fiq-ledger-bar { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 1px; transition: width 0.7s ease; }
.fiq-bar-bist { background: linear-gradient(90deg, rgba(200,163,90,0.4), var(--fiq-gold)); }
.fiq-bar-model { background: linear-gradient(90deg, rgba(77,165,131,0.4), var(--fiq-emerald)); }
.fiq-ledger-bar-val {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  font-family: ui-monospace, Menlo, monospace; font-size: 9px; color: var(--fiq-dim);
}
.fiq-ledger-ic { display: flex; align-items: center; gap: 10px; }
.fiq-ic-axis { position: relative; flex: 1; height: 14px; }
.fiq-ic-axis::before { content: ''; position: absolute; left: 0; right: 0; top: 50%; height: 1px; background: rgba(200,211,202,0.18); }
.fiq-ic-zero { position: absolute; left: 50%; top: 0; bottom: 0; width: 1px; background: rgba(232,236,230,0.4); }
.fiq-ic-dot { position: absolute; top: 50%; width: 8px; height: 8px; margin: -4px 0 0 -4px; border-radius: 50%; box-shadow: 0 0 7px rgba(200,163,90,0.5); }
.fiq-ic-num { font-family: ui-monospace, Menlo, monospace; font-size: 11px; width: 44px; text-align: right; color: var(--fiq-dim); }
.fiq-ledger-inference { cursor: default; opacity: 0.75; grid-template-columns: 56px 1fr; }
.fiq-ledger-inference:hover { border-color: transparent; background: rgba(14,20,19,0.45); }
.fiq-ledger-inference-note { font-family: ui-monospace, Menlo, monospace; font-size: 10.5px; letter-spacing: 0.06em; color: var(--fiq-gold); }
.fiq-ledger-legend { display: flex; gap: 22px; flex-wrap: wrap; margin-top: 12px; font-size: 11px; color: var(--fiq-faint); }
.fiq-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: baseline; }

/* ---- quality ---- */
.fiq-quality-bar { display: flex; height: 26px; border-radius: 2px; overflow: hidden; gap: 2px; margin-bottom: 14px; }
.fiq-quality-seg { position: relative; min-width: 26px; opacity: 0.85; transition: opacity 0.2s, transform 0.2s; }
.fiq-quality-seg:hover { opacity: 1; transform: translateY(-2px); }
.fiq-quality-n {
  position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  font-family: ui-monospace, Menlo, monospace; font-size: 11px; font-weight: 700; color: #0a0e0d;
}
.fiq-quality-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; font-size: 12px; color: var(--fiq-dim); line-height: 1.45; }
.fiq-quality-list strong { color: var(--fiq-paper); font-weight: 600; }

/* ---- caveat ---- */
.fiq-caveat {
  position: sticky; bottom: 14px; z-index: 4; margin-top: 40px;
  display: flex; align-items: center; gap: 10px; width: fit-content;
  font-family: ui-monospace, Menlo, monospace; font-size: 11.5px; letter-spacing: 0.12em;
  color: var(--fiq-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
.fiq-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--fiq-gold); animation: fiqPulse 2.2s ease-in-out infinite; }
.fiq-caveat-sep { color: var(--fiq-faint); }

/* ---- keyframes ---- */
@keyframes fiqCrystal {
  from { opacity: 0; filter: blur(6px); }
  to { opacity: 1; filter: blur(0); }
}
@keyframes fiqEmerge {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes fiqFlicker {
  0%, 100% { opacity: 1; }
  46% { opacity: 0.78; }
  78% { opacity: 0.92; }
}
@keyframes fiqSweep {
  0% { transform: translateX(-110%); }
  100% { transform: translateX(420%); }
}
@keyframes fiqSpinDash { to { stroke-dashoffset: -60; } }
@keyframes fiqPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

@media (prefers-reduced-motion: reduce) {
  .fiq *, .fiq *::before, .fiq *::after { animation: none !important; transition: none !important; }
  .fiq-node { opacity: 1; }
}
@media (max-width: 900px) {
  .fiq-field { min-width: 100%; }
  .fiq-panel { max-width: none; }
  .fiq-ledger { min-width: 100%; }
}
`
