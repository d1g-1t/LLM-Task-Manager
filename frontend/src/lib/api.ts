import type { ApiErrorBody } from './types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  status: number;
  code: string;
  details?: unknown;
  constructor(message: string, status: number, code: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit & { query?: Record<string, unknown> } = {},
): Promise<T> {
  const { query, ...rest } = init;
  const url = new URL(BASE_URL + path);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v === undefined || v === null || v === '') continue;
      url.searchParams.set(k, String(v));
    }
  }
  const res = await fetch(url.toString(), {
    ...rest,
    headers: {
      'content-type': 'application/json',
      ...(rest.headers ?? {}),
    },
    cache: 'no-store',
  });

  if (!res.ok) {
    let body: ApiErrorBody | null = null;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      /* ignore */
    }
    throw new ApiError(
      body?.error.message ?? `Request failed (${res.status})`,
      res.status,
      body?.error.code ?? 'http_error',
      body?.error.details,
    );
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export { BASE_URL };
