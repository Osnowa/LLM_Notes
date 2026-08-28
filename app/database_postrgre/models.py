from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, String, Enum
from enum import StrEnum
from datetime import date


class Base(DeclarativeBase):
    """Базовый класс, от него создаем таблицы"""

    pass


class Priority(StrEnum):
    """Приоритет заметки"""

    low = "low"
    high = "high"


class User(Base):
    """Пользователь"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        unique=True,
    )

    email: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    hashed_password: Mapped[str] = mapped_column(String(200))


class NoteUser(Base):
    """Заметки пользователей"""

    __tablename__ = "notes_user"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    category: Mapped[str] = mapped_column(String(100))

    description: Mapped[str] = mapped_column(String(100))

    priority: Mapped[Priority] = mapped_column(
        Enum(Priority),
        default=Priority.low,
    )

    created_at: Mapped[date] = mapped_column(
        default=date.today,
    )

    deadline: Mapped[date | None] = mapped_column(
        default=None,
        nullable=True,
    )
