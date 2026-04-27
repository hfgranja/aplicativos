import { useEffect, useState } from 'react'
import { Layout } from '../adapters/ui/components/common/Layout'
import { PageSpinner } from '../adapters/ui/components/common/Spinner'
import { ErrorBanner } from '../adapters/ui/components/common/ErrorBanner'
import { EmptyState } from '../adapters/ui/components/common/EmptyState'
import { SchoolCard } from '../adapters/ui/components/schools/SchoolCard'
import { Modal } from '../adapters/ui/components/common/Modal'
import { useSchools } from '../adapters/ui/viewModels/useSchools'
import type { School } from '../domain/entities/School'

export function SchoolsPage() {
  const { schools, teachers, loading, error, loadSchools, loadTeachers, createSchool, createTeacher } = useSchools()
  const [query, setQuery]         = useState('')
  const [selectedSchool, setSelected] = useState<School | null>(null)
  const [showNewSchool, setShowNewSchool] = useState(false)
  const [showNewTeacher, setShowNewTeacher] = useState(false)

  // New school form
  const [inep, setInep]           = useState('')
  const [sName, setSName]         = useState('')
  const [city, setCity]           = useState('')
  const [principal, setPrincipal] = useState('')
  const [saving, setSaving]       = useState(false)

  // New teacher form
  const [tName, setTName]   = useState('')
  const [tEmail, setTEmail] = useState('')
  const [tArea, setTArea]   = useState('')
  const [tEmp, setTEmp]     = useState('')

  useEffect(() => { loadSchools() }, [])
  useEffect(() => { if (selectedSchool) loadTeachers(selectedSchool.id) }, [selectedSchool])

  const filtered = schools.filter(s =>
    s.name.toLowerCase().includes(query.toLowerCase()) ||
    s.city.toLowerCase().includes(query.toLowerCase())
  )

  const handleCreateSchool = async () => {
    setSaving(true)
    const school = await createSchool({ inepCode: inep, name: sName, city, state: 'SP', principalName: principal })
    setSaving(false)
    if (school) { setShowNewSchool(false); setInep(''); setSName(''); setCity('') }
  }

  const handleCreateTeacher = async () => {
    if (!selectedSchool) return
    setSaving(true)
    const teacher = await createTeacher(selectedSchool.id, { name: tName, email: tEmail, subjectArea: tArea, employeeId: tEmp })
    setSaving(false)
    if (teacher) { setShowNewTeacher(false); setTName(''); setTEmail(''); setTArea('') }
  }

  return (
    <Layout title="Escolas">
      <div className="px-4 pt-4 pb-2 lg:px-6 lg:pt-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-lg font-bold text-gray-900 hidden lg:block">Escolas</h1>
          <button className="btn-primary ml-auto" onClick={() => setShowNewSchool(true)}>+ Escola</button>
        </div>
        <input
          className="input mb-3"
          placeholder="Buscar escola ou cidade…"
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
      </div>

      <div className="px-4 lg:px-6">
        {error && <ErrorBanner message={error} />}
        {loading ? <PageSpinner /> : filtered.length === 0 ? (
          <EmptyState icon="🏫" title="Nenhuma escola encontrada"
            action={{ label: '+ Cadastrar escola', onClick: () => setShowNewSchool(true) }} />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {filtered.map(school => (
              <SchoolCard key={school.id} school={school} onClick={() => setSelected(school)} />
            ))}
          </div>
        )}
      </div>

      {/* School detail drawer */}
      {selectedSchool && (
        <Modal title={selectedSchool.name} onClose={() => setSelected(null)}
          footer={
            <button className="btn-primary" onClick={() => setShowNewTeacher(true)}>+ Professor</button>
          }
        >
          <div className="space-y-3">
            <div className="text-xs text-gray-500 space-y-1">
              <p>🏙️ {selectedSchool.city} — SP</p>
              {selectedSchool.principalName && <p>👤 Diretor(a): {selectedSchool.principalName}</p>}
              <p className="font-mono">INEP: {selectedSchool.inepCode}</p>
            </div>
            <div className="border-t border-gray-100 pt-3">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Professores ({teachers.length})
              </p>
              {teachers.length === 0 ? (
                <p className="text-sm text-gray-400 text-center py-4">Nenhum professor cadastrado</p>
              ) : (
                <div className="space-y-2">
                  {teachers.map(t => (
                    <div key={t.id} className="flex items-center gap-3 rounded-lg bg-gray-50 px-3 py-2">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-600 text-xs font-bold">
                        {t.name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{t.name}</p>
                        <p className="text-xs text-gray-400 truncate">{t.subjectArea} · {t.email}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* New school modal */}
      {showNewSchool && (
        <Modal title="Cadastrar Escola" onClose={() => setShowNewSchool(false)} footer={
          <>
            <button className="btn-secondary" onClick={() => setShowNewSchool(false)}>Cancelar</button>
            <button className="btn-primary" onClick={handleCreateSchool} disabled={!sName || !inep || saving}>
              {saving ? 'Salvando…' : 'Cadastrar'}
            </button>
          </>
        }>
          <div className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Código INEP *</label>
              <input className="input" value={inep} onChange={e => setInep(e.target.value)} placeholder="12345678" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Nome da escola *</label>
              <input className="input" value={sName} onChange={e => setSName(e.target.value)} placeholder="EE Prof. João Silva" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Cidade *</label>
              <input className="input" value={city} onChange={e => setCity(e.target.value)} placeholder="São Paulo" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Diretor(a)</label>
              <input className="input" value={principal} onChange={e => setPrincipal(e.target.value)} placeholder="Nome do diretor(a)" /></div>
          </div>
        </Modal>
      )}

      {/* New teacher modal */}
      {showNewTeacher && selectedSchool && (
        <Modal title={`Adicionar Professor — ${selectedSchool.name}`} onClose={() => setShowNewTeacher(false)} footer={
          <>
            <button className="btn-secondary" onClick={() => setShowNewTeacher(false)}>Cancelar</button>
            <button className="btn-primary" onClick={handleCreateTeacher} disabled={!tName || !tEmail || saving}>
              {saving ? 'Salvando…' : 'Adicionar'}
            </button>
          </>
        }>
          <div className="space-y-3">
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
              <input className="input" value={tName} onChange={e => setTName(e.target.value)} /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">E-mail *</label>
              <input type="email" className="input" value={tEmail} onChange={e => setTEmail(e.target.value)} /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Componente curricular *</label>
              <input className="input" value={tArea} onChange={e => setTArea(e.target.value)} placeholder="Ex: Matemática" /></div>
            <div><label className="block text-sm font-medium text-gray-700 mb-1">Registro funcional</label>
              <input className="input" value={tEmp} onChange={e => setTEmp(e.target.value)} /></div>
          </div>
        </Modal>
      )}
    </Layout>
  )
}
