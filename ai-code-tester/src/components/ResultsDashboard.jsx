import HealthGauge from './HealthGauge.jsx'
import ScoreCard from './ScoreCard.jsx'
import { scoreColor } from '../theme.js'

export default function ResultsDashboard({ results, overallScore, onGenerateTests, onReset }) {
  const criticalCount = results.filter(r => r.score < 40).length
  const goodCount = results.filter(r => r.score >= 80).length
  const color = scoreColor(overallScore)

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Overall Score Panel */}
      <div style={{
        background: '#13131A',
        border: `1px solid ${color}30`,
        borderRadius: 20,
        padding: '32px 40px',
        marginBottom: 32,
        display: 'flex',
        alignItems: 'center',
        gap: 48,
        flexWrap: 'wrap',
      }}>
        <HealthGauge score={overallScore} />

        <div style={{ flex: 1, minWidth: 240 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700, marginBottom: 4 }}>
            Score de Qualidade de IA
          </h2>
          <p style={{ fontSize: 13, color: 'rgba(232,232,240,0.5)', marginBottom: 20 }}>
            Análise baseada em 12 técnicas de validação
          </p>

          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
            <Stat value={goodCount} label="Técnicas OK" color="#00C896" />
            <Stat value={12 - goodCount - criticalCount} label="Atenção" color="#FFB020" />
            <Stat value={criticalCount} label="Críticas" color="#FF4D6D" />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <button
            onClick={onGenerateTests}
            style={{
              background: 'linear-gradient(135deg, #6C63FF, #00D4AA)',
              border: 'none', color: '#fff',
              padding: '14px 28px', borderRadius: 10,
              cursor: 'pointer', fontSize: 14, fontWeight: 700,
              boxShadow: '0 6px 24px rgba(108,99,255,0.35)',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={e => { e.target.style.transform = 'translateY(-2px)' }}
            onMouseLeave={e => { e.target.style.transform = 'none' }}
          >
            ✅ Gerar Testes Automáticos
          </button>

          <button
            onClick={onReset}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(232,232,240,0.6)',
              padding: '10px 28px', borderRadius: 10,
              cursor: 'pointer', fontSize: 13, fontWeight: 500,
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.target.style.background = 'rgba(255,255,255,0.1)' }}
            onMouseLeave={e => { e.target.style.background = 'rgba(255,255,255,0.05)' }}
          >
            🔄 Nova Análise
          </button>
        </div>
      </div>

      {/* 12 Score Cards Grid */}
      <h3 style={{ fontSize: 14, fontWeight: 600, letterSpacing: 1, textTransform: 'uppercase',
        color: 'rgba(232,232,240,0.4)', marginBottom: 16 }}>
        Detalhamento por Técnica <span style={{ fontWeight: 400 }}>(clique para expandir)</span>
      </h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
        gap: 12,
      }}>
        {results.map(result => (
          <ScoreCard key={result.id} result={result} />
        ))}
      </div>
    </div>
  )
}

function Stat({ value, label, color }) {
  return (
    <div>
      <div style={{ fontSize: 28, fontWeight: 700, color, fontFamily: 'JetBrains Mono, monospace' }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.4)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
    </div>
  )
}
