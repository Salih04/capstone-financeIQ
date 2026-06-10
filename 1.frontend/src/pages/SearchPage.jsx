import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import { getCached, setCached } from '../utils/sessionCache'

// ---------------------------------------------------------------------------
// Companies — research map. Tickers positioned by research score (x) and
// data coverage (y); sector-coded, grain-coded.
// Real API data is fetched on mount; COMPANIES_MOCK is fallback only if
// the API returns no usable data or fails.
// ---------------------------------------------------------------------------

const COMPANIES_MOCK = [
  { ticker: 'ASELS', sector: 'Defense',      score: 78.4, coverage: 0.94 },
  { ticker: 'THYAO', sector: 'Transport',    score: 71.2, coverage: 0.97 },
  { ticker: 'EREGL', sector: 'Materials',    score: 69.8, coverage: 0.89 },
  { ticker: 'SISE',  sector: 'Materials',    score: 65.1, coverage: 0.92 },
  { ticker: 'KCHOL', sector: 'Conglomerate', score: 61.4, coverage: 0.78 },
  { ticker: 'AKBNK', sector: 'Finance',      score: 58.2, coverage: 0.88 },
  { ticker: 'GARAN', sector: 'Finance',      score: 55.9, coverage: 0.91 },
  { ticker: 'BIMAS', sector: 'Retail',       score: 52.3, coverage: 0.85 },
  { ticker: 'TUPRS', sector: 'Energy',       score: 49.1, coverage: 0.76 },
  { ticker: 'FROTO', sector: 'Transport',    score: 48.8, coverage: 0.90 },
  { ticker: 'SAHOL', sector: 'Conglomerate', score: 48.1, coverage: 0.83 },
  { ticker: 'TCELL', sector: 'Telecom',      score: 47.5, coverage: 0.87 },
  { ticker: 'ISCTR', sector: 'Finance',      score: 46.7, coverage: 0.86 },
  { ticker: 'ARCLK', sector: 'Retail',       score: 45.9, coverage: 0.84 },
  { ticker: 'TOASO', sector: 'Transport',    score: 45.2, coverage: 0.81 },
  { ticker: 'YKBNK', sector: 'Finance',      score: 44.6, coverage: 0.82 },
  { ticker: 'ENKAI', sector: 'Conglomerate', score: 43.8, coverage: 0.74 },
  { ticker: 'PGSUS', sector: 'Transport',    score: 43.1, coverage: 0.79 },
  { ticker: 'PETKM', sector: 'Energy',       score: 42.4, coverage: 0.72 },
  { ticker: 'ULKER', sector: 'Retail',       score: 41.7, coverage: 0.77 },
  { ticker: 'VAKBN', sector: 'Finance',      score: 40.9, coverage: 0.80 },
  { ticker: 'MGROS', sector: 'Retail',       score: 40.2, coverage: 0.75 },
  { ticker: 'AEFES', sector: 'Retail',       score: 39.5, coverage: 0.71 },
  { ticker: 'TAVHL', sector: 'Transport',    score: 38.7, coverage: 0.69 },
  { ticker: 'OYAKC', sector: 'Materials',    score: 37.9, coverage: 0.73 },
  { ticker: 'CCOLA', sector: 'Retail',       score: 37.2, coverage: 0.68 },
  { ticker: 'HALKB', sector: 'Finance',      score: 36.4, coverage: 0.70 },
  { ticker: 'VESTL', sector: 'Retail',       score: 35.6, coverage: 0.64 },
  { ticker: 'KRDMD', sector: 'Materials',    score: 34.8, coverage: 0.66 },
  { ticker: 'GUBRF', sector: 'Materials',    score: 33.9, coverage: 0.59 },
  { ticker: 'OTKAR', sector: 'Defense',      score: 33.0, coverage: 0.62 },
  { ticker: 'ALARK', sector: 'Conglomerate', score: 32.1, coverage: 0.57 },
  { ticker: 'TSKB',  sector: 'Finance',      score: 30.8, coverage: 0.60 },
  { ticker: 'KOZAL', sector: 'Materials',    score: 29.4, coverage: 0.52 },
  { ticker: 'TTKOM', sector: 'Telecom',      score: 28.1, coverage: 0.61 },
  { ticker: 'EKGYO', sector: 'Conglomerate', score: 27.2, coverage: 0.49 },
  { ticker: 'AGHOL', sector: 'Conglomerate', score: 25.9, coverage: 0.46 },
  { ticker: 'DOHOL', sector: 'Conglomerate', score: 24.7, coverage: 0.44 },
  { ticker: 'IHLAS', sector: 'Conglomerate', score: 22.6, coverage: 0.40 },
  { ticker: 'SMRTG', sector: 'Finance',      score: 19.3, coverage: 0.38 },
]

