import { useState } from 'react'
import { AlertTriangle, ChevronDown, ChevronRight, CheckCircle2, XCircle, Info } from 'lucide-react'
import { Chip } from '../components/ui'

/* Never render a raw object/array as a React child. These helpers coerce any
   value to a safe primitive or a structured element. Fixes React error #31. */

export const asText = (v) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? 'yes' : 'no'
  if (typeof v === 'number') return Number.isFinite(v) ? String(v) : '—'
  if (typeof v === 'string') return v.trim() === '' ? '—' : v
  try { return JSON.stringify(v) } catch { return String(v) }
}

export const formatNumber = (v, d = 3) => {
  const n = Number(v)
  return v === null || v === undefined || Number.isNaN(n) ? '—' : n.toFixed(d)
}

export const formatPercent = (v, d = 1) => {
  const n = Number(v)
  return v === null || v === undefined || Number.isNaN(n) ? '—' : `${n.toFixed(d)}%`
}

// 0..1 score -> "0.57 (57)" style; pass scale01=false for already-0..100
export const formatScore = (v, { scale01 = true } = {}) => {
  const n = Number(v)
  if (v === null || v === undefined || Number.isNaN(n)) return '—'
  return scale01 ? `${n.toFixed(3)} (${Math.round(n * 100)})` : n.toFixed(2)
}

export const toArray = (x) => (Array.isArray(x) ? x : x === null || x === undefined ? [] : [x])

export const renderValue = (v) => {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return <ObjectPreview value={v} />
  return asText(v)
}

export function RenderList({ items, color = 'default', empty = '—' }) {
  const arr = toArray(items)
  if (!arr.length) return <span style={{ color: 'var(--text-3)' }}>{empty}</span>
  return (
    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {arr.map((it, i) => (
        <Chip key={i} color={color}>{typeof it === 'object' ? asText(it) : String(it)}</Chip>
      ))}
    </div>
  )
}

export function WarningList({ items }) {
  const arr = toArray(items)
  if (!arr.length) return null
  return (
    <ul style={{ margin: '4px 0 0', paddingLeft: 18, fontSize: 12, color: 'var(--text-2)' }}>
      {arr.map((w, i) => <li key={i}>{typeof w === 'object' ? asText(w) : String(w)}</li>)}
    </ul>
  )
}

export function JsonBlock({ value, maxHeight = 260 }) {
  let text
  try { text = JSON.stringify(value, null, 2) } catch { text = String(value) }
  return (
    <pre style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 8,
      padding: 10, fontSize: 11, overflow: 'auto', maxHeight, margin: 0 }}>{text}</pre>
  )
}

export function ObjectPreview({ value }) {
  if (value === null || value === undefined) return <span style={{ color: 'var(--text-3)' }}>—</span>
  return <JsonBlock value={value} maxHeight={180} />
}

// ─── semantic tone mapping (theme tokens, never raw hex) ──────────────────────
export const toneColor = (tone) => ({
  good: 'var(--success)', bad: 'var(--danger)', warn: 'var(--warning)',
  info: 'var(--secondary)', accent: 'var(--primary)',
}[tone] || 'var(--text-1)')
export const toneSubtle = (tone) => ({
  good: 'var(--success-subtle)', bad: 'var(--danger-subtle)', warn: 'var(--warning-subtle)',
  info: 'var(--secondary-subtle)', accent: 'var(--primary-subtle)',
}[tone] || 'var(--surface-3)')

export const pct01 = (v, d = 0) => {
  const n = Number(v)
  return v === null || v === undefined || Number.isNaN(n) ? '—' : `${(n * 100).toFixed(d)}%`
}

