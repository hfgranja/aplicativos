import { NavLink, useNavigate } from 'react-router-dom'
import { type ReactNode } from 'react'
import { useAuth } from '../../viewModels/useAuth'

const NAV_ITEMS = [
  { to: '/observacoes',   label: 'Observações',  icon: '📋' },
  { to: '/escolas',       label: 'Escolas',      icon: '🏫' },
  { to: '/biblioteca',    label: 'Biblioteca',   icon: '📚' },
  { to: '/boas-praticas', label: 'Boas Práticas', icon: '⭐' },
  { to: '/sincronizar',   label: 'Sincronizar',  icon: '🔄' },
]

interface Props { children: ReactNode; title?: string }

export function Layout({ children, title }: Props) {
  const { logout, currentUser } = useAuth()
  const navigate = useNavigate()
  const user = currentUser()

  return (
    <div className="flex h-dvh flex-col bg-gray-50 lg:flex-row">
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:w-64 lg:flex-col lg:border-r lg:border-gray-200 lg:bg-white">
        <div className="flex h-16 items-center gap-3 border-b border-gray-100 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-seduc-blue text-white text-sm font-bold">
            SP
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 leading-tight">PEC Observation</p>
            <p className="text-xs text-gray-400">SEDUC-SP</p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-50 text-seduc-blue'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        {user && (
          <div className="border-t border-gray-100 p-3">
            <div className="flex items-center gap-3 rounded-lg px-2 py-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 text-brand-600 text-xs font-semibold uppercase">
                {user.full_name?.charAt(0) ?? 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">{user.full_name}</p>
                <p className="text-xs text-gray-400 truncate">{user.email}</p>
              </div>
              <button onClick={logout} title="Sair" className="text-gray-400 hover:text-red-500 transition-colors text-sm">
                ↩
              </button>
            </div>
          </div>
        )}
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-4 lg:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-md bg-seduc-blue text-white text-xs font-bold">SP</div>
            <span className="text-sm font-semibold text-gray-900">{title ?? 'PEC Observation'}</span>
          </div>
          {user && (
            <button onClick={logout} className="text-sm text-gray-400 hover:text-red-500">Sair</button>
          )}
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto pb-20 lg:pb-0">
          {children}
        </main>

        {/* Mobile bottom tab bar */}
        <nav className="fixed bottom-0 left-0 right-0 z-40 flex border-t border-gray-200 bg-white pb-safe lg:hidden">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-1 flex-col items-center justify-center gap-0.5 py-2 text-xs font-medium transition-colors ${
                  isActive ? 'text-seduc-blue' : 'text-gray-400 hover:text-gray-700'
                }`
              }
            >
              <span className="text-xl leading-none">{item.icon}</span>
              <span className="text-[10px] leading-tight">{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>
    </div>
  )
}
