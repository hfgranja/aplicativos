import { GitService, parseRepoUrl } from '../gitService.js'

export default async function gitRoutes(app) {
  /**
   * POST /git/connect
   * Test connection, get repo info and file tree
   */
  app.post('/git/connect', {
    schema: {
      body: {
        type: 'object',
        required: ['provider'],
        properties: {
          provider: { type: 'string' },
          baseUrl: { type: 'string', default: '' },
          token: { type: 'string', default: '' },
          username: { type: 'string', default: '' },
          owner: { type: 'string', default: '' },
          repo: { type: 'string', default: '' },
          branch: { type: 'string', default: 'main' },
          repoUrl: { type: 'string', default: '' },
        },
      },
    },
  }, async (req, reply) => {
    const { provider, baseUrl, token, username, repoUrl, branch = 'main' } = req.body
    let { owner, repo } = req.body

    if (repoUrl && (!owner || !repo)) {
      const parsed = parseRepoUrl(repoUrl)
      owner = parsed.owner
      repo = parsed.repo
    }

    try {
      const svc = new GitService({ provider, baseUrl, token, username })
      const [userInfo, repoInfo] = await Promise.all([
        svc.testConnection(),
        svc.getRepoInfo(owner, repo),
      ])
      const effectiveBranch = branch || repoInfo.defaultBranch || 'main'
      const files = await svc.getFileTree(owner, repo, effectiveBranch)
      return { userInfo, repoInfo, files, effectiveBranch }
    } catch (err) {
      req.log.warn({ err: err.message }, 'git-proxy connect error')
      return reply.code(400).send({ error: err.message, type: err.type || 'GitError' })
    }
  })

  /**
   * POST /git/files
   * Load selected file contents
   */
  app.post('/git/files', {
    schema: {
      body: {
        type: 'object',
        required: ['provider', 'owner', 'repo', 'branch', 'paths'],
        properties: {
          provider: { type: 'string' },
          baseUrl: { type: 'string', default: '' },
          token: { type: 'string', default: '' },
          username: { type: 'string', default: '' },
          owner: { type: 'string' },
          repo: { type: 'string' },
          branch: { type: 'string' },
          paths: { type: 'array', items: { type: 'string' } },
        },
      },
    },
  }, async (req, reply) => {
    const { provider, baseUrl, token, username, owner, repo, branch, paths } = req.body
    try {
      const svc = new GitService({ provider, baseUrl, token, username })
      const code = await svc.loadSelectedFiles(owner, repo, branch, paths)
      return { code, fileCount: paths.length, truncated: false }
    } catch (err) {
      req.log.warn({ err: err.message }, 'git-proxy files error')
      return reply.code(400).send({ error: err.message, type: err.type || 'GitError' })
    }
  })
}
