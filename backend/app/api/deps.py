from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.repositories.task_repository import TaskRepository
from app.services.llm_service import LLMService
from app.services.task_service import TaskService


def get_task_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TaskService:
    return TaskService(TaskRepository(session))


def get_llm_service() -> LLMService:
    return LLMService()


SessionDep = Annotated[AsyncSession, Depends(get_session)]
TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
LLMServiceDep = Annotated[LLMService, Depends(get_llm_service)]
