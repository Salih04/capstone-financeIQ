import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LineChart, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react'

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
      minHeight: '100vh', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 340px), 1fr))', alignItems: 'center',
      gap: 28, padding: 28,
      background: 'var(--bg-deep)',
      backgroundImage: 'linear-gradient(135deg, rgba(244,176,74,0.10), transparent 38%), linear-gradient(315deg, rgba(85,194,195,0.08), transparent 42%)',
    }}>
      <section style={{ maxWidth: 760 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--primary-hover)', background: 'var(--primary-subtle)', border: '1px solid rgba(244,176,74,0.25)', borderRadius: 999, padding: '6px 12px', fontSize: 12, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.8 }}>
          <Sparkles size={15} />
          FinanceIQ Research Terminal
        </div>
        <h1 style={{ margin: '18px 0 10px', color: 'var(--text-1)', fontSize: 'clamp(2.4rem, 6vw, 4.5rem)', lineHeight: 1, fontWeight: 900 }}>
          BIST research support with validated data discipline.
        </h1>
        <p style={{ color: 'var(--text-2)', fontSize: 15.5, lineHeight: 1.7, maxWidth: 650, margin: 0 }}>
          Sign in to access company profiles, research scores, experiments, benchmark diagnostics, and the grounded AI assistant. Research support only; not investment advice.
        </p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 20 }}>
          <span style={heroBadge}><ShieldCheck size={13} /> Leakage-safe methodology</span>
          <span style={heroBadge}><LineChart size={13} /> BIST100 benchmark</span>
        </div>
      </section>

      <div style={{
        background: 'rgba(15, 23, 42, 0.78)', border: '1px solid var(--border-strong)',
        borderRadius: 'var(--radius-xl)', padding: '2.5rem 2.25rem', width: 400,
        maxWidth: '100%', boxSizing: 'border-box', boxShadow: 'var(--shadow-lg)',
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
            <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text-1)' }}>FinanceIQ</div>
            <div style={{ fontSize: 11, color: 'var(--text-3)', letterSpacing: 0.5 }}>Validated Research Terminal</div>
          </div>
        </div>

        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-1)', margin: 0, marginBottom: 4 }}>
          {mode === 'login' ? 'Welcome Back' : 'Create Account'}
        </h2>
        <p style={{ fontSize: 13, color: 'var(--text-3)', margin: 0, marginBottom: 24 }}>
          {mode === 'login' ? 'Sign in to continue' : 'Create access for the research terminal'}
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

const heroBadge = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  background: 'rgba(255,255,255,0.04)',
  border: '1px solid var(--border-strong)',
  borderRadius: 999,
  padding: '7px 11px',
  color: 'var(--text-2)',
  fontSize: 12,
  fontWeight: 800,
}
