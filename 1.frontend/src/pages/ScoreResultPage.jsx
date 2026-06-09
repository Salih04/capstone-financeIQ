import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Download, RotateCcw, GitCompare, TrendingUp, TrendingDown, Lightbulb, FileText, Sparkles, BrainCircuit } from 'lucide-react'
import api from '../api/client'
import { Card, GhostButton, ScoreBadge, getBand, Skeleton, Chip, SectionHeader } from '../components/ui'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const fmt = (v, isRate = false) => {
  if (v == null) return '—'
  if (isRate) return `${(v * 100).toFixed(2)}%`
  return typeof v === 'number' ? v.toFixed(2) : v
}

const METRIC_LABELS = {
  roa: 'ROA',
  roe: 'ROE',
  operating_margin: 'Operating Margin',
  net_margin: 'Net Margin',
  current_ratio: 'Current Ratio',
  quick_ratio: 'Quick Ratio',
  cash_ratio: 'Cash Ratio',
  debt_to_equity: 'Debt / Equity',
  debt_to_assets: 'Debt / Assets',
  ocf_to_debt: 'OCF / Debt',
  ocf_to_assets: 'OCF / Assets',
  cash_flow_margin: 'Cash Flow Margin',
}

const TOKEN_LABELS = {
  roa: 'ROA',
  roe: 'ROE',
  ocf: 'OCF',
  ebit: 'EBIT',
  ytd: 'YTD',
}

const formatMetricLabel = (value) => {
  if (!value) return '—'
  const raw = String(value)
  const key = raw.toLowerCase()
  if (METRIC_LABELS[key]) return METRIC_LABELS[key]
  const tokens = raw.replace(/_/g, ' ').split(' ')
  return tokens.map((t) => {
    const k = t.toLowerCase()
    if (TOKEN_LABELS[k]) return TOKEN_LABELS[k]
    return t.charAt(0).toUpperCase() + t.slice(1)
  }).join(' ')
}

