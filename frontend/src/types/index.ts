export interface Scan {
  id: string;
  target: string;
  scope: string[];
  status: string;
  scan_types: string[];
  authorisation_confirmed: boolean;
  authorisation_token?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  summary?: string;
  total_findings: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  previous_scan_id?: string;
}

export interface Finding {
  id: string;
  scan_id: string;
  title: string;
  description?: string;
  severity: string;
  cvss_score?: number;
  cve_ids: string[];
  cwe_ids: string[];
  affected_component?: string;
  evidence?: string;
  ai_triage_notes?: string;
  ai_remediation?: string;
  false_positive_probability?: number;
  is_false_positive: boolean;
  delta_status?: string;
  scanner_source?: string;
  created_at: string;
}

export interface ScanCreateRequest {
  target: string;
  scope: string[];
  scan_types: string[];
  authorisation_confirmed: boolean;
  previous_scan_id?: string;
}

export interface ScanStatus {
  id: string;
  status: string;
  total_findings: number;
}

export interface ScanListResponse {
  items: Scan[];
  total: number;
  page: number;
  page_size: number;
}