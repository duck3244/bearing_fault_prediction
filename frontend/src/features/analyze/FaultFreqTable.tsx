import { Card } from '@/components/Card';
import { FAULT_NAMES, type FaultDetectionHit, type FaultFrequencies } from '@/api/types';

interface Props {
  faultFrequencies: FaultFrequencies;
  detection: Record<string, FaultDetectionHit[]>;
}

export function FaultFreqTable({ faultFrequencies, detection }: Props) {
  return (
    <Card title="Fault frequencies" subtitle="theoretical vs. detected (h1)">
      <table className="w-full text-sm">
        <thead className="text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="py-1 text-left font-medium">Type</th>
            <th className="py-1 text-right font-medium">Theoretical (Hz)</th>
            <th className="py-1 text-right font-medium">Detected (Hz)</th>
            <th className="py-1 text-right font-medium">Deviation</th>
            <th className="py-1 text-right font-medium">Amplitude</th>
          </tr>
        </thead>
        <tbody className="font-mono">
          {FAULT_NAMES.map((name) => {
            const h1 = detection[name]?.find((h) => h.harmonic === 1);
            const theo = faultFrequencies[name];
            return (
              <tr key={name} className="border-t border-slate-100 dark:border-slate-800">
                <td className="py-1.5 font-semibold">{name}</td>
                <td className="py-1.5 text-right">{theo.toFixed(2)}</td>
                <td className="py-1.5 text-right">{h1 ? h1.detected_freq.toFixed(2) : '—'}</td>
                <td className="py-1.5 text-right">{h1 ? `${h1.deviation.toFixed(2)}%` : '—'}</td>
                <td className="py-1.5 text-right">{h1 ? h1.amplitude.toFixed(4) : '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mt-2 text-xs text-slate-500">FR (shaft): {faultFrequencies.FR.toFixed(2)} Hz</p>
    </Card>
  );
}
