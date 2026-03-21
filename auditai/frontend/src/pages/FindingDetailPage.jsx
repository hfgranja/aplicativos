import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getFinding, acceptRisk, resolveFinding } from '../api/findings'
import StatusBadge from '../components/shared/StatusBadge'
import FixProposalPanel from '../components/fix/FixProposalPanel'

const s = {
  h1: { fontSize: 20, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 },
  meta: { fontSize: 12, color: '#64748b', marginBottom: 24 },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 20 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 12 },
  row: { display: 'flex', gap: 24, marginBottom: 8 },
  label: { fontSize: 11, color: '#64748b', width: 120 },
  value: { fontSize: 13, color: '#cbd5e1', flex: 1 },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 12 },
  dangerBtn: { background: '#7f1d1d', color: '#fca5a5', border: 'none', borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 12 },
  successBtn: { background: '#052e16', color: '#4ade80', border: '1px solid #166534', borderRadius: 6, padding: '7px 14px', cursor: 'pointer', fontSize: 12 },
  pre: { background: '#0f1117', borderRadius: 6, padding: 12, fontSize: 12, color: '#94a3b8', overflow: 'auto', maxHeight: 300 },
}

export default function FindingDetailPage() {
  const { id } = useParams()
  const [finding, setFinding] = useState(null)
  const [justification, setJustification] = useState('')
  const [showAccept, setShowAccept] = useState(false)

  useEffect(() => { getFinding(id).then(setFinding) }, [id])

  const handleResolve = async () => {
    await resolveFinding(id)
    setFinding(f => ({ ...f, is_resolved: true }))
  }

  const handleAcceptRisk = async () => {
    await acceptRisk(id, justification)
    setFinding(f => ({ ...f, is_accepted_risk: true }))
    setShowAccept(false)
  }

  if (!finding) return <div style={{ color: '#64748b' }}>Loading...</div>

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 4 }}>
        <h1 style={s.h1}>{finding.title}</h1>
        <StatusBadge status={finding.severity} />
        {finding.is_resolved && <StatusBadge status="COMPLETED" small />}
        {finding.is_accepted_risk && <span style={{ fontSize: 11, color: '#fbbf24' }}>Risk Accepted</span>}
      </div>
      <div style={s.meta}>
        Engine: {finding.engine} · Level {finding.pyramid_level} · {new Date(finding.created_at).toLocaleString()}
        · <Link to={`/executions/${finding.execution_id}`} style={{ color: '#60a5fa' }}>View Execution</Link>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 24 }}>
        {!finding.is_resolved && (
          <button style={s.successBtn} onClick={handleResolve}>Mark Resolved</button>
        )}
        {!finding.is_accepted_risk && !finding.is_resolved && (
          <button style={s.dangerBtn} onClick={() => setShowAccept(!showAccept)}>Accept Risk</button>
        )}
      </div>

      {showAccept && (
        <div style={{ ...s.section, borderColor: '#92400e' }}>
          <div style={s.sectionTitle}>Risk Acceptance Justification</div>
          <textarea
            style={{ ...s.pre, width: '100%', resize: 'vertical', minHeight: 80, marginBottom: 12 }}
            placeholder="Provide justification for accepting this risk..."
            value={justification}
            onChange={e => setJustification(e.target.value)}
          />
          <button style={s.dangerBtn} onClick={handleAcceptRisk} disabled={!justification}>Confirm Accept Risk</button>
        </div>
      )}

      <div style={s.section}>
        <div style={s.sectionTitle}>Details</div>
        <div style={s.row}><span style={s.label}>Category</span><span style={s.value}>{finding.category}</span></div>
        <div style={s.row}><span style={s.label}>CWE</span><span style={s.value}>{finding.cwe_id || '—'}</span></div>
        <div style={s.row}><span style={s.label}>File</span><span style={s.value}>{finding.file_path || '—'}</span></div>
        <div style={s.row}><span style={s.label}>Line</span><span style={s.value}>{finding.line_number || '—'}</span></div>
        <div style={s.row}><span style={s.label}>Neural Score</span>
          <span style={s.value}>{finding.neural_score != null ? `${(finding.neural_score * 100).toFixed(0)}% confidence` : '—'}</span>
        </div>
        {finding.description && (
          <div style={{ marginTop: 12 }}>
            <div style={{ ...s.label, marginBottom: 6 }}>Description</div>
            <div style={{ fontSize: 13, color: '#cbd5e1' }}>{finding.description}</div>
          </div>
        )}
      </div>

      {finding.evidence && Object.keys(finding.evidence).length > 0 && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Evidence</div>
          <pre style={s.pre}>{JSON.stringify(finding.evidence, null, 2)}</pre>
        </div>
      )}

      {finding.seed && (
        <div style={s.section}>
          <div style={s.sectionTitle}>Seed / Reproducer</div>
          <pre style={s.pre}>{finding.seed}</pre>
        </div>
      )}

      <FixProposalPanel findingId={id} fixProposal={finding.fix_proposal} />
    </div>
  )
}
