// Human-readable one-liner for a failed API call, so demo-data fallback notes
// can say WHY the real API was not used (e.g. "401 — Authentication required."
// on a private deployment) instead of implying the API returned empty data.
// Accepts either a raw axios error (useCachedResource/cachedGet) or the string
// already extracted by researchApi's safeGet/safePost. Returns null when there
// is no error.
export function apiErrorText(error) {
  if (!error) return null
  if (typeof error === 'string') return error
  const status = error?.response?.status
  const detail = error?.response?.data?.detail
  const msg = typeof detail === 'string' && detail ? detail : (error?.message || 'request failed')
  return status ? `${status} — ${msg}` : msg
}

export default apiErrorText
