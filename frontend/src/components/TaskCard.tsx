'use client';

import { useState } from 'react';
import { useDeleteTask, useUpdateTask } from '@/lib/hooks';
import { cn, formatDate, isOverdue } from '@/lib/utils';
import type { Task, TaskPriority, TaskStatus } from '@/lib/types';
import { Trash2, Pencil, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import { TaskFormDialog } from './TaskFormDialog';
import { LLMPanel } from './LLMPanel';

const PRIO_STYLES: Record<TaskPriority, string> = {
  low: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/30',
  medium: 'bg-amber-500/10 text-amber-600 border-amber-500/30',
  high: 'bg-rose-500/10 text-rose-600 border-rose-500/30',
};

const STATUS_LABEL: Record<TaskStatus, string> = {
  pending: 'Ожидает',
  in_progress: 'В работе',
  done: 'Готово',
};

export function TaskCard({ task }: { task: Task }) {
  const [editing, setEditing] = useState(false);
  const [llmOpen, setLlmOpen] = useState(false);
  const update = useUpdateTask();
  const del = useDeleteTask();

  const overdue = isOverdue(task.due_date, task.status);

  return (
    <article
      className={cn(
        'rounded-lg border p-3 transition-shadow hover:shadow-sm',
        'border-border bg-bg',
        overdue && 'border-danger/40',
      )}
    >
      <div className="mb-1 flex items-start justify-between gap-2">
        <h4 className="text-sm font-medium leading-snug">{task.title}</h4>
        <div className="flex shrink-0 items-center gap-1">
          <button
            aria-label="Редактировать задачу"
            onClick={() => setEditing(true)}
            className="rounded p-1 text-muted hover:bg-border/50 hover:text-fg"
          >
            <Pencil className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label="AI-ассистент"
            onClick={() => setLlmOpen((v) => !v)}
            className="rounded p-1 text-muted hover:bg-border/50 hover:text-accent"
          >
            <Sparkles className="h-3.5 w-3.5" />
          </button>
          <button
            aria-label="Удалить задачу"
            onClick={() => {
              if (confirm(`Удалить «${task.title}»?`)) {
                del.mutate(task.id, {
                  onSuccess: () => toast.success('Задача удалена'),
                  onError: (e) => toast.error((e as Error).message),
                });
              }
            }}
            className="rounded p-1 text-muted hover:bg-danger/10 hover:text-danger"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      {task.description && (
        <p className="mb-2 line-clamp-3 text-xs text-muted">{task.description}</p>
      )}

      <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
        <span className={cn('rounded-full border px-2 py-0.5', PRIO_STYLES[task.priority])}>
          {task.priority}
        </span>
        <select
          aria-label="Изменить статус"
          value={task.status}
          onChange={(e) =>
            update.mutate({ id: task.id, patch: { status: e.target.value as TaskStatus } })
          }
          className="rounded-full border border-border bg-transparent px-2 py-0.5"
        >
          {(['pending', 'in_progress', 'done'] as TaskStatus[]).map((s) => (
            <option key={s} value={s}>
              {STATUS_LABEL[s]}
            </option>
          ))}
        </select>
        {task.category && (
          <span className="rounded-full border border-border px-2 py-0.5 text-muted">
            #{task.category}
          </span>
        )}
        {task.due_date && (
          <span className={cn('text-muted', overdue && 'text-danger')}>
            ⏰ {formatDate(task.due_date)}
          </span>
        )}
      </div>

      {task.subtasks.length > 0 && (
        <ul className="mt-2 space-y-0.5 text-xs">
          {task.subtasks.map((st) => (
            <li key={st.id} className={cn('text-muted', st.done && 'line-through opacity-60')}>
              • {st.title}
            </li>
          ))}
        </ul>
      )}

      {llmOpen && (
        <div className="mt-3 border-t border-border pt-3">
          <LLMPanel task={task} onClose={() => setLlmOpen(false)} />
        </div>
      )}

      {editing && <TaskFormDialog open onOpenChange={setEditing} task={task} />}
    </article>
  );
}
