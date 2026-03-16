import { Firestore } from '@google-cloud/firestore'
import { BaseStorageAdapter } from './base.js'

export class FirestoreAdapter extends BaseStorageAdapter {
  constructor() {
    super()
    this.db = new Firestore({ projectId: process.env.GOOGLE_PROJECT_ID })
    this.analyses = this.db.collection('analyses')
    this.incidents = this.db.collection('incidents')
  }

  async saveAnalysis(analysis) {
    await this.analyses.doc(analysis.id).set(analysis)
    return { id: analysis.id }
  }

  async getRecentAnalyses(n = 20) {
    const snap = await this.analyses
      .orderBy('analyzedAt', 'desc')
      .limit(n)
      .get()
    return snap.docs.map(d => d.data())
  }

  async getStats() {
    const snap = await this.analyses.select('overallScore', 'results').get()
    const items = snap.docs.map(d => d.data())
    if (!items.length) return { total: 0, avgScore: null, topWeakArea: null }
    const avgScore = Math.round(items.reduce((s, i) => s + (i.overallScore || 0), 0) / items.length)
    const freq = {}
    for (const item of items) {
      for (const r of (item.results || [])) {
        if (r.score < 60) freq[r.name] = (freq[r.name] || 0) + 1
      }
    }
    const topWeakArea = Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] || null
    return { total: items.length, avgScore, topWeakArea }
  }

  async updateSuggestions(id, suggestions) {
    await this.analyses.doc(id).update({ suggestions })
    return { ok: true }
  }

  async getIncidents() {
    const snap = await this.incidents.orderBy('timestamp', 'desc').limit(50).get()
    return snap.docs.map(d => d.data())
  }

  async saveIncidents(incidents) {
    const batch = this.db.batch()
    for (const inc of incidents) {
      batch.set(this.incidents.doc(inc.id || `${Date.now()}`), inc)
    }
    await batch.commit()
    return { ok: true }
  }
}
