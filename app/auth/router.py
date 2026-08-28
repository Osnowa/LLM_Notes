from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.database_postrgre.db_postgre import SessionDep
from app.database_postrgre.models import User
from app.schemas import SUserRegister, SUserLogin, SUserOut, SToken
from app.auth.service import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/register", response_model=SUserOut, status_code=status.HTTP_201_CREATED)
async def register(user: SUserRegister, session: SessionDep):
    '''Регистрация пользователя'''
    # проверяем, что пользователь с таким email не зарегистрирован
    existitng = await session.execute(select(User).where(User.email == user.email))
    if existitng.scalars().one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже зарегистрирован"
        )

    # создаем пользователя, хешируем пароль
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    session.add(new_user) # добавляем в сессию
    await session.commit() # сохраняем в БД
    await session.refresh(new_user) # достаём id

    return new_user

@router.post("/login", response_model=SToken)
async def login(user_data: SUserLogin, session: SessionDep):
    '''Авторизация пользователя'''
    # Проерка, что такой email действительно существует, и что пароль верный
    result = await session.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    # проверяем, есть ли такой email и совпадает ли хеш пароля
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный логин или пароль"
        )

    # создаем токен
    access_token = create_access_token({"sub": str(user.id)}) # включаем в токен id пользователя (итого в payload {"sub": id, "exp": 30})
    return SToken(access_token=access_token) # токен уходит в теле ответа, клиент сам кладет его в заголовок и хранит
        
    