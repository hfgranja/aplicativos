import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { C, SECTION_COLORS } from '../colors'
import { Card, Badge, Spinner, ScoreBar } from '../components/shared'
import { api } from '../api/client'

export function HomePage() {
  const [llmStatus, setLlmStatus] = useState(null)
  const [recentObs, setRecentObs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.llmStatus().then(setLlmStatus).catch(() => setLlmStatus({ status: 'error' })),
      api.getTeachers()
        .then(async teachers => {
          const all = []
          for (const t of teachers.slice(0, 5)) {
            const obs = await api.getTeacherObservations(t.id)
            obs.forEach(o => all.push({ ...o, teacher: t }))
          }
          all.sort((a, b) => new Date(b.observed_at) - new Date(a.observed_at))
          setRecentObs(all.slice(0, 5))
        })
        .catch(() => {}),
    ]).finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>PEC – Feedback de Aulas</h1>
      <p style={{ color: C.textMuted, fontSize: 13, marginBottom: 32 }}>
        Sistema de acompanhamento pedagógico com LLM local
      </p>

      {/* LLM status */}
      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 10, height: 10, borderRadius: '50%',
            background: llmStatus?.status === 'ok' ? C.success : C.danger,
          }} />
          <span style={{ fontSize: 13, color: C.text }}>
            Ollama (llama3.2): {llmStatus?.status === 'ok' ? (
              <span style={{ color: C.success }}>Online</span>
            ) : llmStatus?.status === 'error' ? (
              <span style={{ color: C.danger }}>Offline – Execute: <code>ollama serve</code></span>
            ) : '...'}
          </span>
          {llmStatus?.models?.length > 0 && (
            <span style={{ color: C.textMuted, fontSize: 11 }}>
              ({llmStatus.models.join(', ')})
            </span>
          )}
        </div>
      </Card>

      {/* Quick actions */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 32 }}>
        {[
          { to: '/nova-observacao', label: 'Nova Observação', icon: '+', color: C.accent },
          { to: '/professores', label: 'Professores', icon: '👤', color: C.accent2 },
          { to: '/evolucao', label: 'Ver Evolução', icon: '↗', color: C.warning },
        ].map(({ to, label, icon, color }) => (
          <Link key={to} to={to} style={{ textDecoration: 'none' }}>
            <Card style={{ textAlign: 'center', cursor: 'pointer', transition: 'border-color 0.15s', borderColor: 'transparent' }}>
              <div style={{ fontSize: 28, marginBottom: 8 }}>{icon}</div>
              <div style={{ color, fontWeight: 700, fontSize: 14 }}>{label}</div>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent observations */}
      <h2 style={{ fontSize: 14, color: C.textMuted, marginBottom: 16, fontWeight: 600 }}>
        Observações Recentes
      </h2>
      {loading ? <Spinner /> : recentObs.length === 0 ? (
        <Card>
          <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: '24px 0' }}>
            Nenhuma observação registrada.{' '}
            <Link to="/nova-observacao" style={{ color: C.accent }}>Criar primeira observação</Link>
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {recentObs.map(obs => (
            <Link key={obs.id} to={`/observacoes/${obs.id}`} style={{ textDecoration: 'none' }}>
              <Card style={{ cursor: 'pointer' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                  <div>
                    <span style={{ color: C.text, fontWeight: 600, fontSize: 14 }}>{obs.teacher.name}</span>
                    <span style={{ color: C.textMuted, fontSize: 12, marginLeft: 10 }}>
                      {obs.teacher.subject} · {new Date(obs.observed_at).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {obs.has_feedback && <Badge color={C.accent2}>Feedback</Badge>}
                    {obs.has_cnv && <Badge color={C.accent}>CNV</Badge>}
                    <Badge color={SECTION_COLORS.total}>{obs.scores?.total || 0}pts</Badge>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  {['s1', 's2', 's3', 's4', 's5'].map(sec => (
                    <div key={sec} style={{ flex: 1 }}>
                      <div style={{ height: 4, background: SECTION_COLORS[sec], borderRadius: 2, opacity: (obs.scores?.[sec] || 0) / 100 + 0.1 }} />
                    </div>
                  ))}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
