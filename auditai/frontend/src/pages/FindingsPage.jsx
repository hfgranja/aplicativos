import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFindings } from '../api/findings'
import StatusBadge from '../components/shared/StatusBadge'

const s = {
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0' },
  filters: { display: 'flex', gap: 10, marginBottom: 20 },
  select: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 6, padding: '6px 12px', color: '#94a3b8', fontSize: 13 },
  table: { width: '100%', borderCollapse: 'collapse', background: '#161b27', borderRadius: 8, overflow: 'hidden' },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '12px 16px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '12px 16px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
  link: { color: '#60a5fa', textDecoration: 'none' },
}

export default function FindingsPage() {
  const [findings, setFindings] = useState([])
  const [severity, setSeverity] = useState('')
  const [engine, setEngine] = useState('')

  useEffect(() => {
    const params = {}
    if (severity) params.severity = severity
    if (engine) params.engine = engine
    listFindings(params).then(setFindings)
  }, [severity, engine])

  const engines = [...new Set(findings.map(f => f.engine))]

  return (
    <div>
      <div style={s.header}>
        <h1 style={s.h1}>Findings ({findings.length})</h1>
      </div>

      <div style={s.filters}>
        <select style={s.select} value={severity} onChange={e => setSeverity(e.target.value)}>
          <option value="">All severities</option>
          {['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'].map(v => <option key={v}>{v}</option>)}
        </select>
        <select style={s.select} value={engine} onChange={e => setEngine(e.target.value)}>
          <option value="">All engines</option>
          {engines.map(e => <option key={e}>{e}</option>)}
        </select>
      </div>

      <table style={s.table}>
        <thead>
          <tr>
            <th style={s.th}>Severity</th>
            <th style={s.th}>Engine</th>
            <th style={s.th}>Title</th>
            <th style={s.th}>File</th>
            <th style={s.th}>Neural</th>
            <th style={s.th}>Status</th>
          </tr>
        </thead>
        <tbody>
          {findings.map(f => (
            <tr key={f.id}>
              <td style={s.td}><StatusBadge status={f.severity} small /></td>
              <td style={s.td}>{f.engine}</td>
              <td style={s.td}>
                <Link to={`/findings/${f.id}`} style={s.link}>{f.title}</Link>
              </td>
              <td style={s.td}>{f.file_path ? `${f.file_path}:${f.line_number}` : '—'}</td>
              <td style={s.td}>{f.neural_score != null ? `${(f.neural_score * 100).toFixed(0)}%` : '—'}</td>
              <td style={s.td}>
                {f.is_resolved ? <StatusBadge status="COMPLETED" small /> :
                 f.is_accepted_risk ? <span style={{ color: '#fbbf24', fontSize: 11 }}>Accepted</span> :
                 <span style={{ color: '#64748b', fontSize: 11 }}>Open</span>}
              </td>
            </tr>
          ))}
          {findings.length === 0 && (
            <tr><td style={{ ...s.td, color: '#475569', textAlign: 'center' }} colSpan={6}>No findings</td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
