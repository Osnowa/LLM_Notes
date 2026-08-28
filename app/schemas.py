from pydantic import BaseModel, ConfigDict, EmailStr
from app.database_postrgre.models import Priority
from datetime import date

### ==             == ###
### == Схемы для регистрации и авторизации в систему == ###
### ==             == ###


class SUserRegister(BaseModel):
    """Схема для регистрации пользователя"""

    email: EmailStr
    password: str


class SUserLogin(BaseModel):
    """Схема для авторизации пользователя"""

    email: EmailStr
    password: str


# Ответ — без пароля!
class SUserOut(BaseModel):
    """Схема для вывода пользователей после регистрации"""

    id: int
    email: str
    model_config = {"from_attributes": True}  # работает с ORM-объектами


class SToken(BaseModel):
    """Схема для токена"""

    access_token: str
    token_type: str = "bearer"


### ==             == ###
### == Схемы для работы с заметками == ###
### ==             == ###


class SNoteAdd(BaseModel):
    """Схема для добавления заметки"""

    category: str
    description: str
    priority: str | None
    created_at: str | None
    deadline: str | None

    model_config = ConfigDict(from_attributes=True)


class SNoteUpdate(BaseModel):
    """Схема для обновления заметки"""

    category: str | None
    description: str | None
    priority: Priority | None
    created_at: str | None
    deadline: date | None

    model_config = ConfigDict(from_attributes=True)


class SNoteOut(BaseModel):
    """Схема для вывода заметки"""

    id: int
    category: str
    description: str
    priority: str | None
    created_at: str | None
    deadline: date | None

    model_config = ConfigDict(from_attributes=True)


### == Для LLM == ###


class SNoteCreate(BaseModel):
    """Создание заметки"""

    text: str


class SNoteOutLLM(BaseModel):
    """Что должна отдавать LLM"""

    category: str
    description: str
    priority: str | None
    deadline: date | None

    model_config = ConfigDict(from_attributes=True)
    # Backend там добавляет created_at, id
