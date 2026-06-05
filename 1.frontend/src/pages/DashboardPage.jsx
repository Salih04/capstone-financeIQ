import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, ShieldCheck, FlaskConical, Building2, Database, Activity } from 'lucide-react'
import { Card, SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, WarningCallout, asText, NOT_ADVICE } from '../utils/safeRender'

export default function DashboardPage() {
  const nav = useNavigate()
  const [summary, setSummary] = useState(null)
  const [bench, setBench] = useState(null)
  const [diag, setDiag] = useState(null)

  useEffect(() => {
    researchApi.summary().then(r => setSummary(r.data))
    researchApi.benchmark().then(r => setBench(r.data))
    researchApi.diagnostics().then(r => setDiag(r.data))
  }, [])

  const ctx = summary?.context || {}
  const conf = summary?.confidence || {}
  const dgx = diag?.diagnostics || {}
  const benchOk = bench?.available
  const valid = ctx.valid_for_modeling

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="FinanceIQ Research Terminal" sub="T→T+1 modeling · BIST100 benchmark · explainable research agent" icon={Activity} />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px,1fr))', gap: 12 }}>
        <MetricCard label="Dataset" value={valid ? 'VALID' : asText(valid)} tone={valid ? 'good' : 'warn'} sub="T→T+1 modeling set" />
        <MetricCard label="Rows" value={asText(ctx.rows)} sub="40 companies × 6 years" />
        <MetricCard label="Features" value={asText(ctx.feature_count)} sub="validated year-varying" />
        <MetricCard label="Target rows" value={asText(ctx.rows_with_target)} sub={`${asText(ctx.inference_only_rows)} inference-only`} />
        <MetricCard label="Benchmark" value={benchOk ? 'Available' : 'Missing'} tone={benchOk ? 'good' : 'warn'} sub={asText(bench?.source)} />
        <MetricCard label="Model signal" value={dgx.weak_backtest ? 'Weak' : 'OK'} tone={dgx.weak_backtest ? 'bad' : 'good'} sub={`Spearman ${asText(dgx.mean_spearman)}`} />
        <MetricCard label="Valuation/profitability" value="Rejected" tone="bad" sub="frozen snapshot" />
        <MetricCard label="Research Agent" value="Available" tone="good" sub={`confidence ${asText(conf.confidence_level)}`} />
      </div>

      <Card>
        <SectionHeader title="Project reality check" sub="Honest status — academically defensible" icon={ShieldCheck} />
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7 }}>
          <li>The T→T+1 pipeline is <b>valid</b> with real next-year return targets.</li>
          <li>BIST100 benchmark is <b>available</b> ({asText(bench?.source)}) → excess/outperform targets enabled.</li>
          <li>Existing yearly XLSX valuation/profitability/income columns are a <b>frozen snapshot</b> and were rejected.</li>
          <li>Quarterly Fintables exports are <b>also frozen</b> — not usable as time-varying fundamentals.</li>
          <li>Predictive skill is <b>weak/unstable</b> until true historical financials are supplied.</li>
          <li><b>{NOT_ADVICE}</b></li>
        </ul>
      </Card>

      <WarningCallout title="What to do next">
        Supply real per-year valuation/profitability history (see Data Quality page), then re-run the pipeline.
        The 17 balance-sheet/growth features alone do not show a reliable edge.
      </WarningCallout>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px,1fr))', gap: 12 }}>
        {[
          ['Research Agent', Bot, '/research-agent', 'Hybrid ML + local LLM insight'],
          ['Data Quality', Database, '/data-quality', 'Frozen columns · leakage · evidence'],
          ['Experiments', FlaskConical, '/experiments', 'Walk-forward · benchmark targets'],
          ['Companies', Building2, '/research/companies', 'Company-level research scores'],
        ].map(([label, Icon, to, sub]) => (
          <Card key={to} hoverable>
            <div onClick={() => nav(to)} style={{ cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'center' }}>
              <Icon size={22} color="var(--accent,#6366f1)" />
              <div>
                <div style={{ fontWeight: 700 }}>{label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{sub}</div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
