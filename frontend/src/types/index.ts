export interface Scan {
  id: string
  target: string
  scope: string[]
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  scan_types: string[]
  authorisation_confirmed: boolean
  authorisation_token?: string
  created_at: string
  updated_at?: string
  completed_at?: string
  summary?: string
  total_findings: number
  critical_count: number
  high_count: number
  medium_count: number
  low_count: number
  info_count: number
  previous_scan_id?: string
}

export interface Finding {
  id: string
  scan_id: string
  title: string
  description: string
  severity: 'critical' | 'high' | 'medium' | 'low' | 'informational'
  cvss_score?: number
  cve_ids: string[]
  cwe_ids: string[]
  affected_component: string
  evidence?: string
  ai_triage_notes?: string
  ai_remediation?: string
  false_positive_probability?: number
  is_false_positive: boolean
  delta_status?: 'new' | 'existing' | 'fixed' | 'regressed'
  scanner_source: string
  created_at: string
}

export interface AuditLog {
  id: string
  scan_id: string
  action: string
  actor: string
  details?: Record<string, unknown>
  timestamp: string
  ip_address?: string
}

export interface ScanCreateRequest {
  target: string
  scope: string[]
  scan_types: string[]
  authorisation_confirmed: boolean
  previous_scan_id?: string
}

export interface ScanStatusResponse {
  id: string
  status: string
  total_findings: number
}

export interface FindingsResponse {
  findings: Finding[]
  total: number
}

export interface ScansResponse {
  scans: Scan[]
  total: number
}

export const SEVERITY_COLORS = {
  critical:      { bg: '#dc2626', text: '#ffffff', light: '#fee2e2', border: '#dc262666' },
  high:          { bg: '#ea580c', text: '#ffffff', light: '#ffedd5', border: '#ea580c66' },
  medium:        { bg: '#ca8a04', text: '#ffffff', light: '#fef9c3', border: '#ca8a0466' },
  low:           { bg: '#2563eb', text: '#ffffff', light: '#dbeafe', border: '#2563eb66' },
  informational: { bg: '#6b7280', text: '#ffffff', light: '#f3f4f6', border: '#6b728066' },
} as const

export type SeverityLevel = keyof typeof SEVERITY_COLORS

export const SCAN_TYPES = [
  { key: 'port',    label: 'Port Scan',      description: 'nmap service discovery' },
  { key: 'web',     label: 'Web Crawl',      description: 'HTTP link extraction' },
  { key: 'headers', label: 'Header Analysis', description: 'Security headers check' },
  { key: 'ssl',     label: 'SSL Check',      description: 'Certificate & TLS analysis' },
  { key: 'semgrep', label: 'SAST (Semgrep)', description: 'Static code analysis' },
] as const