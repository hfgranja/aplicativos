import { queryOllama, checkOllamaAvailability, getCircuitState } from '../services/ollamaClient.js'

const DEVSTRAL = process.env.DEVSTRAL_MODEL || 'devstral'
const QWEN = process.env.QWEN_MODEL || 'qwen3-coder'

const CURRENT_TECHNIQUES = [
  'Análise Estática', 'Complexidade Ciclomática', 'Duplicação de Código',
  'Segurança', 'Segurança de Tipos', 'Risco de Dependências',
  'Cobertura de Testes', 'Qualidade de Documentação', 'Boas Práticas',
  'Anti-padrões de Performance', 'Tratamento de Erros',
  'Contratos de API', 'Testes por Mutação',
  'Property-Based Testing', 'Asserções Probabilísticas',
  'AI Code Review', 'Validação Visual Automatizada', 'Cross-Model Validation',
]

function extractJSON(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  if (fenced) { try { return JSON.parse(fenced[1].trim()) } catch { /* */ } }
  const arr = text.match(/\[[\s\S]*\]/)
  if (arr) { try { return JSON.parse(arr[0]) } catch { /* */ } }
  return []
}

function buildHistoryContext(recentAnalyses = []) {
  if (!recentAnalyses.length) return 'Nenhuma análise anterior disponível.'
  const avg = Math.round(recentAnalyses.reduce((s, a) => s + (a.overallScore || 0), 0) / recentAnalyses.length)
  const freq = {}
  for (const a of recentAnalyses) {
    for (const r of (a.results || [])) {
      if (r.score < 60) freq[r.name] = (freq[r.name] || 0) + 1
    }
  }
  const top3 = Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([n, c]) => `${n} (${c}x)`)
  return `${recentAnalyses.length} análises · score médio: ${avg}/100 · áreas fracas: ${top3.join(', ') || 'nenhuma'}`
}

function buildCurrentContext(currentResults = []) {
  const weak = currentResults
    .filter(r => r.score < 60)
    .map(r => `${r.name} (${r.score}/100): ${(r.issues || []).slice(0, 2).join('; ')}`)
    .slice(0, 5)
  return weak.length ? `Problemáticas:\n${weak.map(w => `  - ${w}`).join('\n')}` : 'Código bem avaliado.'
}

export default async function suggestRoute(app) {
  app.post('/suggest', {
    schema: {
      body: {
        type: 'object',
        properties: {
          currentResults: { type: 'array', default: [] },
          recentAnalyses: { type: 'array', default: [] },
        },
      },
    },
  }, async (req, reply) => {
    const { currentResults = [], recentAnalyses = [] } = req.body

    const avail = await checkOllamaAvailability(DEVSTRAL, QWEN)
    if (!avail.ollamaOnline) {
      return { suggestions: [], models: { devstral: false, qwen: false }, circuitBreaker: getCircuitState() }
    }

    const histCtx = buildHistoryContext(recentAnalyses)
    const currCtx = buildCurrentContext(currentResults)
    const systemPrompt = `Você é especialista em análise estática. Sugira NOVAS técnicas de análise de código.
Técnicas já implementadas (NÃO repita): ${CURRENT_TECHNIQUES.join(', ')}.
Responda APENAS com array JSON: [{ name, icon, description, priority, implementationHint, rationale }]`

    try {
      let candidates = []
      const generatorModel = avail.qwenAvailable ? QWEN : DEVSTRAL
      const qwenContent = await queryOllama(generatorModel, [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: `Histórico: ${histCtx}\n\n${currCtx}\n\nSugira 2-3 novas técnicas.` },
      ])
      candidates = extractJSON(qwenContent)

      // Enrich with Devstral if both available
      if (avail.devstralAvailable && avail.qwenAvailable && candidates.length) {
        const enrichedContent = await queryOllama(DEVSTRAL, [
          { role: 'system', content: `Enriqueça estas sugestões de técnicas de análise. Adicione rationale detalhado. Responda APENAS JSON array.` },
          { role: 'user', content: JSON.stringify(candidates) },
        ])
        const enriched = extractJSON(enrichedContent)
        if (enriched.length) candidates = enriched.map(c => ({ ...c, model: 'composed' }))
        else candidates = candidates.map(c => ({ ...c, model: 'qwen3' }))
      } else {
        candidates = candidates.map(c => ({ ...c, model: generatorModel === QWEN ? 'qwen3' : 'devstral' }))
      }

      return {
        suggestions: candidates,
        models: { devstral: avail.devstralAvailable, qwen: avail.qwenAvailable },
        circuitBreaker: getCircuitState(),
      }
    } catch (err) {
      req.log.error(err)
      return reply.code(500).send({ error: 'Advisory pipeline failed', details: err.message })
    }
  })

  app.get('/availability', async () => {
    const avail = await checkOllamaAvailability(DEVSTRAL, QWEN)
    return { ...avail, circuitBreaker: getCircuitState() }
  })
}
