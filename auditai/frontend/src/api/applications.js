import client from './client'

export const listApplications = () => client.get('/applications').then(r => r.data)
export const getApplication = (id) => client.get(`/applications/${id}`).then(r => r.data)
export const createApplication = (data) => client.post('/applications', data).then(r => r.data)
export const updateApplication = (id, data) => client.patch(`/applications/${id}`, data).then(r => r.data)
export const deleteApplication = (id) => client.delete(`/applications/${id}`).then(r => r.data)
