import { useEffect, useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { FileText, Download, BarChart3, GitCompare, Clock, ChevronRight, Search, Filter, TrendingUp, Target, ArrowUpDown } from 'lucide-react'
import api from '../api/client'
import { Card, ScoreBadge, getBand, Skeleton, EmptyState, GhostButton, SectionHeader, StatCard } from '../components/ui'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const TYPE_ICONS = {
  score: <BarChart3 size={15} />,
  compare: <GitCompare size={15} />,
  export: <Download size={15} />,
}

const TYPE_LABELS = {
  score: 'Score Report',
  compare: 'Comparison',
  export: 'Export',
}

function ReportCard({ run }) {
  const navigate = useNavigate()
  return (
    <div
      onClick={() => navigate(`/score-runs/${run.id}`)}
      style={{
        display: 'flex', alignItems: 'center', gap: 14, padding: '14px 16px',
        borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.15s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div style={{
        width: 36, height: 36, borderRadius: 'var(--radius-md)', background: 'var(--surface-3)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        color: 'var(--primary)'
      }}>
        {TYPE_ICONS.score}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-1)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {run.ticker || run.company_name || `Company #${run.company_id}`}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-3)', display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span>{TYPE_LABELS.score}</span>
          <span>·</span>
          <span>Period: {run.period}</span>
        </div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <ScoreBadge score={run.total_score} style={{ fontSize: 11, padding: '3px 10px', marginBottom: 4, display: 'block' }} />
        <div style={{ fontSize: 11, color: 'var(--text-3)' }}>
          {new Date(run.created_at).toLocaleDateString('en-US')}
        </div>
      </div>
      <ChevronRight size={14} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
    </div>
  )
}

function ExportRow({ run, onExport }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 14, padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-1)', marginBottom: 2 }}>
          {run.ticker || run.company_name || `Company #${run.company_id}`} — {run.period}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
          {new Date(run.created_at).toLocaleDateString('en-US')}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6 }}>
        {['csv', 'json', 'pdf'].map(f => (
          <GhostButton key={f} onClick={() => onExport(run.id, f)} style={{ padding: '4px 10px', fontSize: 11, gap: 4 }}>
            <Download size={11} /> {f.toUpperCase()}
          </GhostButton>
        ))}
      </div>
    </div>
  )
}

