/**
 * Técnica 9: Conformidade com Boas Práticas (SOLID, DRY, KISS)
 * Detecta: funções muito longas, classes com muitas responsabilidades,
 * magic numbers, deep nesting, God objects
 */
import { parseCode, traverse, getFunctions, lineCount } from './astParser.js'

export default function bestPracticesAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  const { ast } = parseCode(code)

  if (ast) {
    const fns = getFunctions(ast)

    // KISS: funções muito longas (> 50 linhas)
    fns.forEach(fn => {
      const name = fn.id?.name || 'anônima'
      const lines = lineCount(fn)
      if (lines > 100) {
        issues.push(`Função '${name}': ${lines} linhas — MUITO LONGA, divida em partes menores`)
        deductions += 15
      } else if (lines > 50) {
        issues.push(`Função '${name}': ${lines} linhas — longa, considere refatorar`)
        deductions += 8
      }
    })

    // DRY: nesting profundo (> 4 levels)
    let maxNesting = 0
    let currentNesting = 0
    traverse(ast, {
      BlockStatement: {
        enter() { currentNesting++; maxNesting = Math.max(maxNesting, currentNesting) },
        exit() { currentNesting-- },
      },
    })
    if (maxNesting > 5) {
      issues.push(`Aninhamento máximo de ${maxNesting} níveis — use early return e extração de funções`)
      deductions += 10
    }

    // Magic numbers
    let magicNumbers = 0
    traverse(ast, {
      NumericLiteral(n) {
        if (![0, 1, 2, -1, 100, 1000].includes(n.value)) {
          magicNumbers++
        }
      },
    })
    if (magicNumbers > 5) {
      issues.push(`${magicNumbers} "magic numbers" detectados — use constantes nomeadas`)
      deductions += Math.min(15, magicNumbers * 2)
    }

    // God component / class (too many methods)
    traverse(ast, {
      ClassDeclaration(n) {
        const methods = (n.body?.body || []).filter(m => m.type === 'ClassMethod')
        if (methods.length > 15) {
          issues.push(`Classe '${n.id?.name}' com ${methods.length} métodos — possível God Object (viola SRP)`)
          deductions += 12
        }
      },
    })

    // Long parameter lists (> 4 params)
    fns.forEach(fn => {
      const name = fn.id?.name || 'anônima'
      if (fn.params?.length > 4) {
        issues.push(`Função '${name}': ${fn.params.length} parâmetros — use objeto de configuração`)
        deductions += 8
      }
    })
  }

  // Magic strings
  const magicStrings = [...code.matchAll(/['"`][a-z0-9_-]{10,}['"`]/gi)].length
  if (magicStrings > 10) {
    issues.push(`${magicStrings} strings literais longas — considere constantes ou i18n`)
    deductions += 5
  }

  const score = Math.max(0, 100 - deductions)

  if (issues.length === 0) {
    suggestions.push('Código segue boas práticas SOLID/DRY/KISS adequadamente')
  } else {
    suggestions.push('Aplique o princípio KISS: cada função deve fazer uma coisa')
    suggestions.push('Siga SRP (Single Responsibility Principle) para classes e módulos')
    suggestions.push('Extraia constantes para o topo do módulo com nomes descritivos')
    suggestions.push('Use early return para reduzir aninhamento profundo')
  }

  return {
    id: 9,
    name: 'Boas Práticas',
    icon: '⚡',
    color: '#FFEAA7',
    score,
    issues: issues.slice(0, 8),
    suggestions,
    detail: 'SOLID · DRY · KISS',
  }
}
