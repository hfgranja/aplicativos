interface Props { message: string; onDismiss?: () => void }

export function ErrorBanner({ message, onDismiss }: Props) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
      <span className="mt-0.5 text-base">⚠️</span>
      <span className="flex-1">{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} className="text-red-500 hover:text-red-700 font-bold">✕</button>
      )}
    </div>
  )
}
