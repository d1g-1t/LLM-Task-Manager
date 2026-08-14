'use client';

import { cn } from '@/lib/utils';
import type { TaskFilters, TaskPriority, TaskStatus } from '@/lib/types';
import { Search } from 'lucide-react';
import { useEffect, useState } from 'react';

const STATUSES: Array<{ v: TaskStatus | 'all'; label: string }> = [
  { v: 'all', label: 'Все' },
  { v: 'pending', label: 'Ожидает' },
  { v: 'in_progress', label: 'В работе' },
  { v: 'done', label: 'Готово' },
];

const PRIORITIES: Array<{ v: TaskPriority | 'all'; label: string }> = [
  { v: 'all', label: 'Все' },
  { v: 'low', label: 'Низкий' },
  { v: 'medium', label: 'Средний' },
  { v: 'high', label: 'Высокий' },
];

export function Filters({
  value,
  onChange,
}: {
  value: TaskFilters;
  onChange: (f: TaskFilters) => void;
}) {
  const [text, setText] = useState(value.search ?? '');

  // Debounce search input -> onChange
  useEffect(() => {
    const t = setTimeout(() => {
      onChange({ ...value, search: text || undefined, offset: 0 });
    }, 250);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  return (
    <section className="flex flex-col gap-3 rounded-xl border border-border bg-bg p-3 sm:flex-row sm:items-center">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          aria-label="Поиск задач"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Поиск по названию или описанию…"
          className="w-full rounded-lg border border-border bg-transparent py-2 pl-9 pr-3 text-sm outline-none focus:border-accent"
        />
      </div>

      <Group label="Статус">
        {STATUSES.map((o) => (
          <Pill
            key={o.v}
            active={(value.status ?? 'all') === o.v}
            onClick={() =>
              onChange({ ...value, status: o.v === 'all' ? undefined : (o.v as TaskStatus), offset: 0 })
            }
          >
            {o.label}
          </Pill>
        ))}
      </Group>

      <Group label="Приоритет">
        {PRIORITIES.map((o) => (
          <Pill
            key={o.v}
            active={(value.priority ?? 'all') === o.v}
            onClick={() =>
              onChange({
                ...value,
                priority: o.v === 'all' ? undefined : (o.v as TaskPriority),
                offset: 0,
              })
            }
          >
            {o.label}
          </Pill>
        ))}
      </Group>

      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={!!value.overdue}
          onChange={(e) => onChange({ ...value, overdue: e.target.checked || undefined, offset: 0 })}
        />
        Просроченные
      </label>
    </section>
  );
}

function Group({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-xs uppercase tracking-wide text-muted">{label}</span>
      <div className="flex gap-1">{children}</div>
    </div>
  );
}

function Pill({
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
      onClick={onClick}
      className={cn(
        'rounded-full border px-2.5 py-1 text-xs',
        active
          ? 'border-accent bg-accent text-white'
          : 'border-border text-muted hover:text-fg',
      )}
    >
      {children}
    </button>
  );
}
