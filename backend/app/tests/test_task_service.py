"""Service-layer tests for TaskService."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.core.errors import NotFoundError
from app.domain.enums import TaskPriority, TaskStatus
from app.schemas.task import SubtaskCreate, TaskCreate, TaskFilters, TaskUpdate


async def _make(service, **kw):
    return await service.create(
        TaskCreate(title=kw.pop("title", "Demo"), **kw)
    )


async def test_create_and_get_roundtrip(task_service):
    created = await _make(task_service, description="d", priority=TaskPriority.HIGH)
    assert created.id is not None
    fetched = await task_service.get(created.id)
    assert fetched.title == "Demo"
    assert fetched.priority == TaskPriority.HIGH


async def test_create_with_subtasks(task_service):
    created = await task_service.create(
        TaskCreate(
            title="Parent",
            subtasks=[SubtaskCreate(title="A"), SubtaskCreate(title="B", position=1)],
        )
    )
    assert len(created.subtasks) == 2
    assert {s.title for s in created.subtasks} == {"A", "B"}


async def test_update_partial(task_service):
    t = await _make(task_service)
    updated = await task_service.update(t.id, TaskUpdate(status=TaskStatus.DONE))
    assert updated.status == TaskStatus.DONE
    assert updated.title == "Demo"  # untouched


async def test_delete(task_service):
    t = await _make(task_service)
    await task_service.delete(t.id)
    with pytest.raises(NotFoundError):
        await task_service.get(t.id)


async def test_get_missing_raises_not_found(task_service):
    from uuid import uuid4

    with pytest.raises(NotFoundError):
        await task_service.get(uuid4())


async def test_list_filters_combine(task_service):
    await _make(task_service, title="Buy milk", priority=TaskPriority.LOW)
    await _make(task_service, title="Ship release", priority=TaskPriority.HIGH,
                status=TaskStatus.IN_PROGRESS)
    await _make(task_service, title="Read book", priority=TaskPriority.LOW,
                status=TaskStatus.DONE)

    items, total = await task_service.list(
        TaskFilters(priority=TaskPriority.LOW, search="milk")
    )
    assert total == 1
    assert items[0].title == "Buy milk"


async def test_list_overdue_filter(task_service):
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=1)
    await _make(task_service, title="Late", due_date=past)
    await _make(task_service, title="Soon", due_date=future)

    items, total = await task_service.list(TaskFilters(overdue=True))
    titles = {i.title for i in items}
    assert "Late" in titles and "Soon" not in titles
    assert total >= 1