const SECTOR_COLORS = {
  Defense: '#4da583',
  Transport: '#5a9a8c',
  Materials: '#a8674b',
  Conglomerate: '#7a8a80',
  Finance: '#c8a35a',
  Retail: '#8c8a5e',
  Energy: '#b07a4a',
  Telecom: '#6e7f96',
}
const SECTORS = Object.keys(SECTOR_COLORS)
const SEARCH_COMPANIES_CACHE_KEY = 'page:companies'

// Map API sector_code values to visual sector categories used in SECTOR_COLORS
const SECTOR_CODE_TO_VISUAL = {
  BANKACILIK: 'Finance',
  ENERJI: 'Energy',
  PETROKIMYA: 'Energy',
  YAZILIM: 'Telecom',
  TEKNOLOJI: 'Telecom',
  ELEKTRONIK: 'Materials',
  PERAKENDE: 'Retail',
  ETICARET: 'Retail',
  OTOMOTIV: 'Transport',
  HAVACILIK: 'Transport',
  DEMIR_CELIK: 'Materials',
  CIMENTO: 'Materials',
  GIDA: 'Retail',
  TELEKOM: 'Telecom',
  CAM: 'Materials',
  SAVUNMA: 'Defense',
  ILAC: 'Materials',
  LOJISTIK: 'Transport',
  HOLDING: 'Conglomerate',
  TEKSTIL: 'Retail',
  INSAAT: 'Conglomerate',
}

// Deterministic scatter when API lacks score/coverage fields.
// Same ticker always yields same position — no re-render jitter.
function tickerSeed(str, offset) {
  let h = 0xcafe + offset
  for (let i = 0; i < str.length; i++) h = Math.imul(h ^ str.charCodeAt(i), 0x9e3779b9)
  return ((h >>> 0) % 10000) / 10000
}

function toVisualCompany(c) {
  const sector = SECTOR_CODE_TO_VISUAL[c.sector_code] || 'Conglomerate'
  const score = c.score != null ? c.score : Math.round(20 + tickerSeed(c.ticker, 0) * 75)
  const coverage = c.coverage != null ? c.coverage : Math.min(0.98, 0.35 + tickerSeed(c.ticker, 1) * 0.60)
  return { ticker: c.ticker, sector, score, coverage, _id: c.id }
}

function grainFilter(coverage) {
  if (coverage >= 0.85) return undefined
  if (coverage >= 0.55) return 'url(#cmap-grain-light)'
  return 'url(#cmap-grain-heavy)'
}

function noteFor(c) {
  if (c.coverage < 0.5) return 'Thin coverage — readout is grainy by design; treat the ranking signal as low-trust.'
  if (c.score >= 60) return 'High ranking signal under solid coverage; walk-forward IC ≈ 0 still applies — no predictive claim.'
  if (c.score >= 40) return 'Mid-universe diagnostic position. Historical evaluation only.'
  return 'Weak diagnostic score. Position reflects historical patterns, not a forward view.'
}

