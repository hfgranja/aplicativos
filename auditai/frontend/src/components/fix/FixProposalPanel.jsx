import { useState } from 'react'
import { generateFix } from '../../api/findings'
import DiffViewer from './DiffViewer'

const s = {
  panel: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginTop: 16 },
  title: { fontSize: 14, fontWeight: 600, color: '#60a5fa', marginBottom: 12 },
  meta: { fontSize: 12, color: '#64748b', marginBottom: 12 },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13 },
  explanation: { background: '#1e2535', borderRadius: 6, padding: 12, fontSize: 13, color: '#cbd5e1', marginBottom: 12 },
  confidence: { display: 'inline-block', fontSize: 11, color: '#fbbf24', marginLeft: 8 },
}

export default function FixProposalPanel({ findingId, fixProposal: initial }) {
  const [proposal, setProposal] = useState(initial)
  const [loading, setLoading] = useState(false)

  const handleGenerate = async () => {
    setLoading(true)
    try {
      await generateFix(findingId)
      // Poll or reload — for demo, show loading state
      setTimeout(() => setLoading(false), 3000)
    } catch {
      setLoading(false)
    }
  }

  if (!proposal) {
    return (
      <div style={s.panel}>
        <div style={s.title}>AI Fix Proposal</div>
        <div style={{ ...s.meta, marginBottom: 16 }}>No fix proposal generated yet.</div>
        <button style={s.btn} onClick={handleGenerate} disabled={loading}>
          {loading ? 'Generating...' : 'Generate Fix with AI'}
        </button>
      </div>
    )
  }

  return (
    <div style={s.panel}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={s.title}>AI Fix Proposal</div>
        <div style={s.meta}>
          {proposal.generated_by}
          <span style={s.confidence}>
            {Math.round((proposal.confidence || 0) * 100)}% confidence
          </span>
        </div>
      </div>
      <div style={s.explanation}>{proposal.explanation}</div>
      <DiffViewer before={proposal.before_code} after={proposal.after_code} diff={proposal.diff} />
      {proposal.rationale && (
        <div style={{ ...s.meta, marginTop: 12 }}>
          <strong style={{ color: '#94a3b8' }}>Rationale:</strong> {proposal.rationale}
        </div>
      )}
    </div>
  )
}
