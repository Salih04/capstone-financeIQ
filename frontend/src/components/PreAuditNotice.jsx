import { Link, useLocation } from 'react-router-dom'

// ---------------------------------------------------------------------------
// Pre-audit notice — sections whose scores, rankings, forecasts or walk-forward
// figures come from the original T→T+1 design, withdrawn by the 2026-10-04
// publication-lag audit (docs/audit/PUBLICATION_LAG_AUDIT.md). The backend marks
// the matching API responses with `X-Evidence-Status: withdrawn_pre_pit`
// (backend/app/core/evidence_status.py). Dashboard and Experiments lead with the
// ScientificRecord instead; data-quality, data-health and admin pages describe
// data or configuration, not results.
// ---------------------------------------------------------------------------

export const PRE_AUDIT_ROUTE_PREFIXES = [
  '/companies',
  '/score-runs',
  '/compare',
  '/validation',
  '/labeling',
  '/forecasting',
  '/research',
  '/research-agent',
  '/autopsy',
  '/courtroom',
  '/benchmark',
]

export function isPreAuditRoute(pathname) {
  return PRE_AUDIT_ROUTE_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`))
}

export default function PreAuditNotice() {
  const { pathname } = useLocation()
  if (!isPreAuditRoute(pathname)) return null

  return (
    <aside className="pan" role="note" aria-label="Pre-audit historical record">
      <style>{CSS}</style>
      <div className="pan-kicker">HISTORICAL RECORD · PRE-AUDIT DESIGN</div>
      <p className="pan-body">
        Scores, rankings and walk-forward figures in this section come from the original T→T+1
        design. The 2026-10-04 audit found it used annual statements before they were public;
        under the corrected point-in-time evaluation no model is distinguishable from chance.
        Shown for transparency, not as evidence. Research support only; not investment advice.
      </p>
      <Link className="pan-link" to="/experiments">Scientific record →</Link>
    </aside>
  )
}

const CSS = `
.pan { --pan-ink: #e8ece6; --pan-dim: #9fae9f; --pan-line: rgba(232,236,230,0.12); --pan-copper: #a8674b;
  border: 1px solid var(--pan-line); border-left: 3px solid var(--pan-copper);
  background: rgba(10,14,13,0.72); color: var(--pan-ink);
  padding: 12px clamp(14px, 2vw, 20px); margin: 0 0 22px;
  display: grid; grid-template-columns: 1fr auto; gap: 4px 16px; align-items: end; }
.pan-kicker { grid-column: 1 / -1; font-family: var(--font-mono, monospace); font-size: 11px;
  letter-spacing: 0.14em; color: var(--pan-copper); }
.pan-body { margin: 0; font-size: 13px; line-height: 1.5; color: var(--pan-dim); }
.pan-link { font-family: var(--font-mono, monospace); font-size: 12px; color: var(--pan-ink);
  white-space: nowrap; text-decoration: none; border-bottom: 1px solid var(--pan-line); }
.pan-link:hover { border-bottom-color: var(--pan-copper); }
@media (max-width: 640px) {
  .pan { grid-template-columns: 1fr; }
}
`
