import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuth, loading } = useAuth()
  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: '#0a0e0d',
        color: '#c8a35a',
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        letterSpacing: '0.16em',
      }}>
        AUTH SIGNAL LOCKING
      </div>
    )
  }
  return isAuth ? children : <Navigate to="/login" replace />
}
