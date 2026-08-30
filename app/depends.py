import chromadb
from environs import Env
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.database_redis.db_redis import dispose_redis
from app.database_postrgre.db_postgre import dispose_engine
from app.llm.llm_prov import LLMClient
from app.llm.repo_chroma import ChromaRepository

###
### == Тут храним все зависимости для FastAPI == ###
###

env = Env()
env.read_env()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # зависимость llm
    llm_client = LLMClient.create_client(
        env.str("LLM_CLIENT"),
        env.str("LLM_OLLAMA_ADRES"),
        env.str("LLM_OLLAMA_MODEL"),
        env.str("MISTRAL_MODEL"),
        env.str("MISTRAL_KEY"),
    )
    app.state.llm_client = llm_client
    
    # chroma
    client = await chromadb.AsyncHttpClient(
        host="chroma",
        port=8000,
    )

    chroma_repo = ChromaRepository(client)
    app.state.chroma_client = chroma_repo

    # то что деалет до старта
    yield  # то что делает во время
    # то что деалет при завершении

    await dispose_engine()  # Закрытие соединения с PostgreSQL
    await dispose_redis()  # Закрытие соединения с Redis
    await llm_client.close()  # закрытие соединения с httpx
    await app.state.chroma.close()  # закрытие соединения с chroma
