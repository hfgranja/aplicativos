import { CosmosClient } from '@azure/cosmos'
import { BaseStorageAdapter } from './base.js'

const DB_NAME = process.env.COSMOS_DB || 'ait-db'
const CONTAINER_ANALYSES = 'analyses'
const CONTAINER_INCIDENTS = 'incidents'

export class CosmosDBAdapter extends BaseStorageAdapter {
  constructor() {
    super()
    this.client = new CosmosClient({
      endpoint: process.env.COSMOS_ENDPOINT,
      key: process.env.COSMOS_KEY,
    })
    this.db = this.client.database(DB_NAME)
  }

  get analyses() { return this.db.container(CONTAINER_ANALYSES) }
  get incidents() { return this.db.container(CONTAINER_INCIDENTS) }

  async saveAnalysis(analysis) {
    await this.analyses.items.create({ ...analysis, _partitionKey: 'analysis' })
    return { id: analysis.id }
  }

  async getRecentAnalyses(n = 20) {
    const { resources } = await this.analyses.items.query(
      `SELECT * FROM c WHERE c._partitionKey = 'analysis' ORDER BY c.analyzedAt DESC OFFSET 0 LIMIT ${n}`
    ).fetchAll()
    return resources
  }

  async getStats() {
    const { resources } = await this.analyses.items.query(
      `SELECT c.overallScore, c.results FROM c WHERE c._partitionKey = 'analysis'`
    ).fetchAll()
    if (!resources.length) return { total: 0, avgScore: null, topWeakArea: null }
    const avgScore = Math.round(resources.reduce((s, i) => s + (i.overallScore || 0), 0) / resources.length)
    const freq = {}
    for (const item of resources) {
      for (const r of (item.results || [])) {
        if (r.score < 60) freq[r.name] = (freq[r.name] || 0) + 1
      }
    }
    const topWeakArea = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] || null
    return { total: resources.length, avgScore, topWeakArea }
  }

  async updateSuggestions(id, suggestions) {
    const item = this.analyses.item(id, 'analysis')
    const { resource } = await item.read()
    if (resource) await item.replace({ ...resource, suggestions })
    return { ok: true }
  }

  async getIncidents() {
    const { resources } = await this.incidents.items.query(
      `SELECT * FROM c ORDER BY c.timestamp DESC OFFSET 0 LIMIT 50`
    ).fetchAll()
    return resources
  }

  async saveIncidents(incidents) {
    await Promise.all(incidents.map(inc => this.incidents.items.upsert(inc)))
    return { ok: true }
  }
}
