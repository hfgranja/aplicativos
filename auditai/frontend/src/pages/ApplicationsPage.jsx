import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listApplications, createApplication } from '../api/applications'
import StatusBadge from '../components/shared/StatusBadge'

const s = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
  card: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  name: { fontSize: 15, fontWeight: 600, color: '#60a5fa', textDecoration: 'none' },
  meta: { fontSize: 12, color: '#64748b', marginTop: 4 },
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modalCard: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 10, padding: 32, width: 440 },
  label: { display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 },
  input: { width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 13, marginBottom: 14 },
  select: { width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 13, marginBottom: 14 },
  actions: { display: 'flex', gap: 10, justifyContent: 'flex-end' },
  cancel: { background: 'none', border: '1px solid #334155', color: '#94a3b8', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
}

export default function ApplicationsPage() {
  const [apps, setApps] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', criticality: 'MEDIUM', domain: '', squad: '', has_ai_code: false })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  useEffect(() => { listApplications().then(setApps) }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const app = await createApplication(form)
      setApps(prev => [app, ...prev])
      setShowForm(false)
      setForm({ name: '', criticality: 'MEDIUM', domain: '', squad: '', has_ai_code: false })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={s.header}>
        <h1 style={s.h1}>Applications</h1>
        <button style={s.btn} onClick={() => setShowForm(true)}>+ New Application</button>
      </div>

      {apps.length === 0 && (
        <div style={{ color: '#475569', textAlign: 'center', padding: 60 }}>
          No applications yet. Add your first application to start testing.
        </div>
      )}

      {apps.map(app => (
        <div style={s.card} key={app.id}>
          <div>
            <Link to={`/applications/${app.id}`} style={s.name}>{app.name}</Link>
            <div style={s.meta}>{app.domain || 'No domain'} · {app.squad || 'No squad'} · {app.has_ai_code ? 'AI code' : 'Human code'}</div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <StatusBadge status={app.criticality} small />
            <button style={{ ...s.btn, background: '#0f1117', border: '1px solid #1e2535', color: '#94a3b8' }}
              onClick={() => navigate(`/executions/new?app=${app.id}`)}>
              Run Tests
            </button>
          </div>
        </div>
      ))}

      {showForm && (
        <div style={s.modal}>
          <div style={s.modalCard}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', marginBottom: 20 }}>New Application</h2>
            <form onSubmit={handleCreate}>
              <label style={s.label}>Name *</label>
              <input style={s.input} value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} required />
              <label style={s.label}>Criticality</label>
              <select style={s.select} value={form.criticality} onChange={e => setForm(f => ({ ...f, criticality: e.target.value }))}>
                {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(v => <option key={v}>{v}</option>)}
              </select>
              <label style={s.label}>Domain</label>
              <input style={s.input} value={form.domain} onChange={e => setForm(f => ({ ...f, domain: e.target.value }))} placeholder="e.g. payments, auth, catalog" />
              <label style={s.label}>Squad</label>
              <input style={s.input} value={form.squad} onChange={e => setForm(f => ({ ...f, squad: e.target.value }))} />
              <label style={{ ...s.label, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                <input type="checkbox" checked={form.has_ai_code} onChange={e => setForm(f => ({ ...f, has_ai_code: e.target.checked }))} />
                Contains AI-generated code
              </label>
              <div style={{ ...s.actions, marginTop: 20 }}>
                <button type="button" style={s.cancel} onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" style={s.btn} disabled={loading}>{loading ? 'Creating...' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
