import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Search } from 'lucide-react'
import { SectionHeader } from '../components/ui'
import { researchApi } from '../api/researchApi'
import { MetricCard, MiniBar, SignalBadge, formatNumber, asText, NOT_ADVICE } from '../utils/safeRender'

// score band -> business status (score is a 0..1 fundamental rank, not advice)
function statusOf(score) {
  if (score == null) return { label: 'Unranked', tone: 'neutral' }
  if (score >= 0.66) return { label: 'Strong', tone: 'good' }
  if (score >= 0.45) return { label: 'Moderate', tone: 'info' }
  if (score >= 0.30) return { label: 'Watchlist', tone: 'warn' }
  return { label: 'Low confidence', tone: 'bad' }
}

export default function CompaniesResearchPage() {
  const nav = useNavigate()
  const [data, setData] = useState(null)
  const [bench, setBench] = useState(null)
  const [q, setQ] = useState('')

  useEffect(() => {
    researchApi.companies().then(r => setData(r.data))
    researchApi.benchmark().then(r => setBench(r.data))
  }, [])

  const all = useMemo(() => (data?.companies || []).slice()
    .sort((a, b) => (a.ml_rank ?? 1e9) - (b.ml_rank ?? 1e9)), [data])
  const rows = useMemo(() =>
    q ? all.filter(c => c.ticker.toLowerCase().includes(q.toLowerCase())) : all, [all, q])

  const scores = all.map(c => c.ml_score).filter(v => v != null)
  const avg = scores.length ? scores.reduce((a, b) => a + b, 0) / scores.length : null
  const top = all.find(c => c.ml_rank === 1) || all[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 1320, margin: '0 auto', padding: '4px 6px' }}>
      <SectionHeader title="Research Universe"
        sub={`${asText(data?.count)} BIST companies · latest research year ${asText(data?.year)}`}
        icon={Building2}
        actions={
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', background: 'var(--surface-2)',
            border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', padding: '7px 12px' }}>
            <Search size={15} color="var(--text-3)" />
            <input value={q} onChange={e => setQ(e.target.value)} placeholder="search ticker…"
              style={{ background: 'transparent', color: 'var(--text-1)', border: 0, outline: 'none', fontSize: 13.5, width: 150 }} />
          </div>
        } />

      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 14 }}>
        <MetricCard label="Companies" value={asText(data?.count)} tone="info" sub="research universe" />
        <MetricCard label="Latest year" value={asText(data?.year)} sub="most recent features" />
        <MetricCard label="Average score" value={avg != null ? formatNumber(avg, 2) : '—'} sub="fundamental rank (0–1)" />
        <MetricCard label="Top-ranked" value={asText(top?.ticker)} tone="good" sub={`score ${formatNumber(top?.ml_score, 2)}`} />
        <MetricCard label="Benchmark" value={bench?.available ? 'Available' : 'Missing'} tone={bench?.available ? 'good' : 'warn'} sub="BIST100 context" />
      </div>

      {/* Company cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(248px,1fr))', gap: 14 }}>
        {rows.length === 0 && <div style={{ color: 'var(--text-3)', fontSize: 13, padding: 20 }}>No matching companies.</div>}
        {rows.map(c => {
          const st = statusOf(c.ml_score)
          return <CompanyCard key={c.ticker} c={c} st={st} onClick={() => nav(`/research/companies/${c.ticker}`)} />
        })}
      </div>

      <p style={{ fontSize: 11.5, color: 'var(--text-3)', margin: 0, textAlign: 'center' }}>
        Score = transparent rank of validated year-end features (benchmark-aware). {NOT_ADVICE}
      </p>
    </div>
  )
}

function CompanyCard({ c, st, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <div onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
      style={{ cursor: 'pointer', background: 'var(--surface-2)',
        border: `1px solid ${hover ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', flexDirection: 'column', gap: 11,
        transition: 'border-color .15s, transform .12s, box-shadow .15s',
        transform: hover ? 'translateY(-2px)' : 'none', boxShadow: hover ? 'var(--shadow-sm)' : 'none' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
          <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-1)' }}>{c.ticker}</span>
          <span style={{ fontSize: 11.5, color: 'var(--text-3)' }}>{asText(c.year)}</span>
        </div>
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-3)', background: 'var(--surface-3)',
          borderRadius: 999, padding: '2px 9px' }}>#{asText(c.ml_rank)}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--primary)', fontVariantNumeric: 'tabular-nums' }}>
          {formatNumber(c.ml_score, 2)}
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-3)' }}>research score</span>
      </div>
      <MiniBar value={(c.ml_score ?? 0) * 100} max={100} tone="accent" />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 }}>
        <SignalBadge tone={st.tone}>{st.label}</SignalBadge>
        <span style={{ fontSize: 11, color: 'var(--text-3)' }}>benchmark-aware</span>
      </div>
    </div>
  )
}
