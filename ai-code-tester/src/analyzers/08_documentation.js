/**
 * Técnica 8: Qualidade de Documentação
 * Verifica: JSDoc em funções, proporção comentário/código,
 * README hints, TODO/FIXME não resolvidos
 */
import { parseCode, getFunctions } from './astParser.js'

export default function documentationQuality(code) {
  const issues = []
  const suggestions = []

  const lines = code.split('\n')
  const codeLines = lines.filter(l => l.trim().length > 0 && !l.trim().startsWith('//')).length
  const commentLines = lines.filter(l => l.trim().startsWith('//') || l.trim().startsWith('*')).length
  const jsdocBlocks = (code.match(/\/\*\*[\s\S]*?\*\//g) || []).length
  const todoCount = (code.match(/\/\/\s*(TODO|FIXME|HACK|XXX|BUG)/gi) || []).length
  const hasJSDoc = jsdocBlocks > 0
  const commentRatio = codeLines === 0 ? 0 : commentLines / codeLines

  // Parse functions
  const { ast } = parseCode(code)
  let fnCount = 0
  let documentedFns = 0

  if (ast) {
    const fns = getFunctions(ast)
    fnCount = fns.length

    // Check JSDoc presence before each function
    fns.forEach(fn => {
      const startLine = fn.loc?.start?.line || 0
      // Look for /** ... */ in 3 lines above
      for (let i = Math.max(0, startLine - 4); i < startLine; i++) {
        if (lines[i]?.includes('/**') || lines[i]?.includes('* @param') || lines[i]?.includes('* @returns')) {
          documentedFns++
          break
        }
      }
    })
  }

  let score = 50 // base

  // JSDoc bonus
  if (hasJSDoc) {
    score += 20
    suggestions.push(`${jsdocBlocks} bloco(s) JSDoc encontrado(s)`)
  } else if (fnCount > 3) {
    issues.push('Nenhum bloco JSDoc encontrado — documente funções públicas')
    score -= 15
  }

  // Comment ratio
  if (commentRatio < 0.05 && codeLines > 20) {
    issues.push(`Proporção de comentários muito baixa (${(commentRatio * 100).toFixed(1)}%) — documente lógica complexa`)
    score -= 10
  } else if (commentRatio >= 0.1) {
    score += 10
  }

  // Function documentation ratio
  if (fnCount > 0) {
    const docRatio = documentedFns / fnCount
    score += Math.round(docRatio * 20)
    if (docRatio < 0.5 && fnCount > 2) {
      issues.push(`${fnCount - documentedFns} de ${fnCount} funções sem documentação JSDoc`)
    }
  }

  // TODOs
  if (todoCount > 0) {
    issues.push(`${todoCount} TODO/FIXME encontrado(s) — resolva antes do deploy`)
    score -= todoCount * 3
  }

  if (issues.length === 0) {
    suggestions.push('Boa cobertura de documentação detectada')
  }
  suggestions.push('Use JSDoc para todas as funções públicas com @param e @returns')
  suggestions.push('Mantenha comentários focados no "porquê", não no "o quê"')

  return {
    id: 8,
    name: 'Qualidade de Documentação',
    icon: '📝',
    color: '#96CEB4',
    score: Math.max(0, Math.min(100, score)),
    issues: issues.slice(0, 8),
    suggestions,
    detail: `${commentLines} linhas comentadas · ${jsdocBlocks} JSDoc · ${todoCount} TODO(s)`,
  }
}
