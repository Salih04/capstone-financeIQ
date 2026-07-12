import { useMemo } from 'react'
import { useCachedResource, CACHE_TTL } from '../api/useCachedResource'


const STATEMENT = '2020–2025 spans a single extraordinary Turkish macro regime (high inflation, deep TRY depreciation). Model behavior across regimes is therefore untested — this lens shows regime context and will only compute regime-conditional diagnostics when regime diversity exists.'

const METRICS = [
  ['cpi_december_yoy_pct', 'CPI YoY', '%'],
  ['policy_rate_year_end_pct', 'Policy rate', '%'],
  ['usdtry_year_end_try_per_usd', 'TRY / USD', ''],
  ['bist100_return_pct', 'BIST100', '%'],
]

const displayValue = (metric, suffix) => {
  const value = Number(metric?.value)
  return Number.isFinite(value) ? `${value.toFixed(1)}${suffix}` : '—'
}

export default function RegimeStrip({ years = [] }) {
  const { data, error } = useCachedResource('/research/regime-context', { ttlMs: CACHE_TTL.LONG })
  const rows = useMemo(() => {
    const selected = new Set(years.map(Number))
    return (data?.macro_context || []).filter((row) => selected.has(Number(row.year)))
  }, [data, years])

  return (
    <section className="rl" aria-label="Descriptive macro regime context">
      <style>{CSS}</style>
      <div className="rl-head">
        <span>REGIME LENS · DESCRIPTIVE CONTEXT ONLY</span>
        <span>{data?.conditional_diagnostics?.status || 'context report unavailable'}</span>
      </div>
      <strong className="rl-statement">{data?.statement || STATEMENT}</strong>

      {rows.length > 0 ? (
        <div className="rl-grid" style={{ '--rl-columns': rows.length }}>
          {rows.map((row) => (
            <div className="rl-year" key={row.year}>
              <span className="rl-year-label">{row.year}</span>
              {METRICS.map(([key, label, suffix]) => {
                const metric = row[key]
                const source = metric?.source?.name || 'unsourced — value withheld'
                const effective = metric?.effective_date || 'no effective date'
                return (
                  <span className="rl-metric" key={key} title={`${source} · effective ${effective}`}>
                    <small>{label}</small>
                    <b>{displayValue(metric, suffix)}</b>
                  </span>
                )
              })}
            </div>
          ))}
        </div>
      ) : (
        <p className="rl-unavailable">
          Macro values withheld because the sourced context report is unavailable{error ? `: ${error.message || 'request failed'}` : ''}.
        </p>
      )}

      <p className="rl-foot">
        Context alignment is not causal evidence. No regime-conditional model statistic is computed with one observed regime.
      </p>
    </section>
  )
}

const CSS = `
.rl { margin-top: 18px; border: 1px solid rgba(200,163,90,0.38); border-left: 3px solid #c8a35a;
  border-radius: 3px; background: rgba(11,16,15,0.76); padding: 14px 16px; color: #e8ece6; }
.rl-head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 9px;
  font-family: var(--font-mono); font-size: 8.5px; letter-spacing: 0.18em; color: #c8a35a; text-transform: uppercase; }
.rl-statement { display: block; max-width: 1080px; font-size: 12px; line-height: 1.55; font-weight: 600; }
.rl-grid { display: grid; grid-template-columns: repeat(var(--rl-columns), minmax(122px, 1fr)); gap: 6px; margin-top: 12px; overflow-x: auto; }
.rl-year { min-width: 122px; border-top: 1px solid rgba(200,211,202,0.16); padding: 8px 7px 4px; }
.rl-year-label { display: block; margin-bottom: 7px; font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.12em; color: #9fae9f; }
.rl-metric { display: flex; justify-content: space-between; gap: 7px; padding: 3px 0; font-family: var(--font-mono); }
.rl-metric small { color: #6b7a70; font-size: 8px; letter-spacing: 0.05em; }
.rl-metric b { color: #e8ece6; font-size: 9px; font-weight: 600; }
.rl-foot, .rl-unavailable { margin: 10px 0 0; font-family: var(--font-mono); font-size: 8.5px; line-height: 1.55; color: #9fae9f; }
.rl-unavailable { color: #a8674b; }
`
