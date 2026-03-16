import TableStore from 'tablestore'
import { BaseStorageAdapter } from './base.js'

const TABLE_ANALYSES = process.env.TABLESTORE_TABLE_ANALYSES || 'ait_analyses'
const TABLE_INCIDENTS = process.env.TABLESTORE_TABLE_INCIDENTS || 'ait_incidents'

export class TableStoreAdapter extends BaseStorageAdapter {
  constructor() {
    super()
    this.client = new TableStore.Client({
      accessKeyId: process.env.TABLESTORE_KEY_ID,
      accessKeySecret: process.env.TABLESTORE_KEY_SECRET,
      endpoint: process.env.TABLESTORE_ENDPOINT,
      instancename: process.env.TABLESTORE_INSTANCE,
    })
  }

  _put(tableName, primaryKey, attrs) {
    return new Promise((resolve, reject) => {
      const attributeColumns = Object.entries(attrs).map(([k, v]) => ({
        [k]: typeof v === 'object' ? JSON.stringify(v) : v,
      }))
      this.client.putRow({
        tableName,
        condition: new TableStore.Condition(TableStore.RowExistenceExpectation.IGNORE, null),
        primaryKey,
        attributeColumns,
      }, (err, data) => err ? reject(err) : resolve(data))
    })
  }

  _scan(tableName, limit = 50) {
    return new Promise((resolve, reject) => {
      this.client.getRange({
        tableName,
        direction: TableStore.Direction.BACKWARD,
        inclusiveStartPrimaryKey: [{ id: TableStore.INF_MAX }],
        exclusiveEndPrimaryKey: [{ id: TableStore.INF_MIN }],
        limit,
      }, (err, data) => {
        if (err) return reject(err)
        const rows = (data.rows || []).map(row => {
          const obj = {}
          for (const attr of row.attributes) {
            try { obj[attr.columnName] = JSON.parse(attr.columnValue) }
            catch { obj[attr.columnName] = attr.columnValue }
          }
          return obj
        })
        resolve(rows)
      })
    })
  }

  async saveAnalysis(analysis) {
    const { id, ...rest } = analysis
    await this._put(TABLE_ANALYSES, [{ id }], rest)
    return { id }
  }

  async getRecentAnalyses(n = 20) {
    return this._scan(TABLE_ANALYSES, n)
  }

  async getStats() {
    const items = await this._scan(TABLE_ANALYSES, 1000)
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
    await this._put(TABLE_ANALYSES, [{ id }], { suggestions: JSON.stringify(suggestions) })
    return { ok: true }
  }

  async getIncidents() {
    return this._scan(TABLE_INCIDENTS, 50)
  }

  async saveIncidents(incidents) {
    await Promise.all(incidents.map(inc =>
      this._put(TABLE_INCIDENTS, [{ id: inc.id || `${Date.now()}` }], inc)
    ))
    return { ok: true }
  }
}
