const DEFAULT_TTL_MS = 5 * 60 * 1000
const cache = new Map()

function isFresh(entry) {
  return entry && (entry.expiresAt === null || entry.expiresAt > Date.now())
}

export function hasCached(key) {
  const entry = cache.get(key)
  if (isFresh(entry)) return true
  cache.delete(key)
  return false
}

export function getCached(key) {
  if (!hasCached(key)) return undefined
  return cache.get(key).value
}

export function setCached(key, value, ttlMs = DEFAULT_TTL_MS) {
  cache.set(key, {
    value,
    expiresAt: ttlMs === null ? null : Date.now() + ttlMs,
  })
  return value
}
