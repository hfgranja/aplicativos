import { useEffect, useState } from "react";
import api from "../api/client.js";
import { Badge, Card, EmptyState, ErrorBanner, Spinner, StatTile } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

export default function DashboardReconciliation() {
  const { merchantId, apiKey } = useMerchant();
  const [settlements, setSettlements] = useState(null);
  const [error, setError] = useState(null);
  const [resolving, setResolving] = useState(null);

  function load() {
    api.getSettlements(apiKey, merchantId).then(setSettlements).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!merchantId || !apiKey) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [merchantId, apiKey]);

  if (!settlements) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  const exceptions = settlements.filter((s) => !s.reconciled);
  const autoRate = settlements.length ? 1 - exceptions.length / settlements.length : 1;

  async function resolve(settlementId) {
    setResolving(settlementId);
    try {
      await api.resolveException(apiKey, settlementId);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setResolving(null);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Dashboard de conciliação</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>Matching automático entre tentativas confirmadas e liquidações.</p>

      <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
        <StatTile label="Taxa de conciliação automática" value={`${(autoRate * 100).toFixed(1)}%`} tone="success" />
        <StatTile label="Exceções em aberto" value={exceptions.length} tone={exceptions.length > 0 ? "warning" : undefined} />
      </div>

      <Card title="Fila de exceções">
        {exceptions.length === 0 ? (
          <EmptyState>Nenhuma exceção de conciliação em aberto — tudo casado automaticamente.</EmptyState>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Liquidação</th>
                <th>Valor bruto</th>
                <th>Divergência</th>
                <th>Ação</th>
              </tr>
            </thead>
            <tbody>
              {exceptions.map((s) => (
                <tr key={s.id}>
                  <td className="mono">{s.id}</td>
                  <td className="mono">R$ {s.gross_amount.toFixed(2)}</td>
                  <td className="mono">
                    <Badge tone="high">R$ {s.discrepancy_amount.toFixed(2)}</Badge>
                  </td>
                  <td>
                    <button onClick={() => resolve(s.id)} disabled={resolving === s.id}>
                      {resolving === s.id ? "Resolvendo…" : "Aprovar ajuste manual"}
                    </button>
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
