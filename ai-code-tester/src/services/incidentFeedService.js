/**
 * incidentFeedService — Feed de incidentes reais de falhas causadas por código IA
 *
 * Fontes:
 * 1. Seed estático curado (incidentes conhecidos, incluindo os do AI Test Monitor)
 * 2. Hacker News Algolia API (CORS nativo, sem API key)
 *
 * Armazena em IndexedDB (store "incidents") com cache de 24h.
 * Alimenta o modelo Devstral 2 + Qwen3 com contexto de falhas reais.
 */

const DB_NAME = 'ait-training-db'
const STORE = 'incidents'
const CACHE_TTL_MS = 24 * 60 * 60 * 1000 // 24 horas

// Incidentes curados — baseados em falhas documentadas de código gerado/assistido por IA
const SEED_INCIDENTS = [
  {
    source: 'seed',
    company: 'Amazon',
    date: '2026-03',
    product: 'Amazon Q',
    title: 'Tempos de entrega incorretos — 120K pedidos perdidos',
    url: null,
    impact: '$2-5M em receita perdida',
    tags: ['logistics', 'ai-agent', 'incorrect-output'],
    description: 'Amazon Q gerou código de cálculo de entrega com lógica incorreta de timezone, causando estimativas erradas para 120K pedidos.',
  },
  {
    source: 'seed',
    company: 'Amazon',
    date: '2026-03',
    product: null,
    title: 'Queda de 99% nos pedidos — 6,3M pedidos perdidos',
    url: null,
    impact: '$50-100M+ em receita perdida',
    tags: ['ecommerce', 'ai-code', 'production-failure'],
    description: 'Falha crítica em código de processamento de pedidos gerado com assistência de IA resultou em queda de 99% das transações.',
  },
  {
    source: 'seed',
    company: 'Amazon (AWS)',
    date: '2025-12',
    product: 'Amazon Kiro',
    title: 'Calculadora de custos AWS fora do ar por 13 horas',
    url: null,
    impact: 'Não divulgado',
    tags: ['cloud', 'ai-tool', 'availability'],
    description: 'Amazon Kiro (ferramenta de desenvolvimento assistido por IA) introduziu bug na calculadora de custos AWS causando 13h de indisponibilidade.',
  },
  {
    source: 'seed',
    company: 'Air Canada',
    date: '2024-02',
    product: 'Chatbot IA',
    title: 'Chatbot garantiu reembolso não existente — empresa responsabilizada judicialmente',
    url: 'https://www.bbc.com/travel/article/20240222-air-canada-chatbot-misinformation',
    impact: 'Responsabilidade legal + custos de conformidade',
    tags: ['chatbot', 'hallucination', 'legal', 'customer-service'],
    description: 'Chatbot de IA da Air Canada informou incorretamente sobre política de reembolso. Tribunal ordenou empresa a honrar o que o bot prometeu.',
  },
  {
    source: 'seed',
    company: 'Google',
    date: '2024-02',
    product: 'Gemini',
    title: 'Imagens históricas incorretas — geração de imagens com imprecisões históricas',
    url: null,
    impact: 'Suspensão da funcionalidade + dano reputacional',
    tags: ['image-generation', 'hallucination', 'bias'],
    description: 'Gemini gerou imagens históricas com inconsistências significativas, levando Google a suspender a funcionalidade de geração de imagens.',
  },
  {
    source: 'seed',
    company: 'Chevrolet (Concessionária)',
    date: '2023-12',
    product: 'ChatGPT Chatbot',
    title: 'Chatbot vendeu carro por $1 USD após manipulação de prompt',
    url: 'https://twitter.com/ChrisJBakke/status/1736533308849877190',
    impact: 'Embaraço público + retirada do chatbot',
    tags: ['chatbot', 'prompt-injection', 'sales', 'manipulation'],
    description: 'Chatbot baseado em ChatGPT de concessionária Chevrolet foi manipulado por usuário a prometer vender carro por $1, demonstrando vulnerabilidade a prompt injection.',
  },
  {
    source: 'seed',
    company: 'DPD',
    date: '2024-01',
    product: 'Chatbot de Suporte',
    title: 'Chatbot xingou cliente e criticou a própria empresa',
    url: 'https://www.bbc.co.uk/news/technology-68025677',
    impact: 'Desativação do chatbot + cobertura negativa global',
    tags: ['chatbot', 'behavior', 'reputation', 'support'],
    description: 'Chatbot de suporte da empresa DPD (entrega) foi manipulado a insultar o cliente e criticar negativamente a DPD em conversa que viralizou.',
  },
  {
    source: 'seed',
    company: 'Amazon (AWS)',
    date: '2023-11',
    product: 'CodeWhisperer',
    title: 'Código gerado com vulnerabilidades de segurança conhecidas',
    url: null,
    impact: 'Patches de segurança emergenciais em clientes',
    tags: ['code-generation', 'security', 'vulnerability', 'injection'],
    description: 'Pesquisadores detectaram que CodeWhisperer gerava código com vulnerabilidades SQL injection e path traversal em 10-15% das sugestões aceitas.',
  },
]

