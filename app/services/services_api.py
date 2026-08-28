import json

from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas import SNoteOutLLM, SNoteOut

from app.database_postrgre.repo_dbp import RepoDB

### Сервис для ручек API ###


class ServicApi:
    """Сервис для ручек API"""

    def __init__(self, session, red, llm_client, user):
        self.repo_dbp = RepoDB(session)  # Репозиторий для работы с БД PostgreSQL
        self.red = red  # Redis
        self.llm = llm_client  # LLM
        self.user = user  # Пользователь

    async def create_notes(self, message):
        """Создание заметки"""
        response = await self.llm.generate_json(
            message
        )  # генерация заметки, получаем строку

        try:
            data = json.loads(response)  # преобразуем в словарь
            validated = SNoteOutLLM.model_validate(data)  # валидация
        except (json.JSONDecodeError, ValidationError) as e:
            raise HTTPException(status_code=400, detail=str(e))

        res = await self.repo_dbp.add_notes(
            self.user, validated
        )  # передаем user и заметку в репозиторий БД PostgreSQL

        await self.red.delete(f"notes:{self.user.id}")  # удаляем из кэша (всех заметок)

        return res

    async def get_note(self, note_id):
        """Получение заметки (1 штучки по id заметки)"""
        res_cache = await self.red.get(f"note:{self.user.id}:{note_id}")

        if res_cache:
            return SNoteOut.model_validate_json(res_cache)

        res = await self.repo_dbp.get_note(self.user, note_id)  # проверяем кеш

        if res is None:
            return None

        note = SNoteOut.model_validate(res)

        await self.red.setex(  # записываем в кэш
            f"note:{self.user.id}:{note_id}", 600, note.model_dump_json()
        )

        return note

    async def get_notes(self, category, priority, created_at, deadline, limit, offset):
        """Получение заметок (по фильтрам)"""

        # Redis используем только если фильтров нет
        if not any([category, priority, created_at, deadline, limit, offset]):
            res_cache = await self.red.get(f"notes:{self.user.id}")

            if res_cache:
                return json.loads(res_cache)

        res = await self.repo_dbp.get_notes(
            self.user, category, priority, created_at, deadline, limit, offset
        )

        notes = [SNoteOut.model_validate(note) for note in res]

        # Кешируем только полный список
        if not any([category, priority, created_at, deadline, limit, offset]):
            await self.red.setex(
                f"notes:{self.user.id}",
                600,
                json.dumps([note.model_dump() for note in notes]),
            )

        return notes

    async def update_note(self, note_id, note):
        """Обновление заметки (1 штучки по id заметки)"""
        # Проверяем, что такая заметка есть
        note_bd = await RepoDB(self.repo_dbp.session).get_note(self.user, note_id)

        if note_bd is None:
            return None

        res = await self.repo_dbp.update_note(self.user, note_id, note)

        await self.red.delete(
            f"note:{self.user.id}:{note_id}"
        )  # удаляем из кэша (замекта)
        await self.red.delete(f"notes:{self.user.id}")  # удаляем из кэша (всех заметок)

        return res

    async def delete_note(self, note_id):
        """Удаление заметки (1 штучки по id заметки)"""
        # Проверяем, что такая заметка есть
        note_bd = await RepoDB(self.repo_dbp.session).get_note(self.user, note_id)

        if note_bd is None:
            return None

        res = await self.repo_dbp.delete_note(self.user, note_id)

        await self.red.delete(
            f"note:{self.user.id}:{note_id}"
        )  # удаляем из кэша (замекта)
        await self.red.delete(f"notes:{self.user.id}")  # удаляем из кэша (всех заметок)

        return
