import clsx from 'clsx';
import { useState } from 'react';
import { ApiError } from '@/lib/api';
import { Card } from '@/components/Card';
import { AnalysisResultView } from '@/features/analyze/AnalysisResultView';
import { FAULT_TYPES, type FaultType } from '@/api/types';
import { useGenerateSample } from './useGenerateSample';

interface Form {
  fault_type: FaultType;
  rpm: number;
  sampling_rate: number;
  num_samples: number;
  noise_level: number;
}

const DEFAULTS: Form = {
  fault_type: 'outer_fault',
  rpm: 1800,
  sampling_rate: 12000,
  num_samples: 10000,
  noise_level: 0.5,
};

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

function FaultTypeRadio({
  value,
  onChange,
}: {
  value: FaultType;
  onChange: (v: FaultType) => void;
}) {
  return (
    <div role="radiogroup" aria-label="Fault type" className="flex flex-wrap gap-1.5">
      {FAULT_TYPES.map((ft) => {
        const selected = ft === value;
        return (
          <button
            key={ft}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(ft)}
            className={clsx(
              'rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition',
              selected
                ? 'bg-slate-900 text-white ring-slate-900 dark:bg-slate-100 dark:text-slate-900 dark:ring-slate-100'
                : 'bg-white text-slate-700 ring-slate-200 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700 dark:hover:bg-slate-800',
            )}
          >
            {ft}
          </button>
        );
      })}
    </div>
  );
}

function NumberRow({
  label,
  value,
  onChange,
  step = 1,
  min,
  max,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  step?: number;
  min?: number;
  max?: number;
}) {
  return (
    <label className="flex items-center justify-between gap-2 text-sm">
      <span className="text-slate-500">{label}</span>
      <input
        type="number"
        value={value}
        step={step}
        min={min}
        max={max}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-28 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono text-xs dark:border-slate-700"
      />
    </label>
  );
}

export function GeneratePage() {
  const [form, setForm] = useState<Form>(DEFAULTS);
  const gen = useGenerateSample();
  const errMsg = errorMessage(gen.error);

  // Single requested fault_type means features dict has exactly one key
  const data = gen.data;
  const featureKey: FaultType | undefined =
    data && (Object.keys(data.features)[0] as FaultType | undefined);
  const feat = featureKey ? data!.features[featureKey] : undefined;

  function submit() {
    gen.mutate(form);
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-6 py-6">
      <div className="grid items-start gap-4 lg:grid-cols-3">
        <Card
          title="Generate synthetic signal"
          subtitle="Backend creates a synthetic vibration trace then runs the same FFT + features + classifier"
          className="lg:col-span-2"
        >
          <div className="space-y-4">
            <div>
              <p className="mb-2 text-xs uppercase tracking-wider text-slate-500">Fault type</p>
              <FaultTypeRadio
                value={form.fault_type}
                onChange={(fault_type) => setForm({ ...form, fault_type })}
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <NumberRow
                label="RPM"
                value={form.rpm}
                onChange={(rpm) => setForm({ ...form, rpm })}
              />
              <NumberRow
                label="Sampling rate (Hz)"
                value={form.sampling_rate}
                onChange={(sampling_rate) => setForm({ ...form, sampling_rate })}
              />
              <NumberRow
                label="Samples"
                value={form.num_samples}
                step={1000}
                onChange={(num_samples) => setForm({ ...form, num_samples })}
              />
              <label className="flex items-center justify-between gap-2 text-sm">
                <span className="text-slate-500">
                  Noise <span className="font-mono text-xs">({form.noise_level.toFixed(2)})</span>
                </span>
                <input
                  type="range"
                  min={0}
                  max={1.5}
                  step={0.05}
                  value={form.noise_level}
                  onChange={(e) => setForm({ ...form, noise_level: Number(e.target.value) })}
                  className="w-32 accent-sky-500"
                />
              </label>
            </div>
            <div className="pt-1">
              <button
                type="button"
                onClick={submit}
                disabled={gen.isPending}
                className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
              >
                {gen.isPending ? 'Generating…' : 'Generate'}
              </button>
            </div>
          </div>
        </Card>

        <Card title="How it works" subtitle="Synthetic playground for the same pipeline">
          <ul className="space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
            <li>
              <span className="font-mono">data_acquisition.create_sample_data()</span> synthesizes
              the signal.
            </li>
            <li>The signal flows through the production analysis path used by uploaded files.</li>
            <li>
              The classifier prediction reflects how confidently the model recognises each fault.
            </li>
          </ul>
        </Card>
      </div>

      {errMsg && (
        <Card>
          <p className="text-sm text-rose-600 dark:text-rose-400">{errMsg}</p>
        </Card>
      )}

      {gen.isPending && (
        <Card>
          <p className="text-sm text-slate-500">Generating sample…</p>
        </Card>
      )}

      {data && feat && featureKey && (
        <AnalysisResultView
          sourceTitle={`Synthetic · ${featureKey}`}
          sourceSubtitle={`sampling rate ${data.sampling_rate} Hz · ${data.rpm} rpm · noise ${form.noise_level.toFixed(
            2,
          )}`}
          signalSample={feat.signal_sample}
          freqSample={feat.freq_sample}
          magnitudeSample={feat.magnitude_sample}
          samplingRate={data.sampling_rate}
          faultFrequencies={data.fault_frequencies}
          faultDetection={feat.fault_detection}
          timeFeatures={feat.time_features}
          freqFeatures={feat.freq_features}
          prediction={feat.prediction}
        />
      )}
    </div>
  );
}
