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
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>

      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={{ ...panel, marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 5 }}>
              <BrainCircuit size={15} style={{ color: 'var(--primary)' }} />
              <span style={kicker}>Research Forecasting Lab</span>
            </div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: 'var(--text-1)', lineHeight: 1.2 }}>
              Parameter-Based Stock Ranking
            </h1>
            <p style={{ margin: '5px 0 0', fontSize: 12, color: 'var(--text-3)', lineHeight: 1.6, maxWidth: 700 }}>
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
            <span style={badgeStyle}><ShieldCheck size={10} /> Not investment advice</span>
            <span style={badgeStyle}><Zap size={10} /> Experimental</span>
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
        <div style={panel}>
          <div style={sectionLabel}>Step 1 · Train Parameters</div>
          <p style={helpText}>
            Identify which features best separate top-25% returners from the rest across training years.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
            <div>
              <label style={fieldLabel}>From year</label>
              <select
                value={trainYearFrom}
                onChange={(e) => setTrainYearFrom(parseInt(e.target.value))}
                style={selectS}
                disabled={!options}
              >
                {(options?.trainable_years || []).map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
            <div>
              <label style={fieldLabel}>To year</label>
              <select
                value={trainYearTo}
                onChange={(e) => setTrainYearTo(parseInt(e.target.value))}
                style={selectS}
                disabled={!options}
              >
                {(options?.trainable_years || []).map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: 10 }}>
            <label style={fieldLabel}>Top features ({topN})</label>
            <input
              type="range"
              min={4}
              max={20}
              value={topN}
              onChange={(e) => setTopN(parseInt(e.target.value))}
              style={{ width: '100%', marginTop: 4, accentColor: 'var(--primary)' }}
            />
          </div>

          <button
            onClick={trainModel}
            disabled={!canTrain || training}
            style={{
              ...primaryBtn,
              opacity: !canTrain || training ? 0.5 : 1,
              cursor: !canTrain || training ? 'not-allowed' : 'pointer',
            }}
          >
            <BrainCircuit size={12} />
            {training ? 'Deriving weights…' : 'Train Parameters'}
          </button>

          {trainError && <div style={errorBox}>{trainError}</div>}
        </div>

        {/* Step 2: Run Forecast */}
        <div style={panel}>
          <div style={sectionLabel}>Step 2 · Run Forecast</div>
          <p style={helpText}>
            Apply trained weights to rank all stocks in the selected year.
            {!trainResult && <span style={{ color: 'var(--warning-light)' }}> Complete Step 1 first.</span>}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8, marginBottom: 10 }}>
            <div>
              <label style={fieldLabel}>Year</label>
              <select
                value={forecastYear}
                onChange={(e) => setForecastYear(e.target.value)}
                style={selectS}
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
              <label style={fieldLabel}>User type</label>
              <select value={userType} onChange={(e) => setUserType(e.target.value)} style={selectS}>
                <option value="individual">Individual</option>
                <option value="advanced">Advanced</option>
                <option value="corporate">Corporate</option>
              </select>
            </div>
            <div>
              <label style={fieldLabel}>Risk</label>
              <select value={riskLevel} onChange={(e) => setRiskLevel(e.target.value)} style={selectS}>
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
              style={{
                ...secondaryBtn,
                opacity: !canRun || running ? 0.5 : 1,
                cursor: !canRun || running ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={12} />
              {running ? 'Ranking…' : 'Run Forecast'}
            </button>
            <button
              disabled
              title="Time-CV requires multi-year next-year returns — not available for 2025 inference rows."
              style={{ ...ghostBtn, opacity: 0.38, cursor: 'not-allowed' }}
            >
              Run Time CV
            </button>
          </div>

          {options?.inference_years?.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-4)' }}>
              * Years marked with * are inference-only (no T+1 return target).
            </div>
          )}

          {forecastError && <div style={errorBox}>{forecastError}</div>}
        </div>
      </div>

      {/* ── Trained parameter weights ─────────────────────────── */}
      {trainResult && (
        <div style={{ ...panel, marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 6 }}>
            <span style={sectionLabel}>Learned Feature Weights</span>
            <span style={{ fontSize: 10.5, color: 'var(--text-4)', fontFamily: 'var(--font-mono)' }}>
              {trainResult.total_training_rows} training rows · {trainResult.winner_rows} top-quartile rows
              · p{trainResult.winner_percentile * 100} threshold
              · years {trainResult.train_year_from}–{trainResult.train_year_to}
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(190px, 1fr))', gap: 5 }}>
            {trainResult.top_parameters.map((p) => (
              <div key={p.name} style={paramChip}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.name}
                </span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, flexShrink: 0 }}>
                  <div style={{ width: 40, height: 3, background: 'var(--border)', borderRadius: 2 }}>
                    <div style={{ width: `${p.weight * 100}%`, height: '100%', background: 'var(--primary)', borderRadius: 2 }} />
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
          <div style={panel}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 4 }}>
              <span style={sectionLabel}>Ranked Stocks</span>
              {forecastResult && (
                <span style={{ fontSize: 10.5, color: 'var(--text-4)', fontFamily: 'var(--font-mono)' }}>
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
                    <tr style={{ position: 'sticky', top: 0, background: 'var(--surface-2)', zIndex: 1 }}>
                      <th style={thStyle}>#</th>
                      <th style={thStyle}>Ticker</th>
                      <th style={{ ...thStyle, textAlign: 'right' }}>Score</th>
                      <th style={{ ...thStyle, textAlign: 'right' }}>Conf</th>
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
                          style={{
                            cursor: 'pointer',
                            background: active ? 'var(--primary-subtle)' : 'transparent',
                            borderBottom: '1px solid var(--border)',
                          }}
                          onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--surface-3)' }}
                          onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent' }}
                        >
                          <td style={{ ...tdStyle, color: 'var(--text-4)', width: 32 }}>#{item.rank}</td>
                          <td style={{ ...tdStyle, fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{item.ticker}</td>
                          <td style={{ ...tdStyle, textAlign: 'right', color: 'var(--primary)', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                            {typeof item.score === 'number' ? item.score.toFixed(3) : '—'}
                          </td>
                          <td style={{ ...tdStyle, textAlign: 'right', fontFamily: 'var(--font-mono)', color: CONFIDENCE_COLOR[item.confidence_label] || 'var(--text-3)' }}>
                            {Math.round((item.confidence ?? 0) * 100)}%
                          </td>
                          <td style={{ ...tdStyle, width: 16 }}>
                            <ChevronRight size={11} style={{ color: active ? 'var(--primary)' : 'var(--text-4)', opacity: active ? 1 : 0.4 }} />
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
          <div style={panel}>
            <span style={sectionLabel}>Explainability</span>
            {!selectedTicker ? (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-4)' }}>
                Click any ranked stock to inspect feature contributions and data quality.
              </div>
            ) : explaining ? (
              <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-3)' }}>
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
        <div style={{ ...panel, marginBottom: 12 }}>
          <span style={sectionLabel}>Session History</span>
          {history.map((h, i) => (
            <div key={i} style={{ borderTop: '1px solid var(--border)', padding: '5px 0', fontSize: 11, color: 'var(--text-3)', display: 'flex', gap: 14 }}>
              <span style={{ color: 'var(--text-4)', fontFamily: 'var(--font-mono)' }}>{h.ts}</span>
              <span>Year {h.year}</span>
              <span>{h.risk_level} risk</span>
              <span>{h.stock_count} stocks ranked</span>
            </div>
          ))}
        </div>
      )}

      {/* ── Disclaimer ───────────────────────────────────────── */}
      <div style={{ padding: '9px 13px', background: 'var(--danger-subtle)', border: '1px solid rgba(233,112,86,0.18)', borderRadius: 'var(--radius-sm)', fontSize: 11, color: 'var(--text-3)', lineHeight: 1.65 }}>
        <strong style={{ color: 'var(--danger-light)' }}>Research Use Only.</strong>{' '}
        Scores are a deterministic ranking signal based on historical patterns.
        Walk-forward Spearman correlation is near zero — no reliable predictive edge has been established.
        This output must not be used for buy, sell, or hold decisions.
      </div>
    </div>
  )
}

function ExplainPanel({ result, stockRow }) {
  return (
    <div style={{ marginTop: 4 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8, flexWrap: 'wrap', gap: 6 }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 15, fontWeight: 800, color: 'var(--text-1)' }}>
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
        <div style={{ fontSize: 10.5, color: 'var(--warning)', background: 'var(--warning-subtle)', borderRadius: 5, padding: '3px 7px', marginBottom: 8 }}>
          2025 inference row — no T+1 return target
        </div>
      )}

      {/* Score drivers from the forecast run */}
      {stockRow?.top_parameters?.length > 0 && (
        <>
          <div style={miniLabel}>Score Drivers</div>
          {stockRow.top_parameters.slice(0, 5).map((c) => (
            <div key={c.name} style={explainRow}>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.name}
              </span>
              <span style={{ fontSize: 10.5, color: 'var(--text-4)', marginLeft: 4 }}>
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
          <div style={{ ...miniLabel, marginTop: 10 }}>Top Features (within-year percentile)</div>
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
      <div style={{ marginTop: 10, padding: '5px 8px', background: 'var(--surface-3)', borderRadius: 5, fontSize: 10.5, color: 'var(--text-3)' }}>
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

const panel = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)',
  padding: '13px 15px',
}

const kicker = {
  fontSize: 11,
  fontWeight: 700,
  color: 'var(--primary)',
  textTransform: 'uppercase',
  letterSpacing: 0.8,
}

const sectionLabel = {
  display: 'block',
  fontSize: 10.5,
  fontWeight: 700,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: 0.7,
  marginBottom: 6,
}

const miniLabel = {
  fontSize: 10,
  fontWeight: 700,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: 0.6,
  marginBottom: 5,
}

const badgeStyle = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid var(--border-strong)',
  borderRadius: 999,
  padding: '3px 8px',
  fontSize: 10.5,
  color: 'var(--text-3)',
  fontWeight: 700,
}

const helpText = {
  fontSize: 11,
  color: 'var(--text-3)',
  lineHeight: 1.6,
  margin: '0 0 9px',
}

const fieldLabel = {
  fontSize: 10,
  color: 'var(--text-4)',
  display: 'block',
  marginBottom: 3,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
}

const selectS = {
  width: '100%',
  background: 'var(--surface-1)',
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-sm)',
  color: 'var(--text-1)',
  padding: '6px 9px',
  fontSize: 12,
  outline: 'none',
}

