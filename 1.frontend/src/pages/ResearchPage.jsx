import { useEffect, useMemo, useState } from 'react'
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts'
import {
  FlaskConical,
  Search,
  AlertTriangle,
  Trophy,
  TrendingUp,
  TrendingDown,
  Activity,
  BarChart3,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import api from '../api/client'
import { researchApi } from '../api/researchApi'
import { Card, EmptyState, Chip } from '../components/ui'
import TerminalFx from '../components/TerminalFx'

const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? '—' : Number(v).toFixed(d))
const pct = (v) => (v === null || v === undefined ? '—' : `${Number(v).toFixed(1)}%`)

const scoreTone = (score) => {
  if (score >= 70) return { label: 'Strong', color: 'var(--success)' }
  if (score >= 55) return { label: 'Moderate', color: 'var(--primary)' }
  if (score >= 40) return { label: 'Watchlist', color: 'var(--warning)' }
  return { label: 'Low confidence', color: 'var(--danger)' }
}

const returnTone = (value) => {
  if (value === null || value === undefined) return 'var(--text-3)'
  return Number(value) >= 0 ? 'var(--success)' : 'var(--danger)'
}

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
  const [terminal, setTerminal] = useState(null)

  useEffect(() => {
    api.get('/research/years')
      .then(({ data }) => {
        setYears(data.years)
        setYear(data.years[data.years.length - 1])
      })
      .catch((e) => setError(e?.response?.data?.detail || 'Failed to load years'))

    api.get('/research/dashboard')
      .then(({ data }) => setDashboard(data))
      .catch(() => {})

    Promise.all([researchApi.summary(), researchApi.benchmark(), researchApi.diagnostics()])
      .then(([s, b, d]) => setTerminal({
        ctx: s.data?.context || {},
        bench: b.data || {},
        diag: d.data?.diagnostics || {},
      }))
      .catch(() => {})
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
    () => (overview?.companies || [])
      .filter((c) => c.fundamental_score != null && c.realized_return != null)
      .map((c) => ({ ...c, x: c.fundamental_score, y: c.realized_return })),
    [overview],
  )

  const topCompany = rows[0]
  const v = dashboard?.validation
  const benchOk = terminal?.bench?.available ?? dashboard?.benchmark?.available
  const featureCount = terminal?.ctx?.feature_count
  const correctedLoaded = terminal?.ctx?.corrected_yearly_financials?.available
  const weak = terminal?.diag?.weak_backtest

  if (error) return <EmptyState icon={AlertTriangle} title="Research data unavailable" description={String(error)} />

  return (
    <div className="tfx tfx-enter" style={styles.page}>
      <TerminalFx />
      <section style={styles.hero}>
        <div style={styles.heroGlow} />
        <div style={styles.heroContent}>
          <div className="tfx-kicker" style={styles.kicker}>
            <Sparkles size={13} />
            Score Explorer
          </div>

          <div style={styles.heroMain}>
            <div>
              <h1 style={styles.title}>Research Score vs Realized Performance</h1>
              <p style={styles.subtitle}>
                Diagnostic view of how the fundamental score aligned with realized same-year returns.
                The project’s actual modeling task remains T → T+1 research, not investment advice.
              </p>
            </div>

            <select
              value={year || ''}
              onChange={(e) => setYear(Number(e.target.value))}
              style={styles.yearSelect}
            >
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </div>

          <div style={styles.heroStats}>
            <HeroStat icon={ShieldCheck} label="Validated features" value={featureCount ?? '—'} sub="17 → 32" tone="good" />
            <HeroStat icon={BarChart3} label="BIST100 benchmark" value={benchOk ? 'Available' : 'Missing'} sub="excess return enabled" tone={benchOk ? 'good' : 'warn'} />
            <HeroStat icon={Activity} label="Corrected financials" value={correctedLoaded ? 'Loaded' : 'Pending'} sub="income & profitability" tone={correctedLoaded ? 'good' : 'warn'} />
            <HeroStat icon={weak ? TrendingDown : TrendingUp} label="Backtest signal" value={weak ? 'Weak' : 'Stable'} sub="honest diagnostic" tone={weak ? 'bad' : 'good'} />
          </div>
        </div>
      </section>

      <section style={styles.explainCard}>
        <b style={{ color: 'var(--text-1)' }}>What this page means:</b>{' '}
        Every company receives a research score for every year. The chart checks whether that score aligned
        with the realized return in the same year. Some years align positively, some years are noisy or inverse.
        That is a diagnostic finding, not a broken system and not a future prediction.
      </section>

      <section style={styles.qualityGrid}>
        <InsightCard
          label="Mean rank correlation"
          value={v ? fmt(v.mean_spearman, 3) : '—'}
          sub="all years · score vs same-year return"
          icon={Activity}
        />
        <InsightCard
          label="Positive alignment years"
          value={v ? (v.years_score_worked.join(', ') || 'none') : '—'}
          sub="score moved with realized returns"
          icon={TrendingUp}
        />
        <InsightCard
          label="Noisy / inverse years"
          value={v ? (v.years_score_failed.join(', ') || 'none') : '—'}
          sub="relationship was weak, not system failure"
          icon={TrendingDown}
        />
        <InsightCard
          label="Companies in selected year"
          value={overview?.count ?? '—'}
          sub={`BIST100: ${overview?.bist100_return != null ? pct(overview.bist100_return) : (benchOk ? 'available' : 'missing')}`}
          icon={BarChart3}
        />
      </section>

      <section style={styles.mainGrid}>
        <Card style={styles.chartCard}>
          <div style={styles.cardHeader}>
            <div>
              <h2 style={styles.cardTitle}>Score vs Realized Return — {year || ''}</h2>
              <p style={styles.cardSub}>Each dot is one company. Click a dot to inspect the company.</p>
            </div>
            <div style={styles.legend}>
              <span style={styles.legendDotSelected} /> Selected
              <span style={styles.legendDot} /> Company
            </div>
          </div>

          <div style={styles.chartBox}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 18, right: 26, bottom: 44, left: 18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(200, 211, 202, 0.12)" />
                <XAxis
                  type="number"
                  dataKey="x"
                  name="Fundamental Score"
                  domain={[0, 100]}
                  label={{ value: 'Fundamental Score', position: 'bottom', fill: 'var(--text-3)', dy: 20 }}
                  stroke="var(--text-3)"
                  fontSize={11}
                  tickLine={false}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  name="Realized Return %"
                  stroke="var(--text-3)"
                  fontSize={11}
                  tickLine={false}
                  label={{ value: 'Realized Return %', angle: -90, position: 'insideLeft', fill: 'var(--text-3)', dx: -6 }}
                />
                <ZAxis range={[76, 76]} />
                <ReferenceLine y={0} stroke="rgba(200, 211, 202, 0.35)" />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ payload }) => {
                    if (!payload?.length) return null
                    const d = payload[0].payload
                    return (
                      <div style={styles.tooltip}>
                        <b>{d.ticker}</b>
                        <div>Score {fmt(d.x)} · Return {pct(d.y)}</div>
                        <div>score #{d.score_rank} · return #{d.return_rank}</div>
                      </div>
                    )
                  }}
                />
                <Scatter data={scatter} onClick={(d) => setSelected(d.ticker)}>
                  {scatter.map((d) => (
                    <Cell
                      key={d.ticker}
                      fill={d.ticker === selected ? 'var(--primary)' : 'rgba(200, 211, 202, 0.72)'}
                      opacity={d.ticker === selected ? 1 : 0.58}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card style={styles.detailCard}>
          {detail ? <CompanyDetail d={detail} /> : <EmptyState icon={Search} title="Select a company" description="Click a dot or a company card." />}
        </Card>
      </section>

      <Card style={styles.companySection}>
        <div style={styles.companyHeader}>
          <div>
            <h2 style={styles.cardTitle}>Company universe — {year || ''}</h2>
            <p style={styles.cardSub}>
              Ranked by selected metric. This replaces the old spreadsheet-style table with a presentation-ready research list.
            </p>
          </div>

          <div style={styles.companyControls}>
            <div style={styles.searchBox}>
              <Search size={15} color="var(--text-3)" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter ticker"
                style={styles.searchInput}
              />
            </div>

            <select value={sortKey} onChange={(e) => setSortKey(e.target.value)} style={styles.sortSelect}>
              <option value="fundamental_score">Sort by score</option>
              <option value="market_score">Sort by market score</option>
              <option value="realized_return">Sort by return</option>
              <option value="score_rank">Sort by score rank</option>
              <option value="return_rank">Sort by return rank</option>
            </select>
          </div>
        </div>

        {loading ? (
          <div style={styles.loading}>Loading companies…</div>
        ) : (
          <div style={styles.companyGrid}>
            {rows.map((c) => (
              <CompanyCard
                key={c.ticker}
                company={c}
                active={c.ticker === selected}
                onClick={() => setSelected(c.ticker)}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

function HeroStat({ icon: Icon, label, value, sub, tone }) {
  const color = tone === 'good' ? 'var(--success)' : tone === 'bad' ? 'var(--danger)' : 'var(--warning)'
  return (
    <div style={styles.heroStat}>
      <div style={{ ...styles.heroIcon, color }}>
        <Icon size={18} />
      </div>
      <div>
        <div style={styles.heroStatLabel}>{label}</div>
        <div style={{ ...styles.heroStatValue, color }}>{value}</div>
        <div style={styles.heroStatSub}>{sub}</div>
      </div>
    </div>
  )
}

function InsightCard({ icon: Icon, label, value, sub }) {
  return (
    <div style={styles.insightCard}>
      <div style={styles.insightTop}>
        <div style={styles.insightIcon}><Icon size={18} /></div>
        <div style={styles.insightLabel}>{label}</div>
      </div>
      <div style={styles.insightValue}>{value}</div>
      <div style={styles.insightSub}>{sub}</div>
    </div>
  )
}

function CompanyDetail({ d }) {
  const profit = d.profit_status || {}
  const tone = scoreTone(Number(d.fundamental_score || 0))

  return (
    <div style={styles.detailWrap}>
      <div style={styles.detailTop}>
        <div>
          <div style={styles.detailTicker}>{d.ticker}</div>
          <div style={styles.detailYear}>{d.year}</div>
        </div>
        <div style={{ ...styles.statusPill, borderColor: tone.color, color: tone.color }}>
          {tone.label}
        </div>
      </div>

      <div>
        <div style={styles.detailScoreRow}>
          <span>Fundamental score</span>
          <b>{fmt(d.fundamental_score)}</b>
        </div>
        <div style={styles.scoreTrack}>
          <div style={{ ...styles.scoreFill, width: `${Math.max(0, Math.min(100, d.fundamental_score || 0))}%` }} />
        </div>
      </div>

      <div style={styles.miniGrid}>
        <Mini label="Realized return" value={d.realized_return != null ? `${d.realized_return.toFixed(1)}%` : '—'} strong color={returnTone(d.realized_return)} />
        <Mini label="Return rank" value={`${d.return_rank ?? '—'} / ${d.total_companies}`} />
        <Mini label="Score rank" value={`${d.score_rank ?? '—'} / ${d.total_companies}`} />
        <Mini label="Market score" value={fmt(d.market_score)} />
        <Mini label="vs BIST100" value={d.excess_vs_bist100 != null ? `${d.excess_vs_bist100.toFixed(1)}%` : 'n/a'} />
        <Mini label="Gap to best" value={d.gap_to_best != null ? `${d.gap_to_best.toFixed(1)}%` : '—'} />
      </div>

      <div style={styles.chipWrap}>
        {Object.entries(profit).map(([k, val]) => (
          <Chip key={k} color={val === true ? 'success' : val === false ? 'danger' : 'default'}>
            {k.replace(/_positive/, '').replace(/_/g, ' ')}: {val === null ? 'n/a' : val ? '✓' : '✗'}
          </Chip>
        ))}
      </div>

      <div style={styles.bestLine}>
        <Trophy size={15} />
        Best {d.year}: <b>{d.best_performer?.ticker}</b> ({fmt(d.best_performer?.return)}%)
      </div>

      <div>
        <div style={styles.breakdownTitle}>Score breakdown by category</div>
        {(d.score_breakdown || []).map((c) => (
          <div key={c.category} style={styles.breakdownRow}>
            <span style={styles.breakdownLabel}>{c.category}</span>
            <div style={styles.breakdownTrack}>
              <div style={{ ...styles.breakdownFill, width: `${Math.max(0, Math.min(100, c.category_score ?? 0))}%` }} />
            </div>
            <span style={styles.breakdownValue}>{c.category_score != null ? c.category_score.toFixed(0) : '—'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function Mini({ label, value, strong, color }) {
  return (
    <div style={styles.mini}>
      <div style={styles.miniLabel}>{label}</div>
      <div style={{ ...styles.miniValue, fontSize: strong ? 17 : 15, color: color || 'var(--text-1)' }}>{value}</div>
    </div>
  )
}

function CompanyCard({ company, active, onClick }) {
  const score = Number(company.fundamental_score || 0)
  const tone = scoreTone(score)
  const outperformed = company.excess_vs_bist100 != null ? company.excess_vs_bist100 >= 0 : null

  return (
    <button type="button" onClick={onClick} className="tfx-card" style={{ ...styles.companyCard, ...(active ? styles.companyCardActive : {}) }}>
      <div style={styles.companyCardTop}>
        <div>
          <div style={styles.rankText}>#{company.score_rank ?? '—'}</div>
          <div style={styles.companyTicker}>{company.ticker}</div>
        </div>
        <div style={{ ...styles.statusPillSmall, color: tone.color, borderColor: tone.color }}>
          {tone.label}
        </div>
      </div>

      <div style={styles.companyMetricRow}>
        <span>Research score</span>
        <b>{fmt(company.fundamental_score)}</b>
      </div>
      <div style={styles.companyScoreTrack}>
        <div style={{ ...styles.companyScoreFill, width: `${Math.max(0, Math.min(100, score))}%` }} />
      </div>

      <div style={styles.companyBottom}>
        <div>
          <span style={styles.companyBottomLabel}>Return</span>
          <b style={{ color: returnTone(company.realized_return) }}>{pct(company.realized_return)}</b>
        </div>
        <div>
          <span style={styles.companyBottomLabel}>Market</span>
          <b>{fmt(company.market_score)}</b>
        </div>
        <div>
          <span style={styles.companyBottomLabel}>Benchmark</span>
          <b style={{ color: outperformed === true ? 'var(--success)' : outperformed === false ? 'var(--danger)' : 'var(--text-3)' }}>
            {outperformed === null ? 'n/a' : outperformed ? 'Beat' : 'Below'}
          </b>
        </div>
      </div>
    </button>
  )
}

const styles = {
  page: {
    maxWidth: 1480,
    margin: '0 auto',
    padding: 'clamp(16px, 2vw, 28px) clamp(12px, 2.4vw, 34px) 64px',
    display: 'flex',
    flexDirection: 'column',
    gap: 22,
  },
  hero: {
    position: 'relative',
    overflow: 'hidden',
    border: '1px solid rgba(200, 211, 202, 0.18)',
    borderRadius: 28,
    background: 'linear-gradient(135deg, rgba(14, 20, 19, 0.96), rgba(12, 17, 15, 0.42))',
    boxShadow: '0 26px 80px rgba(0, 0, 0, 0.28)',
  },
  heroGlow: {
    position: 'absolute',
    inset: -120,
    background: 'radial-gradient(circle at 20% 20%, rgba(200, 163, 90, 0.20), transparent 32%), radial-gradient(circle at 85% 10%, rgba(77, 165, 131, 0.14), transparent 30%)',
    pointerEvents: 'none',
  },
  heroContent: {
    position: 'relative',
    padding: 30,
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
  },
  kicker: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    width: 'fit-content',
    color: 'var(--primary)',
    fontWeight: 800,
    letterSpacing: '.12em',
    textTransform: 'uppercase',
    fontSize: 12,
  },
  heroMain: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 28,
    alignItems: 'flex-start',
  },
  title: {
    margin: 0,
    fontSize: 'clamp(30px, 3.2vw, 48px)',
    lineHeight: 1.04,
    letterSpacing: '-0.04em',
    color: 'var(--text-1)',
  },
  subtitle: {
    margin: '14px 0 0',
    maxWidth: 900,
    color: 'var(--text-2)',
    fontSize: 15,
    lineHeight: 1.7,
  },
  yearSelect: {
    background: 'rgba(14, 20, 19, 0.88)',
    color: 'var(--text-1)',
    border: '1px solid rgba(200, 211, 202, 0.28)',
    borderRadius: 14,
    padding: '11px 16px',
    fontSize: 14,
    outline: 'none',
  },
  heroStats: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))',
    gap: 14,
  },
  heroStat: {
    minHeight: 112,
    padding: 18,
    borderRadius: 20,
    background: 'rgba(14, 20, 19, 0.66)',
    border: '1px solid rgba(200, 211, 202, 0.16)',
    display: 'flex',
    gap: 14,
    alignItems: 'flex-start',
  },
  heroIcon: {
    width: 38,
    height: 38,
    borderRadius: 14,
    background: 'rgba(255,255,255,0.06)',
    display: 'grid',
    placeItems: 'center',
    flexShrink: 0,
  },
  heroStatLabel: {
    color: 'var(--text-3)',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '.08em',
    fontWeight: 800,
  },
  heroStatValue: {
    marginTop: 6,
    fontSize: 24,
    fontWeight: 900,
    letterSpacing: '-0.03em',
  },
  heroStatSub: {
    marginTop: 3,
    color: 'var(--text-3)',
    fontSize: 12,
  },
  explainCard: {
    padding: '16px 20px',
    borderRadius: 18,
    border: '1px solid rgba(77, 165, 131, 0.18)',
    background: 'linear-gradient(135deg, rgba(77, 165, 131, 0.10), rgba(14, 20, 19, 0.78))',
    color: 'var(--text-2)',
    lineHeight: 1.7,
    fontSize: 14,
  },
  qualityGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
    gap: 16,
  },
  insightCard: {
    padding: 20,
    borderRadius: 22,
    background: 'rgba(14, 20, 19, 0.74)',
    border: '1px solid rgba(200, 211, 202, 0.18)',
    boxShadow: '0 18px 48px rgba(0, 0, 0, 0.16)',
  },
  insightTop: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
  },
  insightIcon: {
    width: 34,
    height: 34,
    display: 'grid',
    placeItems: 'center',
    borderRadius: 12,
    background: 'rgba(200, 163, 90, 0.12)',
    color: 'var(--primary)',
  },
  insightLabel: {
    color: 'var(--text-3)',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '.08em',
    fontWeight: 800,
  },
  insightValue: {
    marginTop: 16,
    fontSize: 28,
    lineHeight: 1.05,
    color: 'var(--text-1)',
    fontWeight: 900,
    letterSpacing: '-0.04em',
  },
  insightSub: {
    marginTop: 8,
    color: 'var(--text-3)',
    fontSize: 12.5,
    lineHeight: 1.45,
  },
  mainGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
    gap: 22,
    alignItems: 'stretch',
  },
  chartCard: {
    padding: 0,
    overflow: 'hidden',
  },
  detailCard: {
    padding: 0,
    overflow: 'hidden',
  },
  cardHeader: {
    padding: '24px 26px 6px',
    display: 'flex',
    justifyContent: 'space-between',
    gap: 18,
    alignItems: 'flex-start',
  },
  cardTitle: {
    margin: 0,
    color: 'var(--text-1)',
    fontSize: 23,
    letterSpacing: '-0.035em',
  },
  cardSub: {
    margin: '7px 0 0',
    color: 'var(--text-3)',
    fontSize: 13.5,
    lineHeight: 1.5,
  },
  legend: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    color: 'var(--text-3)',
    fontSize: 12,
    whiteSpace: 'nowrap',
  },
  legendDotSelected: {
    width: 9,
    height: 9,
    borderRadius: 99,
    background: 'var(--primary)',
    display: 'inline-block',
  },
  legendDot: {
    width: 9,
    height: 9,
    borderRadius: 99,
    background: 'rgba(200, 211, 202, 0.72)',
    display: 'inline-block',
    marginLeft: 8,
  },
  chartBox: {
    height: 540,
    padding: '2px 14px 18px',
  },
  tooltip: {
    background: 'rgba(14, 20, 19, 0.96)',
    border: '1px solid rgba(200, 211, 202, 0.24)',
    borderRadius: 12,
    padding: '10px 12px',
    color: 'var(--text-1)',
    fontSize: 12,
    boxShadow: '0 18px 45px rgba(0,0,0,.28)',
  },
  detailWrap: {
    display: 'flex',
    flexDirection: 'column',
    gap: 20,
    padding: 26,
  },
  detailTop: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 18,
    alignItems: 'flex-start',
  },
  detailTicker: {
    fontSize: 28,
    fontWeight: 900,
    color: 'var(--text-1)',
    letterSpacing: '-0.04em',
  },
  detailYear: {
    marginTop: 2,
    color: 'var(--text-3)',
    fontSize: 13,
  },
  statusPill: {
    border: '1px solid',
    borderRadius: 999,
    padding: '8px 12px',
    fontSize: 12,
    fontWeight: 800,
    background: 'rgba(255,255,255,0.04)',
  },
  detailScoreRow: {
    display: 'flex',
    justifyContent: 'space-between',
    color: 'var(--text-2)',
    fontSize: 14,
    marginBottom: 8,
  },
  scoreTrack: {
    height: 12,
    borderRadius: 999,
    background: 'rgba(8, 11, 10, 0.58)',
    overflow: 'hidden',
  },
  scoreFill: {
    height: '100%',
    borderRadius: 999,
    background: 'linear-gradient(90deg, var(--primary), rgba(77, 165, 131, 0.95))',
  },
  miniGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
    gap: 10,
  },
  mini: {
    padding: '12px 13px',
    background: 'rgba(8, 11, 10, 0.32)',
    border: '1px solid rgba(200, 211, 202, 0.14)',
    borderRadius: 14,
  },
  miniLabel: {
    color: 'var(--text-3)',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '.06em',
    marginBottom: 6,
  },
  miniValue: {
    fontWeight: 850,
  },
  chipWrap: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
  },
  bestLine: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
    color: 'var(--text-2)',
    fontSize: 13,
  },
  breakdownTitle: {
    fontSize: 13,
    color: 'var(--text-3)',
    marginBottom: 10,
  },
  breakdownRow: {
    display: 'grid',
    gridTemplateColumns: '108px 1fr 34px',
    alignItems: 'center',
    gap: 10,
    marginBottom: 9,
  },
  breakdownLabel: {
    color: 'var(--text-2)',
    fontSize: 12.5,
  },
  breakdownTrack: {
    height: 9,
    background: 'rgba(8, 11, 10, 0.55)',
    borderRadius: 999,
    overflow: 'hidden',
  },
  breakdownFill: {
    height: '100%',
    borderRadius: 999,
    background: 'linear-gradient(90deg, var(--primary), #c8a35a)',
  },
  breakdownValue: {
    color: 'var(--text-2)',
    fontSize: 12,
    textAlign: 'right',
  },
  companySection: {
    padding: 26,
  },
  companyHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 22,
    alignItems: 'flex-start',
    marginBottom: 22,
  },
  companyControls: {
    display: 'flex',
    gap: 10,
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
  },
  searchBox: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    minWidth: 190,
    background: 'rgba(8, 11, 10, 0.38)',
    border: '1px solid rgba(200, 211, 202, 0.18)',
    borderRadius: 13,
    padding: '9px 11px',
  },
  searchInput: {
    border: 0,
    outline: 'none',
    background: 'transparent',
    color: 'var(--text-1)',
    width: '100%',
    fontSize: 13,
  },
  sortSelect: {
    background: 'rgba(8, 11, 10, 0.38)',
    color: 'var(--text-1)',
    border: '1px solid rgba(200, 211, 202, 0.18)',
    borderRadius: 13,
    padding: '10px 12px',
    fontSize: 13,
    outline: 'none',
  },
  loading: {
    padding: 30,
    color: 'var(--text-3)',
  },
  companyGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(270px, 1fr))',
    gap: 14,
  },
  companyCard: {
    textAlign: 'left',
    border: '1px solid rgba(200, 211, 202, 0.14)',
    borderRadius: 20,
    background: 'linear-gradient(180deg, rgba(14, 20, 19, 0.78), rgba(8, 11, 10, 0.34))',
    padding: 17,
    color: 'var(--text-1)',
    cursor: 'pointer',
    transition: 'transform .18s ease, border-color .18s ease, box-shadow .18s ease, background .18s ease',
  },
  companyCardActive: {
    borderColor: 'rgba(200, 163, 90, 0.65)',
    boxShadow: '0 18px 52px rgba(200, 163, 90, 0.16), inset 0 1px 0 rgba(255,255,255,0.08)',
    background: 'linear-gradient(180deg, rgba(200, 163, 90, 0.12), rgba(14, 20, 19, 0.78))',
  },
  companyCardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 10,
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  rankText: {
    color: 'var(--text-3)',
    fontSize: 12,
    marginBottom: 4,
  },
  companyTicker: {
    fontSize: 22,
    fontWeight: 900,
    letterSpacing: '-0.04em',
  },
  statusPillSmall: {
    border: '1px solid',
    borderRadius: 999,
    padding: '6px 9px',
    fontSize: 11,
    fontWeight: 800,
    background: 'rgba(255,255,255,0.04)',
    whiteSpace: 'nowrap',
  },
  companyMetricRow: {
    display: 'flex',
    justifyContent: 'space-between',
    color: 'var(--text-2)',
    fontSize: 13,
    marginBottom: 8,
  },
  companyScoreTrack: {
    height: 9,
    borderRadius: 999,
    background: 'rgba(8, 11, 10, 0.62)',
    overflow: 'hidden',
    marginBottom: 16,
  },
  companyScoreFill: {
    height: '100%',
    borderRadius: 999,
    background: 'linear-gradient(90deg, var(--primary), rgba(77, 165, 131, 0.95))',
  },
  companyBottom: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: 8,
  },
  companyBottomLabel: {
    display: 'block',
    color: 'var(--text-3)',
    fontSize: 10.5,
    textTransform: 'uppercase',
    letterSpacing: '.06em',
    marginBottom: 4,
  },
}
