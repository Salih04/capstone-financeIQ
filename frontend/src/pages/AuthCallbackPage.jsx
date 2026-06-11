import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AuthCallbackPage() {
  const { isAuth, loading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (loading) return
    navigate(isAuth ? '/dashboard' : '/login', { replace: true })
  }, [isAuth, loading, navigate])

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
      VERIFYING AUTH CALLBACK
    </div>
  )
}
