### == Репозиторий для работы с БД PostgreSQL == ###

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database_postrgre.models import User, NoteUser
from app.schemas import SNoteOut, SNoteOutLLM, SNoteUpdate


class RepoDB:
    """Репозиторий для работы с БД PostgreSQL"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_notes(self, user: User, note: SNoteOutLLM):
        note_us = NoteUser(
            user_id=user.id,
            category=note.category,
            description=note.description,
            priority=note.priority,
            deadline=note.deadline,
        )

        self.session.add(note_us)
        await self.session.commit()
        await self.session.refresh(note_us)
        return note_us

    async def get_note(self, user: User, note_id: int):
        """Получение заметки (1 штучки по id заметки)"""
        res = await self.session.execute(
            select(NoteUser).where(NoteUser.id == note_id, NoteUser.user_id == user.id)
        )
        return res.scalars().one_or_none()  # получаем заметку или None

    async def get_notes(
        self, user: User, category, priority, created_at, deadline, limit, offset
    ):
        """Получение заметок"""
        stmt = (
            select(NoteUser)
            .where(NoteUser.user_id == user.id)
            .limit(limit)
            .offset(offset)
            .order_by(NoteUser.created_at.desc())
        )
        if category:
            stmt = stmt.where(NoteUser.category == category)
        if priority:
            stmt = stmt.where(NoteUser.priority == priority)
        if created_at:
            stmt = stmt.where(NoteUser.created_at == created_at)
        if deadline:
            stmt = stmt.where(NoteUser.deadline == deadline)

        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def update_note(self, user: User, note_id: int, note: SNoteUpdate):
        """Обновление заметки"""

        res = await self.session.execute(
            select(NoteUser).where(NoteUser.id == note_id, NoteUser.user_id == user.id)
        )

        note_us = res.scalars().one()

        if note.category is not None:
            note_us.category = note.category

        if note.description is not None:
            note_us.description = note.description

        if note.priority is not None:
            note_us.priority = note.priority

        if note.deadline is not None:
            note_us.deadline = note.deadline

        await self.session.commit()
        await self.session.refresh(note_us)

        return note_us

    async def delete_note(self, user: User, note_id: int):
        """Удаляем заметку"""
        res = await self.session.execute(
            delete(NoteUser).where(NoteUser.id == note_id, NoteUser.user_id == user.id)
        )
        await self.session.commit()

        return

    async def get_notes_search(self, user: User, filters):
        """Поиск заметок по запросу от LLM"""
        stmt = select(NoteUser).where(NoteUser.user_id == user.id)

        if filters.priority:
            stmt = stmt.where(NoteUser.priority == filters.priority)

        if filters.category:
            stmt = stmt.where(NoteUser.category == filters.category)

        if filters.created_from:
            stmt = stmt.where(NoteUser.created_at >= filters.created_from)

        if filters.created_to:
            stmt = stmt.where(NoteUser.created_at <= filters.created_to)

        if filters.deadline_from:
            stmt = stmt.where(NoteUser.deadline >= filters.deadline_from)

        if filters.deadline_to:
            stmt = stmt.where(NoteUser.deadline <= filters.deadline_to)

        res = await self.session.execute(stmt)
        return res.scalars().all()
