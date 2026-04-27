import type { School } from '../../../../domain/entities/School'

interface Props { school: School; onClick?: () => void }

export function SchoolCard({ school, onClick }: Props) {
  return (
    <div
      className="card p-4 cursor-pointer hover:shadow-md transition-shadow active:scale-[0.99]"
      onClick={onClick}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-brand-100 text-brand-600 text-lg">
          🏫
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{school.name}</p>
          <p className="text-xs text-gray-500">{school.city} — {school.state}</p>
          {school.principalName && (
            <p className="text-xs text-gray-400 mt-0.5">Diretor(a): {school.principalName}</p>
          )}
          <p className="text-xs text-gray-300 mt-1 font-mono">INEP {school.inepCode}</p>
        </div>
        <span className={`badge ${school.isActive ? 'badge-green' : 'badge-gray'}`}>
          {school.isActive ? 'Ativa' : 'Inativa'}
        </span>
      </div>
    </div>
  )
}
