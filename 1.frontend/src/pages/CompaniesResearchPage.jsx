import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Search } from 'lucide-react'
import { Card, SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { formatNumber, asText } from '../utils/safeRender'

export default function CompaniesResearchPage() {
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')

  useEffect(() => { researchApi.companies().then(r => setData(r.data)) }, [])

  const rows = useMemo(() => {
    const all = data?.companies || []
    return q ? all.filter(c => c.ticker.toLowerCase().includes(q.toLowerCase())) : all
  }, [data, q])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <SectionHeader title="Companies" sub={`Research scores · latest year ${asText(data?.year)} · ${asText(data?.count)} companies`} icon={Building2}
        actions={
          <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
            <Search size={15} color="var(--text-3)" />
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="filter ticker" style={inp} />
          </div>
        } />
      <Card>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead><tr style={{ color: 'var(--text-3)', textAlign: 'left' }}>
              <th style={th}>Ticker</th><th style={th}>Year</th><th style={th}>ML score (0–1)</th><th style={th}>ML rank</th>
            </tr></thead>
            <tbody>
              {rows.length === 0 && <tr><td colSpan={4} style={{ padding: 12, color: 'var(--text-3)' }}>—</td></tr>}
              {rows.map(c => (
                <tr key={c.ticker} onClick={() => nav(`/research/companies/${c.ticker}`)} style={{ cursor: 'pointer' }}>
                  <td style={{ ...td, fontWeight: 700 }}>{c.ticker}</td>
                  <td style={td}>{asText(c.year)}</td>
                  <td style={td}>{formatNumber(c.ml_score, 3)}</td>
                  <td style={td}>{asText(c.ml_rank)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
      <p style={{ fontSize: 12, color: 'var(--text-3)' }}>
        ML score = transparent rank of validated year-T features (no trained model beats baseline). Click a row for detail.
      </p>
    </div>
  )
}

const inp = { background: 'var(--surface-1)', color: 'var(--text-1)', border: '1px solid var(--border-strong)', borderRadius: 8, padding: '6px 10px', fontSize: 12 }
const th = { padding: '8px 10px', borderBottom: '1px solid var(--border)' }
const td = { padding: '7px 10px' }
