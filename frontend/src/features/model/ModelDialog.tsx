import clsx from 'clsx';
import { useEffect, useState } from 'react';
import { Modal } from '@/components/Modal';
import { ApiError } from '@/lib/api';
import { useModelInfo } from '@/features/analyze/useModelInfo';
import { useApplyPreset, useBearingPresets, useRetrain } from './hooks';

interface Props {
  open: boolean;
  onClose: () => void;
}

type Mode = 'synthetic' | 'dataset';

interface DatasetForm {
  dataset_dir: string;
  window: number;
  hop: number;
  amplitude_augment: number;
}

const DATASET_DEFAULTS: DatasetForm = {
  dataset_dir: '',
  window: 12000,
  hop: 6000,
  amplitude_augment: 4,
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

function ModeButton({
  active,
  onClick,
  label,
  description,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  description: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={clsx(
        'flex-1 rounded-lg border p-3 text-left transition',
        active
          ? 'border-sky-400 bg-sky-50 text-slate-900 dark:bg-sky-950/40 dark:text-slate-100'
          : 'border-slate-200 bg-white hover:border-slate-300 dark:border-slate-700 dark:bg-slate-900',
      )}
    >
      <div className="text-sm font-medium">{label}</div>
      <div className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{description}</div>
    </button>
  );
}

export function ModelDialog({ open, onClose }: Props) {
  const info = useModelInfo();
  const presets = useBearingPresets();
  const applyPreset = useApplyPreset();
  const retrain = useRetrain();

  const [mode, setMode] = useState<Mode>('synthetic');
  const [save, setSave] = useState(false);
  const [dataset, setDataset] = useState<DatasetForm>(DATASET_DEFAULTS);

  // Reset transient form state when reopening the dialog
  useEffect(() => {
    if (open) retrain.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const retrainErr = errorMessage(retrain.error);
  const presetErr = errorMessage(applyPreset.error);

  function submit() {
    const base = {
      save,
      window: dataset.window,
      hop: dataset.hop,
      amplitude_augment: dataset.amplitude_augment,
      augment_scale_range: [0.3, 3.0] as [number, number],
    };
    if (mode === 'synthetic') {
      retrain.mutate({ mode, ...base });
    } else {
      retrain.mutate({
        mode,
        ...base,
        dataset_dir: dataset.dataset_dir.trim(),
      });
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Model"
      subtitle="Inspect the active classifier, switch the bearing preset, or retrain"
      footer={
        <>
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Close
          </button>
          <button
            type="button"
            onClick={submit}
            disabled={retrain.isPending || (mode === 'dataset' && !dataset.dataset_dir.trim())}
            className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
          >
            {retrain.isPending ? 'Retraining…' : 'Retrain'}
          </button>
        </>
      }
    >
      {/* Current model */}
      <section className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
        <h3 className="mb-2 text-xs uppercase tracking-wider text-slate-500">Current model</h3>
        {info.data ? (
          <dl className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 font-mono text-xs">
            <dt className="text-slate-500">source</dt>
            <dd className="break-all">{info.data.source ?? '—'}</dd>
            <dt className="text-slate-500">classes</dt>
            <dd>{info.data.trained_classes.join(', ') || '—'}</dd>
            <dt className="text-slate-500">model_path</dt>
            <dd className="break-all">{info.data.model_path}</dd>
            <dt className="text-slate-500">persisted</dt>
            <dd>{info.data.persisted ? 'yes' : 'no'}</dd>
          </dl>
        ) : (
          <p className="text-xs text-slate-500">loading…</p>
        )}
      </section>

      {/* Bearing preset */}
      <section className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
        <h3 className="mb-2 text-xs uppercase tracking-wider text-slate-500">Bearing preset</h3>
        {presets.data ? (
          <div className="space-y-2">
            <div role="radiogroup" aria-label="Bearing preset" className="flex flex-wrap gap-1.5">
              {Object.entries(presets.data.presets).map(([name, p]) => {
                const active = presets.data!.current === name;
                return (
                  <button
                    key={name}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    disabled={applyPreset.isPending}
                    onClick={() => applyPreset.mutate(name)}
                    className={clsx(
                      'rounded-full px-3 py-1 text-xs ring-1 ring-inset transition disabled:opacity-50',
                      active
                        ? 'bg-slate-900 text-white ring-slate-900 dark:bg-slate-100 dark:text-slate-900 dark:ring-slate-100'
                        : 'bg-white text-slate-700 ring-slate-200 hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-700 dark:hover:bg-slate-800',
                    )}
                    title={p.description}
                  >
                    {name}
                  </button>
                );
              })}
            </div>
            <p className="text-xs text-slate-500">
              Active: <span className="font-mono">{presets.data.current}</span>
              {presets.data.presets[presets.data.current] && (
                <>
                  {' · '}
                  <span className="font-mono">
                    BD={presets.data.presets[presets.data.current].ball_diameter}mm, PD=
                    {presets.data.presets[presets.data.current].pitch_diameter}mm, N=
                    {presets.data.presets[presets.data.current].num_balls}
                  </span>
                </>
              )}
            </p>
            {presetErr && <p className="text-xs text-rose-600 dark:text-rose-400">{presetErr}</p>}
          </div>
        ) : (
          <p className="text-xs text-slate-500">loading…</p>
        )}
      </section>

      {/* Retrain */}
      <section className="rounded-xl border border-slate-200 p-3 dark:border-slate-800">
        <h3 className="mb-2 text-xs uppercase tracking-wider text-slate-500">Retrain</h3>

        <div className="flex gap-2">
          <ModeButton
            active={mode === 'synthetic'}
            onClick={() => setMode('synthetic')}
            label="Synthetic"
            description="Re-generate training data from the current bearing preset"
          />
          <ModeButton
            active={mode === 'dataset'}
            onClick={() => setMode('dataset')}
            label="Dataset"
            description="Train on a directory of MFPT-style .mat files on the server"
          />
        </div>

        {mode === 'dataset' && (
          <div className="mt-3 space-y-2">
            <label className="block text-xs">
              <span className="text-slate-500">
                Dataset directory (absolute path on backend host)
              </span>
              <input
                type="text"
                value={dataset.dataset_dir}
                placeholder="/path/to/MFPT_Dataset/train"
                onChange={(e) => setDataset({ ...dataset, dataset_dir: e.target.value })}
                className="mt-1 w-full rounded border border-slate-300 bg-transparent px-2 py-1 font-mono text-xs dark:border-slate-700"
              />
            </label>
            <div className="grid grid-cols-3 gap-2 text-xs">
              <label className="flex items-center justify-between gap-1">
                <span className="text-slate-500">Window</span>
                <input
                  type="number"
                  value={dataset.window}
                  onChange={(e) => setDataset({ ...dataset, window: Number(e.target.value) })}
                  className="w-20 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono dark:border-slate-700"
                />
              </label>
              <label className="flex items-center justify-between gap-1">
                <span className="text-slate-500">Hop</span>
                <input
                  type="number"
                  value={dataset.hop}
                  onChange={(e) => setDataset({ ...dataset, hop: Number(e.target.value) })}
                  className="w-20 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono dark:border-slate-700"
                />
              </label>
              <label className="flex items-center justify-between gap-1">
                <span className="text-slate-500">Aug</span>
                <input
                  type="number"
                  min={1}
                  value={dataset.amplitude_augment}
                  onChange={(e) =>
                    setDataset({ ...dataset, amplitude_augment: Number(e.target.value) })
                  }
                  className="w-20 rounded border border-slate-300 bg-transparent px-2 py-1 text-right font-mono dark:border-slate-700"
                />
              </label>
            </div>
          </div>
        )}

        <label className="mt-3 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300">
          <input
            type="checkbox"
            checked={save}
            onChange={(e) => setSave(e.target.checked)}
            className="size-3.5 accent-sky-500"
          />
          Persist to <span className="font-mono">{info.data?.model_path ?? 'MODEL_PATH'}</span> on
          success
        </label>

        {retrainErr && (
          <p className="mt-2 text-xs text-rose-600 dark:text-rose-400">{retrainErr}</p>
        )}

        {retrain.data && (
          <div className="mt-3 rounded-md bg-emerald-50 p-2 text-xs text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-200">
            <p className="font-medium">Retrain complete</p>
            <p className="font-mono">source: {retrain.data.source ?? '—'}</p>
            <p className="font-mono">classes: {retrain.data.trained_classes.join(', ')}</p>
            {retrain.data.n_windows != null && (
              <p className="font-mono">windows: {retrain.data.n_windows}</p>
            )}
            {retrain.data.class_counts && (
              <p className="font-mono">counts: {JSON.stringify(retrain.data.class_counts)}</p>
            )}
            {retrain.data.saved_to && (
              <p className="font-mono">saved_to: {retrain.data.saved_to}</p>
            )}
          </div>
        )}
      </section>
    </Modal>
  );
}
