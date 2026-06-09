import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Bot, Search, RefreshCw, ShieldCheck, Sparkles } from 'lucide-react'
import api from '../api/client'
import { GhostButton } from '../components/ui'
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
      <section style={agentHero}>
        <div>
          <div style={heroKicker}><Sparkles size={15} /> AI Research Assistant</div>
          <h1 style={heroTitle}>Ask questions grounded in validated project data.</h1>
          <p style={heroSub}>
            The assistant explains scores, BIST100 outcomes, weak-signal diagnostics, and company evidence.
            It does not invent LLM usage and never gives investment advice.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 }}>
            <SignalBadge tone="info">Research score, not advice</SignalBadge>
            <SignalBadge tone="good"><ShieldCheck size={12} /> Grounded data</SignalBadge>
          </div>
        </div>
        <div style={heroPanel}>
          <Bot size={22} color="var(--primary)" />
          <div style={{ color: 'var(--text-1)', fontSize: 18, fontWeight: 900 }}>Assistant status</div>
          <div style={{ color: 'var(--text-2)', fontSize: 12.8, lineHeight: 1.55 }}>Reload project context before presenting or testing local LLM mode.</div>
          <GhostButton icon={RefreshCw} onClick={loadAll}>Reload</GhostButton>
        </div>
      </section>

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

      <section style={copilotGrid}>
        <aside style={contextRail}>
          <div style={railTitle}>Project context</div>
          <div style={railMetrics}>
            <MetricCard label="Dataset rows" value={asText(sctx.rows)} sub={`${asText(sctx.rows_with_target)} with target`} />
            <MetricCard label="Validated features" value={asText(sctx.feature_count)} />
            <MetricCard label="Benchmark" value={sctx.benchmark_available ? 'Available' : 'Missing'} tone={sctx.benchmark_available ? 'good' : 'warn'} sub={asText(sctx.benchmark_source)} />
            <MetricCard label="Model signal" value={dgx.weak_backtest ? 'Weak' : 'OK'} tone={dgx.weak_backtest ? 'bad' : 'good'} sub={`Spearman ${asText(dgx.mean_spearman)}`} />
          </div>

          <EvidencePanel title="Company scorecard" sub="Fundamental ranking + data confidence + AI evidence" tone="accent">
            <div style={{ display: 'flex', gap: 8 }}>
              <input value={ticker} onChange={e => setTicker(e.target.value)} placeholder="ticker (e.g. ASELS)"
                onKeyDown={e => e.key === 'Enter' && loadScore()} style={inputS} />
              <button onClick={loadScore} style={primaryBtn}>Score</button>
            </div>
            {score?.loading && <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Scoring...</div>}
            {score?.error && <div style={{ color: 'var(--danger-light)', fontSize: 13 }}>{asText(score.error)}</div>}
            {ready && (
              <>
                <div style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                  <span style={{ fontSize: 18, fontWeight: 900 }}>{asText(sc.ticker || score.ticker)}</span>
                  <span style={{ fontSize: 12, color: 'var(--text-3)' }}>latest year {asText(sc.year)}</span>
                </div>
                <ScoreBreakdown items={[
                  { label: sc.ml_score_label || 'Fundamental ranking model', value: sc.ml_score, tone: 'info', sub: 'rank of validated year-T features' },
                  { label: sc.confidence_label || 'Data confidence', value: sc.confidence_score, tone: 'info', sub: asText(sc.confidence_level || conf.confidence_level) },
                  { label: sc.final_label || 'Final research score', value: sc.final_research_score, tone: 'accent', emphasis: true },
                ]} />
                <div style={aiEvidenceLine}>
                  <Sparkles size={13} color="var(--secondary)" />
                  <span style={{ color: 'var(--text-3)', fontWeight: 800 }}>AI evidence support</span>
                  {sc.llm_support_available
                    ? <SignalBadge tone="info">{formatNumber(sc.llm_research_score, 2)} supporting signal</SignalBadge>
                    : <span style={{ color: 'var(--text-3)' }}>unavailable - score uses fundamentals + data confidence</span>}
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
                <div style={{ fontSize: 11.5, color: 'var(--text-3)', borderTop: '1px solid var(--border)', paddingTop: 8, lineHeight: 1.5 }}>
                  AI evidence can support the final score when available, but validated fundamentals and data confidence remain primary. Not investment advice.
                </div>
              </>
            )}
          </EvidencePanel>
        </aside>

        <main style={chatPanel}>
          <div style={chatHeader}>
            <div>
              <div style={railTitle}>Ask the assistant</div>
              <div style={{ color: 'var(--text-3)', fontSize: 13 }}>Plain-English answer, grounded in validated project data.</div>
            </div>
            <SignalBadge tone={isFallback ? 'info' : 'good'}>
              {isFallback ? 'AI unavailable · fallback from validated project data' : 'AI assisted · grounded in validated project data'}
            </SignalBadge>
          </div>

          <div style={promptPills}>
            {EXAMPLES.map((ex, i) => (
              <button key={i} onClick={() => setQuestion(ex)} style={chipBtn} title="Use this prompt">{ex}</button>
            ))}
          </div>

          <div style={composer}>
            <input value={askTicker} onChange={e => setAskTicker(e.target.value)} placeholder="ticker context (optional)" style={{ ...inputS, maxWidth: 260 }} />
            <textarea value={question} onChange={e => setQuestion(e.target.value)} rows={5}
              placeholder="Ask about outperformance, weak signal, company score evidence, or benchmark context..."
              style={{ ...inputS, width: '100%', resize: 'vertical', fontSize: 15, lineHeight: 1.55 }} />
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <button onClick={ask} disabled={askLoading || !question.trim()}
                style={{ ...primaryBtn, padding: '12px 18px', opacity: (askLoading || !question.trim()) ? 0.6 : 1, cursor: askLoading ? 'wait' : 'pointer' }}>
                <Search size={15} style={{ verticalAlign: 'middle', marginRight: 6 }} />{askLoading ? 'Asking...' : 'Ask FinanceIQ'}
              </button>
              {answer && !askLoading && <button onClick={clearAnswer} style={ghostBtn}>Clear answer</button>}
              {askLoading && <span style={{ color: 'var(--text-3)', fontSize: 13 }}>Updating answer...</span>}
              {askErr && <span style={{ color: 'var(--danger-light)', fontSize: 13 }}>{asText(askErr)} - you can ask again.</span>}
            </div>
          </div>

          {answer && !askLoading && (() => {
            const r = answer.llm_result || {}
            const du = answer.data_used || {}
            return (
              <div style={answerCard}>
                <div style={answerHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Sparkles size={18} color="var(--secondary)" />
                    <div style={{ fontWeight: 900, color: 'var(--text-1)' }}>Grounded response</div>
                  </div>
                  <ModeLine answer={answer} />
                </div>
                <AnswerBlock title="Summary" color="var(--text-1)">{asText(answer.answer)}</AnswerBlock>
                {r.reasoning ? <AnswerBlock title="Evidence" color="var(--secondary)">{asText(r.reasoning)}</AnswerBlock> : null}
                <AnswerBlock title="Interpretation" color="var(--primary)">
                  {answer.intent ? `Intent: ${String(answer.intent).replace(/_/g, ' ')}. ` : ''}
                  Figures and tickers come from validated project data; the assistant only explains the evidence.
                </AnswerBlock>
                {(answer.warnings?.length) ? (
                  <div><div style={lbl('var(--warning-light)')}>Risks & limitations</div><Bullets tone="warn" size={12.5} items={hw(answer.warnings)} /></div>
                ) : null}
                <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
                  {du.source ? <SignalBadge tone="info">source: {asText(du.source)}{du.year ? ` · ${asText(du.year)}` : ''}</SignalBadge> : null}
                  <SignalBadge tone="bad">Not investment advice</SignalBadge>
                </div>
              </div>
            )
          })()}
        </main>
      </section>

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

function AnswerBlock({ title, color, children }) {
  return (
    <section style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={lbl(color)}>{title}</div>
      <p style={{ whiteSpace: 'pre-wrap', fontSize: 14, color: 'var(--text-2)', margin: 0, lineHeight: 1.7 }}>{children}</p>
    </section>
  )
}

const lbl = (c) => ({ fontSize: 11.5, fontWeight: 700, color: c, marginBottom: 6 })
const agentHero = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: 18, alignItems: 'stretch', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.35rem)', lineHeight: 1, fontWeight: 900, maxWidth: 820 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 740 }
const heroPanel = { background: 'rgba(8,15,26,0.54)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }
const copilotGrid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 340px), 1fr))', gap: 18, alignItems: 'start' }
const contextRail = { display: 'flex', flexDirection: 'column', gap: 14 }
const railTitle = { color: 'var(--text-1)', fontSize: 15, fontWeight: 900, letterSpacing: '-0.02em' }
const railMetrics = { display: 'grid', gridTemplateColumns: '1fr', gap: 10 }
const chatPanel = { background: 'linear-gradient(180deg, rgba(17,30,48,0.88), rgba(7,17,31,0.76))', border: '1px solid var(--border-strong)', borderRadius: 24, padding: 22, boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column', gap: 16 }
const chatHeader = { display: 'flex', justifyContent: 'space-between', gap: 16, alignItems: 'flex-start', flexWrap: 'wrap' }
const promptPills = { display: 'flex', gap: 8, flexWrap: 'wrap' }
const composer = { display: 'flex', flexDirection: 'column', gap: 10, background: 'rgba(3,7,18,0.34)', border: '1px solid var(--border)', borderRadius: 18, padding: 14 }
const answerCard = { display: 'flex', flexDirection: 'column', gap: 16, background: 'linear-gradient(135deg, rgba(57,230,208,0.10), rgba(139,92,246,0.09), rgba(3,7,18,0.30))', border: '1px solid rgba(125,211,252,0.26)', borderRadius: 20, padding: 18, boxShadow: 'var(--shadow-sm)' }
const answerHeader = { display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center', flexWrap: 'wrap', borderBottom: '1px solid var(--border)', paddingBottom: 12 }
const aiEvidenceLine = { display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, flexWrap: 'wrap' }
const chipBtn = { background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
  borderRadius: 999, padding: '7px 12px', fontSize: 12, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }
const ghostBtn = { background: 'transparent', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 14px', fontSize: 13, fontWeight: 600, cursor: 'pointer' }
const inputS = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)',
  borderRadius: 'var(--radius-md)', padding: '9px 11px', fontSize: 13, flex: 1, boxSizing: 'border-box', outline: 'none' }
const primaryBtn = { background: 'var(--primary)', color: '#0b111a', border: 0, borderRadius: 'var(--radius-md)',
  padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap' }
