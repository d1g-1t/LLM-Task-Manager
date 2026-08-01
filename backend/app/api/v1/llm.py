from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.deps import LLMServiceDep, TaskServiceDep
from app.schemas.llm import (
    CategorizeRequest,
    CategorizeResponse,
    DecomposeRequest,
    DecomposeResponse,
    PrioritizeRequest,
    PrioritizeResponse,
    WorkloadSummaryResponse,
)
from app.schemas.task import TaskFilters

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/categorize", response_model=CategorizeResponse, summary="Suggest a category (US-3)")
async def categorize(payload: CategorizeRequest, llm: LLMServiceDep) -> CategorizeResponse:
    return await llm.categorize(payload.title, payload.description)


@router.post("/decompose", response_model=DecomposeResponse, summary="Break a task into subtasks (US-4)")
async def decompose(payload: DecomposeRequest, llm: LLMServiceDep) -> DecomposeResponse:
    return await llm.decompose(payload.title, payload.description, payload.max_subtasks)


@router.post("/prioritize", response_model=PrioritizeResponse, summary="Suggest a priority (US-5)")
async def prioritize(payload: PrioritizeRequest, llm: LLMServiceDep) -> PrioritizeResponse:
    return await llm.prioritize(payload.title, payload.description, payload.due_date)


@router.get(
    "/workload-summary",
    response_model=WorkloadSummaryResponse,
    summary="Natural-language workload summary (US-6)",
)
async def workload_summary(
    llm: LLMServiceDep,
    tasks: TaskServiceDep,
) -> WorkloadSummaryResponse:
    items, _ = await tasks.list(TaskFilters(limit=200, offset=0))
    return await llm.workload_summary(items)


@router.get("/workload-summary/stream", summary="Streaming workload summary (US-6)")
async def workload_summary_stream(
    llm: LLMServiceDep,
    tasks: TaskServiceDep,
) -> StreamingResponse:
    items, _ = await tasks.list(TaskFilters(limit=200, offset=0))

    async def generator():
        async for chunk in llm.workload_summary_stream(items):
            yield chunk

    return StreamingResponse(generator(), media_type="text/plain; charset=utf-8")
