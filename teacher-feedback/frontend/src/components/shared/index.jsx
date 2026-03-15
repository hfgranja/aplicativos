import { C } from '../../colors'

export function Card({ children, style }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 12, padding: 24, ...style
    }}>
      {children}
    </div>
  )
}

export function Button({ children, onClick, variant = 'primary', disabled, style, type = 'button' }) {
  const variants = {
    primary: { background: C.accent, color: '#fff', border: 'none' },
    secondary: { background: C.surface2, color: C.text, border: `1px solid ${C.border}` },
    danger: { background: C.danger, color: '#fff', border: 'none' },
    ghost: { background: 'transparent', color: C.textMuted, border: `1px solid ${C.border}` },
    success: { background: C.success, color: '#fff', border: 'none' },
  }
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      style={{
        ...variants[variant],
        borderRadius: 8, padding: '10px 20px', cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1, fontFamily: 'JetBrains Mono', fontSize: 13,
        fontWeight: 600, transition: 'opacity 0.15s', ...style,
      }}
    >
      {children}
    </button>
  )
}

export function Input({ label, value, onChange, placeholder, type = 'text', style }) {
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', color: C.textMuted, fontSize: 12, marginBottom: 6 }}>{label}</label>}
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        style={{
          width: '100%', background: C.surface2, border: `1px solid ${C.border}`,
          borderRadius: 8, padding: '10px 14px', color: C.text,
          fontFamily: 'JetBrains Mono', fontSize: 13, boxSizing: 'border-box', ...style
        }}
      />
    </div>
  )
}

export function Textarea({ label, value, onChange, placeholder, rows = 3, style }) {
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', color: C.textMuted, fontSize: 12, marginBottom: 6 }}>{label}</label>}
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        style={{
          width: '100%', background: C.surface2, border: `1px solid ${C.border}`,
          borderRadius: 8, padding: '10px 14px', color: C.text,
          fontFamily: 'JetBrains Mono', fontSize: 13, resize: 'vertical',
          boxSizing: 'border-box', ...style
        }}
      />
    </div>
  )
}

export function Select({ label, value, onChange, options, style }) {
  return (
    <div style={{ marginBottom: 16 }}>
      {label && <label style={{ display: 'block', color: C.textMuted, fontSize: 12, marginBottom: 6 }}>{label}</label>}
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        style={{
          width: '100%', background: C.surface2, border: `1px solid ${C.border}`,
          borderRadius: 8, padding: '10px 14px', color: value ? C.text : C.textMuted,
          fontFamily: 'JetBrains Mono', fontSize: 13, boxSizing: 'border-box', ...style
        }}
      >
        {options.map(o => (
          <option key={o.value} value={o.value} style={{ background: C.surface2 }}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export function Badge({ children, color = C.accent }) {
  return (
    <span style={{
      background: color + '22', color, borderRadius: 6, padding: '3px 10px',
      fontSize: 11, fontWeight: 700, display: 'inline-block',
    }}>
      {children}
    </span>
  )
}

export function Spinner() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}>
      <div style={{
        width: 32, height: 32, border: `3px solid ${C.border}`,
        borderTop: `3px solid ${C.accent}`, borderRadius: '50%',
        animation: 'spin 0.8s linear infinite',
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export function ErrorBanner({ message }) {
  return message ? (
    <div style={{
      background: C.danger + '22', border: `1px solid ${C.danger}`,
      borderRadius: 8, padding: '12px 16px', color: C.danger, marginBottom: 16, fontSize: 13,
    }}>
      ⚠ {message}
    </div>
  ) : null
}

export function ScoreBar({ score, color, label }) {
  return (
    <div style={{ marginBottom: 8 }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: 11, color: C.textMuted }}>{label}</span>
          <span style={{ fontSize: 11, color, fontWeight: 700 }}>{score}</span>
        </div>
      )}
      <div style={{ background: C.surface3, borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{ width: `${score}%`, background: color, height: '100%', borderRadius: 4, transition: 'width 0.6s ease' }} />
      </div>
    </div>
  )
}
