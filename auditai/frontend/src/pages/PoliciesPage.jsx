import { useState, useEffect } from 'react'
import client from '../api/client'
import StatusBadge from '../components/shared/StatusBadge'

const s = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  card: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 12 },
  name: { fontSize: 15, fontWeight: 600, color: '#e2e8f0', marginBottom: 4 },
  meta: { fontSize: 12, color: '#64748b' },
  rules: { background: '#0f1117', borderRadius: 6, padding: 12, fontSize: 12, color: '#94a3b8', marginTop: 10, fontFamily: 'monospace' },
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState([])
  useEffect(() => { client.get('/policies').then(r => setPolicies(r.data)) }, [])
  return (
    <div>
      <div style={s.header}><h1 style={s.h1}>Policies</h1></div>
      {policies.map(p => (
        <div style={s.card} key={p.id}>
          <div style={s.name}>{p.name}</div>
          <div style={s.meta}>{p.policy_type} · v{p.version}</div>
          <pre style={s.rules}>{JSON.stringify(p.rules, null, 2)}</pre>
        </div>
      ))}
      {policies.length === 0 && (
        <div style={{ color: '#475569', textAlign: 'center', padding: 60 }}>No policies configured yet.</div>
      )}
    </div>
  )
}
