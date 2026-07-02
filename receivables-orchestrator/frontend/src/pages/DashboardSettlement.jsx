import { useEffect, useState } from "react";
import api from "../api/client.js";
import { Badge, Card, EmptyState, ErrorBanner, Spinner, StatTile } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

export default function DashboardSettlement() {
  const { merchantId, apiKey } = useMerchant();
  const [settlements, setSettlements] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!merchantId || !apiKey) return;
    api.getSettlements(apiKey, merchantId).then(setSettlements).catch((e) => setError(e.message));
  }, [merchantId, apiKey]);

  if (!settlements) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  const now = new Date();
  const pending = settlements.filter((s) => !s.settled_at).length;
  const late = settlements.filter((s) => s.expected_settlement_at && new Date(s.expected_settlement_at) < now && !s.settled_at).length;
  const totalNet = settlements.reduce((sum, s) => sum + s.net_amount, 0);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Dashboard de liquidação</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>Valores a liquidar, liquidados e atrasados.</p>

      <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
        <StatTile label="Valor líquido liquidado" value={`R$ ${totalNet.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`} tone="success" />
        <StatTile label="Pendentes" value={pending} />
        <StatTile label="Atrasadas vs. SLA" value={late} tone={late > 0 ? "danger" : undefined} />
      </div>

      <Card title="Liquidações">
        {settlements.length === 0 ? (
          <EmptyState>Nenhuma liquidação registrada ainda.</EmptyState>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Bruto</th>
                <th>Taxa</th>
                <th>Líquido</th>
                <th>Previsão</th>
                <th>Liquidado em</th>
                <th>Conciliação</th>
              </tr>
            </thead>
            <tbody>
              {settlements.map((s) => (
                <tr key={s.id}>
                  <td className="mono">{s.id}</td>
                  <td className="mono">R$ {s.gross_amount.toFixed(2)}</td>
                  <td className="mono">R$ {s.fee.toFixed(2)}</td>
                  <td className="mono">R$ {s.net_amount.toFixed(2)}</td>
                  <td>{s.expected_settlement_at ? new Date(s.expected_settlement_at).toLocaleString("pt-BR") : "—"}</td>
                  <td>{s.settled_at ? new Date(s.settled_at).toLocaleString("pt-BR") : "—"}</td>
                  <td>
                    <Badge tone={s.reconciled ? "low" : "high"}>{s.reconciled ? "conciliado" : "exceção"}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
