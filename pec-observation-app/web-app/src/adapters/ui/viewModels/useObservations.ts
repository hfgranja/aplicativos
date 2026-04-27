import { useState, useCallback } from 'react'
import { FetchNetworkClient } from '../../network/FetchNetworkClient'
import { API_URLS } from '../../network/config'
import type { Observation } from '../../../domain/entities/Observation'

const client = new FetchNetworkClient(API_URLS.observation)

interface CreateObservationInput {
  schoolId: string
  teacherId: string
  subject: string
  grade: string
  scheduledAt: string
  durationMinutes: number
  notes?: string
}

interface ListResponse { items: Observation[]; total: number }

export function useObservations() {
  const [observations, setObservations] = useState<Observation[]>([])
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState<string | null>(null)

  const load = useCallback(async (page = 1, status?: string) => {
    setLoading(true)
    setError(null)
    try {
      const params: Record<string, string> = { page: String(page), page_size: '20' }
      if (status) params.status = status
      const data = await client.get<ListResponse>('/api/v1/observations', params)
      setObservations(data.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar observações')
    } finally {
      setLoading(false)
    }
  }, [])

  const create = useCallback(async (input: CreateObservationInput): Promise<Observation | null> => {
    setLoading(true)
    setError(null)
    try {
      const obs = await client.post<Observation>('/api/v1/observations', {
        school_id:        input.schoolId,
        teacher_id:       input.teacherId,
        subject:          input.subject,
        grade:            input.grade,
        scheduled_at:     input.scheduledAt,
        duration_minutes: input.durationMinutes,
        notes:            input.notes,
      })
      setObservations(prev => [obs, ...prev])
      return obs
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao criar observação')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const transition = useCallback(async (id: string, newStatus: string): Promise<void> => {
    try {
      await client.patch(`/api/v1/observations/${id}/status`, { status: newStatus })
      setObservations(prev =>
        prev.map(o => o.id === id ? { ...o, status: newStatus as Observation['status'] } : o)
      )
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao atualizar status')
    }
  }, [])

  const remove = useCallback(async (id: string): Promise<void> => {
    try {
      await client.delete(`/api/v1/observations/${id}`)
      setObservations(prev => prev.filter(o => o.id !== id))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao remover observação')
    }
  }, [])

  return { observations, loading, error, load, create, transition, remove }
}
