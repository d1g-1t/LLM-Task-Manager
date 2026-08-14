"""End-to-end API tests via httpx ASGI transport."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone


async def test_health(client):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_crud_flow(client):
    payload = {
        "title": "Write blog post",
        "description": "About FastAPI patterns",
        "priority": "high",
        "status": "pending",
    }
    r = await client.post("/api/v1/tasks", json=payload)
    assert r.status_code == 201, r.text
    created = r.json()
    task_id = created["id"]

    r = await client.get(f"/api/v1/tasks/{task_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Write blog post"

    r = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert r.status_code == 200
    assert r.json()["status"] == "done"

    r = await client.delete(f"/api/v1/tasks/{task_id}")
    assert r.status_code == 204

    r = await client.get(f"/api/v1/tasks/{task_id}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_list_search_and_pagination(client):
    for i, title in enumerate(["Buy milk", "Buy bread", "Read paper"]):
        await client.post(
            "/api/v1/tasks",
            json={"title": title, "priority": "medium", "status": "pending"},
        )
    r = await client.get("/api/v1/tasks", params={"search": "buy", "limit": 10})
    body = r.json()
    assert body["total"] == 2
    assert all("Buy" in i["title"] for i in body["items"])


async def test_validation_error_returns_envelope(client):
    r = await client.post("/api/v1/tasks", json={"title": "   "})
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "validation_error"


async def test_filter_overdue(client):
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    await client.post(
        "/api/v1/tasks",
        json={"title": "Late one", "priority": "high", "status": "pending", "due_date": past},
    )
    r = await client.get("/api/v1/tasks", params={"overdue": "true"})
    body = r.json()
    assert any(i["title"] == "Late one" for i in body["items"])
