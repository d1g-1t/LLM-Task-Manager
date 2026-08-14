'use client';

import { useState } from 'react';
import { Loader2, BarChart3 } from 'lucide-react';
import { BASE_URL } from '@/lib/api';
import { toast } from 'sonner';

/**
 * Streams the LLM workload summary from the backend SSE-like endpoint.
 * Falls back to error toast on network failure.
 */
export function WorkloadSummaryButton() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);

  const start = async () => {
    setOpen(true);
    setText('');
    setLoading(true);
    try {
      const res = await fetch(`${BASE_URL}/llm/workload-summary/stream`, {
        cache: 'no-store',
      });
      if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      // eslint-disable-next-line no-constant-condition
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        setText((t) => t + decoder.decode(value, { stream: true }));
      }
    } catch (e) {
      toast.error('Ошибка получения сводки: ' + (e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        onClick={start}
        className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-sm hover:border-accent hover:text-accent"
      >
        <BarChart3 className="h-4 w-4" />
        AI сводка
      </button>

      {open && (
        <div
          role="dialog"
          aria-modal
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
          onClick={() => setOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-xl space-y-3 rounded-xl border border-border bg-bg p-5 shadow-xl"
          >
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              Сводка нагрузки {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            </h2>
            <p className="min-h-[6rem] whitespace-pre-wrap text-sm leading-relaxed text-fg">
              {text || (loading ? 'Генерация…' : '')}
            </p>
            <div className="flex justify-end">
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg border border-border px-3 py-2 text-sm"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
