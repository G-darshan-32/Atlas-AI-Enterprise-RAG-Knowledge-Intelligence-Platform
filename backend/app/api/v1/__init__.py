from fastapi import APIRouter
from app.api.v1.routes import (
    auth, workspaces, documents, chat, search,
    github, analytics, reports, notifications, admin, ws
)

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",         tags=["Authentication"])
api_router.include_router(workspaces.router,    prefix="/workspaces",   tags=["Workspaces"])
api_router.include_router(documents.router,     prefix="/workspaces",   tags=["Documents"])
api_router.include_router(chat.router,          prefix="/workspaces",   tags=["Chat"])
api_router.include_router(search.router,        prefix="/workspaces",   tags=["Search"])
api_router.include_router(github.router,        prefix="/workspaces",   tags=["GitHub"])
api_router.include_router(analytics.router,     prefix="/workspaces",   tags=["Analytics"])
api_router.include_router(reports.router,       prefix="/workspaces",   tags=["Reports"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin.router,         prefix="/admin",        tags=["Admin"])
api_router.include_router(ws.router,            prefix="",              tags=["WebSocket"])
