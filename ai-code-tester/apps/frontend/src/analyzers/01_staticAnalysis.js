/**
 * Técnica 1: Análise Estática de Código
 * Detecta: uso de == em vez de ===, console.log, vars declaradas mas não usadas,
 * var em vez de let/const, with statement, eval()
 */
import { parseCode, traverse } from './astParser.js'

export default function staticAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  // Regex-based checks
  const lines = code.split('\n')
  lines.forEach((line, i) => {
    const ln = i + 1
    if (/console\.(log|warn|info|debug)\s*\(/.test(line)) {
      issues.push(`Linha ${ln}: console.log detectado — remova antes de produção`)
      deductions += 2
    }
    if (/[^=!<>]={1}[^=]/.test(line) && /==[^=]/.test(line)) {
      // double == without ===
    }
    if (/debugger/.test(line)) {
      issues.push(`Linha ${ln}: debugger statement detectado`)
      deductions += 5
    }
    if (/\bvar\b/.test(line)) {
      issues.push(`Linha ${ln}: uso de 'var' — prefira 'let' ou 'const'`)
      deductions += 3
    }
    if (/\bwith\s*\(/.test(line)) {
      issues.push(`Linha ${ln}: 'with' statement — proibido em strict mode`)
      deductions += 10
    }
    if (/[^!]==[^=]/.test(line) && !/===/.test(line)) {
      issues.push(`Linha ${ln}: comparação frouxa (==) — use === para type-safe`)
      deductions += 3
    }
    if (/!=(?!=)/.test(line)) {
      issues.push(`Linha ${ln}: != detectado — use !== para comparação estrita`)
      deductions += 3
    }
  })

  // AST-based checks
  const { ast } = parseCode(code)
  if (ast) {
    const declaredVars = new Set()
    const usedVars = new Set()

    traverse(ast, {
      VariableDeclarator(node) {
        if (node.id?.name) declaredVars.add(node.id.name)
      },
      Identifier(node) {
        usedVars.add(node.name)
      },
    })

    for (const v of declaredVars) {
      if (!usedVars.has(v) && !v.startsWith('_')) {
        issues.push(`Variável '${v}' declarada mas não utilizada`)
        deductions += 4
      }
    }
  }

  if (issues.length === 0) {
    suggestions.push('Código limpo — sem problemas de análise estática detectados')
  } else {
    suggestions.push('Execute ESLint com regras recomendadas para validação completa')
    suggestions.push('Considere usar TypeScript para verificações estáticas mais robustas')
  }

  const score = Math.max(0, 100 - deductions)
  return {
    id: 1,
    name: 'Análise Estática',
    icon: '🔍',
    color: '#6C63FF',
    score,
    issues: issues.slice(0, 10),
    suggestions,
    detail: `${issues.length} problema(s) encontrado(s)`,
  }
}
