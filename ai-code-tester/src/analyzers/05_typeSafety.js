/**
 * Técnica 5: Segurança de Tipos
 * Verifica: uso de TypeScript, PropTypes, JSDoc @param/@returns,
 * any implícito, type assertions perigosas
 */
import { parseCode, getFunctions } from './astParser.js'

export default function typeSafetyAnalysis(code) {
  const issues = []
  const suggestions = []
  let score = 100

  const isTypeScript = /\.ts$|\.tsx$/.test('') ||
    /:\s*(string|number|boolean|any|void|never|unknown)\b/.test(code) ||
    /interface\s+\w+|type\s+\w+\s*=/.test(code)

  const hasPropTypes = /PropTypes\.|\.propTypes\s*=/.test(code)
  const hasJSDoc = /@param|@returns|@type/.test(code)
  const hasAny = /:\s*any\b/.test(code)
  const hasTypeAssertion = /as\s+any\b/.test(code)
  const hasNonNullAssertion = /!\./g.test(code)

  if (!isTypeScript && !hasPropTypes && !hasJSDoc) {
    issues.push('Sem anotações de tipo — código JavaScript puro sem type safety')
    score -= 30
  }

  if (isTypeScript) {
    suggestions.push('TypeScript detectado — boa prática de type safety')
    if (hasAny) {
      issues.push("Uso de 'any' detectado — evite; prefira tipos específicos ou 'unknown'")
      score -= 15
    }
    if (hasTypeAssertion) {
      issues.push("'as any' detectado — type assertion insegura")
      score -= 10
    }
    if (hasNonNullAssertion) {
      issues.push("Non-null assertion (!) detectada — pode causar runtime errors")
      score -= 8
    }
  }

  // Check function parameter types via AST
  const { ast } = parseCode(code)
  if (ast) {
    const fns = getFunctions(ast)
    let untypedParams = 0

    fns.forEach(fn => {
      fn.params?.forEach(param => {
        if (!param.typeAnnotation && !param.optional) {
          untypedParams++
        }
      })
    })

    if (untypedParams > 0 && isTypeScript) {
      issues.push(`${untypedParams} parâmetro(s) sem anotação de tipo`)
      score -= Math.min(20, untypedParams * 3)
    }
  }

  if (!hasPropTypes && !isTypeScript) {
    issues.push('Componentes React sem PropTypes ou TypeScript — props não validadas')
    score -= 15
  }

  if (issues.length === 0) {
    suggestions.push('Type safety adequada detectada')
  }
  if (!isTypeScript) {
    suggestions.push('Migre para TypeScript para type safety em tempo de compilação')
  }
  suggestions.push('Use strict: true no tsconfig.json para máxima segurança de tipos')

  return {
    id: 5,
    name: 'Segurança de Tipos',
    icon: '📐',
    color: '#FFB020',
    score: Math.max(0, score),
    issues: issues.slice(0, 8),
    suggestions,
    detail: isTypeScript ? 'TypeScript detectado' : hasPropTypes ? 'PropTypes detectado' : 'JavaScript puro',
  }
}
