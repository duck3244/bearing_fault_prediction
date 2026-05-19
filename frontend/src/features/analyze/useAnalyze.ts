import { useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { AnalyzeResponse } from '@/api/types';

export interface AnalyzeInput {
  file: File;
  rpm?: number;
  samplingRate?: number;
  signalColumn?: string;
}

async function postAnalyze(input: AnalyzeInput): Promise<AnalyzeResponse> {
  const fd = new FormData();
  fd.append('file', input.file);
  if (input.rpm !== undefined) fd.append('rpm', String(input.rpm));
  if (input.samplingRate !== undefined) fd.append('sampling_rate', String(input.samplingRate));
  if (input.signalColumn) fd.append('signal_column', input.signalColumn);
  return api<AnalyzeResponse>('/api/analyze', { method: 'POST', body: fd });
}

export function useAnalyze() {
  return useMutation({ mutationFn: postAnalyze });
}
