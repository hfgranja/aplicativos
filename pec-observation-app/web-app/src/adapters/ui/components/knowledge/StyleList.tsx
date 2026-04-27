import { useState } from 'react'
import type { FeedbackStyle, StyleTone } from '../../../../domain/entities/Knowledge'
import { STYLE_TONE_LABELS } from '../../../../domain/entities/Knowledge'
import { EmptyState } from '../common/EmptyState'
import { Modal } from '../common/Modal'
import { Spinner } from '../common/Spinner'

interface Props {
  styles: FeedbackStyle[]
  loading: boolean
  onCreate: (input: {
    name: string; description: string; tone: StyleTone
    templatePrompt: string; exampleStrengths: string[]
    exampleImprovements: string[]; isDefault: boolean
  }) => Promise<boolean>
  onDelete: (id: string) => void
}

export function StyleList({ styles, loading, onCreate, onDelete }: Props) {
  const [showModal, setShowModal] = useState(false)
  const [name, setName]           = useState('')
  const [desc, setDesc]           = useState('')
  const [tone, setTone]           = useState<StyleTone>('constructive')
  const [prompt, setPrompt]       = useState('')
  const [strengths, setStrengths] = useState('')
  const [improvements, setImprovements] = useState('')
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving]       = useState(false)

  const handleCreate = async () => {
    setSaving(true)
    const ok = await onCreate({
      name, description: desc, tone,
      templatePrompt: prompt,
      exampleStrengths:   strengths.split('\n').filter(Boolean),
      exampleImprovements: improvements.split('\n').filter(Boolean),
      isDefault,
    })
    setSaving(false)
    if (ok) { setShowModal(false); setName(''); setDesc(''); setPrompt('') }
  }

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400">{styles.length} estilo{styles.length !== 1 ? 's' : ''}</p>
        <button className="btn-primary text-xs py-1.5 px-3" onClick={() => setShowModal(true)}>
          + Novo estilo
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><Spinner /></div>
      ) : styles.length === 0 ? (
        <EmptyState
          icon="🎨"
          title="Nenhum estilo configurado"
          description="Crie estilos de feedback para personalizar o tom e foco da IA."
          action={{ label: 'Novo estilo', onClick: () => setShowModal(true) }}
        />
      ) : (
        <div className="space-y-2">
          {styles.map(style => (
            <div key={style.id} className="card p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-0.5">
                    <p className="text-sm font-semibold text-gray-900">{style.name}</p>
                    {style.isDefault && <span className="badge badge-blue">Padrão</span>}
                    <span className="badge badge-gray">{STYLE_TONE_LABELS[style.tone]}</span>
                  </div>
                  <p className="text-xs text-gray-500 line-clamp-2">{style.description}</p>
                  {style.templatePrompt && (
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2 italic">"{style.templatePrompt}"</p>
                  )}
                </div>
                {!style.isDefault && (
                  <button onClick={() => onDelete(style.id)} className="text-gray-300 hover:text-red-500 transition-colors flex-shrink-0" title="Remover">🗑</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <Modal
          title="Novo Estilo de Feedback"
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
              <button className="btn-primary" onClick={handleCreate} disabled={!name || !prompt || saving}>
                {saving ? 'Salvando…' : 'Criar'}
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input className="input" placeholder="Ex: Encorajador Júnior" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
              <input className="input" placeholder="Breve descrição do estilo" value={desc} onChange={e => setDesc(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tom</label>
              <select className="input" value={tone} onChange={e => setTone(e.target.value as StyleTone)}>
                {Object.entries(STYLE_TONE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Instrução para a IA *</label>
              <textarea className="input resize-none" rows={4} placeholder="Ex: Use linguagem encorajadora, foque nos avanços do professor…" value={prompt} onChange={e => setPrompt(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Exemplos de forças (uma por linha)</label>
              <textarea className="input resize-none" rows={2} placeholder="O professor demonstrou…" value={strengths} onChange={e => setStrengths(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Exemplos de melhorias (uma por linha)</label>
              <textarea className="input resize-none" rows={2} placeholder="Recomenda-se…" value={improvements} onChange={e => setImprovements(e.target.value)} />
            </div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="rounded" checked={isDefault} onChange={e => setIsDefault(e.target.checked)} />
              <span className="text-sm text-gray-700">Definir como estilo padrão</span>
            </label>
          </div>
        </Modal>
      )}
    </>
  )
}
