import { runAllAnalyzers, calcOverallScore } from '@ait/analyzers'
import { randomUUID } from 'crypto'

export default async function analyzeRoute(app) {
  app.post('/analyze', {
    schema: {
      body: {
        type: 'object',
        required: ['code'],
        properties: {
          code: { type: 'string' },
          packageJson: { type: 'string', default: '' },
        },
      },
    },
  }, async (req, reply) => {
    const { code, packageJson = '' } = req.body
    if (!code || !code.trim()) {
      return reply.code(400).send({ error: 'code is required' })
    }

    try {
      const results = await runAllAnalyzers(code, packageJson)
      const overallScore = calcOverallScore(results)
      return {
        analysisId: randomUUID(),
        results,
        overallScore,
        analyzedAt: new Date().toISOString(),
      }
    } catch (err) {
      req.log.error(err)
      return reply.code(500).send({ error: 'Analysis failed', details: err.message })
    }
  })
}
