import { useState, useEffect, useCallback } from 'react'
import { api } from '../api/client'

export function useTeachers() {
  const [teachers, setTeachers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setTeachers(await api.getTeachers())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const create = async (data) => {
    const t = await api.createTeacher(data)
    setTeachers(prev => [...prev, t].sort((a, b) => a.name.localeCompare(b.name)))
    return t
  }

  const update = async (id, data) => {
    const t = await api.updateTeacher(id, data)
    setTeachers(prev => prev.map(x => x.id === id ? t : x))
    return t
  }

  const remove = async (id) => {
    await api.deleteTeacher(id)
    setTeachers(prev => prev.filter(x => x.id !== id))
  }

  return { teachers, loading, error, reload: load, create, update, remove }
}
