from __future__ import annotations

from uuid import UUID

from app.core.errors import NotFoundError
from app.models.task import Subtask, Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import SubtaskCreate, TaskCreate, TaskFilters, TaskUpdate


class TaskService:
    def __init__(self, repo: TaskRepository) -> None:
        self._repo = repo

    async def list(self, filters: TaskFilters) -> tuple[list[Task], int]:
        return await self._repo.list(
            status=filters.status,
            priority=filters.priority,
            due_before=filters.due_before,
            due_after=filters.due_after,
            overdue=filters.overdue,
            search=filters.search,
            limit=filters.limit,
            offset=filters.offset,
        )

    async def get(self, task_id: UUID) -> Task:
        task = await self._repo.get(task_id)
        if task is None:
            raise NotFoundError(f"Task {task_id} not found")
        return task

    async def create(self, payload: TaskCreate) -> Task:
        task = Task(
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status=payload.status,
            category=payload.category,
            due_date=payload.due_date,
        )
        task = await self._repo.create(task)
        if payload.subtasks:
            subtasks = [
                Subtask(title=s.title, done=s.done, position=s.position)
                for s in payload.subtasks
            ]
            await self._repo.add_subtasks(task, subtasks)
        return await self.get(task.id)

    async def update(self, task_id: UUID, payload: TaskUpdate) -> Task:
        task = await self.get(task_id)
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return task
        return await self._repo.update(task, changes)

    async def delete(self, task_id: UUID) -> None:
        task = await self.get(task_id)
        await self._repo.delete(task)

    async def add_subtasks(self, task_id: UUID, items: list[SubtaskCreate]) -> Task:
        task = await self.get(task_id)
        base_pos = max((s.position for s in task.subtasks), default=-1) + 1
        new = [
            Subtask(title=s.title, done=s.done, position=base_pos + i)
            for i, s in enumerate(items)
        ]
        await self._repo.add_subtasks(task, new)
        return await self.get(task_id)
