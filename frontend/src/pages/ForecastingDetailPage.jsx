import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, Cell } from 'recharts'
import { BrainCircuit, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState } from '../components/ui'

function HeatColor({ value }) {
  const v = Math.max(-1, Math.min(1, value / 100))
  const pos = v >= 0
  const alpha = Math.min(0.9, Math.abs(v))
  return <span style={{ color: pos ? '#22c55e' : '#ef4444', opacity: 0.35 + alpha }}>{value.toFixed(2)}</span>
}

export default function ForecastingDetailPage() {
  const [params] = useSearchParams()
  const stockCode = (params.get('stock') || '').toUpperCase()
  const sector = params.get('sector') || undefined
  const year = params.get('year') ? parseInt(params.get('year'), 10) : undefined

  const [trend, setTrend] = useState({ series: [] })
  const [heatmap, setHeatmap] = useState({ heatmap: [] })
  const [paramRanks, setParamRanks] = useState([])

  useEffect(() => {
    if (!stockCode) return
    api.get('/predict/trends', { params: { stock_code: stockCode, sector } }).then(({ data }) => setTrend(data)).catch(() => setTrend({ series: [] }))
  }, [stockCode, sector])

  useEffect(() => {
    if (!year) return
    api.get('/predict/heatmap', { params: { year } }).then(({ data }) => setHeatmap(data)).catch(() => setHeatmap({ heatmap: [] }))
  }, [year])

  useEffect(() => {
    if (!year || !sector) return
    api.get('/get-parameters', { params: { year, sector } }).then(({ data }) => setParamRanks(data.parameters || [])).catch(() => setParamRanks([]))
  }, [year, sector])

  const heatBySector = useMemo(() => {
    const map = {}
    for (const c of heatmap.heatmap || []) {
      map[c.sector] ||= []
      map[c.sector].push(c)
    }
    return map
  }, [heatmap])

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={heroS}>
        <div style={kickerS}><Sparkles size={15} /> Experimental Detail</div>
        <h1 style={titleS}>Forecasting diagnostics for {stockCode || 'selected stock'}.</h1>
        <p style={subtitleS}>
          Trend, parameter importance, and sector heatmap views for legacy forecasting experiments.
          Diagnostic output only; not production prediction or investment advice.
          Based on ~40 public BIST companies, yearly data 2020–2025, nominal TRY returns during a high-inflation period. Historical patterns; no validated predictive skill (walk-forward IC ≈ 0).
        </p>
        <span style={badgeS}><BrainCircuit size={13} /> Experimental tool</span>
      </section>

      {!stockCode ? (
        <EmptyState title="No stock selected" description="Open this page with query params: ?stock=ASELS&sector=...&year=2025" />
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 16 }}>
          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', marginBottom: 10 }}>Historical Trend • {stockCode}</div>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend.series || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="period_return" stroke="var(--primary)" strokeWidth={2} />
                <Line type="monotone" dataKey="return_1y" stroke="#22c55e" strokeWidth={1.5} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card style={{ padding: '1rem' }}>
            <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', marginBottom: 10 }}>Parameter Importance</div>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={(paramRanks || []).slice(0, 10)} layout="vertical" margin={{ left: 10, right: 10 }}>
                <XAxis type="number" />
                <YAxis dataKey="parameter_name" type="category" width={110} />
                <Tooltip />
                <Bar dataKey="score">
                  {(paramRanks || []).slice(0, 10).map((_, i) => (
                    <Cell key={i} fill={i < 3 ? '#22c55e' : 'var(--primary)'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>
      )}

      <Card style={{ padding: '1rem', marginTop: 16 }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', marginBottom: 10 }}>Sector Heatmap ({year || 'n/a'})</div>
        <p style={{ color: 'var(--warning)', fontSize: 12, margin: '0 0 12px', lineHeight: 1.5 }}>
          Sector comparisons with fewer than 10 companies are anecdotal.
        </p>
        {Object.keys(heatBySector).length === 0 ? (
          <EmptyState title="No heatmap data" description="Run forecast and ensure year data exists." />
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Sector</th>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Feature</th>
                  <th style={{ textAlign: 'right', borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>Value</th>
                </tr>
              </thead>
              <tbody>
                {(heatmap.heatmap || []).slice(0, 120).map((c, idx) => (
                  <tr key={`${c.sector}-${c.feature}-${idx}`}>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.sector}</td>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px' }}>{c.feature}</td>
                    <td style={{ borderBottom: '1px solid var(--border)', padding: '8px 10px', textAlign: 'right' }}><HeatColor value={c.value} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

const heroS = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 18 }
const kickerS = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const titleS = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.2rem)', lineHeight: 1, fontWeight: 900 }
const subtitleS = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 760 }
const badgeS = { display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 16, background: 'var(--warning-subtle)', color: 'var(--warning-light)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800 }
