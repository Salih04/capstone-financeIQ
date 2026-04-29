// Shared UI primitives
import { useState, isValidElement } from 'react'

// ─── StatCard ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, sub, accent, icon: Icon, trend }) {
  return (
    <div style={{
      background: 'var(--surface-2)',
      border: '1px solid var(--border-strong)',
      borderRadius: 'var(--radius-lg)',
      padding: '18px 20px',
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      transition: 'border-color 0.15s',
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--border-bright)'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border-strong)'}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.8 }}>
          {label}
        </span>
        {Icon && (
          <span style={{
            width: 32, height: 32, borderRadius: 9,
            background: accent ? `color-mix(in srgb, ${accent} 12%, transparent)` : 'var(--surface-3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: accent || 'var(--primary)',
          }}>
            <Icon size={15} />
          </span>
        )}
      </div>
      <div style={{ fontSize: '1.75rem', fontWeight: 800, color: accent || 'var(--text-1)', lineHeight: 1, fontVariantNumeric: 'tabular-nums' }}>
        {value ?? '—'}
      </div>
      {(sub || trend) && (
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {sub && <span style={{ fontSize: 12, color: 'var(--text-3)' }}>{sub}</span>}
          {trend != null && (
            <span style={{
              fontSize: 11, fontWeight: 700,
              color: trend > 0 ? 'var(--success-light)' : trend < 0 ? 'var(--danger-light)' : 'var(--text-3)',
            }}>
              {trend > 0 ? '▲' : trend < 0 ? '▼' : '●'} {Math.abs(trend).toFixed(1)}%
            </span>
          )}
        </div>
      )}
    </div>
  )
}

// ─── ScoreBadge ───────────────────────────────────────────────────────────────
const SCORE_BANDS = [
  { min: 75, label: 'Strong', bg: 'var(--success-muted)', color: 'var(--success-light)', dot: 'var(--success)' },
  { min: 55, label: 'Moderate', bg: 'var(--warning-muted)', color: 'var(--warning-light)', dot: 'var(--warning)' },
  { min: 35, label: 'Watch', bg: 'rgba(251,146,60,0.12)', color: '#fb923c', dot: '#f97316' },
  { min: 0,  label: 'Risky', bg: 'var(--danger-muted)', color: 'var(--danger-light)', dot: 'var(--danger)' },
]

export function getBand(score) {
  if (score == null) return { label: '—', bg: 'var(--surface-3)', color: 'var(--text-3)', dot: 'var(--text-3)' }
  return SCORE_BANDS.find(b => score >= b.min) || SCORE_BANDS[SCORE_BANDS.length - 1]
}

export function ScoreBadge({ score, size = 'sm' }) {
  const band = getBand(score)
  const pad = size === 'lg' ? '5px 14px' : '3px 10px'
  const fontSize = size === 'lg' ? 13 : 11
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: band.bg, color: band.color,
      borderRadius: 20, padding: pad, fontSize, fontWeight: 700,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: band.dot, flexShrink: 0 }} />
      {band.label}
    </span>
  )
}

// ─── SectionHeader ────────────────────────────────────────────────────────────
export function SectionHeader({ title, sub, subtitle, icon, actions }) {
  const desc = sub || subtitle
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 10 }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {icon && (
            <div style={{
              width: 36, height: 36, borderRadius: 'var(--radius-md)',
              background: 'var(--primary-subtle)', color: 'var(--primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            }}>
              {icon}
            </div>
          )}
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-1)', letterSpacing: '-0.3px' }}>{title}</h1>
        </div>
        {desc && <p style={{ color: 'var(--text-3)', fontSize: 13.5, marginTop: 3 }}>{desc}</p>}
      </div>
      {actions && <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>{actions}</div>}
    </div>
  )
}

