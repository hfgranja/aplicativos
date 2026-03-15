/**
 * Técnica 2: Complexidade Ciclomática
 * Conta caminhos de decisão por função: if, for, while, case, &&, ||, ?, catch
 * CC > 10 = alto risco; CC > 20 = muito alto
 */
import { parseCode, traverse, getFunctions, lineCount } from './astParser.js'

function calcCC(funcNode) {
  let cc = 1 // base
  const decision = new Set([
    'IfStatement', 'ForStatement', 'ForInStatement', 'ForOfStatement',
    'WhileStatement', 'DoWhileStatement', 'SwitchCase',
    'CatchClause', 'ConditionalExpression',
    'LogicalExpression',
  ])
  traverse(funcNode, {
    ...Object.fromEntries([...decision].map(type => [type, () => { cc++ }])),
  })
  return cc
}

export default function complexityAnalysis(code) {
  const issues = []
  const suggestions = []
  let totalCC = 0
  let funcCount = 0
  let highCCCount = 0

  const { ast } = parseCode(code)
  if (!ast) {
    return {
      id: 2, name: 'Complexidade Ciclomática', icon: '🔄', color: '#00D4AA',
      score: 50, issues: ['Não foi possível parsear o código'], suggestions: [], detail: '—',
    }
  }

  const fns = getFunctions(ast)
  fns.forEach(fn => {
    const cc = calcCC(fn)
    const name = fn.id?.name || (fn.parent?.key?.name) || 'anônima'
    const lines = lineCount(fn)
    funcCount++
    totalCC += cc

    if (cc > 20) {
      issues.push(`Função '${name}' (${lines} linhas): CC=${cc} — MUITO ALTO (refatorar urgente)`)
      highCCCount++
    } else if (cc > 10) {
      issues.push(`Função '${name}' (${lines} linhas): CC=${cc} — ALTO (considere dividir)`)
      highCCCount++
    }
  })

  const avgCC = funcCount > 0 ? (totalCC / funcCount).toFixed(1) : 0
  const score = funcCount === 0 ? 70 :
    Math.max(0, 100 - (highCCCount * 15) - Math.max(0, avgCC - 5) * 3)

  if (highCCCount === 0) {
    suggestions.push(`Complexidade média ${avgCC} — dentro do limite recomendado (≤10)`)
  } else {
    suggestions.push('Aplique o princípio de responsabilidade única (SRP)')
    suggestions.push('Extraia condicionais complexas para funções com nomes descritivos')
    suggestions.push('Use early return pattern para reduzir aninhamento')
  }

  return {
    id: 2,
    name: 'Complexidade Ciclomática',
    icon: '🔄',
    color: '#00D4AA',
    score: Math.round(score),
    issues: issues.slice(0, 8),
    suggestions,
    detail: `${funcCount} função(ões) · CC médio: ${avgCC}`,
  }
}
