import { useEffect, useState } from "react";
import api from "../api/client.js";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

export default function Alerts() {
  const { merchantId, apiKey } = useMerchant();
  const [alerts, setAlerts] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    api.listAlerts(apiKey).then(setAlerts).catch((e) => setError(e.message));
  }

  useEffect(() => {
    if (!apiKey) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey, merchantId]);

  async function ack(id) {
    await api.acknowledgeAlert(apiKey, id);
    load();
  }

  if (!alerts) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Alertas operacionais</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>
        Decisões de baixa confiança, exceções de conciliação, opções sem elegibilidade e falhas de provedor.
      </p>

      <Card>
        {alerts.length === 0 ? (
          <EmptyState>Nenhum alerta no momento.</EmptyState>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {alerts.map((a) => (
              <div
                key={a.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "10px 14px",
                  borderRadius: 8,
                  background: "var(--surface-2)",
                  opacity: a.acknowledged ? 0.5 : 1,
                }}
              >
                <div>
                  <div style={{ display: "flex", gap: 8, marginBottom: 4 }}>
                    <Badge tone={a.severity}>{a.severity}</Badge>
                    <Badge tone="info">{a.category}</Badge>
                  </div>
                  <div style={{ fontSize: 13 }}>{a.message}</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    {new Date(a.created_at).toLocaleString("pt-BR")}
                  </div>
                </div>
                {!a.acknowledged && <button onClick={() => ack(a.id)}>Reconhecer</button>}
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
