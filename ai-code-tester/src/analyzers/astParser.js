/**
 * AST Parser wrapper using @babel/parser
 * Supports JS, JSX, TS, TSX with graceful fallback
 */
import * as babelParser from '@babel/parser'

export function parseCode(code) {
  const plugins = ['jsx', 'classProperties', 'optionalChaining', 'nullishCoalescingOperator']

  // Try TypeScript first, fall back to plain JS
  for (const tsPlugin of [['typescript'], []]) {
    try {
      const ast = babelParser.parse(code, {
        sourceType: 'module',
        allowImportExportEverywhere: true,
        allowReturnOutsideFunction: true,
        allowSuperOutsideMethod: true,
        plugins: [...plugins, ...tsPlugin],
        errorRecovery: true,
      })
      return { ast, error: null, isTypeScript: tsPlugin.length > 0 }
    } catch {
      // try next
    }
  }
  return { ast: null, error: 'Could not parse code', isTypeScript: false }
}

/**
 * Traverse all nodes of an AST calling visitor for each
 */
export function traverse(node, visitor) {
  if (!node || typeof node !== 'object') return
  if (visitor[node.type]) visitor[node.type](node)
  for (const key of Object.keys(node)) {
    const child = node[key]
    if (Array.isArray(child)) {
      child.forEach(c => traverse(c, visitor))
    } else if (child && typeof child === 'object' && child.type) {
      traverse(child, visitor)
    }
  }
}

/**
 * Get all function nodes from AST
 */
export function getFunctions(ast) {
  const fns = []
  traverse(ast, {
    FunctionDeclaration: n => fns.push(n),
    FunctionExpression: n => fns.push(n),
    ArrowFunctionExpression: n => fns.push(n),
  })
  return fns
}

/**
 * Count lines in a source range
 */
export function lineCount(node) {
  if (!node?.loc) return 0
  return node.loc.end.line - node.loc.start.line + 1
}
