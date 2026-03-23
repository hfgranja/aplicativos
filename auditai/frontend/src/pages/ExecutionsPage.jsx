import { useState, useEffect } from 'react'
import { Link, useSearchParams, useNavigate } from 'react-router-dom'
import { listExecutions, createExecution } from '../api/executions'
import { listApplications } from '../api/applications'
import StatusBadge from '../components/shared/StatusBadge'

const s = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
  table: { width: '100%', borderCollapse: 'collapse', background: '#161b27', borderRadius: 8 },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '12px 16px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '12px 16px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
  link: { color: '#60a5fa', textDecoration: 'none' },
  modal: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 },
  modalCard: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 10, padding: 32, width: 420 },
  label: { display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 },
  select: { width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '8px 12px', color: '#e2e8f0', fontSize: 13, marginBottom: 14 },
  actions: { display: 'flex', gap: 10, justifyContent: 'flex-end' },
  cancel: { background: 'none', border: '1px solid #334155', color: '#94a3b8', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
}

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState([])
  const [apps, setApps] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ application_id: '', mode: 'FULL' })
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const [params] = useSearchParams()

  useEffect(() => {
    listExecutions().then(setExecutions)
    listApplications().then(a => { setApps(a); if (params.get('app')) setForm(f => ({ ...f, application_id: params.get('app') })) })
    if (params.get('app')) setShowForm(true)
  }, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const ex = await createExecution(form)
      setExecutions(prev => [ex, ...prev])
      setShowForm(false)
      navigate(`/executions/${ex.id}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={s.header}>
        <h1 style={s.h1}>Executions</h1>
        <button style={s.btn} onClick={() => setShowForm(true)}>+ Run Tests</button>
      </div>

      <table style={s.table}>
        <thead>
          <tr>
            <th style={s.th}>ID</th>
            <th style={s.th}>Application</th>
            <th style={s.th}>Mode</th>
            <th style={s.th}>Status</th>
            <th style={s.th}>Started</th>
            <th style={s.th}>Findings</th>
          </tr>
        </thead>
        <tbody>
          {executions.map(ex => (
            <tr key={ex.id}>
              <td style={s.td}><Link to={`/executions/${ex.id}`} style={s.link}>{ex.id.slice(0, 12)}...</Link></td>
              <td style={s.td}>{ex.application_id?.slice(0, 12)}</td>
              <td style={s.td}>{ex.mode}</td>
              <td style={s.td}><StatusBadge status={ex.status} small /></td>
              <td style={s.td}>{ex.started_at ? new Date(ex.started_at).toLocaleString() : '—'}</td>
              <td style={s.td}>{ex.summary?.total_findings ?? '—'}</td>
            </tr>
          ))}
          {executions.length === 0 && (
            <tr><td style={{ ...s.td, color: '#475569', textAlign: 'center' }} colSpan={6}>No executions</td></tr>
          )}
        </tbody>
      </table>

      {showForm && (
        <div style={s.modal}>
          <div style={s.modalCard}>
            <h2 style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', marginBottom: 20 }}>New Execution</h2>
            <form onSubmit={handleCreate}>
              <label style={s.label}>Application *</label>
              <select style={s.select} value={form.application_id} onChange={e => setForm(f => ({ ...f, application_id: e.target.value }))} required>
                <option value="">Select application...</option>
                {apps.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
              </select>
              <label style={s.label}>Mode</label>
              <select style={s.select} value={form.mode} onChange={e => setForm(f => ({ ...f, mode: e.target.value }))}>
                <option value="FAST">FAST — Quick PR check (SAST + Contract)</option>
                <option value="FULL">FULL — All engines</option>
                <option value="REGULATORY">REGULATORY — All engines + Chaos</option>
              </select>
              <div style={s.actions}>
                <button type="button" style={s.cancel} onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" style={s.btn} disabled={loading}>{loading ? 'Starting...' : 'Start Execution'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
