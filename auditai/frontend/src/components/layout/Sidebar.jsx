import { NavLink } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

const NAV = [
  { to: '/', label: 'Dashboard', icon: '◎' },
  { to: '/applications', label: 'Applications', icon: '▦' },
  { to: '/executions', label: 'Executions', icon: '▶' },
  { to: '/findings', label: 'Findings', icon: '⚠' },
  { to: '/releases', label: 'Releases', icon: '⬡' },
  { to: '/policies', label: 'Policies', icon: '⚖' },
  { to: '/audit', label: 'Audit Log', icon: '⧉' },
  { to: '/admin', label: 'Admin', icon: '⚙' },
]

const s = {
  sidebar: { width: 240, background: '#161b27', borderRight: '1px solid #1e2535', display: 'flex', flexDirection: 'column', padding: '0 0 24px 0' },
  logo: { padding: '20px 20px 16px', borderBottom: '1px solid #1e2535', marginBottom: 8 },
  logoText: { fontSize: 18, fontWeight: 700, color: '#60a5fa', letterSpacing: 1 },
  logoSub: { fontSize: 11, color: '#64748b', marginTop: 2 },
  nav: { flex: 1 },
  link: { display: 'flex', alignItems: 'center', gap: 10, padding: '10px 20px', color: '#94a3b8', textDecoration: 'none', fontSize: 14, transition: 'all 0.15s' },
  activeLink: { color: '#60a5fa', background: '#1e2d4a', borderLeft: '3px solid #60a5fa' },
  icon: { fontSize: 16, width: 20, textAlign: 'center' },
  user: { padding: '12px 20px', borderTop: '1px solid #1e2535', fontSize: 12, color: '#64748b' },
  logoutBtn: { background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: 12, marginTop: 4, padding: 0 },
}

export default function Sidebar() {
  const { user, logout } = useAuth()
  return (
    <aside style={s.sidebar}>
      <div style={s.logo}>
        <div style={s.logoText}>AuditAI</div>
        <div style={s.logoSub}>Test Platform</div>
      </div>
      <nav style={s.nav}>
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({ ...s.link, ...(isActive ? s.activeLink : {}) })}
          >
            <span style={s.icon}>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div style={s.user}>
        <div>{user?.full_name || user?.email}</div>
        <div style={{ fontSize: 11, color: '#475569' }}>{user?.email}</div>
        <button style={s.logoutBtn} onClick={logout}>Sign out</button>
      </div>
    </aside>
  )
}
