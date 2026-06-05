import { useCallback, useEffect, useState } from 'react'
import { Bot, Search, AlertTriangle, ShieldQuestion, RefreshCw } from 'lucide-react'
import api from '../api/client'
import { Card, SectionHeader, StatCard, EmptyState, Chip } from '../components/ui'

const NOTICE = 'Research score, not investment advice. The LLM is a decision-support layer, not the numerical predictor.'

/* ---------- safe render helpers (never render a raw object as a child) ---- */
const asText = (v) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? 'yes' : 'no'
  if (typeof v === 'number') return Number.isFinite(v) ? String(v) : '—'
  if (typeof v === 'string') return v
  try { return JSON.stringify(v) } catch { return String(v) }
}
const renderScore = (v, d = 3) =>
  v === null || v === undefined || Number.isNaN(Number(v)) ? '—' : Number(v).toFixed(d)
const toArray = (x) => (Array.isArray(x) ? x : x === null || x === undefined ? [] : [x])
function RenderList({ items, color = 'default', empty = '—' }) {
  const arr = toArray(items)
  if (!arr.length) return <span style={{ color: 'var(--text-3)' }}>{empty}</span>
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {arr.map((it, i) => (
        <Chip key={i} color={color}>{typeof it === 'object' ? asText(it) : String(it)}</Chip>
      ))}
    </div>
  )
}
function RenderObjectPreview({ obj }) {
  if (obj === null || obj === undefined) return <span style={{ color: 'var(--text-3)' }}>—</span>
  return (
    <pre style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8,
      padding: 10, fontSize: 11, overflowX: 'auto', maxHeight: 220, margin: 0 }}>
      {(() => { try { return JSON.stringify(obj, null, 2) } catch { return String(obj) } })()}
    </pre>
  )
}

const errText = (e) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (d) return asText(d)
  return e?.message || 'request failed'
}

