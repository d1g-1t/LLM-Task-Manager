'use client';

import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateTask, useUpdateTask } from '@/lib/hooks';
import type { Task, TaskPriority, TaskStatus } from '@/lib/types';
import { toast } from 'sonner';

const schema = z.object({
  title: z.string().trim().min(1, 'Название обязательно').max(255),
  description: z.string().max(4000).optional().or(z.literal('')),
  priority: z.enum(['low', 'medium', 'high']),
  status: z.enum(['pending', 'in_progress', 'done']),
  category: z.string().max(64).optional().or(z.literal('')),
  due_date: z.string().optional().or(z.literal('')),
});
type FormValues = z.infer<typeof schema>;

export function TaskFormDialog({
  open,
  onOpenChange,
  task,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  task?: Task;
}) {
  const create = useCreateTask();
  const update = useUpdateTask();

  const { register, handleSubmit, reset, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: task?.title ?? '',
      description: task?.description ?? '',
      priority: (task?.priority ?? 'medium') as TaskPriority,
      status: (task?.status ?? 'pending') as TaskStatus,
      category: task?.category ?? '',
      due_date: task?.due_date ? task.due_date.slice(0, 16) : '',
    },
  });

  useEffect(() => {
    if (!open) reset();
  }, [open, reset]);

  if (!open) return null;

  const onSubmit = handleSubmit(async (values) => {
    const payload = {
      title: values.title,
      description: values.description || null,
      priority: values.priority,
      status: values.status,
      category: values.category || null,
      due_date: values.due_date ? new Date(values.due_date).toISOString() : null,
    };
    try {
      if (task) {
        await update.mutateAsync({ id: task.id, patch: payload });
        toast.success('Задача обновлена');
      } else {
        await create.mutateAsync(payload);
        toast.success('Задача создана');
      }
      onOpenChange(false);
    } catch (e) {
      toast.error((e as Error).message);
    }
  });

  return (
    <div
      role="dialog"
      aria-modal
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={() => onOpenChange(false)}
    >
      <form
        onClick={(e) => e.stopPropagation()}
        onSubmit={onSubmit}
        className="w-full max-w-lg space-y-3 rounded-xl border border-border bg-bg p-5 shadow-xl"
      >
        <h2 className="text-lg font-semibold">{task ? 'Редактировать задачу' : 'Новая задача'}</h2>

        <Field label="Название" error={formState.errors.title?.message}>
          <input className={inputCls} autoFocus {...register('title')} />
        </Field>
        <Field label="Описание">
          <textarea rows={3} className={inputCls} {...register('description')} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Приоритет">
            <select className={inputCls} {...register('priority')}>
              <option value="low">Низкий</option>
              <option value="medium">Средний</option>
              <option value="high">Высокий</option>
            </select>
          </Field>
          <Field label="Статус">
            <select className={inputCls} {...register('status')}>
              <option value="pending">Ожидает</option>
              <option value="in_progress">В работе</option>
              <option value="done">Готово</option>
            </select>
          </Field>
          <Field label="Категория">
            <input className={inputCls} placeholder="напр. work" {...register('category')} />
          </Field>
          <Field label="Срок выполнения">
            <input type="datetime-local" className={inputCls} {...register('due_date')} />
          </Field>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => onOpenChange(false)}
            className="rounded-lg border border-border px-3 py-2 text-sm"
          >
            Отмена
          </button>
          <button
            type="submit"
            disabled={formState.isSubmitting}
            className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-60"
          >
            {task ? 'Сохранить' : 'Создать'}
          </button>
        </div>
      </form>
    </div>
  );
}

const inputCls =
  'w-full rounded-lg border border-border bg-transparent px-3 py-2 text-sm outline-none focus:border-accent';

function Field({
  label,
  error,
  children,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs text-muted">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-danger">{error}</span>}
    </label>
  );
}