export default function ReportsPage() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('recent')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('date') // date | score | name
  const [sortDir, setSortDir] = useState('desc') // asc | desc

  useEffect(() => {
    api.get('/users/me/score-runs')
      .then(({ data }) => setRuns(Array.isArray(data) ? data : []))
      .catch(() => setRuns([]))
      .finally(() => setLoading(false))
  }, [])

  const downloadExport = (runId, format) => {
    const token = localStorage.getItem('token')
    const url = `${BASE_URL}/reports/score-runs/${runId}/export.${format}`
    fetch(url, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.blob())
      .then(blob => {
        const objUrl = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = objUrl
        a.download = `score_run_${runId}.${format}`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(objUrl)
      })
      .catch(console.error)
  }

  /* Derived data */
  const filteredRuns = useMemo(() => {
    let r = [...runs]
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      r = r.filter(run =>
        (run.ticker || '').toLowerCase().includes(q) ||
        (run.company_name || '').toLowerCase().includes(q) ||
        (run.period || '').toLowerCase().includes(q) ||
        (run.model_name || '').toLowerCase().includes(q)
      )
    }
    r.sort((a, b) => {
      let cmp = 0
      if (sortBy === 'date') cmp = new Date(a.created_at) - new Date(b.created_at)
      else if (sortBy === 'score') cmp = (a.total_score || 0) - (b.total_score || 0)
      else if (sortBy === 'name') cmp = (a.ticker || a.company_name || '').localeCompare(b.ticker || b.company_name || '')
      return sortDir === 'desc' ? -cmp : cmp
    })
    return r
  }, [runs, searchQuery, sortBy, sortDir])

  const avgScore = useMemo(() => {
    const scored = runs.filter(r => r.total_score != null)
    if (scored.length === 0) return null
    return scored.reduce((s, r) => s + r.total_score, 0) / scored.length
  }, [runs])

  const bestRun = useMemo(() => {
    const scored = runs.filter(r => r.total_score != null)
    if (scored.length === 0) return null
    return scored.reduce((best, r) => r.total_score > best.total_score ? r : best)
  }, [runs])

  const scoreBands = useMemo(() => {
    const b = { strong: 0, moderate: 0, watch: 0, risky: 0 }
    runs.forEach(r => {
      const s = r.total_score ?? 0
      if (s >= 75) b.strong++
      else if (s >= 55) b.moderate++
      else if (s >= 35) b.watch++
      else b.risky++
    })
    return b
  }, [runs])

  const toggleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(field); setSortDir('desc') }
  }

  const tabs = [
    { id: 'recent', label: 'Recent Analyses' },
    { id: 'exports', label: 'Export Center' },
  ]

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-1)', margin: 0, marginBottom: 4 }}>
          Reports
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-3)', margin: 0 }}>
          Your analysis history and export center
        </p>
      </div>

      {/* Summary stat cards */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
          {[1,2,3,4].map(i => <Skeleton key={i} style={{ height: 80, borderRadius: 'var(--radius-lg)' }} />)}
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
          <StatCard
            label="Total Analyses"
            value={runs.length}
            sub={`${filteredRuns.length} shown`}
            accent="var(--primary)"
            icon={BarChart3}
          />
          <StatCard
            label="Avg. Score"
            value={avgScore != null ? avgScore.toFixed(1) : '—'}
            sub={avgScore != null ? getBand(avgScore).label : 'no data'}
            accent={avgScore != null ? getBand(avgScore).dot : 'var(--text-3)'}
            icon={Target}
          />
          <StatCard
            label="Best Score"
            value={bestRun ? bestRun.total_score.toFixed(1) : '—'}
            sub={bestRun ? (bestRun.ticker || bestRun.company_name || '') : 'no data'}
            accent="var(--success)"
            icon={TrendingUp}
          />
          <StatCard
            label="Latest Analysis"
            value={runs.length > 0 ? new Date(runs[0].created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—'}
            sub={runs.length > 0 ? runs[0].ticker || runs[0].company_name || '' : 'none'}
            accent="var(--info)"
            icon={Clock}
          />
        </div>
      )}

      {/* Band distribution strip */}
      {!loading && runs.length > 0 && (
        <div style={{
          display: 'flex', gap: 0, marginBottom: 24, borderRadius: 8, overflow: 'hidden', height: 8,
          background: 'var(--surface-3)',
        }}>
          {[
            { count: scoreBands.strong, color: 'var(--success)' },
            { count: scoreBands.moderate, color: 'var(--warning)' },
            { count: scoreBands.watch, color: '#f97316' },
            { count: scoreBands.risky, color: 'var(--danger)' },
          ].map((b, i) => (
            b.count > 0 && (
              <div key={i} style={{
                flex: b.count, background: b.color, transition: 'flex 0.3s',
              }} title={`${b.count} runs`} />
            )
          ))}
        </div>
      )}

      {/* Search + Tabs row */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 0 }}>
        {/* Search */}
        <div style={{ position: 'relative', flex: 1, maxWidth: 320 }}>
          <Search size={14} style={{
            position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)',
            color: 'var(--text-3)', pointerEvents: 'none',
          }} />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search by ticker, name, period..."
            style={{
              width: '100%', boxSizing: 'border-box', padding: '8px 12px 8px 32px',
              background: 'var(--surface-2)', border: '1px solid var(--border-strong)',
              borderRadius: 8, color: 'var(--text-1)', fontSize: 13, outline: 'none',
            }}
          />
        </div>

        <div style={{ flex: 1 }} />

        {/* Sort controls */}
        <div style={{ display: 'flex', gap: 4 }}>
          {[
            { id: 'date', label: 'Date' },
            { id: 'score', label: 'Score' },
            { id: 'name', label: 'Name' },
          ].map(s => (
            <button
              key={s.id}
              onClick={() => toggleSort(s.id)}
              style={{
                fontSize: 11, fontWeight: 600, padding: '5px 10px', borderRadius: 6,
                border: `1px solid ${sortBy === s.id ? 'var(--primary)' : 'var(--border-strong)'}`,
                background: sortBy === s.id ? 'rgba(0,245,212,0.1)' : 'transparent',
                color: sortBy === s.id ? 'var(--primary)' : 'var(--text-3)',
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 3,
              }}
            >
              {s.label}
              {sortBy === s.id && <span style={{ fontSize: 9 }}>{sortDir === 'desc' ? '▼' : '▲'}</span>}
            </button>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 0, marginBottom: 0, borderBottom: '1px solid var(--border)', marginTop: 12 }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: 'none', border: 'none', padding: '10px 18px', fontSize: 13, fontWeight: 500,
              cursor: 'pointer', color: activeTab === tab.id ? 'var(--primary)' : 'var(--text-3)',
              borderBottom: activeTab === tab.id ? '2px solid var(--primary)' : '2px solid transparent',
              marginBottom: -1, transition: 'color 0.15s',
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <Card style={{ padding: 0, overflow: 'hidden', marginTop: 0, borderTopLeftRadius: 0, borderTopRightRadius: 0 }}>
        {loading ? (
          <div style={{ padding: '1rem' }}>
            {[1,2,3,4,5].map(i => <Skeleton key={i} style={{ height: 60, marginBottom: 8, borderRadius: 'var(--radius-md)' }} />)}
          </div>
        ) : filteredRuns.length === 0 ? (
          <div style={{ padding: '3rem' }}>
            <EmptyState
              icon={<FileText size={32} />}
              title={searchQuery ? 'No matching analyses' : 'No analyses yet'}
              description={searchQuery ? 'Try a different search term.' : 'Run a score on any company page to get started.'}
            />
          </div>
        ) : activeTab === 'recent' ? (
          filteredRuns.map(run => <ReportCard key={run.id} run={run} />)
        ) : (
          filteredRuns.map(run => <ExportRow key={run.id} run={run} onExport={downloadExport} />)
        )}
      </Card>

      {!loading && filteredRuns.length > 0 && (
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--text-3)', textAlign: 'right' }}>
          <Clock size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
          {filteredRuns.length}{filteredRuns.length !== runs.length ? ` of ${runs.length}` : ''} analyses listed
        </div>
      )}
    </div>
  )
}
