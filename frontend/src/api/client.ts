import axios from 'axios'
import type { 
  Scan, Finding, ScanCreateRequest, ScanStatusResponse 
} from '../types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

export const scanApi = {
  create: (data: ScanCreateRequest) =>
    api.post<Scan>('/api/scans', data).then(r => r.data),

  list: async (): Promise<Scan[]> => {
    const r = await api.get('/api/scans')
    const data = r.data
    if (Array.isArray(data)) return data
    if (data && Array.isArray(data.scans)) return data.scans
    if (data && Array.isArray(data.items)) return data.items
    return []
  },

  get: (id: string) =>
    api.get<Scan>(`/api/scans/${id}`).then(r => r.data),

  getStatus: (id: string) =>
    api.get<ScanStatusResponse>(`/api/scans/${id}/status`).then(r => r.data),

  cancel: (id: string) =>
    api.delete(`/api/scans/${id}/cancel`).then(r => r.data),
}

export const findingApi = {
  list: async (scanId: string): Promise<Finding[]> => {
    const r = await api.get(`/api/findings?scan_id=${scanId}`)
    const data = r.data
    if (Array.isArray(data)) return data
    if (data && Array.isArray(data.findings)) return data.findings
    if (data && Array.isArray(data.items)) return data.items
    return []
  },

  update: (id: string, data: Partial<Finding>) =>
    api.patch<Finding>(`/api/findings/${id}`, data).then(r => r.data),
}

export const reportApi = {
  getPdfUrl: (scanId: string) => `${BASE_URL}/api/reports/${scanId}/pdf`,
}

export const demoApi = {
  getScan: () => api.get<Scan>('/api/demo/scan').then(r => r.data),
  getFindings: () => api.get<Finding[]>('/api/demo/findings').then(r => r.data),
}

export default api