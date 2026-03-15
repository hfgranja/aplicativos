import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { C, SECTION_COLORS, RATING_LABELS } from '../../colors'
import { useObservation, STEPS } from '../../hooks/useObservation'
import { Card, Button, Input, Select, ErrorBanner, Spinner } from '../shared'
import { SectionPanel } from './SectionPanel'
import { NarrativePanel } from './NarrativePanel'
import { TeacherQuestionsPanel } from './TeacherQuestionsPanel'
import { ReferencesPanel } from './ReferencesPanel'
import { EF1SectionPanel, EF1MultiSectionPanel } from './EF1SectionPanel'
import { EF1EncaminhamentosPanel } from './EF1EncaminhamentosPanel'
import { api } from '../../api/client'

function UploadPanel({ state, set, teachers }) {
  const [uploading, setUploading] = useState(false)
  const [uploadedFile, setUploadedFile] = useState(null)

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.uploadMedia(fd)
      set('media_file_id', res.id)
      setUploadedFile(res)
    } catch (err) {
      alert('Erro ao fazer upload: ' + err.message)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 24, fontWeight: 700 }}>
        Upload da Aula & Dados Básicos
      </h2>

      <Select
        label="Professor(a) observado(a) *"
        value={state.teacher_id}
        onChange={v => set('teacher_id', v)}
        options={[
          { value: '', label: '-- Selecione --' },
          ...teachers.map(t => ({ value: t.id, label: `${t.name} – ${t.subject || ''} ${t.grade || ''}`.trim() })),
        ]}
      />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <Input
          label="Data da observação *"
          type="datetime-local"
          value={state.observed_at}
          onChange={v => set('observed_at', v)}
        />
        <Input
          label="Nome do PEC"
          value={state.pec_name}
          onChange={v => set('pec_name', v)}
          placeholder="Seu nome"
        />
      </div>

      <Select
        label="Foco curricular da observação"
        value={state.focus_area}
        onChange={v => set('focus_area', v)}
        options={[
          { value: '', label: '-- Selecione --' },
          { value: 'Matemática', label: 'Matemática' },
          { value: 'Língua Portuguesa', label: 'Língua Portuguesa' },
          { value: 'Ciências Humanas', label: 'Ciências Humanas' },
          { value: 'Ciências da Natureza', label: 'Ciências da Natureza' },
        ]}
      />

      {/* File upload */}
      <div style={{ marginTop: 8 }}>
        <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 10 }}>
          Aula gravada (MP4, MP3, WAV – opcional):
        </p>
        {uploadedFile ? (
          <div style={{
            background: C.success + '22', border: `1px solid ${C.success}`,
            borderRadius: 8, padding: '12px 16px', color: C.success, fontSize: 13,
          }}>
            ✓ {uploadedFile.original_name} ({(uploadedFile.file_size_bytes / 1024 / 1024).toFixed(1)} MB)
            <span
              style={{ marginLeft: 12, color: C.textMuted, cursor: 'pointer', fontSize: 11 }}
              onClick={() => { set('media_file_id', null); setUploadedFile(null) }}
            >
              Remover
            </span>
          </div>
        ) : uploading ? (
          <div style={{ color: C.textMuted, fontSize: 13 }}>Enviando arquivo...</div>
        ) : (
          <label style={{
            display: 'block', border: `2px dashed ${C.border}`, borderRadius: 8,
            padding: '28px 20px', textAlign: 'center', cursor: 'pointer', color: C.textMuted,
            fontSize: 13, transition: 'border-color 0.15s',
          }}>
            Clique ou arraste o arquivo aqui
            <input type="file" accept="video/*,audio/*" onChange={handleFile} style={{ display: 'none' }} />
          </label>
        )}
      </div>
    </div>
  )
}

