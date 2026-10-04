// ---------------------------------------------------------------------------
// Scientific record — apparent result → methodological audit → PIT correction
// → revised conclusion. Values are the committed, dated results, not mock data:
//   published   experiments/results/significance_report.md
//   audit       docs/audit/PUBLICATION_LAG_AUDIT.md (commit 838485b1)
//   corrected   experiments/results_pit_v2/report.json (registered at 079bb832)
// ---------------------------------------------------------------------------

const MDE = 0.185 // minimum detectable |IC| at 80 % power, PIT-v2 design
const MDE_TEXT = '0.19'

const BARS = [
  { key: 'pub', label: 'Published baseline', sub: 'FY-T statements from 1 Jan T+1', ic: 0.150, p: '0.017', tone: 'withdrawn' },
  { key: 'diag', label: 'FY-T statements alone', sub: 'used before publication (diagnostic)', ic: 0.193, p: '0.002', tone: 'withdrawn' },
  { key: 'pit', label: 'Point-in-time baseline', sub: 'scored after statements are public', ic: 0.031, p: '0.63', ci: [-0.100, 0.162], tone: 'current' },
  { key: 'pit-stmt', label: 'FY-T statements alone', sub: 'used after publication', ic: 0.041, p: '0.54', tone: 'current' },
]

const STEPS = [
  {
    n: '01', title: 'Apparent result',
    body: 'Published walk-forward: equal-weight baseline IC +0.150 (p = 0.017); no ML model distinguishable from chance.',
    tag: 'preserved, withdrawn',
  },
  {
    n: '02', title: 'Methodological audit',
    body: 'Fiscal-year-T statements are filed 60–70 days after year-end (FY2023: by 20 May 2024), but the return window began on 1 January. Market value also mixed adjustment bases.',
    tag: '2026-10-04',
  },
  {
    n: '03', title: 'Point-in-time correction',
    body: 'Each feature timestamped by public availability; a guard rejects anything not yet public. Signal and return start after 31 May of T+1. Registered before its outcomes.',
    tag: 'post-hoc, registered',
  },
  {
    n: '04', title: 'Revised conclusion',
    body: `Baseline IC +0.031 (p = 0.63); ML null. No evidence of a large reproducible predictive edge; effects below |IC| ≈ ${MDE_TEXT} are outside the study's detection power.`,
    tag: 'current',
  },
]

const SCALE = 0.25 // axis spans -0.25 … +0.25
const pct = (v) => `${50 + (v / SCALE) * 50}%`
const fmt = (v) => `${v >= 0 ? '+' : '−'}${Math.abs(v).toFixed(3)}`

export default function ScientificRecord({ compact = false }) {
  return (
    <section className="sr" aria-labelledby="sr-title">
      <style>{CSS}</style>
      <div className="sr-kicker">SCIENTIFIC RECORD</div>
      <h2 id="sr-title" className="sr-title">An apparent signal, audited away</h2>

      <ol className="sr-steps">
        {STEPS.map((s) => (
          <li key={s.n} className={`sr-step ${s.tag === 'current' ? 'is-current' : ''}`}>
            <div className="sr-step-n" aria-hidden="true">{s.n}</div>
            <div>
              <div className="sr-step-title">{s.title} <span className="sr-tag">{s.tag}</span></div>
              {!compact && <p className="sr-step-body">{s.body}</p>}
            </div>
          </li>
        ))}
      </ol>

      <figure className="sr-chart" aria-label="Equal-weight information coefficient before and after the point-in-time correction">
        <div className="sr-axis" aria-hidden="true">
          <span style={{ left: pct(-0.2) }}>−0.2</span>
          <span style={{ left: pct(0) }}>0</span>
          <span style={{ left: pct(0.2) }}>+0.2</span>
        </div>
        {BARS.map((b) => (
          <div className={`sr-row is-${b.tone}`} key={b.key}>
            <div className="sr-row-label">
              <strong>{b.label}{b.tone === 'withdrawn' && <span className="sr-only"> (withdrawn)</span>}</strong>
              <span>{b.sub}</span>
            </div>
            <div className="sr-track">
              <span className="sr-mde" style={{ left: pct(-MDE), width: `${(MDE / SCALE) * 100}%` }} aria-hidden="true" />
              <span className="sr-zero" aria-hidden="true" />
              {b.ci && (
                <span className="sr-ci" style={{ left: pct(b.ci[0]), width: `${((b.ci[1] - b.ci[0]) / SCALE) * 50}%` }} aria-hidden="true" />
              )}
              <span className="sr-dot" style={{ left: pct(b.ic) }} aria-hidden="true" />
            </div>
            <div className="sr-row-val">
              IC {fmt(b.ic)} <span>p {b.p}</span>
            </div>
          </div>
        ))}
        <figcaption>
          Shaded band: |IC| below {MDE.toFixed(3)}, which this design cannot reliably detect (80 % power).
          Whisker: 95 % bootstrap interval. Withdrawn rows used statements before they were public.
          Sources: RESULTS.md, experiments/results_pit_v2/REPORT.md.
        </figcaption>
      </figure>
    </section>
  )
}

