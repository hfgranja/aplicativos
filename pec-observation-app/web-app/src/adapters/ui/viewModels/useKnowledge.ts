import { useState, useCallback } from 'react'
import { FetchNetworkClient } from '../../network/FetchNetworkClient'
import { API_URLS } from '../../network/config'
import type { KnowledgeDocument, FeedbackStyle, StyleTone } from '../../../domain/entities/Knowledge'

const client = new FetchNetworkClient(API_URLS.knowledge)

export function useKnowledge() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([])
  const [styles, setStyles]       = useState<FeedbackStyle[]>([])
  const [loading, setLoading]     = useState(false)
  const [error, setError]         = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [docsData, stylesData] = await Promise.all([
        client.get<{ items: KnowledgeDocument[] }>('/api/v1/knowledge/documents'),
        client.get<{ items: FeedbackStyle[] }>('/api/v1/knowledge/feedback-styles'),
      ])
      setDocuments(docsData.items)
      setStyles(stylesData.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar base de conhecimento')
    } finally {
      setLoading(false)
    }
  }, [])

  const uploadDocument = useCallback(async (file: File, title: string, docType: string, description?: string): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      const doc = await client.uploadFile<KnowledgeDocument>(
        '/api/v1/knowledge/documents',
        file,
        { title, document_type: docType, ...(description ? { description } : {}) },
      )
      setDocuments(prev => [doc, ...prev])
      return true
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao enviar documento')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteDocument = useCallback(async (id: string): Promise<void> => {
    try {
      await client.delete(`/api/v1/knowledge/documents/${id}`)
      setDocuments(prev => prev.filter(d => d.id !== id))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao remover documento')
    }
  }, [])

  const createStyle = useCallback(async (input: {
    name: string; description: string; tone: StyleTone
    templatePrompt: string; exampleStrengths: string[]
    exampleImprovements: string[]; isDefault: boolean
  }): Promise<boolean> => {
    setLoading(true)
    setError(null)
    try {
      const style = await client.post<FeedbackStyle>('/api/v1/knowledge/feedback-styles', {
        name:                input.name,
        description:         input.description,
        tone:                input.tone,
        template_prompt:     input.templatePrompt,
        example_strengths:   input.exampleStrengths,
        example_improvements: input.exampleImprovements,
        is_default:          input.isDefault,
      })
      setStyles(prev => [style, ...prev])
      return true
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao criar estilo')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const deleteStyle = useCallback(async (id: string): Promise<void> => {
    try {
      await client.delete(`/api/v1/knowledge/feedback-styles/${id}`)
      setStyles(prev => prev.filter(s => s.id !== id))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao remover estilo')
    }
  }, [])

  return { documents, styles, loading, error, loadAll, uploadDocument, deleteDocument, createStyle, deleteStyle }
}
