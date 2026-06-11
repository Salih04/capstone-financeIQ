import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const SHELL = {
  minHeight: '100vh',
  display: 'grid',
  placeItems: 'center',
  background: '#0a0e0d',
  color: '#c8a35a',
  fontFamily: 'var(--font-mono)',
  fontSize: 12,
  letterSpacing: '0.16em',
  textAlign: 'center',
  padding: 24,
}

export default function ProtectedRoute({ children }) {
  const { isAuth, loading, approved, user, logout } = useAuth()

  // Wait for Supabase session restore before deciding — no protected content
  // flashes before the auth/approval check resolves.
  if (loading) {
    return <div style={SHELL}>AUTH SIGNAL LOCKING</div>
  }

  // No session → login. (Backend require_access is the real boundary; this is UX.)
  if (!isAuth) return <Navigate to="/login" replace />

  // Authenticated but not on the approved allowlist → blocked, not redirected.
  if (!approved) {
    return (
      <div style={SHELL}>
        <div style={{ maxWidth: 460, lineHeight: 1.8 }}>
          <div style={{ color: '#a8674b', marginBottom: 14 }}>● PRIVATE DEPLOYMENT</div>
          <div style={{ color: '#e8ece6', fontSize: 13 }}>
            {user?.email ? `${user.email} is not approved for access.` : 'This account is not approved for access.'}
          </div>
          <div style={{ color: '#6b7a70', marginTop: 12, fontSize: 11 }}>
            Contact the owner to be added to the approved users.
          </div>
          <button
            type="button"
            onClick={logout}
            style={{
              marginTop: 22, background: 'transparent', color: '#c8a35a',
              border: '1px solid rgba(200,163,90,0.5)', borderRadius: 2,
              padding: '8px 16px', cursor: 'pointer', fontFamily: 'inherit',
              fontSize: 11, letterSpacing: '0.16em',
            }}
          >
            SIGN OUT
          </button>
        </div>
      </div>
    )
  }

  return children
}
