import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useFarmFieldIds } from "../hooks/useFarmFieldIds.js";
import { formatCurrency, formatNumber } from "../utils/format.js";

function kpiTone(value) {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "";
}

export default function Dashboard() {
  const { auth } = useAuth();
  const [farmId, setFarmId] = useState(null);

  const farmsQuery = useQuery({
    queryKey: ["farms"],
    queryFn: () => api.listFarms(auth.token),
  });

  useEffect(() => {
    if (!farmId && farmsQuery.data?.length) setFarmId(farmsQuery.data[0].id);
  }, [farmsQuery.data, farmId]);

  const healthQuery = useQuery({
    queryKey: ["farm-health", farmId],
    queryFn: () => api.getFarmHealth(auth.token, farmId),
    enabled: Boolean(farmId),
  });

  if (farmsQuery.isLoading) return <div className="loading">Carregando fazendas…</div>;
  if (!farmsQuery.data?.length) {
    return (
      <div>
        <h1>Visão executiva</h1>
        <p className="page-subtitle">Nenhuma fazenda cadastrada ainda.</p>
      </div>
    );
  }

  const health = healthQuery.data;

  return (
    <div>
      <h1>Visão executiva</h1>
      <p className="page-subtitle">
        Responde em segundos: quanto devo produzir, quanto devo faturar, qual a margem esperada, onde está o risco e o que
        fazer primeiro (spec seção 68).
      </p>

      {farmsQuery.data.length > 1 && (
        <div className="tag-row">
          {farmsQuery.data.map((f) => (
            <button key={f.id} className={`tab-button${f.id === farmId ? " active" : ""}`} onClick={() => setFarmId(f.id)}>
              {f.name}
            </button>
          ))}
        </div>
      )}

      {healthQuery.isLoading && <div className="loading">Calculando previsão, risco e margem para todos os talhões…</div>}

      {health && (
        <>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-label">Farm Health Score</div>
              <div
                className={`kpi-value ${health.farm_health_score >= 70 ? "positive" : health.farm_health_score >= 40 ? "warning" : "negative"}`}
              >
                {formatNumber(health.farm_health_score, 0)}
              </div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Produtividade esperada</div>
              <div className="kpi-value">{formatNumber(health.expected_yield_kg_ha, 0)} kg/ha</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Faturamento esperado</div>
              <div className="kpi-value">{formatCurrency(health.expected_revenue)}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Margem esperada</div>
              <div className={`kpi-value ${kpiTone(health.expected_margin)}`}>{formatCurrency(health.expected_margin)}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Área em risco</div>
              <div className="kpi-value warning">{formatNumber(health.area_at_risk_ha, 1)} ha</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Perda potencial</div>
              <div className="kpi-value negative">{formatCurrency(health.potential_economic_loss)}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Margem recuperável</div>
              <div className="kpi-value positive">{formatCurrency(health.potential_recoverable_margin)}</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-label">Risco climático</div>
              <div className="kpi-value">
                <span className={`badge badge-${health.weather_risk}`}>{health.weather_risk}</span>
              </div>
            </div>
          </div>

          <div className="card-row">
            <div className="card">
              <h2>Talhões</h2>
              <p className="muted" style={{ fontSize: 12, marginTop: -8, marginBottom: 12 }}>
                {health.fields_count} talhão(ões) · {health.open_recommendations} recomendação(ões) de ação ·{" "}
                {health.open_alerts} alerta(s) aberto(s)
              </p>
              <FieldsList farmId={farmId} />
            </div>
            <div className="card">
              <h2>O que fazer primeiro</h2>
              <TopRecommendations farmId={farmId} />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function FieldsList({ farmId }) {
  const fieldsQuery = useFarmFieldIds(farmId);

  if (fieldsQuery.isLoading) return <div className="loading">Carregando…</div>;
  if (!fieldsQuery.data?.length) return <div className="empty-state">Nenhum talhão cadastrado.</div>;

  return (
    <div>
      {fieldsQuery.data.map((field) => (
        <FieldRow key={field.id} field={field} />
      ))}
    </div>
  );
}

function FieldRow({ field }) {
  const { auth } = useAuth();
  const analysisQuery = useQuery({
    queryKey: ["field-analysis", field.id],
    queryFn: () => api.getFieldAnalysis(auth.token, field.id),
  });

  const risk = analysisQuery.data?.prediction?.risk_level;

  return (
    <Link className="field-list-item" to={`/fields/${field.id}`}>
      <span>
        {field.name} <span className="muted">· {field.crop}</span>
      </span>
      <span>
        {analysisQuery.isLoading ? (
          <span className="muted">…</span>
        ) : (
          <>
            <span className="muted" style={{ marginRight: 10 }}>
              {formatNumber(analysisQuery.data?.prediction?.yield_expected_kg_ha, 0)} kg/ha
            </span>
            {risk && <span className={`badge badge-${risk}`}>{risk}</span>}
          </>
        )}
      </span>
    </Link>
  );
}

function TopRecommendations({ farmId }) {
  const fieldsQuery = useFarmFieldIds(farmId);
  const { auth } = useAuth();

  const recsQuery = useQuery({
    queryKey: ["top-recs", farmId, fieldsQuery.data?.map((f) => f.id).join(",")],
    queryFn: async () => {
      const lists = await Promise.all(fieldsQuery.data.map((f) => api.getFieldRecommendations(auth.token, f.id)));
      return lists
        .flat()
        .map((r) => ({ ...r, fieldName: fieldsQuery.data.find((f) => f.id === r.field_id)?.name }))
        .sort((a, b) => b.expected_margin_delta_per_ha - a.expected_margin_delta_per_ha)
        .slice(0, 5);
    },
    enabled: Boolean(fieldsQuery.data?.length),
  });

  if (fieldsQuery.isLoading || recsQuery.isLoading) return <div className="loading">Carregando…</div>;
  if (!recsQuery.data?.length) return <div className="empty-state">Nenhuma recomendação de alto valor no momento.</div>;

  return (
    <table>
      <thead>
        <tr>
          <th>Talhão</th>
          <th>Ação</th>
          <th>ROI</th>
          <th>Decisão</th>
        </tr>
      </thead>
      <tbody>
        {recsQuery.data.map((r) => (
          <tr key={r.id}>
            <td>
              <Link to={`/fields/${r.field_id}`}>{r.fieldName}</Link>
            </td>
            <td>{r.suggested_action}</td>
            <td>{r.expected_roi ? `${formatNumber(r.expected_roi * 100, 0)}%` : "—"}</td>
            <td>
              <span className={`badge badge-${r.decision.toLowerCase()}`}>{r.decision}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