// ─── PrimaryButton ────────────────────────────────────────────────────────────
export function PrimaryButton({ children, onClick, disabled, style: extraStyle, icon: Icon, variant = 'primary' }) {
  const [hovered, setHovered] = useState(false)
  const { bg, hoverBg, color } = variant === 'primary'
    ? { bg: 'var(--primary)', hoverBg: 'var(--primary-hover)', color: '#fff' }
    : variant === 'success'
    ? { bg: 'var(--success)', hoverBg: 'var(--success-light)', color: '#fff' }
    : { bg: 'var(--surface-2)', hoverBg: 'var(--surface-hover)', color: 'var(--text-1)' }

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 7,
        background: disabled ? 'var(--surface-3)' : hovered ? hoverBg : bg,
        color: disabled ? 'var(--text-3)' : color,
        border: 'none', borderRadius: 'var(--radius-md)',
        padding: '9px 18px', fontSize: 13.5, fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'background 0.15s, color 0.15s, transform 0.1s',
        transform: hovered && !disabled ? 'translateY(-1px)' : 'none',
        boxShadow: hovered && !disabled && variant === 'primary' ? 'var(--shadow-glow)' : 'none',
        ...extraStyle,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {Icon && <Icon size={15} />}
      {children}
    </button>
  )
}

// ─── GhostButton ──────────────────────────────────────────────────────────────
export function GhostButton({ children, onClick, icon: Icon, style: extraStyle }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={onClick}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 7,
        background: hovered ? 'var(--surface-hover)' : 'transparent',
        color: hovered ? 'var(--text-1)' : 'var(--text-2)',
        border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-md)',
        padding: '8px 14px', fontSize: 13, fontWeight: 500,
        cursor: 'pointer',
        transition: 'background 0.15s, color 0.15s',
        ...extraStyle,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {Icon && <Icon size={14} />}
      {children}
    </button>
  )
}

// ─── Card ─────────────────────────────────────────────────────────────────────
export function Card({ children, style: extraStyle, hoverable }) {
  const [hovered, setHovered] = useState(false)
  return (
    <div
      style={{
        background: 'var(--surface-2)',
        border: `1px solid ${hovered && hoverable ? 'var(--border-bright)' : 'var(--border-strong)'}`,
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        transition: 'border-color 0.15s, box-shadow 0.15s',
        boxShadow: hovered && hoverable ? 'var(--shadow-sm)' : 'none',
        ...extraStyle,
      }}
      onMouseEnter={() => hoverable && setHovered(true)}
      onMouseLeave={() => hoverable && setHovered(false)}
    >
      {children}
    </div>
  )
}

