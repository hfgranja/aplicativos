import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import { useParams } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatCurrency, formatDate, formatNumber } from "../utils/format.js";
import PhenologyTimeline from "../components/PhenologyTimeline.jsx";
import ScenarioSimulator from "../components/ScenarioSimulator.jsx";
import WaterBalanceChart from "../components/WaterBalanceChart.jsx";
import YieldGapPanel from "../components/YieldGapPanel.jsx";

const TABS = ["Visão geral", "Manejo & Fenologia", "Clima & Satélite", "Solo", "Recomendações", "Simulador what-if"];

export default function FieldDetail() {
  const { fieldId } = useParams();
  const { auth } = useAuth();
  const [tab, setTab] = useState(TABS[0]);

  const fieldQuery = useQuery({ queryKey: ["field", fieldId], queryFn: () => api.getField(auth.token, fieldId) });
  const analysisQuery = useQuery({ queryKey: ["field-analysis", fieldId], queryFn: () => api.getFieldAnalysis(auth.token, fieldId) });
  const profitabilityQuery = useQuery({
    queryKey: ["field-profitability", fieldId],
    queryFn: () => api.getFieldProfitability(auth.token, fieldId),
  });
  const weatherQuery = useQuery({ queryKey: ["field-weather", fieldId], queryFn: () => api.getFieldWeather(auth.token, fieldId) });
  const satelliteQuery = useQuery({ queryKey: ["field-satellite", fieldId], queryFn: () => api.getFieldSatellite(auth.token, fieldId) });
  const soilQuery = useQuery({ queryKey: ["field-soil", fieldId], queryFn: () => api.getFieldSoil(auth.token, fieldId) });
  const recsQuery = useQuery({
    queryKey: ["field-recommendations", fieldId],
    queryFn: () => api.getFieldRecommendations(auth.token, fieldId),
  });

  if (fieldQuery.isLoading || !fieldQuery.data) return <div className="loading">Carregando talhão…</div>;
  const field = fieldQuery.data;
  const prediction = analysisQuery.data?.prediction;

  return (
    <div>
      <h1>{field.name}</h1>
      <p className="page-subtitle">
        {field.crop} · safra {field.season} · {formatNumber(field.area_ha, 1)} ha · plantio {formatDate(field.planting_date)}
      </p>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-label">Produtividade esperada</div>
          <div className="kpi-value">{prediction ? `${formatNumber(prediction.yield_expected_kg_ha, 0)} kg/ha` : "…"}</div>
          {prediction && (
            <div className="muted" style={{ fontSize: 11, marginTop: 4 }}>
              P10 {formatNumber(prediction.yield_p10_kg_ha, 0)} · P90 {formatNumber(prediction.yield_p90_kg_ha, 0)}
            </div>
          )}
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Margem de contribuição/ha</div>
          <div className={`kpi-value ${profitabilityQuery.data?.contribution_margin_per_ha < 0 ? "negative" : "positive"}`}>
            {profitabilityQuery.data ? formatCurrency(profitabilityQuery.data.contribution_margin_per_ha) : "…"}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Margem total esperada</div>
          <div className="kpi-value">{profitabilityQuery.data ? formatCurrency(profitabilityQuery.data.total_expected_margin) : "…"}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Confiança da previsão</div>
          <div className="kpi-value">
            {analysisQuery.data ? (
              <>
                {formatNumber(analysisQuery.data.confidence_score, 0)}{" "}
                <span className={`badge badge-${analysisQuery.data.confidence_tier?.toLowerCase()}`}>
                  {analysisQuery.data.confidence_tier}
                </span>
              </>
            ) : (
              "…"
            )}
          </div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Risco</div>
          <div className="kpi-value">
            {prediction && <span className={`badge badge-${prediction.risk_level}`}>{prediction.risk_level}</span>}
          </div>
        </div>
      </div>

      <div className="tag-row">
        {TABS.map((t) => (
          <button key={t} className={`tab-button${tab === t ? " active" : ""}`} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      {tab === "Visão geral" && (
        <div className="card-row">
          <div className="card">
            <h2>Localização</h2>
            <div className="field-map-small">
              <MapContainer center={[field.centroid_lat, field.centroid_lon]} zoom={15} style={{ height: "100%", width: "100%" }}>
                <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                <GeoJSON data={field.boundary_geojson} style={{ color: "#5fd67d", weight: 2, fillOpacity: 0.25 }} />
              </MapContainer>
            </div>
          </div>
          <div className="card">
            <h2>Por que essa previsão? (SHAP)</h2>
            <ShapExplanation shap={prediction?.shap_explanation} />
          </div>
        </div>
      )}

      {tab === "Manejo & Fenologia" && (
        <>
          <div className="card">
            <h2>Estágio fenológico ({analysisQuery.data?.phenology?.crop_label || field.crop})</h2>
            <PhenologyTimeline phenology={analysisQuery.data?.phenology} />
          </div>
          <div className="card">
            <h2>Balanço hídrico da cultura (FAO-56)</h2>
            <WaterBalanceInline fieldId={field.id} />
          </div>
          <div className="card">
            <h2>Yield gap — onde estão os kg/ha que faltam</h2>
            <YieldGapPanel yieldGap={analysisQuery.data?.yield_gap} />
          </div>
        </>
      )}

      {tab === "Clima & Satélite" && (
        <div className="card-row">
          <div className="card">
            <h2>Chuva diária (últimos registros)</h2>
            <RainChart data={weatherQuery.data} />
          </div>
          <div className="card">
            <h2>Histórico de NDVI</h2>
            <NdviChart data={satelliteQuery.data} />
            {satelliteQuery.data?.some((s) => s.is_synthetic) && (
              <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
                Imagens sem credenciais Copernicus configuradas — série sintética exibida para desenvolvimento (nunca
                apresentada como observação real).
              </p>
            )}
          </div>
        </div>
      )}

      {tab === "Solo" && (
        <div className="card">
          <h2>Perfil de solo</h2>
          <SoilTable samples={soilQuery.data} />
        </div>
      )}

      {tab === "Recomendações" && (
        <div className="card">
          <h2>Recomendações priorizadas por valor econômico esperado</h2>
          <RecommendationsTable recs={recsQuery.data} />
          <p className="muted" style={{ fontSize: 11, marginTop: 12 }}>
            Recomendação analítica (Decision Support). Validar com responsável agronômico antes da execução — spec seção 29.
          </p>
        </div>
      )}

      {tab === "Simulador what-if" && <ScenarioSimulator field={field} />}
    </div>
  );
}

function WaterBalanceInline({ fieldId }) {
  const { auth } = useAuth();
  const waterQuery = useQuery({
    queryKey: ["field-water-balance", fieldId],
    queryFn: () => api.getFieldWaterBalance(auth.token, fieldId),
  });
  if (waterQuery.isLoading) return <div className="loading">Calculando ET0/ETc…</div>;
  return <WaterBalanceChart waterBalance={waterQuery.data} />;
}

function ShapExplanation({ shap }) {
  if (!shap?.length) return <div className="empty-state">Sem explicação disponível ainda.</div>;
  const max = Math.max(...shap.map((s) => Math.abs(s.contribution_kg_ha)));
  return (
    <div>
      {shap.map((s) => {
        const pct = (Math.abs(s.contribution_kg_ha) / max) * 100;
        const positive = s.contribution_kg_ha >= 0;
        return (
          <div className="shap-bar-row" key={s.feature}>
            <span className="muted">{s.label}</span>
            <div className="shap-bar-track">
              <div
                className="shap-bar-fill"
                style={{
                  width: `${pct}%`,
                  left: positive ? "50%" : `${50 - pct / 2}%`,
                  background: positive ? "#5fd67d" : "#e2604f",
                }}
              />
            </div>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>
              {positive ? "+" : ""}
              {formatNumber(s.contribution_kg_ha, 0)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function RainChart({ data }) {
  if (!data?.length) return <div className="loading">Carregando…</div>;
  const chartData = data.slice(-45).map((d) => ({ date: formatDate(d.date), chuva: d.precipitation_mm || 0 }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a372f" />
        <XAxis dataKey="date" hide />
        <YAxis stroke="#9fb0a5" fontSize={11} />
        <Tooltip contentStyle={{ background: "#1d2922", border: "1px solid #2a372f" }} />
        <Bar dataKey="chuva" fill="#4a9fe6" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function NdviChart({ data }) {
  if (!data?.length) return <div className="loading">Carregando…</div>;
  const chartData = data.map((d) => ({ date: formatDate(d.date), ndvi: d.ndvi }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a372f" />
        <XAxis dataKey="date" hide />
        <YAxis domain={[0, 1]} stroke="#9fb0a5" fontSize={11} />
        <Tooltip contentStyle={{ background: "#1d2922", border: "1px solid #2a372f" }} />
        <Line type="monotone" dataKey="ndvi" stroke="#5fd67d" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function SoilTable({ samples }) {
  if (!samples?.length) return <div className="empty-state">Sem amostras de solo.</div>;
  return (
    <table>
      <thead>
        <tr>
          <th>Amostra</th>
          <th>Fonte</th>
          <th>Data</th>
          <th>pH</th>
          <th>M.O.</th>
          <th>Argila %</th>
          <th>CTC</th>
        </tr>
      </thead>
      <tbody>
        {samples.map((s) => (
          <tr key={s.sample_id + s.created_at}>
            <td>{s.sample_id}</td>
            <td>
              <span className={`badge ${s.source === "laboratory" ? "badge-action" : "badge-monitor"}`}>{s.source}</span>
            </td>
            <td>{formatDate(s.sample_date)}</td>
            <td>{s.ph}</td>
            <td>{s.organic_matter}</td>
            <td>{s.clay}</td>
            <td>{s.cec}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function RecommendationsTable({ recs }) {
  if (!recs?.length) return <div className="empty-state">Nenhuma recomendação em aberto.</div>;
  return (
    <table>
      <thead>
        <tr>
          <th>Prioridade</th>
          <th>Problema</th>
          <th>Ação sugerida</th>
          <th>Custo/ha</th>
          <th>Δ Margem/ha</th>
          <th>ROI</th>
          <th>Confiança</th>
          <th>Decisão</th>
        </tr>
      </thead>
      <tbody>
        {recs.map((r) => (
          <tr key={r.id}>
            <td>
              <span className={`badge badge-${r.priority}`}>{r.priority}</span>
            </td>
            <td>
              {r.issue}
              <div className="muted" style={{ fontSize: 11 }}>
                {r.evidence?.join(" · ")}
              </div>
            </td>
            <td>{r.suggested_action}</td>
            <td>{formatCurrency(r.estimated_cost_per_ha)}</td>
            <td>{formatCurrency(r.expected_margin_delta_per_ha)}</td>
            <td>{r.expected_roi ? `${formatNumber(r.expected_roi * 100, 0)}%` : "—"}</td>
            <td>{formatNumber(r.confidence, 0)}</td>
            <td>
              <span className={`badge badge-${r.decision.toLowerCase()}`}>{r.decision}</span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