function generateAIInsights(run) {
  if (!run?.details?.length) return []
  const insights = []
  const byMetric = {}
  run.details.forEach(d => { byMetric[d.metric_name] = d })

  const score = run.total_score || 0
  const prob = run.success_probability || 0

  // Overall assessment
  if (score >= 75) {
    insights.push({ type: 'positive', text: `Strong overall performance (${score.toFixed(1)}/100) — company demonstrates solid financial fundamentals across multiple dimensions.` })
  } else if (score >= 50) {
    insights.push({ type: 'neutral', text: `Moderate performance (${score.toFixed(1)}/100) — mixed signals with some metrics performing well while others require attention.` })
  } else {
    insights.push({ type: 'warning', text: `Below-average performance (${score.toFixed(1)}/100) — significant financial challenges identified that may warrant closer monitoring.` })
  }

  // Success probability
  if (prob >= 0.7) {
    insights.push({ type: 'positive', text: `High success probability (${(prob * 100).toFixed(1)}%) suggests the market model rates this company favorably for near-term success.` })
  } else if (prob < 0.4) {
    insights.push({ type: 'warning', text: `Low success probability (${(prob * 100).toFixed(1)}%) indicates elevated risk — consider monitoring cash flow and debt metrics.` })
  }

  // Profitability
  const roa = byMetric['roa'] || byMetric['ROA']
  const roe = byMetric['roe'] || byMetric['ROE']
  const opMargin = byMetric['operating_margin']
  if (roa?.metric_value != null && roa.metric_value > 0.05) {
    insights.push({ type: 'positive', text: `Return on Assets of ${(roa.metric_value * 100).toFixed(1)}% reflects efficient use of company resources to generate profit.` })
  } else if (roa?.metric_value != null && roa.metric_value < 0) {
    insights.push({ type: 'warning', text: `Negative ROA (${(roa.metric_value * 100).toFixed(1)}%) signals the company is currently not generating profit from its asset base.` })
  }

  // Liquidity
  const currentRatio = byMetric['current_ratio']
  const quickRatio = byMetric['quick_ratio']
  if (currentRatio?.metric_value != null) {
    if (currentRatio.metric_value >= 2.0) {
      insights.push({ type: 'positive', text: `Excellent liquidity — current ratio of ${currentRatio.metric_value.toFixed(2)} provides a strong buffer for short-term obligations.` })
    } else if (currentRatio.metric_value < 1.0) {
      insights.push({ type: 'warning', text: `Liquidity risk — current ratio of ${currentRatio.metric_value.toFixed(2)} is below 1.0, meaning current liabilities exceed current assets.` })
    }
  }

  // Leverage
  const dte = byMetric['debt_to_equity']
  const dta = byMetric['debt_to_assets']
  if (dte?.metric_value != null && dte.metric_value > 2.0) {
    insights.push({ type: 'warning', text: `Elevated leverage — debt-to-equity ratio of ${dte.metric_value.toFixed(2)} indicates significant reliance on debt financing.` })
  } else if (dte?.metric_value != null && dte.metric_value < 0.5) {
    insights.push({ type: 'positive', text: `Conservative capital structure with a debt-to-equity ratio of ${dte.metric_value.toFixed(2)}, indicating low financial leverage risk.` })
  }

  // Cash flow
  const ocfDebt = byMetric['ocf_to_debt']
  const cfMargin = byMetric['cash_flow_margin']
  if (ocfDebt?.metric_value != null && ocfDebt.metric_value > 0.3) {
    insights.push({ type: 'positive', text: `Strong operating cash flow relative to debt (${(ocfDebt.metric_value * 100).toFixed(1)}%) suggests solid debt coverage capacity.` })
  } else if (ocfDebt?.metric_value != null && ocfDebt.metric_value < 0.05) {
    insights.push({ type: 'warning', text: `Weak operating cash flow vs. debt ratio (${(ocfDebt.metric_value * 100).toFixed(1)}%) may limit the company's ability to service its obligations.` })
  }

  // Top driver insight
  const sorted = [...run.details].sort((a, b) => b.contribution - a.contribution)
  if (sorted.length > 0 && sorted[0].contribution > 5) {
    insights.push({ type: 'neutral', text: `Key score driver: "${sorted[0].metric_name}" contributed +${sorted[0].contribution.toFixed(1)} pts — the single largest positive factor in this assessment.` })
  }
  if (sorted.length > 0 && sorted[sorted.length - 1].contribution < -3) {
    const worst = sorted[sorted.length - 1]
    insights.push({ type: 'warning', text: `Biggest drag: "${worst.metric_name}" brought the score down by ${Math.abs(worst.contribution).toFixed(1)} pts — addressing this could meaningfully improve the overall rating.` })
  }

  return insights.slice(0, 5)
}

const CATEGORY_COLORS = {
  profitability: 'var(--success)',
  liquidity: 'var(--primary)',
  leverage: 'var(--warning)',
  cash_flow: 'var(--info)',
}

const CATEGORY_LABELS = {
  profitability: 'Profitability',
  liquidity: 'Liquidity',
  leverage: 'Leverage',
  cash_flow: 'Cash Flow',
}

