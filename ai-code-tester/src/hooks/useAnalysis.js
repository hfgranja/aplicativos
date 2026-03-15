import { useReducer, useCallback } from 'react'
import { runAllAnalyzers, calcOverallScore } from '../analyzers/orchestrator.js'
import { generateTests } from '../generators/testGenerator.js'

const initialState = {
  step: 'input',          // 'input' | 'analyzing' | 'results' | 'tests'
  code: '',
  packageJson: '',
  progress: 0,            // 0-12
  currentTechnique: '',
  results: [],
  overallScore: 0,
  generatedTests: '',
  error: null,
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_CODE':
      return { ...state, code: action.payload }
    case 'SET_PKG':
      return { ...state, packageJson: action.payload }
    case 'START_ANALYSIS':
      return { ...state, step: 'analyzing', progress: 0, results: [], error: null }
    case 'PROGRESS':
      return { ...state, progress: action.index, currentTechnique: action.name }
    case 'RESULT_READY':
      return { ...state, results: [...state.results, action.result] }
    case 'ANALYSIS_DONE':
      return {
        ...state,
        step: 'results',
        results: action.results,
        overallScore: action.overallScore,
        progress: 12,
      }
    case 'GENERATE_TESTS':
      return { ...state, step: 'tests', generatedTests: action.tests }
    case 'RESET':
      return { ...initialState }
    case 'ERROR':
      return { ...state, step: 'input', error: action.message }
    default:
      return state
  }
}

export function useAnalysis() {
  const [state, dispatch] = useReducer(reducer, initialState)

  const setCode = useCallback((code) => dispatch({ type: 'SET_CODE', payload: code }), [])
  const setPkg = useCallback((pkg) => dispatch({ type: 'SET_PKG', payload: pkg }), [])
  const reset = useCallback(() => dispatch({ type: 'RESET' }), [])

  const startAnalysis = useCallback(async () => {
    if (!state.code.trim()) {
      dispatch({ type: 'ERROR', message: 'Cole ou carregue o código antes de analisar' })
      return
    }

    dispatch({ type: 'START_ANALYSIS' })

    try {
      const results = await runAllAnalyzers(
        state.code,
        state.packageJson,
        (index, _total, name) => {
          dispatch({ type: 'PROGRESS', index, name })
        }
      )

      const overallScore = calcOverallScore(results)
      dispatch({ type: 'ANALYSIS_DONE', results, overallScore })
    } catch (err) {
      dispatch({ type: 'ERROR', message: `Erro durante análise: ${err.message}` })
    }
  }, [state.code, state.packageJson])

  const generateTestSuite = useCallback(() => {
    const tests = generateTests(state.code, state.results)
    dispatch({ type: 'GENERATE_TESTS', tests })
  }, [state.code, state.results])

  return {
    ...state,
    setCode,
    setPkg,
    startAnalysis,
    generateTestSuite,
    reset,
  }
}
