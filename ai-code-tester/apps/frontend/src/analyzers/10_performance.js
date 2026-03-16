/**
 * Técnica 10: Anti-padrões de Performance
 * Detecta: loops aninhados O(n²), setState em loop, operações síncronas
 * pesadas em async, re-renders desnecessários em React
 */
import { parseCode, traverse } from './astParser.js'

export default function performanceAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  const lines = code.split('\n')

  // Regex checks
  lines.forEach((line, i) => {
    const ln = i + 1

    // Synchronous file/network operations (Node.js patterns)
    if (/\bfs\.readFileSync|fs\.writeFileSync|fs\.existsSync/.test(line)) {
      issues.push(`Linha ${ln}: operação de arquivo síncrona — use versão async/await`)
      deductions += 8
    }

    // JSON.parse in loop
    if (/JSON\.parse/.test(line) && /for|forEach|map|reduce|filter/.test(lines[Math.max(0, i - 2)]) ) {
      issues.push(`Linha ${ln}: JSON.parse dentro de loop — mova para fora do loop`)
      deductions += 6
    }

    // String concatenation in loop
    if (/\+=['"]/.test(line)) {
      issues.push(`Linha ${ln}: concatenação de string com += — use array.join() para performance`)
      deductions += 4
    }

    // document.querySelector in loop
    if (/document\.(querySelector|getElementById|getElementsBy)/.test(line)) {
      deductions += 2
    }
  })

  // AST checks
  const { ast } = parseCode(code)
  if (ast) {
    // Nested loops O(n²)
    let loopDepth = 0
    let maxLoopDepth = 0
    const LOOP_TYPES = new Set(['ForStatement', 'ForInStatement', 'ForOfStatement', 'WhileStatement', 'DoWhileStatement'])

    traverse(ast, {
      ...Object.fromEntries([...LOOP_TYPES].map(type => [
        type,
        { enter: () => { loopDepth++; maxLoopDepth = Math.max(maxLoopDepth, loopDepth) }, exit: () => { loopDepth-- } },
      ])),
    })

    if (maxLoopDepth >= 3) {
      issues.push(`Loop aninhado com ${maxLoopDepth} níveis — complexidade O(n³) ou pior`)
      deductions += 20
    } else if (maxLoopDepth === 2) {
      issues.push('Loop duplo aninhado detectado — complexidade O(n²), considere otimizar')
      deductions += 10
    }

    // React: setState in loop
    let inLoop = false
    traverse(ast, {
      ForStatement: { enter: () => { inLoop = true }, exit: () => { inLoop = false } },
      ForOfStatement: { enter: () => { inLoop = true }, exit: () => { inLoop = false } },
      CallExpression(n) {
        if (!inLoop) return
        const callee = n.callee
        if (callee.type === 'Identifier' &&
            /^set[A-Z]/.test(callee.name)) {
          issues.push(`setState/Hook setter chamado dentro de loop — causa re-renders excessivos`)
          deductions += 15
        }
      },
    })

    // Memory leak: event listeners without cleanup
    let addListenerCount = 0
    let removeListenerCount = 0
    traverse(ast, {
      CallExpression(n) {
        const name = n.callee?.property?.name
        if (name === 'addEventListener') addListenerCount++
        if (name === 'removeEventListener') removeListenerCount++
      },
    })
    if (addListenerCount > removeListenerCount) {
      const leaks = addListenerCount - removeListenerCount
      issues.push(`${leaks} addEventListener sem removeEventListener correspondente — possível memory leak`)
      deductions += leaks * 5
    }

    // Unnecessary spread in render
    const spreadInRender = (code.match(/\.\.\.(?:props|state|obj)\b/g) || []).length
    if (spreadInRender > 5) {
      issues.push('Spread operators excessivos — pode causar re-renders desnecessários')
      deductions += 5
    }
  }

  if (issues.length === 0) {
    suggestions.push('Sem anti-padrões de performance críticos detectados')
  } else {
    suggestions.push('Use useMemo/useCallback para evitar recálculos desnecessários')
    suggestions.push('Prefira operações O(n) usando Map/Set em vez de arrays para lookups')
    suggestions.push('Limpe event listeners e subscriptions no useEffect cleanup')
    suggestions.push('Use React.memo para componentes que recebem props estáveis')
  }

  return {
    id: 10,
    name: 'Anti-padrões de Performance',
    icon: '🚀',
    color: '#DDA0DD',
    score: Math.max(0, 100 - deductions),
    issues: issues.slice(0, 8),
    suggestions,
    detail: `${issues.length} problema(s) de performance`,
  }
}
