import { useState } from 'react'
import researchApi from '../api/researchApi'

const PERSONA_COPY = {
  bull: { index: '01', accent: 'emerald' },
  bear: { index: '02', accent: 'copper' },
  skeptic: { index: '03', accent: 'gold' },
  risk: { index: '04', accent: 'risk' },
}

const formatValue = (value) => {
  if (Array.isArray(value)) return value.length ? value.join(', ') : '[]'
  if (value && typeof value === 'object') return JSON.stringify(value)
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(4).replace(/0+$/, '').replace(/\.$/, '')
  if (value === null || value === undefined) return 'null'
  return String(value)
}

function riskLast(personas) {
  if (!Array.isArray(personas)) return []
  return [
    ...personas.filter((persona) => persona.persona_id !== 'risk'),
    ...personas.filter((persona) => persona.persona_id === 'risk'),
  ]
}

function CitationChip({ citation }) {
  return (
    <div className="cq-citation" title={citation.source_file}>
      <span>{citation.field}</span>
      <strong>{formatValue(citation.value)}</strong>
      <small>{citation.source_file}</small>
    </div>
  )
}

function PersonaPanel({ persona }) {
  const copy = PERSONA_COPY[persona.persona_id] || { index: '—', accent: 'neutral' }
  return (
    <section className={`cq-persona is-${copy.accent}`} aria-labelledby={`cq-${persona.persona_id}`}>
      <header>
        <span className="cq-persona-index">{copy.index}</span>
        <div>
          <div className="cq-persona-type">EVIDENCE LENS</div>
          <h2 id={`cq-${persona.persona_id}`}>{persona.name}</h2>
          <p>{persona.lens}</p>
        </div>
        <span className="cq-budget">{persona.items.length} CITED ITEMS</span>
      </header>

      <ol>
        {persona.items.map((item) => (
          <li key={`${persona.persona_id}-${item.citation.field}`}>
            <p>{item.statement}</p>
            <CitationChip citation={item.citation} />
            <div className="cq-limitation"><strong>LIMITATION</strong><span>{item.limitation}</span></div>
          </li>
        ))}
      </ol>
    </section>
  )
}

