import type { Observation } from '../../../../domain/entities/Observation'
import { STATUS_LABELS, STATUS_COLOR } from '../../../../domain/entities/Observation'

interface Props {
  observation: Observation
  onTransition?: (id: string, status: string) => void
  onDelete?: (id: string) => void
}

export function ObservationCard({ observation, onTransition, onDelete }: Props) {
  const date = new Date(observation.scheduledAt).toLocaleDateString('pt-BR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })

  return (
    <div className="card p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={STATUS_COLOR[observation.status]}>
              {STATUS_LABELS[observation.status]}
            </span>
            <span className="badge badge-gray">{observation.subject}</span>
            <span className="text-xs text-gray-400">{observation.grade}</span>
          </div>
          <p className="text-sm font-semibold text-gray-900 truncate">
            {observation.teacherName ?? observation.teacherId}
          </p>
          <p className="text-xs text-gray-500 truncate">
            {observation.schoolName ?? observation.schoolId}
          </p>
          <p className="text-xs text-gray-400 mt-1">{date} · {observation.durationMinutes} min</p>
        </div>
        <div className="flex flex-col gap-1">
          {observation.status === 'draft' && onTransition && (
            <button
              onClick={() => onTransition(observation.id, 'ready_to_record')}
              className="text-xs text-brand-600 font-medium hover:underline whitespace-nowrap"
            >
              Iniciar
            </button>
          )}
          {onDelete && (
            <button
              onClick={() => onDelete(observation.id)}
              className="text-xs text-red-400 hover:text-red-600 font-medium"
            >
              Remover
            </button>
          )}
        </div>
      </div>
      {observation.notes && (
        <p className="mt-2 text-xs text-gray-500 line-clamp-2 border-t border-gray-50 pt-2">
          {observation.notes}
        </p>
      )}
    </div>
  )
}