export function MetricCard({ label, value, sub, tone, mono = true }) {
  const color = toneColor(tone)
  const accent = tone ? toneColor(tone) : 'var(--border-strong)'
  return (
    <div style={{ position: 'relative', background: 'linear-gradient(180deg, rgba(17,30,48,0.82), rgba(10,18,30,0.72))', border: '1px solid var(--border-strong)',
      borderRadius: 'var(--radius-lg)', padding: '16px 17px', overflow: 'hidden', boxShadow: 'var(--shadow-sm)', backdropFilter: 'blur(18px)' }}>
      <span style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: 3, background: accent, opacity: tone ? 0.9 : 0.25 }} />
      <div style={{ fontSize: 10.5, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.7, fontWeight: 700 }}>{label}</div>
      <div style={{ fontSize: 23, fontWeight: 900, color, marginTop: 5, lineHeight: 1.1,
        fontVariantNumeric: mono ? 'tabular-nums' : 'normal' }}>
        {typeof value === 'object' ? asText(value) : value}
      </div>
      {sub ? <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 3, overflow: 'hidden',
        textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{typeof sub === 'object' ? asText(sub) : sub}</div> : null}
    </div>
  )
}

export function StatusBadge({ status, labels = {} }) {
  // status: 'good' | 'bad' | 'warn' | 'info' | 'neutral'
  const t = { good: 'good', bad: 'bad', warn: 'warn', info: 'info' }[status]
  const fg = t ? toneColor(t) : 'var(--text-2)'
  const bg = t ? toneSubtle(t) : 'var(--surface-3)'
  const label = labels[status] || ({ good: 'OK', bad: 'FAIL', warn: 'WARN', info: 'INFO', neutral: '—' }[status] || '—')
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: bg, color: fg,
      borderRadius: 999, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: fg, flexShrink: 0 }} />
      {label}
    </span>
  )
}

// ─── SignalBadge — inline labelled pill ──────────────────────────────────────
export function SignalBadge({ tone = 'neutral', children }) {
  const fg = tone === 'neutral' ? 'var(--text-2)' : toneColor(tone)
  const bg = tone === 'neutral' ? 'var(--surface-3)' : toneSubtle(tone)
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: bg, color: fg,
      borderRadius: 6, padding: '3px 9px', fontSize: 11.5, fontWeight: 700, whiteSpace: 'nowrap' }}>
      {children}
    </span>
  )
}

// ─── ScoreBar — horizontal 0..1 (or 0..max) meter ────────────────────────────
export function ScoreBar({ label, value, max = 1, tone = 'accent', sub, emphasis }) {
  const n = Number(value)
  const valid = !(value === null || value === undefined || Number.isNaN(n))
  const pct = valid ? Math.max(0, Math.min(100, (n / max) * 100)) : 0
  const color = toneColor(tone)
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 5 }}>
        <span style={{ fontSize: 12, color: emphasis ? 'var(--text-1)' : 'var(--text-2)', fontWeight: emphasis ? 700 : 500 }}>{label}</span>
        <span style={{ fontSize: emphasis ? 15 : 13, fontWeight: 800, color: emphasis ? color : 'var(--text-1)',
          fontVariantNumeric: 'tabular-nums' }}>{valid ? n.toFixed(3) : '—'}</span>
      </div>
      <div style={{ height: emphasis ? 8 : 6, background: 'var(--surface-1)', borderRadius: 999, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, minWidth: valid ? 3 : 0,
          background: emphasis ? `linear-gradient(90deg, ${color}, var(--primary-hover))` : color,
          borderRadius: 999, transition: 'width .3s' }} />
      </div>
      {sub ? <div style={{ fontSize: 10.5, color: 'var(--text-3)', marginTop: 3 }}>{sub}</div> : null}
    </div>
  )
}

// ─── ScoreBreakdown — composes ML/Confidence/LLM/Final bars ───────────────────
export function ScoreBreakdown({ items = [] }) {
  return <div>{items.map((it, i) => <ScoreBar key={i} {...it} />)}</div>
}

