import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'

// ---------------------------------------------------------------------------
// Forecasting — THE SIGNAL TUNER. Experimental, always labeled so.
// Step 1: calibrate the training window (dual-handle range + notched dial).
// Step 2: learned weights render as a frequency spectrum, not a bar chart.
// Step 3: ranked tickers crystallize from noise; inference-only rows pulse amber.
// Real API flow preserved (options → train → run → explain); mock is a
// demo fallback only when the options endpoint yields nothing.
// ---------------------------------------------------------------------------

const FORECASTING_MOCK = {
  options: {
    trainable_years: [2020, 2021, 2022, 2023],
    forecast_years: [2021, 2022, 2023, 2024, 2025],
    feature_columns: 32, ticker_count: 40,
  },
  trained_weights: [
    { name: 'ROE', weight: 0.142, rank: 1, category: 'Profitability' },
    { name: 'Revenue growth', weight: 0.128, rank: 2, category: 'Growth' },
    { name: 'FCF margin', weight: 0.119, rank: 3, category: 'Cash Flow' },
    { name: 'Net margin', weight: 0.108, rank: 4, category: 'Profitability' },
    { name: 'Current ratio', weight: 0.094, rank: 5, category: 'Balance Sheet' },
    { name: 'EV/EBITDA', weight: 0.087, rank: 6, category: 'Valuation' },
  ],
  forecast_results: [
    { ticker: 'ASELS', score: 81.2, confidence: 'high', inference_only: false, top_feature: 'ROE' },
    { ticker: 'THYAO', score: 74.8, confidence: 'high', inference_only: false, top_feature: 'Revenue growth' },
    { ticker: 'EREGL', score: 71.3, confidence: 'medium', inference_only: false, top_feature: 'FCF margin' },
    { ticker: 'SISE', score: 66.9, confidence: 'medium', inference_only: false, top_feature: 'Net margin' },
    { ticker: 'KCHOL', score: 59.4, confidence: 'medium', inference_only: true, top_feature: 'ROE' },
    { ticker: 'SMRTG', score: 22.1, confidence: 'low', inference_only: true, top_feature: 'Current ratio' },
  ],
  experimental_warning: 'Scores reflect historical ranking patterns only. Walk-forward IC ≈ 0. Not investment advice.',
}

const CONF_COLOR = { high: '#4da583', medium: '#c8a35a', low: '#a8674b' }
const errText = (e, fb) => {
  const d = e?.response?.data?.detail
  return typeof d === 'string' ? d : fb
}

