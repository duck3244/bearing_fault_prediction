import { useState } from 'react';
import { ApiError } from '@/lib/api';
import { Card } from '@/components/Card';
import { UploadDropzone } from './UploadDropzone';
import { AnalysisResultView } from './AnalysisResultView';
import { useAnalyze, type AnalyzeInput } from './useAnalyze';

function errorMessage(err: unknown): string | null {
  if (!err) return null;
  if (err instanceof ApiError) {
    if (
      err.body &&
      typeof err.body === 'object' &&
      'error' in err.body &&
      typeof (err.body as { error: unknown }).error === 'string'
    ) {
      return (err.body as { error: string }).error;
    }
    return `HTTP ${err.status}`;
  }
  return String(err);
}

export function AnalyzePage() {
  const [form, setForm] = useState({ rpm: 1800, samplingRate: 12000, signalColumn: '' });
  const [fileName, setFileName] = useState<string | null>(null);
  const analyze = useAnalyze();

  function handleFile(file: File) {
    setFileName(file.name);
    const input: AnalyzeInput = { file };
    if (!file.name.toLowerCase().endsWith('.mat')) {
      input.rpm = form.rpm;
      input.samplingRate = form.samplingRate;
      if (form.signalColumn.trim()) input.signalColumn = form.signalColumn.trim();
    }
    analyze.mutate(input);
  }

  const data = analyze.data;
  const errMsg = errorMessage(analyze.error);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-6">
      <div className="grid items-start gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <UploadDropzone onFile={handleFile} busy={analyze.isPending} fileName={fileName} />
        </div>
        <Card title="CSV defaults" subtitle="Used only for .csv uploads — .mat carries metadata">
          <div className="space-y-2 text-sm">
            <label className="flex items-center justify-between gap-2">
              <span className="text-slate-500">RPM</span>
              <input
                type="number"
                value={form.rpm}
                onChange={(e) => setForm({ ...form, rpm: Number(e.target.value) })}
                className="w-24 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono text-xs dark:border-slate-700"
              />
            </label>
            <label className="flex items-center justify-between gap-2">
              <span className="text-slate-500">Sampling rate (Hz)</span>
              <input
                type="number"
                value={form.samplingRate}
                onChange={(e) => setForm({ ...form, samplingRate: Number(e.target.value) })}
                className="w-24 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono text-xs dark:border-slate-700"
              />
            </label>
            <label className="flex items-center justify-between gap-2">
              <span className="text-slate-500">Signal column</span>
              <input
                type="text"
                placeholder="auto"
                value={form.signalColumn}
                onChange={(e) => setForm({ ...form, signalColumn: e.target.value })}
                className="w-24 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono text-xs dark:border-slate-700"
              />
            </label>
          </div>
        </Card>
      </div>

      {errMsg && (
        <Card>
          <p className="text-sm text-rose-600 dark:text-rose-400">{errMsg}</p>
        </Card>
      )}

      {analyze.isPending && (
        <Card>
          <p className="text-sm text-slate-500">Analyzing signal…</p>
        </Card>
      )}

      {data && (
        <AnalysisResultView
          sourceTitle="Source"
          sourceSubtitle={`sampling rate ${data.sampling_rate} Hz · ${data.rpm} rpm`}
          filename={data.filename}
          signalSample={data.signal_sample}
          freqSample={data.freq_sample}
          magnitudeSample={data.magnitude_sample}
          samplingRate={data.sampling_rate}
          faultFrequencies={data.fault_frequencies}
          faultDetection={data.fault_detection}
          timeFeatures={data.time_features}
          freqFeatures={data.freq_features}
          prediction={data.prediction}
        />
      )}
    </div>
  );
}
