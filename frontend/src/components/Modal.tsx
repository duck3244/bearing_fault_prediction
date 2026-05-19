import { useEffect, useRef, type ReactNode } from 'react';

interface Props {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  /** Tailwind max-width class. Defaults to `max-w-2xl`. */
  size?: string;
}

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  children,
  footer,
  size = 'max-w-2xl',
}: Props) {
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    // Focus the dialog so subsequent Tab presses stay inside
    dialogRef.current?.focus();
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-slate-950/40 p-6 backdrop-blur-sm"
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={typeof title === 'string' ? title : undefined}
        tabIndex={-1}
        className={`relative my-12 w-full ${size} rounded-2xl border border-slate-200 bg-white p-5 shadow-xl outline-none dark:border-slate-800 dark:bg-slate-900`}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="mb-3 flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h2 className="truncate text-base font-semibold tracking-tight">{title}</h2>
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
            )}
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-md p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden>
              <path
                d="M3 3l10 10M13 3L3 13"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </header>
        <div className="space-y-4">{children}</div>
        {footer && <footer className="mt-5 flex justify-end gap-2">{footer}</footer>}
      </div>
    </div>
  );
}
