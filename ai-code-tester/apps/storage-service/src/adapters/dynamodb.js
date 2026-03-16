import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import {
  DynamoDBDocumentClient,
  PutCommand,
  QueryCommand,
  UpdateCommand,
  ScanCommand,
  GetCommand,
} from '@aws-sdk/lib-dynamodb'
import { BaseStorageAdapter } from './base.js'

const TABLE_ANALYSES = process.env.DYNAMODB_TABLE_ANALYSES || 'ait-analyses'
const TABLE_INCIDENTS = process.env.DYNAMODB_TABLE_INCIDENTS || 'ait-incidents'

export class DynamoDBAdapter extends BaseStorageAdapter {
  constructor() {
    super()
    const client = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' })
    this.db = DynamoDBDocumentClient.from(client)
  }

  async saveAnalysis(analysis) {
    await this.db.send(new PutCommand({
      TableName: TABLE_ANALYSES,
      Item: {
        ...analysis,
        pk: 'ANALYSIS',
        sk: `${analysis.analyzedAt}#${analysis.id}`,
        ttl: Math.floor(Date.now() / 1000) + 90 * 86400, // 90 days
      },
    }))
    return { id: analysis.id }
  }

  async getRecentAnalyses(n = 20) {
    const result = await this.db.send(new QueryCommand({
      TableName: TABLE_ANALYSES,
      KeyConditionExpression: 'pk = :pk',
      ExpressionAttributeValues: { ':pk': 'ANALYSIS' },
      ScanIndexForward: false,
      Limit: n,
    }))
    return result.Items || []
  }

  async getStats() {
    const result = await this.db.send(new ScanCommand({
      TableName: TABLE_ANALYSES,
      FilterExpression: 'pk = :pk',
      ExpressionAttributeValues: { ':pk': 'ANALYSIS' },
      ProjectionExpression: 'overallScore, results',
    }))
    const items = result.Items || []
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
    // DynamoDB update requires knowing the full key; store lookup by id via GSI or scan
    await this.db.send(new ScanCommand({
      TableName: TABLE_ANALYSES,
      FilterExpression: '#id = :id',
      ExpressionAttributeNames: { '#id': 'id' },
      ExpressionAttributeValues: { ':id': id },
      Limit: 1,
    })).then(async (res) => {
      const item = (res.Items || [])[0]
      if (!item) return
      await this.db.send(new UpdateCommand({
        TableName: TABLE_ANALYSES,
        Key: { pk: item.pk, sk: item.sk },
        UpdateExpression: 'SET suggestions = :s',
        ExpressionAttributeValues: { ':s': suggestions },
      }))
    })
    return { ok: true }
  }

  async getIncidents() {
    const result = await this.db.send(new QueryCommand({
      TableName: TABLE_INCIDENTS,
      KeyConditionExpression: 'pk = :pk',
      ExpressionAttributeValues: { ':pk': 'INCIDENT' },
      ScanIndexForward: false,
      Limit: 50,
    }))
    return result.Items || []
  }

  async saveIncidents(incidents) {
    await Promise.all(incidents.map(inc =>
      this.db.send(new PutCommand({
        TableName: TABLE_INCIDENTS,
        Item: { ...inc, pk: 'INCIDENT', sk: inc.id || `${Date.now()}` },
      }))
    ))
    return { ok: true }
  }
}
