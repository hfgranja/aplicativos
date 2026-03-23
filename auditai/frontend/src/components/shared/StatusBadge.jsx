const COLORS = {
  GREEN: { bg: '#052e16', color: '#4ade80', border: '#166534' },
  YELLOW: { bg: '#422006', color: '#fbbf24', border: '#92400e' },
  RED: { bg: '#450a0a', color: '#f87171', border: '#991b1b' },
  PENDING: { bg: '#1e2535', color: '#94a3b8', border: '#334155' },
  RUNNING: { bg: '#1e3a5f', color: '#60a5fa', border: '#1d4ed8' },
  COMPLETED: { bg: '#052e16', color: '#4ade80', border: '#166534' },
  FAILED: { bg: '#450a0a', color: '#f87171', border: '#991b1b' },
  CANCELLED: { bg: '#1e2535', color: '#94a3b8', border: '#334155' },
  CRITICAL: { bg: '#450a0a', color: '#f87171', border: '#991b1b' },
  HIGH: { bg: '#431407', color: '#fb923c', border: '#9a3412' },
  MEDIUM: { bg: '#422006', color: '#fbbf24', border: '#92400e' },
  LOW: { bg: '#052e16', color: '#4ade80', border: '#166534' },
  INFO: { bg: '#1e2535', color: '#94a3b8', border: '#334155' },
}

export default function StatusBadge({ status, small }) {
  const c = COLORS[status?.toUpperCase()] || COLORS.INFO
  return (
    <span style={{
      display: 'inline-block',
      padding: small ? '2px 8px' : '4px 12px',
      borderRadius: 9999,
      fontSize: small ? 11 : 12,
      fontWeight: 600,
      background: c.bg,
      color: c.color,
      border: `1px solid ${c.border}`,
      letterSpacing: 0.5,
    }}>
      {status}
    </span>
  )
}
