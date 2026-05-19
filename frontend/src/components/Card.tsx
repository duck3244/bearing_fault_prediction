import clsx from 'clsx';
import { type ReactNode } from 'react';

interface Props {
  title?: ReactNode;
  subtitle?: ReactNode;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
}

const PAD = { sm: 'p-3', md: 'p-4', lg: 'p-5' };

export function Card({ title, subtitle, right, children, className, padding = 'md' }: Props) {
  return (
    <section
      className={clsx(
        'rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900',
        PAD[padding],
        className,
      )}
    >
      {(title || right) && (
        <header className="mb-3 flex items-baseline justify-between gap-3">
          <div className="min-w-0">
            {title && <h3 className="truncate text-sm font-semibold tracking-tight">{title}</h3>}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
            )}
          </div>
          {right && <div className="shrink-0">{right}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
