import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../adapters/ui/viewModels/useAuth'
import { Spinner } from '../adapters/ui/components/common/Spinner'

export function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const { login, loading, error } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    const ok = await login(email, password)
    if (ok) navigate('/observacoes', { replace: true })
  }

  return (
    <div className="min-h-dvh flex flex-col items-center justify-center bg-gradient-to-br from-seduc-blue via-brand-700 to-brand-900 px-4">
      {/* Card */}
      <div className="w-full max-w-sm bg-white rounded-2xl shadow-2xl overflow-hidden">
        {/* Header stripe */}
        <div className="bg-seduc-yellow h-1.5 w-full" />
        <div className="px-8 py-8">
          {/* Logo area */}
          <div className="flex flex-col items-center mb-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-seduc-blue text-white text-2xl font-bold shadow-lg mb-3">
              SP
            </div>
            <h1 className="text-xl font-bold text-gray-900">PEC Observation</h1>
            <p className="text-xs text-gray-400 mt-0.5">Secretaria da Educação do Estado de São Paulo</p>
          </div>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">E-mail</label>
              <input
                type="email"
                className="input"
                placeholder="pec@educacao.sp.gov.br"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Senha</label>
              <input
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
              {loading ? <Spinner size="sm" /> : 'Entrar'}
            </button>
          </form>
        </div>
        <div className="bg-gray-50 px-8 py-3 text-center">
          <p className="text-xs text-gray-400">
            Acesso restrito a PECs credenciados pela SEDUC-SP
          </p>
        </div>
      </div>

      <p className="mt-6 text-xs text-white/40">© 2026 SEDUC-SP — Sistema PEC Observation</p>
    </div>
  )
}