// ─── TabBar ───────────────────────────────────────────────────────────────────
export function TabBar({ tabs, active, onChange }) {
  return (
    <div style={{
      display: 'flex',
      gap: 2,
      borderBottom: '1px solid var(--border)',
      marginBottom: 24,
    }}>
      {tabs.map(tab => {
        const isActive = tab.value === active
        return (
          <button
            key={tab.value}
            onClick={() => onChange(tab.value)}
            style={{
              display: 'flex', alignItems: 'center', gap: 7,
              padding: '10px 16px',
              background: 'none', border: 'none',
              borderBottom: `2px solid ${isActive ? 'var(--primary)' : 'transparent'}`,
              color: isActive ? 'var(--primary-hover)' : 'var(--text-3)',
              fontSize: 13.5, fontWeight: isActive ? 600 : 500,
              cursor: 'pointer',
              transition: 'color 0.15s',
              marginBottom: -1,
            }}
          >
            {tab.icon && <tab.icon size={14} />}
            {tab.label}
            {tab.count != null && (
              <span style={{
                background: isActive ? 'var(--primary-subtle)' : 'var(--surface-3)',
                color: isActive ? 'var(--primary-hover)' : 'var(--text-3)',
                borderRadius: 10, padding: '1px 7px', fontSize: 11, fontWeight: 700,
              }}>{tab.count}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}

// ─── Pill / Chip ──────────────────────────────────────────────────────────────
export function Chip({ children, color = 'default' }) {
  const colors = {
    default: { bg: 'var(--surface-3)', color: 'var(--text-2)' },
    primary: { bg: 'var(--primary-subtle)', color: 'var(--primary-hover)' },
    success: { bg: 'var(--success-subtle)', color: 'var(--success-light)' },
    warning: { bg: 'var(--warning-subtle)', color: 'var(--warning-light)' },
    danger:  { bg: 'var(--danger-subtle)',  color: 'var(--danger-light)' },
  }
  const c = colors[color] || colors.default
  return (
    <span style={{
      display: 'inline-block',
      background: c.bg, color: c.color,
      borderRadius: 6, padding: '2px 9px',
      fontSize: 11, fontWeight: 700,
    }}>{children}</span>
  )
}

// ─── ChangeChip ───────────────────────────────────────────────────────────────
export function ChangeChip({ value, pct }) {
  if (value == null && pct == null) return <span style={{ color: 'var(--text-3)' }}>—</span>
  const num = pct ?? value
  const isPos = num > 0
  const isNeg = num < 0
  const color = isPos ? 'var(--success-subtle)' : isNeg ? 'var(--danger-subtle)' : 'var(--surface-3)'
  const textColor = isPos ? 'var(--success-light)' : isNeg ? 'var(--danger-light)' : 'var(--text-3)'
  const prefix = isPos ? '+' : ''
  const display = pct != null ? `${prefix}${(num * 100).toFixed(1)}%` : `${prefix}${num.toFixed(3)}`
  return (
    <span style={{ display: 'inline-block', background: color, color: textColor, borderRadius: 6, padding: '2px 9px', fontSize: 11, fontWeight: 700 }}>
      {display}
    </span>
  )
}

// ─── EmptyState ───────────────────────────────────────────────────────────────
export function EmptyState({ icon, title, sub, description, action }) {
  const subtitle = sub || description
  const iconNode = icon
    ? isValidElement(icon) ? icon : (() => { const I = icon; return <I size={24} /> })()
    : null
  return (
    <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-3)' }}>
      {iconNode && (
        <div style={{
          width: 56, height: 56, borderRadius: 16,
          background: 'var(--surface-3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 16px',
          color: 'var(--text-3)',
        }}>
          {iconNode}
        </div>
      )}
      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-2)', marginBottom: 6 }}>{title}</div>
      {subtitle && <div style={{ fontSize: 13.5, color: 'var(--text-3)', maxWidth: 320, margin: '0 auto' }}>{subtitle}</div>}
      {action && <div style={{ marginTop: 20 }}>{action}</div>}
    </div>
  )
}

// ─── LoadingSkeleton ──────────────────────────────────────────────────────────
export function Skeleton({ width = '100%', height = 16, radius = 6, style: extra }) {
  return (
    <div style={{
      width, height,
      borderRadius: radius,
      background: 'linear-gradient(90deg, var(--surface-2) 25%, var(--surface-3) 50%, var(--surface-2) 75%)',
      backgroundSize: '400% 100%',
      animation: 'shimmer 1.4s infinite linear',
      ...extra,
    }} />
  )
}

// ─── DataFreshnessBadge ───────────────────────────────────────────────────────
export function FreshnessBadge({ date }) {
  if (!date) return null
  const days = Math.floor((Date.now() - new Date(date)) / 86400000)
  const fresh = days <= 7
  const stale = days > 30
  const color = fresh ? 'var(--success-light)' : stale ? 'var(--danger-light)' : 'var(--warning-light)'
  const bg = fresh ? 'var(--success-subtle)' : stale ? 'var(--danger-subtle)' : 'var(--warning-subtle)'
  const label = days === 0 ? 'Today' : days === 1 ? '1d ago' : `${days}d ago`
  return (
    <span style={{ fontSize: 11, fontWeight: 600, color, background: bg, borderRadius: 6, padding: '2px 8px' }}>
      {label}
    </span>
  )
}
