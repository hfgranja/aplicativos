import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/format.js";

export default function Alerts() {
  const { auth } = useAuth();
  const queryClient = useQueryClient();
  const alertsQuery = useQuery({ queryKey: ["alerts"], queryFn: () => api.listAlerts(auth.token) });

  async function acknowledge(id) {
    await api.acknowledgeAlert(auth.token, id);
    queryClient.invalidateQueries({ queryKey: ["alerts"] });
  }

  return (
    <div>
      <h1>Alertas</h1>
      <p className="page-subtitle">Rule + ML Alert Engine (spec seção 36): chuva, seca, anomalia de NDVI e margem negativa.</p>

      <div className="card">
        {alertsQuery.isLoading && <div className="loading">Carregando…</div>}
        {!alertsQuery.isLoading && !alertsQuery.data?.length && <div className="empty-state">Nenhum alerta no momento.</div>}
        {alertsQuery.data?.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Severidade</th>
                <th>Tipo</th>
                <th>Mensagem</th>
                <th>Disparado em</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {alertsQuery.data.map((alert) => (
                <tr key={alert.id} style={{ opacity: alert.acknowledged ? 0.5 : 1 }}>
                  <td>
                    <span className={`badge badge-${alert.severity}`}>{alert.severity}</span>
                  </td>
                  <td>{alert.kind}</td>
                  <td>
                    <Link to={`/fields/${alert.field_id}`}>{alert.message}</Link>
                  </td>
                  <td>{formatDate(alert.triggered_at)}</td>
                  <td>
                    {!alert.acknowledged && (
                      <button className="btn-secondary" style={{ width: "auto" }} onClick={() => acknowledge(alert.id)}>
                        Reconhecer
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
