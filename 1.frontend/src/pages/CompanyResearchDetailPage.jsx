import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Building2, ShieldCheck, Sparkles } from 'lucide-react'
import { EmptyState, GhostButton } from '../components/ui'
import { researchApi } from '../api/researchApi'
import {
  ScoreBreakdown, EvidencePanel, RenderList, Bullets, CollapsibleJson, SignalBadge,
  DecisionVerdict, humanizeWarning, asText, NOT_ADVICE,
} from '../utils/safeRender'

const hw = (items) => (Array.isArray(items) ? items.map(humanizeWarning) : items)

export default function CompanyResearchDetailPage() {
  const { ticker } = useParams()
  const nav = useNavigate()
  const [detail, setDetail] = useState(null)
  const [score, setScore] = useState(null)
  const [err, setErr] = useState(null)

  useEffect(() => {
    researchApi.company(ticker).then(r => r.error ? setErr(r.error) : setDetail(r.data))
    researchApi.companyScore(ticker).then(r => setScore(r.data))
  }, [ticker])

  if (err) return <EmptyState icon={Building2} title={`${ticker} not found`} description={asText(err)} />

  const ctx = detail?.context || {}
  const sc = score?.score || {}
  const llm = score?.llm || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1080 }}>
      <section style={styles.hero}>
        <div>
          <div style={styles.kicker}><Sparkles size={15} /> Company Research Snapshot</div>
          <h1 style={styles.title}>{asText(ticker).toUpperCase()}</h1>
          <p style={styles.subtitle}>
            Latest year {asText(ctx.latest_year)} · {ctx.is_inference_row ? 'inference-only row with no realized target yet' : 'historical row with next-year target available'}.
            Score is diagnostic research support, not investment advice.
          </p>
          <div style={styles.badges}>
            <SignalBadge tone="good"><ShieldCheck size={12} /> Validated data</SignalBadge>
            <SignalBadge tone="bad">Not investment advice</SignalBadge>
          </div>
        </div>
        <div style={styles.actionPanel}>
          <Building2 size={22} color="var(--primary)" />
          <div style={styles.panelTitle}>Research context</div>
          <div style={styles.panelText}>Hybrid score combines validated features, data confidence, and available AI evidence.</div>
          <GhostButton icon={ArrowLeft} onClick={() => nav('/research/companies')}>Companies</GhostButton>
        </div>
      </section>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px,1fr))', gap: 16 }}>
        {/* Score breakdown */}
        <EvidencePanel title="Hybrid research score" sub={`source: ${asText(sc.score_source)}`} tone="accent">
          <ScoreBreakdown items={[
            { label: 'ML score', value: sc.ml_score, tone: 'info', sub: 'rank of validated year-T features' },
            { label: 'Confidence score', value: sc.confidence_score, tone: 'info', sub: asText(sc.confidence_level) },
            { label: 'LLM support score', value: sc.llm_research_score, tone: 'info', sub: 'decision-support layer' },
            { label: 'Final research score', value: sc.final_research_score, tone: 'accent', emphasis: true },
          ]} />
          {sc.decision_support_verdict && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 700 }}>Decision support</span>
              <DecisionVerdict verdict={sc.decision_support_verdict} />
            </div>
          )}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 2 }}>
            <SignalBadge tone="neutral">target: {asText(sc.target_name)}</SignalBadge>
            <SignalBadge tone="neutral">model: {asText(sc.model_name)}</SignalBadge>
          </div>
        </EvidencePanel>

        {/* Feature signals */}
        <EvidencePanel title="Validated feature signals" sub="percentile rank of year-T features">
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--success-light)', marginBottom: 5 }}>Top positive</div>
            <RenderList items={Object.keys(ctx.top_positive_features || {})} color="success" empty="—" />
          </div>
          <div>
            <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--danger-light)', margin: '4px 0 5px' }}>Top negative</div>
            <RenderList items={Object.keys(ctx.top_negative_features || {})} color="danger" empty="—" />
          </div>
        </EvidencePanel>
      </div>

      {/* Explanation */}
      <EvidencePanel title="Research agent explanation" tone="info"
        footer={`provider: ${asText(score?.provider_used)} · fallback: ${asText(score?.fallback_used)} · ${NOT_ADVICE}`}>
        <p style={{ fontSize: 13, color: 'var(--text-2)', margin: 0, lineHeight: 1.55 }}>{asText(llm.summary)}</p>
        {llm.reasoning && <p style={{ fontSize: 12.5, color: 'var(--text-3)', margin: 0, lineHeight: 1.5 }}>{asText(llm.reasoning)}</p>}
        {(llm.positive_signals?.length || llm.negative_signals?.length) ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px,1fr))', gap: 12 }}>
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--success-light)', marginBottom: 6 }}>Positive signals</div>
              <Bullets tone="good" size={12.5} items={llm.positive_signals} />
            </div>
            <div>
              <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--danger-light)', marginBottom: 6 }}>Negative signals</div>
              <Bullets tone="bad" size={12.5} items={llm.negative_signals} />
            </div>
          </div>
        ) : null}
      </EvidencePanel>

      {/* Warnings & limitations */}
      <EvidencePanel title="Warnings & limitations" tone="warn">
        <div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', marginBottom: 6 }}>Warnings</div>
          <Bullets tone="warn" size={12.5} items={hw(sc.warnings || ctx.warnings)} />
        </div>
        <div>
          <div style={{ fontSize: 11.5, fontWeight: 700, color: 'var(--text-3)', margin: '4px 0 6px' }}>Limitations</div>
          <Bullets tone="warn" size={12.5} items={hw(sc.limitations || llm.limitations)} />
        </div>
        <p style={{ fontSize: 12, color: 'var(--warning-light)', margin: 0 }}>
          Valuation / profitability data is frozen & rejected — score relies on balance-sheet & growth features only.
        </p>
      </EvidencePanel>

      <CollapsibleJson label="View raw response (debug)" value={{ detail, score }} />
    </div>
  )
}

const styles = {
  hero: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
    gap: 18,
    alignItems: 'stretch',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))',
    padding: 24,
  },
  kicker: { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 },
  title: { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2.2rem, 6vw, 4rem)', lineHeight: 1, fontWeight: 900 },
  subtitle: { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 720 },
  badges: { display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 16 },
  actionPanel: { background: 'rgba(8,15,26,0.54)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', padding: 18, display: 'flex', flexDirection: 'column', gap: 10 },
  panelTitle: { color: 'var(--text-1)', fontSize: 18, fontWeight: 900 },
  panelText: { color: 'var(--text-2)', fontSize: 12.8, lineHeight: 1.55 },
}
