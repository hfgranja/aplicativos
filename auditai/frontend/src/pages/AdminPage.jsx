import { useState, useEffect } from 'react'
import client from '../api/client'
import { useAuth } from '../hooks/useAuth'

const s = {
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 24 },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 24 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '8px 12px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '10px 12px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
}

export default function AdminPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [tenants, setTenants] = useState([])

  useEffect(() => {
    if (user?.is_admin) {
      client.get('/users').then(r => setUsers(r.data))
      client.get('/tenants').then(r => setTenants(r.data))
    }
  }, [user])

  if (!user?.is_admin) return <div style={{ color: '#64748b', padding: 40 }}>Access denied</div>

  return (
    <div>
      <h1 style={s.h1}>Administration</h1>

      <div style={s.section}>
        <div style={s.sectionTitle}>Tenants ({tenants.length})</div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>Name</th><th style={s.th}>Slug</th><th style={s.th}>Plan</th><th style={s.th}>Active</th>
          </tr></thead>
          <tbody>
            {tenants.map(t => (
              <tr key={t.id}>
                <td style={s.td}>{t.name}</td>
                <td style={s.td}>{t.slug}</td>
                <td style={s.td}>{t.plan}</td>
                <td style={s.td}>{t.is_active ? '✓' : '✗'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>Users ({users.length})</div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>Email</th><th style={s.th}>Name</th><th style={s.th}>Tenant</th><th style={s.th}>Admin</th>
          </tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td style={s.td}>{u.email}</td>
                <td style={s.td}>{u.full_name || '—'}</td>
                <td style={s.td}>{u.tenant_id?.slice(0, 12)}</td>
                <td style={s.td}>{u.is_admin ? '✓' : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
