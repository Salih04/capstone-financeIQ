import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  LayoutDashboard, Building2, BarChart3, GitCompare, FileText,
  ShieldCheck, Activity, Tag, FlaskConical, ChevronLeft,
  ChevronRight, LogOut, User, Settings, TrendingUp, Sparkles, BrainCircuit,
} from 'lucide-react'

const NAV_SECTIONS = [
  {
    label: null,
    items: [
      { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { path: '/companies', icon: Building2, label: 'Companies' },
      { path: '/compare', icon: GitCompare, label: 'Compare' },
      { path: '/reports', icon: FileText, label: 'Reports' },
    ],
  },
  {
    label: 'Analysis',
    items: [
      { path: '/research', icon: Sparkles, label: 'Research', roles: ['analyst', 'admin'] },
      { path: '/validation', icon: FlaskConical, label: 'Validation Lab', roles: ['analyst', 'admin'] },
      { path: '/forecasting', icon: BrainCircuit, label: 'Forecasting (legacy)', roles: ['analyst', 'admin'] },
    ],
  },
  {
    label: 'Admin',
    roles: ['admin'],
    items: [
      { path: '/admin', icon: ShieldCheck, label: 'Model Registry', roles: ['admin'] },
      { path: '/data-health', icon: Activity, label: 'Data Health', roles: ['admin'] },
      { path: '/labeling', icon: Tag, label: 'Labeling Lab', roles: ['admin'] },
    ],
  },
]

const s = {
  sidebar: {
    position: 'fixed',
    top: 0,
    left: 0,
    height: '100vh',
    background: 'var(--surface-1)',
    borderRight: '1px solid var(--border)',
    display: 'flex',
    flexDirection: 'column',
    zIndex: 100,
    transition: 'width 0.22s cubic-bezier(.4,0,.2,1)',
    overflow: 'hidden',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '0 16px',
    height: 'var(--topbar-h)',
    borderBottom: '1px solid var(--border)',
    flexShrink: 0,
    overflow: 'hidden',
    textDecoration: 'none',
  },
  logoIcon: {
    width: 32,
    height: 32,
    background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
    borderRadius: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    boxShadow: '0 2px 8px var(--primary-glow)',
  },
  logoText: {
    fontWeight: 800,
    fontSize: 16,
    color: 'var(--text-1)',
    letterSpacing: '-0.4px',
    whiteSpace: 'nowrap',
  },
  logoSub: {
    fontSize: 9,
    fontWeight: 600,
    color: 'var(--primary)',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: -2,
  },
  nav: {
    flex: 1,
    overflowY: 'auto',
    overflowX: 'hidden',
    padding: '8px 0',
  },
  sectionLabel: {
    fontSize: 10,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 1.2,
    color: 'var(--text-3)',
    padding: '12px 16px 4px',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '9px 12px 9px 14px',
    margin: '1px 8px',
    borderRadius: 'var(--radius-md)',
    cursor: 'pointer',
    transition: 'background 0.15s, color 0.15s',
    color: 'var(--text-2)',
    fontSize: 13.5,
    fontWeight: 500,
    textDecoration: 'none',
    whiteSpace: 'nowrap',
    overflow: 'hidden',
  },
  itemActive: {
    background: 'var(--primary-subtle)',
    color: 'var(--primary-hover)',
  },
  itemHover: {
    background: 'var(--surface-hover)',
    color: 'var(--text-1)',
  },
  itemIcon: {
    flexShrink: 0,
    width: 18,
    height: 18,
  },
  collapseBtn: {
    margin: '8px',
    padding: '8px',
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-strong)',
    background: 'transparent',
    color: 'var(--text-3)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.15s, color 0.15s',
    flexShrink: 0,
  },
  footer: {
    borderTop: '1px solid var(--border)',
    padding: '10px 8px',
    flexShrink: 0,
  },
  userRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 6px',
    borderRadius: 'var(--radius-md)',
    overflow: 'hidden',
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: 10,
    background: 'linear-gradient(135deg, var(--primary-muted), rgba(85,194,195,0.25))',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'var(--primary-hover)',
    fontSize: 12,
    fontWeight: 700,
    flexShrink: 0,
  },
  userInfo: {
    overflow: 'hidden',
  },
  userEmail: {
    fontSize: 12,
    fontWeight: 600,
    color: 'var(--text-1)',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: 130,
  },
  rolePill: {
    fontSize: 9,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    borderRadius: 4,
    padding: '1px 6px',
    marginTop: 2,
    display: 'inline-block',
  },
  logoutBtn: {
    padding: '7px',
    borderRadius: 'var(--radius-md)',
    border: 'none',
    background: 'transparent',
    color: 'var(--text-3)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    transition: 'background 0.15s, color 0.15s',
    flexShrink: 0,
    marginLeft: 'auto',
  },
}

