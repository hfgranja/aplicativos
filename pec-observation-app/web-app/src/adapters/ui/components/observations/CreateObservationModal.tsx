import { useState } from 'react'
import { Modal } from '../common/Modal'
import type { School, Teacher } from '../../../../domain/entities/School'

interface Props {
  schools: School[]
  teachers: Teacher[]
  onLoadTeachers: (schoolId: string) => void
  onSubmit: (data: {
    schoolId: string; teacherId: string; subject: string; grade: string
    scheduledAt: string; durationMinutes: number; notes: string
  }) => Promise<boolean>
  onClose: () => void
}

const GRADES = ['EF1 - 1º ano', 'EF1 - 2º ano', 'EF1 - 3º ano', 'EF1 - 4º ano', 'EF1 - 5º ano',
  'EF2 - 6º ano', 'EF2 - 7º ano', 'EF2 - 8º ano', 'EF2 - 9º ano',
  'EM - 1ª série', 'EM - 2ª série', 'EM - 3ª série']

export function CreateObservationModal({ schools, teachers, onLoadTeachers, onSubmit, onClose }: Props) {
  const [schoolId, setSchoolId]   = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [subject, setSubject]     = useState('')
  const [grade, setGrade]         = useState('')
  const [scheduledAt, setScheduledAt] = useState(() => {
    const d = new Date(); d.setMinutes(0, 0, 0); return d.toISOString().slice(0, 16)
  })
  const [duration, setDuration] = useState(50)
  const [notes, setNotes]       = useState('')
  const [saving, setSaving]     = useState(false)

  const handleSchoolChange = (id: string) => {
    setSchoolId(id)
    setTeacherId('')
    if (id) onLoadTeachers(id)
  }

  const handleSubmit = async () => {
    setSaving(true)
    const ok = await onSubmit({ schoolId, teacherId, subject, grade, scheduledAt, durationMinutes: duration, notes })
    setSaving(false)
    if (ok) onClose()
  }

  const canSubmit = schoolId && teacherId && subject && grade && scheduledAt && !saving

  return (
    <Modal
      title="Nova Observação"
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn-primary" onClick={handleSubmit} disabled={!canSubmit}>
            {saving ? 'Salvando…' : 'Criar'}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Escola *</label>
          <select className="input" value={schoolId} onChange={e => handleSchoolChange(e.target.value)}>
            <option value="">Selecione uma escola</option>
            {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Professor *</label>
          <select className="input" value={teacherId} onChange={e => setTeacherId(e.target.value)} disabled={!schoolId}>
            <option value="">Selecione um professor</option>
            {teachers.map(t => <option key={t.id} value={t.id}>{t.name} — {t.subjectArea}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Componente *</label>
            <input className="input" placeholder="ex: Matemática" value={subject} onChange={e => setSubject(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Turma *</label>
            <select className="input" value={grade} onChange={e => setGrade(e.target.value)}>
              <option value="">Selecione</option>
              {GRADES.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Data e hora *</label>
            <input type="datetime-local" className="input" value={scheduledAt} onChange={e => setScheduledAt(e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Duração (min)</label>
            <input type="number" className="input" min={10} max={300} value={duration} onChange={e => setDuration(Number(e.target.value))} />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Anotações</label>
          <textarea className="input resize-none" rows={3} placeholder="Observações iniciais…" value={notes} onChange={e => setNotes(e.target.value)} />
        </div>
      </div>
    </Modal>
  )
}
