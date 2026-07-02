import { NavLink } from "react-router-dom";
import { useMerchant } from "../../context/MerchantContext.jsx";

const NAV = [
  { to: "/", label: "Nova Intenção", exact: true },
  { to: "/intents", label: "Intenções" },
  { to: "/policy", label: "Política do Estabelecimento" },
  { to: "/dashboard/performance", label: "Dashboard · Performance" },
  { to: "/dashboard/cost", label: "Dashboard · Custo" },
  { to: "/dashboard/settlement", label: "Dashboard · Liquidação" },
  { to: "/dashboard/reconciliation", label: "Dashboard · Conciliação" },
  { to: "/alerts", label: "Alertas Operacionais" },
  { to: "/audit", label: "Auditoria" },
];

export default function AppShell({ children }) {
  const { merchants, merchant, merchantId, setMerchantId, loading, error } = useMerchant();

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside
        style={{
          width: 250,
          borderRight: "1px solid var(--border)",
          background: "var(--surface)",
          padding: "20px 16px",
          display: "flex",
          flexDirection: "column",
          gap: 18,
        }}
      >
        <div>
          <div style={{ fontWeight: 700, fontSize: 15, letterSpacing: "-0.01em" }}>Receivables Orchestrator</div>
          <div style={{ fontSize: 11.5, color: "var(--text-muted)", marginTop: 2 }}>Motor Inteligente de Recebimentos</div>
        </div>

        <div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
            Estabelecimento
          </div>
          <select
            value={merchantId}
            onChange={(e) => setMerchantId(e.target.value)}
            style={{ width: "100%" }}
            disabled={loading || !merchants.length}
          >
            {merchants.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name}
              </option>
            ))}
          </select>
          {merchant && (
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 6 }}>{merchant.segment}</div>
          )}
        </div>

        <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.exact}
              style={({ isActive }) => ({
                padding: "8px 10px",
                borderRadius: 8,
                fontSize: 13.5,
                textDecoration: "none",
                color: isActive ? "var(--text)" : "var(--text-muted)",
                background: isActive ? "var(--surface-2)" : "transparent",
                fontWeight: isActive ? 600 : 400,
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        {error && <div style={{ fontSize: 12, color: "var(--danger)" }}>Erro ao conectar à API: {error}</div>}
      </aside>

      <main style={{ flex: 1, padding: "28px 32px", maxWidth: 1200 }}>{children}</main>
    </div>
  );
}
