import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ShieldCheck, Sparkles } from 'lucide-react'
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

function toNullableNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const n = Number(value)
  return Number.isFinite(n) ? n : null
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

  const all = useMemo(() => {
    return (data?.companies || [])
      .map(c => ({
        ...c,
        ml_score: toNullableNumber(c.ml_score),
        ml_rank: toNullableNumber(c.ml_rank),
      }))
      .slice()
      .sort((a, b) => {
        const ar = a.ml_rank ?? 1e9
        const br = b.ml_rank ?? 1e9
        return ar - br
      })
  }, [data])

  const rows = useMemo(() => {
    const query = q.trim().toLowerCase()
    return query
      ? all.filter(c => String(c.ticker || '').toLowerCase().includes(query))
      : all
  }, [all, q])

  const scoredCompanies = useMemo(() => {
    return all.filter(c => c.ml_score != null)
  }, [all])

  const scores = useMemo(() => {
    return scoredCompanies.map(c => c.ml_score)
  }, [scoredCompanies])

  const avg = scores.length
    ? scores.reduce((a, b) => a + b, 0) / scores.length
    : null

  const top = scoredCompanies.length
    ? [...scoredCompanies].sort((a, b) => b.ml_score - a.ml_score)[0]
    : null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 22, maxWidth: 1320, margin: '0 auto', padding: '4px 6px' }}>
      <section style={styles.hero}>
        <div>
          <div style={styles.kicker}><Sparkles size={15} /> Research Universe</div>
          <h1 style={styles.title}>Ranked company cards for the validated BIST universe.</h1>
          <p style={styles.subtitle}>
            Latest-year research scores for {asText(data?.count)} selected companies. Scores summarize
            validated year-end features for diagnostic research support, not buy or sell advice.
          </p>
          <div style={styles.badges}>
            <SignalBadge tone="good"><ShieldCheck size={12} /> Leakage-safe context</SignalBadge>
            <SignalBadge tone={bench?.available ? 'good' : 'warn'}>BIST100 {bench?.available ? 'available' : 'missing'}</SignalBadge>
            <SignalBadge tone="bad">Not investment advice</SignalBadge>
          </div>
        </div>

        <div style={styles.searchPanel}>
          <div style={styles.searchLabel}>Find Company</div>
          <div style={styles.searchBox}>
            <Search size={16} color="var(--text-3)" />
            <input
              value={q}
              onChange={e => setQ(e.target.value)}
              placeholder="Search ticker..."
              style={styles.searchInput}
            />
          </div>
          <p style={styles.searchHint}>Open any card for company-level evidence and score explanation.</p>
        </div>
      </section>

      {/* KPI strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px,1fr))', gap: 14 }}>
        <MetricCard label="Companies" value={asText(data?.count)} tone="info" sub="research universe" />
        <MetricCard label="Latest year" value={asText(data?.year)} sub="most recent features" />
        <MetricCard label="Average score" value={avg != null ? formatNumber(avg, 2) : '—'} sub="fundamental rank (0–1)" />
        <MetricCard
          label="Top-ranked"
          value={top ? asText(top.ticker) : '—'}
          tone={top ? 'good' : 'neutral'}
          sub={top ? `score ${formatNumber(top.ml_score, 2)}` : 'score —'}
        />
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
  const hasScore = c.ml_score != null

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
          borderRadius: 999, padding: '2px 9px' }}>#{hasScore ? asText(c.ml_rank) : '—'}</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 24, fontWeight: 800, color: 'var(--primary)', fontVariantNumeric: 'tabular-nums' }}>
          {hasScore ? formatNumber(c.ml_score, 2) : '—'}
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-3)' }}>research score</span>
      </div>
      <MiniBar value={hasScore ? c.ml_score * 100 : 0} max={100} tone="accent" />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 2 }}>
        <SignalBadge tone={st.tone}>{st.label}</SignalBadge>
        <span style={{ fontSize: 11, color: 'var(--text-3)' }}>benchmark-aware</span>
      </div>
    </div>
  )
}

const styles = {
  hero: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))',
    gap: 18,
    alignItems: 'end',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(244,176,74,0.13), rgba(58,199,139,0.08) 44%, var(--surface-2))',
    padding: 24,
  },
  kicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 7,
    color: 'var(--primary-hover)',
    background: 'var(--primary-subtle)',
    border: '1px solid rgba(244,176,74,0.25)',
    borderRadius: 999,
    padding: '5px 11px',
    fontSize: 12,
    fontWeight: 800,
    textTransform: 'uppercase',
    letterSpacing: 0.7,
  },
  title: {
    margin: '14px 0 8px',
    color: 'var(--text-1)',
    fontSize: 'clamp(2rem, 5vw, 3.35rem)',
    lineHeight: 1,
    fontWeight: 900,
    maxWidth: 820,
  },
  subtitle: {
    color: 'var(--text-2)',
    fontSize: 14.5,
    lineHeight: 1.65,
    margin: 0,
    maxWidth: 740,
  },
  badges: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 16,
  },
  searchPanel: {
    background: 'rgba(8,15,26,0.54)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: 16,
  },
  searchLabel: {
    color: 'var(--text-3)',
    fontSize: 11,
    fontWeight: 900,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 8,
  },
  searchBox: {
    display: 'flex',
    gap: 9,
    alignItems: 'center',
    background: 'var(--surface-1)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: '10px 12px',
  },
  searchInput: {
    flex: 1,
    minWidth: 0,
    background: 'transparent',
    color: 'var(--text-1)',
    border: 0,
    outline: 'none',
    fontSize: 13.5,
  },
  searchHint: {
    color: 'var(--text-3)',
    fontSize: 12,
    lineHeight: 1.45,
    margin: '10px 0 0',
  },
}