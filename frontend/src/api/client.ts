import axios from 'axios';
import type { Scan, ScanCreateRequest, ScanListResponse, ScanStatus, Finding } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function createScan(data: ScanCreateRequest): Promise<Scan> {
  const response = await api.post<Scan>('/scans', data);
  return response.data;
}

export async function listScans(params?: {
  status?: string;
  target?: string;
  page?: number;
  page_size?: number;
}): Promise<ScanListResponse> {
  const response = await api.get<ScanListResponse>('/scans', { params });
  return response.data;
}

export async function getScan(id: string): Promise<Scan> {
  const response = await api.get<Scan>(`/scans/${id}`);
  return response.data;
}

export async function getScanStatus(id: string): Promise<ScanStatus> {
  const response = await api.get<ScanStatus>(`/scans/${id}/status`);
  return response.data;
}

export async function cancelScan(id: string): Promise<void> {
  await api.delete(`/scans/${id}/cancel`);
}

export async function listFindings(scanId: string, params?: {
  severity?: string;
  delta_status?: string;
  is_false_positive?: boolean;
  scanner_source?: string;
}): Promise<Finding[]> {
  const response = await api.get<Finding[]>('/findings', {
    params: { scan_id: scanId, ...params },
  });
  return response.data;
}

export async function getFinding(id: string): Promise<Finding> {
  const response = await api.get<Finding>(`/findings/${id}`);
  return response.data;
}

export async function updateFinding(id: string, data: {
  is_false_positive?: boolean;
  severity?: string;
}): Promise<Finding> {
  const response = await api.patch<Finding>(`/findings/${id}`, data);
  return response.data;
}

export async function downloadReport(scanId: string): Promise<Blob> {
  const response = await api.get(`/reports/${scanId}/pdf`, {
    responseType: 'blob',
  });
  return response.data;
}

export async function healthCheck(): Promise<any> {
  const response = await api.get('/health');
  return response.data;
}

export default api;