export default function ForecastingPage() {
  const [options, setOptions] = useState(null)
  const [mockMode, setMockMode] = useState(false)

  const [trainFrom, setTrainFrom] = useState(2020)
  const [trainTo, setTrainTo] = useState(2023)
  const [topN, setTopN] = useState(12)
  const [training, setTraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)
  const [trainError, setTrainError] = useState('')

  const [forecastYear, setForecastYear] = useState('')
  const [running, setRunning] = useState(false)
  const [forecastResult, setForecastResult] = useState(null)
  const [forecastError, setForecastError] = useState('')

  const [hovered, setHovered] = useState(null) // {type:'feature'|'ticker', data}
  const [explain, setExplain] = useState(null)
  const [explaining, setExplaining] = useState(false)

  useEffect(() => {
    api.get('/forecasting/options')
      .then(({ data }) => {
        if (!data?.trainable_years?.length) { setMockMode(true); return }
        setOptions(data)
        setTrainFrom(data.trainable_years[0])
        setTrainTo(data.trainable_years[data.trainable_years.length - 1])
        if (data.all_years?.length) setForecastYear(String(data.all_years[data.all_years.length - 1]))
      })
      .catch(() => setMockMode(true))
  }, [])

  const trainable = mockMode ? FORECASTING_MOCK.options.trainable_years : (options?.trainable_years || [])
  const allYears = mockMode ? FORECASTING_MOCK.options.forecast_years : (options?.all_years || [])
  const inferenceYears = mockMode ? [2025] : (options?.inference_years || [])
  const yMin = trainable[0] ?? 2020
  const yMax = trainable[trainable.length - 1] ?? 2023

  const trainModel = async () => {
    if (mockMode) {
      setTrainResult({ top_parameters: FORECASTING_MOCK.trained_weights, demo: true })
      setForecastResult(null)
      return
    }
    setTraining(true); setTrainError(''); setTrainResult(null); setForecastResult(null); setExplain(null)
    try {
      const { data } = await api.post('/forecasting/train', {
        train_year_from: trainFrom, train_year_to: trainTo, top_n: topN,
      })
      setTrainResult(data)
    } catch (e) { setTrainError(errText(e, 'Training failed.')) } finally { setTraining(false) }
  }

  const runForecast = async () => {
    if (!trainResult) return
    if (mockMode || trainResult.demo) {
      setForecastResult({ items: FORECASTING_MOCK.forecast_results.map((r, i) => ({ ...r, rank: i + 1 })), demo: true, year: 2025 })
      return
    }
    const weights = {}
    trainResult.top_parameters.forEach((p) => { weights[p.name] = p.weight })
    setRunning(true); setForecastError(''); setForecastResult(null); setExplain(null)
    try {
      const { data } = await api.post('/forecasting/run', {
        year: parseInt(forecastYear, 10), trained_weights: weights,
        risk_level: 'medium', user_type: 'individual',
      })
      setForecastResult(data)
    } catch (e) { setForecastError(errText(e, 'Forecast failed.')) } finally { setRunning(false) }
  }

  const openTicker = async (item) => {
    setHovered({ type: 'ticker', data: item })
    if (mockMode || forecastResult?.demo) return
    setExplaining(true); setExplain(null)
    try {
      const params = forecastYear ? { year: parseInt(forecastYear, 10) } : {}
      const { data } = await api.get(`/forecasting/explain/${encodeURIComponent(item.ticker)}`, { params })
      setExplain(data)
    } catch { setExplain(null) } finally { setExplaining(false) }
  }

  // normalize spectrum + results
  const spectrum = useMemo(() => {
    const src = trainResult?.top_parameters || []
    const list = src.map((p, i) => ({
      name: p.name, weight: Number(p.weight) || 0,
      rank: p.rank ?? i + 1, category: p.category || 'validated feature',
    }))
    return list
  }, [trainResult])
  const maxW = Math.max(0.001, ...spectrum.map((s) => s.weight))

  const results = useMemo(() => {
    const items = forecastResult?.items || []
    const yearIsInference = inferenceYears.includes(parseInt(forecastYear, 10))
    return items.map((it, i) => ({
      ticker: it.ticker,
      rank: it.rank ?? i + 1,
      scoreText: it.score == null ? '—' : (it.score > 1 ? Number(it.score).toFixed(1) : Number(it.score).toFixed(3)),
      scorePct: it.score == null ? 0 : (it.score > 1 ? Math.min(it.score, 100) : it.score * 100),
      confidence: it.confidence_label || it.confidence || 'medium',
      inference_only: it.inference_only ?? yearIsInference,
      top_feature: it.top_feature || it.top_parameters?.[0]?.name || null,
      raw: it,
    }))
  }, [forecastResult, forecastYear, inferenceYears])

  // readout target
  const focus = hovered
    || (results[0] ? { type: 'ticker', data: results[0] } : null)
    || (spectrum[0] ? { type: 'feature', data: spectrum[0] } : null)

  // spectrum geometry
  const SW = 640
  const SH = 150
  const BASE = SH - 26

  return (
    <div className="ft">
      <style>{CSS}</style>
      <div className="ft-scan" aria-hidden="true" />

      <header className="ft-head">
        <div>
          <div className="ft-kicker">FINANCEIQ · FORECASTING SIGNAL TUNER</div>
          <h1>Calibrate, listen, <em>distrust</em>.</h1>
          <p>
            A CSV-backed ranking experiment: tune the training window, inspect the frequencies the model
            locked onto, then let a ranked field crystallize. Walk-forward IC ≈ 0 — treat every ranking
            as a historical pattern, never a forward claim.
          </p>
        </div>
        <div className="ft-expbadge">EXPERIMENTAL{(mockMode || trainResult?.demo) ? ' · DEMO DATA' : ''}</div>
      </header>

      <div className="ft-grid">
        <div className="ft-left">
          {/* ── STEP 1: calibration ── */}
          <section className="ft-panel">
            <div className="ft-step">STEP 1 · CALIBRATE TRAINING WINDOW</div>
            <div className="ft-dial">
              <div className="ft-dial-label">
                TRAIN YEARS <strong>{trainFrom}–{trainTo}</strong>
              </div>
              <div className="ft-range">
                <div className="ft-range-track">
                  <div className="ft-range-fill" style={{
                    left: `${((trainFrom - yMin) / Math.max(yMax - yMin, 1)) * 100}%`,
                    right: `${100 - ((trainTo - yMin) / Math.max(yMax - yMin, 1)) * 100}%`,
                  }} />
                </div>
                <input type="range" min={yMin} max={yMax} value={trainFrom} aria-label="Train from year"
                  onChange={(e) => setTrainFrom(Math.min(parseInt(e.target.value, 10), trainTo))} />
                <input type="range" min={yMin} max={yMax} value={trainTo} aria-label="Train to year"
                  onChange={(e) => setTrainTo(Math.max(parseInt(e.target.value, 10), trainFrom))} />
              </div>
              <div className="ft-range-ticks">{trainable.map((y) => <span key={y}>{y}</span>)}</div>
            </div>
            <div className="ft-dial">
              <div className="ft-dial-label">TOP FEATURES <strong>{topN}</strong></div>
              <input className="ft-notch" type="range" min={4} max={20} step={1} value={topN}
                aria-label="Top n features" onChange={(e) => setTopN(parseInt(e.target.value, 10))} list="ft-notches" />
              <datalist id="ft-notches">{[4, 8, 12, 16, 20].map((n) => <option key={n} value={n} />)}</datalist>
              <div className="ft-range-ticks">{[4, 8, 12, 16, 20].map((n) => <span key={n}>{n}</span>)}</div>
            </div>
            <button type="button" className="ft-btn" disabled={training} onClick={trainModel}>
              {training ? 'DERIVING WEIGHTS…' : 'TRAIN PARAMETERS'}
            </button>
            {trainError && <div className="ft-err">{trainError}</div>}
          </section>

          {/* ── STEP 2: spectrum ── */}
          {spectrum.length > 0 && (
            <section className="ft-panel">
              <div className="ft-step">STEP 2 · LEARNED FREQUENCY SPECTRUM</div>
              <svg className="ft-spectrum" viewBox={`0 0 ${SW} ${SH}`} preserveAspectRatio="xMidYMid meet"
                role="group" aria-label="Learned feature weights as a frequency spectrum">
                <line x1={0} y1={BASE} x2={SW} y2={BASE} stroke="rgba(200,211,202,0.3)" />
                {spectrum.map((f, i) => {
                  const x = 30 + (i / Math.max(spectrum.length - 1, 1)) * (SW - 60)
                  const amp = (f.weight / maxW) * (BASE - 22)
                  const on = focus?.type === 'feature' && focus.data.name === f.name
                  const c = on ? '#4da583' : 'rgba(77,165,131,0.55)'
                  return (
                    <g key={f.name}>
                      <path d={`M${x - 22},${BASE} Q${x},${BASE - amp * 2} ${x + 22},${BASE}`}
                        fill={on ? 'rgba(77,165,131,0.18)' : 'rgba(77,165,131,0.07)'} stroke={c} strokeWidth={on ? 1.8 : 1.1} />
                      <text x={x} y={BASE + 14} textAnchor="middle"
                        className={`ft-freq-label ${on ? 'is-on' : ''}`}>{f.name.length > 11 ? `${f.name.slice(0, 10)}…` : f.name}</text>
                      <rect x={x - 24} y={10} width={48} height={SH - 10} fill="transparent" style={{ cursor: 'pointer' }}
                        tabIndex={0} role="button" aria-label={`${f.name}, weight ${f.weight.toFixed(3)}`}
                        onMouseEnter={() => setHovered({ type: 'feature', data: f })}
                        onFocus={() => setHovered({ type: 'feature', data: f })} />
                    </g>
                  )
                })}
              </svg>
            </section>
          )}

          {/* ── STEP 3: forecast field ── */}
          {trainResult && (
            <section className="ft-panel">
              <div className="ft-step-row">
                <div className="ft-step">STEP 3 · RANKED FIELD</div>
                <div className="ft-runrow">
                  <select className="ft-select" value={forecastYear} disabled={mockMode || trainResult.demo}
                    onChange={(e) => setForecastYear(e.target.value)} aria-label="Forecast year">
                    {(allYears.length ? allYears : [2025]).map((y) => (
                      <option key={y} value={y}>{y}{inferenceYears.includes(Number(y)) ? ' · inference-only' : ''}</option>
                    ))}
                  </select>
                  <button type="button" className="ft-btn is-emerald" disabled={running} onClick={runForecast}>
                    {running ? 'RANKING…' : 'RUN FORECAST'}
                  </button>
                </div>
              </div>
              {forecastError && <div className="ft-err">{forecastError}</div>}
              <div className="ft-field">
                {results.map((r, i) => (
                  <button key={r.ticker} type="button"
                    className={`ft-row ${r.confidence === 'low' ? 'is-grainy' : ''} ${r.inference_only ? 'is-inference' : ''} ${focus?.type === 'ticker' && focus.data.ticker === r.ticker ? 'is-active' : ''}`}
                    style={{ animationDelay: `${i * 0.06}s` }}
                    onMouseEnter={() => setHovered({ type: 'ticker', data: r })}
                    onFocus={() => setHovered({ type: 'ticker', data: r })}
                    onClick={() => openTicker(r)}>
                    <span className="ft-row-rank">#{r.rank}</span>
                    <span className="ft-row-ticker">{r.ticker}</span>
                    <span className="ft-row-trace"><span style={{ width: `${r.scorePct}%`, background: CONF_COLOR[r.confidence] || '#c8a35a' }} /></span>
                    <span className="ft-row-score" style={{ color: CONF_COLOR[r.confidence] || '#c8a35a' }}>{r.scoreText}</span>
                    <span className="ft-row-conf">{String(r.confidence).toUpperCase()}</span>
                    {r.inference_only && <span className="ft-row-inf">INFERENCE</span>}
                  </button>
                ))}
                {results.length === 0 && !running && (
                  <div className="ft-empty">Run the forecast to crystallize the ranked field.</div>
                )}
              </div>
            </section>
          )}
        </div>

        {/* ── Signal Readout ── */}
        <aside className="ft-readout" key={focus ? `${focus.type}-${focus.data.name || focus.data.ticker}` : 'none'} aria-live="polite">
          <div className="ft-readout-kicker">SIGNAL READOUT</div>
          {!focus && (
            <>
              <div className="ft-readout-tag">INSTRUMENT STANDBY</div>
              <div className="ft-readout-row"><span>TRAIN WINDOW</span><strong>{trainFrom}–{trainTo}</strong></div>
              <div className="ft-readout-row"><span>TOP FEATURES</span><strong>{topN}</strong></div>
              <div className="ft-readout-row"><span>UNIVERSE</span><strong>{mockMode ? FORECASTING_MOCK.options.ticker_count : (options?.ticker_count ?? '—')} TICKERS</strong></div>
              <div className="ft-readout-row"><span>WALK-FORWARD IC</span><strong style={{ color: '#c8a35a' }}>≈ 0</strong></div>
              <p className="ft-readout-note">Train parameters to energize the spectrum, then run the ranked field.</p>
            </>
          )}
          {focus?.type === 'feature' && (
            <>
              <div className="ft-readout-name">{focus.data.name}</div>
              <div className="ft-readout-tag">FREQUENCY BAND · {String(focus.data.category).toUpperCase()}</div>
              <div className="ft-readout-big" style={{ color: '#4da583' }}>{focus.data.weight.toFixed(3)}<em>LEARNED WEIGHT</em></div>
              <div className="ft-readout-row"><span>SPECTRUM RANK</span><strong>#{focus.data.rank}</strong></div>
              <p className="ft-readout-note">
                Weight measures how strongly this feature separated historical top-quartile returners.
                Effect size is in-sample; IC ≈ 0 out-of-sample.
              </p>
            </>
          )}
          {focus?.type === 'ticker' && (
            <>
              <div className="ft-readout-name">{focus.data.ticker}</div>
              <div className="ft-readout-tag">RANKED FIELD · #{focus.data.rank}</div>
              <div className="ft-readout-big" style={{ color: CONF_COLOR[focus.data.confidence] || '#c8a35a' }}>
                {focus.data.scoreText}<em>DIAGNOSTIC RANKING SCORE</em>
              </div>
              <div className="ft-readout-row"><span>CONFIDENCE</span><strong style={{ color: CONF_COLOR[focus.data.confidence] }}>{String(focus.data.confidence).toUpperCase()}</strong></div>
              {focus.data.top_feature && <div className="ft-readout-row"><span>TOP DRIVER</span><strong>{focus.data.top_feature}</strong></div>}
              {focus.data.inference_only && (
                <div className="ft-readout-inf">INFERENCE-ONLY · NO T+1 TARGET YET — this row cannot be evaluated until the year closes.</div>
              )}
              {explaining && <p className="ft-readout-note">Loading evidence…</p>}
              {explain && (
                <>
                  <div className="ft-readout-row"><span>COVERAGE</span><strong>{((explain.data_quality?.coverage ?? 0) * 100).toFixed(0)}%</strong></div>
                  <div className="ft-readout-row"><span>FEATURES PRESENT</span><strong>{explain.feature_count ?? '—'}</strong></div>
                </>
              )}
              <p className="ft-readout-note">{FORECASTING_MOCK.experimental_warning}</p>
            </>
          )}
        </aside>
      </div>

      <footer className="ft-caveat">
        <span className="ft-caveat-pulse" aria-hidden="true" />
        EXPERIMENTAL · Walk-forward IC ≈ 0 · Historical ranking patterns only · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.ft {
  --ft-ink: #0a0e0d; --ft-paper: #e8ece6; --ft-dim: #9fae9f; --ft-faint: #6b7a70;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--ft-ink) 55%, #080b0a 100%);
  color: var(--ft-paper); overflow: hidden; animation: ftIn 0.7s ease both;
}
.ft * { box-sizing: border-box; }
.ft-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.ft > *:not(.ft-scan) { position: relative; z-index: 2; }

.ft-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 30px; flex-wrap: wrap; margin-bottom: 22px; }
.ft-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--ft-faint); margin-bottom: 13px; }
.ft-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.ft-head h1 em { font-style: italic; color: #4da583; }
.ft-head p { margin: 0; max-width: 60ch; color: var(--ft-dim); font-size: 14px; line-height: 1.55; }
.ft-expbadge { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.26em; color: #c8a35a;
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 8px 14px; background: rgba(14,20,19,0.7);
  animation: ftPulse 2.6s ease-in-out infinite; }

.ft-grid { display: grid; grid-template-columns: 1fr 300px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .ft-grid { grid-template-columns: 1fr; } }
.ft-left { display: flex; flex-direction: column; gap: 18px; }
.ft-panel { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 18px 20px; }
.ft-step { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.28em; color: var(--ft-faint); margin-bottom: 14px; }
.ft-step-row { display: flex; justify-content: space-between; gap: 14px; align-items: center; flex-wrap: wrap; }
.ft-runrow { display: flex; gap: 8px; align-items: center; }

.ft-dial { margin-bottom: 16px; }
.ft-dial-label { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em; color: var(--ft-dim); margin-bottom: 9px; }
.ft-dial-label strong { color: #c8a35a; font-size: 12px; margin-left: 8px; }
.ft-range { position: relative; height: 22px; }
.ft-range-track { position: absolute; left: 0; right: 0; top: 9px; height: 4px; background: rgba(200,211,202,0.1); border-radius: 1px; }
.ft-range-fill { position: absolute; top: 0; bottom: 0; background: #c8a35a; opacity: 0.6; border-radius: 1px; }
.ft-range input[type=range] { position: absolute; inset: 0; width: 100%; margin: 0; background: none;
  pointer-events: none; -webkit-appearance: none; appearance: none; }
.ft-range input[type=range]::-webkit-slider-thumb { -webkit-appearance: none; pointer-events: auto;
  width: 14px; height: 22px; border-radius: 2px; background: #c8a35a; border: 1px solid #0a0e0d;
  box-shadow: 0 0 8px rgba(200,163,90,0.5); cursor: ew-resize; }
.ft-range input[type=range]::-moz-range-thumb { pointer-events: auto; width: 14px; height: 22px; border-radius: 2px;
  background: #c8a35a; border: 1px solid #0a0e0d; cursor: ew-resize; }
.ft-range input[type=range]:focus-visible { outline: 1px solid #c8a35a; outline-offset: 4px; }
.ft-notch { width: 100%; accent-color: #c8a35a; }
.ft-range-ticks { display: flex; justify-content: space-between; margin-top: 5px;
  font-family: var(--font-mono); font-size: 9px; color: var(--ft-faint); letter-spacing: 0.06em; }

.ft-btn { font-family: var(--font-mono); font-size: 11px; font-weight: 700; letter-spacing: 0.18em;
  background: #c8a35a; color: #0a0e0d; border: 0; border-radius: 2px; padding: 10px 16px; cursor: pointer;
  transition: box-shadow 0.18s, transform 0.1s; }
.ft-btn:hover:not(:disabled) { box-shadow: 0 0 18px rgba(200,163,90,0.3); }
.ft-btn:active { transform: translateY(1px); }
.ft-btn:focus-visible { outline: 1px solid var(--ft-paper); outline-offset: 2px; }
.ft-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ft-btn.is-emerald { background: transparent; color: #4da583; border: 1px solid rgba(77,165,131,0.6); }
.ft-btn.is-emerald:hover:not(:disabled) { box-shadow: 0 0 18px rgba(77,165,131,0.25); background: rgba(77,165,131,0.08); }
.ft-select { background: rgba(10,14,13,0.8); border: 1px solid rgba(200,211,202,0.22); border-radius: 2px;
  color: var(--ft-paper); font-family: var(--font-mono); font-size: 11.5px; padding: 9px 10px; outline: none; }
.ft-select:focus { border-color: #4da583; }
.ft-err { margin-top: 10px; font-size: 12px; color: #d08164; border: 1px dashed rgba(168,103,75,0.5);
  border-radius: 2px; padding: 8px 10px; }

.ft-spectrum { width: 100%; height: auto; display: block;
  background: repeating-linear-gradient(0deg, rgba(232,236,230,0.015) 0 1px, transparent 1px 5px); border-radius: 2px; }
.ft-freq-label { font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.04em; fill: var(--ft-faint); }
.ft-freq-label.is-on { fill: var(--ft-paper); }
.ft-spectrum rect:focus-visible { outline: none; stroke: #4da583; stroke-width: 1; }

.ft-field { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.ft-row { display: grid; grid-template-columns: 38px 70px 1fr 58px 70px auto; gap: 12px; align-items: center;
  padding: 10px 14px; border: 1px solid rgba(200,211,202,0.12); border-radius: 2px;
  background: rgba(14,20,19,0.55); color: inherit; font: inherit; text-align: left; cursor: pointer;
  opacity: 0; animation: ftCrystal 0.5s ease forwards;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s; }
.ft-row:hover, .ft-row:focus-visible { border-color: rgba(77,165,131,0.5); background: rgba(18,26,24,0.8); outline: none; }
.ft-row.is-active { border-color: #4da583; box-shadow: inset 3px 0 0 #4da583; }
.ft-row.is-grainy { border-style: dashed;
  background-image: repeating-linear-gradient(0deg, rgba(232,236,230,0.025) 0 1px, transparent 1px 3px); }
.ft-row.is-inference { animation: ftCrystal 0.5s ease forwards, ftAmber 3.2s ease-in-out infinite; }
.ft-row-rank { font-family: var(--font-mono); font-size: 11px; color: var(--ft-faint); }
.ft-row-ticker { font-family: var(--font-mono); font-size: 13px; font-weight: 700; letter-spacing: 0.06em; }
.ft-row-trace { position: relative; height: 8px; background: rgba(200,211,202,0.07); border-radius: 1px; overflow: hidden; }
.ft-row-trace span { display: block; height: 100%; border-radius: 1px; transition: width 0.6s ease; }
.ft-row-score { font-family: var(--font-mono); font-size: 12px; font-weight: 700; text-align: right; }
.ft-row-conf { font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.2em; color: var(--ft-faint); }
.ft-row-inf { font-family: var(--font-mono); font-size: 8px; letter-spacing: 0.16em; color: #c8a35a;
  border: 1px solid rgba(200,163,90,0.5); border-radius: 1px; padding: 2px 6px; }
.ft-empty { font-family: var(--font-mono); font-size: 12px; color: var(--ft-faint); padding: 14px 0; }

.ft-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid #4da583;
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85));
  padding: 18px 20px; border-radius: 3px; animation: ftIn 0.35s ease; }
.ft-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--ft-faint); margin-bottom: 12px; }
.ft-readout-name { font-family: var(--font-mono); font-size: 22px; font-weight: 700; letter-spacing: 0.04em; word-break: break-all; }
.ft-readout-tag { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.2em; color: #c8a35a; margin-top: 6px; }
.ft-readout-big { font-family: var(--font-mono); font-size: 32px; line-height: 1; margin: 12px 0 14px;
  display: flex; flex-direction: column; gap: 3px; }
.ft-readout-big em { font-style: normal; font-size: 9px; letter-spacing: 0.2em; color: var(--ft-faint); }
.ft-readout-row { display: flex; justify-content: space-between; gap: 12px; font-family: var(--font-mono);
  font-size: 10px; letter-spacing: 0.1em; color: var(--ft-dim);
  border-top: 1px dashed rgba(200,211,202,0.14); padding: 8px 0; }
.ft-readout-row strong { color: var(--ft-paper); font-size: 11.5px; }
.ft-readout-inf { margin: 12px 0; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.08em;
  line-height: 1.6; color: #c8a35a; border: 1px solid rgba(200,163,90,0.45); border-radius: 2px; padding: 8px 10px;
  animation: ftAmber 3.2s ease-in-out infinite; }
.ft-readout-note { margin: 12px 0 0; font-size: 11.5px; line-height: 1.55; color: var(--ft-dim); }

.ft-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--ft-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.ft-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: #c8a35a; animation: ftPulse 2.2s ease-in-out infinite; flex-shrink: 0; }

@keyframes ftIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes ftCrystal { from { opacity: 0; filter: blur(5px); } to { opacity: 1; filter: blur(0); } }
@keyframes ftAmber { 0%, 100% { box-shadow: 0 0 0 rgba(200,163,90,0); } 50% { box-shadow: 0 0 16px rgba(200,163,90,0.25); } }
@keyframes ftPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .ft, .ft *, .ft *::before, .ft *::after { animation: none !important; transition: none !important; }
  .ft-row { opacity: 1; }
}
`
