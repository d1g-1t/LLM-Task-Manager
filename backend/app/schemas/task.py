from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import TaskPriority, TaskStatus



class SubtaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    done: bool = False
    position: int = 0


class SubtaskCreate(SubtaskBase):
    pass


class SubtaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    done: bool | None = None
    position: int | None = None


class SubtaskRead(SubtaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime



class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    category: str | None = Field(default=None, max_length=64)
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()


class TaskCreate(TaskBase):
    subtasks: list[SubtaskCreate] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    category: str | None = Field(default=None, max_length=64)
    due_date: datetime | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime
    subtasks: list[SubtaskRead] = Field(default_factory=list)


class TaskListResponse(BaseModel):
    items: list[TaskRead]
    total: int
    limit: int
    offset: int



class TaskFilters(BaseModel):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_before: datetime | None = None
    due_after: datetime | None = None
    overdue: bool | None = None
    search: str | None = Field(default=None, max_length=255)
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
