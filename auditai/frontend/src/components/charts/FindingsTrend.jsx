import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function FindingsTrend({ data = [] }) {
  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2535" />
        <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }} />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
        <Tooltip contentStyle={{ background: '#161b27', border: '1px solid #1e2535', color: '#e2e8f0' }} />
        <Line type="monotone" dataKey="critical" stroke="#f87171" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="high" stroke="#fb923c" dot={false} strokeWidth={2} />
        <Line type="monotone" dataKey="medium" stroke="#fbbf24" dot={false} strokeWidth={1} />
      </LineChart>
    </ResponsiveContainer>
  )
}
