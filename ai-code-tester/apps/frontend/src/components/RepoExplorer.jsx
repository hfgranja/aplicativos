import { useState, useMemo } from 'react'
import { CODE_EXTENSIONS } from '../services/gitService.js'

const PROVIDER_COLORS = {
  github: '#6C63FF',
  gitlab: '#FF6B6B',
  bitbucket: '#45B7D1',
  azure: '#FFB020',
}

const PROVIDER_ICONS = {
  github: '🐙',
  gitlab: '🦊',
  bitbucket: '🪣',
  azure: '☁️',
}

const EXT_GROUPS = [
  { label: 'JS/TS', exts: ['.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'] },
  { label: 'Python', exts: ['.py'] },
  { label: 'Java', exts: ['.java', '.kt'] },
  { label: 'Go', exts: ['.go'] },
  { label: 'Outros', exts: ['.rb', '.php', '.cs', '.cpp', '.c', '.swift', '.rs'] },
]

function buildTree(files) {
  const tree = {}
  files.forEach(file => {
    const parts = file.path.split('/')
    let node = tree
    parts.forEach((part, i) => {
      if (!node[part]) {
        node[part] = i === parts.length - 1
          ? { __file: file }
          : {}
      }
      if (i < parts.length - 1) node = node[part]
    })
  })
  return tree
}

