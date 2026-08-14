# 🧠 LLM Task Manager — Intelligent Task Manager

A web application for managing tasks (To-Do) with an integrated LLM assistant that can automatically categorize tasks, split them into subtasks, suggest priorities, and generate a natural-language workload summary (with streaming).

> A take-home assignment for the position **AI MVP Developer**. The project demonstrates a clean layered architecture, a modern tech stack, production-grade developer experience (DX), and full test coverage.

---

## 🚀 One-command startup

> Only **Docker Desktop** (or Docker + Compose v2) and `make` are required.

```bash
git clone <repo-url> llm-task-manager
cd llm-task-manager
make setup
```

`make setup` is the single command needed to fully start everything from scratch. It:

1. creates `.env` from `.env.example`;
2. builds Docker images (backend + frontend) with BuildKit cache;
3. brings up Postgres 16 and Redis 7, waits for `pg_isready`;
4. starts the backend (FastAPI) and frontend (Next.js);
5. applies Alembic migrations (extensions `pgcrypto` + `pg_trgm`, tables, GIN index, `updated_at` trigger);
6. seeds the database with demo data (16 tasks, various priorities/statuses/categories, overdue items, with subtasks).

After completion:

| Service | URL |
| --- | --- |
| 🖥️ Frontend | http://localhost:3000 |
| 🔌 Backend API | http://localhost:8000/api/v1 |
| 📖 Swagger UI | http://localhost:8000/docs |

Want it even shorter?

```bash
make demo   # = setup + automatically opens the browser
```

Works **without an OpenAI key** thanks to the built-in `mock` provider. To connect a real OpenAI account:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

---

## 1. Implemented features (per spec)

### Required user stories

| ID | Story | Where it lives |
| --- | --- | --- |
| **US-1** | CRUD for tasks (title, description, priority, status, due date, created_at) | `POST/GET/PATCH/DELETE /api/v1/tasks` · UI: kanban board + create/edit dialog |
| **US-2** | Filters (status + priority + overdue) and full-text search, **combinable on the server side** | `GET /api/v1/tasks?status=&priority=&search=&overdue=` · UI: filter chips + search with 250 ms debounce |
| **US-3** | LLM: smart categorization — button → suggestion → accept/reject | `POST /api/v1/llm/categorize` · UI: “🏷️ Category” panel |
| **US-4** | LLM: decompose a task into subtasks | `POST /api/v1/llm/decompose` · UI: “🪓 Split” panel → accepted subtasks are added via `POST /tasks/{id}/subtasks` |
| **US-5** | LLM: suggest priority based on description and due date | `POST /api/v1/llm/prioritize` · UI: “⚡ Suggest priority” panel |
| **US-6** | LLM: natural-language workload summary (overdue, upcoming deadlines, distribution) | `GET /api/v1/llm/workload-summary` (cached) **+ `/stream` with streaming** · UI: “AI summary” modal with streaming output |

### Beyond the spec

- 🧠 **Single-flight LLM cache** on Redis: identical concurrent requests share a single in-flight call — no duplicate costs or thundering herd.
- 🔍 **GIN trigram index** (`pg_trgm`) on `title || description` — ILIKE search runs in milliseconds even on 100k+ rows.
- 🚫 **N+1 eliminated** via `selectinload(Task.subtasks)` in every list/get request.
- 📡 **Streaming workload summaries** via `text/plain` chunked — the UI starts rendering the response immediately.
- ⚡ **Optimistic updates** in TanStack Query when changing status — no UI lags.
- 🐳 **Multi-stage Dockerfile** with an unprivileged user in prod, `HEALTHCHECK`, BuildKit cache mounts (uv for Python, npm cache for Node) — rebuild after code changes takes seconds.
- 🧪 **Tests on every layer** (pytest + Vitest), CI on GitHub Actions with matrices for backend and frontend.
- 🪵 **Structured JSON logs** via `python-json-logger`.
- 🛡️ **Unified error format** on backend and frontend (`{"error": {code, message, status, details}}`).

---

## 2. Installation and environment variables

### Host dependencies

- Docker Desktop ≥ 4.30 *(or Docker Engine 24+ + Compose v2)*
- GNU Make
- ~3 GB free space for images and DB volume

> Local Python / Node installation is **not required** — everything runs in containers.

### Environment variables (`.env`)

`make setup` creates `.env` from the `.env.example` template automatically. Key variables:

| Variable | Purpose | Default |
| --- | --- | --- |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Postgres access | `todo` / `todo` / `todo` |
| `DATABASE_URL` | DSN for backend | `postgresql+asyncpg://todo:todo@postgres:5432/todo` |
| `REDIS_URL` | DSN for Redis | `redis://redis:6379/0` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |
| `LLM_PROVIDER` | `mock` or `openai` | `mock` |
| `OPENAI_API_KEY` | OpenAI key (if `LLM_PROVIDER=openai`) | — |
| `LLM_MODEL` | Model name | `gpt-4o-mini` |
| `LLM_CACHE_TTL_SECONDS` | TTL for cached LLM responses in Redis | `3600` |
| `NEXT_PUBLIC_API_URL` | API URL for the frontend | `http://localhost:8000/api/v1` |

