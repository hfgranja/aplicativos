/**
 * Base interface for storage adapters.
 * All methods must be implemented by cloud-specific adapters.
 */
export class BaseStorageAdapter {
  /** @param {object} analysis - { id, code, results, overallScore, analyzedAt } */
  async saveAnalysis(analysis) { throw new Error('Not implemented') }

  /** @param {number} n @returns {Promise<Array>} */
  async getRecentAnalyses(n = 20) { throw new Error('Not implemented') }

  /** @returns {Promise<{total, avgScore, topWeakArea}>} */
  async getStats() { throw new Error('Not implemented') }

  /** @param {string} id @param {Array} suggestions */
  async updateSuggestions(id, suggestions) { throw new Error('Not implemented') }

  /** @returns {Promise<Array>} */
  async getIncidents() { throw new Error('Not implemented') }

  /** @param {Array} incidents */
  async saveIncidents(incidents) { throw new Error('Not implemented') }
}