function FileTreeNode({ name, node, selectedFiles, onToggle, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2)

  if (node.__file) {
    const file = node.__file
    const checked = selectedFiles.includes(file.path)
    const ext = '.' + file.path.split('.').pop().toLowerCase()
    const isCode = CODE_EXTENSIONS.includes(ext)

    return (
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 6,
          padding: '3px 6px 3px ' + (depth * 16 + 6) + 'px',
          borderRadius: 4, cursor: 'pointer',
          background: checked ? 'rgba(108,99,255,0.08)' : 'transparent',
          opacity: isCode ? 1 : 0.4,
        }}
        onClick={() => isCode && onToggle(file.path)}
      >
        <span style={{
          width: 14, height: 14, border: `1.5px solid ${checked ? '#6C63FF' : 'rgba(255,255,255,0.2)'}`,
          borderRadius: 3, background: checked ? '#6C63FF' : 'transparent',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0, fontSize: 9, color: '#fff',
        }}>
          {checked ? '✓' : ''}
        </span>
        <span style={{ fontSize: 12, color: 'rgba(232,232,240,0.7)' }}>
          {getFileIcon(ext)} {name}
        </span>
        {file.size > 0 && (
          <span style={{ fontSize: 10, color: 'rgba(232,232,240,0.25)', marginLeft: 'auto' }}>
            {formatSize(file.size)}
          </span>
        )}
      </div>
    )
  }

  const children = Object.entries(node).sort(([_a, av], [_b, bv]) => {
    // Folders first
    const aIsFile = av.__file ? 1 : 0
    const bIsFile = bv.__file ? 1 : 0
    return aIsFile - bIsFile
  })

  return (
    <div>
      <div
        style={{
          display: 'flex', alignItems: 'center', gap: 5,
          padding: '3px 6px 3px ' + (depth * 16 + 6) + 'px',
          cursor: 'pointer', borderRadius: 4,
        }}
        onClick={() => setOpen(o => !o)}
      >
        <span style={{ fontSize: 10, color: 'rgba(232,232,240,0.3)', width: 10 }}>
          {open ? '▼' : '▶'}
        </span>
        <span style={{ fontSize: 12, color: 'rgba(232,232,240,0.6)', fontWeight: 600 }}>
          📁 {name}
        </span>
      </div>
      {open && (
        <div>
          {children.map(([childName, childNode]) => (
            <FileTreeNode
              key={childName}
              name={childName}
              node={childNode}
              selectedFiles={selectedFiles}
              onToggle={onToggle}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function RepoExplorer({
  git, files, selectedFiles, onSelectFiles,
  onAnalyze, onDisconnect, loadingFiles, loadProgress,
}) {
  const [extFilter, setExtFilter] = useState(new Set(['.js', '.jsx', '.ts', '.tsx']))
  const [search, setSearch] = useState('')

  const provider = git.provider || 'github'
  const pColor = PROVIDER_COLORS[provider] || '#6C63FF'

  const filteredFiles = useMemo(() => {
    return files.filter(f => {
      const ext = '.' + f.path.split('.').pop().toLowerCase()
      if (!extFilter.has(ext) && extFilter.size > 0) return false
      if (search && !f.path.toLowerCase().includes(search.toLowerCase())) return false
      return CODE_EXTENSIONS.includes(ext)
    })
  }, [files, extFilter, search])

  const tree = useMemo(() => buildTree(filteredFiles), [filteredFiles])

  function toggleFile(path) {
    if (selectedFiles.includes(path)) {
      onSelectFiles(selectedFiles.filter(p => p !== path))
    } else {
      onSelectFiles([...selectedFiles, path])
    }
  }

  function toggleExt(ext) {
    setExtFilter(prev => {
      const next = new Set(prev)
      if (next.has(ext)) next.delete(ext)
      else next.add(ext)
      return next
    })
  }

  function selectAll() {
    onSelectFiles(filteredFiles.map(f => f.path))
  }

  function clearAll() {
    onSelectFiles([])
  }

  const estimatedLines = Math.round(selectedFiles.length * 80)

  if (loadingFiles) {
    return (
      <div style={{ textAlign: 'center', padding: '32px 0' }}>
        <div style={{ fontSize: 28, marginBottom: 12 }}>📥</div>
        <div style={{ fontSize: 14, color: 'rgba(232,232,240,0.6)', marginBottom: 12 }}>
          Carregando arquivos selecionados...
        </div>
        <div style={{ height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${loadProgress}%`,
            background: `linear-gradient(90deg, ${pColor}, #00D4AA)`,
            transition: 'width 0.3s ease',
          }} />
        </div>
        <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.3)', marginTop: 6 }}>
          {loadProgress}%
        </div>
      </div>
    )
  }

  return (
    <div>
      {/* Connected header */}
      <div style={{
        background: `${pColor}12`, border: `1px solid ${pColor}30`,
        borderRadius: 10, padding: '12px 16px', marginBottom: 16,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: 20 }}>{PROVIDER_ICONS[provider]}</span>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: pColor }}>
              {git.owner}/{git.repo}
            </div>
            <div style={{ fontSize: 11, color: 'rgba(232,232,240,0.4)' }}>
              branch: {git.branch || 'main'} · {files.length} arquivos de código
            </div>
          </div>
        </div>
        <button
          onClick={onDisconnect}
          style={{
            background: 'rgba(255,77,109,0.1)', border: '1px solid rgba(255,77,109,0.3)',
            color: '#FF4D6D', padding: '5px 12px', borderRadius: 6,
            cursor: 'pointer', fontSize: 12, fontWeight: 600,
          }}
        >
          🔌 Desconectar
        </button>
      </div>

      {/* Extension filter */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
        {EXT_GROUPS.map(group => {
          const active = group.exts.some(e => extFilter.has(e))
          return (
            <button
              key={group.label}
              type="button"
              onClick={() => group.exts.forEach(e => toggleExt(e))}
              style={{
                fontSize: 11, padding: '3px 10px', borderRadius: 20,
                cursor: 'pointer',
                background: active ? `${pColor}20` : 'rgba(255,255,255,0.04)',
                border: `1px solid ${active ? pColor + '50' : 'rgba(255,255,255,0.1)'}`,
                color: active ? pColor : 'rgba(232,232,240,0.4)',
                fontWeight: active ? 600 : 400,
              }}
            >
              {group.label}
            </button>
          )
        })}
      </div>

      {/* Search + select controls */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, alignItems: 'center' }}>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Filtrar arquivos..."
          style={{
            flex: 1, background: '#0D0D12', border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 6, padding: '6px 12px', color: '#E8E8F0', fontSize: 12,
            outline: 'none', fontFamily: 'JetBrains Mono, monospace',
          }}
        />
        <button type="button" onClick={selectAll}
          style={{ fontSize: 11, padding: '5px 10px', borderRadius: 6, cursor: 'pointer',
            background: 'rgba(108,99,255,0.1)', border: '1px solid rgba(108,99,255,0.3)',
            color: '#6C63FF', fontWeight: 600 }}>
          ✓ Todos
        </button>
        <button type="button" onClick={clearAll}
          style={{ fontSize: 11, padding: '5px 10px', borderRadius: 6, cursor: 'pointer',
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)',
            color: 'rgba(232,232,240,0.4)' }}>
          ✕ Limpar
        </button>
      </div>

      {/* File tree */}
      <div style={{
        background: '#0A0A10', border: '1px solid rgba(255,255,255,0.07)',
        borderRadius: 10, padding: '8px 0', maxHeight: 280, overflowY: 'auto',
        marginBottom: 12,
      }}>
        {filteredFiles.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '20px', fontSize: 13, color: 'rgba(232,232,240,0.3)' }}>
            Nenhum arquivo de código encontrado com os filtros selecionados
          </div>
        ) : (
          Object.entries(tree).sort(([_a, av], [_b, bv]) => {
            return av.__file ? 1 : bv.__file ? -1 : 0
          }).map(([name, node]) => (
            <FileTreeNode
              key={name} name={name} node={node}
              selectedFiles={selectedFiles} onToggle={toggleFile}
            />
          ))
        )}
      </div>

      {/* Selection summary */}
      <div style={{
        fontSize: 12, color: 'rgba(232,232,240,0.5)', marginBottom: 14,
        display: 'flex', justifyContent: 'space-between',
      }}>
        <span>
          <strong style={{ color: pColor }}>{selectedFiles.length}</strong> arquivo(s) selecionado(s)
          {' · '}~<strong style={{ color: 'rgba(232,232,240,0.6)' }}>{estimatedLines.toLocaleString()}</strong> linhas estimadas
        </span>
        <span style={{ color: 'rgba(232,232,240,0.3)' }}>
          {filteredFiles.length} visíveis
        </span>
      </div>

      {/* Analyze button */}
      <button
        type="button"
        onClick={onAnalyze}
        disabled={selectedFiles.length === 0}
        style={{
          width: '100%',
          background: selectedFiles.length > 0
            ? `linear-gradient(135deg, ${pColor}, #00D4AA)`
            : 'rgba(255,255,255,0.05)',
          border: 'none',
          color: selectedFiles.length > 0 ? '#fff' : 'rgba(255,255,255,0.2)',
          padding: '14px', borderRadius: 10,
          cursor: selectedFiles.length > 0 ? 'pointer' : 'not-allowed',
          fontSize: 14, fontWeight: 700, letterSpacing: 0.5,
          transition: 'all 0.2s',
          boxShadow: selectedFiles.length > 0 ? `0 6px 20px ${pColor}35` : 'none',
        }}
        onMouseEnter={e => { if (selectedFiles.length > 0) e.target.style.transform = 'translateY(-1px)' }}
        onMouseLeave={e => { e.target.style.transform = 'none' }}
      >
        🔬 Analisar {selectedFiles.length > 0 ? `${selectedFiles.length} Arquivo(s)` : 'Repositório'} · 13 Técnicas
      </button>
    </div>
  )
}

function getFileIcon(ext) {
  if (['.js', '.mjs', '.cjs'].includes(ext)) return '🟨'
  if (['.jsx'].includes(ext)) return '⚛️'
  if (['.ts'].includes(ext)) return '🔷'
  if (['.tsx'].includes(ext)) return '⚛️'
  if (['.py'].includes(ext)) return '🐍'
  if (['.java', '.kt'].includes(ext)) return '☕'
  if (['.go'].includes(ext)) return '🔵'
  if (['.rb'].includes(ext)) return '💎'
  if (['.php'].includes(ext)) return '🐘'
  if (['.cs'].includes(ext)) return '🎯'
  if (['.cpp', '.c', '.h'].includes(ext)) return '⚙️'
  return '📄'
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / 1024 / 1024).toFixed(1)}MB`
}
