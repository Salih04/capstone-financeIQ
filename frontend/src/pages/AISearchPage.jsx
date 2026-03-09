import { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  Search, Sparkles, X, GitCompare, ChevronRight,
  ArrowRight, Bot, SortAsc, LayoutGrid, LayoutList,
} from 'lucide-react'
import api from '../api/client'
import { ScoreBadge, getBand, Card, EmptyState, Skeleton } from '../components/ui'

// AI keyword → sector_code mapping (same as SearchPage)
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
  construction: ['INSAAT'], building: ['INSAAT'],
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

const SUGGESTED_QUERIES = [
  'tech companies', 'banking sector', 'energy companies', 'automotive industry',
  'pharma stocks', 'defense sector', 'logistics companies', 'holding companies',
]

const parseAI = (query) => {
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

function CompanyCard({ company: c, compareMode, selected, onToggleCompare, onClick }) {
  const [hover, setHover] = useState(false)
  return (
    <div
      onClick={compareMode ? onToggleCompare : onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        background: selected ? 'rgba(0,245,212,0.08)' : hover ? 'var(--surface-3)' : 'var(--surface-2)',
        border: `1.5px solid ${selected ? 'var(--primary)' : hover ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: '16px 18px',
        cursor: 'pointer',
        transition: 'all 0.14s',
        transform: hover && !selected ? 'translateY(-2px)' : 'none',
        boxShadow: hover ? 'var(--shadow-md)' : selected ? '0 0 0 2px rgba(0,245,212,0.2)' : 'none',
        position: 'relative',
      }}
    >
      {compareMode && (
        <div style={{
          position: 'absolute', top: 10, right: 10,
          width: 18, height: 18, borderRadius: 4,
          border: `2px solid ${selected ? 'var(--primary)' : 'var(--border-bright)'}`,
          background: selected ? 'var(--primary)' : 'transparent',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: '#fff', fontSize: 10, fontWeight: 700, transition: 'all 0.12s',
        }}>
          {selected ? '✓' : ''}
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
        <div style={{
          width: 40, height: 40, borderRadius: 11, flexShrink: 0,
          background: selected ? 'rgba(0,245,212,0.15)' : 'var(--surface-3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: selected ? 'var(--primary-hover)' : 'var(--text-2)',
          fontWeight: 800, fontSize: 11, letterSpacing: '-0.2px',
        }}>
          {c.ticker?.substring(0, 2)}
        </div>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 17, fontWeight: 800, color: selected ? 'var(--primary)' : 'var(--primary-hover)', letterSpacing: '-0.3px', lineHeight: 1.1 }}>
            {c.ticker}
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--text-3)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2 }}>
            {c.company_name}
          </div>
        </div>
      </div>

      {c.sector_code && (
        <span style={{
          fontSize: 10, fontWeight: 600, color: 'var(--text-3)',
          background: 'var(--surface-3)', borderRadius: 5,
          padding: '2px 8px', marginRight: 6,
          textTransform: 'uppercase', letterSpacing: 0.4,
        }}>
          {SECTOR_LABELS[c.sector_code] || c.sector_code}
        </span>
      )}

      {!compareMode && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--primary)', fontSize: 12, fontWeight: 600, marginTop: 10 }}>
          View Profile <ChevronRight size={12} />
        </div>
      )}
    </div>
  )
}

export default function AISearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || '')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [sectorFilter, setSectorFilter] = useState(null)
  const [compareSet, setCompareSet] = useState(new Set())
  const [compareMode, setCompareMode] = useState(false)
  const [aiTokens, setAiTokens] = useState({ sectors: [], keywords: [] })
  const [touched, setTouched] = useState(false)
  const [sortBy, setSortBy] = useState('name') // name | sector
  const [viewMode, setViewMode] = useState('grid') // grid | list
  const inputRef = useRef(null)

  useEffect(() => {
    if (inputRef.current) inputRef.current.focus()
    if (searchParams.get('q')) {
      setTouched(true)
    }
  }, [])

  /* Keyboard shortcut: Ctrl+K or Cmd+K to focus search */
  useEffect(() => {
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (inputRef.current) inputRef.current.focus()
      }
      if (e.key === 'Escape' && document.activeElement === inputRef.current) {
        inputRef.current.blur()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  const search = useCallback(async (q) => {
    setLoading(true)
    try {
      const url = q.length >= 1
        ? `/companies?q=${encodeURIComponent(q)}&limit=100`
        : '/companies?limit=100'
      const { data } = await api.get(url)
      setResults(data)
    } catch { setResults([]) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => {
    const parsed = query.trim().length > 1 ? parseAI(query) : { sectors: [], keywords: [] }
    setAiTokens(parsed)
    const t = setTimeout(() => {
      if (touched || query.trim().length > 0) search(query)
    }, 280)
    return () => clearTimeout(t)
  }, [query, search, touched])

  const displayed = useMemo(() => {
    let r = [...results]
    if (aiTokens.sectors.length > 0) {
      r = r.filter(c => aiTokens.sectors.includes(c.sector_code))
    }
    if (sectorFilter) {
      r = r.filter(c => c.sector_code === sectorFilter)
    }
    if (sortBy === 'name') {
      r.sort((a, b) => (a.ticker || '').localeCompare(b.ticker || ''))
    } else if (sortBy === 'sector') {
      r.sort((a, b) => (a.sector_code || '').localeCompare(b.sector_code || ''))
    }
    return r
  }, [results, aiTokens.sectors, sectorFilter, sortBy])

  const toggleCompare = (id) => {
    setCompareSet(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else if (next.size < 8) next.add(id)
      return next
    })
  }

  const handleCompareNow = () => {
    sessionStorage.setItem('comparePreselect', JSON.stringify(Array.from(compareSet)))
    navigate('/compare')
  }

  const availableSectors = [...new Set(results.map(c => c.sector_code).filter(Boolean))].sort()

  const handleSuggest = (q) => {
    setQuery(q)
    setTouched(true)
    if (inputRef.current) inputRef.current.focus()
  }

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>

      {/* Animated gradient keyframes */}
      <style>{`
        @keyframes aiGradient {
          0% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes aiPulse {
          0%, 100% { box-shadow: 0 0 12px rgba(0,245,212,0.15); }
          50% { box-shadow: 0 0 28px rgba(0,245,212,0.35); }
        }
        @keyframes aiFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-6px); }
        }
        @keyframes sparkleRotate {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* ── Hero header with animated gradient background ── */}
      <div style={{
        textAlign: 'center', marginBottom: 32, paddingTop: 4,
        position: 'relative', overflow: 'hidden',
      }}>
        {/* Animated gradient orbs */}
        <div style={{
          position: 'absolute', top: -80, left: '20%', width: 200, height: 200, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(0,245,212,0.08), transparent)',
          animation: 'aiFloat 6s ease-in-out infinite',
          pointerEvents: 'none',
        }} />
        <div style={{
          position: 'absolute', top: -60, right: '15%', width: 160, height: 160, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.06), transparent)',
          animation: 'aiFloat 8s ease-in-out infinite 2s',
          pointerEvents: 'none',
        }} />

        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 16,
          background: 'linear-gradient(135deg, rgba(0,245,212,0.12), rgba(99,102,241,0.08))',
          backgroundSize: '200% 200%',
          animation: 'aiGradient 4s ease infinite, aiPulse 3s ease-in-out infinite',
          border: '1px solid rgba(0,245,212,0.3)',
          borderRadius: 24, padding: '6px 16px 6px 12px',
          position: 'relative',
        }}>
          <div style={{
            width: 26, height: 26, borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--primary), #6366f1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 2px 12px rgba(0,245,212,0.4)',
          }}>
            <Sparkles size={13} color="#fff" style={{ animation: 'sparkleRotate 6s linear infinite' }} />
          </div>
          <span style={{ fontSize: 12, fontWeight: 800, color: 'var(--primary-hover)', letterSpacing: 0.5 }}>
            AI-Powered Search
          </span>
        </div>

        <h1 style={{
          fontSize: '2.2rem', fontWeight: 900, color: 'var(--text-1)',
          margin: '0 0 10px', letterSpacing: '-0.8px',
          background: 'linear-gradient(135deg, var(--text-1), var(--primary-hover))',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
        }}>
          Find any company, any way
        </h1>
        <p style={{ fontSize: 14, color: 'var(--text-3)', margin: 0, maxWidth: 500, marginLeft: 'auto', marginRight: 'auto', lineHeight: 1.5 }}>
          Search by ticker, name, or describe what you're looking for in plain language
          <span style={{ marginLeft: 8, fontSize: 11, color: 'var(--text-4)', background: 'var(--surface-3)', borderRadius: 4, padding: '2px 6px', fontFamily: 'monospace' }}>
            {navigator.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+K
          </span>
        </p>
      </div>

      {/* ── Big search bar with glow ── */}
      <div style={{ position: 'relative', maxWidth: 680, margin: '0 auto 20px' }}>
        {/* Glow background */}
        <div style={{
          position: 'absolute', inset: -2, borderRadius: 16,
          background: 'linear-gradient(135deg, rgba(0,245,212,0.15), rgba(99,102,241,0.1), rgba(0,245,212,0.15))',
          backgroundSize: '200% 200%',
          animation: 'aiGradient 4s ease infinite',
          opacity: 0.5, pointerEvents: 'none', filter: 'blur(4px)',
        }} />
        <Search size={18} style={{
          position: 'absolute', left: 18, top: '50%',
          transform: 'translateY(-50%)', color: 'var(--text-3)', pointerEvents: 'none',
          zIndex: 1,
        }} />
        <input
          ref={inputRef}
          value={query}
          onChange={e => { setQuery(e.target.value); setTouched(true) }}
          placeholder='Try "tech companies", "THYAO", "defense sector"…'
          style={{
            width: '100%', boxSizing: 'border-box',
            background: 'var(--surface-2)',
            border: '1.5px solid var(--border-bright)',
            borderRadius: 14,
            padding: '16px 52px 16px 50px',
            color: 'var(--text-1)', fontSize: 16,
            outline: 'none',
            transition: 'border-color 0.15s, box-shadow 0.15s',
            boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
            position: 'relative',
            zIndex: 1,
          }}
          onFocus={e => {
            e.target.style.borderColor = 'var(--primary)'
            e.target.style.boxShadow = '0 0 0 4px rgba(0,245,212,0.15), 0 4px 24px rgba(0,245,212,0.1)'
          }}
          onBlur={e => {
            e.target.style.borderColor = 'var(--border-bright)'
            e.target.style.boxShadow = '0 4px 20px rgba(0,0,0,0.15)'
          }}
        />
        <div style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', display: 'flex', alignItems: 'center', gap: 6 }}>
          {aiTokens.keywords.length > 0 && (
            <span style={{
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 11, fontWeight: 700, color: 'var(--primary)',
              background: 'rgba(0,245,212,0.1)', borderRadius: 6, padding: '3px 8px',
            }}>
              <Sparkles size={10} /> AI
            </span>
          )}
          {query && (
            <button
              onClick={() => { setQuery(''); setSectorFilter(null) }}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)', display: 'flex', padding: 2 }}
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* ── AI detection banner ── */}
      {aiTokens.keywords.length > 0 && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          maxWidth: 680, margin: '0 auto 18px',
          background: 'rgba(0,245,212,0.06)', border: '1px solid rgba(0,245,212,0.22)',
          borderRadius: 10, padding: '9px 14px', fontSize: 12.5,
        }}>
          <Sparkles size={13} style={{ color: 'var(--primary)', flexShrink: 0 }} />
          <span style={{ color: 'var(--text-3)' }}>AI detected:</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
            {aiTokens.keywords.map(kw => (
              <span key={kw} style={{
                fontSize: 11, fontWeight: 700, color: 'var(--primary-hover)',
                background: 'rgba(0,245,212,0.13)', borderRadius: 5,
                padding: '2px 8px', textTransform: 'capitalize',
              }}>
                {kw}
              </span>
            ))}
          </div>
          <span style={{ color: 'var(--text-4)' }}>→</span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {aiTokens.sectors.map(s => (
              <span key={s} style={{
                fontSize: 11, fontWeight: 600, color: '#22c55e',
                background: 'rgba(34,197,94,0.1)', borderRadius: 5, padding: '2px 8px',
              }}>
                {SECTOR_LABELS[s] || s}
              </span>
            ))}
          </div>
          <span style={{ marginLeft: 'auto', fontSize: 11.5, color: 'var(--text-3)', fontWeight: 600, whiteSpace: 'nowrap' }}>
            {displayed.length} result{displayed.length !== 1 ? 's' : ''}
          </span>
        </div>
      )}

      {/* ── Suggested queries (shown only before first search) ── */}
      {!touched && (
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <p style={{ fontSize: 12, color: 'var(--text-3)', marginBottom: 10 }}>Suggestions</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
            {SUGGESTED_QUERIES.map(q => (
              <button
                key={q}
                onClick={() => handleSuggest(q)}
                style={{
                  fontSize: 12, fontWeight: 500, padding: '6px 14px', borderRadius: 20,
                  border: '1px solid var(--border-strong)', background: 'var(--surface-2)',
                  color: 'var(--text-2)', cursor: 'pointer', transition: 'all 0.12s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--primary)'; e.currentTarget.style.color = 'var(--primary)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-strong)'; e.currentTarget.style.color = 'var(--text-2)' }}
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Controls bar: sector chips + compare toggle + filter ── */}
      {touched && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 }}>
          {/* Sector chips */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', flex: 1, alignItems: 'center' }}>
            <button
              onClick={() => setSectorFilter(null)}
              style={{
                fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 20,
                border: `1.5px solid ${!sectorFilter ? 'var(--primary)' : 'var(--border-strong)'}`,
                background: !sectorFilter ? 'rgba(0,245,212,0.1)' : 'transparent',
                color: !sectorFilter ? 'var(--primary)' : 'var(--text-3)',
                cursor: 'pointer', transition: 'all 0.12s',
              }}
            >
              All
            </button>
            {availableSectors.slice(0, 8).map(code => {
              const label = SECTOR_LABELS[code] || code
              const active = sectorFilter === code
              return (
                <button
                  key={code}
                  onClick={() => setSectorFilter(active ? null : code)}
                  style={{
                    fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 20,
                    border: `1.5px solid ${active ? 'var(--primary)' : 'var(--border-strong)'}`,
                    background: active ? 'rgba(0,245,212,0.1)' : 'transparent',
                    color: active ? 'var(--primary)' : 'var(--text-3)',
                    cursor: 'pointer', transition: 'all 0.12s',
                  }}
                >
                  {label}
                </button>
              )
            })}
            {availableSectors.length > 8 && (
              <span style={{ fontSize: 11, color: 'var(--text-4)' }}>+{availableSectors.length - 8} more</span>
            )}
          </div>

          {/* Compare mode toggle */}
          <button
            onClick={() => { setCompareMode(m => !m); if (compareMode) setCompareSet(new Set()) }}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600,
              padding: '7px 14px', borderRadius: 8, whiteSpace: 'nowrap',
              border: `1.5px solid ${compareMode ? 'var(--primary)' : 'var(--border-strong)'}`,
              background: compareMode ? 'var(--primary)' : 'var(--surface-2)',
              color: compareMode ? '#fff' : 'var(--text-2)',
              cursor: 'pointer', transition: 'all 0.12s',
            }}
          >
            <GitCompare size={13} />
            {compareMode ? `Compare Mode (${compareSet.size}/8)` : 'Compare Mode'}
          </button>

          {/* Sort toggle */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            style={{
              fontSize: 12, fontWeight: 600, padding: '7px 10px', borderRadius: 8,
              border: '1.5px solid var(--border-strong)', background: 'var(--surface-2)',
              color: 'var(--text-2)', cursor: 'pointer', outline: 'none',
            }}
          >
            <option value="name">Sort: Name</option>
            <option value="sector">Sort: Sector</option>
          </select>

          {/* View mode toggle */}
          <div style={{ display: 'flex', border: '1.5px solid var(--border-strong)', borderRadius: 8, overflow: 'hidden' }}>
            <button
              onClick={() => setViewMode('grid')}
              style={{
                display: 'flex', alignItems: 'center', padding: '6px 10px', border: 'none', cursor: 'pointer',
                background: viewMode === 'grid' ? 'var(--primary-subtle)' : 'var(--surface-2)',
                color: viewMode === 'grid' ? 'var(--primary)' : 'var(--text-3)',
              }}
            >
              <LayoutGrid size={14} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              style={{
                display: 'flex', alignItems: 'center', padding: '6px 10px', border: 'none', cursor: 'pointer',
                borderLeft: '1px solid var(--border-strong)',
                background: viewMode === 'list' ? 'var(--primary-subtle)' : 'var(--surface-2)',
                color: viewMode === 'list' ? 'var(--primary)' : 'var(--text-3)',
              }}
            >
              <LayoutList size={14} />
            </button>
          </div>
        </div>
      )}

      {/* ── Stats row ── */}
      {touched && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, fontSize: 12, color: 'var(--text-3)' }}>
          <span style={{ fontWeight: 600 }}>
            {loading ? 'Searching…' : `${displayed.length} compan${displayed.length !== 1 ? 'ies' : 'y'} found`}
          </span>
          {query && !loading && displayed.length > 0 && !aiTokens.keywords.length && (
            <span>for <span style={{ color: 'var(--text-2)', fontWeight: 600 }}>"{query}"</span></span>
          )}
          {compareMode && compareSet.size > 0 && (
            <span style={{ marginLeft: 'auto', color: 'var(--primary)', fontWeight: 700 }}>
              {compareSet.size} selected
            </span>
          )}
        </div>
      )}

      {/* ── Results ── */}
      {!touched ? null : loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {[...Array(12)].map((_, i) => (
            <Skeleton key={i} style={{ height: 140, borderRadius: 'var(--radius-lg)' }} />
          ))}
        </div>
      ) : displayed.length === 0 ? (
        <div style={{ textAlign: 'center', paddingTop: 40 }}>
          <EmptyState
            icon={<Search size={28} />}
            title="No companies found"
            sub={query ? 'Try a different search term or remove sector filters' : 'Start typing to search'}
          />
        </div>
      ) : viewMode === 'grid' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {displayed.map(c => (
            <CompanyCard
              key={c.id}
              company={c}
              compareMode={compareMode}
              selected={compareSet.has(c.id)}
              onToggleCompare={() => toggleCompare(c.id)}
              onClick={() => navigate(`/companies/${c.id}`)}
            />
          ))}
        </div>
      ) : (
        <Card style={{ overflow: 'hidden' }}>
          {displayed.map((c, i) => (
            <div
              key={c.id}
              onClick={compareMode ? () => toggleCompare(c.id) : () => navigate(`/companies/${c.id}`)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '10px 16px', cursor: 'pointer',
                borderTop: i > 0 ? '1px solid var(--border)' : 'none',
                transition: 'background 0.12s',
                background: compareSet.has(c.id) ? 'rgba(0,245,212,0.06)' : 'transparent',
              }}
              onMouseEnter={e => { if (!compareSet.has(c.id)) e.currentTarget.style.background = 'var(--surface-3)' }}
              onMouseLeave={e => { if (!compareSet.has(c.id)) e.currentTarget.style.background = 'transparent' }}
            >
              {compareMode && (
                <div style={{
                  width: 16, height: 16, borderRadius: 4, flexShrink: 0,
                  border: `2px solid ${compareSet.has(c.id) ? 'var(--primary)' : 'var(--border-bright)'}`,
                  background: compareSet.has(c.id) ? 'var(--primary)' : 'transparent',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 9, fontWeight: 700,
                }}>
                  {compareSet.has(c.id) ? '✓' : ''}
                </div>
              )}
              <div style={{
                width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                background: 'var(--surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                color: 'var(--text-2)', fontWeight: 800, fontSize: 10,
              }}>
                {c.ticker?.substring(0, 2)}
              </div>
              <div style={{ width: 80, fontWeight: 800, fontSize: 14, color: 'var(--primary-hover)' }}>
                {c.ticker}
              </div>
              <div style={{ flex: 1, fontSize: 13, color: 'var(--text-2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {c.company_name}
              </div>
              {c.sector_code && (
                <span style={{
                  fontSize: 10, fontWeight: 600, color: 'var(--text-3)',
                  background: 'var(--surface-3)', borderRadius: 5,
                  padding: '2px 8px', textTransform: 'uppercase', letterSpacing: 0.4,
                  whiteSpace: 'nowrap',
                }}>
                  {SECTOR_LABELS[c.sector_code] || c.sector_code}
                </span>
              )}
              <ChevronRight size={14} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
            </div>
          ))}
        </Card>
      )}

      {/* ── Floating compare action bar ── */}
      {compareMode && compareSet.size >= 2 && (
        <div style={{
          position: 'fixed', bottom: 28, left: '50%', transform: 'translateX(-50%)',
          background: 'var(--primary)', borderRadius: 16, padding: '12px 24px',
          display: 'flex', alignItems: 'center', gap: 16,
          boxShadow: '0 8px 32px rgba(0,245,212,0.35)',
          zIndex: 100,
        }}>
          <GitCompare size={16} color="#fff" />
          <span style={{ color: '#fff', fontWeight: 600, fontSize: 14 }}>
            {compareSet.size} companies selected
          </span>
          <button
            onClick={handleCompareNow}
            style={{
              background: '#fff', color: 'var(--primary)', border: 'none',
              borderRadius: 9, padding: '8px 18px', fontWeight: 700,
              fontSize: 13, cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            Compare Now <ArrowRight size={13} />
          </button>
          <button
            onClick={() => setCompareSet(new Set())}
            style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 7, padding: '8px 12px', cursor: 'pointer', color: '#fff', display: 'flex' }}
          >
            <X size={14} />
          </button>
        </div>
      )}
    </div>
  )
}
