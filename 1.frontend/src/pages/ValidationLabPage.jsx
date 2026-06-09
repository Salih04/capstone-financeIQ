import { useState, useEffect } from 'react'
import { FlaskConical, Play, BarChart3, Clock, TrendingUp, TrendingDown, AlertCircle, ShieldCheck, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState } from '../components/ui'

const inputS = {
  background: 'var(--surface-1)',
  border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)',
  color: 'var(--text-1)',
  padding: '8px 12px',
  fontSize: 13,
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
  fontFamily: 'inherit',
}

function MetricCard({ label, value, good }) {
  const color = good == null ? 'var(--primary)' : good ? 'var(--success)' : 'var(--warning)'
  return (
    <div style={{
      background: 'var(--surface-1)',
      border: `1px solid var(--border)`,
      borderRadius: 'var(--radius-lg)',
      padding: '1rem',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>{label}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 800, color }}>{value ?? '–'}</div>
    </div>
  )
}

const validationHero = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 20 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1, fontWeight: 900, maxWidth: 820 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 760 }
const heroBadge = { display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 16, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-strong)', borderRadius: 999, padding: '6px 10px', color: 'var(--text-2)', fontSize: 12, fontWeight: 800 }
function MetricsGrid({ result }) {
  const acc = result.accuracy
  const f1 = result.f1
  const auc = result.roc_auc
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10 }}>
      <MetricCard label="Accuracy" value={acc != null ? `${(acc * 100).toFixed(1)}%` : null} good={acc >= 0.75} />
      <MetricCard label="Precision" value={result.precision?.toFixed(3)} />
      <MetricCard label="Recall" value={result.recall?.toFixed(3)} />
      <MetricCard label="F1 Score" value={f1?.toFixed(3)} good={f1 >= 0.7} />
      <MetricCard label="ROC-AUC" value={auc?.toFixed(3)} good={auc >= 0.75} />
    </div>
  )
}

