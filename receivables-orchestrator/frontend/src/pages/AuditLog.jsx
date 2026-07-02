import { useEffect, useState } from "react";
import api from "../api/client.js";
import { Badge, Card, EmptyState, ErrorBanner, Spinner } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

export default function AuditLog() {
  const { apiKey } = useMerchant();
  const [logs, setLogs] = useState(null);
  const [chainValid, setChainValid] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!apiKey) return;
    api.listAuditLog(apiKey).then(setLogs).catch((e) => setError(e.message));
  }, [apiKey]);

  async function verify() {
    const res = await api.verifyAuditChain(apiKey);
    setChainValid(res.chain_valid);
  }

  if (!logs) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Auditoria</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20 }}>
        Log imutável com cadeia de hash — qualquer adulteração retroativa quebra a cadeia.
      </p>

      <Card
        title="Verificação de integridade"
        action={<button onClick={verify}>Verificar cadeia de hash</button>}
        style={{ marginBottom: 20 }}
      >
        {chainValid === null && <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Ainda não verificado nesta sessão.</p>}
        {chainValid !== null && (
          <Badge tone={chainValid ? "low" : "high"}>{chainValid ? "cadeia íntegra" : "cadeia comprometida"}</Badge>
        )}
      </Card>

      <Card title="Eventos recentes">
        {logs.length === 0 ? (
          <EmptyState>Nenhum evento registrado ainda.</EmptyState>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Quando</th>
                <th>Ator</th>
                <th>Ação</th>
                <th>Entidade</th>
                <th>Hash</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{new Date(l.timestamp).toLocaleString("pt-BR")}</td>
                  <td className="mono">{l.actor}</td>
                  <td>{l.action}</td>
                  <td className="mono">
                    {l.entity_type}:{l.entity_id}
                  </td>
                  <td className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                    {l.hash.slice(0, 12)}…
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
