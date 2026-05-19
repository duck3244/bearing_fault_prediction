import clsx from 'clsx';
import { useRef, useState } from 'react';

interface Props {
  /** Called when the user finalizes a selection. */
  onFile: (file: File) => void;
  busy?: boolean;
  accept?: string;
  fileName?: string | null;
}

export function UploadDropzone({
  onFile,
  busy = false,
  accept = '.csv,.mat',
  fileName = null,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  function pick(file: File | undefined) {
    if (!file) return;
    onFile(file);
  }

  return (
    <div
      className={clsx(
        'group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition',
        isDragging
          ? 'border-sky-400 bg-sky-50 dark:bg-sky-950/30'
          : 'border-slate-300 bg-white hover:border-sky-400 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800',
      )}
      onDragOver={(e) => {
        e.preventDefault();
        if (!busy) setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragging(false);
        if (busy) return;
        pick(e.dataTransfer.files?.[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="sr-only"
        onChange={(e) => pick(e.target.files?.[0] ?? undefined)}
        disabled={busy}
      />
      <p className="text-sm font-medium">
        Drop a <code className="font-mono text-xs">.csv</code> or{' '}
        <code className="font-mono text-xs">.mat</code> file here
      </p>
      <p className="mt-1 text-xs text-slate-500">or</p>
      <button
        type="button"
        className="mt-2 rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-white"
        disabled={busy}
        onClick={() => inputRef.current?.click()}
      >
        {busy ? 'Analyzing…' : 'Choose file'}
      </button>
      {fileName && (
        <p className="mt-3 truncate font-mono text-xs text-slate-500">selected: {fileName}</p>
      )}
    </div>
  );
}