// ─── MiniBar — proportional inline bar for tables ────────────────────────────
export function MiniBar({ value, max = 100, tone = 'info' }) {
  const n = Math.abs(Number(value) || 0)
  const pct = Math.max(0, Math.min(100, (n / max) * 100))
  return (
    <div style={{ height: 7, width: '100%', minWidth: 40, background: 'var(--surface-1)', borderRadius: 999, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${pct}%`, minWidth: 3, background: toneColor(tone), borderRadius: 999 }} />
    </div>
  )
}

// ─── CompactTable — overflow-safe, optional row highlight ────────────────────
export function CompactTable({ columns, rows, highlight, empty = '—', renderCell }) {
  return (
    <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
        <thead>
          <tr style={{ textAlign: 'left' }}>
            {columns.map(c => (
              <th key={c.key} style={{ padding: '8px 12px', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)',
                color: 'var(--text-3)', fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.4, fontWeight: 700,
                textAlign: c.align || 'left' }}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(!rows || rows.length === 0) && (
            <tr><td colSpan={columns.length} style={{ padding: 14, color: 'var(--text-3)' }}>{empty}</td></tr>
          )}
          {(rows || []).map((r, i) => {
            const hi = highlight && highlight(r)
            return (
              <tr key={i} onClick={r.__onClick}
                style={{ background: hi ? 'var(--surface-1)' : 'transparent', cursor: r.__onClick ? 'pointer' : 'default',
                  borderBottom: '1px solid var(--border)' }}>
                {columns.map(c => (
                  <td key={c.key} style={{ padding: '8px 12px', whiteSpace: 'nowrap', textAlign: c.align || 'left',
                    fontVariantNumeric: c.align === 'right' ? 'tabular-nums' : 'normal' }}>
                    {renderCell ? renderCell(c, r, i) : asText(r[c.key])}
                  </td>
                ))}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ─── Collapsible — hides raw JSON / noisy detail behind a toggle ──────────────
export function Collapsible({ label = 'View raw', children, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div>
      <button onClick={() => setOpen(o => !o)} style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
        background: 'var(--surface-1)', color: 'var(--text-2)', border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-md)', padding: '5px 11px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}{label}
      </button>
      {open && <div style={{ marginTop: 10 }}>{children}</div>}
    </div>
  )
}

export function CollapsibleJson({ label = 'View raw JSON', value, defaultOpen = false }) {
  return <Collapsible label={label} defaultOpen={defaultOpen}><JsonBlock value={value} maxHeight={340} /></Collapsible>
}

export function WarningCallout({ title, children, tone = 'warn' }) {
  const fg = toneColor(tone === 'bad' ? 'bad' : tone === 'good' ? 'good' : tone === 'info' ? 'info' : 'warn')
  return (
    <div style={{ display: 'flex', gap: 11, border: `1px solid ${fg}`, borderRadius: 'var(--radius-lg)',
      padding: '12px 14px', background: toneSubtle(tone === 'bad' ? 'bad' : tone === 'good' ? 'good' : tone === 'info' ? 'info' : 'warn') }}>
      {tone === 'good' ? <CheckCircle2 size={18} color={fg} style={{ flexShrink: 0, marginTop: 1 }} />
        : tone === 'info' ? <Info size={18} color={fg} style={{ flexShrink: 0, marginTop: 1 }} />
        : <AlertTriangle size={18} color={fg} style={{ flexShrink: 0, marginTop: 1 }} />}
      <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.55 }}>
        {title ? <div style={{ fontWeight: 700, color: fg, marginBottom: 3 }}>{title}</div> : null}
        {children}
      </div>
    </div>
  )
}

// ─── RealityCheckCard — strong honest-status list ────────────────────────────
export function RealityCheckCard({ title = 'Project reality check', sub, items = [] }) {
  const ICON = { good: CheckCircle2, bad: XCircle, warn: AlertTriangle, info: Info }
  return (
    <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderRadius: 'var(--radius-lg)', padding: 18 }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-1)' }}>{title}</div>
        {sub ? <div style={{ fontSize: 12, color: 'var(--text-3)', marginTop: 2 }}>{sub}</div> : null}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 9 }}>
        {items.map((it, i) => {
          const tone = it.tone || 'info'
          const I = ICON[tone] || Info
          return (
            <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <I size={16} color={toneColor(tone)} style={{ flexShrink: 0, marginTop: 2 }} />
              <div style={{ fontSize: 13, color: 'var(--text-2)', lineHeight: 1.5 }}>{it.text}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── EvidencePanel — titled card with chip rows ──────────────────────────────
export function EvidencePanel({ title, sub, tone = 'neutral', children, footer }) {
  const accent = tone === 'neutral' ? 'var(--border-strong)' : toneColor(tone)
  return (
    <div style={{ background: 'var(--surface-2)', border: '1px solid var(--border-strong)', borderLeft: `3px solid ${accent}`,
      borderRadius: 'var(--radius-lg)', padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)' }}>{title}</div>
        {sub ? <div style={{ fontSize: 11.5, color: 'var(--text-3)', marginTop: 2 }}>{sub}</div> : null}
      </div>
      {children}
      {footer ? <div style={{ fontSize: 11.5, color: 'var(--text-3)', borderTop: '1px solid var(--border)', paddingTop: 9 }}>{footer}</div> : null}
    </div>
  )
}

// ─── Bullets — compact semantic bullet list ──────────────────────────────────
export function Bullets({ items, tone, size = 13 }) {
  const arr = toArray(items)
  if (!arr.length) return <span style={{ color: 'var(--text-3)', fontSize: size }}>—</span>
  const dot = tone ? toneColor(tone) : 'var(--text-3)'
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 6 }}>
      {arr.map((it, i) => (
        <li key={i} style={{ display: 'flex', gap: 8, fontSize: size, color: 'var(--text-2)', lineHeight: 1.5 }}>
          <span style={{ width: 5, height: 5, borderRadius: '50%', background: dot, flexShrink: 0, marginTop: 7 }} />
          <span>{typeof it === 'object' ? asText(it) : String(it)}</span>
        </li>
      ))}
    </ul>
  )
}

// ─── warning/limitation key humanization ────────────────────────────────────
const WARNING_LABELS = {
  small_sample: 'Small sample size',
  frozen_features: 'Frozen valuation/profitability features excluded',
  no_real_valuation_profitability_features: 'Real historical valuation/profitability data is still missing',
  no_real_valuation: 'Real valuation history missing',
  weak_backtest: 'Model signal is still weak',
  benchmark_missing: 'BIST100 benchmark missing',
  manual_financials_missing: 'Manual historical financials missing',
  frozen_snapshot: 'Same snapshot repeated across years',
  leakage_field: 'Future price/return info — not allowed as input',
  misaligned_cells: 'Values appear shifted into wrong columns',
}
export const humanizeWarning = (key) => {
  if (key === null || key === undefined) return '—'
  const k = String(key)
  if (WARNING_LABELS[k]) return WARNING_LABELS[k]
  // already a human sentence? leave it. else prettify snake_case.
  if (/\s/.test(k) || /[A-Z]/.test(k)) return k
  return k.replace(/_/g, ' ').replace(/^\w/, c => c.toUpperCase())
}

// ─── DecisionVerdict — bounded research-interest badge (never advice) ─────────
const VERDICT_TONE = {
  'insufficient evidence': 'neutral',
  'low confidence watchlist': 'warn',
  'moderate research interest': 'info',
  'high research interest': 'good',
}
export function DecisionVerdict({ verdict, size = 'md' }) {
  if (!verdict) return null
  const tone = VERDICT_TONE[String(verdict).toLowerCase()] || 'neutral'
  const fg = tone === 'neutral' ? 'var(--text-2)' : toneColor(tone)
  const bg = tone === 'neutral' ? 'var(--surface-3)' : toneSubtle(tone)
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: bg, color: fg,
      borderRadius: 999, padding: size === 'md' ? '4px 13px' : '2px 10px',
      fontSize: size === 'md' ? 12.5 : 11, fontWeight: 800, textTransform: 'capitalize' }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: fg, flexShrink: 0 }} />
      {verdict}
    </span>
  )
}

export const NOT_ADVICE = 'Research support only — not investment advice.'
