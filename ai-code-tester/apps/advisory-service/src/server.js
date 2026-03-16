import Fastify from 'fastify'
import suggestRoute from './routes/suggest.js'

const PORT = parseInt(process.env.PORT || '3002', 10)
const CORS_ORIGIN = process.env.CORS_ORIGIN || '*'

const app = Fastify({ logger: { level: 'info' } })

app.addHook('onRequest', (req, reply, done) => {
  reply.header('Access-Control-Allow-Origin', CORS_ORIGIN)
  reply.header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
  reply.header('Access-Control-Allow-Headers', 'Content-Type')
  if (req.method === 'OPTIONS') { reply.code(204).send(); return }
  done()
})

app.get('/health', async () => ({ status: 'ok', service: 'advisory-service' }))
app.register(suggestRoute, { prefix: '/api/v1' })

const start = async () => {
  try {
    await app.listen({ port: PORT, host: '0.0.0.0' })
    console.log(`advisory-service listening on :${PORT}`)
  } catch (err) {
    app.log.error(err)
    process.exit(1)
  }
}

process.on('SIGTERM', async () => { await app.close(); process.exit(0) })
process.on('SIGINT', async () => { await app.close(); process.exit(0) })

start()
