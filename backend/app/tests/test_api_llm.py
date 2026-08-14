"""LLM endpoints — exercised against the mock provider."""
from __future__ import annotations


async def test_categorize(client):
    r = await client.post(
        "/api/v1/llm/categorize",
        json={"title": "Buy groceries", "description": "milk, bread"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["category"]
    assert 0.0 <= body["confidence"] <= 1.0


async def test_decompose(client):
    r = await client.post(
        "/api/v1/llm/decompose",
        json={"title": "Launch landing page", "max_subtasks": 4},
    )
    assert r.status_code == 200
    subs = r.json()["subtasks"]
    assert 1 <= len(subs) <= 4


async def test_prioritize(client):
    r = await client.post(
        "/api/v1/llm/prioritize",
        json={"title": "Fix urgent prod bug ASAP", "description": "users blocked"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["priority"] in {"low", "medium", "high"}


async def test_workload_summary_empty(client):
    r = await client.get("/api/v1/llm/workload-summary")
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert "stats" in body


async def test_workload_summary_stream(client):
    r = await client.get("/api/v1/llm/workload-summary/stream")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    assert len(r.text) > 0
