import { useState, useEffect, useCallback } from 'react'
import { findingApi } from '../api/client'
import type { Finding } from '../types'

export function useFindings(scanId: string | undefined) {
  const [findings, setFindings] = useState<Finding[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchFindings = useCallback(async () => {
    if (!scanId) { setLoading(false); return }
    try {
      const result = await findingApi.list(scanId)
      setFindings(Array.isArray(result) ? result : [])
      setError(null)
    } catch (e) {
      console.error('Failed to fetch findings:', e)
      setError('Failed to load findings')
      setFindings([])
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    fetchFindings()
  }, [fetchFindings])

  return { findings, loading, error, refetch: fetchFindings }
}