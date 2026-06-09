import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, CheckCircle, Clock, ChevronDown, ChevronUp, Database, Sparkles } from 'lucide-react'
import api from '../api/client'
import { Card, Skeleton, EmptyState, SectionHeader } from '../components/ui'

const STATUS_STYLE = {
  success: { bg: 'rgba(16,185,129,0.1)', color: 'var(--success)', border: 'rgba(16,185,129,0.25)' },
  partial: { bg: 'rgba(245,158,11,0.1)', color: 'var(--warning)', border: 'rgba(245,158,11,0.25)' },
  failed: { bg: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: 'rgba(239,68,68,0.25)' },
  running: { bg: 'rgba(14,165,233,0.1)', color: 'var(--primary)', border: 'rgba(14,165,233,0.25)' },
  queued: { bg: 'var(--surface-3)', color: 'var(--text-3)', border: 'var(--border)' },
}

const SEVERITY_STYLE = {
  error: { bg: 'rgba(239,68,68,0.1)', color: 'var(--danger)', border: 'rgba(239,68,68,0.25)' },
  warning: { bg: 'rgba(245,158,11,0.1)', color: 'var(--warning)', border: 'rgba(245,158,11,0.25)' },
  info: { bg: 'rgba(99,102,241,0.1)', color: 'var(--info)', border: 'rgba(99,102,241,0.25)' },
}

function StatusBadge({ status }) {
  const st = STATUS_STYLE[status] || STATUS_STYLE.queued
  return (
    <span style={{ background: st.bg, color: st.color, border: `1px solid ${st.border}`, borderRadius: 'var(--radius-2xl)', padding: '2px 9px', fontSize: 11, fontWeight: 600 }}>
      {status}
    </span>
  )
}

