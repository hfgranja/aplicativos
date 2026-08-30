import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_FORM = { name: "", grade_level: "", shift: "manhã", school_year: new Date().getFullYear() };

export default function Classes() {
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showModal, setShowModal] = useState(false);

  function load() {
    api
      .get("/classes")
      .then(setClasses)
      .catch((err) => setError(err.message));
  }

  useEffect(load, []);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  function openEdit(c) {
    setEditing(c);
    setForm({
      name: c.name,
      grade_level: c.grade_level || "",
      shift: c.shift || "manhã",
      school_year: c.school_year,
    });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      if (editing) {
        await api.put(`/classes/${editing.id}`, form);
      } else {
        await api.post("/classes", form);
      }
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(c) {
    if (!confirm(`Excluir a turma "${c.name}"? Alunos vinculados perderão a turma.`)) return;
    try {
      await api.del(`/classes/${c.id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Turmas</h2>
        <button className="btn" onClick={openCreate}>
          + Nova turma
        </button>
      </div>

      {error && <div className="error-text">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>Série/ano</th>
            <th>Turno</th>
            <th>Ano letivo</th>
            <th>Alunos</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {classes.map((c) => (
            <tr key={c.id}>
              <td>{c.name}</td>
              <td>{c.grade_level}</td>
              <td>{c.shift}</td>
              <td>{c.school_year}</td>
              <td>{c.student_count}</td>
              <td>
                <button className="btn secondary small" onClick={() => openEdit(c)}>
                  Editar
                </button>{" "}
                <button className="btn danger small" onClick={() => handleDelete(c)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {classes.length === 0 && <div className="empty-state">Nenhuma turma cadastrada.</div>}

      {showModal && (
        <Modal title={editing ? "Editar turma" : "Nova turma"} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Nome da turma</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Ex: 6º A"
                required
              />
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Série/ano</label>
                <input
                  value={form.grade_level}
                  onChange={(e) => setForm({ ...form, grade_level: e.target.value })}
                  placeholder="Ex: 6º ano EF"
                />
              </div>
              <div className="form-field">
                <label>Turno</label>
                <select value={form.shift} onChange={(e) => setForm({ ...form, shift: e.target.value })}>
                  <option value="manhã">Manhã</option>
                  <option value="tarde">Tarde</option>
                  <option value="noite">Noite</option>
                </select>
              </div>
            </div>
            <div className="form-field">
              <label>Ano letivo</label>
              <input
                type="number"
                value={form.school_year}
                onChange={(e) => setForm({ ...form, school_year: Number(e.target.value) })}
              />
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
    </div>
  );
}
