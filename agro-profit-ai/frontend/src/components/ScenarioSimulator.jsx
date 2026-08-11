import { useState } from "react";
import { api } from "../api/client.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatCurrency, formatNumber } from "../utils/format.js";

const DEFAULT_INPUTS = {
  fertilizer_dose_delta_pct: 0,
  irrigation_mm_delta: 0,
  planting_date_shift_days: 0,
  seed_population_delta_pct: 0,
  intervention_cost_per_ha: 0,
  expected_rainfall_delta_pct: 0,
  yield_response_pct: 0,
};

export default function ScenarioSimulator({ field }) {
  const { auth } = useAuth();
  const [inputs, setInputs] = useState(DEFAULT_INPUTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function update(key, value) {
    setInputs((prev) => ({ ...prev, [key]: Number(value) }));
  }

  async function runSimulation() {
    setLoading(true);
    setError(null);
    try {
      const scenario = await api.createScenario(auth.token, { field_id: field.id, name: "Cenário what-if", ...inputs });
      setResult(scenario);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card-row">
      <div className="card">
        <h2>Simulação what-if</h2>
        <p className="muted" style={{ fontSize: 12, marginTop: -8 }}>
          Altere premissas de manejo e compare Baseline vs. Cenário (spec seção 25).
        </p>

        <div className="form-grid">
          <label>
            Δ Dose de fertilizante (%)
            <input
              type="number"
              value={inputs.fertilizer_dose_delta_pct * 100}
              onChange={(e) => update("fertilizer_dose_delta_pct", e.target.value / 100)}
            />
          </label>
          <label>
            Δ Irrigação (mm)
            <input type="number" value={inputs.irrigation_mm_delta} onChange={(e) => update("irrigation_mm_delta", e.target.value)} />
          </label>
          <label>
            Deslocamento data plantio (dias)
            <input
              type="number"
              value={inputs.planting_date_shift_days}
              onChange={(e) => update("planting_date_shift_days", e.target.value)}
            />
          </label>
          <label>
            Δ População de plantas (%)
            <input
              type="number"
              value={inputs.seed_population_delta_pct * 100}
              onChange={(e) => update("seed_population_delta_pct", e.target.value / 100)}
            />
          </label>
          <label>
            Δ Chuva esperada (%)
            <input
              type="number"
              value={inputs.expected_rainfall_delta_pct * 100}
              onChange={(e) => update("expected_rainfall_delta_pct", e.target.value / 100)}
            />
          </label>
          <label>
            Resposta agronômica esperada (%)
            <input
              type="number"
              value={inputs.yield_response_pct * 100}
              onChange={(e) => update("yield_response_pct", e.target.value / 100)}
            />
          </label>
          <label>
            Custo da intervenção (R$/ha)
            <input
              type="number"
              value={inputs.intervention_cost_per_ha}
              onChange={(e) => update("intervention_cost_per_ha", e.target.value)}
            />
          </label>
        </div>

        <button className="btn-primary" onClick={runSimulation} disabled={loading}>
          {loading ? "Simulando…" : "Rodar simulação (Monte Carlo, 1000 cenários)"}
        </button>
        {error && <p className="login-error">{error}</p>}
      </div>

      <div className="card">
        <h2>Resultado</h2>
        {!result ? (
          <div className="empty-state">Configure as premissas e rode a simulação.</div>
        ) : (
          <>
            <div className="kpi-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
              <div className="kpi-card">
                <div className="kpi-label">Margem baseline/ha</div>
                <div className="kpi-value">{formatCurrency(result.baseline_margin_per_ha)}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Margem cenário/ha</div>
                <div className="kpi-value">{formatCurrency(result.scenario_margin_per_ha)}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Margem incremental/ha</div>
                <div className={`kpi-value ${result.incremental_margin_per_ha >= 0 ? "positive" : "negative"}`}>
                  {formatCurrency(result.incremental_margin_per_ha)}
                </div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">ROI</div>
                <div className="kpi-value">{result.roi !== null ? `${formatNumber(result.roi * 100, 0)}%` : "—"}</div>
              </div>
            </div>

            <h2 style={{ marginTop: 20 }}>Monte Carlo (1000 simulações)</h2>
            <table>
              <tbody>
                <tr>
                  <td>P5 margem/ha</td>
                  <td>{formatCurrency(result.monte_carlo.p5_margin_per_ha)}</td>
                </tr>
                <tr>
                  <td>P50 margem/ha</td>
                  <td>{formatCurrency(result.monte_carlo.p50_margin_per_ha)}</td>
                </tr>
                <tr>
                  <td>P95 margem/ha</td>
                  <td>{formatCurrency(result.monte_carlo.p95_margin_per_ha)}</td>
                </tr>
                <tr>
                  <td>Probabilidade de lucro</td>
                  <td>{formatNumber(result.monte_carlo.probability_of_profit * 100, 0)}%</td>
                </tr>
                <tr>
                  <td>Probabilidade de ROI positivo</td>
                  <td>{formatNumber(result.monte_carlo.probability_of_positive_intervention_roi * 100, 0)}%</td>
                </tr>
                <tr>
                  <td>Break-even (preço)</td>
                  <td>R$ {formatNumber(result.break_even_price, 2)}/kg</td>
                </tr>
                <tr>
                  <td>Break-even (produtividade)</td>
                  <td>{formatNumber(result.break_even_yield, 0)} kg/ha</td>
                </tr>
              </tbody>
            </table>
          </>
        )}
      </div>
    </div>
  );
}