function AdaptiveWeightsCard({ adaptiveInfo }) {
  if (!adaptiveInfo) return null
  const { sufficient_data, message, category_adjustments, periods_analyzed, companies_analyzed, sector_adjustment } = adaptiveInfo
  return (
    <Card style={{ padding: '1.25rem', marginBottom: 20, borderColor: 'rgba(139,92,246,0.3)', background: 'rgba(139,92,246,0.03)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
        <BrainCircuit size={15} style={{ color: '#8B5CF6' }} />
        <span style={{ fontSize: 12, fontWeight: 700, color: '#8B5CF6', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Adaptive Weight Analysis
        </span>
        {sufficient_data && (
          <span style={{ fontSize: 11, background: 'rgba(139,92,246,0.12)', color: '#8B5CF6', borderRadius: 20, padding: '2px 8px' }}>
            {periods_analyzed?.length} periods · {companies_analyzed} companies
          </span>
        )}
      </div>
      {!sufficient_data ? (
        <p style={{ fontSize: 13, color: 'var(--text-3)', margin: 0 }}>{message || 'Insufficient historical data for adaptive weight adjustment.'}</p>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 12 }}>
            {Object.entries(category_adjustments || {}).map(([cat, info]) => {
              const corr = info.correlation
              const mult = info.multiplier
              const color = CATEGORY_COLORS[cat] || 'var(--text-2)'
              const change = mult > 1.05 ? '+' : mult < 0.95 ? '−' : '='
              const changeColor = mult > 1.05 ? 'var(--success)' : mult < 0.95 ? 'var(--danger)' : 'var(--text-3)'
              return (
                <div key={cat} style={{ background: 'var(--surface-3)', borderRadius: 8, padding: '10px 12px', borderLeft: `3px solid ${color}` }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color }}>{CATEGORY_LABELS[cat] || cat}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: changeColor }}>
                      {change} {((Math.abs(mult - 1)) * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-3)', lineHeight: 1.4 }}>
                    Correlation: <strong style={{ color: 'var(--text-2)' }}>{corr >= 0 ? '+' : ''}{corr.toFixed(2)}</strong>
                    {' · '}{info.samples} samples
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text-3)', marginTop: 3, lineHeight: 1.35 }}>
                    {info.explanation}
                  </div>
                </div>
              )
            })}
          </div>
          {sector_adjustment && (
            <div style={{ background: 'rgba(139,92,246,0.08)', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: 'var(--text-2)' }}>
              <strong style={{ color: '#8B5CF6' }}>Sector Adjustment:</strong>{' '}
              {sector_adjustment.explanation}
            </div>
          )}
          <p style={{ fontSize: 11.5, color: 'var(--text-3)', margin: '10px 0 0', lineHeight: 1.5 }}>
            Historical data from {periods_analyzed?.join(', ')} was used to compute correlations between metric category strength and 1-year returns. Weights adjusted accordingly.
          </p>
        </>
      )}
    </Card>
  )
}