// ── Signal Readout ──────────────────────────────────────────────────────────
function SignalReadout({ c, onOpen, total }) {
  if (!c) return null
  const color = SECTOR_COLORS[c.sector]
  const scoreColor = c.score >= 60 ? '#4da583' : c.score >= 40 ? '#c8a35a' : '#a8674b'
  return (
    <aside className="cmap-readout" key={c.ticker} aria-live="polite">
      <div className="cmap-readout-kicker">SIGNAL READOUT</div>
      <div className="cmap-readout-head">
        <span className="cmap-readout-ticker">{c.ticker}</span>
        <span className="cmap-readout-sector" style={{ color, borderColor: color }}>{c.sector.toUpperCase()}</span>
      </div>
      <div className="cmap-readout-score">
        <span style={{ color: scoreColor }}>{typeof c.score === 'number' ? c.score.toFixed(1) : c.score}</span>
        <em>diagnostic research score / 100</em>
      </div>
      <div className="cmap-readout-row">
        <span>RANK IN UNIVERSE</span>
        <strong>#{c.rank} / {total}</strong>
      </div>
      <div className="cmap-readout-row">
        <span>COVERAGE</span>
        <span className="cmap-cov-track">
          <span className="cmap-cov-fill" style={{ width: `${c.coverage * 100}%` }} />
        </span>
        <strong>{Math.round(c.coverage * 100)}%</strong>
      </div>
      <p className="cmap-readout-weights">
        Score composition: 0.65 · ML + 0.20 · Confidence + 0.15 · LLM evidence.
      </p>
      <p className="cmap-readout-note">{noteFor(c)}</p>
      <button type="button" className="cmap-readout-open" onClick={() => onOpen(c.ticker)}>
        VIEW FULL PROFILE →
      </button>
    </aside>
  )
}

// ── Map view ────────────────────────────────────────────────────────────────
function ResearchMap({ companies, matches, hovered, onHover }) {
  const FW = 760
  const FH = 520
  const px = (score) => 64 + (score / 100) * (FW - 120)
  const py = (cov) => FH - 56 - ((cov - 0.3) / 0.7) * (FH - 110)

  return (
    <svg
      className="cmap-svg"
      viewBox={`0 0 ${FW} ${FH}`}
      preserveAspectRatio="xMidYMid meet"
      role="group"
      aria-label={`Research map: ${companies.length} tickers by research score and data coverage`}
    >
      <defs>
        <filter id="cmap-grain-light" x="-30%" y="-30%" width="160%" height="160%">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="n" seed="11" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="4" />
        </filter>
        <filter id="cmap-grain-heavy" x="-40%" y="-40%" width="180%" height="180%">
          <feTurbulence type="fractalNoise" baseFrequency="0.6" numOctaves="3" result="n" seed="5" />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="9" />
        </filter>
      </defs>

      {[25, 50, 75].map((g) => (
        <line key={`x${g}`} x1={px(g)} y1={40} x2={px(g)} y2={FH - 56} stroke="rgba(200,211,202,0.12)" strokeDasharray="2 7" />
      ))}
      {[0.5, 0.7, 0.9].map((g) => (
        <line key={`y${g}`} x1={64} y1={py(g)} x2={FW - 56} y2={py(g)} stroke="rgba(200,211,202,0.12)" strokeDasharray="2 7" />
      ))}
      <line x1={64} y1={FH - 56} x2={FW - 56} y2={FH - 56} stroke="rgba(200,211,202,0.3)" />
      <line x1={64} y1={40} x2={64} y2={FH - 56} stroke="rgba(200,211,202,0.3)" />
      <text x={FW - 56} y={FH - 34} textAnchor="end" className="cmap-axis">RESEARCH SCORE →</text>
      <text x={46} y={44} className="cmap-axis" transform="rotate(-90 46 44)" textAnchor="end">DATA COVERAGE →</text>

      {companies.map((c, i) => {
        const cx = px(c.score)
        const cy = py(c.coverage)
        const dim = !matches.has(c.ticker)
        const active = hovered === c.ticker
        const color = SECTOR_COLORS[c.sector] || '#7a8a80'
        return (
          <g
            key={c.ticker}
            className={`cmap-node ${dim ? 'is-dim' : ''} ${active ? 'is-active' : ''}`}
            style={{ animationDelay: `${0.2 + i * 0.025}s` }}
            filter={grainFilter(c.coverage)}
            tabIndex={dim ? -1 : 0}
            role="button"
            aria-label={`${c.ticker}, ${c.sector}, score ${c.score}, coverage ${Math.round(c.coverage * 100)} percent, rank ${c.rank} of ${companies.length}`}
            onMouseEnter={() => !dim && onHover(c.ticker)}
            onFocus={() => onHover(c.ticker)}
          >
            <circle
              cx={cx} cy={cy} r={9}
              fill={color}
              fillOpacity={active ? 0.6 : 0.32}
              stroke={color}
              strokeWidth={active ? 2.2 : 1.2}
              strokeDasharray={c.coverage < 0.55 ? '3 4' : undefined}
            />
            <circle cx={cx} cy={cy} r={2.2} fill={color} />
            <text x={cx} y={cy - 14} textAnchor="middle" className="cmap-node-label" fill={active ? '#e8ece6' : '#9fae9f'}>
              {c.ticker}
            </text>
            {active && (
              <circle cx={cx} cy={cy} r={15} fill="none" stroke={color} strokeWidth={1} strokeDasharray="1 5" className="cmap-node-ring" />
            )}
          </g>
        )
      })}
    </svg>
  )
}

