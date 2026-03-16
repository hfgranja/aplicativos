import { parseCode, getFunctions } from './astParser.js'

export default function propertyBasedAnalysis(code) {
  const issues = []
  const suggestions = []
  let score = 100
  let deductions = 0

  try {
    const ast = parseCode(code)
    const functions = getFunctions(ast)

    // Check for property-based testing libraries
    const hasFastCheck = /fast-check|fc\.anything|fc\.integer|fc\.string|fc\.array/.test(code)
    const hasHypothesis = /hypothesis|@given|@settings/.test(code)
    const hasJsverify = /jsverify|jsc\./.test(code)
    const hasPBT = hasFastCheck || hasHypothesis || hasJsverify

    if (hasPBT) {
      score += 10  // bonus
      suggestions.push('✅ Property-based testing detectado — continue expandindo a cobertura')
    }

    // Count arithmetic operations that suggest numeric logic
    const mathOps = (code.match(/[\+\-\*\/\%]=?\s*\w/g) || []).length
    const mathFunctions = (code.match(/Math\.\w+\(/g) || []).length
    const hasNumericLogic = mathOps > 3 || mathFunctions > 0

    if (hasNumericLogic && !hasPBT) {
      deductions += 20
      issues.push(`${mathOps + mathFunctions} operação(ões) matemática(s) sem cobertura de edge cases (0, -1, NaN, Infinity)`)
      suggestions.push('Use fast-check: fc.assert(fc.property(fc.integer(), n => fn(n) >= 0))')
    }

    // Check if pure functions exist without property tests
    const pureFunctions = functions.filter(f => {
      const body = f.name ? code.slice(code.indexOf(`function ${f.name}`)) : ''
      return !body.includes('fetch(') &&
             !body.includes('setState') &&
             !body.includes('localStorage') &&
             !body.includes('console.')
    })

    if (pureFunctions.length >= 2 && !hasPBT) {
      deductions += 15
      issues.push(`${pureFunctions.length} função(ões) pura(s) detectada(s) — ideais para property testing mas sem cobertura`)
      suggestions.push('Funções puras são perfeitas para property-based tests: entradas aleatórias, propriedades invariantes')
    }

    // Check for boundary test patterns (even without PBT lib)
    const boundaryPatterns = [
      /expect.*\(-?0\)/.test(code),
      /expect.*\(-1\)/.test(code),
      /expect.*Infinity/.test(code),
      /expect.*NaN/.test(code),
      /expect.*null.*\)/.test(code),
      /expect.*\[\]/.test(code),
    ].filter(Boolean).length

    if (boundaryPatterns < 2 && functions.length > 0) {
      deductions += 10
      issues.push('Poucos testes de boundary detectados (0, -1, NaN, arrays vazios, null)')
      suggestions.push('Adicione testes com: 0, -1, 1, valores negativos, strings vazias, arrays vazios')
    }

    // Arrays operations without empty array test
    const arrayOps = (code.match(/\.map\(|\.filter\(|\.reduce\(|\.forEach\(|\.find\(/g) || []).length
    if (arrayOps >= 2 && !code.includes('[].') && !code.includes('[])')){
      deductions += 10
      issues.push(`${arrayOps} operação(ões) em arrays sem teste com array vazio []`)
      suggestions.push('Sempre teste funções de array com: [], [unico_item], [item_invalido]')
    }

    // If code only has happy-path tests
    const hasTests = /describe\(|it\(|test\(|expect\(/.test(code)
    const testCount = (code.match(/it\(|test\(/g) || []).length
    if (hasTests && testCount > 0 && !hasPBT && mathOps > 0) {
      const happyPathOnly = !/(0|NaN|null|undefined|-1|Infinity|empty|edge|boundary)/i.test(code)
      if (happyPathOnly) {
        deductions += 15
        issues.push('Testes presentes mas aparentemente apenas happy-path — sem edge cases visíveis')
        suggestions.push('Complemente testes existentes com: casos negativos, zero, null, valores extremos')
      }
    }

    const finalScore = Math.max(0, Math.min(100, score - deductions))
    const detail = hasPBT
      ? 'Property-based testing ativo'
      : `${pureFunctions.length} função(ões) pura(s) · ${mathOps + mathFunctions} op. matemáticas`

    return {
      id: 14,
      name: 'Property-Based Testing',
      icon: '🎲',
      color: '#FF9F43',
      score: finalScore,
      issues: issues.slice(0, 6),
      suggestions: suggestions.slice(0, 4),
      detail,
    }
  } catch {
    return {
      id: 14,
      name: 'Property-Based Testing',
      icon: '🎲',
      color: '#FF9F43',
      score: 50,
      issues: ['Não foi possível analisar o código'],
      suggestions: ['Verifique a sintaxe do código'],
      detail: '—',
    }
  }
}
