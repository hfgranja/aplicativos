/**
 * Orquestrador: executa os 18 analyzers sequencialmente
 * Cada um retorna { id, name, score, issues, suggestions, detail }
 */
import staticAnalysis from './01_staticAnalysis.js'
import complexityAnalysis from './02_complexity.js'
import duplicationAnalysis from './03_duplication.js'
import securityScan from './04_security.js'
import typeSafetyAnalysis from './05_typeSafety.js'
import dependencyAnalysis from './06_dependencies.js'
import coverageEstimation from './07_coverage.js'
import documentationQuality from './08_documentation.js'
import bestPracticesAnalysis from './09_bestPractices.js'
import performanceAnalysis from './10_performance.js'
import errorHandlingAnalysis from './11_errorHandling.js'
import apiContractAnalysis from './12_apiContracts.js'
import mutationTestingAnalysis from './13_mutationTesting.js'
import propertyBasedAnalysis from './14_propertyBased.js'
import probabilisticAssertionsAnalysis from './15_probabilisticAssertions.js'
import aiCodeReviewAnalysis from './16_aiCodeReview.js'
import visualValidationAnalysis from './17_visualValidation.js'
import crossModelValidationAnalysis from './18_crossModelValidation.js'

const ANALYZERS = [
  staticAnalysis,
  complexityAnalysis,
  duplicationAnalysis,
  securityScan,
  typeSafetyAnalysis,
  dependencyAnalysis,
  coverageEstimation,
  documentationQuality,
  bestPracticesAnalysis,
  performanceAnalysis,
  errorHandlingAnalysis,
  apiContractAnalysis,
  mutationTestingAnalysis,
  propertyBasedAnalysis,
  probabilisticAssertionsAnalysis,
  aiCodeReviewAnalysis,
  visualValidationAnalysis,
  crossModelValidationAnalysis,
]

/**
 * Run all 18 analyzers with progress callbacks
 * @param {string} code - source code to analyze
 * @param {string} packageJsonCode - optional package.json content
 * @param {function} onProgress - called with (index, total, currentName)
 * @returns {Promise<Array>} array of 18 results
 */
export async function runAllAnalyzers(code, packageJsonCode, onProgress) {
  const results = []
  const total = ANALYZERS.length

  for (let i = 0; i < ANALYZERS.length; i++) {
    const analyzer = ANALYZERS[i]

    // Yield to browser event loop for UI updates
    await new Promise(resolve => setTimeout(resolve, 80))

    // Dependencies analyzer uses package.json if provided
    let input = code
    if (i === 5 && packageJsonCode?.trim()) {
      input = packageJsonCode
    }

    let result
    try {
      result = analyzer(input)
    } catch (_err) {
      result = {
        id: i + 1,
        name: `Técnica ${i + 1}`,
        icon: '⚠️',
        color: '#888',
        score: 0,
        issues: [`Erro interno ao executar análise: ${_err.message}`],
        suggestions: ['Verifique se o código é JavaScript/TypeScript válido'],
        detail: 'Erro',
      }
    }

    results.push(result)
    if (onProgress) onProgress(i + 1, total, result.name)
  }

  return results
}

/**
 * Calculate overall health score (weighted average of 18 techniques)
 * Weights reflect importance: security (2x), error handling (1.5x), AI-specific (1.3-1.4x)
 */
export function calcOverallScore(results) {
  if (results.length === 0) return 0
  // [static, complex, dup, sec, type, deps, cov, doc, bp, perf, err, api, mut, prop, prob, airev, visual, cross]
  const weights = [1, 1, 0.8, 2, 1, 1, 1, 0.7, 1, 1.2, 1.5, 1, 1.2, 1.1, 1.3, 1.4, 0.9, 1.0]
  let total = 0, wSum = 0
  results.forEach((r, i) => {
    const w = weights[i] ?? 1
    total += r.score * w
    wSum += w
  })
  return Math.round(total / wSum)
}
