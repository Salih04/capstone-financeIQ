import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Bot, FlaskConical, Building2, Database, LineChart, ArrowRight } from 'lucide-react'
import { SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, RealityCheckCard, asText, NOT_ADVICE } from '../utils/safeRender'

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
  const dgx = diag?.diagnostics || {}
  const benchOk = bench?.available
  const valid = ctx.valid_for_modeling
  const weak = dgx.weak_backtest

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 18, maxWidth: 1180 }}>
      <SectionHeader
        title="FinanceIQ Research Terminal"
        sub="Validated T→T+1 equity-research system · BIST100 benchmark · explainable hybrid agent"
        icon={LineChart}
      />

      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(155px,1fr))', gap: 12 }}>
        <MetricCard label="Dataset" value={valid ? 'VALID' : asText(valid)} tone={valid ? 'good' : 'warn'} sub="T→T+1 modeling set" />
        <MetricCard label="Rows" value={asText(ctx.rows)} sub="40 companies × 6 years" />
        <MetricCard label="Features" value={asText(ctx.feature_count)} sub="validated year-varying" />
        <MetricCard label="Target rows" value={asText(ctx.rows_with_target)} sub={`${asText(ctx.inference_only_rows)} inference-only`} />
        <MetricCard label="Benchmark" value={benchOk ? 'Available' : 'Missing'} tone={benchOk ? 'good' : 'warn'} sub={asText(bench?.source)} />
        <MetricCard label="Model signal" value={weak ? 'Weak' : 'OK'} tone={weak ? 'bad' : 'good'} sub={`Spearman ${asText(dgx.mean_spearman)}`} />
      </div>

      {/* Reality check + next action */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(330px,1fr))', gap: 16 }}>
        <RealityCheckCard
          sub="Honest status — academically defensible"
          items={[
            { tone: 'good', text: 'T→T+1 pipeline is valid with real next-year return targets.' },
            { tone: 'good', text: `BIST100 benchmark available (${asText(bench?.source)}) → excess / outperform targets enabled.` },
            { tone: 'bad', text: 'Historical valuation / profitability columns are a frozen snapshot — rejected.' },
            { tone: 'warn', text: 'Predictive skill is currently weak / unstable.' },
            { tone: 'info', text: 'Real per-year historical financials required to unlock signal.' },
          ]}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ background: 'linear-gradient(135deg, var(--primary-subtle), transparent)',
            border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: 0.6 }}>Next action</div>
            <p style={{ fontSize: 13.5, color: 'var(--text-2)', marginTop: 8, lineHeight: 1.55 }}>
              Supply real per-year valuation / profitability history, then re-run the pipeline. The 17
              balance-sheet & growth features alone do not show a reliable edge.
            </p>
            <button onClick={() => nav('/data-quality')} style={ctaBtn}>
              Open Data Quality evidence <ArrowRight size={15} />
            </button>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)', fontWeight: 600, textAlign: 'center' }}>{NOT_ADVICE}</div>
        </div>
      </div>

      {/* Action cards */}
      <div>
        <div style={sectionTitle}>Research Terminal</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(215px,1fr))', gap: 12 }}>
          {[
            ['Research Agent', Bot, '/research-agent', 'Hybrid ML + local LLM insight'],
            ['Companies', Building2, '/research/companies', 'Company-level research scores'],
            ['Experiments', FlaskConical, '/experiments', 'Walk-forward · benchmark targets'],
            ['Data Quality', Database, '/data-quality', 'Frozen columns · leakage · evidence'],
            ['Benchmark', LineChart, '/benchmark', 'BIST100 yearly returns'],
          ].map(([label, Icon, to, sub]) => (
            <ActionCard key={to} label={label} Icon={Icon} sub={sub} onClick={() => nav(to)} />
          ))}
        </div>
      </div>
    </div>
  )
}

function ActionCard({ label, Icon, sub, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <div onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{ cursor: 'pointer', background: 'var(--surface-2)',
        border: `1px solid ${hover ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', gap: 12, alignItems: 'center',
        transition: 'border-color .15s, transform .12s', transform: hover ? 'translateY(-2px)' : 'none' }}>
      <span style={{ width: 38, height: 38, borderRadius: 10, flexShrink: 0, background: 'var(--primary-subtle)',
        color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon size={19} />
      </span>
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-1)' }}>{label}</div>
        <div style={{ fontSize: 11.5, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{sub}</div>
      </div>
    </div>
  )
}

const ctaBtn = { display: 'inline-flex', alignItems: 'center', gap: 7, marginTop: 14, background: 'var(--primary)',
  color: '#0b111a', border: 0, borderRadius: 'var(--radius-md)', padding: '9px 16px', fontSize: 13, fontWeight: 700, cursor: 'pointer' }
const sectionTitle = { fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }
