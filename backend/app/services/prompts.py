from __future__ import annotations

from datetime import datetime
from typing import Final


SYSTEM_BASE: Final = (
    "Ты — экспертный ассистент по продуктивности, встроенный в менеджер задач. "
    "Всегда отвечай **строгим JSON**, соответствующим схеме из user-сообщения. "
    "Не добавляй никаких пояснений вне JSON. Не выдумывай поля. "
    "Все текстовые поля (category, rationale, title подзадач и т.д.) должны быть "
    "НА РУССКОМ ЯЗЫКЕ. При сомнениях выбирай консервативный ответ."
)


def categorize_prompt(title: str, description: str | None) -> list[dict[str, str]]:
    user = (
        "Предложи РОВНО ОДНУ короткую категорию (1–2 слова, строчными буквами, "
        "на русском языке) для задачи. Используй существительные в именительном "
        "падеже. Примеры допустимых категорий: разработка, инфраструктура, "
        "работа, личное, здоровье, обучение, контент, карьера, финансы, дом, "
        "покупки, спорт.\n\n"
        'Верни JSON: {"category": str, "confidence": float in [0,1], '
        '"rationale": str <= 140 символов}.\n\n'
        "Примеры:\n"
        '- Задача: «Купить продукты на неделю» → '
        '{"category":"покупки","confidence":0.92,"rationale":"продукты — это покупки"}\n'
        '- Задача: «Отрефакторить auth middleware» → '
        '{"category":"разработка","confidence":0.95,"rationale":"рефакторинг кода"}\n\n'
        f"Название задачи: {title}\n"
        f"Описание задачи: {description or '(нет)'}\n"
        "Верни только JSON."
    )
    return [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": user},
    ]


def decompose_prompt(
    title: str, description: str | None, max_subtasks: int
) -> list[dict[str, str]]:
    user = (
        f"Разбей задачу на 2–{max_subtasks} мелких, конкретных и независимо "
        "выполнимых подзадач НА РУССКОМ ЯЗЫКЕ. Каждая подзадача — глагольная "
        "формулировка длиной до 80 символов. Где уместно — оцени время в минутах.\n\n"
        'Верни JSON: {"subtasks": [{"title": str, "estimate_minutes": int|null}, ...]}.\n\n'
        f"Название задачи: {title}\n"
        f"Описание задачи: {description or '(нет)'}\n"
        "Верни только JSON."
    )
    return [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": user},
    ]


def prioritize_prompt(
    title: str, description: str | None, due_date: datetime | None
) -> list[dict[str, str]]:
    due = due_date.isoformat() if due_date else "(срок не задан)"
    now = datetime.now().isoformat(timespec="seconds")
    user = (
        "Предложи приоритет задачи. Допустимые значения: 'low' | 'medium' | 'high'. "
        "Учитывай срочность (близость дедлайна), важность и зависимости.\n\n"
        'Верни JSON: {"priority": "low"|"medium"|"high", "confidence": float, '
        '"rationale": str <= 140 символов, на русском языке}.\n\n'
        f"Сейчас: {now}\n"
        f"Срок: {due}\n"
        f"Название задачи: {title}\n"
        f"Описание задачи: {description or '(нет)'}\n"
        "Верни только JSON."
    )
    return [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": user},
    ]


def workload_summary_prompt(snapshot_json: str) -> list[dict[str, str]]:
    user = (
        "Тебе дан JSON-снимок задач пользователя. "
        "Напиши краткую (4–6 предложений) дружелюбную сводку рабочей нагрузки "
        "НА РУССКОМ ЯЗЫКЕ. Обязательно упомяни: сколько задач всего, сколько "
        "просрочено, сколько с дедлайном в ближайшие 7 дней, распределение по "
        "приоритетам (низкий/средний/высокий) и статусам (ожидает/в работе/готово). "
        "В конце дай 1–2 практические рекомендации, с чего начать. "
        "Только обычный текст, без markdown, без списков, без эмодзи.\n\n"
        f"Снимок:\n{snapshot_json}\n"
    )
    return [
        {
            "role": "system",
            "content": (
                "Ты — продуктивный ассистент в менеджере задач. "
                "Отвечай ТОЛЬКО на русском языке, обычным текстом, без markdown."
            ),
        },
        {"role": "user", "content": user},
    ]
