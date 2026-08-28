from abc import ABC, abstractmethod
import datetime

import environs
import httpx
from mistralai.client import Mistral

env = environs.Env()
env.read_env()


class LLMClient(ABC):
    """Абстрактный класс для работы с LLM."""

    @staticmethod
    def create_client(
        client_type: str,
        ollama_adres: str,
        ollama_model: str,
        mistral_model: str,
        mistral_key: str,
    ):
        if client_type == "mistral":
            return MistralClient(mistral_model, mistral_key)

        if client_type == "ollama":
            return OllamaClient(ollama_adres, ollama_model)

        raise ValueError(f"Unknown client type: {client_type}")

    @abstractmethod
    async def generate_json(self, messages: str) -> str:
        pass

    @abstractmethod
    async def generate_response(self, messages: str) -> str:
        pass

    @abstractmethod
    async def generate_search(self, messages: str) -> str:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass


def get_system_prompt() -> str:
    """Общий prompt для всех LLM. Для создания заметки."""

    date_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    return f"""
Ты — парсер задач.

Твоя задача — преобразовать текст пользователя в JSON-объект задачи.

НИКОГДА не объясняй свой ответ.
НИКОГДА не пиши код.
НИКОГДА не используй markdown.
НИКОГДА не добавляй текст до или после JSON.

Разрешён ТОЛЬКО такой JSON:

{{
    "category": "string",
    "description": "string",
    "priority": "low | high",
    "deadline": "string | null"
}}

Правила:
- category — категория заметки.
- description — сама задача пользователя.
- priority — low или high.
- deadline — дата в формате YYYY-MM-DD или null.

Правила priority:

- Если пользователь НЕ указывает важность или срочность явно — priority = low.
- Сам факт наличия deadline НЕ означает высокий приоритет.
- "Купить молоко завтра" → priority = low.
- "Купить молоко завтра, это срочно" → priority = high.
- "Купить молоко, это важно" → priority = high.
- "Купить молоко" → priority = low.

Правила deadline:

- Сегодняшняя дата: {date_now}
- "завтра" = следующий день после сегодняшней даты.
- "послезавтра" = через 2 дня.
- "через 3 дня" = через 3 дня.
- Всегда возвращай конкретную дату в формате YYYY-MM-DD.
- Если deadline отсутствует — null.

Пример:

Текст:
"Купить молоко завтра. Это очень важно."

Ответ:
{{
    "category": "shopping",
    "description": "Купить молоко",
    "priority": "high",
    "deadline": "2026-01-02"
}}

Ещё пример:

Текст:
"Позвонить маме."

Ответ:
{{
    "category": "personal",
    "description": "Позвонить маме",
    "priority": "low",
    "deadline": null
}}

Если текст невозможно преобразовать в задачу, или текст не подразумевает задачу, отправь:

"Невозможно преобразовать в задачу"

РАЗРЕШЕНО ТОЛЬКО отправить либо JSON, либо сообщение:
"Невозможно преобразовать в задачу"
"""


