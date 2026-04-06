import { createContext, useContext, useState, useEffect } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem('user')) } catch { return null }
  })
  const [token, setToken] = useState(() => localStorage.getItem('token') || null)

  useEffect(() => {
    if (token) localStorage.setItem('token', token)
    else localStorage.removeItem('token')
  }, [token])

  useEffect(() => {
    if (user) localStorage.setItem('user', JSON.stringify(user))
    else localStorage.removeItem('user')
  }, [user])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login', { email, password })
    setToken(data.access_token)
    setUser(data.user)
    return data
  }

  const register = async (email, password) => {
    const { data } = await api.post('/auth/register', { email, password })
    return data
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  const updateProfile = async (payload) => {
    const { data } = await api.put('/users/me/profile', payload)
    setUser(data)
    return data
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, updateProfile, isAuth: !!token }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