function ConfusionMatrix({ cm }) {
  if (!cm || cm.length < 2) return null
  const cells = [
    { lbl: 'TN', val: cm[0][0], color: 'var(--success)', bg: 'rgba(16,185,129,0.08)' },
    { lbl: 'FP', val: cm[0][1], color: 'var(--danger)', bg: 'rgba(239,68,68,0.08)' },
    { lbl: 'FN', val: cm[1][0], color: 'var(--warning)', bg: 'rgba(245,158,11,0.08)' },
    { lbl: 'TP', val: cm[1][1], color: 'var(--success)', bg: 'rgba(16,185,129,0.08)' },
  ]
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>Confusion Matrix</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, maxWidth: 280 }}>
        {cells.map(({ lbl, val, color, bg }) => (
          <div key={lbl} style={{ background: bg, border: `1px solid ${color}40`, borderRadius: 'var(--radius-md)', padding: '14px 20px', textAlign: 'center' }}>
            <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 4 }}>{lbl}</div>
            <div style={{ fontSize: '1.4rem', fontWeight: 800, color }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function FeatureImportances({ importances }) {
  if (!importances?.length) return null
  const max = Math.max(...importances.map(f => Math.abs(f.coefficient || 0)))
  return (
    <div>
      <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 12 }}>
          Feature Importances (Coefficient Ranking)
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>
            {['Rank', 'Feature', 'Coefficient', 'Direction', 'Visual'].map(h => (
              <th key={h} style={{ background: 'var(--surface-1)', color: 'var(--text-3)', fontSize: 11, padding: '8px 12px', textAlign: 'left', fontWeight: 600 }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {importances.map((f) => {
            const pct = max > 0 ? (Math.abs(f.coefficient) / max) * 100 : 0
            const isPos = (f.coefficient || 0) >= 0
            const color = isPos ? 'var(--success)' : 'var(--danger)'
            return (
              <tr key={f.id || f.feature_name}>
                <td style={{ padding: '8px 12px', color: 'var(--text-2)', borderTop: '1px solid var(--border)' }}>{f.importance_rank}</td>
                <td style={{ padding: '8px 12px', color: 'var(--text-1)', borderTop: '1px solid var(--border)' }}>{f.feature_name}</td>
                <td style={{ padding: '8px 12px', fontWeight: 700, color, borderTop: '1px solid var(--border)' }}>{f.coefficient?.toFixed(4)}</td>
                <td style={{ padding: '8px 12px', borderTop: '1px solid var(--border)' }}>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    background: isPos ? 'rgba(16,185,129,0.12)' : 'rgba(239,68,68,0.12)',
                    color, borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 11, fontWeight: 700,
                  }}>
                    {isPos ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
                    {f.sign_direction || (isPos ? 'positive' : 'negative')}
                  </span>
                </td>
                <td style={{ padding: '8px 12px', borderTop: '1px solid var(--border)' }}>
                  <div style={{ background: 'var(--surface-1)', borderRadius: 4, height: 8, width: 160 }}>
                    <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 4 }} />
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default function ValidationLabPage() {
  const [models, setModels] = useState([])
  const [labelDefs, setLabelDefs] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [trainRatio, setTrainRatio] = useState(0.7)
  const [selectedLabel, setSelectedLabel] = useState('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])
  const [importances, setImportances] = useState([])
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/admin/scoring-models').then(({ data }) => {
      setModels(data)
      if (data.length > 0) setSelectedModel(String(data[0].id))
    }).catch(() => {})
    api.get('/labeling/definitions').then(({ data }) => {
      setLabelDefs(data)
    }).catch(() => {})
  }, [])

  const loadHistory = async (modelId) => {
    if (!modelId) return
    try {
      const { data } = await api.get(`/validation/models/${modelId}/history`)
      setHistory(data)
    } catch { setHistory([]) }
    try {
      const { data } = await api.get(`/validation/models/${modelId}/feature-importances`)
      setImportances(data)
    } catch { setImportances([]) }
  }

  const handleModelChange = (v) => {
    setSelectedModel(v)
    setResult(null)
    loadHistory(v)
  }

  useEffect(() => {
    if (selectedModel) loadHistory(selectedModel)
  }, [selectedModel])

  const runValidation = async () => {
    if (!selectedModel) { setMsg('Please select a model.'); return }
    setRunning(true)
    setMsg('')
    try {
      const payload = { scoring_model_id: parseInt(selectedModel), train_ratio: trainRatio }
      if (selectedLabel) payload.label_def_id = parseInt(selectedLabel)
      const { data } = await api.post('/validation/run', payload)
      setResult(data)
      await loadHistory(selectedModel)
    } catch (e) { setMsg(e.response?.data?.detail || 'Validation failed.') }
    finally { setRunning(false) }
  }

  let confusionMatrix = null
  if (result?.confusion_matrix_json) {
    try { confusionMatrix = JSON.parse(result.confusion_matrix_json) } catch {}
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={validationHero}>
        <div style={heroKicker}><Sparkles size={15} /> Validation Lab</div>
        <h1 style={heroTitle}>Time-split validation for model governance.</h1>
        <p style={heroSub}>Run train/test validation, inspect calibration, and review feature importance. Metrics are diagnostic, not investment claims.</p>
        <span style={heroBadge}><ShieldCheck size={13} /> Leakage-aware evaluation</span>
      </section>

      {msg && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
          borderRadius: 'var(--radius-md)', padding: '10px 14px',
          color: 'var(--danger)', fontSize: 13, marginBottom: 16,
        }}>
          <AlertCircle size={14} />
          {msg}
        </div>
      )}

      {/* Config Card */}
      <Card style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-2)', marginBottom: 14 }}>Validation Configuration</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1.2fr auto', gap: 14, alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-3)', display: 'block', marginBottom: 4 }}>Model</label>
            <select style={inputS} value={selectedModel} onChange={e => handleModelChange(e.target.value)}>
              {models.map(m => <option key={m.id} value={m.id}>{m.model_name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} v{m.version}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-3)', display: 'block', marginBottom: 4 }}>Label Strategy</label>
            <select style={inputS} value={selectedLabel} onChange={e => setSelectedLabel(e.target.value)}>
              <option value="">Default</option>
              {labelDefs.map(ld => <option key={ld.id} value={ld.id}>{ld.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 11, color: 'var(--text-3)', display: 'block', marginBottom: 4 }}>
              Train Ratio: <span style={{ color: 'var(--primary)', fontWeight: 700 }}>{(trainRatio * 100).toFixed(0)}%</span>
            </label>
            <input
              type="range" min={0.5} max={0.9} step={0.05} value={trainRatio}
              onChange={e => setTrainRatio(parseFloat(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--primary)', marginTop: 6 }}
            />
          </div>
          <button
            onClick={runValidation}
            disabled={running}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: running ? 'var(--surface-3)' : 'var(--primary)',
              color: running ? 'var(--text-3)' : '#fff',
              border: 'none', borderRadius: 'var(--radius-md)',
              padding: '10px 20px', fontSize: 13, fontWeight: 700,
              cursor: running ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap',
            }}
          >
            <Play size={14} />
            {running ? 'Running…' : 'Validate'}
          </button>
        </div>
      </Card>

      {/* Results */}
      {result && (
        <Card style={{ marginBottom: 20, borderColor: 'var(--primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <BarChart3 size={16} style={{ color: 'var(--primary)' }} />
            <span style={{ fontWeight: 700, color: 'var(--text-1)' }}>Validation Results</span>
          </div>
          <MetricsGrid result={result} />

          {result.calibration_summary && (
            <div style={{ marginTop: 14, background: 'var(--surface-1)', borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
              <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>Calibration</div>
              <div style={{ fontSize: 13, color: 'var(--text-2)' }}>{result.calibration_summary}</div>
            </div>
          )}

          {confusionMatrix && (
            <div style={{ marginTop: 16 }}>
              <ConfusionMatrix cm={confusionMatrix} />
            </div>
          )}

          {result.train_period_start && (
            <div style={{ marginTop: 14, fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 6, alignItems: 'center' }}>
              <Clock size={12} />
              Train: {result.train_period_start} → {result.train_period_end}
              &nbsp;|&nbsp;
              Test: {result.test_period_start} → {result.test_period_end}
            </div>
          )}
        </Card>
      )}

      {/* Feature Importances */}
      {importances.length > 0 && (
        <Card style={{ marginBottom: 20 }}>
          <FeatureImportances importances={importances} />
        </Card>
      )}

      {/* History */}
      {history.length > 0 && (
        <Card>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <Clock size={15} style={{ color: 'var(--text-3)' }} />
            <span style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, fontWeight: 600 }}>Validation History</span>
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr>
                {['Date', 'Accuracy', 'F1', 'AUC', 'Train End', 'Test End'].map(h => (
                  <th key={h} style={{ background: 'var(--surface-1)', color: 'var(--text-3)', fontSize: 11, padding: '8px 12px', textAlign: 'left', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((h) => (
                <tr key={h.id}>
                  <td style={{ padding: '8px 12px', color: 'var(--text-2)', borderTop: '1px solid var(--border)' }}>
                    {new Date(h.created_at).toLocaleDateString('en-US')}
                  </td>
                  <td style={{ padding: '8px 12px', color: h.accuracy >= 0.75 ? 'var(--success)' : 'var(--warning)', fontWeight: 600, borderTop: '1px solid var(--border)' }}>
                    {h.accuracy != null ? `${(h.accuracy * 100).toFixed(1)}%` : '–'}
                  </td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-1)', borderTop: '1px solid var(--border)' }}>{h.f1?.toFixed(3) ?? '–'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-1)', borderTop: '1px solid var(--border)' }}>{h.roc_auc?.toFixed(3) ?? '–'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-2)', borderTop: '1px solid var(--border)' }}>{h.train_period_end ?? '–'}</td>
                  <td style={{ padding: '8px 12px', color: 'var(--text-2)', borderTop: '1px solid var(--border)' }}>{h.test_period_end ?? '–'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {history.length === 0 && !result && (
        <EmptyState
          icon={<FlaskConical size={32} />}
          title="No validations run yet"
          description="Select a model above and click Validate."
        />
      )}
    </div>
  )
}