const primaryBtn = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  background: 'var(--primary)',
  color: '#07111F',
  fontSize: 12,
  fontWeight: 700,
  padding: '7px 13px',
}

const secondaryBtn = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  border: '1px solid var(--secondary)',
  borderRadius: 'var(--radius-sm)',
  background: 'var(--secondary-subtle)',
  color: 'var(--secondary)',
  fontSize: 12,
  fontWeight: 700,
  padding: '7px 13px',
}

const ghostBtn = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 5,
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-sm)',
  background: 'transparent',
  color: 'var(--text-3)',
  fontSize: 11.5,
  padding: '7px 11px',
}

const errorBox = {
  display: 'flex',
  alignItems: 'center',
  gap: 5,
  marginTop: 7,
  fontSize: 11.5,
  color: 'var(--danger-light)',
  background: 'var(--danger-subtle)',
  borderRadius: 5,
  padding: '6px 9px',
}

const paramChip = {
  display: 'flex',
  alignItems: 'center',
  gap: 7,
  background: 'var(--surface-1)',
  border: '1px solid var(--border)',
  borderRadius: 5,
  padding: '4px 8px',
}

const thStyle = {
  padding: '5px 8px',
  textAlign: 'left',
  fontSize: 10,
  fontWeight: 700,
  color: 'var(--text-4)',
  textTransform: 'uppercase',
  letterSpacing: 0.5,
  borderBottom: '1px solid var(--border-strong)',
}

const tdStyle = {
  padding: '6px 8px',
  fontSize: 11.5,
  color: 'var(--text-2)',
}

const explainRow = {
  display: 'flex',
  alignItems: 'center',
  gap: 6,
  borderTop: '1px solid var(--border)',
  padding: '4px 0',
}
