export default function crossModelValidationAnalysis(code) {
  const issues = []
  const suggestions = []
  let deductions = 0

  try {
    // Detect if this code interacts with AI models at all
    const AI_PATTERNS = [
      /openai|anthropic|gemini|ollama|cohere|mistral|llama/i,
      /\.completions\.|\.messages\.|generateContent|\.chat\(/,
      /gpt-|claude-|gemini-pro|llama-/i,
    ]
    const hasAICode = AI_PATTERNS.some(p => p.test(code))

    if (!hasAICode) {
      return {
        id: 18,
        name: 'Cross-Model Validation',
        icon: '🔀',
        color: '#74B9FF',
        score: 85,
        issues: [],
        suggestions: ['Técnica relevante para código que integra múltiplos modelos de IA ou assume comportamento de modelo específico'],
        detail: 'Sem integrações de modelos de IA detectadas',
      }
    }

    // 1. Hardcoded model names (model lock-in risk)
    const MODEL_NAMES = [
      'gpt-4', 'gpt-4o', 'gpt-3.5', 'gpt-3', 'gpt4', 'gpt3',
      'claude-3', 'claude-2', 'claude-instant', 'claude-3-5',
      'gemini-pro', 'gemini-flash', 'gemini-1.5',
      'llama-3', 'llama-2', 'llama3',
      'mistral-7b', 'mixtral',
      'command-r', 'command',
    ]
    const hardcodedModels = MODEL_NAMES.filter(m => new RegExp(`['"\`]${m}`, 'i').test(code))
    if (hardcodedModels.length > 0) {
      deductions += hardcodedModels.length * 12
      issues.push(`Modelo(s) hardcoded detectado(s): ${hardcodedModels.slice(0, 3).join(', ')} — risco de model lock-in`)
      suggestions.push('Abstraia o modelo em constante: const MODEL = process.env.AI_MODEL || "gpt-4o"')
    }

    // 2. JSON.parse without try/catch on LLM responses
    const jsonParseCount = (code.match(/JSON\.parse\s*\(/g) || []).length
    const hasTryCatch = /try\s*\{[\s\S]*?catch/.test(code)
    const hasSafeParse = /\.safeParse\(|JSON\.parse.*\?\?|JSON\.parse.*catch/.test(code)
    if (jsonParseCount > 0 && !hasTryCatch && !hasSafeParse) {
      deductions += 20
      issues.push(`${jsonParseCount} JSON.parse() sem proteção — modelos diferentes produzem JSON com formatos diferentes`)
      suggestions.push('Use try/catch ou Zod .safeParse() ao parsear JSON de LLMs: respostas variam entre modelos')
    }

    // 3. Missing response format validation
    const hasSchemaValidation = /zod|yup|joi|ajv|z\.object|z\.string|\.parse\(|\.safeParse\(/.test(code)
    const hasManualValidation = /typeof\s+\w+\s*===|instanceof\s+|Array\.isArray/.test(code)
    if (!hasSchemaValidation && !hasManualValidation) {
      deductions += 18
      issues.push('Nenhuma validação de formato de resposta — modelos distintos estruturam respostas diferentemente')
      suggestions.push('Valide o schema da resposta com Zod: z.object({ content: z.string() }).parse(response)')
    }

    // 4. Missing fallback when model returns null/undefined
    const modelCalls = (code.match(/\.(completions|messages|generateContent|chat)\s*\.\s*(create|send|generate)\s*\(/g) || []).length
    const hasNullishFallback = /\?\?\s*['"`\[]|\|\|\s*['"`\[]|\?\s*['"`\[]/.test(code)
    if (modelCalls > 0 && !hasNullishFallback) {
      deductions += 15
      issues.push('Sem fallback para quando o modelo retorna null/undefined — diferentes modelos têm comportamentos distintos')
      suggestions.push('Sempre defina fallback: const text = response?.choices?.[0]?.message?.content ?? "Resposta indisponível"')
    }

    // 5. Long hardcoded prompts without abstraction
    const longPromptStrings = (code.match(/['"`][^'"`\n]{200,}['"`]/g) || []).length
    if (longPromptStrings > 0) {
      deductions += longPromptStrings * 8
      issues.push(`${longPromptStrings} prompt(s) longo(s) hardcoded — dificulta ajuste e teste cross-model`)
      suggestions.push('Extraia prompts para constantes ou arquivos separados para facilitar ajuste por modelo')
    }

    // 6. No model-specific error handling
    const hasModelErrorHandling = /rate.?limit|quota|overloaded|model_not_found|context_length/i.test(code)
    if (!hasModelErrorHandling && hasAICode) {
      deductions += 10
      issues.push('Sem tratamento de erros específicos de modelo (rate limit, quota, context_length_exceeded)')
      suggestions.push('Trate erros específicos: rate_limit_exceeded, model_overloaded, context_length_exceeded')
    }

    // 7. No retry logic for transient failures
    const hasRetry = /retry|retries|backoff|attempt/i.test(code)
    if (!hasRetry && hasAICode) {
      deductions += 8
      issues.push('Sem retry logic para falhas transientes — modelos têm disponibilidade variável')
      suggestions.push('Implemente exponential backoff: aguarde 1s, 2s, 4s antes de cada retry')
    }

    const finalScore = Math.max(0, 100 - deductions)
    return {
      id: 18,
      name: 'Cross-Model Validation',
      icon: '🔀',
      color: '#74B9FF',
      score: finalScore,
      issues: issues.slice(0, 7),
      suggestions: suggestions.slice(0, 4),
      detail: hardcodedModels.length > 0
        ? `${hardcodedModels.length} modelo(s) hardcoded`
        : 'Integração AI sem lock-in detectado',
    }
  } catch {
    return {
      id: 18,
      name: 'Cross-Model Validation',
      icon: '🔀',
      color: '#74B9FF',
      score: 50,
      issues: ['Não foi possível analisar o código'],
      suggestions: [],
      detail: '—',
    }
  }
}
