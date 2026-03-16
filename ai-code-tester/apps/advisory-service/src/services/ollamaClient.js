/**
 * Ollama client with simple circuit breaker pattern.
 * States: CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing)
 */

const OLLAMA_URL = process.env.OLLAMA_URL || 'http://localhost:11434'
const FAILURE_THRESHOLD = 3
const RECOVERY_TIMEOUT_MS = 30_000

let failures = 0
let state = 'CLOSED'     // CLOSED | OPEN | HALF_OPEN
let openedAt = 0

function recordFailure() {
  failures++
  if (failures >= FAILURE_THRESHOLD) {
    state = 'OPEN'
    openedAt = Date.now()
  }
}

function recordSuccess() {
  failures = 0
  state = 'CLOSED'
}

function isOpen() {
  if (state === 'OPEN') {
    if (Date.now() - openedAt > RECOVERY_TIMEOUT_MS) {
      state = 'HALF_OPEN'
      return false
    }
    return true
  }
  return false
}

export async function checkOllamaAvailability(devstralModel = 'devstral', qwenModel = 'qwen3-coder') {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), 5000)
    const resp = await fetch(`${OLLAMA_URL}/api/tags`, { signal: controller.signal })
    clearTimeout(timer)
    if (!resp.ok) return { ollamaOnline: false, devstralAvailable: false, qwenAvailable: false }
    const data = await resp.json()
    const names = (data.models || []).map(m => m.name.toLowerCase())
    return {
      ollamaOnline: true,
      devstralAvailable: names.some(n => n.includes(devstralModel.toLowerCase().split(':')[0])),
      qwenAvailable: names.some(n => n.includes(qwenModel.toLowerCase().split(':')[0])),
    }
  } catch {
    return { ollamaOnline: false, devstralAvailable: false, qwenAvailable: false }
  }
}

export async function queryOllama(model, messages, timeoutMs = 60_000) {
  if (isOpen()) throw new Error('Circuit breaker OPEN — Ollama unavailable')

  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const resp = await fetch(`${OLLAMA_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model, messages, stream: false }),
      signal: controller.signal,
    })
    clearTimeout(timer)
    if (!resp.ok) { recordFailure(); throw new Error(`Ollama HTTP ${resp.status}`) }
    const data = await resp.json()
    recordSuccess()
    return data.message?.content || ''
  } catch (err) {
    clearTimeout(timer)
    recordFailure()
    throw err
  }
}

export function getCircuitState() { return { state, failures } }
