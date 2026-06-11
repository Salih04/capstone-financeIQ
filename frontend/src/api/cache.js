// ---------------------------------------------------------------------------
// Centralized frontend API cache — stale-while-revalidate, sessionStorage-backed.
//
// Why sessionStorage: data (CSV/model outputs) is stable within a browser
// session but we never want day-stale data, and we avoid Render cold-start lag
// on navigation. Cleared when the tab closes.
//
// Safety: auth/session/token endpoints are NEVER cached. Failed responses are
// NEVER cached. In-flight requests are deduped by cache key.
// ---------------------------------------------------------------------------
import api from './client'

export const CACHE_TTL = {
  SHORT: 60_000,        // 1 min  — volatile status (ai-status)
  MEDIUM: 10 * 60_000,  // 10 min — summaries, scores, company detail
  LONG: 30 * 60_000,    // 30 min — diagnostics, options, train results
}

const STORE_PREFIX = 'fiq:cache:'

// Endpoints that must never be cached (auth/session/identity/tokens).
const NO_CACHE = [
  /\/auth(\/|$)/i, /\/login/i, /\/register/i, /\/signup/i, /\/logout/i,
  /\/token/i, /\/users\/me/i, /\/session/i, /supabase/i, /callback/i,
]
export function isCacheablePath(path) {
  return !NO_CACHE.some((re) => re.test(path || ''))
}

// In-memory fallback when sessionStorage is unavailable (private mode / quota).
const mem = new Map()
function store() {
  try {
    const s = window.sessionStorage
    s.getItem(STORE_PREFIX + '__probe__')
    return s
  } catch {
    return null
  }
}

function sortDeep(o) {
  if (Array.isArray(o)) return o.map(sortDeep)
  if (o && typeof o === 'object') {
    return Object.keys(o).sort().reduce((acc, k) => { acc[k] = sortDeep(o[k]); return acc }, {})
  }
  return o
}

export function makeCacheKey(method, path, extra) {
  const m = (method || 'GET').toUpperCase()
  let tail = ''
  if (extra && typeof extra === 'object') {
    try { tail = JSON.stringify(sortDeep(extra)) } catch { tail = String(extra) }
  } else if (extra != null) {
    tail = String(extra)
  }
  return `${m} ${path}${tail ? ` ${tail}` : ''}`
}

export function isExpired(entry) {
  return !entry || (entry.expiresAt != null && entry.expiresAt <= Date.now())
}

export function getEntry(key) {
  const s = store()
  if (!s) return mem.get(key)
  try {
    const raw = s.getItem(STORE_PREFIX + key)
    return raw ? JSON.parse(raw) : undefined
  } catch {
    return mem.get(key)
  }
}

export function getCached(key) {
  const e = getEntry(key)
  return e ? e.value : undefined
}

export function setCached(key, value, ttlMs = CACHE_TTL.MEDIUM) {
  const now = Date.now()
  const entry = {
    value,
    savedAt: now,
    expiresAt: ttlMs == null ? null : now + ttlMs,
    cacheKey: key,
    source: 'api-cache',
  }
  const s = store()
  if (s) {
    try { s.setItem(STORE_PREFIX + key, JSON.stringify(entry)) } catch { mem.set(key, entry) }
  } else {
    mem.set(key, entry)
  }
  return value
}

export function clearCache(key) {
  const s = store()
  if (key == null) {
    if (s) {
      Object.keys(s).filter((k) => k.startsWith(STORE_PREFIX)).forEach((k) => s.removeItem(k))
    }
    mem.clear()
    return
  }
  if (s) s.removeItem(STORE_PREFIX + key)
  mem.delete(key)
}

// ── in-flight dedupe ──────────────────────────────────────────────────────
const inflight = new Map()
function dedupe(key, run) {
  if (inflight.has(key)) return inflight.get(key)
  const p = run()
    .then((v) => { inflight.delete(key); return v })
    .catch((e) => { inflight.delete(key); throw e })
  inflight.set(key, p)
  return p
}

const META = (value, over = {}) => ({
  value, fromCache: false, stale: false, refreshing: false,
  savedAt: null, error: null, warning: null, revalidate: null, ...over,
})

/**
 * cachedGet(path, config?, options?) → {value, fromCache, stale, refreshing, savedAt, error, revalidate?}
 *
 * - fresh cache → returns it immediately (fromCache:true)
 * - stale cache + allowStale → returns stale immediately, attaches `revalidate`
 *   promise resolving to fresh data (background refresh)
 * - no cache → awaits network
 * - network fails but stale cache exists → returns stale + warning
 * - auth paths / failures are never cached
 */
export async function cachedGet(path, config = {}, options = {}) {
  const { ttlMs = CACHE_TTL.MEDIUM, forceRefresh = false, cacheKey, allowStale = true } = options
  const key = cacheKey || makeCacheKey('GET', path, config?.params)

  if (!isCacheablePath(path)) {
    const res = await api.get(path, config)
    return META(res.data)
  }

  const entry = getEntry(key)
  const run = () => dedupe(key, () => api.get(path, config).then((res) => {
    setCached(key, res.data, ttlMs)
    return res.data
  }))

  if (entry && !isExpired(entry) && !forceRefresh) {
    return META(entry.value, { fromCache: true, savedAt: entry.savedAt })
  }

  if (entry && allowStale && !forceRefresh) {
    // stale-while-revalidate: serve stale now, refresh in background
    const revalidate = run().catch(() => null)
    return META(entry.value, { fromCache: true, stale: true, refreshing: true, savedAt: entry.savedAt, revalidate })
  }

  try {
    const data = await run()
    const e = getEntry(key)
    return META(data, { savedAt: e?.savedAt ?? Date.now() })
  } catch (error) {
    if (entry) return META(entry.value, { fromCache: true, stale: true, savedAt: entry.savedAt, error, warning: 'served-stale-on-error' })
    return META(undefined, { error })
  }
}

/**
 * cachedPost(path, body?, options?) — same SWR semantics, keyed by body.
 * For idempotent compute endpoints only (e.g. /forecasting/train). Never used
 * for auth or /research/ask.
 */
export async function cachedPost(path, body = {}, options = {}) {
  const { ttlMs = CACHE_TTL.LONG, forceRefresh = false, cacheKey, allowStale = true } = options
  const key = cacheKey || makeCacheKey('POST', path, body)

  if (!isCacheablePath(path)) {
    const res = await api.post(path, body)
    return META(res.data)
  }

  const entry = getEntry(key)
  const run = () => dedupe(key, () => api.post(path, body).then((res) => {
    setCached(key, res.data, ttlMs)
    return res.data
  }))

  if (entry && !isExpired(entry) && !forceRefresh) {
    return META(entry.value, { fromCache: true, savedAt: entry.savedAt })
  }
  if (entry && allowStale && !forceRefresh) {
    const revalidate = run().catch(() => null)
    return META(entry.value, { fromCache: true, stale: true, refreshing: true, savedAt: entry.savedAt, revalidate })
  }
  try {
    const data = await run()
    const e = getEntry(key)
    return META(data, { savedAt: e?.savedAt ?? Date.now() })
  } catch (error) {
    if (entry) return META(entry.value, { fromCache: true, stale: true, savedAt: entry.savedAt, error, warning: 'served-stale-on-error' })
    return META(undefined, { error })
  }
}
