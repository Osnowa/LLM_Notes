# database/db.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from environs import Env
from typing import Annotated
from fastapi import Depends

env = Env()
env.read_env()

engine = create_async_engine(env.str("DATABASE_URL_PS"), 
                             pool_size=5, 
                             max_overflow=10, 
                             pool_pre_ping=True
                             )

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)
# expire_on_commit=False — доступ к атрибутам объекта работает и после закрытия сессии


## == Создание не нужно, так как Alembic == ##

# async def create_tables():
#     '''Создание таблиц в БД'''
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
        
async def get_session():
    '''Создание сессии'''
    async with SessionFactory() as session:
        yield session

async def dispose_engine():
    '''Закрытие соединения с БД'''
    await engine.dispose()

# для использования в зависимостях FastAPI
SessionDep = Annotated[AsyncSession, Depends(get_session)]
