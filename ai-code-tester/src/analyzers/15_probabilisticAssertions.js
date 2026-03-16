export default function probabilisticAssertionsAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  try {
    // Detect AI API usage
    const AI_PATTERNS = [
      { pattern: /openai|OpenAI|new OpenAI/, name: 'OpenAI' },
      { pattern: /anthropic|Anthropic|new Anthropic/, name: 'Anthropic' },
      { pattern: /@google\/generative-ai|generativeai|GoogleGenerativeAI/, name: 'Google Gemini' },
      { pattern: /ollama|new Ollama/, name: 'Ollama' },
      { pattern: /cohere|new CohereClient/, name: 'Cohere' },
      { pattern: /\.completions\.create|\.chat\.completions/, name: 'OpenAI Chat API' },
      { pattern: /\.messages\.create/, name: 'Anthropic Messages API' },
      { pattern: /generateContent|\.generateMessage/, name: 'Gemini API' },
      { pattern: /huggingface|HfInference/, name: 'HuggingFace' },
    ]

    const detectedAPIs = AI_PATTERNS.filter(p => p.pattern.test(code)).map(p => p.name)
    const hasAICode = detectedAPIs.length > 0

    if (!hasAICode) {
      // Not applicable — give neutral score
      return {
        id: 15,
        name: 'Asserções Probabilísticas',
        icon: '🎯',
        color: '#A29BFE',
        score: 82,
        issues: [],
        suggestions: ['Técnica relevante para código que integra APIs de IA (OpenAI, Anthropic, Gemini)'],
        detail: 'Sem APIs de IA detectadas',
      }
    }

    // AI code detected — now check for probabilistic handling

    // 1. Missing try/catch around AI calls
    const aiCallLines = code.split('\n').filter(l =>
      /\.completions\.|\.messages\.|generateContent|\.chat\(/.test(l)
    )
    const hasTryCatch = /try\s*\{/.test(code)
    if (aiCallLines.length > 0 && !hasTryCatch) {
      deductions += 25
      issues.push(`${aiCallLines.length} chamada(s) à API de IA sem try/catch — LLMs podem falhar inesperadamente`)
      suggestions.push('Sempre envolva chamadas LLM com try/catch e implemente retry logic')
    }

    // 2. Exact string comparison with LLM output (risky)
    const exactLLMComparisons = (code.match(/===\s*['"`][A-Za-z ]{10,}['"`]|['"`][A-Za-z ]{10,}['"`]\s*===/g) || []).length
    if (exactLLMComparisons > 0 && hasAICode) {
      deductions += 20
      issues.push(`${exactLLMComparisons} comparação(ões) exata(s) com strings longas — LLMs não garantem saída determinística`)
      suggestions.push('Use .includes(), .startsWith() ou regex ao invés de === para comparar saídas de LLM')
    }

    // 3. .choices[0] or .content without optional chaining
    const unsafeAccess = (code.match(/\.choices\[0\](?!\?)(?!\s*\?)|\bcontent\b(?<!\?\.)\.|\btext\b(?<!\?\.)\.(?!test\b)/g) || []).length
    if (unsafeAccess > 0) {
      deductions += 20
      issues.push(`Acesso a ${unsafeAccess} propriedade(s) de resposta LLM sem optional chaining (?.)`)
      suggestions.push('Use optional chaining: response?.choices?.[0]?.message?.content ?? ""')
    }

    // 4. JSON.parse on LLM response without try/catch
    const jsonParseCalls = (code.match(/JSON\.parse\s*\(/g) || []).length
    if (jsonParseCalls > 0 && !hasTryCatch) {
      deductions += 15
      issues.push(`${jsonParseCalls} JSON.parse() sem try/catch — LLMs frequentemente retornam JSON malformado`)
      suggestions.push('Envolva JSON.parse() de respostas LLM em try/catch com fallback')
    }

    // 5. Missing schema validation
    const hasSchemaValidation = /zod|yup|joi|ajv|superstruct|valibot|z\.object|z\.string/.test(code)
    if (!hasSchemaValidation && detectedAPIs.length > 0) {
      deductions += 15
      issues.push('Nenhuma validação de schema detectada para respostas de IA (Zod, Yup, Joi)')
      suggestions.push('Use Zod para validar estrutura: z.object({ answer: z.string() }).parse(response)')
    }

    // 6. No timeout/abort for AI calls
    const hasTimeout = /AbortController|timeout|signal|setTimeout.*abort/i.test(code)
    if (!hasTimeout && hasAICode) {
      deductions += 10
      issues.push('Chamadas à IA sem timeout configurado — pode travar indefinidamente')
      suggestions.push('Configure timeout: new AbortController() + signal na chamada à API')
    }

    // 7. Floating point results without tolerance
    const floatOps = (code.match(/\.\d+\s*[+\-\*\/]|\d+\.\d+/g) || []).length
    const hasToBeCloseTo = /toBeCloseTo/.test(code)
    if (floatOps > 2 && !hasToBeCloseTo) {
      deductions += 5
      issues.push('Operações com float sem toBeCloseTo() nos testes — precisão probabilística')
      suggestions.push('Para valores float, use expect(val).toBeCloseTo(expected, 2) ao invés de toBe()')
    }

    const finalScore = Math.max(0, 100 - deductions)
    return {
      id: 15,
      name: 'Asserções Probabilísticas',
      icon: '🎯',
      color: '#A29BFE',
      score: finalScore,
      issues: issues.slice(0, 7),
      suggestions: suggestions.slice(0, 4),
      detail: `APIs detectadas: ${detectedAPIs.join(', ')}`,
    }
  } catch {
    return {
      id: 15,
      name: 'Asserções Probabilísticas',
      icon: '🎯',
      color: '#A29BFE',
      score: 50,
      issues: ['Não foi possível analisar o código'],
      suggestions: [],
      detail: '—',
    }
  }
}