export default function ResearchAgentPage() {
  const [summary, setSummary] = useState(null)
  const [diag, setDiag] = useState(null)
  const [dq, setDq] = useState(null)
  const [loadErr, setLoadErr] = useState({})
  const [ticker, setTicker] = useState('ASELS')
  const [score, setScore] = useState(null)
  const [askTicker, setAskTicker] = useState('')
  const [question, setQuestion] = useState('Is the BIST100 benchmark available and what does it change?')
  const [answer, setAnswer] = useState(null)

  const loadAll = useCallback(() => {
    setLoadErr({})
    api.get('/research/summary').then(r => setSummary(r.data)).catch(e => setLoadErr(p => ({ ...p, summary: errText(e) })))
    api.get('/research/model-diagnostics').then(r => setDiag(r.data)).catch(e => setLoadErr(p => ({ ...p, diag: errText(e) })))
    api.get('/research/data-quality').then(r => setDq(r.data)).catch(e => setLoadErr(p => ({ ...p, dq: errText(e) })))
  }, [])
  useEffect(() => { loadAll() }, [loadAll])

  const loadScore = () => {
    setScore({ loading: true })
    api.get(`/research/company/${encodeURIComponent(ticker.trim().toUpperCase())}/score`)
      .then(r => setScore(r.data)).catch(e => setScore({ error: errText(e) }))
  }
  const ask = () => {
    setAnswer({ loading: true })
    const body = { question }
    if (askTicker.trim()) body.ticker = askTicker.trim().toUpperCase()
    api.post('/research/ask', body).then(r => setAnswer(r.data)).catch(e => setAnswer({ error: errText(e) }))
  }

  const sctx = summary?.context || {}
  const conf = summary?.confidence || {}
  const dgx = diag?.diagnostics || {}
  const dqx = dq?.data_quality || {}
  const sc = (score && !score.loading && !score.error) ? (score.score || {}) : {}
  const llm = (score && score.llm) || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader
        title="FinanceIQ Research Agent"
        sub="Hybrid ML + constrained local LLM research support"
        icon={Bot}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <Chip color="danger">Not investment advice</Chip>
            <button onClick={loadAll} title="reload" style={iconBtn}><RefreshCw size={15} /></button>
          </div>
        }
      />

      {/* Dataset status */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px,1fr))', gap: 12 }}>
        <StatCard label="Dataset rows" value={asText(sctx.rows)} sub={`${asText(sctx.rows_with_target)} with target`} />
        <StatCard label="Validated features" value={asText(sctx.feature_count)} />
        <StatCard label="Inference-only rows" value={asText(sctx.inference_only_rows)} />
        <StatCard label="Benchmark" value={sctx.benchmark_available ? 'available' : 'missing'} sub={asText(sctx.benchmark_source)} />
        <StatCard label="Confidence" value={`${renderScore(conf.confidence_score, 2)} (${asText(conf.confidence_level)})`} />
        <StatCard label="Valid for T→T+1" value={asText(sctx.valid_for_modeling)} />
      </div>
      {loadErr.summary && <ErrCard what="summary" msg={loadErr.summary} onRetry={loadAll} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 16 }}>
        {/* Benchmark */}
        <Card>
          <SectionHeader title="Benchmark" />
          <Row k="Status" v={sctx.benchmark_available ? 'available' : 'missing'} />
          <Row k="Source" v={asText(sctx.benchmark_source)} />
          <Row k="Excess/outperform targets" v={sctx.benchmark_available ? 'enabled' : 'disabled'} />
        </Card>

        {/* Data quality */}
        <Card>
          <SectionHeader title="Data quality" />
          <Row k="Frozen columns excluded" v={asText(toArray(dqx.frozen_columns).length)} />
          <Row k="Misaligned columns" v={asText(toArray(dqx.misaligned_columns).length)} />
          <Row k="Manual financials" v={dqx.manual_financials_present ? 'present' : 'none'} />
          <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6 }}>{asText(dqx.leakage_controls)}</p>
          <p style={{ fontSize: 12, color: 'var(--warning,#b45309)' }}>
            Quarterly files (new_data_quarter) are also a frozen snapshot — not usable.
          </p>
          {loadErr.dq && <ErrCard what="data-quality" msg={loadErr.dq} onRetry={loadAll} />}
        </Card>

        {/* Model diagnostics */}
        <Card>
          <SectionHeader title="Model diagnostics" />
          <Row k="Primary target" v="next_year_return_pct" />
          <Row k="Mean Spearman" v={renderScore(dgx.mean_spearman, 3)} />
          <Row k="Weak backtest" v={asText(dgx.weak_backtest)} />
          <Row k="ML beats baseline consistently" v={asText(dgx.ml_beats_baseline_consistently)} />
          <Row k="Small sample" v={asText(dgx.small_sample)} />
          <p style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 6 }}>{asText(dgx.interpretation)}</p>
          {loadErr.diag && <ErrCard what="diagnostics" msg={loadErr.diag} onRetry={loadAll} />}
        </Card>
      </div>

      {/* Accepted groups + rejected frozen */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 16 }}>
        <Card>
          <SectionHeader title="Accepted feature groups" />
          {Object.entries(sctx.feature_groups || {}).map(([g, arr]) => (
            <Row key={g} k={g} v={asText(toArray(arr).length)} />
          ))}
        </Card>
        <Card>
          <SectionHeader title="Rejected frozen columns" sub="Snapshot — unusable as features" />
          <RenderList items={sctx.rejected_frozen_columns} color="danger" empty="none" />
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(330px,1fr))', gap: 16 }}>
        {/* Company insight */}
        <Card>
          <SectionHeader title="Company hybrid score" />
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <input value={ticker} onChange={e => setTicker(e.target.value)} placeholder="ticker (e.g. ASELS)" style={inputS} />
            <button onClick={loadScore} style={primaryBtn}>Score</button>
          </div>
          {score?.loading && <p style={{ color: 'var(--text-3)' }}>…</p>}
          {score?.error && <p style={{ color: 'var(--danger,#dc2626)' }}>{asText(score.error)}</p>}
          {score && !score.loading && !score.error && (
            <div style={{ fontSize: 13 }}>
              <Row k="Ticker" v={asText(sc.ticker || score.ticker)} />
              <Row k="Year" v={asText(sc.year)} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, margin: '8px 0' }}>
                <Mini label="ml_score" v={renderScore(sc.ml_score)} sub={asText(sc.score_source)} />
                <Mini label="confidence_score" v={renderScore(sc.confidence_score)} />
                <Mini label="llm_research_score" v={renderScore(sc.llm_research_score)} />
                <Mini label="final_research_score" v={renderScore(sc.final_research_score)} hi />
              </div>
              <Row k="Confidence level" v={asText(sc.confidence_level || conf.confidence_level)} />
              <Row k="Target / model" v={`${asText(sc.target_name)} / ${asText(sc.model_name)}`} />
              <p style={{ marginTop: 8 }}>{asText(llm.summary)}</p>
              {llm.reasoning && <p style={{ fontSize: 12, color: 'var(--text-2)' }}>{asText(llm.reasoning)}</p>}
              <Block label="Positive signals"><RenderList items={llm.positive_signals} empty="—" /></Block>
              <Block label="Negative signals"><RenderList items={llm.negative_signals} color="danger" empty="—" /></Block>
              <Block label="Warnings"><RenderList items={sc.warnings || llm.warnings} empty="—" /></Block>
              <Block label="Limitations"><RenderList items={sc.limitations || llm.limitations} empty="—" /></Block>
              <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 8 }}>
                provider: {asText(score.provider_used)} · fallback: {asText(score.fallback_used)} · {NOTICE}
              </p>
            </div>
          )}
        </Card>

        {/* Ask */}
        <Card>
          <SectionHeader title="Ask the research assistant" icon={ShieldQuestion} />
          <input value={askTicker} onChange={e => setAskTicker(e.target.value)} placeholder="ticker (optional)" style={{ ...inputS, marginBottom: 8 }} />
          <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={3}
            style={{ ...inputS, width: '100%', boxSizing: 'border-box' }} />
          <button onClick={ask} style={{ ...primaryBtn, marginTop: 8 }}>
            <Search size={14} style={{ verticalAlign: 'middle' }} /> Ask
          </button>
          {answer?.loading && <p style={{ color: 'var(--text-3)' }}>…</p>}
          {answer?.error && <p style={{ color: 'var(--danger,#dc2626)' }}>{asText(answer.error)}</p>}
          {answer && !answer.loading && !answer.error && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <p style={{ whiteSpace: 'pre-wrap' }}>{asText(answer.answer)}</p>
              <Block label="Warnings"><RenderList items={answer.warnings} empty="—" /></Block>
              <p style={{ fontSize: 11, color: 'var(--text-3)' }}>
                provider: {asText(answer.provider_used)} · fallback: {asText(answer.fallback_used)}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

function Row({ k, v }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, fontSize: 13, padding: '3px 0' }}>
      <span style={{ color: 'var(--text-3)' }}>{k}</span>
      <span style={{ fontWeight: 600, textAlign: 'right' }}>{typeof v === 'object' ? asText(v) : v}</span>
    </div>
  )
}
function Block({ label, children }) {
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 4 }}>{label}</div>
      {children}
    </div>
  )
}
function Mini({ label, v, sub, hi }) {
  return (
    <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{label}</div>
      <div style={{ fontSize: hi ? 18 : 14, fontWeight: 700 }}>{v}</div>
      {sub ? <div style={{ fontSize: 10, color: 'var(--text-3)' }}>{asText(sub)}</div> : null}
    </div>
  )
}
function ErrCard({ what, msg, onRetry }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--danger,#dc2626)', fontSize: 12, marginTop: 6 }}>
      <AlertTriangle size={14} /> {what} failed: {asText(msg)}
      <button onClick={onRetry} style={{ ...iconBtn, padding: '2px 8px' }}>retry</button>
    </div>
  )
}

const inputS = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '8px 10px', fontSize: 13, flex: 1 }
const primaryBtn = { background: 'var(--accent,#6366f1)', color: '#fff', border: 0, borderRadius: 8, padding: '8px 14px', cursor: 'pointer' }
const iconBtn = { background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '6px 8px', cursor: 'pointer' }
