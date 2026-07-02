import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client.js";
import { Card, ErrorBanner, Field } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

const OBJECTIVES = [
  { value: "balanced", label: "Balanceada" },
  { value: "maximize_conversion", label: "Maximizar conversão" },
  { value: "minimize_cost", label: "Minimizar custo" },
  { value: "minimize_risk", label: "Minimizar risco" },
  { value: "maximize_liquidity", label: "Maximizar liquidez" },
  { value: "maximize_experience", label: "Maximizar experiência" },
];

const METHODS = [
  { value: "pix", label: "Pix" },
  { value: "credit_card", label: "Cartão de crédito" },
  { value: "boleto", label: "Boleto" },
];

export default function CreateIntent() {
  const { merchantId, apiKey } = useMerchant();
  const navigate = useNavigate();

  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState({
    customer_id: "",
    amount: "1500.00",
    due_date: new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10),
    objective: "balanced",
    forbidden: [],
    max_cost: "",
    max_risk: "medium",
    liquidity_need: "standard",
  });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!merchantId || !apiKey) return;
    api
      .listCustomers(merchantId, apiKey)
      .then((list) => {
        setCustomers(list);
        setForm((f) => ({ ...f, customer_id: f.customer_id || list[0]?.id || "" }));
      })
      .catch((e) => setError(e.message));
  }, [merchantId, apiKey]);

  function toggleForbidden(method) {
    setForm((f) => ({
      ...f,
      forbidden: f.forbidden.includes(method) ? f.forbidden.filter((m) => m !== method) : [...f.forbidden, method],
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const intent = await api.createIntent(apiKey, {
        merchant_id: merchantId,
        customer_id: form.customer_id,
        amount: parseFloat(form.amount),
        due_date: `${form.due_date}T00:00:00`,
        objective: form.objective,
        allowed_payment_methods: [],
        forbidden_payment_methods: form.forbidden,
        max_cost: form.max_cost ? parseFloat(form.max_cost) : null,
        max_risk: form.max_risk,
        liquidity_need: form.liquidity_need,
      });
      navigate(`/intents/${intent.id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Nova intenção de recebimento</h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 20, maxWidth: 620 }}>
        Declare o que você precisa receber — o motor decide o melhor caminho entre Pix, cartão e boleto.
      </p>

      <ErrorBanner message={error} />

      <Card style={{ maxWidth: 620 }}>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <Field label="Cliente">
            <select
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              required
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} · {c.segment}
                </option>
              ))}
            </select>
          </Field>

          <div style={{ display: "flex", gap: 12 }}>
            <Field label="Valor (R$)" hint="Quanto você precisa receber">
              <input
                type="number"
                step="0.01"
                min="1"
                value={form.amount}
                onChange={(e) => setForm({ ...form, amount: e.target.value })}
                required
              />
            </Field>
            <Field label="Receber até">
              <input
                type="date"
                value={form.due_date}
                onChange={(e) => setForm({ ...form, due_date: e.target.value })}
                required
              />
            </Field>
          </div>

          <Field label="Objetivo" hint="Prioridade que orienta os pesos do motor de decisão">
            <select value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })}>
              {OBJECTIVES.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </Field>

          <Field label="Meios proibidos" hint="O motor nunca vai considerar estas opções">
            <div style={{ display: "flex", gap: 14 }}>
              {METHODS.map((m) => (
                <label key={m.value} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
                  <input
                    type="checkbox"
                    checked={form.forbidden.includes(m.value)}
                    onChange={() => toggleForbidden(m.value)}
                  />
                  {m.label}
                </label>
              ))}
            </div>
          </Field>

          <div style={{ display: "flex", gap: 12 }}>
            <Field label="Custo máximo (%)" hint="Opcional — exclui opções acima deste custo">
              <input
                type="number"
                step="0.1"
                placeholder="ex: 3.5"
                value={form.max_cost}
                onChange={(e) => setForm({ ...form, max_cost: e.target.value })}
              />
            </Field>
            <Field label="Risco máximo aceitável">
              <select value={form.max_risk} onChange={(e) => setForm({ ...form, max_risk: e.target.value })}>
                <option value="low">Baixo</option>
                <option value="medium">Médio</option>
                <option value="high">Alto</option>
              </select>
            </Field>
            <Field label="Necessidade de caixa">
              <select
                value={form.liquidity_need}
                onChange={(e) => setForm({ ...form, liquidity_need: e.target.value })}
              >
                <option value="urgent">Urgente</option>
                <option value="standard">Padrão</option>
                <option value="flexible">Flexível</option>
              </select>
            </Field>
          </div>

          <button type="submit" className="primary" disabled={submitting || !form.customer_id}>
            {submitting ? "Calculando recomendação…" : "Criar intenção e ver recomendação"}
          </button>
        </form>
      </Card>
    </div>
  );
}
