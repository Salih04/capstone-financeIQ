import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Building2,
  ChevronRight,
  Filter,
  LayoutGrid,
  List,
  Search,
  Sparkles,
} from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState, Skeleton } from '../components/ui'

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

const formatSectorCode = (value) => {
  if (!value) return 'Unclassified'
  return SECTOR_LABELS[value] || String(value)
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, (m) => m.toUpperCase())
}

const parseAISectors = (query) => {
  const lower = query.toLowerCase()
  const sectors = []
  const keywords = []
  Object.entries(AI_SECTOR_MAP).forEach(([kw, codes]) => {
    if (!lower.includes(kw)) return
    codes.forEach((code) => {
      if (!sectors.includes(code)) sectors.push(code)
    })
    if (!keywords.includes(kw)) keywords.push(kw)
  })
  return { sectors, keywords }
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [viewMode, setViewMode] = useState('grid')
  const [sortBy, setSortBy] = useState('name')
  const [sectorFilter, setSectorFilter] = useState(null)
  const navigate = useNavigate()

  const aiParsed = query.trim().length > 1 ? parseAISectors(query) : { sectors: [], keywords: [] }

  const availableSectors = useMemo(
    () => [...new Set(results.map((c) => c.sector_code).filter(Boolean))].sort(),
    [results],
  )

  const sectorCounts = useMemo(() => {
    const counts = {}
    results.forEach((c) => {
      if (c.sector_code) counts[c.sector_code] = (counts[c.sector_code] || 0) + 1
    })
    return counts
  }, [results])

  const displayResults = useMemo(() => {
    let rows = [...results]
    if (aiParsed.sectors.length > 0) rows = rows.filter((c) => aiParsed.sectors.includes(c.sector_code))
    if (sectorFilter) rows = rows.filter((c) => c.sector_code === sectorFilter)
    if (sortBy === 'name') rows.sort((a, b) => (a.ticker || '').localeCompare(b.ticker || ''))
    if (sortBy === 'name-desc') rows.sort((a, b) => (b.ticker || '').localeCompare(a.ticker || ''))
    if (sortBy === 'sector') rows.sort((a, b) => (a.sector_code || '').localeCompare(b.sector_code || ''))
    return rows
  }, [results, aiParsed.sectors, sectorFilter, sortBy])

  const search = useCallback(async (q) => {
    setLoading(true)
    try {
      const url = q.length >= 1
        ? `/companies?q=${encodeURIComponent(q)}&limit=200`
        : '/companies?limit=200'
      const { data } = await api.get(url)
      setResults(Array.isArray(data) ? data : [])
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const t = setTimeout(() => search(query), 280)
    return () => clearTimeout(t)
  }, [query, search])

  return (
    <div style={styles.page}>
      <section style={styles.hero}>
        <div style={styles.heroTop}>
          <div>
            <div style={styles.kicker}>
              <Building2 size={15} />
              Company Directory
            </div>
            <h1 style={styles.title}>Research Universe</h1>
            <p style={styles.subtitle}>
              Search BIST companies by ticker, company name, or sector keyword. This directory routes
              to company profiles; research scoring lives in the dedicated Companies research page.
            </p>
          </div>

          <div style={styles.searchBox}>
            <Search size={17} style={styles.searchIcon} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search ticker, name, or sector..."
              style={styles.searchInput}
            />
            {aiParsed.keywords.length > 0 && (
              <span style={styles.aiChip}><Sparkles size={11} /> Sector match</span>
            )}
          </div>
        </div>

        {!loading && results.length > 0 && (
          <div style={styles.kpiGrid}>
            <HeroMetric label="Total Companies" value={results.length} />
            <HeroMetric label="Sectors" value={availableSectors.length} />
            <HeroMetric label="Showing" value={displayResults.length} />
          </div>
        )}
      </section>

      <section style={styles.toolbar}>
        <div style={styles.filterRow}>
          <Filter size={14} style={{ color: 'var(--text-3)' }} />
          <button
            onClick={() => setSectorFilter(null)}
            style={chipStyle(!sectorFilter)}
          >
            All ({results.length})
          </button>
          {availableSectors.map((code) => (
            <button
              key={code}
              onClick={() => setSectorFilter(sectorFilter === code ? null : code)}
              style={chipStyle(sectorFilter === code)}
            >
              {formatSectorCode(code)} ({sectorCounts[code] || 0})
            </button>
          ))}
        </div>

        <div style={styles.controls}>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={styles.select}>
            <option value="name">Sort: A to Z</option>
            <option value="name-desc">Sort: Z to A</option>
            <option value="sector">Sort: Sector</option>
          </select>
          <div style={styles.segment}>
            {[['grid', LayoutGrid], ['list', List]].map(([mode, Icon]) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                title={mode === 'grid' ? 'Grid view' : 'List view'}
                style={segmentButton(viewMode === mode)}
              >
                <Icon size={16} />
              </button>
            ))}
          </div>
        </div>
      </section>

      {aiParsed.keywords.length > 0 && (
        <div style={styles.interpretation}>
          <Sparkles size={14} />
          Detected sector intent from "{aiParsed.keywords.join(', ')}"; showing matching companies only.
        </div>
      )}

      {loading && (
        viewMode === 'grid' ? (
          <div style={styles.grid}>
            {[...Array(8)].map((_, i) => <Skeleton key={i} width="100%" height={156} radius={12} />)}
          </div>
        ) : (
          <div style={styles.listSkeleton}>
            {[...Array(6)].map((_, i) => <Skeleton key={i} width="100%" height={54} radius={10} />)}
          </div>
        )
      )}

      {!loading && viewMode === 'grid' && displayResults.length > 0 && (
        <div style={styles.grid}>
          {displayResults.map((company) => (
            <CompanyCard
              key={company.id}
              company={company}
              onClick={() => navigate(`/companies/${company.id}`)}
            />
          ))}
        </div>
      )}

      {!loading && viewMode === 'list' && displayResults.length > 0 && (
        <Card style={{ overflowX: 'auto' }}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={th}>Ticker</th>
                <th style={th}>Company</th>
                <th style={th}>Sector</th>
                <th style={{ ...th, width: 44 }} />
              </tr>
            </thead>
            <tbody>
              {displayResults.map((company) => (
                <CompanyRow
                  key={company.id}
                  company={company}
                  onClick={() => navigate(`/companies/${company.id}`)}
                />
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {!loading && displayResults.length === 0 && (
        <EmptyState
          icon={Building2}
          title={sectorFilter ? `No companies in ${formatSectorCode(sectorFilter)}` : query ? `No results for "${query}"` : 'No companies found'}
          sub={sectorFilter ? 'Try another sector filter.' : query ? 'Try another ticker, company name, or sector keyword.' : 'Add companies to the database to get started.'}
        />
      )}
    </div>
  )
}

function HeroMetric({ label, value }) {
  return (
    <div style={styles.heroMetric}>
      <div style={styles.metricLabel}>{label}</div>
      <div style={styles.metricValue}>{value}</div>
    </div>
  )
}

function CompanyCard({ company, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ ...styles.companyCard, ...(hover ? styles.companyCardHover : {}) }}
    >
      <div style={styles.cardAccent} />
      <div style={styles.companyTop}>
        <div style={styles.logoMark}>{company.ticker?.slice(0, 2) || '--'}</div>
        <span style={styles.sectorBadge}>{formatSectorCode(company.sector_code)}</span>
      </div>
      <div style={styles.ticker}>{company.ticker}</div>
      <div style={styles.companyName}>{company.company_name}</div>
      <div style={styles.cardFooter}>
        <span>Open Profile</span>
        <ChevronRight size={14} />
      </div>
    </button>
  )
}

function CompanyRow({ company, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <tr
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{ cursor: 'pointer', background: hover ? 'var(--surface-3)' : 'transparent' }}
    >
      <td style={tdTicker}>{company.ticker}</td>
      <td style={td}>{company.company_name}</td>
      <td style={td}><span style={styles.sectorBadge}>{formatSectorCode(company.sector_code)}</span></td>
      <td style={{ ...td, textAlign: 'right' }}><ChevronRight size={15} style={{ color: 'var(--text-3)' }} /></td>
    </tr>
  )
}

const chipStyle = (active) => ({
  border: `1px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
  background: active ? 'var(--primary-subtle)' : 'transparent',
  color: active ? 'var(--primary-hover)' : 'var(--text-2)',
  borderRadius: 999,
  padding: '5px 12px',
  fontSize: 11.5,
  fontWeight: 700,
  cursor: 'pointer',
})

const segmentButton = (active) => ({
  width: 34,
  height: 32,
  border: 0,
  borderRadius: 7,
  background: active ? 'var(--surface-hover)' : 'transparent',
  color: active ? 'var(--text-1)' : 'var(--text-3)',
  cursor: 'pointer',
  display: 'inline-flex',
  alignItems: 'center',
  justifyContent: 'center',
})

const th = {
  padding: '11px 16px',
  textAlign: 'left',
  fontSize: 11,
  fontWeight: 800,
  color: 'var(--text-3)',
  textTransform: 'uppercase',
  letterSpacing: 0.7,
  borderBottom: '1px solid var(--border)',
}

const td = {
  padding: '13px 16px',
  color: 'var(--text-2)',
  fontSize: 13.5,
  borderBottom: '1px solid var(--border)',
}

const tdTicker = {
  ...td,
  fontWeight: 800,
  color: 'var(--primary-hover)',
  fontVariantNumeric: 'tabular-nums',
}

const styles = {
  page: {
    maxWidth: 1240,
    margin: '0 auto',
    display: 'flex',
    flexDirection: 'column',
    gap: 18,
  },
  hero: {
    position: 'relative',
    overflow: 'hidden',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    background: 'linear-gradient(135deg, rgba(58,199,139,0.10), rgba(85,194,195,0.08) 42%, var(--surface-2))',
    padding: 24,
  },
  heroTop: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 280px), 1fr))',
    gap: 20,
    alignItems: 'end',
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
    margin: '12px 0 6px',
    color: 'var(--text-1)',
    fontSize: 'clamp(2rem, 5vw, 3.35rem)',
    lineHeight: 1,
    fontWeight: 900,
  },
  subtitle: {
    color: 'var(--text-2)',
    fontSize: 14.5,
    lineHeight: 1.65,
    maxWidth: 720,
    margin: 0,
  },
  searchBox: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  searchIcon: {
    position: 'absolute',
    left: 14,
    color: 'var(--text-3)',
    pointerEvents: 'none',
  },
  searchInput: {
    width: '100%',
    background: 'rgba(8,15,26,0.58)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: '13px 112px 13px 42px',
    color: 'var(--text-1)',
    fontSize: 14,
    outline: 'none',
    boxSizing: 'border-box',
  },
  aiChip: {
    position: 'absolute',
    right: 10,
    display: 'inline-flex',
    alignItems: 'center',
    gap: 5,
    color: 'var(--primary-hover)',
    background: 'var(--primary-subtle)',
    borderRadius: 999,
    padding: '4px 9px',
    fontSize: 11,
    fontWeight: 800,
  },
  kpiGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: 12,
    marginTop: 22,
  },
  heroMetric: {
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius-md)',
    padding: '13px 14px',
  },
  metricLabel: {
    color: 'var(--text-3)',
    fontSize: 10.5,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    fontWeight: 800,
  },
  metricValue: {
    color: 'var(--text-1)',
    fontSize: 24,
    lineHeight: 1.1,
    fontWeight: 900,
    marginTop: 3,
  },
  toolbar: {
    display: 'flex',
    justifyContent: 'space-between',
    gap: 12,
    alignItems: 'flex-start',
    flexWrap: 'wrap',
  },
  filterRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 7,
    flexWrap: 'wrap',
    flex: 1,
  },
  controls: {
    display: 'flex',
    gap: 8,
    alignItems: 'center',
  },
  select: {
    fontSize: 12,
    fontWeight: 700,
    padding: '8px 10px',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-strong)',
    background: 'var(--surface-2)',
    color: 'var(--text-2)',
    cursor: 'pointer',
    outline: 'none',
  },
  segment: {
    display: 'flex',
    gap: 3,
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: 3,
  },
  interpretation: {
    display: 'inline-flex',
    alignItems: 'center',
    gap: 8,
    color: 'var(--primary-hover)',
    background: 'var(--primary-subtle)',
    border: '1px solid rgba(244,176,74,0.22)',
    borderRadius: 'var(--radius-md)',
    padding: '9px 12px',
    fontSize: 12.5,
    fontWeight: 700,
    width: 'fit-content',
    maxWidth: '100%',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))',
    gap: 14,
  },
  listSkeleton: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
  },
  companyCard: {
    position: 'relative',
    textAlign: 'left',
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-lg)',
    padding: 18,
    minHeight: 156,
    overflow: 'hidden',
    cursor: 'pointer',
    transition: 'border-color .15s, transform .12s, box-shadow .15s, background .15s',
    color: 'inherit',
    font: 'inherit',
  },
  companyCardHover: {
    borderColor: 'var(--border-bright)',
    transform: 'translateY(-2px)',
    boxShadow: 'var(--shadow-sm)',
    background: 'var(--surface-3)',
  },
  cardAccent: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
    background: 'linear-gradient(90deg, var(--primary), var(--secondary))',
  },
  companyTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 10,
  },
  logoMark: {
    width: 42,
    height: 42,
    borderRadius: 10,
    background: 'var(--primary-subtle)',
    color: 'var(--primary-hover)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 12,
    fontWeight: 900,
  },
  sectorBadge: {
    display: 'inline-flex',
    alignItems: 'center',
    borderRadius: 999,
    background: 'var(--surface-3)',
    color: 'var(--text-2)',
    border: '1px solid var(--border)',
    padding: '3px 9px',
    fontSize: 11,
    fontWeight: 800,
    maxWidth: '100%',
  },
  ticker: {
    marginTop: 14,
    color: 'var(--text-1)',
    fontSize: 22,
    lineHeight: 1,
    fontWeight: 900,
  },
  companyName: {
    marginTop: 7,
    minHeight: 34,
    color: 'var(--text-3)',
    fontSize: 12.5,
    lineHeight: 1.35,
    overflow: 'hidden',
    display: '-webkit-box',
    WebkitLineClamp: 2,
    WebkitBoxOrient: 'vertical',
  },
  cardFooter: {
    marginTop: 14,
    display: 'inline-flex',
    alignItems: 'center',
    gap: 4,
    color: 'var(--primary-hover)',
    fontSize: 12,
    fontWeight: 800,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
}
