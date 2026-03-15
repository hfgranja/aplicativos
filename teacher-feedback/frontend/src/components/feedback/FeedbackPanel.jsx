import { useState } from 'react'
import { C, SECTION_COLORS } from '../../colors'
import { Card, Button, Badge, ScoreBar, ErrorBanner, Spinner } from '../shared'
import { api } from '../../api/client'

const SECTION_NAMES = {
  s1: 'Planejamento e Alinhamento Curricular',
  s2: 'Condução Didática da Aula',
  s3: 'Gestão da Aprendizagem dos Alunos',
  s4: 'Uso de Materiais, Recursos e Tempo',
  s5: 'Clima, Relações e Postura Profissional',
}

function FeedbackSection({ sec, data, color }) {
  return (
    <div style={{ marginBottom: 16, paddingBottom: 16, borderBottom: `1px solid ${C.border}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <span style={{ fontSize: 13, color, fontWeight: 700 }}>{SECTION_NAMES[sec]}</span>
      </div>
      {data?.analise && (
        <p style={{ color: C.text, fontSize: 13, marginBottom: 8, lineHeight: 1.6 }}>{data.analise}</p>
      )}
      {data?.recomendacao && (
        <div style={{ background: color + '11', borderLeft: `3px solid ${color}`, padding: '8px 12px', borderRadius: '0 8px 8px 0', fontSize: 12, color: C.textMuted, lineHeight: 1.5 }}>
          💡 {data.recomendacao}
        </div>
      )}
    </div>
  )
}

export function FeedbackPanel({ obsId, feedbackRaw, scores, onRefresh }) {
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    setGenerating(true)
    setError(null)
    try {
      await api.generateFeedback(obsId)
      onRefresh()
    } catch (e) {
      setError(e.message)
    } finally {
      setGenerating(false)
    }
  }

  let fb = null
  try {
    fb = feedbackRaw ? JSON.parse(feedbackRaw) : null
  } catch (_) {}

  return (
    <Card>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h3 style={{ color: C.accent2, fontSize: 16, fontWeight: 700 }}>Feedback da IA (PEC)</h3>
        <Button onClick={handleGenerate} variant={fb ? 'secondary' : 'primary'} disabled={generating}>
          {generating ? 'Gerando...' : fb ? '↻ Regenerar Feedback' : '✦ Gerar Feedback com IA'}
        </Button>
      </div>

      {generating && <Spinner />}
      <ErrorBanner message={error} />

      {!fb && !generating && (
        <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: '40px 0' }}>
          Clique em "Gerar Feedback com IA" para obter a devolutiva formativa completa usando o Ollama (llama3.2).
        </p>
      )}

      {fb && (
        <div>
          {/* Score summary */}
          {scores && (
            <div style={{ marginBottom: 24 }}>
              <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12 }}>Pontuação por seção:</p>
              {['s1', 's2', 's3', 's4', 's5'].map(sec => (
                <ScoreBar key={sec} score={scores[sec] || 0} color={SECTION_COLORS[sec]} label={SECTION_NAMES[sec]} />
              ))}
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.border}` }}>
                <ScoreBar score={scores.total || 0} color={C.accent} label="Score Total" />
              </div>
            </div>
          )}

          {/* Summary */}
          {fb.resumo_geral && (
            <div style={{ background: C.accent + '11', borderRadius: 8, padding: 16, marginBottom: 20 }}>
              <p style={{ color: C.accent, fontWeight: 700, fontSize: 12, marginBottom: 8 }}>SÍNTESE GERAL</p>
              <p style={{ color: C.text, fontSize: 13, lineHeight: 1.7 }}>{fb.resumo_geral}</p>
            </div>
          )}

          {/* Historical analysis */}
          {fb.analise_historica && (
            <div style={{ background: C.warning + '11', borderRadius: 8, padding: 16, marginBottom: 20 }}>
              <p style={{ color: C.warning, fontWeight: 700, fontSize: 12, marginBottom: 8 }}>ANÁLISE HISTÓRICA</p>
              <p style={{ color: C.text, fontSize: 13, lineHeight: 1.7 }}>{fb.analise_historica}</p>
            </div>
          )}

          {/* Strengths */}
          {fb.pontos_fortes?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: C.success, fontWeight: 700, fontSize: 12, marginBottom: 12 }}>✓ PONTOS FORTES</p>
              {fb.pontos_fortes.map((p, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8 }}>
                  <span style={{ color: C.success, fontWeight: 700 }}>✓</span>
                  <span style={{ color: C.text, fontSize: 13 }}>{p}</span>
                </div>
              ))}
            </div>
          )}

          {/* Areas of development */}
          {fb.areas_desenvolvimento?.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: C.warning, fontWeight: 700, fontSize: 12, marginBottom: 12 }}>📌 FOCOS DE DESENVOLVIMENTO</p>
              {fb.areas_desenvolvimento.map((a, i) => (
                <div key={i} style={{ background: C.surface2, borderRadius: 8, padding: 14, marginBottom: 10, borderLeft: `3px solid ${C.warning}` }}>
                  <p style={{ color: C.warning, fontWeight: 700, fontSize: 13, marginBottom: 6 }}>{a.area}</p>
                  <p style={{ color: C.text, fontSize: 12, marginBottom: 8, lineHeight: 1.5 }}>{a.descricao}</p>
                  {a.sugestao_concreta && (
                    <div style={{ background: C.surface3, borderRadius: 6, padding: '8px 12px', fontSize: 12, color: C.textMuted }}>
                      💡 {a.sugestao_concreta}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Section analysis */}
          {fb.secoes && (
            <div style={{ marginBottom: 20 }}>
              <p style={{ color: C.textMuted, fontWeight: 700, fontSize: 12, marginBottom: 16 }}>ANÁLISE POR SEÇÃO</p>
              {Object.entries(fb.secoes).map(([sec, data]) => (
                <FeedbackSection key={sec} sec={sec} data={data} color={SECTION_COLORS[sec]} />
              ))}
            </div>
          )}

          {/* BNCC alignment */}
          {fb.alinhamento_bncc && (
            <div style={{ background: C.accent2 + '11', borderRadius: 8, padding: 16, marginBottom: 20 }}>
              <p style={{ color: C.accent2, fontWeight: 700, fontSize: 12, marginBottom: 8 }}>ALINHAMENTO BNCC</p>
              <p style={{ color: C.text, fontSize: 13, lineHeight: 1.6 }}>{fb.alinhamento_bncc}</p>
            </div>
          )}

          {/* Progress & patterns */}
          {(fb.reconhecimento_avancos?.length > 0 || fb.padroes_identificados?.length > 0) && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
              {fb.reconhecimento_avancos?.length > 0 && (
                <div style={{ background: C.success + '11', borderRadius: 8, padding: 14 }}>
                  <p style={{ color: C.success, fontWeight: 700, fontSize: 12, marginBottom: 10 }}>AVANÇOS IDENTIFICADOS</p>
                  {fb.reconhecimento_avancos.map((a, i) => (
                    <p key={i} style={{ color: C.text, fontSize: 12, marginBottom: 6 }}>↑ {a}</p>
                  ))}
                </div>
              )}
              {fb.padroes_identificados?.length > 0 && (
                <div style={{ background: C.surface2, borderRadius: 8, padding: 14 }}>
                  <p style={{ color: C.textMuted, fontWeight: 700, fontSize: 12, marginBottom: 10 }}>PADRÕES RECORRENTES</p>
                  {fb.padroes_identificados.map((p, i) => (
                    <p key={i} style={{ color: C.text, fontSize: 12, marginBottom: 6 }}>→ {p}</p>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Next steps */}
          {fb.proximos_passos?.length > 0 && (
            <div style={{ background: C.accent + '11', borderRadius: 8, padding: 16 }}>
              <p style={{ color: C.accent, fontWeight: 700, fontSize: 12, marginBottom: 12 }}>PRÓXIMOS PASSOS</p>
              {fb.proximos_passos.map((p, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, marginBottom: 8 }}>
                  <span style={{ color: C.accent, fontWeight: 700 }}>{i + 1}.</span>
                  <span style={{ color: C.text, fontSize: 13 }}>{p}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  )
}
