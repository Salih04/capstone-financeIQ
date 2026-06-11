import { useCallback, useEffect, useRef, useState } from 'react'
import { CACHE_TTL, cachedGet } from './cache'

// ---------------------------------------------------------------------------
// useCachedResource — stale-while-revalidate hook for GET endpoints.
//
// Returns cached data instantly when present, refreshes in the background, and
// updates the UI quietly when fresh data arrives. `refresh()` forces network.
//
//   const { data, error, fromCache, refreshing, savedAt, loading, refresh }
//     = useCachedResource('/research/summary', { ttlMs: CACHE_TTL.MEDIUM })
// ---------------------------------------------------------------------------
export function useCachedResource(path, opts = {}) {
  const { ttlMs = CACHE_TTL.MEDIUM, params, cacheKey, enabled = true } = opts
  const paramKey = params ? JSON.stringify(params) : ''

  const [state, setState] = useState({
    data: undefined, error: null, fromCache: false,
    refreshing: false, savedAt: null, loading: true,
  })
  const mounted = useRef(true)

  const load = useCallback(async (force = false) => {
    if (!enabled) { setState((s) => ({ ...s, loading: false })); return }
    setState((s) => ({ ...s, refreshing: s.data !== undefined, loading: s.data === undefined }))

    const r = await cachedGet(path, params ? { params } : undefined, {
      ttlMs, forceRefresh: force, cacheKey,
    })

    if (mounted.current) {
      if (r.value !== undefined) {
        setState({
          data: r.value, error: r.error, fromCache: r.fromCache,
          refreshing: !!r.refreshing, savedAt: r.savedAt, loading: false,
        })
      } else {
        setState((s) => ({ ...s, error: r.error, refreshing: false, loading: false }))
      }
    }

    if (r.revalidate) {
      const fresh = await r.revalidate
      if (mounted.current) {
        setState((s) => (fresh != null
          ? { ...s, data: fresh, fromCache: false, refreshing: false, savedAt: Date.now() }
          : { ...s, refreshing: false }))
      }
    }
  }, [path, paramKey, ttlMs, cacheKey, enabled]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    mounted.current = true
    load(false)
    return () => { mounted.current = false }
  }, [load])

  const refresh = useCallback(() => load(true), [load])
  return { ...state, refresh }
}

export { CACHE_TTL }
