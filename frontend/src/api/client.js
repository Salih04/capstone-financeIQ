import axios from 'axios'
import { getAccessToken } from '../lib/supabaseClient'

// Normalize: strip trailing slashes so `${base}/research/...` never doubles up.
const rawApiUrl = import.meta.env.VITE_API_URL
const configuredApiUrl = rawApiUrl ? rawApiUrl.replace(/\/+$/, '') : ''

if (!configuredApiUrl) {
  // Loud, single config error. Without VITE_API_URL the SPA host (e.g. Vercel)
  // rewrites every path to index.html, so API calls silently return HTML and
  // pages render incomplete. This makes the misconfiguration obvious.
  // eslint-disable-next-line no-console
  console.error(
    '[FinanceIQ] VITE_API_URL is not set. API calls fall back to "/api" on the ' +
      'frontend host and will NOT reach the backend. Set VITE_API_URL to your ' +
      'deployed backend URL (e.g. https://financeiq-backend.onrender.com) and redeploy.'
  )
}

const api = axios.create({
  baseURL: configuredApiUrl || '/api',
})

api.interceptors.request.use(async (config) => {
  const token = await getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status
    const method = err.config?.method?.toUpperCase()
    const url = err.config?.url
    // Dev-visible diagnostics: method, path, status — never a blank failure.
    // eslint-disable-next-line no-console
    console.error(`[FinanceIQ] API error ${method} ${url} -> ${status ?? 'no-response'}`)

    if (!configuredApiUrl && (status === 405 || status === 404 || !status)) {
      err.response = err.response || {}
      err.response.data = {
        detail:
          'Backend API is not connected. Set VITE_API_URL in Vercel to your ' +
          'deployed backend URL, then redeploy.',
      }
    }
    return Promise.reject(err)
  }
)

export default api
