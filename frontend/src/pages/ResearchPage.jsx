import { useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { apiErrorText } from '../api/errorText'
import { getCached, setCached } from '../utils/sessionCache'

// ---------------------------------------------------------------------------
// Score Explorer — THE DISSECTION TABLE.
// The composite score is opened up and laid flat: weighted category segments
// that unfold into constituent features. Real API data (/research/years,
// /research/scores, /research/company); mock is fallback only.
// ---------------------------------------------------------------------------

const SCORE_EXPLORER_MOCK = {
  selected_ticker: 'ASELS',
  composite_score: 78.4,
  categories: [
    {
      name: 'Profitability', weight: 0.28, score: 82.1,
      features: [
        { name: 'ROE', value: 0.187, percentile: 88, coverage: 1.0 },
        { name: 'ROA', value: 0.094, percentile: 79, coverage: 1.0 },
        { name: 'Net margin', value: 0.124, percentile: 81, coverage: 1.0 },
        { name: 'EBITDA margin', value: 0.198, percentile: 85, coverage: 0.83 },
      ],
    },
    {
      name: 'Balance Sheet', weight: 0.22, score: 74.3,
      features: [
        { name: 'Current ratio', value: 1.84, percentile: 72, coverage: 1.0 },
        { name: 'Net debt/EBITDA', value: 0.43, percentile: 78, coverage: 0.83 },
        { name: 'Equity growth', value: 0.231, percentile: 74, coverage: 1.0 },
      ],
    },
    {
      name: 'Growth', weight: 0.20, score: 79.8,
      features: [
        { name: 'Revenue growth', value: 0.342, percentile: 83, coverage: 1.0 },
        { name: 'Asset growth', value: 0.218, percentile: 71, coverage: 1.0 },
      ],
    },
    {
      name: 'Valuation', weight: 0.18, score: 71.2,
      features: [
        { name: 'P/B ratio', value: 2.14, percentile: 68, coverage: 0.67 },
        { name: 'EV/EBITDA', value: 7.8, percentile: 74, coverage: 0.67 },
        { name: 'P/E ratio', value: 11.4, percentile: 69, coverage: 0.50 },
      ],
    },
    {
      name: 'Cash Flow', weight: 0.12, score: 77.4,
      features: [
        { name: 'FCF margin', value: 0.089, percentile: 76, coverage: 0.83 },
        { name: 'OCF/assets', value: 0.112, percentile: 79, coverage: 1.0 },
      ],
    },
  ],
}

const CAT_COLORS = ['#4da583', '#5a9a8c', '#7a8a80', '#c8a35a', '#a8674b', '#8c8a5e']
const RESEARCH_PAGE_CACHE_KEY = 'page:research'
const RESEARCH_YEARS_CACHE_KEY = 'page:research:years'
const researchScoresCacheKey = (year) => `page:research:scores:${year}`
const researchDetailCacheKey = (year, ticker) => `page:research:detail:${year}:${ticker}`
const clampPct = (v) => Math.max(0, Math.min(100, Number(v) || 0))
const fmt1 = (v) => (v == null || Number.isNaN(Number(v)) ? '—' : Number(v).toFixed(1))

// Normalize real detail OR mock into one dissection structure.
function buildDissection(detail, mockMode) {
  if (mockMode) {
    return {
      ticker: SCORE_EXPLORER_MOCK.selected_ticker,
      composite: SCORE_EXPLORER_MOCK.composite_score,
      categories: SCORE_EXPLORER_MOCK.categories,
      weightsExplicit: true,
    }
  }
  if (!detail) return null
  const breakdown = Array.isArray(detail.score_breakdown) ? detail.score_breakdown : []
  const n = Math.max(breakdown.length, 1)
  return {
    ticker: detail.ticker,
    composite: Number(detail.fundamental_score) || 0,
    categories: breakdown.map((c) => ({
      name: c.category,
      weight: 1 / n,
      score: Number(c.category_score) || 0,
      features: null, // feature-level detail not exposed by this endpoint
    })),
    weightsExplicit: false,
  }
}

export default function ResearchPage() {
  const cachedPage = useMemo(() => getCached(RESEARCH_PAGE_CACHE_KEY), [])
  const cachedYears = useMemo(() => getCached(RESEARCH_YEARS_CACHE_KEY), [])
  const initialYears = cachedPage?.years?.length ? cachedPage.years : (cachedYears || [])
  const initialYear = cachedPage?.year ?? initialYears[initialYears.length - 1] ?? null
  const cachedScores = useMemo(
    () => (initialYear ? getCached(researchScoresCacheKey(initialYear)) : undefined),
    [initialYear],
  )
  const initialCompanies = cachedPage?.companies?.length ? cachedPage.companies : (cachedScores || [])
  const initialSelected = cachedPage?.selected ?? initialCompanies[0]?.ticker ?? null
  const cachedDetail = useMemo(
    () => (initialYear && initialSelected ? getCached(researchDetailCacheKey(initialYear, initialSelected)) : undefined),
    [initialYear, initialSelected],
  )
  const [years, setYears] = useState(() => initialYears)
  const [year, setYear] = useState(() => initialYear)
  const [companies, setCompanies] = useState(() => initialCompanies)
  const [selected, setSelected] = useState(() => initialSelected)
  const [detail, setDetail] = useState(() => cachedPage?.detail ?? cachedDetail ?? null)
  const [query, setQuery] = useState('')
  const [openCat, setOpenCat] = useState(null)
  const [mockMode, setMockMode] = useState(false)
  const [mockReason, setMockReason] = useState(null)

  useEffect(() => {
    let mounted = true

    api.get('/research/years')
      .then(({ data }) => {
        if (!mounted) return
        if (data?.years?.length) {
          setYears(data.years)
          setCached(RESEARCH_YEARS_CACHE_KEY, data.years)
          setYear(data.years[data.years.length - 1])
        } else if (!getCached(RESEARCH_YEARS_CACHE_KEY)?.length) setMockMode(true)
      })
      .catch((e) => {
        if (mounted && !getCached(RESEARCH_YEARS_CACHE_KEY)?.length) {
          setMockMode(true)
          setMockReason(apiErrorText(e))
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!year) return
    let mounted = true
    const cached = getCached(researchScoresCacheKey(year))

    if (cached?.length) {
      setCompanies(cached)
      setSelected((s) => (cached.some((r) => r.ticker === s) ? s : cached[0].ticker))
    }

    api.get('/research/scores', { params: { year } })
      .then(({ data }) => {
        if (!mounted) return
        const rows = (data?.companies || [])
          .slice()
          .sort((a, b) => (b.fundamental_score || 0) - (a.fundamental_score || 0))
        if (rows.length === 0) {
          if (!getCached(researchScoresCacheKey(year))?.length) setMockMode(true)
          return
        }
        setCompanies(rows)
        setCached(researchScoresCacheKey(year), rows)
        setSelected((s) => (rows.some((r) => r.ticker === s) ? s : rows[0].ticker))
      })
      .catch((e) => {
        if (mounted && !getCached(researchScoresCacheKey(year))?.length) {
          setMockMode(true)
          setMockReason(apiErrorText(e))
        }
      })

    return () => {
      mounted = false
    }
  }, [year])

  useEffect(() => {
    if (!year || !selected || mockMode) return
    let mounted = true
    const cached = getCached(researchDetailCacheKey(year, selected))

    if (cached) {
      setDetail(cached)
    } else {
      setDetail(null)
    }

    api.get('/research/company', { params: { ticker: selected, year } })
      .then(({ data }) => {
        if (!mounted) return
        setDetail(data)
        if (data) setCached(researchDetailCacheKey(year, selected), data)
      })
      .catch(() => {
        if (mounted && !cached) setDetail(null)
      })

    return () => {
      mounted = false
    }
  }, [year, selected, mockMode])

  useEffect(() => {
    if (mockMode || (!years.length && !companies.length && !detail)) return
    setCached(RESEARCH_PAGE_CACHE_KEY, {
      years,
      year,
      companies,
      selected,
      detail,
    })
  }, [years, year, companies, selected, detail, mockMode])

  const dissection = useMemo(() => buildDissection(detail, mockMode), [detail, mockMode])
  const list = mockMode
    ? [{ ticker: SCORE_EXPLORER_MOCK.selected_ticker, fundamental_score: SCORE_EXPLORER_MOCK.composite_score }]
    : companies.filter((c) => !query || c.ticker.toUpperCase().includes(query.trim().toUpperCase()))

  const openCategory = dissection?.categories?.find((c) => c.name === openCat) || null

  return (
    <div className="dx">
      <style>{CSS}</style>
      <div className="dx-scan" aria-hidden="true" />

      <header className="dx-head">
        <div>
          <div className="dx-kicker">FINANCEIQ · SCORE DISSECTION TABLE</div>
          <h1>The score, <em>opened up</em>.</h1>
          <p>
            A composite research score is not a number — it is a weighted structure. This table lays it
            flat: categories, constituent features, coverage. Diagnostic ranking signal only;
            walk-forward IC ≈ 0, so no predictive claim travels with it.
          </p>
        </div>
        {!mockMode && years.length > 0 && (
          <label className="dx-yearbox">
            EVALUATION YEAR
            <select value={year || ''} onChange={(e) => setYear(Number(e.target.value))}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
          </label>
        )}
        {mockMode && <div className="dx-mocknote">demo data — {mockReason || 'research API returned no usable rows'}</div>}
      </header>

      <div className="dx-main">
        {/* ── ticker rail ── */}
        <nav className="dx-rail" aria-label="Ticker selector">
          <div className="dx-rail-label">UNIVERSE · {list.length}</div>
          <input
            className="dx-rail-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="FILTER…"
            aria-label="Filter ticker"
            disabled={mockMode}
          />
          <div className="dx-rail-list">
            {list.map((c) => {
              const on = c.ticker === (dissection?.ticker || selected)
              return (
                <button
                  key={c.ticker}
                  type="button"
                  className={`dx-rail-item ${on ? 'is-on' : ''}`}
                  aria-pressed={on}
                  onClick={() => { setSelected(c.ticker); setOpenCat(null) }}
                >
                  <span>{c.ticker}</span>
                  <strong>{fmt1(c.fundamental_score)}</strong>
                </button>
              )
            })}
          </div>
        </nav>

        {/* ── dissection ── */}
        <main className="dx-table">
          {dissection ? (
            <>
              <div className="dx-specimen-head">
                <span className="dx-specimen-ticker">{dissection.ticker}</span>
                <span className="dx-specimen-score">{fmt1(dissection.composite)}<em>/100 COMPOSITE</em></span>
              </div>

              <div className="dx-bar" role="group" aria-label="Composite score segments">
                {dissection.categories.map((cat, i) => {
                  const on = openCat === cat.name
                  return (
                    <button
                      key={cat.name}
                      type="button"
                      className={`dx-seg ${on ? 'is-open' : ''}`}
                      style={{ flexGrow: Math.max(cat.weight, 0.05) * 100, '--seg-c': CAT_COLORS[i % CAT_COLORS.length] }}
                      aria-expanded={on}
                      onClick={() => setOpenCat(on ? null : cat.name)}
                    >
                      <span className="dx-seg-fill" style={{ height: `${clampPct(cat.score)}%` }} />
                      <span className="dx-seg-name">{cat.name.toUpperCase()}</span>
                      <span className="dx-seg-meta">
                        {dissection.weightsExplicit ? `w ${cat.weight.toFixed(2)}` : 'equal display w'} · {fmt1(cat.score)}
                      </span>
                    </button>
                  )
                })}
                {dissection.categories.length === 0 && (
                  <div className="dx-empty">No category breakdown available for this ticker/year.</div>
                )}
              </div>
              <div className="dx-bar-axis"><span>0</span><span>segment fill = category score</span><span>100</span></div>

              {/* unfolded segment */}
              {openCategory && (
                <div className="dx-unfold" key={openCategory.name}>
                  <div className="dx-unfold-head">
                    <span>{openCategory.name.toUpperCase()} · UNFOLDED</span>
                    <span>category score {fmt1(openCategory.score)}</span>
                  </div>
                  {openCategory.features ? openCategory.features.map((f) => (
                    <div key={f.name} className={`dx-feature ${f.coverage < 0.7 ? 'is-grainy' : ''}`}>
                      <span className="dx-feature-name">{f.name}</span>
                      <span className="dx-feature-val">{Number(f.value).toFixed(3)}</span>
                      <span className="dx-feature-track">
                        <span className="dx-feature-fill" style={{ width: `${clampPct(f.percentile)}%` }} />
                      </span>
                      <span className="dx-feature-pct">p{f.percentile}</span>
                      <span className="dx-feature-cov">{Math.round(f.coverage * 100)}% cov</span>
                    </div>
                  )) : (
                    <p className="dx-unfold-note">
                      Feature-level constituents are not exposed by this endpoint — the category score
                      above is the finest validated granularity for live data.
                    </p>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="dx-empty">Loading dissection…</div>
          )}
        </main>

        {/* ── Signal Readout ── */}
        <aside className="dx-readout" key={dissection?.ticker || 'none'} aria-live="polite">
          <div className="dx-readout-kicker">SIGNAL READOUT</div>
          {dissection && (
            <>
              <div className="dx-readout-ticker">{dissection.ticker}</div>
              <div className="dx-readout-score">{fmt1(dissection.composite)}<em>COMPOSITE RESEARCH SCORE</em></div>
              {mockMode ? (
                <>
                  {SCORE_EXPLORER_MOCK.categories.map((c, i) => (
                    <div key={c.name} className="dx-readout-row">
                      <i style={{ background: CAT_COLORS[i % CAT_COLORS.length] }} />
                      <span>{c.name}</span>
                      <strong>{fmt1(c.score)} · w {c.weight.toFixed(2)}</strong>
                    </div>
                  ))}
                  <p className="dx-readout-note">
                    Low-coverage features render grainy: P/E at 50% coverage is the weakest specimen here.
                  </p>
                </>
              ) : detail ? (
                <>
                  <div className="dx-readout-row"><span>REALIZED RETURN ({detail.year})</span><strong>{detail.realized_return != null ? `${Number(detail.realized_return).toFixed(1)}%` : '—'}</strong></div>
                  <div className="dx-readout-row"><span>SCORE RANK</span><strong>#{detail.score_rank ?? '—'} / {detail.total_companies ?? '—'}</strong></div>
                  <div className="dx-readout-row"><span>RETURN RANK</span><strong>#{detail.return_rank ?? '—'} / {detail.total_companies ?? '—'}</strong></div>
                  <div className="dx-readout-row"><span>VS BIST100</span><strong>{detail.excess_vs_bist100 != null ? `${Number(detail.excess_vs_bist100).toFixed(1)}%` : 'n/a'}</strong></div>
                  <p className="dx-readout-note">
                    Same-year alignment between score and return is a diagnostic, not a forecast.
                  </p>
                </>
              ) : (
                <p className="dx-readout-note">Loading company detail…</p>
              )}
            </>
          )}
        </aside>
      </div>

      <footer className="dx-caveat">
        <span className="dx-caveat-pulse" aria-hidden="true" />
        Walk-forward IC ≈ 0 · Score is a ranking structure, not a prediction · Research only · Not investment advice
      </footer>
    </div>
  )
}

const CSS = `
.dx {
  --dx-ink: #0a0e0d;
  --dx-paper: #e8ece6;
  --dx-dim: #9fae9f;
  --dx-faint: #6b7a70;
  --dx-emerald: #4da583;
  --dx-gold: #c8a35a;
  --dx-copper: #a8674b;
  position: relative;
  margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px));
  padding: 34px clamp(22px, 3vw, 52px) 86px;
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.06), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--dx-ink) 55%, #080b0a 100%);
  color: var(--dx-paper);
  overflow: hidden;
  animation: dxIn 0.7s ease both;
}
.dx * { box-sizing: border-box; }
.dx-scan { position: absolute; inset: 0; pointer-events: none; z-index: 1;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px); }
.dx > *:not(.dx-scan) { position: relative; z-index: 2; }

.dx-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 28px; flex-wrap: wrap; margin-bottom: 24px; }
.dx-kicker { font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em; color: var(--dx-faint); margin-bottom: 13px; }
.dx-head h1 { margin: 0 0 10px; font-size: clamp(26px, 3vw, 40px); line-height: 1.05; font-weight: 650; letter-spacing: -0.015em; }
.dx-head h1 em { font-style: italic; color: var(--dx-emerald); }
.dx-head p { margin: 0; max-width: 62ch; color: var(--dx-dim); font-size: 14px; line-height: 1.55; }
.dx-yearbox { display: flex; flex-direction: column; gap: 6px; font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.24em; color: var(--dx-faint); }
.dx-yearbox select { background: rgba(10,14,13,0.8); border: 1px solid rgba(200,211,202,0.22); border-radius: 2px;
  color: var(--dx-paper); font-family: var(--font-mono); font-size: 13px; padding: 8px 10px; outline: none; }
.dx-yearbox select:focus { border-color: var(--dx-emerald); }
.dx-mocknote { font-family: var(--font-mono); font-size: 10px; color: var(--dx-copper);
  border: 1px dashed rgba(168,103,75,0.45); border-radius: 2px; padding: 8px 12px; }

.dx-main { display: grid; grid-template-columns: 190px 1fr 300px; gap: 22px; align-items: start; }
@media (max-width: 1100px) { .dx-main { grid-template-columns: 1fr; } }

/* rail */
.dx-rail { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 12px; }
.dx-rail-label { font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.26em; color: var(--dx-faint); margin-bottom: 9px; }
.dx-rail-search { width: 100%; background: rgba(10,14,13,0.8); border: 1px solid rgba(200,211,202,0.2); border-radius: 2px;
  color: var(--dx-paper); font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.08em; padding: 7px 9px; outline: none; margin-bottom: 9px; }
.dx-rail-search:focus { border-color: var(--dx-emerald); }
.dx-rail-list { max-height: 480px; overflow-y: auto; display: flex; flex-direction: column; gap: 3px; }
.dx-rail-item { display: flex; justify-content: space-between; gap: 8px; padding: 7px 9px;
  border: 1px solid transparent; border-radius: 2px; background: transparent; cursor: pointer;
  font-family: var(--font-mono); font-size: 11px; color: var(--dx-dim); transition: background 0.15s, border-color 0.15s; }
.dx-rail-item:hover, .dx-rail-item:focus-visible { background: rgba(22,29,27,0.8); outline: none; }
.dx-rail-item.is-on { border-color: var(--dx-emerald); color: var(--dx-paper); box-shadow: inset 2px 0 0 var(--dx-emerald); }
.dx-rail-item strong { color: var(--dx-gold); }

/* dissection */
.dx-table { border: 1px solid rgba(200,211,202,0.16); border-radius: 3px; background: rgba(11,16,15,0.6); padding: 18px 20px; min-height: 380px; }
.dx-specimen-head { display: flex; justify-content: space-between; align-items: baseline; gap: 14px; margin-bottom: 16px; flex-wrap: wrap; }
.dx-specimen-ticker { font-family: var(--font-mono); font-size: 24px; font-weight: 700; letter-spacing: 0.05em; }
.dx-specimen-score { font-family: var(--font-mono); font-size: 24px; color: var(--dx-emerald); }
.dx-specimen-score em { font-style: normal; font-size: 9px; letter-spacing: 0.2em; color: var(--dx-faint); margin-left: 8px; }

.dx-bar { display: flex; gap: 3px; height: 110px; }
.dx-seg { position: relative; display: flex; flex-direction: column; justify-content: flex-end; overflow: hidden;
  border: 1px solid rgba(200,211,202,0.18); border-radius: 2px; background: rgba(8,11,10,0.6);
  cursor: pointer; padding: 7px 9px; min-width: 70px; color: inherit; font: inherit; text-align: left;
  transition: border-color 0.18s, box-shadow 0.18s, transform 0.1s; }
.dx-seg:hover { border-color: var(--seg-c); box-shadow: 0 0 14px rgba(200,163,90,0.1); }
.dx-seg:active { transform: translateY(1px); }
.dx-seg:focus-visible { outline: 1px solid var(--seg-c); outline-offset: 2px; }
.dx-seg.is-open { border-color: var(--seg-c); box-shadow: inset 0 -3px 0 var(--seg-c); }
.dx-seg-fill { position: absolute; left: 0; right: 0; bottom: 0; background: var(--seg-c); opacity: 0.22; transition: height 0.5s ease; }
.dx-seg-name { position: relative; font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.16em; color: var(--dx-paper); }
.dx-seg-meta { position: relative; font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.04em; color: var(--dx-dim); margin-top: 3px; }
.dx-bar-axis { display: flex; justify-content: space-between; margin-top: 6px;
  font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.18em; color: var(--dx-faint); }

.dx-unfold { margin-top: 18px; border-top: 1px dashed rgba(200,211,202,0.2); padding-top: 14px; animation: dxIn 0.35s ease; }
.dx-unfold-head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 9.5px; letter-spacing: 0.2em; color: var(--dx-faint); margin-bottom: 12px; }
.dx-feature { display: grid; grid-template-columns: 130px 64px 1fr 38px 64px; gap: 10px; align-items: center;
  font-family: var(--font-mono); padding: 6px 0; border-bottom: 1px solid rgba(200,211,202,0.07); }
.dx-feature.is-grainy { opacity: 0.65; }
.dx-feature.is-grainy .dx-feature-track { border: 1px dashed rgba(200,211,202,0.3); }
.dx-feature-name { font-size: 11px; color: var(--dx-paper); }
.dx-feature-val { font-size: 10.5px; color: var(--dx-dim); text-align: right; }
.dx-feature-track { position: relative; height: 6px; background: rgba(200,211,202,0.08); border-radius: 1px; overflow: hidden; }
.dx-feature-fill { display: block; height: 100%; background: var(--dx-emerald); transition: width 0.5s ease; }
.dx-feature-pct { font-size: 10px; color: var(--dx-gold); text-align: right; }
.dx-feature-cov { font-size: 9px; color: var(--dx-faint); text-align: right; letter-spacing: 0.04em; }
.dx-unfold-note { margin: 0; font-size: 12px; line-height: 1.55; color: var(--dx-dim); }
.dx-empty { font-family: var(--font-mono); font-size: 12px; color: var(--dx-faint); padding: 20px 0; }

/* readout */
.dx-readout { border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--dx-emerald);
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.85)); padding: 18px 20px; border-radius: 3px; animation: dxIn 0.35s ease; }
.dx-readout-kicker { font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.32em; color: var(--dx-faint); margin-bottom: 12px; }
.dx-readout-ticker { font-family: var(--font-mono); font-size: 24px; font-weight: 700; letter-spacing: 0.05em; }
.dx-readout-score { font-family: var(--font-mono); font-size: 34px; color: var(--dx-emerald); margin: 10px 0 16px;
  display: flex; flex-direction: column; gap: 3px; line-height: 1; }
.dx-readout-score em { font-style: normal; font-size: 9px; letter-spacing: 0.2em; color: var(--dx-faint); }
.dx-readout-row { display: flex; align-items: center; gap: 9px; font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.08em; color: var(--dx-dim); border-top: 1px dashed rgba(200,211,202,0.14); padding: 8px 0; }
.dx-readout-row i { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dx-readout-row strong { margin-left: auto; color: var(--dx-paper); font-size: 11.5px; }
.dx-readout-note { margin: 12px 0 0; font-size: 11.5px; line-height: 1.55; color: var(--dx-dim); }

.dx-caveat { position: sticky; bottom: 14px; z-index: 4; margin-top: 28px;
  display: flex; align-items: center; gap: 10px; width: fit-content; max-width: 100%; flex-wrap: wrap;
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.08em;
  color: var(--dx-paper); background: rgba(10,14,13,0.92);
  border: 1px solid rgba(200,163,90,0.5); border-radius: 2px; padding: 9px 16px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.5); }
.dx-caveat-pulse { width: 7px; height: 7px; border-radius: 50%; background: var(--dx-gold); animation: dxPulse 2.2s ease-in-out infinite; flex-shrink: 0; }

@keyframes dxIn { from { opacity: 0; filter: blur(6px); } to { opacity: 1; filter: blur(0); } }
@keyframes dxPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@media (prefers-reduced-motion: reduce) {
  .dx, .dx *, .dx *::before, .dx *::after { animation: none !important; transition: none !important; }
}
`
