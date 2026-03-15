import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { C } from '../../colors'

export function AppShell() {
  return (
    <div style={{
      display: 'flex', minHeight: '100vh', background: C.bg,
      color: C.text, fontFamily: 'JetBrains Mono',
    }}>
      <Sidebar />
      <main style={{ flex: 1, padding: 32, overflowY: 'auto', maxHeight: '100vh' }}>
        <Outlet />
      </main>
    </div>
  )
}
