import clsx from 'clsx';
import { Card } from '@/components/Card';
import type { Prediction } from '@/api/types';

interface Props {
  prediction: Prediction | null | undefined;
}

const LABEL_LOOK: Record<string, { tag: string; bar: string }> = {
  normal: {
    tag: 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900',
    bar: 'bg-emerald-500',
  },
  outer_fault: {
    tag: 'bg-orange-50 text-orange-700 ring-orange-200 dark:bg-orange-950/40 dark:text-orange-300 dark:ring-orange-900',
    bar: 'bg-orange-500',
  },
  inner_fault: {
    tag: 'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900',
    bar: 'bg-rose-500',
  },
  ball_fault: {
    tag: 'bg-purple-50 text-purple-700 ring-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:ring-purple-900',
    bar: 'bg-purple-500',
  },
  cage_fault: {
    tag: 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-900',
    bar: 'bg-amber-500',
  },
};

function look(label: string | null | undefined) {
  return (
    (label && LABEL_LOOK[label]) || {
      tag: 'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700',
      bar: 'bg-slate-400',
    }
  );
}

export function PredictionCard({ prediction }: Props) {
  if (!prediction) {
    return (
      <Card title="Prediction" subtitle="Model is not trained yet">
        <p className="text-sm text-slate-500">No prediction available.</p>
      </Card>
    );
  }
  const entries = Object.entries(prediction.probabilities).sort(([, a], [, b]) => b - a);
  const top = look(prediction.label);

  return (
    <Card
      title="Prediction"
      subtitle={`trained on: ${prediction.trained_classes.join(', ')}`}
      right={
        <span
          className={clsx(
            'rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset',
            top.tag,
          )}
        >
          {prediction.label}
        </span>
      }
    >
      <div className="space-y-2">
        <div className="flex items-baseline justify-between text-sm">
          <span className="text-slate-500">confidence</span>
          <span className="font-mono">{(prediction.confidence * 100).toFixed(1)}%</span>
        </div>
        <div className="space-y-1.5">
          {entries.map(([cls, p]) => (
            <div key={cls}>
              <div className="flex justify-between text-xs">
                <span className="font-mono">{cls}</span>
                <span className="font-mono text-slate-500">{(p * 100).toFixed(1)}%</span>
              </div>
              <div className="mt-0.5 h-1.5 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className={clsx('h-full', look(cls).bar)}
                  style={{ width: `${Math.max(2, p * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
