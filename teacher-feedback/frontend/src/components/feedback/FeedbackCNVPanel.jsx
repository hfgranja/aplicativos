import { useState } from 'react'
import { C } from '../../colors'
import { Card, Button, ErrorBanner, Spinner } from '../shared'
import { api } from '../../api/client'

export function FeedbackCNVPanel({ obsId, cnvRaw, feedbackRaw, onRefresh }) {
  const [questions, setQuestions] = useState([''])
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  // Auto-suggest questions from feedback
  const suggestQuestions = () => {
    let fb = null
    try { fb = JSON.parse(feedbackRaw) } catch (_) {}
    if (!fb) return
    const suggested = []
    fb.areas_desenvolvimento?.forEach(a => {
      suggested.push(`Como abordar ${a.area} com o professor?`)
    })
    if (fb.padroes_identificados?.length > 0) {
      suggested.push(`Como tratar o padrão recorrente: "${fb.padroes_identificados[0]}"?`)
    }
    if (suggested.length > 0) {
      setQuestions(suggested)
    }
  }

  const handleGenerate = async () => {
    const qs = questions.filter(Boolean)
    if (!qs.length) return
    setGenerating(true)
    setError(null)
    try {
      await api.generateCNV(obsId, qs)
      onRefresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  let cnv = null
  try { cnv = cnvRaw ? JSON.parse(cnvRaw) : null } catch (_) {}

  return (
    <Card style={{ marginTop: 24 }}>
      <h3 style={{ color: C.accent2, fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
        Roteiro de Devolutiva (CNV)
      </h3>
      <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 20, lineHeight: 1.6 }}>
        A Comunicação Não-Violenta estrutura o feedback em: <strong style={{ color: C.text }}>Observação → Sentimento → Necessidade → Pedido</strong>
      </p>

      {/* Questions input */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <p style={{ color: C.textMuted, fontSize: 12 }}>Perguntas que o PEC precisa responder na devolutiva:</p>
          {feedbackRaw && (
            <button
              type="button"
              onClick={suggestQuestions}
              style={{ background: 'none', border: 'none', color: C.accent2, cursor: 'pointer', fontSize: 12 }}
            >
              ✦ Sugerir com base no feedback
            </button>
          )}
        </div>
        {questions.map((q, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              value={q}
              onChange={e => {
                const qs = [...questions]
                qs[i] = e.target.value
                setQuestions(qs)
              }}
              placeholder={`Pergunta ${i + 1}: Como abordar...?`}
              style={{
                flex: 1, background: C.surface2, border: `1px solid ${C.border}`, borderRadius: 8,
                padding: '9px 14px', color: C.text, fontFamily: 'JetBrains Mono', fontSize: 12,
              }}
            />
            {questions.length > 1 && (
              <button
                type="button"
                onClick={() => setQuestions(questions.filter((_, j) => j !== i))}
                style={{ background: 'none', border: 'none', color: C.danger, cursor: 'pointer', fontSize: 16 }}
              >
                ×
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={() => setQuestions([...questions, ''])}
          style={{ background: 'none', border: 'none', color: C.accent, cursor: 'pointer', fontSize: 12, fontFamily: 'JetBrains Mono' }}
        >
          + Adicionar pergunta
        </button>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <Button onClick={handleGenerate} disabled={generating || !questions.filter(Boolean).length}>
          {generating ? 'Gerando roteiro...' : cnv ? '↻ Regenerar Roteiro CNV' : '✦ Gerar Roteiro CNV'}
        </Button>
      </div>

      {generating && <Spinner />}
      <ErrorBanner message={error} />

      {cnv && (
        <div>
          {/* Opening */}
          {cnv.opening_script && (
            <div style={{ background: C.accent2 + '11', borderRadius: 8, padding: 14, marginBottom: 20 }}>
              <p style={{ color: C.accent2, fontWeight: 700, fontSize: 11, marginBottom: 6 }}>ABERTURA DA CONVERSA</p>
              <p style={{ color: C.text, fontSize: 13, fontStyle: 'italic', lineHeight: 1.6 }}>"{cnv.opening_script}"</p>
            </div>
          )}

          {/* CNV script blocks */}
          {cnv.cnv_script?.map((block, i) => (
            <div key={i} style={{ background: C.surface2, borderRadius: 10, padding: 18, marginBottom: 16, border: `1px solid ${C.border}` }}>
              <p style={{ color: C.accent, fontWeight: 700, fontSize: 13, marginBottom: 14 }}>
                📌 {block.pergunta}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 10 }}>
                {[
                  { label: 'OBSERVAÇÃO', text: block.observacao, color: '#45B7D1' },
                  { label: 'SENTIMENTO', text: block.sentimento, color: '#DDA0DD' },
                  { label: 'NECESSIDADE', text: block.necessidade, color: C.warning },
                  { label: 'PEDIDO', text: block.pedido, color: C.success },
                ].map(({ label, text, color }) => (
                  <div key={label} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                    <span style={{
                      background: color + '22', color, borderRadius: 4, padding: '2px 8px',
                      fontSize: 10, fontWeight: 700, whiteSpace: 'nowrap', minWidth: 90, textAlign: 'center',
                    }}>
                      {label}
                    </span>
                    <p style={{ color: C.text, fontSize: 13, lineHeight: 1.6, margin: 0 }}>{text}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Closing */}
          {cnv.closing_script && (
            <div style={{ background: C.success + '11', borderRadius: 8, padding: 14 }}>
              <p style={{ color: C.success, fontWeight: 700, fontSize: 11, marginBottom: 6 }}>ENCERRAMENTO DA CONVERSA</p>
              <p style={{ color: C.text, fontSize: 13, fontStyle: 'italic', lineHeight: 1.6 }}>"{cnv.closing_script}"</p>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
