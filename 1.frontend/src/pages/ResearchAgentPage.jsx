import { useEffect, useState } from 'react'
import { Bot, Search, AlertTriangle, ShieldQuestion } from 'lucide-react'
import api from '../api/client'
import { Card, SectionHeader, StatCard, EmptyState, Chip } from '../components/ui'

const NOTICE = 'Research score, not investment advice. The LLM is a decision-support layer, not the numerical predictor.'
const f = (v, d = 3) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d))

export default function ResearchAgentPage() {
  const [summary, setSummary] = useState(null)
  const [diag, setDiag] = useState(null)
  const [dq, setDq] = useState(null)
  const [ticker, setTicker] = useState('ASELS')
  const [score, setScore] = useState(null)
  const [question, setQuestion] = useState('Is the BIST100 benchmark available and what does it change?')
  const [answer, setAnswer] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    api.get('/research/summary').then(r => setSummary(r.data)).catch(e => setErr(e?.response?.data?.detail || 'summary failed'))
    api.get('/research/model-diagnostics').then(r => setDiag(r.data)).catch(() => {})
    api.get('/research/data-quality').then(r => setDq(r.data)).catch(() => {})
  }, [])

  const loadScore = () => {
    setScore(null)
    api.get(`/research/company/${encodeURIComponent(ticker.trim().toUpperCase())}/score`)
      .then(r => setScore(r.data)).catch(e => setScore({ error: e?.response?.data?.detail || 'not found' }))
  }
  const ask = () => {
    setAnswer({ loading: true })
    api.post('/research/ask', { question }).then(r => setAnswer(r.data)).catch(e => setAnswer({ error: e?.response?.data?.detail || 'ask failed' }))
  }

  if (err) return <EmptyState icon={AlertTriangle} title="Research agent unavailable" description={String(err)} />

  const sctx = summary?.context || {}
  const conf = summary?.confidence || {}
  const dqx = dq?.data_quality || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="Research Assistant (LLM-assisted)" sub={NOTICE} icon={Bot} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 12 }}>
        <StatCard label="Dataset rows" value={sctx.rows ?? '—'} sub={`${sctx.rows_with_target ?? '—'} with target`} />
        <StatCard label="Validated features" value={sctx.feature_count ?? '—'} />
        <StatCard label="Benchmark" value={sctx.benchmark_available ? 'available' : 'missing'} sub={sctx.benchmark_source || ''} />
        <StatCard label="Confidence" value={`${f(conf.confidence_score, 2)} (${conf.confidence_level || '—'})`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px,1fr))', gap: 16 }}>
        <Card>
          <SectionHeader title="Data quality" />
          <div style={{ fontSize: 13, color: 'var(--text-2)' }}>
            <p><b>Frozen columns excluded:</b> {(dqx.frozen_columns || []).length}</p>
            <p><b>Misaligned:</b> {(dqx.misaligned_columns || []).length}</p>
            <p><b>Manual financials:</b> {dqx.manual_financials_present ? 'present' : 'none'}</p>
            <p style={{ fontSize: 12, color: 'var(--text-3)' }}>{dqx.leakage_controls}</p>
          </div>
        </Card>
        <Card>
          <SectionHeader title="Accepted feature groups" />
          {Object.entries(sctx.feature_groups || {}).map(([g, arr]) => (
            <div key={g} style={{ marginBottom: 6 }}>
              <b style={{ fontSize: 12 }}>{g}</b>{' '}
              <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{(arr || []).length}</span>
            </div>
          ))}
        </Card>
        <Card>
          <SectionHeader title="Model diagnostics" />
          <div style={{ fontSize: 13, color: 'var(--text-2)' }}>
            <p><b>Mean Spearman:</b> {f(diag?.diagnostics?.mean_spearman, 3)}</p>
            <p><b>Weak backtest:</b> {String(diag?.diagnostics?.weak_backtest)}</p>
            <p style={{ fontSize: 12, color: 'var(--text-3)' }}>{diag?.diagnostics?.interpretation}</p>
          </div>
        </Card>
      </div>

      <Card>
        <SectionHeader title="Rejected frozen columns" sub="From the yearly snapshot — unusable as features" />
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          {(sctx.rejected_frozen_columns || []).map(c => <Chip key={c} color="danger">{c}</Chip>)}
        </div>
      </Card>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        <Card>
          <SectionHeader title="Company hybrid score" />
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <input value={ticker} onChange={e => setTicker(e.target.value)} placeholder="ticker"
              style={{ flex: 1, background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '8px 10px', fontSize: 13 }} />
            <button onClick={loadScore} style={{ background: 'var(--accent,#6366f1)', color: '#fff', border: 0, borderRadius: 8, padding: '8px 14px', cursor: 'pointer' }}>Score</button>
          </div>
          {score?.error && <p style={{ color: 'var(--danger,#dc2626)' }}>{score.error}</p>}
          {score?.score && (
            <div style={{ fontSize: 13 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                <Mini label="ml_score" v={f(score.score.ml_score, 3)} />
                <Mini label="confidence_score" v={f(score.score.confidence_score, 3)} />
                <Mini label="llm_research_score" v={f(score.score.llm_research_score, 3)} />
                <Mini label="final_research_score" v={f(score.score.final_research_score, 3)} hi />
              </div>
              <p style={{ marginTop: 8 }}>{score.llm?.summary}</p>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                {(score.context?.warnings || []).map(w => <Chip key={w} color="default">{w}</Chip>)}
              </div>
              <p style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 8 }}>
                provider: {score.provider_used} · fallback: {String(score.fallback_used)} · {NOTICE}
              </p>
            </div>
          )}
        </Card>

        <Card>
          <SectionHeader title="Ask the research assistant" icon={ShieldQuestion} />
          <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={3}
            style={{ width: '100%', boxSizing: 'border-box', background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '8px 10px', fontSize: 13 }} />
          <button onClick={ask} style={{ marginTop: 8, background: 'var(--accent,#6366f1)', color: '#fff', border: 0, borderRadius: 8, padding: '8px 14px', cursor: 'pointer' }}>
            <Search size={14} style={{ verticalAlign: 'middle' }} /> Ask
          </button>
          {answer?.loading && <p style={{ color: 'var(--text-3)' }}>…</p>}
          {answer?.error && <p style={{ color: 'var(--danger,#dc2626)' }}>{answer.error}</p>}
          {answer?.answer && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <p>{answer.answer}</p>
              <p style={{ fontSize: 11, color: 'var(--text-3)' }}>
                provider: {answer.provider_used} · fallback: {String(answer.fallback_used)}
              </p>
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}

function Mini({ label, v, hi }) {
  return (
    <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{label}</div>
      <div style={{ fontSize: hi ? 18 : 14, fontWeight: 700 }}>{v}</div>
    </div>
  )
}
