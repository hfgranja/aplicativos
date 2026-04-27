import { useEffect, useState } from 'react'
import { Layout } from '../adapters/ui/components/common/Layout'
import { PageSpinner } from '../adapters/ui/components/common/Spinner'
import { ErrorBanner } from '../adapters/ui/components/common/ErrorBanner'
import { EmptyState } from '../adapters/ui/components/common/EmptyState'
import { PracticeCard } from '../adapters/ui/components/bestpractices/PracticeCard'
import { DistributeModal } from '../adapters/ui/components/bestpractices/DistributeModal'
import { useBestPractices } from '../adapters/ui/viewModels/useBestPractices'
import type { BestPracticeCard } from '../domain/entities/BestPractice'
import { CRITERION_LABELS, CRITERION_EMOJI } from '../domain/entities/BestPractice'

type Tab = 'published' | 'draft'

const CRITERIA = ['', 'planejamento', 'didatica', 'engajamento', 'avaliacao', 'gestao'] as const

export function BestPracticesPage() {
  const { cards, loading, error, loadLibrary, publish, distribute, archive } = useBestPractices()
  const [tab, setTab]           = useState<Tab>('published')
  const [criterion, setCriterion] = useState('')
  const [distributeCard, setDistributeCard] = useState<BestPracticeCard | null>(null)

  useEffect(() => { loadLibrary(tab) }, [tab])

  const filtered = criterion
    ? cards.filter(c => c.criterion === criterion)
    : cards

  return (
    <Layout title="Boas Práticas">
      <div className="px-4 pt-4 pb-2 lg:px-6 lg:pt-6">
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-bold text-gray-900 hidden lg:block">Boas Práticas</h1>
        </div>

        {/* Info banner */}
        <div className="flex items-start gap-3 rounded-xl bg-amber-50 border border-amber-200 p-3 mb-4">
          <span className="text-xl">✨</span>
          <p className="text-xs text-amber-800">
            <strong>Como funciona:</strong> A cada observação aprovada, a IA extrai automaticamente os momentos exemplares, anonimiza o conteúdo (nomes de professores, escola e alunos são removidos) e cria uma carta para a biblioteca. O PEC revisa, publica e pode enviar diretamente aos professores.
          </p>
        </div>

        {/* Tabs */}
        <div className="flex rounded-lg bg-gray-100 p-0.5 mb-4 w-fit">
          {([['published', '📚 Biblioteca'], ['draft', '🔍 Rascunhos']] as [Tab, string][]).map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${
                tab === key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}>
              {label}
            </button>
          ))}
        </div>

        {/* Criterion filters */}
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-4 px-4 lg:mx-0 lg:px-0 scrollbar-none mb-2">
          {CRITERIA.map(c => (
            <button key={c}
              onClick={() => setCriterion(c)}
              className={`flex-shrink-0 rounded-full px-3 py-1 text-xs font-medium border transition-colors ${
                criterion === c
                  ? 'bg-seduc-blue text-white border-seduc-blue'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400'
              }`}>
              {c ? `${CRITERION_EMOJI[c as keyof typeof CRITERION_EMOJI]} ${CRITERION_LABELS[c as keyof typeof CRITERION_LABELS]}` : 'Todos'}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 lg:px-6">
        {error && <ErrorBanner message={error} />}

        {loading ? (
          <PageSpinner />
        ) : filtered.length === 0 ? (
          <EmptyState
            icon="⭐"
            title={tab === 'draft' ? 'Nenhum rascunho pendente' : 'Biblioteca vazia'}
            description={
              tab === 'draft'
                ? 'Rascunhos aparecem automaticamente quando uma observação é aprovada.'
                : 'Publique rascunhos para que apareçam aqui.'
            }
          />
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 mt-2">
            {filtered.map(card => (
              <PracticeCard
                key={card.id}
                card={card}
                onPublish={tab === 'draft' ? (id, title) => publish(id, title) : undefined}
                onDistribute={tab === 'published' ? (c) => setDistributeCard(c) : undefined}
                onArchive={(id) => archive(id)}
              />
            ))}
          </div>
        )}
      </div>

      {distributeCard && (
        <DistributeModal
          card={distributeCard}
          onSend={(ids, msg) => distribute(distributeCard.id, ids, msg)}
          onClose={() => setDistributeCard(null)}
        />
      )}
    </Layout>
  )
}
