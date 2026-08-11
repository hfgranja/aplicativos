import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { GeoJSON, MapContainer, TileLayer } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { useFarmFieldIds } from "../hooks/useFarmFieldIds.js";
import { formatCurrency } from "../utils/format.js";

const RISK_COLOR = {
  normal: "#5fd67d",
  watch: "#e6b04a",
  high: "#e2604f",
  critical: "#8f2a1e",
};

function marginColor(marginPerHa) {
  if (marginPerHa === null || marginPerHa === undefined) return "#5b6a60";
  if (marginPerHa < 0) return "#8f2a1e";
  if (marginPerHa < 800) return "#e6b04a";
  if (marginPerHa < 2500) return "#7fd68f";
  return "#5fd67d";
}

export default function FarmMap() {
  const { auth } = useAuth();
  const navigate = useNavigate();
  const [farmId, setFarmId] = useState(null);
  const [mode, setMode] = useState("profitability"); // profitability | risk

  const farmsQuery = useQuery({ queryKey: ["farms"], queryFn: () => api.listFarms(auth.token) });
  useEffect(() => {
    if (!farmId && farmsQuery.data?.length) setFarmId(farmsQuery.data[0].id);
  }, [farmsQuery.data, farmId]);

  const fieldsQuery = useFarmFieldIds(farmId);
  const farm = farmsQuery.data?.find((f) => f.id === farmId);

  const fieldStats = useFieldStats(fieldsQuery.data);

  if (farmsQuery.isLoading) return <div className="loading">Carregando…</div>;
  if (!farm) return <div className="empty-state">Nenhuma fazenda cadastrada.</div>;

  const center = [farm.centroid_lat || -15.7, farm.centroid_lon || -47.9];

  return (
    <div>
      <h1>Mapa de fazendas</h1>
      <p className="page-subtitle">Cada talhão é colorido por margem de contribuição ou nível de risco (spec seção 32).</p>

      <div className="tag-row">
        {farmsQuery.data.map((f) => (
          <button key={f.id} className={`tab-button${f.id === farmId ? " active" : ""}`} onClick={() => setFarmId(f.id)}>
            {f.name}
          </button>
        ))}
        <span style={{ width: 1, background: "var(--border)" }} />
        <button className={`tab-button${mode === "profitability" ? " active" : ""}`} onClick={() => setMode("profitability")}>
          Rentabilidade
        </button>
        <button className={`tab-button${mode === "risk" ? " active" : ""}`} onClick={() => setMode("risk")}>
          Risco
        </button>
      </div>

      <div className="map-container">
        <MapContainer center={center} zoom={13} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {fieldsQuery.data?.map((field) => {
            const stat = fieldStats[field.id];
            const color =
              mode === "profitability"
                ? marginColor(stat?.profitability?.contribution_margin_per_ha)
                : RISK_COLOR[stat?.analysis?.prediction?.risk_level] || "#5b6a60";
            return (
              <GeoJSON
                key={field.id}
                data={field.boundary_geojson}
                style={{ color, weight: 2, fillColor: color, fillOpacity: 0.45 }}
                eventHandlers={{ click: () => navigate(`/fields/${field.id}`) }}
              >
              </GeoJSON>
            );
          })}
        </MapContainer>
      </div>

      <div className="legend">
        {mode === "profitability" ? (
          <>
            <span>
              <span className="legend-swatch" style={{ background: "#8f2a1e" }} /> Margem negativa
            </span>
            <span>
              <span className="legend-swatch" style={{ background: "#e6b04a" }} /> Margem baixa
            </span>
            <span>
              <span className="legend-swatch" style={{ background: "#7fd68f" }} /> Margem moderada
            </span>
            <span>
              <span className="legend-swatch" style={{ background: "#5fd67d" }} /> Margem alta
            </span>
          </>
        ) : (
          Object.entries(RISK_COLOR).map(([level, color]) => (
            <span key={level}>
              <span className="legend-swatch" style={{ background: color }} /> {level}
            </span>
          ))
        )}
      </div>

      <div className="card" style={{ marginTop: 20 }}>
        <h2>Talhões da fazenda</h2>
        <table>
          <thead>
            <tr>
              <th>Talhão</th>
              <th>Cultura</th>
              <th>Área (ha)</th>
              <th>Margem/ha</th>
              <th>Risco</th>
            </tr>
          </thead>
          <tbody>
            {fieldsQuery.data?.map((field) => {
              const stat = fieldStats[field.id];
              return (
                <tr key={field.id} onClick={() => navigate(`/fields/${field.id}`)} style={{ cursor: "pointer" }}>
                  <td>{field.name}</td>
                  <td>{field.crop}</td>
                  <td>{field.area_ha}</td>
                  <td>{formatCurrency(stat?.profitability?.contribution_margin_per_ha)}</td>
                  <td>
                    {stat?.analysis?.prediction?.risk_level && (
                      <span className={`badge badge-${stat.analysis.prediction.risk_level}`}>
                        {stat.analysis.prediction.risk_level}
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function useFieldStats(fields) {
  const { auth } = useAuth();
  const [stats, setStats] = useState({});

  useEffect(() => {
    if (!fields?.length) return;
    let cancelled = false;
    (async () => {
      const entries = await Promise.all(
        fields.map(async (field) => {
          const [profitability, analysis] = await Promise.all([
            api.getFieldProfitability(auth.token, field.id),
            api.getFieldAnalysis(auth.token, field.id),
          ]);
          return [field.id, { profitability, analysis }];
        }),
      );
      if (!cancelled) setStats(Object.fromEntries(entries));
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fields, auth.token]);

  return stats;
}
