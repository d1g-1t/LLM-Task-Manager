from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import TaskPriority


class CategorizeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None


class CategorizeResponse(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class DecomposeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    max_subtasks: int = Field(default=6, ge=1, le=12)


class SubtaskSuggestion(BaseModel):
    title: str
    estimate_minutes: int | None = None


class DecomposeResponse(BaseModel):
    subtasks: list[SubtaskSuggestion]


class PrioritizeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    due_date: datetime | None = None


class PrioritizeResponse(BaseModel):
    priority: TaskPriority
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class WorkloadSummaryResponse(BaseModel):
    summary: str
    overdue_ids: list[UUID] = Field(default_factory=list)
    upcoming_ids: list[UUID] = Field(default_factory=list)
    stats: dict[str, int] = Field(default_factory=dict)
