import { useReducer, useCallback } from 'react'
import { runAllAnalyzers, calcOverallScore } from '../analyzers/orchestrator.js'
import { generateTests } from '../generators/testGenerator.js'
import { GitService } from '../services/gitService.js'

const initialGit = {
  provider: 'github',
  baseUrl: '',
  owner: '',
  repo: '',
  branch: 'main',
  token: '',
  username: '',
  connected: false,
  connecting: false,
  userInfo: null,
  repoInfo: null,
  files: [],
  selectedFiles: [],
  loadingFiles: false,
  loadProgress: 0,
  connectionError: null,
}

const initialState = {
  step: 'input',          // 'input' | 'analyzing' | 'results' | 'tests'
  code: '',
  packageJson: '',
  progress: 0,            // 0-13
  currentTechnique: '',
  results: [],
  overallScore: 0,
  generatedTests: '',
  error: null,
  git: initialGit,
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
        progress: 13,
      }
    case 'GENERATE_TESTS':
      return { ...state, step: 'tests', generatedTests: action.tests }
    case 'RESET':
      return { ...initialState }
    case 'ERROR':
      return { ...state, step: 'input', error: action.message }

    // Git actions
    case 'GIT_SET_FIELD':
      return { ...state, git: { ...state.git, ...action.fields } }
    case 'GIT_CONNECTING':
      return { ...state, git: { ...state.git, connecting: true, connectionError: null } }
    case 'GIT_CONNECTED':
      return {
        ...state,
        git: {
          ...state.git,
          connecting: false,
          connected: true,
          userInfo: action.userInfo,
          repoInfo: action.repoInfo,
          files: action.files,
          connectionError: null,
        },
      }
    case 'GIT_DISCONNECT':
      return { ...state, git: { ...initialGit } }
    case 'GIT_SELECT_FILES':
      return { ...state, git: { ...state.git, selectedFiles: action.paths } }
    case 'GIT_LOAD_START':
      return { ...state, git: { ...state.git, loadingFiles: true, loadProgress: 0 } }
    case 'GIT_LOAD_PROGRESS':
      return { ...state, git: { ...state.git, loadProgress: action.progress } }
    case 'GIT_LOAD_DONE':
      return {
        ...state,
        code: action.code,
        git: { ...state.git, loadingFiles: false, loadProgress: 100 },
      }
    default:
      return state
  }
}

export function useAnalysis() {
  const [state, dispatch] = useReducer(reducer, initialState)

  const setCode = useCallback((code) => dispatch({ type: 'SET_CODE', payload: code }), [])
  const setPkg = useCallback((pkg) => dispatch({ type: 'SET_PKG', payload: pkg }), [])
  const reset = useCallback(() => dispatch({ type: 'RESET' }), [])

  const startAnalysis = useCallback(async (codeOverride) => {
    const codeToAnalyze = codeOverride !== undefined ? codeOverride : state.code
    if (!codeToAnalyze.trim()) {
      dispatch({ type: 'ERROR', message: 'Cole ou carregue o código antes de analisar' })
      return
    }

    dispatch({ type: 'START_ANALYSIS' })

    try {
      const results = await runAllAnalyzers(
        codeToAnalyze,
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

  // Git methods
  const connectGit = useCallback(async (fields, triggerConnect = false) => {
    if (!triggerConnect) {
      dispatch({ type: 'GIT_SET_FIELD', fields })
      return
    }

    dispatch({ type: 'GIT_CONNECTING' })

    try {
      const svc = new GitService({
        provider: fields.provider || state.git.provider,
        baseUrl: fields.baseUrl || state.git.baseUrl,
        token: fields.token !== undefined ? fields.token : state.git.token,
        username: fields.username || state.git.username,
      })

      const owner = fields.owner || state.git.owner
      const repo = fields.repo || state.git.repo
      const branch = fields.branch || state.git.branch || 'main'

      // Test connection + get repo info in parallel
      const [userInfo, repoInfo] = await Promise.all([
        svc.testConnection().catch(() => null),
        svc.getRepoInfo(owner, repo),
      ])

      // Get file tree
      const files = await svc.getFileTree(owner, repo, branch)

      dispatch({
        type: 'GIT_CONNECTED',
        userInfo,
        repoInfo,
        files,
      })
    } catch (err) {
      dispatch({
        type: 'GIT_SET_FIELD',
        fields: { connecting: false, connectionError: err.message },
      })
    }
  }, [state.git])

  const disconnectGit = useCallback(() => {
    dispatch({ type: 'GIT_DISCONNECT' })
  }, [])

  const setSelectedFiles = useCallback((paths) => {
    dispatch({ type: 'GIT_SELECT_FILES', paths })
  }, [])

  const loadAndAnalyze = useCallback(async () => {
    const { provider, baseUrl, token, username, owner, repo, branch, selectedFiles } = state.git

    if (!selectedFiles.length) return

    dispatch({ type: 'GIT_LOAD_START' })

    try {
      const svc = new GitService({ provider, baseUrl, token, username })
      const code = await svc.loadSelectedFiles(owner, repo, branch, selectedFiles, (pct) => {
        dispatch({ type: 'GIT_LOAD_PROGRESS', progress: pct })
      })

      dispatch({ type: 'GIT_LOAD_DONE', code })

      // Kick off analysis with the loaded code
      dispatch({ type: 'SET_CODE', payload: code })
      dispatch({ type: 'START_ANALYSIS' })

      const results = await runAllAnalyzers(
        code,
        state.packageJson,
        (index, _total, name) => {
          dispatch({ type: 'PROGRESS', index, name })
        }
      )

      const overallScore = calcOverallScore(results)
      dispatch({ type: 'ANALYSIS_DONE', results, overallScore })
    } catch (err) {
      dispatch({ type: 'ERROR', message: `Erro ao carregar arquivos: ${err.message}` })
    }
  }, [state.git, state.packageJson])

  return {
    ...state,
    setCode,
    setPkg,
    startAnalysis,
    generateTestSuite,
    reset,
    connectGit,
    disconnectGit,
    setSelectedFiles,
    loadAndAnalyze,
  }
}
