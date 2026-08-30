import { useEffect, useState } from "react";
import { api } from "../api";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/dashboard")
      .then(setStats)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="error-text">{error}</div>;
  if (!stats) return <div className="empty-state">Carregando...</div>;

  return (
    <div>
      <div className="page-header">
        <h2>Painel</h2>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="label">Alunos ativos</div>
          <div className="value">{stats.total_students_active}</div>
        </div>
        <div className="stat-card">
          <div className="label">Professores ativos</div>
          <div className="value">{stats.total_teachers_active}</div>
        </div>
        <div className="stat-card">
          <div className="label">Turmas</div>
          <div className="value">{stats.total_classes}</div>
        </div>
        <div className="stat-card">
          <div className="label">Frequência hoje</div>
          <div className="value">
            {stats.attendance_rate_today != null ? `${stats.attendance_rate_today}%` : "—"}
          </div>
        </div>
      </div>

      <div className="form-grid">
        <div className="card">
          <h3>Ocorrências recentes</h3>
          {stats.recent_occurrences.length === 0 && (
            <div className="empty-state">Nenhuma ocorrência registrada.</div>
          )}
          {stats.recent_occurrences.map((o) => (
            <div key={o.id} style={{ marginBottom: 10 }}>
              <strong>{o.student_name}</strong>{" "}
              <span className={`badge ${o.type === "disciplinar" ? "evadido" : "ativo"}`}>
                {o.type}
              </span>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                {o.date} — {o.description}
              </div>
            </div>
          ))}
        </div>

        <div className="card">
          <h3>Comunicados recentes</h3>
          {stats.recent_announcements.length === 0 && (
            <div className="empty-state">Nenhum comunicado publicado.</div>
          )}
          {stats.recent_announcements.map((a) => (
            <div key={a.id} style={{ marginBottom: 10 }}>
              <strong>{a.title}</strong>
              <div style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
                {a.class_name ? `Turma: ${a.class_name}` : "Geral"} — {a.body}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
