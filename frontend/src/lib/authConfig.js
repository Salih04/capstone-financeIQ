// Frontend auth feature flags (UX + leakage prevention only — the real boundary
// is backend require_access). Defaults are locked down: Google + signup are OFF
// unless explicitly enabled, matching a private deployment.

const flag = (v, def = false) => {
  if (v == null || v === '') return def
  return String(v).trim().toLowerCase() === 'true'
}

export const ENABLE_GOOGLE_AUTH = flag(import.meta.env.VITE_ENABLE_GOOGLE_AUTH, false)
export const ENABLE_SIGNUP = flag(import.meta.env.VITE_ENABLE_SIGNUP, false)
export const REQUIRE_APPROVED_USER = flag(import.meta.env.VITE_REQUIRE_APPROVED_USER, false)

export const APPROVED_EMAILS = new Set(
  String(import.meta.env.VITE_APPROVED_EMAILS || '')
    .split(',')
    .map((s) => s.trim().toLowerCase())
    .filter(Boolean),
)

// True when the email is allowed in. Fail closed: if approval is required but the
// allowlist is empty, nobody is approved. Email compared case-insensitively.
export function isApproved(email) {
  if (!REQUIRE_APPROVED_USER) return true
  if (APPROVED_EMAILS.size === 0) return false
  return APPROVED_EMAILS.has(String(email || '').trim().toLowerCase())
}