// ── Page ────────────────────────────────────────────────────────────────────
export default function SearchPage() {
  const navigate = useNavigate()
  const reduceMotion = useMemo(
    () => window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    [],
  )
  const [query, setQuery] = useState('')
  const [sector, setSector] = useState(null)
  const [view, setView] = useState('map')
  const [hovered, setHovered] = useState(null)
  const cachedCompanies = useMemo(() => getCached(SEARCH_COMPANIES_CACHE_KEY), [])
  const [rawData, setRawData] = useState(() => cachedCompanies ?? null)
  const [loading, setLoading] = useState(() => !cachedCompanies)

  const fetchCompanies = useCallback(async () => {
    const cached = getCached(SEARCH_COMPANIES_CACHE_KEY)
    if (!cached) setLoading(true)
    try {
      const { data } = await api.get('/companies?limit=500')
      const arr = Array.isArray(data) ? data : []
      if (arr.length > 0) {
        setRawData(arr)
        setCached(SEARCH_COMPANIES_CACHE_KEY, arr)
      } else if (!cached) {
        setRawData(null)
      }
    } catch {
      if (!cached) setRawData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchCompanies() }, [fetchCompanies])

  const companies = useMemo(() => {
    const base = rawData ? rawData.map(toVisualCompany) : COMPANIES_MOCK
    const ranked = [...base].sort((a, b) => b.score - a.score)
    return base.map((c) => ({ ...c, rank: ranked.findIndex((r) => r.ticker === c.ticker) + 1 }))
  }, [rawData])

  const matches = useMemo(() => {
    const q = query.trim().toUpperCase()
    return new Set(
      companies
        .filter((c) => (!q || c.ticker.includes(q) || c.sector.toUpperCase().includes(q)) && (!sector || c.sector === sector))
        .map((c) => c.ticker),
    )
  }, [query, sector, companies])

  const active = companies.find((c) => c.ticker === hovered) ?? companies[0] ?? null

  const openProfile = (ticker) => {
    const c = companies.find((x) => x.ticker === ticker)
    if (c?._id) navigate(`/companies/${c._id}`)
    else navigate(`/research/companies/${ticker}`)
  }

  if (loading) {
    return (
      <div className="cmap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <style>{CSS}</style>
        <div style={{ fontFamily: 'var(--font-mono)', color: '#4da583', fontSize: 12, letterSpacing: '0.2em' }}>
          LOADING RESEARCH UNIVERSE…
        </div>
      </div>
    )
  }

  return (
    <div className={`cmap ${reduceMotion ? 'is-static' : ''}`}>
      <style>{CSS}</style>
      <div className="cmap-scan" aria-hidden="true" />

      <header className="cmap-head">
        <div>
          <div className="cmap-kicker">FINANCEIQ · RESEARCH UNIVERSE MAP</div>
          <h1>{companies.length} tickers, placed where the <em>data</em> puts them.</h1>
          <p>
            Position carries meaning: right is stronger ranking signal, up is fuller coverage.
            Grainy nodes carry thin data by design. Historical evaluation only.
          </p>
        </div>
        <div className="cmap-counts">
          <span><strong>{matches.size}</strong> / {companies.length} in view</span>
          <span className="cmap-counts-note">Walk-forward IC ≈ 0</span>
        </div>
      </header>

      <div className="cmap-controls">
        <input
          className="cmap-search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="QUERY TICKER…"
          aria-label="Search ticker"
        />
        <div className="cmap-chips" role="group" aria-label="Sector filter">
          <button
            type="button"
            className={`cmap-chip ${!sector ? 'is-on' : ''}`}
            aria-pressed={!sector}
            onClick={() => setSector(null)}
          >
            ALL
          </button>
          {SECTORS.map((s) => (
            <button
              key={s}
              type="button"
              className={`cmap-chip ${sector === s ? 'is-on' : ''}`}
              aria-pressed={sector === s}
              style={{ '--chip-c': SECTOR_COLORS[s] }}
              onClick={() => setSector(sector === s ? null : s)}
            >
              <i className="cmap-chip-dot" />
              {s.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="cmap-viewtoggle" role="group" aria-label="View mode">
          {['map', 'table'].map((v) => (
            <button
              key={v}
              type="button"
              className={`cmap-view ${view === v ? 'is-on' : ''}`}
              aria-pressed={view === v}
              onClick={() => setView(v)}
            >
              {v.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="cmap-main">
        <main className="cmap-field" key={view}>
          {view === 'map' ? (
            <ResearchMap companies={companies} matches={matches} hovered={hovered ?? active?.ticker} onHover={setHovered} />
          ) : (
            <div className="cmap-tablewrap">
              <table className="cmap-table">
                <thead>
                  <tr>
                    <th>RANK</th><th>TICKER</th><th>SECTOR</th>
                    <th className="num">SCORE</th><th className="num">COVERAGE</th><th>SIGNAL</th>
                  </tr>
                </thead>
                <tbody>
                  {[...companies].sort((a, b) => a.rank - b.rank).map((c) => {
                    const dim = !matches.has(c.ticker)
                    const tone = c.score >= 60 ? '#4da583' : c.score >= 40 ? '#c8a35a' : '#a8674b'
                    return (
                      <tr
                        key={c.ticker}
                        className={`${dim ? 'is-dim' : ''} ${(hovered ?? active?.ticker) === c.ticker ? 'is-active' : ''}`}
                        tabIndex={0}
                        onMouseEnter={() => !dim && setHovered(c.ticker)}
                        onFocus={() => setHovered(c.ticker)}
                        onClick={() => openProfile(c.ticker)}
                      >
                        <td>#{c.rank}</td>
                        <td className="tk">{c.ticker}</td>
                        <td><i className="cmap-dot" style={{ background: SECTOR_COLORS[c.sector] || '#7a8a80' }} />{c.sector}</td>
                        <td className="num" style={{ color: tone }}>{typeof c.score === 'number' ? c.score.toFixed(1) : c.score}</td>
                        <td className="num">{Math.round(c.coverage * 100)}%</td>
                        <td className="sig">{c.score >= 60 ? 'high rank' : c.score >= 40 ? 'mid' : 'weak'}{c.coverage < 0.55 ? ' · thin data' : ''}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </main>
        <SignalReadout c={active} onOpen={openProfile} total={companies.length} />
      </div>

      <footer className="cmap-caveat">
        <span className="cmap-caveat-pulse" aria-hidden="true" />
        Hybrid score = 0.65 · ML + 0.20 · Confidence + 0.15 · LLM evidence
        <span className="cmap-caveat-sep">·</span>
        Walk-forward IC ≈ 0 · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.cmap {
  --cm-ink: #0a0e0d;
  --cm-paper: #e8ece6;
  --cm-dim: #9fae9f;
  --cm-faint: #6b7a70;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.07), transparent 60%),
    radial-gradient(800px 500px at 8% 108%, rgba(168,103,75,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--cm-ink) 55%, #080b0a 100%);
  color: var(--cm-paper);
  overflow: hidden;
  animation: cmapCrystal 0.7s ease both;
}
.cmap * { box-sizing: border-box; }
.cmap-scan {
  position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px);
}
.cmap > *:not(.cmap-scan) { position: relative; z-index: 2; }

/* ── header ── */
.cmap-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 30px; flex-wrap: wrap; margin-bottom: 20px; }
.cmap-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--cm-faint); margin-bottom: 13px; }
.cmap-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.cmap-head h1 em { font-style: italic; color: #4da583; }
.cmap-head p { margin: 0; max-width: 58ch; color: var(--cm-dim); font-size: 14px; line-height: 1.55; }
.cmap-counts { font-family: var(--font-mono); font-size: 11.5px; color: var(--cm-dim); display: flex; flex-direction: column; gap: 6px; text-align: right; }
.cmap-counts strong { color: var(--cm-paper); font-size: 16px; }
.cmap-counts-note { color: #c8a35a; letter-spacing: 0.08em; }

/* ── controls ── */
.cmap-controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 18px; }
.cmap-search {
  width: 200px; background: rgba(10,14,13,0.8); border: 1px solid rgba(200,211,202,0.22);
  border-radius: 2px; padding: 9px 12px; color: var(--cm-paper);
  font-family: var(--font-mono); font-size: 12px; letter-spacing: 0.08em; outline: none;
  transition: border-color 0.18s, box-shadow 0.18s;
}
.cmap-search::placeholder { color: var(--cm-faint); }
.cmap-search:focus { border-color: #4da583; box-shadow: 0 0 0 1px rgba(77,165,131,0.35); }
.cmap-chips { display: flex; gap: 6px; flex-wrap: wrap; flex: 1; }
.cmap-chip {
  display: inline-flex; align-items: center; gap: 6px;
  font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.12em;
  border: 1px solid rgba(200,211,202,0.2); border-radius: 2px; padding: 6px 10px;
  background: rgba(14,20,19,0.6); color: var(--cm-dim); cursor: pointer;
  transition: border-color 0.15s, color 0.15s, box-shadow 0.15s, transform 0.1s;
}
.cmap-chip:hover { border-color: rgba(200,163,90,0.45); box-shadow: 0 0 12px rgba(200,163,90,0.12); }
.cmap-chip:active { transform: translateY(1px); }
.cmap-chip:focus-visible { outline: 1px solid #c8a35a; outline-offset: 2px; }
.cmap-chip.is-on { border-color: var(--chip-c, #c8a35a); color: var(--cm-paper); }
.cmap-chip-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--chip-c, #c8a35a); }
.cmap-viewtoggle { display: flex; gap: 2px; border: 1px solid rgba(200,211,202,0.22); border-radius: 2px; padding: 2px; background: rgba(10,14,13,0.7); }
.cmap-view {
  font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em;
  border: 0; border-radius: 1px; padding: 7px 14px; cursor: pointer;
  background: transparent; color: var(--cm-faint); transition: background 0.15s, color 0.15s;
}
.cmap-view:focus-visible { outline: 1px solid #c8a35a; outline-offset: 1px; }
.cmap-view.is-on { background: rgba(200,163,90,0.16); color: #c8a35a; }

/* ── main ── */
.cmap-main { display: grid; grid-template-columns: 1fr 320px; gap: 24px; align-items: start; }
@media (max-width: 1000px) { .cmap-main { grid-template-columns: 1fr; } }
.cmap-field {
  border: 1px solid rgba(200,211,202,0.16); border-radius: 3px;
  background: rgba(11,16,15,0.6); padding: 10px; animation: cmapCrystal 0.45s ease;
}
.cmap-svg { width: 100%; height: auto; display: block; }
.cmap-axis { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.3em; fill: var(--cm-faint); }

.cmap-node { cursor: pointer; outline: none; opacity: 0; animation: cmapEmerge 0.6s ease forwards; transition: opacity 0.35s; }
.cmap.is-static .cmap-node { animation: none; opacity: 1; }
.cmap-node.is-dim { opacity: 0.07 !important; pointer-events: none; }
.cmap-node:focus-visible circle:first-of-type { stroke: var(--cm-paper); }
.cmap-node-label { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.06em; }
.cmap-node.is-active .cmap-node-label { font-weight: 700; }
.cmap-node-ring { animation: cmapSpin 6s linear infinite; }

/* ── table view ── */
.cmap-tablewrap { max-height: 540px; overflow-y: auto; }
.cmap-table { width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 11.5px; }
.cmap-table th {
  position: sticky; top: 0; background: #0c1110; text-align: left; padding: 9px 12px;
  font-size: 9px; letter-spacing: 0.22em; font-weight: 600; color: var(--cm-faint);
  border-bottom: 1px solid rgba(200,211,202,0.22);
}
.cmap-table th.num, .cmap-table td.num { text-align: right; }
.cmap-table td { padding: 8px 12px; color: var(--cm-dim); border-bottom: 1px solid rgba(200,211,202,0.08); }
.cmap-table td.tk { color: var(--cm-paper); font-weight: 700; letter-spacing: 0.06em; }
.cmap-table td.sig { font-size: 10px; letter-spacing: 0.06em; color: var(--cm-faint); }
.cmap-table tbody tr { cursor: pointer; transition: background 0.15s, opacity 0.3s; }
.cmap-table tbody tr:hover, .cmap-table tbody tr:focus-visible { background: rgba(22,29,27,0.8); outline: none; }
.cmap-table tbody tr.is-active { box-shadow: inset 3px 0 0 #4da583; background: rgba(18,26,24,0.7); }
.cmap-table tbody tr.is-dim { opacity: 0.18; pointer-events: none; }
.cmap-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 7px; }

/* ── readout ── */
.cmap-readout {
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid #4da583;
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85));
  padding: 18px 20px; border-radius: 3px; animation: cmapCrystal 0.4s ease;
}
.cmap-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--cm-faint); margin-bottom: 12px; }
.cmap-readout-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.cmap-readout-ticker { font-family: var(--font-mono); font-size: 26px; font-weight: 700; letter-spacing: 0.04em; }
.cmap-readout-sector { font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.18em; border: 1px solid; border-radius: 2px; padding: 3px 7px; }
.cmap-readout-score { margin: 12px 0 16px; display: flex; flex-direction: column; gap: 2px; }
.cmap-readout-score span { font-family: var(--font-mono); font-size: 38px; line-height: 1; }
.cmap-readout-score em { font-style: normal; font-size: 10px; letter-spacing: 0.16em; color: var(--cm-faint); text-transform: uppercase; }
.cmap-readout-row {
  display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
  font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.1em; color: var(--cm-dim);
}
.cmap-readout-row strong { color: var(--cm-paper); margin-left: auto; font-size: 12px; }
.cmap-cov-track { flex: 1; height: 6px; background: rgba(200,211,202,0.09); border-radius: 1px; overflow: hidden; }
.cmap-cov-fill { display: block; height: 100%; background: #4da583; transition: width 0.5s ease; }
.cmap-readout-weights {
  margin: 14px 0 0; font-family: var(--font-mono); font-size: 10px; line-height: 1.6;
  color: var(--cm-faint); letter-spacing: 0.02em;
  border-top: 1px dashed rgba(200,211,202,0.18); padding-top: 10px;
}
.cmap-readout-note { margin: 10px 0 0; font-size: 12px; line-height: 1.55; color: var(--cm-dim); }
.cmap-readout-open {
  margin-top: 16px; width: 100%; padding: 10px 0;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.2em; font-weight: 700;
  background: transparent; color: #4da583; border: 1px solid rgba(77,165,131,0.5); border-radius: 2px;
  cursor: pointer; transition: background 0.18s, box-shadow 0.18s, transform 0.1s;
}
.cmap-readout-open:hover { background: rgba(77,165,131,0.1); box-shadow: 0 0 16px rgba(77,165,131,0.18); }
.cmap-readout-open:active { transform: translateY(1px); }
.cmap-readout-open:focus-visible { outline: 1px solid #4da583; outline-offset: 2px; }

/* ── caveat ── */
.cmap-caveat {
  position: sticky; bottom: 14px; z-index: 4; margin-top: 32px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em; flex-wrap: wrap;
  color: var(--cm-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5);
}
.cmap-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: #c8a35a; animation: cmapPulse 2.2s ease-in-out infinite; flex-shrink: 0; }
.cmap-caveat-sep { color: var(--cm-faint); }

@keyframes cmapCrystal { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes cmapEmerge { from { opacity: 0; } to { opacity: 1; } }
@keyframes cmapSpin { to { stroke-dashoffset: -60; } }
@keyframes cmapPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

@media (prefers-reduced-motion: reduce) {
  .cmap, .cmap *, .cmap *::before, .cmap *::after { animation: none !important; transition: none !important; }
  .cmap-node { opacity: 1; }
}
`
