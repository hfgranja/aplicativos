const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, { method = "GET", apiKey, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (apiKey) headers["X-Api-Key"] = apiKey;

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
  listMerchants: () => request("/merchants"),
  listCustomers: (merchantId, apiKey) => request(`/merchants/${merchantId}/customers`, { apiKey }),
  getPolicy: (merchantId, apiKey) => request(`/merchants/${merchantId}/policy`, { apiKey }),
  updatePolicy: (merchantId, apiKey, payload) =>
    request(`/merchants/${merchantId}/policy`, { method: "PUT", apiKey, body: payload }),

  createIntent: (apiKey, payload) => request("/receivables/intents", { method: "POST", apiKey, body: payload }),
  listIntents: (apiKey) => request("/receivables/intents", { apiKey }),
  getRecommendation: (apiKey, intentId) => request(`/receivables/intents/${intentId}/recommendation`, { apiKey }),
  executeIntent: (apiKey, intentId, payload) =>
    request(`/receivables/intents/${intentId}/execute`, { method: "POST", apiKey, body: payload }),
  getStatus: (apiKey, intentId) => request(`/receivables/intents/${intentId}/status`, { apiKey }),
  retryIntent: (apiKey, intentId) => request(`/receivables/intents/${intentId}/retry`, { method: "POST", apiKey }),
  applyFallback: (apiKey, intentId) => request(`/receivables/intents/${intentId}/fallback`, { method: "POST", apiKey }),
  getExplanation: (apiKey, intentId) => request(`/receivables/intents/${intentId}/explanation`, { apiKey }),

  getMetrics: (apiKey, merchantId, period = 30) =>
    request(`/receivables/metrics?merchant_id=${merchantId}&period=${period}`, { apiKey }),
  getSettlements: (apiKey, merchantId, period = 30) =>
    request(`/receivables/settlements?merchant_id=${merchantId}&period=${period}`, { apiKey }),
  resolveException: (apiKey, settlementId) =>
    request(`/receivables/settlements/${settlementId}/resolve-exception`, { method: "POST", apiKey }),

  listAuditLog: (apiKey, entityId) =>
    request(`/receivables/audit-log${entityId ? `?entity_id=${entityId}` : ""}`, { apiKey }),
  verifyAuditChain: (apiKey) => request("/receivables/audit-log/verify", { apiKey }),

  listAlerts: (apiKey) => request("/receivables/alerts", { apiKey }),
  acknowledgeAlert: (apiKey, alertId) => request(`/receivables/alerts/${alertId}/acknowledge`, { method: "POST", apiKey }),
};

export default api;
