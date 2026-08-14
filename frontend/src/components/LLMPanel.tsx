'use client';

import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { llmApi, tasksApi } from '@/lib/client';
import { useUpdateTask } from '@/lib/hooks';
import type { Task, TaskPriority } from '@/lib/types';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

type Suggestion =
  | { kind: 'category'; value: string; rationale: string; confidence: number }
  | {
      kind: 'subtasks';
      value: Array<{ title: string; estimate_minutes: number | null }>;
    }
  | { kind: 'priority'; value: TaskPriority; rationale: string; confidence: number };

export function LLMPanel({ task, onClose }: { task: Task; onClose: () => void }) {
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const update = useUpdateTask();
  const qc = useQueryClient();

  const categorize = useMutation({
    mutationFn: () => llmApi.categorize(task.title, task.description),
    onSuccess: (r) =>
      setSuggestion({
        kind: 'category',
        value: r.category,
        rationale: r.rationale,
        confidence: r.confidence,
      }),
    onError: (e) => toast.error((e as Error).message),
  });

  const decompose = useMutation({
    mutationFn: () => llmApi.decompose(task.title, task.description),
    onSuccess: (r) => setSuggestion({ kind: 'subtasks', value: r.subtasks }),
    onError: (e) => toast.error((e as Error).message),
  });

  const prioritize = useMutation({
    mutationFn: () => llmApi.prioritize(task.title, task.description, task.due_date),
    onSuccess: (r) =>
      setSuggestion({
        kind: 'priority',
        value: r.priority,
        rationale: r.rationale,
        confidence: r.confidence,
      }),
    onError: (e) => toast.error((e as Error).message),
  });

  const accept = async () => {
    if (!suggestion) return;
    try {
      if (suggestion.kind === 'category') {
        await update.mutateAsync({ id: task.id, patch: { category: suggestion.value } });
        toast.success('Категория применена');
      } else if (suggestion.kind === 'priority') {
        await update.mutateAsync({ id: task.id, patch: { priority: suggestion.value } });
        toast.success('Приоритет применён');
      } else {
        await tasksApi.addSubtasks(
          task.id,
          suggestion.value.map((s, i) => ({ title: s.title, done: false, position: i })),
        );
        await qc.invalidateQueries({ queryKey: ['tasks'] });
        toast.success('Подзадачи добавлены');
      }
      setSuggestion(null);
      onClose();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const isLoading =
    categorize.isPending || decompose.isPending || prioritize.isPending;

  return (
    <div className="space-y-2 text-xs">
      <div className="flex flex-wrap gap-1.5">
        <button onClick={() => categorize.mutate()} className={btnCls} disabled={isLoading}>
          {categorize.isPending ? <Spinner /> : '🏷️'} Категория
        </button>
        <button onClick={() => decompose.mutate()} className={btnCls} disabled={isLoading}>
          {decompose.isPending ? <Spinner /> : '🪓'} Разбить на подзадачи
        </button>
        <button onClick={() => prioritize.mutate()} className={btnCls} disabled={isLoading}>
          {prioritize.isPending ? <Spinner /> : '⚡'} Предложить приоритет
        </button>
      </div>

      {suggestion && (
        <div className="rounded-lg border border-accent/40 bg-accent/5 p-2">
          <SuggestionView s={suggestion} />
          <div className="mt-2 flex justify-end gap-2">
            <button onClick={() => setSuggestion(null)} className="text-muted hover:text-fg">
              Отклонить
            </button>
            <button
              onClick={accept}
              className="rounded bg-accent px-2 py-1 text-white hover:opacity-90"
            >
              Применить
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function SuggestionView({ s }: { s: Suggestion }) {
  if (s.kind === 'category') {
    return (
      <p>
        Предлагаемая категория: <strong>#{s.value}</strong>{' '}
        <span className="text-muted">({Math.round(s.confidence * 100)}%) — {s.rationale}</span>
      </p>
    );
  }
  if (s.kind === 'priority') {
    return (
      <p>
        Предлагаемый приоритет: <strong>{s.value}</strong>{' '}
        <span className="text-muted">({Math.round(s.confidence * 100)}%) — {s.rationale}</span>
      </p>
    );
  }
  return (
    <ul className="list-disc pl-4">
      {s.value.map((x, i) => (
        <li key={i}>
          {x.title}
          {x.estimate_minutes ? <span className="text-muted"> · ~{x.estimate_minutes} мин</span> : null}
        </li>
      ))}
    </ul>
  );
}

const btnCls =
  'inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 hover:border-accent hover:text-accent disabled:opacity-50';

function Spinner() {
  return <Loader2 className="h-3 w-3 animate-spin" />;
}
