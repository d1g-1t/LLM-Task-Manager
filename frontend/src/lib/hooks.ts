'use client';

import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query';
import { tasksApi } from './client';
import type {
  Task,
  TaskCreateInput,
  TaskFilters,
  TaskListResponse,
  TaskUpdateInput,
} from './types';

const KEYS = {
  all: ['tasks'] as const,
  list: (f: TaskFilters) => [...KEYS.all, 'list', f] as const,
  detail: (id: string) => [...KEYS.all, 'detail', id] as const,
};

export function useTasks(filters: TaskFilters) {
  return useQuery<TaskListResponse>({
    queryKey: KEYS.list(filters),
    queryFn: () => tasksApi.list(filters),
    placeholderData: (prev) => prev, // smooth filter updates
  });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: TaskCreateInput) => tasksApi.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

export function useUpdateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, patch }: { id: string; patch: TaskUpdateInput }) =>
      tasksApi.update(id, patch),
    onMutate: async ({ id, patch }) => {
      await qc.cancelQueries({ queryKey: KEYS.all });
      const snapshots = qc.getQueriesData<TaskListResponse>({ queryKey: KEYS.all });
      for (const [key, data] of snapshots) {
        if (!data) continue;
        qc.setQueryData<TaskListResponse>(key, {
          ...data,
          items: data.items.map((t) => (t.id === id ? ({ ...t, ...patch } as Task) : t)),
        });
      }
      return { snapshots };
    },
    onError: (_e, _v, ctx) => {
      ctx?.snapshots.forEach(([k, d]) => qc.setQueryData(k, d));
    },
    onSettled: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tasksApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  });
}
