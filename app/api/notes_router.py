from fastapi import APIRouter, HTTPException, status, Request
from app.database_postrgre.db_postgre import SessionDep
from app.auth.dependencies import CurrentUser
from app.database_redis.db_redis import RedisDep
from app.schemas import SNoteCreate, SNoteAdd, SNoteOut, SNoteUpdate, SNoteSearch

from app.services.services_api import ServicApi

from datetime import date

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("/", response_model=SNoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    request: Request,  # достаем llm
    note: SNoteCreate,  # форма заметки (для LLM)
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
):
    """Создание заметки"""
    llm = request.app.state.llm_client  # достаем llm
    client_chroma = request.app.state.chroma_client  # достаем БД CHROMA

    return await ServicApi(session, red, llm, user, client_chroma).create_notes(
        note.text
    )


@router.get("/search", response_model=list[SNoteOut])
async def search_notes(
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
    request: Request,
    text: str,
    limit: int = 5,
):
    """Поиск заметок через CHROMA"""
    client_chroma = request.app.state.chroma_client

    return await ServicApi(session, red, None, user, client_chroma).search_notes_chroma(
        text, limit
    )


@router.get("/{note_id}", status_code=status.HTTP_200_OK, response_model=SNoteOut)
async def get_note(
    note_id: int,
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
):
    res = await ServicApi(session, red, None, user, None).get_note(note_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return res


@router.get("/", status_code=status.HTTP_200_OK, response_model=list[SNoteOut])
async def get_notes(
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
    category: str | None = None,
    priority: str | None = None,
    created_at: date | None = None,
    deadline: date | None = None,
    limit: int = 20,
    offset: int = 0,
):

    res = await ServicApi(session, red, None, user, None).get_notes(
        category, priority, created_at, deadline, limit, offset
    )
    if res is None:
        raise HTTPException(status_code=404, detail="Notes not found")
    return res


@router.patch("/{note_id}", status_code=status.HTTP_200_OK, response_model=SNoteOut)
async def update_note(
    note_id: int,
    note: SNoteUpdate,
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
    request: Request
):
    client_chroma = request.app.state.chroma_client
    res = await ServicApi(session, red, None, user, client_chroma).update_note(note_id, note)

    if res is None:
        raise HTTPException(status_code=404, detail="Note not found")

    return res


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: int,
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
    request: Request
):
    client_chroma = request.app.state.chroma_client
    res = await ServicApi(session, red, None, user, client_chroma).delete_note(note_id)

    return


@router.post(
    "/search_llm", status_code=status.HTTP_200_OK, response_model=list[SNoteOut]
)
async def search_note(
    search: SNoteSearch,
    session: SessionDep,  # сессия к БД PostgreSQL
    user: CurrentUser,  # пользователь (проверка на авторизацию)
    red: RedisDep,  # сессия к БД Redis
    request: Request,  # достаем llm
):
    """Поиск заметок через LLM (отдает json для БД)"""
    llm = request.app.state.llm_client  # достаем llm
    res = await ServicApi(session, red, llm, user, None).search_notes(search.text)
    return res
