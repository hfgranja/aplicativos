import { useEffect, useState } from 'react'
import { C } from '../colors'
import { ObservationWizard } from '../components/observation/ObservationWizard'
import { api } from '../api/client'
import { Spinner, ErrorBanner } from '../components/shared'

export function NewObservationPage() {
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getTeachers()
      .then(setTeachers)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <h1 style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>Nova Observação de Aula</h1>
      <p style={{ color: C.textMuted, fontSize: 13, marginBottom: 32 }}>
        Preencha os 10 passos da ficha de observação PEC.
      </p>
      {loading ? <Spinner /> : error ? <ErrorBanner message={error} /> : (
        <ObservationWizard teachers={teachers} />
      )}
    </div>
  )
}
