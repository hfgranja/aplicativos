import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_FORM = { title: "", body: "", class_id: "" };

export default function Announcements() {
  const [announcements, setAnnouncements] = useState([]);
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [showModal, setShowModal] = useState(false);

  function load() {
    api
      .get("/announcements")
      .then(setAnnouncements)
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    load();
    api.get("/classes").then(setClasses);
  }, []);

  function openCreate() {
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/announcements", { ...form, class_id: form.class_id || null });
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(a) {
    if (!confirm(`Excluir o comunicado "${a.title}"?`)) return;
    try {
      await api.del(`/announcements/${a.id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Comunicados</h2>
        <button className="btn" onClick={openCreate}>
          + Novo comunicado
        </button>
      </div>

      {error && <div className="error-text">{error}</div>}

      {announcements.length === 0 && <div className="empty-state">Nenhum comunicado publicado.</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {announcements.map((a) => (
          <div className="card" key={a.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <strong>{a.title}</strong>
                <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {a.class_name ? `Turma: ${a.class_name}` : "Geral"} · por {a.created_by_name} ·{" "}
                  {new Date(a.created_at).toLocaleDateString("pt-BR")}
                </div>
              </div>
              <button className="btn danger small" onClick={() => handleDelete(a)}>
                Excluir
              </button>
            </div>
            <p style={{ marginBottom: 0 }}>{a.body}</p>
          </div>
        ))}
      </div>

      {showModal && (
        <Modal title="Novo comunicado" onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Título</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
            </div>
            <div className="form-field">
              <label>Destinatário</label>
              <select value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })}>
                <option value="">Geral (toda a escola)</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>
                    Turma: {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Mensagem</label>
              <textarea
                rows={4}
                value={form.body}
                onChange={(e) => setForm({ ...form, body: e.target.value })}
                required
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn secondary" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
              <button type="submit" className="btn">
                Publicar
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