const CSS = `
.sr { --sr-ink: #e8ece6; --sr-dim: #9fae9f; --sr-faint: #6b7a70; --sr-line: rgba(232,236,230,0.12);
  --sr-gold: #c8a35a; --sr-emerald: #4da583; --sr-copper: #a8674b;
  border: 1px solid var(--sr-line); background: rgba(10,14,13,0.72); color: var(--sr-ink);
  padding: 22px clamp(16px, 2.4vw, 28px); margin: 0 0 26px; }
.sr-kicker { font-family: var(--font-mono, monospace); font-size: 11px; letter-spacing: 0.14em; color: var(--sr-dim); }
.sr-title { font-size: clamp(20px, 2.4vw, 26px); margin: 6px 0 16px; font-weight: 600; }
.sr-steps { list-style: none; margin: 0 0 20px; padding: 0; display: grid; gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); }
.sr-step { display: flex; gap: 12px; padding: 12px; border: 1px solid var(--sr-line); }
.sr-step.is-current { border-color: var(--sr-emerald); }
.sr-step-n { font-family: var(--font-mono, monospace); color: var(--sr-gold); font-size: 13px; }
.sr-step-title { font-weight: 600; font-size: 14px; }
.sr-tag { display: inline-block; margin-left: 6px; font-family: var(--font-mono, monospace); font-size: 10px;
  letter-spacing: 0.08em; color: var(--sr-dim); border: 1px solid var(--sr-line); padding: 1px 5px; text-transform: uppercase; }
.sr-step-body { margin: 6px 0 0; font-size: 13px; line-height: 1.5; color: var(--sr-dim); }
.sr-chart { margin: 0; position: relative; padding-top: 18px; }
.sr-axis { position: relative; height: 14px; margin-left: calc(min(34%, 260px) + 12px); margin-right: calc(min(22%, 150px) + 12px);
  font-family: var(--font-mono, monospace); font-size: 10px; color: var(--sr-faint); }
.sr-axis span { position: absolute; transform: translateX(-50%); }
.sr-row { display: grid; grid-template-columns: min(34%, 260px) 1fr min(22%, 150px); gap: 12px; align-items: center; padding: 7px 0;
  border-top: 1px solid var(--sr-line); }
.sr-row-label strong { display: block; font-size: 13px; font-weight: 600; }
.sr-row-label span { font-size: 11px; color: var(--sr-faint); }
.sr-track { position: relative; height: 18px; }
.sr-mde { position: absolute; top: 0; bottom: 0; background: rgba(159,174,159,0.10); }
.sr-zero { position: absolute; left: 50%; top: -2px; bottom: -2px; width: 1px; background: var(--sr-faint); }
.sr-ci { position: absolute; top: 8px; height: 2px; background: var(--sr-emerald); }
.sr-dot { position: absolute; top: 3px; width: 12px; height: 12px; border-radius: 50%; transform: translateX(-50%); }
.sr-row.is-withdrawn .sr-dot { background: transparent; border: 2px solid var(--sr-copper); }
.sr-row.is-withdrawn .sr-row-label strong { text-decoration: line-through; text-decoration-color: var(--sr-copper); }
.sr-row.is-current .sr-dot { background: var(--sr-emerald); }
.sr-row-val { font-family: var(--font-mono, monospace); font-size: 12px; text-align: right; }
.sr-row-val span { color: var(--sr-faint); margin-left: 6px; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
.sr-chart figcaption { margin-top: 10px; font-size: 11px; line-height: 1.5; color: var(--sr-faint); }
@media (max-width: 640px) {
  .sr-row { grid-template-columns: 1fr; gap: 4px; }
  .sr-row-val { text-align: left; }
  .sr-axis { display: none; }
}
`
