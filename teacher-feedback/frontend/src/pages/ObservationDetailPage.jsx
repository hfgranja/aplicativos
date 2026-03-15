import { useState, useEffect, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { C, SECTION_COLORS, RATING_LABELS, RATING_COLORS } from '../colors'
import { Card, Badge, Spinner, ErrorBanner, ScoreBar, Button } from '../components/shared'
import { FeedbackPanel } from '../components/feedback/FeedbackPanel'
import { FeedbackCNVPanel } from '../components/feedback/FeedbackCNVPanel'
import { api } from '../api/client'

const SECTION_NAMES = {
  s1: 'Planejamento e Alinhamento Curricular',
  s2: 'Condução Didática da Aula',
  s3: 'Gestão da Aprendizagem dos Alunos',
  s4: 'Uso de Materiais, Recursos e Tempo',
  s5: 'Clima, Relações e Postura Profissional',
}

const SECTION_CRITERIA = {
  s1: ['s1_c1','s1_c2','s1_c3','s1_c4'],
  s2: ['s2_c1','s2_c2','s2_c3','s2_c4','s2_c5','s2_c6'],
  s3: ['s3_c1','s3_c2','s3_c3','s3_c4','s3_c5'],
  s4: ['s4_c1','s4_c2','s4_c3','s4_c4'],
  s5: ['s5_c1','s5_c2','s5_c3','s5_c4','s5_c5'],
}

const CRITERIA_LABELS = {
  s1_c1: 'Alinhado ao Currículo Paulista', s1_c2: 'Objetivos explícitos', s1_c3: 'Habilidades adequadas', s1_c4: 'Atividades coerentes',
  s2_c1: 'Início nos 5 min', s2_c2: 'Retomada de prévios', s2_c3: 'Explicação clara', s2_c4: 'Variedade metodológica', s2_c5: 'Perguntas de verificação', s2_c6: 'Fechamento/síntese',
  s3_c1: 'Engajamento ativo', s3_c2: 'Atende dificuldades', s3_c3: 'Diferenciação', s3_c4: 'Avaliação formativa', s3_c5: 'Feedback aos alunos',
  s4_c1: 'Materiais SEDUC', s4_c2: 'Recursos da escola', s4_c3: 'Distribuição do tempo', s4_c4: 'Registros organizados',
  s5_c1: 'Ambiente de respeito', s5_c2: 'Relação com alunos', s5_c3: 'Manejo de conflitos', s5_c4: 'Preparo prévio', s5_c5: 'Postura profissional',
}

function computeScores(obs) {
  const SCORE = { nao_observado: 0, insuficiente: 33, adequado: 67, muito_bom: 100 }
  const scores = {}
  for (const [sec, fields] of Object.entries(SECTION_CRITERIA)) {
    const vals = fields.map(f => SCORE[obs[f]] ?? 0)
    scores[sec] = Math.round(vals.reduce((a, b) => a + b, 0) / vals.length)
  }
  scores.total = Math.round(Object.values(scores).reduce((a, b) => a + b, 0) / 5)
  return scores
}

export function ObservationDetailPage() {
  const { id } = useParams()
  const [obs, setObs] = useState(null)
  const [teacher, setTeacher] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [transcribing, setTranscribing] = useState(false)

  const load = useCallback(async () => {
    try {
      const o = await api.getObservation(id)
      setObs(o)
      const t = await api.getTeacher(o.teacher_id)
      setTeacher(t)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  const handleTranscribe = async () => {
    if (!obs.media_file_id) return
    setTranscribing(true)
    try {
      await api.transcribeMedia(obs.media_file_id)
      await load()
    } catch (e) {
      alert('Erro na transcrição: ' + e.message)
    } finally {
      setTranscribing(false)
    }
  }

  if (loading) return <Spinner />
  if (error) return <ErrorBanner message={error} />
  if (!obs) return null

  const scores = computeScores(obs)
  let bnccSkills = []
  let methodologies = []
  try { bnccSkills = JSON.parse(obs.bncc_skills || '[]') } catch (_) {}
  try { methodologies = JSON.parse(obs.s2_methodologies || '[]') } catch (_) {}
  let pontosFortes = []
  let focos = []
  try { pontosFortes = JSON.parse(obs.pontos_fortes || '[]') } catch (_) {}
  try { focos = JSON.parse(obs.focos_desenvolvimento || '[]') } catch (_) {}

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Link to="/historico" style={{ color: C.textMuted, fontSize: 12, textDecoration: 'none' }}>
          ← Histórico
        </Link>
        <h1 style={{ fontSize: 20, fontWeight: 700, marginTop: 8, marginBottom: 4 }}>
          Observação de {teacher?.name}
        </h1>
        <p style={{ color: C.textMuted, fontSize: 13 }}>
          {teacher?.subject} · {teacher?.grade} · {obs.observed_at ? new Date(obs.observed_at).toLocaleDateString('pt-BR') : '–'}
          {obs.pec_name && ` · PEC: ${obs.pec_name}`}
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 24 }}>
        <div>
          {/* Section scores */}
          <Card style={{ marginBottom: 20 }}>
            <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 16 }}>SCORES POR SEÇÃO</h3>
            {['s1', 's2', 's3', 's4', 's5'].map(sec => (
              <ScoreBar key={sec} score={scores[sec]} color={SECTION_COLORS[sec]} label={SECTION_NAMES[sec]} />
            ))}
            <div style={{ borderTop: `1px solid ${C.border}`, marginTop: 12, paddingTop: 12 }}>
              <ScoreBar score={scores.total} color={C.accent} label="Score Total" />
            </div>
          </Card>

          {/* Criteria detail */}
          {Object.entries(SECTION_CRITERIA).map(([sec, fields]) => (
            <Card key={sec} style={{ marginBottom: 16 }}>
              <h3 style={{ color: SECTION_COLORS[sec], fontSize: 13, fontWeight: 700, marginBottom: 14 }}>
                {SECTION_NAMES[sec]}
              </h3>
              {fields.map(f => (
                <div key={f} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: `1px solid ${C.border}` }}>
                  <span style={{ fontSize: 12, color: C.text }}>{CRITERIA_LABELS[f]}</span>
                  {obs[f] ? (
                    <Badge color={RATING_COLORS[obs[f]]}>{RATING_LABELS[obs[f]]}</Badge>
                  ) : (
                    <span style={{ color: C.textMuted, fontSize: 11 }}>–</span>
                  )}
                </div>
              ))}
              {sec === 's2' && methodologies.length > 0 && (
                <div style={{ marginTop: 12 }}>
                  <span style={{ color: C.textMuted, fontSize: 11, marginBottom: 8, display: 'block' }}>Metodologias:</span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {methodologies.map(m => (
                      <span key={m} style={{ background: C.accent + '22', color: C.accent, borderRadius: 20, padding: '3px 10px', fontSize: 11 }}>{m}</span>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}

          {/* Feedback + CNV */}
          <FeedbackPanel obsId={id} feedbackRaw={obs.feedback_raw} scores={scores} onRefresh={load} />
          <FeedbackCNVPanel obsId={id} cnvRaw={obs.cnv_script} feedbackRaw={obs.feedback_raw} onRefresh={load} />
        </div>

        {/* Sidebar */}
        <div>
          {/* Media */}
          {obs.media_file_id && (
            <Card style={{ marginBottom: 16 }}>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 12 }}>ARQUIVO DE AULA</h3>
              <Badge color={obs.transcript ? C.success : C.warning}>
                {obs.transcript ? 'Transcrito' : 'Sem transcrição'}
              </Badge>
              {!obs.transcript && (
                <Button
                  onClick={handleTranscribe}
                  variant="secondary"
                  disabled={transcribing}
                  style={{ marginTop: 10, width: '100%', fontSize: 12 }}
                >
                  {transcribing ? 'Transcrevendo...' : '⟳ Transcrever com Whisper'}
                </Button>
              )}
              {obs.transcript && (
                <div style={{ marginTop: 10, maxHeight: 120, overflowY: 'auto', background: C.surface2, borderRadius: 6, padding: 10, fontSize: 11, color: C.textMuted, lineHeight: 1.5 }}>
                  {obs.transcript.slice(0, 400)}...
                </div>
              )}
            </Card>
          )}

          {/* Teacher reflection */}
          {(obs.teacher_feeling || obs.teacher_expectations || obs.teacher_commitment) && (
            <Card style={{ marginBottom: 16 }}>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 12 }}>PERSPECTIVA DO PROFESSOR</h3>
              {obs.teacher_feeling && (
                <div style={{ marginBottom: 10 }}>
                  <p style={{ color: C.textMuted, fontSize: 11, marginBottom: 4 }}>Como se sentiu:</p>
                  <p style={{ color: C.text, fontSize: 12, lineHeight: 1.5 }}>{obs.teacher_feeling}</p>
                </div>
              )}
              {obs.teacher_expectations && (
                <div style={{ marginBottom: 10 }}>
                  <p style={{ color: C.textMuted, fontSize: 11, marginBottom: 4 }}>Expectativas:</p>
                  <p style={{ color: C.text, fontSize: 12, lineHeight: 1.5 }}>{obs.teacher_expectations}</p>
                </div>
              )}
              {obs.teacher_commitment && (
                <div>
                  <p style={{ color: C.textMuted, fontSize: 11, marginBottom: 4 }}>Compromisso:</p>
                  <p style={{ color: C.text, fontSize: 12, lineHeight: 1.5 }}>{obs.teacher_commitment}</p>
                </div>
              )}
            </Card>
          )}

          {/* PEC narrative */}
          {(pontosFortes.length > 0 || focos.length > 0) && (
            <Card style={{ marginBottom: 16 }}>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 12 }}>NARRATIVA PEC</h3>
              {pontosFortes.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <p style={{ color: C.success, fontSize: 11, fontWeight: 700, marginBottom: 6 }}>Pontos fortes:</p>
                  {pontosFortes.map((p, i) => <p key={i} style={{ color: C.text, fontSize: 12, marginBottom: 4 }}>✓ {p}</p>)}
                </div>
              )}
              {focos.length > 0 && (
                <div>
                  <p style={{ color: C.warning, fontSize: 11, fontWeight: 700, marginBottom: 6 }}>Focos:</p>
                  {focos.map((f, i) => <p key={i} style={{ color: C.text, fontSize: 12, marginBottom: 4 }}>→ {f}</p>)}
                </div>
              )}
            </Card>
          )}

          {/* BNCC */}
          {bnccSkills.length > 0 && (
            <Card style={{ marginBottom: 16 }}>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 10 }}>HABILIDADES BNCC</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {bnccSkills.map(s => (
                  <span key={s} style={{ background: C.accent + '22', color: C.accent, borderRadius: 6, padding: '3px 10px', fontSize: 12 }}>{s}</span>
                ))}
              </div>
            </Card>
          )}

          {/* Next observation */}
          {(obs.next_observation_date || obs.next_observation_focus) && (
            <Card>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 10 }}>PRÓXIMA OBSERVAÇÃO</h3>
              {obs.next_observation_date && (
                <p style={{ color: C.text, fontSize: 12 }}>📅 {new Date(obs.next_observation_date).toLocaleDateString('pt-BR')}</p>
              )}
              {obs.next_observation_focus && (
                <p style={{ color: C.textMuted, fontSize: 12 }}>Foco: {obs.next_observation_focus}</p>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
