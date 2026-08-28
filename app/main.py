from fastapi import FastAPI
from environs import Env

from app.api.notes_router import router as notes_router
from app.depends import lifespan
from app.auth.router import router as auth_router

env = Env()
env.read_env()


app = FastAPI(
    lifespan=lifespan,
    title="Notes manager + LLM",
    description="Менеджер заметок для пользователя с LLM",
    version="0.0.1",
)

app.include_router(notes_router)
app.include_router(auth_router)
