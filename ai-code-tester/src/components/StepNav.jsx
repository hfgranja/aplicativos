const STEPS = [
  { id: 'input', label: 'Código', icon: '📂', num: 1 },
  { id: 'analyzing', label: 'Analisando', icon: '⚙️', num: 2 },
  { id: 'results', label: 'Resultados', icon: '📊', num: 3 },
  { id: 'tests', label: 'Testes', icon: '✅', num: 4 },
]

export default function StepNav({ currentStep }) {
  const currentIdx = STEPS.findIndex(s => s.id === currentStep)

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, justifyContent: 'center', marginBottom: 40 }}>
      {STEPS.map((step, i) => {
        const isDone = i < currentIdx
        const isActive = i === currentIdx
        return (
          <div key={step.id} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
            }}>
              <div style={{
                width: 44, height: 44,
                borderRadius: '50%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: isDone ? 16 : 18,
                fontWeight: 700,
                background: isDone
                  ? 'rgba(0,200,150,0.2)'
                  : isActive
                    ? 'rgba(108,99,255,0.25)'
                    : 'rgba(255,255,255,0.05)',
                border: isDone
                  ? '2px solid #00C896'
                  : isActive
                    ? '2px solid #6C63FF'
                    : '2px solid rgba(255,255,255,0.1)',
                color: isDone ? '#00C896' : isActive ? '#6C63FF' : 'rgba(255,255,255,0.3)',
                transition: 'all 0.3s ease',
              }}>
                {isDone ? '✓' : step.num}
              </div>
              <span style={{
                fontSize: 11,
                fontWeight: isActive ? 600 : 400,
                color: isDone ? '#00C896' : isActive ? '#6C63FF' : 'rgba(255,255,255,0.35)',
                letterSpacing: 1,
                textTransform: 'uppercase',
              }}>
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{
                width: 60, height: 2, margin: '0 8px', marginBottom: 24,
                background: i < currentIdx
                  ? 'linear-gradient(90deg, #00C896, #6C63FF)'
                  : 'rgba(255,255,255,0.08)',
                transition: 'background 0.4s ease',
              }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
