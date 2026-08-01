from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.errors import LLMError
from app.domain.enums import TaskPriority, TaskStatus
from app.models.task import Task
from app.schemas.llm import (
    CategorizeResponse,
    DecomposeResponse,
    PrioritizeResponse,
    SubtaskSuggestion,
    WorkloadSummaryResponse,
)
from app.services import prompts
from app.services.llm_cache import cached

log = logging.getLogger(__name__)


class LLMService:

    async def categorize(self, title: str, description: str | None) -> CategorizeResponse:
        payload = {"op": "categorize", "title": title, "description": description}

        async def producer() -> dict[str, Any]:
            return await self._chat_json(prompts.categorize_prompt(title, description))

        raw = await cached("categorize", payload, producer)
        return _validate(CategorizeResponse, raw)

    async def decompose(
        self, title: str, description: str | None, max_subtasks: int
    ) -> DecomposeResponse:
        payload = {
            "op": "decompose",
            "title": title,
            "description": description,
            "max": max_subtasks,
        }

        async def producer() -> dict[str, Any]:
            return await self._chat_json(
                prompts.decompose_prompt(title, description, max_subtasks)
            )

        raw = await cached("decompose", payload, producer)
        return _validate(DecomposeResponse, raw)

    async def prioritize(
        self, title: str, description: str | None, due_date: datetime | None
    ) -> PrioritizeResponse:
        payload = {
            "op": "prioritize",
            "title": title,
            "description": description,
            "due": due_date.isoformat() if due_date else None,
        }

        async def producer() -> dict[str, Any]:
            return await self._chat_json(prompts.prioritize_prompt(title, description, due_date))

        raw = await cached("prioritize", payload, producer)
        return _validate(PrioritizeResponse, raw)

    async def workload_summary(self, tasks: list[Task]) -> WorkloadSummaryResponse:
        snapshot, overdue_ids, upcoming_ids, stats = _build_snapshot(tasks)

        async def producer() -> str:
            return await self._chat_text(prompts.workload_summary_prompt(snapshot))

        # Cache the natural-language part keyed by the snapshot.
        text: str = await cached("summary", snapshot, producer)
        return WorkloadSummaryResponse(
            summary=text.strip(),
            overdue_ids=overdue_ids,
            upcoming_ids=upcoming_ids,
            stats=stats,
        )

    async def workload_summary_stream(self, tasks: list[Task]) -> AsyncIterator[str]:
        snapshot, *_ = _build_snapshot(tasks)
        async for chunk in self._chat_text_stream(prompts.workload_summary_prompt(snapshot)):
            yield chunk

    async def _chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        text = await self._chat_text(messages, json_mode=True)
        try:
            return json.loads(text)  # type: ignore[no-any-return]
        except json.JSONDecodeError as exc:
            log.warning("llm_invalid_json", extra={"raw": text[:300]})
            raise LLMError("LLM returned invalid JSON") from exc

    async def _chat_text(self, messages: list[dict[str, str]], *, json_mode: bool = False) -> str:
        if settings.llm_provider == "mock":
            return _mock_response(messages, json_mode=json_mode)

        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.llm_request_timeout,
        )
        kwargs: dict[str, Any] = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": 0.2,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.5, max=4),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        ):
            with attempt:
                resp = await client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
        return ""

    async def _chat_text_stream(
        self, messages: list[dict[str, str]]
    ) -> AsyncIterator[str]:
        if settings.llm_provider == "mock":
            text = _mock_response(messages, json_mode=False)
            for word in text.split():
                yield word + " "
            return

        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.llm_request_timeout,
        )
        stream = await client.chat.completions.create(
            model=settings.llm_model,
            messages=messages,
            temperature=0.2,
            stream=True,
        )
        async for chunk in stream:
            piece = chunk.choices[0].delta.content
            if piece:
                yield piece


def _validate(model: type, raw: dict[str, Any]):  # type: ignore[no-untyped-def]
    try:
        return model.model_validate(raw)
    except ValidationError as exc:
        log.warning("llm_schema_violation", extra={"errors": exc.errors()})
        raise LLMError("LLM response did not match the expected schema") from exc


def _build_snapshot(
    tasks: list[Task],
) -> tuple[str, list, list, dict[str, int]]:
    now = datetime.now(timezone.utc)
    by_status = {s.value: 0 for s in TaskStatus}
    by_priority = {p.value: 0 for p in TaskPriority}
    overdue: list = []
    upcoming: list = []
    rows: list[dict[str, Any]] = []
    for t in tasks:
        by_status[t.status.value] += 1
        by_priority[t.priority.value] += 1
        if t.due_date and t.status != TaskStatus.DONE:
            if t.due_date < now:
                overdue.append(t.id)
            elif (t.due_date - now).days <= 7:
                upcoming.append(t.id)
        rows.append(
            {
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.value,
                "due": t.due_date.isoformat() if t.due_date else None,
            }
        )
    snapshot_obj = {
        "now": now.isoformat(),
        "totals": {"all": len(tasks), **by_status, **by_priority},
        "tasks": rows[:50],
    }
    stats = {"total": len(tasks), **by_status, **by_priority,
             "overdue": len(overdue), "upcoming": len(upcoming)}
    return json.dumps(snapshot_obj, default=str), overdue, upcoming, stats


