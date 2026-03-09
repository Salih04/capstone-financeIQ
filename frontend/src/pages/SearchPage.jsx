import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, LayoutGrid, List, Building2, ChevronRight, Sparkles, ArrowUpDown, Bot, Filter } from 'lucide-react'
import api from '../api/client'
import { SectionHeader, ScoreBadge, GhostButton, Card, EmptyState, Skeleton } from '../components/ui'

// AI keyword → sector_code mapping
const AI_SECTOR_MAP = {
  banking: ['BANKACILIK'], bank: ['BANKACILIK'],
  energy: ['ENERJI', 'PETROKIMYA'], oil: ['PETROKIMYA', 'ENERJI'], petroleum: ['PETROKIMYA'],
  tech: ['YAZILIM', 'TEKNOLOJI', 'ELEKTRONIK'], technology: ['YAZILIM', 'TEKNOLOJI', 'ELEKTRONIK'],
  software: ['YAZILIM'], electronics: ['ELEKTRONIK'],
  retail: ['PERAKENDE', 'ETICARET'], ecommerce: ['ETICARET'],
  automotive: ['OTOMOTIV'], auto: ['OTOMOTIV'], car: ['OTOMOTIV'],
  airline: ['HAVACILIK'], aviation: ['HAVACILIK'], aerospace: ['HAVACILIK'],
  steel: ['DEMIR_CELIK'], iron: ['DEMIR_CELIK'],
  cement: ['CIMENTO'],
  food: ['GIDA'], beverage: ['GIDA'],
  telecom: ['TELEKOM'], telecommunications: ['TELEKOM'],
  glass: ['CAM'],
  defense: ['SAVUNMA'],
  pharma: ['ILAC'], pharmaceutical: ['ILAC'], medicine: ['ILAC'],
  logistics: ['LOJISTIK'], shipping: ['LOJISTIK'],
  holding: ['HOLDING'], conglomerate: ['HOLDING'],
  textile: ['TEKSTIL'], fashion: ['TEKSTIL'], clothing: ['TEKSTIL'],
  construction: ['INSAAT'], building: ['INSAAT'], real: ['INSAAT'],
}

const SECTOR_LABELS = {
  BANKACILIK: 'Banking', ENERJI: 'Energy', PETROKIMYA: 'Petrochemicals',
  YAZILIM: 'Software', TEKNOLOJI: 'Technology', ELEKTRONIK: 'Electronics',
  PERAKENDE: 'Retail', ETICARET: 'E-Commerce', OTOMOTIV: 'Automotive',
  HAVACILIK: 'Aviation', DEMIR_CELIK: 'Steel & Iron', CIMENTO: 'Cement',
  GIDA: 'Food & Beverage', TELEKOM: 'Telecom', CAM: 'Glass',
  SAVUNMA: 'Defense', ILAC: 'Pharmaceuticals', LOJISTIK: 'Logistics',
  HOLDING: 'Holding', TEKSTIL: 'Textile', INSAAT: 'Construction',
}

const parseAISectors = (query) => {
  const lower = query.toLowerCase()
  const sectors = []
  const keywords = []
  for (const [kw, codes] of Object.entries(AI_SECTOR_MAP)) {
    if (lower.includes(kw)) {
      codes.forEach(c => { if (!sectors.includes(c)) sectors.push(c) })
      if (!keywords.includes(kw)) keywords.push(kw)
    }
  }
  return { sectors, keywords }
}