const ROLE_COLORS = {
  admin: { bg: 'rgba(14,165,233,0.15)', color: 'var(--primary-hover)' },
  analyst: { bg: 'rgba(16,185,129,0.15)', color: 'var(--success-light)' },
  investor: { bg: 'rgba(99,102,241,0.15)', color: '#a5b4fc' },
}

function NavItem({ item, collapsed, active }) {
  const Icon = item.icon
  const [hovered, setHovered] = useState(false)

  const style = {
    ...s.item,
    ...(active ? s.itemActive : {}),
    ...(hovered && !active ? s.itemHover : {}),
    justifyContent: collapsed ? 'center' : 'flex-start',
    padding: collapsed ? '9px' : '9px 12px 9px 14px',
    margin: collapsed ? '1px 6px' : '1px 8px',
    position: 'relative',
  }

  const iconColor = active
    ? 'var(--primary-hover)'
    : hovered
    ? 'var(--text-1)'
    : 'var(--text-2)'

  return (
    <Link
      to={item.path}
      style={style}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      title={collapsed ? item.label : undefined}
    >
      {active && (
        <span style={{
          position: 'absolute',
          left: 0,
          top: '20%',
          height: '60%',
          width: 3,
          background: 'var(--primary)',
          borderRadius: '0 3px 3px 0',
        }} />
      )}
      <Icon size={17} style={{ flexShrink: 0, color: iconColor }} />
      {!collapsed && (
        <span style={{
          fontSize: 13.5,
          fontWeight: active ? 600 : 500,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}>
          {item.label}
        </span>
      )}
    </Link>
  )
}

export default function Sidebar({ collapsed, onToggle }) {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/')
  const hasRole = (roles) => !roles || roles.includes(user?.role)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const userInitials = user?.email?.substring(0, 2).toUpperCase() || 'U'
  const roleColors = ROLE_COLORS[user?.role] || ROLE_COLORS.investor

  return (
    <aside style={{ ...s.sidebar, width: collapsed ? 'var(--sidebar-coll)' : 'var(--sidebar-w)' }}>
      {/* Logo */}
      <Link to="/dashboard" style={s.logo}>
        <div style={s.logoIcon}>
          <TrendingUp size={17} color="#0b111a" />
        </div>
        {!collapsed && (
          <div>
          <div style={s.logoText}>FinanceIQ</div>
          <div style={s.logoSub}>Success DNA</div>
          </div>
        )}
      </Link>

      {/* Navigation */}
      <nav style={s.nav}>
        {NAV_SECTIONS.map((section, si) => {
          if (section.roles && !hasRole(section.roles)) return null
          const visibleItems = section.items.filter(item => hasRole(item.roles))
          if (visibleItems.length === 0) return null

          return (
            <div key={si}>
              {section.label && !collapsed && (
                <div style={s.sectionLabel}>{section.label}</div>
              )}
              {section.label && collapsed && <div style={{ height: 8 }} />}
              {visibleItems.map(item => (
                <NavItem
                  key={item.path}
                  item={item}
                  collapsed={collapsed}
                  active={isActive(item.path)}
                />
              ))}
            </div>
          )
        })}

        {/* AI Search prominent button */}
        <div style={{ padding: collapsed ? '12px 6px' : '12px 8px' }}>
          <Link
            to="/ai-search"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: collapsed ? 'center' : 'flex-start',
              gap: 10,
              padding: collapsed ? '10px' : '10px 14px',
              borderRadius: 12,
              background: isActive('/ai-search')
                ? 'linear-gradient(135deg, rgba(244,176,74,0.2), rgba(85,194,195,0.15))'
                : 'linear-gradient(135deg, rgba(244,176,74,0.08), rgba(85,194,195,0.06))',
              border: '1px solid rgba(244,176,74,0.25)',
              textDecoration: 'none',
              transition: 'all 0.2s',
              cursor: 'pointer',
              boxShadow: isActive('/ai-search') ? '0 0 16px rgba(244,176,74,0.2)' : '0 0 8px rgba(244,176,74,0.08)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.background = 'linear-gradient(135deg, rgba(244,176,74,0.2), rgba(85,194,195,0.15))'
              e.currentTarget.style.borderColor = 'rgba(244,176,74,0.4)'
              e.currentTarget.style.boxShadow = '0 0 20px rgba(244,176,74,0.25)'
            }}
            onMouseLeave={e => {
              if (!isActive('/ai-search')) {
                e.currentTarget.style.background = 'linear-gradient(135deg, rgba(244,176,74,0.08), rgba(85,194,195,0.06))'
                e.currentTarget.style.borderColor = 'rgba(244,176,74,0.25)'
                e.currentTarget.style.boxShadow = '0 0 8px rgba(244,176,74,0.08)'
              }
            }}
            title={collapsed ? 'AI Search' : undefined}
          >
            <div style={{
              width: 26, height: 26, borderRadius: 8, flexShrink: 0,
              background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 2px 8px rgba(244,176,74,0.3)',
            }}>
              <Sparkles size={13} color="#fff" />
            </div>
            {!collapsed && (
              <>
                <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--primary-hover)', flex: 1 }}>AI Search</span>
                <span style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-3)', fontFamily: 'var(--font-mono)', background: 'rgba(244,176,74,0.1)', borderRadius: 4, padding: '1px 5px' }}>
                  {navigator.platform?.includes('Mac') ? '⌘' : '⌃'}K
                </span>
              </>
            )}
          </Link>
        </div>
      </nav>

      {/* Collapse toggle */}
      <button
        style={s.collapseBtn}
        onClick={onToggle}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-2)'; e.currentTarget.style.color = 'var(--text-1)' }}
        onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-3)' }}
        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      {/* User footer */}
      <div style={s.footer}>
        <div style={s.userRow}>
          <div style={s.avatar}>{userInitials}</div>
          {!collapsed && (
            <div style={s.userInfo}>
              <div style={s.userEmail}>{user?.email || 'User'}</div>
              <span style={{ ...s.rolePill, background: roleColors.bg, color: roleColors.color }}>
                {user?.role || 'viewer'}
              </span>
            </div>
          )}
          {!collapsed && (
            <button
              style={s.logoutBtn}
              onClick={handleLogout}
              title="Sign out"
              onMouseEnter={e => { e.currentTarget.style.background = 'var(--danger-subtle)'; e.currentTarget.style.color = 'var(--danger-light)' }}
              onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-3)' }}
            >
              <LogOut size={15} />
            </button>
          )}
        </div>
        {collapsed && (
          <button
            style={{ ...s.logoutBtn, margin: '0 auto', display: 'flex' }}
            onClick={handleLogout}
            title="Sign out"
            onMouseEnter={e => { e.currentTarget.style.background = 'var(--danger-subtle)'; e.currentTarget.style.color = 'var(--danger-light)' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--text-3)' }}
          >
            <LogOut size={15} />
          </button>
        )}
      </div>
    </aside>
  )
}
