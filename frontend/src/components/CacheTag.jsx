// Subtle Fable-5 cache metadata chip: cached / refreshing / live + last-updated
// + a force-refresh control. Monospace, muted, no generic badge styling.

function timeAgo(ts) {
  if (!ts) return ''
  const s = Math.max(0, Math.floor((Date.now() - ts) / 1000))
  if (s < 5) return 'just now'
  if (s < 60) return `${s}s ago`
  const m = Math.floor(s / 60)
  if (m < 60) return `${m}m ago`
  return `${Math.floor(m / 60)}h ago`
}

export default function CacheTag({ fromCache, refreshing, savedAt, onRefresh, className = '' }) {
  const state = refreshing ? 'refreshing' : fromCache ? 'cached' : 'live'
  return (
    <div className={`cachetag ${className}`} aria-live="polite">
      <style>{CSS}</style>
      <span className={`cachetag-state is-${state}`}>
        <i aria-hidden="true" />{state}
      </span>
      {savedAt ? <span className="cachetag-ago" title="Last updated">{timeAgo(savedAt)}</span> : null}
      {onRefresh ? (
        <button
          type="button"
          className="cachetag-btn"
          onClick={onRefresh}
          disabled={refreshing}
          aria-label="Force refresh"
          title="Force refresh"
        >⟳</button>
      ) : null}
    </div>
  )
}

const CSS = `
.cachetag { display: inline-flex; align-items: center; gap: 9px;
  font-family: var(--font-mono); font-size: 9px; letter-spacing: 0.18em; }
.cachetag-state { display: inline-flex; align-items: center; gap: 5px; text-transform: uppercase; }
.cachetag-state i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.cachetag-state.is-cached { color: #4da583; }
.cachetag-state.is-live { color: #6b7a70; }
.cachetag-state.is-refreshing { color: #c8a35a; }
.cachetag-state.is-refreshing i { animation: cachetagPulse 1s ease-in-out infinite; }
.cachetag-ago { color: #6b7a70; letter-spacing: 0.1em; text-transform: none; }
.cachetag-btn { font-family: var(--font-mono); font-size: 12px; line-height: 1; color: #9fae9f;
  background: transparent; border: 1px solid rgba(200,211,202,0.25); border-radius: 2px;
  padding: 2px 6px; cursor: pointer; transition: color 0.15s, border-color 0.15s, transform 0.4s; }
.cachetag-btn:hover:not(:disabled) { color: #c8a35a; border-color: rgba(200,163,90,0.5); }
.cachetag-btn:active:not(:disabled) { transform: rotate(180deg); }
.cachetag-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.cachetag-btn:focus-visible { outline: 1px solid #c8a35a; outline-offset: 2px; }
@keyframes cachetagPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
@media (prefers-reduced-motion: reduce) { .cachetag-state.is-refreshing i { animation: none; } }
`
