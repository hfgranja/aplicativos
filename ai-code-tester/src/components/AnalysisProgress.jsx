const TECHNIQUES = [
  { name: 'Análise Estática', icon: '🔍' },
  { name: 'Complexidade Ciclomática', icon: '🔄' },
  { name: 'Duplicação de Código', icon: '📋' },
  { name: 'Varredura de Segurança', icon: '🛡️' },
  { name: 'Segurança de Tipos', icon: '📐' },
  { name: 'Risco de Dependências', icon: '📦' },
  { name: 'Estimativa de Cobertura', icon: '📊' },
  { name: 'Qualidade de Documentação', icon: '📝' },
  { name: 'Boas Práticas', icon: '⚡' },
  { name: 'Anti-padrões de Performance', icon: '🚀' },
  { name: 'Tratamento de Erros', icon: '🔧' },
  { name: 'Contratos de API', icon: '🔌' },
  { name: 'Testes por Mutação', icon: '🧬' },
]

const TOTAL_TECHNIQUES = TECHNIQUES.length

export default function AnalysisProgress({ progress, currentTechnique }) {
  const pct = Math.round((progress / TOTAL_TECHNIQUES) * 100)

  return (
    <div style={{ maxWidth: 680, margin: '0 auto', textAlign: 'center' }}>
      <div style={{ marginBottom: 48 }}>
        <div style={{ fontSize: 48, marginBottom: 16, animation: 'spin 2s linear infinite' }}>
          ⚙️
        </div>
        <h2 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8, color: '#E8E8F0' }}>
          Analisando seu código...
        </h2>
        <p style={{ color: 'rgba(232,232,240,0.5)', fontSize: 14 }}>
          {currentTechnique || 'Iniciando análise'}
        </p>
      </div>

      {/* Main progress bar */}
      <div style={{ marginBottom: 40 }}>
        <div style={{
          height: 8, background: 'rgba(255,255,255,0.06)',
          borderRadius: 4, overflow: 'hidden', marginBottom: 8,
        }}>
          <div style={{
            height: '100%',
            width: `${pct}%`,
            background: 'linear-gradient(90deg, #6C63FF, #00D4AA)',
            borderRadius: 4,
            transition: 'width 0.4s ease',
            boxShadow: '0 0 12px rgba(108,99,255,0.5)',
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'rgba(232,232,240,0.4)' }}>
          <span>{progress} / {TOTAL_TECHNIQUES} técnicas</span>
          <span style={{ color: '#6C63FF', fontWeight: 600 }}>{pct}%</span>
        </div>
      </div>

      {/* Techniques grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10,
      }}>
        {TECHNIQUES.map((t, i) => {
          const done = i < progress
          const active = i === progress - 1
          return (
            <div key={i} style={{
              padding: '10px 8px',
              borderRadius: 10,
              background: done
                ? 'rgba(0,200,150,0.1)'
                : active
                  ? 'rgba(108,99,255,0.15)'
                  : 'rgba(255,255,255,0.03)',
              border: done
                ? '1px solid rgba(0,200,150,0.3)'
                : active
                  ? '1px solid rgba(108,99,255,0.4)'
                  : '1px solid rgba(255,255,255,0.06)',
              transition: 'all 0.3s ease',
              display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4,
            }}>
              <span style={{ fontSize: 18 }}>{done ? '✓' : t.icon}</span>
              <span style={{
                fontSize: 9, textAlign: 'center',
                color: done ? '#00C896' : active ? '#6C63FF' : 'rgba(232,232,240,0.3)',
                fontWeight: done || active ? 600 : 400,
                lineHeight: 1.3,
              }}>
                {t.name}
              </span>
            </div>
          )
        })}
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
