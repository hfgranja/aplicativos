import { parseCode, getFunctions } from './astParser.js'

export default function aiCodeReviewAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  try {
    const lines = code.split('\n')
    const ast = parseCode(code)
    const functions = getFunctions(ast)

    // 1. TODO / FIXME / placeholder / scaffold comments left by AI
    const scaffoldComments = lines.filter(l =>
      /\/\/\s*(TODO|FIXME|HACK|XXX|PLACEHOLDER|IMPLEMENT|YOUR_CODE_HERE|ADD_YOUR)/i.test(l)
    )
    if (scaffoldComments.length > 0) {
      deductions += scaffoldComments.length * 8
      issues.push(`${scaffoldComments.length} comentário(s) scaffold de IA detectado(s): TODO/FIXME/PLACEHOLDER`)
      suggestions.push('Remova comentários TODO/FIXME gerados por IA e implemente a lógica real')
    }

    // 2. Debug console.log patterns typical of AI output
    const debugLogs = lines.filter(l =>
      /console\.log\s*\(\s*['"`](test|debug|check|here|log|todo|temp|remove|working|step|testing)/i.test(l) ||
      /console\.log\s*\(\s*['"`]\d/.test(l)
    )
    if (debugLogs.length > 0) {
      deductions += debugLogs.length * 5
      issues.push(`${debugLogs.length} console.log de debug de IA detectado(s)`)
      suggestions.push('Remova logs de debug deixados pela IA antes de produção')
    }

    // 3. Dead code after return statements
    let deadCodeCount = 0
    for (let i = 0; i < lines.length - 1; i++) {
      const trimmed = lines[i].trim()
      if (/^return\s/.test(trimmed) || trimmed === 'return;') {
        // Check next non-empty line for dead code
        for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
          const next = lines[j].trim()
          if (next && !next.startsWith('}') && !next.startsWith('//') && !next.startsWith('case ') && !next.startsWith('default:')) {
            deadCodeCount++
            break
          }
        }
      }
    }
    if (deadCodeCount > 0) {
      deductions += deadCodeCount * 12
      issues.push(`${deadCodeCount} bloco(s) de código inacessível após return — padrão comum em código gerado por IA`)
      suggestions.push('Remova código após return — é inacessível (dead code hallucination)')
    }

    // 4. Monolithic functions (AI generates long functions)
    const longFunctions = functions.filter(f => f.lineCount && f.lineCount > 80)
    if (longFunctions.length > 0) {
      deductions += longFunctions.length * 10
      issues.push(`${longFunctions.length} função(ões) com > 80 linhas — IA tende a gerar funções monolíticas`)
      suggestions.push('Quebre funções longas em funções menores e testáveis (Single Responsibility)')
    } else {
      const mediumFunctions = functions.filter(f => f.lineCount && f.lineCount > 50)
      if (mediumFunctions.length >= 2) {
        deductions += 8
        issues.push(`${mediumFunctions.length} função(ões) com 50-80 linhas — considere refatorar`)
        suggestions.push('Funções acima de 50 linhas geralmente têm múltiplas responsabilidades')
      }
    }

    // 5. Deep property access without optional chaining
    const deepAccess = (code.match(/\w+\.\w+\.\w+\.\w+(?!\?)/g) || [])
      .filter(m => !m.startsWith('console.') && !m.startsWith('Math.') && !m.startsWith('Object.') && !m.startsWith('Array.'))
    if (deepAccess.length > 0) {
      deductions += Math.min(deepAccess.length * 4, 20)
      issues.push(`${deepAccess.length} acesso(s) encadeado(s) sem optional chaining (?.) — risco de TypeError`)
      suggestions.push('Use optional chaining: a?.b?.c?.d ao invés de a.b.c.d')
    }

    // 6. Unused variable declarations (common AI pattern)
    const varDeclarations = code.match(/\b(?:const|let|var)\s+(\w+)\s*=/g) || []
    let unusedCount = 0
    for (const decl of varDeclarations) {
      const varNameMatch = decl.match(/(?:const|let|var)\s+(\w+)/)
      if (!varNameMatch) continue
      const varName = varNameMatch[1]
      // Check if variable is used elsewhere (rough heuristic)
      const uses = (code.match(new RegExp(`\\b${varName}\\b`, 'g')) || []).length
      if (uses === 1) unusedCount++  // declared but only mentioned once (the declaration)
    }
    if (unusedCount > 2) {
      deductions += Math.min(unusedCount * 5, 15)
      issues.push(`~${unusedCount} variável(eis) potencialmente não utilizadas — padrão de scaffold de IA`)
      suggestions.push('Remova variáveis declaradas mas não utilizadas')
    }

    // 7. Hardcoded "example" values from AI scaffolding
    const exampleValues = (code.match(/['"`](example|sample|test-data|foo|bar|baz|lorem|ipsum|dummy|mock-data)['"`]/gi) || []).length
    if (exampleValues > 2) {
      deductions += exampleValues * 3
      issues.push(`${exampleValues} valor(es) de exemplo hardcoded detectado(s) (foo/bar/example) — remover antes de produção`)
      suggestions.push('Substitua valores de exemplo por constantes significativas ou dados reais')
    }

    // 8. Repeated identical error handling (AI copy-pastes catch blocks)
    const catchBlocks = (code.match(/catch\s*\(\s*\w+\s*\)\s*\{[^}]*\}/g) || [])
    const identicalCatches = catchBlocks.filter((b, i) => catchBlocks.indexOf(b) !== i).length
    if (identicalCatches > 0) {
      deductions += identicalCatches * 8
      issues.push(`${identicalCatches} bloco(s) catch idêntico(s) — IA frequentemente copia tratamento de erro`)
      suggestions.push('Centralize tratamento de erros em uma função utilitária ao invés de repetir')
    }

    const finalScore = Math.max(0, 100 - deductions)
    const smellCount = scaffoldComments.length + debugLogs.length + deadCodeCount + longFunctions.length
    return {
      id: 16,
      name: 'AI Code Review',
      icon: '🤖',
      color: '#FD79A8',
      score: finalScore,
      issues: issues.slice(0, 8),
      suggestions: suggestions.slice(0, 4),
      detail: `${smellCount} code smell(s) de IA detectado(s)`,
    }
  } catch {
    return {
      id: 16,
      name: 'AI Code Review',
      icon: '🤖',
      color: '#FD79A8',
      score: 50,
      issues: ['Não foi possível analisar o código'],
      suggestions: [],
      detail: '—',
    }
  }
}
