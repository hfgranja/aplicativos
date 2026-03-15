/**
 * Técnica 7: Estimativa de Cobertura de Código
 * Identifica funções, branches e statements testáveis via AST
 * Estima % de código que pode ser coberto por testes
 */
import { parseCode, traverse, getFunctions } from './astParser.js'

export default function coverageEstimation(code) {
  const issues = []
  const suggestions = []

  const { ast } = parseCode(code)
  if (!ast) {
    return {
      id: 7, name: 'Estimativa de Cobertura', icon: '📊', color: '#45B7D1',
      score: 50, issues: ['Não foi possível parsear o código'], suggestions: [], detail: '—',
    }
  }

  const fns = getFunctions(ast)
  let branches = 0
  let testableUnits = 0
  let pureUnits = 0
  const functionsDetected = []

  traverse(ast, {
    IfStatement: () => { branches++ },
    SwitchStatement: () => { branches++ },
    ConditionalExpression: () => { branches++ },
    LogicalExpression: () => { branches++ },
  })

  fns.forEach(fn => {
    const name = fn.id?.name || 'anônima'
    testableUnits++

    // Heuristic: pure function (no side effects) is easier to test
    let sideEffects = 0
    traverse(fn, {
      CallExpression(n) {
        const callee = n.callee
        if (callee.object?.name === 'console') return
        if (callee.object?.name === 'document') sideEffects++
        if (callee.object?.name === 'window') sideEffects++
        if (callee.name === 'fetch' || callee.name === 'axios') sideEffects++
        if (callee.object?.type === 'MemberExpression' &&
            callee.object.object?.name === 'localStorage') sideEffects++
      },
      AssignmentExpression(n) {
        if (n.left?.object?.name === 'window' ||
            n.left?.object?.name === 'document') sideEffects++
      },
    })

    if (sideEffects === 0) pureUnits++
    functionsDetected.push({ name, sideEffects })
  })

  const totalUnits = testableUnits + branches
  const estimatedCoverable = pureUnits + Math.floor(branches * 0.7)
  const coverageEst = totalUnits === 0 ? 0 : Math.round((estimatedCoverable / totalUnits) * 100)

  // Score based on testability
  const pureRatio = testableUnits === 0 ? 0 : pureUnits / testableUnits
  const score = Math.round(30 + pureRatio * 50 + Math.min(20, coverageEst / 5))

  if (testableUnits === 0) {
    issues.push('Nenhuma função detectada para testar')
  }
  if (pureRatio < 0.5 && testableUnits > 0) {
    issues.push(`${testableUnits - pureUnits} função(ões) com side-effects difíceis de testar`)
  }
  if (branches === 0 && testableUnits > 0) {
    issues.push('Sem branches detectados — valide se há lógica condicional não coberta')
  }

  if (testableUnits > 0) {
    suggestions.push(`${testableUnits} função(ões) identificada(s) · ${branches} branch(es) · ${pureUnits} puras`)
  }
  suggestions.push('Escreva testes unitários para todas as funções puras primeiro')
  suggestions.push('Use mocks/stubs para isolar side-effects em testes')
  if (coverageEst < 80) {
    suggestions.push('Meta: ≥80% de cobertura de linhas e branches')
  }

  return {
    id: 7,
    name: 'Estimativa de Cobertura',
    icon: '📊',
    color: '#45B7D1',
    score,
    issues: issues.slice(0, 6),
    suggestions,
    detail: `~${coverageEst}% testável · ${testableUnits} funções · ${branches} branches`,
  }
}
