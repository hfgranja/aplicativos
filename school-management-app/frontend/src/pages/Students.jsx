import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_FORM = {
  name: "",
  ra: "",
  birth_date: "",
  class_id: "",
  status: "ativo",
  guardian_name: "",
  guardian_phone: "",
  guardian_email: "",
  address: "",
  notes: "",
};

export default function Students() {
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [showModal, setShowModal] = useState(false);
  const [filterClass, setFilterClass] = useState("");
  const [search, setSearch] = useState("");

  function load() {
    const params = new URLSearchParams();
    if (filterClass) params.set("class_id", filterClass);
    if (search) params.set("search", search);
    api
      .get(`/students?${params.toString()}`)
      .then(setStudents)
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    api.get("/classes").then(setClasses).catch(() => {});
  }, []);

  useEffect(load, [filterClass, search]);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY_FORM);
    setShowModal(true);
  }

  function openEdit(s) {
    setEditing(s);
    setForm({
      name: s.name,
      ra: s.ra || "",
      birth_date: s.birth_date || "",
      class_id: s.class_id || "",
      status: s.status,
      guardian_name: s.guardian_name || "",
      guardian_phone: s.guardian_phone || "",
      guardian_email: s.guardian_email || "",
      address: s.address || "",
      notes: s.notes || "",
    });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const payload = { ...form, class_id: form.class_id || null, birth_date: form.birth_date || null };
    try {
      if (editing) {
        await api.put(`/students/${editing.id}`, payload);
      } else {
        await api.post("/students", payload);
      }
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(s) {
    if (!confirm(`Excluir o aluno "${s.name}"? Todo o histórico será removido.`)) return;
    try {
      await api.del(`/students/${s.id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Alunos</h2>
        <button className="btn" onClick={openCreate}>
          + Novo aluno
        </button>
      </div>

      <div className="toolbar">
        <input placeholder="Buscar por nome..." value={search} onChange={(e) => setSearch(e.target.value)} />
        <select value={filterClass} onChange={(e) => setFilterClass(e.target.value)}>
          <option value="">Todas as turmas</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="error-text">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>Nome</th>
            <th>RA</th>
            <th>Turma</th>
            <th>Responsável</th>
            <th>Contato</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.id}>
              <td>{s.name}</td>
              <td>{s.ra}</td>
              <td>{s.class_name || "—"}</td>
              <td>{s.guardian_name}</td>
              <td>{s.guardian_phone}</td>
              <td>
                <span className={`badge ${s.status}`}>{s.status}</span>
              </td>
              <td>
                <button className="btn secondary small" onClick={() => openEdit(s)}>
                  Editar
                </button>{" "}
                <button className="btn danger small" onClick={() => handleDelete(s)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {students.length === 0 && <div className="empty-state">Nenhum aluno encontrado.</div>}

      {showModal && (
        <Modal title={editing ? "Editar aluno" : "Novo aluno"} onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Nome completo</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>RA</label>
                <input value={form.ra} onChange={(e) => setForm({ ...form, ra: e.target.value })} />
              </div>
              <div className="form-field">
                <label>Data de nascimento</label>
                <input
                  type="date"
                  value={form.birth_date}
                  onChange={(e) => setForm({ ...form, birth_date: e.target.value })}
                />
              </div>
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Turma</label>
                <select value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })}>
                  <option value="">Sem turma</option>
                  {classes.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label>Status</label>
                <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                  <option value="ativo">Ativo</option>
                  <option value="transferido">Transferido</option>
                  <option value="evadido">Evadido</option>
                </select>
              </div>
            </div>
            <div className="form-field">
              <label>Nome do responsável</label>
              <input
                value={form.guardian_name}
                onChange={(e) => setForm({ ...form, guardian_name: e.target.value })}
              />
            </div>
            <div className="form-grid">
              <div className="form-field">
                <label>Telefone do responsável</label>
                <input
                  value={form.guardian_phone}
                  onChange={(e) => setForm({ ...form, guardian_phone: e.target.value })}
                />
              </div>
              <div className="form-field">
                <label>E-mail do responsável</label>
                <input
                  type="email"
                  value={form.guardian_email}
                  onChange={(e) => setForm({ ...form, guardian_email: e.target.value })}
                />
              </div>
            </div>
            <div className="form-field">
              <label>Endereço</label>
              <input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
            </div>
            <div className="form-field">
              <label>Observações</label>
              <textarea
                rows={2}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
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
