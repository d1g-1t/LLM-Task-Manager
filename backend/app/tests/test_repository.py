"""Repository unit tests — verify SQL-level behavior."""
from __future__ import annotations

from app.domain.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.repositories.task_repository import TaskRepository


async def _add(session, **kw):
    t = Task(title=kw.pop("title", "T"), **kw)
    session.add(t)
    await session.flush()
    return t


async def test_filter_by_status_and_priority(db_session):
    repo = TaskRepository(db_session)
    await _add(db_session, title="A", priority=TaskPriority.HIGH, status=TaskStatus.PENDING)
    await _add(db_session, title="B", priority=TaskPriority.LOW, status=TaskStatus.DONE)

    items, total = await repo.list(priority=TaskPriority.HIGH)
    assert total == 1
    assert items[0].title == "A"


async def test_pagination(db_session):
    repo = TaskRepository(db_session)
    for i in range(5):
        await _add(db_session, title=f"T{i}")
    items, total = await repo.list(limit=2, offset=1)
    assert total == 5
    assert len(items) == 2
