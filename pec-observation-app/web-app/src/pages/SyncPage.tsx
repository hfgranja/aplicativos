import { useEffect, useState } from 'react'
import { Layout } from '../adapters/ui/components/common/Layout'
import { FetchNetworkClient } from '../adapters/network/FetchNetworkClient'
import { API_URLS } from '../adapters/network/config'

interface ServiceHealth { name: string; url: string; port: number; status: 'healthy' | 'down' | 'checking' }

const SERVICES: Omit<ServiceHealth, 'status'>[] = [
  { name: 'Identidade (MS-001)',      url: API_URLS.identity,    port: 8001 },
  { name: 'Escolas (MS-002)',         url: API_URLS.school,      port: 8002 },
  { name: 'Observações (MS-003)',     url: API_URLS.observation, port: 8003 },
  { name: 'Áudio (MS-004)',           url: API_URLS.audio,       port: 8004 },
  { name: 'Feedback (MS-007)',        url: API_URLS.feedback,    port: 8007 },
  { name: 'Conhecimento (MS-011)',    url: API_URLS.knowledge,   port: 8011 },
]

export function SyncPage() {
  const [services, setServices] = useState<ServiceHealth[]>(
    SERVICES.map(s => ({ ...s, status: 'checking' }))
  )
  const [lastChecked, setLastChecked] = useState<Date | null>(null)

  const checkHealth = async () => {
    setServices(prev => prev.map(s => ({ ...s, status: 'checking' })))
    const results = await Promise.all(
      SERVICES.map(async svc => {
        try {
          const res = await fetch(`${svc.url}/health`, { signal: AbortSignal.timeout(4000) })
          return { ...svc, status: res.ok ? 'healthy' : 'down' } as ServiceHealth
        } catch {
          return { ...svc, status: 'down' } as ServiceHealth
        }
      })
    )
    setServices(results)
    setLastChecked(new Date())
  }

  useEffect(() => { checkHealth() }, [])

  const healthy = services.filter(s => s.status === 'healthy').length
  const total   = services.length

  return (
    <Layout title="Sincronização">
      <div className="px-4 pt-4 pb-6 lg:px-6 lg:pt-6 max-w-2xl">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-gray-900 hidden lg:block">Status dos Serviços</h1>
          <button className="btn-secondary text-sm" onClick={checkHealth}>🔄 Verificar</button>
        </div>

        {/* Summary card */}
        <div className={`card p-4 mb-4 flex items-center gap-4 ${healthy === total ? 'border-green-200 bg-green-50/30' : 'border-yellow-200 bg-yellow-50/30'}`}>
          <div className={`text-4xl ${healthy === total ? '' : 'grayscale'}`}>
            {healthy === total ? '✅' : '⚠️'}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {healthy}/{total} serviços online
            </p>
            {lastChecked && (
              <p className="text-xs text-gray-400">
                Última verificação: {lastChecked.toLocaleTimeString('pt-BR')}
              </p>
            )}
          </div>
        </div>

        {/* Service list */}
        <div className="space-y-2">
          {services.map(svc => (
            <div key={svc.name} className="card px-4 py-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-gray-900">{svc.name}</p>
                <p className="text-xs text-gray-400 font-mono">:{svc.port}</p>
              </div>
              <StatusBadge status={svc.status} />
            </div>
          ))}
        </div>

        {/* Info box */}
        <div className="mt-6 rounded-xl bg-brand-50 border border-brand-100 p-4">
          <p className="text-xs font-semibold text-brand-700 mb-1">📡 Sincronização automática</p>
          <p className="text-xs text-brand-600">
            O app mobile sincroniza pendências automaticamente a cada 15 minutos quando há conexão.
            Os dados desta tela são sincronizados em tempo real via API REST.
          </p>
        </div>
      </div>
    </Layout>
  )
}

function StatusBadge({ status }: { status: ServiceHealth['status'] }) {
  if (status === 'checking') return <span className="badge badge-gray animate-pulse">Verificando…</span>
  if (status === 'healthy')  return <span className="badge badge-green">🟢 Online</span>
  return <span className="badge badge-red">🔴 Offline</span>
}
