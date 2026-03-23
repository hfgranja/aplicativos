import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listApplications } from '../api/applications'
import { listExecutions } from '../api/executions'
import { listFindings } from '../api/findings'
import ScoreGauge from '../components/shared/ScoreGauge'
import StatusBadge from '../components/shared/StatusBadge'
import FindingsTrend from '../components/charts/FindingsTrend'

const s = {
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 24 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 },
  card: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20 },
  kpiNum: { fontSize: 32, fontWeight: 700, color: '#60a5fa' },
  kpiLabel: { fontSize: 12, color: '#64748b', marginTop: 4 },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 24 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '8px 12px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase', letterSpacing: 0.5 },
  td: { padding: '10px 12px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
  link: { color: '#60a5fa', textDecoration: 'none' },
}

export default function DashboardPage() {
  const [apps, setApps] = useState([])
  const [executions, setExecutions] = useState([])
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([listApplications(), listExecutions(), listFindings()])
      .then(([a, e, f]) => { setApps(a); setExecutions(e); setFindings(f) })
      .finally(() => setLoading(false))
  }, [])

  const criticalCount = findings.filter(f => f.severity === 'CRITICAL').length
  const highCount = findings.filter(f => f.severity === 'HIGH').length
  const activeExecutions = executions.filter(e => e.status === 'RUNNING').length

  if (loading) return <div style={{ color: '#64748b' }}>Loading dashboard...</div>

  return (
    <div>
      <h1 style={s.h1}>Dashboard</h1>

      <div style={s.grid}>
        <div style={s.card}>
          <div style={s.kpiNum}>{apps.length}</div>
          <div style={s.kpiLabel}>Applications</div>
        </div>
        <div style={s.card}>
          <div style={{ ...s.kpiNum, color: activeExecutions > 0 ? '#60a5fa' : '#4ade80' }}>{activeExecutions}</div>
          <div style={s.kpiLabel}>Running Executions</div>
        </div>
        <div style={s.card}>
          <div style={{ ...s.kpiNum, color: criticalCount > 0 ? '#f87171' : '#4ade80' }}>{criticalCount}</div>
          <div style={s.kpiLabel}>Critical Findings</div>
        </div>
        <div style={s.card}>
          <div style={{ ...s.kpiNum, color: highCount > 0 ? '#fb923c' : '#4ade80' }}>{highCount}</div>
          <div style={s.kpiLabel}>High Findings</div>
        </div>
        <div style={s.card}>
          <div style={s.kpiNum}>{executions.length}</div>
          <div style={s.kpiLabel}>Total Executions</div>
        </div>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>Findings Trend (Last 7 Days)</div>
        <FindingsTrend data={_mockTrend()} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        <div style={s.section}>
          <div style={s.sectionTitle}>Recent Executions</div>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Application</th>
                <th style={s.th}>Mode</th>
                <th style={s.th}>Status</th>
                <th style={s.th}>Started</th>
              </tr>
            </thead>
            <tbody>
              {executions.slice(0, 6).map(ex => (
                <tr key={ex.id}>
                  <td style={s.td}>
                    <Link to={`/executions/${ex.id}`} style={s.link}>
                      {ex.application_id?.slice(0, 8)}...
                    </Link>
                  </td>
                  <td style={s.td}>{ex.mode}</td>
                  <td style={s.td}><StatusBadge status={ex.status} small /></td>
                  <td style={s.td}>{ex.started_at ? new Date(ex.started_at).toLocaleDateString() : '—'}</td>
                </tr>
              ))}
              {executions.length === 0 && (
                <tr><td style={{ ...s.td, color: '#475569' }} colSpan={4}>No executions yet</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={s.section}>
          <div style={s.sectionTitle}>Applications Overview</div>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Name</th>
                <th style={s.th}>Criticality</th>
                <th style={s.th}>Domain</th>
              </tr>
            </thead>
            <tbody>
              {apps.slice(0, 6).map(app => (
                <tr key={app.id}>
                  <td style={s.td}>
                    <Link to={`/applications/${app.id}`} style={s.link}>{app.name}</Link>
                  </td>
                  <td style={s.td}><StatusBadge status={app.criticality} small /></td>
                  <td style={s.td}>{app.domain || '—'}</td>
                </tr>
              ))}
              {apps.length === 0 && (
                <tr><td style={{ ...s.td, color: '#475569' }} colSpan={3}>No applications yet</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function _mockTrend() {
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
  return days.map(d => ({ date: d, critical: Math.floor(Math.random() * 3), high: Math.floor(Math.random() * 8), medium: Math.floor(Math.random() * 15) }))
}
