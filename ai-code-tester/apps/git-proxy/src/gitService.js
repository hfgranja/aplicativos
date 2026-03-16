/**
 * GitService — Serviço unificado para conexão com repositórios Git
 * Suporta: GitHub, GitLab, Bitbucket, Azure DevOps (cloud e enterprise)
 *
 * Segurança:
 * - Tokens nunca são persistidos (apenas passados como parâmetro)
 * - Apenas operações de leitura (GET)
 * - Timeout de 10s por requisição via AbortController
 * - HTTPS enforced
 */

const REQUEST_TIMEOUT_MS = 10000
const MAX_CONCURRENT_FETCHES = 5

// Extensões de código suportadas para análise
export const CODE_EXTENSIONS = [
  '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs',
  '.py', '.java', '.go', '.rb', '.php', '.cs',
  '.cpp', '.c', '.h', '.swift', '.kt', '.rs',
]

// Extensões ignoradas (binários, assets, etc.)
const IGNORED_EXTENSIONS = [
  '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
  '.mp4', '.mp3', '.pdf', '.zip', '.tar', '.gz',
  '.woff', '.woff2', '.ttf', '.eot',
  '.lock', '.bin', '.exe', '.dll',
]

// Paths ignorados
const IGNORED_PATHS = [
  'node_modules/', 'vendor/', '.git/', 'dist/', 'build/', '__pycache__/',
  '.next/', '.nuxt/', 'coverage/', '.nyc_output/',
]

function isIgnoredPath(path) {
  return IGNORED_PATHS.some(p => path.includes(p))
}

/**
 * Make a fetch request with timeout and auth header
 */
async function apiFetch(url, headers = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

  try {
    const resp = await fetch(url, {
      headers: { 'Accept': 'application/json', ...headers },
      signal: controller.signal,
    })
    clearTimeout(timer)

    if (resp.status === 401) throw new GitAuthError('Token inválido ou sem permissão de leitura')
    if (resp.status === 403) throw new GitAuthError('Acesso negado — verifique o escopo do token')
    if (resp.status === 404) throw new GitNotFoundError('Repositório não encontrado ou privado')
    if (resp.status === 429) {
      const reset = resp.headers.get('X-RateLimit-Reset') || resp.headers.get('Retry-After')
      throw new GitRateLimitError(`Limite de requisições atingido. Tente novamente em ${reset ? `${Math.ceil((reset * 1000 - Date.now()) / 60000)} min` : 'alguns minutos'}`)
    }
    if (!resp.ok) throw new GitError(`Erro HTTP ${resp.status}: ${resp.statusText}`)

    const ct = resp.headers.get('content-type') || ''
    if (ct.includes('application/json')) return resp.json()
    return resp.text()
  } catch (err) {
    clearTimeout(timer)
    if (err.name === 'AbortError') throw new GitError('Timeout — resposta demorou mais de 10 segundos')
    throw err
  }
}

export class GitError extends Error { constructor(msg) { super(msg); this.type = 'GitError' } }
export class GitAuthError extends GitError { constructor(msg) { super(msg); this.type = 'GitAuthError' } }
export class GitNotFoundError extends GitError { constructor(msg) { super(msg); this.type = 'GitNotFoundError' } }
export class GitRateLimitError extends GitError { constructor(msg) { super(msg); this.type = 'GitRateLimitError' } }

// =============================================================================
// GITHUB ADAPTER
// =============================================================================
class GitHubAdapter {
  constructor(baseUrl, token) {
    this.base = (baseUrl || 'https://api.github.com').replace(/\/$/, '')
    this.headers = token ? { 'Authorization': `Bearer ${token}` } : {}
  }

  async testConnection() {
    const data = await apiFetch(`${this.base}/user`, this.headers)
    return { login: data.login, name: data.name, avatarUrl: data.avatar_url }
  }

