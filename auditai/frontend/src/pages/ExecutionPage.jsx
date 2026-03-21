import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getExecution, getTestRuns } from '../api/executions'
import { listFindings } from '../api/findings'
import StatusBadge from '../components/shared/StatusBadge'
import ScoreGauge from '../components/shared/ScoreGauge'
import PyramidCoverageChart from '../components/charts/PyramidCoverageChart'

const s = {
  h1: { fontSize: 20, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 },
  meta: { fontSize: 12, color: '#64748b', marginBottom: 24 },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 20 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  engineGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 12 },
  engineCard: { background: '#0f1117', border: '1px solid #1e2535', borderRadius: 8, padding: 14, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 },
  engineName: { fontSize: 12, color: '#94a3b8', textAlign: 'center' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '8px 12px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '10px 12px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
  link: { color: '#60a5fa', textDecoration: 'none' },
}

export default function ExecutionPage() {
  const { id } = useParams()
  const [execution, setExecution] = useState(null)
  const [testRuns, setTestRuns] = useState([])
  const [findings, setFindings] = useState([])

  useEffect(() => {
    if (!id) return
    getExecution(id).then(setExecution)
    getTestRuns(id).then(setTestRuns)
    listFindings({ execution_id: id }).then(setFindings)

    // Auto-refresh if running
    const interval = setInterval(async () => {
      const ex = await getExecution(id)
      setExecution(ex)
      if (ex.status !== 'RUNNING' && ex.status !== 'PENDING') clearInterval(interval)
    }, 5000)
    return () => clearInterval(interval)
  }, [id])

  if (!execution) return <div style={{ color: '#64748b' }}>Loading...</div>

  const criticalFindings = findings.filter(f => f.severity === 'CRITICAL')
  const highFindings = findings.filter(f => f.severity === 'HIGH')

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 4 }}>
        <h1 style={s.h1}>Execution</h1>
        <StatusBadge status={execution.status} />
      </div>
      <div style={s.meta}>
        ID: {execution.id} · Mode: {execution.mode} · {execution.started_at ? new Date(execution.started_at).toLocaleString() : 'Not started'}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        <div style={s.section}>
          <div style={s.sectionTitle}>Test Engines</div>
          <div style={s.engineGrid}>
            {testRuns.map(run => (
              <div style={s.engineCard} key={run.id}>
                <ScoreGauge score={run.score} size={60} />
                <div style={s.engineName}>{run.engine}</div>
                <StatusBadge status={run.status} small />
              </div>
            ))}
            {testRuns.length === 0 && execution.status === 'PENDING' && (
              <div style={{ color: '#64748b', fontSize: 13 }}>Waiting to start...</div>
            )}
          </div>
        </div>

        <div style={s.section}>
          <div style={s.sectionTitle}>Testing Pyramid Coverage</div>
          <PyramidCoverageChart coverage={execution.pyramid_coverage || {}} />
        </div>
      </div>

      <div style={s.section}>
        <div style={s.sectionTitle}>Findings ({findings.length})</div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Severity</th>
              <th style={s.th}>Engine</th>
              <th style={s.th}>Title</th>
              <th style={s.th}>File</th>
              <th style={s.th}>Neural</th>
            </tr>
          </thead>
          <tbody>
            {findings.slice(0, 20).map(f => (
              <tr key={f.id}>
                <td style={s.td}><StatusBadge status={f.severity} small /></td>
                <td style={s.td}>{f.engine}</td>
                <td style={s.td}>
                  <Link to={`/findings/${f.id}`} style={s.link}>{f.title}</Link>
                </td>
                <td style={s.td}>{f.file_path ? `${f.file_path}:${f.line_number}` : '—'}</td>
                <td style={s.td}>{f.neural_score != null ? `${(f.neural_score * 100).toFixed(0)}%` : '—'}</td>
              </tr>
            ))}
            {findings.length === 0 && (
              <tr><td style={{ ...s.td, color: '#475569' }} colSpan={5}>No findings yet</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {testRuns.some(r => r.neural_insights?.length) && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Neural Insights</div>
          {testRuns.filter(r => r.neural_insights?.length).map(run => (
            <div key={run.id} style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#60a5fa', marginBottom: 4 }}>{run.engine}</div>
              {run.neural_insights.map((insight, i) => (
                <div key={i} style={{ fontSize: 12, color: '#94a3b8', padding: '4px 0' }}>• {insight}</div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
