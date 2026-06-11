// Backward-compatible shim. The real cache now lives in src/api/cache.js
// (sessionStorage-backed, SWR, in-flight dedupe). Existing callers
// (getCached/setCached/hasCached) keep working but share one consolidated store.
import { clearCache, getCached, getEntry, isExpired, setCached as _setCached } from '../api/cache'

const DEFAULT_TTL_MS = 5 * 60 * 1000

export function hasCached(key) {
  const e = getEntry(key)
  return !!(e && !isExpired(e))
}

export { getCached, clearCache }

export function setCached(key, value, ttlMs = DEFAULT_TTL_MS) {
  return _setCached(key, value, ttlMs)
}
