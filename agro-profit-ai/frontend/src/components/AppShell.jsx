import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Visão executiva", end: true },
  { to: "/map", label: "Mapa de fazendas" },
  { to: "/data", label: "Dados da fazenda" },
  { to: "/alerts", label: "Alertas" },
];

export default function AppShell({ children }) {
  const { auth, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">AP</span>
          <div>
            <div className="brand-name">Agro Profit AI</div>
            <div className="brand-tagline">decisão econômica geoespacial</div>
          </div>
        </div>
        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-name">{auth?.fullName}</div>
          <div className="user-role">{auth?.role}</div>
          <button className="btn-secondary" onClick={logout}>
            Sair
          </button>
        </div>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}
