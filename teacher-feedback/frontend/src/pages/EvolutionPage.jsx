import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { C } from '../colors'
import { Card, Select, Spinner, ErrorBanner } from '../components/shared'
import { EvolutionChart } from '../components/analytics/EvolutionChart'
import { ComparativeRadar } from '../components/analytics/ComparativeRadar'
import { useTeachers } from '../hooks/useTeachers'
import { api } from '../api/client'

export function EvolutionPage() {
  const [params] = useSearchParams()
  const { teachers } = useTeachers()
  const [selectedTeacher, setSelectedTeacher] = useState(params.get('teacher') || '')
  const [evolutionData, setEvolutionData] = useState(null)
  const [observations, setObservations] = useState([])
  const [comparativeData, setComparativeData] = useState(null)
  const [obs1, setObs1] = useState('')
  const [obs2, setObs2] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingComp, setLoadingComp] = useState(false)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('evolution')

  useEffect(() => {
    if (!selectedTeacher) return
    setLoading(true)
    setError(null)
    Promise.all([
      api.getEvolution(selectedTeacher),
      api.getTeacherObservations(selectedTeacher),
    ]).then(([evo, obs]) => {
      setEvolutionData(evo)
      setObservations(obs)
    }).catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [selectedTeacher])

  const handleCompare = async () => {
    if (!obs1 || !obs2 || obs1 === obs2) return
    setLoadingComp(true)
    try {
      const data = await api.getComparative(selectedTeacher, obs1, obs2)
      setComparativeData(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoadingComp(false)
    }
  }

  const obsOptions = [
    { value: '', label: '-- Selecione --' },
    ...observations.map(o => ({
      value: o.id,
      label: `${new Date(o.observed_at).toLocaleDateString('pt-BR')} – Score: ${o.scores?.total || 0}`,
    })),
  ]

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 24 }}>Evolução e Análises</h1>

      <Select
        label="Selecione o professor:"
        value={selectedTeacher}
        onChange={setSelectedTeacher}
        options={[
          { value: '', label: '-- Selecione um professor --' },
          ...teachers.map(t => ({ value: t.id, label: `${t.name} – ${t.subject || ''}` })),
        ]}
      />

      {selectedTeacher && (
        <>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
            {[
              { id: 'evolution', label: 'Evolução Temporal' },
              { id: 'comparative', label: 'Comparativo' },
            ].map(t => (
              <button
                key={t.id}
                type="button"
                onClick={() => setTab(t.id)}
                style={{
                  padding: '8px 20px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                  cursor: 'pointer', fontFamily: 'JetBrains Mono', transition: 'all 0.15s',
                  background: tab === t.id ? C.accent : C.surface2,
                  border: `1px solid ${tab === t.id ? C.accent : C.border}`,
                  color: tab === t.id ? '#fff' : C.textMuted,
                }}
              >
                {t.label}
              </button>
            ))}
          </div>

          {loading && <Spinner />}
          {error && <ErrorBanner message={error} />}

          {tab === 'evolution' && !loading && (
            <Card>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 20 }}>
                EVOLUÇÃO POR SEÇÃO AO LONGO DO TEMPO
              </h3>
              <EvolutionChart data={evolutionData} />
            </Card>
          )}

          {tab === 'comparative' && !loading && (
            <Card>
              <h3 style={{ color: C.textMuted, fontSize: 12, fontWeight: 700, marginBottom: 16 }}>
                COMPARAR DUAS OBSERVAÇÕES
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 12, alignItems: 'flex-end', marginBottom: 20 }}>
                <Select
                  label="Observação 1:"
                  value={obs1}
                  onChange={setObs1}
                  options={obsOptions}
                />
                <Select
                  label="Observação 2:"
                  value={obs2}
                  onChange={setObs2}
                  options={obsOptions.filter(o => o.value !== obs1)}
                />
                <button
                  type="button"
                  onClick={handleCompare}
                  disabled={!obs1 || !obs2 || obs1 === obs2 || loadingComp}
                  style={{
                    padding: '10px 20px', borderRadius: 8, background: C.accent, color: '#fff',
                    border: 'none', cursor: 'pointer', fontFamily: 'JetBrains Mono', fontSize: 13,
                    fontWeight: 600, opacity: (!obs1 || !obs2) ? 0.5 : 1, marginBottom: 16,
                  }}
                >
                  {loadingComp ? '...' : 'Comparar'}
                </button>
              </div>
              {comparativeData && <ComparativeRadar data={comparativeData} />}
              {!comparativeData && !loadingComp && (
                <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: '24px 0' }}>
                  Selecione duas observações para ver o comparativo.
                </p>
              )}
              {loadingComp && <Spinner />}
            </Card>
          )}
        </>
      )}

      {!selectedTeacher && (
        <Card>
          <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: '40px 0' }}>
            Selecione um professor para ver as análises.
          </p>
        </Card>
      )}
    </div>
  )
}
