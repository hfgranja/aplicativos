import { useState, useCallback } from 'react'
import { FetchNetworkClient } from '../../network/FetchNetworkClient'
import { API_URLS } from '../../network/config'
import type { School, Teacher } from '../../../domain/entities/School'

const client = new FetchNetworkClient(API_URLS.school)

export function useSchools() {
  const [schools, setSchools]   = useState<School[]>([])
  const [teachers, setTeachers] = useState<Teacher[]>([])
  const [loading, setLoading]   = useState(false)
  const [error, setError]       = useState<string | null>(null)

  const loadSchools = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await client.get<{ items: School[] }>('/api/v1/schools')
      setSchools(data.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar escolas')
    } finally {
      setLoading(false)
    }
  }, [])

  const loadTeachers = useCallback(async (schoolId: string) => {
    try {
      const data = await client.get<{ items: Teacher[] }>(`/api/v1/schools/${schoolId}/teachers`)
      setTeachers(data.items)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar professores')
    }
  }, [])

  const createSchool = useCallback(async (input: Omit<School, 'id' | 'createdAt' | 'isActive'>): Promise<School | null> => {
    setLoading(true)
    try {
      const school = await client.post<School>('/api/v1/schools', {
        inep_code:      input.inepCode,
        name:           input.name,
        city:           input.city,
        state:          input.state,
        address:        input.address,
        principal_name: input.principalName,
      })
      setSchools(prev => [school, ...prev])
      return school
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao criar escola')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  const createTeacher = useCallback(async (schoolId: string, input: Omit<Teacher, 'id' | 'createdAt' | 'isActive' | 'schoolId'>): Promise<Teacher | null> => {
    try {
      const teacher = await client.post<Teacher>(`/api/v1/schools/${schoolId}/teachers`, {
        name:         input.name,
        email:        input.email,
        subject_area: input.subjectArea,
        employee_id:  input.employeeId,
      })
      setTeachers(prev => [teacher, ...prev])
      return teacher
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Erro ao adicionar professor')
      return null
    }
  }, [])

  return { schools, teachers, loading, error, loadSchools, loadTeachers, createSchool, createTeacher }
}
