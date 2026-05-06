import { useEffect, useState, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Play, GitCompare, TrendingUp, TrendingDown,
  Minus, BarChart3, DollarSign, Layers, RefreshCw, ArrowUpRight,
  Activity, Shield, Zap,
} from 'lucide-react'
import api from '../api/client'
import {
  SectionHeader, TabBar, Card, PrimaryButton, GhostButton,
  ChangeChip, Skeleton, ScoreBadge, Chip, EmptyState,
} from '../components/ui'

const fmt = (v, pct = false) => {
  if (v == null) return '—'
  if (pct) return (v * 100).toFixed(2) + '%'
  if (Math.abs(v) >= 1e9) return (v / 1e9).toFixed(2) + 'B'
  if (Math.abs(v) >= 1e6) return (v / 1e6).toFixed(2) + 'M'
  return Number.isInteger(v) ? String(v) : v.toFixed(2)
}

const FINANCIAL_ROWS = [
  { key: 'revenue', label: 'Revenue' },
  { key: 'gross_profit', label: 'Gross Profit' },
  { key: 'operating_income', label: 'Operating Income' },
  { key: 'net_income', label: 'Net Income' },
  { key: 'total_assets', label: 'Total Assets' },
  { key: 'total_equity', label: 'Shareholders Equity' },
  { key: 'total_liabilities', label: 'Total Liabilities' },
  { key: 'current_assets', label: 'Current Assets' },
  { key: 'current_liabilities', label: 'Current Liabilities' },
  { key: 'cash', label: 'Cash & Equivalents' },
  { key: 'operating_cash_flow', label: 'Operating Cash Flow' },
  { key: 'inventory', label: 'Inventory' },
]

const METRIC_GROUPS = [
  {
    label: 'Profitability', color: 'var(--success)',
    metrics: [
      { key: 'roa', label: 'ROA', pct: true },
      { key: 'roe', label: 'ROE', pct: true },
      { key: 'operating_margin', label: 'Op. Margin', pct: true },
      { key: 'net_margin', label: 'Net Margin', pct: true },
    ],
  },
  {
    label: 'Liquidity', color: 'var(--primary)',
    metrics: [
      { key: 'current_ratio', label: 'Current Ratio', pct: false },
      { key: 'quick_ratio', label: 'Quick Ratio', pct: false },
      { key: 'cash_ratio', label: 'Cash Ratio', pct: false },
    ],
  },
  {
    label: 'Leverage', color: 'var(--warning)',
    metrics: [
      { key: 'debt_to_equity', label: 'Debt / Equity', pct: false },
      { key: 'debt_to_assets', label: 'Debt / Assets', pct: false },
    ],
  },
  {
    label: 'Cash Flow', color: 'var(--info)',
    metrics: [
      { key: 'ocf_to_debt', label: 'OCF / Debt', pct: false },
      { key: 'ocf_to_assets', label: 'OCF / Assets', pct: false },
      { key: 'cash_flow_margin', label: 'CF Margin', pct: true },
    ],
  },
]

const SCORING_PRESETS = [
  { key: 'all',          label: '5-Model Ensemble', desc: 'ElasticNet + RF + XGBoost + SARIMAX + TFT', selected_models: ['elasticnet', 'random_forest', 'xgboost', 'sarimax', 'tft'] },
  { key: 'stable',       label: 'Stability Focus',  desc: 'ElasticNet + RF + SARIMAX', selected_models: ['elasticnet', 'random_forest', 'sarimax'] },
  { key: 'growth',       label: 'Growth Focus',     desc: 'RF + XGBoost + TFT', selected_models: ['random_forest', 'xgboost', 'tft'] },
  { key: 'interpretable',label: 'Interpretable',    desc: 'ElasticNet + RF', selected_models: ['elasticnet', 'random_forest'] },
]