  async getRepoInfo(owner, repo) {
    const data = await apiFetch(`${this.base}/repos/${owner}/${repo}`, this.headers)
    return {
      name: data.full_name,
      description: data.description,
      defaultBranch: data.default_branch,
      isPrivate: data.private,
      stars: data.stargazers_count,
      language: data.language,
    }
  }

  async getFileTree(owner, repo, branch) {
    // Get commit SHA for branch
    const branchData = await apiFetch(
      `${this.base}/repos/${owner}/${repo}/branches/${branch}`,
      this.headers
    )
    const sha = branchData.commit.sha

    // Fetch recursive tree
    const treeData = await apiFetch(
      `${this.base}/repos/${owner}/${repo}/git/trees/${sha}?recursive=1`,
      this.headers
    )

    return (treeData.tree || [])
      .filter(f => f.type === 'blob' && !isIgnoredPath(f.path))
      .map(f => ({ path: f.path, size: f.size || 0, sha: f.sha }))
  }

  async getFileContent(owner, repo, path, branch) {
    const data = await apiFetch(
      `${this.base}/repos/${owner}/${repo}/contents/${path}?ref=${branch}`,
      this.headers
    )
    if (data.encoding === 'base64') {
      return atob(data.content.replace(/\n/g, ''))
    }
    return data.content || ''
  }
}

// =============================================================================
// GITLAB ADAPTER
// =============================================================================
class GitLabAdapter {
  constructor(baseUrl, token) {
    this.base = (baseUrl || 'https://gitlab.com/api/v4').replace(/\/$/, '')
    this.headers = token ? { 'PRIVATE-TOKEN': token } : {}
  }

  async testConnection() {
    const data = await apiFetch(`${this.base}/user`, this.headers)
    return { login: data.username, name: data.name, avatarUrl: data.avatar_url }
  }

  async getRepoInfo(owner, repo) {
    const id = encodeURIComponent(`${owner}/${repo}`)
    const data = await apiFetch(`${this.base}/projects/${id}`, this.headers)
    return {
      name: data.path_with_namespace,
      description: data.description,
      defaultBranch: data.default_branch,
      isPrivate: data.visibility === 'private',
      stars: data.star_count,
      language: null,
    }
  }

  async getFileTree(owner, repo, branch) {
    const id = encodeURIComponent(`${owner}/${repo}`)
    const files = []
    let page = 1
    const perPage = 100

    while (true) {
      const data = await apiFetch(
        `${this.base}/projects/${id}/repository/tree?recursive=true&per_page=${perPage}&page=${page}&ref=${branch}`,
        this.headers
      )
      const items = Array.isArray(data) ? data : (data.items || [])
      files.push(...items.filter(f => f.type === 'blob' && !isIgnoredPath(f.path)))
      if (items.length < perPage) break
      page++
      if (page > 10) break // max 1000 files
    }

    return files.map(f => ({ path: f.path, size: 0, sha: f.id }))
  }

  async getFileContent(owner, repo, path, branch) {
    const id = encodeURIComponent(`${owner}/${repo}`)
    const encodedPath = encodeURIComponent(path)
    const data = await apiFetch(
      `${this.base}/projects/${id}/repository/files/${encodedPath}?ref=${branch}`,
      this.headers
    )
    if (data.encoding === 'base64') {
      return atob(data.content.replace(/\n/g, ''))
    }
    return data.content || ''
  }
}

// =============================================================================
// BITBUCKET ADAPTER
// =============================================================================
class BitbucketAdapter {
  constructor(_baseUrl, token, username) {
    this.base = 'https://api.bitbucket.org/2.0'
    this.headers = username && token
      ? { 'Authorization': `Basic ${btoa(`${username}:${token}`)}` }
      : {}
  }

  async testConnection() {
    const data = await apiFetch(`${this.base}/user`, this.headers)
    return { login: data.username, name: data.display_name, avatarUrl: data.links?.avatar?.href }
  }

