/**
 * Mutation Testing Generator
 * Detecta pontos de mutação via AST e gera testes mata-mutante
 *
 * Operadores de mutação implementados:
 * AOR - Arithmetic Operator Replacement  (+, -, *, /, %)
 * ROR - Relational Operator Replacement  (>, <, >=, <=, ===, !==)
 * LCR - Logical Connector Replacement    (&& <-> ||)
 * BCR - Boolean Condition Replacement    (if cond -> if !cond)
 * SVR - Statement/Value Return           (return x -> return null/0/'')
 * UOI - Unary Operator Insertion         (! insertion/removal)
 */
import { parseCode, traverse } from '../analyzers/astParser.js'

// Mutation operator mappings
const AOR_MAP = {
  '+': ['-', '*'],
  '-': ['+', '*'],
  '*': ['/', '+'],
  '/': ['*', '+'],
  '%': ['*', '+'],
}

const ROR_MAP = {
  '>':   ['>=', '<', '==='],
  '<':   ['<=', '>', '==='],
  '>=':  ['>', '<='],
  '<=':  ['<', '>='],
  '===': ['!==', '=='],
  '!==': ['===', '!='],
  '==':  ['!=', '==='],
  '!=':  ['==', '!=='],
}

const LCR_MAP = {
  '&&': ['||'],
  '||': ['&&'],
}

/**
 * Get source line from code by line number
 */
function getLine(code, lineNum) {
  if (!lineNum) return ''
  return (code.split('\n')[lineNum - 1] || '').trim().slice(0, 80)
}

/**
 * Detect all mutation points in the code
 * @param {string} code
 * @returns {Array<{operator, type, line, original, mutants, killHint}>}
 */
export function generateMutants(code) {
  const { ast } = parseCode(code)
  if (!ast) return []

  const mutants = []

  traverse(ast, {
    // AOR: Arithmetic Operator Replacement
    BinaryExpression(node) {
      const op = node.operator
      const line = node.loc?.start?.line || 0
      const srcLine = getLine(code, line)

      if (AOR_MAP[op]) {
        mutants.push({
          operator: 'AOR',
          type: 'Arithmetic',
          line,
          original: op,
          mutants: AOR_MAP[op],
          srcLine,
          killHint: `Teste que o resultado com ${op} difere de ${AOR_MAP[op][0]}`,
        })
      }

      if (ROR_MAP[op]) {
        mutants.push({
          operator: 'ROR',
          type: 'Relational',
          line,
          original: op,
          mutants: ROR_MAP[op],
          srcLine,
          killHint: `Teste com valor exatamente no boundary para diferenciar ${op} de ${ROR_MAP[op][0]}`,
        })
      }
    },

    // LCR: Logical Connector Replacement
    LogicalExpression(node) {
      const op = node.operator
      const line = node.loc?.start?.line || 0
      const srcLine = getLine(code, line)

      if (LCR_MAP[op]) {
        mutants.push({
          operator: 'LCR',
          type: 'Logical',
          line,
          original: op,
          mutants: LCR_MAP[op],
          srcLine,
          killHint: `Teste onde apenas uma condição é verdadeira (não ambas)`,
        })
      }
    },

    // BCR: Boolean Condition Replacement
    IfStatement(node) {
      const line = node.loc?.start?.line || 0
      const srcLine = getLine(code, line)
      mutants.push({
        operator: 'BCR',
        type: 'Condition',
        line,
        original: 'if (cond)',
        mutants: ['if (!cond)'],
        srcLine,
        killHint: `Teste o caso onde a condição é falsa (else branch)`,
      })
    },

    // SVR: Statement/Value Return
    ReturnStatement(node) {
      if (!node.argument) return
      const line = node.loc?.start?.line || 0
      const srcLine = getLine(code, line)
      const argType = node.argument.type

      const svMutants = ['return null', 'return undefined']
      if (argType === 'NumericLiteral' || argType === 'BinaryExpression') {
        svMutants.push('return 0', 'return -1')
      }
      if (argType === 'BooleanLiteral') {
        svMutants.push('return !value')
      }
      if (argType === 'StringLiteral') {
        svMutants.push("return ''")
      }

      mutants.push({
        operator: 'SVR',
        type: 'ReturnValue',
        line,
        original: 'return <expr>',
        mutants: svMutants,
        srcLine,
        killHint: `Verifique que o valor de retorno não é null/undefined/0`,
      })
    },

    // UOI: Unary Operator Insertion
    UnaryExpression(node) {
      if (node.operator !== '!') return
      const line = node.loc?.start?.line || 0
      const srcLine = getLine(code, line)
      mutants.push({
        operator: 'UOI',
        type: 'Unary',
        line,
        original: '!expr',
        mutants: ['expr (sem negação)'],
        srcLine,
        killHint: `Teste que a negação boolean está correta`,
      })
    },
  })

  return mutants
}

