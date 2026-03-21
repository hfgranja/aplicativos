export default function ScoreGauge({ score, label, size = 80 }) {
  const r = size / 2 - 8
  const circ = 2 * Math.PI * r
  const pct = Math.max(0, Math.min(100, score || 0))
  const dash = (pct / 100) * circ
  const color = pct >= 80 ? '#4ade80' : pct >= 60 ? '#fbbf24' : '#f87171'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1e2535" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={6}
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        <text x={size / 2} y={size / 2 + 5} textAnchor="middle" fill={color}
          fontSize={size / 5} fontWeight={700}>
          {pct}
        </text>
      </svg>
      {label && <span style={{ fontSize: 11, color: '#64748b' }}>{label}</span>}
    </div>
  )
}
