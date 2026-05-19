import { useMemo } from 'react';
import { Plot } from './plotly';

interface Props {
  samples: number[];
  samplingRate: number;
  height?: number;
}

const LAYOUT_BASE = {
  margin: { l: 50, r: 10, t: 10, b: 40 },
  font: { family: 'ui-monospace, SFMono-Regular, Menlo, monospace', size: 11 },
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  xaxis: {
    title: { text: 'Time (s)', standoff: 6 },
    gridcolor: 'rgba(148,163,184,0.2)',
    zerolinecolor: 'rgba(148,163,184,0.4)',
  },
  yaxis: {
    title: { text: 'Amplitude', standoff: 6 },
    gridcolor: 'rgba(148,163,184,0.2)',
    zerolinecolor: 'rgba(148,163,184,0.4)',
  },
};

export function SignalChart({ samples, samplingRate, height = 240 }: Props) {
  const data = useMemo(() => {
    const dt = 1 / samplingRate;
    const x = samples.map((_, i) => i * dt);
    return [
      {
        type: 'scattergl' as const,
        mode: 'lines' as const,
        x,
        y: samples,
        line: { color: '#0ea5e9', width: 1 },
        hovertemplate: '%{x:.4f}s<br>%{y:.4f}<extra></extra>',
      },
    ];
  }, [samples, samplingRate]);

  return (
    <Plot
      data={data}
      layout={{ ...LAYOUT_BASE, height, autosize: true }}
      config={{ displaylogo: false, responsive: true }}
      style={{ width: '100%', height: `${height}px` }}
      useResizeHandler
    />
  );
}
