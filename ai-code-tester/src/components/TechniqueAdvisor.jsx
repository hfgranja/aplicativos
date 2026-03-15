import { useState } from 'react'
import { exportAsJSONL, clearAll } from '../services/trainingDataService.js'

const STATUS_LABELS = {
  idle: null,
  'querying-qwen': '🔍 Consultando Qwen3-coder...',
  'querying-devstral': '🔬 Refinando com Devstral 2...',
  ready: null,
  error: '⚠️ Erro ao consultar modelo',
}

const PRIORITY_COLORS = {
  high: '#FF4D6D',
  medium: '#FFB020',
  low: '#00D4AA',
}

const MODEL_BADGES = {
  composed: { label: 'Devstral 2 + Qwen3', color: '#E040FB' },
  devstral: { label: 'Devstral 2', color: '#6C63FF' },
  qwen3: { label: 'Qwen3-coder', color: '#45B7D1' },
}

export default function TechniqueAdvisor({ advisor, onConfigUpdate }) {
  const [showConfig, setShowConfig] = useState(false)
  const [configForm, setConfigForm] = useState({
    ollamaUrl: advisor.ollamaUrl,
    devstralModel: advisor.devstralModel,
    qwenModel: advisor.qwenModel,
  })
  const [exporting, setExporting] = useState(false)
  const [clearing, setClearing] = useState(false)

  const {
    suggestions = [],
    status,
    ollamaAvailable,
    devstralAvailable,
    qwenAvailable,
    trainingCount,
    avgScore,
    topWeakArea,
  } = advisor

  function getStatusBadge() {
    if (ollamaAvailable === null) return { color: 'rgba(255,255,255,0.3)', label: '⏳ Verificando Ollama...' }
    if (!ollamaAvailable) return { color: '#FF4D6D', label: '🔴 Ollama offline' }
    if (devstralAvailable && qwenAvailable) return { color: '#00D4AA', label: '🟢 Devstral 2 + Qwen3-coder ativos' }
    if (qwenAvailable) return { color: '#FFB020', label: '🟡 Apenas Qwen3-coder ativo' }
    if (devstralAvailable) return { color: '#FFB020', label: '🟡 Apenas Devstral 2 ativo' }
    return { color: '#FF4D6D', label: '🔴 Nenhum modelo encontrado' }
  }

  async function handleExport() {
    setExporting(true)
    try {
      const jsonl = await exportAsJSONL()
      if (!jsonl.trim()) { setExporting(false); return }
      const blob = new Blob([jsonl], { type: 'application/x-ndjson' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai-code-tester-training-${Date.now()}.jsonl`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setExporting(false)
    }
  }

  async function handleClear() {
    if (!confirm('Limpar todos os dados de treinamento acumulados?')) return
    setClearing(true)
    try { await clearAll() } finally { setClearing(false) }
    if (onConfigUpdate) onConfigUpdate({})  // trigger re-check stats
  }

  function handleConfigSave() {
    if (onConfigUpdate) onConfigUpdate(configForm)
    setShowConfig(false)
  }

  const statusBadge = getStatusBadge()
  const loadingLabel = STATUS_LABELS[status]
  const isLoading = status === 'querying-qwen' || status === 'querying-devstral'

  return (
    <div style={{
      marginTop: 40,
      border: '1px solid rgba(224,64,251,0.2)',
      borderRadius: 14,
      background: 'rgba(224,64,251,0.04)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid rgba(224,64,251,0.12)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>🤖</span>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#E040FB' }}>
              Sugestão de Novas Técnicas
            </div>
            <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.4)' }}>
              Motor de aprendizado contínuo · Devstral 2 + Qwen3-coder-next
            </div>
          </div>
        </div>

        {/* Status badge */}
        <span style={{
          fontSize: 11, padding: '4px 12px', borderRadius: 20,
          background: `${statusBadge.color}15`,
          border: `1px solid ${statusBadge.color}40`,
          color: statusBadge.color, fontWeight: 600,
        }}>
          {statusBadge.label}
        </span>
      </div>

      <div style={{ padding: '16px 20px' }}>
        {/* Ollama offline instructions */}
        {ollamaAvailable === false && (
          <div style={{
            background: 'rgba(255,77,109,0.06)', border: '1px solid rgba(255,77,109,0.2)',
            borderRadius: 10, padding: '14px 16px', marginBottom: 16,
            fontSize: 12, color: 'rgba(232,232,240,0.7)', lineHeight: 1.7,
          }}>
            <div style={{ fontWeight: 700, color: '#FF4D6D', marginBottom: 8 }}>
              Configure o Ollama para ativar as sugestões:
            </div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', background: 'rgba(0,0,0,0.3)', borderRadius: 6, padding: '8px 12px', marginBottom: 8 }}>
              <div style={{ color: '#98D8C8' }}># 1. Instale: <a href="https://ollama.com" target="_blank" rel="noreferrer" style={{ color: '#E040FB' }}>ollama.com</a></div>
              <div style={{ color: '#98D8C8' }}># 2. Inicie com CORS:</div>
              <div>OLLAMA_ORIGINS=&quot;http://localhost:5173&quot; ollama serve</div>
              <div style={{ color: '#98D8C8', marginTop: 4 }}># 3. Baixe os modelos (em terminais separados):</div>
              <div>ollama pull {advisor.qwenModel || 'qwen3-coder'}</div>
              <div>ollama pull {advisor.devstralModel || 'devstral'}</div>
            </div>
            <div style={{ color: 'rgba(232,232,240,0.4)', fontSize: 11 }}>
              Os dados já estão sendo acumulados. As sugestões aparecerão assim que o Ollama for configurado.
            </div>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 10,
            padding: '12px 16px', marginBottom: 16,
            background: 'rgba(224,64,251,0.06)', borderRadius: 8,
            fontSize: 13, color: '#E040FB',
          }}>
            <Spinner color="#E040FB" />
            {loadingLabel}
          </div>
        )}

        {/* Suggestion cards */}
        {suggestions.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(232,232,240,0.5)', letterSpacing: 1, textTransform: 'uppercase', marginBottom: 12 }}>
              Técnicas Sugeridas pelo Modelo
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {suggestions.map((s, i) => {
                const pColor = PRIORITY_COLORS[s.priority] || '#00D4AA'
                const mBadge = MODEL_BADGES[s.model] || MODEL_BADGES.qwen3
                return (
                  <div key={i} style={{
                    background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
                    borderRadius: 10, padding: '14px 16px',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontSize: 18 }}>{s.icon || '💡'}</span>
                        <span style={{ fontSize: 14, fontWeight: 700, color: '#E8E8F0' }}>{s.name}</span>
                      </div>
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                        <span style={{
                          fontSize: 10, padding: '2px 8px', borderRadius: 20,
                          background: `${pColor}15`, border: `1px solid ${pColor}40`,
                          color: pColor, fontWeight: 600, textTransform: 'uppercase',
                        }}>
                          {s.priority || 'medium'}
                        </span>
                        <span style={{
                          fontSize: 10, padding: '2px 8px', borderRadius: 20,
                          background: `${mBadge.color}15`, border: `1px solid ${mBadge.color}30`,
                          color: mBadge.color, fontWeight: 500,
                        }}>
                          {mBadge.label}
                        </span>
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: 'rgba(232,232,240,0.7)', marginBottom: 6, lineHeight: 1.6 }}>
                      {s.description}
                    </div>
                    {s.rationale && (
                      <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.45)', marginBottom: 6, fontStyle: 'italic' }}>
                        💬 {s.rationale}
                      </div>
                    )}
                    {s.implementationHint && (
                      <div style={{
                        fontSize: 11, color: '#98D8C8',
                        background: 'rgba(152,216,200,0.06)', borderRadius: 6,
                        padding: '6px 10px', fontFamily: 'JetBrains Mono, monospace',
                      }}>
                        🔧 {s.implementationHint}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Training data stats */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
          padding: '10px 14px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, marginBottom: 14,
          fontSize: 12, color: 'rgba(232,232,240,0.5)',
        }}>
          <div style={{ display: 'flex', gap: 16 }}>
            <span>
              📊 <strong style={{ color: '#E040FB' }}>{trainingCount || 0}</strong> análise(s) acumulada(s)
            </span>
            {avgScore !== null && avgScore !== undefined && (
              <span>score médio: <strong style={{ color: 'rgba(232,232,240,0.7)' }}>{avgScore}/100</strong></span>
            )}
            {topWeakArea && (
              <span>área mais fraca: <strong style={{ color: '#FFB020' }}>{topWeakArea}</strong></span>
            )}
          </div>
          <div style={{ fontSize: 10, color: 'rgba(232,232,240,0.25)' }}>
            Dados salvos localmente (IndexedDB)
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={handleExport}
            disabled={exporting || !trainingCount}
            style={{
              fontSize: 12, padding: '7px 14px', borderRadius: 7, cursor: trainingCount ? 'pointer' : 'not-allowed',
              background: trainingCount ? 'rgba(224,64,251,0.1)' : 'rgba(255,255,255,0.03)',
              border: `1px solid ${trainingCount ? 'rgba(224,64,251,0.3)' : 'rgba(255,255,255,0.08)'}`,
              color: trainingCount ? '#E040FB' : 'rgba(232,232,240,0.25)',
              fontWeight: 600,
            }}
          >
            {exporting ? '⏳ Exportando...' : '⬇️ Exportar dados de treino (.jsonl)'}
          </button>

          <button
            onClick={() => setShowConfig(c => !c)}
            style={{
              fontSize: 12, padding: '7px 14px', borderRadius: 7, cursor: 'pointer',
              background: showConfig ? 'rgba(108,99,255,0.1)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${showConfig ? 'rgba(108,99,255,0.3)' : 'rgba(255,255,255,0.1)'}`,
              color: showConfig ? '#6C63FF' : 'rgba(232,232,240,0.45)',
              fontWeight: 500,
            }}
          >
            ⚙️ Configurar Ollama
          </button>

          {trainingCount > 0 && (
            <button
              onClick={handleClear}
              disabled={clearing}
              style={{
                fontSize: 12, padding: '7px 14px', borderRadius: 7, cursor: 'pointer',
                background: 'rgba(255,77,109,0.05)', border: '1px solid rgba(255,77,109,0.15)',
                color: 'rgba(255,77,109,0.6)', fontWeight: 500,
              }}
            >
              {clearing ? '⏳' : '🗑️'} Limpar histórico
            </button>
          )}
        </div>

        {/* Config panel */}
        {showConfig && (
          <div style={{
            marginTop: 14, padding: '14px 16px',
            background: 'rgba(255,255,255,0.03)', borderRadius: 10,
            border: '1px solid rgba(255,255,255,0.08)',
          }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'rgba(232,232,240,0.6)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 }}>
              Configuração Ollama
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'URL base do Ollama', key: 'ollamaUrl', placeholder: 'http://localhost:11434' },
                { label: 'Modelo Qwen3 (gerador)', key: 'qwenModel', placeholder: 'qwen3-coder' },
                { label: 'Modelo Devstral (crítico)', key: 'devstralModel', placeholder: 'devstral' },
              ].map(({ label, key, placeholder }) => (
                <div key={key}>
                  <label style={{ fontSize: 11, color: 'rgba(232,232,240,0.5)', display: 'block', marginBottom: 4 }}>
                    {label}
                  </label>
                  <input
                    type="text"
                    value={configForm[key]}
                    onChange={e => setConfigForm(f => ({ ...f, [key]: e.target.value }))}
                    placeholder={placeholder}
                    style={{
                      width: '100%', background: '#0D0D12', border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: 6, padding: '7px 12px', color: '#E8E8F0', fontSize: 12, outline: 'none',
                      fontFamily: 'JetBrains Mono, monospace',
                    }}
                  />
                </div>
              ))}
              <button
                onClick={handleConfigSave}
                style={{
                  alignSelf: 'flex-start', fontSize: 12, padding: '7px 16px', borderRadius: 7, cursor: 'pointer',
                  background: 'linear-gradient(135deg, #6C63FF, #E040FB)', border: 'none',
                  color: '#fff', fontWeight: 700,
                }}
              >
                ✓ Salvar e verificar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function Spinner({ color = '#E040FB' }) {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14, flexShrink: 0,
      border: `2px solid ${color}30`,
      borderTopColor: color, borderRadius: '50%',
      animation: 'spin 0.6s linear infinite',
    }} />
  )
}
