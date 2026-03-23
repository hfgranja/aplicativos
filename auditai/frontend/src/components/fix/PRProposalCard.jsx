import { useState } from 'react'
import { client } from '../../api/client'

const s = {
  card: { background: '#0f1a2e', border: '1px solid #1e3a5f', borderRadius: 8, padding: 20, marginTop: 16 },
  title: { fontSize: 14, fontWeight: 600, color: '#60a5fa', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 },
  desc: { fontSize: 12, color: '#64748b', marginBottom: 16 },
  btn: { background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  btnLoading: { background: '#1e3a6e', color: '#93c5fd', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'not-allowed', fontSize: 13 },
  success: { background: '#052e16', border: '1px solid #166534', borderRadius: 6, padding: 12, marginTop: 12 },
  successText: { fontSize: 13, color: '#4ade80' },
  successLink: { color: '#34d399', fontSize: 12, textDecoration: 'none', display: 'block', marginTop: 4 },
  error: { background: '#1f0505', border: '1px solid #7f1d1d', borderRadius: 6, padding: 12, marginTop: 12 },
  errorText: { fontSize: 12, color: '#fca5a5' },
}

export default function PRProposalCard({ findingId, fixProposal, evidencePr }) {
  const [loading, setLoading] = useState(false)
  const [pr, setPr] = useState(evidencePr || null)
  const [error, setError] = useState(null)

  if (!fixProposal) return null

  const handleCreatePr = async () => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await client.post(`/findings/${findingId}/create-pr`)
      setPr(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create PR. Check that GITHUB_TOKEN or GITLAB_TOKEN is configured.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.card}>
      <div style={s.title}>
        <span>⬡</span>
        Auto-Remediation
      </div>
      <div style={s.desc}>
        Open a pull request with this AI-generated fix directly in your repository.
        The patch is self-validated by the SAST engine before the PR is created.
      </div>

      {pr ? (
        <div style={s.success}>
          <div style={s.successText}>Pull request created successfully.</div>
          <a href={pr.pr_url} target="_blank" rel="noopener noreferrer" style={s.successLink}>
            View PR #{pr.pr_number} on {pr.provider} →
          </a>
        </div>
      ) : (
        <>
          <button
            style={loading ? s.btnLoading : s.btn}
            onClick={handleCreatePr}
            disabled={loading}
          >
            {loading ? 'Creating PR…' : 'Open Pull Request'}
          </button>
          {error && (
            <div style={s.error}>
              <div style={s.errorText}>{error}</div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
