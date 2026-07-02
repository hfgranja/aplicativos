import { useEffect, useState } from "react";
import api from "../api/client.js";
import { Card, ErrorBanner, Field, Spinner } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

const DIMENSIONS = [
  { key: "conversion", label: "Conversão" },
  { key: "cost", label: "Custo" },
  { key: "risk", label: "Risco" },
  { key: "liquidity", label: "Liquidez" },
  { key: "experience", label: "Experiência" },
  { key: "preference", label: "Preferência do cliente" },
];

const METHODS = [
  { value: "pix", label: "Pix" },
  { value: "credit_card", label: "Cartão de crédito" },
  { value: "boleto", label: "Boleto" },
];

const MODES = [
  { value: "recommendation", label: "Recomendação — IA sugere, humano aprova" },
  { value: "assisted", label: "Assistido — executa dentro de regras pré-aprovadas" },
  { value: "automatic", label: "Automático — decide e executa com limites" },
  { value: "conservative", label: "Conservador — só atua com alta confiança" },
];

export default function PolicyConfig() {
  const { merchantId, apiKey } = useMerchant();
  const [policy, setPolicy] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!merchantId || !apiKey) return;
    api.getPolicy(merchantId, apiKey).then(setPolicy).catch((e) => setError(e.message));
  }, [merchantId, apiKey]);

  function updateWeight(key, value) {
    setPolicy((p) => ({ ...p, weights: { ...p.weights, [key]: parseFloat(value) } }));
  }

  function toggleMethod(method) {
    setPolicy((p) => ({
      ...p,
      allowed_methods: p.allowed_methods.includes(method)
        ? p.allowed_methods.filter((m) => m !== method)
        : [...p.allowed_methods, method],
    }));
  }

  async function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.updatePolicy(merchantId, apiKey, policy);
      setPolicy(updated);
      setSaved(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  if (!policy) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  const weightSum = Object.values(policy.weights).reduce((a, b) => a + b, 0);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Política do estabelecimento</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20, maxWidth: 640 }}>
        Define os pesos do motor de scoring, o modo de operação e os limites de exposição para todas as novas
        intenções deste estabelecimento.
      </p>

      <ErrorBanner message={error} />

      <form onSubmit={handleSave} style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 680 }}>
        <Card title="Pesos por dimensão" subtitle={`Soma atual: ${(weightSum * 100).toFixed(0)}% (não precisa somar 100% — é normalizado)`}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {DIMENSIONS.map((d) => (
              <div key={d.key} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span style={{ width: 160, fontSize: 13 }}>{d.label}</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  value={policy.weights[d.key]}
                  onChange={(e) => updateWeight(d.key, e.target.value)}
                  style={{ flex: 1 }}
                />
                <span className="mono" style={{ width: 44, fontSize: 12.5 }}>
                  {(policy.weights[d.key] * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </Card>

        <Card title="Modo de operação">
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {MODES.map((m) => (
              <label key={m.value} style={{ display: "flex", gap: 8, fontSize: 13, alignItems: "center" }}>
                <input
                  type="radio"
                  name="mode"
                  checked={policy.operation_mode === m.value}
                  onChange={() => setPolicy({ ...policy, operation_mode: m.value })}
                />
                {m.label}
              </label>
            ))}
          </div>

          {policy.operation_mode !== "recommendation" && (
            <div style={{ marginTop: 14 }}>
              <Field label="Confiança mínima para execução automática">
                <input
                  type="range"
                  min="0.5"
                  max="0.99"
                  step="0.01"
                  value={policy.confidence_threshold}
                  onChange={(e) => setPolicy({ ...policy, confidence_threshold: parseFloat(e.target.value) })}
                />
                <span className="mono" style={{ fontSize: 12.5 }}>{(policy.confidence_threshold * 100).toFixed(0)}%</span>
              </Field>
            </div>
          )}
        </Card>

        <Card title="Limites e meios habilitados">
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <Field label="Exposição financeira máxima em execução automática (R$)">
              <input
                type="number"
                value={policy.max_exposure}
                onChange={(e) => setPolicy({ ...policy, max_exposure: parseFloat(e.target.value) })}
              />
            </Field>
            <Field label="Meios de pagamento habilitados">
              <div style={{ display: "flex", gap: 14 }}>
                {METHODS.map((m) => (
                  <label key={m.value} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                    <input
                      type="checkbox"
                      checked={policy.allowed_methods.includes(m.value)}
                      onChange={() => toggleMethod(m.value)}
                    />
                    {m.label}
                  </label>
                ))}
              </div>
            </Field>
          </div>
        </Card>

        <div>
          <button type="submit" className="primary" disabled={saving}>
            {saving ? "Salvando…" : "Salvar política"}
          </button>
          {saved && <span style={{ marginLeft: 12, color: "var(--success)", fontSize: 13 }}>Política salva.</span>}
        </div>
      </form>
    </div>
  );
}
