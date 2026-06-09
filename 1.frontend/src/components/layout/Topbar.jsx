import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Search, Bell, Sun, Moon, X, Sparkles } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import api from '../../api/client'

const s = {
  topbar: {
    position: 'fixed',
    top: 0,
    right: 0,
    height: 'var(--topbar-h)',
    background: 'rgba(7,17,31,0.86)',
    backdropFilter: 'blur(18px)',
    borderBottom: '1px solid var(--border)',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '0 20px',
    zIndex: 90,
    transition: 'left 0.22s cubic-bezier(.4,0,.2,1)',
  },
  searchWrap: {
    flex: 1,
    maxWidth: 420,
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  searchIcon: {
    position: 'absolute',
    left: 12,
    color: 'var(--text-3)',
    pointerEvents: 'none',
  },
  searchInput: {
    width: '100%',
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    padding: '8px 14px 8px 38px',
    color: 'var(--text-1)',
    fontSize: 13.5,
    outline: 'none',
    transition: 'border-color 0.15s, box-shadow 0.15s',
  },
  searchDropdown: {
    position: 'absolute',
    top: 'calc(100% + 6px)',
    left: 0,
    right: 0,
    background: 'var(--surface-2)',
    border: '1px solid var(--border-bright)',
    borderRadius: 'var(--radius-lg)',
    boxShadow: 'var(--shadow-lg)',
    zIndex: 200,
    overflow: 'hidden',
    maxHeight: 320,
    overflowY: 'auto',
  },
  searchItem: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '10px 14px',
    cursor: 'pointer',
    transition: 'background 0.12s',
    fontSize: 13.5,
  },
  quickActions: {
    display: 'flex',
    gap: 6,
    marginLeft: 'auto',
  },
  qaBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 6,
    padding: '7px 12px',
    background: 'var(--surface-2)',
    border: '1px solid var(--border-strong)',
    borderRadius: 'var(--radius-md)',
    color: 'var(--text-2)',
    fontSize: 12.5,
    fontWeight: 500,
    cursor: 'pointer',
    whiteSpace: 'nowrap',
    transition: 'background 0.15s, color 0.15s, border-color 0.15s',
  },
  spacer: { flex: 1 },
  iconBtn: {
    width: 36,
    height: 36,
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--border-strong)',
    background: 'var(--surface-2)',
    color: 'var(--text-2)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background 0.15s, color 0.15s',
    flexShrink: 0,
  },
}

