import { scoreColor } from '../theme.js'

function getLabel(score) {
  if (score >= 90) return 'Excelente'
  if (score >= 75) return 'Bom'
  if (score >= 60) return 'Regular'
  if (score >= 40) return 'Ruim'
  return 'Crítico'
}

export default function HealthGauge({ score }) {
  const color = scoreColor(score)
  const r = 70
  const cx = 90
  const cy = 90
  const startAngle = -210
  const totalAngle = 240
  const angle = startAngle + (score / 100) * totalAngle
  const toRad = deg => (deg * Math.PI) / 180

  // Arc path for gauge background
  function describeArc(start, end) {
    const s = toRad(start)
    const e = toRad(end)
    const x1 = cx + r * Math.cos(s)
    const y1 = cy + r * Math.sin(s)
    const x2 = cx + r * Math.cos(e)
    const y2 = cy + r * Math.sin(e)
    const large = end - start > 180 ? 1 : 0
    return `M ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2}`
  }

  const bgPath = describeArc(startAngle, startAngle + totalAngle)
  const fillPath = score > 0 ? describeArc(startAngle, Math.min(startAngle + totalAngle - 0.1, angle)) : ''

  // Needle
  const needleAngle = toRad(angle)
  const needleLen = 52
  const nx = cx + needleLen * Math.cos(needleAngle)
  const ny = cy + needleLen * Math.sin(needleAngle)

  const label = getLabel(score)

  return (
    <div style={{ textAlign: 'center' }}>
      <svg width={180} height={150} viewBox="0 0 180 150">
        {/* Background arc */}
        <path d={bgPath} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={10} strokeLinecap="round" />
        {/* Colored fill arc */}
        {score > 0 && (
          <path d={fillPath} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round"
            style={{ transition: 'stroke 0.5s ease' }} />
        )}
        {/* Glow */}
        {score > 0 && (
          <path d={fillPath} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round"
            opacity={0.3} filter="blur(4px)" />
        )}
        {/* Needle */}
        <line x1={cx} y1={cy} x2={nx} y2={ny}
          stroke={color} strokeWidth={2.5} strokeLinecap="round"
          style={{ transition: 'all 0.8s cubic-bezier(.34,1.56,.64,1)' }} />
        <circle cx={cx} cy={cy} r={6} fill={color} />
        <circle cx={cx} cy={cy} r={3} fill="#0D0D12" />

        {/* Score text */}
        <text x={cx} y={cy + 26} textAnchor="middle"
          fill={color} fontSize={28} fontWeight={700} fontFamily="JetBrains Mono, monospace">
          {score}
        </text>
        <text x={cx} y={cy + 42} textAnchor="middle"
          fill="rgba(232,232,240,0.4)" fontSize={11} fontFamily="Inter, sans-serif">
          /100
        </text>
      </svg>

      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: 8, marginTop: -4,
        background: `${color}15`, border: `1px solid ${color}40`,
        borderRadius: 20, padding: '4px 16px',
      }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
        <span style={{ fontSize: 13, fontWeight: 700, color, letterSpacing: 0.5 }}>
          {label}
        </span>
      </div>
    </div>
  )
}
