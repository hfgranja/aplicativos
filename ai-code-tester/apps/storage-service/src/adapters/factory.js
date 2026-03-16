/**
 * Creates the appropriate storage adapter based on CLOUD_PROVIDER env var.
 * Falls back to in-memory adapter for local dev.
 */

let _instance = null

export async function createAdapter() {
  if (_instance) return _instance

  const provider = (process.env.CLOUD_PROVIDER || 'local').toLowerCase()

  switch (provider) {
    case 'aws': {
      const { DynamoDBAdapter } = await import('./dynamodb.js')
      _instance = new DynamoDBAdapter()
      break
    }
    case 'azure': {
      const { CosmosDBAdapter } = await import('./cosmosdb.js')
      _instance = new CosmosDBAdapter()
      break
    }
    case 'gcp': {
      const { FirestoreAdapter } = await import('./firestore.js')
      _instance = new FirestoreAdapter()
      break
    }
    case 'alibaba': {
      const { TableStoreAdapter } = await import('./tablestore.js')
      _instance = new TableStoreAdapter()
      break
    }
    default: {
      // In-memory adapter for local dev
      const { MemoryAdapter } = await import('./memory.js')
      _instance = new MemoryAdapter()
      console.warn('[storage-service] Using in-memory adapter (no persistence). Set CLOUD_PROVIDER=aws|azure|gcp|alibaba.')
      break
    }
  }

  return _instance
}
