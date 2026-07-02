import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client.js";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

const STATUS_TONE = {
  created: "info",
  scored: "info",
  awaiting_payment: "medium",
  confirmed: "low",
  settled: "low",
  settled_pending_reconciliation: "medium",
  payment_failed: "high",
  failed: "high",
  no_eligible_option: "high",
};

export default function IntentsList() {
  const { apiKey, merchantId } = useMerchant();
  const [intents, setIntents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!apiKey) return;
    setLoading(true);
    api
      .listIntents(apiKey)
      .then(setIntents)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [apiKey, merchantId]);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Intenções de recebimento</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>Histórico de intenções criadas para este estabelecimento.</p>

      <ErrorBanner message={error} />

      <Card>
        {loading && <Spinner />}
        {!loading && intents.length === 0 && <EmptyState>Nenhuma intenção criada ainda.</EmptyState>}
        {!loading && intents.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Valor</th>
                <th>Prazo</th>
                <th>Objetivo</th>
                <th>Status</th>
                <th>Criada em</th>
              </tr>
            </thead>
            <tbody>
              {intents.map((i) => (
                <tr key={i.id}>
                  <td>
                    <Link to={`/intents/${i.id}`} className="mono" style={{ color: "var(--accent)" }}>
                      {i.id}
                    </Link>
                  </td>
                  <td className="mono">R$ {i.amount.toFixed(2)}</td>
                  <td>{new Date(i.due_date).toLocaleDateString("pt-BR")}</td>
                  <td>{i.objective}</td>
                  <td>
                    <Badge tone={STATUS_TONE[i.status] || "info"}>{i.status}</Badge>
                  </td>
                  <td>{new Date(i.created_at).toLocaleString("pt-BR")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
