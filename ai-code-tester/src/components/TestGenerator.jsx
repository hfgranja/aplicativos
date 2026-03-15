import { useState } from 'react'

export default function TestGenerator({ generatedTests, overallScore, onReset }) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(generatedTests).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  function handleDownload() {
    const blob = new Blob([generatedTests], { type: 'text/javascript' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'generated.test.js'
    a.click()
    URL.revokeObjectURL(url)
  }

  const lineCount = generatedTests.split('\n').length
  const testCount = (generatedTests.match(/\bit\s*\(/g) || []).length
  const describeCount = (generatedTests.match(/\bdescribe\s*\(/g) || []).length

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(108,99,255,0.1), rgba(0,212,170,0.1))',
        border: '1px solid rgba(108,99,255,0.25)',
        borderRadius: 20, padding: '28px 36px', marginBottom: 28,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20,
      }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
            ✅ Testes Funcionais Gerados
          </h2>
          <p style={{ fontSize: 13, color: 'rgba(232,232,240,0.5)' }}>
            {describeCount} describe blocks · {testCount} testes · {lineCount} linhas
            &nbsp;·&nbsp; Score base: <strong style={{ color: overallScore >= 70 ? '#00C896' : '#FFB020' }}>{overallScore}/100</strong>
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={handleCopy}
            style={{
              background: copied ? 'rgba(0,200,150,0.2)' : 'rgba(108,99,255,0.15)',
              border: copied ? '1px solid rgba(0,200,150,0.4)' : '1px solid rgba(108,99,255,0.4)',
              color: copied ? '#00C896' : '#6C63FF',
              padding: '10px 20px', borderRadius: 8,
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
              transition: 'all 0.2s',
            }}
          >
            {copied ? '✓ Copiado!' : '📋 Copiar'}
          </button>

          <button
            onClick={handleDownload}
            style={{
              background: 'rgba(0,212,170,0.1)',
              border: '1px solid rgba(0,212,170,0.3)',
              color: '#00D4AA',
              padding: '10px 20px', borderRadius: 8,
              cursor: 'pointer', fontSize: 13, fontWeight: 600,
              transition: 'all 0.2s',
            }}
          >
            ⬇️ Download .test.js
          </button>

          <button
            onClick={onReset}
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.1)',
              color: 'rgba(232,232,240,0.5)',
              padding: '10px 16px', borderRadius: 8,
              cursor: 'pointer', fontSize: 13, fontWeight: 500,
              transition: 'all 0.2s',
            }}
          >
            🔄 Nova Análise
          </button>
        </div>
      </div>

      {/* Instructions */}
      <div style={{
        background: 'rgba(255,176,32,0.06)', border: '1px solid rgba(255,176,32,0.2)',
        borderRadius: 10, padding: '12px 18px', marginBottom: 20, fontSize: 12,
        color: 'rgba(255,176,32,0.8)', display: 'flex', gap: 8, alignItems: 'flex-start',
      }}>
        <span style={{ flexShrink: 0 }}>💡</span>
        <span>
          Os testes são templates baseados na análise do seu código.
          Substitua os comentários <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: 3 }}>// TODO</code> com
          lógica real e ajuste os valores de mock conforme seu domínio.
          Execute com <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: 3 }}>npx vitest</code> ou <code style={{ background: 'rgba(255,255,255,0.1)', padding: '1px 5px', borderRadius: 3 }}>npx jest</code>.
        </span>
      </div>

      {/* Code viewer */}
      <div style={{
        background: '#0A0A10',
        border: '1px solid rgba(255,255,255,0.08)',
        borderRadius: 14, overflow: 'hidden',
      }}>
        <div style={{
          background: '#13131A', padding: '10px 20px',
          borderBottom: '1px solid rgba(255,255,255,0.06)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#FF5F56' }} />
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#FFBD2E' }} />
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#27C93F' }} />
          <span style={{ marginLeft: 12, fontSize: 11, color: 'rgba(232,232,240,0.3)', fontFamily: 'JetBrains Mono, monospace' }}>
            generated.test.js
          </span>
        </div>
        <pre style={{
          margin: 0, padding: '20px 24px',
          color: '#E8E8F0', fontSize: 12, lineHeight: 1.7,
          overflowX: 'auto', overflowY: 'auto',
          maxHeight: 560, whiteSpace: 'pre',
          fontFamily: 'JetBrains Mono, monospace',
        }}>
          {generatedTests}
        </pre>
      </div>
    </div>
  )
}
