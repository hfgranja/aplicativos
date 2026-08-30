import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_TEACHER = { name: "", email: "", phone: "", subjects: "", status: "ativo" };
const EMPTY_ASSIGNMENT = { teacher_id: "", class_id: "", subject: "" };

export default function Teachers() {
  const [teachers, setTeachers] = useState([]);
  const [classes, setClasses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_TEACHER);
  const [showModal, setShowModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assignForm, setAssignForm] = useState(EMPTY_ASSIGNMENT);

  function loadTeachers() {
    api.get("/teachers").then(setTeachers).catch((err) => setError(err.message));
  }
  function loadAssignments() {
    api.get("/teachers/assignments/all").then(setAssignments).catch((err) => setError(err.message));
  }

  useEffect(() => {
    loadTeachers();
    loadAssignments();
    api.get("/classes").then(setClasses).catch(() => {});
  }, []);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_TEACHER);
    setShowModal(true);
  }

  function openEdit(t) {
    setEditing(t);
    setForm({
      name: t.name,
      email: t.email || "",
      phone: t.phone || "",
      subjects: t.subjects || "",
      status: t.status,
    });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      if (editing) {
        await api.put(`/teachers/${editing.id}`, form);
      } else {
        await api.post("/teachers", form);
      }
      setShowModal(false);
      loadTeachers();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(t) {
    if (!confirm(`Excluir o professor "${t.name}"?`)) return;
    try {
      await api.del(`/teachers/${t.id}`);
      loadTeachers();
      loadAssignments();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleAssignSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/teachers/assignments", assignForm);
      setShowAssignModal(false);
      setAssignForm(EMPTY_ASSIGNMENT);
      loadAssignments();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDeleteAssignment(a) {
    if (!confirm("Remover esta atribuição?")) return;
    try {
      await api.del(`/teachers/assignments/${a.id}`);
      loadAssignments();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Professores</h2>
        <button className="btn" onClick={openCreate}>
          + Novo professor
        </button>
      </div>

      {error && <div className="error-text">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Disciplinas</th>
            <th>Contato</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {teachers.map((t) => (
            <tr key={t.id}>
              <td>{t.name}</td>
              <td>{t.subjects}</td>
              <td>
                {t.email}
                {t.email && t.phone ? " · " : ""}
                {t.phone}
              </td>
              <td>
                <span className={`badge ${t.status}`}>{t.status}</span>
              </td>
              <td>
                <button className="btn secondary small" onClick={() => openEdit(t)}>
                  Editar
                </button>{" "}
                <button className="btn danger small" onClick={() => handleDelete(t)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {teachers.length === 0 && <div className="empty-state">Nenhum professor cadastrado.</div>}

      <div className="page-header" style={{ marginTop: 32 }}>
        <h2>Atribuição de aulas</h2>
        <button className="btn" onClick={() => setShowAssignModal(true)}>
          + Nova atribuição
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>Professor</th>
            <th>Turma</th>
            <th>Disciplina</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((a) => (
            <tr key={a.id}>
              <td>{a.teacher_name}</td>
              <td>{a.class_name}</td>
              <td>{a.subject}</td>
              <td>
                <button className="btn danger small" onClick={() => handleDeleteAssignment(a)}>
                  Remover
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {assignments.length === 0 && <div className="empty-state">Nenhuma atribuição cadastrada.</div>}

      {showModal && (
        <Modal title={editing ? "Editar professor" : "Novo professor"} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Nome completo</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-field">
              <label>Disciplinas (separadas por vírgula)</label>
              <input
                value={form.subjects}
                onChange={(e) => setForm({ ...form, subjects: e.target.value })}
                placeholder="Ex: Matemática, Física"
              />
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>E-mail</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              <div className="form-field">
                <label>Telefone</label>
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
              </div>
            </div>
            <div className="form-field">
              <label>Status</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                <option value="ativo">Ativo</option>
                <option value="afastado">Afastado</option>
                <option value="desligado">Desligado</option>
              </select>
            </div>
            <div className="modal-actions">
              <button type="button" className="btn secondary" onClick={() => setShowModal(false)}>
                Cancelar
              </button>
              <button type="submit" className="btn">
                Salvar
              </button>
            </div>
          </form>
        </Modal>
      )}

      {showAssignModal && (
        <Modal title="Nova atribuição de aula" onClose={() => setShowAssignModal(false)}>
          <form onSubmit={handleAssignSubmit}>
            <div className="form-field">
              <label>Professor</label>
              <select
                value={assignForm.teacher_id}
                onChange={(e) => setAssignForm({ ...assignForm, teacher_id: e.target.value })}
                required
              >
                <option value="">Selecione...</option>
                {teachers.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Turma</label>
              <select
                value={assignForm.class_id}
                onChange={(e) => setAssignForm({ ...assignForm, class_id: e.target.value })}
                required
              >
                <option value="">Selecione...</option>
                {classes.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Disciplina</label>
              <input
                value={assignForm.subject}
                onChange={(e) => setAssignForm({ ...assignForm, subject: e.target.value })}
                required
              />
            </div>
            <div className="modal-actions">
              <button type="button" className="btn secondary" onClick={() => setShowAssignModal(false)}>
                Cancelar
              </button>
              <button type="submit" className="btn">
                Salvar
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
