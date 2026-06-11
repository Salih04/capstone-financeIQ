import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import api from '../api/client'
import { authRedirectUrl, isSupabaseConfigured, supabase } from '../lib/supabaseClient'

const AuthContext = createContext(null)

function toAppUser(session) {
  const authUser = session?.user
  if (!authUser) return null
  return {
    id: authUser.id,
    email: authUser.email,
    role: authUser.app_metadata?.role || 'investor',
    user_type: authUser.app_metadata?.user_type || 'individual',
    risk_level: authUser.app_metadata?.risk_level || 'medium',
    investment_scope: authUser.app_metadata?.investment_scope ?? null,
    sector_focus: authUser.app_metadata?.sector_focus ?? null,
    is_active: true,
    created_at: authUser.created_at,
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(isSupabaseConfigured)
  const [authEvent, setAuthEvent] = useState(null)

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return undefined
    }

    let alive = true
    supabase.auth.getSession().then(({ data }) => {
      if (!alive) return
      setSession(data.session ?? null)
      setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((event, nextSession) => {
      setAuthEvent(event)
      setSession(nextSession ?? null)
      setLoading(false)
    })

    return () => {
      alive = false
      listener.subscription.unsubscribe()
    }
  }, [])

  const login = async (email, password) => {
    if (!supabase) throw new Error('Supabase Auth is not configured.')
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    return data
  }

  const register = async (email, password) => {
    if (!supabase) throw new Error('Supabase Auth is not configured.')
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: authRedirectUrl('/auth/callback'),
      },
    })
    if (error) throw error
    return data
  }

  const loginWithGoogle = async () => {
    if (!supabase) throw new Error('Supabase Auth is not configured.')
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: authRedirectUrl('/auth/callback'),
      },
    })
    if (error) throw error
    return data
  }

  const sendPasswordReset = async (email) => {
    if (!supabase) throw new Error('Supabase Auth is not configured.')
    const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: authRedirectUrl('/login?mode=reset-password'),
    })
    if (error) throw error
    return data
  }

  const updatePassword = async (password) => {
    if (!supabase) throw new Error('Supabase Auth is not configured.')
    const { data, error } = await supabase.auth.updateUser({ password })
    if (error) throw error
    return data
  }

  const logout = async () => {
    if (supabase) await supabase.auth.signOut()
    setSession(null)
    setAuthEvent('SIGNED_OUT')
  }

  const updateProfile = async (payload) => {
    const { data } = await api.put('/users/me/profile', payload)
    return data
  }

  const value = useMemo(() => {
    const user = toAppUser(session)
    return {
      session,
      user,
      token: session?.access_token ?? null,
      loading,
      authEvent,
      supabaseConfigured: isSupabaseConfigured,
      login,
      register,
      loginWithGoogle,
      sendPasswordReset,
      updatePassword,
      logout,
      updateProfile,
      isAuth: Boolean(session),
      passwordRecovery: authEvent === 'PASSWORD_RECOVERY',
    }
  }, [session, loading, authEvent])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => useContext(AuthContext)
