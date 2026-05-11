import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2, TrendingUp, Activity, Zap, GitCompare,
  FileText, ChevronRight, ArrowUpRight, ArrowDownRight, Minus,
  Clock, AlertTriangle, CheckCircle2, BarChart3, Search,
  Trophy, Target, BrainCircuit,
} from 'lucide-react'
import { AreaChart, Area, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import api from '../api/client'
import { useAuth } from '../context/AuthContext'
import { StatCard, SectionHeader, ScoreBadge, getBand, PrimaryButton, GhostButton, Card, Skeleton } from '../components/ui'

function QuickActionCard({ icon: Icon, label, sub, onClick, accent }) {
  const [h, setH] = useState(false)
  return (
    <div
      onClick={onClick}
      style={{
        background: h ? 'var(--surface-3)' : 'var(--surface-2)',
        border: `1px solid ${h ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        cursor: 'pointer',
        transition: 'all 0.15s',
        transform: h ? 'translateY(-2px)' : 'none',
        boxShadow: h ? 'var(--shadow-md)' : 'none',
      }}
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
    >
      <div style={{
        width: 40, height: 40, borderRadius: 12,
        background: accent ? `color-mix(in srgb, ${accent} 15%, transparent)` : 'var(--primary-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: accent || 'var(--primary)', marginBottom: 12,
      }}>
        <Icon size={20} />
      </div>
      <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-1)', marginBottom: 3 }}>{label}</div>
      {sub && <div style={{ fontSize: 12, color: 'var(--text-3)' }}>{sub}</div>}
      <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 4, color: accent || 'var(--primary)', fontSize: 12, fontWeight: 600 }}>
        Open <ChevronRight size={13} />
      </div>
    </div>
  )
}

function ScoreRunRow({ run, onClick }) {
  const band = getBand(run.total_score)
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '11px 16px', cursor: 'pointer',
        borderTop: '1px solid var(--border)',
        transition: 'background 0.12s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-3)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div style={{
        width: 34, height: 34, borderRadius: 10,
        background: `color-mix(in srgb, ${band.dot} 12%, transparent)`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: band.dot, fontWeight: 800, fontSize: 12, flexShrink: 0,
        fontVariantNumeric: 'tabular-nums',
      }}>
        {run.total_score?.toFixed(0) ?? '?'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--text-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {run.ticker || run.company_name || `Company #${run.company_id}`}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 1 }}>
          {run.period}
        </div>
      </div>
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <ScoreBadge score={run.total_score} />
        <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 3 }}>
          {new Date(run.created_at).toLocaleDateString('en-US', { month:'short', day:'numeric' })}
        </div>
      </div>
      <ChevronRight size={14} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
    </div>
  )
}

function CompanyRow({ company, onClick }) {
  const sectorLabel = company.sector || (company.sector_code || '').replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, m => m.toUpperCase())
  return (
    <div
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '10px 16px', cursor: 'pointer',
        borderTop: '1px solid var(--border)',
        transition: 'background 0.12s',
      }}
      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-3)'}
      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
    >
      <div style={{
        width: 34, height: 34, borderRadius: 10,
        background: 'var(--primary-subtle)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--primary)', fontWeight: 800, fontSize: 11, flexShrink: 0,
      }}>
        {company.ticker?.substring(0, 2)}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--primary-hover)' }}>{company.ticker}</div>
        <div style={{ fontSize: 12, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {company.company_name}
        </div>
      </div>
      {sectorLabel && (
        <span style={{ fontSize: 11, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 5, padding: '2px 8px', whiteSpace: 'nowrap' }}>
          {sectorLabel}
        </span>
      )}
      <ChevronRight size={14} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
    </div>
  )
}

