from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from app.database_postrgre.db_postgre import get_session
from app.database_postrgre.models import User
from app.auth.service import decode_access_token

# "Инструмент", который говорит FastAPI как достать токен из запроса.
http_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),   # FastAPI сам достанет токен из заголовка
    session: AsyncSession = Depends(get_session),  # FastAPI сам вызовет get_session()
) -> User:
    '''Проверка на авторизацию'''
    token = credentials.credentials

    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Невалидный токен или срок действия истёк",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)  # расшифровываем → получаем словарь
    if not payload:
        raise exc

    user_id = payload.get("sub")  # достаём id пользователя
    if not user_id:
        raise exc

    user = await session.get(User, int(user_id))  # ищем в БД по id
    if not user:
        raise exc

    return user  # вот он — объект User, попадёт в current_user эндпоинта


CurrentUser = Annotated[User, Depends(get_current_user)]


