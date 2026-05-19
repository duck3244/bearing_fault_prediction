import { Card } from '@/components/Card';

interface Props {
  title: string;
  features: Record<string, number>;
  precision?: number;
  /** Optional whitelist & ordering. Defaults to all keys. */
  keys?: string[];
}

function formatNumber(n: number, p: number): string {
  if (!Number.isFinite(n)) return '—';
  if (n === 0) return '0';
  const abs = Math.abs(n);
  if (abs >= 1e6 || abs < 1e-3) return n.toExponential(p);
  return n.toFixed(p);
}

export function FeatureGrid({ title, features, precision = 3, keys }: Props) {
  const list = keys ? keys.filter((k) => k in features) : Object.keys(features);
  return (
    <Card title={title}>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono text-xs sm:grid-cols-3">
        {list.map((k) => (
          <div key={k} className="flex flex-col">
            <dt className="truncate text-[10px] uppercase tracking-wider text-slate-500">{k}</dt>
            <dd className="tabular-nums">{formatNumber(features[k], precision)}</dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}
