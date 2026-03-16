import Fastify from 'fastify'
import { checkAll } from './health.js'

const PORT = parseInt(process.env.PORT || '3005', 10)

const app = Fastify({ logger: { level: 'warn' } })

// Cached health state — refreshed every 10s
let lastHealth = null
let lastChecked = 0
const CACHE_TTL_MS = 10_000

async function getHealth(force = false) {
  const now = Date.now()
  if (!force && lastHealth && now - lastChecked < CACHE_TTL_MS) return lastHealth
  lastHealth = await checkAll()
  lastChecked = now
  return lastHealth
}

app.get('/health', async (req, reply) => {
  const health = await getHealth()
  const code = health.status === 'healthy' ? 200 : health.status === 'critical' ? 503 : 200
  return reply.code(code).send(health)
})

app.get('/ready', async (req, reply) => {
  const health = await getHealth()
  if (health.status === 'critical') {
    return reply.code(503).send({ ready: false, ...health })
  }
  return { ready: true, ...health }
})

// Force refresh endpoint
app.post('/health/refresh', async () => {
  return getHealth(true)
})

const start = async () => {
  try {
    await app.listen({ port: PORT, host: '0.0.0.0' })
    console.log(`cell-health [${process.env.CELL_ID || 'local'}] listening on :${PORT}`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

process.on('SIGTERM', async () => { await app.close(); process.exit(0) })
process.on('SIGINT', async () => { await app.close(); process.exit(0) })

start()
