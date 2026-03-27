from fastapi import APIRouter
from app.api.v1.endpoints import (
    chat, sessions, tasks, files, email, search, settings_api
)

api_router = APIRouter()

api_router.include_router(chat.router,         tags=["Chat"])
api_router.include_router(sessions.router,     tags=["Sessions"])
api_router.include_router(tasks.router,        tags=["Tasks"])
api_router.include_router(files.router,        tags=["Files"])
api_router.include_router(email.router,        tags=["Email"])
api_router.include_router(search.router,       tags=["Search"])
api_router.include_router(settings_api.router, tags=["Settings"])
