import client from './client'

export const listExecutions = (appId) =>
  client.get('/executions', { params: appId ? { app_id: appId } : {} }).then(r => r.data)
export const getExecution = (id) => client.get(`/executions/${id}`).then(r => r.data)
export const createExecution = (data) => client.post('/executions', data).then(r => r.data)
export const cancelExecution = (id) => client.post(`/executions/${id}/cancel`).then(r => r.data)
export const rerunExecution = (id) => client.post(`/executions/${id}/rerun`).then(r => r.data)
export const getTestRuns = (id) => client.get(`/executions/${id}/test-runs`).then(r => r.data)
