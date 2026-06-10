import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Login screen in the dashboard's "signal from noise" visual language:
// deep ink, emerald/gold/copper accents, mono kickers, crystallize entrance.

export default function LoginPage() {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [mode, setMode] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [booted, setBooted] = useState(false)

  useEffect(() => {
    const id = setTimeout(() => setBooted(true), 80)
    return () => clearTimeout(id)
  }, [])

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

  return (
    <div className={`fiq-login ${booted ? 'is-booted' : ''}`}>
      <style>{CSS}</style>
      <div className="fiq-login-scan" aria-hidden="true" />

      <section className="fiq-login-hero">
        <div className="fiq-login-kicker">FINANCEIQ · BIST EQUITY RESEARCH INSTRUMENT</div>
        <h1>
          A weak signal, reported <em>honestly</em>.
        </h1>
        <p>
          T→T+1 historical evaluation over 40 selected BIST stocks, 2020–2025. Leakage-safe features,
          BIST100 benchmarking, and a grounded assistant that explains findings without turning them
          into investment advice.
        </p>
        <div className="fiq-login-badges">
          <span className="fiq-login-badge">LEAKAGE-SAFE METHODOLOGY</span>
          <span className="fiq-login-badge">BIST100 BENCHMARK</span>
          <span className="fiq-login-badge is-gold">WALK-FORWARD IC ≈ 0</span>
        </div>
      </section>

      <div className="fiq-login-card">
        <div className="fiq-login-brand">
          <span className="fiq-login-mark">IQ</span>
          <span>
            <span className="fiq-login-name">FinanceIQ</span>
            <span className="fiq-login-sub">RESEARCH INSTRUMENT</span>
          </span>
        </div>

        <h2>{mode === 'login' ? 'Sign in' : 'Create account'}</h2>
        <p className="fiq-login-lead">
          {mode === 'login' ? 'Access the research terminal.' : 'Create access for the research terminal.'}
        </p>

        <form onSubmit={handle}>
          <label className="fiq-login-label" htmlFor="fiq-email">EMAIL</label>
          <input
            id="fiq-email"
            className="fiq-login-input"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />

          <label className="fiq-login-label" htmlFor="fiq-password">PASSWORD</label>
          <input
            id="fiq-password"
            className="fiq-login-input"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
          />

          {error && <div className="fiq-login-error">{error}</div>}

          <button className="fiq-login-submit" type="submit" disabled={loading}>
            {loading ? 'TUNING…' : mode === 'login' ? 'SIGN IN' : 'SIGN UP'}
          </button>
        </form>

        <div className="fiq-login-switch">
          {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
          <button
            type="button"
            onClick={() => { setMode((m) => (m === 'login' ? 'register' : 'login')); setError('') }}
          >
            {mode === 'login' ? 'Sign up' : 'Sign in'}
          </button>
        </div>

        <div className="fiq-login-caveat">
          <span className="fiq-login-pulse" aria-hidden="true" />
          Research only · Not investment advice
        </div>
      </div>
    </div>
  )
}

const CSS = `
.fiq-login {
  --li-ink: #0a0e0d;
  --li-paper: #e8ece6;
  --li-dim: #9fae9f;
  --li-faint: #6b7a70;
  --li-emerald: #4da583;
  --li-gold: #c8a35a;
  --li-copper: #a8674b;
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr));
  align-items: center;
  gap: clamp(28px, 5vw, 72px);
  padding: clamp(24px, 5vw, 64px);
  background:
    radial-gradient(1100px 540px at 78% -8%, rgba(77,165,131,0.08), transparent 60%),
    radial-gradient(800px 500px at 8% 108%, rgba(168,103,75,0.07), transparent 60%),
    linear-gradient(165deg, #0b100f 0%, var(--li-ink) 55%, #080b0a 100%);
  color: var(--li-paper);
  overflow: hidden;
}
.fiq-login-scan {
  position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0 1px, transparent 1px 4px);
}

.fiq-login-hero, .fiq-login-card {
  position: relative;
  opacity: 0;
  filter: blur(8px);
  transition: opacity 1s ease, filter 1s ease;
}
.fiq-login.is-booted .fiq-login-hero,
.fiq-login.is-booted .fiq-login-card { opacity: 1; filter: blur(0); }
.fiq-login.is-booted .fiq-login-card { transition-delay: 0.18s; }

.fiq-login-hero { max-width: 700px; }
.fiq-login-kicker {
  font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.34em;
  color: var(--li-faint); margin-bottom: 18px;
}
.fiq-login-hero h1 {
  margin: 0 0 14px; font-size: clamp(30px, 4.2vw, 54px); line-height: 1.04;
  font-weight: 650; letter-spacing: -0.015em; color: var(--li-paper);
}
.fiq-login-hero h1 em { font-style: italic; color: var(--li-emerald); }
.fiq-login-hero p { margin: 0; max-width: 58ch; color: var(--li-dim); font-size: 15px; line-height: 1.6; }
.fiq-login-badges { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 24px; }
.fiq-login-badge {
  font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.18em;
  color: var(--li-dim); border: 1px solid rgba(200,211,202,0.2);
  border-radius: 2px; padding: 7px 12px; background: rgba(14,20,19,0.6);
}
.fiq-login-badge.is-gold { color: var(--li-gold); border-color: rgba(200,163,90,0.45); }

.fiq-login-card {
  width: 400px; max-width: 100%; justify-self: start;
  border: 1px solid rgba(200,211,202,0.18); border-left: 3px solid var(--li-emerald);
  border-radius: 3px; padding: 34px 32px 26px;
  background: linear-gradient(180deg, rgba(14,20,19,0.92), rgba(10,14,13,0.88));
  box-shadow: 0 28px 90px rgba(0,0,0,0.5);
}
.fiq-login-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }
.fiq-login-mark {
  width: 38px; height: 38px; display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-weight: 600; font-size: 15px; color: #0a0e0d;
  background: linear-gradient(135deg, var(--li-gold), var(--li-emerald)); border-radius: 2px;
}
.fiq-login-name { display: block; font-size: 16px; font-weight: 700; color: var(--li-paper); }
.fiq-login-sub {
  display: block; font-family: var(--font-mono); font-size: 8.5px;
  letter-spacing: 0.28em; color: var(--li-gold); margin-top: 1px;
}
.fiq-login-card h2 { margin: 0 0 4px; font-size: 19px; font-weight: 650; color: var(--li-paper); }
.fiq-login-lead { margin: 0 0 24px; font-size: 13px; color: var(--li-faint); }

.fiq-login-label {
  display: block; font-family: var(--font-mono); font-size: 10px;
  letter-spacing: 0.26em; color: var(--li-dim); margin-bottom: 7px;
}
.fiq-login-input {
  width: 100%; box-sizing: border-box; margin-bottom: 16px;
  background: rgba(10,14,13,0.8); border: 1px solid rgba(200,211,202,0.22);
  border-radius: 2px; padding: 11px 14px;
  color: var(--li-paper); font-size: 14px; font-family: var(--font-mono);
  outline: none; transition: border-color 0.18s, box-shadow 0.18s;
}
.fiq-login-input::placeholder { color: var(--li-faint); }
.fiq-login-input:focus {
  border-color: var(--li-emerald);
  box-shadow: 0 0 0 1px rgba(77,165,131,0.35), 0 0 18px rgba(77,165,131,0.12);
}
.fiq-login-error {
  background: rgba(168,103,75,0.1); border: 1px solid rgba(168,103,75,0.45);
  border-radius: 2px; padding: 10px 14px; color: #d8a18b; font-size: 13px; margin-bottom: 16px;
}
.fiq-login-submit {
  width: 100%; padding: 12px 0; margin-top: 4px;
  background: var(--li-gold); border: none; border-radius: 2px;
  color: #0a0e0d; font-family: var(--font-mono); font-size: 12px;
  font-weight: 700; letter-spacing: 0.26em; cursor: pointer;
  transition: background 0.18s, box-shadow 0.18s;
}
.fiq-login-submit:hover:not(:disabled) { background: #dcbb74; box-shadow: 0 0 22px rgba(200,163,90,0.3); }
.fiq-login-submit:focus-visible { outline: 1px solid var(--li-paper); outline-offset: 2px; }
.fiq-login-submit:disabled { background: rgba(200,163,90,0.4); cursor: not-allowed; }

.fiq-login-switch { text-align: center; margin-top: 18px; font-size: 13px; color: var(--li-faint); }
.fiq-login-switch button {
  background: none; border: none; padding: 0; font: inherit;
  color: var(--li-emerald); cursor: pointer; font-weight: 600;
}
.fiq-login-switch button:hover { text-decoration: underline; }

.fiq-login-caveat {
  display: flex; align-items: center; gap: 9px; justify-content: center;
  margin-top: 22px; padding-top: 16px; border-top: 1px dashed rgba(200,211,202,0.18);
  font-family: var(--font-mono); font-size: 10.5px; letter-spacing: 0.12em; color: var(--li-dim);
}
.fiq-login-pulse {
  width: 6px; height: 6px; border-radius: 50%; background: var(--li-gold);
  animation: fiqLoginPulse 2.2s ease-in-out infinite;
}
@keyframes fiqLoginPulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }

@media (prefers-reduced-motion: reduce) {
  .fiq-login-hero, .fiq-login-card { opacity: 1 !important; filter: none !important; transition: none !important; }
  .fiq-login-pulse { animation: none; }
}
`
