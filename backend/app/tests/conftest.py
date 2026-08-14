"""Pytest fixtures: in-memory aiosqlite engine + httpx test client.

Tests run against SQLite to avoid requiring Postgres, while the production
schema runs on Postgres via Alembic. The Task model is portable (UUID is
stored as text on SQLite via a custom type-decorator effect). For the test
schema we recreate metadata directly.
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure mock provider before any app module imports.
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/15")
os.environ.setdefault("CORS_ORIGINS", "*")
os.environ.setdefault("ENVIRONMENT", "test")

# Now safe to import the app.
from app.api.deps import get_task_service  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402
from app.models import task as _models  # noqa: F401,E402
from app.repositories.task_repository import TaskRepository  # noqa: E402
from app.services import llm_cache  # noqa: E402
from app.services.task_service import TaskService  # noqa: E402


# ---- in-memory cache stub: bypass real Redis in unit tests ------------------


@pytest.fixture(autouse=True)
def _bypass_llm_cache(monkeypatch):
    async def _direct(_ns, _payload, producer, *, ttl=None):
        return await producer()

    monkeypatch.setattr(llm_cache, "cached", _direct)


# ---- async DB fixtures ------------------------------------------------------


@pytest.fixture
async def engine():
    eng = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with eng.begin() as conn:
        # SQLite has no gen_random_uuid(); generate UUIDs in Python instead.
        from sqlalchemy import event
        from app.models.task import Subtask, Task
        # Drop server defaults that depend on Postgres.
        for tbl in (Task.__table__, Subtask.__table__):
            for col in tbl.columns:
                if col.server_default is not None and "gen_random_uuid" in str(col.server_default.arg):
                    col.server_default = None
                    col.default = lambda: __import__("uuid").uuid4()
                if col.server_default is not None and "now()" in str(col.server_default.arg):
                    col.server_default = None
                    from datetime import datetime, timezone as tz
                    col.default = lambda: datetime.now(tz.utc)
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session_factory(engine):
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def db_session(session_factory) -> AsyncIterator[AsyncSession]:
    async with session_factory() as s:
        yield s
        await s.rollback()


@pytest.fixture
async def client(session_factory) -> AsyncIterator[AsyncClient]:
    async def _override_session():
        async with session_factory() as s:
            try:
                yield s
                await s.commit()
            except Exception:
                await s.rollback()
                raise

    def _override_service():
        # Constructed per-request via _override_session above; FastAPI handles wiring.
        raise RuntimeError("not used")

    app.dependency_overrides[get_session] = _override_session
    # get_task_service depends on get_session, so overriding session is enough.
    app.dependency_overrides.pop(get_task_service, None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def task_service(db_session) -> TaskService:
    return TaskService(TaskRepository(db_session))
