import Fastify from 'fastify'
import analysesRoutes from './routes/analyses.js'
import incidentsRoutes from './routes/incidents.js'

const PORT = parseInt(process.env.PORT || '3004', 10)
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*'

const app = Fastify({ logger: { level: 'info' } })

app.addHook('onRequest', (req, reply, done) => {
  reply.header('Access-Control-Allow-Origin', CORS_ORIGIN)
  reply.header('Access-Control-Allow-Methods', 'GET,POST,PUT,OPTIONS')
  reply.header('Access-Control-Allow-Headers', 'Content-Type')
  if (req.method === 'OPTIONS') { reply.code(204).send(); return }
  done()
})

app.get('/health', async () => ({
  status: 'ok',
  service: 'storage-service',
  provider: process.env.CLOUD_PROVIDER || 'local',
}))

app.register(analysesRoutes, { prefix: '/api/v1' })
app.register(incidentsRoutes, { prefix: '/api/v1' })

const start = async () => {
  try {
    await app.listen({ port: PORT, host: '0.0.0.0' })
    console.log(`storage-service [${process.env.CLOUD_PROVIDER || 'local'}] listening on :${PORT}`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

process.on('SIGTERM', async () => { await app.close(); process.exit(0) })
process.on('SIGINT', async () => { await app.close(); process.exit(0) })

start()
