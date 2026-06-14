import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listFindings, getFinding, updateFinding } from '../api/client';

export function useFindings(scanId: string | undefined, params?: {
  severity?: string;
  delta_status?: string;
}) {
  return useQuery({
    queryKey: ['findings', scanId, params],
    queryFn: () => listFindings(scanId!, params),
    enabled: !!scanId,
  });
}

export function useFinding(id: string | undefined) {
  return useQuery({
    queryKey: ['finding', id],
    queryFn: () => getFinding(id!),
    enabled: !!id,
  });
}

export function useUpdateFinding() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: { is_false_positive?: boolean; severity?: string } }) =>
      updateFinding(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['findings'] });
    },
  });
}