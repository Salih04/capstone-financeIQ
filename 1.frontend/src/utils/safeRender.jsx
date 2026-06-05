import { AlertTriangle } from 'lucide-react'
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

export function MetricCard({ label, value, sub, tone }) {
  const color = tone === 'good' ? 'var(--success,#16a34a)' : tone === 'bad' ? 'var(--danger,#dc2626)'
    : tone === 'warn' ? 'var(--warning,#b45309)' : 'var(--text-1)'
  return (
    <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 10, padding: '12px 14px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color, marginTop: 2 }}>{typeof value === 'object' ? asText(value) : value}</div>
      {sub ? <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>{typeof sub === 'object' ? asText(sub) : sub}</div> : null}
    </div>
  )
}

export function StatusBadge({ status, labels = {} }) {
  // status: 'good' | 'bad' | 'warn' | 'neutral'
  const map = {
    good: { bg: 'rgba(22,163,74,.15)', fg: '#16a34a', t: labels.good || 'OK' },
    bad: { bg: 'rgba(220,38,38,.15)', fg: '#dc2626', t: labels.bad || 'FAIL' },
    warn: { bg: 'rgba(180,83,9,.15)', fg: '#b45309', t: labels.warn || 'WARN' },
    neutral: { bg: 'var(--surface-2)', fg: 'var(--text-2)', t: labels.neutral || '—' },
  }
  const s = map[status] || map.neutral
  return (
    <span style={{ background: s.bg, color: s.fg, borderRadius: 999, padding: '2px 10px',
      fontSize: 11, fontWeight: 700 }}>{s.t}</span>
  )
}

export function WarningCallout({ title, children, tone = 'warn' }) {
  const fg = tone === 'bad' ? 'var(--danger,#dc2626)' : 'var(--warning,#b45309)'
  return (
    <div style={{ display: 'flex', gap: 10, border: `1px solid ${fg}`, borderRadius: 10, padding: '10px 12px',
      background: 'var(--surface-1)' }}>
      <AlertTriangle size={18} color={fg} style={{ flexShrink: 0, marginTop: 1 }} />
      <div style={{ fontSize: 13, color: 'var(--text-2)' }}>
        {title ? <div style={{ fontWeight: 700, color: fg, marginBottom: 2 }}>{title}</div> : null}
        {children}
      </div>
    </div>
  )
}

export const NOT_ADVICE = 'Research support only — not investment advice.'