def _mock_response(messages: list[dict[str, str]], *, json_mode: bool) -> str:
    user_text = " ".join(m["content"] for m in messages if m["role"] == "user").lower()
    if json_mode and ("category" in user_text or "категори" in user_text):
        cat = _guess_category_ru(user_text)
        return json.dumps(
            {"category": cat, "confidence": 0.7, "rationale": "эвристика мок-провайдера"},
            ensure_ascii=False,
        )
    if json_mode and ("subtasks" in user_text or "подзадач" in user_text):
        return json.dumps(
            {
                "subtasks": [
                    {"title": "Сформулировать подход", "estimate_minutes": 15},
                    {"title": "Реализовать основную логику", "estimate_minutes": 60},
                    {"title": "Покрыть тестами", "estimate_minutes": 30},
                    {"title": "Ревью и финальная отправка", "estimate_minutes": 15},
                ]
            },
            ensure_ascii=False,
        )
    if "priority" in user_text and json_mode:
        priority = "high" if "asap" in user_text or "urgent" in user_text or "срочно" in user_text else "medium"
        return json.dumps(
            {"priority": priority, "confidence": 0.6, "rationale": "эвристика мок-провайдера"},
            ensure_ascii=False,
        )
    return _mock_workload_summary(messages)


def _guess_category_ru(text: str) -> str:
    rules: list[tuple[tuple[str, ...], str]] = [
        (("купить", "продукт", "магазин"), "покупки"),
        (("врач", "стоматолог", "здоров", "тренировк", "спорт"), "здоровье"),
        (("прочитать", "глав", "конспект", "курс", "обучен"), "обучение"),
        (("блог", "пост", "статья", "написать"), "контент"),
        (("ssl", "cron", "сервер", "deploy", "деплой", "инфраструктур"), "инфраструктура"),
        (("рефактор", "баг", "код", "тест", "миграц", "api", "pr ", "ci"), "разработка"),
        (("встреч", "созвон", "демо", "презентац", "клиент"), "работа"),
        (("оффер", "рекрутер", "интервью", "карьер"), "карьера"),
        (("полить", "уборк", "почт", "inbox", "лично"), "личное"),
    ]
    for keywords, cat in rules:
        if any(k in text for k in keywords):
            return cat
    return "общее"


def _mock_workload_summary(messages: list[dict[str, str]]) -> str:
    snapshot: dict[str, Any] = {}
    for m in messages:
        if m["role"] != "user":
            continue
        # Snapshot is the substring after "Снимок:" / "Snapshot:" — the rest is JSON.
        for marker in ("Снимок:", "Snapshot:"):
            idx = m["content"].find(marker)
            if idx != -1:
                raw = m["content"][idx + len(marker):].strip()
                try:
                    snapshot = json.loads(raw)
                except json.JSONDecodeError:
                    snapshot = {}
                break
        if snapshot:
            break

    totals: dict[str, int] = snapshot.get("totals", {}) if isinstance(snapshot, dict) else {}
    tasks: list[dict[str, Any]] = snapshot.get("tasks", []) if isinstance(snapshot, dict) else []
    now_iso = snapshot.get("now") if isinstance(snapshot, dict) else None
    try:
        now = datetime.fromisoformat(now_iso) if isinstance(now_iso, str) else datetime.now(timezone.utc)
    except ValueError:
        now = datetime.now(timezone.utc)

    total = int(totals.get("all", len(tasks)))
    pending = int(totals.get(TaskStatus.PENDING.value, 0))
    in_progress = int(totals.get(TaskStatus.IN_PROGRESS.value, 0))
    done = int(totals.get(TaskStatus.DONE.value, 0))
    high = int(totals.get(TaskPriority.HIGH.value, 0))
    medium = int(totals.get(TaskPriority.MEDIUM.value, 0))
    low = int(totals.get(TaskPriority.LOW.value, 0))

    overdue = 0
    upcoming = 0
    for t in tasks:
        due_iso = t.get("due")
        status = t.get("status")
        if not due_iso or status == TaskStatus.DONE.value:
            continue
        try:
            due = datetime.fromisoformat(due_iso)
        except ValueError:
            continue
        delta_days = (due - now).days
        if due < now:
            overdue += 1
        elif delta_days <= 7:
            upcoming += 1

    if total == 0:
        return (
            "Сейчас задач нет — отличный момент, чтобы спланировать ближайшую неделю "
            "или разобрать накопившиеся идеи."
        )

    parts: list[str] = []
    parts.append(
        f"Всего {total} {_plural(total, 'задача', 'задачи', 'задач')}: "
        f"{pending} в ожидании, {in_progress} в работе и {done} уже выполнено."
    )
    if overdue:
        parts.append(
            f"Просрочено {overdue} "
            f"{_plural(overdue, 'задача', 'задачи', 'задач')} — стоит закрыть это в первую очередь."
        )
    if upcoming:
        parts.append(
            f"Ещё {upcoming} {_plural(upcoming, 'задача', 'задачи', 'задач')} с дедлайном "
            "в ближайшие 7 дней."
        )
    if high or medium or low:
        parts.append(
            f"По приоритету: {high} высоких, {medium} средних, {low} низких."
        )

    if overdue and high:
        parts.append(
            "Рекомендую: сначала разберитесь с просроченными задачами высокого приоритета, "
            "затем закройте быстрые победы, чтобы поддержать темп."
        )
    elif overdue:
        parts.append(
            "Рекомендую: начните с просроченных задач, чтобы вернуть контроль над расписанием."
        )
    elif high:
        parts.append(
            "Рекомендую: сосредоточьтесь на высокоприоритетных задачах и параллельно "
            "закрывайте мелкие — это даст ощущение прогресса."
        )
    else:
        parts.append(
            "Нагрузка под контролем — хороший момент, чтобы сделать пару быстрых задач "
            "и спланировать следующий шаг."
        )
    return " ".join(parts)


def _plural(n: int, one: str, few: str, many: str) -> str:
    n = abs(n) % 100
    if 10 < n < 20:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many
