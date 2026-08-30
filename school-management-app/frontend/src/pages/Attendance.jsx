import { useEffect, useState } from "react";
import { api } from "../api";

function todayStr() {
  return new Date().toISOString().slice(0, 10);
}

export default function Attendance() {
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [date, setDate] = useState(todayStr());
  const [students, setStudents] = useState([]);
  const [marks, setMarks] = useState({}); // student_id -> { present, justified }
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get("/classes").then((cs) => {
      setClasses(cs);
      if (cs.length > 0) setClassId(cs[0].id);
    });
  }, []);

  useEffect(() => {
    if (!classId) return;
    setSaved(false);
    Promise.all([
      api.get(`/students?class_id=${classId}&status=ativo`),
      api.get(`/attendance?class_id=${classId}&date=${date}`),
    ])
      .then(([studs, existing]) => {
        setStudents(studs);
        const initial = {};
        studs.forEach((s) => {
          const rec = existing.find((e) => e.student_id === s.id);
          initial[s.id] = rec
            ? { present: rec.present, justified: rec.justified }
            : { present: true, justified: false };
        });
        setMarks(initial);
      })
      .catch((err) => setError(err.message));
  }, [classId, date]);

  function setMark(studentId, present) {
    setMarks((m) => ({ ...m, [studentId]: { ...m[studentId], present, justified: present ? false : m[studentId]?.justified } }));
  }

  function toggleJustified(studentId) {
    setMarks((m) => ({ ...m, [studentId]: { ...m[studentId], justified: !m[studentId]?.justified } }));
  }

  async function handleSave() {
    setError("");
    setSaved(false);
    const entries = students.map((s) => ({
      student_id: s.id,
      present: marks[s.id]?.present ?? true,
      justified: marks[s.id]?.justified ?? false,
    }));
    try {
      await api.post("/attendance/bulk", { class_id: classId, date, entries });
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h2>Frequência</h2>
      </div>

      <div className="toolbar">
        <select value={classId} onChange={(e) => setClassId(e.target.value)}>
          {classes.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} />
      </div>

      {error && <div className="error-text">{error}</div>}
      {saved && <div style={{ color: "var(--success)", marginBottom: 12 }}>Frequência salva.</div>}

      <div className="card">
        {students.length === 0 && <div className="empty-state">Nenhum aluno ativo nesta turma.</div>}
        {students.map((s) => {
          const mark = marks[s.id] || { present: true, justified: false };
          return (
            <div className="attendance-row" key={s.id}>
              <div>{s.name}</div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div className="attendance-toggle">
                  <button
                    type="button"
                    className={mark.present ? "active present" : ""}
                    onClick={() => setMark(s.id, true)}
                  >
                    Presente
                  </button>
                  <button
                    type="button"
                    className={!mark.present ? "active absent" : ""}
                    onClick={() => setMark(s.id, false)}
                  >
                    Ausente
                  </button>
                </div>
                {!mark.present && (
                  <label style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 0 }}>
                    <input
                      type="checkbox"
                      style={{ width: "auto" }}
                      checked={mark.justified}
                      onChange={() => toggleJustified(s.id)}
                    />
                    Justificada
                  </label>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {students.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <button className="btn" onClick={handleSave}>
            Salvar frequência
          </button>
        </div>
      )}
    </div>
  );
}
