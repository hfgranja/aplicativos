import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { C, SECTION_COLORS } from '../colors'
import { Card, Badge, Spinner, ErrorBanner, Select } from '../components/shared'
import { useTeachers } from '../hooks/useTeachers'
import { api } from '../api/client'

export function HistoryPage() {
  const { teachers, loading: loadingTeachers } = useTeachers()
  const [selectedTeacher, setSelectedTeacher] = useState('')
  const [observations, setObservations] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!selectedTeacher) return
    setLoading(true)
    api.getTeacherObservations(selectedTeacher)
      .then(setObservations)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedTeacher])

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>Histórico de Observações</h1>

      <Select
        label="Selecione o professor:"
        value={selectedTeacher}
        onChange={setSelectedTeacher}
        options={[
          { value: '', label: '-- Selecione um professor --' },
          ...teachers.map(t => ({ value: t.id, label: `${t.name} – ${t.subject || ''}` })),
        ]}
      />

      {loading && <Spinner />}
      {error && <ErrorBanner message={error} />}

      {!loading && selectedTeacher && observations.length === 0 && (
        <Card>
          <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: 24 }}>
            Nenhuma observação registrada para este professor.{' '}
            <Link to="/nova-observacao" style={{ color: C.accent }}>Criar primeira observação</Link>
          </p>
        </Card>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {observations.map(obs => (
          <Link key={obs.id} to={`/observacoes/${obs.id}`} style={{ textDecoration: 'none' }}>
            <Card style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 14, color: C.text }}>
                    {obs.observed_at ? new Date(obs.observed_at).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' }) : '–'}
                  </div>
                  <div style={{ color: C.textMuted, fontSize: 12, marginTop: 2 }}>
                    {obs.focus_area && `Foco: ${obs.focus_area}`}
                    {obs.pec_name && ` · PEC: ${obs.pec_name}`}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  {obs.has_feedback && <Badge color={C.accent2}>Feedback</Badge>}
                  {obs.has_cnv && <Badge color={C.accent}>CNV</Badge>}
                  {obs.has_media && <Badge color={C.textMuted}>Áudio/Vídeo</Badge>}
                  <div style={{
                    background: C.accent + '22', color: C.accent, borderRadius: 8,
                    padding: '4px 14px', fontWeight: 700, fontSize: 18,
                  }}>
                    {obs.scores?.total || 0}
                  </div>
                </div>
              </div>

              {/* Section score bars */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8 }}>
                {['s1', 's2', 's3', 's4', 's5'].map(sec => (
                  <div key={sec}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3 }}>
                      <span style={{ fontSize: 9, color: C.textMuted }}>S{sec[1]}</span>
                      <span style={{ fontSize: 9, color: SECTION_COLORS[sec] }}>{obs.scores?.[sec] || 0}</span>
                    </div>
                    <div style={{ height: 4, background: C.surface3, borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ width: `${obs.scores?.[sec] || 0}%`, height: '100%', background: SECTION_COLORS[sec], borderRadius: 2 }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
