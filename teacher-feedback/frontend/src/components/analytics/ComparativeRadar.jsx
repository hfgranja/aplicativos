import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { C } from '../../colors'

export function ComparativeRadar({ data }) {
  if (!data) return null

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Radar */}
        <div>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12, textAlign: 'center' }}>Visão Radar</p>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={data.radar}>
              <PolarGrid stroke={C.border} />
              <PolarAngleAxis dataKey="section" tick={{ fill: C.textMuted, fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              <Radar name={data.obs1.date} dataKey="obs1" stroke="#6C63FF" fill="#6C63FF" fillOpacity={0.2} />
              <Radar name={data.obs2.date} dataKey="obs2" stroke="#00D4AA" fill="#00D4AA" fillOpacity={0.2} />
              <Legend wrapperStyle={{ fontSize: 11, color: C.textMuted }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Bar chart */}
        <div>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12, textAlign: 'center' }}>Comparativo por Seção</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data.radar} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
              <XAxis type="number" domain={[0, 100]} stroke={C.textMuted} fontSize={10} />
              <YAxis type="category" dataKey="key" stroke={C.textMuted} fontSize={10} width={30} />
              <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="obs1" name={data.obs1.date} fill="#6C63FF" fillOpacity={0.8} />
              <Bar dataKey="obs2" name={data.obs2.date} fill="#00D4AA" fillOpacity={0.8} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Diff table */}
      <div style={{ marginTop: 20 }}>
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 12 }}>Variação:</p>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {Object.entries(data.diff).map(([sec, delta]) => (
            <div key={sec} style={{
              background: delta > 0 ? C.success + '22' : delta < 0 ? C.danger + '22' : C.surface2,
              borderRadius: 8, padding: '8px 16px', textAlign: 'center',
            }}>
              <div style={{ color: C.textMuted, fontSize: 10, marginBottom: 2 }}>{sec.toUpperCase()}</div>
              <div style={{ color: delta > 0 ? C.success : delta < 0 ? C.danger : C.textMuted, fontWeight: 700, fontSize: 16 }}>
                {delta > 0 ? '+' : ''}{delta}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
