import { useState } from 'react'
import { Link } from 'react-router-dom'
import { C } from '../colors'
import { Card, Button, Input, Select, ErrorBanner } from '../components/shared'
import { useTeachers } from '../hooks/useTeachers'

function TeacherForm({ initial, onSave, onCancel }) {
  const [form, setForm] = useState(initial || { name: '', school: '', subject: '', grade: '' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handle = async () => {
    if (!form.name.trim()) return
    setSaving(true)
    setError(null)
    try { await onSave(form) } catch (e) { setError(e.message) } finally { setSaving(false) }
  }

  return (
    <Card style={{ marginBottom: 20 }}>
      <h3 style={{ color: C.accent2, fontSize: 14, marginBottom: 16 }}>
        {initial ? 'Editar Professor(a)' : 'Novo(a) Professor(a)'}
      </h3>
      <ErrorBanner message={error} />
      <Input label="Nome *" value={form.name} onChange={v => set('name', v)} placeholder="Nome completo" />
      <Input label="Escola" value={form.school} onChange={v => set('school', v)} placeholder="Nome da escola" />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Select
          label="Componente Curricular"
          value={form.subject}
          onChange={v => set('subject', v)}
          options={[
            { value: '', label: '-- Selecione --' },
            { value: 'Matemática', label: 'Matemática' },
            { value: 'Língua Portuguesa', label: 'Língua Portuguesa' },
            { value: 'Ciências Humanas', label: 'Ciências Humanas' },
            { value: 'Ciências da Natureza', label: 'Ciências da Natureza' },
            { value: 'Arte', label: 'Arte' },
            { value: 'Educação Física', label: 'Educação Física' },
            { value: 'Inglês', label: 'Inglês' },
          ]}
        />
        <Input label="Ano/Série" value={form.grade} onChange={v => set('grade', v)} placeholder="Ex: 6º ano A" />
      </div>
      <div style={{ display: 'flex', gap: 10 }}>
        <Button onClick={handle} disabled={saving || !form.name.trim()}>
          {saving ? 'Salvando...' : 'Salvar'}
        </Button>
        <Button onClick={onCancel} variant="ghost">Cancelar</Button>
      </div>
    </Card>
  )
}

export function TeachersPage() {
  const { teachers, loading, error, create, update, remove } = useTeachers()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)

  const handleCreate = async (d) => { await create(d); setShowForm(false) }
  const handleUpdate = async (d) => { await update(editing.id, d); setEditing(null) }
  const handleDelete = async (id) => {
    if (window.confirm('Confirmar exclusão?')) await remove(id)
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <h1 style={{ fontSize: 20, fontWeight: 700 }}>Professores</h1>
        <Button onClick={() => setShowForm(true)} disabled={showForm}>+ Novo Professor</Button>
      </div>

      {showForm && <TeacherForm onSave={handleCreate} onCancel={() => setShowForm(false)} />}
      {editing && <TeacherForm initial={editing} onSave={handleUpdate} onCancel={() => setEditing(null)} />}

      {error && <ErrorBanner message={error} />}
      {loading ? (
        <p style={{ color: C.textMuted, fontSize: 13 }}>Carregando...</p>
      ) : teachers.length === 0 ? (
        <Card>
          <p style={{ color: C.textMuted, fontSize: 13, textAlign: 'center', padding: '24px 0' }}>
            Nenhum professor cadastrado. Clique em "Novo Professor" para começar.
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {teachers.map(t => (
            <Card key={t.id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: C.text }}>{t.name}</div>
                  <div style={{ color: C.textMuted, fontSize: 12, marginTop: 4 }}>
                    {[t.school, t.subject, t.grade].filter(Boolean).join(' · ')}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Link to={`/evolucao?teacher=${t.id}`}>
                    <Button variant="ghost" style={{ fontSize: 12, padding: '6px 12px' }}>↗ Evolução</Button>
                  </Link>
                  <Button variant="secondary" style={{ fontSize: 12, padding: '6px 12px' }} onClick={() => setEditing(t)}>
                    Editar
                  </Button>
                  <Button variant="danger" style={{ fontSize: 12, padding: '6px 12px' }} onClick={() => handleDelete(t.id)}>
                    ×
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
