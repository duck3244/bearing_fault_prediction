import { Suspense, lazy } from 'react';
import { Card } from '@/components/Card';
import { FaultFreqTable } from './FaultFreqTable';
import { FeatureGrid } from './FeatureGrid';
import { PredictionCard } from './PredictionCard';
import type { FaultDetectionHit, FaultFrequencies, Prediction, TimeFeatures } from '@/api/types';

const SignalChart = lazy(() =>
  import('@/components/charts/SignalChart').then((m) => ({ default: m.SignalChart })),
);
const SpectrumChart = lazy(() =>
  import('@/components/charts/SpectrumChart').then((m) => ({ default: m.SpectrumChart })),
);

const TIME_KEYS = [
  'rms',
  'peak',
  'kurtosis',
  'skewness',
  'crest_factor',
  'impulse_factor',
  'shape_factor',
  'clearance_factor',
  'entropy',
  'energy',
  'std_dev',
  'zero_crossing_rate',
];

const FREQ_KEYS = [
  'mean_magnitude',
  'std_magnitude',
  'max_magnitude',
  'spectral_centroid',
  'bandwidth',
  'low_freq_energy_ratio',
];

function ChartFallback({ height }: { height: number }) {
  return (
    <div
      className="flex items-center justify-center rounded-md bg-slate-100 text-xs text-slate-400 dark:bg-slate-800"
      style={{ height }}
    >
      Loading chart…
    </div>
  );
}

export interface AnalysisResultViewProps {
  sourceTitle: string;
  sourceSubtitle: string;
  filename?: string;
  signalSample: number[];
  freqSample: number[];
  magnitudeSample: number[];
  samplingRate: number;
  faultFrequencies: FaultFrequencies;
  faultDetection: Record<string, FaultDetectionHit[]>;
  timeFeatures: TimeFeatures;
  freqFeatures: Record<string, number>;
  prediction: Prediction | null | undefined;
}

export function AnalysisResultView(props: AnalysisResultViewProps) {
  return (
    <>
      <div className="grid gap-4 lg:grid-cols-3">
        <Card title={props.sourceTitle} subtitle={props.sourceSubtitle}>
          {props.filename && <p className="truncate font-mono text-xs">{props.filename}</p>}
        </Card>
        <div className="lg:col-span-2">
          <PredictionCard prediction={props.prediction} />
        </div>
      </div>

      <Card title="Time-domain signal" subtitle="first 1000 samples">
        <Suspense fallback={<ChartFallback height={240} />}>
          <SignalChart samples={props.signalSample} samplingRate={props.samplingRate} />
        </Suspense>
      </Card>

      <Card title="Frequency spectrum" subtitle="dotted lines mark BPFO/BPFI/BSF/FTF">
        <Suspense fallback={<ChartFallback height={280} />}>
          <SpectrumChart
            freq={props.freqSample}
            magnitude={props.magnitudeSample}
            faultFrequencies={props.faultFrequencies}
          />
        </Suspense>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <FaultFreqTable
          faultFrequencies={props.faultFrequencies}
          detection={props.faultDetection}
        />
        <FeatureGrid
          title="Time-domain features"
          features={props.timeFeatures as unknown as Record<string, number>}
          keys={TIME_KEYS}
        />
      </div>

      <FeatureGrid
        title="Frequency-domain features (subset)"
        features={props.freqFeatures}
        keys={FREQ_KEYS}
      />
    </>
  );
}
