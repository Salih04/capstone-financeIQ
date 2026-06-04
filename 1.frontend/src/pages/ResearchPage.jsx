import { useEffect, useMemo, useState } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import { FlaskConical, Search, AlertTriangle, Trophy } from 'lucide-react'
import api from '../api/client'
import { Card, SectionHeader, StatCard, EmptyState, ScoreBadge, Chip } from '../components/ui'

const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d))
const pct = (v) => (v === null || v === undefined ? '—' : `${Number(v).toFixed(1)}%`)

export default function ResearchPage() {
  const [years, setYears] = useState([])
  const [year, setYear] = useState(null)
  const [overview, setOverview] = useState(null)
  const [dashboard, setDashboard] = useState(null)
  const [selected, setSelected] = useState(null)
  const [detail, setDetail] = useState(null)
  const [sortKey, setSortKey] = useState('fundamental_score')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.get('/research/years')
      .then(({ data }) => {
        setYears(data.years)
        setYear(data.years[data.years.length - 1])
      })
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load years'))
    api.get('/research/dashboard').then(({ data }) => setDashboard(data)).catch(() => {})
  }, [])

  useEffect(() => {
    if (!year) return
    setLoading(true)
    api.get('/research/scores', { params: { year } })
      .then(({ data }) => {
        setOverview(data)
        const first = [...data.companies].sort((a, b) => (b.fundamental_score || 0) - (a.fundamental_score || 0))[0]
        setSelected(first?.ticker || null)
      })
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load scores'))
      .finally(() => setLoading(false))
  }, [year])

  useEffect(() => {
    if (!year || !selected) return
    api.get('/research/company', { params: { ticker: selected, year } })
      .then(({ data }) => setDetail(data))
      .catch(() => setDetail(null))
  }, [year, selected])

  const rows = useMemo(() => {
    if (!overview) return []
    let r = [...overview.companies]
    if (query) r = r.filter((c) => c.ticker.toLowerCase().includes(query.toLowerCase()))
    r.sort((a, b) => (b[sortKey] ?? -1e18) - (a[sortKey] ?? -1e18))
    return r
  }, [overview, sortKey, query])

  const scatter = useMemo(
    () => (overview?.companies || []).filter((c) => c.fundamental_score != null && c.realized_return != null)
      .map((c) => ({ ...c, x: c.fundamental_score, y: c.realized_return })),
    [overview],
  )

  if (error) return <EmptyState icon={AlertTriangle} title="Research data unavailable" description={String(error)} />

  const v = dashboard?.validation
  const benchMissing = dashboard && !dashboard.benchmark?.available

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader
        title="Research — Score vs Realized Performance"
        sub="Fundamental Score is explanatory, not financial advice. Same-year correlation ≠ future prediction."
        icon={FlaskConical}
        actions={
          <select value={year || ''} onChange={(e) => setYear(Number(e.target.value))}
            style={{ background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
            {years.map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        }
      />

      {dashboard?.data_note && (
        <Card style={{ borderColor: 'var(--warning, #b45309)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: 'var(--text-2)', fontSize: 13 }}>
            <AlertTriangle size={18} />
            <span><b>Data note:</b> {dashboard.data_note}</span>
          </div>
        </Card>
      )}

      {benchMissing && (
        <Card style={{ borderColor: 'var(--warning, #b45309)' }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center', color: 'var(--text-2)' }}>
            <AlertTriangle size={18} />
            <span>{dashboard.benchmark?.message || 'BIST100 benchmark missing.'} Excess-return vs BIST100 is hidden until provided.</span>
          </div>
        </Card>
      )}

      {/* Model-quality strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
        <StatCard label="Mean Spearman (all years)" value={v ? fmt(v.mean_spearman, 3) : '—'} sub="score vs same-year return" />
        <StatCard label="Years score worked" value={v ? (v.years_score_worked.join(', ') || 'none') : '—'} />
        <StatCard label="Years score failed" value={v ? (v.years_score_failed.join(', ') || 'none') : '—'} />
        <StatCard label="Companies this year" value={overview?.count ?? '—'} sub={`BIST100: ${overview?.bist100_return != null ? pct(overview.bist100_return) : 'missing'}`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.3fr) minmax(0, 1fr)', gap: 16 }}>
        {/* Scatter */}
        <Card>
          <SectionHeader title={`Score vs Realized Return — ${year || ''}`} sub="Each dot = one company. Selected highlighted." />
          <div style={{ height: 360 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ top: 10, right: 20, bottom: 30, left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" dataKey="x" name="Fundamental Score" domain={[0, 100]}
                  label={{ value: 'Fundamental Score', position: 'bottom', fill: 'var(--text-3)' }} stroke="var(--text-3)" fontSize={11} />
                <YAxis type="number" dataKey="y" name="Realized Return %" stroke="var(--text-3)" fontSize={11}
                  label={{ value: 'Realized Return %', angle: -90, position: 'insideLeft', fill: 'var(--text-3)' }} />
                <ZAxis range={[60, 60]} />
                <ReferenceLine y={0} stroke="var(--text-3)" />
                <Tooltip cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }) => {
                    if (!payload?.length) return null
                    const d = payload[0].payload
                    return <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: 8, fontSize: 12 }}>
                      <b>{d.ticker}</b><br />Score {fmt(d.x)} · Return {pct(d.y)}<br />score#{d.score_rank} · return#{d.return_rank}
                    </div>
                  }} />
                <Scatter data={scatter} onClick={(d) => setSelected(d.ticker)}>
                  {scatter.map((d) => (
                    <Cell key={d.ticker} fill={d.ticker === selected ? 'var(--accent, #6366f1)' : 'var(--text-3)'}
                      opacity={d.ticker === selected ? 1 : 0.5} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Detail panel */}
        <Card>
          {detail ? <CompanyDetail d={detail} /> : <EmptyState icon={Search} title="Select a company" description="Click a dot or a table row." />}
        </Card>
      </div>

      {/* All-companies table */}
      <Card>
        <SectionHeader title={`All companies — ${year || ''}`} sub="Click a row to update the panel. Sortable."
          actions={
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <Search size={15} color="var(--text-3)" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="filter ticker"
                style={{ background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '6px 10px', fontSize: 12 }} />
            </div>
          } />
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text-3)' }}>
                {[['ticker', 'Ticker'], ['fundamental_score', 'Fund. Score'], ['market_score', 'Market Score'],
                  ['realized_return', 'Realized Ret %'], ['score_rank', 'Score #'], ['return_rank', 'Return #']].map(([k, lbl]) => (
                  <th key={k} onClick={() => k !== 'ticker' && setSortKey(k)}
                    style={{ padding: '8px 10px', cursor: k !== 'ticker' ? 'pointer' : 'default', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)' }}>
                    {lbl}{sortKey === k ? ' ▾' : ''}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? <tr><td colSpan={6} style={{ padding: 16, color: 'var(--text-3)' }}>Loading…</td></tr>
                : rows.map((c) => (
                  <tr key={c.ticker} onClick={() => setSelected(c.ticker)}
                    style={{ cursor: 'pointer', background: c.ticker === selected ? 'var(--surface-2)' : 'transparent' }}>
                    <td style={{ padding: '7px 10px', fontWeight: 600 }}>{c.ticker}</td>
                    <td style={{ padding: '7px 10px' }}><ScoreBadge score={c.fundamental_score} /></td>
                    <td style={{ padding: '7px 10px' }}>{fmt(c.market_score)}</td>
                    <td style={{ padding: '7px 10px', color: (c.realized_return || 0) >= 0 ? 'var(--success, #16a34a)' : 'var(--danger, #dc2626)' }}>{pct(c.realized_return)}</td>
                    <td style={{ padding: '7px 10px' }}>{c.score_rank ?? '—'}</td>
                    <td style={{ padding: '7px 10px' }}>{c.return_rank ?? '—'}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}

function CompanyDetail({ d }) {
  const profit = d.profit_status || {}
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div><div style={{ fontSize: 20, fontWeight: 700 }}>{d.ticker}</div><div style={{ color: 'var(--text-3)', fontSize: 12 }}>{d.year}</div></div>
        <ScoreBadge score={d.fundamental_score} size="lg" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <Mini label="Realized Return" value={d.realized_return != null ? `${d.realized_return.toFixed(1)}%` : '—'} />
        <Mini label="Return Rank" value={`${d.return_rank ?? '—'} / ${d.total_companies}`} />
        <Mini label="Score Rank" value={`${d.score_rank ?? '—'} / ${d.total_companies}`} />
        <Mini label="Market Score" value={fmt(d.market_score)} />
        <Mini label="vs BIST100" value={d.excess_vs_bist100 != null ? `${d.excess_vs_bist100.toFixed(1)}%` : 'benchmark missing'} />
        <Mini label="Gap to best" value={d.gap_to_best != null ? `${d.gap_to_best.toFixed(1)}%` : '—'} />
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        {Object.entries(profit).map(([k, val]) => (
          <Chip key={k} color={val === true ? 'success' : val === false ? 'danger' : 'default'}>
            {k.replace(/_positive/, '').replace(/_/g, ' ')}: {val === null ? 'n/a' : val ? '✓' : '✗'}
          </Chip>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontSize: 12, color: 'var(--text-2)' }}>
        <Trophy size={14} /> Best {d.year}: <b>{d.best_performer?.ticker}</b> ({fmt(d.best_performer?.return)}%)
      </div>
      <div>
        <div style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 6 }}>Score breakdown by category (percentile)</div>
        {(d.score_breakdown || []).map((c) => (
          <div key={c.category} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ width: 110, fontSize: 12 }}>{c.category}</span>
            <div style={{ flex: 1, height: 8, background: 'var(--surface-2)', borderRadius: 4 }}>
              <div style={{ width: `${c.category_score ?? 0}%`, height: '100%', background: 'var(--accent, #6366f1)', borderRadius: 4 }} />
            </div>
            <span style={{ width: 38, fontSize: 12, textAlign: 'right' }}>{c.category_score != null ? c.category_score.toFixed(0) : '—'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Mini({ label, value }) {
  return (
    <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{label}</div>
      <div style={{ fontSize: 14, fontWeight: 600 }}>{value}</div>
    </div>
  )
}