---

## 3. Running the application

### The big picture — `make` commands

| Command | What it does |
| --- | --- |
| `make setup` | 🚀 Full bootstrap from scratch (build → up → migrate → seed) |
| `make demo` | `setup` + automatically opens the browser |
| `make up` / `make down` | Start / stop the stack (volume persists) |
| `make restart` | Restart the stack |
| `make logs` | Live-tail logs of all services |
| `make ps` | Container status |
| `make health` | Smoke-check: containers status + `/health` |
| `make open` | Open the frontend in the browser |
| `make migrate` | Apply Alembic migrations |
| `make makemigration m="…"` | Generate a new migration |
| `make seed` | Insert demo data (idempotent) |
| `make test` | Backend (pytest) + frontend (vitest) |
| `make test-backend` / `make test-frontend` | Separately |
| `make coverage` | Coverage report for backend |
| `make lint` / `make format` / `make typecheck` | Code quality |
| `make shell-backend` / `make shell-frontend` | Shell into the container |
| `make clean` | Remove host caches |
| `make nuke` | ☠️ Completely destroy the stack **including the DB volume** |

`make help` will print the same list in the terminal.

### Hot-reload development

Backend and frontend run in hot-reload mode by default (uvicorn `--reload`, `next dev`). Local changes in `backend/app/...` or `frontend/src/...` are picked up instantly — container rebuild is not required.

```bash
make logs                       # everything in one terminal
docker compose logs -f backend  # backend only
docker compose logs -f frontend # frontend only
```

---

## 4. Architectural decisions

### Layered architecture with one-way dependencies

```
api  →  services  →  repositories  →  models / db
                  ↘ schemas (DTOs)
```

- **`api/v1/`** — FastAPI routers. Only request parsing, calling the service, and serialization. No business logic.
- **`services/`** — pure business logic (`TaskService`, `LLMService`). Does not import FastAPI or SQLAlchemy → unit tests without a DB.
- **`repositories/`** — the only layer that sees SQLAlchemy. Returns ORM entities.
- **`models/`** — SQLAlchemy 2.0 with typed `Mapped[...]`.
- **`schemas/`** — Pydantic v2 DTOs for requests/responses.
- **`core/`** — config (`pydantic-settings`), JSON logging, exception handlers, unified error envelope.
- **`db/`** — async engine + session factory + FastAPI dependency with auto-commit/rollback.

### Why this way

- **SQLAlchemy 2.0 async + asyncpg** — top-tier performance, typed `Mapped[...]`, native transactions.
- **`selectinload(Task.subtasks)`** in every list/get eliminates N+1 at the root.
- **`pg_trgm` GIN index** on `coalesce(title,'') || ' ' || coalesce(description,'')` — `ILIKE '%foo%'` executes in milliseconds. All filters (status / priority / overdue / search / due_before|after) are applied **on the server side** as composable SQL expressions (see §4.2 of the spec).
- **Versioned API** under `/api/v1` — advantage noted in §2.2 of the spec.
- **Single-flight LLM cache** (`services/llm_cache.py`) — concurrent identical requests share one in-flight call **before** the value appears in Redis.
- **JSON-mode + Pydantic validation** of LLM responses — invalid output raises `LLMError`, mapped to a structured 502.
- **Streaming workload summaries** via `StreamingResponse` + `ReadableStream.getReader()` on the frontend — immediate response.
- **Optimistic updates** in TanStack Query with snapshots and rollback on error.
- **Idempotent seed** (`make seed` can be run repeatedly — it clears tables before insertion).

### Prompt engineering (§3.1 of the spec)

All prompts live in `backend/app/services/prompts.py`:

- the global `SYSTEM_BASE` fixes the role and requires answering **only with valid JSON**;
- for each LLM function — a separate prompt-constructor function with the required task context;
- few-shot examples for categorization;
- the desired JSON schema is described directly in the prompt + additionally validated via Pydantic in the service layer;
- if the LLM returns invalid JSON — `LLMError(502)` with a human-readable message.

### Unified error format (§2.2 of the spec)

Backend and frontend share one envelope:

```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
      "status": 422,
      "details": []
  }
}
```

The frontend wrapper `apiFetch` parses it into a typed `ApiError` → toast notifications without stack traces in the UI.

### Tests

