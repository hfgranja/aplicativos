import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getReleaseDecision, getReport } from '../api/findings'
import StatusBadge from '../components/shared/StatusBadge'
import ScoreGauge from '../components/shared/ScoreGauge'
import PyramidCoverageChart from '../components/charts/PyramidCoverageChart'

const s = {
  page: { maxWidth: 900 },
  decision: { display: 'flex', alignItems: 'center', gap: 20, marginBottom: 32, background: '#161b27', borderRadius: 12, padding: 28, border: '1px solid #1e2535' },
  decisionIcon: { fontSize: 48 },
  decisionText: { flex: 1 },
  decisionTitle: { fontSize: 24, fontWeight: 700 },
  decisionMeta: { fontSize: 13, color: '#64748b', marginTop: 4 },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 20 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
  exportBtn: { background: '#0f1117', border: '1px solid #1e2535', color: '#94a3b8', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13, marginLeft: 8 },
}

const DECISION_STYLE = {
  GREEN: { color: '#4ade80', icon: '✓', bg: '#052e16', border: '#166534' },
  YELLOW: { color: '#fbbf24', icon: '⚠', bg: '#422006', border: '#92400e' },
  RED: { color: '#f87171', icon: '✗', bg: '#450a0a', border: '#991b1b' },
  PENDING: { color: '#94a3b8', icon: '…', bg: '#1e2535', border: '#334155' },
}

export default function ReleasePage() {
  const { executionId } = useParams()
  const [decision, setDecision] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getReleaseDecision(executionId).then(setDecision).catch(() => {}).finally(() => setLoading(false))
  }, [executionId])

  const exportCSV = async () => {
    const res = await fetch(`/reports/${executionId}?format=csv`)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${executionId}.csv`
    a.click()
  }

  if (loading) return <div style={{ color: '#64748b' }}>Loading...</div>

  if (!decision) return (
    <div style={{ textAlign: 'center', padding: 60 }}>
      <div style={{ color: '#64748b', marginBottom: 16 }}>No release decision available for this execution.</div>
      <Link to={`/executions/${executionId}`} style={{ color: '#60a5fa' }}>View Execution</Link>
    </div>
  )

  const ds = DECISION_STYLE[decision.decision] || DECISION_STYLE.PENDING

  return (
    <div style={s.page}>
      <div style={{ ...s.decision, background: ds.bg, borderColor: ds.border }}>
        <div style={s.decisionIcon}>{ds.icon}</div>
        <div style={s.decisionText}>
          <div style={{ ...s.decisionTitle, color: ds.color }}>
            Release {decision.decision}
          </div>
          <div style={s.decisionMeta}>
            Score: {decision.score}/100 · {new Date(decision.decided_at).toLocaleString()}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <ScoreGauge score={decision.score} size={80} label="Overall" />
        </div>
      </div>

      <div style={{ marginBottom: 20 }}>
        <button style={s.btn} onClick={exportCSV}>Export CSV</button>
        <Link to={`/executions/${executionId}`} style={{ ...s.exportBtn, textDecoration: 'none', display: 'inline-block', lineHeight: '32px' }}>
          View Execution
        </Link>
      </div>

      {decision.blocking_findings?.length > 0 && (
        <div style={{ ...s.section, borderColor: '#991b1b' }}>
          <div style={{ ...s.sectionTitle, color: '#f87171' }}>Blocking Issues ({decision.blocking_findings.length})</div>
          {decision.blocking_findings.map((fid, i) => (
            <div key={i} style={{ fontSize: 13, color: '#fca5a5', padding: '4px 0' }}>
              {fid.startsWith('required_engine_missing:')
                ? `Required engine not run: ${fid.replace('required_engine_missing:', '')}`
                : <Link to={`/findings/${fid}`} style={{ color: '#f87171' }}>Finding: {fid.slice(0, 20)}...</Link>
              }
            </div>
          ))}
        </div>
      )}

      {decision.risk_acceptances?.length > 0 && (
        <div style={{ ...s.section, borderColor: '#92400e' }}>
          <div style={{ ...s.sectionTitle, color: '#fbbf24' }}>Accepted Risks ({decision.risk_acceptances.length})</div>
          {decision.risk_acceptances.map((ra, i) => (
            <div key={i} style={{ fontSize: 12, color: '#fbbf24', padding: '4px 0' }}>
              {ra.severity} — accepted by {ra.accepted_by?.slice(0, 8)}
            </div>
          ))}
        </div>
      )}

      <div style={s.section}>
        <div style={s.sectionTitle}>Testing Pyramid Coverage</div>
        <PyramidCoverageChart coverage={decision.pyramid_coverage_summary || {}} />
      </div>
    </div>
  )
}