export default function ScoreResultPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [run, setRun] = useState(null)
  const [company, setCompany] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get(`/score-runs/${id}`)
      .then(({ data }) => {
        setRun(data)
        return api.get(`/companies/${data.company_id}`).catch(() => null)
      })
      .then(res => { if (res) setCompany(res.data) })
      .catch(() => navigate('/companies'))
      .finally(() => setLoading(false))
  }, [id])

  const downloadExport = (format) => {
    const token = localStorage.getItem('token')
    const url = `${BASE_URL}/reports/score-runs/${id}/export.${format}`
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const objUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = objUrl
        a.download = `score_run_${id}.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(objUrl)
      })
      .catch(console.error)
  }

  if (loading) {
    return (
      <div style={{ maxWidth: 860, margin: '0 auto', padding: '2rem 1.5rem' }}>
        <Skeleton style={{ height: 28, width: 200, marginBottom: 24 }} />
        <Skeleton style={{ height: 220, marginBottom: 20, borderRadius: 'var(--radius-xl)' }} />
        <Skeleton style={{ height: 120, marginBottom: 20, borderRadius: 'var(--radius-xl)' }} />
        <Skeleton style={{ height: 280, borderRadius: 'var(--radius-xl)' }} />
      </div>
    )
  }
  if (!run) return null

  const band = getBand(run.total_score)
  const drivers = run.details ? [...run.details].sort((a, b) => b.contribution - a.contribution) : []
  const topDrivers = drivers.slice(0, 3)
  const riskDrivers = drivers.slice(-3).reverse()
  const richExplanation = (() => {
    try { return run.rich_explanation_json ? JSON.parse(run.rich_explanation_json) : null } catch { return null }
  })()
  const adaptiveWeightsInfo = richExplanation?.adaptive_weights || null

  return (
    <div style={{ maxWidth: 860, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Back */}
      <button
        onClick={() => navigate(`/companies/${run.company_id}`)}
        style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none', color: 'var(--text-2)', cursor: 'pointer', fontSize: 13, marginBottom: 24, padding: 0 }}
      >
        <ArrowLeft size={15} /> Back to Company
      </button>

      {/* ── Hero Score Card ── */}
      <Card style={{ padding: '2rem', textAlign: 'center', marginBottom: 20, position: 'relative', overflow: 'hidden', background: 'linear-gradient(135deg, rgba(244,176,74,0.10), var(--surface-2))' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: band.color }} />
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
          Diagnostic Score Result
        </div>
        {/* Company identity */}
        {company && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--primary-hover)', letterSpacing: '-0.5px', lineHeight: 1.1 }}>
              {company.ticker}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-3)', marginTop: 2 }}>
              {company.company_name}
            </div>
            {company.sector && (
              <span style={{ display: 'inline-block', marginTop: 6, fontSize: 11, fontWeight: 600, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 6, padding: '2px 10px' }}>
                {company.sector}
              </span>
            )}
          </div>
        )}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 4 }}>
          {/* Score ring */}
          <svg width={90} height={90} style={{ transform: 'rotate(-90deg)' }}>
            <circle cx={45} cy={45} r={38} fill="none" stroke="var(--surface-3)" strokeWidth={7} />
            <circle
              cx={45} cy={45} r={38} fill="none"
              stroke={band.color} strokeWidth={7}
              strokeDasharray={`${2 * Math.PI * 38}`}
              strokeDashoffset={`${2 * Math.PI * 38 * (1 - (run.total_score || 0) / 100)}`}
              strokeLinecap="round"
              style={{ transition: 'stroke-dashoffset 1s ease' }}
            />
          </svg>
          <div>
            <div style={{ fontSize: '3.5rem', fontWeight: 800, lineHeight: 1, color: band.color, fontVariantNumeric: 'tabular-nums' }}>
              {run.total_score?.toFixed(1)}
            </div>
            <div style={{ fontSize: 14, color: 'var(--text-3)' }}>/100</div>
          </div>
        </div>
        <div style={{ marginBottom: 16 }}>
          <ScoreBadge score={run.total_score} style={{ fontSize: 13, padding: '5px 16px' }} />
        </div>
        <div style={{ color: 'var(--text-2)', fontSize: 13, marginBottom: 20 }}>
          <span style={{ background: 'var(--surface-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px' }}>
            Period: {run.period}
          </span>
          {' · '}
          <span>Scoring Summary</span>
          {run.label_used && run.label_used !== run.model_name && (
            <Chip label={run.label_used} style={{ marginLeft: 8, fontSize: 11 }} />
          )}
        </div>
        {/* Stats row */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '3rem', flexWrap: 'wrap' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: band.color, fontVariantNumeric: 'tabular-nums' }}>
              {run.success_probability != null ? `${(run.success_probability * 100).toFixed(1)}%` : '—'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 2 }}>Model Probability</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-1)', fontVariantNumeric: 'tabular-nums' }}>
              {run.details?.length || 0}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 2 }}>Metrics</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--text-1)' }}>
              {new Date(run.created_at).toLocaleDateString('en-US')}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginTop: 2 }}>Date</div>
          </div>
        </div>
      </Card>

      {/* ── Score Methodology Box ── */}
      <Card style={{ padding: '1.25rem', marginBottom: 20, borderColor: 'rgba(0,245,212,0.3)', background: 'rgba(0,245,212,0.03)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <FileText size={15} style={{ color: 'var(--primary)' }} />
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            How Is the Score Calculated?
          </span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14, marginBottom: 12 }}>
          {[
            { label: 'Profitability', metrics: 'ROA, ROE, Op. Margin, Net Margin', color: 'var(--success)', pct: '~33%' },
            { label: 'Liquidity', metrics: 'Current Ratio, Quick Ratio, Cash Ratio', color: 'var(--primary)', pct: '~25%' },
            { label: 'Leverage', metrics: 'Debt/Equity, Debt/Assets', color: 'var(--warning)', pct: '~20%' },
            { label: 'Cash Flow', metrics: 'OCF/Debt, OCF/Assets, CF Margin', color: 'var(--info)', pct: '~22%' },
          ].map(cat => (
            <div key={cat.label} style={{ background: 'var(--surface-3)', borderRadius: 8, padding: '10px 12px', borderLeft: `3px solid ${cat.color}` }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: cat.color, marginBottom: 4 }}>{cat.label}</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 4 }}>{cat.metrics}</div>
              <div style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 600 }}>Weight: {cat.pct}</div>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
          {[
            { range: '75–100', label: 'Strong',   color: 'var(--success)' },
            { range: '50–74', label: 'Healthy',  color: 'var(--primary)' },
            { range: '25–49', label: 'Risky',    color: 'var(--warning)' },
            { range: '0–24',  label: 'Critical', color: 'var(--danger)'  },
          ].map(b => (
            <div key={b.range} style={{ display: 'flex', alignItems: 'center', gap: 5, background: 'var(--surface-3)', borderRadius: 6, padding: '4px 10px' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: b.color }} />
              <span style={{ fontSize: 11, color: 'var(--text-2)', fontWeight: 600 }}>{b.range}</span>
              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{b.label}</span>
            </div>
          ))}
        </div>
        <p style={{ fontSize: 12, color: 'var(--text-3)', margin: 0, lineHeight: 1.6 }}>
          Each metric is normalized, weighted contributions are computed, and a final score between 0–100 is produced.
          <strong style={{ color: 'var(--text-2)' }}> Success probability</strong> is derived from a logistic regression model trained on these metrics.
          The score is not a standalone investment recommendation; it is a financial health indicator.
        </p>
      </Card>

      {/* ── Adaptive Weights Explanation ── */}
      {adaptiveWeightsInfo && <AdaptiveWeightsCard adaptiveInfo={adaptiveWeightsInfo} />}

      {/* ── Drivers row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
        <Card style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <TrendingUp size={15} style={{ color: 'var(--success)' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Strengths
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {topDrivers.length === 0
              ? <span style={{ fontSize: 13, color: 'var(--text-3)' }}>No data</span>
              : topDrivers.map(d => (
                <div key={d.metric_name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 13, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {formatMetricLabel(d.metric_name)}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--success)', fontVariantNumeric: 'tabular-nums' }}>
                    +{d.contribution?.toFixed(1)}
                  </span>
                </div>
              ))
            }
          </div>
        </Card>
        <Card style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
            <TrendingDown size={15} style={{ color: 'var(--danger)' }} />
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Risk Factors
            </span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {riskDrivers.length === 0
              ? <span style={{ fontSize: 13, color: 'var(--text-3)' }}>No data</span>
              : riskDrivers.map(d => (
                <div key={d.metric_name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 13, color: 'var(--text-2)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {formatMetricLabel(d.metric_name)}
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--danger)', fontVariantNumeric: 'tabular-nums' }}>
                    {d.contribution?.toFixed(1)}
                  </span>
                </div>
              ))
            }
          </div>
        </Card>
      </div>

      {/* ── Explanation ── */}
      {run.explanation_summary && (
        <Card style={{ padding: '1.25rem', marginBottom: 20, borderColor: 'var(--primary-muted)' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <Lightbulb size={16} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
                Analysis Summary
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.7, margin: 0 }}>
                {run.explanation_summary}
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* ── Analyst Notes ── */}
      {(() => {
        const aiInsights = generateAIInsights(run)
        if (!aiInsights.length) return null
        return (
          <Card style={{ padding: '1.25rem', marginBottom: 20, borderColor: 'rgba(0,245,212,0.3)', background: 'rgba(0,245,212,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <Sparkles size={16} style={{ color: 'var(--info)' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--info)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Analyst Notes
              </span>
              <span style={{ fontSize: 11, color: 'var(--text-3)', marginLeft: 4, background: 'var(--surface-2)', borderRadius: 20, padding: '2px 8px' }}>
                Deterministic explanation
              </span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {aiInsights.map((insight, i) => {
                const color = insight.type === 'positive' ? 'var(--success)' : insight.type === 'warning' ? 'var(--warning)' : 'var(--text-2)'
                const icon = insight.type === 'positive' ? '✓' : insight.type === 'warning' ? '⚠' : '•'
                return (
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 13, color, flexShrink: 0, marginTop: 1, fontWeight: 700 }}>{icon}</span>
                    <p style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.65, margin: 0 }}>{insight.text}</p>
                  </div>
                )
              })}
            </div>
          </Card>
        )
      })()}

      {/* ── Export ── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>        <span style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Export:</span>
        {['csv', 'json', 'pdf'].map(f => (
          <GhostButton key={f} onClick={() => downloadExport(f)} style={{ gap: 5, padding: '6px 14px', fontSize: 12 }}>
            <Download size={13} /> {f.toUpperCase()}
          </GhostButton>
        ))}
      </div>

      {/* ── Metric Breakdown Table ── */}
      <SectionHeader title="Metric Breakdown" icon={<FileText size={15} />} style={{ marginBottom: 12 }} />
      <Card style={{ padding: 0, overflow: 'hidden', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--surface-1)' }}>
              {['Metric', 'Value', 'Norm.', 'Weight', 'Contrib.', 'Bar'].map((h, i) => (
                <th key={h} style={{
                  padding: '10px 14px', fontSize: 11, color: 'var(--text-3)',
                  textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600,
                  textAlign: i === 0 ? 'left' : 'right', borderBottom: '1px solid var(--border)'
                }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {run.details?.map((d) => {
              const pct = d.weight ? Math.min(Math.abs((d.contribution / d.weight) * 100), 100) : 0
              const contribColor = d.contribution >= 0
                ? (pct >= 50 ? 'var(--success)' : pct >= 25 ? 'var(--warning)' : 'var(--text-2)')
                : 'var(--danger)'
              const isRate = d.metric_name?.includes('ROA') || d.metric_name?.includes('ROE')
              return (
                <tr
                  key={d.metric_name}
                  style={{ borderTop: '1px solid var(--border)' }}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={{ padding: '10px 14px', fontSize: 13, color: 'var(--text-1)', textAlign: 'left' }}>
                    {d.metric_name}
                    {d.comment && (
                      <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>💬 {d.comment}</div>
                    )}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: 13, color: 'var(--text-2)', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {fmt(d.metric_value, isRate)}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: 13, color: 'var(--text-3)', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {d.normalized_value != null ? d.normalized_value.toFixed(3) : '—'}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: 13, color: 'var(--text-2)', textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {d.weight?.toFixed ? d.weight.toFixed(2) : d.weight ?? '—'}
                  </td>
                  <td style={{ padding: '10px 14px', fontSize: 13, fontWeight: 600, color: contribColor, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>
                    {d.contribution != null ? (d.contribution >= 0 ? '+' : '') + d.contribution.toFixed(1) : '—'}
                  </td>
                  <td style={{ padding: '10px 14px', textAlign: 'right', minWidth: 100 }}>
                    <div style={{ height: 6, borderRadius: 3, background: 'var(--surface-1)', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, borderRadius: 3, background: contribColor, transition: 'width 0.8s ease' }} />
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </Card>

      {/* ── Bottom Actions ── */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        <GhostButton onClick={() => navigate(`/companies/${run.company_id}`)} style={{ gap: 6 }}>
          <RotateCcw size={14} /> Re-score
        </GhostButton>
        <GhostButton onClick={() => navigate('/compare')} style={{ gap: 6 }}>
          <GitCompare size={14} /> Compare
        </GhostButton>
        <GhostButton onClick={() => navigate('/companies')} style={{ gap: 6 }}>
          <ArrowLeft size={14} /> Back to Companies
        </GhostButton>
      </div>
    </div>
  )
}
