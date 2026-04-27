import { useEffect, useState } from 'react'
import { Layout } from '../adapters/ui/components/common/Layout'
import { ErrorBanner } from '../adapters/ui/components/common/ErrorBanner'
import { DocumentList } from '../adapters/ui/components/knowledge/DocumentList'
import { StyleList } from '../adapters/ui/components/knowledge/StyleList'
import { useKnowledge } from '../adapters/ui/viewModels/useKnowledge'

type Tab = 'documents' | 'styles'

export function KnowledgePage() {
  const { documents, styles, loading, error, loadAll, uploadDocument, deleteDocument, createStyle, deleteStyle } = useKnowledge()
  const [tab, setTab] = useState<Tab>('documents')

  useEffect(() => { loadAll() }, [])

  return (
    <Layout title="Biblioteca">
      <div className="px-4 pt-4 pb-2 lg:px-6 lg:pt-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-gray-900 hidden lg:block">Base de Conhecimento</h1>
        </div>
        <p className="text-xs text-gray-400 mb-4">
          Documentos SEDUC e estilos de feedback enriquecem o contexto da IA durante a geração de feedback.
        </p>

        {/* Tabs */}
        <div className="flex rounded-lg bg-gray-100 p-0.5 mb-4 w-fit">
          {([['documents', '📄 Documentos'], ['styles', '🎨 Estilos']] as [Tab, string][]).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-all ${
                tab === key ? 'bg-white shadow text-gray-900' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 lg:px-6">
        {error && <ErrorBanner message={error} />}

        {tab === 'documents' ? (
          <DocumentList
            documents={documents}
            loading={loading}
            onUpload={uploadDocument}
            onDelete={deleteDocument}
          />
        ) : (
          <StyleList
            styles={styles}
            loading={loading}
            onCreate={createStyle}
            onDelete={deleteStyle}
          />
        )}
      </div>
    </Layout>
  )
}
