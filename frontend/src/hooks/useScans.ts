import { useState, useEffect, useCallback } from 'react'
import { scanApi } from '../api/client'
import type { Scan } from '../types'

export function useScans() {
  const [scans, setScans] = useState<Scan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchScans = useCallback(async () => {
    try {
      const result = await scanApi.list()
      setScans(Array.isArray(result) ? result : [])
      setError(null)
    } catch (e) {
      console.error('Failed to fetch scans:', e)
      setError('Failed to load scans')
      setScans([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchScans()
    const interval = setInterval(fetchScans, 5000)
    return () => clearInterval(interval)
  }, [fetchScans])

  return { scans, loading, error, refetch: fetchScans }
}

export function useScan(scanId: string | undefined) {
  const [scan, setScan] = useState<Scan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchScan = useCallback(async () => {
    if (!scanId) { setLoading(false); return }
    try {
      const result = await scanApi.get(scanId)
      setScan(result)
      setError(null)
    } catch (e) {
      console.error('Failed to fetch scan:', e)
      setError('Scan not found')
    } finally {
      setLoading(false)
    }
  }, [scanId])

  useEffect(() => {
    fetchScan()
  }, [fetchScan])

  return { scan, loading, error, refetch: fetchScan }
}