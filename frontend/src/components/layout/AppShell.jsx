import { useState } from 'react'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function AppShell({ children }) {
  const [collapsed, setCollapsed] = useState(false)
  const sidebarW = collapsed ? 'var(--sidebar-coll)' : 'var(--sidebar-w)'

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <div style={{ flex: 1, marginLeft: sidebarW, transition: 'margin-left 0.22s cubic-bezier(.4,0,.2,1)', minWidth: 0 }}>
        <Topbar sidebarCollapsed={collapsed} />
        <main style={{
          marginTop: 'var(--topbar-h)',
          minHeight: 'calc(100vh - var(--topbar-h))',
          padding: '28px 28px 48px',
        }}>
          {children}
        </main>
      </div>
    </div>
  )
}
