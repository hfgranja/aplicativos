import { useState, useEffect } from 'react'
import { C } from '../../colors'
import { api } from '../../api/client'

const GRADE_BAND_LABELS = { ef1: 'EF I', ef2: 'EF II', em: 'EM' }

export function BestPracticesPanel({ subject, grade, className }) {
  const [practices, setPractices] = useState([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!subject) { setLoading(false); return }
    api.getBestPractices(subject, grade)
      .then(r => setPractices(r.practices || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [subject, grade])

  if (loading || practices.length === 0) return null

  const visible = expanded ? practices : practices.slice(0, 3)

  return (
    <div style={{
      background: C.surface2, borderRadius: 10, padding: 16,
      border: `1px solid ${C.accent}33`,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
        <span style={{ color: C.accent, fontSize: 16 }}>✦</span>
        <h3 style={{ color: C.accent, fontSize: 12, fontWeight: 700, margin: 0 }}>
          Práticas Bem-Sucedidas no Mesmo Contexto
        </h3>
      </div>
      <p style={{ color: C.textMuted, fontSize: 11, marginBottom: 14 }}>
        {subject}{grade ? ` · ${grade}` : ''} – professores que obtiveram resultados positivos
      </p>

      {visible.map((p, i) => (
        <div key={p.id || i} style={{
          borderLeft: `2px solid ${C.accent}66`, paddingLeft: 12, marginBottom: 12,
        }}>
          <p style={{ fontSize: 12, color: C.text, lineHeight: 1.5, marginBottom: 4 }}>
            {p.content.split('\n')[0]}
          </p>
          {p.content.split('\n').slice(1).map((line, j) => line.trim() && (
            <p key={j} style={{ fontSize: 11, color: C.textMuted, lineHeight: 1.4, marginBottom: 2 }}>
              {line}
            </p>
          ))}
          <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
            {p.grade_band && (
              <span style={{ background: C.accent + '22', color: C.accent, borderRadius: 6, padding: '2px 8px', fontSize: 10 }}>
                {GRADE_BAND_LABELS[p.grade_band] || p.grade_band}
              </span>
            )}
            {p.score_at_time > 0 && (
              <span style={{ background: C.success + '22', color: C.success, borderRadius: 6, padding: '2px 8px', fontSize: 10 }}>
                Score: {p.score_at_time}
              </span>
            )}
          </div>
        </div>
      ))}

      {practices.length > 3 && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          style={{
            background: 'none', border: 'none', color: C.accent, cursor: 'pointer',
            fontSize: 12, padding: 0, fontFamily: 'JetBrains Mono',
          }}
        >
          {expanded ? '↑ Mostrar menos' : `Ver mais ${practices.length - 3} práticas`}
        </button>
      )}
    </div>
  )
}