/**
 * Group mutants by operator type
 */
function groupByOperator(mutants) {
  return mutants.reduce((acc, m) => {
    acc[m.operator] = (acc[m.operator] || 0) + 1
    return acc
  }, {})
}

/**
 * Estimate mutation score (0-100) based on heuristics
 */
export function estimateMutationScore(mutants, code) {
  if (mutants.length === 0) return 85 // no mutation points = trivial code

  let score = 30 // conservative base

  // Has existing tests?
  if (/\bdescribe\s*\(|\bit\s*\(|\btest\s*\(/.test(code)) score += 20

  // Uses strict equality?
  const strictCount = (code.match(/===/g) || []).length
  const looseCount = (code.match(/==[^=]/g) || []).length
  if (strictCount > looseCount) score += 5

  // Has explicit return statements?
  const returnCount = (code.match(/\breturn\b/g) || []).length
  if (returnCount > 0) score += 8

  // Has boundary checks (typical in well-tested code)?
  if (/>=\s*0|<=\s*0|>\s*0|<\s*0/.test(code)) score += 5

  // Has error handling (suggests test awareness)?
  if (/try\s*\{/.test(code)) score += 5

  // Penalize based on mutation density
  const lines = code.split('\n').length
  const density = mutants.length / Math.max(1, lines)
  if (density > 1) score -= 10  // many mutations per line = harder to test
  if (density > 2) score -= 10

  // Penalize for many LCR (logical operator swaps are hard to catch)
  const groups = groupByOperator(mutants)
  if ((groups.LCR || 0) > 5) score -= 5

  return Math.max(0, Math.min(95, score))
}

/**
 * Generate a mutation test block for a single mutant
 */
function mutantToTest(m) {
  const label = `[kills ${m.operator} mutant L${m.line}]`

  switch (m.operator) {
    case 'AOR': {
      const [alt] = m.mutants
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Original : operador "${m.original}"
  // Mutante  : operador "${alt}" (resultado diferente!)
  it('deve usar "${m.original}" corretamente, não "${alt}" ${label}', () => {
    // Arrange — escolha inputs que produzam resultados distintos entre ${m.original} e ${alt}
    // const a = 10, b = 3
    // Act
    // const result = funcionQueUsa_${m.original}(a, b)
    // Assert
    // expect(result).toBe(13)   // 10${m.original}3 = 13 (NOT 10${alt}3 = 30)
    expect(true).toBe(true) // TODO: substitua pelo assert real
  })`
    }

    case 'ROR': {
      const [alt] = m.mutants
      const isBoundary = ['>=', '<=', '>', '<'].includes(m.original)
      const boundaryNote = isBoundary
        ? `// Boundary: teste com valor exatamente no limite para diferenciar "${m.original}" de "${alt}"`
        : `// Diferença semântica: "${m.original}" vs "${alt}"`
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Original : "${m.original}"   Mutante: "${alt}"
  ${boundaryNote}
  it('deve usar "${m.original}", não "${alt}" ${label}', () => {
    // Arrange — use valor no exato boundary
    // Act + Assert
    // Se original é "${m.original}", teste o caso onde "${m.original}" é true mas "${alt}" seria diferente
    expect(true).toBe(true) // TODO: substitua pelo assert real
  })`
    }

    case 'LCR': {
      const [alt] = m.mutants
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Original : "${m.original}"   Mutante: "${alt}"
  // Para matar: crie caso onde apenas UMA condição é verdadeira
  it('deve ser falso quando apenas uma condição satisfaz (não ambas) ${label}', () => {
    // Com "${m.original}": ambas devem ser true para o resultado ser true
    // Com "${alt}": basta uma ser true
    // Arrange: condicaoA = true, condicaoB = false
    // Assert: resultado com "${m.original}" = false, mas com "${alt}" = true
    expect(true).toBe(true) // TODO: substitua pelo assert real
  })`
    }

    case 'BCR':
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Mutante  : condição negada — if (!cond) em vez de if (cond)
  it('deve executar o bloco CORRETO quando condição é true ${label}', () => {
    // Teste explícito do then-branch
    expect(true).toBe(true) // TODO: chame a função com input que torna a condição true
  })
  it('deve executar o else-branch quando condição é false ${label}', () => {
    // Teste explícito do else-branch
    expect(true).toBe(true) // TODO: chame a função com input que torna a condição false
  })`

    case 'SVR':
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Mutante  : return null / return 0 / return undefined
  it('deve retornar valor definido e não-nulo ${label}', () => {
    // const result = funcaoQueRetorna(/* args válidos */)
    // expect(result).not.toBeNull()
    // expect(result).not.toBeUndefined()
    // expect(result).toBeDefined()
    expect(true).toBe(true) // TODO: substitua pelo assert real
  })`

    case 'UOI':
      return `
  // ── ${m.operator} · Linha ${m.line} ─────────────────────────────
  // Código   : ${m.srcLine}
  // Mutante  : remoção do operador "!" (negação)
  it('deve aplicar negação corretamente ${label}', () => {
    // Garanta que a lógica booleana está invertida quando esperado
    expect(true).toBe(true) // TODO: substitua pelo assert real
  })`

    default:
      return ''
  }
}

/**
 * Generate full mutation testing section for the test file
 * @param {string} code
 * @returns {string} — formatted test section
 */
export function generateMutationTests(code) {
  const mutants = generateMutants(code)
  if (mutants.length === 0) {
    return `
// ==========================================
// Testes por Mutação (Mutation Testing)
// Nenhum ponto de mutação detectado no código
// ==========================================`
  }

  const groups = groupByOperator(mutants)
  const score = estimateMutationScore(mutants, code)
  const total = mutants.length

  const summaryLines = Object.entries(groups)
    .map(([op, count]) => `// · ${op}: ${count} mutante(s)`)
    .join('\n')

  // Limit to 20 most impactful mutants to avoid bloat
  // Priority: AOR > ROR > LCR > BCR > SVR > UOI
  const PRIORITY = ['AOR', 'ROR', 'LCR', 'BCR', 'SVR', 'UOI']
  const selected = [...mutants]
    .sort((a, b) => PRIORITY.indexOf(a.operator) - PRIORITY.indexOf(b.operator))
    .slice(0, 20)

  const testBlocks = selected.map(m => mutantToTest(m)).filter(Boolean).join('\n')

  return `
// ==========================================
// Testes por Mutação (Mutation Testing)
// ==========================================
// Mutation Score estimado: ~${score}%
// Total de mutantes detectados: ${total}
${summaryLines}
//
// Como usar:
// 1. Substitua os "TODO" com chamadas reais às suas funções
// 2. Execute com Stryker: npx stryker run
// 3. Mutantes "mortos" = testes eficazes | "sobreviventes" = lacunas
// ==========================================

describe('Mutation Testing — Testes Mata-Mutante', () => {
${testBlocks}
})`
}
