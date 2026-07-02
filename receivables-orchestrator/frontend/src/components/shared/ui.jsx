export function Card({ title, subtitle, action, children, style }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: 20,
        ...style,
      }}
    >
      {(title || action) && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
          <div>
            {title && <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{title}</h3>}
            {subtitle && <p style={{ margin: "4px 0 0", fontSize: 12.5, color: "var(--text-muted)" }}>{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

const SEVERITY_COLORS = {
  low: "var(--success)",
  medium: "var(--warning)",
  high: "var(--danger)",
  info: "var(--accent-2)",
  warning: "var(--warning)",
  critical: "var(--danger)",
};

export function Badge({ children, tone = "info" }) {
  const color = SEVERITY_COLORS[tone] || "var(--accent)";
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        fontSize: 11.5,
        fontWeight: 600,
        padding: "3px 9px",
        borderRadius: 999,
        color,
        background: `${color}22`,
        border: `1px solid ${color}55`,
        textTransform: "uppercase",
        letterSpacing: "0.03em",
      }}
    >
      {children}
    </span>
  );
}

export function StatTile({ label, value, sub, tone }) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "16px 18px",
        flex: 1,
        minWidth: 160,
      }}
    >
      <div style={{ fontSize: 11.5, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
        {label}
      </div>
      <div
        className="mono"
        style={{ fontSize: 26, fontWeight: 700, marginTop: 6, color: tone ? `var(--${tone})` : "var(--text)" }}
      >
        {value}
      </div>
      {sub && <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

export function EmptyState({ children }) {
  return (
    <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--text-muted)", fontSize: 13.5 }}>
      {children}
    </div>
  );
}

export function ErrorBanner({ message }) {
  if (!message) return null;
  return (
    <div
      style={{
        background: "rgba(255,77,109,0.12)",
        border: "1px solid var(--danger)",
        color: "var(--danger)",
        borderRadius: 8,
        padding: "10px 14px",
        fontSize: 13,
        marginBottom: 14,
      }}
    >
      {message}
    </div>
  );
}

export function Field({ label, children, hint }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 13 }}>
      <span style={{ color: "var(--text-muted)", fontWeight: 500 }}>{label}</span>
      {children}
      {hint && <span style={{ fontSize: 11.5, color: "var(--text-muted)" }}>{hint}</span>}
    </label>
  );
}

export function Spinner() {
  return <div style={{ color: "var(--text-muted)", fontSize: 13 }}>Carregando…</div>;
}
