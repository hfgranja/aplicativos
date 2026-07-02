import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api/client.js";
import { Card, ErrorBanner, Spinner, StatTile } from "../components/shared/ui.jsx";
import { chartColors } from "../styles/chartColors.js";
import { useMerchant } from "../context/MerchantContext.jsx";

const METHOD_LABEL = { pix: "Pix", credit_card: "Cartão", boleto: "Boleto" };

export default function DashboardCost() {
  const { merchantId, apiKey } = useMerchant();
  const [metrics, setMetrics] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!merchantId || !apiKey) return;
    api.getMetrics(apiKey, merchantId).then(setMetrics).catch((e) => setError(e.message));
  }, [merchantId, apiKey]);

  if (!metrics) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  const costData = Object.entries(metrics.cost_by_method).map(([method, pct]) => ({
    method: METHOD_LABEL[method] || method,
    custo: Math.round(pct * 100) / 100,
  }));
  const totalVolume = Object.values(metrics.volume_by_method).reduce((a, b) => a + b, 0);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Dashboard de custo</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>Últimos {metrics.period_days} dias</p>

      <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
        <StatTile label="Custo médio realizado" value={`${metrics.avg_cost_pct.toFixed(2)}%`} />
        <StatTile label="Volume liquidado no período" value={`R$ ${totalVolume.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`} />
      </div>

      <Card title="Custo médio por meio de pagamento (%)">
        {costData.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Ainda não há liquidações neste período.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.border} />
              <XAxis dataKey="method" stroke={chartColors.textMuted} fontSize={12} />
              <YAxis stroke={chartColors.textMuted} fontSize={12} unit="%" />
              <Tooltip
                contentStyle={{ background: chartColors.surface2, border: `1px solid ${chartColors.border}`, borderRadius: 8 }}
                formatter={(v) => [`${v}%`, "Custo médio"]}
              />
              <Bar dataKey="custo" fill={chartColors.accent2} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}
