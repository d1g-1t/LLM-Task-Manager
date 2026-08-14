import { apiFetch } from './api';
import type {
  Task,
  TaskCreateInput,
  TaskFilters,
  TaskListResponse,
  TaskUpdateInput,
  CategorizeResponse,
  DecomposeResponse,
  PrioritizeResponse,
  WorkloadSummaryResponse,
} from './types';

export const tasksApi = {
  list: (f: TaskFilters = {}) =>
    apiFetch<TaskListResponse>('/tasks', { query: f as Record<string, unknown> }),
  get: (id: string) => apiFetch<Task>(`/tasks/${id}`),
  create: (body: TaskCreateInput) =>
    apiFetch<Task>('/tasks', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: TaskUpdateInput) =>
    apiFetch<Task>(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  remove: (id: string) => apiFetch<void>(`/tasks/${id}`, { method: 'DELETE' }),
  addSubtasks: (
    id: string,
    items: Array<{ title: string; done?: boolean; position?: number }>,
  ) =>
    apiFetch<Task>(`/tasks/${id}/subtasks`, {
      method: 'POST',
      body: JSON.stringify(items),
    }),
};

export const llmApi = {
  categorize: (title: string, description: string | null) =>
    apiFetch<CategorizeResponse>('/llm/categorize', {
      method: 'POST',
      body: JSON.stringify({ title, description }),
    }),
  decompose: (title: string, description: string | null, max_subtasks = 6) =>
    apiFetch<DecomposeResponse>('/llm/decompose', {
      method: 'POST',
      body: JSON.stringify({ title, description, max_subtasks }),
    }),
  prioritize: (title: string, description: string | null, due_date: string | null) =>
    apiFetch<PrioritizeResponse>('/llm/prioritize', {
      method: 'POST',
      body: JSON.stringify({ title, description, due_date }),
    }),
  workloadSummary: () => apiFetch<WorkloadSummaryResponse>('/llm/workload-summary'),
};
