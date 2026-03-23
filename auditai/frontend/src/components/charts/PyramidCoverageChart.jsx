const LEVELS = [
  { level: 1, name: 'Static / SAST', engine: 'sast' },
  { level: 2, name: 'Unit / Mutation', engine: 'mutation' },
  { level: 3, name: 'Property / Fuzzing', engine: 'fuzzing' },
  { level: 4, name: 'Integration', engine: 'integration' },
  { level: 5, name: 'Contract / API', engine: 'contract' },
  { level: 6, name: 'Differential', engine: 'differential' },
  { level: 7, name: 'End-to-End', engine: 'e2e' },
  { level: 8, name: 'Performance', engine: 'performance' },
  { level: 9, name: 'Security / Pentest', engine: 'security' },
  { level: 10, name: 'Chaos / Resilience', engine: 'chaos' },
]

const scoreColor = (score) => {
  if (score === undefined || score === null) return '#1e2535'
  if (score >= 80) return '#166534'
  if (score >= 60) return '#92400e'
  return '#991b1b'
}

const scoreTextColor = (score) => {
  if (score === undefined || score === null) return '#475569'
  if (score >= 80) return '#4ade80'
  if (score >= 60) return '#fbbf24'
  return '#f87171'
}

export default function PyramidCoverageChart({ coverage = {} }) {
  const maxWidth = 600
  const levelHeight = 38

  return (
    <div style={{ padding: 16 }}>
      <div style={{ fontSize: 13, color: '#64748b', marginBottom: 12 }}>Testing Pyramid Coverage</div>
      {[...LEVELS].reverse().map(({ level, name }) => {
        const data = coverage[level]
        const score = data?.score
        const width = 100 + (level / 10) * (maxWidth - 100)
        return (
          <div key={level} style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <div style={{ width: 28, textAlign: 'right', fontSize: 11, color: '#475569' }}>{level}</div>
            <div style={{
              width,
              height: levelHeight,
              background: scoreColor(score),
              borderRadius: 4,
              border: `1px solid ${data ? '#334155' : '#1e2535'}`,
              display: 'flex',
              alignItems: 'center',
              padding: '0 12px',
              justifyContent: 'space-between',
              transition: 'width 0.3s',
            }}>
              <span style={{ fontSize: 12, color: '#94a3b8' }}>{name}</span>
              <span style={{ fontSize: 12, fontWeight: 600, color: scoreTextColor(score) }}>
                {score !== undefined && score !== null ? `${score}` : '—'}
              </span>
            </div>
            {data?.status && (
              <span style={{ fontSize: 11, color: '#64748b' }}>{data.status}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