  async getRepoInfo(workspace, repo) {
    const data = await apiFetch(`${this.base}/repositories/${workspace}/${repo}`, this.headers)
    return {
      name: data.full_name,
      description: data.description,
      defaultBranch: data.mainbranch?.name || 'main',
      isPrivate: data.is_private,
      stars: 0,
      language: data.language,
    }
  }

  async getFileTree(workspace, repo, branch) {
    const files = []
    let url = `${this.base}/repositories/${workspace}/${repo}/src/${branch}/?pagelen=100&q=`

    // Bitbucket uses paginated listing
    const fetchPage = async (pageUrl) => {
      const data = await apiFetch(pageUrl, this.headers)
      for (const item of data.values || []) {
        if (item.type === 'commit_file' && !isIgnoredPath(item.path)) {
          files.push({ path: item.path, size: item.size || 0, sha: item.commit?.hash })
        }
      }
      if (data.next && files.length < 500) await fetchPage(data.next)
    }

    await fetchPage(url)
    return files
  }

  async getFileContent(workspace, repo, path, branch) {
    const text = await apiFetch(
      `${this.base}/repositories/${workspace}/${repo}/src/${branch}/${path}`,
      { ...this.headers, 'Accept': 'text/plain' }
    )
    return typeof text === 'string' ? text : JSON.stringify(text)
  }
}

// =============================================================================
// AZURE DEVOPS ADAPTER
// =============================================================================
class AzureDevOpsAdapter {
  constructor(baseUrl, token) {
    this.base = (baseUrl || 'https://dev.azure.com').replace(/\/$/, '')
    this.headers = token ? { 'Authorization': `Basic ${btoa(`:${token}`)}` } : {}
  }

  _parseUrl(owner) {
    // owner format: "organization/project" or just "organization"
    const parts = owner.split('/')
    return { org: parts[0], project: parts[1] || parts[0] }
  }

  async testConnection() {
    const { org } = this._parseUrl('org')
    const data = await apiFetch(
      `${this.base}/${org}/_apis/connectionData?api-version=7.0`,
      this.headers
    )
    const user = data.authenticatedUser
    return { login: user?.providerDisplayName || 'Azure User', name: user?.providerDisplayName, avatarUrl: null }
  }

  async getRepoInfo(owner, repo) {
    const { org, project } = this._parseUrl(owner)
    const data = await apiFetch(
      `${this.base}/${org}/${project}/_apis/git/repositories/${repo}?api-version=7.0`,
      this.headers
    )
    return {
      name: data.name,
      description: data.description || '',
      defaultBranch: data.defaultBranch?.replace('refs/heads/', '') || 'main',
      isPrivate: true,
      stars: 0,
      language: null,
    }
  }

