const BASE = '/api'

async function request(method, path, body, isFormData = false) {
  const opts = { method, headers: {} }
  if (body && !isFormData) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  } else if (isFormData) {
    opts.body = body
  }
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Erro desconhecido')
  }
  return res.json()
}

export const api = {
  // Teachers
  getTeachers: () => request('GET', '/teachers'),
  createTeacher: (d) => request('POST', '/teachers', d),
  getTeacher: (id) => request('GET', `/teachers/${id}`),
  updateTeacher: (id, d) => request('PUT', `/teachers/${id}`, d),
  deleteTeacher: (id) => request('DELETE', `/teachers/${id}`),
  getTeacherObservations: (id) => request('GET', `/teachers/${id}/observations`),

  // Observations
  createObservation: (d) => request('POST', '/observations', d),
  getObservation: (id) => request('GET', `/observations/${id}`),
  updateObservation: (id, d) => request('PUT', `/observations/${id}`, d),
  deleteObservation: (id) => request('DELETE', `/observations/${id}`),
  generateFeedback: (id) => request('POST', `/observations/${id}/generate-feedback`),
  generateCNV: (id, questions) => request('POST', `/observations/${id}/generate-cnv`, { questions }),

  // Media
  uploadMedia: (formData) => request('POST', '/media/upload', formData, true),
  transcribeMedia: (id) => request('POST', `/media/${id}/transcribe`),
  deleteMedia: (id) => request('DELETE', `/media/${id}`),

  // LLM
  llmStatus: () => request('GET', '/llm/status'),

  // Analytics
  getEvolution: (teacherId) => request('GET', `/analytics/teacher/${teacherId}/evolution`),
  getComparative: (teacherId, obs1, obs2) =>
    request('GET', `/analytics/teacher/${teacherId}/comparative?obs1=${obs1}&obs2=${obs2}`),

  // Knowledge base
  indexObservation: (obsId) => request('POST', `/knowledge/index-observation/${obsId}`),
  getBestPractices: (subject = '', grade = '') =>
    request('GET', `/knowledge/best-practices?subject=${encodeURIComponent(subject)}&grade_band=${encodeURIComponent(grade)}`),
  getSimilarContext: (subject, grade, weakSections = '') =>
    request('GET', `/knowledge/similar-context?subject=${encodeURIComponent(subject)}&grade=${encodeURIComponent(grade)}&weak_sections=${encodeURIComponent(weakSections)}`),

  // Action plan results
  createActionResult: (d) => request('POST', '/action-results', d),
  getTeacherActionResults: (teacherId) => request('GET', `/action-results/teacher/${teacherId}`),
  getPeriodComparison: (teacherId) => request('GET', `/action-results/teacher/${teacherId}/period-comparison`),
  updateActionResult: (id, d) => request('PUT', `/action-results/${id}`, d),
  deleteActionResult: (id) => request('DELETE', `/action-results/${id}`),
}
