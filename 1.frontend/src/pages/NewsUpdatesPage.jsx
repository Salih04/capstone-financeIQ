import { useEffect, useState } from 'react'
import { Newspaper, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState, SectionHeader } from '../components/ui'

export default function NewsUpdatesPage() {
  const [sector, setSector] = useState('All')
  const [data, setData] = useState({ updates: [], ai_insight: '' })
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await api.get('/news/updates', { params: { sector } })
      setData(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [sector])

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <SectionHeader icon={<Newspaper size={20} />} title="News & Updates" subtitle="Sector updates with AI-generated insight" />

      <Card style={{ padding: '1rem', marginBottom: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 8 }}>
          <input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="Sector (e.g. Enerji Uretim ve Dagitim)" style={{ width: '100%', boxSizing: 'border-box', background: 'var(--surface-1)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', color: 'var(--text-1)', padding: '9px 12px', fontSize: 13 }} />
          <button onClick={load} style={{ border: 'none', borderRadius: 'var(--radius-md)', background: 'var(--primary)', color: '#fff', padding: '9px 12px', cursor: 'pointer' }}>Refresh</button>
        </div>
      </Card>

      <Card style={{ padding: '1rem', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginBottom: 8, color: 'var(--primary)' }}>
          <Sparkles size={14} />
          <span style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.6 }}>AI Insight</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.6 }}>{data.ai_insight || 'No insight yet.'}</div>
      </Card>

      <Card style={{ padding: '1rem' }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>Latest Updates</div>
        {loading ? (
          <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Loading...</div>
        ) : data.updates?.length ? (
          data.updates.map((n, i) => (
            <div key={i} style={{ borderTop: '1px solid var(--border)', padding: '10px 0' }}>
              <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)' }}>{n.title}</div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 3 }}>{n.source} • {new Date(n.published_at).toLocaleString('en-US')}</div>
              <div style={{ fontSize: 12.5, color: 'var(--text-2)', marginTop: 6 }}>{n.summary}</div>
            </div>
          ))
        ) : (
          <EmptyState title="No updates" description="Try another sector." />
        )}
      </Card>
    </div>
  )
}
