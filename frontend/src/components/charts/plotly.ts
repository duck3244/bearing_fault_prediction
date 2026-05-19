// Bundles plotly.js-cartesian-dist-min (no surface/3D/maps — keeps the
// vendor chunk closer to 1 MB instead of 3 MB).
import Plotly from 'plotly.js-cartesian-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import type { ComponentType, CSSProperties } from 'react';

interface PlotProps {
  data: unknown[];
  layout?: unknown;
  config?: unknown;
  style?: CSSProperties;
  className?: string;
  useResizeHandler?: boolean;
}

export const Plot = createPlotlyComponent(Plotly) as unknown as ComponentType<PlotProps>;
