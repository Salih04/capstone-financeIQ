import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Bot, Search, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
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
  const [params] = useSearchParams()

  // prefill question from ?q= (Topbar "Ask AI" / search)
  useEffect(() => {
    const q = params.get('q')
    if (q) setQuestion(q)
  }, [params])

  const EXAMPLES = [
    'Which companies outperformed BIST100 in 2025?',
    'Why is ASELS on the watchlist?',
    'Explain THYAO’s score in plain English.',
    'Compare ASELS and FROTO by profitability and valuation.',
    'Why is the model signal weak?',
  ]

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

  // agent status — reflect the ACTUAL last call (llm vs fallback)
  const lastMeta = (ready && score) || answer || {}
  const aiUsed = lastMeta.llm_used === true
  const isFallback = !aiUsed

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader
        title="AI Research Assistant"
        sub="Ask in plain English — grounded in validated project data"
        icon={Bot}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <SignalBadge tone="info">Research score, not advice</SignalBadge>
            <GhostButton icon={RefreshCw} onClick={loadAll}>Reload</GhostButton>
          </div>
        }
      />

      {loadErr && <WarningCallout title="Failed to load agent status" tone="bad">{asText(loadErr)}</WarningCallout>}

      {/* Agent status card */}
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 16,
        display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <span style={{ width: 40, height: 40, borderRadius: 11, background: 'linear-gradient(135deg, var(--primary), var(--secondary))', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, boxShadow: '0 2px 10px rgba(244,176,74,0.3)' }}><Sparkles size={20} /></span>
          <div>
            <div style={{ fontSize: 13.5, fontWeight: 800 }}>FinanceIQ Research Copilot</div>
            <div style={{ fontSize: 11.5, color: 'var(--text-3)' }}>Explains the validated data — the numbers stay the ML model’s</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <SignalBadge tone={isFallback ? 'info' : 'good'}>{isFallback ? 'Validated data mode' : 'AI assistance enabled'}</SignalBadge>
          <SignalBadge tone="good"><ShieldCheck size={12} /> safety mode active</SignalBadge>
        </div>
      </div>

      {/* Plain-language explanation (no debug wording) */}
      <div style={{ fontSize: 12, color: 'var(--text-3)', background: 'var(--surface-1)',
        border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', padding: '9px 12px', lineHeight: 1.5 }}>
        {isFallback
          ? <>Running in <b style={{ color: 'var(--info)' }}>validated data mode</b> — answers are generated directly from the validated project reports. Connect a local model (LM Studio) to add AI phrasing; the figures stay the same either way.</>
          : <>AI assistance is <b style={{ color: 'var(--success-light)' }}>enabled</b> — the assistant phrases answers, but every ticker, score and number comes from validated project data. Nothing is invented.</>}
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
        {/* Company score lookup — analyst scorecard */}
        <EvidencePanel title="Company scorecard" sub="Fundamental ranking + data confidence + AI evidence" tone="accent">
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
                <span style={{ fontSize: 12, color: 'var(--text-3)' }}>latest year {asText(sc.year)}</span>
              </div>
              <ScoreBreakdown items={[
                { label: sc.ml_score_label || 'Fundamental ranking model', value: sc.ml_score, tone: 'info', sub: 'rank of validated year-T features' },
                { label: sc.confidence_label || 'Data confidence', value: sc.confidence_score, tone: 'info', sub: asText(sc.confidence_level || conf.confidence_level) },
                { label: sc.final_label || 'Final research score', value: sc.final_research_score, tone: 'accent', emphasis: true },
              ]} />
              {/* AI evidence support — only when meaningful */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
                <Sparkles size={13} color="var(--secondary)" />
                <span style={{ color: 'var(--text-3)', fontWeight: 700 }}>AI evidence support</span>
                {sc.llm_support_available
                  ? <SignalBadge tone="info">{formatNumber(sc.llm_research_score, 2)}</SignalBadge>
                  : <span style={{ color: 'var(--text-3)' }}>unavailable — score uses fundamentals + data confidence</span>}
              </div>
              {sc.decision_support_verdict && (
                <div style={{ borderTop: '1px solid var(--border)', paddingTop: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700 }}>Decision status</span>
                    <DecisionVerdict verdict={sc.decision_support_verdict} />
                  </div>
                  {sc.blocking_limitations?.length ? <Bullets tone="warn" size={12} items={sc.blocking_limitations} /> : null}
                </div>
              )}
              <div style={{ fontSize: 11, color: 'var(--text-3)', borderTop: '1px solid var(--border)', paddingTop: 8 }}>
                Final = 0.65·fundamentals + 0.20·data confidence + 0.15·AI evidence (AI weight redistributed when unavailable).
                This is a research score, not a buy/sell recommendation.
              </div>
            </>
          )}
        </EvidencePanel>

        {/* Ask */}
        <EvidencePanel title="Ask the assistant" sub="Plain-English answers, grounded in validated project data" tone="info">
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => setQuestion(ex)} style={chipBtn} title="Use this prompt">{ex}</button>
            ))}
          </div>
          <input value={askTicker} onChange={e => setAskTicker(e.target.value)} placeholder="ticker (optional)" style={inputS} />
          <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={3}
            placeholder="Ask anything about the validated data…"
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
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 12, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <div style={lbl('var(--text-2)')}>Summary</div>
                  <p style={{ whiteSpace: 'pre-wrap', fontSize: 13, color: 'var(--text-1)', margin: 0, lineHeight: 1.6, fontWeight: 600 }}>{asText(answer.answer)}</p>
                </div>
                {r.reasoning ? <div><div style={lbl('var(--text-3)')}>Evidence</div><p style={{ fontSize: 12.5, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>{asText(r.reasoning)}</p></div> : null}
                {(answer.warnings?.length) ? <div><div style={lbl('var(--warning-light)')}>Risks & limitations</div><Bullets tone="warn" size={12} items={hw(answer.warnings)} /></div> : null}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                  {answer.intent ? <SignalBadge tone="neutral">{String(answer.intent).replace(/_/g, ' ')}</SignalBadge> : null}
                  {du.source ? <SignalBadge tone="info">source: {asText(du.source)}{du.year ? ` · ${asText(du.year)}` : ''}</SignalBadge> : null}
                  <SignalBadge tone="bad">Not investment advice</SignalBadge>
                </div>
                <ModeLine answer={answer} />
              </div>
            )
          })()}
        </EvidencePanel>
      </div>

      {/* Explanation panel — only when a score is loaded */}
      {ready && (
        <EvidencePanel title="Explanation" tone="info" footer={NOT_ADVICE}>
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

function ModeLine({ answer }) {
  const used = answer?.llm_used
  const model = answer?.model || answer?.diagnostics?.configured_model
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontWeight: 600,
      color: used ? 'var(--success-light)' : 'var(--info)' }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: used ? 'var(--success)' : 'var(--info)' }} />
      {used
        ? `AI assisted${model ? ` · ${asText(model)}` : ''} · grounded in validated project data`
        : 'AI unavailable — generated from validated reports'}
    </div>
  )
}

const lbl = (c) => ({ fontSize: 11.5, fontWeight: 700, color: c, marginBottom: 6 })
const chipBtn = { background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
  borderRadius: 999, padding: '5px 11px', fontSize: 11.5, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }
const ghostBtn = { background: 'transparent', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }
const inputS = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 11px', fontSize: 13, flex: 1, boxSizing: 'border-box', outline: 'none' }
const primaryBtn = { background: 'var(--primary)', color: '#0b111a', border: 0, borderRadius: 'var(--radius-md)',
  padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }
