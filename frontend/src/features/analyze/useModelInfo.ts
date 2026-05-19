import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api';
import type { ModelInfo } from '@/api/types';

export function useModelInfo() {
  return useQuery({
    queryKey: ['model', 'info'],
    queryFn: () => apiGet<ModelInfo>('/api/model/info'),
  });
}
