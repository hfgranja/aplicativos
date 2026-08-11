import { formatNumber } from "../utils/format.js";

export default function YieldGapPanel({ yieldGap }) {
  if (!yieldGap) return <div className="loading">Carregando…</div>;

  const max = yieldGap.yield_potential_kg_ha || 1;
  const bars = [
    { label: "Potencial (sem limitação)", value: yieldGap.yield_potential_kg_ha, color: "#2a5c3a" },
    { label: "Atingível (sequeiro bem manejado)", value: yieldGap.yield_attainable_kg_ha, color: "#3f8a55" },
    { label: "Previsto para este talhão", value: yieldGap.yield_predicted_kg_ha, color: "#5fd67d" },
  ];
  if (yieldGap.yield_regional_kg_ha) {
    bars.push({ label: "Média regional (IBGE)", value: yieldGap.yield_regional_kg_ha, color: "#4a9fe6" });
  }

  return (
    <div>
      {bars.map((bar) => (
        <div className="gap-bar-row" key={bar.label}>
          <span className="gap-bar-label muted">{bar.label}</span>
          <div className="gap-bar-track">
            <div className="gap-bar-fill" style={{ width: `${(bar.value / max) * 100}%`, background: bar.color }} />
          </div>
          <span className="gap-bar-value">{formatNumber(bar.value, 0)} kg/ha</span>
        </div>
      ))}

      <p className="muted" style={{ fontSize: 12, margin: "14px 0 8px" }}>
        Gap para o atingível: <strong>{formatNumber(yieldGap.gap_to_attainable_kg_ha, 0)} kg/ha</strong> (
        {formatNumber(yieldGap.gap_pct_of_attainable, 0)}%)
        {yieldGap.most_limiting && (
          <>
            {" "}
            · fator mais limitante: <strong>{yieldGap.most_limiting}</strong>
          </>
        )}
      </p>

      {yieldGap.limiting_factors?.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Fator limitante</th>
              <th>Penalidade</th>
              <th>Recuperável</th>
              <th>Evidência</th>
            </tr>
          </thead>
          <tbody>
            {yieldGap.limiting_factors.map((f) => (
              <tr key={f.factor}>
                <td>{f.label}</td>
                <td>{formatNumber(f.penalty_pct, 1)}%</td>
                <td>{formatNumber(f.recoverable_kg_ha, 0)} kg/ha</td>
                <td className="muted" style={{ fontSize: 12 }}>{f.evidence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {!yieldGap.limiting_factors?.length && (
        <div className="empty-state">Nenhum fator limitante relevante identificado com os dados atuais.</div>
      )}
    </div>
  );
}
