import redis.asyncio as aioredis
from environs import Env
from typing import Annotated
from fastapi import Depends

env = Env()
env.read_env()

# Подключение к БД Redis
redis_client = aioredis.Redis.from_url(env.str("REDIS_URL"), decode_responses=True)


def get_redis() -> aioredis.Redis:
    '''Функция для использования в зависимостях FastAPI'''
    return redis_client


async def dispose_redis():
    '''Закрытие соединения с БД'''
    await redis_client.aclose()

# для использования в зависимостях FastAPI
RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
