import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const s = {
  page: { minHeight: '100vh', background: '#0f1117', display: 'flex', alignItems: 'center', justifyContent: 'center' },
  card: { background: '#161b27', border: '1px solid #1e2535', borderRadius: 12, padding: 40, width: 380 },
  logo: { fontSize: 24, fontWeight: 700, color: '#60a5fa', marginBottom: 4 },
  sub: { fontSize: 13, color: '#64748b', marginBottom: 32 },
  label: { display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 6 },
  input: { width: '100%', background: '#0f1117', border: '1px solid #1e2535', borderRadius: 6, padding: '10px 12px', color: '#e2e8f0', fontSize: 14, outline: 'none', marginBottom: 16 },
  btn: { width: '100%', background: '#1d4ed8', color: '#fff', border: 'none', borderRadius: 6, padding: '12px', fontSize: 14, fontWeight: 600, cursor: 'pointer' },
  error: { color: '#f87171', fontSize: 13, marginBottom: 12 },
}

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <div style={s.logo}>AuditAI</div>
        <div style={s.sub}>Test Platform — Sign in to continue</div>
        {error && <div style={s.error}>{error}</div>}
        <form onSubmit={handleSubmit}>
          <label style={s.label}>Email</label>
          <input style={s.input} type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="admin@auditai.local" />
          <label style={s.label}>Password</label>
          <input style={s.input} type="password" value={password} onChange={e => setPassword(e.target.value)} required />
          <button style={s.btn} type="submit" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