  async getFileTree(owner, repo, branch) {
    const { org, project } = this._parseUrl(owner)
    const data = await apiFetch(
      `${this.base}/${org}/${project}/_apis/git/repositories/${repo}/items?` +
      `recursionLevel=Full&versionDescriptor.version=${branch}&api-version=7.0`,
      this.headers
    )

    return (data.value || [])
      .filter(f => f.gitObjectType === 'blob' && !isIgnoredPath(f.path.replace(/^\//, '')))
      .map(f => ({ path: f.path.replace(/^\//, ''), size: f.size || 0, sha: f.objectId }))
  }

  async getFileContent(owner, repo, path, branch) {
    const { org, project } = this._parseUrl(owner)
    return apiFetch(
      `${this.base}/${org}/${project}/_apis/git/repositories/${repo}/items?` +
      `path=/${path}&versionDescriptor.version=${branch}&api-version=7.0`,
      { ...this.headers, 'Accept': 'text/plain' }
    )
  }
}

// =============================================================================
// MAIN GitService CLASS
// =============================================================================
export class GitService {
  constructor({ provider, baseUrl, token, username }) {
    switch (provider) {
      case 'github':
        this.adapter = new GitHubAdapter(baseUrl, token)
        break
      case 'gitlab':
        this.adapter = new GitLabAdapter(baseUrl, token)
        break
      case 'bitbucket':
        this.adapter = new BitbucketAdapter(baseUrl, token, username)
        break
      case 'azure':
        this.adapter = new AzureDevOpsAdapter(baseUrl, token)
        break
      default:
        throw new GitError(`Provedor desconhecido: ${provider}`)
    }
    this.provider = provider
  }

  testConnection() { return this.adapter.testConnection() }
  getRepoInfo(owner, repo) { return this.adapter.getRepoInfo(owner, repo) }
  getFileTree(owner, repo, branch) { return this.adapter.getFileTree(owner, repo, branch) }
  getFileContent(owner, repo, path, branch) { return this.adapter.getFileContent(owner, repo, path, branch) }

  /**
   * Load multiple files concurrently and concatenate into a single string
   */
  async loadSelectedFiles(owner, repo, branch, paths, onProgress) {
    const results = []
    let loaded = 0

    // Process in batches of MAX_CONCURRENT_FETCHES
    for (let i = 0; i < paths.length; i += MAX_CONCURRENT_FETCHES) {
      const batch = paths.slice(i, i + MAX_CONCURRENT_FETCHES)
      const batchResults = await Promise.allSettled(
        batch.map(path => this.getFileContent(owner, repo, path, branch))
      )

      batchResults.forEach((result, j) => {
        const path = batch[j]
        loaded++
        if (onProgress) onProgress(Math.round((loaded / paths.length) * 100))

        if (result.status === 'fulfilled') {
          const content = result.value || ''
          // Truncate very large files
          const truncated = content.length > 100000
            ? content.slice(0, 100000) + '\n// [ARQUIVO TRUNCADO — mais de 100KB]'
            : content
          results.push(`// === FILE: ${path} ===\n${truncated}\n`)
        } else {
          results.push(`// === FILE: ${path} === [ERRO: ${result.reason?.message}]\n`)
        }
      })
    }

    return results.join('\n')
  }
}

/**
 * Parse a GitHub/GitLab URL into owner + repo
 * Handles: https://github.com/owner/repo, owner/repo, owner/repo.git
 */
export function parseRepoUrl(url) {
  if (!url) return { owner: '', repo: '' }
  const cleaned = url.trim()
    .replace(/\.git$/, '')
    .replace(/\/$/, '')

  // Full URL
  const urlMatch = cleaned.match(/(?:github\.com|gitlab\.com|bitbucket\.org)[/:]([^/]+)\/([^/]+)/)
  if (urlMatch) return { owner: urlMatch[1], repo: urlMatch[2] }

  // owner/repo format
  const parts = cleaned.split('/')
  if (parts.length >= 2) return { owner: parts[parts.length - 2], repo: parts[parts.length - 1] }

  return { owner: cleaned, repo: '' }
}

/**
 * Recommended token scopes per provider
 */
export const TOKEN_SCOPES = {
  github: {
    label: 'GitHub PAT',
    url: 'https://github.com/settings/tokens/new',
    scopes: 'repo (privado) ou sem escopo (público)',
    steps: 'Settings → Developer settings → Personal access tokens → Tokens (classic)',
  },
  gitlab: {
    label: 'GitLab PAT',
    url: 'https://gitlab.com/-/profile/personal_access_tokens',
    scopes: 'read_repository',
    steps: 'Preferences → Access Tokens → Add new token',
  },
  bitbucket: {
    label: 'Bitbucket App Password',
    url: 'https://bitbucket.org/account/settings/app-passwords/new',
    scopes: 'Repositories: Read',
    steps: 'Personal settings → App passwords → Create app password',
  },
  azure: {
    label: 'Azure DevOps PAT',
    url: 'https://dev.azure.com',
    scopes: 'Code: Read',
    steps: 'User Settings → Personal access tokens → New Token → Code: Read',
  },
}
