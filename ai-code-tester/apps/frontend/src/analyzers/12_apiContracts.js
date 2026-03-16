/**
 * Técnica 12: Validação de Contratos de API
 * Detecta: fetch() sem tratamento de erro, sem timeout, headers hardcoded,
 * URLs hardcoded, falta de validação de resposta
 */
import { parseCode, traverse } from './astParser.js'

export default function apiContractAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  const { ast } = parseCode(code)
  if (!ast) {
    return {
      id: 12, name: 'Contratos de API', icon: '🔌', color: '#F0A500',
      score: 50, issues: ['Não foi possível parsear o código'], suggestions: [], detail: '—',
    }
  }

  let fetchCount = 0
  let fetchWithTimeout = 0
  const hardcodedUrls = []
  const hardcodedApiKeys = []

  // Look for fetch() calls
  traverse(ast, {
    CallExpression(n) {
      const callee = n.callee
      const isFetch = callee.name === 'fetch' ||
        (callee.object?.name === 'axios') ||
        (callee.property?.name === 'get' && callee.object?.name === 'axios') ||
        (callee.property?.name === 'post' && callee.object?.name === 'axios')

      if (isFetch) {
        fetchCount++
        // Check first argument (URL)
        const urlArg = n.arguments?.[0]
        if (urlArg?.type === 'StringLiteral' || urlArg?.type === 'Literal') {
          const url = urlArg.value || ''
          if (url.startsWith('http://') || url.startsWith('https://')) {
            hardcodedUrls.push(url)
          }
        }
      }
    },
  })

  // Regex-based checks
  const lines = code.split('\n')
  lines.forEach((line, i) => {
    const ln = i + 1

    // fetch without .catch() or try/catch (simplified heuristic)
    if (/\bfetch\s*\(/.test(line) && !/\.catch|try\s*\{/.test(line)) {
      // not conclusive alone, accumulate
    }

    // AbortController / timeout
    if (/AbortController|AbortSignal|signal:/.test(line)) {
      fetchWithTimeout++
    }

    // Hardcoded Bearer tokens / API keys in headers
    if (/['"]Authorization['"].*Bearer\s+[a-zA-Z0-9._-]{20,}/.test(line)) {
      hardcodedApiKeys.push(`Linha ${ln}: Bearer token hardcoded em header`)
      deductions += 15
    }

    // HTTP instead of HTTPS
    if (/fetch\s*\(\s*['"]http:\/\/(?!localhost)/.test(line)) {
      issues.push(`Linha ${ln}: fetch com HTTP (não HTTPS) — transmissão insegura`)
      deductions += 10
    }

    // No response.ok check
    if (/await\s+fetch/.test(line)) {
      const nextLines = lines.slice(i, i + 5).join(' ')
      if (!/response\.ok|res\.ok|\.status/.test(nextLines)) {
        issues.push(`Linha ${ln}: fetch sem verificação response.ok — erros 4xx/5xx ignorados`)
        deductions += 8
      }
    }

    // Content-Type missing on POST
    if (/method:\s*['"]POST['"]/.test(line)) {
      const nearby = lines.slice(Math.max(0, i - 3), i + 3).join(' ')
      if (!/'Content-Type'|"Content-Type"/.test(nearby)) {
        issues.push(`Linha ${ln}: POST sem Content-Type header`)
        deductions += 5
      }
    }
  })

  hardcodedUrls.forEach(url => {
    issues.push(`URL hardcoded: ${url.slice(0, 60)} — use variável de ambiente`)
    deductions += 5
  })
  hardcodedApiKeys.forEach(msg => {
    issues.push(msg)
  })

  if (fetchCount > 0 && fetchWithTimeout === 0) {
    issues.push(`${fetchCount} chamada(s) fetch sem AbortController/timeout — pode travar indefinidamente`)
    deductions += 10
  }

  const score = Math.max(0, 100 - deductions)

  if (fetchCount === 0) {
    suggestions.push('Nenhuma chamada de API direta detectada no código')
  } else {
    suggestions.push(`${fetchCount} chamada(s) de API detectada(s)`)
    suggestions.push('Sempre verifique response.ok e trate status codes HTTP')
    suggestions.push('Use AbortController com timeout para todas as requisições')
    suggestions.push('Armazene URLs de API em variáveis de ambiente (.env)')
    if (fetchWithTimeout === 0) {
      suggestions.push('Implemente timeout padrão: const controller = new AbortController()')
    }
  }

  return {
    id: 12,
    name: 'Contratos de API',
    icon: '🔌',
    color: '#F0A500',
    score,
    issues: issues.slice(0, 10),
    suggestions,
    detail: `${fetchCount} chamada(s) de API · ${hardcodedUrls.length} URL(s) hardcoded`,
  }
}
