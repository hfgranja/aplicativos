import { createAdapter } from '../adapters/factory.js'

const INCIDENT_FEED_URL = process.env.INCIDENT_FEED_URL ||
  'https://status.npmjs.org/api/v2/incidents.json'

export default async function incidentsRoutes(app) {
  app.get('/incidents', async () => {
    const db = await createAdapter()
    const incidents = await db.getIncidents()
    return { incidents }
  })

  app.post('/incidents/refresh', async (req, reply) => {
    const db = await createAdapter()
    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 8000)
      const resp = await fetch(INCIDENT_FEED_URL, { signal: controller.signal })
      clearTimeout(timer)
      if (!resp.ok) return reply.code(502).send({ error: `Feed responded ${resp.status}` })
      const data = await resp.json()
      const incidents = (data.incidents || []).slice(0, 20).map(inc => ({
        id: inc.id,
        name: inc.name,
        status: inc.status,
        impact: inc.impact,
        updatedAt: inc.updated_at,
        url: inc.shortlink,
      }))
      await db.saveIncidents(incidents)
      return { count: incidents.length, source: INCIDENT_FEED_URL }
    } catch (err) {
      return reply.code(500).send({ error: err.message })
    }
  })
}
