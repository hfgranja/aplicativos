import { useRef } from 'react'

const PLACEHOLDER = `// Cole seu código aqui ou carregue um arquivo
// Exemplo: componente React, função JavaScript, módulo Node.js...

export function calculateTotal(items) {
  return items.reduce((sum, item) => {
    return sum + item.price * item.quantity
  }, 0)
}

export async function fetchUserData(userId) {
  const response = await fetch('/api/users/' + userId)
  return response.json()
}`

export default function CodeInput({ code, packageJson, onCodeChange, onPkgChange, onAnalyze, error }) {
  const fileRef = useRef(null)
  const pkgRef = useRef(null)

  function handleFile(e, setter) {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = ev => setter(ev.target.result)
    reader.readAsText(file)
  }

  const hasCode = code.trim().length > 0

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: 'rgba(232,232,240,0.7)', letterSpacing: 1, textTransform: 'uppercase' }}>
            Código-Fonte para Análise
          </label>
          <button
            onClick={() => fileRef.current.click()}
            style={{
              background: 'rgba(108,99,255,0.1)',
              border: '1px solid rgba(108,99,255,0.3)',
              color: '#6C63FF',
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: 0.5,
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.target.style.background = 'rgba(108,99,255,0.2)' }}
            onMouseLeave={e => { e.target.style.background = 'rgba(108,99,255,0.1)' }}
          >
            📁 Carregar Arquivo
          </button>
          <input ref={fileRef} type="file" accept=".js,.jsx,.ts,.tsx,.py,.java,.go,.rb,.php"
            style={{ display: 'none' }} onChange={e => handleFile(e, onCodeChange)} />
        </div>

        <textarea
          value={code}
          onChange={e => onCodeChange(e.target.value)}
          placeholder={PLACEHOLDER}
          spellCheck={false}
          style={{
            width: '100%',
            height: 320,
            background: '#0D0D12',
            border: '1px solid rgba(108,99,255,0.25)',
            borderRadius: 12,
            padding: '16px 20px',
            color: '#E8E8F0',
            fontSize: 13,
            lineHeight: 1.7,
            resize: 'vertical',
            outline: 'none',
            transition: 'border-color 0.2s',
            fontFamily: 'JetBrains Mono, monospace',
          }}
          onFocus={e => { e.target.style.borderColor = 'rgba(108,99,255,0.6)' }}
          onBlur={e => { e.target.style.borderColor = 'rgba(108,99,255,0.25)' }}
        />
        <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.3)', marginTop: 6, textAlign: 'right' }}>
          {code.split('\n').length} linhas · {code.length} caracteres
        </div>
      </div>

      {/* Optional package.json */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: 'rgba(232,232,240,0.7)', letterSpacing: 1, textTransform: 'uppercase' }}>
            package.json <span style={{ fontWeight: 400, opacity: 0.5, textTransform: 'none', letterSpacing: 0 }}>(opcional — melhora análise de dependências)</span>
          </label>
          <button
            onClick={() => pkgRef.current.click()}
            style={{
              background: 'rgba(78,205,196,0.1)',
              border: '1px solid rgba(78,205,196,0.3)',
              color: '#4ECDC4',
              padding: '6px 14px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              letterSpacing: 0.5,
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { e.target.style.background = 'rgba(78,205,196,0.2)' }}
            onMouseLeave={e => { e.target.style.background = 'rgba(78,205,196,0.1)' }}
          >
            📁 package.json
          </button>
          <input ref={pkgRef} type="file" accept=".json" style={{ display: 'none' }}
            onChange={e => handleFile(e, onPkgChange)} />
        </div>

        <textarea
          value={packageJson}
          onChange={e => onPkgChange(e.target.value)}
          placeholder='{"name": "meu-projeto", "dependencies": {...}}'
          spellCheck={false}
          style={{
            width: '100%',
            height: 100,
            background: '#0D0D12',
            border: '1px solid rgba(78,205,196,0.2)',
            borderRadius: 12,
            padding: '12px 20px',
            color: '#E8E8F0',
            fontSize: 13,
            resize: 'vertical',
            outline: 'none',
            transition: 'border-color 0.2s',
            fontFamily: 'JetBrains Mono, monospace',
          }}
          onFocus={e => { e.target.style.borderColor = 'rgba(78,205,196,0.5)' }}
          onBlur={e => { e.target.style.borderColor = 'rgba(78,205,196,0.2)' }}
        />
      </div>

      {error && (
        <div style={{
          background: 'rgba(255,77,109,0.1)', border: '1px solid rgba(255,77,109,0.3)',
          borderRadius: 8, padding: '10px 16px', marginBottom: 20, color: '#FF4D6D', fontSize: 13,
        }}>
          ⚠️ {error}
        </div>
      )}

      <div style={{ textAlign: 'center' }}>
        <button
          onClick={onAnalyze}
          disabled={!hasCode}
          style={{
            background: hasCode
              ? 'linear-gradient(135deg, #6C63FF, #00D4AA)'
              : 'rgba(255,255,255,0.05)',
            border: 'none',
            color: hasCode ? '#fff' : 'rgba(255,255,255,0.2)',
            padding: '16px 56px',
            borderRadius: 12,
            cursor: hasCode ? 'pointer' : 'not-allowed',
            fontSize: 16,
            fontWeight: 700,
            letterSpacing: 1,
            transition: 'all 0.3s',
            boxShadow: hasCode ? '0 8px 30px rgba(108,99,255,0.35)' : 'none',
          }}
          onMouseEnter={e => { if (hasCode) e.target.style.transform = 'translateY(-2px)' }}
          onMouseLeave={e => { e.target.style.transform = 'none' }}
        >
          🔬 Analisar com 12 Técnicas
        </button>
        {!hasCode && (
          <p style={{ marginTop: 10, fontSize: 12, color: 'rgba(232,232,240,0.35)' }}>
            Cole seu código acima para começar
          </p>
        )}
      </div>
    </div>
  )
}
