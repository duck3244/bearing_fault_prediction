import clsx from 'clsx';
import { useState } from 'react';
import { AnalyzePage } from '@/features/analyze/AnalyzePage';
import { GeneratePage } from '@/features/generate/GeneratePage';
import { useModelInfo } from '@/features/analyze/useModelInfo';
import { ModelDialog } from '@/features/model/ModelDialog';

type Tab = 'analyze' | 'generate';

function ModelStatusChip({ onClick }: { onClick: () => void }) {
  const { data, isLoading, isError } = useModelInfo();

  let tone =
    'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700';
  let label = 'loading…';
  let detail = '';

  if (isError) {
    tone =
      'bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:ring-rose-900';
    label = 'backend offline';
  } else if (data) {
    const trained = data.is_trained;
    tone = trained
      ? 'bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:ring-emerald-900'
      : 'bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:ring-amber-900';
    label = trained ? 'model ready' : 'untrained';
    detail =
      data.source && data.source.startsWith('dataset:')
        ? `dataset · ${data.trained_classes.length} classes`
        : `${data.source ?? 'synthetic'} · ${data.trained_classes.length} classes`;
  }

  return (
    <button
      type="button"
      onClick={onClick}
      title={isLoading ? 'loading…' : (data?.source ?? '')}
      aria-label="Open model panel"
      className={clsx(
        'flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ring-1 ring-inset transition hover:opacity-80',
        tone,
      )}
    >
      <span>{label}</span>
      {detail && <span className="font-mono text-[10px] opacity-75">{detail}</span>}
    </button>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      role="tab"
      aria-selected={active}
      className={clsx(
        'border-b-2 px-3 py-2 text-sm font-medium transition',
        active
          ? 'border-sky-500 text-slate-900 dark:text-slate-100'
          : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300',
      )}
    >
      {children}
    </button>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>('analyze');
  const [modelOpen, setModelOpen] = useState(false);

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-baseline gap-4">
            <h1 className="text-lg font-semibold tracking-tight">Bearing Fault Prediction</h1>
            <nav role="tablist" aria-label="Sections" className="flex items-center gap-1">
              <TabButton active={tab === 'analyze'} onClick={() => setTab('analyze')}>
                Analyze file
              </TabButton>
              <TabButton active={tab === 'generate'} onClick={() => setTab('generate')}>
                Generate sample
              </TabButton>
            </nav>
          </div>
          <ModelStatusChip onClick={() => setModelOpen(true)} />
        </div>
      </header>
      <main>{tab === 'analyze' ? <AnalyzePage /> : <GeneratePage />}</main>
      <ModelDialog open={modelOpen} onClose={() => setModelOpen(false)} />
    </div>
  );
}
