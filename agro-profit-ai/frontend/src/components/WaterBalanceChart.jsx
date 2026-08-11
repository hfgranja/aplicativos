import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatDate, formatNumber } from "../utils/format.js";

export default function WaterBalanceChart({ waterBalance }) {
  if (!waterBalance?.available) {
    return <div className="empty-state">Balanço hídrico indisponível (sem observações climáticas suficientes).</div>;
  }

  const data = waterBalance.series.map((s) => ({
    date: formatDate(s.date),
    chuva: s.rain_mm,
    etc: s.etc_mm,
    balanço: s.cumulative_balance_mm,
  }));

  const stressTone =
    waterBalance.water_stress_index >= 55 ? "negative" : waterBalance.water_stress_index >= 25 ? "warning" : "positive";

  return (
    <div>
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 14 }}>
        <div className="kpi-card">
          <div className="kpi-label">Índice de estresse hídrico</div>
          <div className={`kpi-value ${stressTone}`}>{formatNumber(waterBalance.water_stress_index, 0)}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Chuva no período</div>
          <div className="kpi-value">{formatNumber(waterBalance.total_rain_mm, 0)} mm</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">ETc (demanda da cultura)</div>
          <div className="kpi-value">{formatNumber(waterBalance.total_etc_mm, 0)} mm</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Balanço acumulado</div>
          <div className={`kpi-value ${waterBalance.cumulative_balance_mm < 0 ? "negative" : "positive"}`}>
            {formatNumber(waterBalance.cumulative_balance_mm, 0)} mm
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a372f" />
          <XAxis dataKey="date" hide />
          <YAxis yAxisId="mm" stroke="#9fb0a5" fontSize={11} />
          <YAxis yAxisId="bal" orientation="right" stroke="#9fb0a5" fontSize={11} />
          <Tooltip contentStyle={{ background: "#1d2922", border: "1px solid #2a372f" }} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar yAxisId="mm" isAnimationActive={false} dataKey="chuva" fill="#4a9fe6" radius={[2, 2, 0, 0]} name="Chuva (mm)" />
          <Line yAxisId="mm" isAnimationActive={false} type="monotone" dataKey="etc" stroke="#e6b04a" strokeWidth={2} dot={false} name="ETc FAO-56 (mm)" />
          <Area
            isAnimationActive={false}
            yAxisId="bal"
            type="monotone"
            dataKey="balanço"
            stroke="#e2604f"
            fill="rgba(226,96,79,0.12)"
            name="Balanço acumulado (mm)"
          />
        </ComposedChart>
      </ResponsiveContainer>
      <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
        ET0 por Hargreaves-Samani (FAO-56) × Kc da fase fenológica corrente. Estresse pondera o déficit pela
        sensibilidade da fase (florescimento/enchimento pesam mais).
      </p>
    </div>
  );
}