export default function Topbar({ sidebarCollapsed }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [searchOpen, setSearchOpen] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark')
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const searchRef = useRef(null)
  const notifRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  useEffect(() => {
    const handler = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setNotifOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const openNotif = async () => {
    if (!notifOpen) {
      try {
        const { data } = await api.get('/users/me/score-runs?limit=6')
        setNotifications(Array.isArray(data) ? data : [])
      } catch { setNotifications([]) }
    }
    setNotifOpen(o => !o)
  }
  const sidebarW = sidebarCollapsed ? 'var(--sidebar-coll)' : 'var(--sidebar-w)'

  useEffect(() => {
    if (searchQuery.length < 1) {
      setSearchResults([])
      setSearchOpen(false)
      return
    }
    const t = setTimeout(async () => {
      try {
        const { data } = await api.get(`/companies?q=${encodeURIComponent(searchQuery)}&limit=8`)
        setSearchResults(data)
        setSearchOpen(true)
      } catch { /* ignore */ }
    }, 250)
    return () => clearTimeout(t)
  }, [searchQuery])

  useEffect(() => {
    const handler = (e) => {
      if (searchRef.current && !searchRef.current.contains(e.target)) {
        setSearchOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSelectCompany = (c) => {
    setSearchQuery('')
    setSearchOpen(false)
    navigate(`/companies/${c.id}`)
  }

  const left = sidebarW

  return (
    <header style={{ ...s.topbar, left }}>
      {/* Search */}
      <div style={s.searchWrap} ref={searchRef}>
        <Search size={14} style={s.searchIcon} />
        <input
          style={s.searchInput}
          placeholder="Search companies, tickers..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          onFocus={() => searchResults.length > 0 && setSearchOpen(true)}
          onKeyDown={e => {
            if (e.key === 'Escape') { setSearchOpen(false); setSearchQuery('') }
            if (e.key === 'Enter' && searchQuery.trim()) {
              navigate(`/research-agent?q=${encodeURIComponent(searchQuery.trim())}`)
              setSearchOpen(false)
              setSearchQuery('')
            }
          }}
        />
        {searchQuery && (
          <button
            style={{ position: 'absolute', right: 10, background: 'none', border: 'none', color: 'var(--text-3)', cursor: 'pointer', display: 'flex' }}
            onClick={() => { setSearchQuery(''); setSearchOpen(false) }}
          >
            <X size={13} />
          </button>
        )}
        {searchOpen && searchResults.length > 0 && (
          <div style={s.searchDropdown}>
            <div style={{ padding: '6px 14px 4px', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--text-3)' }}>
              Companies
            </div>
            {searchResults.map(c => (
              <div
                key={c.id}
                style={s.searchItem}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                onClick={() => handleSelectCompany(c)}
              >
                <span style={{ fontWeight: 700, color: 'var(--primary-hover)', minWidth: 52 }}>{c.ticker}</span>
                <span style={{ color: 'var(--text-2)', fontSize: 13 }}>{c.company_name}</span>
                {c.sector && (
                  <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-3)', background: 'var(--surface-3)', borderRadius: 5, padding: '2px 7px' }}>
                    {c.sector}
                  </span>
                )}
              </div>
            ))}
            {/* AI Search footer */}
            <div
              style={{
                display: 'flex', alignItems: 'center', gap: 7,
                padding: '9px 14px', cursor: 'pointer',
                borderTop: '1px solid var(--border)',
                fontSize: 12, fontWeight: 600, color: 'var(--primary)',
        background: 'rgba(244,176,74,0.04)',
                transition: 'background 0.12s',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'rgba(244,176,74,0.1)'}
              onMouseLeave={e => e.currentTarget.style.background = 'rgba(244,176,74,0.04)'}
              onClick={() => {
                navigate(`/research-agent?q=${encodeURIComponent(searchQuery)}`)
                setSearchOpen(false)
                setSearchQuery('')
              }}
            >
              <Sparkles size={12} />
              Ask AI about "{searchQuery}"
            </div>
          </div>
        )}
      </div>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Theme toggle */}
      <button
        style={s.iconBtn}
        title="Toggle theme"
        onClick={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
        onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--warning)' }}
        onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface-2)'; e.currentTarget.style.color = 'var(--text-2)' }}
      >
        {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
      </button>

      {/* Notifications */}
      <div style={{ position: 'relative' }} ref={notifRef}>
        <button
          style={{ ...s.iconBtn, position: 'relative' }}
          title="Notifications"
          onClick={openNotif}
          onMouseEnter={e => { e.currentTarget.style.background = 'var(--surface-hover)'; e.currentTarget.style.color = 'var(--text-1)' }}
          onMouseLeave={e => { e.currentTarget.style.background = 'var(--surface-2)'; e.currentTarget.style.color = 'var(--text-2)' }}
        >
          <Bell size={15} />
          {notifications.length > 0 && (
            <span style={{
              position: 'absolute', top: 4, right: 4, width: 8, height: 8,
              borderRadius: '50%', background: 'var(--primary)', border: '1.5px solid var(--surface-1)',
            }} />
          )}
        </button>

        {notifOpen && (
          <div style={{
            position: 'absolute', top: 'calc(100% + 8px)', right: 0,
            width: 320, background: 'var(--surface-2)', border: '1px solid var(--border-bright)',
            borderRadius: 'var(--radius-lg)', boxShadow: 'var(--shadow-lg)', zIndex: 300, overflow: 'hidden',
          }}>
            <div style={{ padding: '10px 14px 8px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-1)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Recent Analyses</span>
              <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{notifications.length} runs</span>
            </div>
            {notifications.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', fontSize: 13, color: 'var(--text-3)' }}>
                No recent analyses
              </div>
            ) : (
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                {notifications.map(run => {
                  const scoreColor = run.total_score >= 70 ? 'var(--success)' : run.total_score >= 45 ? 'var(--warning)' : 'var(--danger)'
                  return (
                    <div
                      key={run.id}
                      onClick={() => { navigate(`/score-runs/${run.id}`); setNotifOpen(false) }}
                      style={{ display: 'flex', gap: 10, padding: '10px 14px', borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.12s' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--surface-hover)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-1)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {run.ticker || run.company_name || `Analysis #${run.id}`}
                        </div>
                        <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 2 }}>
                          {run.period} · {new Date(run.created_at).toLocaleDateString('en-US')}
                        </div>
                      </div>
                      {run.total_score != null && (
                        <span style={{ fontSize: 13, fontWeight: 700, color: scoreColor, alignSelf: 'center', fontVariantNumeric: 'tabular-nums' }}>
                          {run.total_score.toFixed(1)}
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
            <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
              <button
                onClick={() => { navigate('/research/companies'); setNotifOpen(false) }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--primary)', fontSize: 12, fontWeight: 600, padding: 0 }}
              >
                View companies →
              </button>
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
