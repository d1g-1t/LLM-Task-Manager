from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete

from app.db.session import SessionLocal
from app.domain.enums import TaskPriority, TaskStatus
from app.models.task import Subtask, Task

NOW = datetime.now(timezone.utc)


def days(n: int) -> datetime:
    return NOW + timedelta(days=n)


def hours(n: int) -> datetime:
    return NOW + timedelta(hours=n)


@dataclass(frozen=True)
class SeedTask:
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    category: str
    due_date: datetime | None
    subtasks: list[tuple[str, bool]] = field(default_factory=list)


DEMO: list[SeedTask] = [
    SeedTask(
        title="Подготовить демо для фаундеров",
        description=(
            "Нужно показать MVP на пятничном звонке: слайды по проблеме/решению, "
            "живой прогон сценария создания задачи и LLM-разбиения, технический "
            "чек-лист (миграции, healthchecks, логи). Резерв-план — записанное видео."
        ),
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        category="работа",
        due_date=hours(20),
        subtasks=[
            ("Собрать 5 слайдов про проблему и решение", True),
            ("Сделать сухой прогон сценария", True),
            ("Записать резервное видео demo", False),
            ("Подготовить ответы на вопросы по архитектуре", False),
        ],
    ),
    SeedTask(
        title="Починить race condition в rate-limit middleware",
        description=(
            "Под нагрузкой иногда зависает auth-эндпоинт. Подозрение на дедлок "
            "между Redis-INCR и token bucket. Воспроизводится локально под k6 "
            "при 200 RPS. Логи в Sentry: TKR-1421."
        ),
        priority=TaskPriority.HIGH,
        status=TaskStatus.IN_PROGRESS,
        category="разработка",
        due_date=days(2),
        subtasks=[
            ("Воспроизвести локально через k6", True),
            ("Добавить tracing-спаны вокруг блокировок", False),
            ("Заменить блокирующий INCR на Lua-скрипт", False),
            ("Добавить регрессионный тест", False),
        ],
    ),
    SeedTask(
        title="Продлить SSL-сертификат для api.example.com",
        description="Let's Encrypt истекает через сутки. ACME-bot молчит, проверить cron.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        category="инфраструктура",
        due_date=days(-1),
        subtasks=[
            ("Проверить cron на проде", False),
            ("Перевыпустить вручную если нужно", False),
        ],
    ),
    SeedTask(
        title="Ответить рекрутеру по офферу",
        description="Нужен финальный ответ до конца недели. Согласовать дату выхода.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        category="карьера",
        due_date=days(-2),
    ),
    SeedTask(
        title="Написать пост в блог про N+1 в SQLAlchemy",
        description=(
            "Разобрать на примере SQLAlchemy 2.0: чем отличается selectinload от "
            "joinedload, когда что выбирать, как ловить лишние запросы через "
            "echo=True или sqltap. 800-1000 слов, два графика, примеры кода."
        ),
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        category="контент",
        due_date=days(7),
        subtasks=[
            ("Набросать оглавление", True),
            ("Собрать примеры запросов", False),
            ("Сделать бенчмарк до и после", False),
            ("Прогнать через корректор", False),
        ],
    ),
    SeedTask(
        title="Сделать code review PR #482 (поисковый индекс)",
        description="Коллега добавил GIN trigram. Проверить план запросов и пограничные случаи с пустой строкой.",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        category="разработка",
        due_date=days(1),
    ),
    SeedTask(
        title="Обновить зависимости фронтенда",
        description="Next.js 15.1 → 15.2, React Query 5.62 → 5.65. Прогнать smoke-тесты и lighthouse.",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.IN_PROGRESS,
        category="разработка",
        due_date=days(4),
        subtasks=[
            ("Запустить npm outdated", True),
            ("Обновить пакеты", True),
            ("Прогнать vitest и lighthouse", False),
        ],
    ),
    SeedTask(
        title="Запланировать встречу с командой дизайна",
        description="Обсудить новую систему токенов и тёмную тему для мобильной версии.",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        category="работа",
        due_date=days(3),
    ),
    SeedTask(
        title="Перевести события аналитики в ClickHouse",
        description=(
            "Текущая таблица events в Postgres растёт на 50М строк в месяц. "
            "Сделать ETL в ClickHouse и Materialized View для агрегатов."
        ),
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.PENDING,
        category="разработка",
        due_date=days(10),
        subtasks=[
            ("Спроектировать схему таблиц", False),
            ("Написать ETL на dbt", False),
            ("Перенаправить дашборды на новые источники", False),
        ],
    ),
    SeedTask(
        title="Купить продукты на неделю",
        description="Молоко, хлеб, овощи, чай, оливковое масло, кофе в зёрнах.",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        category="личное",
        due_date=days(2),
    ),
    SeedTask(
        title="Записаться к стоматологу",
        description="Профилактический осмотр раз в полгода. Клиника на Маяковской.",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        category="здоровье",
        due_date=days(14),
    ),
    SeedTask(
        title="Прочитать главу из «Designing Data-Intensive Applications»",
        description="Глава 7 про транзакции — изоляция, snapshot isolation, serializability.",
        priority=TaskPriority.LOW,
        status=TaskStatus.IN_PROGRESS,
        category="обучение",
        due_date=None,
        subtasks=[
            ("Прочитать главу", False),
            ("Записать конспект в Obsidian", False),
        ],
    ),
    SeedTask(
        title="Разобрать почту в inbox",
        description="Накопилось около 120 писем. Inbox zero за один присест.",
        priority=TaskPriority.LOW,
        status=TaskStatus.PENDING,
        category="личное",
        due_date=days(1),
    ),
    SeedTask(
        title="Настроить GitHub Actions CI",
        description="Backend: ruff, mypy и pytest с сервисами postgres/redis. Frontend: lint, typecheck, тесты, сборка.",
        priority=TaskPriority.HIGH,
        status=TaskStatus.DONE,
        category="разработка",
        due_date=days(-3),
        subtasks=[
            ("Настроить матрицу backend", True),
            ("Настроить матрицу frontend", True),
            ("Включить кэширование npm и uv", True),
        ],
    ),
    SeedTask(
        title="Накатить Alembic-миграцию для GIN trigram индекса",
        description="pg_trgm + GIN на (title || description) для быстрого ILIKE-поиска.",
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.DONE,
        category="разработка",
        due_date=days(-5),
    ),
    SeedTask(
        title="Полить цветы",
        description="Особенно фикус — листья опускаются.",
        priority=TaskPriority.LOW,
        status=TaskStatus.DONE,
        category="личное",
        due_date=days(-1),
    ),
]


async def main() -> None:
    async with SessionLocal() as session:
        await session.execute(delete(Subtask))
        await session.execute(delete(Task))

        for row in DEMO:
            task = Task(
                title=row.title,
                description=row.description,
                priority=row.priority,
                status=row.status,
                category=row.category,
                due_date=row.due_date,
            )
            session.add(task)
            await session.flush()
            for i, (title, done) in enumerate(row.subtasks):
                session.add(
                    Subtask(task_id=task.id, title=title, done=done, position=i)
                )
        await session.commit()

    overdue = sum(
        1
        for t in DEMO
        if t.due_date and t.due_date < NOW and t.status != TaskStatus.DONE
    )
    total_subtasks = sum(len(t.subtasks) for t in DEMO)
    print(
        f"✔ загружено задач: {len(DEMO)} "
        f"(подзадач: {total_subtasks}, просрочено: {overdue})"
    )


if __name__ == "__main__":
    asyncio.run(main())
