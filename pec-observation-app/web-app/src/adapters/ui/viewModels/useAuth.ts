import { useState, useCallback } from 'react'
import { FetchNetworkClient, saveToken, clearToken } from '../../network/FetchNetworkClient'
import { API_URLS } from '../../network/config'

interface LoginResponse {
  access_token: string
  token_type: string
  user: { id: string; email: string; full_name: string; role: string }
}

const client = new FetchNetworkClient(API_URLS.identity)

export function useAuth() {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      const body = new URLSearchParams({ username: email, password })
      const res = await fetch(`${API_URLS.identity}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: body.toString(),
      })
      if (!res.ok) { setError('Email ou senha incorretos'); return false }
      const data: LoginResponse = await res.json()
      saveToken(data.access_token)
      localStorage.setItem('pec_user', JSON.stringify(data.user))
      return true
    } catch {
      setError('Falha ao conectar com o servidor')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    clearToken()
    localStorage.removeItem('pec_user')
    window.location.href = '/login'
  }, [])

  const currentUser = () => {
    try { return JSON.parse(localStorage.getItem('pec_user') ?? 'null') } catch { return null }
  }

  const isAuthenticated = () => !!localStorage.getItem('pec_access_token')

  return { login, logout, loading, error, currentUser, isAuthenticated }
}
