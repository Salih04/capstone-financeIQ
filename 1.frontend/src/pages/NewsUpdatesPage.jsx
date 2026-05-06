import { useEffect, useMemo, useState } from 'react'
import { Newspaper, Sparkles, RefreshCw, ExternalLink } from 'lucide-react'
import api from '../api/client'
import { Card, EmptyState, SectionHeader } from '../components/ui'

const STORAGE_KEY = 'financeiq_news_state'
const MAX_ARTICLES = 9
const MAX_REFRESHES = 2
const MAX_PAGES = 3

const todayKey = () => new Date().toISOString().slice(0, 10)

const readState = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

const writeState = (state) => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export default function NewsUpdatesPage() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState({
    page: 1,
    refreshes: 0,
    date: todayKey(),
    shownIds: [],
  })

  const resetIfNewDay = () => {
    const current = readState()
    const today = todayKey()
    if (!current || current.date !== today) {
      const fresh = { page: 1, refreshes: 0, date: today, shownIds: [] }
      writeState(fresh)
      setStatus(fresh)
      setArticles([])
      return fresh
    }
    setStatus(current)
    return current
  }

  const loadPage = async (page) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/news/updates', { params: { page } })
      const incoming = res.data?.articles || []
      const currentIds = new Set(status.shownIds)
      const unique = incoming.filter(a => a.id && !currentIds.has(a.id))
      const limited = unique.slice(0, Math.max(0, MAX_ARTICLES - articles.length))
      const nextArticles = [...articles, ...limited].slice(0, MAX_ARTICLES)
      const nextIds = [...status.shownIds, ...limited.map(a => a.id)].slice(0, MAX_ARTICLES)
      const nextStatus = { ...status, page, shownIds: nextIds }
      setArticles(nextArticles)
      setStatus(nextStatus)
      writeState(nextStatus)
      if (!limited.length && res.data?.message) setError(res.data.message)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load news.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const state = resetIfNewDay()
    if (state && state.page === 1 && state.shownIds.length === 0) {
      loadPage(1)
    }
  }, [])

  const handleRefresh = async () => {
    if (loading) return
    if (status.refreshes >= MAX_REFRESHES) return
    if (articles.length >= MAX_ARTICLES) return
    const nextPage = Math.min(status.page + 1, MAX_PAGES)
    const nextStatus = { ...status, page: nextPage, refreshes: status.refreshes + 1 }
    setStatus(nextStatus)
    writeState(nextStatus)
    await loadPage(nextPage)
  }

  const canRefresh = status.refreshes < MAX_REFRESHES && articles.length < MAX_ARTICLES
  const refreshesLeft = Math.max(0, MAX_REFRESHES - status.refreshes)
  const shownCount = articles.length
  const displayStatus = useMemo(() => ({ shownCount, refreshesLeft }), [shownCount, refreshesLeft])

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      <SectionHeader icon={<Newspaper size={20} />} title="News & Updates" subtitle="Daily market headlines for BIST investors" />

      <Card style={{ padding: '1rem', marginBottom: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={handleRefresh}
              disabled={!canRefresh || loading}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                border: 'none',
                borderRadius: 'var(--radius-md)',
                background: canRefresh ? 'var(--primary)' : 'var(--surface-3)',
                color: canRefresh ? '#fff' : 'var(--text-3)',
                padding: '9px 12px',
                cursor: canRefresh ? 'pointer' : 'not-allowed',
              }}
            >
              <RefreshCw size={14} />
              {loading ? 'Refreshing...' : 'Refresh News'}
            </button>
            <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
              {displayStatus.shownCount} / {MAX_ARTICLES} news shown
              {' · '}
              Refreshes left: {displayStatus.refreshesLeft}
            </div>
          </div>
          <div style={{ fontSize: 11, color: 'var(--text-3)' }}>Resets daily</div>
        </div>
      </Card>

      <Card style={{ padding: '1rem' }}>
        <div style={{ fontSize: 12, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 8 }}>Latest Updates</div>
        {loading && articles.length === 0 ? (
          <div style={{ fontSize: 13, color: 'var(--text-3)' }}>Loading...</div>
        ) : articles.length ? (
          articles.map((n) => (
            <div key={n.id} style={{ borderTop: '1px solid var(--border)', padding: '12px 0' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                <div style={{ fontSize: 13.5, fontWeight: 700, color: 'var(--text-1)' }}>{n.title}</div>
                {n.url && (
                  <a href={n.url} target="_blank" rel="noreferrer" style={{ fontSize: 11, color: 'var(--primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    Read <ExternalLink size={11} />
                  </a>
                )}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-3)', marginTop: 4 }}>
                {n.source} • {new Date(n.published_at).toLocaleString('en-US')}
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text-2)', marginTop: 6 }}>{n.summary}</div>
              {n.ai_insight && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, color: 'var(--primary)' }}>
                  <Sparkles size={12} />
                  <span style={{ fontSize: 11 }}>{n.ai_insight}</span>
                </div>
              )}
            </div>
          ))
        ) : (
          <EmptyState title="No updates" description="Try refreshing again later." />
        )}
        {error && (
          <div style={{ marginTop: 10, fontSize: 12, color: 'var(--warning)' }}>{error}</div>
        )}
      </Card>
    </div>
  )
}
