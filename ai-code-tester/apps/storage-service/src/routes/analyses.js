import { createAdapter } from '../adapters/factory.js'
import { randomUUID } from 'crypto'

export default async function analysesRoutes(app) {
  app.post('/analyses', async (req, reply) => {
    const db = await createAdapter()
    const analysis = {
      id: randomUUID(),
      analyzedAt: new Date().toISOString(),
      ...req.body,
    }
    const result = await db.saveAnalysis(analysis)
    return reply.code(201).send(result)
  })

  app.get('/analyses/recent', async (req) => {
    const db = await createAdapter()
    const n = parseInt(req.query.n || '20', 10)
    const analyses = await db.getRecentAnalyses(n)
    return { analyses }
  })

  app.get('/analyses/stats', async () => {
    const db = await createAdapter()
    return db.getStats()
  })

  app.put('/analyses/:id/suggestions', async (req, reply) => {
    const db = await createAdapter()
    const { id } = req.params
    const { suggestions } = req.body
    if (!Array.isArray(suggestions)) return reply.code(400).send({ error: 'suggestions must be an array' })
    return db.updateSuggestions(id, suggestions)
  })
}
