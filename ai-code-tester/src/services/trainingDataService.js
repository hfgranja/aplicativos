/**
 * trainingDataService — Persistência de dados de análise em IndexedDB
 * Acumula cada análise realizada para alimentar o motor de sugestões.
 * Zero dependências externas — usa IndexedDB nativo do browser.
 */

const DB_NAME = 'ait-training-db'
const DB_VERSION = 1
const STORE = 'analyses'

let _db = null

function openDB() {
  if (_db) return Promise.resolve(_db)
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = (e) => {
      const db = e.target.result
      if (!db.objectStoreNames.contains(STORE)) {
        const store = db.createObjectStore(STORE, { keyPath: 'id', autoIncrement: true })
        store.createIndex('timestamp', 'timestamp', { unique: false })
      }
    }
    req.onsuccess = (e) => {
      _db = e.target.result
      resolve(_db)
    }
    req.onerror = (e) => reject(e.target.error)
  })
}

function tx(mode = 'readonly') {
  return openDB().then(db => db.transaction(STORE, mode).objectStore(STORE))
}

function idbRequest(req) {
  return new Promise((resolve, reject) => {
    req.onsuccess = (e) => resolve(e.target.result)
    req.onerror = (e) => reject(e.target.error)
  })
}

function detectLanguage(code) {
  if (/import React|\.jsx|\.tsx|useState|useEffect/.test(code)) return 'React/JSX'
  if (/\bdef \w+\(|\bimport \w+\b|:\s*$/.test(code)) return 'Python'
  if (/public class|System\.out\.|\.java/.test(code)) return 'Java'
  if (/\bfunc \w+\(|\bpackage main\b/.test(code)) return 'Go'
  if (/\bfn \w+\(|\blet mut\b/.test(code)) return 'Rust'
  return 'JavaScript'
}

/**
 * Salva o resultado de uma análise no IndexedDB.
 * @returns {Promise<number>} ID do registro inserido
 */
export async function saveAnalysis({ code, results, overallScore }) {
  const topIssues = results
    .filter(r => r.score < 50)
    .flatMap(r => r.issues.slice(0, 2))
    .slice(0, 8)

  const record = {
    timestamp: Date.now(),
    codeSnippet: (code || '').slice(0, 500),
    codeLength: (code || '').length,
    language: detectLanguage(code || ''),
    overallScore,
    results: results.map(r => ({
      id: r.id,
      name: r.name,
      score: r.score,
      issues: r.issues.slice(0, 5),
      suggestions: r.suggestions.slice(0, 3),
    })),
    topIssues,
    suggestionsGiven: null,
  }

  const store = await tx('readwrite')
  const id = await idbRequest(store.add(record))
  return id
}

/**
 * Atualiza as sugestões geradas pelo modelo para um registro existente.
 */
export async function updateSuggestions(id, suggestions) {
  try {
    const store = await tx('readwrite')
    const existing = await idbRequest(store.get(id))
    if (existing) {
      existing.suggestionsGiven = suggestions
      await idbRequest(store.put(existing))
    }
  } catch {
    // silencioso — não é crítico
  }
}

/**
 * Retorna as N análises mais recentes para contexto do modelo.
 */
export async function getRecentAnalyses(n = 20) {
  const store = await tx('readonly')
  const all = await idbRequest(store.getAll())
  return all
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, n)
}

/**
 * Retorna estatísticas do banco de dados de treinamento.
 */
export async function getStats() {
  const store = await tx('readonly')
  const all = await idbRequest(store.getAll())
  if (!all.length) return { total: 0, avgScore: null, topWeakArea: null }

  const avgScore = Math.round(all.reduce((s, r) => s + r.overallScore, 0) / all.length)

  // Técnica com menor score médio acumulado
  const techScores = {}
  for (const analysis of all) {
    for (const result of (analysis.results || [])) {
      if (!techScores[result.name]) techScores[result.name] = []
      techScores[result.name].push(result.score)
    }
  }
  let topWeakArea = null
  let lowestAvg = Infinity
  for (const [name, scores] of Object.entries(techScores)) {
    const avg = scores.reduce((s, v) => s + v, 0) / scores.length
    if (avg < lowestAvg) { lowestAvg = avg; topWeakArea = name }
  }

  return { total: all.length, avgScore, topWeakArea }
}

/**
 * Exporta todos os registros como JSONL para fine-tuning offline.
 * Cada linha é um JSON com o par input/output do modelo.
 */
export async function exportAsJSONL() {
  const store = await tx('readonly')
  const all = await idbRequest(store.getAll())
  return all
    .sort((a, b) => a.timestamp - b.timestamp)
    .map(record => {
      const entry = {
        timestamp: new Date(record.timestamp).toISOString(),
        language: record.language,
        codeLength: record.codeLength,
        overallScore: record.overallScore,
        topIssues: record.topIssues,
        analysisSummary: record.results?.map(r => ({
          technique: r.name,
          score: r.score,
          issues: r.issues,
        })),
        suggestionsGenerated: record.suggestionsGiven,
      }
      return JSON.stringify(entry)
    })
    .join('\n')
}

/**
 * Apaga todos os registros do banco.
 */
export async function clearAll() {
  const store = await tx('readwrite')
  await idbRequest(store.clear())
  _db = null
}
