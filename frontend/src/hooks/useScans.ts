import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createScan, listScans, getScan, getScanStatus, cancelScan, downloadReport } from '../api/client';
import type { ScanCreateRequest } from '../types';

export function useScans(params?: { status?: string; page?: number }) {
  return useQuery({
    queryKey: ['scans', params],
    queryFn: () => listScans(params),
  });
}

export function useScan(id: string | undefined) {
  return useQuery({
    queryKey: ['scan', id],
    queryFn: () => getScan(id!),
    enabled: !!id,
  });
}

export function useScanStatus(id: string | undefined, enabled: boolean = false) {
  return useQuery({
    queryKey: ['scanStatus', id],
    queryFn: () => getScanStatus(id!),
    enabled: !!id && enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useCreateScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScanCreateRequest) => createScan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
    },
  });
}

export function useCancelScan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => cancelScan(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
    },
  });
}

export function useDownloadReport() {
  return useMutation({
    mutationFn: (scanId: string) => downloadReport(scanId),
  });
}