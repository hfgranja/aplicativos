/**
 * Gerador de Testes Funcionais
 * Gera templates Jest/Vitest baseados nos resultados da análise e funções detectadas
 */
import { parseCode, getFunctions } from '../analyzers/astParser.js'
import { generateMutationTests } from './mutationGenerator.js'

function getFunctionName(fn) {
  return fn.id?.name ||
    fn.key?.name ||
    'unknownFunction'
}

function getParamNames(fn) {
  return (fn.params || []).map(p => {
    if (p.type === 'Identifier') return p.name
    if (p.type === 'AssignmentPattern') return p.left?.name || 'param'
    if (p.type === 'RestElement') return `...${p.argument?.name || 'rest'}`
    return 'param'
  })
}

function generateImport(code) {
  // Detect module exports
  const namedExports = [...code.matchAll(/export\s+(?:const|function|class)\s+(\w+)/g)]
    .map(m => m[1])
  const hasDefaultExport = /export\s+default/.test(code)

  if (namedExports.length > 0) {
    return `import { ${namedExports.join(', ')} } from './module'`
  }
  if (hasDefaultExport) {
    return `import moduleUnderTest from './module'`
  }
  return `// Importe o módulo a ser testado\n// import { ... } from './module'`
}

function generateFunctionTests(fn, _code) {
  const name = getFunctionName(fn)
  const params = getParamNames(fn)
  const isAsync = fn.async

  const callSig = params.length > 0
    ? params.join(', ')
    : ''

  const mockParams = params.map(p => {
    if (p.includes('...')) return '[]'
    if (/id|Id/.test(p)) return '1'
    if (/name|Name|str/.test(p)) return `'test-${p}'`
    if (/count|num|index|size|limit/.test(p)) return '10'
    if (/list|arr|items/.test(p)) return '[]'
    if (/obj|data|config|options/.test(p)) return '{}'
    if (/cb|callback|fn/.test(p)) return 'jest.fn()'
    return `/* ${p} */`
  }).join(', ')

  const awaitKeyword = isAsync ? 'await ' : ''

  return `
  describe('${name}', () => {
    it('deve retornar um valor definido com entradas válidas', ${isAsync ? 'async ' : ''}() => {
      // Arrange
      ${params.length > 0 ? `const [${params.join(', ')}] = [${mockParams}]` : '// sem parâmetros'}

      // Act
      const result = ${awaitKeyword}${name}(${callSig})

      // Assert
      expect(result).toBeDefined()
    })

    it('deve lidar com entradas nulas/undefined sem lançar exceção', ${isAsync ? 'async ' : ''}() => {
      ${params.length > 0
        ? `expect(${isAsync ? 'async ' : ''}() => ${awaitKeyword}${name}(${params.map(() => 'null').join(', ')})).not.toThrow()`
        : `const result = ${awaitKeyword}${name}()\n      expect(result).toBeDefined()`
      }
    })
${isAsync ? `
    it('deve rejeitar com erro para entrada inválida', async () => {
      await expect(${name}(${params.map(() => 'undefined').join(', ')})).rejects.toBeDefined()
    })
` : ''}  })`
}

function generateFetchMocks(code) {
  const hasFetch = /\bfetch\s*\(/.test(code)
  const hasAxios = /\baxios\b/.test(code)

  if (!hasFetch && !hasAxios) return ''

  return `
// ==========================================
// Setup: Mock de chamadas de rede
// ==========================================
${hasFetch ? `
// Mock global fetch
global.fetch = jest.fn()

beforeEach(() => {
  fetch.mockClear()
})

// Helper para mock de resposta bem-sucedida
const mockFetchSuccess = (data) => {
  fetch.mockResolvedValueOnce({
    ok: true,
    status: 200,
    json: async () => data,
    text: async () => JSON.stringify(data),
  })
}

// Helper para mock de erro HTTP
const mockFetchError = (status = 500) => {
  fetch.mockResolvedValueOnce({
    ok: false,
    status,
    json: async () => ({ error: 'Server Error' }),
  })
}
` : ''}${hasAxios ? `
// Mock axios
jest.mock('axios')
import axios from 'axios'
` : ''}`
}

function generateSecurityTests(results) {
  const secResult = results.find(r => r.id === 4)
  if (!secResult || secResult.issues.length === 0) return ''

  return `
// ==========================================
// Testes de Segurança (gerados a partir da análise)
// ==========================================
describe('Validação de Segurança', () => {
  it('não deve aceitar input com scripts maliciosos (XSS)', () => {
    const maliciousInput = '<script>alert("xss")</script>'
    // Verifique que o input é sanitizado antes de ser exibido
    // expect(sanitize(maliciousInput)).not.toContain('<script>')
  })

  it('não deve expor dados sensíveis na resposta', () => {
    // Verifique que campos como password, token não são retornados
    // const response = getUser()
    // expect(response).not.toHaveProperty('password')
    // expect(response).not.toHaveProperty('token')
  })

  it('deve validar entradas antes de processar', () => {
    // Teste com inputs extremos
    const extremeInputs = ['', null, undefined, 'a'.repeat(10000), '../../etc/passwd']
    // extremeInputs.forEach(input => {
    //   expect(() => processInput(input)).not.toThrow()
    // })
  })
})`
}

function generateCoverageTests(results) {
  const coverResult = results.find(r => r.id === 7)
  const branchInfo = coverResult?.detail || ''

  return `
// ==========================================
// Testes de Cobertura de Branches
// ${branchInfo}
// ==========================================
describe('Cobertura de Branches', () => {
  it('deve cobrir o caminho principal (happy path)', () => {
    // TODO: teste com entradas que seguem o fluxo esperado
    expect(true).toBe(true) // placeholder
  })

  it('deve cobrir caminhos de erro (sad path)', () => {
    // TODO: teste com entradas inválidas, limites, casos extremos
    expect(true).toBe(true) // placeholder
  })

  it('deve cobrir condições de borda (edge cases)', () => {
    // TODO: teste com valores limite: 0, -1, '', [], null
    expect(true).toBe(true) // placeholder
  })
})`
}

function generateIntegrationTests(code) {
  const hasComponents = /<[A-Z]/.test(code)
  if (!hasComponents) return ''

  return `
// ==========================================
// Testes de Integração (Componentes React)
// ==========================================
// import { render, screen, fireEvent, waitFor } from '@testing-library/react'

describe('Testes de Integração de Componentes', () => {
  it('deve renderizar sem erros', () => {
    // const { container } = render(<ComponentName />)
    // expect(container).toBeInTheDocument()
  })

  it('deve responder a interações do usuário', async () => {
    // render(<ComponentName />)
    // const button = screen.getByRole('button')
    // fireEvent.click(button)
    // await waitFor(() => expect(screen.getByText('resultado')).toBeInTheDocument())
  })

  it('deve exibir estado de loading durante fetch', async () => {
    // mockFetchSuccess({ data: [] })
    // render(<ComponentName />)
    // expect(screen.getByText(/loading/i)).toBeInTheDocument()
    // await waitFor(() => expect(screen.queryByText(/loading/i)).not.toBeInTheDocument())
  })
})`
}

/**
 * Main test generator
 * @param {string} code - source code
 * @param {Array} results - analysis results from orchestrator
 * @returns {string} generated test file content
 */
export function generateTests(code, results) {
  const { ast } = parseCode(code)
  const fns = ast ? getFunctions(ast) : []

  // Filter to named, non-trivial functions
  const testableFns = fns.filter(fn => {
    const name = getFunctionName(fn)
    return name !== 'unknownFunction' && name.length > 1 &&
      !['render', 'constructor'].includes(name)
  }).slice(0, 10) // max 10 functions

  const overallScore = results.length > 0
    ? Math.round(results.reduce((s, r) => s + r.score, 0) / results.length)
    : 0

  const criticalIssues = results.flatMap(r => r.issues).filter(i => /CRÍTICO/i.test(i))

  const header = `/**
 * ============================================================
 * TESTES GERADOS AUTOMATICAMENTE — AI Code Tester
 * Score geral de qualidade: ${overallScore}/100
 * ${criticalIssues.length > 0 ? `⚠️  ${criticalIssues.length} problema(s) crítico(s) detectado(s)` : '✅ Sem problemas críticos'}
 *
 * Execute: npx vitest   ou   npx jest
 * ============================================================
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals'
// Para Vitest: import { describe, it, expect, beforeEach, afterEach, vi as jest } from 'vitest'

${generateImport(code)}
`

  const fetchMocks = generateFetchMocks(code)

  const functionTests = testableFns.length > 0
    ? `
// ==========================================
// Testes Unitários por Função
// ==========================================
${testableFns.map(fn => generateFunctionTests(fn, code)).join('\n')}`
    : `
// ==========================================
// Nenhuma função nomeada exportada detectada
// Adicione testes manualmente para o módulo
// ==========================================`

  const securityTests = generateSecurityTests(results)
  const coverageTests = generateCoverageTests(results)
  const integrationTests = generateIntegrationTests(code)
  const mutationTests = generateMutationTests(code)

  const footer = `

// ==========================================
// Configuração sugerida (vitest.config.js)
// ==========================================
/*
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      threshold: { lines: 80, branches: 70, functions: 80 },
    },
  },
})
*/
`

  return header + fetchMocks + functionTests + securityTests + coverageTests + integrationTests + mutationTests + footer
}
