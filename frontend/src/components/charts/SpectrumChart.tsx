import { useMemo } from 'react';
import { Plot } from './plotly';
import type { FaultFrequencies } from '@/api/types';

interface Props {
  freq: number[];
  magnitude: number[];
  faultFrequencies: FaultFrequencies;
  height?: number;
}

const FAULT_COLORS: Record<keyof FaultFrequencies, string> = {
  BPFO: '#f97316', // orange
  BPFI: '#ef4444', // red
  BSF: '#a855f7', // purple
  FTF: '#22c55e', // green
  FR: '#64748b', // slate
};

const LAYOUT_BASE = {
  margin: { l: 50, r: 10, t: 10, b: 40 },
  font: { family: 'ui-monospace, SFMono-Regular, Menlo, monospace', size: 11 },
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  xaxis: {
    title: { text: 'Frequency (Hz)', standoff: 6 },
    gridcolor: 'rgba(148,163,184,0.2)',
    zerolinecolor: 'rgba(148,163,184,0.4)',
  },
  yaxis: {
    title: { text: 'Magnitude', standoff: 6 },
    gridcolor: 'rgba(148,163,184,0.2)',
    zerolinecolor: 'rgba(148,163,184,0.4)',
  },
  showlegend: true,
  legend: { orientation: 'h' as const, y: -0.25 },
};

export function SpectrumChart({ freq, magnitude, faultFrequencies, height = 280 }: Props) {
  const { data, shapes, annotations } = useMemo(() => {
    const spectrum = {
      type: 'scattergl' as const,
      mode: 'lines' as const,
      x: freq,
      y: magnitude,
      name: 'Spectrum',
      line: { color: '#0ea5e9', width: 1 },
      hovertemplate: '%{x:.1f} Hz<br>%{y:.4f}<extra></extra>',
    };

    const maxFreq = freq[freq.length - 1] ?? 1;
    const yMax = Math.max(...magnitude);

    const shapes = (Object.keys(faultFrequencies) as Array<keyof FaultFrequencies>)
      .filter((k) => k !== 'FR' && faultFrequencies[k] > 0 && faultFrequencies[k] < maxFreq)
      .map((k) => ({
        type: 'line' as const,
        x0: faultFrequencies[k],
        x1: faultFrequencies[k],
        y0: 0,
        y1: yMax,
        line: { color: FAULT_COLORS[k], dash: 'dot' as const, width: 1 },
      }));

    const annotations = (Object.keys(faultFrequencies) as Array<keyof FaultFrequencies>)
      .filter((k) => k !== 'FR' && faultFrequencies[k] > 0 && faultFrequencies[k] < maxFreq)
      .map((k) => ({
        x: faultFrequencies[k],
        y: yMax,
        text: k,
        showarrow: false,
        yshift: 8,
        font: { color: FAULT_COLORS[k], size: 10 },
      }));

    return { data: [spectrum], shapes, annotations };
  }, [freq, magnitude, faultFrequencies]);

  return (
    <Plot
      data={data}
      layout={{ ...LAYOUT_BASE, height, autosize: true, shapes, annotations }}
      config={{ displaylogo: false, responsive: true }}
      style={{ width: '100%', height: `${height}px` }}
      useResizeHandler
    />
  );
}
