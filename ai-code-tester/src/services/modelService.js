/**
 * modelService — Motor de sugestão de técnicas via composição Devstral 2 + Qwen3-coder-next
 *
 * Arquitetura de composição:
 *   1. Qwen3-coder-next (gerador): analisa histórico + análise atual → candidatos JSON
 *   2. Devstral 2 (crítico/enriquecedor): valida e enriquece cada candidato com detalhes AST
 *
 * Fallback: se apenas 1 modelo disponível → usa só ele
 * Fallback: se Ollama offline → retorna [] silenciosamente
 *
 * Requisito do usuário:
 *   OLLAMA_ORIGINS="http://localhost:5173" ollama serve
 *   ollama pull qwen3-coder
 *   ollama pull devstral
 */

const CURRENT_TECHNIQUES = [
  'Análise Estática', 'Complexidade Ciclomática', 'Duplicação de Código',
  'Segurança', 'Segurança de Tipos', 'Risco de Dependências',
  'Cobertura de Testes', 'Qualidade de Documentação', 'Boas Práticas',
  'Anti-padrões de Performance', 'Tratamento de Erros',
  'Contratos de API', 'Testes por Mutação',
]

/**
 * Verifica quais modelos estão disponíveis no Ollama local.
 * @returns {{ ollamaOnline: boolean, devstralAvailable: boolean, qwenAvailable: boolean }}
 */
export async function checkAvailability(ollamaUrl = 'http://localhost:11434', devstralModel = 'devstral', qwenModel = 'qwen3-coder') {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    const resp = await fetch(`${ollamaUrl}/api/tags`, { signal: controller.signal })
    clearTimeout(timer)
    if (!resp.ok) return { ollamaOnline: false, devstralAvailable: false, qwenAvailable: false }

    const data = await resp.json()
    const names = (data.models || []).map(m => m.name.toLowerCase())
    const devstralAvailable = names.some(n => n.includes(devstralModel.toLowerCase().split(':')[0]))
    const qwenAvailable = names.some(n => n.includes(qwenModel.toLowerCase().split(':')[0]))
    return { ollamaOnline: true, devstralAvailable, qwenAvailable }
  } catch {
    return { ollamaOnline: false, devstralAvailable: false, qwenAvailable: false }
  }
}

/**
 * Chama um modelo no Ollama e retorna o conteúdo da resposta.
 */
