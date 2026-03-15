import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { C, SECTION_COLORS } from '../../colors'

const SECTION_LABELS = {
  s1: 'Planejamento', s2: 'Condução', s3: 'Aprendizagem', s4: 'Materiais', s5: 'Clima', total: 'Total',
}

const EF1_COLORS = {
  ef1_dc: '#6C63FF',
  ef1_es: '#00D4AA',
  ef1_me: '#FFB020',
  ef1_md: '#45B7D1',
  ef1_gs: '#FF6B6B',
  ef1_mc: '#A78BFA',
}

const EF1_LABELS = {
  ef1_dc: 'EF1-Domínio', ef1_es: 'EF1-Engaj.', ef1_me: 'EF1-Metod.',
  ef1_md: 'EF1-Material', ef1_gs: 'EF1-Gestão', ef1_mc: 'EF1-Conflitos',
}

export function EvolutionChart({ data }) {
  if (!data?.series?.length) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: C.textMuted, fontSize: 13 }}>
        Nenhuma observação registrada ainda. Adicione observações para ver a evolução.
      </div>
    )
  }

  const hasEf1 = data.has_ef1 === true

  return (
    <div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data.series} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={C.border} />
          <XAxis dataKey="date" stroke={C.textMuted} fontSize={11} />
          <YAxis domain={[0, 100]} stroke={C.textMuted} fontSize={11} />
          <Tooltip
            contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8 }}
            labelStyle={{ color: C.text }}
            itemStyle={{ color: C.text }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: C.textMuted }} />
          {['s1', 's2', 's3', 's4', 's5', 'total'].map(sec => (
            <Line
              key={sec}
              type="monotone"
              dataKey={sec}
              name={SECTION_LABELS[sec]}
              stroke={SECTION_COLORS[sec]}
              strokeWidth={sec === 'total' ? 2.5 : 1.5}
              dot={{ r: 4, fill: SECTION_COLORS[sec] }}
              strokeDasharray={sec === 'total' ? '5 5' : undefined}
            />
          ))}
          {hasEf1 && Object.entries(EF1_COLORS).map(([key, color]) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              name={EF1_LABELS[key]}
              stroke={color}
              strokeWidth={1.5}
              dot={{ r: 3, fill: color }}
              strokeDasharray="3 3"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      {/* Trend badges */}
      {data.trends && (
        <div>
          {/* PEC trends */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 20 }}>
            {Object.entries(data.trends)
              .filter(([sec]) => !sec.startsWith('ef1_'))
              .map(([sec, trend]) => {
                const trendColor = trend.trend === 'improving' ? C.success : trend.trend === 'declining' ? C.danger : C.textMuted
                const trendIcon = trend.trend === 'improving' ? '↑' : trend.trend === 'declining' ? '↓' : '→'
                return (
                  <div key={sec} style={{ background: trendColor + '22', borderRadius: 8, padding: '8px 14px', fontSize: 12 }}>
                    <span style={{ color: SECTION_COLORS[sec] || C.text, fontWeight: 700 }}>{SECTION_LABELS[sec]}</span>
                    <span style={{ color: trendColor, marginLeft: 8 }}>{trendIcon} {trend.delta > 0 ? '+' : ''}{trend.delta}pts</span>
                  </div>
                )
              })}
          </div>
          {/* EF I trends */}
          {hasEf1 && (
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 10 }}>
              {Object.entries(data.trends)
                .filter(([sec]) => sec.startsWith('ef1_'))
                .map(([sec, trend]) => {
                  const trendColor = trend.trend === 'improving' ? C.success : trend.trend === 'declining' ? C.danger : C.textMuted
                  const trendIcon = trend.trend === 'improving' ? '↑' : trend.trend === 'declining' ? '↓' : '→'
                  return (
                    <div key={sec} style={{ background: trendColor + '22', borderRadius: 8, padding: '8px 14px', fontSize: 12, border: `1px solid ${EF1_COLORS[sec]}44` }}>
                      <span style={{ background: EF1_COLORS[sec] + '22', color: EF1_COLORS[sec], borderRadius: 4, padding: '1px 6px', fontSize: 10, marginRight: 6 }}>EF I</span>
                      <span style={{ color: EF1_COLORS[sec], fontWeight: 700 }}>{EF1_LABELS[sec]}</span>
                      <span style={{ color: trendColor, marginLeft: 8 }}>{trendIcon} {trend.delta > 0 ? '+' : ''}{trend.delta}pts</span>
                    </div>
                  )
                })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
