import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { TrendingUp } from 'lucide-react'

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [focusField, setFocusField] = useState(null)

  const getErrorMessage = (err) => {
    const detail = err?.response?.data?.detail
    if (!detail) return 'An error occurred.'
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      const parts = detail
        .map((item) => {
          if (typeof item === 'string') return item
          if (item?.msg) return item.msg
          return null
        })
        .filter(Boolean)
      if (parts.length > 0) return parts.join(' | ')
      return 'Invalid input. Please check your email and password.'
    }
    if (typeof detail === 'object' && detail.msg) return detail.msg
    return 'An error occurred.'
  }

  const handle = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      if (mode === 'login') {
        await login(email, password)
        navigate('/dashboard')
      } else {
        await register(email, password)
        await login(email, password)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const inputStyle = (field) => ({
    width: '100%', boxSizing: 'border-box',
    background: 'var(--surface-1)', border: `1px solid ${focusField === field ? 'var(--primary)' : 'var(--border-strong)'}`,
    borderRadius: 'var(--radius-md)', padding: '10px 14px',
    color: 'var(--text-1)', fontSize: 14, outline: 'none',
    transition: 'border-color 0.15s',
  })

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-deep)',
      backgroundImage: 'radial-gradient(ellipse at 20% 30%, rgba(0,245,212,0.07) 0%, transparent 60%), radial-gradient(ellipse at 80% 70%, rgba(255,77,157,0.05) 0%, transparent 60%)',
    }}>
      {/* Card */}
      <div style={{
        background: 'var(--surface-1)', border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-xl)', padding: '2.5rem 2.25rem', width: 400,
        boxShadow: 'var(--shadow-lg)',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 28 }}>
          <div style={{
            width: 40, height: 40, borderRadius: 'var(--radius-md)', background: 'var(--primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <TrendingUp size={20} color="#fff" />
          </div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-1)' }}>StockScore</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', letterSpacing: 0.5 }}>Financial Analytics Platform</div>
          </div>
        </div>

        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-1)', margin: 0, marginBottom: 4 }}>
          {mode === 'login' ? 'Welcome Back' : 'Create Account'}
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-3)', margin: 0, marginBottom: 24 }}>
          {mode === 'login' ? 'Sign in to continue' : 'Get started in seconds'}
        </p>

        <form onSubmit={handle}>
          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 6, fontWeight: 500 }}>
              Email
            </label>
            <input
              style={inputStyle('email')}
              type="email" required
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@example.com"
              onFocus={() => setFocusField('email')}
              onBlur={() => setFocusField(null)}
            />
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 12, color: 'var(--text-2)', marginBottom: 6, fontWeight: 500 }}>
              Password
            </label>
            <input
              style={inputStyle('password')}
              type="password" required
              value={password} onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              onFocus={() => setFocusField('password')}
              onBlur={() => setFocusField(null)}
            />
          </div>

          {error && (
            <div style={{
              background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 'var(--radius-md)', padding: '10px 14px',
              color: '#fca5a5', fontSize: 13, marginBottom: 16,
            }}>
              {error}
            </div>
          )}

          <button
            type="submit" disabled={loading}
            style={{
              width: '100%', background: loading ? 'var(--primary-muted)' : 'var(--primary)',
              border: 'none', borderRadius: 'var(--radius-md)',
              padding: '11px 0', color: '#fff', fontWeight: 600, fontSize: 14,
              cursor: loading ? 'not-allowed' : 'pointer', transition: 'background 0.15s',
            }}
            onMouseEnter={e => { if (!loading) e.target.style.background = 'var(--primary-hover)' }}
            onMouseLeave={e => { if (!loading) e.target.style.background = 'var(--primary)' }}
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Sign Up'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 18, fontSize: 13, color: 'var(--text-3)' }}>
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <span
            onClick={() => { setMode(m => m === 'login' ? 'register' : 'login'); setError('') }}
            style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 500 }}
          >
            {mode === 'login' ? 'Sign Up' : 'Sign In'}
          </span>
        </div>

      </div>
    </div>
  )
}
