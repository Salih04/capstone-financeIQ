import { useState, useEffect, useRef, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitCompare, Play, X, ChevronRight, Trophy, Search, Filter, Zap } from 'lucide-react'
import api from '../api/client'
import { Card, getBand, Skeleton, EmptyState, GhostButton, SectionHeader } from '../components/ui'
import TerminalFx from '../components/TerminalFx'
const RANK_STYLES = [
  { color: '#c8a35a', label: '1' },
  { color: 'var(--text-2)', label: '2' },
  { color: '#a8674b', label: '3' },
]

const formatSectorCode = (value) => {
  if (!value) return ''
  return String(value)
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (m) => m.toUpperCase())
}

function generateQuarters() {
  const years = [2025, 2024, 2023, 2022, 2021, 2020]
  return years.map(y => `${y}/12`)
}
const ALL_QUARTERS = generateQuarters()
const ACTIVE_MODELS = ['elasticnet', 'random_forest']

function formatApiError(err, fallback = 'Request failed.') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail && typeof detail === 'object') {
    const msg = typeof detail.message === 'string' ? detail.message : fallback
    const warnings = Array.isArray(detail.warnings) ? detail.warnings : []
    return warnings.length ? `${msg} (${warnings.join(' | ')})` : msg
  }
  return fallback
}

