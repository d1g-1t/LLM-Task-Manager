'use client';

import { useState } from 'react';
import { TaskBoard } from '@/components/TaskBoard';
import { Filters } from '@/components/Filters';
import { TaskFormDialog } from '@/components/TaskFormDialog';
import { WorkloadSummaryButton } from '@/components/WorkloadSummary';
import type { TaskFilters } from '@/lib/types';
import { Plus } from 'lucide-react';

export default function HomePage() {
  const [filters, setFilters] = useState<TaskFilters>({ limit: 100 });
  const [open, setOpen] = useState(false);

  return (
    <main className="flex flex-col gap-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">Задачи</h1>
          <p className="text-sm text-muted">
            LLM Task Manager — интеллектуальный менеджер задач с AI-ассистентом.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <WorkloadSummaryButton />
          <button
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white shadow hover:opacity-90"
          >
            <Plus className="h-4 w-4" />
            Новая задача
          </button>
        </div>
      </header>

      <Filters value={filters} onChange={setFilters} />
      <TaskBoard filters={filters} />

      <TaskFormDialog open={open} onOpenChange={setOpen} />
    </main>
  );
}
