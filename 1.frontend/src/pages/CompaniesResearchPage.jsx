import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Search, ChevronRight } from 'lucide-react'
import { SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { CompactTable, MiniBar, formatNumber, asText } from '../utils/safeRender'

export default function CompaniesResearchPage() {
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [q, setQ] = useState('')

  useEffect(() => { researchApi.companies().then(r => setData(r.data)) }, [])

  const rows = useMemo(() => {
    const all = (data?.companies || []).slice().sort((a, b) => (a.ml_rank ?? 1e9) - (b.ml_rank ?? 1e9))
    const filtered = q ? all.filter(c => c.ticker.toLowerCase().includes(q.toLowerCase())) : all
    return filtered.map(c => ({ ...c, __onClick: () => nav(`/research/companies/${c.ticker}`) }))
  }, [data, q, nav])

  const columns = [
    { key: 'ml_rank', label: '#', align: 'right' },
    { key: 'ticker', label: 'Ticker' },
    { key: 'year', label: 'Year', align: 'right' },
    { key: 'ml_score', label: 'ML score', align: 'right' },
    { key: 'bar', label: '', align: 'left' },
    { key: 'go', label: '', align: 'right' },
  ]

  const renderCell = (c, r) => {
    if (c.key === 'ticker') return <span style={{ fontWeight: 700, color: 'var(--text-1)' }}>{r.ticker}</span>
    if (c.key === 'ml_score') return formatNumber(r.ml_score, 3)
    if (c.key === 'bar') return <div style={{ width: 90 }}><MiniBar value={(r.ml_score ?? 0) * 100} max={100} tone="accent" /></div>
    if (c.key === 'go') return <ChevronRight size={15} color="var(--text-3)" />
    return asText(r[c.key])
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, maxWidth: 1000 }}>
      <SectionHeader title="Companies" sub={`Research scores · latest year ${asText(data?.year)} · ${asText(data?.count)} companies`} icon={Building2}
        actions={
          <div style={{ display: 'flex', gap: 7, alignItems: 'center', background: 'var(--surface-2)',
            border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', padding: '6px 11px' }}>
            <Search size={15} color="var(--text-3)" />
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="filter ticker"
              style={{ background: 'transparent', color: 'var(--text-1)', border: 0, outline: 'none', fontSize: 13, width: 130 }} />
          </div>
        } />
      <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 8 }}>
        <CompactTable columns={columns} rows={rows} renderCell={renderCell} empty="No matching companies." />
      </div>
      <p style={{ fontSize: 11.5, color: 'var(--text-3)', margin: 0 }}>
        ML score = transparent rank of validated year-T features (no trained model beats baseline). Click a row for the research snapshot.
      </p>
    </div>
  )
}
