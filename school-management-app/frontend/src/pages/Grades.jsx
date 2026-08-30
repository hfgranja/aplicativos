import { useEffect, useState } from "react";
import { api } from "../api";
import Modal from "../components/Modal";

const EMPTY_FORM = { student_id: "", subject: "", term: 1, value: "", notes: "" };

export default function Grades() {
  const [grades, setGrades] = useState([]);
  const [classes, setClasses] = useState([]);
  const [students, setStudents] = useState([]);
  const [classId, setClassId] = useState("");
  const [term, setTerm] = useState("");
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    api.get("/classes").then(setClasses);
  }, []);

  function load() {
    const params = new URLSearchParams();
    if (classId) params.set("class_id", classId);
    if (term) params.set("term", term);
    api
      .get(`/grades?${params.toString()}`)
      .then(setGrades)
      .catch((err) => setError(err.message));
  }

  useEffect(load, [classId, term]);

  useEffect(() => {
    if (!classId) {
      setStudents([]);
      return;
    }
    api.get(`/students?class_id=${classId}&status=ativo`).then(setStudents);
  }, [classId]);

  function openCreate() {
    setForm({ ...EMPTY_FORM, student_id: students[0]?.id || "" });
    setShowModal(true);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await api.post("/grades", { ...form, term: Number(form.term), value: Number(form.value) });
      setShowModal(false);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleDelete(g) {
    if (!confirm("Excluir esta nota?")) return;
    try {
      await api.del(`/grades/${g.id}`);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Notas</h2>
        <button className="btn" onClick={openCreate} disabled={!classId}>
          + Lançar nota
        </button>
      </div>

      <div className="toolbar">
        <select value={classId} onChange={(e) => setClassId(e.target.value)}>
          <option value="">Selecione uma turma</option>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <select value={term} onChange={(e) => setTerm(e.target.value)}>
          <option value="">Todos os bimestres</option>
          <option value="1">1º bimestre</option>
          <option value="2">2º bimestre</option>
          <option value="3">3º bimestre</option>
          <option value="4">4º bimestre</option>
        </select>
      </div>

      {error && <div className="error-text">{error}</div>}

      <table>
        <thead>
          <tr>
            <th>Aluno</th>
            <th>Disciplina</th>
            <th>Bimestre</th>
            <th>Nota</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {grades.map((g) => (
            <tr key={g.id}>
              <td>{g.student_name}</td>
              <td>{g.subject}</td>
              <td>{g.term}º</td>
              <td>{g.value}</td>
              <td>
                <button className="btn danger small" onClick={() => handleDelete(g)}>
                  Excluir
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {grades.length === 0 && (
        <div className="empty-state">
          {classId ? "Nenhuma nota lançada para o filtro selecionado." : "Selecione uma turma para ver as notas."}
        </div>
      )}

      {showModal && (
        <Modal title="Lançar nota" onClose={() => setShowModal(false)}>
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
            <div className="form-grid">
              <div className="form-field">
                <label>Disciplina</label>
                <input
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  required
                />
              </div>
              <div className="form-field">
                <label>Bimestre</label>
                <select value={form.term} onChange={(e) => setForm({ ...form, term: e.target.value })}>
                  <option value={1}>1º</option>
                  <option value={2}>2º</option>
                  <option value={3}>3º</option>
                  <option value={4}>4º</option>
                </select>
              </div>
            </div>
            <div className="form-field">
              <label>Nota (0 a 10)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="10"
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
                required
              />
            </div>
            <div className="form-field">
              <label>Observações</label>
              <input value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
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
