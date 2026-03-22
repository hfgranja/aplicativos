/**
 * AI Evals Page — shows results from the ai_evals engine across all executions.
 * Filters findings to those from the ai_evals engine and groups by category.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listFindings } from '../api/findings'
import StatusBadge from '../components/shared/StatusBadge'

const CATEGORIES = [
  { id: 'ai_evals.prompt_injection', label: 'Prompt Injection', icon: '⚡', color: '#ef4444' },
  { id: 'ai_evals.hallucination', label: 'Hallucination', icon: '🌀', color: '#f97316' },
  { id: 'ai_evals.bias_toxicity', label: 'Bias / Toxicity', icon: '⚠', color: '#eab308' },
  { id: 'ai_evals.rag_quality', label: 'RAG Quality', icon: '⧉', color: '#06b6d4' },
]

const s = {
  h1: { fontSize: 22, fontWeight: 700, color: '#e2e8f0', marginBottom: 4 },
  sub: { fontSize: 13, color: '#64748b', marginBottom: 24 },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 24 },
  statCard: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 16 },
  statIcon: { fontSize: 20, marginBottom: 8 },
  statValue: { fontSize: 28, fontWeight: 700, color: '#e2e8f0', marginBottom: 2 },
  statLabel: { fontSize: 11, color: '#64748b' },
  section: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 8, padding: 20, marginBottom: 20 },
  sectionTitle: { fontSize: 14, fontWeight: 600, color: '#94a3b8', marginBottom: 16 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', fontSize: 11, color: '#64748b', padding: '8px 12px', borderBottom: '1px solid #1e2535', textTransform: 'uppercase' },
  td: { padding: '10px 12px', fontSize: 13, color: '#cbd5e1', borderBottom: '1px solid #1a2035' },
  link: { color: '#60a5fa', textDecoration: 'none' },
  empty: { color: '#475569', fontSize: 13, padding: '16px 0' },
  badge: { display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 },
}

function categoryLabel(cat) {
  return CATEGORIES.find(c => c.id === cat)?.label || cat
}

function categoryColor(cat) {
  return CATEGORIES.find(c => c.id === cat)?.color || '#94a3b8'
}

export default function AIEvalsPage() {
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterCat, setFilterCat] = useState('')

  useEffect(() => {
    listFindings({ engine: 'ai_evals' })
      .then(data => { setFindings(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const countBy = (cat) => findings.filter(f => f.category === cat).length
  const criticalCount = findings.filter(f => f.severity === 'CRITICAL').length
  const highCount = findings.filter(f => f.severity === 'HIGH').length

  const displayed = filterCat ? findings.filter(f => f.category === filterCat) : findings

  return (
    <div>
      <h1 style={s.h1}>AI Evals</h1>
      <p style={s.sub}>
        Findings from LLM/AI agent validation — hallucination, prompt injection, RAG quality, and bias detection.
      </p>

      <div style={s.statsGrid}>
        {CATEGORIES.map(cat => (
          <div
            key={cat.id}
            style={{ ...s.statCard, borderColor: filterCat === cat.id ? cat.color : '#1e2535', cursor: 'pointer' }}
            onClick={() => setFilterCat(filterCat === cat.id ? '' : cat.id)}
          >
            <div style={s.statIcon}>{cat.icon}</div>
            <div style={{ ...s.statValue, color: cat.color }}>{countBy(cat.id)}</div>
            <div style={s.statLabel}>{cat.label}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
        <div style={{ ...s.statCard, flex: 1 }}>
          <div style={{ fontSize: 12, color: '#ef4444', fontWeight: 600 }}>CRITICAL</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#ef4444' }}>{criticalCount}</div>
        </div>
        <div style={{ ...s.statCard, flex: 1 }}>
          <div style={{ fontSize: 12, color: '#f97316', fontWeight: 600 }}>HIGH</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#f97316' }}>{highCount}</div>
        </div>
        <div style={{ ...s.statCard, flex: 2 }}>
          <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>TOTAL AI EVAL FINDINGS</div>
          <div style={{ fontSize: 24, fontWeight: 700, color: '#e2e8f0' }}>{findings.length}</div>
        </div>
      </div>

      <div style={s.section}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={s.sectionTitle}>
            {filterCat ? `${categoryLabel(filterCat)} Findings` : 'All AI Eval Findings'}
            {filterCat && (
              <button
                onClick={() => setFilterCat('')}
                style={{ marginLeft: 12, fontSize: 11, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Clear filter ×
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div style={s.empty}>Loading...</div>
        ) : displayed.length === 0 ? (
          <div style={s.empty}>
            No AI eval findings yet. Trigger an execution with <code>ai_evals</code> in the engine list
            and ensure the application has an AI framework in its stack info.
          </div>
        ) : (
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Severity</th>
                <th style={s.th}>Category</th>
                <th style={s.th}>Title</th>
                <th style={s.th}>Neural Score</th>
                <th style={s.th}>Execution</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map(f => (
                <tr key={f.id}>
                  <td style={s.td}><StatusBadge status={f.severity} small /></td>
                  <td style={s.td}>
                    <span style={{
                      ...s.badge,
                      background: categoryColor(f.category) + '22',
                      color: categoryColor(f.category),
                    }}>
                      {categoryLabel(f.category)}
                    </span>
                  </td>
                  <td style={s.td}>
                    <Link to={`/findings/${f.id}`} style={s.link}>{f.title}</Link>
                  </td>
                  <td style={s.td}>
                    {f.neural_score != null ? `${(f.neural_score * 100).toFixed(0)}%` : '—'}
                  </td>
                  <td style={s.td}>
                    <Link to={`/executions/${f.execution_id}`} style={s.link}>
                      {f.execution_id?.slice(0, 8)}…
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
