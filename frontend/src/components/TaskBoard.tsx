'use client';

import { useTasks } from '@/lib/hooks';
import type { TaskFilters, TaskStatus } from '@/lib/types';
import { TaskCard } from './TaskCard';

const COLUMNS: Array<{ id: TaskStatus; title: string }> = [
  { id: 'pending', title: 'Ожидает' },
  { id: 'in_progress', title: 'В работе' },
  { id: 'done', title: 'Готово' },
];

export function TaskBoard({ filters }: { filters: TaskFilters }) {
  const { data, isLoading, isError, error } = useTasks(filters);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {COLUMNS.map((c) => (
          <div key={c.id} className="rounded-xl border border-border p-3">
            <h3 className="mb-3 text-sm font-medium text-muted">{c.title}</h3>
            <div className="space-y-2">
              {Array.from({ length: 2 }).map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-lg bg-border/40" />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-danger/40 bg-danger/10 p-4 text-sm">
        Ошибка загрузки задач: {(error as Error).message}
      </div>
    );
  }

  const items = data?.items ?? [];

  return (
    <>
      <div className="text-xs text-muted">
        {data?.total ?? 0} задач{filters.search ? ` по запросу «${filters.search}»` : ''}
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {COLUMNS.map((col) => {
          const colItems = items.filter((t) => t.status === col.id);
          return (
            <div key={col.id} className="rounded-xl border border-border bg-bg p-3">
              <h3 className="mb-3 flex items-center justify-between text-sm font-medium">
                <span>{col.title}</span>
                <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted">
                  {colItems.length}
                </span>
              </h3>
              <div className="space-y-2">
                {colItems.length === 0 ? (
                  <p className="text-xs text-muted">Нет задач.</p>
                ) : (
                  colItems.map((t) => <TaskCard key={t.id} task={t} />)
                )}
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
