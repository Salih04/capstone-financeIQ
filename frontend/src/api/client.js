import axios from 'axios'
import { getAccessToken } from '../lib/supabaseClient'

const configuredApiUrl = import.meta.env.VITE_API_URL

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
    if (!configuredApiUrl && err.response?.status === 405) {
      err.response.data = {
        detail: 'Backend API is not connected. Set VITE_API_URL in Vercel to your deployed backend URL, then redeploy.',
      }
    }
    return Promise.reject(err)
  }
)

export default api
