from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from typing import TypeVar

import redis.asyncio as redis

from app.core.config import settings

T = TypeVar("T")

_redis_client: redis.Redis | None = None
_inflight: dict[str, asyncio.Future[object]] = {}
_inflight_lock = asyncio.Lock()


def _get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _key(namespace: str, payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return f"llm:{namespace}:{hashlib.sha256(raw).hexdigest()[:32]}"


async def cached(
    namespace: str,
    payload: object,
    producer: Callable[[], Awaitable[T]],
    *,
    ttl: int | None = None,
) -> T:
    key = _key(namespace, payload)
    r = _get_redis()

    cached_value = await r.get(key)
    if cached_value is not None:
        return json.loads(cached_value)  # type: ignore[no-any-return]

    async with _inflight_lock:
        future = _inflight.get(key)
        if future is None:
            future = asyncio.get_event_loop().create_future()
            _inflight[key] = future
            owner = True
        else:
            owner = False

    if not owner:
        return await future  # type: ignore[return-value]

    try:
        value = await producer()
        await r.set(
            key,
            json.dumps(value, default=str),
            ex=ttl if ttl is not None else settings.llm_cache_ttl_seconds,
        )
        future.set_result(value)
        return value
    except Exception as exc:
        future.set_exception(exc)
        raise
    finally:
        async with _inflight_lock:
            _inflight.pop(key, None)
