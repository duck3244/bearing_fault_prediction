import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api';
import type {
  BearingPresetApplyResponse,
  BearingPresetsResponse,
  RetrainRequest,
  RetrainResponse,
} from '@/api/types';

const MODEL_INFO_KEY = ['model', 'info'] as const;
const PRESETS_KEY = ['bearing', 'presets'] as const;

export function useBearingPresets() {
  return useQuery({
    queryKey: PRESETS_KEY,
    queryFn: () => apiGet<BearingPresetsResponse>('/api/bearing-presets'),
  });
}

export function useApplyPreset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) =>
      apiPost<BearingPresetApplyResponse>(
        `/api/bearing-presets/${encodeURIComponent(name)}`,
        undefined,
      ),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PRESETS_KEY });
    },
  });
}

export function useRetrain() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: RetrainRequest) => apiPost<RetrainResponse>('/api/model/retrain', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: MODEL_INFO_KEY });
    },
  });
}
