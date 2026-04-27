import { useState } from 'react'
import type { BestPracticeCard } from '../../../../domain/entities/BestPractice'
import { Modal } from '../common/Modal'

interface Props {
  card:     BestPracticeCard
  onSend:   (teacherIds: string[], message: string) => Promise<boolean>
  onClose:  () => void
}

export function DistributeModal({ card, onSend, onClose }: Props) {
  const [teacherInput, setTeacherInput] = useState('')
  const [message, setMessage]           = useState('')
  const [sending, setSending]           = useState(false)
  const [sent, setSent]                 = useState(false)

  const teacherIds = teacherInput.split(',').map(s => s.trim()).filter(Boolean)

  const handleSend = async () => {
    if (!teacherIds.length) return
    setSending(true)
    const ok = await onSend(teacherIds, message)
    setSending(false)
    if (ok) setSent(true)
  }

  if (sent) {
    return (
      <Modal title="Enviado!" onClose={onClose}
        footer={<button className="btn-primary" onClick={onClose}>Fechar</button>}>
        <div className="text-center py-6 space-y-3">
          <span className="text-5xl">📤</span>
          <p className="text-sm text-gray-700">
            Boa prática enviada para {teacherIds.length} professor{teacherIds.length > 1 ? 'es' : ''}.
          </p>
          <p className="text-xs text-gray-400">O conteúdo foi entregue de forma totalmente anonimizada.</p>
        </div>
      </Modal>
    )
  }

  return (
    <Modal
      title="Enviar Boa Prática"
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose}>Cancelar</button>
          <button className="btn-primary" onClick={handleSend}
            disabled={!teacherIds.length || sending}>
            {sending ? 'Enviando…' : `📤 Enviar para ${teacherIds.length || '…'} professor${teacherIds.length !== 1 ? 'es' : ''}`}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Card preview */}
        <div className="rounded-lg bg-gray-50 border border-gray-100 p-3 text-sm">
          <p className="font-semibold text-gray-900 truncate">{card.title}</p>
          <p className="text-gray-500 text-xs mt-0.5">{card.subject} · {card.grade}</p>
        </div>

        {/* Teacher IDs */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            IDs dos professores *
          </label>
          <textarea
            className="input resize-none"
            rows={2}
            placeholder="professor1-id, professor2-id, …"
            value={teacherInput}
            onChange={e => setTeacherInput(e.target.value)}
          />
          <p className="text-xs text-gray-400 mt-0.5">Separe múltiplos IDs com vírgula</p>
        </div>

        {/* Message */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Mensagem (opcional)</label>
          <textarea
            className="input resize-none"
            rows={3}
            placeholder="Ex: Esta aula exemplifica como estruturar uma boa avaliação formativa…"
            value={message}
            onChange={e => setMessage(e.target.value)}
          />
        </div>

        {/* Privacy badge */}
        <div className="flex gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
          <span>🔒</span>
          <span>
            <strong>Privacidade garantida:</strong> O nome do professor, escola e alunos foram completamente removidos.
            O destinatário recebe apenas o conteúdo pedagógico anonimizado.
          </span>
        </div>
      </div>
    </Modal>
  )
}