| Layer | What it covers |
| --- | --- |
| `test_task_service.py` | CRUD, partial updates, combined filters, overdue logic |
| `test_repository.py` | SQL behavior in in-memory aiosqlite |
| `test_api_tasks.py` | HTTP round-trips via httpx ASGI transport, envelope validation |
| `test_llm_service.py` | Mock provider, JSON parsing, validation |
| `test_api_llm.py` | Endpoints categorize / decompose / prioritize / summary / streaming |
| `frontend/src/tests/` | Utilities + extension point for MSW integration |

CI: GitHub Actions with two matrices — backend (with postgres+redis services) and frontend (lint + typecheck + test + build).

---

## 5. Known limitations and trade-offs

- **No authentication** — all tasks are global. Adding auth would be `user_id`-filtering in the repository + NextAuth/Supabase/custom JWT flow on the frontend; the architecture is ready for this.
- **Streaming via `text/plain` chunked** — simpler than full SSE with `Last-Event-ID` and reconnect. Sufficient for an MVP and easy to upgrade.
- **Mock LLM provider** — heuristic, intended only for demo and CI. For real semantics use `LLM_PROVIDER=openai`.
- **Single Postgres instance** — no read replicas or pgbouncer.
- **No rate-limiting** on LLM endpoints — public deployment would require protection against cost runaway.
- **Frontend tests are minimal** — utilities covered, left an extension point for MSW + integration tests for hooks.

---

## 6. What I would add given more time

- **AuthN/AuthZ** (NextAuth or Supabase) with row-level scoping and multi-tenant filtering.
- **WebSocket / SSE** for real-time push of changes between tabs and devices.
- **Background workers** (Arq / Celery) for non-interactive LLM tasks: weekly digest, batch categorization, embeddings for semantic search.
- **Drag-and-drop** on the kanban board (`@dnd-kit`).
- **Rate-limit + cost guard** on LLM endpoints.
- **Playwright E2E + visual regression** in CI.
- **OpenTelemetry** tracing through `API → DB → LLM`, export to Jaeger/Tempo, plus Sentry for errors.
- **Trigram similarity ranking** (`%>` operator) instead of pure ILIKE — fuzzy search with relevance.
- **Offline-first** via TanStack Query persistence + service worker.
- **i18n** — the UI is currently Russian, but the architecture is ready for translation (no hard-coded strings in business logic).

---

## 7. Repository structure

```
llm-task-manager/
├── backend/
│   ├── alembic/                  migrations
│   ├── app/
│   │   ├── api/v1/               FastAPI routers (tasks, llm, health)
│   │   ├── core/                 config, logging, errors
│   │   ├── db/                   engine, session factory
│   │   ├── domain/               enums (TaskStatus, TaskPriority)
│   │   ├── models/               SQLAlchemy 2.0 models
│   │   ├── repositories/         data-access layer
│   │   ├── schemas/              Pydantic DTOs
│   │   ├── services/             business logic + LLM
│   │   ├── scripts/seed.py       demo data
│   │   ├── tests/                pytest suite
│   │   └── main.py               ASGI app factory
│   ├── Dockerfile                multi-stage (dev / prod)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── app/                  Next.js App Router
│   │   ├── components/           TaskBoard, TaskCard, Filters, LLMPanel, …
│   │   ├── lib/                  api client, hooks, types, providers
│   │   └── tests/                vitest
│   ├── Dockerfile
│   └── package.json
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile                      ⭐ single entry point for all operations
└── .env.example
```

---

## 8. Tech stack

| Layer | Choice |
| --- | --- |
| **Backend** | Python 3.12 · **FastAPI** · **SQLAlchemy 2.0 async** + asyncpg · Alembic · Pydantic v2 · Tenacity · python-json-logger · orjson |
| **DB** | **PostgreSQL 16** + `pg_trgm` GIN index |
| **Cache** | **Redis 7** — read-through LLM cache + asyncio single-flight |
| **LLM** | OpenAI-compatible client with JSON mode, retries, **streaming** + built-in mock provider |
| **Frontend** | **Next.js 15** (App Router, RSC) · **React 19** · **TypeScript strict** · TanStack Query v5 · react-hook-form + Zod · Tailwind CSS · sonner · lucide-react |
| **Tests** | pytest + pytest-asyncio + httpx (ASGI transport) · Vitest + Testing Library |
| **Quality** | Ruff · mypy strict · ESLint · tsc · Prettier |
| **Infra** | Docker Compose · multi-stage Dockerfile · BuildKit cache · GitHub Actions CI · Makefile |

---

## 9. Accompanying note

- **Fastest MVP:** a working prototype in ~6 hours at a hackathon (Next.js + Supabase + OpenAI), end-to-end with auth and persistence.
- **AI tools:** ChatGPT, GitHub Copilot, Cursor — for scaffolding, refactoring, test generation and quickly learning unfamiliar APIs. I use them as a co-pilot, not autopilot: every line is reviewed.

