import { useState } from 'react'
import { TOKEN_SCOPES, parseRepoUrl } from '../services/gitService.js'

const PROVIDERS = [
  { id: 'github', label: 'GitHub', color: '#6C63FF', icon: '🐙' },
  { id: 'gitlab', label: 'GitLab', color: '#FF6B6B', icon: '🦊' },
  { id: 'bitbucket', label: 'Bitbucket', color: '#45B7D1', icon: '🪣' },
  { id: 'azure', label: 'Azure DevOps', color: '#FFB020', icon: '☁️' },
]

export default function RepoConnect({ git, onConnect, connecting, connectionError }) {
  const [showToken, setShowToken] = useState(false)
  const [showEnterprise, setShowEnterprise] = useState(false)
  const [showScopes, setShowScopes] = useState(false)

  const provider = git.provider || 'github'
  const scopeInfo = TOKEN_SCOPES[provider]
  const pColor = PROVIDERS.find(p => p.id === provider)?.color || '#6C63FF'

  function handleRepoUrl(val) {
    const { owner, repo } = parseRepoUrl(val)
    onConnect({ ...git, _repoInput: val, owner: owner || git.owner, repo: repo || git.repo })
  }

  function handleSubmit(e) {
    e.preventDefault()
    onConnect(git, true) // true = trigger actual connection
  }

  const canConnect = git.owner && git.repo

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%' }}>
      {/* Provider selector */}
      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Provedor Git</label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {PROVIDERS.map(p => {
            const active = provider === p.id
            return (
              <button
                key={p.id}
                type="button"
                onClick={() => onConnect({ ...git, provider: p.id })}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '8px 14px', borderRadius: 8, cursor: 'pointer',
                  background: active ? `${p.color}20` : 'rgba(255,255,255,0.04)',
                  border: `1.5px solid ${active ? p.color : 'rgba(255,255,255,0.1)'}`,
                  color: active ? p.color : 'rgba(232,232,240,0.5)',
                  fontSize: 13, fontWeight: active ? 700 : 400,
                  transition: 'all 0.2s',
                }}
              >
                <span>{p.icon}</span> {p.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Enterprise URL toggle */}
      <div style={{ marginBottom: 16 }}>
        <button
          type="button"
          onClick={() => setShowEnterprise(e => !e)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: 'rgba(232,232,240,0.4)', fontSize: 12,
            display: 'flex', alignItems: 'center', gap: 4,
          }}
        >
          {showEnterprise ? '▼' : '▶'} Usar URL Enterprise / Self-hosted
        </button>

        {showEnterprise && (
          <div style={{ marginTop: 8 }}>
            <input
              type="url"
              value={git.baseUrl || ''}
              onChange={e => onConnect({ ...git, baseUrl: e.target.value })}
              placeholder={
                provider === 'github' ? 'https://github.empresa.com/api/v3' :
                provider === 'gitlab' ? 'https://gitlab.empresa.com/api/v4' :
                provider === 'azure' ? 'https://dev.azure.com' : ''
              }
              style={inputStyle}
            />
          </div>
        )}
      </div>

      {/* Owner / Repo — accept URL or separate fields */}
      <div style={{ marginBottom: 14 }}>
        <label style={labelStyle}>
          URL ou Caminho do Repositório
        </label>
        <input
          type="text"
          value={git._repoInput || (git.owner && git.repo ? `${git.owner}/${git.repo}` : '')}
          onChange={e => handleRepoUrl(e.target.value)}
          placeholder="ex: facebook/react  ou  https://github.com/user/repo"
          style={inputStyle}
        />
        {git.owner && git.repo && (
          <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.35)', marginTop: 4 }}>
            Proprietário: <strong style={{ color: pColor }}>{git.owner}</strong> · Repositório: <strong style={{ color: pColor }}>{git.repo}</strong>
          </div>
        )}
      </div>

      {/* Branch */}
      <div style={{ marginBottom: 14 }}>
        <label style={labelStyle}>Branch</label>
        <input
          type="text"
          value={git.branch || 'main'}
          onChange={e => onConnect({ ...git, branch: e.target.value })}
          placeholder="main"
          style={{ ...inputStyle, maxWidth: 180 }}
        />
      </div>

      {/* Bitbucket username */}
      {provider === 'bitbucket' && (
        <div style={{ marginBottom: 14 }}>
          <label style={labelStyle}>Usuário Bitbucket</label>
          <input
            type="text"
            value={git.username || ''}
            onChange={e => onConnect({ ...git, username: e.target.value })}
            placeholder="seu-usuario-bitbucket"
            style={{ ...inputStyle, maxWidth: 280 }}
          />
        </div>
      )}

      {/* Token */}
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
          <label style={labelStyle}>
            {scopeInfo?.label || 'Token de Acesso'}
            <span style={{ fontWeight: 400, opacity: 0.5, marginLeft: 6, textTransform: 'none', letterSpacing: 0 }}>
              (opcional para repos públicos)
            </span>
          </label>
          <button
            type="button"
            onClick={() => setShowScopes(s => !s)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 11, color: pColor }}
          >
            📋 Como criar
          </button>
        </div>

        <div style={{ position: 'relative' }}>
          <input
            type={showToken ? 'text' : 'password'}
            value={git.token || ''}
            onChange={e => onConnect({ ...git, token: e.target.value })}
            placeholder="ghp_xxxxxxxxxxxx  (armazenado apenas em memória)"
            autoComplete="off"
            style={{ ...inputStyle, paddingRight: 44 }}
          />
          <button
            type="button"
            onClick={() => setShowToken(s => !s)}
            title={showToken ? 'Ocultar token' : 'Mostrar token'}
            style={{
              position: 'absolute', right: 10, top: '50%', transform: 'translateY(-50%)',
              background: 'none', border: 'none', cursor: 'pointer', fontSize: 14,
              color: 'rgba(232,232,240,0.4)',
            }}
          >
            {showToken ? '🙈' : '👁'}
          </button>
        </div>
      </div>

      {/* Token scope info */}
      {showScopes && scopeInfo && (
        <div style={{
          background: `${pColor}10`, border: `1px solid ${pColor}25`,
          borderRadius: 8, padding: '10px 14px', marginBottom: 14, fontSize: 12,
        }}>
          <div style={{ color: pColor, fontWeight: 600, marginBottom: 4 }}>
            Como criar um token de leitura ({scopeInfo.label}):
          </div>
          <div style={{ color: 'rgba(232,232,240,0.7)', lineHeight: 1.6 }}>
            <div>1. {scopeInfo.steps}</div>
            <div>2. Escopo necessário: <code style={{ background: 'rgba(255,255,255,0.08)', padding: '1px 5px', borderRadius: 3 }}>{scopeInfo.scopes}</code></div>
            <div style={{ marginTop: 4 }}>
              <a href={scopeInfo.url} target="_blank" rel="noreferrer"
                style={{ color: pColor, textDecoration: 'underline' }}>
                Abrir configurações de token →
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Security notice */}
      <div style={{
        background: 'rgba(0,200,150,0.05)', border: '1px solid rgba(0,200,150,0.15)',
        borderRadius: 6, padding: '8px 12px', marginBottom: 16,
        fontSize: 11, color: 'rgba(0,200,150,0.7)', lineHeight: 1.5,
      }}>
        🔒 Token armazenado apenas na memória desta sessão · Nunca enviado a servidores externos ·
        Somente operações de leitura · Limpo ao desconectar
      </div>

      {/* Error */}
      {connectionError && (
        <div style={{
          background: 'rgba(255,77,109,0.1)', border: '1px solid rgba(255,77,109,0.3)',
          borderRadius: 8, padding: '10px 14px', marginBottom: 14,
          fontSize: 13, color: '#FF4D6D',
        }}>
          ⚠️ {connectionError}
        </div>
      )}

      {/* Connect button */}
      <button
        type="submit"
        disabled={!canConnect || connecting}
        style={{
          width: '100%',
          background: canConnect && !connecting
            ? `linear-gradient(135deg, ${pColor}, ${pColor}aa)`
            : 'rgba(255,255,255,0.05)',
          border: 'none',
          color: canConnect && !connecting ? '#fff' : 'rgba(255,255,255,0.2)',
          padding: '13px 24px', borderRadius: 10,
          cursor: canConnect && !connecting ? 'pointer' : 'not-allowed',
          fontSize: 14, fontWeight: 700, letterSpacing: 0.5,
          transition: 'all 0.2s',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
        }}
      >
        {connecting
          ? <><Spinner /> Conectando...</>
          : `🔌 Conectar ao Repositório`
        }
      </button>
    </form>
  )
}

function Spinner() {
  return (
    <span style={{
      display: 'inline-block', width: 14, height: 14,
      border: '2px solid rgba(255,255,255,0.3)',
      borderTopColor: '#fff', borderRadius: '50%',
      animation: 'spin 0.6s linear infinite',
    }} />
  )
}

const labelStyle = {
  display: 'block', fontSize: 11, fontWeight: 700,
  color: 'rgba(232,232,240,0.6)', letterSpacing: 1,
  textTransform: 'uppercase', marginBottom: 6,
}

const inputStyle = {
  width: '100%', background: '#0D0D12',
  border: '1px solid rgba(255,255,255,0.12)',
  borderRadius: 8, padding: '10px 14px',
  color: '#E8E8F0', fontSize: 13, outline: 'none',
  fontFamily: 'JetBrains Mono, monospace',
  transition: 'border-color 0.2s',
}
