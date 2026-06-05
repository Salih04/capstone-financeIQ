import { useCallback, useEffect, useState } from 'react'
import { Bot, Search, RefreshCw, ShieldCheck, Cpu } from 'lucide-react'
import api from '../api/client'
import { SectionHeader, GhostButton } from '../components/ui'
import {
  MetricCard, EvidencePanel, ScoreBreakdown, SignalBadge, Bullets,
  WarningCallout, DecisionVerdict, humanizeWarning, asText, formatNumber, NOT_ADVICE,
} from '../utils/safeRender'

const hw = (items) => (Array.isArray(items) ? items.map(humanizeWarning) : items)

const errText = (e) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string') return d
  if (d) return asText(d)
  return e?.message || 'request failed'
}

export default function ResearchAgentPage() {
  const [summary, setSummary] = useState(null)
  const [diag, setDiag] = useState(null)
  const [loadErr, setLoadErr] = useState(null)
  const [ticker, setTicker] = useState('ASELS')
  const [score, setScore] = useState(null)
  const [askTicker, setAskTicker] = useState('')
  const [question, setQuestion] = useState('Which stocks beat BIST100?')
  const [answer, setAnswer] = useState(null)
  const [askLoading, setAskLoading] = useState(false)
  const [askErr, setAskErr] = useState(null)

  const loadAll = useCallback(() => {
    setLoadErr(null)
    api.get('/research/summary').then(r => setSummary(r.data)).catch(e => setLoadErr(errText(e)))
    api.get('/research/model-diagnostics').then(r => setDiag(r.data)).catch(e => setLoadErr(errText(e)))
  }, [])
  useEffect(() => { loadAll() }, [loadAll])

  const loadScore = () => {
    setScore({ loading: true })
    api.get(`/research/company/${encodeURIComponent(ticker.trim().toUpperCase())}/score`)
      .then(r => setScore(r.data)).catch(e => setScore({ error: errText(e) }))
  }
  const ask = async () => {
    if (!question.trim() || askLoading) return
    setAskLoading(true)
    setAskErr(null)
    const body = { question: question.trim() }
    if (askTicker.trim()) body.ticker = askTicker.trim().toUpperCase()
    try {
      const r = await api.post('/research/ask', body)
      setAnswer(r.data)
    } catch (e) {
      setAskErr(errText(e))
    } finally {
      setAskLoading(false)
    }
  }
  const clearAnswer = () => { setAnswer(null); setAskErr(null) }

  const sctx = summary?.context || {}
  const conf = summary?.confidence || {}
  const dgx = diag?.diagnostics || {}
  const ready = score && !score.loading && !score.error
  const sc = ready ? (score.score || {}) : {}
  const llm = (score && score.llm) || {}

  // agent status — provider/fallback surface from last call, else defaults
  const lastMeta = (ready && score) || answer || {}
  const provider = lastMeta.provider_used ?? 'none'
  const fallback = lastMeta.fallback_used
  const isFallback = provider === 'none' || fallback

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader
        title="FinanceIQ Research Agent"
        sub="Hybrid ML + constrained local LLM research support"
        icon={Bot}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <SignalBadge tone="bad">Not investment advice</SignalBadge>
            <GhostButton icon={RefreshCw} onClick={loadAll}>Reload</GhostButton>
          </div>
        }
      />

      {loadErr && <WarningCallout title="Failed to load agent status" tone="bad">{asText(loadErr)}</WarningCallout>}

      {/* Agent status card */}
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16,
        display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span style={{ width: 40, height: 40, borderRadius: 11, background: 'var(--primary-subtle)', color: 'var(--primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}><Cpu size={20} /></span>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: 700 }}>LLM research layer</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>Decision-support only · numerical predictor stays the ML model</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <SignalBadge tone={isFallback ? 'warn' : 'good'}>{isFallback ? 'Deterministic fallback mode' : 'Connected to LM Studio'}</SignalBadge>
          <SignalBadge tone="good"><ShieldCheck size={12} /> safety mode active</SignalBadge>
        </div>
      </div>

      {/* Plain-language provider explanation */}
      <div style={{ fontSize: 12, color: 'var(--text-3)', background: 'var(--surface-1)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '9px 12px', lineHeight: 1.5 }}>
        {isFallback
          ? <>The backend is using <b style={{ color: 'var(--warning-light)' }}>deterministic fallback</b> — answers come from validated reports only.
              If you run Docker and want LM Studio, set <code>RESEARCH_LLM_BASE_URL</code> to <code>http://host.docker.internal:1234/v1/chat/completions</code> (inside a container <code>localhost</code> is the container itself, not your Mac).</>
          : <>Connected to <b style={{ color: 'var(--success-light)' }}>LM Studio</b> — the assistant phrases answers, but tickers and numbers always come from validated project data.</>}
      </div>

      {/* Dataset KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px,1fr))', gap: 12 }}>
        <MetricCard label="Dataset rows" value={asText(sctx.rows)} sub={`${asText(sctx.rows_with_target)} with target`} />
        <MetricCard label="Validated features" value={asText(sctx.feature_count)} />
        <MetricCard label="Benchmark" value={sctx.benchmark_available ? 'Available' : 'Missing'} tone={sctx.benchmark_available ? 'good' : 'warn'} sub={asText(sctx.benchmark_source)} />
        <MetricCard label="Confidence" value={`${formatNumber(conf.confidence_score, 2)}`} sub={asText(conf.confidence_level)} />
        <MetricCard label="Model signal" value={dgx.weak_backtest ? 'Weak' : 'OK'} tone={dgx.weak_backtest ? 'bad' : 'good'} sub={`Spearman ${asText(dgx.mean_spearman)}`} />
      </div>

      {/* Score lookup + Ask */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px,1fr))', gap: 16 }}>
        {/* Company score lookup */}
        <EvidencePanel title="Company score lookup" sub="Hybrid ML + confidence + LLM support" tone="accent">
          <div style={{ display: 'flex', gap: 8 }}>
            <input value={ticker} onChange={e => setTicker(e.target.value)} placeholder="ticker (e.g. ASELS)"
              onKeyDown={e => e.key === 'Enter' && loadScore()} style={inputS} />
            <button onClick={loadScore} style={primaryBtn}>Score</button>
          </div>
          {score?.loading && <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Scoring…</div>}
          {score?.error && <div style={{ color: 'var(--danger-light)', fontSize: 13 }}>{asText(score.error)}</div>}
          {ready && (
            <>
              <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                <span style={{ fontSize: 16, fontWeight: 800 }}>{asText(sc.ticker || score.ticker)}</span>
                <span style={{ fontSize: 12, color: 'var(--text-3)' }}>year {asText(sc.year)}</span>
              </div>
              <ScoreBreakdown items={[
                { label: 'ML score', value: sc.ml_score, tone: 'info', sub: asText(sc.score_source) },
                { label: 'Confidence score', value: sc.confidence_score, tone: 'info', sub: asText(sc.confidence_level || conf.confidence_level) },
                { label: 'LLM support score', value: sc.llm_research_score, tone: 'info' },
                { label: 'Final research score', value: sc.final_research_score, tone: 'accent', emphasis: true },
              ]} />
              {sc.decision_support_verdict && (
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700 }}>Decision support</span>
                    <DecisionVerdict verdict={sc.decision_support_verdict} />
                  </div>
                  {sc.blocking_limitations?.length ? <Bullets tone="warn" size={12} items={sc.blocking_limitations} /> : null}
                </div>
              )}
            </>
          )}
        </EvidencePanel>

        {/* Ask */}
        <EvidencePanel title="Ask the research assistant" sub="Grounded, specific answers from validated project data" tone="info">
          <input value={askTicker} onChange={e => setAskTicker(e.target.value)} placeholder="ticker (optional)" style={inputS} />
          <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={3}
            placeholder="e.g. Which stocks beat BIST100? · Why is the signal weak? · What columns were rejected?"
            style={{ ...inputS, width: '100%', resize: 'vertical' }} />
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={ask} disabled={askLoading || !question.trim()}
              style={{ ...primaryBtn, opacity: (askLoading || !question.trim()) ? 0.6 : 1, cursor: askLoading ? 'wait' : 'pointer' }}>
              <Search size={14} style={{ verticalAlign: 'middle', marginRight: 5 }} />{askLoading ? 'Asking…' : 'Ask'}
            </button>
            {answer && !askLoading && (
              <button onClick={clearAnswer} style={{ ...ghostBtn }}>Clear answer</button>
            )}
          </div>
          {askLoading && <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Updating answer…</div>}
          {askErr && <div style={{ color: 'var(--danger-light)', fontSize: 13 }}>{asText(askErr)} — you can ask again.</div>}
          {answer && !askLoading && (() => {
            const r = answer.llm_result || {}
            const du = answer.data_used || {}
            return (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {answer.intent ? <SignalBadge tone="neutral">intent: {asText(answer.intent)}</SignalBadge> : null}
                <p style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-1)', margin: 0, lineHeight: 1.55, fontWeight: 600 }}>{asText(answer.answer)}</p>
                {r.reasoning ? <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>{asText(r.reasoning)}</p> : null}
                {(answer.warnings?.length) ? <div><div style={lbl('var(--warning-light)')}>Notes</div><Bullets tone="warn" size={12} items={hw(answer.warnings)} /></div> : null}
                {(du.source) ? <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Data used: {asText(du.source)}{du.year ? ` · year ${asText(du.year)}` : ''}{du.rows_used ? ` · ${asText(du.rows_used)} rows` : ''}</div> : null}
                <ProviderLine provider={answer.provider_used} fallback={answer.fallback_used} diag={answer.diagnostics} />
              </div>
            )
          })()}
        </EvidencePanel>
      </div>

      {/* Explanation panel — only when a score is loaded */}
      {ready && (
        <EvidencePanel title="Explanation" tone="info"
          footer={`provider: ${asText(score.provider_used)} · fallback: ${asText(score.fallback_used)} · ${NOT_ADVICE}`}>
          {llm.summary && <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>{asText(llm.summary)}</p>}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: 14 }}>
            <div>
              <div style={lbl('var(--success-light)')}>Positive signals</div>
              <Bullets tone="good" size={12.5} items={llm.positive_signals} />
            </div>
            <div>
              <div style={lbl('var(--danger-light)')}>Negative signals</div>
              <Bullets tone="bad" size={12.5} items={llm.negative_signals} />
            </div>
            <div>
              <div style={lbl('var(--warning-light)')}>Limitations</div>
              <Bullets tone="warn" size={12.5} items={hw(sc.limitations || llm.limitations)} />
            </div>
          </div>
        </EvidencePanel>
      )}
    </div>
  )
}

function ProviderLine({ provider, fallback, diag }) {
  const fb = provider === 'none' || fallback
  return (
    <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
      {fb
        ? 'LLM unavailable; answer generated from validated reports only.'
        : `Connected to LM Studio (${asText(diag?.configured_model || provider)}).`}
    </div>
  )
}

const lbl = (c) => ({ fontSize: 11.5, fontWeight: 700, color: c, marginBottom: 6 })
const ghostBtn = { background: 'transparent', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }
const inputS = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 11px', fontSize: 13, flex: 1, boxSizing: 'border-box', outline: 'none' }
const primaryBtn = { background: 'var(--primary)', color: '#0b111a', border: 0, borderRadius: 'var(--radius-md)',
  padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }
