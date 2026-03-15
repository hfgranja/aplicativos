/**
 * Técnica 13: Testes por Mutação (Mutation Testing)
 * Detecta pontos de mutação no código via AST e estima o mutation score.
 *
 * Operadores:
 *   AOR — Arithmetic Operator Replacement  (+, -, *, /, %)
 *   ROR — Relational Operator Replacement  (>, <, >=, <=, ===, !==)
 *   LCR — Logical Connector Replacement    (&& <-> ||)
 *   BCR — Boolean Condition Replacement    (if cond -> if !cond)
 *   SVR — Statement/Value Return           (return x -> null/0)
 *   UOI — Unary Operator Insertion         (! insertion)
 */
import { generateMutants, estimateMutationScore } from '../generators/mutationGenerator.js'

export default function mutationTestingAnalysis(code) {
  const issues = []
  const suggestions = []

  const mutants = generateMutants(code)
  const score = estimateMutationScore(mutants, code)

  // Count by operator
  const groups = mutants.reduce((acc, m) => {
    acc[m.operator] = (acc[m.operator] || 0) + 1
    return acc
  }, {})

  const total = mutants.length

  // Issues por operador com mais mutantes
  const sorted = Object.entries(groups).sort((a, b) => b[1] - a[1])

  sorted.forEach(([op, count]) => {
    const desc = {
      AOR: `operadores aritméticos (${count}) sem testes de valor correto`,
      ROR: `operadores relacionais (${count}) sem testes de boundary`,
      LCR: `conectores lógicos (${count}) sem testes de condição parcial`,
      BCR: `condicionais if/else (${count}) sem cobertura de ambos os branches`,
      SVR: `return statements (${count}) sem verificação de valor não-nulo`,
      UOI: `negações ! (${count}) sem testes de inversão booleana`,
    }
    if (desc[op]) {
      issues.push(`${count} mutante(s) ${desc[op]}`)
    }
  })

  // Detecta se o código já tem testes
  const hasTests = /\bdescribe\s*\(|\bit\s*\(|\btest\s*\(/.test(code)
  if (!hasTests && total > 0) {
    issues.push(`${total} mutantes detectados sem nenhuma suíte de testes existente`)
  }

  // Suggestions
  if ((groups.ROR || 0) > 0) {
    suggestions.push('ROR: adicione testes com valores exatamente no boundary (ex: se limite=18, teste com 17, 18 e 19)')
  }
  if ((groups.LCR || 0) > 0) {
    suggestions.push('LCR: teste cenários onde apenas uma das condições && ou || é verdadeira')
  }
  if ((groups.AOR || 0) > 0) {
    suggestions.push('AOR: verifique resultados aritméticos com valores conhecidos — não apenas "toBeDefined()"')
  }
  if ((groups.BCR || 0) > 0) {
    suggestions.push('BCR: cubra explicitamente o then-branch E o else-branch de cada if')
  }
  if (score < 50) {
    suggestions.push('Mutation score baixo — muitos mutantes sobreviveriam: adicione assertions específicas')
    suggestions.push('Use Stryker Mutator (npm i -D @stryker-mutator/core) para mutation testing real')
  } else {
    suggestions.push('Ferramenta recomendada: Stryker Mutator para execução real de mutation tests')
  }
  if (total === 0) {
    suggestions.push('Código sem pontos de mutação detectados — pode ser trivial ou só declarativo')
  }

  const detail = total > 0
    ? `${total} mutantes · ${Object.entries(groups).map(([k, v]) => `${k}:${v}`).join(' ')}`
    : 'Sem pontos de mutação detectados'

  return {
    id: 13,
    name: 'Testes por Mutação',
    icon: '🧬',
    color: '#E040FB',
    score,
    issues: issues.slice(0, 8),
    suggestions,
    detail,
  }
}
