import client from './client'

export const login = (email, password) =>
  client.post('/auth/login', { email, password }).then(r => r.data)

export const refresh = (refresh_token) =>
  client.post('/auth/refresh', { refresh_token }).then(r => r.data)
