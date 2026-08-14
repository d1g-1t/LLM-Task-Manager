export type TaskPriority = 'low' | 'medium' | 'high';
export type TaskStatus = 'pending' | 'in_progress' | 'done';

export interface Subtask {
  id: string;
  title: string;
  done: boolean;
  position: number;
  created_at: string;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  category: string | null;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  subtasks: Subtask[];
}

export interface TaskListResponse {
  items: Task[];
  total: number;
  limit: number;
  offset: number;
}

export interface TaskCreateInput {
  title: string;
  description?: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  category?: string | null;
  due_date?: string | null;
  subtasks?: Array<{ title: string; done?: boolean; position?: number }>;
}
export type TaskUpdateInput = Partial<Omit<TaskCreateInput, 'subtasks'>>;

export interface TaskFilters {
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  overdue?: boolean;
  due_before?: string;
  due_after?: string;
  limit?: number;
  offset?: number;
}

export interface ApiErrorBody {
  error: { code: string; message: string; status: number; details?: unknown };
}

// LLM
export interface CategorizeResponse {
  category: string;
  confidence: number;
  rationale: string;
}
export interface SubtaskSuggestion {
  title: string;
  estimate_minutes: number | null;
}
export interface DecomposeResponse {
  subtasks: SubtaskSuggestion[];
}
export interface PrioritizeResponse {
  priority: TaskPriority;
  confidence: number;
  rationale: string;
}
export interface WorkloadSummaryResponse {
  summary: string;
  overdue_ids: string[];
  upcoming_ids: string[];
  stats: Record<string, number>;
}
