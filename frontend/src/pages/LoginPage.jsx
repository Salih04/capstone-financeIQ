import { useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Chrome,
  KeyRound,
  Loader2,
  Lock,
  Mail,
  Radar,
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { ENABLE_GOOGLE_AUTH, ENABLE_SIGNUP } from '../lib/authConfig'

const MODES = new Set(['login', 'signup', 'forgot', 'reset-password'])
// signup is only reachable when explicitly enabled — otherwise it collapses to login.
const normalizeMode = (m) => (m === 'signup' && !ENABLE_SIGNUP ? 'login' : m)

function messageFrom(error) {
  if (!error) return 'Authentication failed.'
  if (typeof error === 'string') return error
  return error.message || 'Authentication failed.'
}

export default function LoginPage() {
  const auth = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const queryMode = new URLSearchParams(location.search).get('mode')
  const initialMode = normalizeMode(MODES.has(queryMode) ? queryMode : 'login')

  const [mode, setMode] = useState(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [working, setWorking] = useState('')
  const [booted, setBooted] = useState(false)

  const isResetMode = mode === 'reset-password' || auth.passwordRecovery

  useEffect(() => {
    const id = setTimeout(() => setBooted(true), 80)
    return () => clearTimeout(id)
  }, [])

  useEffect(() => {
    if (MODES.has(queryMode)) setMode(normalizeMode(queryMode))
  }, [queryMode])

  const activeTitle = useMemo(() => {
    if (!auth.supabaseConfigured) return 'Configure Supabase'
    if (isResetMode) return 'Set new password'
    if (mode === 'signup') return 'Create account'
    if (mode === 'forgot') return 'Recover access'
    return 'Open terminal'
  }, [auth.supabaseConfigured, isResetMode, mode])

  const lead = useMemo(() => {
    if (!auth.supabaseConfigured) return 'Missing frontend auth environment.'
    if (isResetMode) return 'Enter a new password for the confirmed recovery session.'
    if (mode === 'signup') return 'Supabase will send an email confirmation link.'
    if (mode === 'forgot') return 'Send a password reset link to your email.'
    return 'Use Supabase Auth to enter the research workspace.'
  }, [auth.supabaseConfigured, isResetMode, mode])

  if (!auth.loading && auth.isAuth && !isResetMode) {
    return <Navigate to="/dashboard" replace />
  }

  const clearState = () => {
    setError('')
    setSuccess('')
    setWorking('')
  }

  const switchMode = (next) => {
    clearState()
    setMode(next)
  }

  const handlePasswordAuth = async (event) => {
    event.preventDefault()
    clearState()
    setWorking(mode)
    try {
      if (mode === 'signup') {
        if (!ENABLE_SIGNUP) { setError('Account creation is disabled for this deployment.'); return }
        await auth.register(email, password)
        setPassword('')
        setSuccess('Check your email to confirm your account before signing in.')
      } else {
        await auth.login(email, password)
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      setError(messageFrom(err))
    } finally {
      setWorking('')
    }
  }

  const handleGoogle = async () => {
    clearState()
    setWorking('google')
    try {
      await auth.loginWithGoogle()
    } catch (err) {
      setError(messageFrom(err))
      setWorking('')
    }
  }

  const handleForgot = async (event) => {
    event.preventDefault()
    clearState()
    setWorking('forgot')
    try {
      await auth.sendPasswordReset(email)
      setSuccess('Password reset link sent. Check your email.')
    } catch (err) {
      setError(messageFrom(err))
    } finally {
      setWorking('')
    }
  }

  const handleUpdatePassword = async (event) => {
    event.preventDefault()
    clearState()
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setWorking('reset-password')
    try {
      await auth.updatePassword(newPassword)
      setSuccess('Password updated. Redirecting to the terminal.')
      setTimeout(() => navigate('/dashboard', { replace: true }), 700)
    } catch (err) {
      setError(messageFrom(err))
    } finally {
      setWorking('')
    }
  }

  const disabled = Boolean(working) || !auth.supabaseConfigured

  return (
    <div className={`fiq-login ${booted ? 'is-booted' : ''}`}>
      <style>{CSS}</style>
      <div className="fiq-grid" aria-hidden="true" />

      <section className="fiq-brief">
        <div className="fiq-kicker">FINANCEIQ · AUTH GATE</div>
        <h1>Research Terminal</h1>
        <p>
          Leakage-safe BIST research workspace. Weak signals stay visible.
          Authentication is real; conclusions remain research support only.
        </p>
        <div className="fiq-readout">
          <span>ML PRIMARY</span>
          <span>SUPABASE SESSION</span>
          <span>NOT INVESTMENT ADVICE</span>
        </div>
      </section>

      <section className="fiq-panel" aria-label="Authentication">
        <div className="fiq-brand">
          <span className="fiq-mark"><Radar size={18} /></span>
          <span>
            <span className="fiq-name">FinanceIQ</span>
            <span className="fiq-sub">RESEARCH INSTRUMENT</span>
          </span>
        </div>

        <h2>{activeTitle}</h2>
        <p className="fiq-lead">{lead}</p>

        {!auth.supabaseConfigured && (
          <div className="fiq-message is-error">
            <AlertTriangle size={15} />
            Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY, then restart Vite.
          </div>
        )}

        {error && (
          <div className="fiq-message is-error">
            <AlertTriangle size={15} />
            {error}
          </div>
        )}

        {success && (
          <div className="fiq-message is-success">
            <CheckCircle2 size={15} />
            {success}
          </div>
        )}

        {isResetMode ? (
          <form onSubmit={handleUpdatePassword} className="fiq-form">
            <label htmlFor="new-password">NEW PASSWORD</label>
            <div className="fiq-input-wrap">
              <KeyRound size={16} />
              <input
                id="new-password"
                type="password"
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={disabled}
                required
              />
            </div>
            <label htmlFor="confirm-password">CONFIRM PASSWORD</label>
            <div className="fiq-input-wrap">
              <Lock size={16} />
              <input
                id="confirm-password"
                type="password"
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={disabled}
                required
              />
            </div>
            <button className="fiq-primary" type="submit" disabled={disabled}>
              {working === 'reset-password' ? <Loader2 className="fiq-spin" size={16} /> : <ArrowRight size={16} />}
              UPDATE PASSWORD
            </button>
          </form>
        ) : mode === 'forgot' ? (
          <form onSubmit={handleForgot} className="fiq-form">
            <label htmlFor="email">EMAIL</label>
            <div className="fiq-input-wrap">
              <Mail size={16} />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={disabled}
                required
              />
            </div>
            <button className="fiq-primary" type="submit" disabled={disabled}>
              {working === 'forgot' ? <Loader2 className="fiq-spin" size={16} /> : <ArrowRight size={16} />}
              SEND RESET LINK
            </button>
          </form>
        ) : (
          <form onSubmit={handlePasswordAuth} className="fiq-form">
            <label htmlFor="email">EMAIL</label>
            <div className="fiq-input-wrap">
              <Mail size={16} />
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                disabled={disabled}
                required
              />
            </div>
            <label htmlFor="password">PASSWORD</label>
            <div className="fiq-input-wrap">
              <Lock size={16} />
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                disabled={disabled}
                minLength={8}
                required
              />
            </div>
            <button className="fiq-primary" type="submit" disabled={disabled}>
              {working === mode ? <Loader2 className="fiq-spin" size={16} /> : <ArrowRight size={16} />}
              {mode === 'signup' ? 'CREATE ACCOUNT' : 'SIGN IN'}
            </button>
          </form>
        )}

        {!isResetMode && (
          <>
            {ENABLE_GOOGLE_AUTH && (
              <button className="fiq-google" type="button" onClick={handleGoogle} disabled={disabled}>
                {working === 'google' ? <Loader2 className="fiq-spin" size={16} /> : <Chrome size={16} />}
                CONTINUE WITH GOOGLE
              </button>
            )}
            <div className="fiq-links">
              {mode !== 'login' && <button type="button" onClick={() => switchMode('login')}>Sign in</button>}
              {ENABLE_SIGNUP && mode !== 'signup' && <button type="button" onClick={() => switchMode('signup')}>Create account</button>}
              {mode !== 'forgot' && <button type="button" onClick={() => switchMode('forgot')}>Forgot password</button>}
            </div>
          </>
        )}

        <div className="fiq-caveat">
          {ENABLE_SIGNUP ? 'Research only · Supabase Auth' : 'Private deployment · Approved users only · Accounts created by the owner'}
        </div>
      </section>
    </div>
  )
}

const CSS = `
.fiq-login {
  --li-ink: #0a0e0d;
  --li-panel: #101614;
  --li-paper: #e8ece6;
  --li-dim: #9fae9f;
  --li-faint: #6b7a70;
  --li-emerald: #4da583;
  --li-gold: #c8a35a;
  --li-copper: #a8674b;
  position: relative;
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 420px);
  gap: clamp(26px, 5vw, 68px);
  align-items: center;
  padding: clamp(24px, 5vw, 64px);
  background:
    linear-gradient(135deg, rgba(77,165,131,0.08), transparent 36%),
    linear-gradient(315deg, rgba(200,163,90,0.07), transparent 34%),
    linear-gradient(180deg, #0c1110, #080b0a);
  color: var(--li-paper);
  overflow: hidden;
}
.fiq-grid {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(rgba(255,255,255,0.028) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.024) 1px, transparent 1px),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.018) 0 1px, transparent 1px 5px);
  background-size: 56px 56px, 56px 56px, auto;
  mask-image: linear-gradient(90deg, rgba(0,0,0,0.9), rgba(0,0,0,0.28));
}
.fiq-brief,
.fiq-panel {
  position: relative;
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.7s ease, transform 0.7s ease;
}
.fiq-login.is-booted .fiq-brief,
.fiq-login.is-booted .fiq-panel {
  opacity: 1;
  transform: translateY(0);
}
.fiq-brief {
  max-width: 720px;
}
.fiq-kicker,
.fiq-sub,
.fiq-readout,
.fiq-form label,
.fiq-primary,
.fiq-google,
.fiq-caveat {
  font-family: var(--font-mono);
}
.fiq-kicker {
  font-size: 11px;
  letter-spacing: 0.24em;
  color: var(--li-gold);
  margin-bottom: 18px;
}
.fiq-brief h1 {
  margin: 0 0 16px;
  font-size: clamp(36px, 7vw, 72px);
  line-height: 0.98;
  font-weight: 760;
  letter-spacing: 0;
}
.fiq-brief p {
  margin: 0;
  max-width: 60ch;
  color: var(--li-dim);
  line-height: 1.65;
  font-size: 15px;
}
.fiq-readout {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 24px;
}
.fiq-readout span {
  border: 1px solid rgba(200,211,202,0.18);
  background: rgba(10,14,13,0.62);
  color: var(--li-dim);
  font-size: 10px;
  letter-spacing: 0.14em;
  padding: 7px 10px;
  border-radius: 2px;
}
.fiq-panel {
  border: 1px solid rgba(200,211,202,0.18);
  border-left: 3px solid var(--li-emerald);
  background: linear-gradient(180deg, rgba(16,22,20,0.94), rgba(10,14,13,0.92));
  box-shadow: 0 28px 90px rgba(0,0,0,0.48);
  border-radius: 4px;
  padding: 30px;
}
.fiq-brand {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 26px;
}
.fiq-mark {
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: #0a0e0d;
  background: linear-gradient(135deg, var(--li-gold), var(--li-emerald));
  border-radius: 3px;
}
.fiq-name {
  display: block;
  font-size: 16px;
  font-weight: 760;
}
.fiq-sub {
  display: block;
  color: var(--li-gold);
  font-size: 9px;
  letter-spacing: 0.2em;
  margin-top: 2px;
}
.fiq-panel h2 {
  margin: 0 0 6px;
  font-size: 22px;
  font-weight: 720;
  letter-spacing: 0;
}
.fiq-lead {
  margin: 0 0 22px;
  color: var(--li-dim);
  font-size: 13px;
  line-height: 1.55;
}
.fiq-form {
  display: grid;
  gap: 10px;
}
.fiq-form label {
  color: var(--li-dim);
  font-size: 10px;
  letter-spacing: 0.18em;
  margin-top: 4px;
}
.fiq-input-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  border: 1px solid rgba(200,211,202,0.22);
  background: rgba(10,14,13,0.72);
  border-radius: 3px;
  padding: 0 12px;
  color: var(--li-faint);
}
.fiq-input-wrap:focus-within {
  border-color: var(--li-emerald);
  box-shadow: 0 0 0 1px rgba(77,165,131,0.28), 0 0 18px rgba(77,165,131,0.12);
}
.fiq-input-wrap input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--li-paper);
  padding: 12px 0;
  font-size: 14px;
  font-family: var(--font-mono);
}
.fiq-input-wrap input::placeholder {
  color: var(--li-faint);
}
.fiq-primary,
.fiq-google {
  width: 100%;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 760;
  letter-spacing: 0.16em;
  transition: background 0.16s, border-color 0.16s, color 0.16s, box-shadow 0.16s;
}
.fiq-primary {
  margin-top: 8px;
  border: 1px solid rgba(200,163,90,0.82);
  background: var(--li-gold);
  color: #0a0e0d;
}
.fiq-primary:hover:not(:disabled) {
  background: #dcbb74;
  box-shadow: 0 0 22px rgba(200,163,90,0.28);
}
.fiq-google {
  margin-top: 12px;
  border: 1px solid rgba(200,211,202,0.2);
  background: rgba(10,14,13,0.35);
  color: var(--li-paper);
}
.fiq-google:hover:not(:disabled) {
  border-color: rgba(77,165,131,0.55);
  color: var(--li-emerald);
}
.fiq-primary:disabled,
.fiq-google:disabled,
.fiq-input-wrap input:disabled {
  opacity: 0.58;
  cursor: not-allowed;
}
.fiq-links {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 16px;
}
.fiq-links button {
  border: 0;
  background: transparent;
  color: var(--li-emerald);
  cursor: pointer;
  font-size: 13px;
  padding: 0;
}
.fiq-links button:hover {
  color: var(--li-paper);
}
.fiq-message {
  display: flex;
  align-items: flex-start;
  gap: 9px;
  border-radius: 3px;
  padding: 10px 12px;
  font-size: 13px;
  line-height: 1.45;
  margin-bottom: 14px;
}
.fiq-message.is-error {
  border: 1px solid rgba(168,103,75,0.5);
  background: rgba(168,103,75,0.12);
  color: #d8a18b;
}
.fiq-message.is-success {
  border: 1px solid rgba(77,165,131,0.5);
  background: rgba(77,165,131,0.11);
  color: #9ed8c2;
}
.fiq-caveat {
  margin-top: 22px;
  padding-top: 15px;
  border-top: 1px dashed rgba(200,211,202,0.16);
  color: var(--li-faint);
  text-align: center;
  font-size: 10.5px;
  letter-spacing: 0.1em;
}
.fiq-spin {
  animation: fiq-spin 0.85s linear infinite;
}
@keyframes fiq-spin {
  to { transform: rotate(360deg); }
}
@media (max-width: 840px) {
  .fiq-login {
    grid-template-columns: 1fr;
    align-items: start;
  }
  .fiq-panel {
    padding: 24px;
  }
}
@media (prefers-reduced-motion: reduce) {
  .fiq-brief,
  .fiq-panel,
  .fiq-spin {
    transition: none;
    animation: none;
  }
}
`
