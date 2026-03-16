/**
 * Técnica 11: Qualidade do Tratamento de Erros
 * Verifica: try/catch coverage, .catch() em Promises,
 * erros silenciados, Error boundaries em React
 */
import { parseCode, traverse } from './astParser.js'

export default function errorHandlingAnalysis(code) {
  const issues = []
  const suggestions = []
  let score = 60 // base score

  const { ast } = parseCode(code)

  if (!ast) {
    return {
      id: 11, name: 'Tratamento de Erros', icon: '🔧', color: '#98D8C8',
      score: 50, issues: ['Não foi possível parsear o código'], suggestions: [], detail: '—',
    }
  }

  let tryCatchCount = 0
  let emptyCatchCount = 0
  let asyncFnCount = 0
  let _awaitWithoutTryCatch = 0
  let _promiseCount = 0
  let _promiseWithCatch = 0

  // Count async functions and their try/catch usage
  traverse(ast, {
    TryStatement(n) {
      tryCatchCount++
      // Empty catch block
      const catchBody = n.handler?.body?.body || []
      if (catchBody.length === 0) {
        emptyCatchCount++
        issues.push('Bloco catch vazio detectado — erro sendo silenciado')
        score -= 10
      }
      // catch that only does console.log (not re-throwing)
      if (catchBody.length === 1 && catchBody[0].expression?.callee?.object?.name === 'console') {
        issues.push('catch apenas com console.log — considere re-throw ou notificação do usuário')
        score -= 5
      }
    },
    AwaitExpression() {
      _awaitWithoutTryCatch++
    },
    CallExpression(n) {
      const callee = n.callee
      if (callee.property?.name === 'then') {
        _promiseCount++
      }
      if (callee.property?.name === 'catch') {
        _promiseWithCatch++
        score += 2
      }
    },
  })

  // Async functions without try/catch (regex-based heuristic)
  const asyncFns = [...code.matchAll(/async\s+(?:function|\w+\s*=>|\([^)]*\)\s*=>)/g)]
  asyncFnCount = asyncFns.length

  const awaitLines = (code.match(/\bawait\b/g) || []).length
  if (asyncFnCount > 0 && tryCatchCount === 0 && awaitLines > 0) {
    issues.push(`${asyncFnCount} função(ões) async sem try/catch — erros de Promise não tratados`)
    score -= 15
  }

  // Unhandled promise rejections pattern
  const thenWithoutCatch = (code.match(/\.then\s*\(/g) || []).length - (code.match(/\.catch\s*\(/g) || []).length
  if (thenWithoutCatch > 2) {
    issues.push(`${thenWithoutCatch} .then() sem .catch() correspondente — Promise rejections não tratadas`)
    score -= thenWithoutCatch * 5
  }

  // React Error Boundary
  const hasErrorBoundary = /componentDidCatch|getDerivedStateFromError|ErrorBoundary/.test(code)
  const hasReactComponents = /React\.createElement|jsx|<[A-Z]/.test(code)
  if (hasReactComponents && !hasErrorBoundary && code.length > 500) {
    issues.push('Aplicação React sem Error Boundary — erros de render causam tela branca')
    score -= 8
    suggestions.push('Implemente Error Boundaries para React (componentDidCatch)')
  }

  // window.onerror or global error handling
  const hasGlobalHandler = /window\.onerror|process\.on.*uncaughtException|addEventListener.*error/.test(code)
  if (!hasGlobalHandler && code.length > 200) {
    suggestions.push('Considere adicionar handler global de erros (window.onerror / process.on)')
  }

  if (tryCatchCount > 0) {
    score += Math.min(20, tryCatchCount * 5)
    suggestions.push(`${tryCatchCount} bloco(s) try/catch detectado(s)`)
  } else {
    issues.push('Nenhum try/catch detectado — código sem tratamento de erros explícito')
    score -= 20
  }

  if (issues.length <= 1) {
    suggestions.push('Tratamento de erros adequado para o tamanho do código')
  }
  suggestions.push('Use Error customizados (extends Error) para identificar tipos de falha')
  suggestions.push('Implemente logging centralizado de erros (Sentry, Datadog)')

  return {
    id: 11,
    name: 'Tratamento de Erros',
    icon: '🔧',
    color: '#98D8C8',
    score: Math.max(0, Math.min(100, score)),
    issues: issues.slice(0, 8),
    suggestions,
    detail: `${tryCatchCount} try/catch · ${emptyCatchCount} vazio(s) · ${asyncFnCount} async`,
  }
}
