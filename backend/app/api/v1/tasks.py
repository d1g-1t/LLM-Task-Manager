from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.deps import TaskServiceDep
from app.schemas.task import (
    SubtaskCreate,
    TaskCreate,
    TaskFilters,
    TaskListResponse,
    TaskRead,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskListResponse, summary="List tasks (filter + search)")
async def list_tasks(
    service: TaskServiceDep,
    filters: Annotated[TaskFilters, Query()],
) -> TaskListResponse:
    items, total = await service.list(filters)
    return TaskListResponse(
        items=[TaskRead.model_validate(i) for i in items],
        total=total,
        limit=filters.limit,
        offset=filters.offset,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED, summary="Create task")
async def create_task(payload: TaskCreate, service: TaskServiceDep) -> TaskRead:
    task = await service.create(payload)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead, summary="Get task by id")
async def get_task(task_id: UUID, service: TaskServiceDep) -> TaskRead:
    return TaskRead.model_validate(await service.get(task_id))


@router.patch("/{task_id}", response_model=TaskRead, summary="Update task")
async def update_task(
    task_id: UUID, payload: TaskUpdate, service: TaskServiceDep
) -> TaskRead:
    return TaskRead.model_validate(await service.update(task_id, payload))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    response_class=Response,
)
async def delete_task(task_id: UUID, service: TaskServiceDep) -> Response:
    await service.delete(task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{task_id}/subtasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Append subtasks to a task",
)
async def add_subtasks(
    task_id: UUID, payload: list[SubtaskCreate], service: TaskServiceDep
) -> TaskRead:
    task = await service.add_subtasks(task_id, payload)
    return TaskRead.model_validate(task)