/* Mini score distribution bar chart */
function ScoreDistribution({ runs }) {
  const buckets = useMemo(() => {
    const b = [
      { range: '0–35', label: 'Risky', count: 0, color: 'var(--danger)' },
      { range: '35–55', label: 'Watch', count: 0, color: '#f97316' },
      { range: '55–75', label: 'Moderate', count: 0, color: 'var(--warning)' },
      { range: '75–100', label: 'Strong', count: 0, color: 'var(--success)' },
    ]
    runs.forEach(r => {
      const s = r.total_score ?? 0
      if (s >= 75) b[3].count++
      else if (s >= 55) b[2].count++
      else if (s >= 35) b[1].count++
      else b[0].count++
    })
    return b
  }, [runs])

  if (runs.length === 0) return null

  return (
    <div>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
        Score Distribution
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', height: 80 }}>
        {buckets.map(b => {
          const maxCount = Math.max(...buckets.map(x => x.count), 1)
          const h = Math.max(b.count / maxCount * 60, 4)
          return (
            <div key={b.range} style={{ flex: 1, textAlign: 'center' }}>
              <div style={{ fontSize: 13, fontWeight: 800, color: 'var(--text-1)', marginBottom: 4 }}>
                {b.count}
              </div>
              <div style={{
                height: h, borderRadius: 4, background: b.color,
                transition: 'height 0.3s ease', margin: '0 auto', width: '80%',
              }} />
              <div style={{ fontSize: 10, color: 'var(--text-3)', marginTop: 6, fontWeight: 600 }}>
                {b.label}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* Top performers list */
function TopPerformers({ runs, navigate }) {
  const top = useMemo(() =>
    [...runs]
      .filter(r => r.total_score != null)
      .sort((a, b) => b.total_score - a.total_score)
      .slice(0, 3),
    [runs]
  )
  if (top.length === 0) return null
  return (
    <div>
      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
        Top Performers
      </div>
      {top.map((r, i) => {
        const band = getBand(r.total_score)
        const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : '🥉'
        return (
          <div
            key={r.id}
            onClick={() => navigate(`/score-runs/${r.id}`)}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 0', cursor: 'pointer',
              borderBottom: i < top.length - 1 ? '1px solid var(--border)' : 'none',
            }}
          >
            <span style={{ fontSize: 16 }}>{medal}</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {r.ticker || r.company_name || `Company #${r.company_id}`}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.period}</div>
            </div>
            <div style={{
              fontSize: 14, fontWeight: 800, color: band.dot,
              fontVariantNumeric: 'tabular-nums',
            }}>
              {r.total_score.toFixed(1)}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [recentRuns, setRecentRuns] = useState([])
  const [companies, setCompanies] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.allSettled([
      api.get('/users/me/score-runs'),
      api.get('/companies?limit=50'),
      api.get('/ingestion/dashboard').catch(() => null),
    ]).then(([runs, comps, h]) => {
      if (runs.status === 'fulfilled') setRecentRuns(runs.value.data)
      if (comps.status === 'fulfilled') setCompanies(comps.value.data)
      if (h.status === 'fulfilled' && h.value) setHealth(h.value.data)
    }).finally(() => setLoading(false))
  }, [])

  const firstName = user?.email?.split('@')[0] || 'User'
  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  /* Derived stats */
  const avgScore = useMemo(() => {
    const scored = recentRuns.filter(r => r.total_score != null)
    if (scored.length === 0) return null
    return scored.reduce((s, r) => s + r.total_score, 0) / scored.length
  }, [recentRuns])

  const bestRun = useMemo(() => {
    const scored = recentRuns.filter(r => r.total_score != null)
    if (scored.length === 0) return null
    return scored.reduce((best, r) => r.total_score > best.total_score ? r : best)
  }, [recentRuns])

  const sectorBreakdown = useMemo(() => {
    const map = {}
    companies.forEach(c => {
      const s = c.sector || c.sector_code || 'Other'
      map[s] = (map[s] || 0) + 1
    })
    return Object.entries(map)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }))
  }, [companies])

  /* Score trend data for the area chart */
  const trendData = useMemo(() =>
    [...recentRuns]
      .filter(r => r.total_score != null)
      .slice(0, 12)
      .reverse()
      .map(r => ({
        name: r.ticker || r.company_name?.substring(0, 6) || `#${r.company_id}`,
        score: Math.round(r.total_score * 10) / 10,
      })),
    [recentRuns]
  )

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* Hero greeting */}
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-1)', letterSpacing: '-0.4px' }}>
          {greeting}, <span style={{ color: 'var(--primary-hover)' }}>{firstName}</span> 👋
        </h1>
        <p style={{ color: 'var(--text-3)', fontSize: 14, marginTop: 4 }}>
          Here's what's happening in your financial analysis workspace today.
        </p>
      </div>

      {/* Stat strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
        <StatCard
          label="Total Companies"
          value={loading ? '—' : companies.length}
          sub="in database"
          accent="var(--primary)"
          icon={Building2}
        />
        <StatCard
          label="Score Runs"
          value={loading ? '—' : recentRuns.length}
          sub="total analyses"
          accent="var(--success)"
          icon={BarChart3}
        />
        <StatCard
          label="Avg. Score"
          value={loading ? '—' : avgScore != null ? avgScore.toFixed(1) : '—'}
          sub={avgScore != null ? getBand(avgScore).label : 'no data'}
          accent={avgScore != null ? getBand(avgScore).dot : 'var(--text-3)'}
          icon={Target}
        />
        <StatCard
          label="Best Score"
          value={loading ? '—' : bestRun ? bestRun.total_score.toFixed(1) : '—'}
          sub={bestRun ? (bestRun.ticker || bestRun.company_name || '') : 'no data'}
          accent="var(--success)"
          icon={Trophy}
        />
      </div>

      {/* Score trend chart */}
      {!loading && trendData.length >= 2 && (
        <Card style={{ padding: '20px', marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-1)' }}>Score Trend</div>
              <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>Your recent analyses at a glance</div>
            </div>
            <GhostButton onClick={() => navigate('/reports')} style={{ fontSize: 12, padding: '5px 10px' }}>
              View Reports
            </GhostButton>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={trendData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--primary)" stopOpacity={0.25} />
                  <stop offset="100%" stopColor="var(--primary)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--text-3)' }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{
                  background: 'var(--surface-2)', border: '1px solid var(--border-strong)',
                  borderRadius: 8, fontSize: 12, boxShadow: 'var(--shadow-md)',
                }}
                labelStyle={{ color: 'var(--text-1)', fontWeight: 700 }}
                itemStyle={{ color: 'var(--primary)' }}
              />
              <Area
                type="monotone" dataKey="score" stroke="var(--primary)"
                strokeWidth={2.5} fill="url(#scoreGrad)" dot={{ r: 4, fill: 'var(--primary)', strokeWidth: 0 }}
                activeDot={{ r: 6, fill: 'var(--primary)', stroke: 'var(--surface-2)', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      )}

      {/* Quick actions */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--text-3)', marginBottom: 14 }}>
          Quick Actions
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
          <QuickActionCard
            icon={BrainCircuit}
            label="Forecasting"
            sub="Winner-only sector forecasting"
            onClick={() => navigate('/forecasting')}
            accent="var(--primary)"
          />
          <QuickActionCard
            icon={GitCompare}
            label="Compare"
            sub="Side-by-side comparison"
            onClick={() => navigate('/compare')}
            accent="var(--success)"
          />
          <QuickActionCard
            icon={FileText}
            label="Reports"
            sub="Export & analyze reports"
            onClick={() => navigate('/reports')}
            accent="var(--warning)"
          />
          <QuickActionCard
            icon={Activity}
            label="Data Health"
            sub="Ingestion & quality status"
            onClick={() => navigate('/data-health')}
            accent="var(--info)"
          />
        </div>
      </div>

      {/* Three-column: recent runs + companies + insights */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 300px', gap: 20 }}>
        {/* Recent score runs */}
        <Card>
          <div style={{ padding: '16px 16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-1)' }}>Recent Score Runs</div>
            <GhostButton onClick={() => navigate('/reports')} style={{ fontSize: 12, padding: '5px 10px' }}>
              View all
            </GhostButton>
          </div>
          {loading ? (
            <div style={{ padding: '16px' }}>
              {[...Array(4)].map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                  <Skeleton width={34} height={34} radius={10} />
                  <div style={{ flex: 1 }}>
                    <Skeleton width="60%" height={13} style={{ marginBottom: 5 }} />
                    <Skeleton width="40%" height={11} />
                  </div>
                </div>
              ))}
            </div>
          ) : recentRuns.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}>
              No score runs yet. Open a company to run analysis.
            </div>
          ) : (
            recentRuns.slice(0, 6).map(r => (
              <ScoreRunRow key={r.id} run={r} onClick={() => navigate(`/score-runs/${r.id}`)} />
            ))
          )}
        </Card>

        {/* Company list */}
        <Card>
          <div style={{ padding: '16px 16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-1)' }}>Companies</div>
            <GhostButton onClick={() => navigate('/companies')} style={{ fontSize: 12, padding: '5px 10px' }}>
              View all
            </GhostButton>
          </div>
          {loading ? (
            <div style={{ padding: '16px' }}>
              {[...Array(5)].map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
                  <Skeleton width={34} height={34} radius={10} />
                  <div style={{ flex: 1 }}>
                    <Skeleton width="30%" height={13} style={{ marginBottom: 5 }} />
                    <Skeleton width="55%" height={11} />
                  </div>
                </div>
              ))}
            </div>
          ) : companies.length === 0 ? (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-3)', fontSize: 13 }}>
              No companies in database.
            </div>
          ) : (
            companies.slice(0, 6).map(c => (
              <CompanyRow key={c.id} company={c} onClick={() => navigate(`/companies/${c.id}`)} />
            ))
          )}
        </Card>

        {/* Insights sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Score distribution */}
          {!loading && recentRuns.length > 0 && (
            <Card style={{ padding: '16px' }}>
              <ScoreDistribution runs={recentRuns} />
            </Card>
          )}

          {/* Top performers */}
          {!loading && recentRuns.length > 0 && (
            <Card style={{ padding: '16px' }}>
              <TopPerformers runs={recentRuns} navigate={navigate} />
            </Card>
          )}

          {/* Sector breakdown */}
          {!loading && sectorBreakdown.length > 0 && (
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
                Sectors
              </div>
              {sectorBreakdown.map((s, i) => (
                <div key={s.name} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '6px 0',
                  borderBottom: i < sectorBreakdown.length - 1 ? '1px solid var(--border)' : 'none',
                }}>
                  <div style={{
                    width: 6, height: 6, borderRadius: '50%',
                    background: 'var(--primary)', flexShrink: 0,
                  }} />
                  <div style={{ flex: 1, fontSize: 12, color: 'var(--text-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {s.name}
                  </div>
                  <span style={{
                    fontSize: 11, fontWeight: 700, color: 'var(--text-1)',
                    background: 'var(--surface-3)', borderRadius: 5, padding: '1px 7px',
                  }}>
                    {s.count}
                  </span>
                </div>
              ))}
            </Card>
          )}

          {/* Data health mini card */}
          {!loading && health && (
            <Card style={{ padding: '16px' }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 10 }}>
                Data Health
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                {health.ingestion_success_rate >= 90
                  ? <CheckCircle2 size={16} style={{ color: 'var(--success)' }} />
                  : <AlertTriangle size={16} style={{ color: 'var(--warning)' }} />}
                <span style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-1)' }}>
                  {health.ingestion_success_rate?.toFixed(0) ?? '—'}%
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-3)' }}>Ingestion success rate</div>
              <div
                onClick={() => navigate('/data-health')}
                style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600, marginTop: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 4 }}
              >
                View details <ChevronRight size={12} />
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
