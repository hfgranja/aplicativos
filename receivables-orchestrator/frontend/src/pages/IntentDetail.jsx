import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../api/client.js";
import { Badge, Card, ErrorBanner, Spinner } from "../components/shared/ui.jsx";
import { useMerchant } from "../context/MerchantContext.jsx";

const TABS = [
  { key: "recommendation", label: "Recomendação" },
  { key: "explanation", label: "Explicação da decisão" },
  { key: "attempts", label: "Acompanhar tentativas" },
];

const METHOD_LABEL = { pix: "Pix", credit_card: "Cartão de crédito", boleto: "Boleto" };

const IN_FLIGHT_STATUSES = new Set(["created", "scored", "awaiting_payment"]);
const RETRIABLE_STATUSES = new Set(["payment_failed"]);

export default function IntentDetail() {
  const { intentId } = useParams();
  const { apiKey } = useMerchant();
  const [tab, setTab] = useState("recommendation");

  const [recommendation, setRecommendation] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [error, setError] = useState(null);
  const [executing, setExecuting] = useState(false);
  const [selectedMethod, setSelectedMethod] = useState(null);

  const loadAll = useCallback(async () => {
    try {
      const [rec, status] = await Promise.all([
        api.getRecommendation(apiKey, intentId),
        api.getStatus(apiKey, intentId),
      ]);
      setRecommendation(rec);
      setTimeline(status);
      if (!selectedMethod && rec.recommended_method) setSelectedMethod(rec.recommended_method);
    } catch (e) {
      setError(e.message);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiKey, intentId]);

  useEffect(() => {
    if (!apiKey) return;
    loadAll();
  }, [apiKey, intentId, loadAll]);

  // polling enquanto a intencao esta em fluxo (aguardando pagamento etc.)
  useEffect(() => {
    if (!apiKey || !timeline) return;
    const status = timeline.intent.status;
    if (!IN_FLIGHT_STATUSES.has(status) && status !== "awaiting_payment") return;
    const interval = setInterval(loadAll, 2000);
    return () => clearInterval(interval);
  }, [apiKey, timeline, loadAll]);

  useEffect(() => {
    if (tab === "explanation" && apiKey && !explanation) {
      api.getExplanation(apiKey, intentId).then(setExplanation).catch((e) => setError(e.message));
    }
  }, [tab, apiKey, intentId, explanation]);

  async function handleExecute() {
    setExecuting(true);
    setError(null);
    try {
      await api.executeIntent(apiKey, intentId, { approved_route: selectedMethod, approved_by: "user_demo" });
      await loadAll();
    } catch (e) {
      setError(e.message);
    } finally {
      setExecuting(false);
    }
  }

  async function handleRetry() {
    setError(null);
    try {
      await api.retryIntent(apiKey, intentId);
      await loadAll();
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleFallback() {
    setError(null);
    try {
      await api.applyFallback(apiKey, intentId);
      await loadAll();
    } catch (e) {
      setError(e.message);
    }
  }

  if (!recommendation || !timeline) {
    return (
      <div>
        <ErrorBanner message={error} />
        <Spinner />
      </div>
    );
  }

  const intent = timeline.intent;
  const canExecute = intent.status === "scored";
  const canRetry = RETRIABLE_STATUSES.has(intent.status) && timeline.routes.length > 0;
  const canFallback = RETRIABLE_STATUSES.has(intent.status) && timeline.routes.length > 0;

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }} className="mono">
        {intent.id}
      </h1>
      <p style={{ color: "var(--text-muted)", marginBottom: 16 }}>
        R$ {intent.amount.toFixed(2)} · até {new Date(intent.due_date).toLocaleDateString("pt-BR")} · objetivo:{" "}
        {intent.objective}
      </p>

      <div style={{ marginBottom: 18 }}>
        <Badge tone={intent.status.includes("fail") ? "high" : intent.status.includes("settl") || intent.status === "confirmed" ? "low" : "medium"}>
          {intent.status}
        </Badge>
      </div>

      <ErrorBanner message={error} />

      <div style={{ display: "flex", gap: 4, marginBottom: 18, borderBottom: "1px solid var(--border)" }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            className="ghost"
            onClick={() => setTab(t.key)}
            style={{
              borderRadius: 0,
              border: "none",
              borderBottom: tab === t.key ? "2px solid var(--accent)" : "2px solid transparent",
              background: "transparent",
              fontWeight: tab === t.key ? 600 : 400,
              color: tab === t.key ? "var(--text)" : "var(--text-muted)",
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "recommendation" && (
        <Card title="Ranking de opções" subtitle={`Modo de operação: ${recommendation.operation_mode}`}>
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Meio</th>
                <th>Score</th>
                <th>Confiança</th>
                <th>Conversão esp.</th>
                <th>Custo esp.</th>
                <th>Liquidação</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {recommendation.options.map((o) => (
                <tr key={o.method} style={{ opacity: o.eligible ? 1 : 0.45 }}>
                  <td>{o.rank || "—"}</td>
                  <td>
                    <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      {o.eligible && canExecute && (
                        <input
                          type="radio"
                          name="method"
                          checked={selectedMethod === o.method}
                          onChange={() => setSelectedMethod(o.method)}
                        />
                      )}
                      {METHOD_LABEL[o.method] || o.method}
                    </label>
                  </td>
                  <td className="mono">{o.score != null ? o.score.toFixed(3) : "—"}</td>
                  <td className="mono">{o.confidence != null ? `${(o.confidence * 100).toFixed(0)}%` : "—"}</td>
                  <td className="mono">{(o.estimated_conversion * 100).toFixed(0)}%</td>
                  <td className="mono">{o.estimated_cost_pct.toFixed(2)}%</td>
                  <td className="mono">{o.estimated_settlement_hours.toFixed(0)}h</td>
                  <td>{o.eligible ? <Badge tone="low">elegível</Badge> : <span style={{ fontSize: 12 }}>{o.exclusion_reason}</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {canExecute && (
            <div style={{ marginTop: 18 }}>
              <button className="primary" onClick={handleExecute} disabled={executing || !selectedMethod}>
                {executing ? "Executando…" : `Aprovar e cobrar via ${METHOD_LABEL[selectedMethod] || selectedMethod}`}
              </button>
            </div>
          )}
          {!canExecute && intent.status !== "no_eligible_option" && (
            <p style={{ color: "var(--text-muted)", fontSize: 13, marginTop: 14 }}>
              Esta intenção já foi executada ou está em outro estágio — veja a aba "Acompanhar tentativas".
            </p>
          )}
        </Card>
      )}

      {tab === "explanation" && (
        <Card title="Por que esta decisão?">
          {!explanation && <Spinner />}
          {explanation && (
            <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
              <p>{explanation.reason_summary}</p>

              <div>
                <h4 style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>Pesos aplicados</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {Object.entries(explanation.weights_applied).map(([dim, w]) => (
                    <div key={dim} style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      <span style={{ width: 110, fontSize: 12.5, color: "var(--text-muted)" }}>{dim}</span>
                      <div style={{ flex: 1, background: "var(--surface-2)", borderRadius: 4, height: 8 }}>
                        <div
                          style={{
                            width: `${w * 100}%`,
                            background: "var(--accent)",
                            height: 8,
                            borderRadius: 4,
                          }}
                        />
                      </div>
                      <span className="mono" style={{ fontSize: 12, width: 36 }}>
                        {(w * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>Opções descartadas</h4>
                {explanation.discarded_options.length === 0 && <p style={{ fontSize: 13 }}>Nenhuma outra opção elegível.</p>}
                {explanation.discarded_options.map((d) => (
                  <div key={d.method} style={{ fontSize: 13, marginBottom: 4 }}>
                    <strong>{METHOD_LABEL[d.method] || d.method}:</strong> {d.reason}
                  </div>
                ))}
              </div>

              <div>
                <h4 style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 8 }}>Explicação por público</h4>
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {explanation.audiences.map((a) => (
                    <div key={a.audience} style={{ background: "var(--surface-2)", borderRadius: 8, padding: 12 }}>
                      <div style={{ fontSize: 11, textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 4 }}>
                        {a.audience}
                      </div>
                      <div style={{ fontSize: 13 }}>{a.text}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </Card>
      )}

      {tab === "attempts" && (
        <Card
          title="Linha do tempo de tentativas"
          action={
            <div style={{ display: "flex", gap: 8 }}>
              {canRetry && (
                <button onClick={handleRetry}>Forçar novo retry</button>
              )}
              {canFallback && (
                <button onClick={handleFallback}>Aplicar fallback</button>
              )}
            </div>
          }
        >
          {timeline.routes.length === 0 && <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Nenhuma rota executada ainda.</p>}
          {timeline.routes.map((route) => (
            <div key={route.id} style={{ marginBottom: 18, paddingBottom: 14, borderBottom: "1px solid var(--border)" }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                <strong>{METHOD_LABEL[route.chosen_method] || route.chosen_method}</strong>
                <Badge tone={route.status === "confirmed" ? "low" : route.status === "failed" ? "high" : "medium"}>
                  {route.status}
                </Badge>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  hop #{route.hop_index} · acionado por {route.triggered_by}
                </span>
              </div>
              {route.attempts.map((a) => (
                <div key={a.id} className="mono" style={{ fontSize: 12.5, display: "flex", gap: 12, padding: "4px 0" }}>
                  <span>tentativa {a.attempt_number}</span>
                  <Badge tone={a.status === "confirmed" ? "low" : a.status === "failed" ? "high" : "medium"}>{a.status}</Badge>
                  {a.failure_reason && <span style={{ color: "var(--danger)" }}>{a.failure_reason}</span>}
                  <span style={{ color: "var(--text-muted)" }}>{new Date(a.created_at).toLocaleTimeString("pt-BR")}</span>
                </div>
              ))}
            </div>
          ))}
        </Card>
      )}
    </div>
  );
}
