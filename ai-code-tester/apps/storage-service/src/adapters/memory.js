import { BaseStorageAdapter } from './base.js'
import { randomUUID } from 'crypto'

/**
 * In-memory adapter for local development and testing.
 */
export class MemoryAdapter extends BaseStorageAdapter {
  constructor() {
    super()
    this._analyses = []
    this._incidents = []
  }

  async saveAnalysis(analysis) {
    const id = analysis.id || randomUUID()
    this._analyses.unshift({ ...analysis, id })
    if (this._analyses.length > 1000) this._analyses.length = 1000
    return { id }
  }

  async getRecentAnalyses(n = 20) {
    return this._analyses.slice(0, n)
  }

  async getStats() {
    if (!this._analyses.length) return { total: 0, avgScore: null, topWeakArea: null }
    const avgScore = Math.round(
      this._analyses.reduce((s, a) => s + (a.overallScore || 0), 0) / this._analyses.length
    )
    const freq = {}
    for (const a of this._analyses) {
      for (const r of (a.results || [])) {
        if (r.score < 60) freq[r.name] = (freq[r.name] || 0) + 1
      }
    }
    const topWeakArea = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] || null
    return { total: this._analyses.length, avgScore, topWeakArea }
  }

  async updateSuggestions(id, suggestions) {
    const item = this._analyses.find(a => a.id === id)
    if (item) item.suggestions = suggestions
    return { ok: true }
  }

  async getIncidents() {
    return this._incidents.slice(0, 50)
  }

  async saveIncidents(incidents) {
    this._incidents = incidents
    return { ok: true }
  }
}
