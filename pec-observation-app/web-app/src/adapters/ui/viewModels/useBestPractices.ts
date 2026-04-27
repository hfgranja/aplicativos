import { useState, useCallback } from 'react'
import { FetchNetworkClient } from '../../network/FetchNetworkClient'
import { API_URLS } from '../../network/config'
import type { BestPracticeCard, PracticeDistribution } from '../../../domain/entities/BestPractice'

const client = new FetchNetworkClient(API_URLS.bestPractices)

interface ListResponse { items: BestPracticeCard[]; total: number }

function mapCard(m: Record<string, unknown>): BestPracticeCard {
  return {
    id:              m.id as string,
    title:           m.title as string,
    criterion:       m.criterion as BestPracticeCard['criterion'],
    subject:         m.subject as string,
    grade:           m.grade as string,
    excerpt:         m.excerpt as string,
    aiExplanation:   m.ai_explanation as string,
    rubricAlignment: (m.rubric_alignment as string[]) ?? [],
    tags:            (m.tags as string[]) ?? [],
    status:          m.status as BestPracticeCard['status'],
    hasAudio:        (m.has_audio as boolean) ?? false,
    audioUrl:        m.audio_url as string | undefined,
    createdAt:       m.created_at as string,
    publishedAt:     m.published_at as string | undefined,
  }
}

export function useBestPractices() {
  const [cards, setCards]           = useState<BestPracticeCard[]>([])
  const [distributions, setDists]   = useState<PracticeDistribution[]>([])
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState<string | null>(null)

  const loadLibrary = useCallback(async (status = 'published') => {
    setLoading(true)
    setError(null)
    try {
      const data = await client.get<ListResponse>('/api/v1/best-practices', { status })
      setCards(data.items.map(m => mapCard(m as unknown as Record<string, unknown>)))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar boas práticas')
    } finally {
      setLoading(false)
    }
  }, [])

  const publish = useCallback(async (cardId: string, title?: string): Promise<void> => {
    try {
      await client.post(`/api/v1/best-practices/${cardId}/publish`, { title })
      setCards(prev => prev.map(c => c.id === cardId ? { ...c, status: 'published' as const } : c))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao publicar')
    }
  }, [])

  const distribute = useCallback(async (cardId: string, teacherIds: string[], message: string): Promise<boolean> => {
    try {
      await client.post(`/api/v1/best-practices/${cardId}/distribute`, { teacher_ids: teacherIds, message })
      return true
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao distribuir')
      return false
    }
  }, [])

  const archive = useCallback(async (cardId: string): Promise<void> => {
    try {
      await client.delete(`/api/v1/best-practices/${cardId}`)
      setCards(prev => prev.filter(c => c.id !== cardId))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao arquivar')
    }
  }, [])

  const loadMyDistributions = useCallback(async (teacherId: string): Promise<void> => {
    setLoading(true)
    try {
      const data = await client.get<{ items: unknown[] }>(
        '/api/v1/best-practices/distributions/my',
        { teacher_id: teacherId }
      )
      setDists(data.items.map((m: unknown) => {
        const d = m as Record<string, unknown>
        return {
          distributionId: d.distribution_id as string,
          card:           mapCard(d.card as Record<string, unknown>),
          message:        d.message as string,
          sentAt:         d.sent_at as string,
          viewedAt:       d.viewed_at as string | undefined,
        }
      }))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar distribuições')
    } finally {
      setLoading(false)
    }
  }, [])

  return { cards, distributions, loading, error, loadLibrary, publish, distribute, archive, loadMyDistributions }
}
