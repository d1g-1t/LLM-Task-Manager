from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.enums import TaskPriority, TaskStatus
from app.models.task import Subtask, Task


class TaskRepository:

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, task_id: UUID) -> Task | None:
        stmt = (
            select(Task)
            .options(selectinload(Task.subtasks))
            .where(Task.id == task_id)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        overdue: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Task], int]:
        base = self._apply_filters(
            select(Task),
            status=status,
            priority=priority,
            due_before=due_before,
            due_after=due_after,
            overdue=overdue,
            search=search,
        )
        total = (
            await self._session.execute(
                select(func.count()).select_from(base.order_by(None).subquery())
            )
        ).scalar_one()

        stmt: Select[Any] = (
            base.order_by(Task.created_at.desc())
            .limit(limit)
            .offset(offset)
            .options(selectinload(Task.subtasks))
        )
        items = list((await self._session.execute(stmt)).scalars().all())
        return items, int(total)

    async def list_for_summary(self) -> list[Task]:
        stmt = select(Task).options(selectinload(Task.subtasks))
        return list((await self._session.execute(stmt)).scalars().all())

    async def create(self, task: Task) -> Task:
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task, attribute_names=["id", "created_at", "updated_at"])
        return task

    async def update(self, task: Task, changes: dict[str, Any]) -> Task:
        for field, value in changes.items():
            setattr(task, field, value)
        await self._session.flush()
        await self._session.refresh(task, attribute_names=["updated_at"])
        return task

    async def delete(self, task: Task) -> None:
        await self._session.delete(task)
        await self._session.flush()

    async def add_subtasks(self, task: Task, subtasks: Iterable[Subtask]) -> None:
        for st in subtasks:
            st.task_id = task.id
            self._session.add(st)
        await self._session.flush()

    @staticmethod
    def _apply_filters(
        stmt: Select[Any],
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        due_before: datetime | None,
        due_after: datetime | None,
        overdue: bool | None,
        search: str | None,
    ) -> Select[Any]:
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if due_before is not None:
            stmt = stmt.where(Task.due_date <= due_before)
        if due_after is not None:
            stmt = stmt.where(Task.due_date >= due_after)
        if overdue:
            now = datetime.now(timezone.utc)
            stmt = stmt.where(Task.due_date.is_not(None), Task.due_date < now,
                              Task.status != TaskStatus.DONE)
        if search:
            pattern = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
            )
        return stmt
