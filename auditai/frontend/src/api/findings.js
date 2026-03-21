import client from './client'

export const listFindings = (params) => client.get('/findings', { params }).then(r => r.data)
export const getFinding = (id) => client.get(`/findings/${id}`).then(r => r.data)
export const acceptRisk = (id, justification) =>
  client.post(`/findings/${id}/accept-risk`, { justification }).then(r => r.data)
export const resolveFinding = (id) => client.post(`/findings/${id}/resolve`).then(r => r.data)
export const generateFix = (id) => client.post(`/findings/${id}/fix`).then(r => r.data)
export const getReport = (execId, format = 'json') =>
  client.get(`/reports/${execId}`, { params: { format } }).then(r => r.data)
export const getReleaseDecision = (execId) => client.get(`/releases/${execId}`).then(r => r.data)