function InsufficientData({ report }) {
  return (
    <section className="cq-insufficient" role="status">
      <div className="cq-stamp">INSUFFICIENT_DATA</div>
      <h2>No evidence arguments were created.</h2>
      <p>One or more required repository artifacts are missing or malformed. Missing evidence stays missing.</p>
      <ul>
        {(report?.missing_evidence || []).map((item) => (
          <li key={`${item.source_file}-${item.reason}`}>
            <strong>{item.source_file}</strong>
            <span>{item.reason}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function CourtroomPage() {
  const [ticker, setTicker] = useState('')
  const [year, setYear] = useState('')
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)
  const personas = riskLast(report?.personas)

  const submit = async (event) => {
    event.preventDefault()
    const normalized = ticker.trim().toUpperCase()
    if (!normalized) {
      setError('Ticker is required.')
      return
    }
    setLoading(true)
    setError(null)
    setReport(null)
    const { data, error: requestError } = await researchApi.courtroom(normalized, year || null)
    setLoading(false)
    if (data) setReport(data)
    else setError(requestError || 'Courtroom evidence request failed.')
  }

  return (
    <div className="cq">
      <style>{CSS}</style>
      <div className="cq-grid" aria-hidden="true" />

      <header className="cq-hero">
        <div>
          <div className="cq-kicker">FINANCEIQ · RESEARCH COURTROOM</div>
          <h1>Evidence can disagree <em>without adjudication.</em></h1>
          <p>
            Bull, Bear, Skeptic, and Risk are deterministic views over named repository artifacts.
            Each statement remains attached to its field, value, source file, and limitation.
          </p>
        </div>
        <div className="cq-guardrail">
          <span>STRUCTURAL GUARDRAIL</span>
          <strong>Four equal evidence budgets · Risk always last · no uncited prose</strong>
          <small>Historical research support only · Not investment advice.</small>
        </div>
      </header>

      <form className="cq-docket" onSubmit={submit}>
        <label>
          <span>TICKER</span>
          <input
            value={ticker}
            onChange={(event) => setTicker(event.target.value.toUpperCase())}
            placeholder="ASELS"
            maxLength={16}
            autoComplete="off"
          />
        </label>
        <label>
          <span>CONTEXT YEAR · OPTIONAL</span>
          <input
            value={year}
            onChange={(event) => setYear(event.target.value)}
            placeholder="latest"
            inputMode="numeric"
            pattern="[0-9]{4}"
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'READING ARTIFACTS…' : 'OPEN EVIDENCE DOCKET'}
        </button>
        {report?.status === 'complete' && (
          <div className="cq-loaded">
            <span>DETERMINISTIC · {report.ticker} · {report.year}</span>
            <strong>{report.evidence_budget_per_persona} ITEMS PER LENS</strong>
          </div>
        )}
      </form>

      {error && <div className="cq-error" role="alert">{error}</div>}

      {report?.status === 'insufficient_data' && <InsufficientData report={report} />}

      {report?.status === 'complete' && (
        <main className="cq-personas">
          {personas.map((persona) => <PersonaPanel key={persona.persona_id} persona={persona} />)}
        </main>
      )}

      {report?.closing && (
        <footer className="cq-closing">
          <span>TERMINAL STATE · NO ADJUDICATION SLOT</span>
          <strong>{report.closing}</strong>
        </footer>
      )}
    </div>
  )
}

const CSS = `
.cq {
  --cq-paper: #e8ece6; --cq-dim: #9caaa0; --cq-faint: #65736a;
  --cq-emerald: #4da583; --cq-gold: #c8a35a; --cq-copper: #a8674b;
  position: relative; margin: -30px calc(-1 * clamp(18px, 2.4vw, 38px)) -56px;
  min-height: calc(100vh - var(--topbar-h, 0px)); padding: 38px clamp(22px, 3vw, 52px) 100px;
  color: var(--cq-paper); overflow: visible;
  background: radial-gradient(800px 520px at 50% -12%, rgba(200,163,90,.08), transparent 64%),
    linear-gradient(155deg, #0b100f 0%, #080c0b 62%, #070908 100%);
}
.cq * { box-sizing: border-box; }
.cq-grid { position: absolute; inset: 0; pointer-events: none; opacity: .28;
  background-image: linear-gradient(rgba(232,236,230,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(232,236,230,.025) 1px, transparent 1px);
  background-size: 30px 30px; }
.cq > *:not(.cq-grid) { position: relative; z-index: 1; }
.cq-hero { display: flex; align-items: flex-end; justify-content: space-between; gap: 28px; flex-wrap: wrap; max-width: 1240px; }
.cq-kicker, .cq-guardrail, .cq-docket, .cq-persona-type, .cq-persona-index, .cq-budget, .cq-citation, .cq-limitation, .cq-closing, .cq-stamp { font-family: var(--font-mono); }
.cq-kicker { color: var(--cq-gold); font-size: 10px; letter-spacing: .33em; margin-bottom: 12px; }
.cq-hero h1 { margin: 0 0 12px; font-size: clamp(30px, 4vw, 52px); line-height: 1; font-weight: 620; letter-spacing: -.03em; }
.cq-hero h1 em { color: var(--cq-gold); font-weight: 500; }
.cq-hero p { max-width: 73ch; margin: 0; color: var(--cq-dim); font-size: 13.5px; line-height: 1.7; }
.cq-guardrail { width: min(350px, 100%); padding: 14px 16px; display: grid; gap: 7px; border: 1px solid rgba(200,163,90,.25); border-left: 3px solid var(--cq-gold); background: rgba(11,15,13,.84); }
.cq-guardrail span { color: var(--cq-gold); font-size: 8.5px; letter-spacing: .2em; }
.cq-guardrail strong { color: var(--cq-paper); font-size: 10px; line-height: 1.5; }
.cq-guardrail small { color: var(--cq-faint); font-size: 8.5px; }
.cq-docket { display: grid; grid-template-columns: minmax(160px, 1fr) minmax(180px, .7fr) auto minmax(200px, 1fr); gap: 12px; align-items: end; max-width: 1240px; margin: 28px 0 20px; padding: 15px; border: 1px solid rgba(232,236,230,.14); background: rgba(10,14,12,.78); }
.cq-docket label { display: grid; gap: 6px; }
.cq-docket label > span { color: var(--cq-faint); font-size: 8px; letter-spacing: .16em; }
.cq-docket input { width: 100%; min-height: 39px; padding: 9px 11px; border: 1px solid rgba(232,236,230,.18); background: #0b100e; color: var(--cq-paper); font: 12px var(--font-mono); outline: none; }
.cq-docket input:focus { border-color: var(--cq-gold); box-shadow: 0 0 0 2px rgba(200,163,90,.08); }
.cq-docket button { min-height: 39px; padding: 9px 16px; border: 1px solid rgba(200,163,90,.5); background: rgba(200,163,90,.12); color: var(--cq-gold); font: 700 9px var(--font-mono); letter-spacing: .12em; cursor: pointer; }
.cq-docket button:disabled { opacity: .55; cursor: wait; }
.cq-loaded { align-self: stretch; display: grid; align-content: center; gap: 5px; padding-left: 12px; border-left: 1px solid rgba(232,236,230,.12); }
.cq-loaded span { color: var(--cq-emerald); font-size: 8.5px; }
.cq-loaded strong { color: var(--cq-dim); font-size: 9px; }
.cq-error { max-width: 1240px; padding: 13px 15px; border: 1px solid rgba(168,103,75,.5); color: #dc987a; background: rgba(168,103,75,.08); font: 11px var(--font-mono); }
.cq-personas { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 17px; max-width: 1240px; align-items: start; }
.cq-persona { --accent: var(--cq-dim); border: 1px solid rgba(232,236,230,.15); border-top: 2px solid var(--accent); background: rgba(10,15,13,.92); padding: 18px; min-width: 0; box-shadow: 0 15px 42px rgba(0,0,0,.17); }
.cq-persona.is-emerald { --accent: var(--cq-emerald); }
.cq-persona.is-copper { --accent: var(--cq-copper); }
.cq-persona.is-gold { --accent: var(--cq-gold); }
.cq-persona.is-risk { --accent: #d47d5a; grid-column: 1 / -1; border-width: 1px 1px 2px; box-shadow: 0 -12px 38px rgba(0,0,0,.42); }
.cq-persona > header { display: grid; grid-template-columns: auto 1fr auto; gap: 13px; align-items: start; padding-bottom: 13px; border-bottom: 1px solid rgba(232,236,230,.1); }
.cq-persona-index { color: var(--accent); font-size: 26px; line-height: 1; }
.cq-persona-type { color: var(--accent); font-size: 8px; letter-spacing: .22em; }
.cq-persona h2 { margin: 4px 0 2px; font-size: 20px; }
.cq-persona header p { margin: 0; color: var(--cq-faint); font-size: 10px; }
.cq-budget { color: var(--cq-faint); font-size: 8px; padding: 5px 7px; border: 1px solid rgba(232,236,230,.1); }
.cq-persona ol { margin: 0; padding: 0; list-style: none; }
.cq-persona li { padding: 14px 0; border-bottom: 1px dashed rgba(232,236,230,.1); }
.cq-persona li:last-child { border-bottom: 0; padding-bottom: 0; }
.cq-persona li > p { margin: 0 0 10px; color: var(--cq-paper); font-size: 12px; line-height: 1.65; }
.cq-citation { display: grid; grid-template-columns: minmax(140px, .9fr) minmax(90px, .45fr) minmax(170px, 1fr); gap: 8px; align-items: center; padding: 8px 9px; border: 1px solid rgba(77,165,131,.17); background: rgba(77,165,131,.055); font-size: 8px; }
.cq-citation span { color: var(--cq-emerald); overflow-wrap: anywhere; }
.cq-citation strong { color: var(--cq-dim); font-weight: 500; overflow-wrap: anywhere; }
.cq-citation small { color: var(--cq-faint); overflow-wrap: anywhere; }
.cq-limitation { display: grid; grid-template-columns: auto 1fr; gap: 8px; margin-top: 8px; color: var(--cq-faint); font-size: 8px; line-height: 1.5; }
.cq-limitation strong { color: var(--cq-copper); letter-spacing: .11em; }
.cq-insufficient { max-width: 1240px; min-height: 300px; display: grid; place-content: center; gap: 10px; text-align: center; padding: 30px; border: 1px dashed rgba(168,103,75,.55); background: rgba(18,12,10,.52); }
.cq-stamp { color: var(--cq-copper); font-size: 10px; letter-spacing: .25em; }
.cq-insufficient h2 { margin: 0; font-size: 21px; }
.cq-insufficient p { margin: 0; color: var(--cq-dim); font-size: 12px; }
.cq-insufficient ul { margin: 8px 0 0; padding: 0; list-style: none; display: grid; gap: 7px; }
.cq-insufficient li { display: grid; gap: 3px; color: var(--cq-faint); font: 9px var(--font-mono); }
.cq-insufficient li strong { color: var(--cq-paper); }
.cq-closing { max-width: 1240px; margin-top: 20px; padding: 16px 18px; display: grid; gap: 7px; border: 1px solid rgba(200,163,90,.42); border-left: 4px solid var(--cq-gold); background: rgba(16,14,9,.9); }
.cq-closing span { color: var(--cq-gold); font-size: 8px; letter-spacing: .2em; }
.cq-closing strong { color: var(--cq-paper); font-size: 11px; line-height: 1.6; }
@media (max-width: 980px) { .cq-docket { grid-template-columns: 1fr 1fr; } .cq-loaded { border-left: 0; padding-left: 0; } }
@media (max-width: 760px) { .cq-personas { grid-template-columns: 1fr; } .cq-persona.is-risk { grid-column: auto; position: relative; bottom: auto; } .cq-citation { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .cq-docket { grid-template-columns: 1fr; } .cq-persona > header { grid-template-columns: auto 1fr; } .cq-budget { grid-column: 2; justify-self: start; } }
@media (prefers-reduced-motion: reduce) { .cq, .cq * { animation: none !important; transition: none !important; } }
`
