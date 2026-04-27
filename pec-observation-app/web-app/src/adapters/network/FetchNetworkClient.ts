import type { NetworkClientPort } from '../../ports/NetworkClientPort'

const TOKEN_KEY = 'pec_access_token'

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    clearToken()
    window.location.href = '/login'
    throw new Error('Sessão expirada')
  }
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    let message = text
    try { message = JSON.parse(text)?.detail ?? text } catch { /* ignore */ }
    throw new Error(message || `HTTP ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export class FetchNetworkClient implements NetworkClientPort {
  constructor(private readonly baseUrl: string) {}

  async get<T>(path: string, params?: Record<string, string>): Promise<T> {
    const url = new URL(path, this.baseUrl)
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v))
    const res = await fetch(url.toString(), { headers: { ...authHeaders() } })
    return handleResponse<T>(res)
  }

  async post<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(new URL(path, this.baseUrl).toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(body),
    })
    return handleResponse<T>(res)
  }

  async put<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(new URL(path, this.baseUrl).toString(), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(body),
    })
    return handleResponse<T>(res)
  }

  async patch<T>(path: string, body: unknown): Promise<T> {
    const res = await fetch(new URL(path, this.baseUrl).toString(), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify(body),
    })
    return handleResponse<T>(res)
  }

  async delete(path: string): Promise<void> {
    const res = await fetch(new URL(path, this.baseUrl).toString(), {
      method: 'DELETE',
      headers: { ...authHeaders() },
    })
    await handleResponse<void>(res)
  }

  async uploadFile<T>(path: string, file: File, fields?: Record<string, string>): Promise<T> {
    const form = new FormData()
    if (fields) Object.entries(fields).forEach(([k, v]) => form.append(k, v))
    form.append('file', file)
    const res = await fetch(new URL(path, this.baseUrl).toString(), {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    })
    return handleResponse<T>(res)
  }
}
