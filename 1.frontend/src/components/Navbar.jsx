import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const s = {
  nav: { background: '#1e293b', borderBottom: '1px solid #334155', padding: '0 2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 56 },
  brand: { fontWeight: 700, fontSize: '1.1rem', color: '#38bdf8', textDecoration: 'none', letterSpacing: '-0.5px' },
  right: { display: 'flex', gap: '0.6rem', alignItems: 'center' },
  link: { color: '#94a3b8', textDecoration: 'none', fontSize: 13, padding: '4px 8px', borderRadius: 6 },
  linkActive: { color: '#38bdf8', background: '#0f172a' },
  btn: { background: 'transparent', border: '1px solid #475569', color: '#94a3b8', padding: '5px 12px', borderRadius: 6, cursor: 'pointer', fontSize: 13 },
  roleBadge: { fontSize: 10, fontWeight: 700, borderRadius: 4, padding: '2px 6px', marginLeft: 4 },
}

export default function Navbar() {
  const { isAuth, user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const linkStyle = (path) => ({
    ...s.link,
    ...(location.pathname.startsWith(path) ? s.linkActive : {}),
  })

  const isAdmin = user?.role === 'admin'
  const isAnalyst = user?.role === 'analyst' || isAdmin

  return (
    <nav style={s.nav}>
      <Link to="/search" style={s.brand}>📈 StockScore V3</Link>
      {isAuth && (
        <div style={s.right}>
          <Link to="/search" style={linkStyle('/search')}>Ara</Link>
          <Link to="/compare" style={linkStyle('/compare')}>Compare</Link>
          {isAnalyst && <Link to="/validation" style={linkStyle('/validation')}>Validation</Link>}
          {isAdmin && <Link to="/admin" style={linkStyle('/admin')}>Admin</Link>}
          {isAdmin && <Link to="/data-health" style={linkStyle('/data-health')}>Data Health</Link>}
          {isAdmin && <Link to="/labeling" style={linkStyle('/labeling')}>Labeling</Link>}
          <span style={{ ...s.link, color: '#64748b', fontSize: 12 }}>
            {user?.email}
            {user?.role && (
              <span style={{ ...s.roleBadge,
                background: isAdmin ? '#1e3a5f' : isAnalyst ? '#14532d' : '#0f172a',
                color: isAdmin ? '#60a5fa' : isAnalyst ? '#4ade80' : '#64748b',
              }}>{user.role}</span>
            )}
          </span>
          <button style={s.btn} onClick={handleLogout}>Sign Out</button>
        </div>
      )}
    </nav>
  )
}
