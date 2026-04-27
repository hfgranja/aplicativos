export function Spinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const cls = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }[size]
  return (
    <div className={`${cls} animate-spin rounded-full border-2 border-gray-200 border-t-seduc-blue`} />
  )
}

export function PageSpinner() {
  return (
    <div className="flex h-48 items-center justify-center">
      <Spinner size="lg" />
    </div>
  )
}
