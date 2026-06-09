import axios from 'axios'

const configuredApiUrl = import.meta.env.VITE_API_URL

const api = axios.create({
  baseURL: configuredApiUrl || '/api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
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
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api