export default function ComparePage() {
  const navigate = useNavigate()
  const [companies, setCompanies] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [period, setPeriod] = useState('')
  const [results, setResults] = useState(null)
  const [warnings, setWarnings] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [progressStep, setProgressStep] = useState('')
  const progressTimer = useRef(null)
  const [compLoading, setCompLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [sectorFilter, setSectorFilter] = useState(null)

  useEffect(() => {
    api.get('/companies?limit=200')
      .then(({ data }) => setCompanies(data || []))
      .catch(() => {})
      .finally(() => setCompLoading(false))
  }, [])

  // Pre-select companies passed from AI Search page
  useEffect(() => {
    const stored = sessionStorage.getItem('comparePreselect')
    if (stored) {
      try {
        const ids = JSON.parse(stored)
        if (Array.isArray(ids)) setSelected(new Set(ids))
      } catch {}
      sessionStorage.removeItem('comparePreselect')
    }
  }, [])

  const toggleSelect = (id) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 8) next.add(id)
      return next
    })
  }

  const STEPS = [
    { at: 8,  label: 'Loading financial statements…' },
    { at: 22, label: 'Computing financial ratios…' },
    { at: 40, label: 'Running scoring analysis…' },
    { at: 58, label: 'Normalising sector benchmarks…' },
    { at: 72, label: 'Ranking companies…' },
    { at: 85, label: 'Preparing results…' },
  ]

  const startProgress = () => {
    setProgress(0)
    setProgressStep(STEPS[0].label)
    let current = 0
    progressTimer.current = setInterval(() => {
      current += 1
      setProgress(current)
      const step = [...STEPS].reverse().find(s => current >= s.at)
      if (step) setProgressStep(step.label)
      if (current >= 85) clearInterval(progressTimer.current)
    }, 90)
  }

  const finishProgress = () => {
    clearInterval(progressTimer.current)
    setProgress(100)
    setProgressStep('Done!')
  }

  const runCompare = async () => {
    if (selected.size < 2) { setError('Please select at least 2 companies.'); return }
    setLoading(true)
    setError('')
    startProgress()
    try {
      const { data } = await api.post('/scoring/compare', {
        company_ids: Array.from(selected),
        period: period || null,
        selected_models: ACTIVE_MODELS,
      })
      finishProgress()
      await new Promise(r => setTimeout(r, 1200))
      setResults(data.items || [])
      setWarnings(data.warnings || [])
    } catch (e) {
      setError(formatApiError(e, 'Comparison failed.'))
    } finally {
      clearInterval(progressTimer.current)
      setLoading(false)
      setProgress(0)
    }
  }

  const filtered = companies.filter(c => {
    if (sectorFilter && c.sector_code !== sectorFilter) return false
    if (!search) return true
    return c.ticker?.toUpperCase().includes(search.toUpperCase())
      || c.company_name?.toLowerCase().includes(search.toLowerCase())
  })

  const availableSectors = useMemo(() =>
    [...new Set(companies.map(c => c.sector_code).filter(Boolean))].sort(),
    [companies]
  )

  const selectedCompanies = companies.filter(c => selected.has(c.id))
  const companyWarnings = warnings.filter(w =>

  w.toLowerCase().includes('excluded') || w.toLowerCase().includes('no computed metrics')

)

  return (
    <div className="tfx tfx-enter" style={{ maxWidth: 1040, margin: '0 auto', padding: '2.5rem 1.75rem' }}>
      <TerminalFx />

      {/* ── Loading overlay ── */}
      {loading && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 999,
          background: 'rgba(8,11,10,0.88)',
          backdropFilter: 'blur(6px)',
          display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center',
          gap: 0,
        }}>
          {/* Glow ring */}
          <div style={{
            width: 88, height: 88, borderRadius: '50%', marginBottom: 28,
            background: 'radial-gradient(circle, rgba(200,163,90,0.2) 0%, transparent 70%)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 40px rgba(200,163,90,0.25)',
          }}>
            <GitCompare size={36} color='var(--primary)' style={{ animation: 'spin 2s linear infinite' }} />
          </div>

          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-1)', marginBottom: 6 }}>
            Comparing Companies
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-3)', marginBottom: 20 }}>
            {selectedCompanies.map(c => c.ticker).join(' · ')}
          </div>

          {/* Bar track */}
          <div style={{
            width: 340, height: 6, borderRadius: 99,
            background: 'rgba(255,255,255,0.08)',
            overflow: 'hidden', marginBottom: 14,
          }}>
            <div style={{
              height: '100%', borderRadius: 99,
              width: `${progress}%`,
              background: 'linear-gradient(90deg, rgba(200,163,90,0.6) 0%, #C8A35A 100%)',
              boxShadow: '0 0 12px rgba(200,163,90,0.6)',
              transition: 'width 0.12s linear',
            }} />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', width: 340, marginBottom: 18 }}>
            <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{progressStep}</span>
            <span style={{ fontSize: 11, color: 'var(--primary)', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>
              {progress}%
            </span>
          </div>

          {/* Company chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center', maxWidth: 420 }}>
            {selectedCompanies.map(c => (
              <div key={c.id} style={{
                padding: '4px 12px', borderRadius: 99,
                background: 'rgba(200,163,90,0.08)',
                border: '1px solid rgba(200,163,90,0.25)',
                fontSize: 12, color: 'var(--primary)', fontWeight: 600,
              }}>
                {c.ticker}
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      {/* Header */}
      <div style={{ marginBottom: 24, position: 'relative', overflow: 'hidden', background: 'linear-gradient(135deg, rgba(200,163,90,0.13), rgba(77,165,131,0.08) 44%, var(--surface-2))', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-xl)', padding: '28px 32px' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 4, background: 'linear-gradient(180deg, var(--primary), var(--secondary))' }} />
        <div className="tfx-kicker" style={{ position: 'relative', display: 'inline-block', color: 'var(--text-3)', fontSize: 10.5, marginBottom: 10 }}>SIGNAL COMPARISON CONSOLE</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6, position: 'relative' }}>
          <div style={{ width: 40, height: 40, borderRadius: 4, background: 'linear-gradient(135deg, rgba(200,163,90,0.2), rgba(77,165,131,0.12))', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(200,163,90,0.25)' }}>
            <GitCompare size={18} color="var(--primary)" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-1)', margin: 0, letterSpacing: '-0.015em' }}>
              Company Comparison
            </h1>
            <p style={{ fontSize: 13, color: 'var(--text-3)', margin: 0 }}>
              Pick 2-8 companies for diagnostic comparison with identical settings and period. Research support only.
            </p>
          </div>
        </div>
        {selected.size > 0 && (
          <div style={{ display: 'flex', gap: 6, marginTop: 14, position: 'relative' }}>
            <Zap size={12} style={{ color: 'var(--primary)', marginTop: 4 }} />
            <span style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600 }}>
              {selected.size} selected
            </span>
            <span style={{ fontSize: 12, color: 'var(--text-3)' }}>— ready to compare</span>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))', gap: 20, alignItems: 'start' }}>
        {/* Left: company list */}
        <div>
          {/* Selected chips */}
          {selectedCompanies.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
              {selectedCompanies.map(c => (
                <div key={c.id} style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  background: 'var(--primary-muted)', border: '1px solid var(--primary)',
                  borderRadius: 'var(--radius-2xl)', padding: '4px 12px', fontSize: 12, color: 'var(--primary)',
                }}>
                  <span style={{ fontWeight: 600 }}>{c.ticker}</span>
                  <button
                    onClick={() => toggleSelect(c.id)}
                    style={{ background: 'none', border: 'none', padding: 0, cursor: 'pointer', color: 'var(--primary)', display: 'flex', lineHeight: 1 }}
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
              <div style={{ fontSize: 12, color: 'var(--text-3)', alignSelf: 'center' }}>
                {selected.size}/8 selected
              </div>
            </div>
          )}

          {/* Search */}
          <div style={{ position: 'relative', marginBottom: 8 }}>
            <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)', pointerEvents: 'none' }} />
            <input
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)', padding: '9px 12px 9px 34px',
                color: 'var(--text-1)', fontSize: 13, outline: 'none',
              }}
              placeholder="Search by ticker or name..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>

          {/* Sector filter chips */}
          {availableSectors.length > 0 && (
            <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', marginBottom: 10, alignItems: 'center' }}>
              <Filter size={11} style={{ color: 'var(--text-3)' }} />
              <button
                onClick={() => setSectorFilter(null)}
                className="tfx-chip"
                aria-pressed={!sectorFilter}
                style={{
                  fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em', padding: '3px 10px', borderRadius: 2,
                  border: `1px solid ${!sectorFilter ? 'var(--primary)' : 'var(--border-strong)'}`,
                  background: !sectorFilter ? 'rgba(200,163,90,0.12)' : 'transparent',
                  color: !sectorFilter ? 'var(--primary)' : 'var(--text-3)',
                  cursor: 'pointer',
                }}
              >
                All
              </button>
              {availableSectors.slice(0, 10).map(code => {
                const active = sectorFilter === code
                return (
                  <button
                    key={code}
                    onClick={() => setSectorFilter(active ? null : code)}
                    className="tfx-chip"
                    aria-pressed={active}
                    style={{
                      fontFamily: 'var(--font-mono)', fontSize: 10, letterSpacing: '0.06em', padding: '3px 10px', borderRadius: 2,
                      border: `1px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                      background: active ? 'rgba(200,163,90,0.12)' : 'transparent',
                      color: active ? 'var(--primary)' : 'var(--text-3)',
                      cursor: 'pointer',
                    }}
                  >
                    {code}
                  </button>
                )
              })}
            </div>
          )}

          {/* Company list */}
          <Card style={{ padding: 0, overflow: 'hidden', maxHeight: 440, overflowY: 'auto' }}>
            {compLoading ? (
              <div style={{ padding: '1rem' }}>
                {[1,2,3,4,5].map(i => <Skeleton key={i} style={{ height: 52, marginBottom: 6, borderRadius: 'var(--radius-md)' }} />)}
              </div>
            ) : filtered.length === 0 ? (
              <div style={{ padding: '2rem' }}>
                <EmptyState icon={<GitCompare size={28} />} title="No companies found" />
              </div>
            ) : filtered.map(c => {
              const isSelected = selected.has(c.id)
              return (
                <div
                  key={c.id}
                  onClick={() => toggleSelect(c.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px',
                    borderBottom: '1px solid var(--border)',
                    background: isSelected ? 'var(--primary-muted)' : 'transparent',
                    cursor: 'pointer', transition: 'background 0.15s',
                  }}
                  onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = 'var(--surface-hover)' }}
                  onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = 'transparent' }}
                >
                  {/* Checkbox */}
                  <div style={{
                    width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                    border: `2px solid ${isSelected ? 'var(--primary)' : 'var(--border-bright)'}`,
                    background: isSelected ? 'var(--primary)' : 'transparent',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: '#fff', fontSize: 11, fontWeight: 700,
                  }}>
                    {isSelected ? '✓' : ''}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: isSelected ? 'var(--primary)' : 'var(--text-1)' }}>
                      {c.ticker}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.company_name}
                    </div>
                  </div>
                  {c.sector_code && (
                    <span style={{ fontSize: 11, background: 'var(--surface-3)', color: 'var(--text-3)', borderRadius: 'var(--radius-sm)', padding: '2px 8px' }}>
                    {formatSectorCode(c.sector_code)}
                    </span>
                  )}
                </div>
              )
            })}
          </Card>
        </div>

        {/* Right: controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Card style={{ padding: '1.25rem' }}>
            <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 14, fontWeight: 600 }}>
              Analysis Settings
            </div>

            <div style={{
              marginBottom: 12, fontSize: 12, color: 'var(--text-2)',
              background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-md)', padding: '8px 10px',
            }}>
              <div style={{ fontWeight: 700, color: 'var(--primary)', marginBottom: 4 }}>Ensemble v1</div>
              <div>ElasticNet + RandomForest</div>
            </div>

            <div style={{ marginBottom: 12, fontSize: 11, color: 'var(--text-3)', lineHeight: 1.45 }}>
              Sector comparisons with fewer than 10 companies are anecdotal.
            </div>

            <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 6 }}>Period</label>
            <select
              value={period} onChange={e => setPeriod(e.target.value)}
              style={{
                width: '100%', boxSizing: 'border-box',
                background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
                borderRadius: 'var(--radius-md)', color: 'var(--text-1)', padding: '8px 12px',
                fontSize: 13, outline: 'none', marginBottom: 16,
              }}
            >
              <option value="">Latest available</option>
              {ALL_QUARTERS.map(q => (
                <option key={q} value={q}>{q}</option>
              ))}
            </select>

            {error && (
              <div style={{
                background: 'rgba(185,95,68,0.08)', border: '1px solid rgba(185,95,68,0.3)',
                borderRadius: 'var(--radius-md)', padding: '8px 12px', color: '#fca5a5',
                fontSize: 12, marginBottom: 12,
              }}>
                {error}
              </div>
            )}

            <button
              onClick={runCompare}
              disabled={selected.size < 2 || loading}
              className="tfx-press"
              style={{
                width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                background: selected.size < 2 ? 'var(--surface-3)' : 'var(--primary)',
                border: 'none', borderRadius: 2, padding: '12px 0',
                color: selected.size < 2 ? 'var(--text-3)' : '#0a0e0d',
                fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 12.5, letterSpacing: '0.08em',
                cursor: selected.size < 2 ? 'not-allowed' : 'pointer',
              }}
            >
              <Play size={15} />
              {loading ? 'COMPARING…' : `COMPARE ${selected.size} COMPANIES`}
            </button>

            {selected.size < 2 && (
              <div style={{ fontSize: 11, color: 'var(--text-3)', textAlign: 'center', marginTop: 8 }}>
              Select at least 2 companies
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Results */}
      {results && (
        <div style={{ marginTop: 28 }}>
          <SectionHeader
            title={`Comparison Results — ${results.length} Companies`}
            icon={<Trophy size={15} />}
            style={{ marginBottom: 16 }}
          />

        {companyWarnings.length > 0 && (
          <Card style={{ padding: '12px 16px', marginBottom: 16, border: '1px solid rgba(200,163,90,0.35)', background: 'rgba(200,163,90,0.08)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#c8a35a', marginBottom: 6 }}>Excluded companies</div>
            <div style={{ fontSize: 12, color: 'var(--text-2)', lineHeight: 1.5 }}>
              {companyWarnings.join(' · ')}
            </div>
          </Card>
        )}

          {/* Ranking cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12, marginBottom: 20 }}>
            {results.slice(0, 3).map((r, idx) => {
              const band = getBand(r.total_score)
              return (
                <Card
                  key={r.company_id}
                  hoverable
                  style={{ padding: '1.25rem', cursor: 'pointer', position: 'relative', overflow: 'hidden' }}
                  onClick={() => navigate(`/companies/${r.company_id}`)}
                >
                  <div style={{
                    position: 'absolute', top: -12, right: -12, width: 64, height: 64,
                    borderRadius: '50%', background: band.color, opacity: 0.08, pointerEvents: 'none'
                  }} />
                  <div style={{ fontSize: 22, marginBottom: 4 }}>
                    {idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'}
                  </div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--primary)', marginBottom: 2 }}>{r.ticker}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-3)', marginBottom: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.company_name}</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 800, color: band.color, fontVariantNumeric: 'tabular-nums' }}>
                    {r.total_score?.toFixed(1)}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-3)' }}>/100</div>
                </Card>
              )
            })}
          </div>

          {/* Full table */}
          <Card style={{ padding: 0, overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--surface-1)' }}>
                  {['#', 'Company', 'Score', 'Success Prob.', 'Period', ''].map((h, i) => (
                    <th key={i} style={{
                      padding: '10px 14px', fontSize: 11, color: 'var(--text-3)',
                      textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600,
                      textAlign: i <= 1 ? 'left' : 'right', borderBottom: '1px solid var(--border)',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((r, idx) => {
                  const band = getBand(r.total_score)
                  return (
                    <tr
                      key={r.company_id}
                      style={{ borderTop: '1px solid var(--border)' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <td style={{ padding: '12px 14px', width: 36 }}>
                        <span style={{
                          fontSize: 13, fontWeight: 700,
                          color: idx < 3 ? (RANK_STYLES[idx]?.color || 'var(--text-2)') : 'var(--text-3)'
                        }}>
                          {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}
                        </span>
                      </td>
                      <td style={{ padding: '12px 14px' }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--primary)' }}>{r.ticker}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-3)' }}>{r.company_name}</div>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <div style={{ fontSize: 15, fontWeight: 700, color: band.color, fontVariantNumeric: 'tabular-nums' }}>
                          {r.total_score?.toFixed(1)}
                        </div>
                        <div style={{ height: 4, borderRadius: 2, background: 'var(--surface-3)', marginTop: 4, width: 80, marginLeft: 'auto' }}>
                          <div style={{ height: '100%', width: `${Math.min(r.total_score || 0, 100)}%`, borderRadius: 2, background: band.color, transition: 'width 0.8s ease' }} />
                        </div>
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right', fontSize: 13, color: band.color, fontVariantNumeric: 'tabular-nums' }}>
                        {r.success_probability != null ? `${(r.success_probability * 100).toFixed(1)}%` : '—'}
                      </td>
                      <td style={{ padding: '12px 14px', textAlign: 'right', fontSize: 13, color: 'var(--text-2)' }}>{r.period || '—'}</td>
                      <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                        <GhostButton onClick={() => navigate(`/companies/${r.company_id}`)} style={{ padding: '5px 12px', fontSize: 12, gap: 4 }}>
                          Profile <ChevronRight size={12} />
                        </GhostButton>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </Card>

          {results.length > 0 && (
            <div style={{ marginTop: 14, fontSize: 13, color: 'var(--text-3)' }}>
              <span style={{ color: 'var(--primary)', fontWeight: 600 }}>{results[0].ticker}</span>
              {' '}scored highest ({results[0].total_score?.toFixed(1)}/100).
              {results.length > 1 && ` ${results[results.length - 1].ticker} ranked last with ${results[results.length - 1].total_score?.toFixed(1)}/100.`}
            </div>
          )}
        </div>
      )}

      <footer className="tfx-caveat">
        <span className="tfx-pulse" aria-hidden="true" />
        Side-by-side diagnostic comparison · Research only · Not investment advice
      </footer>
    </div>
  )
}
