from environs import Env
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.database_redis.db_redis import dispose_redis
from app.database_postrgre.db_postgre import dispose_engine
from app.llm.llm_prov import LLMClient

###
### == Тут храним все зависимости для FastAPI == ###
###

env = Env()
env.read_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    llm_client = LLMClient.create_client(
        env.str("LLM_CLIENT"),
        env.str("LLM_OLLAMA_ADRES"),
        env.str("LLM_OLLAMA_MODEL"),
        env.str("MISTRAL_MODEL"),
        env.str("MISTRAL_KEY"),
    )
    app.state.llm_client = llm_client
    yield
    await dispose_engine()  # Закрытие соединения с PostgreSQL
    await dispose_redis()  # Закрытие соединения с Redis
    await llm_client.close()  # закрытие соединения с httpx
