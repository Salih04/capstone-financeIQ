import { useEffect, useState } from 'react'
import { BrainCircuit, Play, ShieldCheck, ChevronRight, Zap, AlertCircle } from 'lucide-react'
import api from '../api/client'

const CONFIDENCE_COLOR = {
  high: 'var(--success)',
  medium: 'var(--warning)',
  low: 'var(--danger)',
}

export default function ForecastingPage() {
  const [options, setOptions] = useState(null)
  const [optionsErr, setOptionsErr] = useState('')

  const [trainYearFrom, setTrainYearFrom] = useState(2020)
  const [trainYearTo, setTrainYearTo] = useState(2024)
  const [topN, setTopN] = useState(12)
  const [training, setTraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)
  const [trainError, setTrainError] = useState('')

  const [forecastYear, setForecastYear] = useState('')
  const [userType, setUserType] = useState('individual')
  const [riskLevel, setRiskLevel] = useState('medium')
  const [running, setRunning] = useState(false)
  const [forecastResult, setForecastResult] = useState(null)
  const [forecastError, setForecastError] = useState('')

  const [selectedTicker, setSelectedTicker] = useState(null)
  const [explaining, setExplaining] = useState(false)
  const [explainResult, setExplainResult] = useState(null)
  const [explainError, setExplainError] = useState('')

  const [history, setHistory] = useState([])

  useEffect(() => {
    api.get('/forecasting/options')
      .then(({ data }) => {
        setOptions(data)
        if (data.all_years?.length) {
          setForecastYear(String(data.all_years[data.all_years.length - 1]))
        }
        if (data.trainable_years?.length) {
          setTrainYearFrom(data.trainable_years[0])
          setTrainYearTo(data.trainable_years[data.trainable_years.length - 1])
        }
      })
      .catch((e) => setOptionsErr(e.response?.data?.detail || 'Could not load dataset. Check backend connection.'))
  }, [])

  const trainModel = async () => {
    setTraining(true)
    setTrainError('')
    setTrainResult(null)
    setForecastResult(null)
    setSelectedTicker(null)
    setExplainResult(null)
    try {
      const { data } = await api.post('/forecasting/train', {
        train_year_from: trainYearFrom,
        train_year_to: trainYearTo,
        top_n: topN,
      })
      setTrainResult(data)
    } catch (e) {
      setTrainError(e.response?.data?.detail || 'Training failed.')
    } finally {
      setTraining(false)
    }
  }

  const runForecast = async () => {
    if (!trainResult) return
    const weights = {}
    trainResult.top_parameters.forEach((p) => { weights[p.name] = p.weight })
    setRunning(true)
    setForecastError('')
    setForecastResult(null)
    setSelectedTicker(null)
    setExplainResult(null)
    try {
      const { data } = await api.post('/forecasting/run', {
        year: parseInt(forecastYear, 10),
        trained_weights: weights,
        risk_level: riskLevel,
        user_type: userType,
      })
      setForecastResult(data)
      setHistory((h) => [
        {
          year: data.year,
          risk_level: data.risk_level,
          stock_count: data.stock_count,
          ts: new Date().toLocaleTimeString(),
        },
        ...h.slice(0, 9),
      ])
    } catch (e) {
      setForecastError(e.response?.data?.detail || 'Forecast failed.')
    } finally {
      setRunning(false)
    }
  }

  const openStock = async (ticker) => {
    setSelectedTicker(ticker)
    setExplaining(true)
    setExplainResult(null)
    setExplainError('')
    try {
      const params = forecastYear ? { year: parseInt(forecastYear, 10) } : {}
      const { data } = await api.get(`/forecasting/explain/${encodeURIComponent(ticker)}`, { params })
      setExplainResult(data)
    } catch (e) {
      setExplainError(e.response?.data?.detail || 'Detail not available.')
    } finally {
      setExplaining(false)
    }
  }

  const canTrain = Boolean(options && !optionsErr)
  const canRun = Boolean(trainResult && forecastYear)

  return (
    <div className="fc" style={{ maxWidth: 1200, margin: '0 auto', position: 'relative' }}>
      <style>{CSS}</style>
      <div className="fc-scan" aria-hidden="true" />

      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="fc-panel fc-accent" style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8 }}>
              <BrainCircuit size={13} style={{ color: 'var(--primary)' }} />
              <span style={kicker}>FINANCEIQ · RESEARCH FORECASTING LAB</span>
            </div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 650, letterSpacing: '-0.015em', color: 'var(--text-1)', lineHeight: 1.1 }}>
              Parameter-based ranking, <em style={{ fontStyle: 'italic', color: 'var(--secondary)' }}>weak signal</em> reported honestly.
            </h1>
            <p style={{ margin: '8px 0 0', fontSize: 12.5, color: 'var(--text-3)', lineHeight: 1.6, maxWidth: 700 }}>
              Derive feature weights from historical top-quartile BIST returners, then rank all public-universe stocks
              by those learned parameters.
              {options && (
                <span style={{ color: 'var(--text-4)' }}>
                  {' '}· {options.ticker_count} stocks · {options.data_source}
                </span>
              )}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignSelf: 'flex-start' }}>
            <span style={badgeStyle}><ShieldCheck size={10} /> NOT INVESTMENT ADVICE</span>
            <span style={{ ...badgeStyle, color: 'var(--primary)', borderColor: 'rgba(200,163,90,0.45)' }}><Zap size={10} /> EXPERIMENTAL</span>
          </div>
        </div>
        {optionsErr && (
          <div style={errorBox}>
            <AlertCircle size={12} /> {optionsErr}
          </div>
        )}
      </div>

      {/* ── Steps row ─────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>

        {/* Step 1: Train */}
        <div className="fc-panel">
          <div style={sectionLabel}>STEP 1 · TRAIN PARAMETERS</div>
          <p style={helpText}>
            Identify which features best separate top-25% returners from the rest across training years.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
            <div>
              <label style={fieldLabel}>FROM YEAR</label>
              <select
                value={trainYearFrom}
                onChange={(e) => setTrainYearFrom(parseInt(e.target.value))}
                className="fc-input"
                disabled={!options}
              >
                {(options?.trainable_years || []).map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={fieldLabel}>TO YEAR</label>
              <select
                value={trainYearTo}
                onChange={(e) => setTrainYearTo(parseInt(e.target.value))}
                className="fc-input"
                disabled={!options}
              >
                {(options?.trainable_years || []).map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: 12 }}>
            <label style={fieldLabel}>TOP FEATURES ({topN})</label>
            <input
              type="range"
              min={4}
              max={20}
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value))}
              className="fc-range"
              style={{ width: '100%', marginTop: 6 }}
            />
          </div>

          <button
            onClick={trainModel}
            disabled={!canTrain || training}
            className="fc-btn fc-btn-primary"
            style={{
              opacity: !canTrain || training ? 0.5 : 1,
              cursor: !canTrain || training ? 'not-allowed' : 'pointer',
            }}
          >
            <BrainCircuit size={12} />
            {training ? 'DERIVING WEIGHTS…' : 'TRAIN PARAMETERS'}
          </button>

          {trainError && <div style={errorBox}>{trainError}</div>}
        </div>

        {/* Step 2: Run Forecast */}
        <div className="fc-panel">
          <div style={sectionLabel}>STEP 2 · RUN FORECAST</div>
          <p style={helpText}>
            Apply trained weights to rank all stocks in the selected year.
            {!trainResult && <span style={{ color: 'var(--warning-light)' }}> Complete Step 1 first.</span>}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
            <div>
              <label style={fieldLabel}>YEAR</label>
              <select
                value={forecastYear}
                onChange={(e) => setForecastYear(e.target.value)}
                className="fc-input"
                disabled={!options}
              >
                {(options?.all_years || []).map((y) => (
                  <option key={y} value={y}>
                    {y}{(options?.inference_years || []).includes(y) ? '*' : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label style={fieldLabel}>USER TYPE</label>
              <select value={userType} onChange={(e) => setUserType(e.target.value)} className="fc-input">
                <option value="individual">Individual</option>
                <option value="advanced">Advanced</option>
                <option value="corporate">Corporate</option>
              </select>
            </div>
            <div>
              <label style={fieldLabel}>RISK</label>
              <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} className="fc-input">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              onClick={runForecast}
              disabled={!canRun || running}
              className="fc-btn fc-btn-secondary"
              style={{
                opacity: !canRun || running ? 0.5 : 1,
                cursor: !canRun || running ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={12} />
              {running ? 'RANKING…' : 'RUN FORECAST'}
            </button>
            <button
              disabled
              title="Time-CV requires multi-year next-year returns — not available for 2025 inference rows."
              className="fc-btn fc-btn-ghost"
              style={{ opacity: 0.38, cursor: 'not-allowed' }}
            >
              RUN TIME CV
            </button>
          </div>

          {options?.inference_years?.length > 0 && (
            <div style={{ marginTop: 10, fontSize: 10.5, color: 'var(--text-4)', fontFamily: 'var(--font-mono)', letterSpacing: '0.03em' }}>
              * Years marked with * are inference-only (no T+1 return target).
            </div>
          )}

          {forecastError && <div style={errorBox}>{forecastError}</div>}
        </div>
      </div>

      {/* ── Trained parameter weights ─────────────────────────── */}
      {trainResult && (
<<<<<<< HEAD
        <div style={{ ...panel, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 6 }}>
            <span style={sectionLabel}>Learned Feature Weights</span>
            <span style={{ fontSize: 10.5, color: 'var(--text-4)', fontFamily: 'var(--font-mono)' }}>
              {trainResult.total_training_rows} training rows · {trainResult.winner_rows} top-quartile rows
=======
        <div className="fc-panel" style={{ marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 6 }}>
            <span style={sectionLabel}>LEARNED FEATURE WEIGHTS</span>
            <span style={metaLine}>
              {trainedWeights.total_training_rows} training rows · {trainedWeights.winner_rows} top-quartile rows
>>>>>>> local/nice-chatelet-dce077
              · p{trainResult.winner_percentile * 100} threshold
              · years {trainResult.train_year_from}–{trainResult.train_year_to}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: 6 }}>
            {trainResult.top_parameters.map((p) => (
              <div key={p.name} style={paramChip}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.name}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
                  <div style={{ width: 40, height: 3, background: 'rgba(200,211,202,0.1)', borderRadius: 1 }}>
                    <div style={{ width: `${p.weight * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: 1 }} />
                  </div>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--primary)', minWidth: 34, textAlign: 'right' }}>
                    {p.weight.toFixed(3)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Forecast results: ranked table + explainability ──── */}
      {(forecastResult || (forecastError && trainResult)) && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>

          {/* Ranked Stocks */}
          <div className="fc-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 4 }}>
              <span style={sectionLabel}>RANKED STOCKS</span>
              {forecastResult && (
                <span style={metaLine}>
                  {forecastResult.stock_count} stocks · {forecastResult.year} · {forecastResult.risk_level}
                </span>
              )}
            </div>

            {!forecastResult ? (
              <div style={{ fontSize: 12, color: 'var(--danger-light)' }}>{forecastError}</div>
            ) : (
              <div style={{ maxHeight: 440, overflowY: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 11.5 }}>
                  <thead>
                    <tr style={{ position: 'sticky', top: 0, background: 'var(--bg)', zIndex: 1 }}>
                      <th style={thStyle}>#</th>
                      <th style={thStyle}>TICKER</th>
                      <th style={{ ...thStyle, textAlign: 'right' }}>SCORE</th>
                      <th style={{ ...thStyle, textAlign: 'right' }}>CONF</th>
                      <th style={{ ...thStyle, width: 16 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecastResult.items.map((item) => {
                      const active = selectedTicker === item.ticker
                      return (
                        <tr
                          key={item.ticker}
                          onClick={() => openStock(item.ticker)}
                          className="fc-row"
                          style={{
                            cursor: 'pointer',
                            background: active ? 'var(--primary-subtle)' : 'transparent',
                            borderBottom: '1px solid var(--border)',
                            boxShadow: active ? 'inset 3px 0 0 var(--secondary)' : 'none',
                          }}
                          onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--surface-hover)' }}
                          onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent' }}
                        >
                          <td style={{ ...tdStyle, color: 'var(--text-4)', width: 32, fontFamily: 'var(--font-mono)' }}>#{item.rank}</td>
                          <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', fontWeight: 700, letterSpacing: '0.04em' }}>{item.ticker}</td>
                          <td style={{ ...tdStyle, textAlign: 'right', color: 'var(--primary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                            {typeof item.score === 'number' ? item.score.toFixed(3) : '—'}
                          </td>
                          <td style={{ ...tdStyle, textAlign: 'right', fontFamily: 'var(--font-mono)', color: CONFIDENCE_COLOR[item.confidence_label] || 'var(--text-3)' }}>
                            {Math.round((item.confidence ?? 0) * 100)}%
                          </td>
                          <td style={{ ...tdStyle, width: 16 }}>
                            <ChevronRight size={11} style={{ color: active ? 'var(--secondary)' : 'var(--text-4)', opacity: active ? 1 : 0.4 }} />
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Explainability panel */}
          <div className="fc-panel fc-accent">
            <span style={sectionLabel}>EXPLAINABILITY</span>
            {!selectedTicker ? (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-4)' }}>
                Click any ranked stock to inspect feature contributions and data quality.
              </div>
            ) : explaining ? (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>
                Loading {selectedTicker}…
              </div>
            ) : explainError ? (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--danger-light)' }}>{explainError}</div>
            ) : explainResult ? (
              <ExplainPanel
                result={explainResult}
                stockRow={forecastResult?.items?.find((s) => s.ticker === selectedTicker)}
              />
            ) : null}
          </div>
        </div>
      )}

      {/* ── Session run history ───────────────────────────────── */}
      {history.length > 0 && (
        <div className="fc-panel" style={{ marginBottom: 12 }}>
          <span style={sectionLabel}>SESSION HISTORY</span>
          {history.map((h, i) => (
            <div key={i} style={{ borderTop: '1px solid var(--border)', padding: '6px 0', fontSize: 11, color: 'var(--text-3)', display: 'flex', gap: 14, fontFamily: 'var(--font-mono)', letterSpacing: '0.02em' }}>
              <span style={{ color: 'var(--text-4)' }}>{h.ts}</span>
              <span>Year {h.year}</span>
              <span>{h.risk_level} risk</span>
              <span>{h.stock_count} stocks ranked</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Disclaimer ───────────────────────────────────────── */}
      <div className="fc-caveat">
        <span className="fc-caveat-pulse" aria-hidden="true" />
        <span>
          <strong style={{ color: 'var(--primary)' }}>Research only · Not investment advice.</strong>{' '}
          Scores are a deterministic ranking signal based on historical patterns.
          Walk-forward Spearman correlation is near zero — no reliable predictive edge has been established.
          This output must not be used for buy, sell, or hold decisions.
        </span>
      </div>
    </div>
  )
}

function ExplainPanel({ result, stockRow }) {
  return (
    <div style={{ marginTop: 6 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 10, flexWrap: 'wrap', gap: 6 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 18, fontWeight: 700, color: 'var(--text-1)', letterSpacing: '0.03em' }}>
          {result.ticker}
        </span>
        {stockRow && (
          <div style={{ display: 'flex', gap: 10, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
            <span>Score <strong style={{ color: 'var(--primary)' }}>{stockRow.score.toFixed(3)}</strong></span>
            <span>Rank <strong style={{ color: 'var(--text-2)' }}>#{stockRow.rank}</strong></span>
            <span style={{ color: CONFIDENCE_COLOR[stockRow.confidence_label] }}>
              {Math.round(stockRow.confidence * 100)}% conf
            </span>
          </div>
        )}
      </div>

      {result.is_inference_row && (
        <div style={{ fontSize: 10.5, color: 'var(--warning)', background: 'var(--warning-subtle)', border: '1px solid rgba(200,163,90,0.3)', borderRadius: 2, padding: '4px 8px', marginBottom: 8, fontFamily: 'var(--font-mono)' }}>
          2025 inference row — no T+1 return target
        </div>
      )}

      {/* Score drivers from the forecast run */}
      {stockRow?.top_parameters?.length > 0 && (
        <>
          <div style={miniLabel}>SCORE DRIVERS</div>
          {stockRow.top_parameters.slice(0, 5).map((c) => (
            <div key={c.name} style={explainRow}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.name}
              </span>
              <span style={{ fontSize: 10.5, color: 'var(--text-4)', marginLeft: 4, fontFamily: 'var(--font-mono)' }}>
                w={c.weight.toFixed(3)}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--primary)', minWidth: 48, textAlign: 'right' }}>
                +{c.contribution.toFixed(4)}
              </span>
            </div>
          ))}
        </>
      )}

      {/* Top features from explain endpoint */}
      {result.top_features?.length > 0 && (
        <>
          <div style={{ ...miniLabel, marginTop: 12 }}>TOP FEATURES (WITHIN-YEAR PERCENTILE)</div>
          {result.top_features.slice(0, 6).map((f) => (
            <div key={f.name} style={explainRow}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {f.name}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 10.5, color: 'var(--text-3)', minWidth: 64, textAlign: 'right' }}>
                {typeof f.value === 'number' ? f.value.toFixed(2) : '—'}
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: f.signal === 'above_median' ? 'var(--secondary)' : 'var(--text-4)', minWidth: 38, textAlign: 'right' }}>
                p{f.percentile_in_year.toFixed(0)}
              </span>
            </div>
          ))}
        </>
      )}

      {/* Data quality */}
      <div style={{ marginTop: 12, padding: '6px 9px', background: 'rgba(26,36,33,0.6)', border: '1px solid var(--border)', borderRadius: 2, fontSize: 10.5, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
        Coverage {((result.data_quality?.coverage ?? 0) * 100).toFixed(0)}% · {result.feature_count} features
        {result.missing_features?.length > 0 && (
          <span style={{ color: 'var(--warning)', marginLeft: 4 }}>
            · missing: {result.missing_features.slice(0, 4).join(', ')}{result.missing_features.length > 4 ? '…' : ''}
          </span>
        )}
      </div>

      {/* Warnings */}
      {stockRow?.warnings?.length > 0 && (
        <div style={{ marginTop: 6, fontSize: 10, color: 'var(--text-4)', lineHeight: 1.5 }}>
          {stockRow.warnings.filter((w) => !w.includes('Experimental')).map((w, i) => (
            <div key={i}>⚠ {w}</div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Style constants ───────────────────────────────────────────────────────────

const kicker = {
  fontFamily: 'var(--font-mono)',
  fontSize: 10.5,
  fontWeight: 600,
  color: 'var(--text-3)',
  textTransform: 'uppercase',
  letterSpacing: '0.3em',
}

const sectionLabel = {
  display: 'block',
  fontFamily: 'var(--font-mono)',
  fontSize: 10,
  fontWeight: 600,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: '0.26em',
  marginBottom: 8,
}

const metaLine = {
  fontSize: 10,
  color: 'var(--text-4)',
  fontFamily: 'var(--font-mono)',
  letterSpacing: '0.04em',
}

const miniLabel = {
  fontFamily: 'var(--font-mono)',
  fontSize: 9.5,
  fontWeight: 600,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: '0.22em',
  marginBottom: 6,
}

const badgeStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
  background: 'rgba(14,20,19,0.6)',
  border: '1px solid var(--border-strong)',
  borderRadius: 2,
  padding: '4px 9px',
  fontFamily: 'var(--font-mono)',
  fontSize: 9.5,
  color: 'var(--text-3)',
  fontWeight: 600,
  letterSpacing: '0.14em',
}

const helpText = {
  fontSize: 11.5,
  color: 'var(--text-3)',
  lineHeight: 1.6,
  margin: '0 0 11px',
}

const fieldLabel = {
  fontFamily: 'var(--font-mono)',
  fontSize: 9,
  color: 'var(--text-4)',
  display: 'block',
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: '0.2em',
}

const errorBox = {
  display: 'flex',
  alignItems: 'center',
  gap: 5,
  marginTop: 8,
  fontSize: 11.5,
  color: 'var(--danger-light)',
  background: 'var(--danger-subtle)',
  border: '1px solid rgba(185,95,68,0.4)',
  borderRadius: 2,
  padding: '7px 10px',
}

const paramChip = {
  display: 'flex',
  alignItems: 'center',
  gap: 7,
  background: 'rgba(10,14,13,0.55)',
  border: '1px solid var(--border)',
  borderRadius: 2,
  padding: '5px 9px',
}

const thStyle = {
  padding: '6px 8px',
  textAlign: 'left',
  fontFamily: 'var(--font-mono)',
  fontSize: 9.5,
  fontWeight: 600,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: '0.18em',
  borderBottom: '1px solid var(--border-strong)',
}

const tdStyle = {
  padding: '7px 8px',
  fontSize: 11.5,
  color: 'var(--text-2)',
}

const explainRow = {
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  borderTop: '1px solid var(--border)',
  padding: '5px 0',
}

const CSS = `
.fc { animation: fcCrystal 0.7s ease both; }
.fc-scan {
  position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.012) 0 1px, transparent 1px 4px);
}
.fc > *:not(.fc-scan) { position: relative; z-index: 1; }

.fc-panel {
  background: linear-gradient(180deg, rgba(18,26,24,0.85), rgba(11,16,15,0.75));
  border: 1px solid var(--border-strong);
  border-radius: 3px;
  padding: 15px 17px;
  box-shadow: inset 0 0 30px rgba(77,165,131,0.02);
}
.fc-accent { border-left: 3px solid var(--secondary); }

.fc-input {
  width: 100%; box-sizing: border-box;
  background: rgba(10,14,13,0.8);
  border: 1px solid var(--border-strong);
  border-radius: 2px;
  color: var(--text-1);
  padding: 7px 10px;
  font-size: 12px;
  font-family: var(--font-mono);
  outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.fc-input:focus {
  border-color: var(--secondary);
  box-shadow: 0 0 0 1px rgba(77,165,131,0.3);
}
.fc-input:disabled { opacity: 0.5; }

.fc-range { accent-color: var(--primary); }

.fc-btn {
  display: inline-flex; align-items: center; gap: 6px;
  border-radius: 2px; padding: 9px 15px;
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  letter-spacing: 0.18em; transition: background 0.18s, box-shadow 0.18s, border-color 0.18s;
}
.fc-btn-primary { border: none; background: var(--primary); color: #0a0e0d; }
.fc-btn-primary:hover:not(:disabled) { box-shadow: 0 0 20px rgba(200,163,90,0.3); }
.fc-btn-secondary { border: 1px solid var(--secondary); background: var(--secondary-subtle); color: var(--secondary); }
.fc-btn-secondary:hover:not(:disabled) { box-shadow: 0 0 18px rgba(77,165,131,0.22); }
.fc-btn-ghost { border: 1px solid var(--border-strong); background: transparent; color: var(--text-3); }

.fc-row { transition: background 0.15s; }

.fc-caveat {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 11px 14px;
  background: rgba(10,14,13,0.85);
  border: 1px solid rgba(200,163,90,0.4);
  border-radius: 2px;
  font-size: 11px; color: var(--text-3); line-height: 1.65;
}
.fc-caveat-pulse {
  flex-shrink: 0; margin-top: 4px;
  width: 7px; height: 7px; border-radius: 50%; background: var(--primary);
  animation: fcPulse 2.2s ease-in-out infinite;
}

@keyframes fcCrystal {
  from { opacity: 0; filter: blur(6px); }
  to { opacity: 1; filter: blur(0); }
}
@keyframes fcPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

@media (prefers-reduced-motion: reduce) {
  .fc { animation: none; }
  .fc-caveat-pulse { animation: none; }
}
`