function CompanyCard({ company, onClick }) {
  const [h, setH] = useState(false)
  return (
    <div
      onClick={onClick}
      style={{
        background: h ? 'var(--surface-3)' : 'var(--surface-2)',
        border: `1px solid ${h ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: '18px 20px',
        cursor: 'pointer',
        transition: 'all 0.14s',
        transform: h ? 'translateY(-2px)' : 'none',
        boxShadow: h ? 'var(--shadow-md)' : 'none',
        position: 'relative',
        overflow: 'hidden',
      }}
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
    >
      {/* Accent gradient top strip */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 3, background: h ? 'linear-gradient(90deg, var(--primary), #6366f1)' : 'transparent', transition: 'background 0.2s' }} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(0,245,212,0.12), var(--surface-3))',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'var(--primary-hover)', fontWeight: 800, fontSize: 12,
        }}>
          {company.ticker?.substring(0, 2)}
        </div>
        {company.sector_code && (
          <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--primary)', background: 'rgba(0,245,212,0.08)', borderRadius: 5, padding: '3px 8px', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            {SECTOR_LABELS[company.sector_code] || company.sector_code}
          </span>
        )}
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--primary-hover)', letterSpacing: '-0.3px' }}>{company.ticker}</div>
      <div style={{ fontSize: 12.5, color: 'var(--text-3)', marginTop: 3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{company.company_name}</div>
      <div style={{ marginTop: 12, display: 'flex', alignItems: 'center', gap: 4, color: 'var(--primary)', fontSize: 12, fontWeight: 600 }}>
        View Profile <ChevronRight size={12} />
      </div>
    </div>
  )
}

function CompanyRow({ company, onClick }) {
  const [h, setH] = useState(false)
  return (
    <tr
      onClick={onClick}
      style={{ cursor: 'pointer', background: h ? 'var(--surface-3)' : 'transparent', transition: 'background 0.12s' }}
      onMouseEnter={() => setH(true)}
      onMouseLeave={() => setH(false)}
    >
      <td style={{ padding: '12px 16px', fontWeight: 700, color: 'var(--primary-hover)', fontSize: 14 }}>{company.ticker}</td>
      <td style={{ padding: '12px 16px', color: 'var(--text-2)', fontSize: 13.5 }}>{company.company_name}</td>
      <td style={{ padding: '12px 16px' }}>
        {company.sector_code ? (
          <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--primary)', background: 'rgba(0,245,212,0.08)', borderRadius: 5, padding: '3px 9px' }}>{SECTOR_LABELS[company.sector_code] || company.sector_code}</span>
        ) : <span style={{ color: 'var(--text-4)' }}>—</span>}
      </td>
      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
        <ChevronRight size={14} style={{ color: 'var(--text-4)' }} />
      </td>
    </tr>
  )
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('grid')
  const [sortBy, setSortBy] = useState('name')
  const [sectorFilter, setSectorFilter] = useState(null)
  const navigate = useNavigate()

  // Derived AI filter from current query
  const aiParsed = query.trim().length > 1 ? parseAISectors(query) : { sectors: [], keywords: [] }

  const availableSectors = useMemo(() =>
    [...new Set(results.map(c => c.sector_code).filter(Boolean))].sort(),
    [results]
  )

  const displayResults = useMemo(() => {
    let r = [...results]
    if (aiParsed.sectors.length > 0) {
      r = r.filter(c => aiParsed.sectors.includes(c.sector_code))
    }
    if (sectorFilter) {
      r = r.filter(c => c.sector_code === sectorFilter)
    }
    if (sortBy === 'name') r.sort((a, b) => (a.ticker || '').localeCompare(b.ticker || ''))
    else if (sortBy === 'name-desc') r.sort((a, b) => (b.ticker || '').localeCompare(a.ticker || ''))
    else if (sortBy === 'sector') r.sort((a, b) => (a.sector_code || '').localeCompare(b.sector_code || ''))
    return r
  }, [results, aiParsed.sectors, sectorFilter, sortBy])

  const search = useCallback(async (q) => {
    setLoading(true)
    try {
      const url = q.length >= 1 ? `/companies?q=${encodeURIComponent(q)}&limit=50` : '/companies?limit=50'
      const { data } = await api.get(url)
      setResults(data)
    } catch { /* ignore */ } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => search(query), 280)
    return () => clearTimeout(t)
  }, [query, search])

  const sectorCounts = useMemo(() => {
    const map = {}
    results.forEach(c => {
      if (c.sector_code) map[c.sector_code] = (map[c.sector_code] || 0) + 1
    })
    return map
  }, [results])

  return (
    <div style={{ maxWidth: 1200 }}>
      {/* ── Header with stats ── */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16, marginBottom: 20 }}>
          <div>
            <h1 style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--text-1)', letterSpacing: '-0.5px', margin: '0 0 4px' }}>Companies</h1>
            <p style={{ fontSize: 14, color: 'var(--text-3)', margin: 0 }}>Search and explore all financial entities in the database</p>
          </div>
          <button
            onClick={() => navigate('/ai-search')}
            style={{
              display: 'flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(135deg, rgba(0,245,212,0.12), rgba(99,102,241,0.12))',
              border: '1px solid rgba(0,245,212,0.3)',
              borderRadius: 12, padding: '10px 18px', cursor: 'pointer',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.transform = 'translateY(-1px)' }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(0,245,212,0.3)'; e.currentTarget.style.transform = 'none' }}
          >
            <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Bot size={12} color="#fff" />
            </div>
            <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary-hover)' }}>AI Search</span>
            <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'monospace', background: 'var(--surface-3)', borderRadius: 4, padding: '1px 6px' }}>
              {navigator.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+K
            </span>
          </button>
        </div>

        {/* Stats strip */}
        {!loading && results.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 0 }}>
            <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: '14px 18px' }}>
              <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.7, color: 'var(--text-3)', marginBottom: 4 }}>Total Companies</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--primary)', fontVariantNumeric: 'tabular-nums' }}>{results.length}</div>
            </div>
            <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: '14px 18px' }}>
              <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.7, color: 'var(--text-3)', marginBottom: 4 }}>Sectors</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--info)', fontVariantNumeric: 'tabular-nums' }}>{availableSectors.length}</div>
            </div>
            <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: '14px 18px' }}>
              <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.7, color: 'var(--text-3)', marginBottom: 4 }}>Showing</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--success)', fontVariantNumeric: 'tabular-nums' }}>{displayResults.length}</div>
            </div>
          </div>
        )}
      </div>

      {/* Toolbar */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: 440 }}>
          <Search size={14} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-3)', pointerEvents: 'none' }} />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by ticker, name, or sector keyword..."
            style={{
              width: '100%', boxSizing: 'border-box',
              background: 'var(--surface-2)',
              border: '1.5px solid var(--border-strong)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px 10px 38px',
              color: 'var(--text-1)',
              fontSize: 13.5,
              outline: 'none',
              transition: 'border-color 0.15s, box-shadow 0.15s',
            }}
            onFocus={e => { e.target.style.borderColor = 'var(--primary)'; e.target.style.boxShadow = '0 0 0 3px rgba(0,245,212,0.08)' }}
            onBlur={e => { e.target.style.borderColor = 'var(--border-strong)'; e.target.style.boxShadow = 'none' }}
          />
          {aiParsed.keywords.length > 0 && (
            <span style={{
              position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 10, fontWeight: 700, color: 'var(--primary)',
              background: 'var(--primary-subtle)', borderRadius: 5, padding: '2px 7px',
              pointerEvents: 'none',
            }}>
              <Sparkles size={9} /> AI
            </span>
          )}
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={e => setSortBy(e.target.value)}
          style={{
            fontSize: 12, fontWeight: 600, padding: '8px 10px', borderRadius: 'var(--radius-md)',
            border: '1.5px solid var(--border-strong)', background: 'var(--surface-2)',
            color: 'var(--text-2)', cursor: 'pointer', outline: 'none',
          }}
        >
          <option value="name">Sort: A → Z</option>
          <option value="name-desc">Sort: Z → A</option>
          <option value="sector">Sort: Sector</option>
        </select>

        {/* View toggle */}
        <div style={{ display: 'flex', gap: 4, background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-md)', padding: 3 }}>
          {[['grid', LayoutGrid], ['list', List]].map(([mode, Icon]) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                border: 'none', borderRadius: 8,
                background: viewMode === mode ? 'var(--surface-hover)' : 'transparent',
                color: viewMode === mode ? 'var(--text-1)' : 'var(--text-3)',
                padding: '6px 9px', cursor: 'pointer', display: 'flex', alignItems: 'center',
                transition: 'background 0.12s, color 0.12s',
              }}
            >
              <Icon size={15} />
            </button>
          ))}
        </div>
      </div>

      {/* ── Sector filter chips ── */}
      {!loading && availableSectors.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: aiParsed.keywords.length > 0 ? 10 : 16, alignItems: 'center' }}>
          <Filter size={12} style={{ color: 'var(--text-3)', marginRight: 2 }} />
          <button
            onClick={() => setSectorFilter(null)}
            style={{
              fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 20,
              border: `1.5px solid ${!sectorFilter ? 'var(--primary)' : 'var(--border-strong)'}`,
              background: !sectorFilter ? 'rgba(0,245,212,0.1)' : 'transparent',
              color: !sectorFilter ? 'var(--primary)' : 'var(--text-3)',
              cursor: 'pointer', transition: 'all 0.12s',
            }}
          >
            All ({results.length})
          </button>
          {availableSectors.map(code => {
            const active = sectorFilter === code
            const label = SECTOR_LABELS[code] || code
            return (
              <button
                key={code}
                onClick={() => setSectorFilter(active ? null : code)}
                style={{
                  fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 20,
                  border: `1.5px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                  background: active ? 'rgba(0,245,212,0.1)' : 'transparent',
                  color: active ? 'var(--primary)' : 'var(--text-3)',
                  cursor: 'pointer', transition: 'all 0.12s',
                }}
              >
                {label} ({sectorCounts[code] || 0})
              </button>
            )
          })}
        </div>
      )}

      {/* AI interpretation banner */}
      {!loading && aiParsed.keywords.length > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16,
          background: 'rgba(0,245,212,0.06)', border: '1px solid rgba(0,245,212,0.22)',
          borderRadius: 'var(--radius-md)', padding: '8px 14px',
        }}>
          <Sparkles size={13} style={{ color: 'var(--primary)', flexShrink: 0 }} />
          <span style={{ fontSize: 12.5, color: 'var(--text-2)' }}>
            <strong style={{ color: 'var(--primary)' }}>AI Search</strong>
            {' '}— detected <strong>{aiParsed.keywords.join(', ')}</strong> · showing {displayResults.length} {displayResults.length === 1 ? 'company' : 'companies'} in matching sector{aiParsed.sectors.length > 1 ? 's' : ''}
          </span>
          {displayResults.length === 0 && results.length > 0 && (
            <span style={{ fontSize: 11, color: 'var(--text-3)', marginLeft: 6 }}>(no sector match — showing all {results.length})</span>
          )}
        </div>
      )}

      {/* Loading skeletons */}
      {loading && (
        viewMode === 'grid' ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {[...Array(8)].map((_, i) => <Skeleton key={i} width="100%" height={130} radius={14} />)}
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...Array(6)].map((_, i) => <Skeleton key={i} width="100%" height={44} radius={10} />)}
          </div>
        )
      )}

      {/* Grid view */}
      {!loading && viewMode === 'grid' && displayResults.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {displayResults.map(c => (
            <CompanyCard key={c.id} company={c} onClick={() => navigate(`/companies/${c.id}`)} />
          ))}
        </div>
      )}

      {/* Table view */}
      {!loading && viewMode === 'list' && displayResults.length > 0 && (
        <Card>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: 'var(--surface-3)' }}>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Ticker</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Company</th>
                <th style={{ padding: '10px 16px', textAlign: 'left', fontSize: 11, fontWeight: 700, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8 }}>Sector</th>
                <th style={{ padding: '10px 16px', width: 40 }} />
              </tr>
            </thead>
            <tbody>
              {displayResults.map(c => (
                <CompanyRow key={c.id} company={c} onClick={() => navigate(`/companies/${c.id}`)} />
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Empty state */}
      {!loading && displayResults.length === 0 && (
        <EmptyState
          icon={Building2}
          title={sectorFilter ? `No companies in ${SECTOR_LABELS[sectorFilter] || sectorFilter}` : query ? `No results for "${query}"` : 'No companies found'}
          sub={sectorFilter ? 'Try selecting a different sector filter.' : query ? 'Try a different ticker or company name.' : 'Add companies to the database to get started.'}
        />
      )}
    </div>
  )
}