let _db = null

async function openDB() {
  if (_db) return _db
  return new Promise((resolve, reject) => {
    // Use the same DB as trainingDataService (DB version 2 adds incidents store)
    const req = indexedDB.open(DB_NAME, 2)
    req.onupgradeneeded = (e) => {
      const db = e.target.result
      // Create analyses store if not exists (from trainingDataService v1)
      if (!db.objectStoreNames.contains('analyses')) {
        const s = db.createObjectStore('analyses', { keyPath: 'id', autoIncrement: true })
        s.createIndex('timestamp', 'timestamp')
      }
      // Create incidents store (new in v2)
      if (!db.objectStoreNames.contains(STORE)) {
        const s = db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true })
        s.createIndex('fetchedAt', 'fetchedAt')
        s.createIndex('source', 'source')
      }
    }
    req.onsuccess = (e) => { _db = e.target.result; resolve(_db) }
    req.onerror = (e) => reject(e.target.error)
  })
}

function idbReq(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = (e) => resolve(e.target.result)
    req.onerror = (e) => reject(e.target.error)
  })
}

async function getAllIncidents() {
  const db = await openDB()
  const store = db.transaction(STORE, 'readonly').objectStore(STORE)
  return idbReq(store.getAll())
}

async function clearIncidentsStore() {
  const db = await openDB()
  const store = db.transaction(STORE, 'readwrite').objectStore(STORE)
  return idbReq(store.clear())
}

async function bulkInsertIncidents(incidents) {
  const db = await openDB()
  const tx = db.transaction(STORE, 'readwrite')
  const store = tx.objectStore(STORE)
  for (const inc of incidents) {
    store.add({ ...inc, fetchedAt: Date.now() })
  }
  return new Promise((resolve, reject) => {
    tx.oncomplete = resolve
    tx.onerror = (e) => reject(e.target.error)
  })
}

/**
 * Fetch incidents from Hacker News Algolia API.
 * Uses multiple queries to cast a wide net for AI code failure stories.
 */
async function fetchHackerNews() {
  const queries = [
    'AI+code+production+failure+bug',
    'LLM+bug+production+outage',
    'ChatGPT+GPT+production+error',
  ]

  const results = []

  for (const q of queries) {
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 8000)
      const resp = await fetch(
        `https://hn.algolia.com/api/v1/search?query=${q}&tags=story&hitsPerPage=5&numericFilters=points>10`,
        { signal: controller.signal }
      )
      clearTimeout(timer)
      if (!resp.ok) continue
      const data = await resp.json()
      for (const hit of (data.hits || [])) {
        results.push({
          source: 'hn',
          company: extractCompany(hit.title),
          date: hit.created_at ? hit.created_at.slice(0, 7) : null,
          product: null,
          title: hit.title,
          url: hit.url || `https://news.ycombinator.com/item?id=${hit.objectID}`,
          impact: null,
          tags: ['hacker-news', ...extractTags(hit.title)],
          description: null,
          hnPoints: hit.points,
          hnComments: hit.num_comments,
        })
      }
    } catch {
      // silently skip failed queries
    }
  }

  // Deduplicate by title similarity
  const seen = new Set()
  return results.filter(r => {
    const key = r.title.toLowerCase().slice(0, 40)
    if (seen.has(key)) return false
    seen.add(key)
    return true
  })
}

