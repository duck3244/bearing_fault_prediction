// Minimal ambient module declarations for the partial Plotly bundles we use.
// We never call into Plotly directly — it's passed straight to
// `react-plotly.js/factory`, which treats it as opaque.
declare module 'plotly.js-cartesian-dist-min' {
  const Plotly: unknown;
  export default Plotly;
}

declare module 'react-plotly.js/factory' {
  import type { ComponentType } from 'react';
  const createPlotlyComponent: (plotly: unknown) => ComponentType<Record<string, unknown>>;
  export default createPlotlyComponent;
}
