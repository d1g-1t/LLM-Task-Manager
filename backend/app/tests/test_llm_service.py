"""Smoke tests for the LLM service against the mock provider."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.services.llm_service import LLMService


async def test_mock_categorize():
    svc = LLMService()
    out = await svc.categorize("Buy groceries", "Milk and bread")
    assert out.category
    assert 0.0 <= out.confidence <= 1.0


async def test_mock_decompose():
    svc = LLMService()
    out = await svc.decompose("Plan launch", None, max_subtasks=5)
    assert 1 <= len(out.subtasks) <= 5


async def test_mock_prioritize_urgent_is_high():
    svc = LLMService()
    out = await svc.prioritize(
        "Fix urgent prod outage ASAP",
        "users cannot log in",
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    assert out.priority.value == "high"