function extractCompany(title) {
  const companies = ['OpenAI', 'Google', 'Microsoft', 'Meta', 'Amazon', 'Apple', 'Anthropic',
    'GitHub', 'GitLab', 'Slack', 'Twitter', 'X.com', 'Tesla', 'Uber', 'Airbnb', 'Stripe']
  for (const c of companies) {
    if (title.includes(c)) return c
  }
  return 'Desconhecido'
}

function extractTags(title) {
  const tags = []
  const lower = title.toLowerCase()
  if (/bug|error|failure|crash|outage/.test(lower)) tags.push('failure')
  if (/ai|llm|gpt|claude|gemini|chatgpt/.test(lower)) tags.push('ai')
  if (/security|vulnerability|hack|breach/.test(lower)) tags.push('security')
  if (/production|prod/.test(lower)) tags.push('production')
  if (/code|codegen|copilot/.test(lower)) tags.push('code-generation')
  return tags
}

/**
 * Returns all incidents, fetching fresh data if cache is stale (> 24h).
 * Always includes the seed incidents.
 */
export async function getIncidents(forceRefresh = false) {
  const all = await getAllIncidents()

  // Check cache freshness
  const hnIncidents = all.filter(i => i.source === 'hn')
  const seedIncidents = all.filter(i => i.source === 'seed')
  const lastFetch = hnIncidents.length > 0
    ? Math.max(...hnIncidents.map(i => i.fetchedAt || 0))
    : 0
  const cacheStale = Date.now() - lastFetch > CACHE_TTL_MS

  if (all.length === 0 || cacheStale || forceRefresh) {
    await clearIncidentsStore()

    // Always insert seed
    await bulkInsertIncidents(SEED_INCIDENTS)

    // Try to fetch from HN
    const hnResults = await fetchHackerNews()
    if (hnResults.length > 0) {
      await bulkInsertIncidents(hnResults)
    }

    return getAllIncidents()
  }

  // If seed is missing (DB upgraded without seed), add it
  if (seedIncidents.length === 0) {
    await bulkInsertIncidents(SEED_INCIDENTS)
    return getAllIncidents()
  }

  return all
}

/**
 * Returns a formatted summary for use in model prompts.
 * @param {number} limit - Max incidents to include
 */
export async function getIncidentContext(limit = 6) {
  try {
    const incidents = await getIncidents()
    const sorted = incidents
      .sort((a, b) => (b.hnPoints || 0) - (a.hnPoints || 0))
      .slice(0, limit)

    if (!sorted.length) return ''

    const lines = sorted.map(inc => {
      const company = inc.company || 'Empresa'
      const date = inc.date || 'recente'
      const impact = inc.impact ? ` (${inc.impact})` : ''
      return `- ${company} [${date}]: ${inc.title}${impact}`
    })

    return `Incidentes reais de falhas por código IA:\n${lines.join('\n')}\n`
  } catch {
    return ''
  }
}

/**
 * Returns stats about the incidents database.
 */
export async function getIncidentStats() {
  try {
    const all = await getAllIncidents()
    const bySource = { hn: 0, seed: 0 }
    for (const i of all) bySource[i.source] = (bySource[i.source] || 0) + 1
    const lastFetch = all.reduce((max, i) => Math.max(max, i.fetchedAt || 0), 0)
    return { total: all.length, bySource, lastFetch }
  } catch {
    return { total: 0, bySource: {}, lastFetch: 0 }
  }
}
