import { useMutation } from '@tanstack/react-query';
import { apiPost } from '@/lib/api';
import type { GenerateSampleRequest, SampleDataResponse } from '@/api/types';

export function useGenerateSample() {
  return useMutation({
    mutationFn: (body: GenerateSampleRequest) =>
      apiPost<SampleDataResponse>('/api/generate-sample', body),
  });
}
