import { NavLink, Outlet, Navigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Painel", end: true },
  { to: "/alunos", label: "Alunos" },
  { to: "/turmas", label: "Turmas" },
  { to: "/professores", label: "Professores" },
  { to: "/frequencia", label: "Frequência" },
  { to: "/notas", label: "Notas" },
  { to: "/ocorrencias", label: "Ocorrências" },
  { to: "/comunicados", label: "Comunicados" },
];

export default function Layout() {
  const { user, loading, logout } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>Gestão Escolar</h1>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="user-box">
          <div>{user.name}</div>
          <div style={{ opacity: 0.7 }}>{user.role}</div>
          <button onClick={logout}>Sair</button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