function ReviewPanel({ state, teachers }) {
  const teacher = teachers.find(t => t.id === state.teacher_id)
  const sections = ['s1', 's2', 's3', 's4', 's5']
  const sectionLabels = {
    s1: 'Planejamento', s2: 'Condução', s3: 'Aprendizagem', s4: 'Materiais', s5: 'Clima',
  }

  const getCriteriaForSection = (sec) => {
    const counts = { nao_observado: 0, insuficiente: 0, adequado: 0, muito_bom: 0, null: 0 }
    const fields = Object.keys(state).filter(k => k.startsWith(sec + '_c'))
    fields.forEach(f => {
      const v = state[f] || 'null'
      counts[v] = (counts[v] || 0) + 1
    })
    return { total: fields.length, counts }
  }

  return (
    <div>
      <h2 style={{ color: C.accent2, fontSize: 16, marginBottom: 24, fontWeight: 700 }}>
        Revisão da Observação
      </h2>

      <div style={{ background: C.surface2, borderRadius: 8, padding: 16, marginBottom: 20 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: 13 }}>
          <div>
            <span style={{ color: C.textMuted }}>Professor(a): </span>
            <span style={{ color: C.text, fontWeight: 600 }}>{teacher?.name || '–'}</span>
          </div>
          <div>
            <span style={{ color: C.textMuted }}>Data: </span>
            <span style={{ color: C.text }}>{state.observed_at ? new Date(state.observed_at).toLocaleDateString('pt-BR') : '–'}</span>
          </div>
          <div>
            <span style={{ color: C.textMuted }}>Componente: </span>
            <span style={{ color: C.text }}>{teacher?.subject || '–'}</span>
          </div>
          <div>
            <span style={{ color: C.textMuted }}>Foco: </span>
            <span style={{ color: C.text }}>{state.focus_area || '–'}</span>
          </div>
          <div>
            <span style={{ color: C.textMuted }}>PEC: </span>
            <span style={{ color: C.text }}>{state.pec_name || '–'}</span>
          </div>
          <div>
            <span style={{ color: C.textMuted }}>Arquivo: </span>
            <span style={{ color: state.media_file_id ? C.success : C.textMuted }}>
              {state.media_file_id ? '✓ Enviado' : 'Sem arquivo'}
            </span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 20 }}>
        {sections.map(sec => {
          const { counts, total } = getCriteriaForSection(sec)
          const filled = total - (counts.null || 0)
          return (
            <div key={sec} style={{
              background: C.surface2, borderRadius: 8, padding: 12, textAlign: 'center',
              border: `1px solid ${filled === total ? SECTION_COLORS[sec] + '55' : C.border}`,
            }}>
              <div style={{ color: SECTION_COLORS[sec], fontWeight: 700, fontSize: 12, marginBottom: 4 }}>
                {sectionLabels[sec]}
              </div>
              <div style={{ color: filled === total ? C.success : C.warning, fontSize: 18, fontWeight: 700 }}>
                {filled}/{total}
              </div>
              <div style={{ color: C.textMuted, fontSize: 10 }}>preenchidos</div>
            </div>
          )
        })}
      </div>

      {state.pontos_fortes.filter(Boolean).length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 8 }}>Pontos fortes:</p>
          {state.pontos_fortes.filter(Boolean).map((p, i) => (
            <div key={i} style={{ color: C.text, fontSize: 13, paddingLeft: 12, borderLeft: `2px solid ${C.success}`, marginBottom: 6 }}>
              {p}
            </div>
          ))}
        </div>
      )}

      {state.bncc_skills.length > 0 && (
        <div>
          <p style={{ color: C.textMuted, fontSize: 12, marginBottom: 8 }}>Habilidades BNCC:</p>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {state.bncc_skills.map(s => (
              <span key={s} style={{ background: C.accent + '22', color: C.accent, borderRadius: 6, padding: '3px 10px', fontSize: 12 }}>
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export function ObservationWizard({ teachers }) {
  const nav = useNavigate()
  const obs = useObservation()
  const { state, next, prev, goTo, set, setRating, toggleMethodology, setArrayItem,
    addBnccSkill, removeBnccSkill, addAction, setAction, removeAction,
    addEf1Encaminhamento, setEf1Encaminhamento, removeEf1Encaminhamento,
    toPayload, reset } = obs
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const canNext = () => {
    if (state.step === 0) return !!state.teacher_id && !!state.observed_at
    return true
  }

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      const payload = toPayload()
      const created = await api.createObservation(payload)
      reset()
      nav(`/observacoes/${created.id}`)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const renderStep = () => {
    switch (state.step) {
      case 0: return <UploadPanel state={state} set={set} teachers={teachers} />
      case 1: return <SectionPanel section="s1" state={state} setRating={setRating} />
      case 2: return <SectionPanel section="s2" state={state} setRating={setRating} toggleMethodology={toggleMethodology} />
      case 3: return <SectionPanel section="s3" state={state} setRating={setRating} />
      case 4: return <SectionPanel section="s4" state={state} setRating={setRating} />
      case 5: return <SectionPanel section="s5" state={state} setRating={setRating} />
      case 6: return <NarrativePanel state={state} set={set} setArrayItem={setArrayItem} />
      case 7: return <EF1SectionPanel domain="dc" state={state} setRating={setRating} />
      case 8: return <EF1SectionPanel domain="es" state={state} setRating={setRating} />
      case 9: return <EF1SectionPanel domain="me" state={state} setRating={setRating} />
      case 10: return <EF1MultiSectionPanel domains={['md', 'gs']} state={state} setRating={setRating} />
      case 11: return <EF1EncaminhamentosPanel state={state} set={set} addEf1Encaminhamento={addEf1Encaminhamento} setEf1Encaminhamento={setEf1Encaminhamento} removeEf1Encaminhamento={removeEf1Encaminhamento} />
      case 12: return <TeacherQuestionsPanel state={state} set={set} />
      case 13: return <ReferencesPanel state={state} set={set} addBnccSkill={addBnccSkill} removeBnccSkill={removeBnccSkill} addAction={addAction} setAction={setAction} removeAction={removeAction} />
      case 14: return <ReviewPanel state={state} teachers={teachers} />
      default: return null
    }
  }

  return (
    <div style={{ maxWidth: 820, margin: '0 auto' }}>
      {/* Step progress */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 32, overflowX: 'auto', paddingBottom: 4 }}>
        {STEPS.map((s, i) => (
          <button
            key={s.id}
            type="button"
            onClick={() => goTo(i)}
            style={{
              flex: '0 0 auto', padding: '8px 14px', borderRadius: 8, fontSize: 11, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'JetBrains Mono', transition: 'all 0.15s',
              background: i === state.step ? C.accent : i < state.step ? C.accent + '33' : C.surface2,
              border: `1px solid ${i === state.step ? C.accent : i < state.step ? C.accent + '55' : C.border}`,
              color: i === state.step ? '#fff' : i < state.step ? C.accent : C.textMuted,
            }}
          >
            {i + 1}. {s.label}
          </button>
        ))}
      </div>

      <Card>
        {renderStep()}
        <ErrorBanner message={error} />
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 32, paddingTop: 20, borderTop: `1px solid ${C.border}` }}>
          <Button onClick={prev} variant="ghost" disabled={state.step === 0}>
            ← Anterior
          </Button>
          {state.step < STEPS.length - 1 ? (
            <Button onClick={next} disabled={!canNext()}>
              Próximo →
            </Button>
          ) : (
            <Button onClick={handleSave} variant="success" disabled={saving}>
              {saving ? 'Salvando...' : '✓ Salvar Observação'}
            </Button>
          )}
        </div>
      </Card>
    </div>
  )
}
