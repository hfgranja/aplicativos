const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, { method = "GET", token, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      /* noop */
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),

  listFarms: (token) => request("/farms", { token }),
  getFarm: (token, farmId) => request(`/farms/${farmId}`, { token }),
  getFarmHealth: (token, farmId) => request(`/farms/${farmId}/health`, { token }),
  listFarmFields: (token, farmId) => request(`/farms/${farmId}/fields`, { token }),
  createFarm: (token, payload) => request("/farms", { method: "POST", token, body: payload }),

  createField: (token, payload) => request("/fields", { method: "POST", token, body: payload }),
  importFields: (token, payload) => request("/fields/import", { method: "POST", token, body: payload }),
  getField: (token, fieldId) => request(`/fields/${fieldId}`, { token }),
  getFieldAnalysis: (token, fieldId) => request(`/fields/${fieldId}/analysis`, { token }),
  getFieldSatellite: (token, fieldId) => request(`/fields/${fieldId}/satellite`, { token }),
  getFieldWeather: (token, fieldId) => request(`/fields/${fieldId}/weather`, { token }),
  getFieldSoil: (token, fieldId) => request(`/fields/${fieldId}/soil`, { token }),
  getFieldYieldForecast: (token, fieldId) => request(`/fields/${fieldId}/yield-forecast`, { token }),
  getFieldProfitability: (token, fieldId) => request(`/fields/${fieldId}/profitability`, { token }),
  getFieldRecommendations: (token, fieldId) => request(`/fields/${fieldId}/recommendations`, { token }),

  createScenario: (token, payload) => request("/scenarios", { method: "POST", token, body: payload }),
  listScenarios: (token, fieldId) => request(`/scenarios/${fieldId}`, { token }),

  listAlerts: (token) => request("/alerts", { token }),
  acknowledgeAlert: (token, alertId) => request(`/alerts/${alertId}/acknowledge`, { method: "POST", token }),

  importSoilSample: (token, payload) => request("/data/soil/import", { method: "POST", token, body: payload }),
  importYieldRecord: (token, payload) => request("/data/yield/import", { method: "POST", token, body: payload }),
  importOperation: (token, payload) => request("/data/operations/import", { method: "POST", token, body: payload }),
};
