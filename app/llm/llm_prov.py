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
    async def close(self) -> None:
        pass


def get_system_prompt() -> str:
    """Общий prompt для всех LLM."""

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

    async def close(self) -> None:
        """
        Mistral SDK здесь отдельно закрывать не требуется.
        Клиент создаётся один раз в lifespan.
        """
        pass


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

    async def close(self) -> None:
        """Закрытие соединения с httpx."""

        await self._client.aclose()