const TABS = [
  { value: 'overview', label: 'Overview', icon: BarChart3 },
  { value: 'financials', label: 'Financials', icon: DollarSign },
  { value: 'metrics', label: 'Metrics', icon: Layers },
  { value: 'transitions', label: 'Transitions', icon: RefreshCw },
  { value: 'sector', label: 'Sector Z-Score', icon: ArrowUpRight },
  { value: 'score', label: 'Run Analysis', icon: Play },
]

// Q4-only periods for available datasets
const ALL_QUARTERS = [
  '2025Q4',
  '2024Q4',
  '2023Q4',
  '2022Q4',
  '2021Q4',
  '2020Q4',
]

function MetricCardGroup({ group, metric }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 10 }}>
        <div style={{ width: 3, height: 14, borderRadius: 3, background: group.color }} />
        <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.9, color: 'var(--text-3)' }}>{group.label}</span>
        <span style={{ fontSize: 10, color: 'var(--text-4)', marginLeft: 4 }}>({group.metrics.length} metrics)</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 8 }}>
        {group.metrics.map(m => {
          const val = metric?.[m.key]
          const isGood = m.pct ? val > 0 : val > 1
          return (
            <div key={m.key} style={{ background: 'var(--surface-3)', borderRadius: 10, padding: '12px 14px', position: 'relative', overflow: 'hidden', border: '1px solid transparent', transition: 'border-color 0.15s' }}
              onMouseEnter={e => e.currentTarget.style.borderColor = group.color}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'transparent'}
            >
              <div style={{ position: 'absolute', top: 0, left: 0, width: 3, height: '100%', background: group.color, borderRadius: '3px 0 0 3px', opacity: 0.5 }} />
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 5, textTransform: 'uppercase', letterSpacing: 0.5 }}>{m.label}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-1)', fontVariantNumeric: 'tabular-nums' }}>
                  {fmt(val, m.pct)}
                </div>
                {val != null && (
                  isGood
                    ? <TrendingUp size={12} style={{ color: 'var(--success)' }} />
                    : <TrendingDown size={12} style={{ color: 'var(--danger-light)' }} />
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function CompanyPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [company, setCompany] = useState(null)
  const [financials, setFinancials] = useState([])
  const [metrics, setMetrics] = useState([])
  const [transitions, setTransitions] = useState([])
  const [sectorScores, setSectorScores] = useState([])
  const [loading, setLoading] = useState(true)
  const [scoring, setScoring] = useState(false)
  const [scoreProgress, setScoreProgress] = useState(0)
  const [scoreStep, setScoreStep] = useState(0)
  const [error, setError] = useState('')
  const [selectedPeriod, setSelectedPeriod] = useState('')
  const [selectedPreset, setSelectedPreset] = useState('all')
  const [selectedYear, setSelectedYear] = useState(2025)
  const [activeTab, setActiveTab] = useState('overview')

  const SCORE_STEPS = [
    'Fetching financial data...',
    'Computing ratios...',
    'Normalizing metrics...',
    'Running scoring model...',
    'Calculating success probability...',
    'Building sector comparisons...',
    'Generating AI insights...',
    'Finalising report...',
  ]

  useEffect(() => {
    setLoading(true)
    Promise.all([
      api.get(`/companies/${id}`),
      api.get(`/companies/${id}/financials`),
      api.get(`/companies/${id}/metrics`),
      api.get(`/companies/${id}/transitions`).catch(() => ({ data: [] })),
      api.get(`/companies/${id}/sector-scores`).catch(() => ({ data: [] })),
    ]).then(([c, f, m, t, sc]) => {
  const filteredFinancials = (f.data || [])
    .filter((item) => ALL_QUARTERS.includes(item?.period))

  const filteredMetrics = (m.data || [])
    .filter((item) => ALL_QUARTERS.includes(item?.period))
    .sort((a, b) => String(b.period).localeCompare(String(a.period)))

  setCompany(c.data)
  setFinancials(filteredFinancials)
  setMetrics(filteredMetrics)
  setTransitions(t.data)
  setSectorScores(sc.data)

  if (filteredMetrics.length > 0) setSelectedPeriod(filteredMetrics[0].period)
  else setSelectedPeriod(ALL_QUARTERS[0])
}).catch(() => navigate('/companies'))
      .finally(() => setLoading(false))
  }, [id])

  const runScore = async () => {
    setError('')
    setScoring(true)
    setScoreProgress(0)
    setScoreStep(0)

    // Fire real API call immediately
    const preset = SCORING_PRESETS.find(p => p.key === selectedPreset)
    const apiPromise = api.post(`/companies/${id}/score`, {
      period: selectedPeriod || null,
      year: selectedYear,
       ensemble: true,
       selected_models: preset?.selected_models || ['elasticnet', 'random_forest', 'xgboost', 'sarimax', 'tft'],
    }).then(r => r.data).catch(e => ({ error: e }))

    // Animate progress over ~12 seconds regardless of API speed
    const totalMs = 12000
    const intervalMs = 120
    const ticks = totalMs / intervalMs
    let tick = 0
    const timer = setInterval(() => {
      tick++
      const pct = Math.min((tick / ticks) * 100, 97)
      setScoreProgress(pct)
      setScoreStep(Math.min(Math.floor((pct / 100) * SCORE_STEPS.length), SCORE_STEPS.length - 1))
      if (tick >= ticks) clearInterval(timer)
    }, intervalMs)

    // Wait for both min animation time AND api to finish
    const minWait = new Promise(r => setTimeout(r, totalMs))
    const [result] = await Promise.all([apiPromise, minWait])
    clearInterval(timer)
    setScoreProgress(100)

    if (result?.error) {
      const detail = result.error.response?.data?.detail
      if (typeof detail === 'string') setError(detail)
      else if (detail && typeof detail === 'object') {
        const msg = typeof detail.message === 'string' ? detail.message : 'Scoring failed. Please try again.'
        const warnings = Array.isArray(detail.warnings) ? detail.warnings : []
        setError(warnings.length ? `${msg} (${warnings.join(' | ')})` : msg)
      } else {
        setError('Scoring failed. Please try again.')
      }
      setScoring(false)
      return
    }
    // Short pause to show 100%
    await new Promise(r => setTimeout(r, 400))
    navigate(`/score-runs/${result.id}`)
  }

  if (loading) {
    return (
      <div style={{ maxWidth: 1140, margin: '0 auto', padding: '0.5rem 0.5rem 2rem' }}>
        <Skeleton width={140} height={14} style={{ marginBottom: 24 }} />
        <div style={{ display: 'flex', gap: 14, marginBottom: 24 }}>
          <Skeleton width={64} height={64} radius={16} />
          <div style={{ flex: 1 }}>
            <Skeleton width="30%" height={24} style={{ marginBottom: 8 }} />
            <Skeleton width="50%" height={14} />
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
          {[...Array(4)].map((_, i) => <Skeleton key={i} height={90} radius={14} />)}
        </div>
      </div>
    )
  }

  if (!company) return null

  // ── Scoring Overlay ──────────────────────────────────────────────────────
  if (scoring) {
    const band = scoreProgress >= 75 ? '#2BD97F' : scoreProgress >= 50 ? '#00F5D4' : scoreProgress >= 25 ? '#FFC857' : '#9ca3af'
    return (
      <div style={{
        position: 'fixed', inset: 0, zIndex: 999,
        background: 'rgba(0,0,0,0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexDirection: 'column',
      }}>
        <div style={{
          background: 'var(--surface-2)',
          border: '1px solid var(--border-bright)',
          borderRadius: 20,
          padding: '48px 52px',
          maxWidth: 480,
          width: '90%',
          textAlign: 'center',
          boxShadow: '0 32px 80px rgba(0,0,0,0.6)',
        }}>
          {/* Animated ring */}
          <div style={{ position: 'relative', width: 96, height: 96, margin: '0 auto 24px' }}>
            <svg width={96} height={96} style={{ transform: 'rotate(-90deg)' }}>
              <circle cx={48} cy={48} r={40} fill="none" stroke="var(--surface-3)" strokeWidth={6} />
              <circle
                cx={48} cy={48} r={40} fill="none"
                stroke="#00F5D4" strokeWidth={6}
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - scoreProgress / 100)}`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.15s ease' }}
              />
            </svg>
            <div style={{
              position: 'absolute', inset: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 15, fontWeight: 800, color: 'var(--primary)',
              fontVariantNumeric: 'tabular-nums',
            }}>
              {Math.round(scoreProgress)}%
            </div>
          </div>

          <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-1)', marginBottom: 6 }}>
            Analysing {company.ticker}
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 28 }}>
            {company.company_name}
          </div>

          {/* Progress bar */}
          <div style={{ height: 6, background: 'var(--surface-3)', borderRadius: 4, overflow: 'hidden', marginBottom: 20 }}>
            <div style={{
              height: '100%',
              width: `${scoreProgress}%`,
              background: 'linear-gradient(90deg, #00B894, #00F5D4, #80FEE8)',
              borderRadius: 4,
              transition: 'width 0.15s ease',
            }} />
          </div>

          {/* Step label */}
          <div style={{
            fontSize: 13, color: 'var(--primary)', fontWeight: 600,
            minHeight: 20, transition: 'opacity 0.3s',
          }}>
            {SCORE_STEPS[scoreStep]}
          </div>

          {/* Steps checklist */}
          <div style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 6, textAlign: 'left' }}>
            {SCORE_STEPS.map((step, i) => {
              const done = i < scoreStep
              const active = i === scoreStep
              return (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  opacity: done || active ? 1 : 0.3,
                  transition: 'opacity 0.3s',
                }}>
                  <span style={{
                    width: 18, height: 18, borderRadius: '50%', flexShrink: 0,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 10, fontWeight: 700,
                    background: done ? '#2BD97F' : active ? '#00F5D4' : 'var(--surface-3)',
                    color: done || active ? '#fff' : 'var(--text-3)',
                    border: active ? '2px solid #33F7DC' : 'none',
                    boxShadow: active ? '0 0 10px rgba(0,245,212,0.5)' : 'none',
                    transition: 'all 0.3s',
                  }}>
                    {done ? '✓' : i + 1}
                  </span>
                  <span style={{ fontSize: 12.5, color: active ? 'var(--text-1)' : done ? 'var(--success)' : 'var(--text-3)', fontWeight: active ? 600 : 400 }}>
                    {step}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    )
  }
  const sortedFinancials = [...financials]
    .filter(f => ALL_QUARTERS.includes(f?.period))
    .sort((a, b) => String(b.period).localeCompare(String(a.period)))

  const financialByPeriod = Object.fromEntries(sortedFinancials.map(f => [f.period, f]))
  const periods = sortedFinancials.map(f => f.period)
  const latestMetric = metrics.find(m => m.period === selectedPeriod) || metrics[0]
  const latestTransPeriod = transitions.length ? transitions[0].to_period : null
  const latestTrans = latestTransPeriod ? transitions.filter(t => t.to_period === latestTransPeriod) : []
  const sectorForPeriod = sectorScores.filter(ss => ss.period === selectedPeriod)

  const thStyle = {
    padding: '10px 14px', textAlign: 'left',
    fontSize: 11, fontWeight: 700, color: 'var(--text-3)',
    textTransform: 'uppercase', letterSpacing: 0.8,
    background: 'var(--surface-3)',
  }
  const tdStyle = {
    padding: '11px 14px', fontSize: 13, color: 'var(--text-2)',
    borderTop: '1px solid var(--border)',
    fontVariantNumeric: 'tabular-nums',
  }

  return (
    <div style={{ maxWidth: 1100 }}>
      {/* Back */}
      <button
        onClick={() => navigate('/companies')}
        style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', fontSize: 13, marginBottom: 20, padding: 0 }}
        onMouseEnter={e => e.currentTarget.style.color = 'var(--text-1)'}
        onMouseLeave={e => e.currentTarget.style.color = 'var(--text-3)'}
      >
        <ArrowLeft size={15} /> Back to Companies
      </button>

      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, var(--surface-2), rgba(244,176,74,0.1))',
        border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-xl)', padding: '28px 32px', marginBottom: 24,
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Decorative gradient orb */}
        <div style={{ position: 'absolute', top: -60, right: -60, width: 180, height: 180, borderRadius: '50%', background: 'radial-gradient(circle, rgba(85,194,195,0.12), transparent)', pointerEvents: 'none' }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, position: 'relative' }}>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{
              width: 64, height: 64, borderRadius: 18,
              background: 'linear-gradient(135deg, rgba(244,176,74,0.2), rgba(85,194,195,0.12))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--primary-hover)', fontWeight: 800, fontSize: 20, flexShrink: 0,
              border: '1px solid rgba(244,176,74,0.25)',
            }}>
              {company.ticker?.substring(0, 2)}
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <h1 style={{ fontSize: '1.8rem', fontWeight: 900, color: 'var(--primary-hover)', letterSpacing: '-0.5px', margin: 0 }}>
                  {company.ticker}
                </h1>
                {company.sector && (
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 6, padding: '3px 10px' }}>
                    {company.sector}
                  </span>
                )}
                {company.sector_code && (
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary)', background: 'var(--primary-subtle)', borderRadius: 6, padding: '3px 10px' }}>
                    {company.sector_code}
                  </span>
                )}
              </div>
              <p style={{ color: 'var(--text-2)', fontSize: 14, marginTop: 4, marginBottom: 0, fontWeight: 500 }}>{company.company_name}</p>
              {company.description && (
                <p style={{ color: 'var(--text-3)', fontSize: 12.5, marginTop: 6, marginBottom: 0, maxWidth: 500, lineHeight: 1.4 }}>{company.description}</p>
              )}
              {metrics.length > 0 && (
                <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 4, padding: '2px 8px' }}>
                    {metrics.length} period{metrics.length !== 1 ? 's' : ''} of data
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 4, padding: '2px 8px' }}>
                    Latest: {metrics[0]?.period}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <GhostButton icon={GitCompare} onClick={() => navigate('/compare')}>Compare</GhostButton>
            <PrimaryButton icon={Play} onClick={() => setActiveTab('score')}>Run Analysis</PrimaryButton>
          </div>
        </div>
      </div>

      {/* Key metrics strip */}
      {metrics.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
          {[
              { label: 'ROA', value: fmt(latestMetric?.roa, true), color: 'var(--success)', icon: TrendingUp, raw: latestMetric?.roa },
              { label: 'ROE', value: fmt(latestMetric?.roe, true), color: 'var(--primary)', icon: Activity, raw: latestMetric?.roe },
              { label: 'Net Margin', value: fmt(latestMetric?.net_margin, true), color: 'var(--warning)', icon: Zap, raw: latestMetric?.net_margin },
              { label: 'Current Ratio', value: fmt(latestMetric?.current_ratio), color: 'var(--secondary)', icon: Shield, raw: latestMetric?.current_ratio },
            ].map(m => {
            const Icon = m.icon
            return (
              <div key={m.label} style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: '16px 18px', position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: -8, right: -8, width: 48, height: 48, borderRadius: '50%', background: m.color, opacity: 0.06, pointerEvents: 'none' }} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <Icon size={13} style={{ color: m.color }} />
                  <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.7, color: 'var(--text-3)' }}>{m.label}</div>
                </div>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: m.color, fontVariantNumeric: 'tabular-nums' }}>{m.value}</div>
                {m.raw != null && (
                  <div style={{ height: 3, borderRadius: 2, background: 'var(--surface-3)', marginTop: 8 }}>
                    <div style={{ height: '100%', borderRadius: 2, background: m.color, width: `${Math.min(Math.abs(m.raw) * (m.label === 'Current Ratio' ? 33 : 200), 100)}%`, transition: 'width 0.6s ease' }} />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Tabs */}
      <TabBar tabs={TABS} active={activeTab} onChange={setActiveTab} />

      {/* Overview tab */}
      {activeTab === 'overview' && (
        <div>
          {metrics.length === 0 ? (
            <EmptyState icon={BarChart3} title="No metrics data available" sub="Upload financial data to compute ratios." />
          ) : (
            <>
              {/* Health Summary Card */}
              {(() => {
                const m = latestMetric
                if (!m) return null
                const healthChecks = [
                  { label: 'Profitability', pass: m.roa > 0 && m.roe > 0, detail: m.roa > 0 ? 'Positive returns' : 'Negative returns' },
                  { label: 'Liquidity', pass: m.current_ratio >= 1, detail: m.current_ratio >= 1 ? 'Adequate coverage' : 'Below threshold' },
                  { label: 'Leverage', pass: m.debt_to_equity != null && m.debt_to_equity < 2, detail: m.debt_to_equity < 2 ? 'Manageable debt' : 'High leverage' },
                  { label: 'Cash Flow', pass: m.cash_flow_margin > 0, detail: m.cash_flow_margin > 0 ? 'Positive cash generation' : 'Negative cash flow' },
                ]
                const score = healthChecks.filter(c => c.pass).length
                const scoreColor = score >= 3 ? 'var(--success)' : score >= 2 ? 'var(--warning)' : 'var(--danger-light)'
                return (
                  <Card style={{ padding: '20px 24px', marginBottom: 20, background: 'linear-gradient(135deg, var(--surface-2), rgba(0,245,212,0.03))' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-1)', marginBottom: 2 }}>Financial Health Overview</div>
                        <div style={{ fontSize: 12, color: 'var(--text-3)' }}>Period: {latestMetric?.period}</div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ fontSize: '1.6rem', fontWeight: 900, color: scoreColor, fontVariantNumeric: 'tabular-nums' }}>{score}/4</div>
                        <div style={{ fontSize: 11, color: scoreColor, fontWeight: 600 }}>checks passed</div>
                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10 }}>
                      {healthChecks.map(c => (
                        <div key={c.label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 12px', background: 'var(--surface-3)', borderRadius: 10 }}>
                          <div style={{ width: 20, height: 20, borderRadius: '50%', background: c.pass ? 'rgba(43,217,127,0.15)' : 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, flexShrink: 0 }}>
                            {c.pass ? '✓' : '✗'}
                          </div>
                          <div>
                            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-1)' }}>{c.label}</div>
                            <div style={{ fontSize: 10, color: c.pass ? 'var(--success)' : 'var(--danger-light)' }}>{c.detail}</div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </Card>
                )
              })()}

              {METRIC_GROUPS.map(g => <MetricCardGroup key={g.label} group={g} metric={latestMetric} />)}
            </>
          )}
        </div>
      )}

      {/* Financials tab */}
      {activeTab === 'financials' && (
        financials.length === 0 ? (
          <EmptyState icon={DollarSign} title="No financial data" sub="No financial records found for this company." />
        ) : (
          <Card>
            <div style={{ padding: '14px 18px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-2)' }}>
                Financial Statements <span style={{ fontSize: 11, color: 'var(--text-3)', fontWeight: 400 }}>— {periods.length} period{periods.length !== 1 ? 's' : ''}</span>
              </div>
              {financials.length >= 2 && (
                <span style={{ fontSize: 11, color: 'var(--primary)', fontWeight: 600 }}>
                  Trend indicators vs. previous period
                </span>
              )}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 600 }}>
                <thead>
                  <tr>
                    <th style={{ ...thStyle, textAlign: 'left' }}>Item</th>
                    {periods.map(p => <th key={p} style={{ ...thStyle, textAlign: 'right' }}>{p}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {FINANCIAL_ROWS.map(row => (
                    <tr key={row.key}>
                      <td style={{ ...tdStyle, color: 'var(--text-3)', fontWeight: 500 }}>{row.label}</td>
                      {periods.map((p, pIdx) => {
                        const val = financialByPeriod[p]?.[row.key]
                        const prevPeriod = periods[pIdx + 1]
                        const prevVal = prevPeriod ? financialByPeriod[prevPeriod]?.[row.key] : null
                        const showTrend = pIdx === 0 && val != null && prevVal != null
                        const trendUp = showTrend && val > prevVal
                        const trendDown = showTrend && val < prevVal
                        return (
                          <td key={p} style={{ ...tdStyle, textAlign: 'right' }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 4 }}>
                              <span>{fmt(val)}</span>
                              {showTrend && (trendUp || trendDown) && (
                                trendUp
                                  ? <TrendingUp size={11} style={{ color: 'var(--success)', flexShrink: 0 }} />
                                  : <TrendingDown size={11} style={{ color: 'var(--danger-light)', flexShrink: 0 }} />
                              )}
                            </div>
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )
      )}

      {/* Metrics tab */}
      {activeTab === 'metrics' && (
        metrics.length === 0 ? (
          <EmptyState icon={Layers} title="No metrics data" sub="Metrics are computed from financial data." />
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 20 }}>
              <span style={{ fontSize: 13, color: 'var(--text-3)' }}>Period:</span>
              <select
                value={selectedPeriod}
                onChange={e => setSelectedPeriod(e.target.value)}
                style={{
                  background: 'var(--surface-2)', border: '1px solid var(--border-strong)',
                  borderRadius: 'var(--radius-md)', color: 'var(--text-1)', padding: '7px 12px', fontSize: 13, outline: 'none',
                }}
              >
                {ALL_QUARTERS.map(q => <option key={q} value={q}>{q}</option>)}
              </select>
            </div>
            {METRIC_GROUPS.map(g => <MetricCardGroup key={g.label} group={g} metric={latestMetric} />)}
          </>
        )
      )}

      {/* Transitions tab */}
      {activeTab === 'transitions' && (
        latestTrans.length === 0 ? (
          <EmptyState icon={RefreshCw} title="No transition data" sub="Transitions require at least 2 financial periods." />
        ) : (
          <Card>
            <div style={{ padding: '14px 16px', borderBottom: '1px solid var(--border)', fontSize: 13, color: 'var(--text-3)' }}>
              Period: <strong style={{ color: 'var(--text-2)' }}>{latestTrans[0]?.from_period}</strong> → <strong style={{ color: 'var(--text-2)' }}>{latestTransPeriod}</strong>
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={thStyle}>Metric</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Previous</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Current</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Change</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>% Change</th>
                  </tr>
                </thead>
                <tbody>
                  {latestTrans.map(t => (
                    <tr key={t.metric_name}>
                      <td style={{ ...tdStyle, fontWeight: 500 }}>{t.metric_name}</td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>{t.old_value != null ? t.old_value.toFixed(4) : '—'}</td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>{t.new_value != null ? t.new_value.toFixed(4) : '—'}</td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <ChangeChip value={t.abs_change} />
                      </td>
                      <td style={{ ...tdStyle, textAlign: 'right' }}>
                        <ChangeChip pct={t.pct_change} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        )
      )}

      {/* Sector Z-Score tab */}
      {activeTab === 'sector' && (
        sectorForPeriod.length === 0 ? (
          <EmptyState icon={ArrowUpRight} title="No sector data" sub="Sector benchmarks require at least 2 companies in the same sector." />
        ) : (
          <Card>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={thStyle}>Metric</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Raw Value</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Z-Score</th>
                    <th style={{ ...thStyle, textAlign: 'right' }}>Sector Percentile</th>
                  </tr>
                </thead>
                <tbody>
                  {sectorForPeriod.map(ss => {
                    const pct = ss.percentile_rank
                    const chipColor = pct >= 60 ? 'success' : pct <= 40 ? 'danger' : 'default'
                    return (
                      <tr key={ss.feature_name}>
                        <td style={{ ...tdStyle, fontWeight: 500 }}>{ss.feature_name}</td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>{ss.raw_value != null ? ss.raw_value.toFixed(4) : '—'}</td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>{ss.z_score != null ? ss.z_score.toFixed(3) : '—'}</td>
                        <td style={{ ...tdStyle, textAlign: 'right' }}>
                          {pct != null ? <Chip color={chipColor}>{pct.toFixed(1)}th pct.</Chip> : '—'}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )
      )}

      {/* Run Analysis tab */}
      {activeTab === 'score' && (
        <Card style={{ padding: 28, maxWidth: 480 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-1)', marginBottom: 4 }}>Run Scoring Analysis</div>
          <p style={{ color: 'var(--text-3)', fontSize: 13.5, marginBottom: 22, lineHeight: 1.5 }}>
            Select a period and model to compute a financial health score for {company.ticker}.
          </p>

          {metrics.length === 0 ? (
            <div style={{ color: 'var(--text-3)', fontSize: 13 }}>No financial data available to score.</div>
          ) : (
            <>
              <div style={{ marginBottom: 20 }}>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 6 }}>Period</label>
                  <select
                    value={selectedPeriod}
                    onChange={e => setSelectedPeriod(e.target.value)}
                    style={{ width: '100%', background: 'var(--surface-3)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', color: 'var(--text-1)', padding: '9px 12px', fontSize: 13.5, outline: 'none' }}
                  >
                    {ALL_QUARTERS.map(q => (
                        <option key={q} value={q}>{q}</option>
                      ))}
                  </select>
                </div>
                <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-3)', display: 'block', marginBottom: 8 }}>Scoring Preset</label>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 8 }}>
                  {SCORING_PRESETS.map(preset => {
                    const active = selectedPreset === preset.key
                    return (
                      <button
                        key={preset.key}
                        onClick={() => setSelectedPreset(preset.key)}
                        style={{
                          background: active ? 'var(--primary-subtle)' : 'var(--surface-3)',
                          border: `1.5px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                          borderRadius: 10, padding: '10px 12px', cursor: 'pointer',
                          textAlign: 'left', transition: 'all 0.14s',
                        }}
                      >
                        <div style={{ fontSize: 13, fontWeight: 700, color: active ? 'var(--primary-hover)' : 'var(--text-1)', marginBottom: 3 }}>{preset.label}</div>
                        <div style={{ fontSize: 10.5, color: 'var(--text-3)', lineHeight: 1.3 }}>{preset.desc}</div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {error && (
                <div style={{ background: 'var(--danger-subtle)', border: '1px solid var(--danger-muted)', borderRadius: 'var(--radius-md)', padding: '10px 14px', color: 'var(--danger-light)', fontSize: 13, marginBottom: 16 }}>
                  {error}
                </div>
              )}

              <PrimaryButton
                icon={Play}
                onClick={runScore}
                disabled={scoring}
                style={{ width: '100%', justifyContent: 'center', padding: '12px 18px', fontSize: 15 }}
              >
                {scoring ? 'Running analysis...' : 'Run Analysis'}
              </PrimaryButton>
            </>
          )}
        </Card>
      )}
    </div>
  )
}