async function queryOllama(ollamaUrl, model, messages, timeoutMs = 30000) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const resp = await fetch(`${ollamaUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages, stream: false }),
      signal: controller.signal,
    })
    clearTimeout(timer)
    if (!resp.ok) throw new Error(`Ollama HTTP ${resp.status}`)
    const data = await resp.json()
    return data.message?.content || ''
  } catch (err) {
    clearTimeout(timer)
    throw err
  }
}

/**
 * Extrai array JSON de uma resposta de texto do modelo.
 */
function extractJSON(text) {
  const fenced = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  if (fenced) {
    try { return JSON.parse(fenced[1].trim()) } catch { /* continue */ }
  }
  const arrMatch = text.match(/\[[\s\S]*\]/)
  if (arrMatch) {
    try { return JSON.parse(arrMatch[0]) } catch { /* continue */ }
  }
  return []
}

/**
 * Constrói um resumo das análises recentes para contexto do modelo.
 */
function buildHistoryContext(recentAnalyses) {
  if (!recentAnalyses.length) return 'Nenhuma análise anterior disponível.'
  const avgScore = Math.round(recentAnalyses.reduce((s, a) => s + a.overallScore, 0) / recentAnalyses.length)

  // Conta frequência de issues por técnica
  const issueFreq = {}
  for (const analysis of recentAnalyses) {
    for (const result of (analysis.results || [])) {
      if (result.score < 60) {
        issueFreq[result.name] = (issueFreq[result.name] || 0) + 1
      }
    }
  }
  const top3Weak = Object.entries(issueFreq)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, count]) => `${name} (${count}x)`)

  return `${recentAnalyses.length} análises anteriores · score médio: ${avgScore}/100 · áreas mais fracas: ${top3Weak.join(', ') || 'nenhuma'}`
}

/**
 * Constrói o resumo da análise atual.
 */
function buildCurrentContext(currentResults) {
  const weak = currentResults
    .filter(r => r.score < 60)
    .map(r => `${r.name} (${r.score}/100): ${r.issues.slice(0, 2).join('; ')}`)
    .slice(0, 5)
  return weak.length
    ? `Áreas problemáticas desta análise:\n${weak.map(w => `  - ${w}`).join('\n')}`
    : 'Código bem avaliado em todas as técnicas.'
}

/**
 * Estágio 1: Qwen3-coder-next gera candidatos de novas técnicas.
 */
async function stageGenerate(ollamaUrl, qwenModel, historyCtx, currentCtx, onStatus) {
  onStatus('querying-qwen')
  const systemPrompt = `Você é um especialista em qualidade de código e ferramentas de análise estática.
Analise dados de uso de uma ferramenta de validação de código e sugira NOVAS técnicas de análise ainda não implementadas.

Técnicas JÁ implementadas (NÃO repita):
${CURRENT_TECHNIQUES.map((t, i) => `${i + 1}. ${t}`).join('\n')}

Responda APENAS com um array JSON válido, sem texto adicional.
Cada item deve ter: name, icon (emoji), description, priority (high/medium/low), implementationHint`

  const userPrompt = `Dados históricos: ${historyCtx}

${currentCtx}

Sugira 2 ou 3 novas técnicas de análise que agregariam valor com base nos problemas observados.
Foque em técnicas que podem ser implementadas via análise estática de AST no browser.`

  const content = await queryOllama(ollamaUrl, qwenModel, [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ])

  return extractJSON(content)
}

/**
 * Estágio 2: Devstral 2 enriquece e valida os candidatos.
 */
async function stageEnrich(ollamaUrl, devstralModel, candidates, historyCtx, currentCtx, onStatus) {
  onStatus('querying-devstral')
  if (!candidates.length) return []

  const systemPrompt = `Você é um arquiteto de ferramentas de análise de código AST.
Avalie estas sugestões de técnicas de análise de código e enriqueça-as.

Para cada técnica:
1. Valide se é relevante aos problemas observados
2. Adicione um campo "rationale" explicando por que é necessária com base nos dados
3. Melhore "implementationHint" com exemplos concretos de nós AST a inspecionar

Técnicas já existentes (não repita): ${CURRENT_TECHNIQUES.join(', ')}

Responda APENAS com o array JSON enriquecido, sem texto adicional.`

  const userPrompt = `Dados históricos: ${historyCtx}
${currentCtx}

Candidatos para enriquecer:
${JSON.stringify(candidates, null, 2)}`

  const content = await queryOllama(ollamaUrl, devstralModel, [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userPrompt },
  ])

  const enriched = extractJSON(content)
  // Se falhou, retorna os originais com rationale padrão
  if (!enriched.length) {
    return candidates.map(c => ({ ...c, rationale: 'Sugerido com base nos padrões detectados.', model: 'qwen3' }))
  }
  return enriched.map(c => ({ ...c, model: 'composed' }))
}

/**
 * Pipeline principal de sugestão de técnicas.
 * Compõe Qwen3 (gerador) + Devstral (crítico).
 *
 * @param {Array} recentAnalyses - últimas N análises do IndexedDB
 * @param {Array} currentResults - resultados da análise atual (13 itens)
 * @param {Object} config - { ollamaUrl, devstralModel, qwenModel, timeoutMs }
 * @param {Function} onStatus - callback de status: (status: string) => void
 * @returns {Promise<Array<Suggestion>>}
 */
export async function suggestTechniques(recentAnalyses, currentResults, config = {}, onStatus = () => {}) {
  const {
    ollamaUrl = 'http://localhost:11434',
    devstralModel = 'devstral',
    qwenModel = 'qwen3-coder',
  } = config

  const historyCtx = buildHistoryContext(recentAnalyses)
  const currentCtx = buildCurrentContext(currentResults)

  // Verifica disponibilidade
  const avail = await checkAvailability(ollamaUrl, devstralModel, qwenModel)
  if (!avail.ollamaOnline) return []

  try {
    // Se só Devstral disponível: usa ele como único modelo
    if (!avail.qwenAvailable && avail.devstralAvailable) {
      onStatus('querying-devstral')
      const candidates = await stageGenerate(ollamaUrl, devstralModel, historyCtx, currentCtx, () => {})
      return candidates.map(c => ({ ...c, model: 'devstral' }))
    }

    // Se só Qwen disponível: usa ele como único modelo
    if (avail.qwenAvailable && !avail.devstralAvailable) {
      const candidates = await stageGenerate(ollamaUrl, qwenModel, historyCtx, currentCtx, onStatus)
      return candidates.map(c => ({ ...c, model: 'qwen3' }))
    }

    // Composição completa: Qwen3 → Devstral
    const candidates = await stageGenerate(ollamaUrl, qwenModel, historyCtx, currentCtx, onStatus)
    if (!candidates.length) return []
    const enriched = await stageEnrich(ollamaUrl, devstralModel, candidates, historyCtx, currentCtx, onStatus)
    return enriched
  } catch {
    return []
  }
}
