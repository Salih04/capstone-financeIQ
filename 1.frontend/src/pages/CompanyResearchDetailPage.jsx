import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Building2 } from 'lucide-react'
import { Card, SectionHeader, EmptyState } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, RenderList, WarningList, JsonBlock, formatNumber, asText, NOT_ADVICE } from '../utils/safeRender'

export default function CompanyResearchDetailPage() {
  const { ticker } = useParams()
  const nav = useNavigate()
  const [detail, setDetail] = useState(null)
  const [score, setScore] = useState(null)
  const [err, setErr] = useState(null)
  const [showJson, setShowJson] = useState(false)

  useEffect(() => {
    researchApi.company(ticker).then(r => r.error ? setErr(r.error) : setDetail(r.data))
    researchApi.companyScore(ticker).then(r => setScore(r.data))
  }, [ticker])

  if (err) return <EmptyState icon={Building2} title={`${ticker} not found`} description={asText(err)} />

  const ctx = detail?.context || {}
  const sc = score?.score || {}
  const llm = score?.llm || {}

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader
        title={`${asText(ticker).toUpperCase()} — research detail`}
        sub={`Latest year ${asText(ctx.latest_year)} · ${ctx.is_inference_row ? 'inference-only' : 'has target'}`}
        icon={Building2}
        actions={<button onClick={() => nav('/research/companies')} style={btn}><ArrowLeft size={14} /> back</button>}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px,1fr))', gap: 12 }}>
        <MetricCard label="ML score" value={formatNumber(sc.ml_score, 3)} sub={asText(sc.score_source)} />
        <MetricCard label="Confidence" value={formatNumber(sc.confidence_score, 3)} sub={asText(sc.confidence_level)} />
        <MetricCard label="LLM research score" value={formatNumber(sc.llm_research_score, 3)} />
        <MetricCard label="Final research score" value={formatNumber(sc.final_research_score, 3)} tone="good" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px,1fr))', gap: 16 }}>
        <Card>
          <SectionHeader title="Research agent explanation" />
          <p style={{ fontSize: 13 }}>{asText(llm.summary)}</p>
          {llm.reasoning && <p style={{ fontSize: 12, color: 'var(--text-2)' }}>{asText(llm.reasoning)}</p>}
          <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 6 }}>
            provider: {asText(score?.provider_used)} · fallback: {asText(score?.fallback_used)}
          </div>
        </Card>
        <Card>
          <SectionHeader title="Validated features (percentile rank)" />
          <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 4 }}>Top positive</div>
          <RenderList items={Object.keys(ctx.top_positive_features || {})} empty="—" />
          <div style={{ fontSize: 12, color: 'var(--text-3)', margin: '8px 0 4px' }}>Top negative</div>
          <RenderList items={Object.keys(ctx.top_negative_features || {})} color="danger" empty="—" />
        </Card>
      </div>

      <Card>
        <SectionHeader title="Warnings & limitations" />
        <div style={{ fontSize: 12, color: 'var(--text-3)' }}>Warnings</div>
        <WarningList items={sc.warnings || ctx.warnings} />
        <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 8 }}>Limitations</div>
        <WarningList items={sc.limitations || llm.limitations} />
        <p style={{ fontSize: 12, color: 'var(--warning,#b45309)', marginTop: 8 }}>
          Valuation/profitability data is frozen & rejected — score relies on balance-sheet/growth only.
        </p>
        <p style={{ fontSize: 11, fontWeight: 700, marginTop: 6 }}>{NOT_ADVICE}</p>
      </Card>

      <Card>
        <SectionHeader title="Raw response (debug)"
          actions={<button onClick={() => setShowJson(s => !s)} style={btn}>{showJson ? 'hide' : 'show'}</button>} />
        {showJson && <JsonBlock value={{ detail, score }} maxHeight={360} />}
      </Card>
    </div>
  )
}

const btn = { background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '4px 10px', fontSize: 12, cursor: 'pointer' }
