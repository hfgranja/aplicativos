import { useEffect, useState } from 'react'
import { Layout } from '../adapters/ui/components/common/Layout'
import { PageSpinner } from '../adapters/ui/components/common/Spinner'
import { ErrorBanner } from '../adapters/ui/components/common/ErrorBanner'
import { EmptyState } from '../adapters/ui/components/common/EmptyState'
import { ObservationCard } from '../adapters/ui/components/observations/ObservationCard'
import { CreateObservationModal } from '../adapters/ui/components/observations/CreateObservationModal'
import { useObservations } from '../adapters/ui/viewModels/useObservations'
import { useSchools } from '../adapters/ui/viewModels/useSchools'

const STATUS_FILTERS = [
  { label: 'Todas', value: '' },
  { label: 'Rascunho', value: 'draft' },
  { label: 'Em andamento', value: 'audio_uploaded' },
  { label: 'Feedback pronto', value: 'feedback_ready' },
  { label: 'Aprovado', value: 'approved' },
]

export function ObservationsPage() {
  const { observations, loading, error, load, create, transition, remove } = useObservations()
  const { schools, teachers, loadSchools, loadTeachers } = useSchools()
  const [filter, setFilter]   = useState('')
  const [showModal, setShowModal] = useState(false)

  useEffect(() => { load(1, filter || undefined) }, [filter])
  useEffect(() => { loadSchools() }, [])

  return (
    <Layout title="Observações">
      <div className="px-4 pt-4 pb-2 lg:px-6 lg:pt-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-gray-900 hidden lg:block">Observações</h1>
          <button className="btn-primary ml-auto" onClick={() => setShowModal(true)}>
            + Nova observação
          </button>
        </div>

        {/* Filter chips */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 lg:mx-0 lg:px-0 scrollbar-none">
          {STATUS_FILTERS.map(f => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`flex-shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors border ${
                filter === f.value
                  ? 'bg-seduc-blue text-white border-seduc-blue'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 lg:px-6">
        {error && <ErrorBanner message={error} />}

        {loading ? (
          <PageSpinner />
        ) : observations.length === 0 ? (
          <EmptyState
            icon="📋"
            title="Nenhuma observação encontrada"
            description="Crie uma nova observação para começar o ciclo de feedback pedagógico."
            action={{ label: '+ Nova observação', onClick: () => setShowModal(true) }}
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 mt-3">
            {observations.map(obs => (
              <ObservationCard
                key={obs.id}
                observation={obs}
                onTransition={transition}
                onDelete={remove}
              />
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <CreateObservationModal
          schools={schools}
          teachers={teachers}
          onLoadTeachers={loadTeachers}
          onSubmit={async data => {
            const obs = await create(data)
            return obs !== null
          }}
          onClose={() => setShowModal(false)}
        />
      )}
    </Layout>
  )
}
