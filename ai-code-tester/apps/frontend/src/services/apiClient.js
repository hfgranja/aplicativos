/**
 * apiClient — HTTP client for cell services
 *
 * In local mode (VITE_LOCAL_MODE=true), falls back to in-browser implementations.
 * In cell mode, routes requests to the cell API.
 */

const CELL_API = import.meta.env.VITE_CELL_API_URL || ''
const LOCAL_MODE = import.meta.env.VITE_LOCAL_MODE === 'true' || !CELL_API

/**
 * POST /api/v1/analyze — analysis-service (port 3001 in cell)
 */
export async function analyzeCode(code, packageJson = '') {
  if (LOCAL_MODE) {
    // In-browser fallback: import orchestrator directly
    const { runAllAnalyzers, calcOverallScore } = await import('../analyzers/orchestrator.js')
    const results = await runAllAnalyzers(code, packageJson)
    const overallScore = calcOverallScore(results)
    return { results, overallScore }
  }
  const resp = await fetch(`${CELL_API}/api/v1/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, packageJson }),
  })
  if (!resp.ok) throw new Error(`analysis-service error: ${resp.status}`)
  return resp.json()
}

/**
 * POST /api/v1/suggest — advisory-service (port 3002 in cell)
 */
export async function suggestTechniquesRemote(currentResults, recentAnalyses) {
  if (LOCAL_MODE) {
    const { suggestTechniques } = await import('./modelService.js')
    return suggestTechniques(recentAnalyses, currentResults)
  }
  const resp = await fetch(`${CELL_API}/api/v1/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ currentResults, recentAnalyses }),
  })
  if (!resp.ok) throw new Error(`advisory-service error: ${resp.status}`)
  const data = await resp.json()
  return data.suggestions
}

/**
 * POST /api/v1/git/connect — git-proxy (port 3003 in cell)
 */
export async function gitConnect(config) {
  if (LOCAL_MODE) {
    const { GitService } = await import('./gitService.js')
    const svc = new GitService(config)
    const userInfo = await svc.testConnection()
    const { owner, repo, branch } = config
    const repoInfo = await svc.getRepoInfo(owner, repo)
    const allFiles = await svc.getFileTree(owner, repo, branch)
    return { userInfo, repoInfo, files: allFiles }
  }
  const resp = await fetch(`${CELL_API}/api/v1/git/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  })
  if (!resp.ok) throw new Error(`git-proxy error: ${resp.status}`)
  return resp.json()
}

/**
 * POST /api/v1/git/files — git-proxy
 */
export async function gitLoadFiles(config, paths, onProgress) {
  if (LOCAL_MODE) {
    const { GitService } = await import('./gitService.js')
    const svc = new GitService(config)
    const code = await svc.loadSelectedFiles(config.owner, config.repo, config.branch, paths, onProgress)
    return { code }
  }
  const resp = await fetch(`${CELL_API}/api/v1/git/files`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...config, paths }),
  })
  if (!resp.ok) throw new Error(`git-proxy error: ${resp.status}`)
  return resp.json()
}

/**
 * POST /api/v1/analyses — storage-service
 */
export async function saveAnalysisRemote(analysis) {
  if (LOCAL_MODE) {
    const { saveAnalysis } = await import('./trainingDataService.js')
    return saveAnalysis(analysis)
  }
  const resp = await fetch(`${CELL_API}/api/v1/analyses`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(analysis),
  })
  if (!resp.ok) throw new Error(`storage-service error: ${resp.status}`)
  return resp.json()
}

/**
 * GET /api/v1/analyses/recent — storage-service
 */
export async function getRecentAnalysesRemote(n = 20) {
  if (LOCAL_MODE) {
    const { getRecentAnalyses } = await import('./trainingDataService.js')
    return getRecentAnalyses(n)
  }
  const resp = await fetch(`${CELL_API}/api/v1/analyses/recent?n=${n}`)
  if (!resp.ok) throw new Error(`storage-service error: ${resp.status}`)
  const data = await resp.json()
  return data.analyses
}

/**
 * GET /api/v1/analyses/stats — storage-service
 */
export async function getStatsRemote() {
  if (LOCAL_MODE) {
    const { getStats } = await import('./trainingDataService.js')
    return getStats()
  }
  const resp = await fetch(`${CELL_API}/api/v1/analyses/stats`)
  if (!resp.ok) throw new Error(`storage-service error: ${resp.status}`)
  return resp.json()
}

/**
 * GET /health — cell-health (port 3005)
 */
export async function getCellHealth() {
  const url = CELL_API ? `${CELL_API}/health` : '/health'
  try {
    const resp = await fetch(url)
    if (!resp.ok) return null
    return resp.json()
  } catch {
    return null
  }
}

export const isLocalMode = LOCAL_MODE
