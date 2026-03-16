/**
 * Técnica 6: Análise de Risco de Dependências
 * Verifica package.json: versões com wildcard, deps desatualizadas,
 * scripts perigosos, ausência de lockfile hints
 */

const KNOWN_RISKY = [
  'event-stream', 'flatmap-stream', 'colors', 'faker',
  'node-ipc', 'ua-parser-js', 'coa', 'rc',
]

const DEPRECATED_PACKAGES = [
  'request', 'node-uuid', 'jade', 'bower', 'grunt',
]

export default function dependencyAnalysis(code) {
  const issues = []
  const suggestions = []
  let score = 100

  // Try to parse as package.json
  let pkg = null
  try {
    pkg = JSON.parse(code)
  } catch {
    // not JSON, analyze import statements
  }

  if (pkg) {
    const allDeps = {
      ...pkg.dependencies,
      ...pkg.devDependencies,
      ...pkg.peerDependencies,
    }

    Object.entries(allDeps || {}).forEach(([name, version]) => {
      // Wildcard versions
      if (version === '*' || version === 'latest') {
        issues.push(`'${name}': versão '${version}' — use versão específica para reproducibilidade`)
        score -= 8
      }
      // Very loose ranges
      if (version.startsWith('>') && !version.startsWith('>=')) {
        issues.push(`'${name}': range aberto '${version}' — muito permissivo`)
        score -= 5
      }
      // Known risky packages
      if (KNOWN_RISKY.includes(name)) {
        issues.push(`'${name}': pacote com histórico de comprometimento de supply chain`)
        score -= 20
      }
      // Deprecated packages
      if (DEPRECATED_PACKAGES.includes(name)) {
        issues.push(`'${name}': pacote deprecado — use alternativa mantida`)
        score -= 10
      }
    })

    // Check scripts for dangerous patterns
    const scripts = pkg.scripts || {}
    Object.entries(scripts).forEach(([cmd, script]) => {
      if (/curl\s+.*\|\s*(bash|sh)/.test(script)) {
        issues.push(`Script '${cmd}': curl-pipe-bash detectado — vetor de ataque supply chain`)
        score -= 25
      }
      if (/rm\s+-rf/.test(script)) {
        issues.push(`Script '${cmd}': rm -rf detectado — risco de deleção acidental`)
        score -= 10
      }
    })

    // No engines field
    if (!pkg.engines) {
      issues.push('Campo "engines" ausente — especifique a versão Node.js mínima')
      score -= 5
    }

    const depCount = Object.keys(allDeps || {}).length
    suggestions.push(`${depCount} dependência(s) analisada(s)`)
  } else {
    // Analyze import statements in JS code
    const imports = [...code.matchAll(/(?:import|require)\s*[({]?\s*['"`]([^'"` ]+)['"`]/g)]
    const pkgNames = imports.map(m => m[1]).filter(n => !n.startsWith('.') && !n.startsWith('/'))

    pkgNames.forEach(name => {
      const baseName = name.split('/')[0].replace(/^@/, '')
      if (KNOWN_RISKY.includes(baseName)) {
        issues.push(`Import '${name}': pacote com histórico de comprometimento`)
        score -= 20
      }
      if (DEPRECATED_PACKAGES.includes(baseName)) {
        issues.push(`Import '${name}': pacote deprecado`)
        score -= 10
      }
    })

    if (pkgNames.length > 0) {
      suggestions.push(`${pkgNames.length} import(s) externos analisados`)
      suggestions.push('Cole o conteúdo do package.json para análise completa de dependências')
    } else {
      suggestions.push('Cole package.json para análise completa de dependências')
    }
  }

  if (issues.length === 0) {
    suggestions.push('Dependências sem riscos óbvios detectados')
  }
  suggestions.push('Execute npm audit regularmente para detectar CVEs conhecidas')
  suggestions.push('Use Dependabot ou Renovate para atualizações automáticas')

  return {
    id: 6,
    name: 'Risco de Dependências',
    icon: '📦',
    color: '#4ECDC4',
    score: Math.max(0, score),
    issues: issues.slice(0, 10),
    suggestions,
    detail: pkg ? `package.json analisado` : 'Análise por imports',
  }
}
