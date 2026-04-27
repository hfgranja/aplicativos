interface Props { icon?: string; title: string; description?: string; action?: { label: string; onClick: () => void } }

export function EmptyState({ icon = '📋', title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      <span className="text-5xl mb-4">{icon}</span>
      <h3 className="text-base font-semibold text-gray-900 mb-1">{title}</h3>
      {description && <p className="text-sm text-gray-500 max-w-xs mb-4">{description}</p>}
      {action && (
        <button onClick={action.onClick} className="btn-primary mt-2">{action.label}</button>
      )}
    </div>
  )
}
