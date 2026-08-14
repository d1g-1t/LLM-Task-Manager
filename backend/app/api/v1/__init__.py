"""Aggregates v1 sub-routers under a single APIRouter."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import health, llm, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(llm.router)