def get_prompt_search() -> str:
    """Промт для генерации атрибутов для поиска в БД"""
    date_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    return f"""
Ты — парсер поисковых запросов для заметок.

Твоя задача — преобразовать естественный язык пользователя
в JSON с параметрами поиска заметок.

НЕ ищи заметки сам.
НЕ обращайся к базе данных.
НЕ придумывай значения.
НЕ объясняй ответ.
НЕ используй markdown.

Разрешён ТОЛЬКО такой JSON:

{{
    "priority": "low | high | null",
    "category": "string | null",
    "deadline_from": "YYYY-MM-DD | null",
    "deadline_to": "YYYY-MM-DD | null",
    "created_from": "YYYY-MM-DD | null",
    "created_to": "YYYY-MM-DD | null"
}}

Сегодняшняя дата: {date_now}

Правила priority:

- "важные", "срочные" → high
- "обычные", "неважные" → low
- если приоритет не указан → null

Правила deadline:

- "на сегодня" → deadline_from = сегодняшняя дата,
  deadline_to = сегодняшняя дата

- "на завтра" → deadline_from = дата завтра,
  deadline_to = дата завтра

- "до 1 сентября" → deadline_to = 1 сентября

- "после 1 сентября" → deadline_from = 1 сентября

- "с 1 по 10 сентября" → deadline_from = 1 сентября,
  deadline_to = 10 сентября

- "между 1 и 10 сентября" → deadline_from = 1 сентября,
  deadline_to = 10 сентября

- если deadline не указан → оба значения null

Правила created_at:

- "созданные после 20 августа" → created_from = 20 августа
- "созданные до 20 августа" → created_to = 20 августа
- "созданные с 20 августа" → created_from = 20 августа
- "созданные с 20 по 25 августа" →
  created_from = 20 августа,
  created_to = 25 августа
- если дата создания не указана → оба значения null

Правила category:

- если пользователь указывает категорию → category = эта категория
- иначе → null

Примеры:

Пользователь:
"Покажи важные задачи на завтра"

Ответ:
{{
    "priority": "high",
    "category": null,
    "deadline_from": "2026-08-29",
    "deadline_to": "2026-08-29",
    "created_from": null,
    "created_to": null
}}

Пользователь:
"Покажи задачи с дедлайном до 1 сентября"

Ответ:
{{
    "priority": null,
    "category": null,
    "deadline_from": null,
    "deadline_to": "2026-09-01",
    "created_from": null,
    "created_to": null
}}

Пользователь:
"Покажи задачи с дедлайном между 1 и 10 сентября"

Ответ:
{{
    "priority": null,
    "category": null,
    "deadline_from": "2026-09-01",
    "deadline_to": "2026-09-10",
    "created_from": null,
    "created_to": null
}}

Пользователь:
"Покажи задачи, созданные после 20 августа"

Ответ:
{{
    "priority": null,
    "category": null,
    "deadline_from": null,
    "deadline_to": null,
    "created_from": "2026-08-20",
    "created_to": null
}}

Пользователь:
"Покажи важные рабочие задачи с дедлайном до 5 сентября"

Ответ:
{{
    "priority": "high",
    "category": "work",
    "deadline_from": null,
    "deadline_to": "2026-09-05",
    "created_from": null,
    "created_to": null
}}
"""


### == MistralClient (облачная API ) == ###


class MistralClient(LLMClient):
    """Облачная LLM Mistral."""

    def __init__(self, model: str, key: str):
        self.model = model
        self.client = Mistral(api_key=key)

    async def generate_json(self, messages: str) -> str:
        """Генерация заметки."""

        response = await self.client.chat.complete_async(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": get_system_prompt(),
                },
                {
                    "role": "user",
                    "content": messages,
                },
            ],
            max_tokens=200,
            temperature=0.2,
        )

        message = response.choices[0].message

        if message is None:
            raise RuntimeError("Mistral returned empty message")

        content = message.content

        if not isinstance(content, str):
            raise RuntimeError("Mistral returned non-text content")

        return content

    async def generate_response(self, messages: str) -> str:
        """Генерация обычного ответа пользователю."""
        raise NotImplementedError

    async def generate_search(self, messages: str) -> str:
        """Генерация запроса поиска для БД"""
        response = await self.client.chat.complete_async(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": get_prompt_search(),
                },
                {
                    "role": "user",
                    "content": messages,
                },
            ],
            max_tokens=200,
            temperature=0.2,
        )

        message = response.choices[0].message

        if message is None:
            raise RuntimeError("Mistral returned empty message")

        content = message.content

        if not isinstance(content, str):
            raise RuntimeError("Mistral returned non-text content")

        return content

    async def close(self) -> None:
        """
        Mistral SDK здесь отдельно закрывать не требуется.
        Клиент создаётся один раз в lifespan.
        """
        pass


### == Ollama (локальная LLM) == ###


class OllamaClient(LLMClient):
    """Локальная LLM Ollama."""

    def __init__(self, adres: str, model: str):
        self.adres = adres
        self.model = model
        self._client = httpx.AsyncClient(timeout=120)

    async def generate_json(self, messages: str) -> str:
        """Генерация заметки."""

        response = await self._client.post(
            self.adres,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": get_system_prompt(),
                    },
                    {
                        "role": "user",
                        "content": messages,
                    },
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 2048,
                },
            },
        )

        response.raise_for_status()

        return response.json()["message"]["content"]

    async def generate_response(self, messages: str) -> str:
        """Генерация обычного ответа пользователю."""
        raise NotImplementedError

    async def generate_search(self, messages: str) -> str:
        """Генерация запроса поиска для БД"""
        response = await self._client.post(
            self.adres,
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": get_prompt_search(),
                    },
                    {
                        "role": "user",
                        "content": messages,
                    },
                ],
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 2048,
                },
            },
        )

        response.raise_for_status()

        return response.json()["message"]["content"]

    async def close(self) -> None:
        """Закрытие соединения с httpx."""

        await self._client.aclose()
