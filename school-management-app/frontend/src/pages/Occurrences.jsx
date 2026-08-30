import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_FORM = {
  student_id: "",
  type: "disciplinar",
  description: "",
  action_taken: "",
  guardian_notified: false,
};

const TYPE_LABELS = {
  disciplinar: "Disciplinar",
  elogio: "Elogio",
  saude: "Saúde",
  outro: "Outro",
};

export default function Occurrences() {
  const [occurrences, setOccurrences] = useState([]);
  const [students, setStudents] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    api.get("/students").then(setStudents);
  }, []);

  function load() {
    const params = new URLSearchParams();
    if (typeFilter) params.set("type", typeFilter);
    api
      .get(`/occurrences?${params.toString()}`)
      .then(setOccurrences)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [typeFilter]);

  function openCreate() {
    setForm({ ...EMPTY_FORM, student_id: students[0]?.id || "" });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/occurrences", form);
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(o) {
    if (!confirm("Excluir esta ocorrência?")) return;
    try {
      await api.del(`/occurrences/${o.id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Ocorrências</h2>
        <button className="btn" onClick={openCreate}>
          + Nova ocorrência
        </button>
      </div>

      <div className="toolbar">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">Todos os tipos</option>
          <option value="disciplinar">Disciplinar</option>
          <option value="elogio">Elogio</option>
          <option value="saude">Saúde</option>
          <option value="outro">Outro</option>
        </select>
      </div>

      {error && <div className="error-text">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>Data</th>
            <th>Aluno</th>
            <th>Tipo</th>
            <th>Descrição</th>
            <th>Responsável avisado</th>
            <th>Registrado por</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {occurrences.map((o) => (
            <tr key={o.id}>
              <td>{o.date}</td>
              <td>{o.student_name}</td>
              <td>{TYPE_LABELS[o.type] || o.type}</td>
              <td>{o.description}</td>
              <td>{o.guardian_notified ? "Sim" : "Não"}</td>
              <td>{o.reported_by_name}</td>
              <td>
                <button className="btn danger small" onClick={() => handleDelete(o)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {occurrences.length === 0 && <div className="empty-state">Nenhuma ocorrência registrada.</div>}

      {showModal && (
        <Modal title="Nova ocorrência" onClose={() => setShowModal(false)}>
          <form onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Aluno</label>
              <select
                value={form.student_id}
                onChange={(e) => setForm({ ...form, student_id: e.target.value })}
                required
              >
                <option value="">Selecione...</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-field">
              <label>Tipo</label>
              <select value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option value="disciplinar">Disciplinar</option>
                <option value="elogio">Elogio</option>
                <option value="saude">Saúde</option>
                <option value="outro">Outro</option>
              </select>
            </div>
            <div className="form-field">
              <label>Descrição</label>
              <textarea
                rows={3}
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                required
              />
            </div>
            <div className="form-field">
              <label>Providência tomada</label>
              <textarea
                rows={2}
                value={form.action_taken}
                onChange={(e) => setForm({ ...form, action_taken: e.target.value })}
              />
            </div>
            <label style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <input
                type="checkbox"
                style={{ width: "auto" }}
                checked={form.guardian_notified}
                onChange={(e) => setForm({ ...form, guardian_notified: e.target.checked })}
              />
              Responsável já foi avisado
            </label>
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
