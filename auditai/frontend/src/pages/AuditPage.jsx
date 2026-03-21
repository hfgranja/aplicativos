import { useState, useEffect } from 'react'
import client from '../api/client'

const s = {
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 24 },
  table: { width: '100%', borderCollapse: 'collapse', background: '#161b27', borderRadius: 8 },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '12px 16px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '10px 16px', fontSize: 12, color: '#94a3b8', borderBottom: '1px solid #1a2035', fontFamily: 'monospace' },
  action: { color: '#60a5fa' },
}

export default function AuditPage() {
  const [events, setEvents] = useState([])
  useEffect(() => { client.get('/audit').then(r => setEvents(r.data)) }, [])

  return (
    <div>
      <h1 style={s.h1}>Audit Log</h1>
      <table style={s.table}>
        <thead>
          <tr>
            <th style={s.th}>Timestamp</th>
            <th style={s.th}>Action</th>
            <th style={s.th}>Resource</th>
            <th style={s.th}>User</th>
            <th style={s.th}>IP</th>
          </tr>
        </thead>
        <tbody>
          {events.map(e => (
            <tr key={e.id}>
              <td style={s.td}>{new Date(e.created_at).toLocaleString()}</td>
              <td style={{ ...s.td, ...s.action }}>{e.action}</td>
              <td style={s.td}>{e.resource_type ? `${e.resource_type}:${e.resource_id?.slice(0, 12)}` : '—'}</td>
              <td style={s.td}>{e.user_id?.slice(0, 12) || '—'}</td>
              <td style={s.td}>{e.ip_address || '—'}</td>
            </tr>
          ))}
          {events.length === 0 && (
            <tr><td style={{ ...s.td, color: '#475569', textAlign: 'center' }} colSpan={5}>No audit events</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
