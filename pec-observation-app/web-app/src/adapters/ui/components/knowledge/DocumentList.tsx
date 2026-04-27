import { useRef, useState } from 'react'
import type { KnowledgeDocument } from '../../../../domain/entities/Knowledge'
import { DOCUMENT_TYPE_LABELS } from '../../../../domain/entities/Knowledge'
import { EmptyState } from '../common/EmptyState'
import { Modal } from '../common/Modal'
import { Spinner } from '../common/Spinner'

interface Props {
  documents: KnowledgeDocument[]
  loading: boolean
  onUpload: (file: File, title: string, type: string, description?: string) => Promise<boolean>
  onDelete: (id: string) => void
}

export function DocumentList({ documents, loading, onUpload, onDelete }: Props) {
  const [showModal, setShowModal] = useState(false)
  const [file, setFile]           = useState<File | null>(null)
  const [title, setTitle]         = useState('')
  const [docType, setDocType]     = useState('seduc_policy')
  const [description, setDesc]    = useState('')
  const [saving, setSaving]       = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const handleUpload = async () => {
    if (!file || !title) return
    setSaving(true)
    const ok = await onUpload(file, title, docType, description || undefined)
    setSaving(false)
    if (ok) { setShowModal(false); setFile(null); setTitle(''); setDesc('') }
  }

  return (
    <>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs text-gray-400">{documents.length} documento{documents.length !== 1 ? 's' : ''}</p>
        <button className="btn-primary text-xs py-1.5 px-3" onClick={() => setShowModal(true)}>
          + Adicionar documento
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-10"><Spinner /></div>
      ) : documents.length === 0 ? (
        <EmptyState
          icon="📄"
          title="Nenhum documento"
          description="Adicione documentos da SEDUC para enriquecer o feedback gerado pela IA."
          action={{ label: 'Adicionar documento', onClick: () => setShowModal(true) }}
        />
      ) : (
        <div className="space-y-2">
          {documents.map(doc => (
            <div key={doc.id} className="card p-3 flex items-start gap-3">
              <span className="text-2xl mt-0.5">📄</span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{doc.title}</p>
                <p className="text-xs text-gray-500">
                  {DOCUMENT_TYPE_LABELS[doc.documentType]} · {doc.chunkCount} trechos
                </p>
                {doc.description && (
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{doc.description}</p>
                )}
                <p className="text-[10px] text-gray-300 mt-1 font-mono truncate">{doc.sourceFilename}</p>
              </div>
              <button
                onClick={() => onDelete(doc.id)}
                className="text-gray-300 hover:text-red-500 transition-colors flex-shrink-0"
                title="Remover"
              >
                🗑
              </button>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <Modal
          title="Adicionar Documento SEDUC"
          onClose={() => setShowModal(false)}
          footer={
            <>
              <button className="btn-secondary" onClick={() => setShowModal(false)}>Cancelar</button>
              <button className="btn-primary" onClick={handleUpload} disabled={!file || !title || saving}>
                {saving ? 'Enviando…' : 'Enviar'}
              </button>
            </>
          }
        >
          <div className="space-y-4">
            <div
              className="rounded-xl border-2 border-dashed border-gray-200 p-6 text-center cursor-pointer hover:border-brand-400 hover:bg-brand-50/30 transition-colors"
              onClick={() => fileRef.current?.click()}
            >
              {file ? (
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <>
                  <p className="text-3xl mb-2">📂</p>
                  <p className="text-sm text-gray-500">Clique para selecionar PDF ou TXT</p>
                  <p className="text-xs text-gray-400 mt-1">Máx. 20 MB</p>
                </>
              )}
              <input ref={fileRef} type="file" accept=".pdf,.txt" className="hidden"
                onChange={e => setFile(e.target.files?.[0] ?? null)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Título *</label>
              <input className="input" placeholder="Nome do documento" value={title} onChange={e => setTitle(e.target.value)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
              <select className="input" value={docType} onChange={e => setDocType(e.target.value)}>
                {Object.entries(DOCUMENT_TYPE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
              <textarea className="input resize-none" rows={2} placeholder="Descrição opcional…" value={description} onChange={e => setDesc(e.target.value)} />
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