const healthHero = { border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(58,199,139,0.13), rgba(85,194,195,0.08) 44%, var(--surface-2))', padding: 24, marginBottom: 24 }
const heroKicker = { display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '5px 11px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.7 }
const heroTitle = { margin: '14px 0 8px', color: 'var(--text-1)', fontSize: 'clamp(2rem, 5vw, 3.25rem)', lineHeight: 1, fontWeight: 900, maxWidth: 820 }
const heroSub = { color: 'var(--text-2)', fontSize: 14.5, lineHeight: 1.65, margin: 0, maxWidth: 760 }
const heroBadge = { display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 16, background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-strong)', borderRadius: 999, padding: '6px 10px', color: 'var(--text-2)', fontSize: 12, fontWeight: 800 }
function SeverityBadge({ severity }) {
  const st = SEVERITY_STYLE[severity] || SEVERITY_STYLE.info
  return (
    <span style={{ background: st.bg, color: st.color, border: `1px solid ${st.border}`, borderRadius: 'var(--radius-2xl)', padding: '2px 9px', fontSize: 11, fontWeight: 600 }}>
      {severity}
    </span>
  )
}

const durationStr = (job) => {
  if (!job.started_at || !job.finished_at) return '–'
  const diff = (new Date(job.finished_at) - new Date(job.started_at)) / 1000
  return diff < 60 ? `${diff.toFixed(1)}s` : `${(diff / 60).toFixed(1)}m`
}

export default function DataHealthPage() {
  const [dashboard, setDashboard] = useState(null)
  const [issues, setIssues] = useState([])
  const [filter, setFilter] = useState('all')
  const [selectedJob, setSelectedJob] = useState(null)
  const [jobDetail, setJobDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [apiError, setApiError] = useState(false)

  useEffect(() => {
    setApiError(false)
    Promise.all([
      api.get('/ingestion/dashboard').catch(() => null),
      api.get('/ingestion/issues?limit=50').catch(() => null),
    ])
      .then(([dashRes, issuesRes]) => {
        if (dashRes) setDashboard(dashRes.data)
        if (issuesRes) setIssues(Array.isArray(issuesRes.data) ? issuesRes.data : [])
        if (!dashRes && !issuesRes) setApiError(true)
      })
      .finally(() => setLoading(false))
  }, [])

  const loadJobDetail = async (jobId) => {
    if (selectedJob === jobId) { setSelectedJob(null); setJobDetail(null); return }
    setSelectedJob(jobId)
    try {
      const { data } = await api.get(`/ingestion/jobs/${jobId}`)
      setJobDetail(data)
    } catch { setJobDetail(null) }
  }

  const filteredIssues = filter === 'all' ? issues : issues.filter(i => i.severity === filter)

  const thS = { padding: '10px 14px', fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600, textAlign: 'left', borderBottom: '1px solid var(--border)' }
  const tdS = { padding: '10px 14px', fontSize: 13, color: 'var(--text-2)', borderTop: '1px solid var(--border)' }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <section style={healthHero}>
        <div style={heroKicker}><Sparkles size={15} /> Data Operations</div>
        <h1 style={heroTitle}>Pipeline health and ingestion history.</h1>
        <p style={heroSub}>Monitor data jobs, issue severity, and stale companies without mixing operational alerts with research conclusions.</p>
        <span style={heroBadge}><Database size={13} /> Audit workflow</span>
      </section>

      {/* API error banner */}
      {apiError && (
        <div style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 'var(--radius-md)', padding: '12px 16px', marginBottom: 20, color: 'var(--danger)', fontSize: 13 }}>
          ⚠ Could not load data health information. Make sure the backend is running and you are logged in.
        </div>
      )}

      {/* Stat cards */}
      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 24 }}>
          {[1,2,3,4].map(i => <Skeleton key={i} style={{ height: 76, borderRadius: 'var(--radius-lg)' }} />)}
        </div>
      ) : dashboard ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, marginBottom: 24 }}>
          {[
            {
              label: 'Last Ingestion', icon: <Clock size={16} />,
              value: dashboard.last_ingestion_at ? new Date(dashboard.last_ingestion_at).toLocaleDateString('en-US') : '–',
              color: 'var(--primary)', small: true,
            },
            {
              label: 'Failed Jobs (Last 20)', icon: <AlertTriangle size={16} />,
              value: dashboard.failed_jobs_last20 ?? '–',
              color: dashboard.failed_jobs_last20 > 0 ? 'var(--danger)' : 'var(--success)',
            },
            {
              label: 'Stale Companies', icon: <Activity size={16} />,
              value: dashboard.stale_companies ?? '–',
              color: dashboard.stale_companies > 0 ? 'var(--warning)' : 'var(--success)',
            },
            {
              label: 'Total Jobs', icon: <CheckCircle size={16} />,
              value: dashboard.total_jobs ?? '–',
              color: 'var(--text-1)',
            },
          ].map(stat => (
            <Card key={stat.label} style={{ padding: '1rem 1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: 'var(--text-3)' }}>
                {stat.icon}
                <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5 }}>{stat.label}</span>
              </div>
              <div style={{ fontSize: stat.small ? 14 : '1.6rem', fontWeight: 700, color: stat.color, fontVariantNumeric: 'tabular-nums' }}>
                {stat.value}
              </div>
            </Card>
          ))}
        </div>
      ) : null}

      {/* Jobs table */}
      <SectionHeader title="Recent Ingestion Jobs" icon={<Activity size={15} />} style={{ marginBottom: 12 }} />
      <Card style={{ padding: 0, overflow: 'hidden', marginBottom: 24 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--surface-1)' }}>
              {['#', 'Source', 'Status', 'Total', 'Success', 'Errors', 'Duration', 'Date', ''].map(h => (
                <th key={h} style={thS}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={9} style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-3)' }}>Loading...</td></tr>
            ) : !dashboard?.recent_jobs?.length ? (
              <tr><td colSpan={9} style={{ padding: '2rem', textAlign: 'center' }}>
                <EmptyState icon={<Activity size={24} />} title="No ingestion jobs yet" />
              </td></tr>
            ) : dashboard.recent_jobs.map(job => (
              <>
                <tr
                  key={job.id}
                  onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                >
                  <td style={tdS}>#{job.id}</td>
                  <td style={tdS}>{job.source_name || '–'}</td>
                  <td style={tdS}><StatusBadge status={job.job_status} /></td>
                  <td style={{ ...tdS, fontVariantNumeric: 'tabular-nums' }}>{job.items_total ?? '–'}</td>
                  <td style={{ ...tdS, color: 'var(--success)', fontVariantNumeric: 'tabular-nums' }}>{job.items_success ?? '–'}</td>
                  <td style={{ ...tdS, color: job.items_failed > 0 ? 'var(--danger)' : 'var(--text-2)', fontVariantNumeric: 'tabular-nums' }}>{job.items_failed ?? '–'}</td>
                  <td style={{ ...tdS, fontVariantNumeric: 'tabular-nums' }}>{durationStr(job)}</td>
                  <td style={tdS}>{job.started_at ? new Date(job.started_at).toLocaleString('en-US') : '–'}</td>
                  <td style={tdS}>
                    <button
                      onClick={() => loadJobDetail(job.id)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, padding: 0 }}
                    >
                      {selectedJob === job.id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                  </td>
                </tr>
                {selectedJob === job.id && jobDetail && (
                  <tr key={`${job.id}-detail`}>
                    <td colSpan={9} style={{ background: 'var(--bg)', padding: '12px 16px', borderTop: '1px solid var(--border)' }}>
                      {jobDetail.error_summary && (
                        <div style={{ color: 'var(--danger)', fontSize: 12, marginBottom: 8 }}>⚠ {jobDetail.error_summary}</div>
                      )}
                      {jobDetail.issues?.length > 0 ? (
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                          <thead>
                            <tr>{['Severity', 'Type', 'Company', 'Period', 'Message'].map(h => (
                              <th key={h} style={{ ...thS, fontSize: 10, background: 'var(--surface-1)' }}>{h}</th>
                            ))}</tr>
                          </thead>
                          <tbody>
                            {jobDetail.issues.map(iss => (
                              <tr key={iss.id}>
                                <td style={tdS}><SeverityBadge severity={iss.severity} /></td>
                                <td style={tdS}>{iss.issue_type}</td>
                                <td style={tdS}>{iss.company_id ?? '–'}</td>
                                <td style={tdS}>{iss.period ?? '–'}</td>
                                <td style={tdS}>{iss.issue_message}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      ) : (
                        <div style={{ color: 'var(--text-3)', fontSize: 12 }}>No issues recorded for this job.</div>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </Card>

      {/* Issues table */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <SectionHeader title="Data Quality Issues" icon={<AlertTriangle size={15} />} />
        <div style={{ display: 'flex', gap: 6 }}>
          {['all', 'error', 'warning', 'info'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                background: filter === f ? 'var(--primary-muted)' : 'var(--surface-2)',
                border: `1px solid ${filter === f ? 'var(--primary)' : 'var(--border)'}`,
                borderRadius: 'var(--radius-md)', padding: '4px 12px', fontSize: 12, fontWeight: 500,
                color: filter === f ? 'var(--primary)' : 'var(--text-3)', cursor: 'pointer',
              }}
            >
              {f === 'all' ? 'All' : f}
            </button>
          ))}
        </div>
      </div>
      <Card style={{ padding: 0, overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--surface-1)' }}>
              {['Severity', 'Type', 'Company', 'Period', 'Message', 'Detected'].map(h => <th key={h} style={thS}>{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {filteredIssues.length === 0 ? (
              <tr><td colSpan={6} style={{ padding: '2rem', textAlign: 'center' }}>
                <EmptyState icon={<CheckCircle size={24} />} title="No issues found" description="All data looks clean." />
              </td></tr>
            ) : filteredIssues.map(iss => (
              <tr
                key={iss.id}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
              >
                <td style={tdS}><SeverityBadge severity={iss.severity} /></td>
                <td style={tdS}>
                  <span style={{ background: 'var(--surface-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px', fontSize: 11 }}>
                    {iss.issue_type}
                  </span>
                </td>
                <td style={tdS}>{iss.company_id ?? '–'}</td>
                <td style={{ ...tdS, fontVariantNumeric: 'tabular-nums' }}>{iss.period ?? '–'}</td>
                <td style={{ ...tdS, maxWidth: 320, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{iss.issue_message}</td>
                <td style={tdS}>{iss.detected_at ? new Date(iss.detected_at).toLocaleString('en-US') : '–'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
