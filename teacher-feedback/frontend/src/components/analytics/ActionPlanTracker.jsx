import { useState, useEffect } from 'react'
import { C } from '../../colors'
import { Card, Button, Spinner, Badge } from '../shared'
import { api } from '../../api/client'

const STATUS_COLORS = {
  pendente: '#FFB020',
  realizado: '#00C896',
  parcial: '#45B7D1',
}

const STATUS_LABELS = {
  pendente: 'Pendente',
  realizado: 'Realizado',
  parcial: 'Parcial',
}

function ResultModal({ action, onSave, onClose }) {
  const [status, setStatus] = useState(action.status)
  const [notes, setNotes] = useState(action.result_notes || '')
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await onSave(action.id, { status, result_notes: notes })
      onClose()
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: 28, width: 480, maxWidth: '95vw' }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Registrar Resultado</h3>
        <p style={{ fontSize: 12, color: C.textMuted, marginBottom: 20 }}>{action.action_text}</p>

        <div style={{ marginBottom: 16 }}>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 8 }}>Status:</p>
          <div style={{ display: 'flex', gap: 8 }}>
            {['realizado', 'parcial', 'pendente'].map(s => (
              <button
                key={s}
                type="button"
                onClick={() => setStatus(s)}
                style={{
                  padding: '7px 16px', borderRadius: 8, fontSize: 12, cursor: 'pointer',
                  fontFamily: 'JetBrains Mono', fontWeight: status === s ? 700 : 400,
                  background: status === s ? STATUS_COLORS[s] + '33' : C.surface2,
                  border: `1px solid ${status === s ? STATUS_COLORS[s] : C.border}`,
                  color: status === s ? STATUS_COLORS[s] : C.textMuted,
                }}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 8 }}>Relato do resultado:</p>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            placeholder="Descreva como ficou após a execução do combinado..."
            rows={3}
            style={{
              width: '100%', background: C.surface2, border: `1px solid ${C.border}`,
              borderRadius: 8, padding: '10px 12px', color: C.text, fontSize: 13,
              fontFamily: 'JetBrains Mono', resize: 'vertical', boxSizing: 'border-box',
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <Button onClick={onClose} variant="ghost">Cancelar</Button>
          <Button onClick={handleSave} variant="success" disabled={saving}>
            {saving ? 'Salvando...' : 'Salvar'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export function ActionPlanTracker({ teacherId }) {
  const [results, setResults] = useState([])
  const [comparison, setComparison] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedAction, setSelectedAction] = useState(null)

  const load = async () => {
    try {
      const [r, c] = await Promise.all([
        api.getTeacherActionResults(teacherId),
        api.getPeriodComparison(teacherId),
      ])
      setResults(r)
      setComparison(c)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [teacherId])

  const handleUpdate = async (id, data) => {
    await api.updateActionResult(id, data)
    await load()
  }

  if (loading) return <Spinner />

  if (results.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '40px 0', color: C.textMuted, fontSize: 13 }}>
        Nenhum combinado registrado ainda. Os combinados são criados ao salvar observações com ações combinadas.
      </div>
    )
  }

  const realized = results.filter(r => r.status === 'realizado').length
  const total = results.length

  return (
    <div>
      {/* Summary */}
      {comparison && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
          <div style={{ background: C.surface2, borderRadius: 10, padding: 16, textAlign: 'center' }}>
            <div style={{ color: C.accent2, fontSize: 26, fontWeight: 700 }}>{comparison.completion_rate ?? 0}%</div>
            <div style={{ color: C.textMuted, fontSize: 12, marginTop: 4 }}>Taxa de conclusão</div>
          </div>
          <div style={{ background: C.surface2, borderRadius: 10, padding: 16, textAlign: 'center' }}>
            <div style={{ color: comparison.avg_delta > 0 ? C.success : C.textMuted, fontSize: 26, fontWeight: 700 }}>
              {comparison.avg_delta > 0 ? '+' : ''}{comparison.avg_delta}
            </div>
            <div style={{ color: C.textMuted, fontSize: 12, marginTop: 4 }}>Delta médio (pts)</div>
          </div>
          <div style={{ background: C.surface2, borderRadius: 10, padding: 16, textAlign: 'center' }}>
            <div style={{ color: C.text, fontSize: 26, fontWeight: 700 }}>{realized}/{total}</div>
            <div style={{ color: C.textMuted, fontSize: 12, marginTop: 4 }}>Realizados</div>
          </div>
        </div>
      )}

      {/* Action list */}
      {results.map(r => (
        <div key={r.id} style={{
          background: C.surface2, borderRadius: 10, padding: 16, marginBottom: 10,
          border: `1px solid ${STATUS_COLORS[r.status]}33`,
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
            <div style={{ flex: 1 }}>
              <p style={{ fontSize: 13, color: C.text, marginBottom: 6 }}>{r.action_text}</p>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
                <Badge color={STATUS_COLORS[r.status]}>{STATUS_LABELS[r.status]}</Badge>
                {r.responsible && (
                  <span style={{ color: C.textMuted, fontSize: 11 }}>→ {r.responsible}</span>
                )}
                {r.deadline && (
                  <span style={{ color: C.textMuted, fontSize: 11 }}>
                    📅 {new Date(r.deadline).toLocaleDateString('pt-BR')}
                  </span>
                )}
              </div>
              {r.score_before != null && r.score_after != null && (
                <div style={{ marginTop: 8, fontSize: 12, color: C.textMuted }}>
                  Score: {r.score_before} →{' '}
                  <span style={{ color: r.delta_score > 0 ? C.success : r.delta_score < 0 ? C.danger : C.textMuted, fontWeight: 700 }}>
                    {r.score_after}
                  </span>
                  {r.delta_score != null && (
                    <span style={{ color: r.delta_score > 0 ? C.success : C.danger, marginLeft: 4 }}>
                      ({r.delta_score > 0 ? '+' : ''}{r.delta_score}pts)
                    </span>
                  )}
                </div>
              )}
              {r.result_notes && (
                <p style={{ fontSize: 12, color: C.textMuted, marginTop: 6, fontStyle: 'italic' }}>
                  "{r.result_notes}"
                </p>
              )}
            </div>
            {r.status === 'pendente' && (
              <Button
                onClick={() => setSelectedAction(r)}
                variant="secondary"
                style={{ fontSize: 11, padding: '6px 12px', whiteSpace: 'nowrap' }}
              >
                Registrar resultado
              </Button>
            )}
          </div>
        </div>
      ))}

      {selectedAction && (
        <ResultModal
          action={selectedAction}
          onSave={handleUpdate}
          onClose={() => setSelectedAction(null)}
        />
      )}
    </div>
  )
}
