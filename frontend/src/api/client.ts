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

// Add auth token to every request
api.interceptors.request.use((config) => {
  try {
    const stored = localStorage.getItem('vulnai_user')
    if (stored) {
      const user = JSON.parse(stored)
      if (user?.access_token) {
        config.headers.Authorization = `Bearer ${user.access_token}`
      }
    }
  } catch {}
  return config
})

// Handle 401 responses (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('vulnai_user')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

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