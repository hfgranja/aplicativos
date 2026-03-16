/**
 * Aggregates health of all services in the cell.
 * Uses simple fetch with short timeout for each service.
 */

const SERVICES = {
  analysis: process.env.ANALYSIS_URL || 'http://analysis-service:3001',
  advisory: process.env.ADVISORY_URL || 'http://advisory-service:3002',
  'git-proxy': process.env.GIT_PROXY_URL || 'http://git-proxy:3003',
  storage: process.env.STORAGE_URL || 'http://storage-service:3004',
}

const TIMEOUT_MS = 3000

async function pingService(url) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS)
  try {
    const resp = await fetch(`${url}/health`, { signal: controller.signal })
    clearTimeout(timer)
    return resp.ok ? 'up' : 'degraded'
  } catch {
    clearTimeout(timer)
    return 'down'
  }
}

export async function checkAll() {
  const results = await Promise.all(
    Object.entries(SERVICES).map(async ([name, url]) => [name, await pingService(url)])
  )
  const services = Object.fromEntries(results)
  const statuses = Object.values(services)
  const downCount = statuses.filter(s => s === 'down').length
  const degradedCount = statuses.filter(s => s === 'degraded').length

  let status
  if (downCount === 0 && degradedCount === 0) status = 'healthy'
  else if (downCount > statuses.length / 2) status = 'critical'
  else status = 'degraded'

  return {
    status,
    cell: process.env.CELL_ID || 'local',
    services,
    checkedAt: new Date().toISOString(),
  }
}
