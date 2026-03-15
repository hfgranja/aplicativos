import { NavLink } from 'react-router-dom'
import { C } from '../../colors'

const links = [
  { to: '/', label: 'Início', icon: '⌂' },
  { to: '/professores', label: 'Professores', icon: '👤' },
  { to: '/nova-observacao', label: 'Nova Observação', icon: '+' },
  { to: '/historico', label: 'Histórico', icon: '≡' },
  { to: '/evolucao', label: 'Evolução', icon: '↗' },
]

export function Sidebar() {
  return (
    <aside style={{
      width: 220, background: C.surface, borderRight: `1px solid ${C.border}`,
      padding: '24px 0', display: 'flex', flexDirection: 'column', flexShrink: 0, minHeight: '100vh',
    }}>
      <div style={{ padding: '0 20px 24px', borderBottom: `1px solid ${C.border}`, marginBottom: 16 }}>
        <div style={{ color: C.accent, fontSize: 14, fontWeight: 700 }}>PEC Feedback</div>
        <div style={{ color: C.textMuted, fontSize: 11, marginTop: 2 }}>Acompanhamento Pedagógico</div>
      </div>
      <nav>
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px',
              color: isActive ? C.accent : C.textMuted, textDecoration: 'none',
              background: isActive ? C.accent + '11' : 'transparent',
              borderLeft: `3px solid ${isActive ? C.accent : 'transparent'}`,
              fontSize: 13, fontFamily: 'JetBrains Mono', transition: 'all 0.15s',
            })}
          >
            <span style={{ fontSize: 16 }}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
