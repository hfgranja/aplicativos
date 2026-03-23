import { Outlet, Navigate } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'
import Sidebar from './Sidebar'

const styles = {
  shell: { display: 'flex', minHeight: '100vh', background: '#0f1117' },
  main: { flex: 1, padding: '24px', overflowY: 'auto', maxWidth: 'calc(100vw - 240px)' },
}

export default function AppShell() {
  const { user, loading } = useAuth()
  if (loading) return <div style={{ color: '#e2e8f0', padding: 40 }}>Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return (
    <div style={styles.shell}>
      <Sidebar />
      <main style={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}
