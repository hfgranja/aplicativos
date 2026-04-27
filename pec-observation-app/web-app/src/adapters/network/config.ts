// Service base URLs — overridable via env vars at build time
export const API_URLS = {
  identity:    import.meta.env.VITE_IDENTITY_URL    ?? 'http://localhost:8001',
  school:      import.meta.env.VITE_SCHOOL_URL      ?? 'http://localhost:8002',
  observation: import.meta.env.VITE_OBSERVATION_URL ?? 'http://localhost:8003',
  audio:       import.meta.env.VITE_AUDIO_URL       ?? 'http://localhost:8004',
  feedback:    import.meta.env.VITE_FEEDBACK_URL    ?? 'http://localhost:8007',
  knowledge:   import.meta.env.VITE_KNOWLEDGE_URL   ?? 'http://localhost:8011',
}
