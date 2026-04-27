import { useState } from 'react'
import type { BestPracticeCard } from '../../../../domain/entities/BestPractice'
import { CRITERION_LABELS, CRITERION_EMOJI } from '../../../../domain/entities/BestPractice'
import { Modal } from '../common/Modal'

interface Props {
  card:          BestPracticeCard
  onPublish?:    (id: string, title: string) => void
  onDistribute?: (card: BestPracticeCard) => void
  onArchive?:    (id: string) => void
  getVideoUrl?:  (cardId: string) => Promise<string | null>
}

export function PracticeCard({ card, onPublish, onDistribute, onArchive, getVideoUrl }: Props) {
  const [showDetail, setShowDetail] = useState(false)
  const emoji = CRITERION_EMOJI[card.criterion] ?? '📚'
  const label = CRITERION_LABELS[card.criterion] ?? card.criterion

  return (
    <>
      <div
        className="card p-4 cursor-pointer hover:shadow-md transition-shadow"
        onClick={() => setShowDetail(true)}
      >
        <div className="flex items-start gap-3">
          <span className="text-2xl mt-0.5">{emoji}</span>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-brand-600 mb-0.5">{label}</p>
            <p className="text-sm font-semibold text-gray-900 line-clamp-2">{card.title}</p>
            <p className="text-xs text-gray-500 italic mt-1 line-clamp-2">"{card.excerpt}"</p>
            <div className="flex flex-wrap gap-1.5 mt-2">
              <span className="badge badge-blue">{card.subject}</span>
              <span className="badge badge-gray">{card.grade}</span>
              {card.hasAudio && (
                <span className="badge badge-green">🎙 Áudio</span>
              )}
              {card.hasVideo && (
                <span className="badge badge-purple">🎬 Vídeo</span>
              )}
              {card.videoStatus === 'processing' && (
                <span className="badge badge-orange">⏳ Gerando…</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-2 mt-3 pt-3 border-t border-gray-50">
          {card.status === 'draft' && onPublish && (
            <button
              className="btn-primary text-xs py-1 px-3"
              onClick={e => { e.stopPropagation(); onPublish(card.id, card.title) }}
            >
              ✅ Publicar
            </button>
          )}
          {card.status === 'published' && onDistribute && (
            <button
              className="btn-primary text-xs py-1 px-3"
              onClick={e => { e.stopPropagation(); onDistribute(card) }}
            >
              📤 Enviar
            </button>
          )}
          {onArchive && (
            <button
              className="btn-secondary text-xs py-1 px-3"
              onClick={e => { e.stopPropagation(); onArchive(card.id) }}
            >
              Arquivar
            </button>
          )}
        </div>
      </div>

      {showDetail && (
        <PracticeDetailModal card={card} onClose={() => setShowDetail(false)}
          onPublish={onPublish} onDistribute={onDistribute} getVideoUrl={getVideoUrl} />
      )}
    </>
  )
}

function PracticeDetailModal({ card, onClose, onPublish, onDistribute, getVideoUrl }: {
  card: BestPracticeCard
  onClose: () => void
  onPublish?: (id: string, title: string) => void
  onDistribute?: (card: BestPracticeCard) => void
  getVideoUrl?: (cardId: string) => Promise<string | null>
}) {
  const [editTitle, setEditTitle]       = useState(card.title)
  const [videoSrc, setVideoSrc]         = useState<string | null>(null)
  const [videoLoading, setVideoLoading] = useState(false)

  async function handleWatchVideo() {
    if (!getVideoUrl) return
    setVideoLoading(true)
    const url = await getVideoUrl(card.id)
    setVideoLoading(false)
    if (url) setVideoSrc(url)
  }

  return (
    <Modal
      title={card.title}
      onClose={onClose}
      footer={
        <>
          <button className="btn-secondary" onClick={onClose}>Fechar</button>
          {card.status === 'draft' && onPublish && (
            <button className="btn-primary" onClick={() => { onPublish(card.id, editTitle); onClose() }}>
              ✅ Publicar
            </button>
          )}
          {card.status === 'published' && onDistribute && (
            <button className="btn-primary" onClick={() => { onDistribute(card); onClose() }}>
              📤 Enviar para professores
            </button>
          )}
        </>
      }
    >
      <div className="space-y-4">
        {/* Criterion + tags */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-blue">{CRITERION_EMOJI[card.criterion]} {CRITERION_LABELS[card.criterion]}</span>
          <span className="badge badge-gray">{card.subject}</span>
          <span className="badge badge-gray">{card.grade}</span>
        </div>

        {/* Excerpt */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Trecho da aula (anonimizado)
          </p>
          <blockquote className="border-l-4 border-brand-200 pl-3 text-sm italic text-gray-700 bg-gray-50 py-2 pr-3 rounded-r-lg">
            {card.excerpt}
          </blockquote>
        </div>

        {/* Audio */}
        {card.hasAudio && card.audioUrl && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Áudio anonimizado
            </p>
            <audio controls src={card.audioUrl} className="w-full" />
          </div>
        )}

        {/* AI explanation */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Por que é uma boa prática?
          </p>
          <p className="text-sm text-gray-700">{card.aiExplanation}</p>
        </div>

        {/* Rubric */}
        {card.rubricAlignment.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
              Alinhamento SEDUC
            </p>
            <ul className="space-y-1">
              {card.rubricAlignment.map(item => (
                <li key={item} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="text-green-600 mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Edit title before publish */}
        {card.status === 'draft' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Título (editável antes de publicar)</label>
            <input className="input" value={editTitle} onChange={e => setEditTitle(e.target.value)} />
          </div>
        )}

        {/* Video section */}
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Vídeo da boa prática
          </p>
          {card.videoStatus === 'ready' && !videoSrc && (
            <button
              className="btn-primary w-full"
              onClick={handleWatchVideo}
              disabled={videoLoading}
            >
              {videoLoading ? '⏳ Carregando…' : '▶ Assistir vídeo anime'}
              {card.videoDurationS != null && !videoLoading && (
                <span className="ml-2 text-xs opacity-75">
                  ({Math.floor(card.videoDurationS / 60)}m{card.videoDurationS % 60}s)
                </span>
              )}
            </button>
          )}
          {videoSrc && (
            <video
              src={videoSrc}
              controls
              autoPlay
              className="w-full rounded-lg mt-1"
              style={{ maxHeight: '360px' }}
            />
          )}
          {card.videoStatus === 'processing' && (
            <p className="text-xs text-orange-600">⏳ Vídeo sendo gerado…</p>
          )}
          {card.videoStatus === 'failed' && (
            <p className="text-xs text-red-600">⚠️ Falha na geração do vídeo</p>
          )}
          {card.videoStatus === 'pending' && (
            <p className="text-xs text-gray-400">🎬 Vídeo será gerado em breve</p>
          )}
        </div>

        {/* Privacy notice */}
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-800">
          🔒 Este conteúdo foi completamente anonimizado — nomes de professores, escolas e alunos foram substituídos antes do armazenamento.
        </div>
      </div>
    </Modal>
  )
}
