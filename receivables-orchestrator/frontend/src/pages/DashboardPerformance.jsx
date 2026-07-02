import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api from "../api/client.js";
import { Card, ErrorBanner, Spinner, StatTile } from "../components/shared/ui.jsx";
import { chartColors } from "../styles/chartColors.js";
import { useMerchant } from "../context/MerchantContext.jsx";

const METHOD_LABEL = { pix: "Pix", credit_card: "Cartão", boleto: "Boleto" };

export default function DashboardPerformance() {
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

  const conversionData = Object.entries(metrics.conversion_by_method).map(([method, rate]) => ({
    method: METHOD_LABEL[method] || method,
    conversao: Math.round(rate * 1000) / 10,
  }));

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Dashboard de performance</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>Últimos {metrics.period_days} dias · {metrics.total_intents} intenções</p>

      <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
        <StatTile label="Conversão geral" value={`${(metrics.conversion_rate * 100).toFixed(1)}%`} tone="success" />
        <StatTile label="Tempo médio até pagamento" value={`${metrics.avg_time_to_payment_hours.toFixed(1)}h`} />
        <StatTile label="Taxa de fallback" value={`${(metrics.fallback_rate * 100).toFixed(1)}%`} tone={metrics.fallback_rate > 0.15 ? "warning" : undefined} />
        <StatTile label="Retry bem-sucedido" value={`${(metrics.retry_success_rate * 100).toFixed(1)}%`} />
      </div>

      <Card title="Conversão por meio de pagamento">
        {conversionData.length === 0 ? (
          <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Ainda não há tentativas suficientes neste período.</p>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={conversionData}>
              <CartesianGrid strokeDasharray="3 3" stroke={chartColors.border} />
              <XAxis dataKey="method" stroke={chartColors.textMuted} fontSize={12} />
              <YAxis stroke={chartColors.textMuted} fontSize={12} unit="%" />
              <Tooltip
                contentStyle={{ background: chartColors.surface2, border: `1px solid ${chartColors.border}`, borderRadius: 8 }}
                formatter={(v) => [`${v}%`, "Conversão"]}
              />
              <Bar dataKey="conversao" fill={chartColors.accent} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Card>
    </div>
  );
}
